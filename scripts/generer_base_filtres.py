"""Write the fictional filtered study of the tests (v0.21, plan § 8): a questionnaire designed
with the tool's own functions (filters, random orders, attention checks), its file for
LimeSurvey, 300 invented responses as LimeSurvey Cloud 7.6 exports them (`.sav`, CSV) and as
SurveyMonkey would (`.sav`, its `qNNNN` names), and the answer key.

Nothing real: the questions, the scales and the answers are invented; no instrument is a real
one. A fixed seed: two runs write the same bytes. The answer key is counted here, person by
person, from the branches each invented person went through, never by the tool's own
functions: the tests compare the tool to it.

The planted cases: 10 refusals of the consent (every section after it not asked); "Avez-vous
des enfants ?" answered "Non" by 120, left empty by 6 and answered "Préfère ne pas répondre"
(9, declared missing) by 4, so that "Combien ?" is not asked to them (9 ≠ 1, an empty answer
meets no condition); 5 asked "Combien ?" without answering; 3 answers to it under "Non" (an
anomaly, said "< 5") and 7 persons without a job who answered the work climate grid (said by
its number); 4 under 18 among the full-time workers ("De nuit ?" not asked); 6 who answered 3
of the 6 statements of the grid; 12 failures at its attention statement, 9 at the second
attention check, 5 at both, 3 who left the second empty; 5 who ticked no transport; 8 too
quick completions.

Run: uv run python scripts/generer_base_filtres.py [folder]   (default: exemples/bases-fictives/)
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

from ddict import design, design_limesurvey
from ddict.design import Draft, Item
from ddict.project.model import Condition, Project, Term

SEED = 20261021
N = 300
OUT = common.DEFAULT_OUT_DIR
STEM = "filtres"
NOW = "2026-10-21T10:00:00"
SPSS_ZERO = dt.datetime(1582, 10, 14)
AGREE = ("Pas du tout d'accord", "Plutôt pas d'accord", "Ni d'accord ni pas d'accord",
         "Plutôt d'accord", "Tout à fait d'accord")  # fmt: skip
OFTEN = ("Jamais", "Rarement", "Parfois", "Souvent", "Toujours")
CLIMATE = (
    "Mon équipe s'entraide.", "Je sais ce qu'on attend de moi.", "Mes idées sont écoutées.",
    "La charge de travail est raisonnable.", "Je peux organiser mon temps.",
    "Les décisions me sont expliquées.",
    "Pour cet énoncé, choisissez « Plutôt d'accord ».",
)  # fmt: skip
WELLBEING = (
    "Je me sens reposé·e.", "J'ai de l'énergie.", "Je me sens tendu·e.",
    "Je profite de mes journées.", "Je dors bien.", "Je me sens seul·e.", "J'ai le moral.",
    "Je me sens utile.",
)  # fmt: skip
REVERSED = ("SQ003", "SQ006")  # tension, loneliness: fictional reversed statements
HABITS = (("sport", "Faites-vous du sport ?"), ("lecture", "Lisez-vous pour le plaisir ?"),
          ("sorties", "Sortez-vous avec des amis ?"))  # fmt: skip
TRANSPORT = ("En voiture", "À vélo", "En transports en commun")


def _items(texts, codes=None):
    codes = codes or [str(n) for n in range(1, len(texts) + 1)]
    return tuple(Item(t, c) for t, c in zip(texts, codes, strict=True))


def _rows(texts):
    return tuple(Item(t, f"SQ{n:03d}") for n, t in enumerate(texts, start=1))


def _when(*terms, combine="all"):
    return Condition(
        combine=combine, terms=[Term(target=a, operator=o, value=v) for a, o, v in terms]
    )


def project() -> Project:
    """The questionnaire of § 8, its codes decided."""
    found = design.new_project("Familles et travail (fictif)", "fr", "2026-10-21")
    design.modify_section(found, "S1", "Consentement")
    for title in ("Profil", "Travail", "Bien-être", "Habitudes"):
        design.add_section(found, title)
    yes_no = _items(("Oui", "Non"))
    drafts = [
        ("consent", Draft(kind="single", text="Acceptez-vous de participer ?", section="S1",
                          required=True, options=yes_no)),
        ("age", Draft(kind="open", text="Quel âge avez-vous ?", section="S2", answer="number")),
        ("enfants", Draft(kind="single", text="Avez-vous des enfants ?", section="S2",
                          options=_items(("Oui", "Non", "Préfère ne pas répondre"),
                                         ["1", "2", "9"]))),
        ("nbenfants", Draft(kind="open", text="Combien d'enfants vivent avec vous ?",
                            section="S2", answer="number")),
        ("emploi", Draft(kind="single", text="Occupez-vous un emploi ?", section="S2",
                         options=_items(("Temps plein", "Temps partiel", "Non")))),
        ("transport", Draft(kind="checkbox", text="Comment vous déplacez-vous ?", section="S2",
                            options=(*_items(TRANSPORT, ["SQ001", "SQ002", "SQ003"]),
                                     Item("Autre", other=True)))),
        ("climat", Draft(kind="grid", text="Au travail…", section="S3",
                         instruction="Une réponse par ligne.", options=_items(AGREE),
                         rows=_rows(CLIMATE))),
        ("nuit", Draft(kind="single", text="Travaillez-vous de nuit ?", section="S3",
                       options=yes_no)),
        ("bienetre", Draft(kind="grid", text="Au cours des deux dernières semaines…",
                           section="S4", instruction="Une réponse par ligne.",
                           options=_items(OFTEN), rows=_rows(WELLBEING))),
        ("controle", Draft(kind="single", section="S4", options=_items(OFTEN),
                           text="Pour montrer que vous lisez, choisissez « Jamais ».")),
        ("commentaires", Draft(kind="open", text="Des commentaires ?", section="S4",
                               answer="long")),
        *((code, Draft(kind="single", text=text, section="S5", options=_items(OFTEN[:4])))
          for code, text in HABITS),
    ]  # fmt: skip
    for code, draft in drafts:
        question_id = design.add_question(found, draft)
        design.decide_code(found, question_id, "write", now=NOW, value=code)
    # The plan's table, and the same consent on the two last sections: a refusal ends the
    # questionnaire.
    for section in ("S2", "S4", "S5"):
        design.set_condition(found, section, _when(("Q1", "eq", "1")))
    design.set_condition(found, "Q4", _when(("Q3", "eq", "1")))
    design.set_condition(found, "S3", _when(("Q5", "in", ["1", "2"])))
    design.set_condition(found, "Q8", _when(("Q2", "ge", 18), ("Q5", "eq", "1")))
    design.set_shuffle(found, "Q6", True)
    design.set_shuffle(found, "Q7", True)
    design.set_shuffle(found, "Q9", True)
    design.set_shuffle(found, "S5", True)
    design.set_attention(found, "Q7.r7", ["4"])
    design.set_attention(found, "Q10", ["1"])
    return found


# --- The invented persons. ---


def _people() -> list[dict]:
    """Each person's answers (None: an empty cell) and the branches it went through."""
    rng = np.random.default_rng(SEED)
    order = rng.permutation(N)
    people = [{} for _ in range(N)]
    consenting = [int(i) for i in order[10:]]
    for i in order[:10]:
        people[i]["consent"] = 2
    for i in consenting:
        people[i]["consent"] = 1
    # Children: 160 yes, 120 no, 6 empty, 4 "prefers not to answer".
    kids = {"yes": consenting[:160], "no": consenting[160:280], "empty": consenting[280:286],
            "nine": consenting[286:290]}  # fmt: skip
    for i in kids["yes"]:
        people[i]["enfants"] = 1
    for i in kids["no"]:
        people[i]["enfants"] = 2
    for i in kids["nine"]:
        people[i]["enfants"] = 9
    for n, i in enumerate(kids["yes"]):
        people[i]["nbenfants"] = None if n < 5 else int(rng.integers(1, 5))
    for i in kids["no"][:3]:  # the anomalies
        people[i]["nbenfants"] = int(rng.integers(1, 4))
    # Jobs, shuffled apart from the children: 150 full time, 60 part time, 80 none.
    jobs = [int(i) for i in rng.permutation(consenting)]
    full, part, none = jobs[:150], jobs[150:210], jobs[210:]
    for i in full:
        people[i]["emploi"] = 1
    for i in part:
        people[i]["emploi"] = 2
    for i in none:
        people[i]["emploi"] = 3
    minors = full[:4] + part[:3] + none[:3]
    for i in consenting:
        people[i]["age"] = int(rng.integers(16, 18)) if i in minors else int(rng.integers(18, 71))
    # Transport: 5 tick nothing; 10 write another means.
    for n, i in enumerate(consenting):
        ticked = rng.random(3) < (0.5, 0.3, 0.4) if n >= 5 else np.zeros(3, bool)
        if n >= 5 and not ticked.any():
            ticked[0] = True
        for k in range(3):
            people[i][f"transport_SQ{k + 1:03d}"] = "Y" if ticked[k] else None
        people[i]["transport_other"] = f"Moyen fictif {n}" if 5 <= n < 15 else None
    # The work climate: asked to 210; 6 answer 3 statements of 6; 2 leave the check empty;
    # 12 fail it; 7 without a job answer it all (anomalies).
    workers = [int(i) for i in rng.permutation(full + part)]
    for n, i in enumerate(workers):
        for k in range(6):
            people[i][f"climat_SQ{k + 1:03d}"] = (
                None if (n < 6 and k >= 3) else int(rng.integers(1, 6))
            )
        if 6 <= n < 8:
            check = None
        elif 8 <= n < 20:
            check = int(rng.choice([1, 2, 3, 5]))
        else:
            check = 4
        people[i]["climat_SQ007"] = check
    failed_climate = workers[8:20]
    for i in none[3:10]:
        for k in range(7):
            people[i][f"climat_SQ{k + 1:03d}"] = int(rng.integers(1, 6))
    for i in full:
        if people[i]["age"] >= 18:
            people[i]["nuit"] = int(rng.integers(1, 3))
    # Well-being: 4 leave the grid empty. The second check: 3 empty, 9 failures, 5 of whom
    # also failed the first.
    for n, i in enumerate(consenting):
        for k in range(8):
            people[i][f"bienetre_SQ{k + 1:03d}"] = None if n < 4 else int(rng.integers(1, 6))
    others = [i for i in consenting if i not in failed_climate]
    failed_second = failed_climate[:5] + others[:4]
    empty_second = others[4:7]
    for i in consenting:
        if i in failed_second:
            people[i]["controle"] = int(rng.integers(2, 6))
        elif i in empty_second:
            people[i]["controle"] = None
        else:
            people[i]["controle"] = 1
    for n, i in enumerate(consenting[:40]):
        people[i]["commentaires"] = f"Commentaire fictif numéro {n + 1}."
    for i in consenting:
        for code, _text in HABITS:
            people[i][code] = int(rng.integers(1, 5))
    # When: 8 too quick (under two minutes).
    start = dt.datetime(2026, 11, 2, 9, 0, 0)
    for n, i in enumerate(order):
        begun = start + dt.timedelta(minutes=17 * n)
        seconds = int(rng.integers(40, 110)) if 10 <= n < 18 else int(rng.integers(300, 1500))
        people[i]["startdate"] = begun.isoformat(sep=" ")
        people[i]["submitdate"] = (begun + dt.timedelta(seconds=seconds)).isoformat(sep=" ")
    for n, person in enumerate(people, start=1):
        person["id"] = n
    return people


