"""The reliability of a score in the Method (v0.12, step 6, D-096): Cronbach's alpha
computed again on the sample analysed (after the exclusion rules, the missing codes and the
reversed items), on the people who answered every item of the score, with its 95 %
confidence interval after Feldt (1965). The alpha the Groups page shows, observed on the
whole file before the decisions, does not change. Omega is postponed (D-096).
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats

from ddict.analysis.data import PreparedData
from ddict.export.preparation import plan
from ddict.project.model import Project

LEVEL = 0.95


@dataclass(frozen=True)
class Reliability:
    group: str
    score: str  # the score's name
    items: int  # k
    n: int  # the people who answered every item
    alpha: float | None  # None: fewer than 2 such people, or no variance
    low: float | None
    high: float | None


def feldt(alpha: float, n: int, k: int, level: float = LEVEL) -> tuple[float, float]:
    """The bounds of alpha from the F distribution (Feldt, 1965)."""
    df1, df2 = n - 1, (n - 1) * (k - 1)
    tail = (1 - level) / 2
    return (
        1 - (1 - alpha) * stats.f.ppf(1 - tail, df1, df2),
        1 - (1 - alpha) * stats.f.ppf(tail, df1, df2),
    )


def reliabilities(project: Project, prepared: PreparedData) -> list[Reliability]:
    """For each structured scoring, in the order of the groups, its score's alpha."""
    found = []
    for score in plan(project)[1]:
        items = prepared.table[score.items].dropna()
        n, k = len(items), len(score.items)
        total = items.sum(axis=1).var(ddof=1) if n >= 2 else 0.0
        if n < 2 or k < 2 or not total > 0:
            found.append(Reliability(score.group, score.name, k, n, None, None, None))
            continue
        alpha = float(k / (k - 1) * (1 - items.var(ddof=1).sum() / total))
        low, high = feldt(alpha, n, k)
        found.append(Reliability(score.group, score.name, k, n, alpha, float(low), float(high)))
    return found
