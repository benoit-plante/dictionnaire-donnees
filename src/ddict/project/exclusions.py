"""The exclusion rules of a project (v0.12, D-093): written by a person, each with a reason
and a rank, never a list of people. A rule that would name a person is refused, with its
reason: a condition on a value of an identifier or of a free text. Only the duplicate rule
compares identifiers, between rows, without ever naming a value.
"""

from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from ddict.i18n import _
from ddict.project.decisions import is_accepted
from ddict.project.model import (
    CompletenessRule,
    ConditionRule,
    DuplicateRule,
    DurationRule,
    ExclusionRule,
    Group,
    Project,
    StraightliningRule,
)

NAMING = ("likely_identifier", "free_text")  # a value of these would name a person
MIN_GRID = 4  # items of a grid, for a straight line to mean something
ORDERED = ("lt", "le", "gt", "ge")
_RULE = TypeAdapter(ExclusionRule)


class ExclusionRefused(Exception):
    """The rule cannot be kept; `reasons` says why, in plain words."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(" ".join(reasons))
        self.reasons = reasons


def members(group: Group) -> list[str]:
    """The original names of a group's items, as accepted."""
    return list(group.members.value or []) if is_accepted(group.members) else []


def _group(project: Project, group_id: str) -> Group | None:
    return next((g for g in project.groups if g.group_id == group_id), None)


def _variable(project: Project, name: str, found: list[str]) -> bool:
    try:
        entry = project.variable(name)
    except KeyError:
        found.append(_("{name} : variable inconnue du projet.").format(name=name))
        return False
    if entry.set_aside is not None:  # D-158
        found.append(_("{name} : variable écartée du codebook.").format(name=name))
        return False
    return True


def _condition(project: Project, rule: ConditionRule, found: list[str]) -> None:
    if rule.recode is not None:  # v0.15: a recoded variable, codes as numbers
        if all(r.id != rule.recode for r in project.recodes.rules):
            found.append(_("{id} : aucun recodage ne porte ce numéro.").format(id=rule.recode))
        return
    if rule.score is not None:
        group = _group(project, rule.score)
        scoring = group.scoring if group else None
        if scoring is None or not scoring.items:
            found.append(
                _("{group} : aucune cotation structurée, donc aucun score.").format(
                    group=rule.score
                )
            )
        return
    if not _variable(project, rule.variable, found):
        return
    entry = project.variable(rule.variable)
    privacy = entry.privacy.privacy_class.value
    if privacy in NAMING and rule.operator != "missing":
        found.append(
            _(
                "{name} : une condition sur une valeur d'un identifiant ou d'un texte libre "
                "nommerait une personne ; une exclusion décrit une règle, pas une liste."
            ).format(name=rule.variable)
        )
    textual = entry.file.storage_type != "numeric"
    if textual and rule.operator in ORDERED:
        found.append(
            _("{name} : une variable texte ne se compare pas par plus petit ou plus grand.").format(
                name=rule.variable
            )
        )


def _items(project: Project, group_id: str, found: list[str]) -> list[str]:
    group = _group(project, group_id)
    if group is None:
        found.append(_("{group} : groupe inconnu du projet.").format(group=group_id))
        return []
    items = members(group)
    if not items:
        found.append(_("{group} : groupe sans items acceptés.").format(group=group_id))
    return items


def _date(project: Project, name: str, text_format: str | None, found: list[str]) -> None:
    from ddict.profile.compute import TEXT_DATETIME_FORMATS

    if not _variable(project, name, found):
        return
    entry = project.variable(name)
    if entry.data_type != "datetime":
        found.append(
            _(
                "{name} : ce n'est pas une date avec l'heure ; la durée ne se calcule qu'entre "
                "deux variables de date et d'heure."
            ).format(name=name)
        )
    elif (entry.file.storage_type == "numeric") != (text_format is None):
        found.append(
            _("{name} : le format de la date ne correspond pas à celui du fichier.").format(
                name=name
            )
        )
    elif text_format is not None and text_format not in TEXT_DATETIME_FORMATS:
        found.append(_("Format de date inconnu : {format}.").format(format=text_format))


