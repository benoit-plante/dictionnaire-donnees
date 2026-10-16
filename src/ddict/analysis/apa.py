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
from ddict.analysis.data import PreparedData
from ddict.analysis.models import _codes
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


FigureKind = Literal["bars", "grouped_bars", "scatter", "coefficients", "flow"]


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


def _mid(label: str) -> str:
    """A label inside a title: "score de stress", but "TCC" and "QFS total" stay."""
    if len(label) > 1 and label[0].isupper() and label[1].islower():
        return label[0].lower() + label[1:]
    return label


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
    for name in variables:
        label = book.label(name)
        if book.levels.get(name) == "scale":
            cells = [
                f"{apa(p[name].mean())} ({apa(p[name].std())})" if p[name].notna().any() else ""
                for p in every
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
                        *[count_pct(int((p[name] == code).sum()), len(p)) for p in every],
                        indent=1,
                    )
                )
                if counts[code] < SMALL:
                    small.append(f"{label} : {category}")
        lost = int(kept[name].isna().sum())
        if lost:
            missing.append(_("{label} : {n} valeurs manquantes").format(label=label, n=lost))
    note = [_("Pourcentages calculés sur l'effectif de chaque colonne.")]
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
        wanted = [float(c) for c in str(result.options["levels"]).split(",")]
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
        x = table[name].dropna()
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


BUILDERS = {
    "table1": _table1,
    "t_test": _t_test,
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
        BUILDERS[result.analysis](builder, book, prepared, result)
        return ApaDocument(
            result.analysis,
            language or i18n.language(),
            tuple(builder.tables),
            tuple(builder.figures),
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
