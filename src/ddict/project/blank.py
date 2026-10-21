"""The codes of the blanks for SPSS and R (v0.21, D-167): one for a question not asked (not
applicable), one for a question asked and not answered (missing). Chosen by the team on the
page "Export" or with `ddict codes vides`, none by default, for the whole project; written by
the preparation scripts in the empty cells of the numeric variables, declared missing and
labelled there, never in the documented copy (D-026). The tool's own computation tells the
two apart in any case.

Refused, for a variable that would receive it: a code that is already a choice, a value label
or a code observed; a code equal to a missing code already declared; more missing codes than
SPSS takes (three discrete codes, or one beside a range).
"""

from __future__ import annotations

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import aside, skip
from ddict.project.decisions import is_accepted
from ddict.project.model import BlankCodes, Project, VariableEntry
from ddict.questionnaire import link
from ddict.questionnaire.labels import accepted_labels

SPSS_MAX_DISCRETE = 3


class BlankError(ValueError):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def _numeric(entry: VariableEntry) -> bool:
    return entry.file.storage_type == "numeric"


def filtered(project: Project) -> list[VariableEntry]:
    """The numeric variables with a condition: they receive the code of the not applicable."""
    conditions = skip.conditions_of(project)
    return [e for e in aside.kept(project) if e.name in conditions and _numeric(e)]


def of_the_questionnaire(project: Project) -> list[VariableEntry]:
    """The numeric variables of the questionnaire (linked to a question, planned, or with a
    condition): they receive the code of the missing, where asked and left empty."""
    conditions = skip.conditions_of(project)
    found = []
    for entry in aside.kept(project):
        linked = is_accepted(entry.question) and entry.question.value not in (
            None,
            link.NO_QUESTION,
        )
        if _numeric(entry) and (linked or entry.planned is not None or entry.name in conditions):
            found.append(entry)
    return found


def _taken(entry: VariableEntry) -> set[str]:
    """The codes a blank code may not take: choices, labels, observed codes, missing codes."""
    found = {skip.code_text(v.code) for v in accepted_labels(entry)}
    found |= {skip.code_text(v.code) for v in entry.file.value_labels}
    if entry.profile is not None:
        found |= {skip.code_text(v.code) for v in entry.profile.observed_values or []}
    found |= {skip.code_text(c) for c in w.confirmed_missing(entry)}
    found |= {skip.code_text(m.low) for m in entry.file.declared_missing if m.low == m.high}
    return found


def _within(entry: VariableEntry, code: float) -> bool:
    return any(m.low <= code <= m.high for m in entry.file.declared_missing if m.low != m.high)


def problems(project: Project, codes: BlankCodes) -> list[str]:
    found = []
    for code in (codes.not_applicable, codes.missing):
        if code is not None and skip.as_number(code) is None:
            found.append(_("Un code des vides est un nombre : {code}.").format(code=code))
    if found:
        return found
    receiving = {}
    if codes.not_applicable is not None:
        for entry in filtered(project):
            receiving.setdefault(entry.name, (entry, []))[1].append(codes.not_applicable)
    if codes.missing is not None:
        for entry in of_the_questionnaire(project):
            receiving.setdefault(entry.name, (entry, []))[1].append(codes.missing)
    for name, (entry, added) in receiving.items():
        taken = _taken(entry)
        for code in added:
            if skip.code_text(code) in taken or _within(entry, float(code)):
                found.append(
                    _(
                        "{name} : le code {code} y est déjà une valeur, un choix ou un code "
                        "manquant."
                    ).format(name=name, code=skip.code_text(code))
                )
        discrete = {skip.code_text(m.low) for m in entry.file.declared_missing if m.low == m.high}
        discrete |= {skip.code_text(c) for c in w.confirmed_missing(entry)}
        ranged = any(m.low != m.high for m in entry.file.declared_missing)
        allowed = 1 if ranged else SPSS_MAX_DISCRETE
        if len(discrete | {skip.code_text(c) for c in added}) > allowed:
            found.append(
                _("{name} : SPSS accepte au plus {n} codes manquants.").format(name=name, n=allowed)
            )
    return found


def set_codes(project: Project, not_applicable=None, missing=None) -> None:
    """Choose the two codes (None: not chosen). Raises BlankError, the project unchanged."""

    def number(value):
        found = skip.as_number(value) if value is not None else None
        if value is not None and found is None:
            raise BlankError([_("Un code des vides est un nombre : {code}.").format(code=value)])
        return None if found is None else (int(found) if found.is_integer() else found)

    try:
        codes = BlankCodes(not_applicable=number(not_applicable), missing=number(missing))
    except ValueError as error:
        if isinstance(error, BlankError):
            raise
        raise BlankError([_("Le non applicable et le manquant demandent deux codes.")]) from None
    found = problems(project, codes)
    if found:
        raise BlankError(found)
    project.settings.blank_codes = codes
