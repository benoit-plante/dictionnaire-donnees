"""The bench of the AI's advice (v0.9, step 7): objectives written for the fictional
database of the analyses, each with the analysis and the variables expected
(`objectifs-analyses.json`), and how many proposals are right.

A proposal is right when its analysis is the expected one and every role holds exactly the
expected variables; the rows and columns of a chi-square count as one set, as the variables
of a correlation or of a Table 1. An objective that no analysis of the catalogue answers
expects no proposal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ddict.io import read_database
from ddict.llm.advise import Proposal, advise
from ddict.project import build_project
from ddict.project.model import Project
from ddict.review import study

if TYPE_CHECKING:
    from ddict.llm.client import ModelClient

OBJECTIVES_FILE = "objectifs-analyses.json"
KEY_FILE = "corrige-analyses.json"
SOURCE = "Corrigé de la base fictive des analyses (exemple inventé)"


FOLLOW_UP_FILE = "objectifs-suivi.json"  # v0.14 (D-115): the widened catalogue


def load_objectives(folder: Path, name: str = OBJECTIVES_FILE) -> dict:
    return json.loads((folder / name).read_text(encoding="utf-8"))


def bench_project(folder: Path, sav: str | None = None) -> Project:
    """The fictional database of the analyses, its scale scored as the answer key says; or,
    for another base of the objectives (the follow-up base, v0.14), that base as read."""
    key = json.loads((folder / KEY_FILE).read_text(encoding="utf-8"))
    if sav is not None and sav != key["sav"]:
        return build_project(read_database(folder / sav))
    project = build_project(read_database(folder / key["sav"]))
    scoring = key["scoring"]
    group = next(g for g in project.groups if "bienetre_1" in (g.members.value or []))
    group.reverse_items = scoring["reverse_items"]
    study.set_scoring(project, group.group_id, scoring["group_items"], "sum", 1.0, 5.0,
                      scoring["min_items_answered"], scoring["score_name"], SOURCE, "")  # fmt: skip
    return project


def _sets(analysis: str, roles: dict[str, list[str]]) -> dict[str, frozenset]:
    found = {role: frozenset(names) for role, names in roles.items() if names}
    if analysis == "chi_square":  # the key writes "variables"; a proposal, rows and columns
        both = roles.get("variables", []) + roles.get("rows", []) + roles.get("columns", [])
        found = {"variables": frozenset(both)}
    return found


def is_right(expected: dict, proposal: Proposal) -> bool:
    return proposal.analysis == expected["analysis"] and _sets(
        proposal.analysis, proposal.chosen
    ) == _sets(expected["analysis"], expected["roles"])


@dataclass(frozen=True)
class Score:
    objective: str
    outcome: str  # "succeeded", "invalid_response", "failed"
    first_analysis: bool  # the first proposal's analysis is the expected one
    first_right: bool  # the first proposal is right, variables included
    any_right: bool  # one of the proposals is right
    method_right: bool | None  # when the expected method matters
    refused_conditions: int  # proposals the codebook's conditions refuse
    seconds: float
    input_tokens: int = 0  # v0.18: what the answer cost
    output_tokens: int = 0


def score(expected: dict | None, proposals: tuple[Proposal, ...] | None) -> dict:
    """How right the proposals are for one objective; an invalid answer (None) never is."""
    if proposals is None:
        method = None if expected is None or "method" not in expected else False
        return {"first_analysis": False, "first_right": False, "any_right": False,
                "method_right": method}  # fmt: skip
    if expected is None:  # no analysis of the catalogue fits: none should be proposed
        right = not proposals
        return {"first_analysis": right, "first_right": right, "any_right": right,
                "method_right": None}  # fmt: skip
    first = proposals[0] if proposals else None
    method = expected.get("method")
    return {
        "first_analysis": first is not None and first.analysis == expected["analysis"],
        "first_right": first is not None and is_right(expected, first),
        "any_right": any(is_right(expected, p) for p in proposals),
        "method_right": None
        if method is None
        else first is not None and first.options.get("method") == method,
    }


def run_advice_bench(
    project: Project,
    client: ModelClient,
    objectives: list[dict],
    *,
    now,
    clock,
    log_dir: Path | None = None,
) -> list[Score]:
    """Ask the model for each objective; `clock()` gives seconds, `now()` the time stamp."""
    scores = []
    for item in objectives:
        start = clock()
        found = advise(project, client, item["objective"], now=now(), log_dir=log_dir)
        refused = sum(1 for p in found.proposals or () if not p.check.ok)
        usage = [call.get("usage") or {} for call in found.result.calls]
        scores.append(
            Score(
                objective=item["id"],
                outcome=found.result.run.outcome,
                refused_conditions=refused,
                seconds=round(clock() - start, 1),
                input_tokens=sum(u.get("input_tokens", 0) for u in usage),
                output_tokens=sum(u.get("output_tokens", 0) for u in usage),
                **score(item["expected"], found.proposals),
            )
        )
    return scores


def summary(scores: list[Score]) -> dict[str, int]:
    return {
        "objectives": len(scores),
        "valid_answers": sum(s.outcome == "succeeded" for s in scores),
        "first_analysis": sum(s.first_analysis for s in scores),
        "first_right": sum(s.first_right for s in scores),
        "any_right": sum(s.any_right for s in scores),
        "refused_conditions": sum(s.refused_conditions for s in scores),
        "input_tokens": sum(s.input_tokens for s in scores),
        "output_tokens": sum(s.output_tokens for s in scores),
    }
