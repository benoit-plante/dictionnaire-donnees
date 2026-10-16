"""v0.12, step 5: the signals of the quality of administration (D-095), and the duration
rule on dates written in text, read the same way in the tool, PSPP and R."""

import datetime as dt
import subprocess

import pandas as pd
import pyreadstat
import pytest

from ddict.analysis import quality
from ddict.analysis.data import apply_decisions
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from ddict.io import read_database
from ddict.project import build_project
from ddict.project import exclusions as ex
from test_exclusions import EXAMPLES, KEY, TODAY, _project
from test_syntax import _pspp, _rscript

SAV = EXAMPLES / "travail-t1_surveymonkey.sav"


def _kept_by_the_first_rules():
    """The fictional database of administration, with the rules E1 to E3: the signals are
    computed among the people they keep."""
    project, table = _project(rules=False)
    for rule in KEY["rules"][:3]:
        ex.add(project, {k: v for k, v in rule.items() if k != "id"})
    return project, apply_decisions(project, table)


@pytest.fixture(scope="module")
def kept():
    return _kept_by_the_first_rules()


# --- The planted cases. ---


def test_the_durations(kept):
    project, prepared = kept
    assert quality.date_variables(project) == ["debut", "fin"]
    found = quality.durations(project, prepared, "debut", "fin")
    assert found.text_format is None and found.n == 367 and found.invalid == 0
    assert found.p5 < found.p10 < found.median
    assert quality.below(project, prepared, found, 180) == 10  # the planted cases


def test_no_count_without_the_teams_threshold(kept):
    project, prepared = kept
    found = quality.durations(project, prepared, "debut", "fin")
    # Only aggregates, and no threshold: the count needs one, given by the team.
    assert {f for f in found.__dataclass_fields__} == {
        "start",
        "end",
        "text_format",
        "n",
        "invalid",
        "median",
        "p5",
        "p10",
    }
    with pytest.raises(TypeError):
        quality.below(project, prepared, found)  # no default threshold


def test_the_grids(kept):
    project, prepared = kept
    grids = {g.group: g for g in quality.grids(project, prepared)}
    assert grids["G2"].count == 8 and grids["G2"].items == 8  # the planted cases


def test_the_duplicates(kept):
    project, prepared = kept
    assert quality.duplicate_variables(project) == ["id_participant", "courriel"]
    assert quality.duplicates(project, prepared, ["courriel"]).count == 5
    assert quality.duplicates(project, prepared, ["id_participant"]).count == 0


def test_a_signal_is_never_applied_alone(kept):
    project, prepared = kept
    quality.durations(project, prepared, "debut", "fin")
    quality.grids(project, prepared)
    quality.duplicates(project, prepared, ["courriel"])
    assert [r.id for r in project.exclusions.rules] == ["E1", "E2", "E3"]
    assert len(prepared.table) == 367


def test_a_platform_export():
    database = read_database(SAV)
    project = build_project(database)
    prepared = apply_decisions(project, database.table)
    assert quality.proposed_dates(project) == ("StartDate", "EndDate")
    assert quality.duplicate_variables(project) == ["RespondentID", "EmailAddress", "IPAddress"]
    found = quality.durations(project, prepared, "StartDate", "EndDate")
    assert found.text_format == "%m/%d/%Y %I:%M:%S %p" and found.n == len(database.table)


# --- Dates in text, the same in the tool, PSPP and R. ---

START = dt.datetime(2026, 3, 8, 11, 50, 0)
# Durations in seconds, with the traps: noon, midnight, a night, a day.
SPANS = [60, 120, 170, 179, 180, 181, 600, 3600, 30, 900, 15, 200, 400, 86400 + 30, 7200, 45]
FORMATS = {
    "iso": "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %I:%M:%S %p": "%m/%d/%Y %I:%M:%S %p",
    "%d/%m/%Y %H:%M": "%d/%m/%Y %H:%M",
}


