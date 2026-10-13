"""Build the messages sent to the model, from the project file only.

The project file already went through the privacy gate (metadata and aggregates, small
counts masked). Messages reduce it further (CONCEPTION.md, § 6.1):
- sensitive variables: name, file label, type and a note, nothing else;
- counts become proportions, rounded; masked counts stay "masqué";
- date ranges become years;
- never the data file name or path, nor the team's notes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources

from ddict.export.wording import anomalies, code_text
from ddict.project.model import Group, Project, VariableEntry

PROMPT_VERSION = "variables-v1"
DEFAULT_BLOCK_SIZE = 12
MASKED = "masqué"

SENSITIVE_NOTES = {
    "likely_identifier": "identifiant probable : aucune valeur transmise",
    "free_text": "texte libre : aucune valeur transmise",
    "quasi_identifier": "quasi-identifiant : aucune valeur transmise",
}


@dataclass(frozen=True)
class Block:
    block_id: str
    names: tuple[str, ...]
    messages: tuple[dict, ...]

    @property
    def sha256(self) -> str:
        return message_sha256(self.messages)


def system_prompt() -> str:
    path = resources.files("ddict.llm") / "prompts" / f"{PROMPT_VERSION}.fr.txt"
    return path.read_text(encoding="utf-8")


def message_sha256(messages: tuple[dict, ...] | list[dict]) -> str:
    canonical = json.dumps(list(messages), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _round(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits) + 0.0


def variable_payload(entry: VariableEntry, neighbors: list[str], groups: dict[str, Group]) -> dict:
    p = entry.profile
    payload: dict = {"name": entry.name}
    if neighbors:
        payload["neighbors"] = neighbors
    if entry.file.label:
        payload["file_label"] = entry.file.label
    payload["type"] = p.inferred_type

    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    if privacy_class != "ordinary":
        payload["note"] = SENSITIVE_NOTES.get(privacy_class, "variable sensible")
        return payload

    if entry.file.measure_level:
        payload["measure_level"] = entry.file.measure_level
    if entry.file.value_labels:
        payload["value_labels"] = {code_text(v.code): v.label for v in entry.file.value_labels}
    if p.observed_values is not None:
        present = p.n_rows - p.n_system_missing
        payload["observed"] = {
            code_text(o.code): MASKED if o.count is None else _round(o.count / present)
            for o in p.observed_values
        }
    payload["pct_missing"] = _round(
        100 * (p.n_system_missing + p.n_declared_missing) / p.n_rows if p.n_rows else 0.0, 1
    )
    if entry.file.declared_missing:
        payload["declared_missing"] = [
            code_text(m.low) if m.low == m.high else f"{code_text(m.low)}..{code_text(m.high)}"
            for m in entry.file.declared_missing
        ]
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
        if group.descriptive_label.value:
            payload["group"]["description"] = group.descriptive_label.value
    found = anomalies(p)
    if found:
        payload["anomalies"] = found
    return payload


def build_blocks(project: Project, *, size: int = DEFAULT_BLOCK_SIZE) -> tuple[Block, ...]:
    """Blocks of consecutive variables, each with its full list of messages."""
    if size < 1:
        raise ValueError("Block size must be at least 1")
    variables = project.variables
    groups = {g.group_id: g for g in project.groups}
    system = system_prompt()
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
            payloads.append(variable_payload(entry, neighbors, groups))
        user = json.dumps({"block": block_id, "variables": payloads}, ensure_ascii=False, indent=2)
        blocks.append(
            Block(
                block_id=block_id,
                names=tuple(e.name for e in chunk),
                messages=(
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ),
            )
        )
    return tuple(blocks)
