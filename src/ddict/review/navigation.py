"""The pages of the interface by phase (v0.16, D-122), and the state each one shows in the
navigation: what waits there, or a tick when nothing waits. Without Streamlit."""

from __future__ import annotations

from dataclasses import dataclass

from ddict.i18n import N_, _
from ddict.project.model import Project
from ddict.workflow import Task


@dataclass(frozen=True)
class PageInfo:
    mode: str  # the key kept in the session ("mode"), and the end of the page's address
    title: str  # in French, translated where it is shown (N_)
    icon: str


# Documenter, analyser, rédiger; then the settings, outside the steps.
SECTIONS: dict[str, tuple[PageInfo, ...]] = {
    N_("Documenter"): (
        PageInfo("base", N_("Base"), ":material/table_view:"),
        PageInfo("questionnaire", N_("Questionnaire"), ":material/description:"),
        PageInfo("glossary", N_("Glossaire"), ":material/menu_book:"),
        PageInfo("variables", N_("Variables"), ":material/list:"),
        PageInfo("groups", N_("Groupes"), ":material/workspaces:"),
        PageInfo("names", N_("Noms"), ":material/badge:"),
        PageInfo("export", N_("Export"), ":material/download:"),
    ),
    N_("Analyser"): (
        PageInfo("plan", N_("Plan"), ":material/flag:"),
        PageInfo("analyses", N_("Analyses"), ":material/functions:"),
        PageInfo("notebook", N_("Carnet"), ":material/book:"),
    ),
    N_("Rédiger"): (
        PageInfo("method", N_("Méthode"), ":material/edit_note:"),
        PageInfo("verify", N_("Vérifier"), ":material/fact_check:"),
    ),
    N_("Réglages"): (PageInfo("ai", N_("IA locale"), ":material/smart_toy:"),),
}
PAGES = {page.mode: page for pages in SECTIONS.values() for page in pages}
FIRST = "base"  # a project opens on its database (v0.3)

# The pages whose work the dashboard follows: a tick when nothing waits there.
FOLLOWED = ("base", "questionnaire", "glossary", "variables", "groups", "names", "plan")
DONE = "✓"


def waiting(tasks: list[Task]) -> dict[str, int]:
    """What waits on each page, from the dashboard's tasks."""
    found: dict[str, int] = {}
    for task in tasks:
        found[task.mode] = found.get(task.mode, 0) + task.count
    return found


def state(project: Project, mode: str, counts: dict[str, int]) -> str:
    """The mark after a page's title: "(12)" when 12 things wait there, "✓" when the page
    is followed and nothing waits, nothing otherwise."""
    if counts.get(mode):
        return f"({counts[mode]})"
    if mode == "plan":
        return DONE if project.plan.frozen is not None else ""
    return DONE if mode in FOLLOWED else ""


def title(project: Project, mode: str, counts: dict[str, int]) -> str:
    mark = state(project, mode, counts)
    name = _(PAGES[mode].title)
    return f"{name} {mark}" if mark else name
