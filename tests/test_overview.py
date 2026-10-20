"""v0.17, step B1 (plan § 7.1 to 7.3, D-133): where a project is, without its database —
the columns of the home page's table on the projects of `projets_stades`, no error from a
project that cannot be read, the cache, and the time it takes."""

import os
import shutil
import time
from pathlib import Path

import pytest

import projets_stades as stages
from ddict import i18n, overview, recents
from ddict.analysis import notebook as nb
from ddict.project import load_project, save_project
from ddict.review import logic
from ddict.workflow import Task, tasks

COLUMNS = (
    overview.phase_text,
    overview.waiting_text,
    overview.plan_text,
    overview.notebook_text,
    overview.base_text,
)
EXPECTED = {
    "neuf": ("Documenter", "4 · Ajouter le questionnaire de l'étude", "—", "—", "trouvée"),
    "moitie": ("Documenter", "4 · Sigles à valider : 3", "—", "—", "trouvée"),
    "plan": ("Analyser", "1 · Ajouter le questionnaire de l'étude", "figé, 1 amendement", "—",
             "trouvée"),
    "carnet": ("Analyser", "2 · Ajouter le questionnaire de l'étude", "—",
               "2 retenues · 1 à confirmer · 1 à recalculer", "trouvée"),
    "article": ("Rédiger", "3 · Ajouter le questionnaire de l'étude", "—", "1 retenue",
                "trouvée"),
    "sans-base": ("Documenter", "4 · Ajouter le questionnaire de l'étude", "—", "—",
                  "introuvable"),
    "introuvable": ("—", "Introuvable : le fichier n'est plus à cet endroit.", "—", "—", "—"),
    "recent": ("—", "Écrit par une version plus récente de l'outil (format 0.999.0) : mettez "
               "l'outil à jour.", "—", "—", "—"),
    "abime": ("—", "Fichier projet illisible.", "—", "—", "—"),
    "concu": ("Concevoir", "5 · Points de relecture : 5", "—", "—", "pas encore"),
    "collecte": ("En collecte", "5 · Points de relecture : 5", "—", "—", "pas encore"),
}  # fmt: skip


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    return stages.make(tmp_path_factory.mktemp("stades"))


@pytest.fixture(autouse=True)
def fresh():
    overview.clear_cache()
    yield
    overview.clear_cache()


@pytest.mark.parametrize("stage", stages.STAGES)
def test_each_column(made, stage):
    found = overview.row(made[stage])
    assert tuple(text(found) for text in COLUMNS) == EXPECTED[stage]
    assert found.name in ("etude-sommeil", "etude-analyses", "etude-concu", "etude-collecte")
    assert "Études 2026" in found.folder


@pytest.mark.parametrize("stage", ["neuf", "moitie", "plan", "carnet", "article"])
def test_the_same_figures_as_the_open_project(made, stage):
    """The codebook's share is the sidebar's; the tasks are the dashboard's, without the
    notebook's recomputation (which reads the database)."""
    found = overview.row(made[stage])
    project = load_project(made[stage])
    assert found.codebook == logic.codebook_progress(project)
    assert overview.codebook_text(found) == f"{round(100 * found.codebook)} %"
    assert list(found.tasks) == tasks(project, made[stage])


def test_a_half_reviewed_codebook_says_its_first_task(made):
    found = overview.row(made["moitie"])
    assert found.tasks[0] == Task(3, "Sigles à valider : {n}", "glossary")
    assert found.first_page() == ("glossary", None)


def test_the_plan(made):
    found = overview.row(made["plan"])
    assert (found.hypotheses, found.frozen, found.amendments) == (5, "2026-10-18", 1)
    assert overview.plan_text(overview.ProjectRow(Path("x.dd.json"), None, frozen="2026-10-18")) \
        == "figé le 2026-10-18"  # fmt: skip
    assert overview.plan_text(overview.ProjectRow(Path("x.dd.json"), None, hypotheses=2)) \
        == "en cours (2 hypothèses)"  # fmt: skip


