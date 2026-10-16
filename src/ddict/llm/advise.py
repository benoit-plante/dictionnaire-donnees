"""The local model proposes analyses of the catalogue for an objective (v0.9, step 7, D-073,
D-079).

The model reads the objective written by the team, the catalogue (keys, purposes, roles and
the measure levels they take, methods) and the variables an analysis may use (final name,
label, measure level, group): metadata only, never a value nor a statistic. Identifiers,
free texts and dates are left out, as the analyses leave them out.

The answer is one to three proposals, each an analysis of the catalogue with variables of
the project, a method of that analysis and a short reason; the schema allows nothing else
(no code, no threshold, no reference). An unknown analysis, role, variable or method refuses
the answer. The codebook's conditions are checked on each proposal, and a person confirms,
changes or rejects it: nothing is computed without them. Proposals stay in memory; the
exchange is kept next to the project (D-079).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from ddict import i18n
from ddict.analysis import conditions
from ddict.analysis.catalogue import CATALOGUE, CHOICES, PURPOSES
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.llm.messages import Block, recorded_version, system_prompt
from ddict.llm.validate import InvalidResponse
from ddict.project.model import Project

if TYPE_CHECKING:
    from ddict.llm.client import LocalModelClient
    from ddict.llm.run import BlockResult

ADVICE_PROMPT_VERSION = "advise-v2"
BLOCK_ID = "a-001"
MAX_OBJECTIVE_CHARS = 1000
MAX_PROPOSALS = 3
MAX_REASON_CHARS = 400
MAX_LABEL_CHARS = 60
MIN_COMMON_CHARS = 15  # a shorter common start of the items' labels says nothing
# The local model reads 4,096 tokens by default (Ollama), its answer included: the message
# keeps about 800 for the answer (D-080). Measured with qwen2.5: 3.6 characters per token
# for this message; 3.5 stays cautious.
MAX_MESSAGE_TOKENS = 3300
CHARS_PER_TOKEN = 3.5

AnalysisKey = Literal["table1", "t_test", "anova", "chi_square", "correlation", "regression"]
RoleKey = Literal["variables", "group", "outcome", "rows", "columns", "predictors"]
Method = Literal["", "welch", "student", "mann_whitney", "anova", "kruskal_wallis", "pearson",
                 "fisher", "spearman"]  # fmt: skip
Reason = Annotated[str, StringConstraints(strip_whitespace=True, max_length=MAX_REASON_CHARS)]


class RoleChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: RoleKey
    variables: list[str]


class AdviceProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: AnalysisKey
    roles: list[RoleChoice]
    method: Method
    reason: Reason


class AdviceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: str
    proposals: list[AdviceProposal] = Field(max_length=MAX_PROPOSALS)


class AdviceError(ValueError):
    """The objective cannot be sent; `reason`: "empty", "too_long", or "too_large" when
    the message would not fit in the local model's context."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Proposal:
    """A proposal of the model, checked against the codebook; always to be confirmed."""

    analysis: str
    chosen: dict[str, list[str]]
    options: dict[str, str]
    reason: str
    check: conditions.Check = field(default_factory=conditions.Check)


@dataclass(frozen=True)
class AdviceResult:
    result: BlockResult
    proposals: tuple[Proposal, ...] | None  # None unless the run succeeded


def usable(project: Project) -> dict[str, str]:
    """The variables an analysis may use, by final name, with their measure level."""
    allowed = {
        name
        for analysis in CATALOGUE.values()
        for role in analysis.roles
        for name in conditions.candidates(project, analysis, role.key)
    }
    return {n: lv for n, lv in conditions.levels(project).items() if n in allowed}


def advice_schema(project: Project) -> dict:
    """The schema of the answer; the variables, an enumeration of the project's own."""
    schema = AdviceResponse.model_json_schema()
    names = list(usable(project))
    schema["$defs"]["RoleChoice"]["properties"]["variables"]["items"]["enum"] = names
    return schema


def _members(project: Project) -> dict[str, list[str]]:
    """Group id -> the final names of its members, in the order of the group."""
    names = w.names_of(project)
    return {
        group.group_id: [names[m] for m in group.members.value or [] if m in names]
        for group in project.groups
    }


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_LABEL_CHARS else text[: MAX_LABEL_CHARS - 1] + "…"


def _common_start(labels: list[str]) -> str:
    """What the labels of a group's items begin with, cut at a word: often the question of
    a grid."""
    if len(labels) < 2:
        return ""
    start = labels[0]
    for label in labels[1:]:
        while not label.startswith(start):
            start = start[:-1]
    if start != labels[0] and labels[0][len(start) : len(start) + 1] != " ":
        start = start[: start.rfind(" ")] if " " in start else ""  # not in the middle of a word
    return start.strip(" -:–—?.") if len(start) >= MIN_COMMON_CHARS else ""


