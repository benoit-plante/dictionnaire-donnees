"""v0.15, step 2: the recodings (D-120; docs/verification-depot.md, § 1): a derived variable
kept as a decision of the team, computed in memory after the scores and before the
exclusion rules, refused when a value has no place, and usable in the analyses, the
exclusion rules, the subgroups, the notebook and the plan."""

import json

import pandas as pd
import pytest

from ddict.analysis import conditions, recode
from ddict.analysis import notebook as nb
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import CATALOGUE
from ddict.analysis.compute import run
from ddict.analysis.data import apply_decisions, decided
from ddict.analysis.results import Subset
from ddict.io import read_database
from ddict.project import build_project, fingerprint, load_project, recodes, save_project
from ddict.project import exclusions as rules
from ddict.project.model import VariableRef
from test_paired import EXAMPLES, KEY
from test_text_categories import _base

SEXE_2 = {
    "kind": "groups",
    "source": {"variable": "sexe"},
    "name": "sexe_2",
    "label": "Sexe, en deux groupes",
    "groups": [
        {"code": 1, "label": "Femme", "values": [1]},
        {"code": 2, "label": "Homme ou autre identité", "values": [2, 3]},
    ],
    "reason": "Trop peu de personnes d'une autre identité pour un groupe à part.",
}
AGE_CLASSE = {
    "kind": "classes",
    "source": {"variable": "age"},
    "name": "age_classe",
    "label": "Âge, en trois classes",
    "cuts": [30, 45],
    "labels": ["moins de 30", "30 à moins de 45", "45 et plus"],
    "reason": "Classes d'âge du rapport de l'organisme.",
}


@pytest.fixture
def base():
    data = read_database(EXAMPLES / KEY["sav"])
    return build_project(data), data.table


def _added(project, *fields):
    for data in fields:
        recodes.add(project, recodes.validated(project, data))
    return project


def _checked(project, table, data):
    rule = recodes.validated(project, data)
    before, _rev, _scores = decided(project, table)
    book = Codebook(project, apply_decisions(project, table))
    source = recodes.source_name(project, rule.source)
    return recode.check(project, rule, before, book.value_labels(source))


# --- The examples of the sheet. ---


def test_the_examples_of_the_sheet(base):
    project, table = base
    sexe = _checked(project, table, SEXE_2)
    assert sexe.ok and sexe.counts == [("Femme", 133), ("Homme ou autre identité", 107)]
    age = _checked(project, table, AGE_CLASSE)
    assert age.ok and age.counts == [
        ("moins de 30", 49),
        ("30 à moins de 45", 79),
        ("45 et plus", 112),
    ]
    assert sexe.warnings == age.warnings == []


def test_in_memory_after_the_scores(base):
    project, table = base
    _added(project, SEXE_2, AGE_CLASSE)
    data = apply_decisions(project, table).table
    assert list(data.columns[-2:]) == ["sexe_2", "age_classe"]
    assert data["sexe_2"].value_counts().to_dict() == {1.0: 133, 2.0: 107}
    # A cut belongs to the class it starts, as R's findInterval.
    ages = pd.Series([29.9, 30.0, 44.99, 45.0, None])
    rule = project.recodes.rules[1]
    assert recode.column(rule, ages).tolist()[:4] == [1.0, 2.0, 2.0, 3.0]
    assert pd.isna(recode.column(rule, ages).iloc[4])


