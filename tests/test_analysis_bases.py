"""v0.9, step 2: the fictional database of the analyses, its planted effects and its answer
key (D-075)."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from ddict.io import read_database
from ddict.project import build_project

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-analyses.json").read_text(encoding="utf-8"))
FILES = ["etude-analyses.sav", "etude-analyses.csv", "corrige-analyses.json"]


def _generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    path = ROOT / "scripts" / "generer_base_analyses.py"
    spec = importlib.util.spec_from_file_location("generer_base_analyses", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_files_match_the_generator(tmp_path):
    written = {p.name: p for p in _generator().write_all(tmp_path)}
    assert sorted(written) == sorted(FILES)
    for name in FILES:
        assert _sha(written[name]) == _sha(EXAMPLES / name), (
            f"{name} differs: run uv run python scripts/generer_base_analyses.py"
        )


def test_the_key_is_what_the_files_hold():
    """The exact statistics computed again from the committed CSV give the key's."""
    table = pd.read_csv(EXAMPLES / KEY["csv"])
    again = json.loads(json.dumps(_generator().answer_key(table)["exact"]))
    assert again == KEY["exact"]


def test_the_planted_effects():
    exact = KEY["exact"]
    assert 0.4 < exact["t_groupe"]["d"] < 0.7
    assert abs(exact["t_sexe"]["d"]) < 0.15
    means = exact["anova_etudes"]["means"]
    assert means["1"] > means["2"] > means["3"] and exact["anova_etudes"]["eta2"] > 0.1
    assert 0.2 < exact["khi2_teletravail_secteur"]["V"] < 0.4
    assert exact["khi2_sexe_secteur"]["V"] < 0.1
    assert 0.3 < exact["r_heures_stress"]["r"] < 0.5
    assert abs(exact["r_age_stress"]["r"]) < 0.15
    b0, b1, b2 = exact["regression_satisfaction"]["coef"]
    assert abs(b1 - 0.5) < 0.05 and abs(b2 + 0.3) < 0.05 and abs(b0 - 2) < 0.3


def test_the_traps():
    data, meta = pyreadstat.read_sav(str(EXAMPLES / KEY["sav"]), user_missing=True)
    assert meta.missing_ranges == {
        "age": [{"lo": 999.0, "hi": 999.0}],
        "stress": [{"lo": -9.0, "hi": -9.0}],
    }
    assert (data["region"] == 4).sum() == 3  # the small group
    assert meta.variable_measure["sport"] == "ordinal"
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    assert project.variable("id_participant").privacy.privacy_class.value == "likely_identifier"
    scale = next(g for g in project.groups if "bienetre_1" in (g.members.value or []))
    assert scale.members.value == KEY["scoring"]["group_items"]
    assert project.variable("bienetre_4").profile.reverse_suspect


@pytest.mark.parametrize("name", ["etude-analyses.sav", "etude-analyses.csv"])
def test_read_by_the_tool(name):
    project = build_project(read_database(EXAMPLES / name))
    assert len(project.variables) == 19 and project.source.n_rows == KEY["rows"]
