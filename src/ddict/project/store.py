"""Save and load project files (*.dd.json), byte for byte reproducibly."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from ddict.io.model import LoadedData
from ddict.project.model import SCHEMA_VERSION, Project

PROJECT_SUFFIX = ".dd.json"


class ProjectError(Exception):
    """The project file cannot be read."""


def dumps(project: Project) -> str:
    """Keys in model order, indent 2, UTF-8 characters kept, final newline."""
    data = project.model_dump(mode="json")
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def save_project(project: Project, path: Path | str) -> None:
    """Write through a temporary file, so that an interrupted save never truncates a project."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(dumps(project))
    temporary.replace(path)


def load_project(path: Path | str) -> Project:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProjectError(f"Cannot read {path.name}: {error}") from error
    version = data.get("schema_version") if isinstance(data, dict) else None
    if not isinstance(version, str) or version.split(".")[0] != SCHEMA_VERSION.split(".")[0]:
        raise ProjectError(f"{path.name}: unsupported schema version {version!r}")
    try:
        return Project.model_validate(data)
    except ValidationError as error:
        raise ProjectError(f"{path.name} is not a valid project file: {error}") from error


def source_differences(project: Project, data: LoadedData) -> list[str]:
    """What changed between the database of the project and the one opened now.

    An empty list means the same file (same SHA-256). Otherwise, short codes:
    "content", "rows", "columns", "variables".
    """
    source = data.source
    if source.sha256 == project.source.sha256:
        return []
    differences = ["content"]
    if source.n_rows != project.source.n_rows:
        differences.append("rows")
    if source.n_columns != project.source.n_columns:
        differences.append("columns")
    if [v.name for v in data.variables] != [e.name for e in project.variables]:
        differences.append("variables")
    return differences
