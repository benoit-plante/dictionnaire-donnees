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

from ddict import glossary
from ddict.llm.client import LocalModelClient
from ddict.llm.messages import Block, build_blocks
from ddict.llm.run import BlockResult, run_block
from ddict.llm.schemas import VariableProposal
from ddict.llm.validate import invention_signals, parse_block_response
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
        and run.prompt_version == block.prompt_version
        for run in project.ai_runs
    )


def may_replace(tracked: TrackedValue) -> bool:
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


def _apply(
    entry: VariableEntry,
    proposal: VariableProposal,
    run_id: str,
    file_has_labels: bool,
    known_acronyms: frozenset[str],
) -> None:
    signals = [s for s in entry.ai_signals if s.split(":")[0] not in ("label", "description")]
    for field in ("label", "description"):
        new = _proposal(getattr(proposal, field), run_id)
        if new is not None and may_replace(getattr(entry, field)):
            setattr(entry, field, new)
            signals += [f"{field}:{s}" for s in invention_signals(new.value, known_acronyms)]
            if field == "label" and not entry.file.label and file_has_labels:
                # Without a label in the file, models borrow a neighbour's (trial of
                # 2026-10-13): the label is a guess, to be checked against the questionnaire.
                # Only where other variables have one: in a CSV every label is a guess, and
                # flagging them all would flag nothing.
                signals.append("label:no_file_label")
    # Inconsistencies are no longer asked of the model (D-009): pending ones from an
    # earlier prompt are dropped, those a person accepted are kept.
    entry.issues = [i for i in entry.issues if i.status in ("validated", "corrected")]
    signals = [s for s in signals if not s.startswith("issues:")]
    entry.ai_signals = sorted(set(signals))


def apply_proposals(project: Project, result: BlockResult) -> None:
    file_has_labels = any(e.file.label for e in project.variables)
    known = frozenset(e.term.casefold() for e in project.glossary if glossary.is_accepted(e))
    for proposal in result.proposals:
        entry = project.variable(proposal.name)
        _apply(entry, proposal, result.run.run_id, file_has_labels, known)


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
    yield from run_blocks(
        project,
        client,
        build_blocks(project, size=block_size),
        apply=apply_proposals,
        schema=None,
        parse=parse_block_response,
        now=now,
        redo=redo,
        save=save,
        log_dir=log_dir,
    )


def run_blocks(
    project: Project,
    client: LocalModelClient,
    blocks: tuple[Block, ...],
    *,
    apply: Callable[[Project, BlockResult], None],
    schema: dict | None,
    parse: Callable[[str, Block], tuple],
    now: Callable[[], str],
    redo: bool,
    save: Callable[[Project], None] | None,
    log_dir: Path | None,
) -> Iterator[BlockEvent]:
    """Send the blocks one by one: record each run, apply its proposals when it succeeded,
    save, and yield. A block already done with the same messages is skipped."""
    for block in blocks:
        if not redo and is_done(project, block, client.model):
            yield BlockEvent(block, None)
            continue
        result = run_block(
            client, block, run_id=next_run_id(project), now=now(), schema=schema, parse=parse
        )
        project.ai_runs.append(result.run)
        if result.proposals is not None:
            apply(project, result)
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
