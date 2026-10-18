"""What the review interface does to a project, without any interface.

Each function changes the project in memory and returns nothing; the interface saves the
project after each call. Errors are ReviewError with a French message for the person.
"""

from __future__ import annotations

from typing import Literal

from pydantic import ValidationError

from ddict import glossary, i18n
from ddict.export.wording import entry_anomalies
from ddict.i18n import N_, Texts, _, quoted
from ddict.project import completeness
from ddict.project.decisions import DecisionError, correct, enter, reject, validate
from ddict.project.model import (
    Group,
    Project,
    SentinelDecision,
    SourcedText,
    TheoreticalRange,
    Threshold,
    TrackedValue,
    VariableEntry,
)
from ddict.questionnaire import link
from ddict.questionnaire.labels import propose_value_labels

Field = Literal["label", "description", "unit", "question", "value_labels"]
Action = Literal["accept", "correct", "reject"]
Filter = Literal["all", "to_review", "flagged", "sensitive", "unlinked", "suspects"]

PRIVACY_CLASSES = ("ordinary", "likely_identifier", "free_text", "quasi_identifier")

SIGNALS = Texts(
    {
        "citation": N_("ressemble à une citation"),
        "threshold": N_("ressemble à un seuil"),
        "instrument": N_("ressemble à un nom d'instrument"),
        "acronym": N_("donne le sens d'un sigle absent du glossaire"),
        "observed_range": N_(
            "présente l'étendue observée comme celle de l'échelle : à vérifier dans le manuel"
        ),
        "no_file_label": N_("deviné : la variable n'a pas d'étiquette dans le fichier"),
        "computed_disagrees": N_(
            "s'écarte du choix sûr du calcul : comparez avec la première question de la liste"
        ),
    }
)
FIELD_NAMES = Texts(
    {
        "label": N_("Libellé"),
        "description": N_("Description"),
        "issues": N_("Signalement"),
        "question": N_("Question"),
        "value_labels": N_("Étiquettes de valeurs"),
    }
)

# French messages for the fields of the human-only models; "" is a rule on the whole value.
FIELD_PROBLEMS = Texts(
    {
        "source": N_("Une source documentée est obligatoire."),
        "meaning": N_("La signification du seuil est obligatoire."),
        "value": N_("La valeur est obligatoire."),
        "": N_("Étendue invalide : le minimum doit être inférieur au maximum."),
    }
)


class ReviewError(ValueError):
    """A decision that cannot be recorded; the message is for the person."""


def is_sensitive(entry: VariableEntry) -> bool:
    return (entry.privacy.privacy_class.value or "ordinary") != "ordinary"


def pending(entry: VariableEntry) -> list[str]:
    """Fields with an AI proposal waiting for a decision."""
    names = ("question", "value_labels", "label", "description")
    fields = [f for f in names if getattr(entry, f).status == "proposed"]
    fields += ["issues"] * sum(1 for i in entry.issues if i.status == "proposed")
    return fields


def is_flagged(entry: VariableEntry) -> bool:
    return bool(entry_anomalies(entry) or entry.ai_signals)


def has_undecided_suspects(entry: VariableEntry) -> bool:
    """A suspect missing code the team has not settled yet (D-028)."""
    decided = {d.code for d in entry.sentinel_decisions}
    return any(code not in decided for code in entry.profile.suspect_missing_codes)


def select(project: Project, which: Filter) -> list[VariableEntry]:
    tests = {
        "all": lambda e: True,
        "to_review": lambda e: bool(pending(e)),
        "flagged": is_flagged,
        "sensitive": is_sensitive,
        "unlinked": lambda e: project.questionnaire is not None and not link.is_linked(e),
        "suspects": has_undecided_suspects,
    }
    return [e for e in project.variables if tests[which](e)]


