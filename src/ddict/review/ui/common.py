"""What every view shares: the project of the session, and buttons that run a decision.

Buttons read the fields they need when clicked (`state`), never when the page was drawn:
otherwise a value typed just before the click would be lost.
"""

from __future__ import annotations

import contextlib
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import streamlit as st

from ddict import recents
from ddict.analysis import notebook as nb
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import ProjectChanged, ProjectError, load_project, ondisk, save_project
from ddict.project.model import Project, TrackedValue
from ddict.review import logic
from ddict.workflow import leftover_notes


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
        st.session_state[LEFTOVERS] = leftover_notes(project_path())  # v0.17
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


def act(
    action, *args, key: str, timed: bool, reset: tuple[str, ...], label: str | None = None
) -> None:
    """Run a decision with its arguments read now, save, and keep a message to show next to
    the button `key`. On success, the fields in `reset` are drawn again from the project.
    `label`, the button's, is recalled if the save is refused (v0.17, D-130)."""
    values = [a() if callable(a) else a for a in args]
    kwargs = {"now": now()} if timed else {}
    before = recall(label)  # before the decision: afterwards, the fields equal the project
    try:
        action(project(), *values, **kwargs)
    except logic.ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    if not save(key, before):
        return
    st.session_state.message = ("success", _("Enregistré."), key)
    for name in reset:
        st.session_state[name] = st.session_state.fresh[name]()


def field(key: str, fresh, *, label: str = "") -> str:
    """Key of an input whose starting value `fresh()` comes from the project.

    The value is set through the session state, never with `value=`: after a decision, `act`
    sets it again, which the browser shows (it keeps its own copy of a field otherwise).
    The field remembers where it is drawn (`set_place`): a value typed there and not saved
    becomes a draft when the person goes elsewhere (v0.16, D-124). `label` names it when a
    refused save recalls what was typed (v0.17, D-130).
    """
    st.session_state.setdefault("fresh", {})[key] = fresh
    st.session_state.setdefault(PLACES, {})[key] = st.session_state.get(PLACE)
    st.session_state.setdefault(LABELS, {})[key] = label
    if key not in st.session_state:
        st.session_state[key] = fresh()
    return key


# --- Typed and not saved (v0.16, D-124). ---

PLACE = "place"  # Place of the fields drawn now
PLACES = "field-places"  # key -> the Place where the field was drawn
LABELS = "field-labels"  # key -> the field's label (v0.17)
DRAFTS = "drafts"  # [Draft]: what was typed, not saved, where the person left it
TAKEN_BACK = "drafts-taken-back"  # a draft went back into its fields on this run


@dataclass(frozen=True)
class Place:
    """Where a field is: its page, the variable or group it belongs to, words for a person,
    and what opens it again (the fields `go_to` fills: a filter, a variable, a tab)."""

    mode: str
    item: str | None
    title: str
    opens: tuple[tuple[str, object], ...] = ()

    def same(self, other: Place | None) -> bool:
        return other is not None and (self.mode, self.item) == (other.mode, other.item)


@dataclass(frozen=True)
class Draft:
    place: Place
    values: tuple[tuple[str, object], ...]


def set_place(mode: str, item: str | None, title: str, **opens) -> None:
    """Where the fields drawn from now on are (`opens`: what `go_to` fills to come back)."""
    st.session_state[PLACE] = Place(mode, item, title, tuple(opens.items()))


def _plain(value):
    if value is None:
        return ""  # an empty list or field: no value either way
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _differs(key: str) -> bool:
    fresh = st.session_state.get("fresh", {}).get(key)
    if fresh is None or key not in st.session_state:
        return False
    try:
        return _plain(st.session_state[key]) != _plain(fresh())
    except (KeyError, ValueError, AttributeError, IndexError):
        return False  # the project changed under the field (a variable gone): no draft


def unsaved(keys=None) -> list[str]:
    """The fields that differ from the project: typed, not saved."""
    places = st.session_state.get(PLACES, {})
    return [k for k in (keys if keys is not None else list(places)) if _differs(k)]


