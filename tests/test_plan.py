"""v0.13, step 2: the analysis plan in the project (D-101 to D-104, D-109), as the validated
sheet docs/plan-analyse-article.md describes it: hypotheses tied to the catalogue, refused
with their reason when badly tied, a fingerprint of their own, freezing and amendments."""

import json

import pytest

from ddict.analysis import planning as pl
from ddict.project import fingerprint
from ddict.project.model import TrackedValue
from ddict.project.store import load_project, save_project
from test_analysis_data import KEY, _prepared, analyses_project

TODAY = "2026-10-20"
LATER = "2026-11-02"


def _v(name):
    return {"variable": name}


SCORE = {"score": "G1"}
# The sheet's example plan (§ 1).
EXAMPLE = [
    {"statement": "Le bien-être au travail est plus élevé dans le groupe d'intervention que "
                  "dans le groupe contrôle.",
     "analysis": "t_test", "roles": {"outcome": [SCORE], "group": [_v("groupe")]},
     "direction": "first_higher", "kind": "confirmatory", "family": "F1"},
    {"statement": "Plus les heures de travail sont nombreuses, plus le stress est élevé.",
     "analysis": "correlation", "roles": {"variables": [_v("heures_travail"), _v("stress")]},
     "direction": "positive", "family": "F1"},
    {"statement": "Le stress diffère selon le niveau d'études.",
     "analysis": "anova", "roles": {"outcome": [_v("stress")], "group": [_v("niveau_etudes")]},
     "family": "F1"},
    {"statement": "Le soutien des collègues prédit la satisfaction au travail, à charge de "
                  "travail égale.",
     "analysis": "regression",
     "roles": {"outcome": [_v("satisfaction")], "predictors": [_v("soutien"), _v("charge")]},
     "effect": {"kind": "predictor", "variable": _v("soutien")}, "direction": "positive"},
    {"statement": "L'âge est lié au stress.", "analysis": "correlation",
     "roles": {"variables": [_v("age"), _v("stress")]}, "kind": "exploratory"},
]  # fmt: skip
RULES = {
    "alpha": 0.05,
    "correction": "holm",
    "data_origin": "primary",
    "data_status": "before_analysis",
    "sample_size": "Toutes les réponses de la base, sans calcul de puissance préalable.",
}


@pytest.fixture(scope="module")
def prepared():
    return _prepared(analyses_project(), KEY["sav"])


@pytest.fixture
def project():
    return analyses_project()


def _planned(project, prepared, frozen=False):
    for data in EXAMPLE:
        pl.add(project, data, prepared)
    pl.set_rules(project, RULES)
    if frozen:
        pl.freeze(project, prepared, today=TODAY)
    return project


# --- The sheet's example. ---


def test_the_sheets_example(project, prepared):
    _planned(project, prepared)
    plan = project.plan
    assert [h.id for h in plan.hypotheses] == ["H1", "H2", "H3", "H4", "H5"]
    assert plan.next_id == 6
    h1 = json.loads(plan.hypotheses[0].model_dump_json())
    assert h1["roles"] == {"outcome": [{"score": "G1"}], "group": [{"variable": "groupe"}]}
    assert h1["options"] == {"method": "welch", "alternative": "greater"}  # from the direction
    assert h1["effect"] == {"kind": "difference"}
    assert (h1["direction"], h1["kind"], h1["family"]) == ("first_higher", "confirmatory", "F1")
    h2 = plan.hypotheses[1]
    assert h2.effect.kind == "pair"  # two variables: their one pair, chosen by the tool
    assert [r.variable for r in h2.effect.variables] == ["heures_travail", "stress"]
    assert plan.hypotheses[2].effect.kind == "group"
    assert plan.hypotheses[2].options == {"method": "anova", "post_hoc": "none"}
    assert plan.hypotheses[4].kind == "exploratory" and plan.hypotheses[4].family is None
    for hypothesis in plan.hypotheses:
        assert pl.review(project, hypothesis, prepared).refusals == []


