"""Steps of the workflow shared by the command line and the interface (v0.3)."""

from __future__ import annotations

from pathlib import Path

from ddict.export.wording import anomalies
from ddict.i18n import _
from ddict.io import read_database
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import PROJECT_SUFFIX, build_project, save_project
from ddict.project.model import Project


class ProjectExists(FileExistsError):
    """A project file is already there: replacing it would lose the decisions it holds."""


def default_project_path(database: Path) -> Path:
    return database.with_name(database.stem + PROJECT_SUFFIX)


def profile_database(
    database: Path | str,
    output: Path | str | None = None,
    *,
    replace: bool = False,
    min_cell_count: int = MIN_CELL_COUNT,
) -> tuple[Project, Path]:
    """Read a database and write its project file, next to it unless `output` is given."""
    database = Path(database)
    output = Path(output) if output else default_project_path(database)
    if output.exists() and not replace:
        raise ProjectExists(output)
    project = build_project(read_database(database), min_cell_count=min_cell_count)
    save_project(project, output)
    return project, output


def profile_summary(project: Project) -> str:
    """One line: "34 variables, 200 lignes ; 4 variables sensibles ; 10 avec signalements"."""
    sensitive = sum(
        1 for e in project.variables if (e.privacy.privacy_class.value or "ordinary") != "ordinary"
    )
    # The same count as the "Avec signalements" filter of the review (notes excluded).
    flagged = sum(1 for e in project.variables if anomalies(e.profile))
    return _(
        "{n} variables, {rows} lignes ; {sensitive} variables sensibles ; "
        "{flagged} avec signalements."
    ).format(
        n=len(project.variables),
        rows=project.source.n_rows,
        sensitive=sensitive,
        flagged=flagged,
    )
