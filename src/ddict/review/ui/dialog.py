"""The system's "Open" window, to choose a file without typing its path (v0.3, D-020).

It opens on this computer, where the interface runs. It runs in a process of its own:
tkinter must own its thread, which a Streamlit script does not. The process prints the
chosen path, or nothing when the person cancels.

Run as: python -m ddict.review.ui.dialog database|project|questionnaire
"""

from __future__ import annotations

import subprocess
import sys

KINDS = {
    "database": (
        "Choisir la base de données",
        [
            ("Bases de données", "*.sav *.zsav *.csv *.dta *.sas7bdat *.xlsx"),
            ("Tous les fichiers", "*.*"),
        ],
    ),
    "project": (
        "Choisir un fichier projet",
        [("Fichiers projet", "*.dd.json"), ("Tous les fichiers", "*.*")],
    ),
    "questionnaire": (
        "Choisir le questionnaire",
        [("Questionnaires", "*.pdf *.txt"), ("Tous les fichiers", "*.*")],
    ),
}
TIMEOUT = 600  # seconds: a person may take a while to find the file


def choose(kind: str) -> str | None:
    """Open the window and return the chosen path, or None (cancelled or impossible)."""
    if kind not in KINDS:
        raise ValueError(kind)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ddict.review.ui.dialog", kind],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = result.stdout.strip()
    return path or None


def _open_window(kind: str) -> str:
    import tkinter
    from tkinter import filedialog

    title, types = KINDS[kind]
    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # in front of the browser, not behind it
    try:
        return filedialog.askopenfilename(parent=root, title=title, filetypes=types) or ""
    finally:
        root.destroy()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(_open_window(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] in KINDS else "")
