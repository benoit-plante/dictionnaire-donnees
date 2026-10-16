"""The R script equivalent to an analysis (v0.9, D-071, D-077): base R only, and haven to
read the database. It runs the command file and the preparation script first, then the
analysis, with the same formulas as the tool; it prints the results and keeps them in a list
`resultats`. The tool never runs it: it is for the team, to redo the analysis elsewhere.
"""

from __future__ import annotations

from datetime import date

from ddict import __version__
from ddict.analysis import conditions
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


def _levels_line(options) -> str:
    if options.get("levels"):
        codes = ", ".join(
            str(float(c)).removesuffix(".0") for c in str(options["levels"]).split(",")
        )
        return f"codes <- c({codes})"
    return "codes <- sort(unique(g[ok]))"


R_ALTERNATIVES = {"two_sided": "two.sided", "greater": "greater", "less": "less"}


def _t_test(chosen, options, _levels) -> list[str]:
    outcome, group = chosen["outcome"][0], chosen["group"][0]
    alternative = R_ALTERNATIVES[options.get("alternative", "two_sided")]
    lines = [
        f"y <- {_column(outcome)}",
        f"g <- {_column(group)}",
        "ok <- complete.cases(y, g)",
        _levels_line(options),
        "a <- y[ok & g == codes[1]]",
        "b <- y[ok & g == codes[2]]",
        "n1 <- length(a); n2 <- length(b)",
        "resultats <- list(n1 = n1, n2 = n2, m1 = mean(a), m2 = mean(b), sd1 = sd(a), sd2 = sd(b))",
        "# Levene (centré sur la médiane) : ANOVA des écarts absolus à la médiane du groupe",
        "yy <- c(a, b); gg <- factor(rep(1:2, c(n1, n2)))",
        "dev <- abs(yy - ave(yy, gg, FUN = median))",
        "lev <- summary(aov(dev ~ gg))[[1]]",
        'resultats$levene_F <- lev[1, "F value"]; resultats$levene_p <- lev[1, "Pr(>F)"]',
    ]
    if options["method"] == "mann_whitney":
        return [
            *lines,
            "test <- wilcox.test(a, b, exact = FALSE, correct = TRUE,",
            f'                    alternative = "{alternative}")',
            "print(test)",
            "resultats$U <- unname(test$statistic); resultats$p <- test$p.value",
            "resultats$rb <- 2 * resultats$U / (n1 * n2) - 1",
            "print(resultats)",
        ]
    equal = "TRUE" if options["method"] == "student" else "FALSE"
    return [
        *lines,
        f'test <- t.test(a, b, var.equal = {equal}, alternative = "{alternative}")',
        "print(test)",
        "resultats$t <- unname(test$statistic); resultats$df <- unname(test$parameter)",
        "resultats$p <- test$p.value",
        "resultats$diff <- mean(a) - mean(b)",
        "resultats$diff_low <- test$conf.int[1]; resultats$diff_high <- test$conf.int[2]",
        "# d de Cohen (écart type combiné) et son intervalle par la loi t non centrale",
        "sp <- sqrt(((n1 - 1) * var(a) + (n2 - 1) * var(b)) / (n1 + n2 - 2))",
        "d <- (mean(a) - mean(b)) / sp; k <- sqrt(1 / n1 + 1 / n2)",
        "tt <- d / k; ddl <- n1 + n2 - 2",
        "bas <- uniroot(function(nc) pt(tt, ddl, nc, lower.tail = FALSE) - 0.025,",
        "               c(tt - 8, tt), tol = 1e-10)$root",
        "haut <- uniroot(function(nc) pt(tt, ddl, nc) - 0.025, c(tt, tt + 8),",
        "                tol = 1e-10)$root",
        "resultats$d <- d; resultats$d_low <- bas * k; resultats$d_high <- haut * k",
        "print(resultats)",
    ]


