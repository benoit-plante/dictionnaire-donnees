"""What a file was on the disk when the tool read it, so that a save never overwrites what
someone else wrote in between (v0.17, D-129).

The project and the notebook remember the SHA-256 of the bytes they were read from, in
memory only (never in the file). Before writing, the file is read again: if its content
changed, or it is gone, nothing is written. The date and the size only say whether reading
again is worth it: OneDrive may touch the date without changing a byte, and a change may
keep the size ("validated" and "corrected" have the same length).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Reason = Literal["changed", "missing", "exists"]


class FileChanged(Exception):
    """The file is not what the tool read: changed or removed since, or (for a new one)
    already there. Nothing was written."""

    def __init__(self, path: Path, reason: Reason) -> None:
        super().__init__(f"{path.name}: {reason}")
        self.path = path
        self.reason = reason


@dataclass(frozen=True)
class DiskState:
    key: str  # the path, as compared (`key`)
    sha256: str
    mtime_ns: int
    size: int


def key(path: Path | str) -> str:
    """The path as compared: absolute, without case. Never `resolve()`, which may turn a
    network drive (Z:) into its \\\\server\\share path."""
    return os.path.normcase(str(Path(path).absolute()))


def _state(path: Path, content: bytes, stat: os.stat_result) -> DiskState:
    return DiskState(key(path), hashlib.sha256(content).hexdigest(), stat.st_mtime_ns, len(content))


def read(path: Path) -> tuple[bytes, DiskState]:
    """The file's bytes, and what to remember of them. Raises OSError."""
    with path.open("rb") as stream:
        stat = os.fstat(stream.fileno())
        content = stream.read()
    return content, _state(path, content, stat)


def remembered(document) -> DiskState | None:
    return getattr(document, "_disk", None)


def remember(document, state: DiskState | None) -> None:
    document._disk = state


def check(path: Path, known: DiskState | None, *, overwrite: bool = False) -> None:
    """Raise FileChanged when writing to `path` would overwrite what the tool did not read.

    Known (read from this path): the file must still have the same content. Not known (a
    new document, or one read elsewhere): the file must not exist, unless `overwrite`."""
    if known is None or known.key != key(path):
        if path.exists() and not overwrite:
            raise FileChanged(path, "exists")
        return
    try:
        content, _ = read(path)
    except FileNotFoundError as error:
        raise FileChanged(path, "missing") from error
    if hashlib.sha256(content).hexdigest() != known.sha256:
        raise FileChanged(path, "changed")


def unchanged(path: Path, known: DiskState) -> bool:
    """Whether the file still holds what was read: by the date and size first (no reading),
    then by the content when they moved."""
    try:
        stat = path.stat()
    except OSError:
        return False
    if (stat.st_mtime_ns, stat.st_size) == (known.mtime_ns, known.size):
        return True
    try:
        content, _ = read(path)
    except OSError:
        return False
    return hashlib.sha256(content).hexdigest() == known.sha256


def write(document, text: str, path: Path, *, overwrite: bool = False) -> None:
    """Check, then write through a temporary file, so that an interrupted save never
    truncates the file; the document then remembers what was written."""
    check(path, remembered(document), overwrite=overwrite)
    content = text.encode("utf-8")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(content)
    temporary.replace(path)
    remember(document, _state(path, content, path.stat()))
