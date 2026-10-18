"""The facts of the Method (v0.12, step 7, D-097, D-100), computed on the database with the
decisions in force: the flow of participants, the description of the sample analysed, the
reliability of each score, the missing codes, and the methods of the retained analyses. The
notebook keeps their aggregates (`statistics`), compared and confirmed as an analysis; the
paragraphs are written from them by `ddict.analysis.method_text`.

Aggregates only: counts, means, standard deviations, percentages, alphas; never a value of
a person, a minimum or a maximum (D-088).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ddict.analysis import notebook as nb
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import CATALOGUE
from ddict.analysis.compute import code_key
from ddict.analysis.data import PreparedData, _missing_codes
from ddict.analysis.exclusions import Flow
from ddict.analysis.reliability import Reliability, reliabilities
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.project.exclusions import members
from ddict.project.model import Project

CATEGORICAL = ("nominal", "ordinal")


@dataclass(frozen=True)
class Described:
    """A variable describing the sample: M and SD, or the share of each category."""

    name: str  # final name
    label: str
    n: int
    mean: float | None = None
    sd: float | None = None
    categories: tuple[tuple[object, str, float], ...] = ()  # code, label, percent


@dataclass(frozen=True)
class Facts:
    flow: Flow
    described: tuple[Described, ...]
    reliabilities: tuple[Reliability, ...]
    missing: tuple[tuple[str, tuple[object, ...]], ...]  # final name, its missing codes
    methods: tuple[tuple[str, str, str], ...]  # analysis, method, post hoc, as used
    recodes: tuple[str, ...] = ()  # v0.15: the sentences of the recodings it speaks of


def _flow(prepared: PreparedData) -> Flow:
    if prepared.flow is not None:
        return prepared.flow
    return Flow(len(prepared.table), (), len(prepared.table))


def _describe(project: Project, prepared: PreparedData, name: str, book: Codebook) -> Described:
    column = prepared.table[name]
    level = book.levels.get(name)
    if name in prepared.scores:
        level = "scale"
    present = column.dropna()
    label = book.label(name)
    if level in CATEGORICAL:
        shares = present.value_counts(normalize=True).sort_index()
        categories = tuple(
            (code, book.category(name, code), 100 * float(share)) for code, share in shares.items()
        )
        return Described(name, label, len(present), categories=categories)
    numbers = pd.to_numeric(present, errors="coerce").dropna()
    sd = float(numbers.std(ddof=1)) if len(numbers) > 1 else None
    return Described(name, label, len(numbers), float(numbers.mean()), sd)


def _used(project: Project, notebook: nb.Notebook) -> list[str]:
    """Final names of the variables the Method speaks of: the retained analyses', the
    sample's, the items of the scores."""
    found: list[str] = []
    for entry in notebook.entries:
        if not entry.retained:
            continue
        try:
            for names in nb.resolved(project, entry).values():
                found += names
        except nb.NotebookError:
            continue
    for ref in notebook.method.variables:
        try:
            found.append(nb.resolve(project, ref))
        except nb.NotebookError:
            continue
    names = w.names_of(project)
    for score in plan(project)[1]:
        group = next(g for g in project.groups if g.group_id == score.group)
        found += [names[n] for n in members(group)]
    return list(dict.fromkeys(found))


def _missing(project: Project, used: list[str]) -> tuple[tuple[str, tuple[object, ...]], ...]:
    by_final = {w.final_name(e): e for e in project.variables}
    found = []
    for name in used:
        entry = by_final.get(name)
        if entry is None:
            continue
        singles, ranges = _missing_codes(entry)
        codes = tuple(sorted(singles, key=lambda c: (isinstance(c, str), str(c))))
        codes += tuple(f"{w.code_text(low)}–{w.code_text(high)}" for low, high in ranges)
        if codes:
            found.append((name, codes))
    return tuple(found)


def _recodes(project: Project, notebook: nb.Notebook, used: list[str]) -> tuple[str, ...]:
    """The recodings the Method speaks of (v0.15, D-120): those of the variables it uses,
    of the subgroups of the retained analyses, of the exclusion rules; in the project's
    order."""
    from ddict.project.recodes import method_sentence

    named = set(used)
    for entry in notebook.entries:
        if entry.retained and entry.subgroup is not None:
            try:
                named.add(nb.resolve(project, entry.subgroup.variable))
            except nb.NotebookError:
                continue
    ids = {getattr(r, "recode", None) for r in project.exclusions.rules}
    return tuple(
        method_sentence(project, rule)
        for rule in project.recodes.rules
        if rule.name in named or rule.id in ids
    )


def _methods(notebook: nb.Notebook) -> tuple[tuple[str, str, str], ...]:
    """The methods of the retained analyses, in the catalogue's order, each once."""
    found = set()
    for entry in notebook.entries:
        if not entry.retained:
            continue
        default = CATALOGUE[entry.analysis].options.get("method", ("",))[0]
        method = entry.options.get("method") or default
        post_hoc = entry.options.get("post_hoc", "none")
        found.add((entry.analysis, method, post_hoc))
    order = list(CATALOGUE)
    return tuple(sorted(found, key=lambda m: (order.index(m[0]), m[1], m[2])))


def facts(project: Project, prepared: PreparedData, notebook: nb.Notebook) -> Facts:
    book = Codebook(project, prepared)
    described = []
    for ref in notebook.method.variables:
        try:
            described.append(_describe(project, prepared, nb.resolve(project, ref), book))
        except nb.NotebookError:
            continue
    used = _used(project, notebook)
    return Facts(
        _flow(prepared),
        tuple(described),
        tuple(reliabilities(project, prepared)),
        _missing(project, used),
        _methods(notebook),
        _recodes(project, notebook, used),
    )


def statistics(found: Facts) -> dict[str, float]:
    """The aggregates the notebook keeps and compares (D-100), by position."""
    stats: dict[str, float] = {"n_start": float(found.flow.start)}
    for rule, excluded in found.flow.excluded:
        stats[f"excluded_{rule}"] = float(excluded)
    stats["n_analysed"] = float(found.flow.analysed)
    for i, d in enumerate(found.described, start=1):
        stats[f"v{i}_n"] = float(d.n)
        if d.mean is not None:
            stats[f"v{i}_m"] = d.mean
        if d.sd is not None:
            stats[f"v{i}_sd"] = d.sd
        for code, _label, percent in d.categories:
            stats[f"v{i}_pct_{code_key(code)}"] = percent
    for r in found.reliabilities:
        stats[f"alpha_n_{r.group}"] = float(r.n)
        if r.alpha is not None:
            stats[f"alpha_{r.group}"] = r.alpha
            stats[f"alpha_low_{r.group}"] = r.low
            stats[f"alpha_high_{r.group}"] = r.high
    return dict(sorted(stats.items()))


def computed(project: Project, found: Facts, today: str) -> nb.Computed:
    """The Method as the notebook keeps it, like an analysis."""
    from ddict.analysis.report import versions
    from ddict.project import fingerprint

    return nb.Computed(
        date=today,
        fingerprint=fingerprint.fingerprint(project),
        versions=versions(),
        n_used=found.flow.analysed,
        n_excluded=found.flow.start - found.flow.analysed,
        statistics=statistics(found),
        sentence="",
        warnings=[],
    )
