"""Steps of the workflow shared by the command line and the interface (v0.3)."""

from __future__ import annotations

import glob
import re
from dataclasses import dataclass
from pathlib import Path

from ddict import naming, platforms, waves
from ddict.analysis.report import AnalysisFiles
from ddict.export import write_markdown, write_xlsx
from ddict.export.context import write_context
from ddict.export.documented import CopyError, CopyResult, find_database, write_documented_copy
from ddict.export.preparation import needed as preparation_needed
from ddict.export.preparation import write_preparation
from ddict.export.syntax import SUFFIXES, write_syntax
from ddict.export.wording import entry_anomalies
from ddict.glossary import propose_from_questionnaire, undefined_acronyms
from ddict.i18n import N_, Texts, _
from ddict.io import read_database
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import PROJECT_SUFFIX, build_project, ondisk, save_project
from ddict.project.decisions import is_accepted
from ddict.project.model import Project, Questionnaire
from ddict.questionnaire import language as study_language
from ddict.questionnaire import load_questionnaire
from ddict.questionnaire.labels import propose_value_labels
from ddict.questionnaire.link import (
    check_against_platform,
    drop_stale_links,
    platform_coverage,
    project_questions,
)


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
    save_project(project, output, overwrite=replace)
    return project, output


def profile_summary(project: Project) -> str:
    """One line: "34 variables, 200 lignes ; 4 variables sensibles ; 10 avec signalements"."""
    sensitive = sum(
        1 for e in project.variables if (e.privacy.privacy_class.value or "ordinary") != "ordinary"
    )
    # The same count as the "Avec signalements" filter of the review (notes excluded).
    flagged = sum(1 for e in project.variables if entry_anomalies(e))
    if project.source is None:
        return _("{n} variables prévues ; pas encore de base.").format(n=len(project.variables))
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
    platform = platforms.of(project)
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


# What each format lacks of a .sav file (D-054): the tool guesses it.
_LACKS_ALL = N_("ni étiquettes des valeurs, ni codes de valeurs manquantes, ni niveaux de mesure")
FORMAT_LACKS = {
    "csv": _LACKS_ALL,
    "xlsx": _LACKS_ALL,
    "sas7bdat": _LACKS_ALL,  # its value labels live in a format catalog, not read
    "dta": N_("ni codes de valeurs manquantes, ni niveaux de mesure"),
}
FORMAT_TITLES = {"csv": "CSV", "xlsx": "Excel", "sas7bdat": "SAS", "dta": "Stata"}


def format_note(project: Project) -> str | None:
    """Below a database that is not a .sav file (D-054): what was guessed, to check. None
    for a .sav, or when the platform note already advises its .sav export."""
    source = project.source
    if source is None:
        return None
    lacks = FORMAT_LACKS.get(source.format)
    if lacks is None or (platforms.by_name(source.platform) and source.format in ("xlsx", "csv")):
        return None
    return _(
        "Un fichier {format} ne contient {lacks} : l'outil les devine, vérifiez-les. "
        "Un export .sav, quand il est possible, donne de meilleurs résultats."
    ).format(format=FORMAT_TITLES[source.format], lacks=_(lacks))


# --- The questionnaire (v0.2), from the command line or the interface. ---

TO_CHECK = Texts(
    {
        "grid_header_unclear": N_("titres de colonnes collés"),
        "grid_without_header": N_("grille sans titres de colonnes"),
        "grid_rows_unnumbered": N_("énoncés de grille non numérotés"),
        "platform_rows_differ": N_("pas le même nombre d'énoncés que dans la base"),
        "platform_options_differ": N_("pas le même nombre d'options que dans la base"),
        "kind_from_platform": N_("cases à cocher d'après la base"),
        "not_in_platform_structure": N_("aucune question correspondante dans la base"),
        "found_by_platform": N_("lue comme un paragraphe, retrouvée par la structure de la base"),
        # v0.20 (D-148): a LimeSurvey structure file.
        "platform_text_differs": N_("autres mots que dans la base, au même code"),
        "lss_type_unsupported": N_("type de question LimeSurvey que l'outil ne lit pas encore"),
        "lss_expression": N_("contient une expression LimeSurvey entre accolades"),
    }
)
KINDS = Texts(
    {
        "open": N_("ouvertes"),
        "single": N_("à choix unique"),
        "checkbox": N_("à cocher"),
        "grid": N_("grilles"),
        "display": N_("textes d'affichage"),
    }
)


