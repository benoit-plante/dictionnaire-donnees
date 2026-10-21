"""v0.21, step 9 (§ 5.8.5 of the plan, D-167): downstream of the arrival, what was not asked
is never a missing value. The preparation's mask; the completeness of a group among the items
asked; "missing" meaning asked and left empty; Table 1, its percentages among those who
answered a filtered question and its note; a project without conditions as before. Nothing
real: the base of `scripts/generer_base_filtres.py`, compared to its answer key."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from ddict import arrival
from ddict.analysis.apa import describe, plain
from ddict.analysis.compute import run
from ddict.analysis.data import apply_decisions
from ddict.io.load import read_database
from ddict.project import exclusions
from ddict.project.exclusions import ExclusionRefused
from ddict.project.model import TrackedValue

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-filtres.json").read_text(encoding="utf-8"))
BASE = EXAMPLES / "reponses-filtres.sav"


def _generator():
    script = ROOT / "scripts" / "generer_base_filtres.py"
    spec = importlib.util.spec_from_file_location("generer_base_filtres", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project():
    found = _generator().project()
    arrival.receive(found, BASE)
    return found


@pytest.fixture(scope="module")
def table():
    return read_database(BASE).table


def _group(project, variable):
    return next(g.group_id for g in project.groups if variable in (g.members.value or []))


def test_the_mask_of_what_was_not_asked(project, table):
    prepared = apply_decisions(project, table)
    na = prepared.not_applicable
    for name in ("nbenfants", "climat_SQ001", "nuit", "age"):  # not asked: with the anomalies
        counts = KEY["variables"][name]
        assert int(na[name].sum()) == counts["not_applicable"] + counts["anomalies"]
    assert len(na) == len(prepared.table) == KEY["n"]
    assert "consent" not in na.columns  # always asked


def test_the_completeness_counts_among_the_items_asked(project, table):
    group = _group(project, "climat_SQ001")
    exclusions.add(
        project,
        {"kind": "completeness", "group": group, "min_answered": 5, "reason": "Grille incomplète"},
    )
    prepared = apply_decisions(project, table)
    assert prepared.flow.excluded == (("E1", KEY["climat_fewer_than_5"]),)  # 6, not 6 + 83
    assert prepared.not_applicable is not None and len(prepared.not_applicable) == KEY["n"] - 6


def test_missing_means_asked_and_left_empty(project, table):
    exclusions.add(
        project,
        {"kind": "condition", "variable": "nbenfants", "operator": "missing",
         "reason": "Nombre d'enfants non donné"},
    )  # fmt: skip
    prepared = apply_decisions(project, table)
    assert prepared.flow.excluded == (("E1", KEY["nbenfants_missing"]),)  # 5, not 5 + 137


def test_a_completeness_on_items_asked_to_different_people_is_refused(project):
    group = next(g for g in project.groups if "climat_SQ001" in (g.members.value or []))
    group.members = group.members.model_copy(update={"value": [*group.members.value, "age"]})
    with pytest.raises(ExclusionRefused, match="pas posés aux mêmes personnes"):
        exclusions.add(
            project,
            {"kind": "completeness", "group": group.group_id, "min_answered": 5, "reason": "r"},
        )


def test_table1_counts_among_those_asked(project, table):
    for name, level in (("nuit", "nominal"), ("nbenfants", "scale")):  # as on the page Base
        project.variable(name).measure_level = TrackedValue[str](value=level, origin="human")
    prepared = apply_decisions(project, table)
    result = run(project, prepared, "table1", {"variables": ["nuit", "nbenfants"]})
    doc = describe(project, prepared, result, language="fr")
    cells = [[plain(c) for c in row.cells] for row in doc.tables[0].rows]
    counts = KEY["table1"]["nuit"]["counts"]
    asked = KEY["table1"]["nuit"]["asked"]
    yes = next(row for row in cells if row[0] == "Oui")
    assert yes[1] == f"{counts['1']} ({100 * counts['1'] / asked:.1f})".replace(".", ",")
    note = plain(doc.tables[0].note)
    assert f"question posée à {asked} personnes" in note
    nb = KEY["table1"]["nbenfants"]
    assert (
        f"question posée à {nb['asked']} personnes ; {nb['unanswered']} sans réponse ; "
        f"{KEY['variables']['nbenfants']['anomalies']} réponses sous une condition fausse, "
        "hors du tableau"
    ) in note
    assert "valeurs manquantes" not in note
    english = describe(project, prepared, result, language="en")
    assert f"asked of {asked} people" in plain(english.tables[0].note)


def test_a_project_without_conditions_prepares_as_before(table):
    from test_analysis_data import KEY as ANALYSES
    from test_analysis_data import _prepared, analyses_project

    prepared = _prepared(analyses_project(), ANALYSES["sav"])
    assert prepared.not_applicable is None


# --- The Method (§ 5.8.6) and the notes of the analyses. ---


def _method(project, table, language="fr"):
    from ddict import i18n
    from ddict.analysis import method, method_text
    from ddict.analysis import notebook as nb
    from ddict.project.model import Scoring

    for name, level in (("nuit", "nominal"), ("nbenfants", "scale"), ("age", "scale")):
        project.variable(name).measure_level = TrackedValue[str](value=level, origin="human")
    group = next(g for g in project.groups if "climat_SQ001" in (g.members.value or []))
    group.scoring = Scoring(
        items=list(group.members.value), aggregation="mean", scale_min=1, scale_max=5,
        score_name="climat_moyenne", source="Cotation fictive, inventée pour les tests",
    )  # fmt: skip
    prepared = apply_decisions(project, table)
    notebook = nb.new_notebook(project, Path("familles.dd.json"))
    notebook.method.variables = [nb.reference(project, n) for n in ("age", "nbenfants", "nuit")]
    result = run(project, prepared, "correlation", {"variables": ["age", "nbenfants"]})
    nb.add(notebook, project, result, today="2026-10-21")
    found = method.facts(project, prepared, notebook)
    with i18n.using(language):
        return (
            found,
            plain(method_text.participants(project, found, 1)),
            [plain(p) for p in method_text.instruments(project, prepared, found)],
            plain(method_text.analyses(found, "familles-article.R")),
            describe(project, prepared, result, language=language),
        )


def test_the_method_says_the_filtered_questions(project, table):
    found, participants, instruments, analyses, doc = _method(project, table)
    nb = KEY["table1"]["nbenfants"]
    assert "Le questionnaire comprenait deux items de contrôle de l'attention." in participants
    assert f"parmi les {nb['asked']} personnes à qui la question a été posée)" in participants
    asked = KEY["table1"]["nuit"]["asked"]
    assert f"travaillez-vous de nuit ? (question posée à {asked} personnes : " in participants
    assert "Certaines questions n'étaient posées qu'aux personnes" in analyses
    assert (
        "combien d'enfants vivent avec vous ? (posée si consent = Oui et enfants = Oui)" in analyses
    )
    assert any(
        "présentés dans un ordre aléatoire, tiré pour chaque personne" in text
        for text in instruments
    )
    note = plain(doc.tables[0].note)
    assert (
        "Combien d'enfants vivent avec vous ? : posée seulement si consent = Oui et "
        "enfants = Oui ; l'analyse porte sur les personnes à qui elle a été posée." in note
    )
    from ddict.analysis import method

    stats = method.statistics(found)
    assert stats["v2_asked"] == nb["asked"]  # a new aggregate, kept by the notebook


def test_the_method_in_english(project, table):
    _found, participants, _instruments, analyses, doc = _method(project, table, "en")
    assert "The questionnaire included two attention-check items." in participants
    assert "of the 160 people who were asked the question)" in participants
    assert "Some questions were asked only of respondents" in analyses
    assert "The filtered questions are:" in analyses
    assert (
        "Combien d'enfants vivent avec vous ?: asked only if consent = Oui and enfants = Oui; "
        "the analysis includes the people who were asked it."
    ) in plain(doc.tables[0].note)


def test_a_method_without_conditions_says_nothing_new():
    from ddict.analysis import method, method_text
    from test_method import _ready

    project, _table, prepared, notebook = _ready()
    found = method.facts(project, prepared, notebook)
    assert found.filtered == () and found.attention == 0
    assert "filtrées" not in plain(method_text.analyses(found, "x.R"))
    assert not any(k.endswith("_asked") for k in method.statistics(found))
