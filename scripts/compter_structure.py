"""Count what the tool finds in a survey platform export, as numbers only (v0.7, D-046).

For the real exports kept outside the repository: every result is a count or a rate, never
a value, a label, a question text nor a file name, so that it can be shown, kept in a trial
report or compared by a test without revealing anything. An error is reported by its type
only, since its message could quote the data.

The expected structure comes from the names alone (SurveyMonkey's `q0003_0004`), read
independently of the tool, so that the counts measure the tool against it.

A base is a folder holding one `.sav` file and, optionally, the `.xlsx` export of the same
survey and its questionnaire (`.pdf`, `.txt`). With a folder of folders, each subfolder is a
base, named `base1`, `base2`, ... in alphabetical order.

Usage (from the repository root):
    uv run python scripts/compter_structure.py <folder>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from ddict.io import read_database
from ddict.project import build_project
from ddict.questionnaire import link, load_questionnaire, read_questionnaire
from ddict.workflow import add_questionnaire

NUMBERED_LINE = re.compile(r"\s*(?:Q\s?)?\d{1,3}\s?[.)]\s", re.IGNORECASE)
ITEM_NAME = re.compile(r"q(\d{4})(?:_(\d{4}|other))?", re.IGNORECASE)
PLATFORM_NAMES = {
    "collectornm",
    "respondentid",
    "collectorid",
    "startdate",
    "enddate",
    "ipaddress",
    "emailaddress",
    "firstname",
    "lastname",
    "customdata1",
    "respondent_id",
    "collector_id",
    "date_created",
    "date_modified",
    "ip_address",
    "email_address",
    "first_name",
    "last_name",
    "custom_1",
}
DATE_NAMES = {"startdate", "enddate", "date_created", "date_modified"}
DATE_FORMATS = (
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%Y-%m-%d",
)
MAX_MISSING_LABEL_WORDS = 6
# A label that is a non-answer as a whole: short, and starting with one of these.
MISSING_LABEL = re.compile(
    r"\s*((je )?ne (le )?sai[st] pas|nsp|pr[ée]f[èe]re ne pas|refus|sans objet"
    r"|ne s'applique pas|(i )?don'?t know|prefer not|refused|not applicable|n/?a)(\W|$)",
    re.IGNORECASE,
)


def _structure(variables) -> dict[str, dict[int, list]]:
    """Grids, checkbox sets and single questions, by question rank, from names and labels."""
    by_question: dict[int, list] = defaultdict(list)
    for variable in variables:
        match = ITEM_NAME.fullmatch(variable.name)
        if match:
            by_question[int(match.group(1))].append((variable, match.group(2)))
    kinds: dict[str, dict[int, list]] = {"grid": {}, "checkbox": {}, "single": {}}
    for rank, members in by_question.items():
        items = [v for v, part in members if part and part.lower() != "other"]
        if not items:
            kinds["single"][rank] = [v for v, _part in members]
        elif all(len(v.value_labels) == 1 for v in items):
            kinds["checkbox"][rank] = items
        else:
            kinds["grid"][rank] = items
    return kinds


def _date_rate(column: pd.Series) -> tuple[float, int | None]:
    """The share of values read by the best of DATE_FORMATS, and that format's rank (a
    pattern, not a value)."""
    texts = [str(v).strip() for v in column if isinstance(v, str) and str(v).strip()]
    if not texts:
        return 100.0, None
    best, rank = 0, None
    for number, fmt in enumerate(DATE_FORMATS):
        parsed = pd.to_datetime(pd.Series(texts), format=fmt, errors="coerce")
        if int(parsed.notna().sum()) > best:
            best, rank = int(parsed.notna().sum()), number
    return round(100 * best / len(texts), 1), rank


def count_database(sav: Path) -> dict[str, float | int]:
    data = read_database(sav)
    project = build_project(data)
    kinds = _structure(data.variables)
    by_name = {e.name: e for e in project.variables}
    counts: dict[str, float | int] = {
        "variables": len(data.variables),
        "lignes": data.source.n_rows,
        "variables_plateforme": sum(v.name.lower() in PLATFORM_NAMES for v in data.variables),
        "plateforme_reconnue": int(getattr(project.source, "platform", None) is not None),
        "questions_plateforme": len({r for k in kinds.values() for r in k}),
        "grilles": len(kinds["grid"]),
        "ensembles_a_cocher": len(kinds["checkbox"]),
        "questions_simples": len(kinds["single"]),
        "groupes": len(project.groups),
    }

    group_of = {m: g.group_id for g in project.groups for m in (g.members.value or [])}
    ranks = {}
    for variable in data.variables:
        match = ITEM_NAME.fullmatch(variable.name)
        if match:
            ranks[variable.name] = int(match.group(1))
    counts["groupes_melant_des_questions"] = sum(
        len({ranks.get(m) for m in (g.members.value or [])}) > 1 for g in project.groups
    )
    whole = split = 0
    for items in kinds["grid"].values():
        groups = {group_of.get(v.name) for v in items}
        whole += groups == {group_of.get(items[0].name)} and None not in groups
        split += len(groups - {None}) > 1
    counts["grilles_entieres"] = whole
    counts["grilles_coupees"] = split
    counts["ensembles_a_cocher_groupes"] = sum(
        {group_of.get(v.name) for v in items} == {group_of.get(items[0].name)}
        and group_of.get(items[0].name) is not None
        and next(g for g in project.groups if g.group_id == group_of[items[0].name]).kind
        == "multiple_response"
        for items in kinds["checkbox"].values()
    )

    grid_items = [v.name for items in kinds["grid"].values() for v in items]
    counts["items_de_grille_identifiant_probable"] = sum(
        by_name[n].privacy.privacy_class.value == "likely_identifier" for n in grid_items
    )
    scale_items = [n for n in grid_items if by_name[n].file.measure_level == "scale"]
    counts["items_de_grille_niveau_scale"] = len(scale_items)
    counts["items_niveau_scale_signales"] = sum(
        "measure_level_doubtful" in by_name[n].profile.flags for n in scale_items
    )

    dates = [v.name for v in data.variables if v.name.lower() in DATE_NAMES]
    counts["dates_de_passation"] = len(dates)
    counts["dates_lues_comme_dates"] = sum(
        by_name[n].profile.inferred_type in ("date", "datetime") for n in dates
    )
    counts["dates_classees_texte_libre"] = sum(
        by_name[n].privacy.privacy_class.value == "free_text" for n in dates
    )
    rates = [_date_rate(data.table[n]) for n in dates]
    counts["taux_min_valeurs_de_date_lisibles_pct"] = min((r for r, _f in rates), default=100.0)
    formats = {f for _r, f in rates if f is not None}
    counts["format_des_dates"] = (
        DATE_FORMATS[formats.pop()] if len(formats) == 1 else f"{len(formats)} formats"
    )

    # Codes chosen by at least one person: a code never observed is not a suspect value.
    labelled_missing = [
        (v.name, code)
        for v in data.variables
        for code, label in v.value_labels.items()
        if MISSING_LABEL.match(str(label))
        and len(str(label).split()) <= MAX_MISSING_LABEL_WORDS
        and code in {o.code for o in by_name[v.name].profile.observed_values or []}
    ]
    counts["codes_a_etiquette_de_manquant"] = len(labelled_missing)
    counts["codes_a_etiquette_de_manquant_signales"] = sum(
        code in by_name[name].profile.suspect_missing_codes for name, code in labelled_missing
    )
    return counts


def count_questionnaire(path: Path, prefix: str) -> dict[str, int]:
    lines = read_questionnaire(path).lines
    numbered = sum(bool(NUMBERED_LINE.match(line.text)) for line in lines)
    questionnaire = load_questionnaire(path)
    kinds = Counter(q.kind for q in questionnaire.questions)
    return {
        f"{prefix}_questions": len(questionnaire.questions),
        **{f"{prefix}_{kind}": kinds.get(kind, 0) for kind in ("open", "single", "checkbox")},
        f"{prefix}_grilles": kinds.get("grid", 0),
        f"{prefix}_enonces_de_grille": sum(len(q.rows) for q in questionnaire.questions),
        f"{prefix}_a_verifier": sum(bool(q.to_check) for q in questionnaire.questions),
        f"{prefix}_lignes_lues": len(lines),
        f"{prefix}_lignes_numerotees": numbered,
    }


def count_links(sav: Path, questionnaire: Path, prefix: str) -> dict[str, int]:
    """Links given by the structure of the export, the questionnaire being `questionnaire`;
    and, of these, how many point to a row or option whose text agrees with the variable's
    label (a check: they all should)."""
    project = build_project(read_database(sav))
    add_questionnaire(project, questionnaire)
    platform = link.platforms.by_name(project.source.platform)
    choices = link.platform_choices(project)
    questions = {name: target for name, target in choices.items() if target != link.NO_QUESTION}
    agreeing = 0
    for name, target_id in questions.items():
        found = link.target(project.questionnaire, target_id)
        entry = project.variable(name)
        texts = [entry.file.label, *(v.label for v in entry.file.value_labels)]
        if platform.place(name).other:  # an "other" option, in any language
            texts = list(platform.other_cells)
        if any(link.texts_agree(t, found.part or found.question.text) for t in texts):
            agreeing += 1
    in_questions = [e.name for e in project.variables if platform and platform.place(e.name)]
    asked, unmatched = link.platform_coverage(project)
    checks = Counter(c for q in project.questionnaire.questions for c in q.to_check)
    return {
        f"{prefix}_questions_de_la_base": asked,
        f"{prefix}_questions_de_la_base_sans_concordance": unmatched,
        **{f"{prefix}_a_verifier_{code}": checks.get(code, 0) for code in link.PLATFORM_CHECKS},
        f"{prefix}_variables_de_questions": len(in_questions),
        f"{prefix}_liens_par_la_structure": len(questions),
        f"{prefix}_liens_dont_le_texte_concorde": agreeing,
    }


def count_excel(xlsx: Path, sav_rows: int, sav_names: set[str]) -> dict[str, int]:
    data = read_database(xlsx)
    names = [v.name for v in data.variables]
    return {
        "xlsx_lignes_en_trop": data.source.n_rows - sav_rows,
        "xlsx_colonnes_sans_nom": sum(n.startswith("colonne_") for n in names),
        "xlsx_noms_absents_du_sav": sum(n not in sav_names for n in names),
    }


def _guarded(counts: dict, step: str, function, *args) -> None:
    try:
        counts.update(function(*args))
    except Exception as error:  # only the type: a message could quote the data
        counts[f"erreur_{step}"] = type(error).__name__


def main_database(folder: Path) -> Path | None:
    """The .sav of a base: the one with an Excel export of the same name, else the last by
    name (a folder may hold an earlier wave too)."""
    savs = sorted(folder.glob("*.sav"))
    paired = [s for s in savs if s.with_suffix(".xlsx").is_file()]
    return (paired or savs or [None])[-1]


def _coverage(sav: Path, questionnaire: Path) -> tuple[int, int]:
    """How well a questionnaire fits a base: (questions of the base without a match,
    minus structural links), lower is better."""
    project = build_project(read_database(sav))
    add_questionnaire(project, questionnaire)
    _asked, unmatched = link.platform_coverage(project)
    return unmatched, -len(link.platform_choices(project))


def questionnaire_of(sav: Path, paths: list[Path]) -> Path | None:
    """The questionnaire that fits the base best, among several (one per wave)."""
    if len(paths) <= 1:
        return paths[0] if paths else None
    scored = []
    for path in paths:
        try:
            scored.append((_coverage(sav, path), path))
        except Exception:  # an unreadable file fits nothing
            continue
    return min(scored)[1] if scored else None


def count_context(sav: Path) -> dict[str, float]:
    """The size of the analysis context of the base as read (v0.8, step 6): tokens per
    variable (about four characters a token), without the text of the questions."""
    from ddict.export.context import render_context

    project = build_project(read_database(sav))
    text = render_context(project)
    kept = text.split("\n## Texte des questions")[0]
    return {"contexte_tokens_par_variable": round(len(kept) / 4 / len(project.variables), 1)}


def count_base(folder: Path) -> dict[str, float | int | str]:
    """All the counts of one base: its .sav, its Excel export, its questionnaires."""
    counts: dict[str, float | int | str] = {}
    sav = main_database(folder)
    if sav is None:
        return {"erreur": "aucun_fichier_sav"}
    counts["fichiers_sav"] = len(list(folder.glob("*.sav")))
    _guarded(counts, "sav", count_database, sav)
    xlsx = sav.with_suffix(".xlsx")
    if not xlsx.is_file():
        xlsx = next(iter(sorted(folder.glob("*.xlsx"))), None)
    if xlsx is not None:
        try:
            sav_names = {v.name for v in read_database(sav).variables}
        except Exception as error:
            counts["erreur_xlsx"] = type(error).__name__
        else:
            _guarded(counts, "xlsx", count_excel, xlsx, counts.get("lignes", 0), sav_names)
        _guarded(counts, "liens_xlsx", count_links, sav, xlsx, "entete")
    for suffix in ("pdf", "txt"):
        path = questionnaire_of(sav, sorted(folder.glob(f"*.{suffix}")))
        if path is not None:
            _guarded(counts, suffix, count_questionnaire, path, suffix)
            _guarded(counts, f"liens_{suffix}", count_links, sav, path, suffix)
    _guarded(counts, "contexte", count_context, sav)
    if counts["fichiers_sav"] > 1:  # several waves of the study
        _guarded(counts, "vagues", count_waves, folder)
    return counts


def bases(folder: Path) -> dict[str, Path]:
    """The bases of a folder: itself, or its subfolders as base1, base2, ..."""
    if any(folder.glob("*.sav")):
        return {"base1": folder}
    subfolders = sorted(p for p in folder.iterdir() if p.is_dir())
    return {f"base{n}": path for n, path in enumerate(subfolders, start=1)}


def _named_wave(sav: Path, mark: str, path: Path, reference: Path | None):
    """A wave named as a team would: the names of the earlier wave taken, a prefix given to
    every other grid, everything proposed accepted; saved in `path` (a temporary folder)."""
    from ddict import naming, waves

    now = "2026-01-01T00:00:00"
    project = build_project(read_database(sav))
    naming.set_wave(project, mark)
    report = None
    if reference is not None:
        earlier = waves.read_earlier_wave(reference)
        report = waves.match(project, earlier)
        waves.apply(project, earlier, report)
    for group in project.groups:
        if group.kind == "scale" and not group.name_prefix.value:
            prefix = f"g{group.members.value[0][1:5].lstrip('0')}"
            naming.set_prefix(project, group.group_id, prefix, now=now)
        elif group.name_prefix.status == "proposed":
            group.name_prefix = group.name_prefix.model_copy(update={"status": "validated"})
    naming.propose(project)
    for entry in project.variables:
        if entry.new_name.status == "proposed":
            naming.decide(project, entry.name, "accept", now=now)
    from ddict.project import save_project

    save_project(project, path)
    return project, report


def count_waves(folder: Path) -> dict[str, int]:
    """A folder with several waves (`.sav` files, in name order): each wave named, the next
    one taking its names. Counts only: matches, added, removed, to decide, and checks that
    a team would expect (a match between an item and a whole question; an item whose words
    agree with an earlier one but left unmatched)."""
    import tempfile

    from ddict import waves
    from ddict.platforms import SURVEYMONKEY

    savs = sorted(folder.glob("*.sav"))
    counts: dict[str, int] = {"vagues": len(savs)}
    with tempfile.TemporaryDirectory() as temporary:
        previous = None
        for number, sav in enumerate(savs, start=1):
            path = Path(temporary) / f"vague{number}.dd.json"
            project, report = _named_wave(sav, f"t{number}", path, previous)
            if report is not None:
                prefix = f"vagues_{number - 1}_{number}"
                earlier = read_database(savs[number - 2])
                labels = [v.label for v in earlier.variables if SURVEYMONKEY.place(v.name)]
                agreeing = {
                    e.name
                    for e in project.variables
                    if SURVEYMONKEY.place(e.name)
                    and any(link.texts_agree(e.file.label, label) for label in labels)
                }
                matched = {m.variable for m in report.matches}
                by_name = {v.name: v for v in waves.read_earlier_wave(previous).variables}
                # An earlier variable goes to one variable only: words repeated in this wave
                # (the same item twice) leave the second one unmatched, rightly.
                free = [
                    w.label
                    for w in by_name.values()
                    if w.name not in {m.earlier for m in report.matches}
                    and SURVEYMONKEY.place(w.original or "")
                ]
                left = {
                    name
                    for name in agreeing - matched
                    if any(link.texts_agree(project.variable(name).file.label, f) for f in free)
                }
                kinds = 0
                for match in report.matches:
                    now_place = SURVEYMONKEY.place(match.variable)
                    old_place = SURVEYMONKEY.place(by_name[match.earlier].original or "")
                    if (
                        now_place
                        and old_place
                        and (
                            (now_place.item is None) != (old_place.item is None)
                            or now_place.other != old_place.other
                        )
                    ):
                        kinds += 1
                counts |= {
                    f"{prefix}_appariees": len(report.matches),
                    f"{prefix}_ajoutees": len(report.added),
                    f"{prefix}_a_departager": len(report.candidates),
                    f"{prefix}_retirees": len(report.removed),
                    f"{prefix}_etiquettes_de_valeurs_changees": len(report.value_labels_changed),
                    f"{prefix}_mots_concordants": len(agreeing),
                    f"{prefix}_mots_concordants_deja_pris": len(agreeing - matched - left),
                    f"{prefix}_mots_concordants_non_apparies": len(left),
                    f"{prefix}_natures_differentes": kinds,
                }
            previous = path
    return counts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Décompte la structure d'exports de sondage.")
    parser.add_argument("folder", type=Path)
    args = parser.parse_args(argv)
    result = {name: count_base(path) for name, path in bases(args.folder).items()}
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
