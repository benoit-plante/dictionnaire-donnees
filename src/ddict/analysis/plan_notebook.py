"""The plan and the notebook side by side (v0.13, step 3, D-102 to D-104; the sheet
`docs/plan-analyse-article.md`, § 5 to 7).

Freezing the plan ties each hypothesis to an entry of the notebook: the same analysis, the
same variables by role and the same options already there (then listed in `prior`: the
notebook held it before the plan was frozen), or a new entry, computed. An amendment that
changes what an hypothesis computes, or removes it, unties its entry, which is no longer
retained and says which amendment replaced it; `sync` then ties the hypothesis to a new
entry. Every entry has a state against the plan (planned, planned exploratory, superseded,
variant, exploratory, descriptive) and every hypothesis whose analysis is not retained or
cannot be computed is a deviation.

The correction for multiple comparisons (Holm or Bonferroni, as R's `p.adjust`) is applied
within each family of confirmatory hypotheses, to the p-value of each tested effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ddict.analysis import notebook as nb
from ddict.analysis import planning
from ddict.analysis.catalogue import CHOICES, OPTIONS
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.data import PreparedData
from ddict.i18n import _
from ddict.project.model import Hypothesis, PriorAnalysis, Project

P_ADJ = "p_adj"  # the adjusted p kept with an entry's statistics
ADJ_M = "adj_m"  # how many p-values were adjusted together


# --- Comparing what an entry computes with what an hypothesis plans. ---


def _refs(variables: dict) -> dict[str, list[str]]:
    """Variables by role, each role's list without its order; empty roles left out."""
    return {
        role: sorted(json.dumps(r.model_dump(mode="json"), sort_keys=True) for r in refs)
        for role, refs in variables.items()
        if refs
    }


def same_variables(entry: nb.Entry, hypothesis: Hypothesis) -> bool:
    return entry.analysis == hypothesis.analysis and _refs(entry.variables) == _refs(
        hypothesis.roles
    )


def identical(entry: nb.Entry, hypothesis: Hypothesis) -> bool:
    """The same analysis, variables by role and options."""
    return same_variables(entry, hypothesis) and dict(entry.options) == dict(hypothesis.options)


def frozen(project: Project) -> bool:
    return project.plan.frozen is not None


def _linked(notebook: nb.Notebook) -> dict[str, nb.Entry]:
    return {e.hypothesis: e for e in notebook.entries if e.hypothesis is not None}


def _free(notebook: nb.Notebook, hypothesis: Hypothesis) -> nb.Entry | None:
    """An entry that computes exactly what the hypothesis plans and is tied to nothing."""
    for entry in notebook.entries:
        if entry.hypothesis is None and entry.superseded is None and identical(entry, hypothesis):
            return entry
    return None


def _create(notebook, project, prepared, hypothesis: Hypothesis, today: str) -> nb.Entry:
    """A new entry for the hypothesis, computed now. Raises NotebookError or
    AnalysisRefused."""
    roles = hypothesis.roles.items()
    chosen = {role: [nb.resolve(project, r) for r in refs] for role, refs in roles}
    result = run(project, prepared, hypothesis.analysis, chosen, dict(hypothesis.options))
    entry = nb.add(notebook, project, result, today=today)
    entry.hypothesis = hypothesis.id
    return entry


# --- Freezing and keeping the notebook in step with the plan. ---


def freeze(
    notebook: nb.Notebook, project: Project, prepared: PreparedData | None, today: str
) -> list[PriorAnalysis]:
    """Freeze the plan and tie each hypothesis to its entry (D-102); the database must be
    open, since a new entry is computed. Returns the planned analyses the notebook already
    held. Raises PlanRefused."""
    if prepared is None or not nb.belongs(notebook, project):
        raise planning.PlanRefused(
            [
                _(
                    "Ouvrez la base pour figer le plan : chaque hypothèse devient une analyse du "
                    "carnet."
                )
            ]
        )
    planning.freeze(project, prepared, today)
    prior = []
    for hypothesis in project.plan.hypotheses:
        entry = _free(notebook, hypothesis)
        if entry is not None:
            entry.hypothesis = hypothesis.id
            prior.append(PriorAnalysis(hypothesis=hypothesis.id, entry=entry.id, added=entry.added))
        else:
            _create(notebook, project, prepared, hypothesis, today)
    project.plan.frozen.prior = prior
    return prior


def _amended_on(project: Project, hypothesis_id: str, today: str) -> str:
    dates = [a.date for a in project.plan.amendments if a.target == hypothesis_id]
    return dates[-1] if dates else today


