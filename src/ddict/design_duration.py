"""The estimated duration of a designed questionnaire (v0.21, D-171), computed on the
questionnaire alone:

    duration = words read ÷ reading speed + Σ answering times

The words are counted as Word does (runs separated by spaces): the sections' titles and
instructions, each question's text and instruction, its choices once, a grid's statements and
its columns once, the displayed texts. The reading speed is taken from a published source, the
IReST texts read aloud (Trauzettel-Klosinski and Dietz, 2012): reading silently is quicker,
so the duration is rather overestimated, which suits a duration announced to a committee. The
answering times are the tool's own marks, said as such wherever the duration shows, to be
calibrated by the pilot.

With filters, a range: from the shortest path (no filtered question asked) to the longest
(all asked), without enumerating the paths.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ddict import design
from ddict.i18n import _
from ddict.project import skip
from ddict.project.model import Project, Question

# Words per minute, standardized texts read aloud (IReST, table of the article).
SPEEDS = {"fr": 195, "en": 228}
SOURCE = "Trauzettel-Klosinski et Dietz (2012), IOVS 53(9), 5452-5461"
# Seconds to answer, after reading: the tool's marks, with no primary source found.
CLOSED, SHORT, LONG = 3, 10, 60


@dataclass(frozen=True)
class Part:
    """What a path through the questionnaire asks to read and to answer."""

    words: int = 0
    closed: int = 0  # a choice, a grid's statement, a whole checkbox question
    short: int = 0  # a short text, a number, a date
    long: int = 0  # a long text

    def __add__(self, other: Part) -> Part:
        return Part(
            self.words + other.words,
            self.closed + other.closed,
            self.short + other.short,
            self.long + other.long,
        )

    def seconds(self, speed: int) -> float:
        return (
            self.words * 60 / speed + self.closed * CLOSED + self.short * SHORT + self.long * LONG
        )


@dataclass(frozen=True)
class Duration:
    shortest: Part
    longest: Part
    speed: int

    @property
    def low(self) -> int:
        return _minutes(self.shortest.seconds(self.speed))

    @property
    def high(self) -> int:
        return _minutes(self.longest.seconds(self.speed))

    @property
    def filtered(self) -> bool:
        return self.shortest != self.longest


def _minutes(seconds: float) -> int:
    """Rounded to the minute, half up; at least one minute for a questionnaire that asks."""
    return max(1, math.floor(seconds / 60 + 0.5)) if seconds > 0 else 0


def words(text: str | None) -> int:
    return len(text.split()) if text else 0


def _question(question: Question) -> Part:
    read = words(question.text) + words(question.instruction)
    read += sum(words(o.text) for o in question.options)
    read += sum(words(r.text) for r in question.rows)
    if question.kind in ("single", "checkbox"):
        return Part(read, closed=1)
    if question.kind == "grid":
        return Part(read, closed=len(question.rows))
    if question.kind == "open":
        return Part(read, long=1) if question.answer == "long" else Part(read, short=1)
    return Part(read)  # a displayed text: read, not answered


def estimate(project: Project) -> Duration:
    found = design.questionnaire(project)
    always, filtered = Part(), Part()
    for section in found.sections:
        part = Part(words(section.title) + words(section.instruction))
        if section.condition is None:
            always += part
        else:
            filtered += part
    for question in found.questions:
        if skip.effective(found, question):
            filtered += _question(question)
        else:
            always += _question(question)
    speed = SPEEDS.get(project.settings.language, SPEEDS["fr"])
    return Duration(always, always + filtered, speed)


def text(duration: Duration) -> str:
    """ "environ 11 à 14 minutes", "environ 12 minutes"."""
    if duration.low == duration.high:
        if duration.high <= 1:
            return _("environ une minute")
        return _("environ {n} minutes").format(n=duration.high)
    return _("environ {low} à {high} minutes").format(low=duration.low, high=duration.high)


def formula(duration: Duration) -> list[str]:
    """The formula and its terms, one line each, for the review and the working Word."""

    def terms(part: Part) -> str:
        counts = [
            (part.words, _("{n} mot lu"), _("{n} mots lus")),
            (part.closed, _("{n} réponse fermée"), _("{n} réponses fermées")),
            (part.short, _("{n} réponse courte"), _("{n} réponses courtes")),
            (part.long, _("{n} réponse longue"), _("{n} réponses longues")),
        ]
        return ", ".join((one if n <= 1 else many).format(n=n) for n, one, many in counts)

    lines = [
        _(
            "Durée = mots lus ÷ vitesse de lecture + temps de réponse ({closed} s par réponse "
            "fermée, {short} s par réponse courte, nombre ou date, {long} s par réponse longue)."
        ).format(closed=CLOSED, short=SHORT, long=LONG),
        _(
            "Vitesse de lecture : {speed} mots par minute, textes standardisés lus à voix haute "
            "(IReST, {source}) ; une lecture silencieuse est plus rapide, la durée est donc "
            "plutôt surestimée."
        ).format(speed=duration.speed, source=SOURCE),
        _(
            "Les temps de réponse sont des repères de l'outil, sans source publiée : le pilote "
            "les recalibrera."
        ),
    ]
    if duration.filtered:
        lines.append(
            _("Chemin le plus court (aucune question filtrée posée) : {terms}.").format(
                terms=terms(duration.shortest)
            )
        )
        lines.append(
            _("Chemin le plus long (toutes posées) : {terms}.").format(
                terms=terms(duration.longest)
            )
        )
    else:
        lines.append(_("Questionnaire : {terms}.").format(terms=terms(duration.longest)))
    return lines
