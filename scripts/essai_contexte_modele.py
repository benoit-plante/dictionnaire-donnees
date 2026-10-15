"""Trial of the analysis context with a local model (v0.8, step 8): not a bench, a first look.

The reviewed fictional sleep study (tests/context_examples.py) is described to the model in
two ways: (A) the Markdown report of the codebook, (B) the analysis context. The same task
asks for R code (a score, its mean by gender, its correlation with age). The code is run in R
on the fictional database only, and its results compared with the right answers, computed
here independently; the code itself is checked for the errors an analysis must avoid.

The model receives documents of metadata only, never the data; Ollama runs on this computer.

    uv run python scripts/essai_contexte_modele.py [--modele qwen2.5:7b-instruct-q4_K_M]
        [--essais 3] [--sortie dossier]

Prints a JSON summary; the codes and results are kept in the output folder.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from context_examples import PROJECTS  # noqa: E402
from ddict.export import render_markdown  # noqa: E402
from ddict.export.context import render_context  # noqa: E402
from ddict.export.syntax import write_syntax  # noqa: E402
from test_syntax import _rscript  # noqa: E402

SAV = ROOT / "exemples" / "bases-fictives" / "etude-sommeil.sav"
URL = "http://127.0.0.1:11434/api/chat"
ITEMS = [f"sommeil_q{i}" for i in range(1, 9)]
SENSITIVE = ("courriel", "id_participant", "date_naissance", "commentaire")
INVENTED = ("seuil", "cutoff", "cut-off", "psqi", "pittsburgh", "isi", "insomnia severity")
TASK = """Un objet R `donnees` est déjà chargé : la base etude-sommeil.sav, lue avec
haven::read_sav(user_na = TRUE), puis le fichier de commandes de l'équipe appliqué (libellés,
étiquettes de valeurs, codes manquants déclarés). Les codes manquants sont donc encore
présents dans les données, déclarés comme tels.

En te fiant uniquement au document ci-dessus, écris un script R qui :
1. calcule le score total de qualité du sommeil de chaque participant, dans un vecteur
   numérique `score` (une valeur par ligne de `donnees`, NA quand il ne peut être calculé) ;
2. calcule la moyenne de `score` pour chaque genre, dans un vecteur numérique nommé
   `moyennes_genre` dont les noms sont les étiquettes des genres ;
3. calcule la corrélation de Pearson entre `score` et l'âge, dans `correlation`.

N'affiche aucune donnée individuelle. Réponds seulement avec le code R, dans un bloc ```r."""
SYSTEM = "Tu es un assistant d'analyse statistique. Tu écris du code R correct et prudent."


def documents(project) -> dict[str, str]:
    return {"A_rapport": render_markdown(project), "B_contexte": render_context(project)}


def ask(model: str, document: str, seed: int) -> str:
    response = httpx.post(
        URL,
        json={
            "model": model,
            "stream": False,
            "options": {"seed": seed, "temperature": 0.3, "num_ctx": 16384},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"{document}\n\n---\n\n{TASK}"},
            ],
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def code_of(answer: str) -> str:
    found = re.findall(r"```(?:r|R)?\s*\n(.*?)```", answer, flags=re.S)
    return max(found, key=len) if found else answer


# --- The right answers, and the usual mistakes, computed here. ---


def table() -> pd.DataFrame:
    data, _meta = pyreadstat.read_sav(str(SAV), user_missing=True)
    return data


def score_variant(data, *, reverse=True, drop_nine=True, rule="prorate") -> pd.Series:
    items = data[ITEMS].apply(pd.to_numeric, errors="coerce")
    if drop_nine:
        items = items.where(items != 9)
    if reverse:
        for name in ("sommeil_q3", "sommeil_q6"):
            items[name] = 6 - items[name]
    answered = items.notna().sum(axis=1)
    if rule == "prorate":
        return (items.mean(axis=1) * 8).where(answered >= 7)
    if rule == "sum_answered":
        return items.sum(axis=1).where(answered >= 7)
    return items.sum(axis=1, min_count=8)  # complete cases only


VARIANTS = {
    "juste": {},
    "sans inversion": {"reverse": False},
    "code 9 compté": {"drop_nine": False},
    "somme des items répondus": {"rule": "sum_answered"},
    "huit items exigés": {"rule": "complete"},
    "sans inversion, code 9 compté": {"reverse": False, "drop_nine": False},
}


def truth(data) -> dict:
    score = score_variant(data)
    genre = data["genre"].where(data["genre"] != 9)
    labels = {1: "Femme", 2: "Homme", 3: "Autre identité"}
    means = {labels[g]: score[genre == g].mean() for g in labels}
    age = data["age"].where(data["age"] != 999)
    both = score.notna() & age.notna()
    return {
        "score": score,
        "means": means,
        "correlation": np.corrcoef(score[both], age[both])[0, 1],
    }


