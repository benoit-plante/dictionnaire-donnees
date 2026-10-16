"""The results document of the notebook (v0.11, step 4, D-089, D-090, D-092): the retained
analyses, in the notebook's order, each recomputed on the database with the decisions in
force (never copied from the notebook), with its heading, its APA sentence, its tables and
its figures, numbered one after the other; at the end, the codebook's fingerprint, the date,
the versions and the list of the analyses, and those left out because impossible.

A retained analysis that changed and waits for a person's confirmation blocks the export.

Since v0.12 (D-099), the document opens with the Method: Participants (with the flow
diagram, Figure 1 by default), Instruments and Analyses, written by templates
(`method_text`); the Results follow, numbered after it. Its figures are confirmed as an
analysis's (D-100).
"""

from __future__ import annotations

import io
import zipfile
from datetime import date
from pathlib import Path

from ddict import i18n
from ddict.analysis import method as method_facts
from ddict.analysis import method_text
from ddict.analysis import notebook as nb
from ddict.analysis import notebook_check as check
from ddict.analysis.apa import Edit, Section, assembled, describe, describe_flow, edited
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import ROLES, TITLES
from ddict.analysis.data import PreparedData
from ddict.analysis.formats import available
from ddict.analysis.report import versions
from ddict.analysis.rscript import r_master
from ddict.export.preparation import needed as preparation_needed
from ddict.export.preparation import render_preparation
from ddict.export.syntax import render_syntax
from ddict.i18n import _, semicolon
from ddict.project import fingerprint
from ddict.project.model import Project


class ExportBlocked(Exception):
    """Retained analyses changed and wait for a confirmation (`ids`)."""

    def __init__(self, ids: list[str]) -> None:
        super().__init__(", ".join(ids))
        self.ids = ids


def heading(entry: nb.Entry) -> str:
    """ "A2 — Test t : comparer deux groupes" (the sheet, § 8, point 6)."""
    return f"{entry.id} — {TITLES[entry.analysis]}"


def _edits(entry: nb.Entry) -> dict[str, Edit]:
    """A person's titles and notes; never a number: the order numbers (D-090)."""
    return {key: Edit(title=e.title, note=e.note) for key, e in entry.edits.items()}


def _variables(book: Codebook, chosen: dict[str, list[str]]) -> str:
    parts = []
    for role, names in chosen.items():
        parts.append(f"{ROLES[role]} : " + ", ".join(book.label(n) for n in names))
    return semicolon().join(parts)


def _method(project, prepared, notebook, found, table: int, figure: int):
    """The sections of the Method, and the numbers of the next table and figure."""
    from ddict.workflow import project_stem

    flow = describe_flow(project, prepared.flow, number=figure)
    sections = [Section("methode", _("Méthode"), "", level=1)]
    sections.append(
        Section(
            "participants",
            _("Participants"),
            "",
            figures=(flow,) if flow else (),
            paragraphs=(method_text.participants(project, found, flow.number if flow else None),),
        )
    )
    figure += 1 if flow else 0
    paragraphs = method_text.instruments(project, prepared, found)
    if paragraphs:
        sections.append(Section("instruments", _("Instruments"), "", paragraphs=tuple(paragraphs)))
    script = project_stem(Path(notebook.project.file)) + "-resultats.R"
    sections.append(
        Section(
            "analyses",
            _("Analyses"),
            "",
            paragraphs=(method_text.analyses(found, script),),
        )
    )
    sections.append(Section("resultats", _("Résultats"), "", level=1))
    return sections, table, figure


def _rules(project) -> list[str]:
    """The exclusion rules, at the end of the document, with their source."""
    lines = []
    for rule in project.exclusions.rules:
        line = f"{rule.id} — {rule.reason}"
        if rule.source:
            line += f" ({rule.source})"
        lines.append(line)
    return [_("Règles d'exclusion :"), *lines] if lines else []


def results_document(
    project: Project,
    prepared: PreparedData,
    notebook: nb.Notebook,
    *,
    language: str | None = None,
    today: str | None = None,
):
    """The ApaDocument of the retained analyses, recomputed. Raises ExportBlocked."""
    return _results(project, prepared, notebook, language=language, today=today)[0]


