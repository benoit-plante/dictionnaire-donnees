"""The analysis plan of a project (v0.13, step 2, D-101 to D-104, D-109): hypotheses written
by the team, each tied to an analysis of the catalogue and to the one p-value it is about
(its tested effect), and the general rules (alpha, correction, missing data, sample size,
origin and state of the data). The sheet is `docs/plan-analyse-article.md` (validated).

An hypothesis badly tied is refused, with its reason; the conditions of the codebook
(D-074) are those of the analyses, checked on the data when they are open. Freezing gives
the plan a date and a fingerprint; afterwards it can still change, but every change needs
a reason and becomes an amendment, kept forever (D-102). The plan's fingerprint is its own:
writing the plan never makes an analysis of the notebook "changed".
"""

from __future__ import annotations

import hashlib
import json
from datetime import date

from pydantic import ValidationError

from ddict.analysis import conditions
from ddict.analysis.catalogue import CATALOGUE, NOMINAL
from ddict.analysis.data import PreparedData
from ddict.analysis.notebook import NotebookError, reason_text, reference, resolve
from ddict.i18n import N_, Texts, _
from ddict.project.model import Amendment, Frozen, Hypothesis, Plan, Project

# The effects each analysis may test, the first by default when there is no choice.
EFFECTS = {
    "t_test": ("difference",),
    "paired": ("difference",),
    "anova": ("group",),
    "chi_square": ("association",),
    "correlation": ("pair",),
    "regression": ("model", "predictor"),
}
# The expected directions each effect may take; a t test's sets its one-sided option.
DIRECTIONS = {
    "difference": ("first_higher", "second_higher"),
    "pair": ("positive", "negative"),
    "predictor": ("positive", "negative"),
}
ALTERNATIVE = {"first_higher": "greater", "second_higher": "less"}
ONE_SIDED = ("t_test", "paired")  # the analyses whose expected direction sets the test
EXTRA_OPTIONS = {"t_test": ("levels",)}  # free options of the catalogue, beyond its choices
RULE_FIELDS = ("alpha", "correction", "missing", "sample_size", "data_origin", "data_status")

NAMES = Texts(
    {
        "table1": N_("Le Tableau 1"),
        "t_test": N_("Un test t"),
        "paired": N_("Un test t apparié"),
        "anova": N_("Une ANOVA"),
        "chi_square": N_("Un khi-carré"),
        "correlation": N_("Une corrélation"),
        "regression": N_("Une régression"),
    }
)
EFFECT_NAMES = Texts(
    {
        "difference": N_("la différence entre les deux groupes"),
        "group": N_("l'effet du groupe"),
        "association": N_("l'association"),
        "model": N_("le modèle"),
        "pair": N_("une paire de variables"),
        "predictor": N_("un prédicteur"),
    }
)