def test_a_two_sided_test_chosen_by_the_team_stays_two_sided(project, prepared):
    data = EXAMPLE[0] | {"options": {"alternative": "two_sided"}}
    assert pl.add(project, data, prepared).options["alternative"] == "two_sided"


def test_without_the_data_the_conditions_wait(project):
    hypothesis = pl.add(project, EXAMPLE[2])
    warnings = pl.review(project, hypothesis).warnings
    assert "Conditions à vérifier quand la base sera ouverte." in warnings


# --- An hypothesis badly tied is refused, with its reason (the criterion of step 2). ---

T_TEST = EXAMPLE[0]
REFUSED = [
    ("table1", {"analysis": "table1", "roles": {"variables": [_v("age")]}},
     "Le Tableau 1 décrit l'échantillon ; il ne teste aucune hypothèse."),
    ("unknown analysis", {"analysis": "mediation", "effect": {"kind": "model"}},
     "Analyse inconnue : mediation."),
    ("unknown role", {"roles": T_TEST["roles"] | {"covariates": [_v("age")]}},
     "covariates : rôle inconnu pour cette analyse."),
    ("unknown option", {"options": {"method": "bayes"}},
     "method : « bayes » n'est pas un choix permis."),
    ("wrong level", {"roles": {"outcome": [SCORE], "group": [_v("stress")]}},
     "stress : niveau « échelle », ne convient pas au rôle « variable de groupe »."),
    ("unknown variable", {"roles": {"outcome": [_v("bonheur")], "group": [_v("groupe")]}},
     "bonheur : la variable n'est plus dans le projet."),
    ("effect of another analysis", {"effect": {"kind": "pair",
                                               "variables": [_v("stress"), _v("age")]}},
     "Un test t teste la différence entre les deux groupes, pas une paire de variables."),
    ("direction an ANOVA cannot test", {**EXAMPLE[2], "direction": "positive"},
     "Une ANOVA ne teste pas de sens ; laissez le sens attendu vide."),
    ("direction of another effect", {"direction": "positive"},
     "Pour un test t, le sens attendu est le premier ou le second groupe plus élevé."),
    ("direction against the one-sided test", {"options": {"alternative": "less"}},
     "Le sens attendu contredit le test unilatéral choisi."),
    ("an exploratory hypothesis in a family", {"kind": "exploratory"},
     "Une hypothèse exploratoire n'est pas corrigée ; retirez sa famille."),
    ("empty statement", {"statement": "   "},
     "Écrivez l'hypothèse (1 000 caractères au plus)."),
    ("statement too long", {"statement": "x" * 1001},
     "Écrivez l'hypothèse (1 000 caractères au plus)."),
    ("pair outside the correlation", {**EXAMPLE[1], "effect": {
        "kind": "pair", "variables": [_v("heures_travail"), _v("age")]}},
     "age n'est pas une variable de cette corrélation."),
    ("predictor outside the regression", {**EXAMPLE[3], "effect": {
        "kind": "predictor", "variable": _v("age")}},
     "age n'est pas un prédicteur de cette régression."),
    ("nominal predictor of three modalities", {
        **EXAMPLE[3], "roles": {"outcome": [_v("satisfaction")],
                                "predictors": [_v("soutien"), _v("secteur")]},
        "effect": {"kind": "predictor", "variable": _v("secteur")}, "direction": None},
     "Un prédicteur nominal de 3 modalités a 2 coefficients ; une hypothèse ne porte que sur "
     "un seul. Testez le modèle, ou choisissez une variable de 2 modalités."),
    ("regression without its effect", {**EXAMPLE[3], "effect": None},
     "Choisissez l'effet testé : le modèle ou un prédicteur."),
    ("correlation of three variables without its pair", {
        **EXAMPLE[1], "roles": {"variables": [_v("heures_travail"), _v("stress"), _v("age")]}},
     "Choisissez la paire testée."),
]  # fmt: skip


