"""Step 9: messages for the model — only aggregates, never a canary, always the same."""

import json

import pytest
from pydantic import ValidationError

from ddict.cli import main
from ddict.io import read_csv, read_sav
from ddict.llm import (
    PROMPT_VERSION,
    BlockResponse,
    build_blocks,
    message_sha256,
    response_schema,
    system_prompt,
)
from ddict.project import build_project


@pytest.fixture(scope="module", params=["etude-sommeil.sav", "etude-sommeil_excel-fr.csv"])
def project(request, fictional_files):
    path = fictional_files[request.param]
    return build_project(read_sav(path) if path.suffix == ".sav" else read_csv(path))


@pytest.fixture(scope="module")
def payloads(project):
    found = {}
    for block in build_blocks(project):
        content = json.loads(block.messages[1]["content"])
        for variable in content["variables"]:
            found[variable["name"]] = variable
    return found


def _all_text(project):
    return "".join(m["content"] for b in build_blocks(project) for m in b.messages)


def test_no_canary_in_any_message(project, generator):
    text = _all_text(project)
    for canary in generator.CANARIES:
        assert canary not in text


def test_no_file_name_nor_notes(project):
    project.variables[0].notes = "Note interne de l'équipe"
    try:
        text = _all_text(project)
    finally:
        project.variables[0].notes = None
    assert "etude-sommeil" not in text
    assert "Note interne" not in text


def test_messages_are_deterministic(project):
    first, second = build_blocks(project), build_blocks(project)
    assert first == second
    assert [b.sha256 for b in first] == [b.sha256 for b in second]


def test_blocks_cover_every_variable_once_in_order(project):
    blocks = build_blocks(project, size=12)
    assert [b.block_id for b in blocks] == ["b-001", "b-002", "b-003"]
    names = [name for b in blocks for name in b.names]
    assert names == [v.name for v in project.variables]
    assert [len(b.names) for b in build_blocks(project, size=10)] == [10, 10, 10, 3]


def test_sensitive_variables_send_only_their_description(payloads):
    for name in ["id_participant", "courriel", "date_naissance", "commentaire"]:
        assert set(payloads[name]) <= {"name", "neighbors", "file_label", "type", "note"}
        assert "aucune valeur transmise" in payloads[name]["note"]


def test_counts_become_proportions_and_masked_stay_masked(payloads):
    genre = payloads["genre"]["observed"]
    assert genre["3"] == "masqué"
    # Never a single masked count (D-008): in the .sav, 2 is masked with 3; in the CSV,
    # where 9 is not declared missing, 9 is masked with 3.
    assert sum(1 for v in genre.values() if v == "masqué") == 2
    assert isinstance(genre["1"], float) and 0 < genre["1"] < 1
    for payload in payloads.values():
        for value in payload.get("observed", {}).values():
            assert value == "masqué" or (isinstance(value, float) and 0 <= value <= 1)


def test_dates_are_years_only(payloads):
    assert payloads["date_passation"]["years"] == "2026-2026"
    assert "date_min" not in payloads["date_passation"]


def test_groups_are_sent_but_not_anomalies(payloads):
    """The model is not asked for inconsistencies (D-009): computed ones are not sent."""
    assert payloads["anx5"]["group"]["id"] == "G2"
    assert not any("anomalies" in payload for payload in payloads.values())
    assert payloads["age"]["max"] == 999.0


def test_neighbors(payloads):
    assert payloads["id_participant"]["neighbors"] == ["courriel"]
    assert payloads["anx4"]["neighbors"] == ["anx3", "heures_sommeil"]


def test_system_prompt_forbids_invention():
    prompt = system_prompt()
    assert PROMPT_VERSION == "variables-v2"
    assert "N'invente jamais de seuil clinique" in prompt
    assert "nom d'instrument" in prompt
    assert "ne reprends pas le libellé d'une variable voisine" in prompt
    assert "rétablis les accents" in prompt
    assert "issues" not in prompt


def test_response_schema_has_no_field_for_inventions():
    schema = json.dumps(response_schema())
    for forbidden in ["threshold", "cutoff", "range", "reference", "instrument", "seuil"]:
        assert forbidden not in schema.lower()


def test_response_with_an_extra_field_is_refused():
    answer = {
        "block": "b-001",
        "variables": [{"name": "x", "label": "X", "description": "", "seuil_clinique": 14}],
    }
    with pytest.raises(ValidationError):
        BlockResponse.model_validate(answer)


def test_response_lengths_are_bounded():
    answer = {
        "block": "b-001",
        "variables": [{"name": "x", "label": "L" * 81, "description": ""}],
    }
    with pytest.raises(ValidationError):
        BlockResponse.model_validate(answer)


def test_sha256_is_over_the_exact_messages():
    messages = ({"role": "user", "content": "é"},)
    assert message_sha256(messages) != message_sha256(({"role": "user", "content": "e"},))


def test_preview_command_sends_nothing_and_writes_the_messages(fictional_files, tmp_path, capsys):
    project_path = tmp_path / "etude.dd.json"
    assert (
        main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(project_path)]) == 0
    )
    assert main(["enrichir", str(project_path), "--apercu"]) == 0
    output = capsys.readouterr().out
    assert "rien n'a été envoyé" in output
    folder = tmp_path / "etude.dd-envois" / "apercu"
    files = sorted(p.name for p in folder.iterdir())
    assert files == ["b-001.json", "b-002.json", "b-003.json"]
    record = json.loads((folder / "b-001.json").read_text(encoding="utf-8"))
    assert record["prompt_version"] == PROMPT_VERSION
    assert record["message_sha256"] == message_sha256(record["messages"])
    # A second preview with another block size replaces the first one.
    assert main(["enrichir", str(project_path), "--apercu", "--taille-bloc", "20"]) == 0
    assert sorted(p.name for p in folder.iterdir()) == ["b-001.json", "b-002.json"]


def test_enrich_without_preview_is_not_available_yet(fictional_files, tmp_path, capsys):
    project_path = tmp_path / "etude.dd.json"
    main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(project_path)])
    assert main(["enrichir", str(project_path)]) == 2
    assert "--apercu" in capsys.readouterr().err
