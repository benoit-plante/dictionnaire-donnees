"""Where each followed project is, for the home page's table and `ddict projets lister`
(v0.17, § 7 of plan-v0.17).

A row reads the project file and its notebook, never the database: whether the database
is there is said from its name only. Nothing is written, nothing is added to the recent
projects, and no error comes out: a project not found, unreadable or written by a newer
tool gives a row that says so. Rows are kept in memory while the files they were read
from keep their date and size.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from ddict import i18n
from ddict.analysis import notebook as nb
from ddict.analysis.notebook_export import SUFFIX
from ddict.analysis.verify import paths as report_paths
from ddict.i18n import N_, _
from ddict.project import fingerprint, load_project, ondisk
from ddict.project.model import Project
from ddict.project.store import ProjectError, ProjectNewer
from ddict.review import logic
from ddict.review.navigation import SECTIONS
from ddict.workflow import Task, project_stem, tasks

# The phase (D-133): how far the project went, from the files the tool wrote. The names
# are those of the interface's sections; the first page of each opens a project with
# nothing waiting.
DOCUMENT, ANALYSE, WRITE = N_("Documenter"), N_("Analyser"), N_("Rédiger")
PHASES = (DOCUMENT, ANALYSE, WRITE)


@dataclass(frozen=True)
class ProjectRow:
    path: Path
    modified: float | None  # the latest of the project's and the notebook's dates
    problem: str | None = None  # "missing", "unreadable" or "newer"; the rest is then empty
    version: str | None = None  # the format of a project written by a newer tool
    phase: str | None = None
    codebook: float | None = None  # 0 to 1, as the sidebar's bar
    tasks: tuple[Task, ...] = ()
    hypotheses: int = 0
    frozen: str | None = None  # the date the plan was frozen
    amendments: int = 0
    notebook: str | None = None  # None (no notebook), "found", "unreadable" or "other"
    retained: int = 0
    to_confirm: int = 0
    to_recompute: int = 0
    source: str | None = None  # the database's file name
    base: bool | None = None  # a file of that name next to the project

    @property
    def name(self) -> str:
        return project_stem(self.path)

    @property
    def folder(self) -> str:
        return str(self.path.parent)

    def first_page(self) -> tuple[str, str | None]:
        """Where a click opens the project: its first task, else the first page of its
        phase."""
        if self.tasks:
            return self.tasks[0].mode, self.tasks[0].filter
        return SECTIONS[self.phase or DOCUMENT][0].mode, None


# --- Reading a row. ---


def _stat(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


def _files(path: Path) -> tuple[Path, Path, Path, Path]:
    """The project, its notebook, the article's draft and its check report: what a row is
    read from (the last two say the phase and a task)."""
    draft = path.with_name(project_stem(path) + SUFFIX + ".docx")
    return path, nb.notebook_path(path), draft, report_paths(draft)["md"]


def _modified(*stats: tuple[int, int] | None) -> float | None:
    found = [s[0] / 1e9 for s in stats if s is not None]
    return max(found) if found else None


def _notebook(row: dict, project: Project, path: Path) -> int:
    """The notebook's counts into `row`; returns its number of analyses (for the phase). A
    notebook that cannot be read counts as one: the tool writes it with a first analysis."""
    if not path.is_file():
        return 0
    try:
        notebook = nb.load_notebook(path)
    except nb.NotebookError:
        row["notebook"] = "unreadable"
        return 1
    if not nb.belongs(notebook, project):
        row["notebook"] = "other"
        return 1
    current = fingerprint.fingerprint(project)
    kept = [e for e in notebook.entries if e.retained and e.superseded is None]
    parts = [(e.computed, e.pending) for e in kept]
    if notebook.method.computed is not None:
        parts.append((notebook.method.computed, notebook.method.pending))
    row.update(
        notebook="found",
        retained=len(kept),
        to_confirm=sum(1 for _c, pending in parts if pending is not None),
        to_recompute=sum(
            1 for computed, pending in parts if pending is None and computed.fingerprint != current
        ),
    )
    return len(notebook.entries)


def _read(path: Path, stats: list) -> ProjectRow:
    try:
        project = load_project(path)
    except ProjectNewer as error:
        return ProjectRow(path, _modified(stats[0]), "newer", version=error.version)
    except ProjectError:
        return ProjectRow(path, _modified(stats[0]), "unreadable")
    files = _files(path)
    row: dict = {}
    analyses = _notebook(row, project, files[1])
    plan = project.plan
    if files[2].is_file():
        phase = WRITE
    elif plan.hypotheses or analyses:
        phase = ANALYSE
    else:
        phase = DOCUMENT
    return ProjectRow(
        path,
        _modified(stats[0], stats[1]),
        phase=phase,
        codebook=logic.codebook_progress(project),
        tasks=tuple(tasks(project, path)),
        hypotheses=len(plan.hypotheses),
        frozen=plan.frozen.date[:10] if plan.frozen else None,
        amendments=len(plan.amendments) if plan.frozen else 0,
        source=project.source.name,
        **row,
    )


_CACHE: dict[tuple[str, str], tuple[tuple, ProjectRow]] = {}
_LOCK = threading.Lock()


def row(path: Path | str) -> ProjectRow:
    """The row of one project; read again only when one of its files changed (date or
    size), or in another language (the tasks' texts are in it)."""
    path = Path(path)
    stats = [_stat(p) for p in _files(path)]
    if stats[0] is None and not path.is_file():
        return ProjectRow(path, None, "missing")
    key = (ondisk.key(path), i18n.language())
    with _LOCK:
        cached = _CACHE.get(key)
    if cached is not None and cached[0] == tuple(stats):
        found = cached[1]
    else:
        found = _read(path, stats)
        with _LOCK:
            _CACHE[key] = (tuple(stats), found)
    if found.source is None:
        return found
    # Looked at each time, never opened: the tool checks it is the right database when the
    # project is opened.
    return replace(found, base=path.with_name(found.source).is_file())


def rows(paths: list[Path]) -> list[ProjectRow]:
    """The rows of these projects, the latest changed first; those without a date last."""
    found = [row(p) for p in paths]
    return sorted(found, key=lambda r: (r.modified is None, -(r.modified or 0), r.name.casefold()))


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()


# --- The row as text: the table's cells and `ddict projets lister`. ---


def phase_text(row: ProjectRow) -> str:
    return _(row.phase) if row.phase else "—"


def codebook_text(row: ProjectRow) -> str:
    return "—" if row.codebook is None else f"{round(100 * row.codebook)} %"


def waiting_text(row: ProjectRow) -> str:
    if row.problem == "missing":
        return _("Introuvable : le fichier n'est plus à cet endroit.")
    if row.problem == "newer":
        return _(
            "Écrit par une version plus récente de l'outil (format {version}) : mettez "
            "l'outil à jour."
        ).format(version=row.version)
    if row.problem == "unreadable":
        return _("Fichier projet illisible.")
    if not row.tasks:
        return "—"
    first = row.tasks[0]
    return f"{len(row.tasks)} · {first.text.format(n=first.count)}"


def plan_text(row: ProjectRow) -> str:
    if row.frozen and row.amendments == 1:
        return _("figé, 1 amendement")
    if row.frozen and row.amendments:
        return _("figé, {n} amendements").format(n=row.amendments)
    if row.frozen:
        return _("figé le {date}").format(date=row.frozen)
    if row.hypotheses == 1:
        return _("en cours (1 hypothèse)")
    if row.hypotheses:
        return _("en cours ({n} hypothèses)").format(n=row.hypotheses)
    return "—"


def notebook_text(row: ProjectRow) -> str:
    if row.notebook == "unreadable":
        return _("carnet illisible")
    if row.notebook == "other":
        return _("carnet d'un autre projet")
    if row.notebook is None:
        return "—"
    parts = [_("1 retenue") if row.retained == 1 else _("{n} retenues").format(n=row.retained)]
    if row.to_confirm:
        parts.append(_("{n} à confirmer").format(n=row.to_confirm))
    if row.to_recompute:
        parts.append(_("{n} à recalculer").format(n=row.to_recompute))
    return " · ".join(parts)


def base_text(row: ProjectRow) -> str:
    if row.base is None:
        return "—"
    return _("trouvée") if row.base else _("introuvable")


def modified_text(row: ProjectRow) -> str:
    if row.modified is None:
        return "—"
    return datetime.fromtimestamp(row.modified).strftime("%Y-%m-%d %H:%M")
