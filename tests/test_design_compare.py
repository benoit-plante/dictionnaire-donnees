"""v0.20, step E3: close the loop (D-150). A structure re-exported from LimeSurvey is compared
with the project by the codes of its questions; each sort of difference is found on fictional
re-exports changed on purpose; nothing changes without a decision. "Marquer comme envoyé"
keeps a copy, and what changed since each version sent is computed. Fictional projects only.
"""

import csv
import io

import pytest

from ddict import design, design_compare, design_limesurvey
from ddict.design import DesignError
from ddict.questionnaire.lss import read_limesurvey
from projet_concu import project as designed

NOW = "2026-10-20T10:00:00"


def _reexport(project, tmp_path, change=None):
    """The file written for LimeSurvey, changed as LimeSurvey would have it, read again."""
    text = design_limesurvey.text(project)
    reader = csv.reader(io.StringIO(text), delimiter="\t", quotechar='"')
    header, *rows = list(reader)
    rows = [dict(zip(header, r, strict=True)) for r in rows]
    if change is not None:
        rows = change(rows)
    out = io.StringIO()
    writer = csv.writer(out, delimiter="\t", quotechar='"', lineterminator="\n")
    writer.writerow(header)
    writer.writerows([[r.get(h, "") for h in header] for r in rows])
    path = tmp_path / "reexport.txt"
    path.write_text(out.getvalue(), encoding="utf-8", newline="\n")
    return read_limesurvey(path, "fr")


def _question(rows, name):
    return next(r for r in rows if r["class"] == "Q" and r["name"] == name)


def test_the_same_questionnaire_has_no_difference(tmp_path):
    project = designed()
    assert design_compare.with_limesurvey(project, _reexport(project, tmp_path)) == []


def test_each_sort_of_difference(tmp_path):
    project = designed()

    def change(rows):
        _question(rows, "Q1")["text"] = "Quel est ton genre ?"  # reworded
        _question(rows, "Q1")["mandatory"] = "N"
        _question(rows, "Q2")["name"] = "age"  # recoded, same text
        q4 = _question(rows, "Q4")
        q4["help"] = ""
        for r in rows:
            if r["class"] == "SQ" and r["name"] == "SQ003":
                r["name"] = "SQ009"  # an item recoded
            if r["class"] == "A" and r["id"] == q4["id"] and r["name"] == "4":
                r["text"] = "Tout le temps"  # a column reworded
        rows = [r for r in rows if not (r["class"] == "Q" and r["name"] == "Q3")]  # removed
        rows.append(dict(_question(rows, "Q5"), id="99", name="Q9", **{
            "type/scale": "S", "text": "Un mot de la fin ?", "other": "N",
            "question_theme_name": "shortfreetext"}))  # fmt: skip
        return rows

    found = design_compare.with_limesurvey(project, _reexport(project, tmp_path, change))
    kinds = {d.code: d.kind for d in found}
    assert kinds == {"Q1": "changed", "Q4": "changed", "Q2": "renamed", "Q3": "removed",
                     "Q9": "added"}  # fmt: skip
    q1 = next(d for d in found if d.code == "Q1")
    assert q1.fields == ["text", "required"]
    assert ("-", "votre") in q1.words() and ("+", "ton") in q1.words()
    q4 = next(d for d in found if d.code == "Q4")
    assert q4.fields == ["instruction"]
    assert {(i.kind, i.code, i.before) for i in q4.items} == {
        ("recoded", "SQ009", "SQ003"), ("reworded", "4", "Toujours"),
    }  # fmt: skip
    assert next(d for d in found if d.code == "Q2").theirs.code == "age"


def test_nothing_changes_without_a_decision(tmp_path):
    project = designed()
    before = project.model_dump()
    read = _reexport(project, tmp_path, lambda rows: rows[:-3])
    assert design_compare.with_limesurvey(project, read)
    assert project.model_dump() == before


def test_take_each_difference_into_the_project(tmp_path):
    project = designed()

    def change(rows):
        _question(rows, "Q1")["text"] = "Quel est ton genre ?"
        _question(rows, "Q2")["name"] = "age"
        for r in rows:
            if r["class"] == "SQ" and r["name"] == "SQ003":
                r["name"] = "SQ009"
        rows = [r for r in rows if not (r["class"] == "Q" and r["name"] == "Q3")]
        rows.append(dict(_question(rows, "Q5"), id="99", name="fin", **{
            "type/scale": "S", "text": "Un mot de la fin ?", "other": "N"}))  # fmt: skip
        return rows

    read = _reexport(project, tmp_path, change)
    rows_before = {r.code: r for r in design.find(project, "Q4").rows}
    for difference in design_compare.with_limesurvey(project, read):
        design_compare.take(project, difference, now=NOW)
    assert design_compare.with_limesurvey(project, read) == []
    assert design.find(project, "Q1").text == "Quel est ton genre ?"
    assert design.code(project, design.find(project, "Q2")) == "age"
    with pytest.raises(DesignError):
        design.find(project, "Q3")
    # The items of the same code keep their ids and their provenance; the recoded one too,
    # as a new item of LimeSurvey's code.
    rows = design.find(project, "Q4").rows
    assert rows[0].row_id == rows_before["SQ001"].row_id
    assert rows[0].provenance == rows_before["SQ001"].provenance
    assert rows[2].code == "SQ009"
    added = design.questionnaire(project).questions[-1]
    assert (added.text, added.kind, design.code(project, added)) == (
        "Un mot de la fin ?", "open", "fin",
    )  # fmt: skip
    assert added.section == "S2"


