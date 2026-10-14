"""Keep the English catalog up to date (v0.5, D-033): extract the strings marked with `_`,
`N_` and `field_label` in src/ddict (read by Python's own parser, which also sees the calls
inside f-strings), update src/ddict/locale/en/LC_MESSAGES/ddict.po (new strings
empty, translations kept, strings gone removed), and compile ddict.mo.

Run: uv run python scripts/traductions.py
Babel is a development dependency only; the tool reads the .mo with gettext.
"""

from __future__ import annotations

import ast
import io
from datetime import UTC, datetime
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "ddict"
LOCALE = SOURCE / "locale"
LANGUAGES = ["en"]
# Fixed dates: two runs on the same sources give the same files.
FIXED = datetime(2026, 1, 1, tzinfo=UTC)


KEYWORDS = {"_", "N_", "field_label"}


def marked(path: Path) -> list[str]:
    """The strings given to `_`, `N_` or `field_label` in a source file, in order."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in KEYWORDS
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and node.args[0].value
        ):
            found.append(node.args[0].value)
    return found


def template() -> Catalog:
    catalog = Catalog(project="ddict", creation_date=FIXED, charset="utf-8")
    for path in sorted(SOURCE.rglob("*.py")):
        for message in marked(path):
            catalog.add(message)
    return catalog


def po_path(language: str) -> Path:
    return LOCALE / language / "LC_MESSAGES" / "ddict.po"


def read(language: str) -> Catalog:
    path = po_path(language)
    if not path.is_file():
        return Catalog(locale=language, project="ddict", creation_date=FIXED, charset="utf-8")
    with path.open("rb") as stream:
        return read_po(stream, locale=language)


def updated(language: str) -> Catalog:
    catalog = read(language)
    catalog.update(template(), no_fuzzy_matching=True)
    catalog.obsolete.clear()
    catalog.creation_date = FIXED
    catalog.revision_date = FIXED
    catalog.fuzzy = False
    return catalog


def po_bytes(catalog: Catalog) -> bytes:
    out = io.BytesIO()
    write_po(out, catalog, sort_output=True, omit_header=False, no_location=True, width=100)
    return out.getvalue()


def mo_bytes(catalog: Catalog) -> bytes:
    out = io.BytesIO()
    write_mo(out, catalog, use_fuzzy=False)
    return out.getvalue()


def main() -> None:
    for language in LANGUAGES:
        catalog = updated(language)
        path = po_path(language)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(po_bytes(catalog))
        path.with_suffix(".mo").write_bytes(mo_bytes(read(language)))
        missing = sum(1 for m in catalog if m.id and not m.string)
        print(f"{path.relative_to(ROOT)} : {len(catalog)} phrases, {missing} sans traduction")


if __name__ == "__main__":
    main()
