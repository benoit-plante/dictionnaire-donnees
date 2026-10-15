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
        score_name=score_name.strip() if items else None,
        source=source.strip(),
        note=note or None,
    )
    try:
        sc.set_scoring(project, group_id, scoring)
    except sc.ScoringError as error:
        raise ReviewError(" ".join(SCORING_PROBLEMS[p] for p in error.problems)) from error


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