def test_the_other_text_stays_the_project_s(tmp_path):
    project = designed()

    def change(rows):
        _question(rows, "Q5")["mandatory"] = "Y"
        return rows

    [difference] = design_compare.with_limesurvey(project, _reexport(project, tmp_path, change))
    design_compare.take(project, difference, now=NOW)
    question = design.find(project, "Q5")
    assert question.required
    other = next(o for o in question.options if o.other)
    assert other.text == "Autre" and other.option_id == "Q5.o3"


# --- Marking as sent, and what changed since (D-150) -------------------------------------------


def test_mark_as_sent_then_change():
    project = designed()
    assert design_compare.warnings(project) == []
    design_compare.mark_sent(project, "limesurvey", "2026-10-20")
    design_compare.mark_sent(project, "ethics", "2026-10-21", note="  ")
    [first, second] = project.design.publications
    assert first.fingerprint == design.questionnaire(project).sha256 and second.note is None
    assert first.questionnaire == design.questionnaire(project)
    assert design_compare.warnings(project) == []
    assert design_compare.since(first, project) == []

    design.add_question(project, design.Draft(kind="open", text="Un commentaire ?", section="S2"))
    q1 = design.find(project, "Q1")
    options = tuple(design.Item(o.text, o.code, item_id=o.option_id) for o in q1.options)
    draft = design.Draft(kind="single", text="Quel est ton genre ?", section="S1",
                         required=True, options=options)  # fmt: skip
    design.modify_question(project, "Q1", draft)
    warnings = " ".join(design_compare.warnings(project))
    assert "publié dans LimeSurvey le 2026-10-20" in warnings
    assert "envoyé au comité d'éthique le 2026-10-21" in warnings
    changed = {d.code: d.kind for d in design_compare.since(first, project)}
    assert changed == {"Q1": "changed", "Q6": "added"}
    # Sent again, the warning of that place goes.
    design_compare.mark_sent(project, "limesurvey", "2026-10-22")
    assert len(design_compare.warnings(project)) == 1


# --- The page "Publier" ------------------------------------------------------------------------


def _page(path, **state):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "publish"
    for key, value in state.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_mark_as_sent_on_the_page(tmp_path):
    from ddict.project import load_project, save_project

    path = tmp_path / "Étude conçue.dd.json"
    save_project(designed(), path)
    app = _page(path)
    assert any("Aucune version envoyée." in c.value for c in app.caption)
    app.text_input(key="publish-sent-note").set_value("Dépôt initial")
    app.button(key="publish-mark").click().run()
    assert not app.exception, app.exception
    [publication] = load_project(path).design.publications
    assert publication.kind == "ethics" and publication.note == "Dépôt initial"
    assert not app.warning
    # A change after it: the page warns, and says what changed since.
    project = load_project(path)
    design.add_question(project, design.Draft(kind="open", text="Un mot ?", section="S2"))
    save_project(project, path, overwrite=True)
    app = _page(path)
    assert "envoyé au comité d'éthique le" in app.warning[0].value
    assert any("Un mot ?" in m.value for m in app.markdown)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_compare_a_reexport_on_the_page(tmp_path):
    from ddict.project import load_project, save_project

    path = tmp_path / "Étude conçue.dd.json"
    save_project(designed(), path)

    def change(rows):
        _question(rows, "Q1")["text"] = "Quel est ton genre ?"
        _question(rows, "Q2")["mandatory"] = "Y"
        return rows

    _reexport(designed(), tmp_path, change)
    reexport = str(tmp_path / "reexport.txt")
    app = _page(path, **{"publish-reexport": reexport})
    texts = " ".join(m.value for m in app.markdown)
    assert "~~votre~~ **ton**" in texts and "Changé : obligatoire." in texts
    app.button(key="publish-keep-changed-Q2").click().run()
    assert "LimeSurvey est à corriger pour : `Q2`" in app.warning[-1].value
    app.button(key="publish-review-changed-Q2").click().run()  # back on it, tool still open
    assert not [w for w in app.warning if "à corriger" in w.value]
    app.button(key="publish-keep-changed-Q2").click().run()
    app.button(key="publish-take-changed-Q1").click().run()
    assert not app.exception, app.exception
    assert design.find(load_project(path), "Q1").text == "Quel est ton genre ?"
    assert not design.find(load_project(path), "Q2").required  # kept as the project says
