"""v0.16, step A4 (D-123): the colours of the interface, given by `ddict reviser`, with
contrasts of at least 4.5:1 (WCAG AA); the explanations that carry a decision are normal
text, not faded captions."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import review_command
from ddict.review.theme import THEME
from ddict.workflow import profile_database

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
WHITE = "#FFFFFF"
SIDEBAR = "#F0F2F6"  # Streamlit's secondary background, light theme
CAPTION_OPACITY = 0.6  # a caption is the text colour at 60 % (measured in the browser)
AA = 4.5


def _rgb(colour: str) -> tuple[float, ...]:
    return tuple(int(colour[i : i + 2], 16) for i in (1, 3, 5))


def _luminance(rgb) -> float:
    channels = [c / 255 for c in rgb]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b) -> float:
    """WCAG 2.1 contrast ratio of two colours, as "#RRGGBB" or RGB tuples."""
    high, low = sorted((_luminance(_rgb(c) if isinstance(c, str) else c) for c in (a, b)),
                       reverse=True)  # fmt: skip
    return (high + 0.05) / (low + 0.05)


def _over(colour: str, background: str, opacity: float) -> tuple[float, ...]:
    pairs = zip(_rgb(colour), _rgb(background), strict=True)
    return tuple(opacity * f + (1 - opacity) * b for f, b in pairs)


def test_contrast_formula():
    assert round(contrast("#000000", WHITE), 1) == 21.0
    assert round(contrast("#FF4B4B", WHITE), 2) == 3.30  # Streamlit's red, as reviewed


def test_the_command_gives_the_theme():
    command, _env = review_command(None, 8501)
    joined = " ".join(command)
    assert "--theme.base light" in joined
    for key, value in THEME.items():
        assert f"--theme.{key} {value}" in joined


def test_every_colour_reaches_aa():
    text = THEME["textColor"]
    assert contrast(WHITE, THEME["primaryColor"]) >= AA  # white on the main colour
    assert contrast(THEME["primaryColor"], SIDEBAR) >= AA
    assert contrast(THEME["redColor"], WHITE) >= AA
    assert contrast(text, WHITE) >= AA
    for background in (WHITE, SIDEBAR):
        assert contrast(_over(text, background, CAPTION_OPACITY), background) >= AA
    # A success message: its text on Streamlit's light green background (green at 10 %).
    green = _over("#21C354", WHITE, 0.1)
    assert contrast(_rgb(THEME["greenTextColor"]), green) >= AA


def test_red_is_kept_for_errors():
    assert THEME["primaryColor"].upper() != "#FF4B4B"
    red = _rgb(THEME["redColor"])
    primary = _rgb(THEME["primaryColor"])
    assert red[0] > red[2] and primary[2] > primary[0]  # a red, and a blue


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_decisive_explanations_are_normal_text(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "groups"
    app.run()
    assert not app.exception, app.exception
    decisive = ("Réservée aux personnes, avec une source", "Nom de l'instrument : réservé")
    captions = [c.value for c in app.caption]
    texts = [m.value for m in app.markdown]
    for start in decisive:
        assert not any(c.startswith(start) for c in captions), start
        assert any(t.startswith(start) for t in texts), start
