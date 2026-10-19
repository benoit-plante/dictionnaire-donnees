"""v0.20, step A1: a LimeSurvey structure file read as the questionnaire (D-148) — the `.lss`
of LimeSurvey 4 and later and the tab-separated `.txt`, as LimeSurvey Cloud 7.6 exported a
fictional survey (`docs/essais/2026-10-19-limesurvey-fictif.md`). The files of the tests come
from `scripts/generer_limesurvey_fictif.py`; the author's own exports, kept off the
repository, are compared to them by the tests marked `limesurvey`."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from conftest import ROOT
from ddict.io.model import ReadError
from ddict.questionnaire import load_questionnaire, read_limesurvey
from ddict.questionnaire.lss import is_limesurvey_text

SCRIPT = ROOT / "scripts" / "generer_limesurvey_fictif.py"
EXAMPLES = ROOT / "exemples" / "bases-fictives"
# The author's exports of the same survey, outside the repository (they carry the
# administrator's address): only compared, never copied (D-046).
REAL = os.environ.get("DDICT_LIMESURVEY")


def _generator():
    spec = importlib.util.spec_from_file_location("generer_limesurvey_fictif", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _generator()


@pytest.fixture(scope="module")
def files(generator, tmp_path_factory):
    folder = tmp_path_factory.mktemp("LimeSurvey fictif é")
    lss, txt = generator.write_all(folder)
    return {"lss": lss, "txt": txt}


def _content(questionnaire):
    data = questionnaire.model_dump()
    del data["file_name"], data["sha256"]
    return data


def test_two_runs_write_the_same_bytes_and_the_committed_examples(generator, files, tmp_path):
    again = generator.write_all(tmp_path)
    for path in again:
        assert path.read_bytes() == files[path.suffix[1:]].read_bytes()
        assert path.read_bytes() == (EXAMPLES / path.name).read_bytes(), path.name


def test_the_two_forms_give_the_same_questionnaire(files):
    lss = read_limesurvey(files["lss"], "fr")
    txt = read_limesurvey(files["txt"], "fr")
    assert lss.format == txt.format == "lss"
    assert _content(lss) == _content(txt)
    assert load_questionnaire(files["txt"], language="fr") == txt  # recognized by its content


def test_each_kind_with_its_exact_codes(files):
    found = read_limesurvey(files["lss"], "fr")
    assert [(s.section_id, s.title) for s in found.sections] == [
        ("S1", "Vous"),
        ("S2", "Votre sommeil"),
    ]
    questions = {q.code: q for q in found.questions}
    assert [q.code for q in found.questions] == [
        "genre", "age", "region", "journal", "profession", "intro", "sommeil", "aides", "nuit",
    ]  # fmt: skip
    assert [q.question_id for q in found.questions][:2] == ["Q1", "Q2"]
    genre = questions["genre"]
    assert (genre.kind, genre.layout, genre.required, genre.section) == (
        "single",
        "radio",
        True,
        "S1",
    )
    assert [(o.code, o.text, o.other) for o in genre.options] == [
        ("1", "Femme", False), ("2", "Homme", False), ("9", "Préfère ne pas répondre", False),
        ("-oth-", "Autre", True),
    ]  # fmt: skip
    assert questions["region"].layout == "dropdown"
    assert [questions[c].answer for c in ("age", "journal", "profession", "nuit")] == [
        "number", "date", "short", "long",
    ]  # fmt: skip
    assert questions["intro"].kind == "display" and not questions["intro"].required
    sleep = questions["sommeil"]
    assert sleep.kind == "grid" and sleep.instruction == "Cochez une case par ligne."
    assert [(r.row_id, r.code) for r in sleep.rows] == [
        ("Q7.r1", "SQ001"), ("Q7.r2", "SQ002"), ("Q7.r3", "SQ003"),
    ]  # fmt: skip
    assert [o.code for o in sleep.options] == ["1", "2", "3", "4"]
    aids = questions["aides"]
    assert aids.kind == "checkbox"
    assert [(o.code, o.other) for o in aids.options] == [
        ("SQ001", False),
        ("SQ002", False),
        (None, True),
    ]
    assert all(q.to_check == [] for q in found.questions)


def test_the_order_is_sorted_not_counted(files):
    """LimeSurvey numbers the questions of a group with gaps (its subquestions count)."""
    text = files["lss"].read_text(encoding="utf-8")
    assert "<question_order><![CDATA[5]]></question_order>" in text  # "aides", after gaps
    found = read_limesurvey(files["lss"], "fr")
    assert [q.code for q in found.questions if q.section == "S2"] == [
        "intro",
        "sommeil",
        "aides",
        "nuit",
    ]


def test_html_expressions_and_unknown_types(files, tmp_path):
    text = files["lss"].read_text(encoding="utf-8")
    text = (
        text.replace(
            "<![CDATA[Quel est votre genre ?]]>",
            "<![CDATA[<p>Quel est <strong>votre</strong>&nbsp;genre&#8239;?</p>]]>",
        )
        .replace(
            "<![CDATA[Décrivez une nuit difficile.]]>",
            "<![CDATA[Décrivez une nuit difficile, {TOKEN:FIRSTNAME}.]]>",
        )
        .replace("<type><![CDATA[S]]></type>", "<type><![CDATA[R]]></type>")
    )
    path = tmp_path / "variante.lss"
    path.write_text(text, encoding="utf-8")
    questions = {q.code: q for q in read_limesurvey(path, "fr").questions}
    assert questions["genre"].text == "Quel est votre genre ?"
    assert questions["nuit"].to_check == ["lss_expression"]
    ranked = questions["profession"]
    assert ranked.kind == "open" and ranked.to_check == ["lss_type_unsupported"]


def test_an_external_entity_is_never_read(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TEMOIN-ENTITE-EXTERNE", encoding="utf-8")
    uri = secret.resolve().as_uri()
    path = tmp_path / "piege.lss"
    path.write_text(
        f'<?xml version="1.0"?>\n<!DOCTYPE document [<!ENTITY x SYSTEM "{uri}">]>\n'
        "<document><LimeSurveyDocType>Survey</LimeSurveyDocType><languages><language>fr"
        "</language></languages><questions><rows><row><qid>1</qid><parent_qid>0</parent_qid>"
        "<gid>1</gid><type>S</type><title>q</title><question_order>0</question_order></row>"
        "</rows></questions><question_l10ns><rows><row><qid>1</qid><question>&x;</question>"
        "<language>fr</language></row></rows></question_l10ns></document>",
        encoding="utf-8",
    )
    found = read_limesurvey(path)
    assert "TEMOIN" not in found.model_dump_json()


def test_what_is_not_read(files, tmp_path):
    old = tmp_path / "ancien.lss"
    old.write_text(
        '<?xml version="1.0"?><document><LimeSurveyDocType>Survey</LimeSurveyDocType>'
        "<DBVersion>366</DBVersion><questions><rows/></questions></document>",
        encoding="utf-8",
    )
    with pytest.raises(ReadError, match="LimeSurvey 4 and later"):
        read_limesurvey(old)
    other = tmp_path / "autre.lss"
    other.write_text("<?xml version='1.0'?><html/>", encoding="utf-8")
    with pytest.raises(ReadError, match="not a LimeSurvey survey structure"):
        read_limesurvey(other)
    plain = tmp_path / "questionnaire.txt"
    plain.write_text("1. Quel âge avez-vous ?\n", encoding="utf-8")
    assert not is_limesurvey_text(plain)
    assert load_questionnaire(plain).format == "txt"  # a text questionnaire, as before
    # The survey's settings never enter the questionnaire.
    dumped = read_limesurvey(files["lss"]).model_dump_json()
    assert "example.org" not in dumped and "Équipe fictive" not in dumped


# --- The author's real exports (marked `limesurvey`) ------------------------------------------


@pytest.mark.limesurvey
@pytest.mark.skipif(not (REAL and Path(REAL).is_dir()), reason="DDICT_LIMESURVEY non défini")
def test_the_fictional_files_read_as_limesurvey_exported_them(files):
    real = Path(REAL)
    for name in ("fictif-454667.lss", "fictif-454667.txt"):
        assert _content(read_limesurvey(real / name, "fr")) == _content(
            read_limesurvey(files["lss"], "fr")
        ), name
    header = (real / "fictif-454667.txt").read_text(encoding="utf-8-sig").splitlines()[0]
    assert header.split("\t") == _generator().TSV_COLUMNS