def test_the_notebook_of_another_project_or_unreadable(made, tmp_path):
    folder = tmp_path / "copie"
    shutil.copytree(made["carnet"].parent, folder)
    path = folder / made["carnet"].name
    notebook = nb.notebook_path(path)
    other = nb.load_notebook(notebook)
    other.project.source_sha256 = "0" * 64
    notebook.write_text(nb.dumps(other), encoding="utf-8", newline="\n")
    assert overview.notebook_text(overview.row(path)) == "carnet d'un autre projet"
    notebook.write_text("{", encoding="utf-8")
    found = overview.row(path)
    assert overview.notebook_text(found) == "carnet illisible"
    assert overview.phase_text(found) == "Analyser"  # written with a first analysis


def test_where_a_click_opens_the_project():
    path = Path("etude.dd.json")
    assert overview.ProjectRow(path, None, phase="Documenter").first_page() == ("base", None)
    assert overview.ProjectRow(path, None, phase="Analyser").first_page() == ("plan", None)
    assert overview.ProjectRow(path, None, phase="Rédiger").first_page() == ("method", None)
    waiting = (Task(2, "Rattachements proposés à réviser : {n}", "variables", "to_review"),)
    assert overview.ProjectRow(path, None, phase="Rédiger", tasks=waiting).first_page() == (
        "variables", "to_review"
    )  # fmt: skip


# --- Never the database; never an error; nothing written. ---


def test_the_database_is_never_opened(made, tmp_path, monkeypatch):
    folder = tmp_path / "copie"
    shutil.copytree(made["carnet"].parent, folder)
    path = folder / made["carnet"].name
    before = overview.row(path)
    (folder / stages.ANALYSES).write_bytes(b"\x00 pas une base \xff")
    overview.clear_cache()

    def opened(*args, **kwargs):
        raise AssertionError("the database was opened")

    import ddict.analysis.data
    import ddict.io

    monkeypatch.setattr(ddict.io, "read_database", opened)
    monkeypatch.setattr(ddict.analysis.data, "file_sha256", opened)
    after = overview.row(path)
    assert after == before


def test_nothing_is_written(made):
    root = made["neuf"].parents[1]
    before = {p: p.stat().st_mtime_ns for p in root.rglob("*")}
    recents.clear()
    overview.rows(list(made.values()))
    assert {p: p.stat().st_mtime_ns for p in root.rglob("*")} == before
    assert recents.load() == []


def test_sorted_by_the_latest_change(made):
    found = overview.rows(list(made.values()))
    assert found[-1].problem == "missing"
    dates = [r.modified for r in found[:-1]]
    assert dates == sorted(dates, reverse=True)


# --- The cache. ---


@pytest.fixture
def counted(monkeypatch):
    calls = []
    real = overview.load_project

    def load(path):
        calls.append(Path(path).name)
        return real(path)

    monkeypatch.setattr(overview, "load_project", load)
    return calls


def test_an_unchanged_file_is_not_read_again(made, counted):
    overview.row(made["carnet"])
    overview.row(made["carnet"])
    overview.rows([made["carnet"], made["neuf"]])
    assert len(counted) == 2


def test_read_again_after_a_save(made, tmp_path, counted):
    folder = tmp_path / "copie"
    shutil.copytree(made["neuf"].parent, folder)
    path = folder / made["neuf"].name
    assert overview.row(path).hypotheses == 0
    project = load_project(path)
    project.dataset.unit_of_observation = "participant"
    save_project(project, path)
    overview.row(path)
    assert len(counted) == 2
    # The notebook, the draft and its report are watched too.
    nb.save_notebook(nb.new_notebook(project, path), nb.notebook_path(path))
    assert overview.notebook_text(overview.row(path)) == "0 retenues"
    draft = path.with_name("etude-sommeil-article.docx")
    draft.write_bytes(b"PK")
    assert overview.phase_text(overview.row(path)) == "Rédiger"
    assert len(counted) == 4
    # A date touched without change: read again, nothing more.
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    assert overview.phase_text(overview.row(path)) == "Rédiger"
    assert len(counted) == 5