def keep_drafts(here: Place) -> None:
    """Before a page is drawn: what was typed elsewhere and not saved becomes a draft (the
    fields of another page are not drawn, and Streamlit forgets their values)."""
    places = st.session_state.get(PLACES, {})
    found: dict[Place, dict] = {}
    for key in unsaved():
        place = places.get(key)
        if place is not None and not place.same(here):
            found.setdefault(place, {})[key] = st.session_state[key]
    drafts = [d for d in st.session_state.get(DRAFTS, []) if d.place not in found]
    drafts += [Draft(place, tuple(values.items())) for place, values in found.items()]
    # Back where a draft was typed (by "Revenir", by the menu, or when a click on the menu
    # was lost while the field was being sent): its values go back into its fields.
    kept = [d for d in drafts if not d.place.same(here)]
    for draft in drafts:
        if draft.place.same(here):
            st.session_state.update(dict(draft.values))
            st.session_state[TAKEN_BACK] = True
    st.session_state[DRAFTS] = kept


def _back(draft: Draft) -> None:
    """Open the draft's place; its values go back into its fields there (`keep_drafts`)."""
    go_to(draft.place.mode, **dict(draft.place.opens))


def _drop() -> None:
    st.session_state[DRAFTS] = []


def drafts_notice(here: Place) -> None:
    """On the page where the person arrives: what was left unsaved, to go back to or drop;
    and, back where it was typed, that it was taken back."""
    if st.session_state.pop(TAKEN_BACK, False):
        st.info(_("Votre saisie non enregistrée est reprise dans ses champs."))
    drafts = st.session_state.get(DRAFTS, [])
    if not drafts:
        return
    with st.container(border=True):
        st.warning(
            _("Saisie non enregistrée : {places}.").format(
                places=" ; ".join(d.place.title for d in drafts)
            ),
            icon=":material/edit_note:",
        )
        with st.container(horizontal=True):
            for index, draft in enumerate(drafts):
                st.button(
                    _("Revenir à {place}").format(place=draft.place.title),
                    key=f"draft-back-{index}",
                    on_click=_back,
                    args=(draft,),
                    type="primary",
                )
            st.button(_("Abandonner"), key="draft-drop", on_click=_drop)


# --- Changed elsewhere (v0.17, D-129, D-130). ---

REFUSED = "refused"  # [Refusal]: decisions not saved, the file having changed elsewhere
ELSEWHERE = "changed-elsewhere"  # the file changed since it was read, seen before any save
REDO = "redo"  # [Refusal]: after the reload, what to decide again
LEFTOVERS = "leftovers"  # the interrupted saves found when the project was opened


@dataclass(frozen=True)
class Refusal:
    """A decision that was not saved, in words: where, the button, what was typed."""

    place: str
    action: str | None
    fields: tuple[tuple[str, str], ...]

    def text(self) -> str:
        head = f"**{self.place}**" if self.place else ""
        if self.action:
            head = f"{head} — « {self.action} »" if head else f"« {self.action} »"
        typed = " ; ".join(f"{name} : « {value} »" for name, value in self.fields)
        return " ; ".join(part for part in (head, typed) if part)


def _shown(value) -> str:
    if value is None or value == "" or value == []:
        return DASH
    if isinstance(value, bool):
        return _("oui") if value else _("non")
    if isinstance(value, list | tuple):
        return ", ".join(str(v) for v in value)
    return str(value)


def _typed(values) -> tuple[tuple[str, str], ...]:
    labels = st.session_state.get(LABELS, {})
    return tuple((labels.get(k) or k, _shown(v)) for k, v in values)


def recall(action: str | None = None) -> Refusal:
    """The decision about to be made here: the place, the button, and the fields of this
    place that differ from the project (call it before the decision changes the project)."""
    here = st.session_state.get(PLACE)
    places = st.session_state.get(PLACES, {})
    keys = [k for k in unsaved() if here is not None and here.same(places.get(k))]
    typed = _typed((k, st.session_state.get(k)) for k in keys)
    return Refusal(here.title if here is not None else "", action, typed)


def _refused(key: str | None, refusal: Refusal | None, action: str | None, what: str) -> None:
    st.session_state.setdefault(REFUSED, []).append(refusal or recall(action))
    if key is not None:
        text = (
            _("Non enregistré : le projet a été modifié ailleurs (voir en haut de la page).")
            if what == "project"
            else _("Non enregistré : le carnet a été modifié ailleurs (voir en haut de la page).")
        )
        st.session_state.message = ("error", text, key)


