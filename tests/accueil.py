"""The tabs of the home page in tests (D-160): chosen by the session's "home_tab", as a
project's page is chosen by "mode" (AppTest cannot click in the sidebar's menu)."""

from streamlit.testing.v1 import AppTest


def tab(app: AppTest, name: str) -> AppTest:
    """Show the tab `name` ("projets", "nouveau", "concevoir", "ouvrir", "reglages")."""
    app.session_state["home_tab"] = name
    app.run()
    assert not app.exception, app.exception
    return app
