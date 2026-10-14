"""The model chooses, among the computed candidates, the question a variable comes from
(v0.2, D-013). Prompt `link-v1`.

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
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, ValidationError

from ddict.export.wording import code_text
from ddict.llm.messages import SENSITIVE_NOTES, Block, system_prompt
from ddict.llm.validate import InvalidResponse
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.questionnaire import link

if TYPE_CHECKING:
    from ddict.llm.client import LocalModelClient
    from ddict.llm.enrich import BlockEvent
    from ddict.llm.run import BlockResult

LINK_PROMPT_VERSION = "link-v1"
# Ollama keeps 4,096 tokens of context by default: 12 variables with 5 candidates each
# already took 3,654 tokens on the fictional base (trial of 2026-10-14).
DEFAULT_LINK_BLOCK_SIZE = 6
MAX_QUESTION_CHARS = 150  # enough to tell questions apart; the answer is an identifier
NONE_ANSWER = "aucune"  # the variable comes from no question
UNSURE_ANSWER = "incertain"  # no proposal: a person chooses


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


def _shorten(text: str) -> str:
    if len(text) <= MAX_QUESTION_CHARS:
        return text
    return text[: MAX_QUESTION_CHARS - 1].rsplit(" ", 1)[0] + "…"


def _candidate(found: link.Target) -> dict:
    payload = {"id": found.target_id, "question": _shorten(found.question.text)}
    if found.part is not None:
        payload["item"] = found.part
    return payload


def _payload(entry: VariableEntry, found: list[link.Target]) -> dict:
    payload: dict = {"name": entry.name}
    if entry.file.label:
        payload["file_label"] = entry.file.label
    payload["type"] = entry.profile.inferred_type
    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    if privacy_class != "ordinary":
        payload["note"] = SENSITIVE_NOTES.get(privacy_class, "variable sensible")
    elif entry.file.value_labels:
        payload["value_labels"] = {code_text(v.code): v.label for v in entry.file.value_labels}
    payload["candidates"] = [_candidate(t) for t in found]
    return payload


def is_decided(entry: VariableEntry) -> bool:
    """A link a person entered, validated or corrected: never sent again."""
    question = entry.question
    if question.origin == "human":
        return question.value is not None
    return question.status in ("validated", "corrected")


def build_link_blocks(project: Project, *, size: int) -> tuple[Block, ...]:
    """Blocks of the variables that have candidates and no decision yet, in file order."""
    if size < 1:
        raise ValueError("Block size must be at least 1")
    if project.questionnaire is None:
        return ()
    by_id = {t.target_id: t for t in link.targets(project.questionnaire)}
    found = link.candidates(project)
    waiting = [e for e in project.variables if found.get(e.name) and not is_decided(e)]
    system = system_prompt(LINK_PROMPT_VERSION)
    blocks = []
    for start in range(0, len(waiting), size):
        block_id = f"l-{start // size + 1:03d}"
        chunk = waiting[start : start + size]
        payloads = [_payload(e, [by_id[i] for i in found[e.name]]) for e in chunk]
        user = json.dumps({"block": block_id, "variables": payloads}, ensure_ascii=False, indent=2)
        blocks.append(
            Block(
                block_id=block_id,
                names=tuple(e.name for e in chunk),
                messages=(
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ),
                prompt_version=LINK_PROMPT_VERSION,
            )
        )
    return tuple(blocks)


def _allowed(block: Block) -> dict[str, set[str]]:
    """The identifiers each variable of the block may be answered with."""
    content = json.loads(block.messages[-1]["content"])
    return {
        v["name"]: {c["id"] for c in v["candidates"]} | {NONE_ANSWER, UNSURE_ANSWER}
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


def apply_links(project: Project, result: BlockResult) -> None:
    for choice in result.proposals:
        answer = choice.question.strip()
        entry = project.variable(choice.name)
        if answer == UNSURE_ANSWER or not _may_replace(entry.question):
            continue
        value = link.NO_QUESTION if answer == NONE_ANSWER else answer
        entry.question = TrackedValue[str](
            value=value, origin="ai", status="proposed", ai_run=result.run.run_id
        )


def propose_links(
    project: Project,
    client: LocalModelClient,
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