class QuestionnaireExists(ValueError):
    """The project has a questionnaire already: replacing it may remove links."""


class DesignedQuestionnaire(ValueError):
    """The project's questionnaire is designed in the tool (v0.20): no file replaces it."""


# Characters Windows refuses in a file name.
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def design_path(folder: Path | str, name: str) -> Path:
    """The project file of a questionnaire designed in the tool: its name, in the folder
    chosen (v0.20, D-145); a character Windows refuses becomes "-"."""
    stem = _UNSAFE.sub("-", name.strip()).rstrip(". ")
    return Path(folder) / f"{stem}.dd.json"


def create_design(folder: Path | str, name: str, language: str, today: str) -> Path:
    """A project to design a questionnaire, before its collection (v0.20): written in the
    folder chosen, never over an existing file (ProjectExists). Raises DesignError for a
    name that is empty, FileNotFoundError for a folder that is not there."""
    from ddict import design

    project = design.new_project(name, language, today)
    if not Path(folder).is_dir():
        raise FileNotFoundError(str(folder))
    path = design_path(folder, name)
    if path.exists():
        raise ProjectExists(str(path))
    save_project(project, path)
    return path


def add_questionnaire(project: Project, path: Path | str, *, replace: bool = False) -> int:
    """Read the questionnaire into the project (not saved): acronyms it defines become
    proposals, links to a former questionnaire are removed, value labels are refreshed.
    Returns the number of links removed. Raises ReadError when the file cannot be read."""
    if project.design is not None:  # v0.20: the questionnaire designed in the tool
        raise DesignedQuestionnaire(project.questionnaire.file_name)
    if project.questionnaire is not None and not replace:
        raise QuestionnaireExists(project.questionnaire.file_name)
    # The kind of each question of a platform's export header, from the database (v0.7).
    kinds = {q.rank: q.kind for q in project_questions(project) if q.kind != "single"}
    questionnaire = load_questionnaire(path, kinds, project.settings.language)
    previous = project.questionnaire
    project.questionnaire = questionnaire
    check_against_platform(project)  # v0.7: the structure of a platform export
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


def platform_summary(project: Project) -> list[str]:
    """How the questionnaire covers the questions of a platform export (v0.7)."""
    platform = platforms.of(project)
    asked, unmatched = platform_coverage(project)
    if platform is None or not asked:
        return []
    if unmatched:
        return [
            _(
                "Structure de l'export {platform} : {n} questions, dont {m} sans question "
                "concordante dans ce questionnaire."
            ).format(platform=platform.title, n=asked, m=unmatched)
        ]
    return [
        _(
            "Structure de l'export {platform} : {n} questions, toutes retrouvées dans ce "
            "questionnaire."
        ).format(platform=platform.title, n=asked)
    ]


# --- New names (v0.7), from the command line or the interface. ---


def rename(
    project: Project,
    *,
    suffix: str | None = None,
    prefix: str | None = None,
    reference: Path | str | None = None,
) -> waves.WaveReport | None:
    """Set the mark of the wave if given ("_t2" as a suffix, "t2_" as a prefix); take the
    names of an earlier wave if given (its project, documented copy or table of names,
    D-052); then propose stems and names by the rules where nothing is decided (not saved).
    Returns the report of the differences between the waves, with a reference."""
    if suffix and prefix:
        raise naming.NamingError(["suffix_and_prefix"])
    if suffix:
        naming.set_wave(project, suffix.strip("_"), "suffix")
    elif prefix:
        naming.set_wave(project, prefix.strip("_"), "prefix")
    if reference is None:
        naming.propose(project)
        return None
    earlier = waves.read_earlier_wave(reference)
    report = waves.match(project, earlier)
    waves.apply(project, earlier, report)
    return report


def wave_report_path(project_path: Path) -> Path:
    return project_path.with_name(f"{project_stem(project_path)}-ecarts-vagues.md")


