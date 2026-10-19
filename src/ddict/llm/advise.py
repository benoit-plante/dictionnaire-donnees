"""The AI proposes analyses of the catalogue for an objective (v0.9, step 7, D-073,
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
from ddict.analysis.catalogue import CATALOGUE, CHOICES, PURPOSES, Analysis, Role
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.llm.messages import Block, recorded_version, system_prompt
from ddict.llm.validate import InvalidResponse
from ddict.project.model import Project

if TYPE_CHECKING:
    from ddict.llm.client import ModelClient
    from ddict.llm.run import BlockResult

# A local or OpenAI-compatible server: the compact message of D-080, which fits in a small
# context. Anthropic (v0.18): the whole labels, the items with theirs, one bound only.
ADVICE_PROMPT_VERSION = "advise-v2"
ADVICE_API_PROMPT_VERSION = "advise-v3"
MAX_MESSAGE_CHARS = 100_000  # advise-v3: beyond, nothing is sent
BLOCK_ID = "a-001"
MAX_OBJECTIVE_CHARS = 1000
MAX_PROPOSALS = 3
MAX_REASON_CHARS = 400
MAX_LABEL_CHARS = 60
MAX_ROLES = max(len(a.roles) for a in CATALOGUE.values())
MAX_ROLE_VARIABLES = max(r.most for a in CATALOGUE.values() for r in a.roles)
MIN_COMMON_CHARS = 15  # a shorter common start of the items' labels says nothing
# advise-v2 fits in a small context of 4,096 tokens, its answer included (the model on this
# computer of v0.9 to v0.17): the message keeps about 800 for the answer (D-080). Measured:
# 3.6 characters per token for this message; 3.5 stays cautious.
MAX_MESSAGE_TOKENS = 3300
CHARS_PER_TOKEN = 3.5

# The catalogue's keys: the message offers every analysis, a proposal names one of them;
# its roles and methods too, so that a new analysis needs no change here (v0.14).
AnalysisKey = Literal[tuple(CATALOGUE)]  # type: ignore[valid-type]
ROLE_KEYS = tuple(dict.fromkeys(r.key for a in CATALOGUE.values() for r in a.roles))
METHOD_KEYS = tuple(
    dict.fromkeys(m for a in CATALOGUE.values() for m in a.options.get("method", ()))
)
RoleKey = Literal[ROLE_KEYS]  # type: ignore[valid-type]
Method = Literal[("", *METHOD_KEYS)]  # type: ignore[valid-type]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, max_length=MAX_REASON_CHARS)]


class RoleChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: RoleKey
    # Bounded in the schema too: the server's grammar then stops a list that would not end.
    variables: list[str] = Field(min_length=1, max_length=MAX_ROLE_VARIABLES)


class AdviceProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: AnalysisKey
    roles: list[RoleChoice] = Field(min_length=1, max_length=MAX_ROLES)
    method: Method
    reason: Reason


class AdviceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: str
    proposals: list[AdviceProposal] = Field(max_length=MAX_PROPOSALS)


class AdviceError(ValueError):
    """The objective cannot be sent; `reason`: "empty", "too_long", or "too_large" when
    the message would not fit in what the model reads."""

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


def _role_schema(project: Project, analysis: Analysis, role: Role) -> dict | None:
    names = conditions.candidates(project, analysis, role.key)
    if not names:
        return None
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["role", "variables"],
        "properties": {
            "role": {"type": "string", "enum": [role.key]},
            "variables": {
                "type": "array",
                "minItems": 1,
                "maxItems": role.most,
                "items": {"type": "string", "enum": names},
            },
        },
    }


def _proposal_schema(project: Project, analysis: Analysis) -> dict | None:
    """One analysis: its own roles, each with the variables of a fitting level, and its own
    methods. None when a role it needs has no variable."""
    roles = {r.key: _role_schema(project, analysis, r) for r in analysis.roles}
    if any(roles[r.key] is None for r in analysis.roles if r.least):
        return None
    # In the catalogue's order, each once; the required roles first (only Table 1's group
    # is optional, and it comes last).
    allowed = [roles[r.key] for r in analysis.roles if roles[r.key] is not None]
    required = sum(1 for r in analysis.roles if r.least)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["analysis", "roles", "method", "reason"],
        "properties": {
            "analysis": {"type": "string", "enum": [analysis.key]},
            "roles": {
                "type": "array",
                "prefixItems": allowed,
                "minItems": required,
                "maxItems": len(allowed),
            },
            "method": {"type": "string", "enum": ["", *analysis.options.get("method", ())]},
            "reason": {"type": "string", "maxLength": MAX_REASON_CHARS},
        },
    }


def advice_schema(project: Project, *, flat: bool = False) -> dict:
    """The schema sent with the message, stricter than the answer's model: each analysis
    with its own roles and methods, each role with the variables whose level fits it. The
    server's grammar then cannot write a role an analysis lacks, nor an unfit variable.

    `flat` (v0.18, for Anthropic, whose compiled grammar of the strict schema is "too
    large"): one list of the feasible analyses, of the roles, of the methods and of the
    usable variables. `parse_advice` then refuses a role or a method the analysis lacks and
    a variable not offered, and `checked` shows the codebook's conditions (levels, roles
    missing) before a person confirms."""
    proposals = [p for a in CATALOGUE.values() if (p := _proposal_schema(project, a))]
    if flat:
        proposals = [_flat_proposal(project, [p["properties"]["analysis"]["enum"][0]
                                              for p in proposals])]  # fmt: skip
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["block", "proposals"],
        "properties": {
            # The one block id: with many groups (G1, G2…), a model may write a group's.
            "block": {"type": "string", "enum": [BLOCK_ID]},
            "proposals": {
                "type": "array",
                "maxItems": MAX_PROPOSALS,
                "items": proposals[0] if flat else {"anyOf": proposals},
            },
        },
    }


def _flat_proposal(project: Project, analyses: list[str]) -> dict:
    role = {
        "type": "object",
        "additionalProperties": False,
        "required": ["role", "variables"],
        "properties": {
            "role": {"type": "string", "enum": list(ROLE_KEYS)},
            "variables": {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_ROLE_VARIABLES,
                "items": {"type": "string", "enum": list(usable(project))},
            },
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["analysis", "roles", "method", "reason"],
        "properties": {
            "analysis": {"type": "string", "enum": analyses},
            "roles": {"type": "array", "minItems": 1, "maxItems": MAX_ROLES, "items": role},
            "method": {"type": "string", "enum": ["", *METHOD_KEYS]},
            "reason": {"type": "string", "maxLength": MAX_REASON_CHARS},
        },
    }


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


def _content(project: Project, objective: str, whole: bool = False) -> dict:
    """The variables by measure level, each as [name, label]; groups of items as one entry
    each, their items by name only; labels shortened; scores with their group (D-080).

    `whole` (advise-v3, v0.18): labels whole, and each item of a group as [name, label]. A
    group's description never has its range of observed codes (level 1, D-136)."""
    shorten = (lambda text: " ".join(text.split())) if whole else _short
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
        described = _common_start(labels) or w.group_description(group, "final", observed=False)
        entry = {
            "group": group.group_id,
            "label": shorten(described),
            "level": max(levels, key=levels.count),  # the most frequent, first on a tie
            "items": [[n, shorten(t)] for n, t in zip(items, labels, strict=True)]
            if whole
            else items,
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
        variables.setdefault(level, []).append([name, shorten(label)])
    content = {
        "block": BLOCK_ID,
        "objective": objective,
        "analyses": [_analysis(k) for k in CATALOGUE],
        "variables": variables,
    }
    if groups:
        content["groups"] = groups
    content["objective_again"] = objective  # after a long list, the model may lose it
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


def build_advice_block(
    project: Project, objective: str, version: str = ADVICE_PROMPT_VERSION
) -> Block:
    """The one message of an advice: the objective, the catalogue, the usable variables.
    Refused when it would not fit in a small context (advise-v2, D-080), or, with
    advise-v3, beyond MAX_MESSAGE_CHARS."""
    objective = objective.strip()
    if not objective:
        raise AdviceError("empty")
    if len(objective) > MAX_OBJECTIVE_CHARS:
        raise AdviceError("too_long")
    language = project.settings.language
    with i18n.using(language):
        content = _content(project, objective, whole=version == ADVICE_API_PROMPT_VERSION)
    system = system_prompt(version, language)
    text = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    messages = ({"role": "system", "content": system}, {"role": "user", "content": text})
    if version == ADVICE_API_PROMPT_VERSION:
        if sum(len(m["content"]) for m in messages) > MAX_MESSAGE_CHARS:
            raise AdviceError("too_large")
    elif estimated_tokens(messages) > MAX_MESSAGE_TOKENS:
        raise AdviceError("too_large")
    return Block(
        block_id=BLOCK_ID,
        names=tuple(usable(project)),
        messages=messages,
        prompt_version=recorded_version(version, language),
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
    client: ModelClient,
    objective: str,
    *,
    now: str,
    log_dir: Path | None = None,
) -> AdviceResult:
    """Ask the model for proposals; the exchange is kept in `log_dir` (D-079)."""
    from ddict.llm.enrich import _log  # needs httpx, an optional dependency
    from ddict.llm.run import run_block

    # Anthropic (v0.18): the whole message (B3), and the flat schema, as it refuses the
    # grammar of the strict one as too large (A5).
    anthropic = getattr(client, "protocol", "") == "anthropic"
    version = ADVICE_API_PROMPT_VERSION if anthropic else ADVICE_PROMPT_VERSION
    block = build_advice_block(project, objective, version)
    result = run_block(
        client,
        block,
        run_id=run_id(now),
        now=now,
        schema=advice_schema(project, flat=anthropic),
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
