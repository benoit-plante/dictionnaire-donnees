"""The model chooses, among the computed candidates, the question a variable comes from
(v0.2, D-013). Prompt `link-v2` (v0.3: with the question before each candidate).

- The model sees, for each variable, its candidates only, never the whole questionnaire:
  small models have a short context, and a questionnaire of 27 pages does not fit.
- It answers with an identifier ("Q12", "Q12.o3"), "aucune" or "incertain", never with
  text: an identifier outside the variable's candidates refuses the whole block. The text
  shown for a link is then looked up in the questionnaire: the model cannot write it.
- Every choice enters as a proposal, which a person accepts, changes or rejects; a link a
  person decided is never sent again, nor replaced.
- Paragraphs of the questionnaire (consent page, instructions) are never sent.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, ValidationError

from ddict.export.wording import code_text
from ddict.llm.messages import Block, recorded_version, sensitive_note, system_prompt
from ddict.llm.validate import InvalidResponse
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.questionnaire import link

if TYPE_CHECKING:
    from ddict.llm.client import ModelClient
    from ddict.llm.enrich import BlockEvent
    from ddict.llm.run import BlockResult

LINK_PROMPT_VERSION = "link-v2"
# Only for the variables offered neighbour questions, in blocks of their own (v0.6,
# D-040): the rule about neighbours, given to all, led the model astray elsewhere.
NEIGHBOUR_PROMPT_VERSION = "link-v3"
# For a small context of 4,096 tokens (before v0.18): 12 variables with 5 candidates each
# already took 3,654 tokens on the fictional base (trial of 2026-10-14).
DEFAULT_LINK_BLOCK_SIZE = 6
# Through an API key (v0.18): no context to fit in, fewer and larger blocks.
API_LINK_BLOCK_SIZE = 20
MAX_QUESTION_CHARS = 150  # enough to tell questions apart; the answer is an identifier
AFTER_CHARS = 80  # the question just before a candidate (link-v2)
FOLLOW_UP = re.compile(r"\s*(si (oui|non)|if (yes|no))\b", re.IGNORECASE)  # "Si oui, …"
NONE_ANSWER = "aucune"  # the variable comes from no question
UNSURE_ANSWER = "incertain"  # no proposal: a person chooses
# The same answers in the English instructions (v0.5).
NONE_ANSWERS = {NONE_ANSWER, "none"}
UNSURE_ANSWERS = {UNSURE_ANSWER, "unsure"}


class LinkChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    question: str


class LinkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: str
    variables: list[LinkChoice]


def link_schema() -> dict:
    return LinkResponse.model_json_schema()


def _shorten(text: str, limit: int = MAX_QUESTION_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _candidate(found: link.Target, previous: dict) -> dict:
    payload = {"id": found.target_id}
    if found.question.page:
        payload["page"] = found.question.page
    payload["question"] = _shorten(found.question.text)
    if found.part is not None:
        payload["item"] = found.part
    before = previous.get(found.question.question_id)
    if before is not None:
        payload["after"] = _shorten(before.text, AFTER_CHARS)
    return payload


def _needing_context(questionnaire) -> dict:
    """The question before, for the questions that cannot be told apart without it: a text
    repeated in the questionnaire ("À quelle fréquence cette personne vous apporte du
    soutien ?" after "Votre conjoint·e"), or a follow-up ("Si oui, quels professionnels…").
    Given for every candidate, it led the model astray elsewhere (trial of 2026-10-14)."""
    texts = [link.words(q.text) for q in questionnaire.questions]
    previous = link.previous_questions(questionnaire)
    return {
        q.question_id: previous[q.question_id]
        for q, mine in zip(questionnaire.questions, texts, strict=True)
        if q.question_id in previous and (texts.count(mine) > 1 or FOLLOW_UP.match(q.text))
    }


# The "no question" candidate (v0.6, D-039): the answer word of the prompt, and why.
NO_QUESTION_IDS = {"fr": NONE_ANSWER, "en": "none"}
NO_QUESTION_WHY = {
    "fr": {
        "identifier": "identifiant",
        "completion_date": "date de passation ou de réponse",
        "computed_score": "score calculé",
    },
    "en": {
        "identifier": "identifier",
        "completion_date": "date of completion or response",
        "computed_score": "computed score",
    },
}


def _no_question_candidate(entry: VariableEntry, language: str) -> dict:
    reason = link.no_question_reason(entry) or "identifier"
    why = NO_QUESTION_WHY.get(language, NO_QUESTION_WHY["fr"])[reason]
    return {"id": NO_QUESTION_IDS.get(language, NONE_ANSWER), "question": f"({why})"}


def _payload(
    entry: VariableEntry,
    found: list[link.Target],
    previous: dict,
    language: str = "fr",
    no_question_first: bool = False,
    neighbour: bool = False,
    sure: str | None = None,
) -> dict:
    payload: dict = {"name": entry.name}
    if entry.file.label:
        payload["file_label"] = entry.file.label
    payload["type"] = entry.profile.inferred_type
    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    if privacy_class != "ordinary":
        payload["note"] = sensitive_note(privacy_class, language)
    elif entry.file.value_labels:
        payload["value_labels"] = {code_text(v.code): v.label for v in entry.file.value_labels}
    payload["candidates"] = [_candidate(t, previous) for t in found]
    if neighbour:  # no word in common: from its place in the questionnaire (D-040)
        for candidate in payload["candidates"]:
            candidate["neighbour"] = True
    if no_question_first:
        payload["candidates"].insert(0, _no_question_candidate(entry, language))
    # The computation's sure choice (D-041), as a fact the model may weigh.
    sure_id = NO_QUESTION_IDS.get(language, NONE_ANSWER) if sure == link.NO_QUESTION else sure
    for candidate in payload["candidates"]:
        if sure_id is not None and candidate["id"] == sure_id:
            candidate["computed"] = "sure"
    return payload


def is_decided(entry: VariableEntry) -> bool:
    """A link a person entered, validated or corrected: never sent again."""
    question = entry.question
    if question.origin == "human":
        return question.value is not None
    return question.status in ("validated", "corrected")


def build_link_blocks(project: Project, *, size: int) -> tuple[Block, ...]:
    """Blocks of the variables that have candidates and no decision yet, in file order; then
    the blocks of the variables offered neighbour questions (D-040), with their own
    instructions."""
    if size < 1:
        raise ValueError("Block size must be at least 1")
    if project.questionnaire is None:
        return ()
    by_id = {t.target_id: t for t in link.targets(project.questionnaire)}
    previous = _needing_context(project.questionnaire)
    found = link.candidates(project)
    near = link.neighbours(project, found)
    sure = link.sure_choices(project)
    offered = {**near, **{name: ids for name, ids in found.items() if ids}}
    waiting = [e for e in project.variables if offered.get(e.name) and not is_decided(e)]
    language = project.settings.language
    groups = (
        (LINK_PROMPT_VERSION, [e for e in waiting if found.get(e.name)]),
        (NEIGHBOUR_PROMPT_VERSION, [e for e in waiting if not found.get(e.name)]),
    )
    blocks = []
    for version, entries in groups:
        system = system_prompt(version, language)
        for start in range(0, len(entries), size):
            block_id = f"l-{len(blocks) + 1:03d}"
            chunk = entries[start : start + size]
            payloads = [
                _payload(
                    e,
                    [by_id[i] for i in offered[e.name] if i != link.NO_QUESTION],
                    previous,
                    language,
                    no_question_first=offered[e.name][0] == link.NO_QUESTION,
                    neighbour=version == NEIGHBOUR_PROMPT_VERSION,
                    sure=sure.get(e.name),
                )
                for e in chunk
            ]
            content = {"block": block_id, "variables": payloads}
            user = json.dumps(content, ensure_ascii=False, indent=2)
            blocks.append(
                Block(
                    block_id=block_id,
                    names=tuple(e.name for e in chunk),
                    messages=(
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ),
                    prompt_version=recorded_version(version, language),
                )
            )
    return tuple(blocks)


def _allowed(block: Block) -> dict[str, set[str]]:
    """The identifiers each variable of the block may be answered with."""
    content = json.loads(block.messages[-1]["content"])
    return {
        v["name"]: {c["id"] for c in v["candidates"]} | NONE_ANSWERS | UNSURE_ANSWERS
        for v in content["variables"]
    }


def parse_link_response(content: str, block: Block) -> tuple[LinkChoice, ...]:
    """Valid JSON, exactly the schema, the same variables, and only allowed identifiers."""
    if not content.strip():
        raise InvalidResponse("empty_response", "Empty answer")
    try:
        response = LinkResponse.model_validate(json.loads(content))
    except json.JSONDecodeError as error:
        raise InvalidResponse("not_json", f"Not JSON: {error}") from error
    except ValidationError as error:
        raise InvalidResponse("schema", f"Does not match the schema: {error}") from error
    if response.block != block.block_id:
        raise InvalidResponse("block_mismatch", f"Answer for {response.block!r}")
    if tuple(v.name for v in response.variables) != block.names:
        raise InvalidResponse("names_mismatch", "Variables differ, or their order changed")
    allowed = _allowed(block)
    unknown = [v.name for v in response.variables if v.question.strip() not in allowed[v.name]]
    if unknown:
        raise InvalidResponse("unknown_target", f"Not among the candidates: {unknown}")
    return tuple(response.variables)


def _may_replace(tracked: TrackedValue) -> bool:
    if tracked.origin == "ai":
        return tracked.status in ("proposed", "rejected")
    return tracked.value is None


DISAGREES = "question:computed_disagrees"  # the model left the computation's sure choice


def apply_links(project: Project, result: BlockResult) -> None:
    sure = link.sure_choices(project)
    for choice in result.proposals:
        answer = choice.question.strip()
        entry = project.variable(choice.name)
        if answer in UNSURE_ANSWERS or not _may_replace(entry.question):
            continue
        value = link.NO_QUESTION if answer in NONE_ANSWERS else answer
        entry.question = TrackedValue[str](
            value=value, origin="ai", status="proposed", ai_run=result.run.run_id
        )
        # Kept, never replaced in silence, but flagged (D-041).
        signals = [s for s in entry.ai_signals if s != DISAGREES]
        if choice.name in sure and value != sure[choice.name]:
            signals.append(DISAGREES)
        entry.ai_signals = sorted(signals)


def propose_links(
    project: Project,
    client: ModelClient,
    *,
    now: Callable[[], str],
    block_size: int,
    redo: bool = False,
    save: Callable[[Project], None] | None = None,
    log_dir: Path | None = None,
) -> Iterator[BlockEvent]:
    """Have the model choose among the candidates, block by block; saved after each one."""
    from ddict.llm.enrich import run_blocks  # needs httpx, an optional dependency

    yield from run_blocks(
        project,
        client,
        build_link_blocks(project, size=block_size),
        apply=apply_links,
        schema=link_schema(),
        parse=parse_link_response,
        now=now,
        redo=redo,
        save=save,
        log_dir=log_dir,
    )