def write_wave_report(project: Project, report: waves.WaveReport, project_path: Path) -> Path:
    """Write the report of differences between the waves next to the project."""
    path = wave_report_path(project_path)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(waves.report_markdown(project, report))
    return path


def wave_summary(report: waves.WaveReport) -> list[str]:
    lines = [
        _(
            "Vague précédente : {matched} variables appariées, {added} ajoutées, "
            "{candidates} à apparier par une personne, {removed} retirées, {changed} aux "
            "étiquettes de valeurs changées."
        ).format(
            matched=len(report.matches),
            added=len(report.added),
            candidates=len(report.candidates),
            removed=len(report.removed),
            changed=len(report.value_labels_changed),
        )
    ]
    if report.fragile:
        lines.append(
            _(
                "{n} appariements reposent sur le seul nom d'origine : à vérifier, la "
                "numérotation de la plateforme a pu changer."
            ).format(n=report.fragile)
        )
    return lines


def naming_summary(project: Project) -> list[str]:
    counts = naming.summary(project)
    lines = [
        _("{proposed} noms proposés, {accepted} acceptés, {to_name} variables à nommer.").format(
            **counts
        )
    ]
    if counts["conflicts"]:
        lines.append(
            _("{n} variables ont un nom en conflit avec un autre.").format(n=counts["conflicts"])
        )
    wave = project.settings.naming
    if wave.wave:
        mark = f"_{wave.wave}" if wave.position == "suffix" else f"{wave.wave}_"
        lines.append(_("Marque de vague : {mark}").format(mark=mark))
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


@dataclass(frozen=True)
class NotebookState:
    """What the notebook's recomputation says (v0.16): computed by the interface, which
    keeps it while nothing changes, since it reads the database."""

    to_confirm: int  # retained analyses, or the Method, whose numbers changed
    impossible: int  # analyses that can no longer be computed


def tasks(
    project: Project,
    project_path: Path | None = None,
    notebook: NotebookState | None = None,
) -> list[Task]:
    """What is waiting, in the recommended order: questionnaire, glossary, links, value
    labels, labels and descriptions; then (v0.16) the plan to freeze, the notebook's numbers
    to confirm, the Method's holes, the draft to check. Empty when nothing waits. Without
    the project's path or the notebook's state, those parts are left out."""
    found: list[Task] = []
    if project.design is not None:  # v0.20: the review of the designed questionnaire, first
        from ddict import design_points

        open_points = len(design_points.points(project))
        if open_points:
            found.append(Task(open_points, _("Points de relecture : {n}"), "design_review"))
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
        for code in e.suspect_codes
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
    levels = sum(1 for e in project.variables if e.measure_level.status == "proposed")
    if levels:  # v0.8 (D-063): decided on the "Base" page
        found.append(Task(levels, _("Niveaux de mesure proposés : {n}"), "base"))
    # New names (v0.7): only once the team has begun to rename.
    if any(e.new_name.value for e in project.variables):
        grids = sum(
            1 for g in project.groups if g.kind == "scale" and not is_accepted(g.name_prefix)
        )
        if grids:
            found.append(Task(grids, _("Grilles sans préfixe de noms : {n}"), "groups"))
        proposed = sum(1 for e in project.variables if e.new_name.status == "proposed")
        if proposed:
            found.append(Task(proposed, _("Noms proposés à valider : {n}"), "names", "proposed"))
        clashes = len(naming.conflicts(project))
        if clashes:
            found.append(Task(clashes, _("Noms en conflit : {n}"), "names", "conflicts"))
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
    found.extend(_writing_tasks(project, project_path, notebook))
    return found


