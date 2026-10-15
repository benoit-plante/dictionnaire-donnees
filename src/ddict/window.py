"""The interface in its own window, without a console (v0.7.1, D-055).

The icon starts `ddict-fenetre` (a GUI script: no console window). It starts the local
interface unseen, shows it in a window of its own (pywebview, on the Edge engine already in
Windows) and stops everything when the window is closed. Messages that a console would have
shown go to a journal next to the recent projects (`journal.txt`), rewritten at each start.

Without pywebview, or when the window cannot open, the interface opens in the browser, as
`ddict` does; the "Quit the tool" button of the interface then stops it.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any

from ddict import settings
from ddict.cli import REVIEW_HOST, _port_open, _wait_for_port, review_command
from ddict.i18n import _
from ddict.recents import config_dir

DEFAULT_PORT = 8501
JOURNAL = "journal.txt"


def journal_path() -> Path:
    return config_dir() / JOURNAL


def _open_journal():
    """The journal, or nowhere when it cannot be written: it is a convenience."""
    path = journal_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("w", encoding="utf-8", newline="\n", buffering=1)
    except OSError:
        return io.StringIO()


def _load_gui() -> Any | None:
    try:
        import webview
    except ImportError:
        return None
    return webview


def start_server(port: int, log) -> subprocess.Popen:
    """The local interface, unseen: no console window of its own."""
    command, env = review_command(None, port)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(command, env=env, stdout=log, stderr=log, creationflags=flags)


def stop_server(server: subprocess.Popen | None) -> None:
    if server is None or server.poll() is not None:
        return
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()


def _close_with(server: subprocess.Popen, window) -> None:
    """Close the window when the server ends ("Quit the tool"); it may be closed already."""
    server.wait()
    with contextlib.suppress(Exception):
        window.destroy()


def run(
    port: int = DEFAULT_PORT,
    *,
    gui: Any | None = None,
    start=start_server,
    opener=webbrowser.open,
    log=None,
) -> int:
    """Show the interface in a window; return when it is closed, the server stopped."""
    settings.apply()
    log = log or sys.stdout
    url = f"http://{REVIEW_HOST}:{port}"
    server = None
    if _port_open(REVIEW_HOST, port):
        # Already open (started from the icon or from `ddict`): one more window on it, which
        # leaves it running when closed.
        print(_("L'outil est déjà ouvert : une fenêtre de plus s'ouvre sur lui."), file=log)
    else:
        server = start(port, log)
        if not _wait_for_port(REVIEW_HOST, port, server):
            print(_("L'interface n'a pas démarré : voir les messages ci-dessus."), file=log)
            stop_server(server)
            return 1
    print(_("Interface sur {url} (cet ordinateur seulement).").format(url=url), file=log)
    if gui is not None:
        try:
            window = gui.create_window(
                _("Dictionnaire de données"), url, width=1400, height=900, min_size=(900, 600)
            )
            if server is not None:
                # The "Quit the tool" button stops the server: the window follows.
                threading.Thread(target=_close_with, args=(server, window), daemon=True).start()
            gui.settings["ALLOW_DOWNLOADS"] = True
            gui.start()
        except Exception as error:  # any failure of the window: the browser
            print(_("Fenêtre impossible ({error}) : ouverture dans le navigateur.").format(
                error=error), file=log)  # fmt: skip
        else:
            print(_("Fenêtre fermée : arrêt de l'outil."), file=log)
            stop_server(server)
            return 0
    opener(url)
    if server is not None:
        server.wait()  # until "Quit the tool"
    return 0


def main() -> int:
    log = _open_journal()
    sys.stdout = sys.stderr = log  # a GUI script has no console
    with contextlib.closing(log):
        return run(gui=_load_gui(), log=log)


if __name__ == "__main__":
    sys.exit(main())
