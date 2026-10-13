"""Decisions on a tracked value: validate, correct, reject, or enter a value by hand.

Each function returns a new TrackedValue; `now` is an ISO 8601 timestamp given by the
caller, which keeps these functions deterministic and testable.
"""

from __future__ import annotations

from typing import TypeVar

from ddict.project.model import TrackedValue

T = TypeVar("T")


class DecisionError(ValueError):
    """The decision does not apply to this value."""


def validate(tracked: TrackedValue[T], *, now: str) -> TrackedValue[T]:
    if tracked.value is None:
        raise DecisionError("Nothing to validate")
    if tracked.origin == "human":
        raise DecisionError("A value entered by a person needs no validation")
    return tracked.model_copy(update={"status": "validated", "updated_at": now})


def correct(tracked: TrackedValue[T], new_value: T, *, now: str) -> TrackedValue[T]:
    """Replace the value, keeping the one from the file or the model in proposed_value."""
    if tracked.origin == "human":
        return enter(tracked, new_value, now=now)
    original = tracked.proposed_value if tracked.status == "corrected" else tracked.value
    if original is None:
        raise DecisionError("Nothing to correct")
    return tracked.model_validate(
        {
            **tracked.model_dump(),
            "value": new_value,
            "status": "corrected",
            "proposed_value": original,
            "updated_at": now,
        }
    )


def reject(tracked: TrackedValue[T], *, now: str) -> TrackedValue[T]:
    if tracked.origin != "ai":
        raise DecisionError("Only AI proposals can be rejected")
    return tracked.model_copy(update={"status": "rejected", "updated_at": now})


def enter(tracked: TrackedValue[T], value: T | None, *, now: str) -> TrackedValue[T]:
    """A value typed by a person where nothing came from the file or the model."""
    if tracked.origin != "human":
        raise DecisionError("Use correct() to change a value from the file or the model")
    return type(tracked)(value=value, origin="human", status="none", updated_at=now)


def is_accepted(tracked: TrackedValue) -> bool:
    """Whether the value may appear in the final export (principle 3)."""
    if tracked.value is None:
        return False
    if tracked.origin == "ai":
        return tracked.status in ("validated", "corrected")
    return tracked.status != "rejected"