@pytest.mark.parametrize(
    ("data", "reason"), [(d, r) for _n, d, r in REFUSED], ids=[n for n, _d, _r in REFUSED]
)
def test_an_hypothesis_badly_tied_is_refused_with_its_reason(project, prepared, data, reason):
    with pytest.raises(pl.PlanRefused) as refused:
        pl.add(project, T_TEST | data, prepared)
    assert reason in refused.value.reasons
    assert project.plan.hypotheses == [] and project.plan.next_id == 1


def test_a_binary_nominal_predictor_is_allowed(project, prepared):
    data = EXAMPLE[3] | {
        "roles": {"outcome": [_v("satisfaction")], "predictors": [_v("soutien"), _v("sexe")]},
        "effect": {"kind": "predictor", "variable": _v("sexe")},
        "direction": None,
    }
    assert pl.add(project, data, prepared).effect.kind == "predictor"


def test_references_survive_a_renaming(project, prepared):
    hypothesis = pl.add(project, EXAMPLE[1], prepared)
    project.variable("stress").new_name = TrackedValue[str](
        value="stress_total", origin="human", status="none"
    )
    renamed = _prepared(project, KEY["sav"])
    assert pl.review(project, hypothesis, renamed).refusals == []
    assert hypothesis.effect.variables[1].variable == "stress"


# --- The project file (format 0.5.0) and the fingerprints. ---


