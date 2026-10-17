"""The analysis notebook (v0.11, D-087 to D-092): the analyses of a study, kept next to the
project in `<projet>-carnet.json`, never in the project file, which stays a codebook. The
sheet is `docs/carnet-analyses.md` (validated).

An entry keeps what was asked (the analysis, its variables by their key in the project, its
options), what a person changed (titles and notes), whether it is retained for the article,
and its last confirmed computation: the codebook's fingerprint, the date, the versions, the
counts, the aggregate statistics, the APA sentence and the warnings. Never a row of the
database, an identifier, a point of a scatter plot nor an observed range (D-088).

The order of the entries is their rank. Identifiers only grow: a removed A5 never comes
back.

Since 1.1.0 (v0.12, D-100), the notebook keeps the figures of the Method too (`method`):
the variables chosen to describe the sample, and the last confirmed computation of the
flow, the description and the reliabilities, compared and confirmed as an analysis. A
notebook 1.0.0 reads as it is.

Since 1.2.0 (v0.13, D-102), an entry may be the planned analysis of an hypothesis of the
project's frozen plan (`hypothesis`), or one an amendment replaced (`superseded`). A planned
analysis is never removed from the notebook: it can stop being retained, or the plan be
amended. A notebook 1.1.0 reads as it is.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ddict.analysis.apa import Edit
from ddict.analysis.catalogue import CATALOGUE
from ddict.analysis.results import AnalysisResult
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.i18n import _
from ddict.project import fingerprint
from ddict.project.model import Project, VariableRef

NOTEBOOK_VERSION = "1.2.0"
METHOD = "M"  # the identifier of the Method in the states and the confirmations
SUFFIX = "-carnet.json"


class NotebookError(Exception):
    """The notebook cannot be read, or a variable cannot be found; `reason` says why."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason, detail)
        self.reason = reason
        self.detail = detail


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ItemEdit(_Strict):
    """A table's or a figure's title and note, as a person changed them; None keeps the
    computed one. Never a number: the document numbers by the order (D-090)."""

    title: str | None = None
    note: str | None = None


class Computed(_Strict):
    date: str
    fingerprint: str
    versions: dict[str, str]
    n_used: int
    n_excluded: int
    statistics: dict[str, float]
    sentence: str
    warnings: list[str]


class Superseded(_Strict):
    """An entry that was the planned analysis of an hypothesis until an amendment changed
    the hypothesis (`modified`) or removed it (`removed`), on that date (v0.13)."""

    date: str
    hypothesis: str
    change: Literal["modified", "removed"]


class Entry(_Strict):
    id: str
    analysis: str
    variables: dict[str, list[VariableRef]]
    options: dict[str, str]
    edits: dict[str, ItemEdit]
    retained: bool
    added: str
    computed: Computed
    pending: Computed | None = None
    hypothesis: str | None = None  # v0.13: the planned analysis of this hypothesis
    superseded: Superseded | None = None


class MethodPart(_Strict):
    """The Method's part of the notebook (v0.12, D-100)."""

    variables: list[VariableRef] = []  # describe the sample analysed, in this order
    computed: Computed | None = None
    pending: Computed | None = None


class ProjectLink(_Strict):
    file: str
    source_sha256: str


class Notebook(_Strict):
    carnet_version: str = NOTEBOOK_VERSION
    project: ProjectLink
    next_id: int = 1
    first_table: int = 1
    first_figure: int = 1
    entries: list[Entry] = []
    method: MethodPart = MethodPart()


# --- Variables by their key in the project. ---


def _originals(project: Project) -> dict[str, str]:
    """Final name -> original name."""
    return {final: original for original, final in w.names_of(project).items()}


