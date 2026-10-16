"""The analyses of the catalogue, computed in the tool (v0.9, steps 4 and 5, D-070, D-071):
SciPy for the tests; effect sizes and Table 1 by their formulas (docs/catalogue-analyses.md).
Only the catalogue's own code runs here, never code written by a model.
"""

from __future__ import annotations

import math

import pandas as pd
from scipy import stats

from ddict.analysis import conditions, models
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import CATALOGUE
from ddict.analysis.data import PreparedData
from ddict.analysis.results import (
    AnalysisResult,
    Table,
    count_percent,
    interval,
    number,
    p_part,
)
from ddict.i18n import _
from ddict.project.model import Project

SMALL = conditions.SMALL


AnalysisRefused = conditions.AnalysisRefused


def _options(key: str, options: dict[str, str] | None) -> dict[str, str]:
    return {k: v[0] for k, v in CATALOGUE[key].options.items()} | (options or {})


# --- Table 1. ---


def _describe(
    column: pd.Series, name: str, book: Codebook, total: int, small: list[str]
) -> list[list[str]]:
    level = book.levels.get(name)
    label = book.label(name)
    if level == "scale":
        x = column.dropna()
        if x.empty:
            return [[label, "0", "", ""]]
        return [
            [
                label,
                str(x.size),
                f"{number(x.mean())} ({number(x.std(ddof=1))})",
                f"{number(x.min(), 1)} – {number(x.max(), 1)}",
            ]
        ]
    rows = [[label, str(column.notna().sum()), "", ""]]
    counts = column.value_counts()
    order = [c for c in book.value_labels(name) if c in counts.index]
    order += [c for c in counts.index if c not in order]
    for code in order:
        count = int(counts[code])
        mark = " ⚠" if count < SMALL else ""
        rows.append([f"  {book.category(name, code)}", "", count_percent(count, total) + mark, ""])
        if count < SMALL:
            small.append(f"{name} : {book.category(name, code)}")
    missing = int(column.isna().sum())
    if missing:
        rows.append([f"  {_('manquant')}", "", count_percent(missing, total), ""])
    return rows


