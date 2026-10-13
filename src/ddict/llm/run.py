"""Send one block to the model, with one more try, and trace the outcome."""

from __future__ import annotations

from dataclasses import dataclass

from ddict.llm.client import LocalModelClient, ModelCallError
from ddict.llm.messages import PROMPT_VERSION, Block
from ddict.llm.schemas import VariableProposal, response_schema
from ddict.llm.validate import InvalidResponse, parse_block_response
from ddict.project.model import AiRun

MAX_ATTEMPTS = 2


@dataclass(frozen=True)
class BlockResult:
    run: AiRun
    proposals: tuple[VariableProposal, ...] | None  # None unless the run succeeded
    answers: tuple[str, ...] = ()  # raw answers, for the exchange log only


def run_block(client: LocalModelClient, block: Block, *, run_id: str, now: str) -> BlockResult:
    """Never a partial answer: either every variable of the block, or nothing."""
    schema = response_schema()
    outcome, detail, proposals = "failed", None, None
    attempts = 0
    answers: list[str] = []
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        try:
            content = client.complete(list(block.messages), schema)
            answers.append(content)
        except ModelCallError as error:
            # The server is down or refuses: trying again at once would not help.
            outcome, detail = "failed", error.code
            break
        try:
            proposals = parse_block_response(content, block)
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
        prompt_version=PROMPT_VERSION,
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
    )
