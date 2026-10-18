"""v0.14, step 1: the fictional follow-up database, its planted effects and its answer key
(docs/catalogue-elargi.md)."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pyreadstat

from ddict.io import read_database
from ddict.project import build_project

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-suivi.json").read_text(encoding="utf-8"))
FILES = ["etude-suivi.sav", "etude-suivi.csv", "corrige-suivi.json"]


def _generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    path = ROOT / "scripts" / "generer_base_suivi.py"
    spec = importlib.util.spec_from_file_location("generer_base_suivi", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_files_match_the_generator(tmp_path):
    generator = _generator()
    first = {p.name: _sha(p) for p in generator.write_all(tmp_path / "a")}
    second = {p.name: _sha(p) for p in generator.write_all(tmp_path / "b")}
    assert first == second  # the same seed, the same bytes
    for name in FILES:
        assert first[name] == _sha(EXAMPLES / name), (
            f"{name} differs: run uv run python scripts/generer_base_suivi.py"
        )


def test_the_key_is_what_the_file_holds():
    """The key computed again from the committed .sav, read without the tool."""
    table, _meta = pyreadstat.read_sav(str(EXAMPLES / KEY["sav"]))
    again = json.loads(json.dumps(_generator().answer_key(table)["exact"]))
    assert again == KEY["exact"]


def test_the_planted_effects_as_the_sheet_says():
    exact = KEY["exact"]
    paired = exact["t_apparie_t1_t2"]
    assert (paired["n"], round(paired["d_z"], 2)) == (228, 0.54)
    rm = exact["anova_rm_anxiete"]
    assert rm["n"] == 203 and [round(m, 2) for m in rm["means"]] == [21.6, 18.69, 17.86]
    assert 0.8 < rm["gg_epsilon"] < 0.9  # sphericity not perfect
    logistic = exact["logistique_abandon"]
    assert (logistic["events"], round(logistic["odds_ratios"][1], 2)) == (76, 0.6)
    moderation = exact["moderation_epuisement"]
    assert moderation["coef"][3] < 0  # the interaction
    slopes = moderation["simple_slopes"]
    assert slopes["low"] > slopes["mean"] > slopes["high"] > 0
    partial = exact["partielle_stress_sommeil"]
    assert round(partial["r"], 2) == -0.38 and round(partial["r_partial"], 2) == -0.12


def test_the_tool_reads_it():
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    assert project.variable("id_participant").privacy.privacy_class.value == "likely_identifier"
    assert [m.low for m in project.variable("anxiete_t3").file.declared_missing] == [-9]
    assert len(project.variables) == 13
