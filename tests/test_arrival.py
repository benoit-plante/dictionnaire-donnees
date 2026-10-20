"""v0.20, step E4: the database of a designed questionnaire arrives. A fictional database
simulated from the fictional questionnaire, with one variable too many, one absent, a code
outside the planned codes and a value label changed: the four are found; the decisions of
the planned variables are taken again; the project documents its database. Nothing real."""

import math
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from ddict import arrival, design
from ddict.cli import EXIT_ERROR, main
from ddict.project import load_project, save_project
from ddict.project.model import TrackedValue
from ddict.review import navigation
from projet_concu import project as designed

NAN = math.nan
FREQUENCY = {1.0: "Jamais", 2.0: "Parfois", 3.0: "Souvent", 4.0: "Tout le temps"}  # changed
ROWS = 8


def _base(path: Path) -> Path:
    """The responses as LimeSurvey's .sav would give them, changed on purpose."""
    data = pd.DataFrame(
        {
            "id": [float(n) for n in range(1, ROWS + 1)],
            "submitdate": ["2026-10-20 10:00:00"] * ROWS,
            "lastpage": [2.0] * ROWS,
            "startlanguage": ["fr"] * ROWS,
            "seed": [float(1000 + n) for n in range(ROWS)],
            "Q1": [1.0, 2.0, 1.0, 9.0, 2.0, 1.0, 7.0, 3.0],  # 7: not a planned code
            "Q2": [34.0, 51.0, 27.0, NAN, 42.0, 30.0, 61.0, 45.0],
            "Q3": [""] * ROWS,
            "Q4_SQ001": [1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0],
            "Q4_SQ002": [4.0, 3.0, 2.0, 1.0, 4.0, 3.0, 2.0, 1.0],
            # Q4_SQ003 absent: the item was removed in LimeSurvey
            "Q5_1": ["Y", "", "Y", "", "Y", "", "Y", ""],
            "Q5_2": ["", "Y", "", "Y", "", "Y", "", "Y"],
            "Q5_other": [""] * ROWS,
            "commentaire": [""] * ROWS,  # not planned
        }
    )
    labels = {
        "Q1": {1.0: "Femme", 2.0: "Homme", 3.0: "Autre", 9.0: "Préfère ne pas répondre"},
        "Q4_SQ001": FREQUENCY,
        "Q4_SQ002": FREQUENCY,
    }
    pyreadstat.write_sav(data, str(path), variable_value_labels=labels)
    return path


@pytest.fixture
def ready(tmp_path):
    project = designed()
    entry = project.variable("Q2")
    entry.new_name = TrackedValue[str](value="age", origin="human", updated_at="2026-10-19")
    entry.description = TrackedValue[str](value="Âge déclaré, en années.", origin="human")
    path = tmp_path / "Étude conçue.dd.json"
    save_project(project, path)
    return path, _base(tmp_path / "reponses.sav")


def test_the_four_differences_are_found(ready):
    path, base = ready
    project = load_project(path)
    found = arrival.receive(project, base)
    assert found.absent == ["Q4_SQ003"]
    assert found.extra == ["commentaire"]  # LimeSurvey's own variables aside
    assert found.codes == {"Q1": ["7"]}
    assert found.labels == {
        "Q4_SQ001": [("4", "Toujours", "Tout le temps")],
        "Q4_SQ002": [("4", "Toujours", "Tout le temps")],
    }
    assert found.types == {}
    assert found == arrival.conformity(project)  # computed again at any time


def test_the_decisions_are_taken_again(ready):
    path, base = ready
    project = load_project(path)
    arrival.receive(project, base)
    entry = project.variable("Q2")
    assert entry.profile is not None and entry.planned is not None
    assert entry.new_name.value == "age" and entry.description.value.startswith("Âge")
    assert entry.question.value == "Q2"
    assert project.variable("Q4_SQ002").question.value == "Q4.r2"
    grid = next(g for g in project.groups if g.question == "Q4")
    assert grid.members.value == ["Q4_SQ001", "Q4_SQ002"]  # the absent item left
    assert project.variable("commentaire").planned is None
    assert project.source.name == "reponses.sav" and project.source.platform == "limesurvey"
    # The project now documents its database.
    assert navigation.first(project) == "base"
    assert not navigation.waits_for_base(project, "analyses")


def test_the_questionnaire_is_unchanged_and_kept(ready):
    path, base = ready
    project = load_project(path)
    before = design.questionnaire(project).model_copy(deep=True)
    arrival.receive(project, base)
    assert design.questionnaire(project) == before
    with pytest.raises(arrival.AlreadyThere):
        arrival.receive(project, base)
    # A change of the questionnaire afterwards leaves the variables of the base alone.
    names = [e.name for e in project.variables]
    design.add_question(project, design.Draft(kind="open", text="Un mot ?", section="S2"))
    assert [e.name for e in project.variables] == names
    assert "Q6" in arrival.conformity(project).absent


def test_the_report(ready):
    path, base = ready
    project = load_project(path)
    text = arrival.report_markdown(project, arrival.receive(project, base))
    assert "## Variables prévues absentes de la base\n\n- `Q4_SQ003`" in text
    assert "- `Q1` : `7`" in text
    assert "- `Q4_SQ001`, `4` : « Toujours » → « Tout le temps »" in text
    assert "- `commentaire`" in text
    assert arrival.report_path(path).name == "Étude conçue-conformite.md"


