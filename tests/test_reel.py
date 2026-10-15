"""Real survey exports, kept outside the repository (D-046).

The folder is given by DDICT_DONNEES_REELLES: one subfolder per base, each with its `.sav`
file and, when there are, its `.xlsx` export and its questionnaire. Without it, every test
is skipped, so continuous integration never runs them.

What may be shown: counts and rates only. The counts come from scripts/compter_structure.py,
which never returns a value, a label, a text nor a file name, and reports an error by its
type only; assertions compare numbers, so a failure shows numbers. Tests are named base1,
base2, never after the files.

Each finding of the trial (docs/plan-v0.7.md, § 1) has its test, fixed in v0.7, steps 2 to
5. A finding may not show in every base (a base without grids cannot have one cut in two):
a test without object in a base is skipped.
"""

import os
from pathlib import Path

import pytest

from conftest import load_counter

pytestmark = pytest.mark.reel

_FOLDER = os.environ.get("DDICT_DONNEES_REELLES")
_COUNTER = load_counter()
BASES = _COUNTER.bases(Path(_FOLDER)) if _FOLDER and Path(_FOLDER).is_dir() else {}
_CACHE: dict[str, dict] = {}


def _params():
    if not BASES:
        reason = "DDICT_DONNEES_REELLES non défini ou introuvable"
        return [pytest.param(None, marks=pytest.mark.skip(reason=reason), id="sans-donnees")]
    return [pytest.param(name, id=name) for name in sorted(BASES)]


@pytest.fixture(params=_params())
def counts(request) -> dict:
    name = request.param
    if name not in _CACHE:
        _CACHE[name] = _COUNTER.count_base(BASES[name])
    return _CACHE[name]


def _needs(counts: dict, key: str) -> None:
    if not counts.get(key):
        pytest.skip(f"sans objet : {key} = 0")


def test_the_base_is_read(counts):
    assert sorted(k for k in counts if k.startswith("erreur")) == []
    assert counts["variables_plateforme"] > 0


def test_the_platform_is_recognized(counts):
    assert counts["plateforme_reconnue"] == 1


def test_the_second_header_row_is_not_a_participant(counts):
    if "xlsx_lignes_en_trop" not in counts:
        pytest.skip("pas d'export .xlsx")
    assert counts["xlsx_lignes_en_trop"] == 0
    assert counts["xlsx_colonnes_sans_nom"] == 0
    assert counts["xlsx_noms_absents_du_sav"] == 0


def test_single_questions_do_not_make_a_group(counts):
    assert counts["groupes_melant_des_questions"] == 0


def test_a_grid_is_one_group(counts):
    _needs(counts, "grilles")
    assert counts["grilles_coupees"] == 0
    assert counts["grilles_entieres"] == counts["grilles"]


def test_a_checkbox_set_is_a_multiple_response_group(counts):
    _needs(counts, "ensembles_a_cocher")
    assert counts["ensembles_a_cocher_groupes"] == counts["ensembles_a_cocher"]


def test_no_grid_item_is_an_identifier(counts):
    _needs(counts, "grilles")
    assert counts["items_de_grille_identifiant_probable"] == 0


def test_the_survey_dates_are_read_as_dates(counts):
    assert counts["dates_lues_comme_dates"] == counts["dates_de_passation"]
    assert counts["dates_classees_texte_libre"] == 0


def test_dont_know_codes_are_suspect_missing_codes(counts):
    _needs(counts, "codes_a_etiquette_de_manquant")
    assert (
        counts["codes_a_etiquette_de_manquant_signales"] == counts["codes_a_etiquette_de_manquant"]
    )


def test_the_scale_level_of_labelled_items_is_flagged(counts):
    _needs(counts, "items_de_grille_niveau_scale")
    assert counts["items_niveau_scale_signales"] == counts["items_de_grille_niveau_scale"]


def test_the_pdf_has_the_grids_and_checkboxes_of_the_base(counts):
    if "pdf_questions" not in counts:
        pytest.skip("pas de questionnaire PDF")
    assert counts["pdf_grilles"] == counts["grilles"]
    # Read as checkboxes, or found such by the structure of the export.
    checkboxes = counts["pdf_checkbox"] + counts["pdf_a_verifier_kind_from_platform"]
    assert checkboxes == counts["ensembles_a_cocher"]


def test_the_excel_header_links_every_question_variable(counts):
    if "entete_liens_par_la_structure" not in counts:
        pytest.skip("pas d'export .xlsx")
    assert counts["entete_liens_par_la_structure"] == counts["entete_variables_de_questions"]
    assert counts["entete_liens_dont_le_texte_concorde"] == counts["entete_liens_par_la_structure"]


def test_structural_links_agree_with_the_pdf(counts):
    if "pdf_liens_par_la_structure" not in counts:
        pytest.skip("pas de questionnaire PDF")
    assert counts["pdf_liens_dont_le_texte_concorde"] == counts["pdf_liens_par_la_structure"]