def _writing_tasks(
    project: Project, project_path: Path | None, notebook: NotebookState | None
) -> list[Task]:
    """From the analysis to the article (v0.16): only what the files already say."""
    from ddict.analysis import notebook as nb
    from ddict.analysis.method_text import instrument_holes
    from ddict.analysis.notebook_export import SUFFIX
    from ddict.analysis.verify import paths as report_paths

    found: list[Task] = []
    if project.plan.hypotheses and project.plan.frozen is None:
        found.append(Task(1, _("Plan à figer"), "plan"))
    if notebook is not None and notebook.to_confirm:
        found.append(Task(notebook.to_confirm, _("Chiffres à confirmer au carnet : {n}"),
                          "notebook"))  # fmt: skip
    if notebook is not None and notebook.impossible:
        found.append(Task(notebook.impossible, _("Analyses impossibles à calculer : {n}"),
                          "notebook"))  # fmt: skip
    if project_path is None or not nb.notebook_path(project_path).is_file():
        return found
    holes = instrument_holes(project)
    if holes:
        found.append(Task(holes, _("Trous de la Méthode à combler (groupes) : {n}"), "groups"))
    draft = project_path.with_name(project_stem(project_path) + SUFFIX + ".docx")
    report = report_paths(draft)["md"]
    if draft.is_file() and (not report.is_file() or report.stat().st_mtime < draft.stat().st_mtime):
        found.append(Task(1, _("Vérifier les chiffres de l'ébauche"), "verify"))
    return found


# --- The AI (v0.3: shared by the command line and the interface). ---


def project_stem(project_path: Path) -> str:
    """ "etude" for "etude.dd.json": the name the files next to the project start with."""
    name = project_path.name
    return name[: -len(PROJECT_SUFFIX)] if name.endswith(PROJECT_SUFFIX) else project_path.stem