def test_the_project_file(tmp_path, project, prepared):
    path = tmp_path / "etude-analyses.dd.json"
    save_project(project, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "0.9.0"
    assert list(data["plan"]) == ["alpha", "correction", "missing", "sample_size", "data_origin",
                                  "data_status", "next_id", "hypotheses", "frozen",
                                  "amendments"]  # fmt: skip
    del data["plan"]
    data["schema_version"] = "0.4.0"  # a project of v0.12
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    old = load_project(path)
    assert old.schema_version == "0.9.0" and old.plan.hypotheses == []
    _planned(old, prepared, frozen=True)
    pl.modify(old, "H2", {"options": {"method": "spearman"}}, prepared, "Asymétrie", LATER)
    save_project(old, path)
    text = path.read_text(encoding="utf-8")
    again = load_project(path)
    assert again.plan == old.plan
    save_project(again, path)
    assert path.read_text(encoding="utf-8") == text  # byte for byte


def test_writing_the_plan_never_changes_the_codebooks_fingerprint(project, prepared):
    before = fingerprint.fingerprint(project)
    _planned(project, prepared, frozen=True)
    assert fingerprint.fingerprint(project) == before


def test_the_plans_fingerprint(project, prepared):
    _planned(project, prepared)
    first = pl.plan_fingerprint(project.plan)
    assert len(first) == 64
    pl.move(project, "H5", 1)  # the order of the article only
    assert pl.plan_fingerprint(project.plan) == first
    pl.set_rules(project, {"correction": "bonferroni"})
    assert pl.plan_fingerprint(project.plan) != first


# --- Freezing and amendments (D-102). ---


def test_freezing_needs_what_the_sheet_says(project, prepared):
    with pytest.raises(pl.PlanRefused) as refused:
        pl.freeze(project, prepared)
    assert refused.value.reasons == [
        "Le plan n'a aucune hypothèse.",
        "Tapez le seuil α du plan.",
        "Dites l'origine des données et leur état quand le plan a été écrit.",
    ]
    _planned(project, prepared, frozen=True)
    frozen = project.plan.frozen
    assert frozen.date == TODAY and frozen.prior == []
    assert frozen.fingerprint == pl.plan_fingerprint(project.plan)
    with pytest.raises(pl.PlanRefused, match=r"Le plan est déjà arrêté\."):
        pl.freeze(project, prepared)


def test_before_freezing_no_amendment(project, prepared):
    _planned(project, prepared)
    pl.modify(project, "H2", {"options": {"method": "spearman"}}, prepared)
    pl.remove(project, "H5")
    assert project.plan.amendments == []


def test_after_freezing_every_change_needs_a_reason(project, prepared):
    _planned(project, prepared, frozen=True)
    frozen = project.plan.frozen.fingerprint
    changes = [
        lambda r: pl.modify(project, "H2", {"options": {"method": "spearman"}}, prepared, r),
        lambda r: pl.add(project, EXAMPLE[2] | {"family": None}, prepared, r),
        lambda r: pl.remove(project, "H5", r),
        lambda r: pl.set_rules(project, {"correction": "bonferroni"}, r),
    ]
    for change in changes:
        with pytest.raises(pl.PlanRefused) as refused:
            change("  ")
        assert refused.value.reasons == [
            "Le plan est arrêté : donnez la raison de cette modification."
        ]
    assert project.plan.amendments == []
    assert pl.plan_fingerprint(project.plan) == frozen
    pl.move(project, "H4", 1)  # never an amendment
    assert project.plan.amendments == []


def test_amendments_keep_only_what_changed(project, prepared):
    _planned(project, prepared, frozen=True)
    pl.modify(project, "H2", {"options": {"method": "spearman"}}, prepared,
              "Distribution des heures très asymétrique", LATER)  # fmt: skip
    pl.set_rules(project, {"correction": "bonferroni"}, "Avis du comité", LATER)
    added = pl.add(project, EXAMPLE[2] | {"family": None}, prepared, "Oubli", LATER)
    pl.remove(project, "H5", "Hors du sujet", LATER)
    pl.modify(project, "H1", {"statement": EXAMPLE[0]["statement"]}, prepared, "Rien")
    amendments = [a.model_dump(mode="json") for a in project.plan.amendments]
    assert len(amendments) == 4  # the same statement again: nothing changed, no amendment
    assert amendments[0] == {
        "date": LATER, "target": "H2", "change": "modified",
        "reason": "Distribution des heures très asymétrique",
        "before": {"options": {"method": "pearson"}}, "after": {"options": {"method": "spearman"}},
    }  # fmt: skip
    assert amendments[1]["target"] == "rules"
    assert (amendments[1]["before"], amendments[1]["after"]) == (
        {"correction": "holm"},
        {"correction": "bonferroni"},
    )
    assert amendments[2]["change"] == "added" and amendments[2]["target"] == added.id == "H6"
    assert amendments[2]["before"] == {} and amendments[2]["after"]["analysis"] == "anova"
    assert amendments[3]["change"] == "removed" and amendments[3]["after"] == {}
    assert amendments[3]["before"]["statement"] == EXAMPLE[4]["statement"]
    assert project.plan.frozen.fingerprint != pl.plan_fingerprint(project.plan)


def test_changing_the_direction_of_a_t_test_changes_its_one_sided_option(project, prepared):
    pl.add(project, EXAMPLE[0], prepared)
    changed = pl.modify(project, "H1", {"direction": "second_higher"}, prepared)
    assert changed.options["alternative"] == "less"


def test_a_refused_change_leaves_the_plan_as_it_was(project, prepared):
    _planned(project, prepared, frozen=True)
    before = project.plan.model_dump(mode="json")
    with pytest.raises(pl.PlanRefused):
        pl.modify(project, "H3", {"direction": "positive"}, prepared, "Essai")
    with pytest.raises(pl.PlanRefused):
        pl.set_rules(project, {"alpha": 1.5}, "Essai")
    assert project.plan.model_dump(mode="json") == before


def test_the_whole_plan_can_be_removed(project, prepared):
    _planned(project, prepared, frozen=True)
    pl.clear(project)
    assert project.plan.model_dump(mode="json") == pl.Plan().model_dump(mode="json")
