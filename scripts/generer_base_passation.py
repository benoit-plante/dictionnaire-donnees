"""Generate the fictional database of administration (v0.12, step 2): exclusion cases
planted in advance, so that the exclusion rules, the flow diagram, the quality signals and
the Method section can be checked against a known answer (docs/methode-gabarits.md, § 1).

An invented questionnaire, 400 answers, a fixed seed, readable names. Planted cases, some
of them with two reasons to check the order of the rules:
- 12 refusals of consent (questionnaire empty afterwards), 2 of them also under 18;
- 9 people under 18 (the 2 above included);
- 14 people with fewer than 5 of the 6 anxiety items answered;
- 10 administrations shorter than 3 minutes, 3 of them also straight-lining;
- 8 straight-lined satisfaction grids (the 3 above included);
- 5 e-mail addresses repeated by a later answer.
Traps: a declared missing code (999 for age, on 6 kept people), an item to reverse (anx3),
a kept person with one anxiety item missing (the prorated sum), canary strings (`ZQX…`) in
the identifier and the e-mail address.

The answer key (`corrige-passation.json`) gives the rules in the format of the sheet, the
counts per rule in two orders, the description of the analysed sample and Cronbach's alpha
with its Feldt interval, computed here from the formulas with numpy (and SciPy for the F
quantiles only), independently of the tool's code.

Usage (from the repository root):
    uv run python scripts/generer_base_passation.py [output_folder]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

SEED = 20261020
N = 400
STEM = "etude-passation"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
CANARY_ID = "ZQXID"
CANARY_MAIL = "zqxmail"
ANXIETY = [f"anx{i}" for i in range(1, 7)]
REVERSED = "anx3"
SATISFACTION = [f"sat{i}" for i in range(1, 9)]
FAST_SECONDS = 180

LABELS = {
    "id_participant": "Identifiant du participant",
    "courriel": "Adresse courriel",
    "debut": "Début de la passation",
    "fin": "Fin de la passation",
    "consentement": "Consentement à participer",
    "age": "Âge (années)",
    "genre": "Genre",
    "anx1": "Je me suis senti·e nerveux·se.",
    "anx2": "J'ai eu du mal à me détendre.",
    "anx3": "Je me suis senti·e calme.",
    "anx4": "Je me suis inquiété·e pour des riens.",
    "anx5": "J'ai eu peur que quelque chose de grave arrive.",
    "anx6": "J'ai été facilement irritable.",
    "sat1": "Je suis satisfait·e de mon horaire.",
    "sat2": "Je suis satisfait·e de mon logement.",
    "sat3": "Je suis satisfait·e de mes relations.",
    "sat4": "Je suis satisfait·e de ma santé.",
    "sat5": "Je suis satisfait·e de mes loisirs.",
    "sat6": "Je suis satisfait·e de mes finances.",
    "sat7": "Je suis satisfait·e de mon quartier.",
    "sat8": "Je suis satisfait·e de ma vie en général.",
    "stress": "Score de stress (0 à 40)",
}
FREQUENCY = {1: "Jamais", 2: "Parfois", 3: "Souvent", 4: "Très souvent"}
AGREEMENT = {1: "Pas du tout d'accord", 2: "Plutôt pas d'accord", 3: "Neutre",
             4: "Plutôt d'accord", 5: "Tout à fait d'accord"}  # fmt: skip
VALUE_LABELS = {
    "consentement": {1: "Oui", 2: "Non"},
    "genre": {1: "Femme", 2: "Homme", 3: "Autre"},
    "age": {999: "Préfère ne pas répondre"},
    **{name: FREQUENCY for name in ANXIETY},
    **{name: AGREEMENT for name in SATISFACTION},
}
MEASURES = {
    "id_participant": "nominal", "courriel": "nominal", "debut": "scale", "fin": "scale",
    "consentement": "nominal", "age": "scale", "genre": "nominal", "stress": "scale",
    **{name: "ordinal" for name in ANXIETY + SATISFACTION},
}  # fmt: skip
FORMATS = {
    "debut": "DATETIME20", "fin": "DATETIME20", "consentement": "F1.0", "age": "F3.0",
    "genre": "F1.0", "stress": "F4.1",
    **{name: "F1.0" for name in ANXIETY + SATISFACTION},
}  # fmt: skip
MISSING = {"age": 999}

# The rules of the sheet (§ 2), in their default order.
RULES = [
    {"id": "E1", "kind": "condition", "variable": "consentement", "operator": "eq", "value": 2,
     "reason": "Refus de consentement"},
    {"id": "E2", "kind": "condition", "variable": "age", "operator": "lt", "value": 18,
     "reason": "Moins de 18 ans"},
    {"id": "E3", "kind": "completeness", "group": "G1", "min_answered": 5,
     "reason": "Moins de 5 items d'anxiété répondus sur 6"},
    {"id": "E4", "kind": "duration", "start": "debut", "end": "fin", "min_seconds": FAST_SECONDS,
     "reason": "Passation de moins de 3 minutes",
     "source": "Seuil fixé par l'équipe (fictif)"},
    {"id": "E5", "kind": "straightlining", "group": "G2",
     "reason": "Grille de satisfaction en ligne droite"},
    {"id": "E6", "kind": "duplicate", "variables": ["courriel"], "keep": "first",
     "reason": "Courriel en double"},
]  # fmt: skip


def build() -> tuple[pd.DataFrame, dict, dict]:
    """The database, its SPSS metadata, and the planted rows by case (for the answer key)."""
    rng = np.random.default_rng(SEED)
    perm = [int(i) for i in rng.permutation(N)]
    refusal = perm[0:12]
    minor = perm[0:2] + perm[12:19]
    incomplete = perm[19:33]
    fast = perm[33:43]
    straight = perm[33:36] + perm[43:48]
    clean = sorted(perm[48:])
    duplicate = sorted(int(i) for i in rng.choice([i for i in clean if i >= 200], 5, False))
    original = sorted(int(i) for i in rng.choice([i for i in clean if i < 200], 5, False))
    kept = [i for i in clean if i not in duplicate]
    missing_age = sorted(int(i) for i in rng.choice(kept, 6, False))
    one_missing = sorted(int(i) for i in rng.choice(kept, 4, False))

    latent = rng.normal(0, 1, N)
    anx = {}
    for name in ANXIETY:
        sign = -1 if name == REVERSED else 1
        raw = 2.5 + sign * 0.8 * latent + rng.normal(0, 0.6, N)
        anx[name] = np.clip(np.round(raw), 1, 4).astype(float)
    sat_level = rng.normal(0, 1, N)
    sat = {
        name: np.clip(np.round(3.2 + 0.8 * sat_level + rng.normal(0, 0.9, N)), 1, 5).astype(float)
        for name in SATISFACTION
    }
    stress = np.clip(np.round(20 + 5 * latent + rng.normal(0, 4, N), 1), 0, 40)
    age = np.round(rng.uniform(18, 70, N)).astype(float)
    genre = rng.choice([1.0, 2.0, 3.0], N, p=[0.52, 0.46, 0.02])
    consent = np.ones(N)
    seconds = rng.integers(300, 1800, N).astype(float)
    begin = [
        dt.datetime(2026, 3, 1, 8, 0) + dt.timedelta(minutes=int(m))
        for m in rng.integers(0, 60 * 24 * 60, N)
    ]

    for i in range(N):  # no accidental straight line in a kept grid
        values = [sat[name][i] for name in SATISFACTION]
        if len(set(values)) == 1:
            sat["sat8"][i] = values[0] + (1 if values[0] < 5 else -1)
    for i in refusal:
        consent[i] = 2
        for name in ANXIETY + SATISFACTION:
            (anx if name in anx else sat)[name][i] = np.nan
        stress[i], age[i], genre[i] = np.nan, np.nan, np.nan
        seconds[i] = rng.integers(20, 60)
    for i in minor:
        age[i] = rng.integers(15, 18)
    for i in incomplete:
        answered = int(rng.integers(2, 5))  # 2 to 4 of 6
        for name in rng.choice(ANXIETY, len(ANXIETY) - answered, replace=False):
            anx[str(name)][i] = np.nan
    for i in fast:
        seconds[i] = rng.integers(60, FAST_SECONDS)
    for i in straight:
        value = float(rng.integers(1, 6))
        for name in SATISFACTION:
            sat[name][i] = value
    for i in one_missing:
        anx[str(rng.choice(ANXIETY))][i] = np.nan
    for i in missing_age:
        age[i] = 999.0

    mails = [f"{CANARY_MAIL}{i + 1:04d}@exemple.org" for i in range(N)]
    for dup, orig in zip(duplicate, original, strict=True):
        mails[dup] = mails[orig]
    df = pd.DataFrame(
        {
            "id_participant": [f"{CANARY_ID}-{i + 1:04d}" for i in range(N)],
            "courriel": mails,
            "debut": pd.to_datetime(begin),
            "fin": pd.to_datetime(
                [b + dt.timedelta(seconds=float(s)) for b, s in zip(begin, seconds, strict=True)]
            ),
            "consentement": consent,
            "age": age,
            "genre": genre,
            **anx,
            **sat,
            "stress": stress,
        }
    )
    meta = {
        "file_label": "Etude de passation (fictive)",
        "column_labels": [LABELS[c] for c in df.columns],
        "variable_value_labels": VALUE_LABELS,
        "missing_ranges": {name: [code] for name, code in MISSING.items()},
        "variable_measure": MEASURES,
        "variable_format": FORMATS,
    }
    planted = {
        "refusal": len(refusal), "minor": len(minor), "minor_and_refusal": 2,
        "incomplete": len(incomplete), "fast": len(fast), "straight": len(straight),
        "fast_and_straight": 3, "duplicate": len(duplicate), "missing_age_kept": len(missing_age),
        "one_anxiety_item_missing_kept": len(one_missing),
    }  # fmt: skip
    return df, meta, planted


# --- The answer key, from the formulas, independently of the tool. ---


def _flags(df: pd.DataFrame) -> dict[str, pd.Series]:
    """For each rule, the rows it would exclude on its own (missing codes removed first)."""
    age = df["age"].where(df["age"] != MISSING["age"])
    seconds = (df["fin"] - df["debut"]).dt.total_seconds()
    sat = df[SATISFACTION]
    return {
        "E1": df["consentement"] == 2,
        "E2": age < 18,
        "E3": df[ANXIETY].notna().sum(axis=1) < 5,
        "E4": seconds < FAST_SECONDS,
        "E5": sat.notna().all(axis=1) & (sat.nunique(axis=1) == 1),
        "E6": df["courriel"].duplicated(keep="first"),
    }


def flow(df: pd.DataFrame, order: list[str]) -> dict:
    flags = _flags(df)
    remaining = pd.Series(True, index=df.index)
    counts = {}
    for rule in order:
        hit = remaining & flags[rule]
        counts[rule] = int(hit.sum())
        remaining &= ~hit
    return {"order": order, "start": len(df), "excluded": counts,
            "analysed": int(remaining.sum())}, remaining  # fmt: skip


def _feldt(alpha: float, n: int, k: int, level: float = 0.95) -> list[float]:
    """Feldt (1965): the bounds of alpha from the F distribution."""
    df1, df2 = n - 1, (n - 1) * (k - 1)
    tail = (1 - level) / 2
    return [1 - (1 - alpha) * stats.f.ppf(1 - tail, df1, df2),
            1 - (1 - alpha) * stats.f.ppf(tail, df1, df2)]  # fmt: skip


def method_statistics(df: pd.DataFrame) -> dict:
    summary, kept = flow(df, [r["id"] for r in RULES])
    data = df[kept]
    age = data["age"].where(data["age"] != MISSING["age"]).dropna()
    genre = data["genre"].dropna()
    items = data[ANXIETY].copy()
    items[REVERSED] = 5 - items[REVERSED]  # max + min - x, on 1 to 4
    complete = items.dropna()
    k = len(ANXIETY)
    alpha = k / (k - 1) * (1 - complete.var(ddof=1).sum() / complete.sum(axis=1).var(ddof=1))
    answered = items.notna().sum(axis=1)
    score = (items.mean(axis=1) * k).where(answered >= 5)
    return {
        "flow": summary,
        "flow_e5_before_e4": flow(df, ["E1", "E2", "E3", "E5", "E4", "E6"])[0],
        "sample": {
            "age": {"n": len(age), "mean": age.mean(), "sd": age.std(ddof=1)},
            "genre": {
                "n": len(genre),
                "percent": {
                    str(int(c)): 100 * float((genre == c).mean()) for c in sorted(genre.unique())
                },
            },
        },
        "anxiety": {
            "alpha": alpha,
            "n": len(complete),
            "k": k,
            "ci95": _feldt(alpha, len(complete), k),
            "score": {"n": int(score.notna().sum()), "mean": score.mean(), "sd": score.std(ddof=1)},
        },
    }


def answer_key(df: pd.DataFrame, planted: dict) -> dict:
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
        "rows": N,
        "groups": {"G1": ANXIETY, "G2": SATISFACTION},
        "scoring": {
            "group_items": ANXIETY,
            "reverse_items": [REVERSED],
            "aggregation": "sum",
            "scale_min": 1,
            "scale_max": 4,
            "min_items_answered": 5,
            "missing_rule": "prorate",
            "score_name": "anx_total",
            "instrument": "Échelle d'anxiété fictive",
            "source": "Laboratoire fictif (2024)",
        },
        "missing_codes": MISSING,
        "rules": RULES,
        "planted": planted,
        "exact": tidy(method_statistics(df)),
    }


def write_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df, meta, planted = build()
    sav = out_dir / f"{STEM}.sav"
    common.write_sav(df, meta, sav)
    key = out_dir / "corrige-passation.json"
    key.write_text(
        json.dumps(answer_key(df, planted), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return [sav, key]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère la base fictive de passation (v0.12).")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