def codebook_progress(project: Project) -> float:
    """How far the codebook is documented, from 0 to 1 (v0.16): the mean of its parts, as the
    page "Base" lists them (questions, labels, value labels, levels, scorings...), the
    description of the database being one of them. A file that brings its labels does not
    make a new project look finished: each part counts the same."""
    shares = [p.done / p.applicable for p in completeness.parts(project) if p.applicable]
    shares.append(1 - len(completeness.dataset_missing(project)) / 2)
    return sum(shares) / len(shares)


def progress(project: Project) -> tuple[int, int]:
    """Variables without pending proposal, out of all variables."""
    done = sum(1 for e in project.variables if not pending(e))
    return done, len(project.variables)


def signal_texts(entry: VariableEntry) -> list[str]:
    texts = []
    for signal in entry.ai_signals:
        field, _sep, code = signal.partition(":")
        texts.append(f"{FIELD_NAMES.get(field, field)} {SIGNALS.get(code, code)}")
    return texts


def decide(
    project: Project,
    name: str,
    field: Field,
    action: Action,
    *,
    now: str,
    value: str | None = None,
) -> None:
    """Accept, correct or reject the value of a field of a variable."""
    entry = project.variable(name)
    tracked: TrackedValue[str] = getattr(entry, field)
    try:
        if action == "accept":
            new = validate(tracked, now=now)
        elif action == "reject":
            new = reject(tracked, now=now)
        else:
            text = (value or "").strip()
            if not text:
                raise ReviewError(_("La valeur corrigée est vide."))
            new = correct(tracked, text, now=now)
    except DecisionError as error:
        raise ReviewError(_("Décision impossible : {detail}").format(detail=error)) from error
    setattr(entry, field, new)
    if field == "question":
        propose_value_labels(project)
    if action in ("accept", "correct", "reject"):
        # A decision on the field settles its signals.
        entry.ai_signals = [s for s in entry.ai_signals if not s.startswith(f"{field}:")]


def write(project: Project, name: str, field: Field, value: str, *, now: str) -> None:
    """Enter or change a value by hand, whatever its origin."""
    entry = project.variable(name)
    tracked: TrackedValue[str] = getattr(entry, field)
    text = value.strip() or None
    if tracked.origin == "human":
        setattr(entry, field, enter(tracked, text, now=now))
    elif text is not None and text != tracked.value:
        decide(project, name, field, "correct", now=now, value=text)


def link_question(project: Project, name: str, target_id: str | None, *, now: str) -> None:
    """Link a variable to a question, a row or an option, or to none (link.NO_QUESTION).

    Choosing what the model proposed accepts it; choosing something else corrects it.
    """
    if target_id is None:  # the list starts on no choice (v0.16, D-126)
        raise ReviewError(_("Choisissez une question, ou « Aucune question du questionnaire »."))
    if target_id != link.NO_QUESTION and link.target(project.questionnaire, target_id) is None:
        raise ReviewError(_("Question inconnue : {id}").format(id=target_id))
    entry = project.variable(name)
    tracked: TrackedValue[str] = entry.question
    if tracked.origin == "ai" and tracked.value == target_id and tracked.status != "corrected":
        entry.question = validate(tracked, now=now)
    elif tracked.origin == "human":
        entry.question = enter(tracked, target_id, now=now)
    else:
        entry.question = correct(tracked, target_id, now=now)
    # A person decided: the signals on the link are settled (D-041).
    entry.ai_signals = [s for s in entry.ai_signals if not s.startswith("question:")]
    propose_value_labels(project)


def decide_sentinel(project: Project, name: str, code, missing: bool | None, *, now: str) -> None:
    """A suspect missing code is a missing code (True) or a real value (False); None takes
    the decision back (D-028)."""
    entry = project.variable(name)
    if code not in entry.profile.suspect_missing_codes:
        raise ReviewError(
            _("{code} n'est pas un code suspect de cette variable.").format(code=code)
        )
    kept = [d for d in entry.sentinel_decisions if d.code != code]
    if missing is not None:
        kept.append(SentinelDecision(code=code, missing=missing, updated_at=now))
    order = list(entry.profile.suspect_missing_codes)
    entry.sentinel_decisions = sorted(kept, key=lambda d: order.index(d.code))


