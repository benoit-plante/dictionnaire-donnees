import importlib.util
import sys
from pathlib import Path

import pytest

from ddict import i18n

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


@pytest.fixture(scope="session", autouse=True)
def isolated_session_config(tmp_path_factory):
    """Before any fixture of a module or a session: never the settings of this computer (a
    language chosen on the home page made module fixtures write their files in English)."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("DDICT_CONFIG_DIR", str(tmp_path_factory.mktemp("session-config")))
        patch.delenv("DDICT_LANG", raising=False)
        yield


@pytest.fixture(autouse=True)
def isolated_config(tmp_path_factory, monkeypatch):
    """The list of recent projects (v0.3) goes to a temporary folder, never the user's."""
    monkeypatch.setenv("DDICT_CONFIG_DIR", str(tmp_path_factory.mktemp("config")))
    # The interface language (v0.5): French in every test, whatever this computer chose.
    monkeypatch.delenv("DDICT_LANG", raising=False)
    i18n.set_language("fr")
    yield
    i18n.set_language("fr")


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


ENGLISH_GENERATOR_PATH = ROOT / "scripts" / "generer_base_anglaise.py"


@pytest.fixture(scope="session")
def english_generator():
    """The English version of the sleep study (v0.5)."""
    spec = importlib.util.spec_from_file_location("generer_base_anglaise", ENGLISH_GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def english_files(english_generator, tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("sleep-study")
    return {path.name: path for path in english_generator.write_all(out_dir)}


SURVEYMONKEY_GENERATOR_PATH = ROOT / "scripts" / "generer_base_surveymonkey.py"


@pytest.fixture(scope="session")
def surveymonkey_generator():
    """The fictional SurveyMonkey export, in two waves (v0.7)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "generer_base_surveymonkey", SURVEYMONKEY_GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def surveymonkey_files(surveymonkey_generator, tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("surveymonkey")
    return {path.name: path for path in surveymonkey_generator.write_all(out_dir)}


def load_counter():
    """scripts/compter_structure.py: counts only, for the real exports (D-046)."""
    spec = importlib.util.spec_from_file_location(
        "compter_structure", ROOT / "scripts" / "compter_structure.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
