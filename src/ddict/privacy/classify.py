"""Classify variables by how much they could reveal about a person.

The classification is a cautious guess, confirmed or changed by a person during review. It
looks at the name, the file label and the values themselves, so it runs in the
deterministic layer, before the privacy gate. Reasons are short codes, translated by the
interface.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from ddict.io.model import LoadedData, VariableMetadata
from ddict.profile.model import VariableProfile

PrivacyClass = Literal["likely_identifier", "free_text", "quasi_identifier", "ordinary"]
Reason = Literal[
    "identifier_name",
    "email_values",
    "phone_values",
    "unique_text_values",
    "free_text_name",
    "long_text_values",
    "birth_date_name",
    "birth_place_name",
    "postal_code_name",
    "postal_code_values",
    "wide_date_range",
]

# Short words must match a whole word of the name; long ones may appear inside it.
_IDENTIFIER_WORDS = {"id", "nom", "nas", "ramq", "tel", "ip", "name", "nam"}
_IDENTIFIER_PARTS = (
    "identif",  # not "ident", which is inside "accident"
    "matricule",
    "dossier",
    "courriel",
    "email",
    "mail",
    "prenom",
    "firstname",
    "lastname",
    "surname",
    "telephone",
    "phone",
    "cellulaire",
    "adresse",
    "address",
)
# A file label of at most this many words, small words aside, names what the variable is.
SHORT_LABEL_WORDS = 3
_LABEL_SMALL_WORDS = {
    "le", "la", "les", "l", "un", "une", "de", "du", "des", "d", "votre", "vos", "ton", "ta",
    "quel", "quelle", "quels", "quelles", "est", "sont", "the", "a", "an", "of", "your",
    "what", "is", "are", "please", "veuillez", "indiquer", "indiquez", "inscrire", "inscrivez",
}  # fmt: skip
# Verbs that hold an identifier word ("identif") and start a sentence, not a name.
_IDENTIFIER_VERBS = {"identifier", "identify", "identifiez", "identifie"}
_FREE_TEXT_WORDS = {"autre", "precisez", "precision", "texte", "text", "notes"}
_FREE_TEXT_PARTS = ("comment", "remarque", "verbatim", "precise", "observation")
_BIRTH_WORDS = {"ddn", "dob", "dn"}
_BIRTH_PREFIXES = ("naissance", "birth")  # at the start of a word: not "reconnaissance"
_PLACE_WORDS = {"pays", "lieu", "ville", "province", "country", "place", "city"}
_POSTAL_WORDS = {"cp", "zip", "rta", "fsa"}
_POSTAL_PARTS = ("postal",)

_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
_POSTAL_CODE = re.compile(r"[A-Za-z]\d[A-Za-z](\s?\d[A-Za-z]\d)?")

# Share of values that must have a format (email, phone, postal code) to count.
FORMAT_SHARE = 0.5
# Free text: most values contain a space and they are long on average.
FREE_TEXT_SPACE_SHARE = 0.5
FREE_TEXT_MEAN_LENGTH = 20
# All distinct text values make an identifier only from this many values on.
UNIQUE_MIN_VALUES = 10
# An identifier name does not count for a numeric column with fewer distinct values than
# this (a checkbox such as "motif_identification": 1 or empty): it cannot single anyone out.
IDENTIFIER_NAME_MIN_DISTINCT = 3
# Long texts are categories, not free text, when this share of them belongs to values
# given by at least CATEGORY_MIN_COUNT people ("Avec les deux parents", ...).
CATEGORY_SHARE = 0.9
CATEGORY_MIN_COUNT = 5
# Dates spread over more years than this look like birth dates rather than visits.
BIRTH_DATE_SPAN_YEARS = 15


@dataclass(frozen=True)
class PrivacyClassification:
    name: str
    privacy_class: PrivacyClass
    reasons: tuple[Reason, ...] = ()


def _words(text: str | None) -> list[str]:
    if not text:
        return []
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return [word for word in re.split(r"[^a-z]+", plain.lower()) if word]


def _matches(words: list[str], whole: set[str], parts: tuple[str, ...]) -> bool:
    return any(w in whole or any(p in w for p in parts) for w in words)


def _starts(words: list[str], prefixes: tuple[str, ...]) -> bool:
    return any(w.startswith(prefixes) for w in words)


def _repeated_share(values: list[str]) -> float:
    """Share of values that at least CATEGORY_MIN_COUNT values repeat exactly."""
    counts = pd.Series(values).value_counts()
    return counts[counts >= CATEGORY_MIN_COUNT].sum() / len(values) if values else 0.0


def _share(values: list[str], pattern: re.Pattern) -> float:
    return sum(1 for v in values if pattern.fullmatch(v)) / len(values) if values else 0.0


def _label_names_identifier(label: str | None) -> bool:
    """Whether a file label *designates* an identifier (v0.7): "Identifiant", "ID",
    "Numéro de participant", "Quel est votre nom ?"; not a sentence that merely holds such a
    word ("J'ai pu identifier les sources de tension"). A short label (once the small words
    are set aside) counts by any identifier word; a longer one by its first word only, and
    never by the verb "identifier"."""
    words = [w for w in _words(label) if w not in _LABEL_SMALL_WORDS]
    if not words:
        return False
    if len(words) <= SHORT_LABEL_WORDS:
        return _matches(words, _IDENTIFIER_WORDS, _IDENTIFIER_PARTS)
    first = words[0]
    return first not in _IDENTIFIER_VERBS and _matches(
        [first], _IDENTIFIER_WORDS, _IDENTIFIER_PARTS
    )


def classify_variable(
    variable: VariableMetadata, profile: VariableProfile, column: pd.Series
) -> PrivacyClassification:
    words = _words(variable.name) + _words(variable.label)
    name_words = _words(variable.name)
    is_text = profile.inferred_type in ("text", "mixed")
    texts = [str(v).strip() for v in column if isinstance(v, str) and v.strip()]

    def result(privacy_class: PrivacyClass, *reasons: Reason) -> PrivacyClassification:
        return PrivacyClassification(variable.name, privacy_class, reasons)

    identifier: list[Reason] = []
    checkbox = (
        not is_text
        and profile.n_distinct is not None
        and profile.n_distinct < IDENTIFIER_NAME_MIN_DISTINCT
    )
    identifier_words = _matches(name_words, _IDENTIFIER_WORDS, _IDENTIFIER_PARTS)
    if (identifier_words or _label_names_identifier(variable.label)) and not checkbox:
        identifier.append("identifier_name")
    if is_text and _share(texts, _EMAIL) >= FORMAT_SHARE:
        identifier.append("email_values")
    if is_text and _share(texts, _PHONE) >= FORMAT_SHARE:
        identifier.append("phone_values")
    if identifier:
        return result("likely_identifier", *identifier)

    free_text: list[Reason] = []
    if is_text and _matches(words, _FREE_TEXT_WORDS, _FREE_TEXT_PARTS):
        free_text.append("free_text_name")
    # Dates written as text ("10/02/2026 09:15:23 AM") are long and spaced, but are dates.
    if texts and profile.inferred_type not in ("date", "datetime"):
        with_space = sum(1 for t in texts if re.search(r"\s", t)) / len(texts)
        mean_length = sum(len(t) for t in texts) / len(texts)
        long_texts = with_space >= FREE_TEXT_SPACE_SHARE and mean_length >= FREE_TEXT_MEAN_LENGTH
        if long_texts and _repeated_share(texts) < CATEGORY_SHARE:
            free_text.append("long_text_values")
    if free_text:
        return result("free_text", *free_text)

    if (
        profile.inferred_type == "text"
        and profile.n_valid >= UNIQUE_MIN_VALUES
        and profile.n_distinct == profile.n_valid
    ):
        return result("likely_identifier", "unique_text_values")

    quasi: list[Reason] = []
    if _matches(words, _BIRTH_WORDS, ()) or _starts(words, _BIRTH_PREFIXES):
        is_place = any(w in _PLACE_WORDS for w in words)
        quasi.append("birth_place_name" if is_place else "birth_date_name")
    if _matches(words, _POSTAL_WORDS, _POSTAL_PARTS):
        quasi.append("postal_code_name")
    if is_text and _share(texts, _POSTAL_CODE) >= FORMAT_SHARE:
        quasi.append("postal_code_values")
    if profile.date_min and profile.date_max:
        span = int(profile.date_max[:4]) - int(profile.date_min[:4])
        if span > BIRTH_DATE_SPAN_YEARS:
            quasi.append("wide_date_range")
    if quasi:
        return result("quasi_identifier", *quasi)
    return result("ordinary")


def classify_database(
    data: LoadedData, profiles: tuple[VariableProfile, ...]
) -> tuple[PrivacyClassification, ...]:
    return tuple(
        classify_variable(variable, profile, data.table[variable.name])
        for variable, profile in zip(data.variables, profiles, strict=True)
    )