def table1(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    table = prepared.table
    variables = chosen["variables"]
    group = (chosen.get("group") or [None])[0]
    columns = [_("Variable"), "n", _("M (ÉT) ou effectif (%)"), _("Étendue")]
    tables = []
    parts = [(None, table)]
    if group:
        kept = table[table[group].notna()]
        codes = [c for c in book.value_labels(group) if c in set(kept[group])]
        codes += [c for c in sorted(set(kept[group])) if c not in codes]
        parts = [(code, kept[kept[group] == code]) for code in codes]
    warnings = []
    for code, part in parts:
        rows = []
        small: list[str] = []
        for name in variables:
            rows += _describe(part[name], name, book, len(part), small)
        if small:
            where = f" ({book.category(group, code)})" if code is not None else ""
            warnings.append(
                _("Moins de {n} personnes{where} : {cases}.").format(
                    n=SMALL, where=where, cases="; ".join(small)
                )
            )
        title = _("Ensemble ({n})").format(n=len(part))
        if code is not None:
            title = f"{book.label(group)} : {book.category(group, code)} (n = {len(part)})"
            if len(part) < SMALL:
                warnings.append(
                    _("{group} : moins de {n} personnes dans {code}.").format(
                        group=group, n=SMALL, code=book.category(group, code)
                    )
                )
        tables.append(Table(title, columns, rows))
    excluded = len(table) - sum(len(part) for _code, part in parts)
    return AnalysisResult("table1", chosen, options, len(table) - excluded, excluded, tables,
                          warnings=warnings)  # fmt: skip


# --- Correlation. ---


def _pair(x: pd.Series, y: pd.Series, method: str) -> dict:
    keep = x.notna() & y.notna()
    a, b = x[keep].to_numpy(float), y[keep].to_numpy(float)
    if method == "spearman":
        found = stats.spearmanr(a, b)
        return {"n": int(keep.sum()), "r": float(found.statistic), "p": float(found.pvalue)}
    found = stats.pearsonr(a, b)
    ci = found.confidence_interval(0.95)
    return {"n": int(keep.sum()), "r": float(found.statistic), "p": float(found.pvalue),
            "ci_low": float(ci.low), "ci_high": float(ci.high)}  # fmt: skip


def correlation(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    names = chosen["variables"]
    method = options["method"]
    symbol = "ρ" if method == "spearman" else "r"
    rows, found = [], {}
    for i, first in enumerate(names):
        for second in names[i + 1 :]:
            pair = _pair(prepared.table[first], prepared.table[second], method)
            found[(first, second)] = pair
            ci = interval(pair["ci_low"], pair["ci_high"]) if "ci_low" in pair else ""
            rows.append([book.label(first), book.label(second), str(pair["n"]),
                         number(pair["r"]), ci, p_part(pair["p"])])  # fmt: skip
    columns = [_("Variable"), _("Variable"), "n", symbol, _("IC 95 %"), "p"]
    used = prepared.table[names].dropna()
    result = AnalysisResult("correlation", chosen, options, len(used),
                            len(prepared.table) - len(used),
                            [Table(_("Corrélations"), columns, rows)])  # fmt: skip
    if len(names) == 2:
        pair = found[(names[0], names[1])]
        result.statistics = pair
        if method == "spearman":
            result.sentence = _(
                "La corrélation de Spearman entre {a} et {b} était ρ = {r}, {p} (n = {n})."
            ).format(a=book.label(names[0]), b=book.label(names[1]), r=number(pair["r"]),
                     p=p_part(pair["p"]), n=pair["n"])  # fmt: skip
        else:
            result.sentence = _(
                "La corrélation entre {a} et {b} était r({df}) = {r}, {ci}, {p}."
            ).format(a=book.label(names[0]), b=book.label(names[1]), df=pair["n"] - 2,
                     r=number(pair["r"]), ci=interval(pair["ci_low"], pair["ci_high"]),
                     p=p_part(pair["p"]))  # fmt: skip
    return result


# --- Chi-square. ---


def chi_square(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    row_name, col_name = chosen["rows"][0], chosen["columns"][0]
    data = prepared.table[[row_name, col_name]].dropna()
    observed = pd.crosstab(data[row_name], data[col_name])
    test = stats.chi2_contingency(observed.to_numpy(), correction=False)
    n = int(observed.to_numpy().sum())
    smaller = min(observed.shape) - 1
    v = math.sqrt(test.statistic / (n * smaller)) if smaller else float("nan")
    statistics = {"chi2": float(test.statistic), "df": int(test.dof), "p": float(test.pvalue),
                  "V": v, "n": n}  # fmt: skip
    expected = test.expected_freq
    share_low = float((expected < 5).mean())
    warnings = []
    two_by_two = observed.shape == (2, 2)
    if share_low > 0.2 or expected.min() < 1:
        text = _("{k} effectifs attendus sur {n} sont sous 5 (minimum {m}).").format(
            k=int((expected < 5).sum()), n=expected.size, m=number(float(expected.min()), 1)
        )
        if two_by_two:
            text += " " + _("Le test exact de Fisher convient mieux.")
        warnings.append(text)
    if (observed.to_numpy() < SMALL).any():
        warnings.append(_("Au moins une case compte moins de {n} personnes.").format(n=SMALL))
    if options.get("method") == "fisher" and two_by_two:
        odds, p_fisher = stats.fisher_exact(observed.to_numpy())
        statistics |= {"fisher_p": float(p_fisher), "odds_ratio": float(odds)}
    columns = [book.label(row_name)] + [book.category(col_name, c) for c in observed.columns]
    rows = [
        [book.category(row_name, r)]
        + [str(int(x)) + (" ⚠" if x < SMALL else "") for x in observed.loc[r]]
        for r in observed.index
    ]
    sentence = _(
        "Association entre {a} et {b} : χ²({df}) = {chi2}, {p}, V = {v} (n = {n})."
    ).format(
        a=book.label(row_name),
        b=book.label(col_name),
        df=statistics["df"],
        chi2=number(statistics["chi2"]),
        p=p_part(statistics["p"]),
        v=number(v),
        n=n,
    )
    if "fisher_p" in statistics:
        sentence += " " + _("Test exact de Fisher : {p}.").format(p=p_part(statistics["fisher_p"]))
    return AnalysisResult("chi_square", chosen, options, n, len(prepared.table) - n,
                          [Table(_("Effectifs observés"), columns, rows)], statistics, sentence,
                          warnings)  # fmt: skip


COMPUTE = {
    "table1": table1,
    "t_test": models.t_test,
    "anova": models.anova,
    "chi_square": chi_square,
    "correlation": correlation,
    "regression": models.regression,
}


def run(
    project: Project,
    prepared: PreparedData,
    key: str,
    chosen: dict[str, list[str]],
    options: dict[str, str] | None = None,
) -> AnalysisResult:
    """Check the conditions, then compute. Raises AnalysisRefused when they refuse."""
    found = conditions.check(project, key, chosen, options, prepared)
    if not found.ok:
        raise AnalysisRefused(found)
    result = COMPUTE[key](project, prepared, chosen, _options(key, options))
    result.warnings = found.warnings + [x for x in result.warnings if x not in found.warnings]
    return result
