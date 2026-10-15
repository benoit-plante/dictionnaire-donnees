"""v0.7.1: the interface in its own window, without a console, and "Quit the tool" (D-055).

The window and the server are fakes: no display, no process, no network.
"""

import io
import threading
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import recents, window
from ddict.review import shutdown

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


class FakeServer:
    def __init__(self):
        self.ended = threading.Event()
        self.terminated = False

    def poll(self):
        return 0 if self.ended.is_set() else None

    def wait(self, timeout=None):
        self.ended.wait(timeout)
        return 0

    def terminate(self):
        self.terminated = True
        self.ended.set()

    def kill(self):
        self.terminate()


class FakeWindow:
    def __init__(self):
        self.destroyed = threading.Event()

    def destroy(self):
        self.destroyed.set()


class FakeGui:
    """pywebview's surface used by the tool; `start` returns when the window closes."""

    def __init__(self, on_start=None, fails=False):
        self.settings = {}
        self.windows = []
        self.on_start = on_start
        self.fails = fails

    def create_window(self, title, url, **options):
        self.windows.append((title, url))
        self.window = FakeWindow()
        return self.window

    def start(self):
        if self.fails:
            raise RuntimeError("no WebView2")
        if self.on_start:
            self.on_start(self)


@pytest.fixture
def server_up(monkeypatch):
    """A port closed until the fake server starts, then answering."""
    monkeypatch.setattr(window, "_port_open", lambda host, port: False)
    monkeypatch.setattr(window, "_wait_for_port", lambda host, port, process: True)
    started = []

    def start(port, log):
        started.append(FakeServer())
        return started[-1]

    return start, started


def test_closing_the_window_stops_the_tool(server_up):
    start, started = server_up
    gui = FakeGui()  # the person closes the window at once
    opened = []
    assert window.run(8599, gui=gui, start=start, opener=opened.append, log=io.StringIO()) == 0
    assert gui.windows == [("Dictionnaire de données", "http://127.0.0.1:8599")]
    assert gui.settings["ALLOW_DOWNLOADS"] is True
    assert started[0].terminated
    assert opened == []  # no browser


def test_quit_closes_the_window(server_up):
    start, started = server_up

    def quit_from_the_page(gui):
        started[0].ended.set()  # "Quit the tool": the server ends by itself
        assert gui.window.destroyed.wait(5)

    gui = FakeGui(on_start=quit_from_the_page)
    assert window.run(8599, gui=gui, start=start, log=io.StringIO()) == 0


def test_without_a_window_the_browser(server_up):
    start, started = server_up
    log, opened = io.StringIO(), []

    def opener(url):
        opened.append(url)
        started[-1].ended.set()  # then "Quit the tool"

    assert window.run(8599, gui=FakeGui(fails=True), start=start, opener=opener, log=log) == 0
    assert opened == ["http://127.0.0.1:8599"]
    assert "navigateur" in log.getvalue()
    # pywebview missing altogether: the same.
    opened.clear()
    assert window.run(8599, gui=None, start=start, opener=opener, log=log) == 0
    assert opened == ["http://127.0.0.1:8599"]


def test_already_open_one_more_window_that_leaves_it_running(monkeypatch):
    monkeypatch.setattr(window, "_port_open", lambda host, port: True)
    gui, log = FakeGui(), io.StringIO()
    assert window.run(8599, gui=gui, start=pytest.fail, log=log) == 0
    assert len(gui.windows) == 1
    assert "déjà ouvert" in log.getvalue()


def test_a_server_that_does_not_start(monkeypatch):
    monkeypatch.setattr(window, "_port_open", lambda host, port: False)
    monkeypatch.setattr(window, "_wait_for_port", lambda host, port, process: False)
    server, gui = FakeServer(), FakeGui()
    assert window.run(8599, gui=gui, start=lambda p, log: server, log=io.StringIO()) == 1
    assert gui.windows == [] and server.terminated


def test_the_journal_is_next_to_the_recent_projects():
    assert window.journal_path() == recents.config_dir() / "journal.txt"


def test_a_gui_script_without_console():
    text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert '[project.gui-scripts]\nddict-fenetre = "ddict.window:main"' in text


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize("project", [False, True])
def test_quit_the_tool(monkeypatch, fictional_files, tmp_path, project):
    stopped = []
    monkeypatch.setattr(shutdown, "stop_soon", lambda: stopped.append(True))
    test = AppTest.from_file(APP, default_timeout=30)
    if project:
        from ddict.workflow import profile_database

        path = tmp_path / "etude-sommeil.sav"
        path.write_bytes(fictional_files["etude-sommeil.sav"].read_bytes())
        test.session_state["project_path"] = str(profile_database(path)[1])
    else:
        test.session_state["project_path"] = ""
    test.run()
    test.sidebar.button(key="quit").click().run()
    assert not test.exception, test.exception
    assert test.title[0].value == "L'outil est arrêté."
    assert stopped