def test_the_command_line(ready, capsys):
    path, base = ready
    assert main(["profiler", str(base), "--projet", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Conformité" in out or "conformité" in out
    project = load_project(path)
    assert project.source is not None and project.variable("Q2").new_name.value == "age"
    report = arrival.report_path(path)
    assert "Q4_SQ003" in report.read_text(encoding="utf-8")
    assert main(["profiler", str(base), "--projet", str(path)]) == EXIT_ERROR
    assert "a déjà sa base" in capsys.readouterr().err


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_base_page(ready):
    from streamlit.testing.v1 import AppTest

    path, base = ready
    app_path = Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "base"
    app.run()
    app.button(key="base-arrival").click().run()
    assert "Choisissez d'abord la base" in app.error[0].value
    app.text_input(key="base-arrival-path").set_value(str(base))
    app.button(key="base-arrival").click().run()
    assert not app.exception, app.exception
    assert load_project(path).source is not None
    assert any("variables prévues absentes : 1 ;" in s.value for s in app.success)
    assert arrival.report_path(path).is_file()
    texts = " ".join(m.value for m in app.markdown)
    assert "Variables prévues absentes de la base" in texts and "`Q4_SQ003`" in texts


def test_what_limesurvey_s_sav_writes_of_an_other_answer(tmp_path):
    """The real export of 2026-10-19: a single choice with "other" is a text column of codes
    "1" and "-oth-", which pandas calls "mixed", and "-oth-" is labelled "Other", in English.
    Neither is a difference from the questionnaire."""
    project = designed()
    design.add_question(
        project,
        design.Draft(kind="single", text="Où dormez-vous ?", section="S2",
                     options=(design.Item("Chez moi", "1"),
                              design.Item("Ailleurs, précisez", other=True))),
    )  # fmt: skip
    path = tmp_path / "Étude conçue.dd.json"
    save_project(project, path)
    data = pd.DataFrame({"Q6": ["1", "-oth-", "1", "1", "-oth-", "1"],
                         "Q6_other": ["", "Chez un ami", "", "", "Au chalet", ""]})  # fmt: skip
    base = tmp_path / "reponses.sav"
    pyreadstat.write_sav(data, str(base), variable_value_labels={
        "Q6": {"1": "Chez moi", "-oth-": "Other"}})  # fmt: skip
    found = arrival.receive(load_project(path), base)
    assert "Q6" not in found.labels and "Q6" not in found.types


# --- A question whose code or text changed in LimeSurvey (the author's trial, 2026-10-20) ----

QUESTION = "Au cours du dernier mois, à quelle fréquence..."  # LimeSurvey's three dots
CHECKBOX = "Qu'est-ce qui vous aide à dormir ? Cochez tout ce qui s'applique."


def _reworded(path: Path, checkbox: str = CHECKBOX) -> Path:
    """The .sav of LimeSurvey, its labels as it writes them: the gender reworded, and the
    checkbox question of code `Q6` there, `Q5` in the questionnaire."""
    from projet_concu import ROWS as ITEMS

    labels = {
        "Q1": "Quel est ton genre ?",
        "Q2": "Quel âge avez-vous ?",
        **{f"Q4_SQ00{n}": f"[{t}] {QUESTION}" for n, t in enumerate(ITEMS, start=1)},
        "Q6_1": f"[La lecture] {checkbox}",
        "Q6_2": f"[La musique] {checkbox}",
        "Q6_other": f"[Autre] {checkbox}",
    }
    data = pd.DataFrame({name: [1.0, 2.0, 1.0, 2.0, 1.0, 2.0] for name in labels})
    data["Q6_other"] = ["", "Le silence", "", "", "", ""]
    pyreadstat.write_sav(data, str(path), column_labels=labels)
    return path


def test_a_question_renamed_in_limesurvey_is_found_by_its_texts(tmp_path):
    project = designed()
    project.variable("Q5_1").description = TrackedValue[str](value="Lit avant de dormir.",
                                                             origin="human")  # fmt: skip
    found = arrival.receive(project, _reworded(tmp_path / "reponses.sav"))
    assert found.renamed == {"Q5_1": "Q6_1", "Q5_2": "Q6_2", "Q5_other": "Q6_other"}
    assert not [n for n in found.absent if n.startswith("Q5")]
    assert not [n for n in found.extra if n.startswith("Q6")]
    entry = project.variable("Q6_1")
    assert entry.question.value == "Q5.o1" and entry.description.value == "Lit avant de dormir."
    group = next(g for g in project.groups if g.question == "Q5")
    assert group.members.value == ["Q6_1", "Q6_2"]
    # The one text changed, said once; the three dots of LimeSurvey are no change.
    assert found.texts == [("Q1", "Quel est votre genre ?", "Quel est ton genre ?")]
    assert found == arrival.conformity(project)
    text = arrival.report_markdown(project, found)
    assert "- `Q5_1` → `Q6_1`" in text
    assert "- `Q1` : « Quel est votre genre ? » → « Quel est ton genre ? »" in text


def test_a_question_renamed_and_reworded_is_not_guessed(tmp_path):
    project = designed()
    base = _reworded(
        tmp_path / "reponses.sav", checkbox="Qu'est-ce qui vous aide à vous endormir ?"
    )
    found = arrival.receive(project, base)
    assert found.renamed == {}
    assert {"Q5_1", "Q5_2", "Q5_other"} <= set(found.absent)
    assert {"Q6_1", "Q6_2", "Q6_other"} <= set(found.extra)
    assert project.variable("Q6_1").question.value is None
