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


@pytest.fixture(autouse=True)
def isolated_config(tmp_path_factory, monkeypatch):
    """The list of recent projects (v0.3) goes to a temporary folder, never the user's."""
    monkeypatch.setenv("DDICT_CONFIG_DIR", str(tmp_path_factory.mktemp("config")))


FAMILY_GENERATOR_PATH = ROOT / "scripts" / "generer_enquete_familles.py"


@pytest.fixture(scope="session")
def family_generator():
    """The second fictional database (v0.4): a survey of families."""
    spec = importlib.util.spec_from_file_location("generer_enquete_familles", FAMILY_GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def family_files(family_generator, tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("enquete-familles")
    return {path.name: path for path in family_generator.write_all(out_dir)}