def _conditions_of(project: Project, items: list[str]) -> set:
    """The distinct conditions of these variables, as a comparison sees them."""
    from ddict.questionnaire.relevance import canonical

    found = set()
    for name in items:
        entry = project.variable(name)
        tracked = entry.asked_if
        conditions = tracked.value if tracked is not None and is_accepted(tracked) else []
        found.add(tuple(canonical(c) for c in conditions or []))
    return found


def refusals(project: Project, rule: ExclusionRule) -> list[str]:
    """Why a rule cannot be kept; empty when it can."""
    found: list[str] = []
    if isinstance(rule, ConditionRule):
        _condition(project, rule, found)
    elif isinstance(rule, CompletenessRule):
        items = _items(project, rule.group, found)
        if items and len(_conditions_of(project, items)) > 1:  # v0.21 (D-167)
            found.append(
                _(
                    "{group} : ses items ne sont pas posés aux mêmes personnes (des conditions "
                    "différentes) ; une règle de complétude ne s'y applique pas dans cette "
                    "version."
                ).format(group=rule.group)
            )
        if items and rule.min_answered > len(items):
            found.append(
                _("{group} : {n} items exigés, mais le groupe en compte {k}.").format(
                    group=rule.group, n=rule.min_answered, k=len(items)
                )
            )
    elif isinstance(rule, DurationRule):
        _date(project, rule.start, rule.text_format, found)
        _date(project, rule.end, rule.text_format, found)
        if rule.start == rule.end:
            found.append(_("Le début et la fin sont la même variable."))
    elif isinstance(rule, StraightliningRule):
        items = _items(project, rule.group, found)
        if items and len(items) < MIN_GRID:
            found.append(
                _(
                    "{group} : une grille de moins de {n} items ne se juge pas en ligne droite."
                ).format(group=rule.group, n=MIN_GRID)
            )
    elif isinstance(rule, DuplicateRule):
        for name in rule.variables:
            _variable(project, name, found)
    return found


def _incomplete(error: ValidationError) -> list[str]:
    """What a rule lacks, in plain words."""
    found = []
    for problem in error.errors():
        field = str(problem["loc"][-1]) if problem["loc"] else ""
        if field == "source":
            found.append(_("Un seuil de durée est un choix de l'équipe : donnez sa source."))
        elif field == "reason":
            found.append(_("Donnez la raison de la règle, en clair."))
        else:
            text = _("Règle incomplète : {field} ({detail}).")
            found.append(text.format(field=field, detail=problem["msg"]))
    return list(dict.fromkeys(found))


def add(project: Project, data: dict) -> ExclusionRule:
    """A new rule at the end, with the next identifier. Raises ExclusionRefused."""
    try:
        rule = _RULE.validate_python({**data, "id": f"E{project.exclusions.next_id}"})
    except ValidationError as error:
        raise ExclusionRefused(_incomplete(error)) from None
    found = refusals(project, rule)
    if found:
        raise ExclusionRefused(found)
    project.exclusions.rules.append(rule)
    project.exclusions.next_id += 1
    return rule


def find(project: Project, rule_id: str) -> ExclusionRule:
    for rule in project.exclusions.rules:
        if rule.id == rule_id:
            return rule
    raise ExclusionRefused([_("{id} : aucune règle ne porte ce numéro.").format(id=rule_id)])


def remove(project: Project, rule_id: str) -> None:
    project.exclusions.rules.remove(find(project, rule_id))


def move(project: Project, rule_id: str, position: int) -> None:
    """Put a rule at this rank (1 is the first); the others keep their order."""
    rule = find(project, rule_id)
    rules = project.exclusions.rules
    rules.remove(rule)
    position = max(1, min(position, len(rules) + 1))
    rules.insert(position - 1, rule)


# --- What the page and `ddict exclusions` share (v0.12, step 8). ---

