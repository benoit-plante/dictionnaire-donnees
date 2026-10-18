"""The scoring of a group and the description of the database (v0.8, step 4), without
Streamlit: written by a person, checked here, with a message a person can act on."""

from __future__ import annotations

from ddict.i18n import N_, Texts, _
from ddict.project import dataset as ds
from ddict.project import scoring as sc
from ddict.project.decisions import correct, reject, validate
from ddict.project.model import DesignVariables, Project, Scoring, TrackedValue
from ddict.review.logic import ReviewError, group

SCORING_PROBLEMS = Texts(
    {
        "kind": N_("Un groupe de cases à cocher n'a pas de cotation."),
        "items": N_("Ces items ne sont pas tous dans le groupe."),
        "score_name": N_(
            "Nom de score invalide : minuscules, chiffres et « _ », une lettre au début, "
            "différent des noms des variables."
        ),
        "score_name_taken": N_("Ce nom de score est déjà celui d'un autre groupe."),
    }
)


def set_scoring(
    project: Project,
    group_id: str,
    items: list[str],
    aggregation: str,
    scale_min: float | None,
    scale_max: float | None,
    min_items: int | None,
    score_name: str,
    source: str,
    note: str,
    missing_rule: str = "prorate",
) -> None:
    """The scoring a person wrote (D-060): structured when items are chosen, else a note.
    The source is required either way."""
    target = group(project, group_id)
    items = [n for n in target.members.value or [] if n in items]
    note = (note or "").strip()
    if not (source or "").strip():
        raise ReviewError(_("La cotation exige une source documentée (manuel, article)."))
    if not items and not note:
        raise ReviewError(_("Choisissez les items du score, ou décrivez la cotation en note."))
    if items:
        if not (score_name or "").strip():
            raise ReviewError(_("Donnez un nom au score."))
        if scale_min is None or scale_max is None or scale_min >= scale_max:
            raise ReviewError(_("Le minimum de l'échelle doit être inférieur à son maximum."))
        if min_items and min_items > len(items):
            raise ReviewError(
                _("Le nombre minimal d'items répondus dépasse le nombre d'items ({n}).").format(
                    n=len(items)
                )
            )
    scoring = Scoring(
        items=items,
        aggregation=aggregation if items else None,
        scale_min=scale_min if items else None,
        scale_max=scale_max if items else None,
        min_items_answered=(min_items or None) if items else None,
        missing_rule=missing_rule if missing_rule in ("prorate", "sum_answered") else "prorate",
        score_name=score_name.strip() if items else None,
        source=source.strip(),
        note=note or None,
    )
    try:
        sc.set_scoring(project, group_id, scoring)
    except sc.ScoringError as error:
        raise ReviewError(" ".join(SCORING_PROBLEMS[p] for p in error.problems)) from error


def set_scoring_chosen(
    project: Project,
    group_id: str,
    items: list[str],
    aggregation: str | None,
    scale_min: float | None,
    scale_max: float | None,
    least: int | None,
    score_name: str,
    source: str,
    note: str,
    missing_rule: str | None,
) -> None:
    """The scoring as the page's fields give it (v0.16, D-126): nothing is chosen by default,
    so a structured scoring says its calculation and how many items must be answered (0: all);
    a sum that accepts missing items says its rule."""
    if items and (source or "").strip():
        if aggregation is None:
            raise ReviewError(_("Choisissez le calcul du score : somme ou moyenne."))
        if least is None:
            raise ReviewError(
                _("Dites combien d'items doivent être répondus, au minimum (0 : tous).")
            )
        partial = 0 < int(least) < len(items)
        if aggregation == "sum" and partial and missing_rule is None:
            raise ReviewError(_("Choisissez comment la somme traite les items manquants."))
    set_scoring(
        project,
        group_id,
        items,
        aggregation or "sum",
        scale_min,
        scale_max,
        int(least or 0) or None,
        score_name,
        source,
        note,
        missing_rule or "prorate",
    )


def remove_scoring(project: Project, group_id: str) -> None:
    sc.set_scoring(project, group_id, None)


# --- The description of the database (D-064). ---


def decide_structure(project: Project, action: str, *, now: str) -> None:
    """Accept or reject the structure a rule proposes."""
    tracked = project.dataset.structure
    if tracked.status != "proposed":
        raise ReviewError(_("Aucune structure proposée."))
    project.dataset.structure = (validate if action == "accept" else reject)(tracked, now=now)


def set_dataset(
    project: Project,
    unit: str,
    unit_other: str,
    structure: str,
    wave: str,
    suffixes: str,
    design: dict[str, str],
    description: str,
    *,
    now: str,
) -> None:
    """What a person wrote of the database; an empty field is "not said"."""
    if unit and unit not in ds.UNITS:
        raise ReviewError(_("Unité d'observation inconnue."))
    if structure and structure not in ds.STRUCTURES:
        raise ReviewError(_("Structure inconnue."))
    names = {e.name for e in project.variables}
    unknown = [v for v in design.values() if v and v not in names]
    if unknown:
        raise ReviewError(_("Variables inconnues : {names}.").format(names=", ".join(unknown)))
    found = project.dataset
    found.unit_of_observation = unit or None
    found.unit_other = (unit_other or "").strip() or None if unit == "other" else None
    tracked = found.structure
    current = tracked.value if tracked.status != "proposed" else None
    if (structure or None) != current:
        if tracked.status == "proposed" and structure == tracked.value:
            found.structure = validate(tracked, now=now)  # the proposal, chosen
        elif structure and tracked.origin == "rule":
            found.structure = correct(tracked, structure, now=now)
        else:
            found.structure = TrackedValue[str](
                value=structure or None, origin="human", updated_at=now
            )
    found.wave = (wave or "").strip() or None
    found.time_suffixes = [s.strip() for s in (suffixes or "").split(",") if s.strip()]
    found.design = DesignVariables(**{k: (design.get(k) or None) for k in ds.DESIGN})
    found.description = (description or "").strip() or None


# --- One "Enregistrer" for each tab of a group (v0.16, D-124). ---


def save_items(
    project: Project, group_id: str, prefix: str | None, reverse: list[str], *, now: str
) -> None:
    """The tab "Items": the prefix of the new names (a scale only) and the reversed items,
    each saved when it changed. A refused prefix changes nothing."""
    from ddict.review import logic, names

    target = group(project, group_id)
    if prefix is not None and prefix.strip() != (target.name_prefix.value or ""):
        names.set_group_prefix(project, group_id, prefix, now=now)
    if list(reverse or []) != list(target.reverse_items):
        logic.set_reverse_items(project, group_id, list(reverse or []))


def save_instrument(
    project: Project, group_id: str, value: str, source: str, omit: bool | None
) -> None:
    """The tab "Instrument": its name with its source, and the choice not to reproduce the
    text of its questions (when there is a questionnaire), each saved when it changed."""
    from ddict.review import logic

    target = group(project, group_id)
    current = target.instrument_name
    if (value or "").strip() != (current.value if current else "") or (
        current is not None and (source or "").strip() != current.source
    ):
        logic.set_instrument(project, group_id, value or "", source or "")
    if omit is not None and bool(omit) != target.omit_question_text:
        logic.set_omit_question_text(project, group_id, omit)
