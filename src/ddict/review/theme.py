"""The colours of the interface (v0.16, D-123), given to Streamlit by `ddict reviser` as
`--theme.*` options: they apply whatever the folder the tool is started from.

A light theme, a dark neutral main colour, red kept for errors. The text is darker than
Streamlit's: a caption (`st.caption`) is the text colour at 60 % opacity, so the text colour
sets the contrast of every caption too (at least 4.5:1, WCAG AA).
"""

from __future__ import annotations

THEME = {
    "base": "light",
    "primaryColor": "#1F4E79",  # buttons, choices, progress: 8.66:1 with white
    "redColor": "#B42318",  # errors only: 6.57:1
    "textColor": "#14161C",  # 18.08:1; captions 4.73:1 on white, 4.55:1 in the sidebar
    "greenTextColor": "#146C2E",  # the text of a success message
}


def options() -> list[str]:
    """The command-line options of `streamlit run`."""
    return [part for key, value in THEME.items() for part in (f"--theme.{key}", value)]