class PlanRefused(Exception):
    """The plan cannot take this change; `reasons` says why, in plain words."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(" ".join(reasons))
        self.reasons = reasons


def _today(today: str | None) -> str:
    return today or date.today().isoformat()


# --- Checking an hypothesis. ---


def _resolved(project: Project, hypothesis: Hypothesis, check: conditions.Check) -> dict:
    """Final names by role; a reference that leads nowhere is a refusal."""
    chosen: dict[str, list[str]] = {}
    for role, refs in hypothesis.roles.items():
        names = []
        for ref in refs:
            try:
                names.append(resolve(project, ref))
            except NotebookError as error:
                check.refusals.append(reason_text(error))
        chosen[role] = names
    return chosen


def _same(a, b) -> bool:
    return a.model_dump(mode="json") == b.model_dump(mode="json")


def _effect(project, hypothesis: Hypothesis, chosen: dict, data, check) -> None:
    key, effect = hypothesis.analysis, hypothesis.effect
    allowed = EFFECTS[key]
    if effect.kind not in allowed:
        check.refusals.append(
            _("{analysis} teste {allowed}, pas {effect}.").format(
                analysis=NAMES[key],
                allowed=_(" ou ").join(EFFECT_NAMES[k] for k in allowed),
                effect=EFFECT_NAMES[effect.kind],
            )
        )
        return
    if effect.kind == "pair":
        refs = hypothesis.roles.get("variables", [])
        first, second = effect.variables
        if _same(first, second):
            check.refusals.append(_("Une paire réunit deux variables différentes."))
        for ref in effect.variables:
            if not any(_same(ref, r) for r in refs):
                check.refusals.append(
                    _("{name} n'est pas une variable de cette corrélation.").format(
                        name=_ref_text(project, ref)
                    )
                )
    elif effect.kind == "predictor":
        refs = hypothesis.roles.get("predictors", [])
        if not any(_same(effect.variable, r) for r in refs):
            check.refusals.append(
                _("{name} n'est pas un prédicteur de cette régression.").format(
                    name=_ref_text(project, effect.variable)
                )
            )
            return
        try:
            name = resolve(project, effect.variable)
        except NotebookError:
            return  # already refused with its reason
        if conditions.levels(project).get(name) == NOMINAL and data is not None:
            k = int(data.table[name].dropna().nunique())
            if k > 2:
                check.refusals.append(
                    _(
                        "Un prédicteur nominal de {k} modalités a {c} coefficients ; une "
                        "hypothèse ne porte que sur un seul. Testez le modèle, ou choisissez une "
                        "variable de 2 modalités."
                    ).format(k=k, c=k - 1)
                )


def _ref_text(project: Project, ref) -> str:
    try:
        return resolve(project, ref)
    except NotebookError:
        return ref.variable or ref.score or ref.reversed or ""


def _direction(hypothesis: Hypothesis, check: conditions.Check) -> None:
    direction = hypothesis.direction
    if direction is None:
        return
    allowed = DIRECTIONS.get(hypothesis.effect.kind, ())
    if not allowed:
        check.refusals.append(
            _("{analysis} ne teste pas de sens ; laissez le sens attendu vide.").format(
                analysis=NAMES[hypothesis.analysis]
            )
        )
    elif direction not in allowed:
        if hypothesis.analysis == "paired":
            text = _(
                "Pour un test t apparié, le sens attendu est la première ou la seconde "
                "mesure plus élevée."
            )
        elif hypothesis.effect.kind == "difference":
            text = _(
                "Pour un test t, le sens attendu est le premier ou le second groupe plus élevé."
            )
        else:
            text = _(
                "Le sens attendu d'une corrélation ou d'un coefficient est positif ou négatif."
            )
        check.refusals.append(text)
    elif direction in ALTERNATIVE:
        alternative = hypothesis.options.get("alternative", "two_sided")
        opposite = "less" if ALTERNATIVE[direction] == "greater" else "greater"
        if alternative == opposite:
            check.refusals.append(_("Le sens attendu contredit le test unilatéral choisi."))


def _options(hypothesis: Hypothesis, check: conditions.Check) -> None:
    analysis = CATALOGUE[hypothesis.analysis]
    for option, value in hypothesis.options.items():
        if option in EXTRA_OPTIONS.get(analysis.key, ()):
            continue
        if option not in analysis.options:
            check.refusals.append(_("Option inconnue : {option}.").format(option=option))
        elif value not in analysis.options[option]:
            check.refusals.append(
                _("{option} : « {value} » n'est pas un choix permis.").format(
                    option=option, value=value
                )
            )


def review(
    project: Project, hypothesis: Hypothesis, data: PreparedData | None = None
) -> conditions.Check:
    """Why an hypothesis cannot be kept (refusals) and what is fragile (warnings)."""
    check = conditions.Check()
    key = hypothesis.analysis
    if key == "table1":
        check.refusals.append(
            _("Le Tableau 1 décrit l'échantillon ; il ne teste aucune hypothèse.")
        )
        return check
    if key not in CATALOGUE or key not in EFFECTS:
        check.refusals.append(_("Analyse inconnue : {key}.").format(key=key))
        return check
    roles = {r.key for r in CATALOGUE[key].roles}
    for role in hypothesis.roles:
        if role not in roles:
            check.refusals.append(_("{role} : rôle inconnu pour cette analyse.").format(role=role))
    _options(hypothesis, check)
    if hypothesis.kind == "exploratory" and hypothesis.family is not None:
        check.refusals.append(
            _("Une hypothèse exploratoire n'est pas corrigée ; retirez sa famille.")
        )
    chosen = _resolved(project, hypothesis, check)
    if check.ok:
        found = conditions.check(project, key, chosen, hypothesis.options, data)
        check.refusals += found.refusals
        check.warnings += found.warnings
    _effect(project, hypothesis, chosen, data, check)
    _direction(hypothesis, check)
    if data is None and check.ok:
        check.warnings.append(_("Conditions à vérifier quand la base sera ouverte."))
    check.refusals = list(dict.fromkeys(check.refusals))
    return check


# --- Building an hypothesis from what a person chose. ---


def _incomplete(error: ValidationError) -> list[str]:
    found = []
    for problem in error.errors():
        field = str(problem["loc"][0]) if problem["loc"] else ""
        if field == "statement":
            found.append(_("Écrivez l'hypothèse (1 000 caractères au plus)."))
        elif field == "family":
            found.append(_("Le nom d'une famille compte de 1 à 30 caractères."))
        elif field == "effect":
            found.append(_("Effet testé incomplet : {detail}.").format(detail=problem["msg"]))
        else:
            text = _("Hypothèse incomplète : {field} ({detail}).")
            found.append(text.format(field=field, detail=problem["msg"]))
    return list(dict.fromkeys(found))


def _default_effect(data: dict) -> dict | None:
    key = data.get("analysis")
    allowed = EFFECTS.get(key, ())
    if len(allowed) == 1 and allowed[0] != "pair":
        return {"kind": allowed[0]}
    if key == "correlation" and len(data.get("roles", {}).get("variables", [])) == 2:
        return {"kind": "pair", "variables": data["roles"]["variables"]}
    return None


def build(project: Project, data: dict, hypothesis_id: str) -> Hypothesis:
    """An hypothesis from its fields, completed as the sheet says: the catalogue's default
    options, the effect when there is no choice, and a t test's one-sided option from its
    expected direction (unless the team chose the option itself). Raises PlanRefused."""
    data = dict(data)
    key = data.get("analysis")
    given = dict(data.get("options") or {})
    if key in CATALOGUE:
        options = {k: v[0] for k, v in CATALOGUE[key].options.items()} | given
        direction = data.get("direction")
        if key in ONE_SIDED and direction in ALTERNATIVE and "alternative" not in given:
            options["alternative"] = ALTERNATIVE[direction]
        data["options"] = options
    if data.get("effect") is None:
        effect = _default_effect(data)
        if effect is None:
            if key == "regression":
                raise PlanRefused([_("Choisissez l'effet testé : le modèle ou un prédicteur.")])
            if key == "correlation":
                raise PlanRefused([_("Choisissez la paire testée.")])
            effect = {"kind": "difference"}  # refused by review(), with its reason
        data["effect"] = effect
    if not data.get("family"):
        data["family"] = None
    try:
        return Hypothesis.model_validate({**data, "id": hypothesis_id})
    except ValidationError as error:
        raise PlanRefused(_incomplete(error)) from None


def _kept(project: Project, hypothesis: Hypothesis, data: PreparedData | None) -> None:
    found = review(project, hypothesis, data)
    if not found.ok:
        raise PlanRefused(found.refusals)


# --- Changing the plan; after it was frozen, every change is an amendment. ---


def _reason(project: Project, reason: str | None) -> str | None:
    if project.plan.frozen is None:
        return None
    if not (reason or "").strip():
        raise PlanRefused([_("Le plan est arrêté : donnez la raison de cette modification.")])
    return reason.strip()


def _amend(project, reason, target, change, before, after, today) -> None:
    if reason is None:
        return
    project.plan.amendments.append(
        Amendment(
            date=_today(today),
            target=target,
            change=change,
            reason=reason,
            before=before,
            after=after,
        )
    )


def _dump(hypothesis: Hypothesis) -> dict:
    return hypothesis.model_dump(mode="json", exclude={"id"})


def find(project: Project, hypothesis_id: str) -> Hypothesis:
    for hypothesis in project.plan.hypotheses:
        if hypothesis.id == hypothesis_id:
            return hypothesis
    raise PlanRefused([_("{id} : aucune hypothèse ne porte ce numéro.").format(id=hypothesis_id)])


def add(
    project: Project,
    data: dict,
    prepared: PreparedData | None = None,
    reason: str | None = None,
    today: str | None = None,
) -> Hypothesis:
    """A new hypothesis at the end, with the next identifier. Raises PlanRefused."""
    reason = _reason(project, reason)
    hypothesis = build(project, data, f"H{project.plan.next_id}")
    _kept(project, hypothesis, prepared)
    project.plan.hypotheses.append(hypothesis)
    project.plan.next_id += 1
    _amend(project, reason, hypothesis.id, "added", {}, _dump(hypothesis), today)
    return hypothesis


def modify(
    project: Project,
    hypothesis_id: str,
    changes: dict,
    prepared: PreparedData | None = None,
    reason: str | None = None,
    today: str | None = None,
) -> Hypothesis:
    """The hypothesis with these fields changed, checked again. Nothing changed: nothing
    happens, not even an amendment. Raises PlanRefused."""
    old = find(project, hypothesis_id)
    before = _dump(old)
    data = before | changes
    if "analysis" in changes and changes["analysis"] != old.analysis:
        if "effect" not in changes:
            data["effect"] = None
        if "options" not in changes:
            data["options"] = {}
    elif "roles" in changes and "effect" not in changes and old.effect.kind == "pair":
        data["effect"] = None  # a correlation of two variables: its one pair again
    if "direction" in changes and "options" not in changes and old.analysis in ONE_SIDED:
        data["options"] = {k: v for k, v in data["options"].items() if k != "alternative"}
    new = build(project, data, old.id)
    after = _dump(new)
    if after == before:
        return old
    reason = _reason(project, reason)
    _kept(project, new, prepared)
    hypotheses = project.plan.hypotheses
    hypotheses[hypotheses.index(old)] = new
    changed = [k for k in after if after[k] != before.get(k)]
    _amend(
        project,
        reason,
        old.id,
        "modified",
        {k: before[k] for k in changed},
        {k: after[k] for k in changed},
        today,
    )
    return new


def remove(
    project: Project, hypothesis_id: str, reason: str | None = None, today: str | None = None
) -> None:
    hypothesis = find(project, hypothesis_id)
    reason = _reason(project, reason)
    project.plan.hypotheses.remove(hypothesis)
    _amend(project, reason, hypothesis.id, "removed", _dump(hypothesis), {}, today)


def move(project: Project, hypothesis_id: str, position: int) -> None:
    """Put an hypothesis at this rank (1 is the first): only the order of the article, not
    in the plan's fingerprint, so never an amendment."""
    hypothesis = find(project, hypothesis_id)
    hypotheses = project.plan.hypotheses
    hypotheses.remove(hypothesis)
    position = max(1, min(position, len(hypotheses) + 1))
    hypotheses.insert(position - 1, hypothesis)


