"""The language of a study (v0.5, D-032): French or English, guessed from its own words.

The language of the project is that of its questionnaire and labels: the model writes the
labels in it (step 5). It is guessed from the words of the questionnaire, or of the file's
labels, and a person can change it on the "Base" page.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ddict.project.model import Project

WORDS = {
    "fr": {
        "le", "la", "les", "des", "du", "de", "un", "une", "et", "est", "vous", "votre",
        "vos", "avez", "quel", "quelle", "pour", "dans", "sur", "au", "aux", "pas", "ou",
        "nombre", "oui", "non",
    },
    "en": {
        "the", "a", "an", "of", "and", "is", "are", "you", "your", "do", "how", "what",
        "which", "for", "in", "on", "at", "to", "not", "or", "number", "yes", "no",
    },
}  # fmt: skip
_WORD = re.compile(r"[a-zà-ÿ]+")
MIN_WORDS = 5  # fewer telling words: no guess


def guess(texts: Iterable[str]) -> str | None:
    """ "fr" or "en" when the words say so clearly, else None."""
    counts = {language: 0 for language in WORDS}
    for text in texts:
        for word in _WORD.findall(text.lower()):
            for language, words in WORDS.items():
                if word in words:
                    counts[language] += 1
    best = max(counts, key=counts.get)
    others = sum(n for language, n in counts.items() if language != best)
    if counts[best] >= MIN_WORDS and counts[best] >= 2 * others:
        return best
    return None


def project_texts(project: Project) -> list[str]:
    """The study's own words: the questionnaire's questions, else the file's labels."""
    if project.questionnaire is not None:
        found = []
        for question in project.questionnaire.questions:
            found.append(question.text)
            found += [o.text for o in question.options] + [r.text for r in question.rows]
        return found
    texts = [e.file.label or "" for e in project.variables]
    texts += [v.label for e in project.variables for v in e.file.value_labels]
    return texts


def update(project: Project) -> str:
    """Set the project's language from its words, when they are clear; returns it."""
    found = guess(project_texts(project))
    if found:
        project.settings.language = found
    return project.settings.language