# The variables in the order of the exports, LimeSurvey's names.
def variables() -> list[str]:
    names = ["id", "submitdate", "startdate", "consent", "age", "enfants", "nbenfants", "emploi"]
    names += [f"transport_SQ{k:03d}" for k in (1, 2, 3)] + ["transport_other"]
    names += [f"climat_SQ{k:03d}" for k in range(1, 8)] + ["nuit"]
    names += [f"bienetre_SQ{k:03d}" for k in range(1, 9)] + ["controle", "commentaires"]
    return names + [code for code, _t in HABITS]


DATES = ("submitdate", "startdate")
TEXTS = {"transport_SQ001", "transport_SQ002", "transport_SQ003", "transport_other", "commentaires"}


# --- When each variable is asked, said here in plain Python (the answer key). ---


def _asked(person: dict, name: str) -> bool | None:
    """None: always asked (a platform's variable, the consent)."""
    consent = person.get("consent") == 1
    if name in ("id", "submitdate", "startdate", "consent"):
        return None
    if name == "nbenfants":
        return consent and person.get("enfants") == 1
    if name.startswith("climat_"):
        return consent and person.get("emploi") in (1, 2)
    if name == "nuit":
        return consent and person.get("emploi") == 1 and person.get("age", 0) >= 18
    return consent