def leftover_notes(project_path: Path) -> list[str]:
    """A save of the project or of its notebook was interrupted: its temporary file is
    left. Said when the project is opened; the tool never removes it (v0.17)."""
    from datetime import datetime

    from ddict.analysis.notebook import notebook_path

    notes = []
    for path in (project_path, notebook_path(project_path)):
        left = ondisk.leftover(path)
        if left is None:
            continue
        try:
            when = datetime.fromtimestamp(left.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            when = "?"
        notes.append(
            _(
                "Un enregistrement a été interrompu (le {date}) : le fichier {name} est resté. "
                "{kept} est le dernier enregistré en entier ; le fichier {name} peut être "
                "supprimé."
            ).format(
                date=when,
                name=left.name,
                kept=_("Le projet ouvert") if path == project_path else _("Le carnet"),
            )
        )
    return notes


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


def export_name_table(project: Project, project_path: Path) -> Path | None:
    """The table of names (D-052) next to the project, when a person accepted new names:
    "etude-correspondance.csv", the reference of the next wave."""
    if not any(e.name != naming.final_name(e) for e in project.variables):
        return None
    path = project_path.with_name(project_stem(project_path) + "-correspondance.csv")
    waves.write_name_table(project, path)
    return path


def context_paths(project_path: Path) -> tuple[Path, Path]:
    """The analysis context next to the project (v0.8, D-058): "etude-contexte.md" and
    "etude-datapackage.json"."""
    stem = project_stem(project_path)
    return (
        project_path.with_name(stem + "-contexte.md"),
        project_path.with_name(stem + "-datapackage.json"),
    )


def export_context(
    project: Project,
    project_path: Path,
    *,
    statistics: bool = False,
    omit_groups: tuple[str, ...] = (),
    language: str | None = None,
) -> tuple[Path, ...]:
    """Write the analysis context: accepted values only; statistics only on request (D-059).
    Returns the files written: without a database yet (v0.20), the Markdown only."""
    check_groups(project, omit_groups)
    markdown, package = context_paths(project_path)
    write_context(
        project,
        markdown,
        package,
        statistics=statistics,
        omit_groups=omit_groups,
        language=language,
    )
    return (markdown, package) if project.source is not None else (markdown,)


def syntax_paths(project_path: Path) -> dict[str, Path]:
    """The command files next to the project: "etude-metadonnees.sps" and ".R"."""
    stem = project_stem(project_path) + "-metadonnees"
    return {program: project_path.with_name(stem + suffix) for program, suffix in SUFFIXES.items()}


def preparation_paths(project_path: Path) -> dict[str, Path]:
    """The preparation scripts (v0.8): "etude-preparation.sps" and ".R"."""
    stem = project_stem(project_path) + "-preparation"
    return {program: project_path.with_name(stem + suffix) for program, suffix in SUFFIXES.items()}


def export_syntax(
    project: Project, project_path: Path, *, language: str | None = None
) -> dict[str, Path]:
    """Write the SPSS and R command files: accepted decisions only (D-025, D-030); and, when
    the project has reversed items or a scoring, the preparation scripts (v0.8, D-062)."""
    paths = syntax_paths(project_path)
    write_syntax(project, paths, language=language)
    if not preparation_needed(project):
        return paths
    preparation = preparation_paths(project_path)
    write_preparation(project, preparation, language=language)
    return {**paths, **{f"{p}-preparation": path for p, path in preparation.items()}}


def analysis_files(project_path: Path) -> AnalysisFiles:
    """The files of the next analysis (v0.9, D-078): "etude-analyse-1.md", ".xlsx" and ".R",
    and its APA tables and figures (v0.10: ".docx", "-graphiques.xlsx"), with the first
    number none of them takes yet; and the R files that script runs."""
    stem = project_stem(project_path)
    number = 1
    pattern = glob.escape(stem)  # a project named "étude [2]" stays a plain name
    while any(
        any(project_path.parent.glob(f"{pattern}-analyse-{number}{tail}*")) for tail in (".", "-")
    ):
        number += 1
    name = f"{stem}-analyse-{number}"
    return AnalysisFiles(
        markdown=project_path.with_name(name + ".md"),
        xlsx=project_path.with_name(name + ".xlsx"),
        r=project_path.with_name(name + ".R"),
        syntax=syntax_paths(project_path)["r"],
        preparation=preparation_paths(project_path)["r"],
    )


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


def copy_error_text(error: CopyError, project: Project) -> str:
    """Why the documented copy was not written, or the database not found, in plain French."""
    if error.reason == "no_base":
        return _(
            "Ce projet n'a pas encore de base : elle s'ouvrira quand les réponses seront arrivées."
        )
    source_name = project.source.name if project.source is not None else ""
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
    if error.reason == "name_conflict":
        return _(
            "Deux variables auraient le même nom dans la copie : réglez les conflits de "
            "noms sur la page « Noms ». Rien n'a été écrit."
        )
    if error.reason == "not_identical":
        return _(
            "La copie relue ne correspondait pas à l'original ({n} cases différentes) : elle a "
            "été supprimée. Utilisez plutôt les fichiers de commandes, et signalez ce problème."
        ).format(n=error.detail)
    return _("La copie n'a pas pu être écrite : {detail}. Rien n'a été gardé.").format(
        detail=error.detail
    )


def failure_advice(detail: str | None, endpoint: str, model: str) -> str | None:
    """What to do when the AI failed, for the reasons a person can act on."""
    if detail == "connection":
        return _(
            "Impossible de joindre {endpoint} : vérifiez la connexion Internet et l'adresse "
            "(page « IA »)."
        ).format(endpoint=endpoint)
    if detail == "http_404":
        return _(
            "Le modèle « {model} » est introuvable à cette adresse : vérifiez son nom sur la "
            "page « IA »."
        ).format(model=model)
    if detail == "timeout":
        return _("Le modèle n'a pas répondu à temps : réessayez, ou réduisez la taille des blocs.")
    # Through an API key (v0.18).
    if detail == "auth":
        return _(
            "La clé d'API est refusée ou absente : enregistrez-la sur la page « IA » "
            "(ou par « ddict ia cle »)."
        )
    if detail == "key_store":
        return _("Le gestionnaire d'identifiants de Windows n'a pas donné la clé d'API.")
    if detail == "bad_request":
        return _(
            "Le service a refusé la demande ; son explication est gardée dans le dossier des "
            "envois, à côté du projet."
        )
    if detail == "rate_limit":
        return _("Trop de demandes pour cette clé : réessayez dans quelques minutes.")
    if detail == "overloaded":
        return _("Le service est surchargé : réessayez plus tard.")
    return None


def advice_error_text(error) -> str:
    """Why the objective was not sent to the model (v0.9, D-079)."""
    if error.reason == "empty":
        return _("Écrivez d'abord l'objectif de l'analyse.")
    if error.reason == "too_large":
        return _(
            "La base compte trop de variables : le message dépasserait ce que le modèle peut "
            "lire. Rien n'a été envoyé ; choisissez l'analyse vous-même."
        )
    from ddict.llm.advise import MAX_OBJECTIVE_CHARS

    return _("L'objectif est trop long : {n} caractères au plus.").format(n=MAX_OBJECTIVE_CHARS)
