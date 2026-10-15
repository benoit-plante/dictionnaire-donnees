"""Build the messages sent to the model, from the project file only.

The project file already went through the privacy gate (metadata and aggregates, small
counts masked). Messages reduce it further (CONCEPTION.md, § 6.1):
- sensitive variables: name, file label, type and a note, nothing else;
- counts become proportions, rounded; masked counts stay "masqué";
- date ranges become years;
- never the data file name or path, nor the team's notes;
- no computed anomalies: the model is not asked for coding inconsistencies (D-009).

Prompt `variables-v3` (v0.2) adds two documented sources:
- the exact words of the question a variable comes from, once a person accepted the link
  (a proposed link is not used: it may be wrong);
- the accepted glossary entries for the acronyms of the block (D-015), so that the model
  reads "OCF" as the team defined it instead of guessing.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib import resources

from ddict import glossary, i18n
from ddict.export.wording import code_text, confirmed_missing, group_description
from ddict.project import measure
from ddict.project.decisions import is_accepted
from ddict.project.model import Group, Project, VariableEntry
from ddict.questionnaire import link
from ddict.questionnaire.labels import accepted_labels

PROMPT_VERSION = "variables-v3"
PROMPTS_WITH_QUESTIONNAIRE = ("variables-v3",)
MAX_QUESTION_CHARS = 300
# With v3, 12 variables left too little room for the answer in Ollama's 4,096 tokens.
DEFAULT_BLOCK_SIZE = 8
# What the model reads besides the data, in the language of the study (v0.5, D-032).
MASKED = {"fr": "masqué", "en": "masked"}
SENSITIVE_NOTES = {
    "fr": {
        "likely_identifier": "identifiant probable : aucune valeur transmise",
        "free_text": "texte libre : aucune valeur transmise",
        "quasi_identifier": "quasi-identifiant : aucune valeur transmise",
        "other": "variable sensible",
    },
    "en": {
        "likely_identifier": "likely identifier: no value sent",
        "free_text": "free text: no value sent",
        "quasi_identifier": "quasi-identifier: no value sent",
        "other": "sensitive variable",
    },
}


def sensitive_note(privacy_class: str, language: str) -> str:
    notes = SENSITIVE_NOTES.get(language, SENSITIVE_NOTES["fr"])
    return notes.get(privacy_class, notes["other"])


def recorded_version(version: str, language: str) -> str:
    """ "variables-v3" in French, as before v0.5; "variables-v3.en" in English."""
    return version if language == "fr" else f"{version}.{language}"


@dataclass(frozen=True)
class Block:
    block_id: str
    names: tuple[str, ...]
    messages: tuple[dict, ...]
    prompt_version: str = PROMPT_VERSION

    @property
    def sha256(self) -> str:
        return message_sha256(self.messages)


def system_prompt(version: str = PROMPT_VERSION, language: str = "fr") -> str:
    """The instructions in the language of the study; French when there is no translation."""
    folder = resources.files("ddict.llm") / "prompts"
    path = folder / f"{version}.{language}.txt"
    if not path.is_file():
        path = folder / f"{version}.fr.txt"
    return path.read_text(encoding="utf-8")


def message_sha256(messages: tuple[dict, ...] | list[dict]) -> str:
    canonical = json.dumps(list(messages), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _round(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits) + 0.0


def _shorten(text: str) -> str:
    if len(text) <= MAX_QUESTION_CHARS:
        return text
    return text[: MAX_QUESTION_CHARS - 1].rsplit(" ", 1)[0] + "…"


def question_payload(project: Project, entry: VariableEntry) -> dict | None:
    """The words of the question the variable comes from, when a person accepted the link."""
    tracked = entry.question
    if not is_accepted(tracked) or tracked.value == link.NO_QUESTION:
        return None
    found = link.target(project.questionnaire, tracked.value)
    if found is None:
        return None
    payload = {"text": _shorten(found.question.text)}
    if found.part is not None:
        payload["item"] = found.part
    return payload


def block_glossary(project: Project, entries: list[VariableEntry]) -> dict[str, str]:
    """Accepted acronyms found in the names, file labels or questions of the block."""
    found: set[str] = set()
    for entry in entries:
        found.update(glossary.name_parts(entry.name))
        texts = [entry.file.label or ""]
        question = question_payload(project, entry)
        if question:
            texts += [question["text"], question.get("item", "")]
        found.update(w.casefold() for text in texts for w in re.findall(r"\w+", text))
    return {
        item.term: item.meaning
        for item in project.glossary
        if glossary.is_accepted(item) and item.term.casefold() in found
    }


def variable_payload(
    entry: VariableEntry,
    neighbors: list[str],
    groups: dict[str, Group],
    question: dict | None = None,
    language: str = "fr",
) -> dict:
    p = entry.profile
    payload: dict = {"name": entry.name}
    if neighbors:
        payload["neighbors"] = neighbors
    if entry.file.label:
        payload["file_label"] = entry.file.label
    if question:
        payload["question"] = question
    payload["type"] = p.inferred_type

    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    if privacy_class != "ordinary":
        payload["note"] = sensitive_note(privacy_class, language)
        return payload

    if measure.level(entry):  # the level in force (v0.8, D-063)
        payload["measure_level"] = measure.level(entry)
    labels = accepted_labels(entry)  # the file's, or those a person accepted (D-016)
    if labels:
        payload["value_labels"] = {code_text(v.code): v.label for v in labels}
    if p.observed_values is not None:
        present = p.n_rows - p.n_system_missing
        payload["observed"] = {
            code_text(o.code): MASKED.get(language, MASKED["fr"])
            if o.count is None
            else _round(o.count / present)
            for o in p.observed_values
        }
    payload["pct_missing"] = _round(
        100 * (p.n_system_missing + p.n_declared_missing) / p.n_rows if p.n_rows else 0.0, 1
    )
    declared = [
        code_text(m.low) if m.low == m.high else f"{code_text(m.low)}..{code_text(m.high)}"
        for m in entry.file.declared_missing
    ]
    declared += [code_text(c) for c in confirmed_missing(entry)]  # by the team (D-028)
    if declared:
        payload["declared_missing"] = declared
    if p.min is not None:
        payload["min"] = _round(p.min)
        payload["max"] = _round(p.max)
    if p.mean is not None:
        payload["mean"] = _round(p.mean)
    if p.date_min:
        payload["years"] = f"{p.date_min[:4]}-{p.date_max[:4]}"
    group_id = entry.group_id.value
    if group_id and group_id in groups:
        group = groups[group_id]
        payload["group"] = {"id": group_id}
        with i18n.using(language):  # a computed description, in the study's language
            description = group_description(group, "work")
        if description:
            payload["group"]["description"] = description
    return payload


def build_blocks(
    project: Project, *, size: int = DEFAULT_BLOCK_SIZE, version: str = PROMPT_VERSION
) -> tuple[Block, ...]:
    """Blocks of consecutive variables, each with its full list of messages.

    `version` is the prompt; an earlier one is kept for trials (docs/essais).
    """
    if size < 1:
        raise ValueError("Block size must be at least 1")
    variables = project.variables
    groups = {g.group_id: g for g in project.groups}
    language = project.settings.language
    system = system_prompt(version, language)
    sources = version in PROMPTS_WITH_QUESTIONNAIRE
    blocks = []
    for start in range(0, len(variables), size):
        block_id = f"b-{start // size + 1:03d}"
        chunk = variables[start : start + size]
        payloads = []
        for offset, entry in enumerate(chunk):
            index = start + offset
            neighbors = [
                variables[i].name for i in (index - 1, index + 1) if 0 <= i < len(variables)
            ]
            question = question_payload(project, entry) if sources else None
            payloads.append(variable_payload(entry, neighbors, groups, question, language))
        content: dict = {"block": block_id}
        terms = block_glossary(project, chunk) if sources else {}
        if terms:
            content["glossary"] = terms
        content["variables"] = payloads
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
