"""The APA 7 tables and figures of an analysis, described without any format (v0.10, step 2,
D-083). The sheets are `docs/tableaux-figures-apa.md` (validated): each format (Word today,
others later) renders this description and adds nothing to it.

A text is a sequence of runs, each roman or italic: statistical symbols are italic (M, SD, t,
p), Greek letters roman. Numbers follow the catalogue's conventions (two decimals, three for
p, no leading zero for what cannot exceed 1, the true minus sign). The numbers come from the
analysis, never from a person: only a table's or a figure's number, title and note may be
changed (D-086).
"""

from __future__ import annotations

import string
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from ddict import i18n
from ddict.analysis.book import Codebook
from ddict.analysis.data import PreparedData, apply_subset, chosen_levels
from ddict.analysis.models import _codes, _mid
from ddict.analysis.results import MINUS, AnalysisResult, number, p_value
from ddict.i18n import _
from ddict.project import fingerprint
from ddict.project.model import Project

SMALL = 5
NBSP = chr(0xA0)  # a no-break space

# --- Texts. ---


@dataclass(frozen=True)
class Run:
    text: str
    italic: bool = False
    hole: bool = False  # v0.12 (D-097): "[à compléter : …]", highlighted in Word
    bold: bool = False  # v0.13: "H1." in the Discussion
    sub: bool = False  # v0.14: the "z" of d_z


Text = tuple[Run, ...]


def rich(*parts: str | Run) -> Text:
    """A text from plain strings and italic runs: rich("Âge, ", it("M"), " (", it("ÉT"), ")")."""
    runs = [
        p if isinstance(p, Run) else Run(p) for p in parts if (p.text if isinstance(p, Run) else p)
    ]
    return tuple(runs)


def it(text: str) -> Run:
    return Run(text, italic=True)


def hole(what: str) -> Run:
    """A fact the codebook does not hold, left for a person (D-097): never guessed."""
    return Run(_("[à compléter : {what}]").format(what=what), hole=True)


def marked(template: str, **values: str | Run | Text) -> Text:
    """A whole sentence, translated as one, with its symbols in their places:
    marked(_("Test {t} de Welch."), t=it("t")). A Run or a Text keeps its italics."""
    runs: list[Run] = []
    for literal, name, _spec, _conversion in string.Formatter().parse(template):
        if literal:
            runs.append(Run(literal))
        if name is not None:
            value = values[name]
            if isinstance(value, Run):
                runs.append(value)
            elif isinstance(value, tuple):
                runs.extend(value)
            else:
                runs.append(Run(str(value)))
    return tuple(runs)


def plain(text: Text) -> str:
    return "".join(r.text for r in text)


# --- Numbers, APA style. ---


def apa(value: float, digits: int = 2, zero: bool = True) -> str:
    """A statistic; without its leading zero when it cannot exceed 1 (r, β, p, V, η²)."""
    text = number(value, digits)
    if not zero:
        sign = MINUS if text.startswith(MINUS) else ""
        body = text[len(sign) :]
        if body.startswith("0") and len(body) > 1 and not body[1].isdigit():
            body = body[1:]
        text = sign + body
    return text


def brackets(low: float, high: float, digits: int = 2, zero: bool = True) -> str:
    """ "[0,35 ; 0,81]" in French, "[0.35, 0.81]" in English."""
    return _("[{low} ; {high}]").format(low=apa(low, digits, zero), high=apa(high, digits, zero))


def p_cell(p: float) -> str:
    """ ",861" or "< ,001": the p column of a table."""
    return p_value(p)


def p_text(p: float) -> Text:
    """ "p = ,861" or "p < ,001", p in italic: in a note."""
    shown = p_value(p)
    return rich(it("p"), f" {shown}" if shown.startswith("<") else f" = {shown}")


def count_pct(count: int, total: int) -> str:
    return f"{count} ({number(100 * count / total if total else 0.0, 1)})"


# --- The description. ---

Align = Literal["left", "center"]


@dataclass(frozen=True)
class Column:
    header: Text
    align: Align = "center"


@dataclass(frozen=True)
class Spanner:
    """A header over several columns, `first` to `last` included (0 is the first column)."""

    label: Text
    first: int
    last: int


@dataclass(frozen=True)
class Row:
    cells: tuple[Text, ...]
    indent: int = 0  # a category under its variable


@dataclass(frozen=True)
class ApaTable:
    key: str  # stable within an analysis: "table-1", "table-2"…
    number: int
    title: str
    columns: tuple[Column, ...]
    rows: tuple[Row, ...]
    spanners: tuple[Spanner, ...] = ()
    note: Text = ()


FigureKind = Literal["bars", "grouped_bars", "scatter", "coefficients", "flow", "line"]


@dataclass(frozen=True)
class FlowStep:
    """A rule of the flow of participants (v0.12, D-098): who it excluded, who remain."""

    rule: str  # "E1"
    reason: str
    excluded: int
    remaining: int


@dataclass(frozen=True)
class Series:
    name: str
    values: tuple[float, ...]
    low: tuple[float, ...] = ()  # the error bars, as the bounds of the interval
    high: tuple[float, ...] = ()


@dataclass(frozen=True)
class ApaFigure:
    key: str
    number: int
    title: str
    kind: FigureKind
    x_label: str
    y_label: str
    categories: tuple[str, ...] = ()  # bars: one per category; coefficients: the predictors
    series: tuple[Series, ...] = ()
    points: tuple[tuple[float, float], ...] = ()  # scatter
    line: tuple[float, float] | None = None  # scatter: intercept, slope
    legend_title: str = ""
    y_min: float | None = None
    y_max: float | None = None
    reference: float | None = None  # coefficients: the dashed line, at 0
    log_scale: bool = False  # v0.14: odds ratios, around their dashed line at 1
    note: Text = ()
    flow_start: int = 0  # flow (v0.12): the answers received, then each rule
    flow: tuple[FlowStep, ...] = ()