def _content(project: Project, objective: str) -> dict:
    """The variables by measure level, each as [name, label]; groups of items as one entry
    each, their items by name only; labels shortened; scores with their group (D-080)."""
    found = usable(project)
    entries = {w.final_name(e): e for e in project.variables}
    scores = {s.name: s.group for s in plan(project)[1]}
    groups, grouped = [], set()
    for group in project.groups:
        items = [n for n in _members(project)[group.group_id] if n in found]
        if len(items) < 2:
            continue
        grouped.update(items)
        labels = [w.label_text(entries[n], "final") for n in items]
        levels = [found[n] for n in items]
        entry = {
            "group": group.group_id,
            "label": _short(_common_start(labels) or w.group_description(group, "final")),
            "level": max(levels, key=levels.count),  # the most frequent, first on a tie
            "items": items,
        }
        score = next((s for s, g in scores.items() if g == group.group_id and s in found), None)
        if score:
            entry["score"] = score
        groups.append(entry)
    variables: dict[str, list[list[str]]] = {}
    for name, level in found.items():
        if name in grouped:
            continue
        if name in scores:
            label = i18n._("{name} (score de {group})").format(name=name, group=scores[name])
        else:
            label = w.label_text(entries[name], "final")
        variables.setdefault(level, []).append([name, _short(label)])
    content = {
        "block": BLOCK_ID,
        "objective": objective,
        "analyses": [_analysis(k) for k in CATALOGUE],
        "variables": variables,
    }
    if groups:
        content["groups"] = groups
    return content


def _analysis(key: str) -> dict:
    analysis = CATALOGUE[key]
    payload = {
        "key": key,
        "purpose": PURPOSES[key],
        "roles": [
            {"role": r.key, "levels": list(r.levels), "min": r.least, "max": r.most}
            for r in analysis.roles
        ],
    }
    if "method" in analysis.options:
        payload["methods"] = list(analysis.options["method"])
    return payload


def estimated_tokens(messages: tuple[dict, ...]) -> int:
    """A cautious estimate of the tokens the model reads."""
    return int(sum(len(m["content"]) for m in messages) / CHARS_PER_TOKEN)


def build_advice_block(project: Project, objective: str) -> Block:
    """The one message of an advice: the objective, the catalogue, the usable variables.
    Refused when it would not fit in the local model's context (D-080)."""
    objective = objective.strip()
    if not objective:
        raise AdviceError("empty")
    if len(objective) > MAX_OBJECTIVE_CHARS:
        raise AdviceError("too_long")
    language = project.settings.language
    with i18n.using(language):
        content = _content(project, objective)
    system = system_prompt(ADVICE_PROMPT_VERSION, language)
    text = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    messages = ({"role": "system", "content": system}, {"role": "user", "content": text})
    if estimated_tokens(messages) > MAX_MESSAGE_TOKENS:
        raise AdviceError("too_large")
    return Block(
        block_id=BLOCK_ID,
        names=tuple(usable(project)),
        messages=messages,
        prompt_version=recorded_version(ADVICE_PROMPT_VERSION, language),
    )


def parse_advice(content: str, block: Block) -> tuple[AdviceProposal, ...]:
    """Valid JSON, exactly the schema, and only analyses, roles, variables and methods of
    the catalogue and of the block."""
    if not content.strip():
        raise InvalidResponse("empty_response", "Empty answer")
    try:
        response = AdviceResponse.model_validate(json.loads(content))
    except json.JSONDecodeError as error:
        raise InvalidResponse("not_json", f"Not JSON: {error}") from error
    except ValidationError as error:
        raise InvalidResponse("schema", f"Does not match the schema: {error}") from error
    if response.block != block.block_id:
        raise InvalidResponse("block_mismatch", f"Answer for {response.block!r}")
    known = set(block.names)
    for proposal in response.proposals:
        analysis = CATALOGUE[proposal.analysis]
        roles = {r.key for r in analysis.roles}
        for choice in proposal.roles:
            if choice.role not in roles:
                raise InvalidResponse(
                    "unknown_role", f"{proposal.analysis} has no role {choice.role!r}"
                )
            unknown = [n for n in choice.variables if n not in known]
            if unknown:
                raise InvalidResponse("unknown_variable", f"Variables not offered: {unknown}")
        if proposal.method and proposal.method not in analysis.options.get("method", ()):
            raise InvalidResponse(
                "unknown_method", f"{proposal.analysis} has no method {proposal.method!r}"
            )
    return tuple(response.proposals)


def checked(project: Project, proposal: AdviceProposal) -> Proposal:
    """A proposal as the page and the command use it, with the codebook's conditions."""
    chosen: dict[str, list[str]] = {}
    for choice in proposal.roles:
        for name in choice.variables:
            if name not in chosen.setdefault(choice.role, []):
                chosen[choice.role].append(name)
    options = {"method": proposal.method} if proposal.method else {}
    found = conditions.check(project, proposal.analysis, chosen, options)
    return Proposal(proposal.analysis, chosen, options, proposal.reason, found)


def run_id(now: str) -> str:
    """ "conseil-20261016-142501": advice is not recorded in the project (D-079)."""
    return "conseil-" + now.replace("-", "").replace(":", "").replace("T", "-")[:15]


def advise(
    project: Project,
    client: LocalModelClient,
    objective: str,
    *,
    now: str,
    log_dir: Path | None = None,
) -> AdviceResult:
    """Ask the model for proposals; the exchange is kept in `log_dir` (D-079)."""
    from ddict.llm.enrich import _log  # needs httpx, an optional dependency
    from ddict.llm.run import run_block

    block = build_advice_block(project, objective)
    result = run_block(
        client,
        block,
        run_id=run_id(now),
        now=now,
        schema=advice_schema(project),
        parse=parse_advice,
    )
    if log_dir is not None:
        _log(log_dir, block, result)
    if result.proposals is None:
        return AdviceResult(result, None)
    return AdviceResult(result, tuple(checked(project, p) for p in result.proposals))


def method_text(proposal: Proposal) -> str:
    """The method as the interface shows it, or "" for the default one."""
    method = proposal.options.get("method")
    return CHOICES[method] if method else ""
