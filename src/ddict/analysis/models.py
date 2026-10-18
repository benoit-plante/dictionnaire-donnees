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
from ddict.analysis.data import chosen_levels, code_key
from ddict.analysis.results import (
    AnalysisResult,
    Table,
    bounded,
    bounded_interval,
    interval,
    number,
    p_part,
)
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
        wanted = chosen_levels(options["levels"], data[group])
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


# --- Paired t test and Wilcoxon signed-rank test (v0.14, D-111). ---


def paired_d(differences: np.ndarray) -> tuple[float, float, float]:
    """d_z, the mean difference over its standard deviation, and its 95 % interval by the
    noncentral t (df = n - 1)."""
    n = len(differences)
    dz = float(differences.mean() / differences.std(ddof=1))
    k = 1 / math.sqrt(n)
    t, df = dz / k, n - 1
    low = optimize.brentq(lambda nc: stats.nct.sf(t, df, nc) - 0.025, t - 8, t)
    high = optimize.brentq(lambda nc: stats.nct.cdf(t, df, nc) - 0.025, t, t + 8)
    return dz, float(low * k), float(high * k)


def wilcoxon(differences: np.ndarray, alternative: str) -> dict[str, float]:
    """The signed-rank test as R's wilcox.test(exact = FALSE, correct = TRUE) computes it
    (R 4.6, stats:::.wilcox_test_one_pval_asymp, `correct` then 0): zero differences left
    out; the normal approximation with the ties and continuity corrections; the two-sided p
    as 2 min(p, 1 - p). The rank-biserial correlation is (W+ - W-) / (W+ + W-)."""
    nonzero = differences[differences != 0]
    n = len(nonzero)
    ranks = stats.rankdata(np.abs(nonzero))
    plus, minus = float(ranks[nonzero > 0].sum()), float(ranks[nonzero < 0].sum())
    _values, ties = np.unique(ranks, return_counts=True)
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24 - float((ties**3 - ties).sum()) / 48)
    z = plus - n * (n + 1) / 4
    correction = {"two-sided": math.copysign(0.5, z) if z else 0.0, "greater": 0.5,
                  "less": -0.5}[alternative]  # fmt: skip
    z = (z - correction) / sigma
    low = float(stats.norm.cdf(z))
    if alternative == "less":
        p = low
    elif alternative == "greater":
        p = float(stats.norm.sf(z))
    else:
        p = 2 * min(low, 1 - low)
    return {"V": plus, "p": p, "rb": (plus - minus) / (plus + minus),
            "zeros": float(len(differences) - n)}  # fmt: skip


