"""The two reviewed fictional projects of the analysis context (v0.8, step 6): the decisions
a team would have taken, as in the examples validated at step 1. The context they give is
`docs/exemples-contexte/`; regenerate with DDICT_REGENERATE=1 after a wanted change."""

import json
from pathlib import Path

from ddict import naming
from ddict.io import read_database
from ddict.project import build_project
from ddict.project.model import SentinelDecision, TrackedValue
from ddict.questionnaire import link
from ddict.review import levels, study
from ddict.workflow import add_questionnaire

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
OUTPUT = ROOT / "docs" / "exemples-contexte"
NOW = "2026-10-15T12:00:00"
SOURCE = "Manuel fictif de l'échelle de sommeil, p. 4 (référence inventée pour l'exemple)"


def _accept(value: str) -> TrackedValue[str]:
    return TrackedValue[str](value=value, origin="human", updated_at=NOW)


def _accept_levels(project) -> None:
    waiting = {e.name: "accept" for e in project.variables if e.measure_level.status == "proposed"}
    levels.apply_table(project, {}, waiting, now=NOW)


def sleep_study():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    add_questionnaire(project, EXAMPLES / "questionnaire-sommeil.pdf")
    key = json.loads((EXAMPLES / "corrige-banc.json").read_text(encoding="utf-8"))
    links = next(b for b in key["bases"] if b["name"] == "etude-sommeil")["links"]
    for name, target in links.items():
        project.variable(name).question = _accept(link.NO_QUESTION if target == "none" else target)
    for name, code in [("age", 999), ("sommeil_q3", 9), ("nb_reveils", -9)]:
        project.variable(name).sentinel_decisions = [
            SentinelDecision(code=code, missing=True, updated_at=NOW)
        ]
    project.groups[0].reverse_items = ["sommeil_q3", "sommeil_q6"]
    items = [f"sommeil_q{i}" for i in range(1, 9)]
    study.set_scoring(project, "G1", items, "sum", 1.0, 5.0, 7, "sommeil_total", SOURCE, "")
    study.set_dataset(project, "participant", "", "cross_sectional", "", "", {},
                      "Étude fictive sur le sommeil, une seule passation.", now=NOW)  # fmt: skip
    _accept_levels(project)
    return project


def survey_wave_2():
    key = json.loads((EXAMPLES / "corrige-surveymonkey.json").read_text(encoding="utf-8"))
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    add_questionnaire(project, EXAMPLES / "travail-t2_surveymonkey.xlsx")
    for name, target in link.sure_choices(project).items():
        project.variable(name).question = _accept(target)
    satisfaction = next(g for g in project.groups if g.group_id == "G2")
    for name in satisfaction.members.value:
        project.variable(name).sentinel_decisions = [
            SentinelDecision(code=6, missing=True, updated_at=NOW),
            SentinelDecision(code=7, missing=True, updated_at=NOW),
        ]
    _accept_levels(project)  # by original names, before renaming
    naming.set_wave(project, "t2")
    for name, value in key["waves"]["t2"]["names"].items():
        project.variable(name).new_name = _accept(value)
    study.set_dataset(project, "participant", "", "one_wave_per_file", "t2", "",
                      {"cluster_id": "q0012"}, "Enquête fictive sur le travail, deuxième vague.",
                      now=NOW)  # fmt: skip
    return project


PROJECTS = {"etude-sommeil": sleep_study, "travail-t2_surveymonkey": survey_wave_2}