def _busy(key: str | None) -> None:
    """Windows held the file a moment: nothing written. The decision is undone in memory
    (the project is read again: the file is what this session read), so that the page never
    shows as decided what is not saved; what was typed stays in its fields."""
    if key is not None:
        st.session_state.message = (
            "error",
            _(
                "Le fichier est occupé, peut-être par la synchronisation de OneDrive : rien "
                "n'est enregistré. Réessayez dans un instant."
            ),
            key,
        )


def save(
    key: str | None = None, refusal: Refusal | None = None, *, action: str | None = None
) -> bool:
    """Save the session's project: the only way the pages do it (v0.17). False, nothing
    written, when the file changed since it was read; the page then says so at the top, with
    what the person had decided (`refusal`, or `action` and what is typed here now)."""
    try:
        save_project(project(), project_path())
    except ProjectChanged:
        _refused(key, refusal, action, "project")
        return False
    except ondisk.FileBusy:
        _busy(key)
        with contextlib.suppress(ProjectError):
            st.session_state.project = load_project(project_path())
        return False
    return True


def save_notebook(
    notebook, key: str | None = None, refusal: Refusal | None = None, *, action: str | None = None
) -> bool:
    """Save the project's notebook, like `save`."""
    try:
        nb.save_notebook(notebook, nb.notebook_path(project_path()))
    except nb.NotebookChanged:
        _refused(key, refusal, action, "notebook")
        return False
    except ondisk.FileBusy:
        _busy(key)  # the notebook is read again by each action
        return False
    return True


def watch(current: Project) -> None:
    """At each run: whether the project file still holds what this session read (by its
    date and size, then its content). Changed: said before the person decides anything."""
    known = ondisk.remembered(current)
    if known is not None and not ondisk.unchanged(project_path(), known):
        st.session_state[ELSEWHERE] = True


def reload() -> None:
    """Read the project again, on the same page; what was refused or typed and not saved is
    kept to be decided again, in words only: never put back into the fields, where it would
    bring back the old values of what the other person changed (D-130)."""
    here = st.session_state.get(PLACE)
    redo = list(st.session_state.get(REFUSED, []))
    redo += [
        Refusal(d.place.title, None, _typed(d.values)) for d in st.session_state.get(DRAFTS, [])
    ]
    typed = recall()
    if typed.fields:
        redo.append(typed)
    open_project(project_path())
    if here is not None:
        go_to(here.mode, **dict(here.opens))
    if redo:
        st.session_state[REDO] = redo


def changed_notice() -> None:
    """At the top of every page of a project: changed elsewhere, what was not saved, and the
    way to read the project again; after the reload, what to decide again."""
    refused = st.session_state.get(REFUSED, [])
    if refused or st.session_state.get(ELSEWHERE):
        with st.container(border=True):
            text = _(
                "Ce projet a été modifié ailleurs depuis que vous l'avez ouvert (autre onglet, "
                "autre personne ou ligne de commande)."
            )
            if refused:
                text += " " + _("Votre dernière décision n'est pas enregistrée.")
            st.warning(text, icon=":material/sync_problem:")
            for refusal in refused:
                st.markdown(_("Votre décision : {decision}").format(decision=refusal.text()))
            if refused:
                st.write(
                    _(
                        "« Recharger le projet » lit le projet tel qu'il est maintenant ; votre "
                        "décision restera affichée pour que vous la refassiez."
                    )
                )
            st.button(
                _("Recharger le projet"),
                key="reload-project",
                on_click=reload,
                type="primary",
                icon=":material/refresh:",
            )
    leftovers = st.session_state.get(LEFTOVERS)
    if leftovers:
        with st.container(border=True):
            for note in leftovers:
                st.warning(note, icon=":material/report:")
            st.button(
                _("Compris"),
                key="leftovers-close",
                on_click=lambda: st.session_state.pop(LEFTOVERS),
            )
    redo = st.session_state.get(REDO)
    if redo:
        with st.container(border=True):
            st.info(
                _("Décision à refaire : elle n'a pas été enregistrée avant le rechargement."),
                icon=":material/replay:",
            )
            for refusal in redo:
                st.markdown(refusal.text())
            st.button(
                _("Fermer"), key="redo-close", on_click=lambda: st.session_state.pop(REDO, None)
            )


def unsaved_note(keys) -> None:
    """Next to the "Enregistrer" of a section: its fields hold what is not saved yet."""
    if keys and unsaved(list(keys)):
        st.caption(_(":material/edit: Modifications non enregistrées."))


