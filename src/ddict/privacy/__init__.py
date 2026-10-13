"""Privacy: classify variables and build the only view that may leave the tool."""

from ddict.privacy.classify import PrivacyClassification, classify_database, classify_variable
from ddict.privacy.gate import (
    MIN_CELL_COUNT,
    SafeCount,
    SafeVariable,
    safe_database,
    safe_variable,
)

__all__ = [
    "MIN_CELL_COUNT",
    "PrivacyClassification",
    "SafeCount",
    "SafeVariable",
    "classify_database",
    "classify_variable",
    "safe_database",
    "safe_variable",
]
