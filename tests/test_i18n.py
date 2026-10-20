"""v0.5, step 1: the language of the interface, read when a string is shown (D-032, D-033)."""

import ast
import importlib.util
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import i18n, settings
from ddict.export import wording as w
from ddict.i18n import _

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "ddict"
APP = str(SOURCE / "review" / "app.py")


def _script():
    spec = importlib.util.spec_from_file_location(
        "traductions", ROOT / "scripts" / "traductions.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_string_is_translated_at_import():
    """A string translated at import keeps its first language: tables use N_ and Texts."""
    found = []
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        inside = {
            id(sub)
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda)
            for sub in ast.walk(node)
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_"
                and id(node) not in inside
            ):
                found.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not found, found


def test_the_catalog_is_up_to_date():
    module = _script()
    template = {m.id for m in module.template() if m.id}
    catalog = module.read("en")
    assert {m.id for m in catalog if m.id} == template, "run: uv run python scripts/traductions.py"
    mo = module.po_path("en").with_suffix(".mo")
    assert mo.read_bytes() == module.mo_bytes(catalog), "run: uv run python scripts/traductions.py"


def test_strings_follow_the_language():
    assert _("Nouveau projet") == "Nouveau projet"
    assert w.TYPES["date"] == "date"
    i18n.set_language("en")
    assert _("Nouveau projet") == "New project"
    assert _("une phrase absente du catalogue") == "une phrase absente du catalogue"
    i18n.set_language("fr")
    assert _("Nouveau projet") == "Nouveau projet"
    assert i18n.set_language("de") == "fr"  # an unknown language means French


def test_tables_are_translated_when_read(monkeypatch):
    table = i18n.Texts({"a": i18n.N_("Accueil"), "b": (i18n.N_("Accueil"), 3)})
    assert table["a"] == "Accueil"
    monkeypatch.setattr(i18n, "_catalog", lambda language: _Fake())
    assert table["a"] == "[Accueil]"
    assert table["b"] == ("[Accueil]", 3)
    assert dict(table.items())["a"] == "[Accueil]"
    assert i18n.TextList([i18n.N_("Accueil")])[0] == "[Accueil]"


class _Fake:
    def gettext(self, text):
        return f"[{text}]"


def test_the_choice_is_kept_on_this_computer(monkeypatch):
    assert settings.interface_language() == "fr"
    settings.save_interface_language("en")
    assert settings.interface_language() == "en"
    found = json.loads((settings.config_dir() / settings.FILE_NAME).read_text(encoding="utf-8"))
    assert found == {"interface_language": "en"}
    monkeypatch.setenv("DDICT_LANG", "fr")
    assert settings.interface_language() == "fr"  # DDICT_LANG wins
    with pytest.raises(ValueError):
        settings.save_interface_language("de")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_home_page_switches_without_restarting():
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = ""
    app.session_state["home_tab"] = "reglages"  # D-160: the language is in "Réglages"
    app.run()
    assert app.title[0].value == "Réglages"
    app.button_group(key="interface-language").set_value("en").run()
    assert not app.exception, app.exception
    assert app.title[0].value == "Settings"
    assert settings.interface_language() == "en"
    app.run()  # kept on the next run
    assert app.title[0].value == "Settings"
    app.button_group(key="interface-language").set_value("fr").run()
    assert app.title[0].value == "Réglages"
