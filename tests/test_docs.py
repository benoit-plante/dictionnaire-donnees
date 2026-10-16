"""v0.5, step 7: the guides link to each other, and every link leads somewhere."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
LINK = re.compile(r"\]\(([^)\s]+)\)")


@pytest.mark.parametrize("path", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_lead_to_a_file(path):
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.split("#", 1)[0]
        assert (path.parent / file_part).exists(), f"{path.name}: {target}"


def test_every_guide_links_to_the_others():
    guides = {
        "installation-windows.md": ["en/installation-windows.md"],
        "en/installation-windows.md": ["../installation-windows.md"],
    }
    for guide, targets in guides.items():
        text = (ROOT / "docs" / guide).read_text(encoding="utf-8")
        for target in targets:
            assert f"]({target}" in text, (guide, target)