@dataclass(frozen=True)
class ApaDocument:
    """One analysis's tables and figures; or, with `sections` (v0.11), those of several
    analyses, numbered one after the other, `tables` and `figures` then holding them all
    in order, and `closing` the lines that end the document."""

    analysis: str
    language: str
    tables: tuple[ApaTable, ...] = ()
    figures: tuple[ApaFigure, ...] = ()
    sentence: str = ""
    fingerprint: str = ""  # of the codebook, short
    sections: tuple[Section, ...] = ()
    closing: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    """An analysis of the results document (v0.11): its heading, its APA sentence, its
    tables and its figures, already numbered. Since v0.12, a part of the Method too: its
    paragraphs, written by templates; and the headings of level 1, "Méthode" and
    "Résultats", which hold nothing."""

    key: str  # the notebook's identifier: "A2"; or "methode", "participants"...
    heading: str
    sentence: str
    tables: tuple[ApaTable, ...] = ()
    figures: tuple[ApaFigure, ...] = ()
    paragraphs: tuple[Text, ...] = ()
    level: int = 2  # APA heading level
    # v0.13, the article: a heading with its runs (the title, a hole), `heading` then being
    # its plain text; no heading at all when `heading` is empty (the title page); a page
    # break after the section (the title page, the abstract) or before it (References).
    title: Text = ()
    break_after: bool = False
    break_before: bool = False


def assembled(language: str, sections: list[Section], closing: list[str], fingerprint: str = ""):
    """The document of several analyses: every table and figure, in the sections' order."""
    return ApaDocument(
        "results",
        language,
        tuple(t for s in sections for t in s.tables),
        tuple(f for s in sections for f in s.figures),
        "",
        fingerprint,
        tuple(sections),
        tuple(closing),
    )


def _note(parts) -> Text:
    """A note given as texts, one after the other."""
    return _join(parts, " ") if parts else ()


@dataclass
class _Builder:
    """Numbers tables and figures as they come."""

    table_number: int = 1
    figure_number: int = 1
    tables: list[ApaTable] = field(default_factory=list)
    figures: list[ApaFigure] = field(default_factory=list)

    def table(self, title, columns, rows, spanners=(), note=()) -> None:
        self.tables.append(
            ApaTable(
                f"table-{len(self.tables) + 1}",
                self.table_number,
                title,
                tuple(columns),
                tuple(rows),
                tuple(spanners),
                _note(note),
            )
        )
        self.table_number += 1

    def figure(self, title, kind, x_label, y_label, note=(), **values) -> None:
        self.figures.append(
            ApaFigure(
                f"figure-{len(self.figures) + 1}",
                self.figure_number,
                title,
                kind,
                x_label,
                y_label,
                note=_note(note),
                **values,
            )
        )
        self.figure_number += 1


def _join(parts: Iterable[Text], separator: str = " ") -> Text:
    found: list[Run] = []
    for i, part in enumerate(parts):
        if i:
            found.append(Run(separator))
        found.extend(part)
    return tuple(found)


def _left(text: str | Text) -> Column:
    return Column(rich(text) if isinstance(text, str) else text, "left")


def _col(text: str | Text) -> Column:
    return Column(rich(text) if isinstance(text, str) else text)


def _row(*cells: str | Text, indent: int = 0) -> Row:
    return Row(tuple(rich(c) if isinstance(c, str) else c for c in cells), indent)


