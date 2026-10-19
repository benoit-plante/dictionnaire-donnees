"""What the model may answer.

There is deliberately no field for a clinical threshold, a theoretical range, a reference
or an instrument name (principle 4): with extra="forbid", an answer that adds one is
refused as a whole. Coding inconsistencies are not asked either (D-009): the tool computes
them exactly.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Label = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]


class VariableProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    label: Label
    description: Description


class BlockResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: str
    variables: list[VariableProposal]


def response_schema() -> dict:
    """The JSON schema given to the server as response_format."""
    return BlockResponse.model_json_schema()


# What the Anthropic API refuses in a schema (a 400), or does not document (titles, which
# pydantic writes everywhere and which say nothing to the model). Checked 2026-10-19.
DROPPED_KEYWORDS = frozenset(
    {
        "title",
        "maxLength",
        "minLength",
        "maxItems",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
    }
)
ACCEPTED_KEYWORDS = frozenset(
    {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "minItems",
        "enum",
        "const",
        "anyOf",
        "allOf",
        "$ref",
        "$defs",
        "definitions",
        "default",
        "description",
        "format",
        "pattern",
    }
)
MAX_OPTIONAL_PARAMETERS = 24
MAX_UNION_PARAMETERS = 16
_NAMED = ("properties", "$defs", "definitions")  # their keys are names, not keywords


def wire_schema(schema: dict) -> dict:
    """The schema as the Anthropic API takes it: the bounds it refuses are left out
    (lengths, numbers of items, numeric limits), `prefixItems` becomes `items` (any of the
    listed schemas), `minItems` is at most 1. The answer is still validated whole on this
    computer: that, not the server's grammar, is the guarantee (D-135)."""
    return _wire(schema)


def _wire(schema: object) -> object:
    if not isinstance(schema, dict):
        return schema
    wired: dict = {}
    for key, value in schema.items():
        if key in DROPPED_KEYWORDS or key == "prefixItems":
            continue
        if key in _NAMED:
            wired[key] = {name: _wire(sub) for name, sub in value.items()}
        elif key in ("anyOf", "allOf"):
            wired[key] = [_wire(sub) for sub in value]
        elif key in ("items", "additionalProperties") and isinstance(value, dict):
            wired[key] = _wire(value)
        else:
            wired[key] = value
    if "prefixItems" in schema:
        items = [_wire(sub) for sub in schema["prefixItems"]]
        wired["items"] = items[0] if len(items) == 1 else {"anyOf": items}
    if wired.get("minItems", 0) > 1:
        wired["minItems"] = 1
    if wired.get("type") == "object" and wired.get("additionalProperties") is not False:
        raise ValueError("Every object of a response schema needs additionalProperties: false")
    return wired


def schema_nodes(schema: object):
    """Every schema in `schema`, itself included (not the names of properties)."""
    if not isinstance(schema, dict):
        return
    yield schema
    for key, value in schema.items():
        if key in _NAMED:
            for sub in value.values():
                yield from schema_nodes(sub)
        elif key in ("anyOf", "allOf", "prefixItems"):
            for sub in value:
                yield from schema_nodes(sub)
        elif key in ("items", "additionalProperties"):
            yield from schema_nodes(value)


def optional_parameters(schema: dict) -> int:
    """Properties that are not required, over every object of the schema."""
    return sum(
        len(set(node.get("properties", {})) - set(node.get("required", ())))
        for node in schema_nodes(schema)
    )


def union_parameters(schema: dict) -> int:
    """Schemas with several possible types (`anyOf`, or a list of types)."""
    return sum(
        1 for node in schema_nodes(schema) if "anyOf" in node or isinstance(node.get("type"), list)
    )
