"""The R script equivalent to an analysis (v0.9, D-071, D-077): base R only, and haven to
read the database. It runs the command file and the preparation script first, then the
analysis, with the same formulas as the tool; it prints the results and keeps them in a list
`resultats`. The tool never runs it: it is for the team, to redo the analysis elsewhere.
"""

from __future__ import annotations

from datetime import date

from ddict import __version__
from ddict.analysis.catalogue import CATALOGUE, TITLES
from ddict.export.preparation import needed as preparation_needed
from ddict.export.syntax import _r_reader
from ddict.i18n import _, in_language
from ddict.project import fingerprint
from ddict.project.model import Project

HELPER = [
    "ddict_num <- function(x) {",
    '  if (inherits(x, "haven_labelled")) x <- haven::zap_missing(x)',
    '  as.numeric(if (inherits(x, "vctrs_vctr")) vctrs::vec_data(x) else x)',
    "}",
]


def _text(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _column(name: str) -> str:
    return f"ddict_num(donnees[[{_text(name)}]])"


def _header(project: Project, stem: str, key: str, today: str) -> list[str]:
    lines = [
        "# "
        + _(
            "{analysis} : script R équivalent, produit par dictionnaire-donnees {version} "
            "le {date}."
        ).format(analysis=TITLES[key], version=__version__, date=today),
        "# "
        + _("Empreinte du codebook : {fingerprint}.").format(
            fingerprint=fingerprint.short(project)
        ),
        "# " + _("R de base et haven seulement ; à exécuter dans le dossier du projet."),
        "",
        f"donnees <- {_r_reader(project)}",
        f'source("{stem}-metadonnees.R", encoding = "UTF-8")',
    ]
    if preparation_needed(project):
        lines.append(f'source("{stem}-preparation.R", encoding = "UTF-8")')
    return [*lines, "", *HELPER, ""]


def _table1(chosen, options) -> list[str]:
    lines = ["resultats <- list()"]
    for name in chosen["variables"]:
        column = _column(name)
        lines += [
            f"x <- {column}",
            f"resultats[[{_text(name + '_n')}]] <- sum(!is.na(x))",
            f"resultats[[{_text(name + '_moyenne')}]] <- mean(x, na.rm = TRUE)",
            f"resultats[[{_text(name + '_et')}]] <- sd(x, na.rm = TRUE)",
            f'print(table(donnees[[{_text(name)}]], useNA = "ifany"))',
        ]
    return [*lines, "print(resultats)"]


def _correlation(chosen, options) -> list[str]:
    a, b = chosen["variables"][:2]
    method = options.get("method", "pearson")
    exact = ", exact = FALSE" if method == "spearman" else ""
    lines = [
        f"x <- {_column(a)}",
        f"y <- {_column(b)}",
        "ok <- complete.cases(x, y)",
        f'test <- cor.test(x[ok], y[ok], method = "{method}"{exact})',
        "print(test)",
        "resultats <- list(r = unname(test$estimate), p = test$p.value, n = sum(ok))",
    ]
    if method == "pearson":
        lines.append("resultats$ci_low <- test$conf.int[1]; resultats$ci_high <- test$conf.int[2]")
    return [*lines, "print(resultats)"]


def _chi_square(chosen, options) -> list[str]:
    a, b = chosen["rows"][0], chosen["columns"][0]
    lines = [
        f"x <- {_column(a)}",
        f"y <- {_column(b)}",
        "ok <- complete.cases(x, y)",
        "tableau <- table(x[ok], y[ok])",
        "print(tableau)",
        "test <- chisq.test(tableau, correct = FALSE)",
        "print(test)",
        "v <- sqrt(unname(test$statistic) / (sum(tableau) * (min(dim(tableau)) - 1)))",
        "resultats <- list(chi2 = unname(test$statistic), df = unname(test$parameter), "
        "p = test$p.value, V = v, n = sum(tableau))",
    ]
    if options.get("method") == "fisher":
        lines += [
            "if (all(dim(tableau) == 2)) {",
            "  fisher <- fisher.test(tableau)",
            "  print(fisher)",
            "  resultats$fisher_p <- fisher$p.value",
            "}",
        ]
    return [*lines, "print(resultats)"]


BODIES = {"table1": _table1, "correlation": _correlation, "chi_square": _chi_square}


@in_language
def r_script(
    project: Project,
    stem: str,
    key: str,
    chosen: dict[str, list[str]],
    options: dict[str, str] | None = None,
    today: str | None = None,
) -> str:
    """The R script of an analysis; `stem` names the files next to the project."""
    options = {k: v[0] for k, v in CATALOGUE[key].options.items()} | (options or {})
    lines = _header(project, stem, key, today or date.today().isoformat())
    lines += BODIES[key](chosen, options)
    return "\n".join(lines) + "\n"
