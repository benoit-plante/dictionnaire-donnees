"""The model proposes the stem of a question's names, where nothing is decided (v0.7, D-051).

Only stems: never a group's prefix (an instrument's acronym is a name, principle 4), never a
platform variable's name, never a rank. The model reads, for each question, what the
privacy gate already lets through for links and labels: the text of the question (from the
questionnaire, through an accepted or sure link, or the file label), the kind of question,
its answer options as the value labels say them, and the type of its variables. Never a
value of a participant.

The answer is a stem per question, or "" when unsure; the schema allows nothing else, and a
stem that breaks the naming rules refuses the block. A stem enters as a proposal ("ai");
one that looks like an acronym the question's text does not hold (nor the accepted
glossary) is flagged: it may name an instrument. The rules then derive the names.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from ddict import glossary, naming
from ddict.llm.messages import Block, recorded_version, sensitive_note, system_prompt
from ddict.llm.validate import InvalidResponse
from ddict.project.model import Project, TrackedValue
from ddict.questionnaire import link

if TYPE_CHECKING:
    from ddict.llm.client import LocalModelClient
    from ddict.llm.enrich import BlockEvent
    from ddict.llm.run import BlockResult

STEM_PROMPT_VERSION = "rename-v1"
DEFAULT_STEM_BLOCK_SIZE = 8  # questions per message
MAX_OPTIONS = 10  # answer options shown for a question
MAX_TEXT_CHARS = 300
ACRONYM_SIGNAL = "stem:acronym"
# A part of a stem that may be an acronym: two to five letters (a digit allowed), not a word
# of the question.
_SHORT_PART = re.compile(r"[a-z][a-z0-9]{1,4}")

Stem = Annotated[str, StringConstraints(strip_whitespace=True, max_length=naming.MAX_STEM)]


class StemChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    stem: Stem  # "" when unsure


class StemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: str
    questions: list[StemChoice]


def stem_schema() -> dict:
    return StemResponse.model_json_schema()


def _open(project: Project, key: str) -> bool:
    """A stem the model may (re)propose: none, a pending proposal of the rules or of the
    model, or one a person rejected."""
    found = naming.stem(project, key)
    if found is None or not found.stem.value:
        return True
    tracked = found.stem
    if tracked.origin in ("rule", "ai"):
        return tracked.status in ("proposed", "rejected")
    return False


def _payload(project: Project, question: naming.StemQuestion, sure: dict[str, str]) -> dict:
    language = project.settings.language
    text = naming.question_text(project, question, sure) or ""
    payload: dict = {"key": question.key, "question": text[:MAX_TEXT_CHARS]}
    if question.options:
        payload["kind"] = "checkbox"
        options = []
        for name, _rank in question.options:
            entry = project.variable(name)
            labels = [v.label for v in entry.file.value_labels]
            options.append((labels[0] if len(labels) == 1 else entry.file.label) or "")
        payload["options"] = [o[:120] for o in options[:MAX_OPTIONS]]
    elif question.single:
        entry = project.variable(question.single)
        privacy = entry.privacy.privacy_class.value or "ordinary"
        if privacy != "ordinary":
            payload["note"] = sensitive_note(privacy, language)
        payload["type"] = entry.profile.inferred_type
        labels = [v.label[:120] for v in entry.file.value_labels]
        if labels:
            payload["options"] = labels[:MAX_OPTIONS]
    if question.other:
        payload["other"] = True
    return payload


def build_stem_blocks(project: Project, *, size: int) -> tuple[Block, ...]:
    """Blocks of the questions whose stem is not decided, in survey order."""
    if size < 1:
        raise ValueError("Block size must be at least 1")
    questions = [q for q in naming.stem_questions(project) if _open(project, q.key)]
    language = project.settings.language
    system = system_prompt(STEM_PROMPT_VERSION, language)
    sure = naming.sure_links(project)
    blocks = []
    for start in range(0, len(questions), size):
        block_id = f"r-{len(blocks) + 1:03d}"
        chunk = questions[start : start + size]
        content = {"block": block_id, "questions": [_payload(project, q, sure) for q in chunk]}
        blocks.append(
            Block(
                block_id=block_id,
                names=tuple(q.key for q in chunk),
                messages=(
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(content, ensure_ascii=False, indent=2)},
                ),
                prompt_version=recorded_version(STEM_PROMPT_VERSION, language),
            )
        )
    return tuple(blocks)


def parse_stem_response(content: str, block: Block) -> tuple[StemChoice, ...]:
    """Valid JSON, exactly the schema, the same questions in the same order, and stems the
    naming rules accept (or "")."""
    if not content.strip():
        raise InvalidResponse("empty_response", "Empty answer")
    try:
        response = StemResponse.model_validate(json.loads(content))
    except json.JSONDecodeError as error:
        raise InvalidResponse("not_json", f"Not JSON: {error}") from error
    except ValidationError as error:
        raise InvalidResponse("schema", f"Does not match the schema: {error}") from error
    if response.block != block.block_id:
        raise InvalidResponse("block_mismatch", f"Answer for {response.block!r}")
    if tuple(q.key for q in response.questions) != block.names:
        raise InvalidResponse("names_mismatch", "Questions differ, or their order changed")
    bad = [q.key for q in response.questions if q.stem and not naming.valid_stem(q.stem)]
    if bad:
        raise InvalidResponse("invalid_stem", f"Stems the naming rules refuse: {bad}")
    return tuple(response.questions)


def acronym_signal(
    project: Project, key: str, stem: str, sure: dict[str, str] | None = None
) -> bool:
    """Whether a stem holds a short part that the question's text does not hold, nor the
    accepted glossary: perhaps an instrument's acronym, which a person must give."""
    question = next((q for q in naming.stem_questions(project) if q.key == key), None)
    text = naming.question_text(project, question, sure) if question else ""
    words = {naming.slug(w) for w in link.words(text or "")}
    known = {e.term.lower() for e in project.glossary if glossary.is_accepted(e)}
    for part in stem.split("_"):
        if not _SHORT_PART.fullmatch(part) or part in known:
            continue
        if part not in words and not any(w.startswith(part) for w in words if len(part) >= 3):
            return True
    return False


