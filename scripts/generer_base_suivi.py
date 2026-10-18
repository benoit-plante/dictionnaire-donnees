"""Generate the fictional database of the widened catalogue (v0.14, step 1, D-111): effects
planted in advance, so that every new analysis can be checked against a known answer.

An invented follow-up of a stress-management programme, 240 participants, a fixed seed.
Planted effects:

- paired t test: anxiety falls from the first to the second measure (about d_z = 0.5);
- repeated-measures ANOVA: anxiety at three times (means about 22, 19, 18), the third
  measure more spread out, so that sphericity is not perfect;
- logistic regression: dropping out of the programme is less likely with higher motivation
  (an odds ratio of about 0.6 per point), age unrelated; about one person in four drops out;
- moderation: exhaustion rises with workload, less so when support from colleagues is high
  (a negative interaction);
- partial correlation: stress and hours of sleep are related (about r = -0.35) mostly
  through workload; with workload held constant, the relation is much weaker;
- subgroup: three sexes, the third with few people.

Traps: an identifier, a declared missing code (-9 for the third anxiety measure), people
missing at the second or third measure.

The answer key (`corrige-suivi.json`) gives the planted parameters and the exact values of
each statistic, computed here with numpy from the formulas themselves (no SciPy, no
statsmodels): an independent computation to judge the tool by. The p-values, which need the
distributions, are checked against R instead.

Usage (from the repository root):
    uv run python scripts/generer_base_suivi.py [output_folder]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

SEED = 20261019
N = 240
STEM = "etude-suivi"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
ANXIETY = ["anxiete_t1", "anxiete_t2", "anxiete_t3"]

LABELS = {
    "id_participant": "Identifiant du participant",
    "sexe": "Sexe",
    "age": "Âge (années)",
    "anxiete_t1": "Anxiété au début du programme (0 à 40)",
    "anxiete_t2": "Anxiété à la fin du programme (0 à 40)",
    "anxiete_t3": "Anxiété trois mois après (0 à 40)",
    "motivation": "Motivation au début du programme (1 à 10)",
    "abandon": "A abandonné le programme",
    "charge": "Charge de travail perçue (0 à 10)",
    "soutien": "Soutien des collègues (0 à 10)",
    "epuisement": "Score d'épuisement (0 à 30)",
    "stress": "Score de stress (0 à 40)",
    "sommeil": "Heures de sommeil par nuit",
}
VALUE_LABELS = {
    "sexe": {1: "Femme", 2: "Homme", 3: "Autre identité"},
    "abandon": {0: "Non", 1: "Oui"},
    "anxiete_t3": {-9: "Non réponse"},
}
MEASURES = {
    "id_participant": "nominal", "sexe": "nominal", "age": "scale",
    **{name: "scale" for name in ANXIETY},
    "motivation": "scale", "abandon": "nominal", "charge": "scale", "soutien": "scale",
    "epuisement": "scale", "stress": "scale", "sommeil": "scale",
}  # fmt: skip
MISSING = {"anxiete_t3": -9}


def build() -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    sexe = rng.choice([1, 2, 3], N, p=[0.55, 0.42, 0.03])
    age = np.round(rng.uniform(22, 64, N)).astype(float)
    # Anxiety: a stable personal level, a fall at the end, a third measure more spread out.
    person = rng.normal(0, 5, N)
    t1 = 22 + person + rng.normal(0, 4, N)
    t2 = 19 + person + rng.normal(0, 4, N)
    t3 = 18 + 0.5 * person + rng.normal(0, 7, N)
    t1, t2, t3 = (np.clip(np.round(x, 1), 0, 40) for x in (t1, t2, t3))
    t2[rng.choice(N, 12, replace=False)] = np.nan  # missing at the end of the programme
    t3[rng.choice(N, 20, replace=False)] = np.nan  # lost three months later
    t3[rng.choice(np.flatnonzero(~np.isnan(t3)), 5, replace=False)] = -9  # declared code
    motivation = np.clip(np.round(rng.normal(6, 1.8, N)), 1, 10)
    logit = -1.1 - 0.5 * (motivation - 6) + 0.0 * (age - 43)
    abandon = (rng.random(N) < 1 / (1 + np.exp(-logit))).astype(float)
    charge = np.clip(np.round(rng.normal(5, 2, N), 1), 0, 10)
    soutien = np.clip(np.round(rng.normal(6, 2, N), 1), 0, 10)
    c, s = charge - 5, soutien - 6
    epuisement = 12 + 1.2 * c - 0.6 * s - 0.25 * c * s + rng.normal(0, 3, N)
    epuisement = np.clip(np.round(epuisement, 1), 0, 30)
    stress = 20 + 2.2 * c + rng.normal(0, 4, N)
    sommeil = 7 - 0.12 * c - 0.03 * (stress - 20) + rng.normal(0, 0.8, N)
    stress = np.clip(np.round(stress, 1), 0, 40)
    sommeil = np.clip(np.round(sommeil, 1), 3, 11)
    df = pd.DataFrame(
        {
            "id_participant": [f"S-{i:03d}" for i in range(1, N + 1)],
            "sexe": sexe.astype(float),
            "age": age,
            "anxiete_t1": t1,
            "anxiete_t2": t2,
            "anxiete_t3": t3,
            "motivation": motivation,
            "abandon": abandon,
            "charge": charge,
            "soutien": soutien,
            "epuisement": epuisement,
            "stress": stress,
            "sommeil": sommeil,
        }
    )
    meta = {
        "file_label": "Etude de suivi (fictive)",
        "column_labels": [LABELS[c] for c in df.columns],
        "variable_value_labels": VALUE_LABELS,
        "missing_ranges": {name: [code] for name, code in MISSING.items()},
        "variable_measure": MEASURES,
    }
    return df, meta


# --- The exact statistics, from the formulas, with numpy only. ---


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for name, code in MISSING.items():
        data[name] = data[name].where(data[name] != code)
    return data


def _paired(a: np.ndarray, b: np.ndarray) -> dict:
    d = a - b
    n = len(d)
    sd = d.std(ddof=1)
    return {"n": n, "mean_diff": d.mean(), "t": d.mean() / (sd / np.sqrt(n)), "df": n - 1,
            "d_z": d.mean() / sd}  # fmt: skip


def _residuals(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones(len(y)), X])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ coef


def _partial(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> dict:
    return {"n": len(x), "r": float(np.corrcoef(x, y)[0, 1]),
            "r_partial": float(np.corrcoef(_residuals(x, z), _residuals(y, z))[0, 1])}  # fmt: skip


def _ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float]:
    X = np.column_stack([np.ones(len(y)), X])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ coef
    return coef, 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def _moderation(y: np.ndarray, x: np.ndarray, w: np.ndarray) -> dict:
    xc, wc = x - x.mean(), w - w.mean()
    coef, r2 = _ols(y, np.column_stack([xc, wc, xc * wc]))
    _, r2_main = _ols(y, np.column_stack([xc, wc]))
    sd = w.std(ddof=1)
    slopes = {name: coef[1] + coef[3] * value for name, value in
              (("low", -sd), ("mean", 0.0), ("high", sd))}  # fmt: skip
    return {"n": len(y), "coef": coef.tolist(), "r2": r2, "delta_r2": r2 - r2_main,
            "simple_slopes": slopes}  # fmt: skip


def _logistic(y: np.ndarray, X: np.ndarray) -> dict:
    """Maximum likelihood by Newton-Raphson (iteratively reweighted least squares)."""
    X = np.column_stack([np.ones(len(y)), X])
    beta = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ beta))
        gradient = X.T @ (y - p)
        hessian = X.T @ (X * (p * (1 - p))[:, None])
        step = np.linalg.solve(hessian, gradient)
        beta += step
        if np.abs(step).max() < 1e-12:
            break
    p = 1 / (1 + np.exp(-X @ beta))
    loglik = float((y * np.log(p) + (1 - y) * np.log(1 - p)).sum())
    p0 = y.mean()
    null = float(len(y) * (p0 * np.log(p0) + (1 - p0) * np.log(1 - p0)))
    return {"n": len(y), "events": int(y.sum()), "coef": beta.tolist(),
            "odds_ratios": np.exp(beta).tolist(), "chi2": 2 * (loglik - null),
            "mcfadden_r2": 1 - loglik / null}  # fmt: skip


def _rm_anova(Y: np.ndarray) -> dict:
    """One within-person factor: sums of squares and the Greenhouse-Geisser epsilon."""
    n, k = Y.shape
    grand = Y.mean()
    ss_time = n * ((Y.mean(axis=0) - grand) ** 2).sum()
    ss_person = k * ((Y.mean(axis=1) - grand) ** 2).sum()
    ss_error = ((Y - grand) ** 2).sum() - ss_time - ss_person
    df1, df2 = k - 1, (k - 1) * (n - 1)
    # Epsilon from the double-centred covariance matrix of the measures.
    S = np.cov(Y, rowvar=False)
    C = np.eye(k) - np.ones((k, k)) / k
    D = C @ S @ C
    epsilon = np.trace(D) ** 2 / ((k - 1) * (D**2).sum())
    return {"n": n, "means": Y.mean(axis=0).tolist(), "F": (ss_time / df1) / (ss_error / df2),
            "df": [df1, df2], "eta2_partial": ss_time / (ss_time + ss_error),
            "gg_epsilon": float(epsilon)}  # fmt: skip


def exact_statistics(df: pd.DataFrame) -> dict:
    data = _clean(df)
    pair = data[["anxiete_t1", "anxiete_t2"]].dropna()
    women = data[data.sexe == 1][["anxiete_t1", "anxiete_t2"]].dropna()
    times = data[ANXIETY].dropna()
    logistic = data[["abandon", "motivation", "age"]].dropna()
    moderation = data[["epuisement", "charge", "soutien"]].dropna()
    partial = data[["stress", "sommeil", "charge"]].dropna()
    return {
        "t_apparie_t1_t2": _paired(pair.anxiete_t1.values, pair.anxiete_t2.values),
        "t_apparie_t1_t2_femmes": _paired(women.anxiete_t1.values, women.anxiete_t2.values),
        "anova_rm_anxiete": _rm_anova(times.values),
        "logistique_abandon": _logistic(
            logistic.abandon.values, logistic[["motivation", "age"]].values
        ),
        "moderation_epuisement": _moderation(
            moderation.epuisement.values, moderation.charge.values, moderation.soutien.values
        ),
        "partielle_stress_sommeil": _partial(
            partial.stress.values, partial.sommeil.values, partial.charge.values
        ),
    }


def answer_key(df: pd.DataFrame) -> dict:
    def tidy(value):
        if isinstance(value, dict):
            return {k: tidy(v) for k, v in value.items()}
        if isinstance(value, list | tuple):
            return [tidy(v) for v in value]
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, float | np.floating):
            return round(float(value), 10)
        return value

    return {
        "sav": f"{STEM}.sav",
        "csv": f"{STEM}.csv",
        "rows": N,
        "missing_codes": MISSING,
        "planted": {
            "t_apparie_t1_t2": "baisse de la 1re à la 2e mesure, d_z d'environ 0,5",
            "anova_rm_anxiete": "moyennes d'environ 22, 19, 18 ; 3e mesure dispersée",
            "logistique_abandon": "RC d'environ 0,6 par point de motivation ; âge sans lien",
            "moderation_epuisement": "pente de la charge plus faible à soutien haut",
            "partielle_stress_sommeil": "r d'environ -0,35, bien plus faible à charge constante",
            "small_group": "sexe : Autre identité, quelques personnes",
            "identifier": "id_participant",
        },
        "exact": tidy(exact_statistics(df)),
    }


def write_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df, meta = build()
    sav = out_dir / f"{STEM}.sav"
    common.write_sav(df, meta, sav)
    csv = out_dir / f"{STEM}.csv"
    common.write_csv(df, csv, encoding="utf-8", delimiter=",", decimal=".", line_end="\n")
    key = out_dir / "corrige-suivi.json"
    key.write_text(
        json.dumps(answer_key(df), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return [sav, csv, key]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère la base fictive de suivi (v0.14).")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