def sync(
    notebook: nb.Notebook, project: Project, prepared: PreparedData | None, today: str
) -> list[str]:
    """After an amendment: untie the entries that no longer compute what their hypothesis
    plans (or whose hypothesis was removed), then tie each hypothesis without an entry to an
    entry tied to nothing that computes it, or to a new one when the database is open.
    Returns why an hypothesis is still without its entry."""
    if not frozen(project):
        return []
    hypotheses = {h.id: h for h in project.plan.hypotheses}
    for entry in notebook.entries:
        if entry.hypothesis is None:
            continue
        hypothesis = hypotheses.get(entry.hypothesis)
        if hypothesis is None or not identical(entry, hypothesis):
            change = "removed" if hypothesis is None else "modified"
            when = _amended_on(project, entry.hypothesis, today)
            entry.superseded = nb.Superseded(date=when, hypothesis=entry.hypothesis, change=change)
            entry.hypothesis = None
            entry.retained = False
    linked = _linked(notebook)
    waiting = []
    for hypothesis in project.plan.hypotheses:
        if hypothesis.id in linked:
            continue
        entry = _free(notebook, hypothesis)
        if entry is not None:
            entry.hypothesis = hypothesis.id
            continue
        if prepared is None or not nb.belongs(notebook, project):
            waiting.append(
                _("{id} : l'analyse prévue sera calculée quand la base sera ouverte.").format(
                    id=hypothesis.id
                )
            )
            continue
        try:
            _create(notebook, project, prepared, hypothesis, today)
        except nb.NotebookError as error:
            waiting.append(f"{hypothesis.id} : {nb.reason_text(error)}")
        except AnalysisRefused as error:
            waiting.append(f"{hypothesis.id} : {' '.join(error.check.refusals)}")
    return waiting


def clear(notebook: nb.Notebook, project: Project) -> None:
    """Remove the whole plan (a person confirmed it), and every tie of the notebook to it:
    the entries stay, as they are, retained or not."""
    planning.clear(project)
    for entry in notebook.entries:
        entry.hypothesis = None
        entry.superseded = None


# --- The state of each entry against the plan. ---


@dataclass(frozen=True)
class PlanState:
    kind: str  # planned, planned_exploratory, superseded, variant, exploratory, descriptive
    hypothesis: str | None = None
    detail: str = ""


def _option_changes(entry: nb.Entry, hypothesis: Hypothesis) -> str:
    """ "Méthode : Spearman au lieu de Pearson"."""
    found = []
    for key in sorted(set(entry.options) | set(hypothesis.options)):
        new, old = entry.options.get(key), hypothesis.options.get(key)
        if new != old:
            found.append(
                _("{option} : {new} au lieu de {old}").format(
                    option=OPTIONS.get(key, key),
                    new=CHOICES.get(new, new or "—"),
                    old=CHOICES.get(old, old or "—"),
                )
            )
    return " ; ".join(found)


def state(notebook: nb.Notebook, project: Project, entry: nb.Entry) -> PlanState | None:
    """An entry's state against the frozen plan; None without a frozen plan."""
    if not frozen(project):
        return None
    hypotheses = {h.id: h for h in project.plan.hypotheses}
    if entry.hypothesis in hypotheses:
        kind = hypotheses[entry.hypothesis].kind
        planned = "planned" if kind == "confirmatory" else "planned_exploratory"
        return PlanState(planned, entry.hypothesis)
    if entry.superseded is not None:
        return PlanState("superseded", entry.superseded.hypothesis)
    if entry.analysis == "table1":
        return PlanState("descriptive")
    for hypothesis in project.plan.hypotheses:
        if same_variables(entry, hypothesis):
            return PlanState("variant", hypothesis.id, _option_changes(entry, hypothesis))
    return PlanState("exploratory")


def state_text(found: PlanState | None, entry: nb.Entry | None = None) -> str:
    """An entry's state against the plan, in plain words; empty without a frozen plan."""
    if found is None:
        return ""
    from ddict.analysis.prereg import long_date

    if found.kind == "planned":
        return _("prévue ({id})").format(id=found.hypothesis)
    if found.kind == "planned_exploratory":
        return _("prévue, exploratoire ({id})").format(id=found.hypothesis)
    if found.kind == "superseded":
        superseded = entry.superseded if entry is not None else None
        if superseded is not None and superseded.change == "removed":
            return _("{id} retirée du plan le {date}").format(
                id=superseded.hypothesis, date=long_date(superseded.date)
            )
        when = long_date(superseded.date) if superseded is not None else ""
        return _("remplacée par l'amendement du {date} ({id})").format(
            date=when, id=found.hypothesis
        )
    if found.kind == "variant":
        return _("variante de {id} : {detail}").format(id=found.hypothesis, detail=found.detail)
    if found.kind == "descriptive":
        return _("descriptive")
    return _("exploratoire")


@dataclass(frozen=True)
class Deviation:
    hypothesis: str
    kind: str  # missing, not_retained, impossible
    text: str