def _anova(chosen, options, _levels) -> list[str]:
    outcome, group = chosen["outcome"][0], chosen["group"][0]
    lines = [
        f"y <- {_column(outcome)}",
        f"g <- {_column(group)}",
        "ok <- complete.cases(y, g)",
        "y <- y[ok]; g <- factor(g[ok])",
        "dev <- abs(y - ave(y, g, FUN = median))",
        "lev <- summary(aov(dev ~ g))[[1]]",
        'resultats <- list(n = length(y), levene_F = lev[1, "F value"],',
        '                  levene_p = lev[1, "Pr(>F)"])',
    ]
    if options["method"] == "kruskal_wallis":
        return [
            *lines,
            "test <- kruskal.test(y ~ g)",
            "print(test)",
            "resultats$H <- unname(test$statistic); resultats$df <- unname(test$parameter)",
            "resultats$p <- test$p.value; resultats$epsilon2 <- resultats$H / (length(y) - 1)",
            "print(resultats)",
        ]
    lines += [
        "fit <- aov(y ~ g)",
        "s <- summary(fit)[[1]]",
        "print(s)",
        'ssb <- s[1, "Sum Sq"]; sse <- s[2, "Sum Sq"]; dfb <- s[1, "Df"]; dfe <- s[2, "Df"]',
        "mse <- sse / dfe",
        'resultats$F <- s[1, "F value"]; resultats$df1 <- dfb; resultats$df2 <- dfe',
        'resultats$p <- s[1, "Pr(>F)"]; resultats$eta2 <- ssb / (ssb + sse)',
        "resultats$omega2 <- (ssb - dfb * mse) / (ssb + sse + mse)",
    ]
    if options.get("post_hoc") == "tukey":
        lines += [
            "tk <- TukeyHSD(fit)$g",
            "print(tk)",
            "for (paire in rownames(tk)) {",
            '  cle <- gsub("-", "_", paire)',
            '  resultats[[paste0("tukey_", cle)]] <- tk[paire, "diff"]',
            '  resultats[[paste0("tukey_p_", cle)]] <- tk[paire, "p adj"]',
            "}",
        ]
    return [*lines, "print(resultats)"]


def _regression(chosen, options, levels) -> list[str]:
    outcome = chosen["outcome"][0]
    columns = [f"y = {_column(outcome)}"]
    for i, name in enumerate(chosen["predictors"], start=1):
        value = _column(name)
        if levels.get(name) == "nominal":
            value = f"factor({value})"
        columns.append(f"x{i} = {value}")
    return [
        "d <- data.frame(" + ", ".join(columns) + ")",
        "d <- d[complete.cases(d), ]",
        "fit <- lm(y ~ ., data = d)",
        "print(summary(fit))",
        "co <- summary(fit)$coefficients; ci <- confint(fit); f <- summary(fit)$fstatistic",
        "mm <- model.matrix(fit)[, -1, drop = FALSE]",
        "beta <- coef(lm(scale(d$y) ~ scale(mm)))[-1]",
        "vif <- sapply(seq_len(ncol(mm)), function(j) {",
        "  if (ncol(mm) == 1) return(1)",
        "  1 / (1 - summary(lm(mm[, j] ~ mm[, -j]))$r.squared)",
        "})",
        "resultats <- list(n = nrow(d), r2 = summary(fit)$r.squared,",
        "                  r2adj = summary(fit)$adj.r.squared, F = unname(f[1]),",
        "                  df1 = unname(f[2]), df2 = unname(f[3]),",
        "                  Fp = pf(f[1], f[2], f[3], lower.tail = FALSE)[[1]])",
        "for (i in seq_len(nrow(co))) {",
        '  resultats[[paste0("coef_", i - 1)]] <- co[i, 1]',
        '  resultats[[paste0("se_", i - 1)]] <- co[i, 2]',
        '  resultats[[paste0("p_", i - 1)]] <- co[i, 4]',
        '  resultats[[paste0("low_", i - 1)]] <- ci[i, 1]',
        '  resultats[[paste0("high_", i - 1)]] <- ci[i, 2]',
        "}",
        "for (j in seq_along(beta)) {",
        '  resultats[[paste0("beta_", j)]] <- unname(beta[j])',
        '  resultats[[paste0("vif_", j)]] <- vif[j]',
        "}",
        "print(resultats)",
    ]


BODIES = {
    "table1": lambda c, o, _l: _table1(c, o),
    "t_test": _t_test,
    "anova": _anova,
    "chi_square": lambda c, o, _l: _chi_square(c, o),
    "correlation": lambda c, o, _l: _correlation(c, o),
    "regression": _regression,
}


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
    lines += BODIES[key](chosen, options, conditions.levels(project))
    return "\n".join(lines) + "\n"
