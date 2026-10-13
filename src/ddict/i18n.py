"""Translatable interface strings (gettext). Source strings are in French (D-004)."""

from __future__ import annotations

import gettext
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent / "locale"

_translation = gettext.translation("ddict", localedir=LOCALE_DIR, fallback=True)
_ = _translation.gettext
