"""The glossary of acronyms (v0.2, D-015): found in the questionnaire or written by a person.

No model is involved, on purpose: acronyms are exactly what small models invent ("OCF" read
as "offices de contrôle" instead of "organismes communautaires Famille").

- `find_definitions` spots "long form (ACRONYM)" in the questionnaire, when the initials of
  the words before the parenthesis spell the acronym: "thérapie cognitivo-comportementale
  (TCC)", "l'Échelle fictive d'anxiété (EFA)". "Centre Jeunesse (DPJ)" does not qualify.
- `name_acronyms` lists the probable acronyms in variable names: a part of a name written
  in capitals in the questionnaire or a file label (OCF, ANX), or without any vowel (dpj).
"""

from __future__ import annotations

import re
import unicodedata

from ddict.project.model import GlossaryEntry, Project, Questionnaire

# Words that do not give an initial: "Questionnaire fictif du sommeil (QFS)".
STOP_WORDS = {
    "a", "à", "au", "aux", "d", "de", "des", "du", "en", "et", "l", "la", "le", "les",
    "par", "pour", "sur", "and", "for", "in", "of", "on", "the", "to",
}  # fmt: skip
# Short parts of names that are abbreviations of words or units, not acronyms to define.
NOT_ACRONYMS = {
    "nb", "nbr", "no", "id", "tx", "pct", "moy", "tot", "st", "dt", "q",
    "cm", "mm", "km", "kg", "mg", "ml", "hr", "hrs", "sec",
}  # fmt: skip
MAX_EXTRA_WORDS = 3  # stop words allowed inside a long form, beyond one word per letter

_DEFINED = re.compile(r"\(([A-Z][A-Z0-9]{1,7})\)")
_CAPITALS = re.compile(r"\b[A-Z][A-Z0-9]{1,7}\b")
_ELISION = re.compile(r"^(?:[dlj]|qu)['’]", re.IGNORECASE)
_VOWELS = set("aeiouy")


class GlossaryError(ValueError):
    """A glossary decision that cannot be recorded; the message is for the person."""


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def _initials(words: list[str]) -> list[str]:
    letters = []
    for word in words:
        for part in _ELISION.sub("", word).split("-"):
            plain = _plain(part).strip(".,;:!?«»\"'()")
            if plain and plain not in STOP_WORDS:
                letters.append(plain[0])
    return letters


def long_form(before: str, term: str) -> str | None:
    """The words just before "(TERM)" whose initials spell it, or None."""
    letters = [c for c in _plain(term) if c.isalpha()]
    if len(letters) < 2:
        return None
    words = before.split()
    for count in range(1, min(len(words), len(letters) + MAX_EXTRA_WORDS) + 1):
        chosen = words[-count:]
        if _plain(_ELISION.sub("", chosen[0]))[:1] in STOP_WORDS:
            continue  # a long form starts with a meaningful word
        if _initials(chosen) == letters:
            text = " ".join(chosen).strip(" ,;:")
            return _ELISION.sub("", text) if _ELISION.match(text) else text
    return None


def _questionnaire_texts(questionnaire: Questionnaire) -> list[tuple[int | None, str]]:
    found = []
    for question in questionnaire.questions:
        found.append((question.page, question.text))
        found += [(question.page, option.text) for option in question.options]
        found += [(question.page, row.text) for row in question.rows]
    found += [(text.page, text.text) for text in questionnaire.texts]
    return sorted(found, key=lambda item: item[0] or 0)


def find_definitions(questionnaire: Questionnaire) -> list[tuple[str, str, int | None]]:
    """(acronym, long form, page) for each acronym defined in the questionnaire, first
    definition kept, in page order."""
    found: dict[str, tuple[str, str, int | None]] = {}
    for page, text in _questionnaire_texts(questionnaire):
        for match in _DEFINED.finditer(text):
            term = match.group(1)
            meaning = long_form(text[: match.start()], term)
            if meaning and term.casefold() not in found:
                found[term.casefold()] = (term, meaning, page)
    return list(found.values())


def _source(questionnaire: Questionnaire, page: int | None) -> str:
    return f"{questionnaire.file_name}, p. {page}" if page else questionnaire.file_name


def entry(project: Project, term: str) -> GlossaryEntry | None:
    key = term.strip().casefold()
    return next((e for e in project.glossary if e.term.casefold() == key), None)