def _base(tmp_path, written: str):
    """Sixteen administrations, their start and end written in text."""
    starts = [START + dt.timedelta(hours=7 * i, minutes=13 * i) for i in range(len(SPANS))]
    ends = [s + dt.timedelta(seconds=d) for s, d in zip(starts, SPANS, strict=True)]
    if "%M" in written and "%S" not in written:  # minutes only: whole minutes
        starts = [s.replace(second=0) for s in starts]
        ends = [e.replace(second=0) for e in ends]
    expected = sum(0 <= (e - s).total_seconds() < 180 for s, e in zip(starts, ends, strict=True))
    table = pd.DataFrame(
        {
            "id": [f"P{i}" for i in range(len(SPANS))],
            "debut": [s.strftime(written) for s in starts],
            "fin": [e.strftime(written) for e in ends],
            "score": [float(i % 5) for i in range(len(SPANS))],
        }
    )
    sav = tmp_path / "base.sav"
    pyreadstat.write_sav(table, str(sav))
    database = read_database(sav)
    project = build_project(database)
    prepared = apply_decisions(project, database.table)
    text_format = quality.text_format(project, prepared, "debut", "fin")
    ex.add(project, {"kind": "duration", "start": "debut", "end": "fin", "min_seconds": 180,
                     "text_format": text_format, "reason": "Trop court",
                     "source": "Seuil d'essai"})  # fmt: skip
    return project, database, sav, text_format, expected


@pytest.mark.parametrize("key", list(FORMATS))
def test_dates_in_text_in_the_tool(tmp_path, key):
    project, database, _sav, text_format, expected = _base(tmp_path, FORMATS[key])
    assert text_format == key
    flow = apply_decisions(project, database.table).flow
    assert flow.excluded == (("E1", expected),) and expected >= 5


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
@pytest.mark.parametrize("key", list(FORMATS))
def test_dates_in_text_in_pspp(tmp_path, key):
    project, _database, sav, _format, expected = _base(tmp_path, FORMATS[key])
    write_syntax(project, {"spss": tmp_path / "m.sps"}, TODAY)
    script = render_preparation(project, "spss", TODAY)
    (tmp_path / "p.sps").write_text(
        script.replace("SELECT IF (ddict_exclusion = 0).\n", ""), encoding="utf-8"
    )
    out = tmp_path / "out.sav"
    job = tmp_path / "job.sps"
    job.write_text(
        f"GET FILE='{sav}'.\nINSERT FILE='{tmp_path / 'm.sps'}' ENCODING='UTF-8'.\n"
        f"INSERT FILE='{tmp_path / 'p.sps'}' ENCODING='UTF-8'.\nSAVE OUTFILE='{out}'.\n",
        encoding="utf-8",
    )
    done = subprocess.run([_pspp(), str(job)], capture_output=True, text=True, errors="replace")
    said = (done.stdout + done.stderr).lower()
    assert done.returncode == 0 and "error" not in said and "warning" not in said, said
    result, _meta = pyreadstat.read_sav(str(out))
    assert int((result["ddict_exclusion"] == 1).sum()) == expected
    assert "ddict_debut1" not in result.columns


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize("key", list(FORMATS))
def test_dates_in_text_in_r(tmp_path, key):
    project, _database, sav, _format, expected = _base(tmp_path, FORMATS[key])
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    (tmp_path / "p.R").write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
    out = tmp_path / "out.csv"
    job = tmp_path / "job.R"
    job.write_text(
        'Sys.setlocale("LC_TIME", "French")\n'  # "PM" is read whatever the language
        f'donnees <- haven::read_sav("{sav.as_posix()}")\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        f'write.csv(data.frame(n = nrow(donnees)), "{out.as_posix()}", row.names = FALSE)\n',
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(job)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    assert int(pd.read_csv(out)["n"][0]) == len(SPANS) - expected


def test_a_text_date_needs_its_format(tmp_path):
    project, _database, _sav, _format, _expected = _base(tmp_path, FORMATS["iso"])
    with pytest.raises(ex.ExclusionRefused) as error:
        ex.add(project, {"kind": "duration", "start": "debut", "end": "fin", "min_seconds": 60,
                         "reason": "x", "source": "s"})  # fmt: skip
    assert "format de la date" in " ".join(error.value.reasons)
