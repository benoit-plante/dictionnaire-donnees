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
