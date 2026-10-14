"""Steps of the workflow shared by the command line and the interface (v0.3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ddict.export import write_markdown, write_xlsx
from ddict.export.wording import anomalies
from ddict.glossary import propose_from_questionnaire, undefined_acronyms
from ddict.i18n import _
from ddict.io import read_database
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import PROJECT_SUFFIX, build_project, save_project
from ddict.project.model import Project, Questionnaire
from ddict.questionnaire import load_questionnaire
from ddict.questionnaire.labels import propose_value_labels
from ddict.questionnaire.link import drop_stale_links


class ProjectExists(FileExistsError):
    """A project file is already there: replacing it would lose the decisions it holds."""


def default_project_path(database: Path) -> Path:
    return database.with_name(database.stem + PROJECT_SUFFIX)


def profile_database(
    database: Path | str,
    output: Path | str | None = None,
    *,
    replace: bool = False,
    min_cell_count: int = MIN_CELL_COUNT,
) -> tuple[Project, Path]:
    """Read a database and write its project file, next to it unless `output` is given."""
    database = Path(database)
    output = Path(output) if output else default_project_path(database)
    if output.exists() and not replace:
        raise ProjectExists(output)
    project = build_project(read_database(database), min_cell_count=min_cell_count)
    save_project(project, output)
    return project, output


def profile_summary(project: Project) -> str:
    """One line: "34 variables, 200 lignes ; 4 variables sensibles ; 10 avec signalements"."""
    sensitive = sum(
        1 for e in project.variables if (e.privacy.privacy_class.value or "ordinary") != "ordinary"
    )
    # The same count as the "Avec signalements" filter of the review (notes excluded).
    flagged = sum(1 for e in project.variables if anomalies(e.profile))
    return _(
        "{n} variables, {rows} lignes ; {sensitive} variables sensibles ; "
        "{flagged} avec signalements."
    ).format(
        n=len(project.variables),
        rows=project.source.n_rows,
        sensitive=sensitive,
        flagged=flagged,
    )


# --- The questionnaire (v0.2), from the command line or the interface. ---

TO_CHECK = {
    "grid_header_unclear": _("titres de colonnes collés"),
    "grid_without_header": _("grille sans titres de colonnes"),
    "grid_rows_unnumbered": _("énoncés de grille non numérotés"),
}
KINDS = {
    "open": _("ouvertes"),
    "single": _("à choix unique"),
    "checkbox": _("à cocher"),
    "grid": _("grilles"),
}


class QuestionnaireExists(ValueError):
    """The project has a questionnaire already: replacing it may remove links."""


def add_questionnaire(project: Project, path: Path | str, *, replace: bool = False) -> int:
    """Read the questionnaire into the project (not saved): acronyms it defines become
    proposals, links to a former questionnaire are removed, value labels are refreshed.
    Returns the number of links removed. Raises ReadError when the file cannot be read."""
    if project.questionnaire is not None and not replace:
        raise QuestionnaireExists(project.questionnaire.file_name)
    questionnaire = load_questionnaire(path)
    previous = project.questionnaire
    project.questionnaire = questionnaire
    propose_from_questionnaire(project)
    removed = drop_stale_links(project, previous) if previous is not None else 0
    propose_value_labels(project)
    return removed


def questionnaire_summary(questionnaire: Questionnaire) -> list[str]:
    """What was read: the file, the questions by kind, and those to check."""
    questions = questionnaire.questions
    pages = _(" ({n} pages)").format(n=questionnaire.n_pages) if questionnaire.n_pages else ""
    counts = ", ".join(
        f"{sum(1 for q in questions if q.kind == kind)} {label}"
        for kind, label in KINDS.items()
        if any(q.kind == kind for q in questions)
    )
    rows = sum(len(q.rows) for q in questions)
    grids = _(" ; {n} énoncés de grille").format(n=rows) if rows else ""
    lines = [
        _("Questionnaire lu : {name}{pages}").format(name=questionnaire.file_name, pages=pages),
        _("{n} questions : {counts}{grids}.").format(n=len(questions), counts=counts, grids=grids),
    ]
    for question in questions:
        if question.to_check:
            reasons = ", ".join(TO_CHECK.get(code, code) for code in question.to_check)
            lines.append(
                _("À vérifier : {qid} ({reasons}).").format(
                    qid=question.question_id, reasons=reasons
                )
            )
    return lines


def acronym_summary(project: Project) -> list[str]:
    lines = []
    pending = [e.term for e in project.glossary if e.status == "proposed"]
    if pending:
        lines.append(
            _("Sigles définis dans le questionnaire, à valider : {terms}.").format(
                terms=", ".join(pending)
            )
        )
    undefined = undefined_acronyms(project)
    if undefined:
        lines.append(
            _("Sigles probables des noms de variables, sans définition : {terms}.").format(
                terms=", ".join(undefined)
            )
        )
    return lines


# --- Where the project stands (v0.3, dashboard). ---


@dataclass(frozen=True)
class Task:
    """Something waiting for the team, and where the interface shows it."""

    count: int
    text: str
    mode: str  # "questionnaire", "glossary", "variables", ...
    filter: str | None = None  # for the variables


def tasks(project: Project) -> list[Task]:
    """What is waiting, in the recommended order: questionnaire, glossary, links, value
    labels, labels and descriptions. Empty when nothing waits."""
    found: list[Task] = []
    if project.questionnaire is None:
        found.append(Task(1, _("Ajouter le questionnaire de l'étude"), "questionnaire"))
    pending_terms = sum(1 for e in project.glossary if e.status == "proposed")
    if pending_terms:
        found.append(Task(pending_terms, _("Sigles à valider : {n}"), "glossary"))
    undefined = len(undefined_acronyms(project))
    if undefined:
        found.append(Task(undefined, _("Sigles sans définition : {n}"), "glossary"))
    proposed_links = sum(1 for e in project.variables if e.question.status == "proposed")
    if proposed_links:
        found.append(
            Task(
                proposed_links,
                _("Rattachements proposés à réviser : {n}"),
                "variables",
                "to_review",
            )
        )
    if project.questionnaire is not None:
        unlinked = sum(1 for e in project.variables if e.question.value is None)
        if unlinked:
            found.append(
                Task(unlinked, _("Variables sans question : {n}"), "variables", "unlinked")
            )
    labels = sum(1 for e in project.variables if e.value_labels.status == "proposed")
    if labels:
        found.append(
            Task(labels, _("Étiquettes de valeurs à vérifier : {n}"), "variables", "to_review")
        )
    texts = sum(
        1
        for e in project.variables
        if e.label.status == "proposed" or e.description.status == "proposed"
    )
    if texts:
        found.append(
            Task(
                texts,
                _("Libellés ou descriptions proposés : {n}"),
                "variables",
                "to_review",
            )
        )
    return found


# --- The local model (v0.3: shared by the command line and the interface). ---


def project_stem(project_path: Path) -> str:
    """ "etude" for "etude.dd.json": the name the files next to the project start with."""
    name = project_path.name
    return name[: -len(PROJECT_SUFFIX)] if name.endswith(PROJECT_SUFFIX) else project_path.stem


def exchange_dir(project_path: Path) -> Path:
    """Where what is (or would be) sent to the model is kept, next to the project."""
    return project_path.with_name(project_stem(project_path) + ".dd-envois")


# --- Exports (v0.3: shared by the command line and the interface). ---


class UnknownGroups(ValueError):
    """Groups named for the omitted question texts that the project does not have."""

    def __init__(self, unknown: list[str], known: list[str]) -> None:
        super().__init__(", ".join(unknown))
        self.unknown = unknown
        self.known = known


def export_paths(project_path: Path, kind: str) -> tuple[Path, Path]:
    """The codebook and the report next to the project; "-travail" for a work export."""
    stem = project_stem(project_path) + ("-travail" if kind == "work" else "")
    return project_path.with_name(stem + ".xlsx"), project_path.with_name(stem + ".md")


def check_groups(project: Project, omit_groups: tuple[str, ...]) -> None:
    known = [g.group_id for g in project.groups]
    unknown = sorted(set(omit_groups) - set(known))
    if unknown:
        raise UnknownGroups(unknown, known)


def export_codebook(
    project: Project,
    project_path: Path,
    *,
    kind: str = "final",
    omit_groups: tuple[str, ...] = (),
    xlsx: Path | None = None,
    markdown: Path | None = None,
) -> tuple[Path, Path]:
    """Write the Excel codebook and the Markdown report; next to the project by default."""
    check_groups(project, omit_groups)
    default_xlsx, default_markdown = export_paths(project_path, kind)
    xlsx = xlsx or default_xlsx
    markdown = markdown or default_markdown
    write_xlsx(project, xlsx, kind=kind, omit_groups=omit_groups)
    write_markdown(project, markdown, kind=kind, omit_groups=omit_groups)
    return xlsx, markdown


def failure_advice(detail: str | None, endpoint: str, model: str) -> str | None:
    """What to do when the local server failed, for the reasons a person can act on."""
    if detail == "connection":
        return _("Le serveur {endpoint} ne répond pas. Ollama est-il lancé ?").format(
            endpoint=endpoint
        )
    if detail == "http_404":
        return _(
            "Le modèle « {model} » est introuvable sur le serveur. "
            "Avec Ollama, téléchargez-le d'abord : ollama pull {model}"
        ).format(model=model)
    if detail == "timeout":
        return _(
            "Le modèle n'a pas répondu à temps. Sur un ordinateur sans carte graphique, "
            "réduisez la taille des blocs."
        )
    return None