def answer_key(people: list[dict]) -> dict:
    boxes = [f"transport_SQ{k:03d}" for k in (1, 2, 3)]
    found = {}
    for name in variables():
        counts = {"asked": 0, "not_applicable": 0, "missing": 0, "anomalies": 0}
        if _asked(people[0], name) is None:
            continue
        for person in people:
            asked = _asked(person, name)
            if name in boxes:
                present = person.get(name) is not None
                answered = any(person.get(b) is not None for b in boxes)
            else:
                present = answered = person.get(name) is not None
            if asked:
                counts["asked"] += 1
                counts["missing"] += not answered
            elif present:
                counts["anomalies"] += 1
            else:
                counts["not_applicable"] += 1
        found[name] = counts
    consenting = [p for p in people if p["consent"] == 1]
    first = [
        p
        for p in consenting
        if p.get("emploi") in (1, 2) and p.get("climat_SQ007") not in (None, 4)
    ]
    second = [p for p in consenting if p.get("controle") not in (None, 1)]
    both = [p for p in first if p.get("controle") not in (None, 1)]

    def seconds(person):
        return (dt.datetime.fromisoformat(person["submitdate"])
                - dt.datetime.fromisoformat(person["startdate"])).total_seconds()  # fmt: skip

    return {
        "n": len(people),
        "variables": found,
        "attention": {
            "climat_SQ007_failed": len(first),
            "controle_failed": len(second),
            "both_failed": len(both),
            "controle_empty": sum(p.get("controle") is None for p in consenting),
        },
        "quick": sum(seconds(p) < 120 for p in people),
        "climat_fewer_than_5": sum(
            1
            for p in people
            if p.get("consent") == 1
            and p.get("emploi") in (1, 2)
            and sum(p.get(f"climat_SQ{k:03d}") is not None for k in range(1, 7)) < 5
        ),
        # Table 1 (v0.21, step 9): whom a filtered question was asked, who answered it.
        "table1": {
            "nuit": {
                "asked": sum(_asked(p, "nuit") for p in people),
                "counts": {
                    str(code): sum(p.get("nuit") == code for p in people) for code in (1, 2)
                },
            },
            "nbenfants": {
                "asked": sum(bool(_asked(p, "nbenfants")) for p in people),
                "unanswered": sum(
                    bool(_asked(p, "nbenfants")) and p.get("nbenfants") is None for p in people
                ),
            },
        },
        # A rule "nbenfants is missing": the asked who left it empty, never the not asked.
        "nbenfants_missing": sum(
            bool(_asked(p, "nbenfants")) and p.get("nbenfants") is None for p in people
        ),
        "surveymonkey": surveymonkey_names(),
    }