def reference(project: Project, name: str) -> VariableRef:
    """The key in the project of a variable an analysis used, by its final name."""
    originals = _originals(project)
    if name in originals:
        return VariableRef(variable=originals[name])
    reversals, scores, _notes = plan(project)
    for score in scores:
        if score.name == name:
            return VariableRef(score=score.group)
    for item in reversals:
        if item.new == name:
            return VariableRef(reversed=originals[item.name])
    raise NotebookError("unknown_variable", name)


def resolve(project: Project, ref: VariableRef) -> str:
    """The final name in force of a variable of the notebook; NotebookError when its key
    leads nowhere any more (D-089: the analysis is then impossible, with this reason)."""
    names = w.names_of(project)
    if ref.variable is not None:
        if ref.variable not in names:
            raise NotebookError("variable_removed", ref.variable)
        return names[ref.variable]
    reversals, scores, _notes = plan(project)
    if ref.score is not None:
        for score in scores:
            if score.group == ref.score:
                return score.name
        raise NotebookError("score_removed", ref.score)
    final = names.get(ref.reversed or "")
    for item in reversals:
        if item.name == final:
            return item.new
    raise NotebookError("not_reversed", ref.reversed or "")


def resolved(project: Project, entry: Entry) -> dict[str, list[str]]:
    """An entry's variables as the analyses take them: final names, by role."""
    return {role: [resolve(project, r) for r in refs] for role, refs in entry.variables.items()}


def reason_text(error: NotebookError) -> str:
    """Why an analysis of the notebook cannot be computed, or the notebook read or changed,
    in plain words."""
    texts = {
        "variable_removed": _("{name} : la variable n'est plus dans le projet."),
        "score_removed": _("{name} : le groupe n'a plus de cotation, donc plus de score."),
        "not_reversed": _("{name} : l'item n'est plus inversé."),
        "unknown_variable": _("{name} : variable inconnue du projet."),
        "unknown_entry": _("{name} : aucune analyse du carnet ne porte ce numéro."),
        "nothing_pending": _("{name} : aucun changement à confirmer."),
        "planned": _(
            "{name} est une analyse prévue par le plan : elle ne se retire pas du carnet. Ne "
            "la retenez plus, ou modifiez le plan."
        ),
        "unreadable": _("Le carnet ne peut pas être lu : {name}"),
        "version": _(
            "Ce carnet (version {name}) a été fait par une version plus récente de l'outil."
        ),
    }
    return texts.get(error.reason, "{name}").format(name=error.detail)


# --- What an entry keeps. ---


def computed(project: Project, result: AnalysisResult, today: str | None = None) -> Computed:
    """The aggregates of a result, as the notebook keeps them (D-088)."""
    from ddict.analysis.report import versions

    statistics = {
        key: float(value)
        for key, value in sorted(result.statistics.items())
        if isinstance(value, int | float) and math.isfinite(float(value))
    }
    return Computed(
        date=today or date.today().isoformat(),
        fingerprint=fingerprint.fingerprint(project),
        versions=versions(),
        n_used=int(result.n_used),
        n_excluded=int(result.n_excluded),
        statistics=statistics,
        sentence=result.sentence,
        warnings=list(result.warnings),
    )


def _edits(edits: dict[str, Edit] | None) -> dict[str, ItemEdit]:
    found = {}
    for key, edit in sorted((edits or {}).items()):
        if edit.title is not None or edit.note is not None:
            found[key] = ItemEdit(title=edit.title, note=edit.note)
    return found


# --- The notebook's entries. ---


def new_notebook(project: Project, project_path: Path) -> Notebook:
    return Notebook(
        project=ProjectLink(file=project_path.name, source_sha256=project.source.sha256)
    )


def belongs(notebook: Notebook, project: Project) -> bool:
    """Whether the notebook was made with this project's database."""
    return notebook.project.source_sha256 == project.source.sha256


def find(notebook: Notebook, entry_id: str) -> Entry:
    for entry in notebook.entries:
        if entry.id == entry_id:
            return entry
    raise NotebookError("unknown_entry", entry_id)


