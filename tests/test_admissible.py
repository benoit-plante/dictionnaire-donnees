"""v0.16, step C3 (finding 22): in each list of an analysis, the variables that fit the role
come first, the others after, each with its reason. Only the order and the reasons are new:
no analysis becomes possible where it was not."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import conditions
from ddict.analysis.catalogue import CATALOGUE
from ddict.review import admissible
from ddict.workflow import profile_database
from test_analysis_data import KEY, _prepared, analyses_project
from test_notebook_page import _folder

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


@pytest.fixture(scope="module")
def study():
    project = analyses_project()
    return project, _prepared(project, KEY["sav"])


def test_the_groups_of_a_t_test(study):
    project, prepared = study
    fits = admissible.ranked(project, "t_test", "group", prepared)
    first = [(f.name, f.rank) for f in fits[:5]]
    assert first == [("groupe", 0), ("sexe", 0), ("teletravail", 0), ("region", 1),
                     ("secteur", 1)]  # fmt: skip
    region = next(f for f in fits if f.name == "region")
    assert region.reason == "4 modalités : choisir les deux comparées"
    item = next(f for f in fits if f.name == "bienetre_1")  # a Likert item: allowed, rarely meant
    assert (item.rank, item.reason) == (
        admissible.LESS_SUITED,
        "niveau ordinal ; 5 modalités : choisir les deux comparées",
    )
    age = next(f for f in fits if f.name == "age")
    assert (age.rank, age.reason) == (admissible.DOES_NOT_FIT, "niveau échelle")
    assert [f.rank for f in fits] == sorted(f.rank for f in fits)


def test_the_counts_of_modalities(study):
    project, prepared = study
    fits = {f.name: f for f in admissible.ranked(project, "anova", "group", prepared)}
    assert fits["region"].rank == admissible.FITS  # 4 groups: an ANOVA takes 3 to 10
    assert fits["groupe"].reason == "2 modalités ; il en faut au moins 3"
    assert fits["groupe"].rank == admissible.DOES_NOT_FIT


def test_without_the_database_only_the_levels(study):
    project, _prepared_data = study
    fits = {f.name: f for f in admissible.ranked(project, "t_test", "group", None)}
    assert fits["region"].rank == admissible.FITS  # its modalities are not known
    assert fits["age"].reason == "niveau échelle"


def test_identifiers_texts_and_dates_stay_out(study):
    project, prepared = study
    names = {f.name for f in admissible.ranked(project, "correlation", "variables", prepared)}
    assert not names & conditions.excluded(project)


@pytest.mark.parametrize("base", ["analyses", "sommeil", "suivi"])
def test_no_analysis_becomes_possible(base, tmp_path, study):
    """For every analysis and role: a variable said not to fit is refused by the check, as
    before; the variables of the right level are exactly those of the old lists."""
    if base == "analyses":
        project, prepared = study
    else:
        name = {"sommeil": "etude-sommeil.sav", "suivi": "etude-suivi.sav"}[base]
        shutil.copy(EXAMPLES / name, tmp_path / name)
        project, _path = profile_database(tmp_path / name)
        prepared = _prepared(project, name)
    for key, analysis in CATALOGUE.items():
        lists = {r.key: admissible.ranked(project, key, r.key, prepared) for r in analysis.roles}
        for role in analysis.roles:
            fits = lists[role.key]
            wrong_level = {
                f.name
                for f in fits
                if f.rank == admissible.DOES_NOT_FIT and f.reason.startswith("niveau ")
            }
            right_level = {f.name for f in fits} - wrong_level
            assert right_level == set(conditions.candidates(project, analysis, role.key)), key
            for fit in fits:
                if fit.rank != admissible.DOES_NOT_FIT:
                    continue
                # The other roles filled with variables that fit, as a person would.
                chosen = {role.key: [fit.name]}
                for other in analysis.roles:
                    if other.key == role.key or other.least == 0:
                        continue
                    good = [f.name for f in lists[other.key]
                            if f.rank == admissible.FITS and f.name != fit.name]  # fmt: skip
                    chosen[other.key] = good[: other.least]
                found = conditions.check(project, key, chosen, None, prepared)
                assert any(fit.name in r for r in found.refusals), (key, role.key, fit)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_list_on_the_page(tmp_path):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(_folder(tmp_path))
    app.session_state["mode"] = "analyses"
    app.run()
    app.selectbox(key="analysis-key").set_value("t_test").run()
    options = app.selectbox(key="analysis-t_test-group").options
    assert options[0].startswith("groupe")
    assert any(o.endswith("(niveau ordinal ; 5 modalités : choisir les deux comparées)")
               for o in options)  # fmt: skip
    assert options[-1].endswith("(niveau échelle)")
