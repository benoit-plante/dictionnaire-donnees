"""The recodings of a project (v0.15, D-120): a derived variable as a decision of the team,
with its reason, never the column itself. Two kinds: categories gathered into new ones, a
number cut into classes. Never an identifier, a free text or a date, as the exclusion rules
and the subgroups (D-093, D-113); never a recoding of a recoding. What needs the data (a
value without a group, the counts) is in `ddict.analysis.recode`.
"""

from __future__ import annotations

import itertools

from pydantic import TypeAdapter, ValidationError

from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.i18n import _
from ddict.naming import RESERVED, problems
from ddict.project import measure
from ddict.project.model import (
    ClassesRecode,
    GroupsRecode,
    Project,
    Recode,
    VariableRef,
)

NAMING = ("likely_identifier", "free_text")  # a value of these would name a person
_RULE = TypeAdapter(Recode)


class RecodeRefused(Exception):
    """The recoding cannot be kept; `reasons` says why, in plain words."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(" ".join(reasons))
        self.reasons = reasons


def source_name(project: Project, ref: VariableRef) -> str | None:
    """The final name in force of a recoding's source; None when it leads nowhere."""
    if ref.variable is not None:
        return w.names_of(project).get(ref.variable)
    if ref.score is not None:
        return next((s.name for s in plan(project)[1] if s.group == ref.score), None)
    return None


def source_level(project: Project, ref: VariableRef) -> str | None:
    """The measure level of the source: the level in force, "scale" for a score."""
    if ref.score is not None:
        return "scale"
    try:
        return measure.level(project.variable(ref.variable or ""))
    except KeyError:
        return None


def by_name(project: Project) -> dict[str, Recode]:
    """The recodings by the name of the variable they make."""
    return {rule.name: rule for rule in project.recodes.rules}


def _taken(project: Project, rule: Recode) -> bool:
    """A name a variable, a score, a reversed item or another recoding already has."""
    name = rule.name.lower()
    names = {n.lower() for n in w.names_of(project).values()}
    names |= {e.name.lower() for e in project.variables}
    reversals, scores, _notes = plan(project)
    names |= {s.name.lower() for s in scores} | {r.new.lower() for r in reversals}
    names |= {r.name.lower() for r in project.recodes.rules if r.id != rule.id}
    return name in names


def refusals(project: Project, rule: Recode) -> list[str]:
    """Why a recoding cannot be kept, without the data; empty when it can."""
    found: list[str] = []
    ref = rule.source
    shown = ref.variable or ref.score or ""
    name = source_name(project, ref)
    if name is None:
        found.append(_("{name} : variable inconnue du projet.").format(name=shown))
        return found
    if ref.variable is not None:
        entry = project.variable(ref.variable)
        if (entry.privacy.privacy_class.value in NAMING) or entry.data_type in (
            "empty",
            "mixed",
            "date",
            "datetime",
        ):
            found.append(
                _(
                    "{name} : identifiant, texte libre ou date ; une variable ne se recode pas "
                    "ainsi."
                ).format(name=name)
            )
            return found
    level = source_level(project, ref)
    if level is None:
        found.append(
            _("{name} : niveau de mesure non décidé ; décidez-le d'abord.").format(name=name)
        )
    elif isinstance(rule, GroupsRecode) and level not in ("nominal", "ordinal"):
        found.append(
            _(
                "{name} : seules des catégories (nominales ou ordinales) se regroupent ; un "
                "nombre se découpe en classes."
            ).format(name=name)
        )
    elif isinstance(rule, ClassesRecode) and level != "scale":
        found.append(
            _(
                "{name} : seul un nombre (une échelle ou un score) se découpe en classes ; des "
                "catégories se regroupent."
            ).format(name=name)
        )
    style = problems(project, "", rule.name)
    if "style" in style or "length" in style or rule.name.lower() in RESERVED:
        found.append(
            _(
                "{name} : nom invalide (lettres minuscules, chiffres et _, au plus {n} "
                "caractères, pas un mot réservé)."
            ).format(name=rule.name, n=project.settings.naming.max_length)
        )
    elif _taken(project, rule):
        found.append(_("{name} : nom déjà pris.").format(name=rule.name))
    return found


def _incomplete(error: ValidationError) -> list[str]:
    """What a recoding lacks, in plain words."""
    found = []
    for problem in error.errors():
        field = str(problem["loc"][-1]) if problem["loc"] else ""
        message = str(problem["msg"])
        if field == "reason":
            found.append(_("Donnez la raison du recodage, en clair."))
        elif "in two groups" in message:
            found.append(_("Une valeur est dans deux groupes."))
        elif "same code" in message:
            found.append(_("Deux groupes ont le même code."))
        elif "must increase" in message:
            found.append(_("Les seuils doivent aller croissant."))
        elif "one label per class" in message:
            found.append(_("Une étiquette par classe : une de plus que les seuils."))
        elif "recoded from its own source" in message:
            found.append(_("Une variable recodée se recode depuis sa propre source."))
        elif "reversed item" in message:
            found.append(_("Un item inversé ne se recode pas ; recodez l'item d'origine."))
        elif field == "groups":
            found.append(_("Il faut au moins deux groupes."))
        elif field == "cuts":
            found.append(_("Il faut au moins un seuil."))
        else:
            text = _("Recodage incomplet : {field} ({detail}).")
            found.append(text.format(field=field, detail=message))
    return list(dict.fromkeys(found))