def propose_from_questionnaire(project: Project) -> list[GlossaryEntry]:
    """Add the acronyms defined in the questionnaire as proposals; return the new ones.

    An acronym the team already defined or decided on is left as it is; a pending
    proposal is refreshed, and one no longer found in the questionnaire is dropped.
    """
    definitions = find_definitions(project.questionnaire) if project.questionnaire else []
    terms = {term.casefold() for term, _meaning, _page in definitions}
    project.glossary = [
        e
        for e in project.glossary
        if not (e.status == "proposed" and e.term.casefold() not in terms)
    ]
    added = []
    for term, meaning, page in definitions:
        current = entry(project, term)
        proposal = GlossaryEntry(
            term=term,
            meaning=meaning,
            origin="questionnaire",
            status="proposed",
            source=_source(project.questionnaire, page),
        )
        if current is None:
            project.glossary.append(proposal)
            added.append(proposal)
        elif current.status == "proposed":
            project.glossary[project.glossary.index(current)] = proposal
    return added


def is_accepted(item: GlossaryEntry) -> bool:
    """Whether the entry may be used by the model and appear in the codebook."""
    return item.origin == "human" or item.status in ("validated", "corrected")


def decide(project: Project, term: str, action: str, *, now: str) -> None:
    """Accept or reject an acronym found in the questionnaire."""
    current = entry(project, term)
    if current is None or current.origin != "questionnaire":
        raise GlossaryError(f"Aucune proposition du questionnaire pour « {term} ».")
    status = {"accept": "validated", "reject": "rejected"}[action]
    index = project.glossary.index(current)
    project.glossary[index] = current.model_copy(update={"status": status, "updated_at": now})


def write(project: Project, term: str, meaning: str, *, now: str) -> None:
    """Define an acronym, or change its meaning; an empty meaning removes the team's own
    entry (an entry from the questionnaire is rejected instead)."""
    term, meaning = term.strip(), meaning.strip()
    if not term:
        raise GlossaryError("Le sigle est vide.")
    current = entry(project, term)
    if current is None:
        if not meaning:
            raise GlossaryError("La définition est vide.")
        project.glossary.append(
            GlossaryEntry(term=term, meaning=meaning, origin="human", updated_at=now)
        )
        return
    index = project.glossary.index(current)
    if current.origin == "human":
        if meaning:
            project.glossary[index] = current.model_copy(
                update={"meaning": meaning, "updated_at": now}
            )
        else:
            del project.glossary[index]
        return
    if not meaning:
        raise GlossaryError("La définition est vide ; utilisez « Rejeter ».")
    original = current.proposed_meaning or current.meaning
    if meaning == original:
        updated = {"meaning": meaning, "status": "validated", "proposed_meaning": None}
    else:
        updated = {"meaning": meaning, "status": "corrected", "proposed_meaning": original}
    project.glossary[index] = GlossaryEntry.model_validate(
        {**current.model_dump(), **updated, "updated_at": now}
    )


def name_parts(name: str) -> list[str]:
    return [part for part in re.split(r"[^a-z]+", _plain(name)) if part]


def _capital_words(project: Project) -> set[str]:
    texts = [e.file.label or "" for e in project.variables]
    if project.questionnaire:
        texts += [text for _page, text in _questionnaire_texts(project.questionnaire)]
    return {word.casefold() for text in texts for word in _CAPITALS.findall(text)}


def name_acronyms(project: Project) -> dict[str, list[str]]:
    """Probable acronyms in variable names, with the variables using each, in name order."""
    capitals = _capital_words(project)
    found: dict[str, list[str]] = {}
    for variable in project.variables:
        for part in dict.fromkeys(name_parts(variable.name)):
            if part in NOT_ACRONYMS or not 2 <= len(part) <= 6:
                continue
            if part in capitals or not (set(part) & _VOWELS):
                found.setdefault(part, []).append(variable.name)
    return found


def undefined_acronyms(project: Project) -> dict[str, list[str]]:
    """Probable acronyms of the names that have no entry yet, or only a rejected one."""
    return {
        part: names
        for part, names in name_acronyms(project).items()
        if (current := entry(project, part)) is None or current.status == "rejected"
    }


def variables_using(project: Project, term: str) -> list[str]:
    key = _plain(term)
    return [e.name for e in project.variables if key in name_parts(e.name)]