# --- The exports. ---


def _labels(found: Project) -> tuple[dict, dict]:
    """The labels of the .sav, as LimeSurvey 7.6 writes them: "[item] question" for an item;
    value labels from the choices."""
    labels = {"id": "ID de la réponse", "submitdate": "Date de soumission",
              "startdate": "Date de lancement"}  # fmt: skip
    values: dict[str, dict] = {}
    for question in found.questionnaire.questions:
        code = design.code(found, question)
        choices = {
            float(o.code): o.text
            for o in question.options
            if o.code and o.code.isdigit() and not o.other
        }
        if question.kind == "grid":
            for row in question.rows:
                labels[f"{code}_{row.code}"] = f"[{row.text}] {question.text}"
                values[f"{code}_{row.code}"] = choices
        elif question.kind == "checkbox":
            for option in question.options:
                name = f"{code}_{'other' if option.other else option.code}"
                labels[name] = f"[{option.text}] {question.text}"
                if not option.other:
                    values[name] = {"Y": "Oui"}
        else:
            labels[code] = question.text
            if question.kind == "single":
                values[code] = choices
    return labels, values


def _seconds(value: str) -> float:
    return (dt.datetime.fromisoformat(value) - SPSS_ZERO).total_seconds()


def write_sav(people: list[dict], path: Path, names: dict[str, str] | None = None) -> None:
    """LimeSurvey's .sav (its names), or SurveyMonkey's (`names`: LimeSurvey's -> its own)."""
    found = project()
    labels, values = _labels(found)
    data, formats = {}, {}
    for name in variables():
        column = [p.get(name) for p in people]
        if name in DATES:
            data[name] = [_seconds(v) for v in column]
            formats[name] = "DATETIME20"
        elif name in TEXTS:
            data[name] = ["" if v is None else v for v in column]
            formats[name] = f"A{max(1, max(len(str(v)) for v in data[name]))}"
        else:
            data[name] = [float("nan") if v is None else float(v) for v in column]
            formats[name] = "F3.0"
    meta = {
        "column_labels": labels,
        "variable_value_labels": values,
        "variable_format": formats,
        "missing_ranges": {"enfants": [9.0]},
    }
    frame = pd.DataFrame(data)
    if names is not None:  # SurveyMonkey: its names; a ticked box is 1; no missing declared
        frame = frame.rename(columns=names)
        for old in ("transport_SQ001", "transport_SQ002", "transport_SQ003"):
            frame[names[old]] = [1.0 if v == "Y" else float("nan") for v in frame[names[old]]]
            formats[old] = "F8.2"
            values[old] = {1.0: labels[old].split("]")[0][1:]}
        meta = {
            "column_labels": {names[k]: v for k, v in labels.items() if k in names},
            "variable_value_labels": {names[k]: v for k, v in values.items() if k in names},
            "variable_format": {names[k]: v for k, v in formats.items()},
        }
    common.write_sav(frame, meta, path)