def deviations(
    notebook: nb.Notebook, project: Project, statuses: list | None = None
) -> list[Deviation]:
    """The hypotheses whose planned analysis is not in the notebook, not retained, or can no
    longer be computed (`statuses`, from `notebook_check.check_all`)."""
    if not frozen(project):
        return []
    linked = _linked(notebook)
    impossible = {s.entry_id: s.reason for s in statuses or [] if s.state == "impossible"}
    found = []
    for hypothesis in project.plan.hypotheses:
        entry = linked.get(hypothesis.id)
        hid = hypothesis.id
        if entry is None:
            text = _("{id} : l'analyse prévue n'est pas dans le carnet.").format(id=hid)
            found.append(Deviation(hid, "missing", text))
        elif entry.id in impossible:
            text = _("{id} : l'analyse prévue ne peut plus être faite : {reason}").format(
                id=hid, reason=impossible[entry.id]
            )
            found.append(Deviation(hid, "impossible", text))
        elif not entry.retained:
            text = _("{id} : l'analyse prévue n'est pas retenue dans le carnet.").format(id=hid)
            found.append(Deviation(hid, "not_retained", text))
    return found


# --- The correction for multiple comparisons (D-104). ---


def adjust(pvalues: list[float], method: str) -> list[float]:
    """Adjusted p-values, as R's `p.adjust`: Holm (step-down) or Bonferroni."""
    m = len(pvalues)
    if method == "bonferroni":
        return [min(1.0, m * p) for p in pvalues]
    if method != "holm":
        return list(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])  # stable, as R's order()
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvalues[i])
        adjusted[i] = min(1.0, running)
    return adjusted


def effect_p_key(
    project: Project, prepared: PreparedData | None, hypothesis: Hypothesis, entry: nb.Entry
) -> str | None:
    """The key of the tested effect's p-value among the entry's statistics (§ 3 of the
    sheet); None when it cannot be found (a predictor needs the data)."""
    effect = hypothesis.effect
    if effect.kind in ("difference", "group"):
        return "p"
    if effect.kind == "association":
        return "fisher_p" if entry.options.get("method") == "fisher" else "p"
    if effect.kind == "model":
        return "Fp"
    if effect.kind == "pair":
        refs = [r.model_dump(mode="json") for r in entry.variables.get("variables", [])]
        try:
            i, j = sorted(refs.index(r.model_dump(mode="json")) for r in effect.variables)
        except ValueError:
            return None
        return f"p_{j + 1}_{i + 1}"
    if prepared is None:
        return None
    from ddict.analysis.book import Codebook
    from ddict.analysis.models import design

    try:
        outcome = nb.resolve(project, entry.variables["outcome"][0])
        predictors = [nb.resolve(project, r) for r in entry.variables["predictors"]]
        name = nb.resolve(project, effect.variable)
    except (KeyError, nb.NotebookError):
        return None
    data = prepared.table[[outcome, *predictors]].dropna()
    columns = list(design(Codebook(project, prepared), data, predictors).columns)
    for index, column in enumerate(columns, start=1):  # 0 is the constant
        if column == name or column.startswith(f"{name}["):
            return f"p_{index}"
    return None


def _latest(entry: nb.Entry) -> nb.Computed:
    return entry.pending or entry.computed


def corrections(
    notebook: nb.Notebook, project: Project, prepared: PreparedData | None, statuses: list
) -> dict[str, tuple[float, int]]:
    """The adjusted p-value of each planned entry in a family, with the family's size:
    confirmatory hypotheses of the same family whose entry is retained and computed. A
    family of one is not adjusted."""
    plan = project.plan
    if not frozen(project) or plan.correction == "none":
        return {}
    computable = {s.entry_id for s in statuses if s.state not in ("impossible", "no_database")}
    linked = _linked(notebook)
    families: dict[str, list[tuple[str, float]]] = {}
    for hypothesis in plan.hypotheses:
        entry = linked.get(hypothesis.id)
        if hypothesis.kind != "confirmatory" or hypothesis.family is None or entry is None:
            continue
        if not entry.retained or entry.id not in computable:
            continue
        key = effect_p_key(project, prepared, hypothesis, entry)
        p = _latest(entry).statistics.get(key) if key else None
        if p is not None:
            families.setdefault(hypothesis.family, []).append((entry.id, p))
    found = {}
    for members in families.values():
        if len(members) < 2:
            continue
        adjusted = adjust([p for _id, p in members], plan.correction)
        for (entry_id, _p), value in zip(members, adjusted, strict=True):
            found[entry_id] = (value, len(members))
    return found


def family_sizes(project: Project) -> dict[str, int]:
    """How many confirmatory hypotheses each family counts in the plan."""
    sizes: dict[str, int] = {}
    for hypothesis in project.plan.hypotheses:
        if hypothesis.kind == "confirmatory" and hypothesis.family is not None:
            sizes[hypothesis.family] = sizes.get(hypothesis.family, 0) + 1
    return sizes