def paired(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    first, second = chosen["first"][0], chosen["second"][0]
    data = prepared.table[[first, second]].dropna()
    a, b = data[first].to_numpy(float), data[second].to_numpy(float)
    differences = a - b
    n = len(differences)
    names = [book.label(first), book.label(second)]
    alternative = ALTERNATIVES[options.get("alternative", "two_sided")]
    warnings: list[str] = []
    found: dict[str, float] = {
        "n": n,
        "m1": float(a.mean()),
        "m2": float(b.mean()),
        "sd1": float(a.std(ddof=1)),
        "sd2": float(b.std(ddof=1)),
    }
    shapiro = _shapiro(differences)
    if shapiro is not None:
        found["shapiro_p"] = shapiro
        if shapiro < 0.05 and n < SHAPIRO_FEW:
            warnings.append(
                _(
                    "Différences peu normales (Shapiro-Wilk {p}) avec moins de {n} personnes."
                ).format(p=p_part(shapiro), n=SHAPIRO_FEW)
            )
    rows = [
        [names[0], str(n), f"{number(a.mean())} ({number(a.std(ddof=1))})"],
        [names[1], str(n), f"{number(b.mean())} ({number(b.std(ddof=1))})"],
    ]
    tables = [Table(_("Mesures"), [_("Mesure"), "n", _("M (ÉT)")], rows)]
    if options["method"] == "wilcoxon":
        test = wilcoxon(differences, alternative)
        found |= test | {"mdn1": float(np.median(a)), "mdn2": float(np.median(b))}
        if test["zeros"]:
            warnings.append(
                _("{n} différences nulles écartées par le test de Wilcoxon.").format(
                    n=int(test["zeros"])
                )
            )
        sentence = _(
            "{a} : médiane de {m1} ; {b} : médiane de {m2} ; V = {v}, {p}, r = {r} (n = {n})."
        ).format(
            a=names[0],
            m1=number(found["mdn1"]),
            b=_mid(names[1]),
            m2=number(found["mdn2"]),
            v=number(test["V"], 1),
            p=p_part(test["p"]),
            r=bounded(test["rb"]),
            n=n,
        )
    else:
        test = stats.ttest_rel(a, b, alternative=alternative)
        diff = float(differences.mean())
        half = stats.t.ppf(0.975, n - 1) * differences.std(ddof=1) / math.sqrt(n)
        dz, dz_low, dz_high = paired_d(differences)
        found |= {
            "t": float(test.statistic),
            "df": float(n - 1),
            "p": float(test.pvalue),
            "diff": diff,
            "diff_low": float(diff - half),
            "diff_high": float(diff + half),
            "d": dz,
            "d_low": dz_low,
            "d_high": dz_high,
        }
        sentence = _(
            "{a} : M = {m1} (ÉT = {s1}) ; {b} : M = {m2} (ÉT = {s2}) ; différence {diff}, "
            "{diff_ci}, t({df}) = {t}, {p}, d_z = {d}, {ci} (n = {n})."
        ).format(
            a=names[0],
            m1=number(a.mean()),
            s1=number(a.std(ddof=1)),
            b=_mid(names[1]),
            m2=number(b.mean()),
            s2=number(b.std(ddof=1)),
            diff=number(diff),
            diff_ci=interval(diff - half, diff + half),
            df=n - 1,
            t=number(test.statistic),
            p=p_part(test.pvalue),
            d=number(dz),
            ci=interval(dz_low, dz_high),
            n=n,
        )
    return AnalysisResult(
        "paired", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
    )


def _mid(label: str) -> str:
    """A label inside a title: "score de stress", but "TCC" and "QFS total" stay."""
    if len(label) > 1 and label[0].isupper() and label[1].islower():
        return label[0].lower() + label[1:]
    return label


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
        tukey = pairwise_tukeyhsd(values, data[group].to_numpy())
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
            pair = f"{code_key(g2)}_{code_key(g1)}"
            found[f"tukey_{pair}"] = float(diff)
            found[f"tukey_p_{pair}"] = float(padj)
            found[f"tukey_low_{pair}"] = float(low)
            found[f"tukey_high_{pair}"] = float(high)
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


# --- Partial correlation (v0.14, D-111). ---


def _residuals(y: pd.Series, Z: pd.DataFrame) -> np.ndarray:
    fit = sm.OLS(y.astype(float), sm.add_constant(Z.astype(float), has_constant="add")).fit()
    return fit.resid.to_numpy()


def partial(project, prepared, chosen, options) -> AnalysisResult:
    """The correlation of the residuals of the two variables regressed on the covariates;
    t with n - 2 - k degrees of freedom, the interval by Fisher's transformation."""
    book = Codebook(project, prepared)
    (first, second), covariates = chosen["variables"], chosen["covariates"]
    data = prepared.table[[first, second, *covariates]].dropna()
    Z = design(book, data, covariates)
    n, k = len(data), Z.shape[1]
    rx, ry = _residuals(data[first], Z), _residuals(data[second], Z)
    r = float(np.corrcoef(rx, ry)[0, 1])
    df = n - 2 - k
    t = r * math.sqrt(df / (1 - r**2))
    p = float(2 * stats.t.sf(abs(t), df))
    half = stats.norm.ppf(0.975) / math.sqrt(n - 3 - k)
    low, high = math.tanh(math.atanh(r) - half), math.tanh(math.atanh(r) + half)
    simple = stats.pearsonr(data[first].astype(float), data[second].astype(float))
    found = {"n": n, "k": k, "r": r, "df": float(df), "t": float(t), "p": p,
             "ci_low": float(low), "ci_high": float(high),
             "r_simple": float(simple.statistic), "p_simple": float(simple.pvalue)}  # fmt: skip
    names = [book.label(first), book.label(second)]
    held = ", ".join(_mid(book.label(c)) for c in covariates)
    warnings = []
    if n < SHAPIRO_FEW:
        warnings.append(_("Moins de {n} observations.").format(n=SHAPIRO_FEW))
    rows = [[names[0], names[1], str(n), number(simple.statistic), number(r),
             interval(low, high), number(t), p_part(p)]]  # fmt: skip
    columns = [_("Variable"), _("Variable"), "n", "r", _("r partiel"), _("IC 95 %"), "t", "p"]
    sentence = _(
        "La corrélation partielle entre {a} et {b} (covariables : {z}) était r({df}) = {r}, "
        "{ci}, {p} ; la corrélation simple était r = {simple} (n = {n})."
    ).format(
        a=_mid(names[0]),
        b=_mid(names[1]),
        z=held,
        df=df,
        r=bounded(r),
        ci=bounded_interval(low, high),
        p=p_part(p),
        simple=bounded(simple.statistic),
        n=n,
    )
    return AnalysisResult("partial", chosen, options, n, len(prepared.table) - n,
                          [Table(_("Corrélation partielle"), columns, rows)], found, sentence,
                          warnings)  # fmt: skip


# --- Moderation (v0.14, D-111). ---


def moderation_design(book: Codebook, data: pd.DataFrame, chosen, options):
    """The model's columns in R's order (x, w, covariates, x:w), the moderator's values for
    the simple slopes with their labels, and whether the moderator is nominal: its second
    code is then 1, the first 0."""
    outcome, focal = chosen["outcome"][0], chosen["focal"][0]
    moderator, covariates = chosen["moderator"][0], chosen.get("covariates", [])
    center = options.get("center", "yes") == "yes"
    x = data[focal].astype(float)
    nominal = book.levels.get(moderator) == "nominal"
    if nominal:
        codes = sorted(_codes(book, moderator, data[moderator]))
        w = (data[moderator] == codes[1]).astype(float)
        at = [(0.0, book.category(moderator, codes[0])), (1.0, book.category(moderator, codes[1]))]
        if center:
            x = x - x.mean()
    else:
        w = data[moderator].astype(float)
        mean, sd = float(w.mean()), float(w.std(ddof=1))
        if center:
            x, w = x - x.mean(), w - mean
            mean = 0.0
        at = [(mean - sd, _("−1 ÉT")), (mean, _("moyenne")), (mean + sd, _("+1 ÉT"))]
    columns = {focal: x, moderator: w}
    columns |= dict(design(book, data, covariates).items())
    columns["interaction"] = x * w
    return data[outcome].astype(float), pd.DataFrame(columns, index=data.index), at, nominal


def moderation(project, prepared, chosen, options) -> AnalysisResult:
    book = Codebook(project, prepared)
    outcome, focal = chosen["outcome"][0], chosen["focal"][0]
    moderator, covariates = chosen["moderator"][0], chosen.get("covariates", [])
    data = prepared.table[[outcome, focal, moderator, *covariates]].dropna()
    y, X, at, nominal = moderation_design(book, data, chosen, options)
    exog = sm.add_constant(X, has_constant="add")
    if np.linalg.matrix_rank(exog.to_numpy()) < exog.shape[1]:
        raise conditions.AnalysisRefused(
            conditions.Check(refusals=[_("Des termes du modèle se déduisent les uns des autres.")])
        )
    fit = sm.OLS(y, exog).fit()
    main = sm.OLS(y, exog.drop(columns="interaction")).fit()
    n, last = int(fit.nobs), exog.shape[1] - 1
    ci = fit.conf_int().to_numpy()
    f_change = (fit.rsquared - main.rsquared) / ((1 - fit.rsquared) / fit.df_resid)
    found: dict[str, float] = {
        "n": n,
        "r2": float(fit.rsquared),
        "delta_r2": float(fit.rsquared - main.rsquared),
        "f_change": float(f_change),
        "f_change_p": float(stats.f.sf(f_change, 1, fit.df_resid)),
        "df_resid": float(fit.df_resid),
        "b": float(fit.params.iloc[last]),
        "se": float(fit.bse.iloc[last]),
        "t": float(fit.tvalues.iloc[last]),
        "p": float(fit.pvalues.iloc[last]),
        "low": float(ci[last, 0]),
        "high": float(ci[last, 1]),
    }
    x_label, w_label = book.label(focal), book.label(moderator)
    centred = options.get("center", "yes") == "yes"
    names = [
        _("Constante"),
        _("{x} (centré)").format(x=x_label) if centred else x_label,
        w_label if nominal or not centred else _("{x} (centré)").format(x=w_label),
        *[book.label(c) if c in book.entries else c for c in X.columns[2:-1]],
        f"{x_label} × {w_label}",  # noqa: RUF001 (the multiplication sign)
    ]
    rows = []
    for i, label in enumerate(names):
        found |= {f"coef_{i}": float(fit.params.iloc[i]), f"se_{i}": float(fit.bse.iloc[i]),
                  f"t_{i}": float(fit.tvalues.iloc[i]), f"p_{i}": float(fit.pvalues.iloc[i]),
                  f"low_{i}": float(ci[i, 0]), f"high_{i}": float(ci[i, 1])}  # fmt: skip
        rows.append([label, number(fit.params.iloc[i]), number(fit.bse.iloc[i]),
                     interval(ci[i, 0], ci[i, 1]), number(fit.tvalues.iloc[i]),
                     p_part(fit.pvalues.iloc[i])])  # fmt: skip
    cov = fit.cov_params().to_numpy()
    q = stats.t.ppf(0.975, fit.df_resid)
    slopes = []
    for j, (value, label) in enumerate(at, start=1):
        b = fit.params.iloc[1] + value * fit.params.iloc[last]
        se = math.sqrt(cov[1, 1] + value**2 * cov[last, last] + 2 * value * cov[1, last])
        t = b / se
        p = float(2 * stats.t.sf(abs(t), fit.df_resid))
        key = f"slope_{j}"
        found |= {f"{key}_at": float(value), key: float(b), f"{key}_se": se,
                  f"{key}_t": float(t), f"{key}_p": p, f"{key}_low": float(b - q * se),
                  f"{key}_high": float(b + q * se)}  # fmt: skip
        slopes.append((label, b, se, t, p))
    tables = [
        Table(book.label(outcome), [_("Prédicteur"), "b", _("ET"), _("IC 95 %"), "t", "p"], rows),
        Table(
            _("Pentes simples de {x}").format(x=_mid(x_label)),
            [w_label, "b", _("ET"), "t", "p"],
            [[label, number(b), number(se), number(t), p_part(p)] for label, b, se, t, p in slopes],
        ),
    ]
    warnings = []
    vif = [float(variance_inflation_factor(exog.to_numpy(), i)) for i in range(1, last + 1)]
    high = [names[i + 1] for i, v in enumerate(vif) if v > VIF_HIGH]
    if high:
        warnings.append(
            _("Termes très liés entre eux (VIF > {v}) : {names}.").format(
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
    if nominal:
        where = _(" et ").join(
            _("{b} pour {w}").format(b=number(b), w=label) for label, b, *_rest in slopes
        )
    else:
        where = _("{low} à −1 ÉT de {w}, {mid} à sa moyenne et {high} à +1 ÉT").format(
            low=number(slopes[0][1]), w=_mid(w_label), mid=number(slopes[1][1]),
            high=number(slopes[2][1]),
        )  # fmt: skip
    sentence = _(
        "L'interaction entre {x} et {w} était b = {b}, {ci}, t({df}) = {t}, {p}, ΔR² = {dr2} "
        "(n = {n}). La pente de {x} était b = {where}."
    ).format(
        x=_mid(x_label),
        w=_mid(w_label),
        b=number(found["b"]),
        ci=interval(found["low"], found["high"]),
        df=int(fit.df_resid),
        t=number(found["t"]),
        p=p_part(found["p"]),
        dr2=bounded(found["delta_r2"]),
        n=n,
        where=where,
    )
    return AnalysisResult(
        "moderation", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
    )


# --- Binary logistic regression (v0.14, D-111). ---

SEPARATION_SE = 100.0  # a standard error this large: the estimate runs away


def logistic(project, prepared, chosen, options) -> AnalysisResult:
    """Maximum likelihood (statsmodels' Logit, Newton); odds ratios and their Wald interval;
    the likelihood-ratio test against the model without predictor; McFadden's and
    Nagelkerke's R²."""
    import warnings as python_warnings

    book = Codebook(project, prepared)
    outcome, predictors = chosen["outcome"][0], chosen["predictors"]
    data = prepared.table[[outcome, *predictors]].dropna()
    codes = sorted(set(data[outcome]))  # in the order of their codes, as in the R script
    event = codes[1] if options.get("event", "second") == "second" else codes[0]
    y = (data[outcome] == event).astype(float)
    X = design(book, data, predictors)
    exog = sm.add_constant(X, has_constant="add")
    if np.linalg.matrix_rank(exog.to_numpy()) < exog.shape[1]:
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
    with python_warnings.catch_warnings(record=True) as caught:
        python_warnings.simplefilter("always")
        fit = sm.Logit(y, exog).fit(method="newton", maxiter=100, disp=0)
    n = int(fit.nobs)
    ci = fit.conf_int().to_numpy()
    ll, ll0 = float(fit.llf), float(fit.llnull)
    nagelkerke = (1 - math.exp(2 * (ll0 - ll) / n)) / (1 - math.exp(2 * ll0 / n))
    found: dict[str, float] = {
        "n": n,
        "events": float(y.sum()),
        "chi2": float(fit.llr),
        "df": float(fit.df_model),
        "chi2_p": float(fit.llr_pvalue),
        "mcfadden": float(1 - ll / ll0),
        "nagelkerke": float(nagelkerke),
    }
    labels = [_("Constante"), *[book.label(c) if c in book.entries else c for c in X.columns]]
    rows = []
    vif = [float(variance_inflation_factor(exog.to_numpy(), i)) for i in range(1, exog.shape[1])]
    for i, label in enumerate(labels):
        b, se = float(fit.params.iloc[i]), float(fit.bse.iloc[i])
        with np.errstate(over="ignore"):  # under separation, an infinite ratio
            low, high = float(np.exp(ci[i, 0])), float(np.exp(ci[i, 1]))
            ratio = float(np.exp(b))
        found |= {f"coef_{i}": b, f"se_{i}": se, f"z_{i}": float(fit.tvalues.iloc[i]),
                  f"p_{i}": float(fit.pvalues.iloc[i]), f"or_{i}": ratio,
                  f"or_low_{i}": low, f"or_high_{i}": high}  # fmt: skip
        if i:
            found[f"vif_{i}"] = vif[i - 1]
        rows.append([label, number(b), number(se), number(fit.tvalues.iloc[i]),
                     p_part(fit.pvalues.iloc[i]), number(ratio) if i else "",
                     interval(low, high) if i else ""])  # fmt: skip
    tables = [
        Table(
            book.label(outcome),
            [_("Prédicteur"), "b", _("ET"), "z", "p", _("RC"), _("IC 95 % du RC")],
            rows,
        )
    ]
    warnings = []
    converged = bool(fit.mle_retvals.get("converged", True))
    separated = any("separation" in str(w.message).lower() for w in caught)
    if separated or not converged or float(fit.bse.max()) > SEPARATION_SE:
        warnings.append(
            _(
                "Séparation complète ou quasi complète : un prédicteur distingue presque "
                "parfaitement les deux modalités, et les estimations ne sont pas fiables."
            )
        )
    high = [labels[i + 1] for i, v in enumerate(vif) if v > VIF_HIGH]
    if high:
        warnings.append(
            _("Prédicteurs très liés entre eux (VIF > {v}) : {names}.").format(
                v=VIF_HIGH, names=", ".join(high)
            )
        )
    sentence = _(
        "Régression logistique de « {outcome} » ({event}, {k} sur {n}) : χ²({df}) = {chi2}, {p} "
        "face au modèle sans prédicteur, R² de Nagelkerke = {r2}. Les coefficients et les "
        "rapports de cotes sont dans le tableau."
    ).format(
        outcome=book.label(outcome),
        event=book.category(outcome, event),
        k=int(y.sum()),
        n=n,
        df=int(fit.df_model),
        chi2=number(fit.llr),
        p=p_part(fit.llr_pvalue),
        r2=bounded(nagelkerke),
    )
    return AnalysisResult(
        "logistic", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
    )


# --- Repeated-measures ANOVA (v0.14, D-111). ---

MAUCHLY_ALPHA = 0.05  # below it, the sentence gives the Greenhouse-Geisser correction


def holm(p_values: list[float]) -> list[float]:
    """Holm's step-down adjustment, as R's p.adjust(method = "holm")."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


def sphericity(Y: np.ndarray) -> tuple[float, float, float]:
    """Mauchly's W and its p (R's mauchly.test), and the Greenhouse-Geisser epsilon, from
    the covariance of the measures on orthonormal contrasts."""
    n, k = Y.shape
    contrasts = np.linalg.qr(np.column_stack([np.ones(k), np.eye(k)[:, :-1]]))[0][:, 1:]
    T = contrasts.T @ np.cov(Y, rowvar=False) @ contrasts
    p = k - 1
    w = float(np.linalg.det(T) / (np.trace(T) / p) ** p)
    rho = 1 - (2 * p**2 + p + 2) / (6 * p * (n - 1))
    statistic = -(n - 1) * rho * math.log(w)
    w_p = float(stats.chi2.sf(statistic, p * (p + 1) / 2 - 1))
    epsilon = float(np.trace(T) ** 2 / (p * np.trace(T @ T)))
    return w, w_p, epsilon


def rm_anova(project, prepared, chosen, options) -> AnalysisResult:
    """One within-person factor, the measures in their order: F, partial eta squared,
    Mauchly's test and the Greenhouse-Geisser correction, reported when Mauchly's p is below
    ,05 (the sheet, § 9); pairwise paired t tests corrected by Holm."""
    book = Codebook(project, prepared)
    names = chosen["measures"]
    data = prepared.table[names].dropna()
    Y = data.to_numpy(float)
    n, k = Y.shape
    grand = Y.mean()
    ss_time = n * float(((Y.mean(axis=0) - grand) ** 2).sum())
    ss_person = k * float(((Y.mean(axis=1) - grand) ** 2).sum())
    ss_error = float(((Y - grand) ** 2).sum()) - ss_time - ss_person
    df1, df2 = k - 1, (k - 1) * (n - 1)
    f = (ss_time / df1) / (ss_error / df2)
    p_plain = float(stats.f.sf(f, df1, df2))
    w, w_p, epsilon = sphericity(Y)
    gg_p = float(stats.f.sf(f, epsilon * df1, epsilon * df2))
    corrected = w_p < MAUCHLY_ALPHA
    found: dict[str, float] = {
        "n": n,
        "F": float(f),
        "df1": float(df1),
        "df2": float(df2),
        "p_uncorrected": p_plain,
        "eta2p": ss_time / (ss_time + ss_error),
        "mauchly_W": w,
        "mauchly_p": w_p,
        "gg_eps": epsilon,
        "gg_df1": epsilon * df1,
        "gg_df2": epsilon * df2,
        "gg_p": gg_p,
        "p": gg_p if corrected else p_plain,
        "corrected": float(corrected),
    }
    labels = [book.label(name) for name in names]
    rows = []
    for i, (label, column) in enumerate(zip(labels, Y.T, strict=True), start=1):
        found |= {f"m_{i}": float(column.mean()), f"sd_{i}": float(column.std(ddof=1))}
        rows.append([label, f"{number(column.mean())} ({number(column.std(ddof=1))})"])
    tables = [Table(_("Mesures"), [_("Mesure"), _("M (ÉT)")], rows)]
    warnings = []
    if n < SMALL:
        warnings.append(_("Moins de {n} personnes ont toutes les mesures.").format(n=SMALL))
    if corrected:
        warnings.append(
            _(
                "Sphéricité rejetée (Mauchly {p}) : les degrés de liberté sont corrigés par "
                "Greenhouse-Geisser (ε = {eps})."
            ).format(p=p_part(w_p), eps=number(epsilon))
        )
    if options.get("post_hoc") == "holm":
        pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
        tests = [stats.ttest_rel(Y[:, i], Y[:, j]) for i, j in pairs]
        adjusted = holm([float(t.pvalue) for t in tests])
        post = []
        for (i, j), test, p_holm in zip(pairs, tests, adjusted, strict=True):
            key = f"ph_{i + 1}_{j + 1}"
            diff = float((Y[:, i] - Y[:, j]).mean())
            found |= {f"{key}_diff": diff, f"{key}_t": float(test.statistic),
                      f"{key}_p": float(test.pvalue), f"{key}_p_holm": p_holm}  # fmt: skip
            post.append([f"{labels[i]} − {labels[j]}", number(diff), number(test.statistic),
                         p_part(test.pvalue), p_part(p_holm)])  # fmt: skip
        tables.append(
            Table(
                _("Comparaisons deux à deux (Holm)"),
                [_("Paire"), _("Différence"), f"t({n - 1})", "p", _("p corrigé (Holm)")],
                post,
            )
        )
    means = " ; ".join(
        f"{label} {number(column.mean())}" for label, column in zip(labels, Y.T, strict=True)
    )
    if corrected:
        test_text = _("F({df1} ; {df2}) = {f}, {p}, η²p = {eta}, ε = {eps} (Greenhouse-Geisser)")
        test_text = test_text.format(
            df1=number(epsilon * df1), df2=number(epsilon * df2), f=number(f), p=p_part(gg_p),
            eta=bounded(found["eta2p"]), eps=number(epsilon),
        )  # fmt: skip
    else:
        test_text = _("F({df1}, {df2}) = {f}, {p}, η²p = {eta}").format(
            df1=df1, df2=df2, f=number(f), p=p_part(p_plain), eta=bounded(found["eta2p"])
        )
    sentence = _("Comparaison de {k} mesures : {test} ; moyennes : {means} (n = {n}).").format(
        k=k, test=test_text, means=means, n=n
    )
    return AnalysisResult(
        "rm_anova", chosen, options, n, len(prepared.table) - n, tables, found, sentence, warnings
    )