def test_the_project_keeps_the_rule_never_the_column(base, tmp_path):
    project, _table = base
    before = fingerprint.fingerprint(project)
    _added(project, SEXE_2, AGE_CLASSE)
    assert fingerprint.fingerprint(project) != before  # a recoding is a decision
    path = tmp_path / "etude-suivi.dd.json"
    save_project(project, path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "0.7.0"
    assert saved["recodes"]["next_id"] == 3
    assert saved["recodes"]["rules"][0] == {"id": "R1", **SEXE_2, "level": "nominal",
                                            "missing_values": []}  # fmt: skip
    assert load_project(path) == project
    # A project without recodings keeps its fingerprint.
    assert fingerprint.fingerprint(build_project(read_database(EXAMPLES / KEY["sav"]))) == before


# --- Refusals. ---


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"reason": " "}, "Donnez la raison du recodage, en clair."),
        ({"groups": [{"code": 1, "label": "Tous", "values": [1, 2, 3]}]},
         "Il faut au moins deux groupes."),
        ({"groups": [{"code": 1, "label": "A", "values": [1]},
                     {"code": 1, "label": "B", "values": [2, 3]}]},
         "Deux groupes ont le même code."),
        ({"groups": [{"code": 1, "label": "A", "values": [1, 2]},
                     {"code": 2, "label": "B", "values": [2.0, 3]}]},
         "Une valeur est dans deux groupes."),
        ({"source": {"recode": "R1"}}, "Une variable recodée se recode depuis sa propre source."),
        ({"source": {"variable": "inconnue"}}, "inconnue : variable inconnue du projet."),
        ({"source": {"variable": "id_participant"}},
         "id_participant : identifiant, texte libre ou date ; une variable ne se recode pas "
         "ainsi."),
        ({"source": {"variable": "age"}},
         "age : seules des catégories (nominales ou ordinales) se regroupent ; un nombre se "
         "découpe en classes."),
        ({"name": "age"}, "age : nom déjà pris."),
        ({"name": "anxiete_t1"}, "anxiete_t1 : nom déjà pris."),
        ({"name": "Sexe 2"}, "Sexe 2 : nom invalide (lettres minuscules, chiffres et _, au plus "
                             "32 caractères, pas un mot réservé)."),
    ],
)  # fmt: skip
def test_refused_groups(base, change, reason):
    project, _table = base
    with pytest.raises(recodes.RecodeRefused) as refused:
        recodes.validated(project, {**SEXE_2, **change})
    assert reason in refused.value.reasons


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"cuts": [45, 30]}, "Les seuils doivent aller croissant."),
        ({"cuts": []}, "Il faut au moins un seuil."),
        ({"labels": ["moins de 30", "30 et plus"]},
         "Une étiquette par classe : une de plus que les seuils."),
        ({"source": {"variable": "sexe"}},
         "sexe : seul un nombre (une échelle ou un score) se découpe en classes ; des catégories "
         "se regroupent."),
    ],
)  # fmt: skip
def test_refused_classes(base, change, reason):
    project, _table = base
    with pytest.raises(recodes.RecodeRefused) as refused:
        recodes.validated(project, {**AGE_CLASSE, **change})
    assert reason in refused.value.reasons


def test_every_observed_value_has_a_place(base):
    project, table = base
    two = {**SEXE_2, "groups": [{"code": 1, "label": "Femme", "values": [1]},
                                {"code": 2, "label": "Homme", "values": [2]}]}  # fmt: skip
    found = _checked(project, table, two)
    assert found.refusals == [
        "Valeurs sans groupe : 3 (Autre identité, 14 personnes). Mettez-les dans un groupe, ou "
        "déclarez-les manquantes."
    ]
    declared = _checked(project, table, {**two, "missing_values": [3]})
    assert declared.ok and declared.counts == [("Femme", 133), ("Homme", 93)]


def test_warnings_empty_class_and_small_category(base):
    project, table = base
    found = _checked(project, table, {**AGE_CLASSE, "cuts": [23, 70],
                                      "labels": ["jeunes", "adultes", "aînés"]})  # fmt: skip
    assert found.ok
    assert found.warnings == ["Moins de 5 personnes : jeunes (1).", "Classe vide : aînés."]


def test_text_categories_regroup(tmp_path):
    project, _path = _base(tmp_path)
    table = read_database(_path.with_name("etude-textes.csv")).table
    data = {"kind": "groups", "source": {"variable": "region"}, "name": "region_2",
            "label": "Région, en deux", "reason": "Comparer le centre et le reste.",
            "groups": [{"code": 1, "label": "Centre-ville", "values": ["centre-ville"]},
                       {"code": 2, "label": "Ailleurs",
                        "values": ["nord-est", "sud", "ouest"]}]}  # fmt: skip
    found = _checked(project, table, data)
    assert found.ok and sum(n for _label, n in found.counts) == len(table)


