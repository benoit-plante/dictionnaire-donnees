"""Spelling variants of a same answer in a text variable (v0.2, step 7), no model.

"Français", "français" and "Francais" differ only by case, accents or spaces: they are
grouped and flagged, for the team to decide whether to recode them. Nothing else is
compared: "Espagnol" and "Espanol" are two words to the tool, which does not guess.

Only categories already visible in the project are compared, never the data: a rare
category hidden by the privacy gate (D-006) is never revealed by this signal, and
variables without visible categories (sensitive ones, more than 20 categories) have none.
"""

from __future__ import annotations

import unicodedata

from ddict.project.model import Profile


def _key(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(plain.casefold().split())


def spelling_variants(profile: Profile) -> list[list[str]]:
    """Groups of visible text categories that differ only by case, accents or spaces: the
    most frequent group first, and in each group the most frequent spelling first."""
    groups: dict[str, list[tuple[int, str]]] = {}
    for value in profile.observed_values or []:
        if isinstance(value.code, str) and value.code.strip() and value.count is not None:
            groups.setdefault(_key(value.code), []).append((value.count, value.code))
    found = [members for members in groups.values() if len(members) > 1]
    found.sort(key=lambda members: -sum(count for count, _code in members))
    return [[code for _count, code in sorted(g, key=lambda c: (-c[0], c[1]))] for g in found]
