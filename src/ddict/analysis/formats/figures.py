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
from matplotlib.ticker import FuncFormatter

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


def _tick(language: str):
    def show(value, _position):
        text = f"{value:g}" if float(value).is_integer() else f"{value:.1f}"
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
    ax.set_yticks(y, figure.categories)
    ax.set_ylim(-0.6, len(figure.categories) - 0.4)


DRAW = {"bars": _bars, "grouped_bars": _grouped, "scatter": _scatter, "coefficients": _coefficients}


def image(figure: ApaFigure, language: str, kind: str = "png") -> bytes:
    """The figure drawn, as PNG (or SVG) bytes."""
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
            ax.xaxis.set_major_formatter(_tick(language))
        fig.tight_layout()
        out = io.BytesIO()
        metadata = {"Software": None} if kind == "png" else None  # the same bytes every time
        fig.savefig(out, format=kind, dpi=DPI, metadata=metadata)
        plt.close(fig)
    return out.getvalue()
