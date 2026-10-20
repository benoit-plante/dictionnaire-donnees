"""Screenshots of every page of the interface (v0.16, D-127), for a look at the layout after
a change: the fictional sleep study, at 1400x900 (the window of the icon) and 900x600
(its smallest size).

Since v0.20, the pages of "Concevoir" too, on the fictional designed questionnaire of the
tests (`tests/projet_concu.py`): `1400x900\\design-01-design.png`...

A development tool, outside `pytest`: it starts the tool on this computer (127.0.0.1) and
drives the Microsoft Edge already installed, through Playwright; no browser is downloaded,
and nothing leaves this computer. Fictional data only: the study is copied into a
temporary folder. Each picture shows what one sees on arriving on the page (Streamlit scrolls
inside its main area), not its whole length.

Run: uv run python scripts/captures.py [--dossier C:\\chemin\\captures]
The pictures land in the folder given, by default `%TEMP%\\ddict-captures`, one subfolder per
size: `1400x900\\03-glossary.png`...
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ddict.analysis import notebook as nb  # noqa: E402
from ddict.cli import main as ddict  # noqa: E402
from ddict.cli import review_command  # noqa: E402
from ddict.project import load_project, save_project  # noqa: E402
from ddict.review.navigation import DESIGN, PAGES  # noqa: E402
from ddict.workflow import add_questionnaire, profile_database  # noqa: E402

EXAMPLES = ROOT / "exemples" / "bases-fictives"
SIZES = ((1400, 900), (900, 600))
PORT = 8531
HOST = "127.0.0.1"


def study(folder: Path) -> Path:
    """The sleep study with its questionnaire and one analysis in the notebook, so that
    the pages of the notebook, the Method and the dashboard have something to show."""
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(EXAMPLES / name, folder / name)
    project, path = profile_database(folder / "etude-sommeil.sav")
    add_questionnaire(project, folder / "questionnaire-sommeil.pdf")
    save_project(project, path)
    ddict(["carnet", "ajouter", str(path), "correlation", "--variables", "heures_sommeil",
           "nb_reveils"])  # fmt: skip
    assert nb.notebook_path(path).is_file() and load_project(path).questionnaire
    return path


def start(project: Path, config: Path) -> subprocess.Popen:
    command, env = review_command(project, PORT)
    env = {**env, "DDICT_CONFIG_DIR": str(config)}
    server = subprocess.Popen(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            with urllib.request.urlopen(f"http://{HOST}:{PORT}/_stcore/health", timeout=1):
                return server
        except OSError:
            time.sleep(0.5)
    server.terminate()
    raise SystemExit("L'outil n'a pas démarré.")


def settled(page: Page) -> None:
    """Wait until Streamlit has drawn the page: its main area, then no more running."""
    page.wait_for_selector('[data-testid="stMain"] h1, [data-testid="stMain"] h2', timeout=60000)
    page.wait_for_function(
        "!document.querySelector('[data-testid=\"stStatusWidget\"] button')", timeout=60000
    )
    page.wait_for_timeout(1500)


def designed(folder: Path) -> Path:
    """The fictional questionnaire designed in the tool, before its collection (v0.20)."""
    sys.path.insert(0, str(ROOT / "tests"))
    from projet_concu import project

    path = folder / "Étude conçue.dd.json"
    save_project(project(), path)
    return path


def shoot(out: Path, modes, prefix: str = "") -> list[Path]:
    taken = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge")
        for width, height in SIZES:
            folder = out / f"{width}x{height}"
            folder.mkdir(parents=True, exist_ok=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            for rank, mode in enumerate(modes, start=1):
                page.goto(f"http://{HOST}:{PORT}/{mode}")
                settled(page)
                target = folder / f"{prefix}{rank:02d}-{mode}.png"
                page.screenshot(path=str(target), full_page=True)
                taken.append(target)
            page.close()
        browser.close()
    return taken


def run(out: Path) -> list[Path]:
    work = Path(tempfile.mkdtemp(prefix="ddict-captures-"))
    taken = []
    try:
        design = work / "conception"
        design.mkdir()
        for project, modes, prefix in (
            (study(work), [m for m in PAGES if m not in {p.mode for p in DESIGN}], ""),
            (designed(design), [p.mode for p in DESIGN], "design-"),
        ):
            server = start(project, work / "config")
            try:
                taken += shoot(out, modes, prefix)
            finally:
                server.terminate()
                server.wait(timeout=30)
        return taken
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default = Path(os.environ.get("TEMP", tempfile.gettempdir())) / "ddict-captures"
    parser.add_argument("--dossier", type=Path, default=default)
    folder = parser.parse_args().dossier
    pictures = run(folder)
    print(f"{len(pictures)} captures dans {folder}")