def diagnose(found: pd.Series, data) -> str:
    for name, options in VARIANTS.items():
        expected = score_variant(data, **options)
        if len(found) == len(expected) and np.allclose(found, expected, equal_nan=True):
            return name
    return "autre"


# --- Running the model's code in R, on the fictional database. ---


def run_r(code: str, folder: Path) -> dict:
    metadata = folder / "metadonnees.R"
    write_syntax(PROJECTS["etude-sommeil"](), {"r": metadata}, "2026-10-15")
    (folder / "modele.R").write_text(code, encoding="utf-8")
    runner = folder / "run.R"
    runner.write_text(
        f'donnees <- haven::read_sav("{SAV.as_posix()}", user_na = TRUE)\n'
        f'source("{metadata.as_posix()}", encoding = "UTF-8")\n'
        "ddict_out <- tryCatch({\n"
        f'  source("{(folder / "modele.R").as_posix()}", encoding = "UTF-8", local = TRUE)\n'
        '  "ok"\n'
        "}, error = function(e) paste('ERREUR:', conditionMessage(e)))\n"
        f'writeLines(ddict_out, "{(folder / "statut.txt").as_posix()}")\n'
        'if (exists("score")) write.csv(data.frame(score = as.numeric(score)), '
        f'"{(folder / "score.csv").as_posix()}", row.names = FALSE)\n'
        'if (exists("moyennes_genre")) write.csv(data.frame(nom = names(moyennes_genre), '
        "valeur = as.numeric(moyennes_genre)), "
        f'"{(folder / "moyennes.csv").as_posix()}", row.names = FALSE)\n'
        'if (exists("correlation")) writeLines(format(as.numeric(correlation)[1], '
        f'digits = 15), "{(folder / "correlation.txt").as_posix()}")\n',
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(runner)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)  # fmt: skip
    status = (folder / "statut.txt").read_text(encoding="utf-8").strip() if (
        folder / "statut.txt").is_file() else f"ERREUR: {done.stderr.strip()[-200:]}"  # fmt: skip
    found = {"statut": status}
    if (folder / "score.csv").is_file():
        found["score"] = pd.read_csv(folder / "score.csv")["score"]
    if (folder / "moyennes.csv").is_file():
        means = pd.read_csv(folder / "moyennes.csv")
        found["means"] = dict(zip(means["nom"].astype(str), means["valeur"], strict=True))
    if (folder / "correlation.txt").is_file():
        text = (folder / "correlation.txt").read_text(encoding="utf-8").strip()
        found["correlation"] = float(text) if text not in ("", "NA") else None
    return found


def check(code: str, found: dict, data, right: dict) -> dict:
    lower = code.lower()
    result = {"s_execute": found["statut"] == "ok"}
    score = found.get("score")
    result["score"] = diagnose(score, data) if score is not None else "absent"
    means = found.get("means") or {}
    result["moyennes_justes"] = bool(means) and set(means) == set(right["means"]) and all(
        np.isclose(means[k], v) for k, v in right["means"].items())  # fmt: skip
    result["genre_9_exclu"] = bool(means) and not any(
        ("pr" in k.lower() and "pond" in k.lower()) or k.strip() == "9" for k in means)  # fmt: skip
    corr = found.get("correlation")
    result["correlation_juste"] = corr is not None and bool(np.isclose(corr, right["correlation"]))
    result["variable_sensible_utilisee"] = [n for n in SENSITIVE if n in lower]
    result["invention_possible"] = [w for w in INVENTED if re.search(rf"\b{w}\b", lower)]
    result["age_999_traite"] = "999" in code or "zap_missing" in lower or "is.na" in lower
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modele", default="qwen2.5:7b-instruct-q4_K_M")
    parser.add_argument("--essais", type=int, default=3)
    parser.add_argument("--sortie", type=Path, default=None)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # a model's answer may hold any character
        stream.reconfigure(encoding="utf-8")
    out = args.sortie or Path(tempfile.mkdtemp(prefix="essai-contexte-"))
    project = PROJECTS["etude-sommeil"]()
    data = table()
    right = truth(data)
    summary = {"modele": args.modele, "taille_documents_car": {}, "essais": []}
    for condition, document in documents(project).items():
        summary["taille_documents_car"][condition] = len(document)
        for seed in range(1, args.essais + 1):
            folder = out / f"{condition}-{seed}"
            folder.mkdir(parents=True, exist_ok=True)
            answer = ask(args.modele, document, seed)
            (folder / "reponse.md").write_text(answer, encoding="utf-8")
            code = code_of(answer)
            found = run_r(code, folder)
            result = {"condition": condition, "graine": seed, "statut": found["statut"][:160]}
            result |= check(code, found, data, right)
            summary["essais"].append(result)
            print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
    summary["dossier"] = str(out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
