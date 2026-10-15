"""Steps of the workflow shared by the command line and the interface (v0.3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ddict import platforms
from ddict.export import write_markdown, write_xlsx
from ddict.export.documented import CopyError, CopyResult, find_database, write_documented_copy
from ddict.export.syntax import SUFFIXES, write_syntax
from ddict.export.wording import entry_anomalies
from ddict.glossary import propose_from_questionnaire, undefined_acronyms
from ddict.i18n import N_, Texts, _
from ddict.io import read_database
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import PROJECT_SUFFIX, build_project, save_project
from ddict.project.model import Project, Questionnaire
from ddict.questionnaire import language as study_language
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
    study_language.update(project)  # from the file's labels, when they say (v0.5)
    save_project(project, output)
    return project, output


def profile_summary(project: Project) -> str:
    """One line: "34 variables, 200 lignes ; 4 variables sensibles ; 10 avec signalements"."""
    sensitive = sum(
        1 for e in project.variables if (e.privacy.privacy_class.value or "ordinary") != "ordinary"
    )
    # The same count as the "Avec signalements" filter of the review (notes excluded).
    flagged = sum(1 for e in project.variables if entry_anomalies(e))
    return _(
        "{n} variables, {rows} lignes ; {sensitive} variables sensibles ; "
        "{flagged} avec signalements."
    ).format(
        n=len(project.variables),
        rows=project.source.n_rows,
        sensitive=sensitive,
        flagged=flagged,
    )


def platform_notes(project: Project) -> list[str]:
    """What to know about a survey platform export (v0.7): which platform, and that its .sav
    file is better than its Excel or CSV export, which has neither codes nor labels."""
    platform = platforms.by_name(project.source.platform)
    if platform is None:
        return []
    notes = [_("Export {platform} reconnu.").format(platform=platform.title)]
    if project.source.format in ("xlsx", "csv"):
        notes.append(
            _(
                "Si vous avez aussi l'export .sav de ce sondage, préférez-le : il garde les "
                "codes des réponses et leurs étiquettes, que l'export {format} remplace par "
                "du texte."
            ).format(format=project.source.format.upper())
        )
    return notes


# --- The questionnaire (v0.2), from the command line or the interface. ---

TO_CHECK = Texts(
    {
        "grid_header_unclear": N_("titres de colonnes collés"),
        "grid_without_header": N_("grille sans titres de colonnes"),
        "grid_rows_unnumbered": N_("énoncés de grille non numérotés"),
    }
)
KINDS = Texts(
    {
        "open": N_("ouvertes"),
        "single": N_("à choix unique"),
        "checkbox": N_("à cocher"),
        "grid": N_("grilles"),
    }
)


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
    study_language.update(project)  # the questionnaire's language (v0.5)
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
    sentinels = sum(
        1
        for e in project.variables
        for code in e.profile.suspect_missing_codes
        if all(d.code != code for d in e.sentinel_decisions)
    )
    if sentinels:
        found.append(
            Task(sentinels, _("Codes suspects à confirmer : {n}"), "variables", "suspects")
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
    language: str | None = None,
) -> tuple[Path, Path]:
    """Write the Excel codebook and the Markdown report; next to the project by default.
    `language`: of the codebook, by default that of the interface (D-032)."""
    check_groups(project, omit_groups)
    default_xlsx, default_markdown = export_paths(project_path, kind)
    xlsx = xlsx or default_xlsx
    markdown = markdown or default_markdown
    write_xlsx(project, xlsx, kind=kind, omit_groups=omit_groups, language=language)
    write_markdown(project, markdown, kind=kind, omit_groups=omit_groups, language=language)
    return xlsx, markdown


def syntax_paths(project_path: Path) -> dict[str, Path]:
    """The command files next to the project: "etude-metadonnees.sps" and ".R"."""
    stem = project_stem(project_path) + "-metadonnees"
    return {program: project_path.with_name(stem + suffix) for program, suffix in SUFFIXES.items()}


def export_syntax(
    project: Project, project_path: Path, *, language: str | None = None
) -> dict[str, Path]:
    """Write the SPSS and R command files: accepted decisions only (D-025, D-030)."""
    paths = syntax_paths(project_path)
    write_syntax(project, paths, language=language)
    return paths


def documented_copy(
    project: Project,
    project_path: Path,
    *,
    database: Path | None = None,
    target: Path | None = None,
    replace: bool = False,
) -> CopyResult:
    """The documented copy of the database, next to it (D-026)."""
    found = find_database(project, project_path, database)
    return write_documented_copy(project, found, target, replace=replace)


def copy_error_text(error: CopyError, source_name: str) -> str:
    """Why the documented copy was not written, in plain French."""
    if error.reason == "exists":
        return _("{name} existe déjà. Rien n'a été écrit ; confirmez pour le remplacer.").format(
            name=Path(error.detail).name
        )
    if error.reason == "not_found":
        return _(
            "La base {name} est introuvable à côté du projet. Placez-la dans le même dossier "
            "que le projet, ou indiquez où elle se trouve."
        ).format(name=source_name)
    if error.reason == "other_file":
        return _(
            "{name} n'est plus le fichier d'où vient le projet : son contenu a changé. Rien "
            "n'a été écrit."
        ).format(name=Path(error.detail).name)
    if error.reason == "same_file":
        return _("La copie ne peut pas porter le nom de la base d'origine.")
    if error.reason == "not_identical":
        return _(
            "La copie relue ne correspondait pas à l'original ({n} cases différentes) : elle a "
            "été supprimée. Utilisez plutôt les fichiers de commandes, et signalez ce problème."
        ).format(n=error.detail)
    return _("La copie n'a pas pu être écrite : {detail}. Rien n'a été gardé.").format(
        detail=error.detail
    )


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
