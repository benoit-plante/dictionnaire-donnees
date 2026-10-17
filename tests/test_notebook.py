"""v0.11, step 2: the analysis notebook, its entries and its file (D-087, D-088, D-091), as
the validated sheet docs/carnet-analyses.md describes them."""

import json

import pytest

from ddict.analysis import notebook as nb
from ddict.analysis.apa import Edit
from ddict.analysis.compute import run
from ddict.analysis.data import apply_decisions
from ddict.io import read_database
from ddict.project import build_project
from ddict.project.model import TrackedValue
from ddict.review import study
from test_analysis_data import KEY, _prepared, analyses_project

TODAY = "2026-10-16"
CASES = [
    ("table1", {"variables": ["age", "sexe", "niveau_etudes", "bienetre_total"],
                "group": ["groupe"]}, None),
    ("t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]}, None),
    ("anova", {"outcome": ["stress"], "group": ["niveau_etudes"]}, {"post_hoc": "tukey"}),
    ("correlation", {"variables": ["heures_travail", "stress", "soutien"]}, None),
    ("chi_square", {"rows": ["teletravail"], "columns": ["secteur"]}, None),
]  # fmt: skip


@pytest.fixture
def ready(tmp_path):
    project = analyses_project()
    return project, _prepared(project, KEY["sav"]), tmp_path / "etude-analyses.dd.json"


def _filled(ready):
    """The sheet's example: five analyses added, A5 removed, A2 retained first."""
    project, prepared, path = ready
    notebook = nb.new_notebook(project, path)
    for key, chosen, options in CASES:
        nb.add(notebook, project, run(project, prepared, key, chosen, options), today=TODAY)
    nb.remove(notebook, "A5")
    nb.move(notebook, "A2", 1)
    nb.move(notebook, "A3", 2)
    nb.retain(notebook, "A4", False)
    return notebook


# --- The entries. ---


def test_the_sheets_example(ready):
    notebook = _filled(ready)
    assert [e.id for e in notebook.entries] == ["A2", "A3", "A1", "A4"]
    assert [e.retained for e in notebook.entries] == [True, True, True, False]
    assert notebook.next_id == 6
    project, prepared, _path = ready
    result = run(project, prepared, "t_test", CASES[1][1])
    added = nb.add(notebook, project, result, today=TODAY)
    assert added.id == "A6"  # never A5 again


def test_an_entry_keeps_what_the_sheet_says(ready):
    project, prepared, path = ready
    notebook = nb.new_notebook(project, path)
    result = run(project, prepared, "t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]})
    edits = {"table-1": Edit(number=4, title="Bien-être selon le groupe"), "figure-1": Edit()}
    entry = nb.add(notebook, project, result, edits=edits, today=TODAY)
    data = json.loads(entry.model_dump_json())
    assert data["variables"] == {"outcome": [{"score": "G1"}], "group": [{"variable": "groupe"}]}
    assert data["options"] == {"alternative": "two_sided", "method": "welch"}
    assert data["edits"] == {"table-1": {"title": "Bien-être selon le groupe", "note": None}}
    computed = data["computed"]
    assert computed["statistics"]["t"] == pytest.approx(KEY["exact"]["t_groupe"]["t"])
    assert list(computed["statistics"]) == sorted(computed["statistics"])
    assert computed["n_used"] == 300 and computed["sentence"] == result.sentence
    assert set(computed["versions"]) == {"dictionnaire-donnees", "Python", "SciPy", "statsmodels"}
    assert len(computed["fingerprint"]) == 64 and data["pending"] is None


def test_table1_and_correlation_keep_their_aggregates_by_position(ready):
    project, prepared, _path = ready
    s = run(project, prepared, "table1", CASES[0][1]).statistics
    assert s["v1_n_1"] == 148 and s["v1_m_total"] == pytest.approx(43.5627, abs=1e-4)
    assert s["v2_k1_1"] == 81 and s["v2_k2_total"] == 152  # women of group 1, men in all
    assert not any("min" in k or "max" in k for k in s)  # never the observed range
    correlation = run(project, prepared, "correlation", CASES[3][1]).statistics
    assert correlation["r_2_1"] == pytest.approx(KEY["exact"]["r_heures_stress"]["r"])
    assert {"r_3_1", "r_3_2", "low_3_2", "high_3_2", "n_3_2", "p_3_2"} <= set(correlation)


# --- Variables by their key in the project. ---


def test_references_survive_a_renaming(ready):
    project, prepared, path = ready
    notebook = nb.new_notebook(project, path)
    result = run(project, prepared, "anova", CASES[2][1], CASES[2][2])
    entry = nb.add(notebook, project, result, today=TODAY)
    project.variable("stress").new_name = TrackedValue[str](
        value="stress_total", origin="human", status="none"
    )
    assert nb.resolved(project, entry) == {"outcome": ["stress_total"], "group": ["niveau_etudes"]}


def test_a_reversed_item_and_lost_references(ready):
    project = ready[0]
    ref = nb.reference(project, "bienetre_4_inv")
    assert ref == nb.VariableRef(reversed="bienetre_4")
    assert nb.resolve(project, ref) == "bienetre_4_inv"
    group = next(g for g in project.groups if "bienetre_1" in (g.members.value or []))
    study.remove_scoring(project, group.group_id)
    with pytest.raises(nb.NotebookError) as error:
        nb.resolve(project, nb.VariableRef(score=group.group_id))
    assert error.value.reason == "score_removed"
    assert "plus de cotation" in nb.reason_text(error.value)
    with pytest.raises(nb.NotebookError) as error:
        nb.resolve(project, nb.VariableRef(variable="inconnue"))
    assert error.value.reason == "variable_removed"
    with pytest.raises(ValueError):
        nb.VariableRef(variable="age", score="G1")  # exactly one key


# --- The file. ---


def test_round_trip_byte_for_byte(ready):
    notebook = _filled(ready)
    _project, _prepared_data, project_path = ready
    path = nb.notebook_path(project_path)
    assert path.name == "etude-analyses-carnet.json"
    nb.save_notebook(notebook, path)
    first = path.read_bytes()
    assert b"\r\n" not in first and first.endswith(b"\n")
    again = nb.load_notebook(path)
    assert again == notebook
    nb.save_notebook(again, path)
    assert path.read_bytes() == first
    data = json.loads(first)
    assert list(data) == ["carnet_version", "project", "next_id", "first_table", "first_figure",
                          "entries", "method"]  # fmt: skip
    assert data["carnet_version"] == "1.2.0" and data["project"]["file"] == project_path.name


def test_a_notebook_of_v0_11_reads_as_it_is(ready):
    """1.0.0 had no Method (D-100): it reads, and is written again in 1.1.0."""
    notebook = _filled(ready)
    path = ready[2].with_name("carnet.json")
    data = json.loads(nb.dumps(notebook))
    data["carnet_version"] = "1.0.0"
    del data["method"]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    old = nb.load_notebook(path)
    assert old.carnet_version == nb.NOTEBOOK_VERSION and old.method == nb.MethodPart()
    assert old.entries == notebook.entries


@pytest.mark.parametrize("version", ["2.0.0", "1.9.0", "1.3.0", "0.9.0", "un"])
def test_a_notebook_of_another_version_is_refused(ready, version):
    notebook = _filled(ready)
    path = ready[2].with_name("carnet.json")
    data = json.loads(nb.dumps(notebook))
    data["carnet_version"] = version
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(nb.NotebookError) as error:
        nb.load_notebook(path)
    assert error.value.reason == "version"


def test_a_notebook_belongs_to_its_project(ready, fictional_files):
    notebook = _filled(ready)
    assert nb.belongs(notebook, ready[0])
    other = build_project(read_database(fictional_files["etude-sommeil.sav"]))
    assert not nb.belongs(notebook, other)


# --- No individual data (D-088): the canary test. ---


def test_no_individual_data_in_the_notebook(fictional_files, generator, tmp_path):
    """The sleep study carries canaries in its identifier, e-mail and comment; an analysis
    of each kind goes into the notebook, and none of them, nor any row, comes out."""
    database = read_database(fictional_files["etude-sommeil.sav"])
    project = build_project(database)
    prepared = apply_decisions(project, database.table)
    notebook = nb.new_notebook(project, tmp_path / "etude-sommeil.dd.json")
    cases = [
        ("table1", {"variables": ["age", "genre", "heures_sommeil"]}, None),
        ("t_test", {"outcome": ["heures_sommeil"], "group": ["genre"]}, {"levels": "1,2"}),
        ("anova", {"outcome": ["heures_sommeil"], "group": ["genre"]}, None),
        ("correlation", {"variables": ["age", "heures_sommeil"]}, None),
        ("regression", {"outcome": ["heures_sommeil"], "predictors": ["age"]}, None),
    ]
    for key, chosen, options in cases:
        nb.add(notebook, project, run(project, prepared, key, chosen, options), today=TODAY)
    text = nb.dumps(notebook)
    for canary in generator.CANARIES:
        assert canary not in text
    assert "points" not in text and "Étendue" not in text
    # The scatter plot of the correlation never enters: its entry holds a handful of
    # aggregates, not 200 pairs of values.
    correlation = json.loads(text)["entries"][3]["computed"]["statistics"]
    assert len(correlation) <= 10
    ages = prepared.table["age"].dropna()
    table1 = json.loads(text)["entries"][0]["computed"]["statistics"]
    assert float(ages.max()) not in table1.values()  # the oldest person's age is not kept