def add(
    notebook: Notebook,
    project: Project,
    result: AnalysisResult,
    *,
    edits: dict[str, Edit] | None = None,
    today: str | None = None,
) -> Entry:
    """Add an analysis that was just run, at the end, retained; its identifier is the next
    one, never a removed one's."""
    today = today or date.today().isoformat()
    entry = Entry(
        id=f"A{notebook.next_id}",
        analysis=result.analysis,
        variables={  # in the catalogue's order of the roles, however they were chosen
            role.key: [reference(project, n) for n in result.chosen[role.key]]
            for role in CATALOGUE[result.analysis].roles
            if result.chosen.get(role.key)
        },
        options={k: str(v) for k, v in sorted(result.options.items())},
        edits=_edits(edits),
        retained=True,
        added=today,
        computed=computed(project, result, today),
    )
    notebook.entries.append(entry)
    notebook.next_id += 1
    return entry


def remove(notebook: Notebook, entry_id: str) -> None:
    """Remove an entry; never a planned analysis (v0.13), which NotebookError refuses."""
    entry = find(notebook, entry_id)
    if entry.hypothesis is not None:
        raise NotebookError("planned", entry_id)
    notebook.entries.remove(entry)


def move(notebook: Notebook, entry_id: str, position: int) -> None:
    """Put an entry at this position (1 is the first); the others keep their order."""
    entry = find(notebook, entry_id)
    notebook.entries.remove(entry)
    position = max(1, min(position, len(notebook.entries) + 1))
    notebook.entries.insert(position - 1, entry)


def retain(notebook: Notebook, entry_id: str, retained: bool) -> None:
    find(notebook, entry_id).retained = retained


def describe_sample(notebook: Notebook, project: Project, names: list[str]) -> None:
    """The variables that describe the sample analysed (v0.12), by their final names, in
    this order. Raises NotebookError for a name the project does not know."""
    notebook.method.variables = [reference(project, name) for name in dict.fromkeys(names)]


def sample_names(notebook: Notebook, project: Project) -> list[str]:
    """The final names of the variables that describe the sample; those whose key leads
    nowhere any more are left out."""
    found = []
    for ref in notebook.method.variables:
        try:
            found.append(resolve(project, ref))
        except NotebookError:
            continue
    return found


# --- The file. ---


def notebook_path(project_path: Path) -> Path:
    """ "etude-carnet.json" next to "etude.dd.json" (D-091)."""
    from ddict.workflow import project_stem

    return project_path.with_name(project_stem(project_path) + SUFFIX)


def open_notebook(project: Project, project_path: Path) -> Notebook:
    """The project's notebook, or a new empty one when there is none yet (nothing is
    written until an analysis is added). Raises NotebookError."""
    path = notebook_path(project_path)
    if path.is_file():
        return load_notebook(path)
    return new_notebook(project, project_path)


def dumps(notebook: Notebook) -> str:
    """Deterministic JSON: the model's key order, indent 2, UTF-8, LF."""
    data = notebook.model_dump(mode="json")
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def save_notebook(notebook: Notebook, path: Path) -> None:
    """Written to a temporary file, then put in place at once (as the project)."""
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(dumps(notebook))
    temporary.replace(path)


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def load_notebook(path: Path) -> Notebook:
    """Read a notebook; refused when made by a newer tool or another major version."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise NotebookError("unreadable", str(error)) from error
    version = str(data.get("carnet_version", "0"))
    try:
        found, ours = _version(version), _version(NOTEBOOK_VERSION)
    except ValueError as error:
        raise NotebookError("version", version) from error
    if found[0] != ours[0] or found > ours:
        raise NotebookError("version", version)
    try:
        notebook = Notebook.model_validate(data)
    except ValueError as error:
        raise NotebookError("unreadable", str(error)) from error
    notebook.carnet_version = NOTEBOOK_VERSION
    return notebook