def set_rules(
    project: Project, changes: dict, reason: str | None = None, today: str | None = None
) -> None:
    """Change the general rules of the plan. Raises PlanRefused."""
    unknown = [k for k in changes if k not in RULE_FIELDS]
    if unknown:
        raise PlanRefused([_("Règle inconnue : {name}.").format(name=", ".join(unknown))])
    current = project.plan.model_dump(mode="json")
    before = {k: current[k] for k in RULE_FIELDS}
    try:
        checked = Plan.model_validate(before | changes)
    except ValidationError as error:
        found = []
        for problem in error.errors():
            field = str(problem["loc"][0]) if problem["loc"] else ""
            if field == "alpha":
                found.append(_("Le seuil α est un nombre strictement entre 0 et 1."))
            elif field == "sample_size":
                found.append(_("La taille d'échantillon tient en 2 000 caractères au plus."))
            else:
                found.append(_("{field} : choix non permis.").format(field=field))
        raise PlanRefused(list(dict.fromkeys(found))) from None
    after = {k: getattr(checked, k) for k in RULE_FIELDS}
    changed = [k for k in RULE_FIELDS if after[k] != before[k]]
    if not changed:
        return
    reason = _reason(project, reason)
    for k in changed:
        setattr(project.plan, k, after[k])
    _amend(
        project,
        reason,
        "rules",
        "modified",
        {k: before[k] for k in changed},
        {k: after[k] for k in changed},
        today,
    )


