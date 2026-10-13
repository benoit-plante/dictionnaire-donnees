"""Deterministic profiling: everything that can be computed exactly, without any model."""

from ddict.profile.compute import profile_database, profile_variable
from ddict.profile.model import ObservedValue, VariableProfile

__all__ = ["ObservedValue", "VariableProfile", "profile_database", "profile_variable"]