def validated(project: Project, data: dict, rule_id: str | None = None) -> Recode:
    """A recoding from its fields, checked without the data. Raises RecodeRefused."""
    try:
        rule = _RULE.validate_python({**data, "id": rule_id or f"R{project.recodes.next_id}"})
    except ValidationError as error:
        raise RecodeRefused(_incomplete(error)) from None
    found = refusals(project, rule)
    if found:
        raise RecodeRefused(found)
    return rule


def add(project: Project, rule: Recode) -> Recode:
    """A recoding checked by `validated`, at the end, with the next identifier."""
    project.recodes.rules.append(rule)
    project.recodes.next_id += 1
    return rule


def find(project: Project, rule_id: str) -> Recode:
    for rule in project.recodes.rules:
        if rule.id == rule_id:
            return rule
    raise RecodeRefused([_("{id} : aucun recodage ne porte ce numéro.").format(id=rule_id)])


def replace(project: Project, rule: Recode) -> None:
    """A recoding changed: the same identifier, the same place."""
    rules = project.recodes.rules
    rules[rules.index(find(project, rule.id))] = rule


def used_by(project: Project, rule_id: str) -> list[str]:
    """What names a recoding in the project: exclusion rules, hypotheses of the plan."""
    found = [r.id for r in project.exclusions.rules if getattr(r, "recode", None) == rule_id]
    for h in project.plan.hypotheses:
        refs = [ref for refs in h.roles.values() for ref in refs]
        if h.subgroup is not None:
            refs.append(h.subgroup.variable)
        if any(ref.recode == rule_id for ref in refs):
            found.append(h.id)
    return found


def remove(project: Project, rule_id: str) -> None:
    """Remove a recoding nothing in the project names. Raises RecodeRefused."""
    rule = find(project, rule_id)
    users = used_by(project, rule_id)
    if users:
        raise RecodeRefused(
            [
                _("{id} : utilisé par {users} ; retirez-les ou changez-les d'abord.").format(
                    id=rule_id, users=", ".join(users)
                )
            ]
        )
    project.recodes.rules.remove(rule)


# --- How a recoding is said: the codebook, the analysis context, the Method (step 3). ---


def parts_text(rule: Recode) -> str:
    """ "Femme (1) ; Homme ou autre identité (2, 3)", "moins de 30 (< 30) ; 30 à moins de 45
    (≥ 30 et < 45) ; 45 et plus (≥ 45)": each new category and what it gathers. Source
    codes are written as in the data file, since they identify values."""
    from ddict.i18n import semicolon

    if isinstance(rule, ClassesRecode):
        bounds = [None, *rule.cuts, None]
        parts = []
        for i, label in enumerate(rule.labels):
            low, high = bounds[i], bounds[i + 1]
            if low is None:
                span = f"< {w.code_text(high)}"
            elif high is None:
                span = f"≥ {w.code_text(low)}"
            else:
                span = _("≥ {low} et < {high}").format(low=w.code_text(low), high=w.code_text(high))
            parts.append(f"{label} ({span})")
    else:
        parts = [
            f"{g.label} ({w.codes(g.values)})" for g in sorted(rule.groups, key=lambda g: g.code)
        ]
        if rule.missing_values:
            parts.append(_("manquant : {values}").format(values=w.codes(rule.missing_values)))
    return semicolon().join(parts)


def method_sentence(project: Project, rule: Recode) -> str:
    """The Method's sentence of a recoding (D-120)."""
    return _("La variable {name} a été tirée de {source} : {parts}.").format(
        name=rule.name, source=source_name(project, rule.source) or "?", parts=parts_text(rule)
    )


def default_labels(cuts: list[float]) -> list[str]:
    """ "moins de 30", "30 à moins de 45", "45 et plus": the labels the tool proposes."""
    shown = [w.code_text(c) for c in cuts]
    labels = [_("moins de {high}").format(high=shown[0])]
    labels += [
        _("{low} à moins de {high}").format(low=low, high=high)
        for low, high in itertools.pairwise(shown)
    ]
    return [*labels, _("{low} et plus").format(low=shown[-1])]


def reference(project: Project, name: str) -> VariableRef:
    """A recoding's source by its final name, its name in the file, or a score's name."""
    for entry in project.variables:
        if name in (w.final_name(entry), entry.name):
            return VariableRef(variable=entry.name)
    for score in plan(project)[1]:
        if score.name == name:
            return VariableRef(score=score.group)
    raise RecodeRefused([_("{name} : variable inconnue du projet.").format(name=name)])


def frozen_users(project: Project, rule_id: str) -> list[str]:
    """The hypotheses of a frozen plan that use a recoding: it cannot change under them."""
    if project.plan.frozen is None:
        return []
    return [u for u in used_by(project, rule_id) if u.startswith("H")]