def _results(project, prepared, notebook, *, language=None, today=None):
    """The document, and the analyses it holds as the R master script takes them
    (identifier, analysis, final names by role, options): from one computation."""
    today = today or date.today().isoformat()
    analyses = []
    with i18n.using(language):
        language = i18n.language()
        statuses = check.check_all(notebook, project, prepared, today=today, always=True)
        statuses.append(check.check_method(notebook, project, prepared, today=today))
        blocked = check.blocking(notebook, statuses)
        if blocked:
            raise ExportBlocked(blocked)
        by_id = {s.entry_id: s for s in statuses}
        book = Codebook(project, prepared)
        listed, left_out = [], []
        found = method_facts.facts(project, prepared, notebook)
        sections, table, figure = _method(
            project, prepared, notebook, found, notebook.first_table, notebook.first_figure
        )
        for entry in notebook.entries:
            if not entry.retained:
                continue
            status = by_id[entry.id]
            if status.state in ("impossible", "no_database") or status.result is None:
                left_out.append(f"{heading(entry)} : {status.reason}")
                continue
            result = status.result
            document = describe(
                project, prepared, result, language=language, first_table=table, first_figure=figure
            )
            document = edited(document, _edits(entry))
            sections.append(
                Section(
                    entry.id, heading(entry), result.sentence, document.tables, document.figures
                )
            )
            listed.append(f"{heading(entry)} — {_variables(book, result.chosen)}")
            analyses.append((entry.id, entry.analysis, result.chosen, dict(entry.options)))
            table += len(document.tables)
            figure += len(document.figures)
        made = versions()
        closing = [
            _("Empreinte du codebook : {fingerprint}.").format(
                fingerprint=fingerprint.short(project)
            ),
            _("Produit le {date} par dictionnaire-donnees {version} ({others}).").format(
                date=today,
                version=made["dictionnaire-donnees"],
                others=", ".join(
                    f"{k} {v}" for k, v in made.items() if k != "dictionnaire-donnees"
                ),
            ),
            _("Analyses du document :"),
            *listed,
            *_rules(project),
        ]
        if left_out:
            closing += [_("Analyses retenues mais écartées, impossibles à calculer :"), *left_out]
        document = assembled(language, sections, closing, fingerprint.short(project))
        return document, analyses


def results_paths(project_path: Path) -> dict[str, Path]:
    """ "etude-resultats.docx", "-resultats-graphiques.xlsx", "-resultats-R.zip" (D-092)."""
    from ddict.workflow import project_stem

    stem = project_stem(project_path) + "-resultats"
    return {
        "docx": project_path.with_name(stem + ".docx"),
        "xlsx": project_path.with_name(stem + "-graphiques.xlsx"),
        "r": project_path.with_name(stem + "-R.zip"),
    }


def write_results(
    project: Project,
    prepared: PreparedData,
    notebook: nb.Notebook,
    project_path: Path,
    *,
    language: str | None = None,
    today: str | None = None,
) -> list[Path]:
    """Write the results document, its charts workbook and the R master script next to the
    project, replacing the former ones (D-092). Raises ExportBlocked. The notebook is
    updated in memory (an unchanged entry gets the new fingerprint): the caller saves it."""
    today = today or date.today().isoformat()
    document, analyses = _results(project, prepared, notebook, language=language, today=today)
    paths = results_paths(project_path)
    written = []
    for found in available(document):
        path = paths[found.key]
        path.write_bytes(found.render(document))
        written.append(path)
    paths["r"].write_bytes(
        r_bundle(project, project_path, analyses, language=document.language, today=today)
    )
    return [*written, paths["r"]]


def r_bundle(
    project: Project,
    project_path: Path,
    analyses: list,
    *,
    language: str | None = None,
    today: str | None = None,
) -> bytes:
    """The R master script (v0.11, step 5), with the command file and the preparation
    script it runs, in a zip: to run in the database's folder."""
    from ddict.workflow import project_stem

    stem = project_stem(project_path)
    today = today or date.today().isoformat()
    with i18n.using(language):
        files = {
            f"{stem}-resultats.R": r_master(project, stem, analyses, today),
            f"{stem}-metadonnees.R": render_syntax(project, "r", today),
        }
        if preparation_needed(project):
            files[f"{stem}-preparation.R"] = render_preparation(project, "r", today)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, text.encode("utf-8"))
    return out.getvalue()
