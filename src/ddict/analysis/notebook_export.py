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

Since v0.13 (D-106, D-107), the document is the draft of an IMRaD article,
`<projet>-article.docx`: the title page and the abstract (holes), the Introduction with the
hypotheses of the frozen plan, the Method with its paragraph "Plan d'analyse", the Results,
the Discussion and the References (`article_text`).
"""

from __future__ import annotations

import io
import zipfile
from datetime import date
from pathlib import Path

from ddict import i18n
from ddict.analysis import article_text as article
from ddict.analysis import method as method_facts
from ddict.analysis import method_text, plan_notebook
from ddict.analysis import notebook as nb
from ddict.analysis import notebook_check as check
from ddict.analysis.apa import (
    Edit,
    Section,
    assembled,
    describe,
    describe_flow,
    edited,
    hole,
    plain,
    rich,
)
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import ROLES, TITLES
from ddict.analysis.data import PreparedData
from ddict.analysis.formats import available
from ddict.analysis.report import versions
from ddict.analysis.rscript import r_master
from ddict.export.preparation import needed as preparation_needed
from ddict.export.preparation import render_preparation
from ddict.export.syntax import render_syntax
from ddict.i18n import _, colon, semicolon
from ddict.project import fingerprint
from ddict.project.model import Project

SUFFIX = "-article"  # v0.13 (D-106); "-resultats" before


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
        parts.append(ROLES[role] + colon() + ", ".join(book.label(n) for n in names))
    return semicolon().join(parts)


def script_name(project_path: Path) -> str:
    """ "etude-article.R": the R master script, named in the Method (A5) and in the zip."""
    from ddict.workflow import project_stem

    return project_stem(project_path) + SUFFIX + ".R"


def _front(project) -> list[Section]:
    """The title page, the abstract and the Introduction, under the article's title."""
    title = (hole(_("titre")),)
    return [
        Section("titre", "", "", paragraphs=tuple(article.title_page()), level=1,
                break_after=True),
        Section("resume", _("Résumé"), "", paragraphs=tuple(article.abstract()), level=1,
                break_after=True),
        Section("introduction", plain(title), "",
                paragraphs=tuple(article.introduction(project)), level=1, title=title),
    ]  # fmt: skip


def _method(project, prepared, notebook, found, table: int, figure: int, tested=None):
    """The sections of the Method, and the numbers of the next table and figure."""
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
    script = script_name(Path(notebook.project.file))
    sections.append(
        Section(
            "analyses",
            _("Analyses"),
            "",
            paragraphs=(method_text.analyses(found, script),),
        )
    )
    if plan_notebook.frozen(project):
        sections.append(
            Section(
                "plan",
                _("Plan d'analyse"),
                "",
                paragraphs=(article.plan_paragraph(project, notebook, tested),),
            )
        )
    sections.append(Section("resultats", _("Résultats"), "", level=1))
    return sections, table, figure


def _back(project, notebook, found, middle) -> list[Section]:
    """The Discussion and the References."""
    opening, ending = article.discussion_frame(project)
    references = article.references(
        project, notebook, feldt=method_text.cites_feldt(project, found)
    )
    return [
        Section("discussion", _("Discussion"), "", paragraphs=(*opening, *middle, *ending),
                level=1),
        Section("references", _("Références"), "", paragraphs=tuple(references), level=1,
                break_before=True),
    ]  # fmt: skip


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


def _tested(project, prepared, notebook, by_id) -> dict[str, article.Tested]:
    """Each hypothesis of the frozen plan whose entry is retained and computed."""
    found = {}
    linked = {e.hypothesis: e for e in notebook.entries if e.hypothesis}
    for hypothesis in project.plan.hypotheses:
        entry = linked.get(hypothesis.id)
        status = by_id.get(entry.id) if entry is not None else None
        if entry is None or not entry.retained or status is None or status.result is None:
            continue
        if status.state in ("impossible", "no_database"):
            continue
        statistics = entry.computed.statistics
        variable = None
        if hypothesis.effect.kind == "predictor":
            try:
                variable = nb.resolve(project, hypothesis.effect.variable)
            except nb.NotebookError:
                variable = None
        m = statistics.get(plan_notebook.ADJ_M)
        found[hypothesis.id] = article.Tested(
            hypothesis,
            status.result,
            plan_notebook.effect_p_key(project, prepared, hypothesis, entry),
            statistics.get(plan_notebook.P_ADJ),
            int(m) if m is not None else None,
            variable,
        )
    return found


def _family_tested(project, tested) -> dict[str, int]:
    """How many hypotheses of each family could be tested."""
    counts: dict[str, int] = {}
    for hypothesis in project.plan.hypotheses:
        if hypothesis.kind == "confirmatory" and hypothesis.family and hypothesis.id in tested:
            counts[hypothesis.family] = counts.get(hypothesis.family, 0) + 1
    return counts


