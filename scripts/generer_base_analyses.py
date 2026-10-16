"""Generate the fictional database of the analyses (v0.9, step 2, D-075): effects planted in
advance, so that every analysis of the catalogue can be checked against a known answer.

An invented study of well-being at work, 300 participants, a fixed seed. Planted effects:

- t test: the intervention group scores higher on well-being (about d = 0.5); no difference
  between the two sexes;
- ANOVA: stress differs by level of education (means 22, 19, 16); a fourth region with 3
  people, for the warning on small groups;
- chi-square: remote work depends on the sector (about V = 0.3); sex and sector independent;
- correlation: working hours and stress (about r = 0.4); age and stress unrelated;
- regression: satisfaction = 2 + 0.5 x support - 0.3 x workload + noise.

Traps: declared missing codes (999 for age, -9 for stress), an ordinal variable (sport), an
identifier, a scale whose fourth item is reversed.

The answer key (`corrige-analyses.json`) gives the planted parameters and the exact values
of each statistic, computed here with numpy from the formulas themselves (no SciPy, no
statsmodels): an independent computation to judge the tool by. The p-values, which need the
distributions, are checked against R instead.

Usage (from the repository root):
    uv run python scripts/generer_base_analyses.py [output_folder]
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

SEED = 20261018
N = 300
STEM = "etude-analyses"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
WELLBEING = [f"bienetre_{i}" for i in range(1, 6)]
REVERSED = "bienetre_4"

LABELS = {
    "id_participant": "Identifiant du participant",
    "groupe": "Groupe de l'étude",
    "sexe": "Sexe",
    "age": "Âge (années)",
    "niveau_etudes": "Plus haut niveau d'études",
    "region": "Région",
    "secteur": "Secteur d'emploi",
    "teletravail": "Télétravail au moins un jour par semaine",
    "heures_travail": "Heures de travail par semaine",
    "stress": "Score de stress (0 à 40)",
    "soutien": "Soutien des collègues (0 à 10)",
    "charge": "Charge de travail perçue (0 à 10)",
    "satisfaction": "Satisfaction au travail (0 à 10)",
    "sport": "Fréquence de l'activité physique",
    "bienetre_1": "Je me sens énergique au travail.",
    "bienetre_2": "Je trouve mon travail utile.",
    "bienetre_3": "Je me sens calme pendant la journée.",
    "bienetre_4": "Je me sens épuisé·e à la fin de la journée.",
    "bienetre_5": "J'ai hâte de commencer ma journée.",
}
AGREEMENT = {1: "Pas du tout d'accord", 2: "Plutôt pas d'accord", 3: "Neutre",
             4: "Plutôt d'accord", 5: "Tout à fait d'accord"}  # fmt: skip
VALUE_LABELS = {
    "groupe": {1: "Intervention", 2: "Contrôle"},
    "sexe": {1: "Femme", 2: "Homme"},
    "niveau_etudes": {1: "Secondaire", 2: "Collégial", 3: "Universitaire"},
    "region": {1: "Nord", 2: "Sud", 3: "Est", 4: "Ouest"},
    "secteur": {1: "Public", 2: "Privé", 3: "Communautaire"},
    "teletravail": {1: "Oui", 2: "Non"},
    "sport": {1: "Jamais", 2: "Rarement", 3: "Parfois", 4: "Souvent", 5: "Tous les jours"},
    "age": {999: "Préfère ne pas répondre"},
    "stress": {-9: "Non réponse"},
    **{name: AGREEMENT for name in WELLBEING},
}
MEASURES = {
    "id_participant": "nominal", "groupe": "nominal", "sexe": "nominal", "age": "scale",
    "niveau_etudes": "ordinal", "region": "nominal", "secteur": "nominal",
    "teletravail": "nominal", "heures_travail": "scale", "stress": "scale", "soutien": "scale",
    "charge": "scale", "satisfaction": "scale", "sport": "ordinal",
    **{name: "ordinal" for name in WELLBEING},
}  # fmt: skip
MISSING = {"age": 999, "stress": -9}


def build() -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    groupe = np.repeat([1, 2], N // 2)
    rng.shuffle(groupe)
    sexe = rng.choice([1, 2], N)
    etudes = rng.choice([1, 2, 3], N, p=[0.3, 0.35, 0.35])
    region = rng.choice([1, 2, 3], N)
    region[rng.choice(N, 3, replace=False)] = 4  # a group of 3: the warning
    secteur = rng.choice([1, 2, 3], N, p=[0.4, 0.4, 0.2])
    remote_share = {1: 0.65, 2: 0.45, 3: 0.25}  # remote work depends on the sector
    teletravail = np.where(rng.random(N) < np.vectorize(remote_share.get)(secteur), 1, 2)
    age = np.round(rng.uniform(20, 65, N)).astype(float)
    heures = np.round(rng.normal(38, 6, N), 1)
    base_stress = {1: 22.0, 2: 19.0, 3: 16.0}
    stress = np.vectorize(base_stress.get)(etudes) + 0.45 * (heures - 38) + rng.normal(0, 5, N)
    stress = np.clip(np.round(stress, 1), 0, 40)
    soutien = np.clip(np.round(rng.normal(6, 2, N), 1), 0, 10)
    charge = np.clip(np.round(rng.normal(5, 2, N), 1), 0, 10)
    satisfaction = 2 + 0.5 * soutien - 0.3 * charge + rng.normal(0, 1.2, N)
    satisfaction = np.round(satisfaction, 2)
    sport = rng.choice([1, 2, 3, 4, 5], N, p=[0.15, 0.25, 0.3, 0.2, 0.1])
    # Well-being: a latent level, higher in the intervention group; five items 1 to 5.
    latent = rng.normal(0, 1, N) + np.where(groupe == 1, 0.4, 0.0)
    items = {}
    for name in WELLBEING:
        sign = -1 if name == REVERSED else 1
        raw = 3 + sign * 0.9 * latent + rng.normal(0, 0.8, N)
        items[name] = np.clip(np.round(raw), 1, 5).astype(float)
    for name in WELLBEING[:3]:  # a few answers missing
        items[name][rng.choice(N, 4, replace=False)] = np.nan
    age[rng.choice(N, 5, replace=False)] = 999  # declared missing code
    stress[rng.choice(N, 4, replace=False)] = -9  # declared missing code
    df = pd.DataFrame(
        {
            "id_participant": [f"P-{i:03d}" for i in range(1, N + 1)],
            "groupe": groupe.astype(float),
            "sexe": sexe.astype(float),
            "age": age,
            "niveau_etudes": etudes.astype(float),
            "region": region.astype(float),
            "secteur": secteur.astype(float),
            "teletravail": teletravail.astype(float),
            "heures_travail": heures,
            "stress": stress,
            "soutien": soutien,
            "charge": charge,
            "satisfaction": satisfaction,
            "sport": sport.astype(float),
            **items,
        }
    )
    meta = {
        "file_label": "Etude des analyses (fictive)",
        "column_labels": [LABELS[c] for c in df.columns],
        "variable_value_labels": VALUE_LABELS,
        "missing_ranges": {name: [code] for name, code in MISSING.items()},
        "variable_measure": MEASURES,
    }
    return df, meta


# --- The exact statistics, from the formulas, with numpy only. ---


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """The data as the tool will analyse it: missing codes removed, the score computed."""
    data = df.copy()
    for name, code in MISSING.items():
        data[name] = data[name].where(data[name] != code)
    items = data[WELLBEING].copy()
    items[REVERSED] = 6 - items[REVERSED]
    answered = items.notna().sum(axis=1)
    data["bienetre_total"] = (items.mean(axis=1) * 5).where(answered >= 4)
    return data


def _welch(a: np.ndarray, b: np.ndarray) -> dict:
    n1, n2 = len(a), len(b)
    m1, m2 = a.mean(), b.mean()
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    se = np.sqrt(v1 / n1 + v2 / n2)
    df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    pooled = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    return {"n": [n1, n2], "means": [m1, m2], "t": (m1 - m2) / se, "df": df,
            "d": (m1 - m2) / pooled}  # fmt: skip


def _anova(values: np.ndarray, groups: np.ndarray) -> dict:
    grand = values.mean()
    levels = sorted(set(groups))
    ssb = sum(len(values[groups == g]) * (values[groups == g].mean() - grand) ** 2 for g in levels)
    sst = ((values - grand) ** 2).sum()
    sse = sst - ssb
    dfb, dfe = len(levels) - 1, len(values) - len(levels)
    mse = sse / dfe
    return {"F": (ssb / dfb) / mse, "df": [dfb, dfe], "eta2": ssb / sst,
            "omega2": (ssb - dfb * mse) / (sst + mse),
            "means": {int(g): values[groups == g].mean() for g in levels}}  # fmt: skip


def _chi2(a: np.ndarray, b: np.ndarray) -> dict:
    rows, cols = sorted(set(a)), sorted(set(b))
    observed = np.array([[np.sum((a == r) & (b == c)) for c in cols] for r in rows], float)
    expected = observed.sum(1, keepdims=True) * observed.sum(0, keepdims=True) / observed.sum()
    chi2 = ((observed - expected) ** 2 / expected).sum()
    n = observed.sum()
    return {"chi2": chi2, "df": (len(rows) - 1) * (len(cols) - 1),
            "V": np.sqrt(chi2 / (n * (min(len(rows), len(cols)) - 1)))}  # fmt: skip


def _r(x: np.ndarray, y: np.ndarray) -> dict:
    keep = ~np.isnan(x) & ~np.isnan(y)
    return {"n": int(keep.sum()), "r": float(np.corrcoef(x[keep], y[keep])[0, 1])}


def _ols(y: np.ndarray, *xs: np.ndarray) -> dict:
    X = np.column_stack([np.ones(len(y)), *xs])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ coef
    r2 = 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return {"n": len(y), "coef": coef.tolist(), "r2": r2}


def exact_statistics(df: pd.DataFrame) -> dict:
    data = _clean(df)
    score = data[["bienetre_total", "groupe"]].dropna()
    by_sex = data[["bienetre_total", "sexe"]].dropna()
    stress = data[["stress", "niveau_etudes"]].dropna()
    reg = data[["satisfaction", "soutien", "charge"]].dropna()
    return {
        "t_groupe": _welch(
            score[score.groupe == 1].bienetre_total.values,
            score[score.groupe == 2].bienetre_total.values,
        ),
        "t_sexe": _welch(
            by_sex[by_sex.sexe == 1].bienetre_total.values,
            by_sex[by_sex.sexe == 2].bienetre_total.values,
        ),
        "anova_etudes": _anova(stress.stress.values, stress.niveau_etudes.values),
        "khi2_teletravail_secteur": _chi2(data.teletravail.values, data.secteur.values),
        "khi2_sexe_secteur": _chi2(data.sexe.values, data.secteur.values),
        "r_heures_stress": _r(data.heures_travail.values, data.stress.values),
        "r_age_stress": _r(data.age.values, data.stress.values),
        "regression_satisfaction": _ols(
            reg.satisfaction.values, reg.soutien.values, reg.charge.values
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
        "scoring": {
            "group_items": WELLBEING,
            "reverse_items": [REVERSED],
            "aggregation": "sum",
            "scale_min": 1,
            "scale_max": 5,
            "min_items_answered": 4,
            "missing_rule": "prorate",
            "score_name": "bienetre_total",
        },
        "missing_codes": MISSING,
        "planted": {
            "t_groupe": "intervention plus haute, d d'environ 0,5",
            "t_sexe": "aucune différence",
            "anova_etudes": "moyennes de stress 22, 19, 16 selon le niveau d'études",
            "small_group": "région Ouest : 3 personnes",
            "khi2_teletravail_secteur": "associés, V d'environ 0,3",
            "khi2_sexe_secteur": "indépendants",
            "r_heures_stress": "r d'environ 0,4",
            "r_age_stress": "r d'environ 0",
            "regression_satisfaction": "2 + 0,5 x soutien - 0,3 x charge",
            "ordinal": "sport",
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
    key = out_dir / "corrige-analyses.json"
    key.write_text(
        json.dumps(answer_key(df), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return [sav, csv, key]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère la base fictive des analyses (v0.9).")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
