"""v0.6, step 1: the control base (D-042), set aside until the end of v0.6."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
FILES = ["etude-activite.csv", "questionnaire-activite.txt", "questionnaire-activite.pdf"]


def _generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "generer_base_controle", ROOT / "scripts" / "generer_base_controle.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_files_match_the_generator(tmp_path):
    written = {p.name: p for p in _generator().write_all(tmp_path)}
    assert sorted(written) == sorted(FILES)
    for name in FILES:
        assert _sha(written[name]) == _sha(EXAMPLES / name), (
            f"{name} differs: run uv run python scripts/generer_base_controle.py"
        )


def test_the_key_covers_every_variable():
    generator = _generator()
    key = json.loads((EXAMPLES / "corrige-controle.json").read_text(encoding="utf-8"))
    links = key["bases"][0]["links"]
    assert sorted(links) == sorted(generator.COLUMN_ORDER)
    assert {n for n, t in links.items() if t == "none"} == set(
        generator.TRAPS["variables_without_question"]
    )


def test_the_score_is_the_sum_of_its_items():
    generator = _generator()
    df = generator.build_dataset()
    items = generator.TRAPS["computed_score"]["score_motivation"]
    assert (df[items].sum(axis=1) == df["score_motivation"]).all()


def test_in_the_bench_once_measured():
    """Set aside during v0.6, in the bench since its final measure (D-042, step 6)."""
    bench = json.loads((EXAMPLES / "corrige-banc.json").read_text(encoding="utf-8"))
    control = json.loads((EXAMPLES / "corrige-controle.json").read_text(encoding="utf-8"))
    in_bench = next(b for b in bench["bases"] if b["name"] == "etude-activite")
    assert in_bench == control["bases"][0]
