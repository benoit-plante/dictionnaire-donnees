import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GENERATOR_PATH = ROOT / "scripts" / "generer_bases_fictives.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generer_bases_fictives", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def generator():
    """The fictional database generator (scripts/generer_bases_fictives.py)."""
    return _load_generator()


@pytest.fixture(scope="session")
def fictional_files(generator, tmp_path_factory):
    """The fictional .sav and CSV files, freshly generated, keyed by file name."""
    out_dir = tmp_path_factory.mktemp("bases-fictives")
    return {path.name: path for path in generator.write_all(out_dir)}