class _Results:
    """The sections of the Results, their tables and figures numbered as they come."""

    def __init__(self, project, prepared, notebook, language, table, figure):
        self.project, self.prepared, self.notebook = project, prepared, notebook
        self.language, self.table, self.figure = language, table, figure
        self.book = Codebook(project, prepared)
        self.sections: list[Section] = []
        self.listed: list[str] = []
        self.analyses: list = []

    def entry(self, entry, result, key, title, level=2, sentence=None, tested=None):
        document = describe(
            self.project, self.prepared, result, language=self.language,
            first_table=self.table, first_figure=self.figure,
        )  # fmt: skip
        document = edited(document, _edits(entry))
        if tested is not None:
            document = article.adjusted_tables(document, tested, self.project.plan.correction)
        self.sections.append(
            Section(key, title, result.sentence if sentence is None else sentence,
                    document.tables, document.figures, level=level)
        )  # fmt: skip
        self.listed.append(f"{heading(entry)} — {_variables(self.book, result.chosen)}")
        self.analyses.append((entry.id, entry.analysis, result.chosen, dict(entry.options)))
        self.table += len(document.tables)
        self.figure += len(document.figures)

    def hypothesis(self, hypothesis, tested, deviation, level):
        title = f"{hypothesis.id} — {hypothesis.statement}"
        if tested is None:
            text = article._sentences([
                rich(deviation),
                (hole(_("raison de l'écart au plan pour {id}").format(id=hypothesis.id)),),
            ])  # fmt: skip
            self.sections.append(Section(hypothesis.id, title, "", paragraphs=(text,),
                                         level=level))  # fmt: skip
            return
        entry = next(e for e in self.notebook.entries if e.hypothesis == hypothesis.id)
        method = self.project.plan.correction
        sentence = article.analysis_sentence(tested, method)
        effect = article.effect_only(self.book, tested, method)
        sentence = f"{sentence} {effect}".strip()
        self.entry(entry, tested.result, hypothesis.id, title, level, sentence, tested)


def _ordered(project, prepared, notebook, by_id, builder, tested):
    """The Results of a frozen plan (§ 11): the descriptive entries, a section per
    confirmatory hypothesis, then the exploratory analyses."""
    deviations = {d.hypothesis: d.text for d in plan_notebook.deviations(
        notebook, project, list(by_id.values()))}  # fmt: skip
    usable = [
        e for e in notebook.entries
        if e.retained and by_id[e.id].result is not None
        and by_id[e.id].state not in ("impossible", "no_database")
    ]  # fmt: skip
    states = {e.id: plan_notebook.state(notebook, project, e) for e in usable}
    for entry in usable:
        if states[entry.id].kind == "descriptive":
            builder.entry(entry, by_id[entry.id].result, entry.id, heading(entry))
    for hypothesis in project.plan.hypotheses:
        if hypothesis.kind == "confirmatory":
            builder.hypothesis(hypothesis, tested.get(hypothesis.id),
                               deviations.get(hypothesis.id, ""), 2)  # fmt: skip
    exploratory_hypotheses = [h for h in project.plan.hypotheses if h.kind == "exploratory"]
    others = [e for e in usable if states[e.id].kind in ("variant", "exploratory", "superseded")]
    if exploratory_hypotheses or others:
        builder.sections.append(Section("exploratoires", _("Analyses exploratoires"), "", level=2))
    for hypothesis in exploratory_hypotheses:
        builder.hypothesis(hypothesis, tested.get(hypothesis.id),
                           deviations.get(hypothesis.id, ""), 3)  # fmt: skip
    for entry in others:
        result = by_id[entry.id].result
        state = states[entry.id]
        sentence = result.sentence
        if state.kind == "variant":
            detail = state.detail[:1].lower() + state.detail[1:]
            sentence = (
                _("Variante de {id} : {detail}.").format(id=state.hypothesis, detail=detail)
                + " "
                + sentence
            )
        builder.entry(entry, result, entry.id, heading(entry), 3, sentence)
    return deviations, bool(others)


def _results(project, prepared, notebook, *, language=None, today=None):
    """The document, and the analyses it holds as the R master script takes them
    (identifier, analysis, final names by role, options): from one computation."""
    today = today or date.today().isoformat()
    with i18n.using(language):
        language = i18n.language()
        statuses = check.check_all(notebook, project, prepared, today=today, always=True)
        statuses.append(check.check_method(notebook, project, prepared, today=today))
        blocked = check.blocking(notebook, statuses)
        if blocked:
            raise ExportBlocked(blocked)
        by_id = {s.entry_id: s for s in statuses}
        frozen = plan_notebook.frozen(project)
        tested = _tested(project, prepared, notebook, by_id) if frozen else {}
        left_out = []
        found = method_facts.facts(project, prepared, notebook)
        sections = _front(project)
        method, table, figure = _method(
            project, prepared, notebook, found, notebook.first_table, notebook.first_figure,
            _family_tested(project, tested),
        )  # fmt: skip
        sections += method
        builder = _Results(project, prepared, notebook, language, table, figure)
        for entry in notebook.entries:
            status = by_id[entry.id] if entry.retained else None
            if status is not None and (
                status.state in ("impossible", "no_database") or status.result is None
            ):
                left_out.append(f"{heading(entry)} : {status.reason}")
        if frozen:
            deviations, exploratory = _ordered(project, prepared, notebook, by_id, builder,
                                               tested)  # fmt: skip
        else:
            for entry in notebook.entries:
                status = by_id[entry.id]
                if entry.retained and status.result is not None and status.state not in (
                    "impossible", "no_database"
                ):  # fmt: skip
                    builder.entry(entry, status.result, entry.id, heading(entry))
        sections += builder.sections
        if frozen:
            middle = article.discussion(project, builder.book, prepared, tested, deviations,
                                        exploratory)  # fmt: skip
        else:
            middle = article.discussion_without_plan()
        sections += _back(project, notebook, found, middle)
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
            *builder.listed,
            *_rules(project),
            *article.closing(project),
        ]
        if left_out:
            closing += [_("Analyses retenues mais écartées, impossibles à calculer :"), *left_out]
        document = assembled(language, sections, closing, fingerprint.short(project))
        return document, builder.analyses


def results_paths(project_path: Path) -> dict[str, Path]:
    """ "etude-article.docx", "-article-graphiques.xlsx", "-article-R.zip" (D-092, D-106)."""
    from ddict.workflow import project_stem

    stem = project_stem(project_path) + SUFFIX
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
            script_name(project_path): r_master(project, stem, analyses, today),
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