def apply_stems(project: Project, result: BlockResult) -> None:
    """The model's stems as proposals where nothing is decided; then the names follow."""
    taken = {
        s.stem.value
        for s in project.stems
        if s.stem.value
        and s.stem.status != "rejected"
        and s.key not in {c.key for c in result.proposals}
    }
    sure = naming.sure_links(project)
    for choice in result.proposals:
        value = choice.stem.strip()
        if not value or not _open(project, choice.key):
            continue
        base, number = value, 2
        while value in taken:
            value, number = f"{base}_{number}", number + 1
        taken.add(value)
        tracked = TrackedValue[str](
            value=value, origin="ai", status="proposed", ai_run=result.run.run_id
        )
        flagged = acronym_signal(project, choice.key, value, sure)
        signals = [ACRONYM_SIGNAL] if flagged else []
        naming.set_stem_proposal(project, choice.key, tracked, signals)
    naming.propose(project)


def propose_stems(
    project: Project,
    client: LocalModelClient,
    *,
    now: Callable[[], str],
    block_size: int = DEFAULT_STEM_BLOCK_SIZE,
    redo: bool = False,
    save: Callable[[Project], None] | None = None,
    log_dir: Path | None = None,
) -> Iterator[BlockEvent]:
    """Have the model propose stems, block by block; saved after each one."""
    from ddict.llm.enrich import run_blocks  # needs httpx, an optional dependency

    naming.propose(project)  # the rules' stems first: the model replaces only those
    yield from run_blocks(
        project,
        client,
        build_stem_blocks(project, size=block_size),
        apply=apply_stems,
        schema=stem_schema(),
        parse=parse_stem_response,
        now=now,
        redo=redo,
        save=save,
        log_dir=log_dir,
    )
