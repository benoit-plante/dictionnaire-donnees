"""Check an answer of the model before anything is kept (CONCEPTION.md, § 6.4)."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from ddict.llm.messages import Block
from ddict.llm.schemas import BlockResponse, VariableProposal


class InvalidResponse(ValueError):
    """The answer is refused as a whole; `code` is a short reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def parse_block_response(content: str, block: Block) -> tuple[VariableProposal, ...]:
    """Valid JSON, exactly the schema, the same block and exactly the variables sent."""
    if not content.strip():
        raise InvalidResponse("empty_response", "Empty answer")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        raise InvalidResponse("not_json", f"Not JSON: {error}") from error
    try:
        response = BlockResponse.model_validate(data)
    except ValidationError as error:
        raise InvalidResponse("schema", f"Does not match the schema: {error}") from error
    if response.block != block.block_id:
        raise InvalidResponse("block_mismatch", f"Answer for {response.block!r}")
    names = tuple(v.name for v in response.variables)
    if names != block.names:
        missing = sorted(set(block.names) - set(names))
        invented = sorted(set(names) - set(block.names))
        raise InvalidResponse(
            "names_mismatch",
            f"Variables differ: missing {missing}, invented {invented}, or order changed",
        )
    return tuple(response.variables)


# Text that looks like what the model must never invent (principle 4). It is not refused:
# it is flagged, so that the person reviewing sees it.
_CITATION = re.compile(r"\b[A-ZÉ][\w'-]+(?: et al\.?| & [A-ZÉ][\w'-]+)?,? \(?(?:19|20)\d{2}\)?")
_THRESHOLD = re.compile(
    r"(?:[≥≤<>]=?\s*\d)|\b(?:seuil|cut-?off|point de coupure|score critique)\b", re.IGNORECASE
)
_INSTRUMENT = re.compile(
    r"\b(?i:inventaire|questionnaire|échelle|inventory|scale)\s+(?:de\s+|d')?[A-ZÉ]"
    r"|\b[A-Z]{2,}-(?:\d+|[IVX]+)\b"  # PHQ-9, GAD-7, BDI-II
)


def invention_signals(text: str) -> tuple[str, ...]:
    """Codes for what in the text looks like a citation, a threshold or an instrument name."""
    found = []
    if _CITATION.search(text):
        found.append("citation")
    if _THRESHOLD.search(text):
        found.append("threshold")
    if _INSTRUMENT.search(text):
        found.append("instrument")
    return tuple(found)