# --- The fingerprint, freezing, removing the whole plan. ---


def plan_content(plan: Plan) -> dict:
    """What the plan's fingerprint is computed from: the rules and the hypotheses, in the
    order of their identifiers (their order in the article is not a decision of the plan).
    Neither the freezing nor the amendments."""
    data = plan.model_dump(mode="json")
    hypotheses = sorted(data["hypotheses"], key=lambda h: int(h["id"][1:]))
    return {**{k: data[k] for k in RULE_FIELDS}, "hypotheses": hypotheses}


def plan_fingerprint(plan: Plan) -> str:
    text = json.dumps(plan_content(plan), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def freeze_refusals(project: Project, prepared: PreparedData | None = None) -> list[str]:
    """Why the plan cannot be frozen; empty when it can."""
    plan = project.plan
    found = []
    if plan.frozen is not None:
        found.append(_("Le plan est déjà arrêté."))
    if not plan.hypotheses:
        found.append(_("Le plan n'a aucune hypothèse."))
    if plan.alpha is None:
        found.append(_("Tapez le seuil α du plan."))
    if plan.data_origin is None or plan.data_status is None:
        found.append(_("Dites l'origine des données et leur état quand le plan a été écrit."))
    for hypothesis in plan.hypotheses:
        for reason in review(project, hypothesis, prepared).refusals:
            found.append(f"{hypothesis.id} : {reason}")
    return found


def freeze(project: Project, prepared: PreparedData | None = None, today: str | None = None):
    """Give the plan its date and fingerprint (D-102). Raises PlanRefused. The planned
    analyses the notebook already held are listed in step 3."""
    found = freeze_refusals(project, prepared)
    if found:
        raise PlanRefused(found)
    project.plan.frozen = Frozen(date=_today(today), fingerprint=plan_fingerprint(project.plan))
    return project.plan.frozen


def clear(project: Project) -> None:
    """Remove the whole plan, its freezing and its amendments: the only way back from a
    frozen plan, which a person confirms first."""
    project.plan = Plan()


# --- What the page and the command line give (v0.13, step 6). ---


def data_from_names(
    project: Project,
    statement: str,
    analysis: str,
    chosen: dict[str, list[str]],
    options: dict[str, str] | None = None,
    *,
    pair: list[str] | None = None,
    predictor: str | None = None,
    model: bool = False,
    direction: str | None = None,
    kind: str = "confirmatory",
    family: str | None = None,
) -> dict:
    """The fields of an hypothesis from final names, as `add` and `modify` take them; the
    effect from the pair, the predictor or the model chosen (none: the default one).
    Raises PlanRefused for a name the project does not know."""

    def ref(name: str) -> dict:
        try:
            return reference(project, name).model_dump(mode="json")
        except NotebookError as error:
            raise PlanRefused([reason_text(error)]) from None

    order = [r.key for r in CATALOGUE[analysis].roles] if analysis in CATALOGUE else list(chosen)
    data: dict = {
        "statement": statement,
        "analysis": analysis,
        "roles": {role: [ref(n) for n in chosen[role]] for role in order if chosen.get(role)},
        "options": dict(options or {}),
        "direction": direction or None,
        "kind": kind,
        "family": family or None,
    }
    if pair:
        data["effect"] = {"kind": "pair", "variables": [ref(n) for n in pair]}
    elif predictor:
        data["effect"] = {"kind": "predictor", "variable": ref(predictor)}
    elif model:
        data["effect"] = {"kind": "model"}
    return data
