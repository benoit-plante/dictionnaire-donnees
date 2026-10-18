"""The APA figures as images (v0.10, step 3), shared by every format that shows an image.

APA 7 style, set once: Arial, greys, axes named, no grid, no frame at the top and right, no
title in the image (it is in the document, editable), error bars as the description gives
them. 16 cm wide, 300 dots per inch. French numbers take a decimal comma.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")  # no window: the image is written in memory

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator

from ddict.analysis.apa import ApaFigure
from ddict.analysis.results import MINUS

WIDTH_CM = 16
HEIGHT_CM = 9.5
DPI = 300
GREYS = ["0.45", "0.85", "0.65", "0.25", "0.95", "0.55"]
STYLE = {
    "font.family": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "svg.fonttype": "none",
}


def log_ticks(low: float, high: float) -> list[float]:
    """v0.14: a few plain values on a logarithmic axis (0,5, 0,7, 1, 1,5...), not the
    powers of ten that matplotlib writes when the range is under a decade."""
    tenths = tuple(m / 10 for m in range(10, 100))
    halves = tuple(m / 2 for m in range(2, 20))
    # The finest steps that give at most seven values.
    for steps in (tenths, halves, (1, 1.5, 2, 3, 5, 7), (1, 2, 5), (1,)):
        ticks = [m * 10.0**k for k in range(-4, 5) for m in steps]
        ticks = [round(v, 6) for v in ticks if low <= v * 1.000001 and v <= high * 1.000001]
        if len(ticks) <= 7:
            break
    return ticks or [low, high]


def _tick(language: str, plain: bool = False):
    """The numbers of an axis; plain (a logarithmic axis): as many decimals as they have."""

    def show(value, _position):
        text = f"{value:g}" if plain or float(value).is_integer() else f"{value:.1f}"
        text = text.replace("-", MINUS)
        return text.replace(".", ",") if language == "fr" else text

    return FuncFormatter(show)


def _errors(series, index=None):
    values = np.array(series.values)
    if not series.low:
        return None
    return [values - np.array(series.low), np.array(series.high) - values]


def _bars(ax, figure: ApaFigure) -> None:
    series = figure.series[0]
    ax.bar(
        figure.categories,
        series.values,
        yerr=_errors(series),
        color="0.7",
        edgecolor="black",
        linewidth=0.8,
        capsize=6,
        width=0.55,
    )


def _grouped(ax, figure: ApaFigure) -> None:
    x = np.arange(len(figure.categories))
    width = 0.8 / len(figure.series)
    for i, series in enumerate(figure.series):
        offset = (i - (len(figure.series) - 1) / 2) * width
        ax.bar(
            x + offset,
            series.values,
            width,
            label=series.name,
            color=GREYS[i % len(GREYS)],
            edgecolor="black",
            linewidth=0.8,
        )
    ax.set_xticks(x, figure.categories)
    ax.legend(
        title=figure.legend_title or None,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=min(len(figure.series), 4),
    )


def _scatter(ax, figure: ApaFigure) -> None:
    x = np.array([p[0] for p in figure.points])
    y = np.array([p[1] for p in figure.points])
    ax.scatter(x, y, s=14, color="0.45", alpha=0.6, edgecolors="none")
    if figure.line is not None:
        intercept, slope = figure.line
        xs = np.array([x.min(), x.max()])
        ax.plot(xs, intercept + slope * xs, color="black", linewidth=1.5)


def _coefficients(ax, figure: ApaFigure) -> None:
    series = figure.series[0]
    y = np.arange(len(figure.categories))[::-1]
    ax.errorbar(
        series.values, y, xerr=_errors(series), fmt="o", color="black", capsize=5, markersize=6
    )
    if figure.reference is not None:
        ax.axvline(figure.reference, color="0.5", linestyle="--", linewidth=1)
    if figure.log_scale:
        ax.set_xscale("log")
        ends = [*series.values, *(series.low or ()), *(series.high or ())]
        if figure.reference is not None:
            ends.append(figure.reference)
        ax.xaxis.set_major_locator(FixedLocator(log_ticks(min(ends), max(ends))))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks(y, figure.categories)
    ax.set_ylim(-0.6, len(figure.categories) - 0.4)


def _line(ax, figure: ApaFigure) -> None:
    """v0.14: the means of the measures of the same people, in their order, with their
    intervals; or several series (a moderation's simple slopes), told apart by their marker
    and their dashes, with a legend."""
    x = np.arange(len(figure.categories))
    styles = [("o", "-", "black"), ("s", "--", "0.35"), ("^", ":", "0.55")]
    for i, series in enumerate(figure.series):
        marker, dashes, color = styles[i % len(styles)]
        ax.errorbar(x, series.values, yerr=_errors(series), color=color, marker=marker,
                    linestyle=dashes, linewidth=1, capsize=6, label=series.name)  # fmt: skip
    ax.set_xticks(x, figure.categories)
    ax.set_xlim(-0.5, len(x) - 0.5)
    if len(figure.series) > 1:
        ax.legend(title=figure.legend_title or None, frameon=False)


DRAW = {"bars": _bars, "grouped_bars": _grouped, "scatter": _scatter,
        "coefficients": _coefficients, "line": _line}  # fmt: skip


# --- The flow of participants (v0.12, D-098): boxes and arrows, in centimetres. ---

LINE_CM = 0.5  # the height of a line of text
BOX_PAD_CM = 0.3
LEFT_CENTRE, LEFT_WIDTH = 3.4, 6.6
RIGHT_FROM, RIGHT_WIDTH = 7.6, 8.3
WRAP = 38  # characters of a line of the exclusions box, its count included
NBSP = chr(0xA0)  # keeps "(n = 14)" on one line
FLOW_STYLE = {
    **STYLE,
    "mathtext.fontset": "custom",
    "mathtext.rm": "Arial",
    "mathtext.it": "Arial:italic",
}


def _count(symbol: str, value: int) -> str:
    """ "(N = 400)", the symbol in italics."""
    return f"($\\mathit{{{symbol}}}$ = {value})"


def _escaped(text: str) -> str:
    return text.replace("$", "\\$")


def _box(ax, x: float, y: float, width: float, height: float) -> None:
    from matplotlib.patches import Rectangle

    ax.add_patch(Rectangle((x, y), width, height, fill=False, edgecolor="black", linewidth=0.8))


def _arrow(ax, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "-|>", "color": "black", "linewidth": 0.8, "shrinkA": 0,
                    "shrinkB": 0},
    )  # fmt: skip


def _flow_lines(figure: ApaFigure) -> list[tuple[str, bool]]:
    """The lines of the exclusions box: its heading, then each reason (wrapped)."""
    import textwrap

    from ddict.i18n import _

    total = sum(step.excluded for step in figure.flow)
    lines = [(f"{_escaped(_('Exclues'))} {_count('n', total)}", False)]
    for step in figure.flow:
        count = f"(n{NBSP}={NBSP}{step.excluded})"  # counted as it shows, never cut
        wrapped = textwrap.wrap(f"{_escaped(step.reason)} {count}", WRAP)
        wrapped[-1] = wrapped[-1].replace(count, _count("n", step.excluded))
        lines += [(line, True) for line in wrapped]
    return lines


def _flow(figure: ApaFigure, kind: str) -> bytes:
    lines = _flow_lines(figure)
    right_height = len(lines) * LINE_CM + 2 * BOX_PAD_CM
    small = LINE_CM + 2 * BOX_PAD_CM
    height = max(right_height + 2 * small + 1.0, 2 * small + 2.0)
    analysed = figure.flow[-1].remaining if figure.flow else figure.flow_start
    with plt.rc_context(FLOW_STYLE):
        fig = plt.figure(figsize=(WIDTH_CM / 2.54, height / 2.54))
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(-0.1, WIDTH_CM + 0.1)  # a margin: the frames do not touch the edge
        ax.set_ylim(-0.1, height + 0.1)
        ax.axis("off")
        left = LEFT_CENTRE - LEFT_WIDTH / 2
        for y, text in (
            (height - small, f"{_escaped(figure.x_label)} {_count('N', figure.flow_start)}"),
            (0, f"{_escaped(figure.y_label)} {_count('N', analysed)}"),
        ):
            _box(ax, left, y, LEFT_WIDTH, small)
            ax.text(LEFT_CENTRE, y + small / 2, text, ha="center", va="center")
        middle = height / 2
        bottom = middle - right_height / 2
        _box(ax, RIGHT_FROM, bottom, RIGHT_WIDTH, right_height)
        for i, (text, indented) in enumerate(lines):
            y = bottom + right_height - BOX_PAD_CM - (i + 0.5) * LINE_CM
            x = RIGHT_FROM + BOX_PAD_CM + (0.4 if indented else 0)
            ax.text(x, y, text, ha="left", va="center")
        _arrow(ax, (LEFT_CENTRE, height - small), (LEFT_CENTRE, small))
        _arrow(ax, (LEFT_CENTRE, middle), (RIGHT_FROM, middle))
        out = io.BytesIO()
        metadata = {"Software": None} if kind == "png" else None
        fig.savefig(out, format=kind, dpi=DPI, metadata=metadata)
        plt.close(fig)
    return out.getvalue()


def image(figure: ApaFigure, language: str, kind: str = "png") -> bytes:
    """The figure drawn, as PNG (or SVG) bytes."""
    if figure.kind == "flow":
        return _flow(figure, kind)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(WIDTH_CM / 2.54, HEIGHT_CM / 2.54))
        DRAW[figure.kind](ax, figure)
        ax.set_xlabel(figure.x_label)
        ax.set_ylabel(figure.y_label)
        if figure.y_min is not None or figure.y_max is not None:
            ax.set_ylim(bottom=figure.y_min, top=figure.y_max)
        if figure.kind != "coefficients":
            ax.yaxis.set_major_formatter(_tick(language))
        if figure.kind in ("scatter", "coefficients"):
            ax.xaxis.set_major_formatter(_tick(language, plain=figure.log_scale))
        fig.tight_layout()
        out = io.BytesIO()
        metadata = {"Software": None} if kind == "png" else None  # the same bytes every time
        fig.savefig(out, format=kind, dpi=DPI, metadata=metadata)
        plt.close(fig)
    return out.getvalue()
