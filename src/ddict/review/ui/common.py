"""What every view shares: the project of the session, and buttons that run a decision.

Buttons read the fields they need when clicked (`state`), never when the page was drawn:
otherwise a value typed just before the click would be lost.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

from ddict import recents
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import load_project, save_project
from ddict.project.model import Project, TrackedValue
from ddict.review import logic


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def project_path() -> Path:
    if "project_path" not in st.session_state:
        st.session_state.project_path = sys.argv[1] if len(sys.argv) > 1 else ""
    return Path(st.session_state.project_path)


def has_project() -> bool:
    """Whether a project is open; without one, the home page is shown (v0.3)."""
    project_path()  # the first time, from the command line
    return bool(str(st.session_state.project_path).strip())


def project() -> Project:
    if "project" not in st.session_state:
        st.session_state.project = load_project(project_path())
        recents.add(project_path())
    return st.session_state.project


def open_project(path: Path | str) -> None:
    """Open a project in this session: everything of the previous one is forgotten."""
    st.session_state.clear()
    st.session_state.project_path = str(path)


def close_project() -> None:
    """Back to the home page."""
    st.session_state.clear()
    st.session_state.project_path = ""


def state(key: str):
    return lambda: st.session_state[key]


def act(action, *args, key: str, timed: bool, reset: tuple[str, ...]) -> None:
    """Run a decision with its arguments read now, save, and keep a message to show next to
    the button `key`. On success, the fields in `reset` are drawn again from the project."""
    values = [a() if callable(a) else a for a in args]
    kwargs = {"now": now()} if timed else {}
    try:
        action(project(), *values, **kwargs)
    except logic.ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    save_project(project(), project_path())
    st.session_state.message = ("success", _("Enregistré."), key)
    for name in reset:
        st.session_state[name] = st.session_state.fresh[name]()


def field(key: str, fresh) -> str:
    """Key of an input whose starting value `fresh()` comes from the project.

    The value is set through the session state, never with `value=`: after a decision, `act`
    sets it again, which the browser shows (it keeps its own copy of a field otherwise).
    """
    st.session_state.setdefault("fresh", {})[key] = fresh
    if key not in st.session_state:
        st.session_state[key] = fresh()
    return key


def go_to(mode: str, **filled) -> None:
    """Open another page with its fields filled (v0.16): the only place that knows how a
    page is chosen, so that the navigation by phases changes only this function."""
    st.session_state.mode = mode
    st.session_state.update(filled)


def go_button(label: str, key: str, mode: str, **filled) -> None:
    """The button of a message that points to another page (v0.16, finding 11)."""
    st.button(
        label, key=key, on_click=go_to, args=(mode,), kwargs=filled, icon=":material/arrow_forward:"
    )


def variable_fields(name: str) -> dict:
    """What `go_to` fills to open the page Variables on one variable."""
    return {"filter": "all", "current": name, "variable": name}


def offer(label: str, key: str, target: str, value) -> None:
    """A button that puts what the tool computes into the field `target`, without saving it
    (v0.16, D-126): a decision field never starts from a computed value."""
    st.button(
        label,
        key=key,
        on_click=lambda: st.session_state.update({target: value}),
        icon=":material/arrow_downward:",
    )


def show_message(key: str) -> None:
    message = st.session_state.get("shown_message")
    if message and message[2] == key:
        (st.error if message[0] == "error" else st.success)(message[1])
        st.session_state.message_placed = True


def message_for(prefix: str) -> bool:
    """Whether the message to show answers a button whose key starts with `prefix`."""
    message = st.session_state.get("shown_message")
    return bool(message and message[2].startswith(prefix))


def button(
    label: str,
    key: str,
    action,
    *args,
    timed: bool = False,
    primary: bool = False,
    reset: tuple[str, ...] = (),
    submit: bool = False,
    message: bool = True,
) -> None:
    """A button that runs a decision; `submit` for the button of a form (st.form), whose
    fields are sent together when it is clicked. Without `message`, its message is shown
    by the caller (buttons side by side, v0.16)."""
    widget = st.form_submit_button if submit else st.button
    widget(
        label,
        key=key,
        on_click=act,
        args=(action, *args),
        kwargs={"key": key, "timed": timed, "reset": reset},
        type="primary" if primary else "secondary",
    )
    if message:
        show_message(key)


def origin(project: Project, tracked: TrackedValue) -> str:
    text = w.ORIGINS[tracked.origin]
    if tracked.status != "none":
        text += f" — {w.STATUSES[tracked.status]}"
    if tracked.ai_run:
        run = next((r for r in project.ai_runs if r.run_id == tracked.ai_run), None)
        if run is not None:
            text += f" ({run.model}, {run.run_id})"
    return text
