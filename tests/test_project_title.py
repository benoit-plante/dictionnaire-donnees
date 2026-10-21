"""Plan-accueil, step D1 (D-161): a project's title — format 0.11.0, a 0.10.0 file read as it
is, a 0.11.0 file "newer" for the tool before it; trimmed, one line, 120 characters at most;
not in the codebook's fingerprint, never in a message to the AI; shown instead of the
file's name on the home page, in the project's sidebar and by `ddict projets`; no file
renamed."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import overview, tracked
from ddict.cli import main
from ddict.llm import build_blocks
from ddict.llm.advise import build_advice_block
from ddict.llm.link import build_link_blocks
from ddict.llm.stems import build_stem_blocks
from ddict.project import SCHEMA_VERSION, fingerprint, load_project, save_project, store
from ddict.project.store import ProjectNewer
from ddict.project.title import MAX_LENGTH, TitleError, check, name, set_title
from ddict.workflow import add_questionnaire, profile_database

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
EXAMPLES = ROOT / "exemples" / "bases-fictives"
WITNESS = "Titre témoin 4242 de l'équipe"


@pytest.fixture
def path(tmp_path):
    folder = tmp_path / "Études 2026"
    folder.mkdir()
    for file in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(EXAMPLES / file, folder / file)
    project, found = profile_database(folder / "etude-sommeil.sav")
    add_questionnaire(project, folder / "questionnaire-sommeil.pdf")
    save_project(project, found)
    overview.clear_cache()
    return found


# --- The rule. ---


def test_trimmed_one_line_not_too_long():
    assert check("  Sommeil et anxiété, cohorte 2026  ") == "Sommeil et anxiété, cohorte 2026"
    assert check("   ") is None  # empty: the file's name comes back
    assert check("x" * MAX_LENGTH) == "x" * MAX_LENGTH
    with pytest.raises(TitleError, match="121 caractères ; 120 au plus"):
        check("x" * (MAX_LENGTH + 1))
    with pytest.raises(TitleError, match="une seule ligne"):
        check("Sommeil\net anxiété")
    assert check("Étude : vague 2 / CON?") == "Étude : vague 2 / CON?"  # not a file name


def test_set_and_take_off(path):
    project = load_project(path)
    assert name(project, path) == "etude-sommeil"
    assert set_title(project, " Sommeil 2026 ") is True
    assert set_title(project, "Sommeil 2026") is False  # the same: nothing changes
    assert name(project, path) == "Sommeil 2026"
    assert set_title(project, "") is True and project.title is None


# --- The format. ---


def test_written_after_the_version_and_read_again(path):
    assert SCHEMA_VERSION == "0.12.0"
    project = load_project(path)
    set_title(project, WITNESS)
    save_project(project, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert list(data)[:2] == ["schema_version", "title"]
    assert data["title"] == WITNESS and data["schema_version"] == "0.12.0"
    assert load_project(path).title == WITNESS
    assert sorted(p.name for p in path.parent.iterdir()) == [
        "etude-sommeil.dd.json", "etude-sommeil.sav", "questionnaire-sommeil.pdf"
    ]  # fmt: skip  # no file renamed


def test_a_0_10_0_project_reads_as_it_is(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = "0.10.0"
    del data["title"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    old = load_project(path)
    assert old.title is None and old.schema_version == "0.12.0"


def test_a_0_11_0_project_is_newer_for_the_tool_before(path, monkeypatch):
    monkeypatch.setattr(store, "SCHEMA_VERSION", "0.10.0")  # the reader of the 0.20.1
    with pytest.raises(ProjectNewer):
        load_project(path)


def test_not_in_the_fingerprint(path):
    project = load_project(path)
    before = fingerprint.fingerprint(project)
    set_title(project, WITNESS)
    assert fingerprint.fingerprint(project) == before


def test_never_sent_to_the_ai(path):
    project = load_project(path)
    set_title(project, WITNESS)
    blocks = [
        *build_blocks(project, size=25),
        *build_link_blocks(project, size=20),
        *build_stem_blocks(project, size=8),
        build_advice_block(project, "Le sommeil est-il lié à l'anxiété ?", "advise-v3"),
    ]
    text = "\n".join(m["content"] for b in blocks for m in b.messages)
    assert text and "4242" not in text and "témoin" not in text


# --- Where it is shown. ---


def test_the_home_page_and_the_command_line(path, capsys):
    tracked.follow(path)
    assert main(["projets", "renommer", str(path), "Sommeil et anxiété, cohorte 2026"]) == 0
    assert "Titre du projet : Sommeil et anxiété, cohorte 2026." in capsys.readouterr().out
    row = overview.row(path)
    assert (row.name, row.file_name) == ("Sommeil et anxiété, cohorte 2026", "etude-sommeil")
    assert main(["projets", "lister"]) == 0
    assert "Sommeil et anxiété, cohorte 2026" in capsys.readouterr().out
    assert main(["projets", "renommer", str(path), "--effacer"]) == 0
    assert "porte le nom de son fichier" in capsys.readouterr().out
    assert overview.row(path).name == "etude-sommeil"


@pytest.mark.parametrize(
    ("args", "said"),
    [
        ([], "Donnez un titre, ou --effacer"),
        (["Titre", "--effacer"], "Donnez un titre, ou --effacer"),
        (["x" * 121], "120 au plus"),
    ],
)
def test_the_command_line_refuses(path, capsys, args, said):
    before = path.read_bytes()
    assert main(["projets", "renommer", str(path), *args]) == 2
    assert said in capsys.readouterr().err
    assert path.read_bytes() == before


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_sidebar_of_the_open_project(path):
    project = load_project(path)
    set_title(project, "Sommeil 2026")
    save_project(project, path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.run()
    assert not app.exception, app.exception
    assert app.sidebar.title[0].value == "Sommeil 2026"
    assert "etude-sommeil.sav" in [c.value for c in app.sidebar.caption]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_mes_projets_shows_the_title(path):
    project = load_project(path)
    set_title(project, "Sommeil 2026")
    save_project(project, path)
    tracked.follow(path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert app.sidebar.button(key="home-project-0").label.startswith("Sommeil 2026")
    assert app.subheader[0].value == "Sommeil 2026"
    assert "etude-sommeil.dd.json" in app.caption[1].value  # the file's name, in its path
