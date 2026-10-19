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
    N_("Réglages"): (PageInfo("ai", N_("IA"), ":material/smart_toy:"),),
}
# v0.20 (D-149): designing the questionnaire, first, for a project created by "Concevoir
# un questionnaire"; its questionnaire is this one, not a file read on "Questionnaire".
DESIGN: tuple[PageInfo, ...] = (
    PageInfo("design", N_("Questionnaire"), ":material/edit_document:"),
)
PAGES = {page.mode: page for pages in (DESIGN, *SECTIONS.values()) for page in pages}
FIRST = "base"  # a project opens on its database (v0.3)
# The pages that show the database: before it arrives (v0.20, D-145), they say they wait.
NEEDS_BASE = ("base", "analyses", "notebook", "method", "verify")


def sections(project: Project) -> dict[str, tuple[PageInfo, ...]]:
    """The phases and their pages for this project: "Concevoir" first for a designed one,
    kept after its database arrives (D-149)."""
    if project.design is None:
        return SECTIONS
    found = {N_("Concevoir"): DESIGN}
    for name, pages in SECTIONS.items():
        found[name] = tuple(p for p in pages if p.mode != "questionnaire")
    return found


def first(project: Project) -> str:
    """The page a project opens on: its questionnaire while a designed one has no database
    yet, its database otherwise (v0.20, D-149)."""
    if project.design is not None and project.source is None:
        return "design"
    return FIRST


def waits_for_base(project: Project, mode: str) -> bool:
    return project.source is None and mode in NEEDS_BASE


# The pages whose whole work the dashboard follows: a tick when nothing waits there. Not the
# groups nor the names: their tasks appear only once the team has begun (a scoring, a name),
# so a tick there would say "done" of work not started.
FOLLOWED = ("base", "questionnaire", "glossary", "variables", "plan")
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