# --- Where a recoded variable goes. ---


def test_in_an_analysis_with_its_labels(base):
    project, table = base
    _added(project, SEXE_2)
    prepared = apply_decisions(project, table)
    assert conditions.levels(project)["sexe_2"] == "nominal"
    assert "sexe_2" in conditions.candidates(project, CATALOGUE["t_test"], "group")
    result = run(project, prepared, "t_test", {"outcome": ["stress"], "group": ["sexe_2"]})
    assert "pour Femme et M = " in result.sentence
    assert "pour Homme ou autre identité" in result.sentence
    assert Codebook(project, prepared).label("sexe_2") == "Sexe, en deux groupes"


def test_in_an_exclusion_rule_and_a_subgroup(base):
    project, table = base
    _added(project, AGE_CLASSE)
    rules.add(project, {"kind": "condition", "recode": "R1", "operator": "eq", "value": 1,
                        "reason": "Moins de 30 ans"})  # fmt: skip
    prepared = apply_decisions(project, table)
    assert len(prepared.table) == 240 - 49
    assert prepared.flow.excluded == (("E1", 49),)
    project.exclusions.rules.clear()
    prepared = apply_decisions(project, table)
    result = run(project, prepared, "paired", {"first": ["anxiete_t1"],
                                               "second": ["anxiete_t2"]},
                 None, Subset("age_classe", "eq", 3.0))  # fmt: skip
    assert result.sentence.startswith("Sous-groupe (age_classe = 45 et plus).")


def test_in_the_notebook_by_its_rule(base):
    project, _table = base
    _added(project, SEXE_2)
    ref = nb.reference(project, "sexe_2")
    assert ref == VariableRef(recode="R1")
    project.recodes.rules[0].name = "sexe_deux"  # a renaming keeps the reference
    assert nb.resolve(project, ref) == "sexe_deux"
    project.recodes.rules.clear()
    with pytest.raises(nb.NotebookError) as error:
        nb.resolve(project, ref)
    assert nb.reason_text(error.value) == "R1 : le recodage n'est plus dans le projet."


def test_removal_refused_while_used(base):
    project, _table = base
    _added(project, AGE_CLASSE)
    rules.add(project, {"kind": "condition", "recode": "R1", "operator": "eq", "value": 1,
                        "reason": "Moins de 30 ans"})  # fmt: skip
    with pytest.raises(recodes.RecodeRefused) as refused:
        recodes.remove(project, "R1")
    assert refused.value.reasons == ["R1 : utilisé par E1 ; retirez-les ou changez-les d'abord."]
    project.exclusions.rules.clear()
    recodes.remove(project, "R1")
    assert project.recodes.rules == [] and project.recodes.next_id == 2


def test_in_a_hypothesis_and_its_frozen_notebook(base, tmp_path):
    from ddict.analysis import plan_notebook as pn
    from ddict.analysis import planning as pl

    project, table = base
    _added(project, SEXE_2, AGE_CLASSE)
    prepared = apply_decisions(project, table)
    data = pl.data_from_names(project, "Le stress diffère selon le sexe.", "t_test",
                              {"outcome": ["stress"], "group": ["sexe_2"]}, {},
                              subgroup=Subset("age_classe", "ge", 2.0))  # fmt: skip
    hypothesis = pl.add(project, data, prepared, None, "2026-10-18")
    assert hypothesis.roles["group"] == [VariableRef(recode="R1")]
    assert hypothesis.subgroup.variable == VariableRef(recode="R2")
    assert pl.review(project, hypothesis, prepared).ok
    with pytest.raises(recodes.RecodeRefused) as refused:
        recodes.remove(project, "R1")
    assert refused.value.reasons == ["R1 : utilisé par H1 ; retirez-les ou changez-les d'abord."]
    notebook = nb.new_notebook(project, tmp_path / "etude-suivi.dd.json")
    project.plan.alpha, project.plan.data_origin = 0.05, "primary"
    project.plan.data_status = "before_analysis"
    pn.freeze(notebook, project, prepared, "2026-10-18")
    statistics = notebook.entries[0].computed.statistics
    assert statistics["n1"] + statistics["n2"] == 240 - 49
