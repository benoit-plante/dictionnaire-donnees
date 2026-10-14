"""v0.2, step 7: spelling variants of a same answer, flagged without revealing anything."""

import json

import pytest

from ddict.export import render_markdown, write_xlsx
from ddict.export.wording import anomalies
from ddict.io import read_database
from ddict.llm.messages import build_blocks
from ddict.profile.variants import spelling_variants
from ddict.project import build_project, dumps
from ddict.project.model import ObservedCount, Profile
from ddict.review import logic


@pytest.fixture(params=["etude-sommeil.sav", "etude-sommeil.csv"])
def project(request, fictional_files):
    return build_project(read_database(fictional_files[request.param]))


def test_variants_of_the_fictional_base(project, generator):
    expected = generator.TRAPS["spelling_variants"]
    found = {
        e.name: spelling_variants(e.profile)
        for e in project.variables
        if spelling_variants(e.profile)
    }
    assert found == expected
    assert found["langue_maison"][0][0] == "Français"  # the most frequent spelling first


def test_flagged_for_review(project):
    texts = anomalies(project.variable("langue_maison").profile)
    assert "Variantes d'écriture d'une même réponse : « Anglais », « anglais »" in texts
    assert "langue_maison" in [e.name for e in logic.select(project, "flagged")]


def test_hidden_variants_are_never_revealed(project, generator, tmp_path):
    """The rare spellings stay out of the project, the exports and the messages."""
    hidden = generator.TRAPS["hidden_variants"]["langue_maison"]
    path = tmp_path / "codebook.xlsx"
    write_xlsx(project, path)
    import zipfile

    with zipfile.ZipFile(path) as archive:
        workbook = "".join(archive.read(n).decode("utf-8") for n in archive.namelist())
    messages = json.dumps([b.messages for b in build_blocks(project)], ensure_ascii=False)
    for text in (dumps(project), render_markdown(project), workbook, messages):
        for spelling in hidden:
            assert spelling not in text
            assert spelling.casefold() not in text.casefold()
    assert project.variable("langue_maison").profile.n_rare_values_hidden == 2


def _profile(*counts) -> Profile:
    return Profile(
        inferred_type="text",
        n_rows=100,
        n_valid=100,
        n_system_missing=0,
        n_declared_missing=0,
        observed_values=[ObservedCount(code=code, count=count) for code, count in counts],
    )


@pytest.mark.parametrize(
    ("counts", "groups"),
    [
        (
            (("Montréal", 20), ("Montreal", 8), ("MONTRÉAL", 6)),
            [["Montréal", "Montreal", "MONTRÉAL"]],
        ),
        ((("Saint Jean", 10), ("Saint  Jean ", 7)), [["Saint Jean", "Saint  Jean "]]),
        ((("Espagnol", 10), ("Espanol", 7)), []),  # a spelling, not case or accents: no guess
        ((("Oui", 10), ("oui", None)), []),  # a masked count is not compared
        ((("", 10), (" ", 7)), []),
        (((1, 10), (2, 10)), []),
    ],
)
def test_rules(counts, groups):
    assert spelling_variants(_profile(*counts)) == groups