SYMBOLS = {"eq": "=", "ne": "≠", "lt": "<", "le": "≤", "gt": ">", "ge": "≥"}


def original(project: Project, name: str) -> str:
    """A variable's original name, given by its original or its final name."""
    from ddict.export import wording as w

    if any(e.name == name for e in project.variables):
        return name
    for first, final in w.names_of(project).items():
        if final == name:
            return first
    return name  # unknown: `refusals` says so


def typed(project: Project, name: str, text: str):
    """A value typed by a person, as the variable holds it: a number for a numeric
    variable (ExclusionRefused when it is not one), else the text."""
    text = text.strip()
    try:
        entry = project.variable(name)
    except KeyError:
        return text
    if entry.file.storage_type != "numeric":
        return text
    try:
        number = float(text.replace(",", "."))
    except ValueError:
        raise ExclusionRefused(
            [_("{name} : « {value} » n'est pas un nombre.").format(name=name, value=text)]
        ) from None
    return int(number) if number.is_integer() else number


def _value(value) -> str:
    from ddict.export import wording as w

    return w.code_text(value)


def rule_text(rule: ExclusionRule) -> str:
    """The condition of a rule, in plain words: "age < 18", "doublon sur email"."""
    if isinstance(rule, ConditionRule):
        what = _("score de {group}").format(group=rule.score) if rule.score else rule.variable
        if rule.operator == "missing":
            return _("{what} manquant").format(what=what)
        if rule.operator == "in":
            values = ", ".join(_value(v) for v in rule.value)
            return _("{what} parmi {values}").format(what=what, values=values)
        return f"{what} {SYMBOLS[rule.operator]} {_value(rule.value)}"
    if isinstance(rule, CompletenessRule):
        return _("moins de {m} items de {group} répondus").format(
            m=rule.min_answered, group=rule.group
        )
    if isinstance(rule, DurationRule):
        return _("passation de moins de {seconds} s, de {start} à {end}").format(
            seconds=_value(rule.min_seconds), start=rule.start, end=rule.end
        )
    if isinstance(rule, StraightliningRule):
        return _("tous les items de {group} à la même valeur").format(group=rule.group)
    if isinstance(rule, DuplicateRule):
        return _("doublon sur {names}, la première réponse gardée").format(
            names=", ".join(rule.variables)
        )
    raise ValueError(f"exclusion rule not written yet: {rule.kind}")  # v0.21, step 10


# How a person may write an operator: its code, its symbol, or a French word.
OPERATORS = {
    **{code: code for code in ("eq", "ne", "lt", "le", "gt", "ge", "in", "missing")},
    "=": "eq", "==": "eq", "!=": "ne", "<>": "ne", "<": "lt", "<=": "le", ">": "gt",
    ">=": "ge", "parmi": "in", "manquant": "missing",
}  # fmt: skip


def condition_data(
    project: Project, what: str, operator: str, values: list[str], *, score: bool = False
) -> dict:
    """A condition rule's fields from what a person typed (without its reason): a variable
    by its original or final name, or a group's score. Raises ExclusionRefused."""
    code = OPERATORS.get(operator.strip().lower())
    if code is None:
        raise ExclusionRefused([_("Opérateur inconnu : {operator}.").format(operator=operator)])
    data: dict = {"kind": "condition", "operator": code}
    if score:
        data["score"] = what
    else:
        what = original(project, what)
        data["variable"] = what
    if code == "missing":
        return data
    if not values:
        raise ExclusionRefused([_("Cette condition demande une valeur.")])
    if score:
        found = [typed_number(v) for v in values]
    else:
        found = [typed(project, what, v) for v in values]
    data["value"] = found if code == "in" else found[0]
    return data


def typed_number(text: str) -> float:
    try:
        number = float(text.strip().replace(",", "."))
    except ValueError:
        raise ExclusionRefused(
            [_("« {value} » n'est pas un nombre.").format(value=text.strip())]
        ) from None
    return int(number) if number.is_integer() else number
