"""Check an answer of the model before anything is kept (CONCEPTION.md, § 6.4)."""

from __future__ import annotations

import json
import re
import unicodedata

from pydantic import ValidationError

from ddict import glossary
from ddict.llm.messages import Block
from ddict.llm.schemas import BlockResponse, VariableProposal


class InvalidResponse(ValueError):
    """The answer is refused as a whole; `code` is a short reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _neighbors(block: Block) -> set[str]:
    """Names given to the model as neighbors only: they may lie outside the block."""
    names: set[str] = set()
    for message in block.messages:
        try:
            content = json.loads(message["content"])
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(content, dict):
            for variable in content.get("variables", []):
                names.update(variable.get("neighbors", []))
    return names - set(block.names)


def parse_block_response(content: str, block: Block) -> tuple[VariableProposal, ...]:
    """Valid JSON, exactly the schema, the same block and exactly the variables sent.

    A neighbor answered as if it were in the block is dropped, not held against the block:
    it is a name the model was shown, not one it invented.
    """
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
    neighbors = _neighbors(block)
    variables = tuple(v for v in response.variables if v.name not in neighbors)
    names = tuple(v.name for v in variables)
    if names != block.names:
        missing = sorted(set(block.names) - set(names))
        invented = sorted(set(names) - set(block.names))
        raise InvalidResponse(
            "names_mismatch",
            f"Variables differ: missing {missing}, invented {invented}, or order changed",
        )
    return variables


# Text that looks like what the model must never invent (principle 4). It is not refused:
# it is flagged, so that the person reviewing sees it.
_CITATION = re.compile(r"\b[A-ZÉ][\w'-]+(?: et al\.?| & [A-ZÉ][\w'-]+)?,? \(?(?:19|20)\d{2}\)?")
_THRESHOLD = re.compile(
    r"(?:[≥≤<>]=?\s*\d)|\b(?:seuil|cut-?off|point de coupure|score critique)\b", re.IGNORECASE
)
_INSTRUMENT = re.compile(
    r"\b(?i:inventaire|questionnaire|échelle|inventory|scale)\s+(?:de\s+|d')?[A-ZÉ]"
    r"|\b[A-Z]{2,}-(?:\d+[A-Z]?|[IVX]+)\b"  # PHQ-9, GAD-7, BDI-II, EQ-5D
)


# "CBCL (Child Behavior Checklist)", "Child Behavior Checklist (CBCL)": an acronym defined.
_ACRONYM_THEN_MEANING = re.compile(r"\b([A-Z][A-Z0-9]{1,7})\s*\(([^()]+)\)")
_MEANING_THEN_ACRONYM = re.compile(r"\(([A-Z][A-Z0-9]{1,7})\)")


def _plain(letter: str) -> str:
    return unicodedata.normalize("NFKD", letter)[0].casefold()


def _defines_acronym(text: str, known: frozenset[str]) -> bool:
    """Whether the text gives the meaning of an acronym that is not in the glossary (D-015)."""
    for match in _ACRONYM_THEN_MEANING.finditer(text):
        term, inside = match.group(1), match.group(2).split()
        if term.casefold() in known or any(c.isdigit() for c in match.group(2)):
            continue
        if len(inside) >= 2 and _plain(inside[0][0]) == _plain(term[0]):
            return True
    for match in _MEANING_THEN_ACRONYM.finditer(text):
        term = match.group(1)
        if term.casefold() not in known and glossary.long_form(text[: match.start()], term):
            return True
    return False


# "sur une échelle de 0 à 21": a range given for a scale (v0.3, step 6).
_SCALE_RANGE = re.compile(
    r"(?i:échelle|scale|score)[^.;]*?\b(?i:de|entre|from)\s+(-?\d+(?:[.,]\d+)?)\s+(?i:à|et|to)\s+(-?\d+(?:[.,]\d+)?)"
)


def presents_observed_range(text: str, low: float | None, high: float | None) -> bool:
    """Whether the text gives the observed minimum and maximum as the range of a scale: the
    model saw them as statistics, and nothing says the scale stops there (K6, 0 to 24, was
    described "sur une échelle de 0 à 21" in the trial of the prompt v3)."""
    if low is None or high is None:
        return False
    for match in _SCALE_RANGE.finditer(text):
        first, second = (float(g.replace(",", ".")) for g in match.groups())
        if abs(first - low) < 0.01 and abs(second - high) < 0.01:
            return True
    return False


def invention_signals(text: str, known_acronyms: frozenset[str] = frozenset()) -> tuple[str, ...]:
    """Codes for what in the text looks like a citation, a threshold, an instrument name, or
    the meaning of an acronym missing from the glossary (`known_acronyms`, case-folded)."""
    found = []
    if _CITATION.search(text):
        found.append("citation")
    if _THRESHOLD.search(text):
        found.append("threshold")
    if _INSTRUMENT.search(text):
        found.append("instrument")
    if _defines_acronym(text, known_acronyms):
        found.append("acronym")
    return tuple(found)
