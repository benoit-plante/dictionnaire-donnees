"""Send one block to the model, with one more try, and trace the outcome."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ddict.llm.client import ModelCallError, ModelClient
from ddict.llm.messages import Block
from ddict.llm.schemas import response_schema
from ddict.llm.validate import InvalidResponse, parse_block_response
from ddict.project.model import AiRun

MAX_ATTEMPTS = 2
# The server answered, but not with a usable answer: tried again, like an invalid one.
ANSWER_FAILURES = frozenset({"refusal", "truncated"})


@dataclass(frozen=True)
class BlockResult:
    run: AiRun
    proposals: tuple | None  # None unless the run succeeded
    answers: tuple[str, ...] = ()  # raw answers, for the exchange log only
    calls: tuple[dict, ...] = ()  # request ids and tokens, for the exchange log only
    error: str | None = None  # what the server said of a failure, for the exchange log only


def run_block(
    client: ModelClient,
    block: Block,
    *,
    run_id: str,
    now: str,
    schema: dict | None = None,
    parse: Callable[[str, Block], tuple] = parse_block_response,
) -> BlockResult:
    """Never a partial answer: either every variable of the block, or nothing.

    `schema` and `parse` are those of labels and descriptions unless given (links).
    """
    schema = schema or response_schema()
    outcome, detail, proposals = "failed", None, None
    attempts = 0
    answers: list[str] = []
    calls: list[dict] = []
    error_text = None
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        try:
            content = client.complete(list(block.messages), schema)
            answers.append(content)
        except ModelCallError as error:
            if client.last_call:
                calls.append(dict(client.last_call))
            if error.code in ANSWER_FAILURES:
                outcome, detail = "invalid_response", error.code
                continue
            # The server is down or refuses: trying again at once would not help.
            outcome, detail, error_text = "failed", error.code, str(error)
            break
        if client.last_call:
            calls.append(dict(client.last_call))
        try:
            proposals = parse(content, block)
        except InvalidResponse as error:
            outcome, detail = "invalid_response", error.code
            continue
        outcome, detail = "succeeded", None
        break
    run = AiRun(
        run_id=run_id,
        block=block.block_id,
        endpoint=client.endpoint,
        model=client.model,
        parameters=client.parameters,
        prompt_version=block.prompt_version,
        message_sha256=block.sha256,
        started_at=now,
        attempts=attempts,
        outcome=outcome,
        detail=detail,
    )
    return BlockResult(
        run=run,
        proposals=proposals if outcome == "succeeded" else None,
        answers=tuple(answers),
        calls=tuple(calls),
        error=error_text,
    )
