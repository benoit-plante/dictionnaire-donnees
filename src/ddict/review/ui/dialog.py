"""The system's "Open" window, to choose a file without typing its path (v0.3, D-020).

It opens on this computer, where the interface runs. It runs in a process of its own:
tkinter must own its thread, which a Streamlit script does not. The process prints the
chosen path, or nothing when the person cancels.

Run as: python -m ddict.review.ui.dialog database|project|questionnaire|reference|folder
(v0.17: "folder", the "Choose a folder" window, to look for projects in it)
"""

from __future__ import annotations

import subprocess
import sys

from ddict import settings
from ddict.i18n import N_, _

KINDS = {
    "database": (
        N_("Choisir la base de données"),
        [
            (N_("Bases de données"), "*.sav *.zsav *.csv *.dta *.sas7bdat *.xlsx"),
            (N_("Tous les fichiers"), "*.*"),
        ],
    ),
    "project": (
        N_("Choisir un fichier projet"),
        [(N_("Fichiers projet"), "*.dd.json"), (N_("Tous les fichiers"), "*.*")],
    ),
    "questionnaire": (
        N_("Choisir le questionnaire"),
        [(N_("Questionnaires"), "*.pdf *.txt *.xlsx *.lss"), (N_("Tous les fichiers"), "*.*")],
    ),
    "limesurvey": (  # v0.20: a structure re-exported from LimeSurvey
        N_("Choisir la structure réexportée de LimeSurvey"),
        [(N_("Structures LimeSurvey"), "*.lss *.txt"), (N_("Tous les fichiers"), "*.*")],
    ),
    "manuscript": (
        N_("Choisir le manuscrit"),
        [(N_("Documents Word"), "*.docx"), (N_("Tous les fichiers"), "*.*")],
    ),
    "reference": (
        N_("Choisir la vague précédente"),
        [
            (N_("Projet, copie documentée ou table de noms"), "*.dd.json *.sav *.csv"),
            (N_("Tous les fichiers"), "*.*"),
        ],
    ),
}
FOLDER = "folder"
FOLDER_TITLE = N_("Choisir le dossier où chercher les projets")
TIMEOUT = 600  # seconds: a person may take a while to find the file


def choose(kind: str) -> str | None:
    """Open the window and return the chosen path, or None (cancelled or impossible)."""
    if kind not in KINDS and kind != FOLDER:
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

    settings.apply()  # the language of this computer (v0.5)
    if kind == FOLDER:
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            return filedialog.askdirectory(parent=root, title=_(FOLDER_TITLE), mustexist=True)
        finally:
            root.destroy()
    title, types = KINDS[kind]
    title = _(title)
    types = [(_(name), pattern) for name, pattern in types]
    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # in front of the browser, not behind it
    try:
        return filedialog.askopenfilename(parent=root, title=title, filetypes=types) or ""
    finally:
        root.destroy()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    known = len(sys.argv) > 1 and (sys.argv[1] in KINDS or sys.argv[1] == FOLDER)
    print(_open_window(sys.argv[1]) if known else "")
