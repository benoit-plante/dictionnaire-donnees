"""v0.2, step 1: the fictional questionnaire matches the database and contains its traps."""

import re

import numpy as np
import pyreadstat
import pytest

TXT = "questionnaire-sommeil.txt"
PDF = "questionnaire-sommeil.pdf"


@pytest.fixture(scope="module")
def key(generator):
    return generator.questionnaire_key()


@pytest.fixture(scope="module")
def text(fictional_files):
    return fictional_files[TXT].read_text(encoding="utf-8")


def test_every_variable_is_asked_or_listed_as_not_asked(generator, key):
    not_asked = generator.QUESTIONNAIRE_TRAPS["variables_without_question"]
    assert set(key) | set(not_asked) == set(generator.COLUMN_ORDER)
    assert not set(key) & set(not_asked)


def test_key_places_options_and_grid_rows(generator, key):
    traps = generator.QUESTIONNAIRE_TRAPS
    options = [key[name] for name in traps["checkbox_question"]]
    # Q1 consent; Q2-Q6 page 2; Q7 sleep grid, Q8 hours, Q9 awakenings, Q10 sleep aids.
    assert {(page, rank) for page, rank, _row in options} == {(3, 10)}
    assert [row for _page, _rank, row in options] == [1, 2, 3, 4]
    assert key["sommeil_q7"] == (3, 7, 7)
    assert key["anx1"] == (4, 12, 1) and key["anx7"] == (4, 12, 7)
    assert key["heures_sommeil"] == key["heures_sommeil_2"] == (3, 8, None)
    assert key["genre"] == (2, 4, None)


def test_text_version_holds_the_questions_and_traps(generator, text):
    traps = generator.QUESTIONNAIRE_TRAPS
    for acronym, meaning in traps["defined_acronyms"].items():
        assert f"{meaning} ({acronym})" in text
    assert traps["consent_page_canary"] in text
    assert traps["question_without_variable"][0] in text
    assert "\t" in text  # the grids, as tables copied from a word processor
    assert re.search(r"^7\. J'évite les écrans", text, re.MULTILINE)


def test_pdf_is_well_formed(generator, fictional_files):
    """A hand-written PDF: every cross-reference offset must point at its object."""
    raw = fictional_files[PDF].read_bytes()
    assert raw.startswith(b"%PDF-1.4") and raw.endswith(b"%%EOF\n")
    start = int(re.search(rb"startxref\n(\d+)\n", raw).group(1))
    assert raw[start:].startswith(b"xref\n")
    offsets = [int(o) for o in re.findall(rb"(\d{10}) 00000 n ", raw)]
    for number, offset in enumerate(offsets, start=1):
        assert raw[offset:].startswith(b"%d 0 obj\n" % number)
    assert raw.count(b"/Type /Page ") == len(generator.QUESTIONNAIRE) == 4
    assert generator.CANARY_CONSENT.encode() in raw  # text is stored uncompressed


def test_checkbox_variables_hold_ticks_only(generator, fictional_files):
    df, _meta = pyreadstat.read_sav(fictional_files["etude-sommeil.sav"])
    items = generator.AID_ITEMS
    for name in items:
        values = set(df[name].dropna())
        assert values == {1.0}, name
        assert df[name].isna().any(), name
    others = df[items[:-1]].eq(1).any(axis=1)
    assert not (df["aide_aucune"].eq(1) & others).any()  # "Rien de cela" stands alone
    assert np.all(df[items].eq(1).sum() >= 5)  # every option ticked by at least 5 people
