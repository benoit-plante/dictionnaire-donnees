"""Enrich a project block by block: send, validate, record proposals, save.

Rules:
- every proposal enters with the status "proposed" and the run that produced it;
- a decision already taken by a person (validated, corrected, entered) is never replaced;
- a pending or rejected proposal is replaced by the new one;
- a block already enriched with the same messages, model and prompt is not sent again,
  so an interrupted enrichment resumes where it stopped.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from ddict.llm.client import LocalModelClient
from ddict.llm.messages import PROMPT_VERSION, Block, build_blocks
from ddict.llm.run import BlockResult, run_block
from ddict.llm.schemas import VariableProposal
from ddict.llm.validate import invention_signals
from ddict.project.model import Project, TrackedValue, VariableEntry

# Failures that concern the server, not the block: no use going on with other blocks.
STOPPING_FAILURES = {"connection", "timeout", "http_404"}


def next_run_id(project: Project) -> str:
    return f"run-{len(project.ai_runs) + 1:04d}"


def is_done(project: Project, block: Block, model: str) -> bool:
    return any(
        run.outcome == "succeeded"
        and run.message_sha256 == block.sha256
        and run.model == model
        and run.prompt_version == PROMPT_VERSION
        for run in project.ai_runs
    )


def _may_replace(tracked: TrackedValue) -> bool:
    if tracked.origin == "ai":
        return tracked.status in ("proposed", "rejected")
    if tracked.origin == "human":
        return tracked.value is None
    return tracked.status == "none"  # from the file: replaced only as a proposal


def _proposal(value: str, run_id: str) -> TrackedValue[str] | None:
    value = value.strip()
    if not value:
        return None
    return TrackedValue[str](value=value, origin="ai", status="proposed", ai_run=run_id)


def _apply(entry: VariableEntry, proposal: VariableProposal, run_id: str) -> None:
    signals = [s for s in entry.ai_signals if s.split(":")[0] not in ("label", "description")]
    for field in ("label", "description"):
        new = _proposal(getattr(proposal, field), run_id)
        if new is not None and _may_replace(getattr(entry, field)):
            setattr(entry, field, new)
            signals += [f"{field}:{s}" for s in invention_signals(new.value)]
    kept = [i for i in entry.issues if i.status in ("validated", "corrected")]
    known = {i.value for i in kept}
    new_issues = [
        i
        for i in (_proposal(text, run_id) for text in proposal.issues)
        if i is not None and i.value not in known
    ]
    entry.issues = kept + new_issues
    signals = [s for s in signals if not s.startswith("issues:")]
    for issue in new_issues:
        signals += [f"issues:{s}" for s in invention_signals(issue.value)]
    entry.ai_signals = sorted(set(signals))


def apply_result(project: Project, result: BlockResult) -> None:
    """Record the run, and the proposals when it succeeded."""
    project.ai_runs.append(result.run)
    if result.proposals is None:
        return
    for proposal in result.proposals:
        _apply(project.variable(proposal.name), proposal, result.run.run_id)


@dataclass(frozen=True)
class BlockEvent:
    block: Block
    result: BlockResult | None  # None: already done, skipped


def enrich(
    project: Project,
    client: LocalModelClient,
    *,
    now: Callable[[], str],
    block_size: int,
    redo: bool = False,
    save: Callable[[Project], None] | None = None,
    log_dir: Path | None = None,
) -> Iterator[BlockEvent]:
    """Enrich block by block, yielding after each one; the project is saved each time."""
    for block in build_blocks(project, size=block_size):
        if not redo and is_done(project, block, client.model):
            yield BlockEvent(block, None)
            continue
        result = run_block(client, block, run_id=next_run_id(project), now=now())
        apply_result(project, result)
        if log_dir is not None:
            _log(log_dir, block, result)
        if save is not None:
            save(project)
        yield BlockEvent(block, result)
        if result.run.outcome == "failed" and result.run.detail in STOPPING_FAILURES:
            return


def _log(folder: Path, block: Block, result: BlockResult) -> None:
    """Keep the exact exchange next to the project (CONCEPTION.md, § 5.4)."""
    folder.mkdir(parents=True, exist_ok=True)
    record = {
        "run": result.run.model_dump(mode="json"),
        "messages": list(block.messages),
        "answers": list(result.answers),
    }
    path = folder / f"{result.run.run_id}-{block.block_id}.json"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
