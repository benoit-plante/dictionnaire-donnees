"""v0.8, step 6: the analysis context (D-058, D-059, D-066)."""

import json
import os
import shutil
from pathlib import Path

import jsonschema
import pytest
from streamlit.testing.v1 import AppTest

from context_examples import OUTPUT, PROJECTS
from ddict.cli import main
from ddict.export.context import context_package, package_text, render_context
from ddict.io import read_database
from ddict.project import build_project, fingerprint, save_project
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
SCHEMAS = ROOT / "tests" / "schemas"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
MAX_TOKENS = 60  # per variable, on average, without the text of the questions (§ 3.1)


@pytest.fixture(scope="module")
def schema():
    return json.loads((SCHEMAS / "datapackage-2.0.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module", params=sorted(PROJECTS))
def example(request):
    return request.param, PROJECTS[request.param]()


def _tokens_per_variable(text: str, n: int) -> float:
    """About four characters a token; without the text of the questions."""
    return len(text.split("\n## ")[0] + "".join(
        f"\n## {part}" for part in text.split("\n## ")[1:] if not part.startswith(("Texte",
                                                                                   "Text"))
    )) / 4 / n  # fmt: skip


def test_the_examples_are_what_the_tool_writes(example):
    """The examples validated at step 1, now written by the module itself."""
    name, project = example
    written = {
        f"{name}-contexte.md": render_context(project),
        f"{name}-datapackage.json": package_text(context_package(project)),
    }
    for file_name, text in written.items():
        path = OUTPUT / file_name
        if os.environ.get("DDICT_REGENERATE"):
            path.write_text(text, encoding="utf-8", newline="\n")
        assert text == path.read_text(encoding="utf-8"), file_name


def test_valid_frictionless(example, schema):
    _name, project = example
    for statistics in (False, True):
        package = context_package(project, statistics=statistics)
        errors = list(jsonschema.Draft7Validator(schema).iter_errors(package))
        assert not errors, [e.message for e in errors[:3]]


def test_short_enough(example):
    _name, project = example
    assert _tokens_per_variable(render_context(project), len(project.variables)) <= MAX_TOKENS


@pytest.mark.parametrize(
    "base",
    ["etude-sommeil.csv", "enquete-familles.csv", "etude-activite.csv", "sleep-study.csv"],
)
def test_short_enough_as_read(base):
    project = build_project(read_database(EXAMPLES / base))
    assert _tokens_per_variable(render_context(project), len(project.variables)) <= MAX_TOKENS


def test_what_the_sleep_study_says():
    project = PROJECTS["etude-sommeil"]()
    text = render_context(project)
    assert f"empreinte `{fingerprint.short(project)}`" in text
    assert "- Une ligne représente : un participant" in text
    assert "Cotation : sommeil_total = somme des 8 items, après inversion de sommeil_q3, " in text
    assert (
        "| `sommeil_q3` | Q3 reveils nocturnes | entier | ordinal | → G1 | 9 | G1 | Q7.r3 | inv |"
        in text
    )
    assert "| `age` | Age | entier | échelle |  | 999 |  | Q3 |  |" in text
    assert "| `courriel` | Courriel | texte |  |  |  |  | Q5 | sensible (identifiant) |" in text
    assert "Cotation : non documentée." in text  # G2
    assert "`langue_maison` : variantes d'écriture d'une même réponse." in text
    # No observed value, and no statistics unless asked.
    assert "Français" not in text and "## Statistiques" not in text
    assert "Libellé : sommeil_q7" in text  # what is not documented is said


def test_statistics_on_request_only():
    project = PROJECTS["etude-sommeil"]()
    text = render_context(project, statistics=True)
    stats = text.split("## Statistiques")[1].split("\n## ")[0]
    assert "- `age` : n = " in stats and "moyenne" in stats
    assert "- `genre` : n = " in stats and "1 Femme: " in stats
    for sensitive in ("courriel", "id_participant", "date_naissance", "commentaire"):
        assert f"`{sensitive}`" not in stats
    package = context_package(project, statistics=True)
    fields = {f["name"]: f for f in package["resources"][0]["schema"]["fields"]}
    assert fields["age"]["_ddict"]["statistics"]["n_valid"] > 0
    assert "statistics" not in fields["courriel"]["_ddict"]
    # Counts below 5 are masked, except those of missing codes, which stay exact (D-007).
    for field in fields.values():
        missing = {m["value"] for m in field.get("missingValues", [])}
        for count in field.get("_ddict", {}).get("statistics", {}).get("counts", []):
            small = count["count"] is not None and count["count"] < 5
            assert not small or str(count["value"]) in missing, (field["name"], count)
    assert "statistics" not in json.dumps(context_package(project)["resources"])


def test_renamed_names_and_checkboxes():
    project = PROJECTS["travail-t2_surveymonkey"]()
    text = render_context(project)
    assert "copie documentée `travail-t2_surveymonkey-documente.sav`" in text
    assert "| `eft_1_t2` (q0003_0001) |" in text
    assert "une case vide est une option non cochée" in text
    assert "| `taches_1_t2` (q0005_0001) | Accueil de la clientèle |" in text
    package = context_package(project)
    resource = package["resources"][0]
    assert resource["path"] == "travail-t2_surveymonkey-documente.sav"
    assert resource["_ddict"]["renamed_from"]["path"] == "travail-t2_surveymonkey.sav"
    assert "multiple_response_empty_is_unchecked" in package["_ddict"]["rules"]
    assert package["_ddict"]["dataset"]["design_variables"] == {"cluster_id": "id_participant_t2"}


def test_in_english():
    project = PROJECTS["etude-sommeil"]()
    text = render_context(project, language="en")
    assert text.startswith("# Analysis context: etude-sommeil.sav")
    assert "## Rules" in text and "## Règles" not in text
    assert context_package(project, language="en")["_ddict"]["language"] == "fr"  # the study's


def test_the_command(tmp_path, capsys):
    path = tmp_path / "etude-sommeil.dd.json"
    save_project(PROJECTS["etude-sommeil"](), path)
    assert main(["exporter", str(path), "--contexte", "--avec-statistiques"]) == 0
    out = capsys.readouterr().out
    assert "etude-sommeil-contexte.md" in out and "etude-sommeil-datapackage.json" in out
    assert "## Statistiques" in (tmp_path / "etude-sommeil-contexte.md").read_text(encoding="utf-8")
    assert main(["export", str(path), "--context", "--language", "en"]) == 0
    text = (tmp_path / "etude-sommeil-contexte.md").read_text(encoding="utf-8")
    assert "## Statistics" not in text and text.startswith("# Analysis context")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_export_page(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "export"
    app.run()
    assert not app.exception, app.exception
    app.checkbox(key="context-statistics").check().run()
    app.button(key="context-write").click().run()
    assert not app.exception, app.exception
    text = (tmp_path / "etude-sommeil-contexte.md").read_text(encoding="utf-8")
    assert "## Statistiques" in text
    assert (tmp_path / "etude-sommeil-datapackage.json").is_file()
