"""Value labels proposed from the options of the linked question (v0.2, D-016), no model.

A proposal is made only when all of these hold:
- the file gives the variable no value labels;
- a person accepted the link, to a question with options or to a row of a grid (whose
  options are the grid's columns), not to an option itself (a ticked box);
- the codes observed, declared missing ones aside, are whole numbers 1..n or 0..n-1;
- there are exactly as many options as codes.

Options are then given to codes in their order. That is what survey platforms usually do,
not a certainty: the proposal says so ("ordre supposé, à vérifier") and waits for a person.
Otherwise nothing is proposed: the tool does not guess.
"""

from __future__ import annotations

from ddict.i18n import N_
from ddict.project.decisions import is_accepted
from ddict.project.model import Project, TrackedValue, ValueLabel, VariableEntry
from ddict.questionnaire import link

ASSUMED_ORDER = N_("ordre supposé, à vérifier")
UNCLEAR_OPTIONS = {"grid_header_unclear", "grid_without_header"}


def _codes(entry: VariableEntry) -> list[int] | None:
    """Observed codes, declared missing ones aside, if they are 1..n or 0..n-1."""
    observed = entry.profile.observed_values if entry.profile is not None else None
    if not observed:
        return None
    codes = []
    for value in observed:
        if value.declared_missing:
            continue
        code = value.code
        if isinstance(code, str) or float(code) != int(code):
            return None
        codes.append(int(code))
    codes.sort()
    if codes and codes[0] in (0, 1) and codes == list(range(codes[0], codes[0] + len(codes))):
        return codes
    return None


def options_for(project: Project, entry: VariableEntry) -> list[str] | None:
    """The option texts of the accepted link, when it has options and is not one itself."""
    if not is_accepted(entry.question) or entry.question.value == link.NO_QUESTION:
        return None
    found = link.target(project.questionnaire, entry.question.value)
    if found is None:
        return None
    if found.part is not None and found.question.kind != "grid":
        return None  # an option: the variable is the box, ticked or not
    if UNCLEAR_OPTIONS & set(found.question.to_check):
        return None  # columns run into each other: their number is unsure
    options = [option.text for option in found.question.options]
    return options or None


def proposal(project: Project, entry: VariableEntry) -> list[ValueLabel] | None:
    """The value labels the rule allows for this variable, or None."""
    if entry.file.value_labels:
        return None
    options = options_for(project, entry)
    codes = _codes(entry)
    if options is None or codes is None or len(options) != len(codes):
        return None
    return [ValueLabel(code=code, label=text) for code, text in zip(codes, options, strict=True)]


def _waiting(tracked: TrackedValue) -> bool:
    """No decision by a person yet: a pending proposal, or nothing."""
    if tracked.origin == "questionnaire":
        return tracked.status == "proposed"
    return tracked.origin == "human" and tracked.value is None


def propose_value_labels(project: Project) -> list[str]:
    """Make, refresh or withdraw the proposals of the variables without a decision, and
    return the names of those with a proposal waiting. A decision is never changed."""
    waiting = []
    for entry in project.variables:
        if not _waiting(entry.value_labels):
            continue
        labels = proposal(project, entry)
        if labels is None:
            entry.value_labels = TrackedValue[list[ValueLabel]](origin="human")
            continue
        if entry.value_labels.value != labels:
            entry.value_labels = TrackedValue[list[ValueLabel]](
                value=labels, origin="questionnaire", status="proposed"
            )
        waiting.append(entry.name)
    return waiting


def accepted_labels(entry: VariableEntry) -> list[ValueLabel]:
    """The value labels to use: the file's, or those a person accepted."""
    if entry.file.value_labels:
        return list(entry.file.value_labels)
    if is_accepted(entry.value_labels):
        return list(entry.value_labels.value or [])
    return []
