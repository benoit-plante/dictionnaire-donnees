"""t test, ANOVA and linear regression (v0.9, step 5), computed in the tool with SciPy and
statsmodels, effect sizes by the formulas of docs/catalogue-analyses.md (D-077)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import optimize, stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor

from ddict.analysis import conditions
from ddict.analysis.book import Codebook
from ddict.analysis.results import AnalysisResult, Table, bounded, interval, number, p_part
from ddict.i18n import _, semicolon

SMALL = 5
SHAPIRO_FEW = 30  # below this many, a non-normal sample is worth a warning
VIF_HIGH = 5
ALTERNATIVES = {"two_sided": "two-sided", "greater": "greater", "less": "less"}


def _codes(book: Codebook, name: str, observed) -> list:
    """The codes of a grouping variable, in the order of its labels, then the others."""
    present = set(observed)
    order = [c for c in book.value_labels(name) if c in present]
    return order + sorted(c for c in present if c not in order)


def _shapiro(values: np.ndarray) -> float | None:
    return float(stats.shapiro(values).pvalue) if 3 <= len(values) <= 5000 else None


def cohens_d(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """d with the pooled standard deviation, and its 95 % interval by the noncentral t."""
    n1, n2 = len(a), len(b)
    pooled = math.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    d = (a.mean() - b.mean()) / pooled
    k = math.sqrt(1 / n1 + 1 / n2)
    t, df = d / k, n1 + n2 - 2

    # Each bound on its own side of t, with the tail that stays small: a cdf close to 1 loses
    # its precision (SciPy then gives NaN).
    low = optimize.brentq(lambda nc: stats.nct.sf(t, df, nc) - 0.025, t - 8, t)
    high = optimize.brentq(lambda nc: stats.nct.cdf(t, df, nc) - 0.025, t, t + 8)
    return float(d), float(low * k), float(high * k)


# --- t test. ---


def t_test(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    outcome, group = chosen["outcome"][0], chosen["group"][0]
    data = prepared.table[[outcome, group]].dropna()
    codes = sorted(set(data[group]))  # in the order of their codes, as in the R script
    if options.get("levels"):
        wanted = [float(c) for c in str(options["levels"]).split(",")]
        codes = [c for c in wanted if c in set(data[group])]
    first, second = codes[:2]
    a = data.loc[data[group] == first, outcome].to_numpy(float)
    b = data.loc[data[group] == second, outcome].to_numpy(float)
    used = len(a) + len(b)
    names = [book.category(group, first), book.category(group, second)]
    alternative = ALTERNATIVES[options.get("alternative", "two_sided")]
    warnings: list[str] = []
    stats_found: dict[str, float] = {
        "n1": len(a),
        "n2": len(b),
        "m1": float(a.mean()),
        "m2": float(b.mean()),
        "sd1": float(a.std(ddof=1)),
        "sd2": float(b.std(ddof=1)),
    }
    levene = stats.levene(a, b, center="median")
    shapiro = [_shapiro(a), _shapiro(b)]
    stats_found |= {"levene_F": float(levene.statistic), "levene_p": float(levene.pvalue)}
    for label, values, p in zip(names, (a, b), shapiro, strict=True):
        if p is not None and p < 0.05 and len(values) < SHAPIRO_FEW:
            warnings.append(
                _(
                    "Distribution peu normale pour {group} (Shapiro-Wilk {p}) avec moins de "
                    "{n} personnes."
                ).format(group=label, p=p_part(p), n=SHAPIRO_FEW)
            )
    rows = [
        [names[0], str(len(a)), f"{number(a.mean())} ({number(a.std(ddof=1))})"],
        [names[1], str(len(b)), f"{number(b.mean())} ({number(b.std(ddof=1))})"],
    ]
    tables = [Table(book.label(outcome), [book.label(group), "n", _("M (ÉT)")], rows)]
    label = book.label(outcome)
    if options["method"] == "mann_whitney":
        test = stats.mannwhitneyu(a, b, alternative=alternative, method="asymptotic")
        rb = 2 * test.statistic / (len(a) * len(b)) - 1
        stats_found |= {"U": float(test.statistic), "p": float(test.pvalue), "rb": float(rb),
                        "mdn1": float(np.median(a)), "mdn2": float(np.median(b))}  # fmt: skip
        sentence = _(
            "{outcome} : médiane de {m1} pour {g1} et de {m2} pour {g2}, U = {u}, {p}, "
            "r = {r} (n = {n})."
        ).format(
            outcome=label,
            m1=number(float(np.median(a))),
            g1=names[0],
            m2=number(float(np.median(b))),
            g2=names[1],
            u=number(test.statistic, 1),
            p=p_part(test.pvalue),
            r=bounded(rb),
            n=used,
        )
        return AnalysisResult(
            "t_test",
            chosen,
            options,
            used,
            len(prepared.table) - used,
            tables,
            stats_found,
            sentence,
            warnings,
        )
    student = options["method"] == "student"
    if student and levene.pvalue < 0.05:
        warnings.append(
            _("Variances inégales (Levene {p}) : le test de Welch convient mieux.").format(
                p=p_part(levene.pvalue)
            )
        )
    test = stats.ttest_ind(a, b, equal_var=student, alternative=alternative)
    diff = a.mean() - b.mean()
    if student:
        df = len(a) + len(b) - 2
        pooled = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / df
        se = math.sqrt(pooled * (1 / len(a) + 1 / len(b)))
    else:
        df = float(test.df)
        se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    half = stats.t.ppf(0.975, df) * se
    d, d_low, d_high = cohens_d(a, b)
    stats_found |= {
        "t": float(test.statistic),
        "df": float(df),
        "p": float(test.pvalue),
        "diff": float(diff),
        "diff_low": float(diff - half),
        "diff_high": float(diff + half),
        "d": d,
        "d_low": d_low,
        "d_high": d_high,
    }
    df_text = number(df) if not student else str(int(df))
    sentence = _(
        "{outcome} : M = {m1} (ÉT = {s1}) pour {g1} et M = {m2} (ÉT = {s2}) pour {g2}, "
        "t({df}) = {t}, {p}, d = {d}, {ci}."
    ).format(
        outcome=label,
        m1=number(a.mean()),
        s1=number(a.std(ddof=1)),
        g1=names[0],
        m2=number(b.mean()),
        s2=number(b.std(ddof=1)),
        g2=names[1],
        df=df_text,
        t=number(test.statistic),
        p=p_part(test.pvalue),
        d=number(d),
        ci=interval(d_low, d_high),
    )
    return AnalysisResult(
        "t_test",
        chosen,
        options,
        used,
        len(prepared.table) - used,
        tables,
        stats_found,
        sentence,
        warnings,
    )


# --- ANOVA. ---


def anova(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    outcome, group = chosen["outcome"][0], chosen["group"][0]
    data = prepared.table[[outcome, group]].dropna()
    codes = _codes(book, group, data[group])
    samples = [data.loc[data[group] == c, outcome].to_numpy(float) for c in codes]
    names = [book.category(group, c) for c in codes]
    n = len(data)
    label = book.label(outcome)
    rows = [
        [nm, str(len(s)), f"{number(s.mean())} ({number(s.std(ddof=1))})"]
        for nm, s in zip(names, samples, strict=True)
    ]
    tables = [Table(label, [book.label(group), "n", _("M (ÉT)")], rows)]
    levene = stats.levene(*samples, center="median")
    found: dict[str, float] = {
        "n": n,
        "levene_F": float(levene.statistic),
        "levene_p": float(levene.pvalue),
    }
    warnings: list[str] = []
    if options["method"] == "kruskal_wallis":
        test = stats.kruskal(*samples)
        epsilon = test.statistic / (n - 1)
        found |= {
            "H": float(test.statistic),
            "df": len(samples) - 1,
            "p": float(test.pvalue),
            "epsilon2": float(epsilon),
        }
        sentence = _("{outcome} selon {group} : H({df}) = {h}, {p}, ε² = {e} (n = {n}).").format(
            outcome=label,
            group=book.label(group),
            df=len(samples) - 1,
            h=number(test.statistic),
            p=p_part(test.pvalue),
            e=bounded(epsilon),
            n=n,
        )
        return AnalysisResult(
            "anova", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
        )
    if levene.pvalue < 0.05:
        warnings.append(
            _("Variances inégales entre les groupes (Levene {p}).").format(p=p_part(levene.pvalue))
        )
    values = data[outcome].to_numpy(float)
    grand = values.mean()
    ssb = sum(len(s) * (s.mean() - grand) ** 2 for s in samples)
    sst = float(((values - grand) ** 2).sum())
    sse = sst - ssb
    dfb, dfe = len(samples) - 1, n - len(samples)
    mse = sse / dfe
    f_value = (ssb / dfb) / mse
    p = float(stats.f.sf(f_value, dfb, dfe))
    eta2 = ssb / sst
    omega2 = (ssb - dfb * mse) / (sst + mse)
    found |= {
        "F": float(f_value),
        "df1": dfb,
        "df2": dfe,
        "p": p,
        "eta2": float(eta2),
        "omega2": float(omega2),
    }
    if options.get("post_hoc") == "tukey":
        tukey = pairwise_tukeyhsd(values, data[group].to_numpy(float))
        groups = tukey.groupsunique
        pairs = [
            (groups[i], groups[j]) for i in range(len(groups)) for j in range(i + 1, len(groups))
        ]
        post = []
        for (g1, g2), diff, low, high, padj in zip(
            pairs,
            tukey.meandiffs,
            tukey.confint[:, 0],
            tukey.confint[:, 1],
            tukey.pvalues,
            strict=True,
        ):
            post.append(
                [
                    f"{book.category(group, g2)} − {book.category(group, g1)}",
                    number(diff),
                    interval(low, high),
                    p_part(padj),
                ]
            )
            found[f"tukey_{int(g2)}_{int(g1)}"] = float(diff)
            found[f"tukey_p_{int(g2)}_{int(g1)}"] = float(padj)
            found[f"tukey_low_{int(g2)}_{int(g1)}"] = float(low)
            found[f"tukey_high_{int(g2)}_{int(g1)}"] = float(high)
        tables.append(
            Table(
                _("Comparaisons deux à deux (Tukey)"),
                [_("Différence"), _("Écart"), _("IC 95 %"), "p"],
                post,
            )
        )
    means = semicolon().join(
        f"{nm} {number(s.mean())} (n = {len(s)})" for nm, s in zip(names, samples, strict=True)
    )
    sentence = _(
        "{outcome} selon {group} : F({df1}, {df2}) = {f}, {p}, η² = {eta}, ω² = {omega} ; "
        "moyennes : {means}."
    ).format(
        outcome=label,
        group=book.label(group),
        df1=dfb,
        df2=dfe,
        f=number(f_value),
        p=p_part(p),
        eta=bounded(eta2),
        omega=bounded(omega2),
        means=means,
    )
    return AnalysisResult(
        "anova", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
    )


# --- Linear regression. ---


def design(book: Codebook, data: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    """The predictors as columns: a nominal one as indicators, its first code the reference."""
    columns = {}
    for name in predictors:
        if book.levels.get(name) == "nominal":
            codes = _codes(book, name, data[name])
            for code in sorted(codes)[1:]:
                columns[f"{name}[{book.category(name, code)}]"] = (data[name] == code).astype(float)
        else:
            columns[name] = data[name].astype(float)
    return pd.DataFrame(columns, index=data.index)


def regression(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    outcome = chosen["outcome"][0]
    predictors = chosen["predictors"]
    data = prepared.table[[outcome, *predictors]].dropna()
    X = design(book, data, predictors)
    y = data[outcome].astype(float)
    exog = sm.add_constant(X, has_constant="add").to_numpy()
    if np.linalg.matrix_rank(exog) < exog.shape[1]:
        raise conditions.AnalysisRefused(
            conditions.Check(
                refusals=[
                    _(
                        "Des prédicteurs sont redondants (l'un se déduit exactement des autres) : "
                        "retirez-en un."
                    )
                ]
            )
        )
    fit = sm.OLS(y, sm.add_constant(X, has_constant="add")).fit()
    standard = sm.OLS(
        (y - y.mean()) / y.std(ddof=1),
        sm.add_constant((X - X.mean()) / X.std(ddof=1), has_constant="add"),
    ).fit()
    vif = [float(variance_inflation_factor(exog, i)) for i in range(1, exog.shape[1])]
    ci = fit.conf_int().to_numpy()
    beta_ci = standard.conf_int().to_numpy()
    n = int(fit.nobs)
    found: dict[str, float] = {
        "n": n,
        "r2": float(fit.rsquared),
        "r2adj": float(fit.rsquared_adj),
        "F": float(fit.fvalue),
        "df1": float(fit.df_model),
        "df2": float(fit.df_resid),
        "Fp": float(fit.f_pvalue),
    }
    rows = []
    labels = [_("Constante"), *[book.label(c) if c in book.entries else c for c in X.columns]]
    for i, label in enumerate(labels):
        found |= {
            f"coef_{i}": float(fit.params.iloc[i]),
            f"se_{i}": float(fit.bse.iloc[i]),
            f"p_{i}": float(fit.pvalues.iloc[i]),
            f"low_{i}": float(ci[i, 0]),
            f"high_{i}": float(ci[i, 1]),
            f"t_{i}": float(fit.tvalues.iloc[i]),
        }
        beta = ""
        if i:
            found[f"beta_{i}"] = float(standard.params.iloc[i])
            found[f"beta_low_{i}"] = float(beta_ci[i, 0])
            found[f"beta_high_{i}"] = float(beta_ci[i, 1])
            found[f"vif_{i}"] = vif[i - 1]
            beta = number(standard.params.iloc[i])
        rows.append(
            [
                label,
                number(fit.params.iloc[i]),
                number(fit.bse.iloc[i]),
                interval(ci[i, 0], ci[i, 1]),
                beta,
                number(fit.tvalues.iloc[i]),
                p_part(fit.pvalues.iloc[i]),
            ]
        )
    tables = [
        Table(
            book.label(outcome), [_("Prédicteur"), "b", _("ET"), _("IC 95 %"), "β", "t", "p"], rows
        )
    ]
    warnings = []
    high = [labels[i + 1] for i, v in enumerate(vif) if v > VIF_HIGH]
    if high:
        warnings.append(
            _("Prédicteurs très liés entre eux (VIF > {v}) : {names}.").format(
                v=VIF_HIGH, names=", ".join(high)
            )
        )
    shapiro = _shapiro(fit.resid.to_numpy())
    if shapiro is not None:
        found["shapiro_p"] = shapiro
        if shapiro < 0.05 and n < SHAPIRO_FEW:
            warnings.append(
                _("Résidus peu normaux (Shapiro-Wilk {p}) avec moins de {n} observations.").format(
                    p=p_part(shapiro), n=SHAPIRO_FEW
                )
            )
    sentence = _(
        "Le modèle expliquait {pct} % de la variance de {outcome}, F({df1}, {df2}) = {f}, {p}, "
        "R² ajusté = {adj} (n = {n})."
    ).format(
        pct=number(100 * fit.rsquared, 1),
        outcome=book.label(outcome),
        df1=int(fit.df_model),
        df2=int(fit.df_resid),
        f=number(fit.fvalue),
        p=p_part(fit.f_pvalue),
        adj=bounded(fit.rsquared_adj),
        n=n,
    )
    return AnalysisResult(
        "regression", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
    )