def test_the_database_removed_is_seen_at_once(made, tmp_path, counted):
    folder = tmp_path / "copie"
    shutil.copytree(made["neuf"].parent, folder)
    path = folder / made["neuf"].name
    assert overview.row(path).base is True
    (folder / stages.SLEEP).unlink()
    assert overview.row(path).base is False
    assert len(counted) == 1


def test_another_language_reads_again(made, counted):
    overview.row(made["neuf"])
    i18n.set_language("en")
    found = overview.row(made["neuf"])
    assert overview.waiting_text(found) == "4 · Add the study questionnaire"
    assert len(counted) == 2


def test_thirty_projects_in_less_than_two_seconds(made, tmp_path):
    paths = []
    for index in range(30):
        folder = tmp_path / f"Étude {index:02d}"
        shutil.copytree(made["carnet"].parent, folder)
        paths.append(folder / made["carnet"].name)
    start = time.perf_counter()
    first = overview.rows(paths)
    took = time.perf_counter() - start
    assert len(first) == 30 and took < 2, took
    start = time.perf_counter()
    assert overview.rows(paths) == first
    assert time.perf_counter() - start < took / 5


# --- The detail of a project (plan-accueil, step C3, D-160). ---


def test_the_questionnaire(made, tmp_path):
    moitie, concu = overview.row(made["moitie"]), overview.row(made["concu"])
    assert overview.row(made["neuf"]).questionnaire is None
    assert (moitie.questionnaire, moitie.designed) == ("questionnaire-sommeil.pdf", False)
    assert moitie.questionnaire_found is False  # stages: never copied next to the project
    assert concu.designed and concu.questionnaire and concu.questionnaire_found is None
    folder = tmp_path / "copie"
    shutil.copytree(made["moitie"].parent, folder)
    shutil.copy(stages.EXAMPLES / "questionnaire-sommeil.pdf", folder)
    assert overview.row(folder / made["moitie"].name).questionnaire_found is True


def test_the_files_produced_next_to_the_project(made, tmp_path):
    folder = tmp_path / "Études 2026" / "Équipe"
    shutil.copytree(made["carnet"].parent, folder)
    path = folder / made["carnet"].name
    for name in (
        "etude-analyses.xlsx", "etude-analyses-travail.md", "etude-analyses-analyse-2.docx",
        "etude-analyses-analyse-12-graphiques.xlsx", "etude-analyses-article.docx",
        "etude-analyses-article-verification.md", "etude-analyses-depot.zip",
        "etude-analyses-metadonnees.R", "etude-analyses-documente.sav",
        "etude-analyses-notes.docx",  # the team's: not the tool's
        "etude-analyses-analyse-x.docx",  # not a number
        "etude-analyses.xlsx.tmp",  # an interrupted save
        "autre-etude.xlsx",
    ):  # fmt: skip
        (folder / name).write_bytes(b"x")
    (folder / "etude-analyses.dd-envois").mkdir()
    assert overview.produced(overview.row(path)) == [
        "etude-analyses-analyse-12-graphiques.xlsx", "etude-analyses-analyse-2.docx",
        "etude-analyses-article-verification.md", "etude-analyses-article.docx",
        "etude-analyses-carnet.json", "etude-analyses-depot.zip",
        "etude-analyses-documente.sav", "etude-analyses-metadonnees.R",
        "etude-analyses-travail.md", "etude-analyses.dd-envois\\", "etude-analyses.xlsx",
    ]  # fmt: skip


def test_no_file_produced_for_a_folder_gone(made):
    assert overview.produced(overview.row(made["introuvable"])) == []
    assert overview.produced(overview.ProjectRow(Path("Z:/absent/etude.dd.json"), None)) == []
