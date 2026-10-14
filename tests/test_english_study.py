"""v0.5, step 4: a study run in English: its fictional base, questionnaire and language."""

import hashlib
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import glossary
from ddict.io import read_database
from ddict.project import build_project, load_project
from ddict.questionnaire import language, link, load_questionnaire
from ddict.workflow import add_questionnaire, profile_database

ROOT = Path(__file__).resolve().parent.parent
FILES = ["sleep-study.sav", "sleep-study.csv", "questionnaire-sleep.txt", "questionnaire-sleep.pdf"]
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_two_runs_write_identical_files(english_generator, english_files, tmp_path):
    again = {p.name: p for p in english_generator.write_all(tmp_path)}
    assert sorted(again) == sorted(FILES)
    for name in FILES:
        assert _sha(again[name]) == _sha(english_files[name]), name


def test_committed_examples_match_the_generator(english_files):
    for name in FILES:
        committed = ROOT / "exemples" / "bases-fictives" / name
        assert _sha(committed) == _sha(english_files[name]), (
            f"{name} differs: run uv run python scripts/generer_base_anglaise.py"
        )


def test_same_participants_as_the_french_study(english_generator, generator):
    english, _meta = english_generator.build_dataset()
    french, _meta = generator.build_dataset()
    renamed = french.rename(columns=english_generator.NAMES)
    numbers = [c for c in english.columns if c not in ("home_language", "comment")]
    assert english[numbers].equals(renamed[numbers])


@pytest.mark.parametrize("suffix", ["txt", "pdf"])
def test_same_questions_as_the_french_questionnaire(english_files, fictional_files, suffix):
    english = load_questionnaire(english_files[f"questionnaire-sleep.{suffix}"]).questions
    french = load_questionnaire(fictional_files["questionnaire-sommeil.txt"]).questions
    assert [q.kind for q in english] == [q.kind for q in french]
    assert [len(q.rows) for q in english] == [len(q.rows) for q in french]
    assert [len(q.options) for q in english] == [len(q.options) for q in french]
    assert not any("ZQX" in q.text for q in english)  # the consent page is no question


def test_english_acronyms(english_generator, english_files):
    questionnaire = load_questionnaire(english_files["questionnaire-sleep.pdf"])
    found = {
        term: meaning.lower() for term, meaning, _page in glossary.find_definitions(questionnaire)
    }
    expected = english_generator.TRAPS["defined_acronyms"]
    assert found == {term: meaning.lower() for term, meaning in expected.items()}


def test_the_project_and_its_language(english_generator, english_files):
    project = build_project(read_database(english_files["sleep-study.csv"]))
    classes = {e.name: e.privacy.privacy_class.value for e in project.variables}
    assert classes["participant_id"] == classes["email"] == "likely_identifier"
    assert classes["comment"] == "free_text"
    assert project.settings.language == "fr"  # a CSV without labels: nothing to go by
    add_questionnaire(project, english_files["questionnaire-sleep.pdf"])
    assert project.settings.language == "en"  # the questionnaire's
    variants = project.variable("home_language")
    from ddict.export import wording as w

    assert any("FRENCH" in text for text in w.entry_anomalies(variants))
    # Most links are found by the computation alone; the model will do the rest (step 5).
    computed = link.best_guess(project)
    questions = project.questionnaire.questions
    right = 0
    for name, (_page, rank, row) in english_generator.answer_key().items():
        question = questions[rank - 1]
        target = question.question_id
        if row is not None:
            target += f".{'r' if question.kind == 'grid' else 'o'}{row}"
        right += computed[name] == target
    assert right >= 27


def test_the_language_is_guessed_from_the_words(english_files, fictional_files, tmp_path):
    assert (
        language.guess(["How old are you?", "What is your gender?", "Do you agree to this?"])
        == "en"
    )
    assert (
        language.guess(["Quel âge avez-vous ?", "Quel est votre genre ?", "Êtes-vous d'accord ?"])
        == "fr"
    )
    assert language.guess(["Age", "Score"]) is None  # too few words: no guess
    shutil.copy(english_files["sleep-study.sav"], tmp_path / "sleep-study.sav")
    project, _path = profile_database(tmp_path / "sleep-study.sav")
    assert project.settings.language == "en"  # from the file's labels
    french, _path = profile_database(fictional_files["etude-sommeil.sav"], tmp_path / "f.dd.json")
    assert french.settings.language == "fr"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_language_can_be_changed_on_the_base_page(english_files, tmp_path):
    shutil.copy(english_files["sleep-study.sav"], tmp_path / "sleep-study.sav")
    _project, path = profile_database(tmp_path / "sleep-study.sav")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.run()
    assert app.selectbox(key="study-language").value == "en"
    app.selectbox(key="study-language").set_value("fr").run()
    assert not app.exception, app.exception
    assert load_project(path).settings.language == "fr"


def test_the_model_reads_english_for_an_english_study(english_files, fictional_files):
    import json

    from ddict.llm.link import build_link_blocks
    from ddict.llm.messages import build_blocks

    project = build_project(read_database(english_files["sleep-study.csv"]))
    add_questionnaire(project, english_files["questionnaire-sleep.pdf"])
    blocks = build_blocks(project)
    assert blocks[0].messages[0]["content"].startswith("You help a research team")
    assert blocks[0].prompt_version == "variables-v3.en"
    sent = [v for b in blocks for v in json.loads(b.messages[1]["content"])["variables"]]
    notes = {v["name"]: v.get("note") for v in sent}
    assert notes["email"] == "likely identifier: no value sent"
    assert "masqué" not in json.dumps(sent, ensure_ascii=False)
    groups = [v["group"]["description"] for v in sent if "group" in v]
    assert '8 items, codes from 1 to 5, prefix "sleep_q"' in groups
    links = build_link_blocks(project, size=6)
    assert links[0].messages[0]["content"].startswith("You help a research team link")
    assert links[0].prompt_version == "link-v2.en"
    # A French study is sent exactly as before v0.5.
    french = build_project(read_database(fictional_files["etude-sommeil.csv"]))
    assert build_blocks(french)[0].prompt_version == "variables-v3"
    assert build_blocks(french)[0].messages[0]["content"].startswith("Tu aides une équipe")


def test_english_answers_none_and_unsure(english_files):
    import json

    from ddict.llm.link import build_link_blocks, parse_link_response

    project = build_project(read_database(english_files["sleep-study.csv"]))
    add_questionnaire(project, english_files["questionnaire-sleep.pdf"])
    block = build_link_blocks(project, size=40)[0]
    names = block.names
    answer = {
        "block": block.block_id,
        "variables": [
            {"name": n, "question": "none" if i == 0 else "unsure"} for i, n in enumerate(names)
        ],
    }
    choices = parse_link_response(json.dumps(answer), block)
    assert [c.question for c in choices][:2] == ["none", "unsure"]