def write_csv(people: list[dict], path: Path) -> None:
    """LimeSurvey's CSV with codes: its names with brackets, every cell between quotes."""

    def header(name: str) -> str:
        stem, _sep, item = name.partition("_")
        return f"{stem}[{item}]" if item and name not in DATES else name

    def cell(value) -> str:
        return "" if value is None else '"' + str(value).replace('"', '""') + '"'

    lines = [",".join(f'"{header(n)}"' for n in variables())]
    lines += [",".join(cell(p.get(n)) for n in variables()) for p in people]
    path.write_bytes(("﻿" + "\r\n".join(lines) + "\r\n").encode("utf-8"))


def surveymonkey_names() -> dict[str, str]:
    """LimeSurvey's names -> SurveyMonkey's: platform variables, then questions by rank."""
    found = {"id": "respondent_id", "startdate": "date_created", "submitdate": "date_modified"}
    rank = 0
    current = None
    for name in variables():
        if name in found:
            continue
        stem, _sep, item = name.partition("_")
        if stem != current:
            rank, current, sub = rank + 1, stem, 0
        if item and item != "other":
            sub += 1
            found[name] = f"q{rank:04d}_{sub:04d}"
        elif item == "other":
            found[name] = f"q{rank:04d}_other"
        else:
            found[name] = f"q{rank:04d}"
    return found


def write_all(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    people = _people()
    designed = project()
    written = []  # the project itself is built by `project()`: a .dd.json stays off the repo
    path = folder / f"questionnaire-{STEM}.txt"
    path.write_text(design_limesurvey.text(designed), encoding="utf-8", newline="\n")
    written.append(path)
    for suffix, write in ((".sav", write_sav), (".csv", write_csv)):
        path = folder / f"reponses-{STEM}{suffix}"
        write(people, path)
        written.append(path)
    path = folder / f"reponses-{STEM}-surveymonkey.sav"
    write_sav(people, path, surveymonkey_names())
    written.append(path)
    path = folder / f"corrige-{STEM}.json"
    text = json.dumps(answer_key(people), ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
    written.append(path)
    return written


if __name__ == "__main__":
    for written in write_all(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT):
        print(written)
