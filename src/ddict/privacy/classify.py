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
_FREE_TEXT_WORDS = {"autre", "precisez", "precision", "texte", "text", "notes"}
_FREE_TEXT_PARTS = ("comment", "remarque", "verbatim", "precise", "observation")
_BIRTH_WORDS = {"ddn", "dob", "dn"}
_BIRTH_PARTS = ("naissance", "birth")
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


def _share(values: list[str], pattern: re.Pattern) -> float:
    return sum(1 for v in values if pattern.fullmatch(v)) / len(values) if values else 0.0


def classify_variable(
    variable: VariableMetadata, profile: VariableProfile, column: pd.Series
) -> PrivacyClassification:
    words = _words(variable.name) + _words(variable.label)
    is_text = profile.inferred_type in ("text", "mixed")
    texts = [str(v).strip() for v in column if isinstance(v, str) and v.strip()]

    def result(privacy_class: PrivacyClass, *reasons: Reason) -> PrivacyClassification:
        return PrivacyClassification(variable.name, privacy_class, reasons)

    identifier: list[Reason] = []
    if _matches(words, _IDENTIFIER_WORDS, _IDENTIFIER_PARTS):
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
    if texts:
        with_space = sum(1 for t in texts if re.search(r"\s", t)) / len(texts)
        mean_length = sum(len(t) for t in texts) / len(texts)
        if with_space >= FREE_TEXT_SPACE_SHARE and mean_length >= FREE_TEXT_MEAN_LENGTH:
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
    if _matches(words, _BIRTH_WORDS, _BIRTH_PARTS):
        quasi.append("birth_date_name")
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