def decide_issue(project: Project, name: str, index: int, action: Action, *, now: str) -> None:
    entry = project.variable(name)
    issue = entry.issues[index]
    entry.issues[index] = validate(issue, now=now) if action == "accept" else reject(issue, now=now)


def set_project_language(project: Project, language: str) -> None:
    """The language of the study: its questionnaire and labels (v0.5, D-032)."""
    if language not in i18n.LANGUAGES:
        raise ReviewError(_("Langue inconnue : {language}").format(language=language))
    project.settings.language = language


def set_privacy(project: Project, name: str, privacy_class: str, *, now: str) -> None:
    """Confirm the computed class, or change it."""
    if privacy_class not in PRIVACY_CLASSES:
        raise ReviewError(_("Classe de confidentialité inconnue : {c}").format(c=privacy_class))
    privacy = project.variable(name).privacy
    tracked = privacy.privacy_class
    if privacy_class == tracked.value:
        privacy.privacy_class = validate(tracked, now=now)
    else:
        privacy.privacy_class = correct(tracked, privacy_class, now=now)


def _sourced(build):
    try:
        return build()
    except ValidationError as error:
        problems = {str(e["loc"][-1]) if e["loc"] else "" for e in error.errors()}
        messages = [text for field, text in FIELD_PROBLEMS.items() if field in problems]
        raise ReviewError(" ".join(messages) or _("Valeur invalide.")) from error


def _all_said(missing: list[str], build):
    """Build a sourced value, saying the missing numbers with the other problems."""
    try:
        built = _sourced(build)
    except ReviewError as error:
        raise ReviewError(" ".join([*missing, str(error)])) from error
    if missing:
        raise ReviewError(" ".join(missing))
    return built


def add_threshold(
    project: Project, name: str, value: float | None, meaning: str, source: str
) -> None:
    # The field starts empty (v0.16, D-126): said with what else is missing.
    missing = [_("Tapez la valeur du seuil.")] if value is None else []
    threshold = _all_said(
        missing, lambda: Threshold(value=value or 0, meaning=meaning, source=source)
    )
    project.variable(name).thresholds.append(threshold)


def remove_threshold(project: Project, name: str, index: int) -> None:
    del project.variable(name).thresholds[index]


def set_theoretical_range(
    project: Project, name: str, low: float | None, high: float | None, source: str
) -> None:
    empty = low is None or high is None  # the fields start empty (v0.16, D-126)
    missing = [_("Tapez le minimum et le maximum de l'étendue.")] if empty else []
    value = _all_said(
        missing,
        lambda: TheoreticalRange(min=0 if empty else low, max=1 if empty else high, source=source),
    )
    project.variable(name).theoretical_range = value


def clear_theoretical_range(project: Project, name: str) -> None:
    project.variable(name).theoretical_range = None


def set_references(project: Project, name: str, text: str) -> None:
    project.variable(name).references = [line.strip() for line in text.splitlines() if line.strip()]


def set_notes(project: Project, name: str, text: str) -> None:
    project.variable(name).notes = text.strip() or None


def set_references_and_notes(project: Project, name: str, references: str, notes: str) -> None:
    set_references(project, name, references)
    set_notes(project, name, notes)


def group(project: Project, group_id: str) -> Group:
    for found in project.groups:
        if found.group_id == group_id:
            return found
    raise KeyError(group_id)


def glossary_decide(project: Project, term: str, action: Action, *, now: str) -> None:
    """Accept or reject an acronym found in the questionnaire (D-015)."""
    try:
        glossary.decide(project, term, action, now=now)
    except glossary.GlossaryError as error:
        raise ReviewError(str(error)) from error


def glossary_write(project: Project, term: str, meaning: str, *, now: str) -> None:
    """Define an acronym, or change its meaning."""
    try:
        glossary.write(project, term, meaning, now=now)
    except glossary.GlossaryError as error:
        raise ReviewError(str(error)) from error


