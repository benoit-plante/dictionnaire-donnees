"""Projects at different stages, for the home page's table (v0.17, plan § 8.1): made in a
temporary folder from the fictional databases (fixed seed), in a folder with accents and
spaces. Nothing real."""

import shutil
from pathlib import Path

from ddict.analysis import notebook as nb
from ddict.analysis import planning as pl
from ddict.analysis.compute import run
from ddict.analysis.notebook_export import SUFFIX
from ddict.project import SCHEMA_VERSION, dumps, save_project
from ddict.project.decisions import validate
from ddict.project.model import Publication
from ddict.workflow import add_questionnaire, default_project_path, profile_database
from projet_concu import project as designed
from test_analysis_data import KEY, _prepared, analyses_project
from test_plan import EXAMPLE, RULES

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
SLEEP, ANALYSES = "etude-sommeil.sav", KEY["sav"]
NOW = "2026-10-18T09:00:00"
STAGES = (
    "neuf", "moitie", "plan", "carnet", "article", "sans-base", "introuvable", "recent",
    "abime", "concu", "collecte",
)  # fmt: skip


def _folder(root: Path, stage: str, database: str) -> Path:
    folder = root / "Études 2026" / "Vague 2" / stage
    folder.mkdir(parents=True)
    shutil.copy(EXAMPLES / database, folder / database)
    return folder / database


def _sleep(root: Path, stage: str) -> tuple:
    return profile_database(_folder(root, stage, SLEEP))


def _analyses(root: Path, stage: str):
    """The analyses' study, its scale scored, saved next to its database."""
    base = _folder(root, stage, ANALYSES)
    project = analyses_project()
    path = default_project_path(base)
    save_project(project, path)
    return project, path, _prepared(project, ANALYSES)


def _planned(project, prepared) -> None:
    """The example plan, frozen, then amended once."""
    for data in EXAMPLE:
        pl.add(project, data, prepared)
    pl.set_rules(project, RULES)
    pl.freeze(project, prepared, today="2026-10-18")
    pl.modify(project, "H5", {"statement": "L'âge est lié au stress perçu."}, prepared,
              reason="Énoncé précisé.", today="2026-10-19")  # fmt: skip


def make(root: Path) -> dict[str, Path]:
    """Each stage's project file, by its name in STAGES."""
    found = {}

    found["neuf"] = _sleep(root, "neuf")[1]

    project, path = _sleep(root, "moitie")  # half reviewed: questionnaire, unit, levels
    add_questionnaire(project, EXAMPLES / "questionnaire-sommeil.pdf")
    project.dataset.unit_of_observation = "participant"
    for entry in project.variables:
        for field in ("measure_level", "question"):
            if getattr(entry, field).status == "proposed":
                setattr(entry, field, validate(getattr(entry, field), now=NOW))
    save_project(project, path)
    found["moitie"] = path

    project, path, prepared = _analyses(root, "plan")
    _planned(project, prepared)
    save_project(project, path)
    found["plan"] = path

    # A notebook: two analyses retained, one not; a new calculation waits on the first;
    # a decision taken after the calculation changes the codebook's fingerprint.
    project, path, prepared = _analyses(root, "carnet")
    notebook = nb.new_notebook(project, path)
    for key, chosen in (
        ("anova", {"outcome": ["stress"], "group": ["niveau_etudes"]}),
        ("correlation", {"variables": ["heures_travail", "stress"]}),
        ("chi_square", {"rows": ["teletravail"], "columns": ["secteur"]}),
    ):
        nb.add(notebook, project, run(project, prepared, key, chosen), today="2026-10-18")
    nb.retain(notebook, "A3", False)
    notebook.entries[0].pending = notebook.entries[0].computed.model_copy()
    nb.save_notebook(notebook, nb.notebook_path(path))
    project.dataset.unit_of_observation = "participant"
    save_project(project, path)
    found["carnet"] = path

    project, path, prepared = _analyses(root, "article")
    nb.add(notebook := nb.new_notebook(project, path), project,
           run(project, prepared, "correlation", {"variables": ["age", "stress"]}))  # fmt: skip
    nb.save_notebook(notebook, nb.notebook_path(path))
    path.with_name(path.name.removesuffix(".dd.json") + SUFFIX + ".docx").write_bytes(b"PK")
    found["article"] = path

    _project, path = _sleep(root, "sans-base")
    path.with_name(SLEEP).unlink()
    found["sans-base"] = path

    _project, path = _sleep(root, "introuvable")
    path.unlink()
    found["introuvable"] = path

    project, path = _sleep(root, "recent")
    major = SCHEMA_VERSION.split(".")[0]
    text = dumps(project).replace(
        f'"schema_version": "{SCHEMA_VERSION}"', f'"schema_version": "{major}.999.0"'
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    found["recent"] = path

    project, path = _sleep(root, "abime")
    text = dumps(project)
    path.write_text(text[: len(text) // 2], encoding="utf-8", newline="\n")
    found["abime"] = path

    # v0.20 (D-154): a questionnaire designed in the tool, then marked as sent.
    for stage in ("concu", "collecte"):
        folder = root / "Études 2026" / "Vague 2" / stage
        folder.mkdir(parents=True)
        project = designed()
        if stage == "collecte":
            project.design.publications = [
                Publication(kind="limesurvey", date="2026-10-20", fingerprint="0" * 64,
                            questionnaire=project.questionnaire.model_copy(deep=True))
            ]  # fmt: skip
        path = folder / "etude-concue.dd.json"
        save_project(project, path)
        found[stage] = path

    return found