def _mean_ci(values: np.ndarray) -> tuple[float, float, float]:
    """The mean and its 95 % interval, by the t distribution."""
    mean = float(values.mean())
    if len(values) < 2:
        return mean, mean, mean
    half = float(stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return mean, mean - half, mean + half


# --- Table 1. ---


def _table1(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    table = prepared.table
    variables = result.chosen["variables"]
    group = (result.chosen.get("group") or [None])[0]
    kept = table[table[group].notna()] if group else table
    parts = []
    if group:
        parts = [
            (book.category(group, c), kept[kept[group] == c])
            for c in _codes(book, group, kept[group])
        ]
    columns = [_left(_("Caractéristique"))]
    # No-break spaces: "(n = 150)" never cut in two.
    columns += [
        _col(rich(f"{name} (", it("n"), f"{NBSP}={NBSP}{len(part)})")) for name, part in parts
    ]
    columns.append(_col(rich(_("Total") + " (", it("N"), f"{NBSP}={NBSP}{len(kept)})")))
    every = [part for _name, part in parts] + [kept]
    rows, missing, small = [], [], []
    na = prepared.not_applicable  # v0.21 (D-167)
    filtered = [n for n in variables if na is not None and n in na.columns]
    for name in variables:
        label = book.label(name)
        # A filtered question: its percentages among those who answered it; its note says
        # whom it was asked, never "missing" for those who were not.
        asked = (~na[name]).loc[kept.index] if name in filtered else None
        # A filtered question: only those it was asked (an answer under a false condition
        # stays out of the table, and the note counts it).
        shown = every if asked is None else [p[asked.loc[p.index].to_numpy()] for p in every]
        if book.levels.get(name) == "scale":
            cells = [
                f"{apa(p[name].mean())} ({apa(p[name].std())})" if p[name].notna().any() else ""
                for p in shown
            ]
            rows.append(_row(rich(f"{label}, ", it("M"), " (", it(_("ÉT")), ")"), *cells))
        else:
            rows.append(_row(rich(f"{label}, ", it("n"), " (%)"), *[""] * len(every)))
            counts = kept[name].value_counts()
            order = [c for c in book.value_labels(name) if c in counts.index]
            order += [c for c in counts.index if c not in order]
            for code in order:
                category = book.category(name, code)
                rows.append(
                    _row(
                        category,
                        *[
                            count_pct(
                                int((p[name] == code).sum()),
                                int(p[name].notna().sum()) if asked is not None else len(p),
                            )
                            for p in shown
                        ],
                        indent=1,
                    )
                )
                if counts[code] < SMALL:
                    small.append(f"{label} : {category}")
        if asked is not None:
            n_asked = int(asked.sum())
            unanswered = int((asked & kept[name].isna()).sum())
            text = _("{label} : question posée à {n} personnes").format(label=label, n=n_asked)
            if unanswered:
                text += _(" ; {n} sans réponse").format(n=unanswered)
            outside = int((~asked & kept[name].notna()).sum())
            if outside:
                text += _(" ; {n} réponses sous une condition fausse, hors du tableau").format(
                    n=outside
                )
            missing.append(text)
            continue
        lost = int(kept[name].isna().sum())
        if lost:
            missing.append(_("{label} : {n} valeurs manquantes").format(label=label, n=lost))
    note = [_("Pourcentages calculés sur l'effectif de chaque colonne.")]
    if any(book.levels.get(n) != "scale" for n in filtered):
        note = [
            _(
                "Pourcentages calculés sur l'effectif de chaque colonne ; pour une question "
                "filtrée, parmi les personnes qui y ont répondu."
            )
        ]
    if missing:
        note.insert(0, "; ".join(missing) + ".")
    if small:
        note.append(_("Moins de {n} personnes : {cases}.").format(n=SMALL, cases="; ".join(small)))
    if group and len(kept) < len(table):
        note.append(
            _("{n} personnes sans {group} écartées.").format(
                n=len(table) - len(kept), group=book.label(group)
            )
        )
    title = _("Caractéristiques des participants")
    if group:
        title = _("Caractéristiques des participants selon {group}").format(
            group=_mid(book.label(group))
        )
    b.table(title, columns, rows, note=[rich(" ".join(note))])


# --- t test. ---


def _two_groups(book, prepared, result):
    outcome, group = result.chosen["outcome"][0], result.chosen["group"][0]
    data = prepared.table[[outcome, group]].dropna()
    codes = sorted(set(data[group]))
    if result.options.get("levels"):
        wanted = chosen_levels(result.options["levels"], data[group])
        codes = [c for c in wanted if c in set(data[group])]
    codes = codes[:2]
    samples = [data.loc[data[group] == c, outcome].to_numpy(float) for c in codes]
    return outcome, group, [book.category(group, c) for c in codes], samples


def _t_test(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    s = result.statistics
    outcome, group, names, samples = _two_groups(book, prepared, result)
    label = book.label(outcome)
    title = _("{outcome} selon {group}").format(outcome=label, group=_mid(book.label(group)))
    sizes_text = _join(
        [
            marked(_("{group} : {n} = {count}"), group=name, n=it("n"), count=len(x))
            for name, x in zip(names, samples, strict=True)
        ],
        _(" ; "),
    )
    if result.options.get("method") == "mann_whitney":
        b.table(
            title,
            [
                _left(_("Variable")),
                _col(rich(it("Mdn"))),
                _col(rich(it("Mdn"))),
                _col(rich(it("U"))),
                _col(rich(it("p"))),
                _col(rich(it("r"))),
            ],
            [
                _row(
                    label,
                    apa(s["mdn1"]),
                    apa(s["mdn2"]),
                    apa(s["U"], 1),
                    p_cell(s["p"]),
                    apa(s["rb"], zero=False),
                )
            ],
            spanners=[Spanner(rich(names[0]), 1, 1), Spanner(rich(names[1]), 2, 2)],
            note=[
                marked(
                    _("{sizes}. Test de Mann-Whitney ; {r} : corrélation bisériale de rang."),
                    sizes=sizes_text,
                    r=it("r"),
                )
            ],
        )
        return
    welch = result.options.get("method", "welch") == "welch"
    df = apa(s["df"]) if welch else str(int(s["df"]))
    b.table(
        title,
        [
            _left(_("Variable")),
            _col(rich(it("M"))),
            _col(rich(it(_("ÉT")))),
            _col(rich(it("M"))),
            _col(rich(it(_("ÉT")))),
            _col(rich(it("t"), f"({df})")),
            _col(rich(it("p"))),
            _col(rich(it("d"))),
            _col(marked(_("IC 95 % de {stat}"), stat=it("d"))),
        ],
        [
            _row(
                label,
                apa(s["m1"]),
                apa(s["sd1"]),
                apa(s["m2"]),
                apa(s["sd2"]),
                apa(s["t"]),
                p_cell(s["p"]),
                apa(s["d"]),
                brackets(s["d_low"], s["d_high"]),
            )
        ],
        spanners=[Spanner(rich(names[0]), 1, 2), Spanner(rich(names[1]), 3, 4)],
        note=[
            marked(
                _(
                    "{sizes}. Test {t} de Welch (variances inégales permises). {d} de Cohen "
                    "calculé avec l'écart-type combiné."
                )
                if welch
                else _(
                    "{sizes}. Test {t} de Student (variances égales supposées). {d} de Cohen "
                    "calculé avec l'écart-type combiné."
                ),
                sizes=sizes_text,
                t=it("t"),
                d=it("d"),
            )
        ],
    )
    _bars(b, book, label, group, names, samples)


def _bars(b, book, label, group, names, samples) -> None:
    ci = [_mean_ci(x) for x in samples]
    total = sum(len(x) for x in samples)
    b.figure(
        _("Moyenne de {outcome} selon {group}").format(
            outcome=_mid(label), group=_mid(book.label(group))
        ),
        "bars",
        book.label(group),
        label,
        categories=tuple(names),
        series=(
            Series(
                label,
                tuple(m for m, _l, _h in ci),
                tuple(lo for _m, lo, _h in ci),
                tuple(hi for _m, _l, hi in ci),
            ),
        ),
        y_min=0.0,
        note=[
            marked(
                _(
                    "Les barres d'erreur représentent l'intervalle de confiance à 95 % de la "
                    "moyenne. {N} = {n}."
                ),
                N=it("N"),
                n=total,
            )
        ],
    )


# --- Paired t test (v0.14). ---


def _paired(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    s = result.statistics
    first, second = result.chosen["first"][0], result.chosen["second"][0]
    names = [book.label(first), book.label(second)]
    data = prepared.table[[first, second]].dropna()
    title = _("{a} et {b}").format(a=names[0], b=_mid(names[1]))
    spanners = [Spanner(rich(names[0]), 1, 1), Spanner(rich(names[1]), 2, 2)]
    if result.options.get("method") == "wilcoxon":
        b.table(
            title,
            [
                _left(_("Paire")),
                _col(rich(it("Mdn"))),
                _col(rich(it("Mdn"))),
                _col(rich(it("V"))),
                _col(rich(it("p"))),
                _col(rich(it("r"))),
            ],
            [
                _row(
                    marked("{n} = {count}", n=it("n"), count=int(s["n"])),
                    apa(s["mdn1"]),
                    apa(s["mdn2"]),
                    apa(s["V"], 1),
                    p_cell(s["p"]),
                    apa(s["rb"], zero=False),
                )
            ],
            spanners=spanners,
            note=[
                marked(
                    _(
                        "Test de Wilcoxon des rangs signés ; différences nulles écartées : "
                        "{zeros}. {r} : corrélation bisériale de rang, positive quand la "
                        "première mesure est plus élevée."
                    ),
                    zeros=int(s["zeros"]),
                    r=it("r"),
                )
            ],
        )
    else:
        spanners = [Spanner(rich(names[0]), 1, 2), Spanner(rich(names[1]), 3, 4)]
        b.table(
            title,
            [
                _left(_("Paire")),
                _col(rich(it("M"))),
                _col(rich(it(_("ÉT")))),
                _col(rich(it("M"))),
                _col(rich(it(_("ÉT")))),
                _col(_("Différence")),
                _col(rich(it("t"), f"({int(s['df'])})")),
                _col(rich(it("p"))),
                _col(rich(it("d"), Run("z", sub=True))),
                _col(marked(_("IC 95 % de {stat}"), stat=rich(it("d"), Run("z", sub=True)))),
            ],
            [
                _row(
                    marked("{n} = {count}", n=it("n"), count=int(s["n"])),
                    apa(s["m1"]),
                    apa(s["sd1"]),
                    apa(s["m2"]),
                    apa(s["sd2"]),
                    _join([rich(apa(s["diff"])), rich(brackets(s["diff_low"], s["diff_high"]))]),
                    apa(s["t"]),
                    p_cell(s["p"]),
                    apa(s["d"]),
                    brackets(s["d_low"], s["d_high"]),
                )
            ],
            spanners=spanners,
            note=[
                marked(
                    _(
                        "Test {t} apparié ; la différence est la première mesure moins la "
                        "seconde, avec son IC 95 %. {d} : moyenne des différences divisée par "
                        "leur écart-type."
                    ),
                    t=it("t"),
                    d=rich(it("d"), Run("z", sub=True)),
                )
            ],
        )
    ci = [_mean_ci(data[name].to_numpy(float)) for name in (first, second)]
    b.figure(
        title,
        "line",
        _("Mesure"),
        _("Moyenne"),
        categories=tuple(names),
        series=(
            Series(
                _("Moyenne"),
                tuple(m for m, _l, _h in ci),
                tuple(lo for _m, lo, _h in ci),
                tuple(hi for _m, _l, hi in ci),
            ),
        ),
        note=[
            marked(
                _(
                    "Les barres d'erreur représentent l'intervalle de confiance à 95 % de la "
                    "moyenne. {N} = {n}, les mêmes personnes aux deux mesures."
                ),
                N=it("N"),
                n=len(data),
            )
        ],
    )


# --- ANOVA. ---


def _anova(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    s = result.statistics
    outcome, group = result.chosen["outcome"][0], result.chosen["group"][0]
    data = prepared.table[[outcome, group]].dropna()
    codes = _codes(book, group, data[group])
    samples = [data.loc[data[group] == c, outcome].to_numpy(float) for c in codes]
    names = [book.category(group, c) for c in codes]
    label, group_label = book.label(outcome), book.label(group)
    title = _("{outcome} selon {group}").format(outcome=label, group=_mid(group_label))
    if result.options.get("method") == "kruskal_wallis":
        rows = [
            _row(nm, str(len(x)), apa(float(np.median(x))))
            for nm, x in zip(names, samples, strict=True)
        ]
        b.table(
            title,
            [_left(group_label), _col(rich(it("n"))), _col(rich(it("Mdn")))],
            rows,
            note=[
                rich(
                    it("H"),
                    f"({s['df']}) = {apa(s['H'])}, ",
                    *p_text(s["p"]),
                    f", ε² = {apa(s['epsilon2'], zero=False)}.",
                )
            ],
        )
        return
    rows = []
    for nm, x in zip(names, samples, strict=True):
        mean, low, high = _mean_ci(x)
        rows.append(
            _row(nm, str(len(x)), apa(mean), apa(float(x.std(ddof=1))), brackets(low, high))
        )
    b.table(
        title,
        [
            _left(group_label),
            _col(rich(it("n"))),
            _col(rich(it("M"))),
            _col(rich(it(_("ÉT")))),
            _col(marked(_("IC 95 % de {stat}"), stat=it("M"))),
        ],
        rows,
        note=[
            rich(
                it("F"),
                f"({s['df1']}, {s['df2']}) = {apa(s['F'])}, ",
                *p_text(s["p"]),
                f", η² = {apa(s['eta2'], zero=False)}, ω² = {apa(s['omega2'], zero=False)}.",
            )
        ],
    )
    if result.options.get("post_hoc") == "tukey":
        rows = []
        ordered = sorted(codes)  # as the Tukey test orders them
        for i, first in enumerate(ordered):
            for second in ordered[i + 1 :]:
                key = f"{int(second)}_{int(first)}"
                rows.append(
                    _row(
                        f"{book.category(group, second)} − {book.category(group, first)}",
                        apa(s[f"tukey_{key}"]),
                        brackets(s[f"tukey_low_{key}"], s[f"tukey_high_{key}"]),
                        p_cell(s[f"tukey_p_{key}"]),
                    )
                )
        b.table(
            _("Comparaisons deux à deux de {outcome} (Tukey)").format(outcome=_mid(label)),
            [
                _left(_("Comparaison")),
                _col(_("Différence")),
                _col(_("IC 95 %")),
                _col(rich(it("p"))),
            ],
            rows,
            note=[
                marked(
                    _(
                        "Différences de moyennes ; intervalles et {p} ajustés par la méthode "
                        "de Tukey."
                    ),
                    p=it("p"),
                )
            ],
        )
    _bars(b, book, label, group, names, samples)


# --- Chi-square. ---


def _chi_square(
    b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult
) -> None:
    s = result.statistics
    row_name, col_name = result.chosen["rows"][0], result.chosen["columns"][0]
    data = prepared.table[[row_name, col_name]].dropna()
    observed = pd.crosstab(data[row_name], data[col_name])
    totals = observed.sum()
    columns = [_left(book.label(row_name))]
    columns += [
        _col(rich(f"{book.category(col_name, c)} ", it("n"), " (%)")) for c in observed.columns
    ]
    rows = [
        _row(
            book.category(row_name, r),
            *[count_pct(int(observed.loc[r, c]), int(totals[c])) for c in observed.columns],
        )
        for r in observed.index
    ]
    rows.append(_row(_("Total"), *[str(int(totals[c])) for c in observed.columns]))
    note = marked(
        _(
            "Pourcentages calculés dans chaque colonne. χ²({df}, {N} = {n}) = {chi2}, {p}, {V} "
            "de Cramér = {v}."
        ),
        df=s["df"],
        N=it("N"),
        n=s["n"],
        chi2=apa(s["chi2"]),
        p=p_text(s["p"]),
        V=it("V"),
        v=apa(s["V"], zero=False),
    )
    if "fisher_p" in s:
        note += marked(" " + _("Test exact de Fisher : {p}."), p=p_text(s["fisher_p"]))
    b.table(
        _("{rows} selon {columns}").format(
            rows=book.label(row_name), columns=_mid(book.label(col_name))
        ),
        columns,
        rows,
        note=[note],
    )
    percent = observed / totals * 100
    b.figure(
        _("Pourcentage de {rows} selon {columns}").format(
            rows=_mid(book.label(row_name)), columns=_mid(book.label(col_name))
        ),
        "grouped_bars",
        book.label(col_name),
        _("Pourcentage de la colonne"),
        categories=tuple(book.category(col_name, c) for c in observed.columns),
        series=tuple(
            Series(book.category(row_name, r), tuple(float(v) for v in percent.loc[r]))
            for r in observed.index
        ),
        legend_title=book.label(row_name),
        y_min=0.0,
        y_max=100.0,
        note=[rich(it("N"), f" = {s['n']}.")],
    )


# --- Correlation. ---


def _correlation(
    b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult
) -> None:
    from ddict.analysis.compute import _pair

    names = result.chosen["variables"]
    spearman = result.options.get("method") == "spearman"
    symbol = "ρ" if spearman else "r"
    table = prepared.table
    pairs = {
        (i, j): _pair(table[names[i]], table[names[j]], result.options.get("method", "pearson"))
        for i in range(len(names))
        for j in range(i)
    }
    columns = [
        _left(_("Variable")),
        _col(rich(it("n"))),
        _col(rich(it("M"))),
        _col(rich(it(_("ÉT")))),
    ]
    columns += [_col(str(k + 1)) for k in range(len(names))]
    rows = []
    for i, name in enumerate(names):
        # Who enters at least one correlation of the table (step 7: a variable's own n
        # beside N = 182 read as a contradiction).
        others = table[[n for k, n in enumerate(names) if k != i]].notna().any(axis=1)
        x = table.loc[table[name].notna() & others, name]
        cells = []
        for j in range(len(names)):
            if j < i:
                pair = pairs[(i, j)]
                cell = apa(pair["r"], zero=False)
                if "ci_low" in pair:
                    cell += " " + brackets(pair["ci_low"], pair["ci_high"], zero=False)
                cells.append(cell)
            else:
                cells.append("—" if j == i else "")
        rows.append(
            _row(
                f"{i + 1}. {book.label(name)}",
                str(len(x)),
                apa(float(x.mean())),
                apa(float(x.std())),
                *cells,
            )
        )
    sizes = [pair["n"] for pair in pairs.values()]
    kind = (
        _("Corrélations de Spearman.")
        if spearman
        else _("Corrélations de Pearson ; entre crochets, l'IC 95 %.")
    )
    if min(sizes) == max(sizes):
        note = marked(kind + " " + "{N} = {n}.", N=it("N"), n=sizes[0])
    else:
        note = marked(
            kind
            + " "
            + _(
                "Chaque corrélation est calculée sur les personnes qui ont les deux valeurs "
                "({n} de {a} à {b})."
            ),
            n=it("n"),
            a=min(sizes),
            b=max(sizes),
        )
    for i in range(1, len(names)):
        ps = [p_text(pairs[(i, j)]["p"]) for j in range(i)]
        note += marked(" " + _("Ligne {i} : {ps}."), i=i + 1, ps=_join(ps, _(" et ")))
    b.table(_("Statistiques descriptives et corrélations"), columns, rows, note=[note])
    if len(names) != 2:
        return
    a, c = names
    both = table[[a, c]].dropna()
    pair = pairs[(1, 0)]
    slope, intercept = np.polyfit(both[a].to_numpy(float), both[c].to_numpy(float), 1)
    stat = rich(it(symbol) if symbol == "r" else symbol, f" = {apa(pair['r'], zero=False)}")
    if "ci_low" in pair:
        stat += rich(
            ", "
            + _("IC 95 % {ci}").format(ci=brackets(pair["ci_low"], pair["ci_high"], zero=False))
        )
    b.figure(
        _("{y} selon {x}").format(y=book.label(c), x=_mid(book.label(a))),
        "scatter",
        book.label(a),
        book.label(c),
        points=tuple((float(u), float(v)) for u, v in zip(both[a], both[c], strict=True)),
        line=None if spearman else (float(intercept), float(slope)),
        note=[rich(it("N"), f" = {len(both)}. ", *stat, ".")],
    )


# --- Regression. ---


def _regression(
    b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult
) -> None:
    s = result.statistics
    outcome = result.chosen["outcome"][0]
    # The constant in the language asked, then each term as the analysis named it.
    labels = [_("Constante"), *[r[0] for r in result.tables[0].rows[1:]]]
    rows = []
    for i, label in enumerate(labels):
        rows.append(
            _row(
                label,
                apa(s[f"coef_{i}"]),
                brackets(s[f"low_{i}"], s[f"high_{i}"]),
                apa(s[f"se_{i}"]),
                apa(s[f"beta_{i}"], zero=False) if i else "",
                apa(s[f"t_{i}"]),
                p_cell(s[f"p_{i}"]),
            )
        )
    note = marked(
        _(
            "{N} = {n}. {R}² = {r2}, {R}² ajusté = {adj}, {F}({df1}, {df2}) = {f}, {p}. {b} : "
            "coefficient non standardisé ; β : coefficient standardisé ; {se} : erreur type."
        ),
        N=it("N"),
        n=s["n"],
        R=it("R"),
        r2=apa(s["r2"], zero=False),
        adj=apa(s["r2adj"], zero=False),
        F=it("F"),
        df1=int(s["df1"]),
        df2=int(s["df2"]),
        f=apa(s["F"]),
        p=p_text(s["Fp"]),
        b=it("b"),
        se=it(_("ET")),
    )
    references = []
    for name in result.chosen["predictors"]:
        if book.levels.get(name) == "nominal":
            data = prepared.table[[outcome, *result.chosen["predictors"]]].dropna()
            first = sorted(_codes(book, name, data[name]))[0]
            references.append(
                _("Référence pour {var} : {cat}.").format(
                    var=book.label(name), cat=book.category(name, first)
                )
            )
    if references:
        note += rich(" " + " ".join(references))
    b.table(
        _("Régression de {outcome}").format(outcome=_mid(book.label(outcome))),
        [
            _left(_("Prédicteur")),
            _col(rich(it("b"))),
            _col(marked(_("IC 95 % de {stat}"), stat=it("b"))),
            _col(rich(it(_("ET")))),
            _col("β"),
            _col(rich(it("t"))),
            _col(rich(it("p"))),
        ],
        rows,
        note=[note],
    )
    terms = range(1, len(labels))
    b.figure(
        _("Coefficients standardisés de la régression de {outcome}").format(
            outcome=_mid(book.label(outcome))
        ),
        "coefficients",
        _("Coefficient standardisé (β)"),
        "",
        categories=tuple(labels[i] for i in terms),
        series=(
            Series(
                "β",
                tuple(s[f"beta_{i}"] for i in terms),
                tuple(s[f"beta_low_{i}"] for i in terms),
                tuple(s[f"beta_high_{i}"] for i in terms),
            ),
        ),
        reference=0.0,
        note=[
            marked(
                _("Les barres d'erreur représentent l'IC 95 % de β. {N} = {n}."),
                N=it("N"),
                n=s["n"],
            )
        ],
    )


# --- Partial correlation (v0.14). ---


def _partial(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    from ddict.analysis.models import _residuals, design

    s = result.statistics
    (first, second), covariates = result.chosen["variables"], result.chosen["covariates"]
    data = prepared.table[[first, second, *covariates]].dropna()
    n = int(s["n"])
    half = float(stats.norm.ppf(0.975) / np.sqrt(n - 3))
    simple = (np.tanh(np.arctanh(s["r_simple"]) - half), np.tanh(np.arctanh(s["r_simple"]) + half))
    held = ", ".join(book.label(c) for c in covariates)
    b.table(
        _("Corrélation simple et partielle de {a} et {b}").format(
            a=_mid(book.label(first)), b=_mid(book.label(second))
        ),
        [
            _left(_("Variables")),
            _col(rich(it("n"))),
            _col(rich(it("r"))),
            _col(marked(_("IC 95 % de {stat}"), stat=it("r"))),
            _col(marked(_("{r} partiel"), r=it("r"))),
            _col(marked(_("IC 95 % de {stat}"), stat=marked(_("{r} partiel"), r=it("r")))),
            _col(rich(it("t"), f"({int(s['df'])})")),
            _col(rich(it("p"))),
        ],
        [
            _row(
                f"{book.label(first)} — {book.label(second)}",
                str(n),
                apa(s["r_simple"], zero=False),
                brackets(*simple, zero=False),
                apa(s["r"], zero=False),
                brackets(s["ci_low"], s["ci_high"], zero=False),
                apa(s["t"]),
                p_cell(s["p"]),
            )
        ],
        note=[
            marked(
                _(
                    "Corrélations de Pearson ; le {r} partiel est la corrélation des résidus des "
                    "deux variables régressées sur les covariables : {held}. Le {p} est celui du "
                    "{r} partiel ; celui du {r} simple : {simple}."
                ),
                r=it("r"),
                held=held,
                p=it("p"),
                simple=p_text(s["p_simple"]),
            )
        ],
    )
    Z = design(book, data, covariates)
    rx, ry = _residuals(data[first], Z), _residuals(data[second], Z)
    slope = float(np.dot(rx, ry) / np.dot(rx, rx))
    b.figure(
        _("Résidus de {y} selon les résidus de {x}").format(
            y=_mid(book.label(second)), x=_mid(book.label(first))
        ),
        "scatter",
        _("Résidus de {x}").format(x=_mid(book.label(first))),
        _("Résidus de {y}").format(y=_mid(book.label(second))),
        points=tuple((float(u), float(v)) for u, v in zip(rx, ry, strict=True)),
        line=(0.0, slope),
        note=[
            marked(
                _("{N} = {n}. Covariables : {held}. {r} partiel = {r_value}."),
                N=it("N"),
                n=n,
                held=held,
                r=it("r"),
                r_value=apa(s["r"], zero=False),
            )
        ],
    )


# --- Moderation (v0.14). ---


def _moderation(
    b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult
) -> None:
    from ddict.analysis.models import moderation_design

    s = result.statistics
    chosen = result.chosen
    outcome, focal = chosen["outcome"][0], chosen["focal"][0]
    moderator, covariates = chosen["moderator"][0], chosen.get("covariates", [])
    data = prepared.table[[outcome, focal, moderator, *covariates]].dropna()
    _y, X, at, nominal = moderation_design(book, data, chosen, result.options)
    labels = [r[0] for r in result.tables[0].rows]
    labels[0] = _("Constante")
    rows = [
        _row(
            label,
            apa(s[f"coef_{i}"]),
            brackets(s[f"low_{i}"], s[f"high_{i}"]),
            apa(s[f"se_{i}"]),
            apa(s[f"t_{i}"]),
            p_cell(s[f"p_{i}"]),
        )
        for i, label in enumerate(labels)
    ]
    centred = result.options.get("center", "yes") == "yes"
    note = marked(
        _(
            "{N} = {n}. {R}² = {r2} ; interaction : Δ{R}² = {dr2}, {F}(1, {df}) = {f}, {p}. "
            "{b} : coefficient non standardisé ; {se} : erreur type."
        ),
        N=it("N"),
        n=int(s["n"]),
        R=it("R"),
        r2=apa(s["r2"], zero=False),
        dr2=apa(s["delta_r2"], zero=False),
        F=it("F"),
        df=int(s["df_resid"]),
        f=apa(s["f_change"]),
        p=p_text(s["f_change_p"]),
        b=it("b"),
        se=it(_("ET")),
    )
    if centred:
        note += rich(" " + _("Les variables continues du terme d'interaction sont centrées."))
    b.table(
        _("Modération de {outcome}").format(outcome=_mid(book.label(outcome))),
        [
            _left(_("Prédicteur")),
            _col(rich(it("b"))),
            _col(marked(_("IC 95 % de {stat}"), stat=it("b"))),
            _col(rich(it(_("ET")))),
            _col(rich(it("t"))),
            _col(rich(it("p"))),
        ],
        rows,
        note=[note],
    )
    slope_rows = [
        _row(
            label,
            apa(s[f"slope_{j}"]),
            brackets(s[f"slope_{j}_low"], s[f"slope_{j}_high"]),
            apa(s[f"slope_{j}_se"]),
            apa(s[f"slope_{j}_t"]),
            p_cell(s[f"slope_{j}_p"]),
        )
        for j, (_value, label) in enumerate(at, start=1)
    ]
    b.table(
        _("Pentes simples de {x} selon {w}").format(
            x=_mid(book.label(focal)), w=_mid(book.label(moderator))
        ),
        [
            _left(book.label(moderator)),
            _col(rich(it("b"))),
            _col(marked(_("IC 95 % de {stat}"), stat=it("b"))),
            _col(rich(it(_("ET")))),
            _col(rich(it("t"), f"({int(s['df_resid'])})")),
            _col(rich(it("p"))),
        ],
        slope_rows,
        note=[
            marked(
                _("La pente de {x} à chaque valeur de {w}, avec son IC 95 %."),
                x=_mid(book.label(focal)),
                w=_mid(book.label(moderator)),
            )
        ],
    )
    # The predicted values at -1 SD, the mean and +1 SD of the predictor, for each value of
    # the moderator; the covariates at their mean.
    x = X.iloc[:, 0]
    sd = float(x.std(ddof=1))
    points = [float(x.mean()) - sd, float(x.mean()), float(x.mean()) + sd]
    last = X.shape[1]
    others = sum(s[f"coef_{i + 1}"] * float(X.iloc[:, i].mean()) for i in range(2, last - 1))
    series = []
    for value, label in at:
        values = tuple(
            s["coef_0"] + s["coef_1"] * p + s["coef_2"] * value + s[f"coef_{last}"] * p * value
            + others
            for p in points
        )  # fmt: skip
        name = label if nominal else f"{book.label(moderator)} : {label}"
        series.append(Series(name, values))
    b.figure(
        _("Valeurs prédites de {y} selon {x} et {w}").format(
            y=_mid(book.label(outcome)), x=_mid(book.label(focal)), w=_mid(book.label(moderator))
        ),
        "line",
        book.label(focal),
        book.label(outcome),
        categories=(_("−1 ÉT"), _("moyenne"), _("+1 ÉT")),
        series=tuple(series),
        legend_title=book.label(moderator),
        note=[
            marked(
                _(
                    "Valeurs prédites par le modèle, à −1 écart-type, à la moyenne et à +1 "
                    "écart-type de {x}{covariates}. {N} = {n}."
                ),
                x=_mid(book.label(focal)),
                covariates=_(", les covariables à leur moyenne") if covariates else "",
                N=it("N"),
                n=int(s["n"]),
            )
        ],
    )


# --- Binary logistic regression (v0.14). ---


def _logistic(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    s = result.statistics
    outcome, predictors = result.chosen["outcome"][0], result.chosen["predictors"]
    data = prepared.table[[outcome, *predictors]].dropna()
    codes = sorted(set(data[outcome]))
    event = codes[1] if result.options.get("event", "second") == "second" else codes[0]
    labels = [_("Constante"), *[r[0] for r in result.tables[0].rows[1:]]]
    rows = [
        _row(
            label,
            apa(s[f"coef_{i}"]),
            apa(s[f"se_{i}"]),
            apa(s[f"z_{i}"]),
            p_cell(s[f"p_{i}"]),
            apa(s[f"or_{i}"]) if i else "",
            brackets(s[f"or_low_{i}"], s[f"or_high_{i}"]) if i else "",
        )
        for i, label in enumerate(labels)
    ]
    note = marked(
        _(
            "{N} = {n}, dont {k} « {event} », la modalité prédite. χ²({df}) = {chi2}, {p}, face "
            "au modèle sans prédicteur ; {R}² de McFadden = {mf}, de Nagelkerke = {ng}. {b} : "
            "coefficient ; {se} : erreur type ; RC : rapport de cotes, avec son IC 95 % (Wald)."
        ),
        N=it("N"),
        n=int(s["n"]),
        k=int(s["events"]),
        event=book.category(outcome, event),
        df=int(s["df"]),
        chi2=apa(s["chi2"]),
        p=p_text(s["chi2_p"]),
        R=it("R"),
        mf=apa(s["mcfadden"], zero=False),
        ng=apa(s["nagelkerke"], zero=False),
        b=it("b"),
        se=it(_("ET")),
    )
    references = []
    for name in predictors:
        if book.levels.get(name) == "nominal":
            first = sorted(_codes(book, name, data[name]))[0]
            references.append(
                _("Référence pour {var} : {cat}.").format(
                    var=book.label(name), cat=book.category(name, first)
                )
            )
    if references:
        note += rich(" " + " ".join(references))
    b.table(
        _("Régression logistique de {outcome}").format(outcome=_mid(book.label(outcome))),
        [
            _left(_("Prédicteur")),
            _col(rich(it("b"))),
            _col(rich(it(_("ET")))),
            _col(rich(it("z"))),
            _col(rich(it("p"))),
            _col(_("RC")),
            _col(_("IC 95 % du RC")),
        ],
        rows,
        note=[note],
    )
    terms = range(1, len(labels))
    b.figure(
        _("Rapports de cotes de la régression logistique de {outcome}").format(
            outcome=_mid(book.label(outcome))
        ),
        "coefficients",
        _("Rapport de cotes (échelle logarithmique)"),
        "",
        categories=tuple(labels[i] for i in terms),
        series=(
            Series(
                _("RC"),
                tuple(s[f"or_{i}"] for i in terms),
                tuple(s[f"or_low_{i}"] for i in terms),
                tuple(s[f"or_high_{i}"] for i in terms),
            ),
        ),
        reference=1.0,
        log_scale=True,
        note=[
            marked(
                _(
                    "Les barres d'erreur représentent l'IC 95 % du rapport de cotes ; la ligne "
                    "verticale marque 1, aucun lien. {N} = {n}."
                ),
                N=it("N"),
                n=int(s["n"]),
            )
        ],
    )


# --- Repeated-measures ANOVA (v0.14). ---


def _rm_anova(b: _Builder, book: Codebook, prepared: PreparedData, result: AnalysisResult) -> None:
    s = result.statistics
    names = result.chosen["measures"]
    labels = [book.label(name) for name in names]
    data = prepared.table[names].dropna()
    n = int(s["n"])
    rows = [
        _row(label, apa(s[f"m_{i}"]), apa(s[f"sd_{i}"])) for i, label in enumerate(labels, start=1)
    ]
    note = marked(
        _(
            "{N} = {n}, les mêmes personnes à chaque mesure. {F}({df1}, {df2}) = {f}, {p}, "
            "η² partiel = {eta}. Sphéricité : {W} de Mauchly = {w}, {wp} ; Greenhouse-Geisser : "
            "ε = {eps}, {F}({gdf1} ; {gdf2}), {gp}."
        ),
        N=it("N"),
        n=n,
        F=it("F"),
        df1=int(s["df1"]),
        df2=int(s["df2"]),
        f=apa(s["F"]),
        p=p_text(s["p_uncorrected"]),
        eta=apa(s["eta2p"], zero=False),
        W=it("W"),
        w=apa(s["mauchly_W"]),
        wp=p_text(s["mauchly_p"]),
        eps=apa(s["gg_eps"]),
        gdf1=apa(s["gg_df1"]),
        gdf2=apa(s["gg_df2"]),
        gp=p_text(s["gg_p"]),
    )
    title = _("Mesures répétées de {first} à {last}").format(
        first=_mid(labels[0]), last=_mid(labels[-1])
    )
    b.table(
        title,
        [_left(_("Mesure")), _col(rich(it("M"))), _col(rich(it(_("ÉT"))))],
        rows,
        note=[note],
    )
    if result.options.get("post_hoc") == "holm":
        k = len(names)
        post = []
        for i in range(k):
            for j in range(i + 1, k):
                key = f"ph_{i + 1}_{j + 1}"
                post.append(
                    _row(
                        f"{labels[i]} − {labels[j]}",
                        apa(s[f"{key}_diff"]),
                        apa(s[f"{key}_t"]),
                        p_cell(s[f"{key}_p"]),
                        p_cell(s[f"{key}_p_holm"]),
                    )
                )
        b.table(
            _("Comparaisons deux à deux des mesures"),
            [
                _left(_("Paire")),
                _col(_("Différence")),
                _col(rich(it("t"), f"({n - 1})")),
                _col(rich(it("p"))),
                _col(marked(_("{p} corrigé ({method})"), p=it("p"), method="Holm")),
            ],
            post,
            note=[
                rich(_("Tests t appariés ; la différence est la première mesure moins la seconde."))
            ],
        )
    ci = [_mean_ci(data[name].to_numpy(float)) for name in names]
    b.figure(
        title,
        "line",
        _("Mesure"),
        _("Moyenne"),
        categories=tuple(labels),
        series=(
            Series(
                _("Moyenne"),
                tuple(m for m, _l, _h in ci),
                tuple(lo for _m, lo, _h in ci),
                tuple(hi for _m, _l, hi in ci),
            ),
        ),
        note=[
            marked(
                _(
                    "Les barres d'erreur représentent l'intervalle de confiance à 95 % de la "
                    "moyenne. {N} = {n}, les mêmes personnes à chaque mesure."
                ),
                N=it("N"),
                n=n,
            )
        ],
    )


def filtered_notes(project: Project, prepared: PreparedData, result: AnalysisResult) -> list[str]:
    """For each filtered variable of the analysis (v0.21, D-167): "Nombre d'enfants : posée
    seulement si enfants = Oui ; l'analyse porte sur les personnes à qui elle a été posée." """
    from ddict.export import wording as w

    na = prepared.not_applicable
    if na is None:
        return []
    book = Codebook(project, prepared)
    found = []
    for names in result.chosen.values():
        for name in names or []:
            words = w.asked_words(project, name) if name in na.columns else None
            if words:
                found.append(
                    _(
                        "{label} : posée seulement si {condition} ; l'analyse porte sur les "
                        "personnes à qui elle a été posée."
                    ).format(label=book.label(name), condition=words)
                )
    return list(dict.fromkeys(found))


BUILDERS = {
    "table1": _table1,
    "t_test": _t_test,
    "paired": _paired,
    "rm_anova": _rm_anova,
    "logistic": _logistic,
    "partial": _partial,
    "moderation": _moderation,
    "anova": _anova,
    "chi_square": _chi_square,
    "correlation": _correlation,
    "regression": _regression,
}


def describe(
    project: Project,
    prepared: PreparedData,
    result: AnalysisResult,
    *,
    language: str | None = None,
    first_table: int = 1,
    first_figure: int = 1,
) -> ApaDocument:
    """The tables and figures of an analysis, in the language asked (the interface's)."""
    with i18n.using(language):
        book = Codebook(project, prepared)
        builder = _Builder(first_table, first_figure)
        # The tables and figures read the data again: those of the subgroup's people only.
        if result.subgroup is not None:
            prepared = apply_subset(prepared, result.subgroup)
        BUILDERS[result.analysis](builder, book, prepared, result)
        tables, figures = builder.tables, builder.figures
        if result.subgroup_text:  # v0.14 (D-113): every note says who was analysed
            said = rich(
                _("Sous-groupe : {condition}.").format(condition=result.subgroup_text) + " "
            )
            tables = [replace(t, note=said + t.note) for t in tables]
            figures = [replace(f, note=said + f.note) for f in figures]
        filtered = filtered_notes(project, prepared, result)
        if filtered and result.analysis != "table1":  # v0.21: Table 1 says it its own way
            said = rich(" ".join(filtered) + " ")
            tables = [replace(t, note=said + t.note) for t in tables]
            figures = [replace(f, note=said + f.note) for f in figures]
        return ApaDocument(
            result.analysis,
            language or i18n.language(),
            tuple(tables),
            tuple(figures),
            result.sentence,
            fingerprint.short(project),
        )


@dataclass(frozen=True)
class Edit:
    """What a person may change (D-086); None keeps the computed value."""

    number: int | None = None
    title: str | None = None
    note: str | None = None


def edited(document: ApaDocument, edits: dict[str, Edit]) -> ApaDocument:
    """The document with a person's numbers, titles and notes; never the numbers inside."""

    def apply(item):
        edit = edits.get(item.key)
        if edit is None:
            return item
        changes = {}
        if edit.number is not None:
            changes["number"] = edit.number
        if edit.title is not None and edit.title.strip():
            changes["title"] = edit.title.strip()
        if edit.note is not None:
            changes["note"] = rich(edit.note.strip()) if edit.note.strip() else ()
        return replace(item, **changes)

    return replace(
        document,
        tables=tuple(apply(t) for t in document.tables),
        figures=tuple(apply(f) for f in document.figures),
    )


# --- The flow of participants (v0.12, step 4, D-098). ---


def describe_flow(project: Project, flow, *, number: int = 1, language: str | None = None):
    """The flow diagram of the exclusion rules, as a figure: the answers received, each
    rule in its rank with who it excluded, the sample analysed. `flow` is
    `PreparedData.flow`; None without a rule (no diagram, D-098)."""
    if flow is None or not flow.excluded:
        return None
    reasons = {rule.id: rule.reason for rule in project.exclusions.rules}
    with i18n.using(language):
        steps, remaining = [], flow.start
        for rule, excluded in flow.excluded:
            remaining -= excluded
            steps.append(FlowStep(rule, reasons.get(rule, rule), excluded, remaining))
        return ApaFigure(
            key="figure-flow",
            number=number,
            title=_("Flux des participants"),
            kind="flow",
            x_label=_("Réponses reçues"),
            y_label=_("Échantillon analysé"),
            note=rich(
                _(
                    "Les exclusions sont appliquées dans l'ordre ; une personne n'est "
                    "comptée que par la première raison qui l'exclut."
                )
            ),
            flow_start=flow.start,
            flow=tuple(steps),
        )
