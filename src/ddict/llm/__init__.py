"""Optional AI enrichment: messages, response schemas, and (later) the local client."""

from ddict.llm.messages import (
    DEFAULT_BLOCK_SIZE,
    PROMPT_VERSION,
    Block,
    build_blocks,
    message_sha256,
    system_prompt,
)
from ddict.llm.schemas import BlockResponse, VariableProposal, response_schema

__all__ = [
    "DEFAULT_BLOCK_SIZE",
    "PROMPT_VERSION",
    "Block",
    "BlockResponse",
    "VariableProposal",
    "build_blocks",
    "message_sha256",
    "response_schema",
    "system_prompt",
]