def glossary_accept(project: Project, term: str, shown: str, *, now: str) -> None:
    """Accept the meaning shown in the field (v0.16, D-121): the questionnaire's, validated;
    or the person's correction, kept with the questionnaire's as its origin."""
    current = glossary.entry(project, term)
    if current is None or current.status != "proposed":
        raise ReviewError(
            _("Ce sigle n'attend plus de décision : {term}.").format(term=quoted(term))
        )
    glossary_write(project, term, shown, now=now)


def glossary_proposals(project: Project) -> list[str]:
    """The acronyms of the questionnaire that wait for a decision."""
    return [e.term for e in project.glossary if e.status == "proposed"]


def accept_glossary(project: Project, shown: dict[str, str], terms: list[str], *, now: str) -> None:
    """Accept these acronyms, each with the meaning shown in the list, one decision each."""
    allowed = set(glossary_proposals(project))
    outside = [t for t in terms if t not in allowed]
    if outside:
        raise ReviewError(
            _("Ces sigles n'attendent plus de décision : {terms}.").format(terms=", ".join(outside))
        )
    if not terms:
        raise ReviewError(_("Aucun sigle coché."))
    for term in terms:
        glossary_accept(project, term, shown[term], now=now)


def set_instrument(project: Project, group_id: str, value: str, source: str) -> None:
    target = group(project, group_id)
    if not value.strip():
        target.instrument_name = None
        return
    target.instrument_name = _sourced(lambda: SourcedText(value=value, source=source))


def set_omit_question_text(project: Project, group_id: str, omit: bool) -> None:
    """D-014: leave the words of this group's questions out of the exports (copyright)."""
    group(project, group_id).omit_question_text = bool(omit)


def set_reverse_items(project: Project, group_id: str, names: list[str]) -> None:
    target = group(project, group_id)
    members = target.members.value or []
    unknown = [n for n in names if n not in members]
    if unknown:
        raise ReviewError(_("Pas dans le groupe : {names}").format(names=", ".join(unknown)))
    target.reverse_items = [n for n in members if n in names]


# --- v0.4, step 5: grouped decisions, shown first (D-029). ---


def agreeing_links(project: Project) -> list[str]:
    """Variables whose link proposed by the model is also what the tool computes first."""
    if project.questionnaire is None:
        return []
    computed = link.best_guess(project)
    return [
        e.name
        for e in project.variables
        if e.question.origin == "ai"
        and e.question.status == "proposed"
        and e.question.value is not None
        and computed.get(e.name) == e.question.value
    ]


def accept_links(project: Project, names: list[str], *, now: str) -> None:
    """Accept the links of these variables, one decision each; only those that agree."""
    allowed = set(agreeing_links(project))
    outside = [n for n in names if n not in allowed]
    if outside:
        raise ReviewError(
            _("Ces rattachements ne sont plus en accord : {names}.").format(
                names=", ".join(outside)
            )
        )
    if not names:
        raise ReviewError(_("Aucune variable cochée."))
    for name in names:
        decide(project, name, "question", "accept", now=now)


def group_label_proposals(project: Project, group_id: str) -> list[str]:
    """Members of a group whose value labels from the questionnaire wait for a decision."""
    members = group(project, group_id).members.value or []
    return [n for n in members if project.variable(n).value_labels.status == "proposed"]


def accept_group_labels(project: Project, group_id: str, names: list[str], *, now: str) -> None:
    """Accept the value labels of these members of the group, one decision each."""
    allowed = set(group_label_proposals(project, group_id))
    outside = [n for n in names if n not in allowed]
    if outside:
        raise ReviewError(
            _("Ces étiquettes n'attendent plus de décision dans ce groupe : {names}.").format(
                names=", ".join(outside)
            )
        )
    if not names:
        raise ReviewError(_("Aucune variable cochée."))
    for name in names:
        decide(project, name, "value_labels", "accept", now=now)
