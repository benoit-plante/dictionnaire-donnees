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
    # Categories written as text (v0.13): an empty text is missing, as in the tool.
    "ddict_txt <- function(x) {",
    '  if (inherits(x, "haven_labelled")) x <- haven::zap_missing(x)',
    '  x <- as.character(if (inherits(x, "vctrs_vctr")) vctrs::vec_data(x) else x)',
    "  x <- enc2utf8(x)",
    '  x[trimws(x) == ""] <- NA',
    "  x",
    "}",
    # The codes in the tool's order: "radix" sorts text by code points, as Python does.
    'ddict_tri <- function(x) sort(unique(x[!is.na(x)]), method = "radix")',
    "ddict_fac <- function(x) factor(x, levels = ddict_tri(x))",
    # A subgroup (v0.14): a missing value never meets its condition.
    "ddict_vrai <- function(x) !is.na(x) & x",
]


def _text(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _column(name: str, texts: set[str] = frozenset()) -> str:
    reader = "ddict_txt" if name in texts else "ddict_num"
    return f"{reader}(donnees[[{_text(name)}]])"


def _header(project: Project, stem: str, title: str, today: str) -> list[str]:
    lines = [
        "# "
        + _(
            "{analysis} : script R équivalent, produit par dictionnaire-donnees {version} "
            "le {date}."
        ).format(analysis=title, version=__version__, date=today),
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


# A code inside a statistic's key, as the tool writes it: "1", "2p5" for 2.5, "m9" for -9.
CODE_KEY = [
    "ddict_cle <- function(v) {",
    '  if (is.character(v)) return(paste0("s", gsub("[^0-9A-Za-z]", "_", v, perl = TRUE)))',
    "  s <- if (v == round(v)) format(round(v), scientific = FALSE, trim = TRUE)"
    " else as.character(v)",
    '  gsub("\\\\.", "p", gsub("-", "m", s))',
    "}",
]


def _table1(chosen, options, levels, texts) -> list[str]:
    """Each variable's n, mean and SD (its name, as in v0.9), and, by position (v0.11), the
    aggregates the notebook keeps: for each column (a group's code, then "total"), n and
    mean and SD of a scale variable, or the count of each code."""
    group = (chosen.get("group") or [None])[0]
    lines = ["resultats <- list()", *CODE_KEY]
    if group:
        lines += [
            f"g <- {_column(group, texts)}",
            "garde <- !is.na(g)",
            "colonnes <- c(as.list(ddict_tri(g)), list(NULL))",
        ]
    else:
        lines += ["garde <- rep(TRUE, nrow(donnees))", "colonnes <- list(NULL)"]
    for i, name in enumerate(chosen["variables"], start=1):
        column = _column(name, texts)
        lines += [
            f"x <- {column}",
            f"resultats[[{_text(name + '_n')}]] <- sum(!is.na(x))",
            f"resultats[[{_text(name + '_moyenne')}]] <- mean(x, na.rm = TRUE)",
            f"resultats[[{_text(name + '_et')}]] <- sd(x, na.rm = TRUE)",
            f'print(table(donnees[[{_text(name)}]], useNA = "ifany"))',
            "for (co in colonnes) {",
            # NULL is the column of everyone: a text code may well be "total".
            "  dans <- if (is.null(co)) garde else garde & g == co",
            "  xx <- x[dans & !is.na(x)]",
            '  cc <- if (is.null(co)) "total" else ddict_cle(co)',
            f'  resultats[[paste0("v{i}_n_", cc)]] <- length(xx)',
        ]
        if levels.get(name) == "scale":
            lines += [
                f'  if (length(xx) > 0) resultats[[paste0("v{i}_m_", cc)]] <- mean(xx)',
                f'  if (length(xx) > 1) resultats[[paste0("v{i}_sd_", cc)]] <- sd(xx)',
            ]
        else:
            lines += [
                "  for (k in ddict_tri(xx)) {",
                f'    resultats[[paste0("v{i}_k", ddict_cle(k), "_", cc)]] <- sum(xx == k)',
                "  }",
            ]
        lines.append("}")
    return [*lines, "print(resultats)"]


def _correlation(chosen, options, texts) -> list[str]:
    """Every pair, by position (row j, column i of the APA matrix: `r_2_1`), as v0.11 keeps
    them; and, for two variables, the keys of v0.9 (r, p, n, ci_low, ci_high)."""
    names = chosen["variables"]
    method = options.get("method", "pearson")
    exact = ", exact = FALSE" if method == "spearman" else ""
    lines = [
        "v <- list(" + ", ".join(_column(n, texts) for n in names) + ")",
        "resultats <- list()",
        "for (j in 2:length(v)) for (i in 1:(j - 1)) {",
        "  ok <- complete.cases(v[[i]], v[[j]])",
        f'  test <- cor.test(v[[i]][ok], v[[j]][ok], method = "{method}"{exact})',
        "  print(test)",
        '  cle <- paste0("_", j, "_", i)',
        '  resultats[[paste0("r", cle)]] <- unname(test$estimate)',
        '  resultats[[paste0("p", cle)]] <- test$p.value',
        '  resultats[[paste0("n", cle)]] <- sum(ok)',
    ]
    if method == "pearson":
        lines += [
            '  resultats[[paste0("low", cle)]] <- test$conf.int[1]',
            '  resultats[[paste0("high", cle)]] <- test$conf.int[2]',
        ]
    lines.append("}")
    if len(names) == 2:
        lines.append(
            "resultats$r <- resultats$r_2_1; resultats$p <- resultats$p_2_1; "
            "resultats$n <- resultats$n_2_1"
        )
        if method == "pearson":
            lines.append(
                "resultats$ci_low <- resultats$low_2_1; resultats$ci_high <- resultats$high_2_1"
            )
    return [*lines, "print(resultats)"]


def _chi_square(chosen, options, texts) -> list[str]:
    a, b = chosen["rows"][0], chosen["columns"][0]
    lines = [
        f"x <- {_column(a, texts)}",
        f"y <- {_column(b, texts)}",
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


def _levels_line(options, text: bool) -> str:
    if options.get("levels"):
        parts = [c.strip() for c in str(options["levels"]).split(",")]
        if text:
            codes = ", ".join(_text(c) for c in parts)
        else:
            codes = ", ".join(str(float(c)).removesuffix(".0") for c in parts)
        return f"codes <- c({codes})"
    return "codes <- ddict_tri(g[ok])"


R_ALTERNATIVES = {"two_sided": "two.sided", "greater": "greater", "less": "less"}


def _t_test(chosen, options, _levels, texts) -> list[str]:
    outcome, group = chosen["outcome"][0], chosen["group"][0]
    alternative = R_ALTERNATIVES[options.get("alternative", "two_sided")]
    lines = [
        f"y <- {_column(outcome, texts)}",
        f"g <- {_column(group, texts)}",
        "ok <- complete.cases(y, g)",
        _levels_line(options, group in texts),
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


def _paired(chosen, options, _levels, texts) -> list[str]:
    """v0.14: the paired t test, or Wilcoxon's signed-rank test, with the tool's formulas
    for d_z and the rank-biserial correlation; the interval of the difference two-sided."""
    first, second = chosen["first"][0], chosen["second"][0]
    alternative = R_ALTERNATIVES[options.get("alternative", "two_sided")]
    lines = [
        f"x <- {_column(first, texts)}",
        f"y <- {_column(second, texts)}",
        "ok <- complete.cases(x, y)",
        "a <- x[ok]; b <- y[ok]; dd <- a - b; n <- length(dd)",
        "resultats <- list(n = n, m1 = mean(a), m2 = mean(b), sd1 = sd(a), sd2 = sd(b))",
    ]
    if options.get("method") == "wilcoxon":
        return [
            *lines,
            "test <- wilcox.test(a, b, paired = TRUE, exact = FALSE, correct = TRUE,",
            f'                    alternative = "{alternative}")',
            "print(test)",
            "resultats$V <- unname(test$statistic); resultats$p <- test$p.value",
            "nz <- dd[dd != 0]; rg <- rank(abs(nz))",
            "plus <- sum(rg[nz > 0]); moins <- sum(rg[nz < 0])",
            "resultats$rb <- (plus - moins) / (plus + moins); resultats$zeros <- sum(dd == 0)",
            "resultats$mdn1 <- median(a); resultats$mdn2 <- median(b)",
            "print(resultats)",
        ]
    return [
        *lines,
        f'test <- t.test(a, b, paired = TRUE, alternative = "{alternative}")',
        "print(test)",
        "resultats$t <- unname(test$statistic); resultats$df <- unname(test$parameter)",
        "resultats$p <- test$p.value; resultats$diff <- mean(dd)",
        "demi <- qt(0.975, n - 1) * sd(dd) / sqrt(n)",
        "resultats$diff_low <- mean(dd) - demi; resultats$diff_high <- mean(dd) + demi",
        "# d_z (moyenne des différences / leur écart type) et son intervalle par la loi t",
        "# non centrale",
        "d <- mean(dd) / sd(dd); k <- 1 / sqrt(n); tt <- d / k; ddl <- n - 1",
        "bas <- uniroot(function(nc) pt(tt, ddl, nc, lower.tail = FALSE) - 0.025,",
        "               c(tt - 8, tt), tol = 1e-10)$root",
        "haut <- uniroot(function(nc) pt(tt, ddl, nc) - 0.025, c(tt, tt + 8),",
        "                tol = 1e-10)$root",
        "resultats$d <- d; resultats$d_low <- bas * k; resultats$d_high <- haut * k",
        "print(resultats)",
    ]


def _anova(chosen, options, _levels, texts) -> list[str]:
    outcome, group = chosen["outcome"][0], chosen["group"][0]
    lines = [
        f"y <- {_column(outcome, texts)}",
        f"g <- {_column(group, texts)}",
        "ok <- complete.cases(y, g)",
        "y <- y[ok]; niv <- ddict_tri(g[ok]); g <- factor(g[ok], levels = niv)",
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
            *CODE_KEY,
            "tk <- TukeyHSD(fit)$g",
            "print(tk)",
            # Each pair by its two codes, never by splitting a name: a code may hold "-".
            "for (j in 2:length(niv)) for (i in 1:(j - 1)) {",
            '  paire <- paste(levels(g)[j], levels(g)[i], sep = "-")',
            '  cle <- paste0(ddict_cle(niv[j]), "_", ddict_cle(niv[i]))',
            '  resultats[[paste0("tukey_", cle)]] <- tk[paire, "diff"]',
            '  resultats[[paste0("tukey_p_", cle)]] <- tk[paire, "p adj"]',
            '  resultats[[paste0("tukey_low_", cle)]] <- tk[paire, "lwr"]',
            '  resultats[[paste0("tukey_high_", cle)]] <- tk[paire, "upr"]',
            "}",
        ]
    return [*lines, "print(resultats)"]


def _regression(chosen, options, levels, texts) -> list[str]:
    outcome = chosen["outcome"][0]
    columns = [f"y = {_column(outcome, texts)}"]
    for i, name in enumerate(chosen["predictors"], start=1):
        value = _column(name, texts)
        if levels.get(name) == "nominal":
            value = f"ddict_fac({value})"
        columns.append(f"x{i} = {value}")
    return [
        "d <- data.frame(" + ", ".join(columns) + ")",
        "d <- droplevels(d[complete.cases(d), ])",
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


def _frame(names: list[str], levels, texts, prefix: str) -> list[str]:
    """`name = column` for a data frame, a nominal variable as a factor in the tool's order."""
    found = []
    for i, name in enumerate(names, start=1):
        value = _column(name, texts)
        if levels.get(name) == "nominal":
            value = f"ddict_fac({value})"
        found.append(f"{prefix}{i} = {value}")
    return found


def _partial(chosen, options, levels, texts) -> list[str]:
    """v0.14: the correlation of the residuals on the covariates; t with n - 2 - k degrees
    of freedom, the interval by Fisher's transformation; the simple correlation."""
    first, second = chosen["variables"]
    columns = [f"x = {_column(first, texts)}", f"y = {_column(second, texts)}"]
    columns += _frame(chosen["covariates"], levels, texts, "z")
    return [
        "d <- data.frame(" + ", ".join(columns) + ")",
        "d <- droplevels(d[complete.cases(d), ])",
        "z <- d[, -(1:2), drop = FALSE]",
        "rx <- resid(lm(d$x ~ ., data = z)); ry <- resid(lm(d$y ~ ., data = z))",
        "n <- nrow(d); k <- ncol(model.matrix(~ ., data = z)) - 1",
        "r <- cor(rx, ry); ddl <- n - 2 - k; tt <- r * sqrt(ddl / (1 - r^2))",
        "demi <- qnorm(0.975) / sqrt(n - 3 - k)",
        "simple <- cor.test(d$x, d$y)",
        "resultats <- list(n = n, k = k, r = r, df = ddl, t = tt, p = 2 * pt(-abs(tt), ddl),",
        "                  ci_low = tanh(atanh(r) - demi), ci_high = tanh(atanh(r) + demi),",
        "                  r_simple = unname(simple$estimate), p_simple = simple$p.value)",
        "print(resultats)",
    ]


def _moderation(chosen, options, levels, texts) -> list[str]:
    """v0.14: y on x, w, the covariates and x:w (R's order of the terms); the variables of
    the interaction centred unless the team chose not to; a nominal moderator coded 0 and
    1 (its second code); the simple slopes by their formula."""
    outcome, focal = chosen["outcome"][0], chosen["focal"][0]
    moderator, covariates = chosen["moderator"][0], chosen.get("covariates", [])
    center = options.get("center", "yes") == "yes"
    nominal = levels.get(moderator) == "nominal"
    moderator_value = _column(moderator, texts)
    if nominal:
        moderator_value = f"ddict_fac({moderator_value})"
    columns = [f"y = {_column(outcome, texts)}", f"x = {_column(focal, texts)}",
               f"w = {moderator_value}", *_frame(covariates, levels, texts, "c")]  # fmt: skip
    lines = [
        "d <- data.frame(" + ", ".join(columns) + ")",
        "d <- droplevels(d[complete.cases(d), ])",
    ]
    if nominal:
        lines.append("niv <- levels(d$w); d$w <- as.numeric(d$w == niv[2])")
    if center:
        lines.append("d$x <- d$x - mean(d$x)")
        if not nominal:
            lines.append("d$w <- d$w - mean(d$w)")
    terms = " + ".join(["x", "w", *[f"c{i}" for i in range(1, len(covariates) + 1)]])
    at = "valeurs <- c(0, 1)" if nominal else "valeurs <- mean(d$w) + c(-1, 0, 1) * sd(d$w)"
    return [
        *lines,
        f"m <- lm(y ~ {terms} + x:w, data = d)",
        f"m0 <- lm(y ~ {terms}, data = d)",
        "print(summary(m))",
        "co <- summary(m)$coefficients; ci <- confint(m); V <- vcov(m)",
        "chg <- anova(m0, m); last <- nrow(co)",
        "resultats <- list(n = nrow(d), r2 = summary(m)$r.squared,",
        "                  delta_r2 = summary(m)$r.squared - summary(m0)$r.squared,",
        '                  f_change = chg$F[2], f_change_p = chg$"Pr(>F)"[2],',
        "                  df_resid = m$df.residual, b = co[last, 1], se = co[last, 2],",
        "                  t = co[last, 3], p = co[last, 4], low = ci[last, 1],",
        "                  high = ci[last, 2])",
        "for (i in seq_len(last)) {",
        '  resultats[[paste0("coef_", i - 1)]] <- co[i, 1]',
        '  resultats[[paste0("se_", i - 1)]] <- co[i, 2]',
        '  resultats[[paste0("t_", i - 1)]] <- co[i, 3]',
        '  resultats[[paste0("p_", i - 1)]] <- co[i, 4]',
        '  resultats[[paste0("low_", i - 1)]] <- ci[i, 1]',
        '  resultats[[paste0("high_", i - 1)]] <- ci[i, 2]',
        "}",
        "# Les pentes simples de x : b_x + w b_x:w, ET = racine(V_xx + w² V_ii + 2 w V_xi)",
        at,
        "q <- qt(0.975, m$df.residual)",
        "for (j in seq_along(valeurs)) {",
        "  w <- valeurs[j]",
        '  b <- coef(m)["x"] + w * coef(m)["x:w"]',
        '  se <- sqrt(V["x", "x"] + w^2 * V["x:w", "x:w"] + 2 * w * V["x", "x:w"])',
        '  cle <- paste0("slope_", j)',
        '  resultats[[cle]] <- unname(b); resultats[[paste0(cle, "_at")]] <- w',
        '  resultats[[paste0(cle, "_se")]] <- se',
        '  resultats[[paste0(cle, "_t")]] <- unname(b / se)',
        '  resultats[[paste0(cle, "_p")]] <- 2 * pt(-abs(unname(b / se)), m$df.residual)',
        '  resultats[[paste0(cle, "_low")]] <- unname(b - q * se)',
        '  resultats[[paste0(cle, "_high")]] <- unname(b + q * se)',
        "}",
        "print(resultats)",
    ]


def _logistic(chosen, options, levels, texts) -> list[str]:
    """v0.14: glm(binomial), its convergence tightened to the tool's (the default leaves
    standard errors 10⁻⁶ apart); the odds ratios and their Wald interval; the
    likelihood-ratio test; McFadden's and Nagelkerke's R²."""
    outcome = chosen["outcome"][0]
    position = 2 if options.get("event", "second") == "second" else 1
    columns = [f"y = {_column(outcome, texts)}", *_frame(chosen["predictors"], levels, texts, "x")]
    return [
        "d <- data.frame(" + ", ".join(columns) + ")",
        "d <- droplevels(d[complete.cases(d), ])",
        f"evenement <- ddict_tri(d$y)[{position}]",
        "d$y <- as.numeric(d$y == evenement)",
        "fit <- glm(y ~ ., data = d, family = binomial, control = glm.control(epsilon = 1e-12,",
        "           maxit = 100))",
        "print(summary(fit))",
        "co <- summary(fit)$coefficients; ci <- confint.default(fit); n <- nrow(d)",
        "ll <- as.numeric(logLik(fit))",
        "ll0 <- as.numeric(logLik(glm(y ~ 1, data = d, family = binomial)))",
        "resultats <- list(n = n, events = sum(d$y), chi2 = fit$null.deviance - fit$deviance,",
        "                  df = fit$df.null - fit$df.residual, mcfadden = 1 - ll / ll0,",
        "                  nagelkerke = (1 - exp(2 * (ll0 - ll) / n)) / (1 - exp(2 * ll0 / n)))",
        "resultats$chi2_p <- pchisq(resultats$chi2, resultats$df, lower.tail = FALSE)",
        "for (i in seq_len(nrow(co))) {",
        '  resultats[[paste0("coef_", i - 1)]] <- co[i, 1]',
        '  resultats[[paste0("se_", i - 1)]] <- co[i, 2]',
        '  resultats[[paste0("z_", i - 1)]] <- co[i, 3]',
        '  resultats[[paste0("p_", i - 1)]] <- co[i, 4]',
        '  resultats[[paste0("or_", i - 1)]] <- exp(co[i, 1])',
        '  resultats[[paste0("or_low_", i - 1)]] <- exp(ci[i, 1])',
        '  resultats[[paste0("or_high_", i - 1)]] <- exp(ci[i, 2])',
        "}",
        "print(resultats)",
    ]


def _rm_anova(chosen, options, _levels, texts) -> list[str]:
    """v0.14: anova.mlm with test = "Spherical" (F and the Greenhouse-Geisser p), Mauchly's
    test, epsilon on orthonormal (polynomial) contrasts, partial eta squared from F; the p
    reported corrected when Mauchly's p is below ,05; pairwise paired t tests and Holm."""
    names = chosen["measures"]
    lines = [
        "Y <- cbind(" + ", ".join(_column(n, texts) for n in names) + ")",
        "Y <- Y[complete.cases(Y), , drop = FALSE]; n <- nrow(Y); k <- ncol(Y)",
        "fit <- lm(Y ~ 1)",
        'sph <- anova(fit, X = ~1, test = "Spherical"); print(sph)',
        "mau <- mauchly.test(fit, X = ~1); print(mau)",
        "M <- contr.poly(k); T <- t(M) %*% cov(Y) %*% M",
        "eps <- sum(diag(T))^2 / ((k - 1) * sum(diag(T %*% T)))",
        "f <- sph$F[1]; df1 <- k - 1; df2 <- (k - 1) * (n - 1)",
        "resultats <- list(n = n, F = f, df1 = df1, df2 = df2,",
        '                  p_uncorrected = sph$"Pr(>F)"[1], eta2p = f * df1 / (f * df1 + df2),',
        "                  mauchly_W = unname(mau$statistic), mauchly_p = mau$p.value,",
        "                  gg_eps = eps, gg_df1 = eps * df1, gg_df2 = eps * df2,",
        '                  gg_p = sph$"G-G Pr"[1])',
        "resultats$corrected <- as.numeric(mau$p.value < 0.05)",
        "resultats$p <- if (resultats$corrected == 1) resultats$gg_p else resultats$p_uncorrected",
        "for (i in seq_len(k)) {",
        '  resultats[[paste0("m_", i)]] <- mean(Y[, i])',
        '  resultats[[paste0("sd_", i)]] <- sd(Y[, i])',
        "}",
    ]
    if options.get("post_hoc") == "holm":
        lines += [
            "paires <- combn(k, 2); bruts <- numeric(ncol(paires))",
            "for (c in seq_len(ncol(paires))) {",
            "  i <- paires[1, c]; j <- paires[2, c]",
            "  test <- t.test(Y[, i], Y[, j], paired = TRUE)",
            '  cle <- paste0("ph_", i, "_", j); bruts[c] <- test$p.value',
            '  resultats[[paste0(cle, "_diff")]] <- mean(Y[, i] - Y[, j])',
            '  resultats[[paste0(cle, "_t")]] <- unname(test$statistic)',
            '  resultats[[paste0(cle, "_p")]] <- test$p.value',
            "}",
            'holm <- p.adjust(bruts, method = "holm")',
            "for (c in seq_len(ncol(paires))) {",
            '  resultats[[paste0("ph_", paires[1, c], "_", paires[2, c], "_p_holm")]] <- holm[c]',
            "}",
        ]
    return [*lines, "print(resultats)"]


BODIES = {
    "table1": _table1,
    "t_test": _t_test,
    "paired": _paired,
    "rm_anova": _rm_anova,
    "anova": _anova,
    "chi_square": lambda c, o, _l, t: _chi_square(c, o, t),
    "correlation": lambda c, o, _l, t: _correlation(c, o, t),
    "regression": _regression,
    "logistic": _logistic,
    "partial": _partial,
    "moderation": _moderation,
}


SUBSET_SYMBOLS = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}


def _r_code_value(value, text: bool) -> str:
    if text:
        return _text(str(value))
    number = float(value)
    return str(int(number)) if number.is_integer() else repr(number)


def subset_lines(subset, texts) -> list[str]:
    """v0.14 (D-113): the rows of the subgroup only, first in the analysis."""
    if subset is None:
        return []
    text = subset.name in texts
    column = _column(subset.name, texts)
    if subset.operator == "in":
        values = ", ".join(_r_code_value(v, text) for v in subset.value)
        condition = f"{column} %in% c({values})"
    else:
        symbol = SUBSET_SYMBOLS[subset.operator]
        condition = f"{column} {symbol} {_r_code_value(subset.value, text)}"
    return [
        "# " + _("Sous-groupe : seules ces lignes entrent dans l'analyse."),
        f"donnees <- donnees[ddict_vrai({condition}), , drop = FALSE]",
    ]


@in_language
def r_script(
    project: Project,
    stem: str,
    key: str,
    chosen: dict[str, list[str]],
    options: dict[str, str] | None = None,
    today: str | None = None,
    subgroup=None,
) -> str:
    """The R script of an analysis; `stem` names the files next to the project."""
    options = {k: v[0] for k, v in CATALOGUE[key].options.items()} | (options or {})
    lines = _header(project, stem, TITLES[key], today or date.today().isoformat())
    texts = conditions.texts(project)
    lines += subset_lines(subgroup, texts)
    lines += BODIES[key](chosen, options, conditions.levels(project), texts)
    return "\n".join(lines) + "\n"


@in_language
def r_master(
    project: Project,
    stem: str,
    analyses: list[tuple[str, str, dict[str, list[str]], dict[str, str]]],
    today: str | None = None,
) -> str:
    """The master script of the notebook (v0.11, step 5): the database, the command file
    and the preparation script once, then each analysis `(id, key, chosen, options)` in its
    own space (`local`), so that their working variables never mix, kept as
    `resultats$A2`."""
    levels, texts = conditions.levels(project), conditions.texts(project)
    lines = _header(project, stem, _("Résultats du carnet"), today or date.today().isoformat())
    lines += ["resultats <- list()", ""]
    for entry_id, key, chosen, options, *rest in analyses:
        options = {k: v[0] for k, v in CATALOGUE[key].options.items()} | dict(options)
        body = subset_lines(rest[0] if rest else None, texts)  # the subgroup, v0.14
        body += BODIES[key](chosen, options, levels, texts)
        lines += [f"# {entry_id} — {TITLES[key]}", f"resultats${entry_id} <- local({{"]
        lines += [f"  {line}" for line in body]
        lines += ["  resultats", "})", ""]
    lines.append("invisible(resultats)")
    return "\n".join(lines) + "\n"