DASH = "—"  # an empty cell of a table, never "None" (v0.16, finding 17)


def dash(value) -> str:
    """A cell to show: the value, or the dash when there is none."""
    return DASH if value is None or value == "" else str(value)


GOTO = "goto"  # the page a button asks for; the navigation opens it (v0.16, D-122)


def go_to(mode: str, **filled) -> None:
    """Open another page with its fields filled (v0.16): the only place that knows how a
    page is chosen."""
    st.session_state[GOTO] = mode
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


def tabs(key: str, labels: list[str]):
    """Tabs whose open one is kept in the session under `key` (v0.16, finding 14): a button
    of another page can open one (`go_to(mode, **{key: label})`), and a rerun keeps it."""
    if st.session_state.get(key) not in labels:
        st.session_state.pop(key, None)
    return st.tabs(labels, key=key, on_change="rerun")


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
    watch: tuple[str, ...] = (),
) -> None:
    """A button that runs a decision; `submit` for the button of a form (st.form), whose
    fields are sent together when it is clicked. Without `message`, its message is shown
    by the caller (buttons side by side, v0.16)."""
    widget = st.form_submit_button if submit else st.button
    with st.container(horizontal=True, vertical_alignment="center"):
        widget(
            label,
            key=key,
            on_click=act,
            args=(action, *args),
            kwargs={"key": key, "timed": timed, "reset": reset, "label": label},
            type="primary" if primary else "secondary",
        )
        # Beside the button, never above it: a note that appears must not move the button
        # under the pointer (v0.16, found in the browser).
        unsaved_note(watch)
    if message:
        show_message(key)


def decision_card(
    project: Project,
    tracked: TrackedValue,
    *,
    key: str,
    title: str,
    show,
    field=None,
    input_key: str | None = None,
    changed: bool = False,
    accept: tuple | None = None,
    reject: tuple | None = None,
    save: tuple | None = None,
    labels: tuple[str, str] | None = None,
    save_label: str | None = None,
    note: str | None = None,
    origin_text: str | None = None,
) -> None:
    """One way to decide a value, on every page (v0.16, D-121): the value, its origin and its
    status, the field to change it, then "Accepter", which takes the value shown in the
    field, and "Rejeter", side by side. Once decided, "Enregistrer" changes it.

    `show()` draws the value; `field()` draws its input under `input_key` (none for a value
    that is accepted or rejected as a whole); `changed` says the field differs from the
    proposal. `accept`, `reject` and `save` are (action, *arguments), the arguments read
    when the button is clicked. `origin_text` replaces the origin of a value that is not a
    tracked one (an acronym of the glossary)."""
    st.markdown(f"**{title}**")
    show()
    if origin_text is not None:
        st.caption(origin_text)
    elif tracked.value is not None or tracked.status != "none":
        st.caption(origin(project, tracked))
    proposed = getattr(tracked, "proposed_value", None)
    if proposed is not None:
        st.caption(_("Valeur d'origine : {v}").format(v=proposed))
    if note:
        st.caption(note)
    if field is not None:
        field()
    reset = (input_key,) if input_key else ()
    if tracked.status == "proposed" and accept is not None:
        if changed:
            st.write(_("« Accepter » enregistrera votre correction ; la proposition sera gardée "
                       "comme origine."))  # fmt: skip
        accept_label, reject_label = labels or (_("Accepter"), _("Rejeter"))
        with st.container(horizontal=True):
            button(accept_label, f"accept-{key}", *accept, timed=True, primary=True,
                   reset=reset, message=False)  # fmt: skip
            if reject is not None:
                button(reject_label, f"reject-{key}", *reject, timed=True, reset=reset,
                       message=False)  # fmt: skip
    elif save is not None:
        button(save_label or _("Enregistrer"), f"save-{key}", *save, timed=True, reset=reset,
               message=False)  # fmt: skip
    for kind in ("accept", "reject", "save"):
        show_message(f"{kind}-{key}")


def origin(project: Project, tracked: TrackedValue) -> str:
    text = w.ORIGINS[tracked.origin]
    if tracked.status != "none":
        text += f" — {w.STATUSES[tracked.status]}"
    if tracked.ai_run:
        run = next((r for r in project.ai_runs if r.run_id == tracked.ai_run), None)
        if run is not None:
            text += f" ({run.model}, {run.run_id})"
    return text
