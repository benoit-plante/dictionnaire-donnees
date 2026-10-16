"""v0.12, step 2: the fictional database of administration, its planted exclusion cases and
its answer key (docs/methode-gabarits.md, § 1)."""

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
KEY = json.loads((EXAMPLES / "corrige-passation.json").read_text(encoding="utf-8"))
FILES = ["etude-passation.sav", "corrige-passation.json"]


def _generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    path = ROOT / "scripts" / "generer_base_passation.py"
    spec = importlib.util.spec_from_file_location("generer_base_passation", path)
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
            f"{name} differs: run uv run python scripts/generer_base_passation.py"
        )


def test_the_key_is_what_the_file_holds():
    """The key computed again from the committed .sav, read without the tool."""
    table, _meta = pyreadstat.read_sav(str(EXAMPLES / KEY["sav"]))
    again = json.loads(json.dumps(_generator().answer_key(table, KEY["planted"])["exact"]))
    assert again == KEY["exact"]


def test_the_planted_cases_as_the_sheet_says():
    exact = KEY["exact"]
    assert exact["flow"]["excluded"] == {"E1": 12, "E2": 7, "E3": 14, "E4": 10, "E5": 5, "E6": 5}
    assert exact["flow"]["start"] == 400 and exact["flow"]["analysed"] == 347
    other = exact["flow_e5_before_e4"]
    assert (other["excluded"]["E5"], other["excluded"]["E4"]) == (8, 7)
    assert other["analysed"] == 347  # the order changes the counts per rule, never the N
    assert exact["sample"]["age"]["n"] == 341  # six 999 among the kept
    low, high = exact["anxiety"]["ci95"]
    assert low < exact["anxiety"]["alpha"] < high
    assert [r["id"] for r in KEY["rules"]] == ["E1", "E2", "E3", "E4", "E5", "E6"]


def test_the_tool_reads_it():
    database = read_database(EXAMPLES / KEY["sav"])
    project = build_project(database)
    kinds = {v.name: v.profile.inferred_type for v in project.variables}
    assert kinds["debut"] == kinds["fin"] == "datetime"
    privacy = {v.name: v.privacy.privacy_class.value for v in project.variables}
    assert privacy["id_participant"] == privacy["courriel"] == "likely_identifier"
    assert project.variable("age").profile.n_declared_missing == 6
    groups = {g.group_id: g.members.value for g in project.groups}
    assert groups == KEY["groups"]
    assert all(t.startswith(("ZQXID-",)) for t in database.table["id_participant"])
