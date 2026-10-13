"""What the model may answer.

There is deliberately no field for a clinical threshold, a theoretical range, a reference
or an instrument name (principle 4): with extra="forbid", an answer that adds one is
refused as a whole.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Label = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
Issue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class VariableProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    label: Label
    description: Description
    issues: list[Issue] = Field(max_length=5)


class BlockResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: str
    variables: list[VariableProposal]


def response_schema() -> dict:
    """The JSON schema given to the server as response_format."""
    return BlockResponse.model_json_schema()
