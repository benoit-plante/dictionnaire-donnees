"""Step 12: review — decisions, human-only fields, interface, local launch."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import REVIEW_HOST, review_command
from ddict.io import read_sav
from ddict.project import build_project, is_accepted, load_project, save_project
from ddict.project.model import TrackedValue
from ddict.review import logic

NOW = "2026-10-13T17:00:00"
APP = Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py"


def _ai(value, run="run-0001"):
    return TrackedValue[str](value=value, origin="ai", status="proposed", ai_run=run)


@pytest.fixture
def project(fictional_files):
    """The fictional project, as after an enrichment of two variables."""
    project = build_project(read_sav(fictional_files["etude-sommeil.sav"]))
    project.variable("sommeil_q1").label = _ai("Difficulté d'endormissement")
    project.variable("sommeil_q1").description = _ai("Difficulté à s'endormir, de 1 à 5.")
    project.variable("sommeil_q7").label = _ai("Routine sommeil")
    project.variable("sommeil_q7").ai_signals = ["label:no_file_label"]
    return project


def test_filters(project):
    names = lambda which: [e.name for e in logic.select(project, which)]  # noqa: E731
    assert names("to_review") == ["sommeil_q1", "sommeil_q7"]
    assert names("sensitive") == ["id_participant", "courriel", "date_naissance", "commentaire"]
    assert "sommeil_q7" in names("flagged") and "age" in names("flagged")
    assert "sommeil_q2" not in names("flagged")
    assert len(names("all")) == 34
    assert logic.progress(project) == (32, 34)


def test_accept_reject_correct(project):
    logic.decide(project, "sommeil_q1", "label", "accept", now=NOW)
    assert project.variable("sommeil_q1").label.status == "validated"
    logic.decide(project, "sommeil_q1", "description", "correct", now=NOW, value="Ma version.")
    description = project.variable("sommeil_q1").description
    assert (description.value, description.proposed_value) == (
        "Ma version.",
        "Difficulté à s'endormir, de 1 à 5.",
    )
    logic.decide(project, "sommeil_q7", "label", "reject", now=NOW)
    assert not is_accepted(project.variable("sommeil_q7").label)
    assert project.variable("sommeil_q7").ai_signals == []  # settled by the decision
    assert logic.progress(project) == (34, 34)


def test_empty_correction_is_refused(project):
    with pytest.raises(logic.ReviewError, match="vide"):
        logic.decide(project, "sommeil_q1", "label", "correct", now=NOW, value="  ")


def test_file_label_cannot_be_rejected(project):
    with pytest.raises(logic.ReviewError):
        logic.decide(project, "sommeil_q2", "label", "reject", now=NOW)


def test_write_by_hand(project):
    logic.write(project, "age", "unit", "années", now=NOW)
    assert (project.variable("age").unit.value, project.variable("age").unit.origin) == (
        "années",
        "human",
    )
    logic.write(project, "sommeil_q2", "label", "Sommeil réparateur", now=NOW)
    label = project.variable("sommeil_q2").label
    assert (label.value, label.status, label.proposed_value) == (
        "Sommeil réparateur",
        "corrected",
        "Q2 sommeil reparateur",
    )
    logic.write(project, "sommeil_q2", "label", "Sommeil réparateur", now=NOW)  # no change
    assert project.variable("sommeil_q2").label.proposed_value == "Q2 sommeil reparateur"


def test_privacy_confirmed_or_changed(project):
    logic.set_privacy(project, "courriel", "likely_identifier", now=NOW)
    assert project.variable("courriel").privacy.privacy_class.status == "validated"
    logic.set_privacy(project, "taille_cm", "quasi_identifier", now=NOW)
    tracked = project.variable("taille_cm").privacy.privacy_class
    assert (tracked.value, tracked.status, tracked.proposed_value) == (
        "quasi_identifier",
        "corrected",
        "ordinary",
    )
    with pytest.raises(logic.ReviewError):
        logic.set_privacy(project, "age", "secret", now=NOW)


@pytest.mark.parametrize("source", ["", "   "])
def test_thresholds_and_ranges_need_a_source(project, source):
    with pytest.raises(logic.ReviewError, match="source documentée"):
        logic.add_threshold(project, "sommeil_q1", 14, "Seuil fictif", source)
    with pytest.raises(logic.ReviewError, match="source documentée"):
        logic.set_theoretical_range(project, "sommeil_q1", 1, 5, source)
    with pytest.raises(logic.ReviewError, match="source documentée"):
        logic.set_instrument(project, "G1", "Questionnaire fictif", source)
    entry = project.variable("sommeil_q1")
    assert entry.thresholds == [] and entry.theoretical_range is None
    assert project.groups[0].instrument_name is None


def test_sourced_fields_with_a_source(project):
    logic.add_threshold(project, "sommeil_q1", 14, "Seuil fictif", "Manuel fictif, p. 3")
    logic.set_theoretical_range(project, "sommeil_q1", 1, 5, "Questionnaire fictif")
    logic.set_instrument(project, "G1", "Questionnaire fictif du sommeil", "Manuel fictif")
    logic.set_references_and_notes(project, "sommeil_q1", "Réf. A\n\nRéf. B\n", "  Note  ")
    entry = project.variable("sommeil_q1")
    assert entry.thresholds[0].source == "Manuel fictif, p. 3"
    assert (entry.theoretical_range.min, entry.theoretical_range.max) == (1, 5)
    assert entry.references == ["Réf. A", "Réf. B"] and entry.notes == "Note"
    assert project.groups[0].instrument_name.value == "Questionnaire fictif du sommeil"
    logic.remove_threshold(project, "sommeil_q1", 0)
    assert entry.thresholds == []


def test_range_must_be_ordered(project):
    with pytest.raises(logic.ReviewError, match="invalide"):
        logic.set_theoretical_range(project, "sommeil_q1", 5, 1, "Source")


def test_reverse_items(project):
    logic.set_reverse_items(project, "G1", ["sommeil_q6", "sommeil_q3"])
    assert project.groups[0].reverse_items == ["sommeil_q3", "sommeil_q6"]
    with pytest.raises(logic.ReviewError, match="anx1"):
        logic.set_reverse_items(project, "G1", ["anx1"])


def test_signal_texts(project):
    assert logic.signal_texts(project.variable("sommeil_q7")) == [
        "Libellé deviné : la variable n'a pas d'étiquette dans le fichier"
    ]


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (lambda p: logic.add_threshold(p, "sommeil_q1", 14, "", "Manuel"), "signification"),
        (lambda p: logic.set_theoretical_range(p, "sommeil_q1", 5, 1, "Manuel"), "minimum"),
    ],
)
def test_invalid_values_are_explained_in_french(project, build, expected):
    with pytest.raises(logic.ReviewError) as caught:
        build(project)
    assert expected in str(caught.value)
    assert "validation error" not in str(caught.value)


# --- The interface, run by Streamlit's test runner: no browser, no network. ---
# On Windows, its event loop opens an internal socket pair on this computer: allow_hosts
# lets sockets be created but connect only to 127.0.0.1 (not enable_socket, which would
# lift every restriction).


@pytest.fixture
def app(project, tmp_path):
    path = tmp_path / "etude.dd.json"
    save_project(project, path)
    test = AppTest.from_file(str(APP), default_timeout=30)
    test.session_state["project_path"] = str(path)
    test.run()
    assert not test.exception, test.exception
    return test, path


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_interface_opens_on_the_variables_to_review(app):
    test, _path = app
    assert test.sidebar.selectbox(key="variable").value == "sommeil_q1"
    assert test.header[0].value.startswith("sommeil_q1")
    assert "2 variables" not in test.sidebar.markdown  # progress shown as a bar
    labels = [b.label for b in test.button]
    assert "Accepter" in labels and "Rejeter" in labels


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_accept_in_the_interface_saves_the_project(app):
    test, path = app
    test.button(key="accept-sommeil_q1-label").click().run()
    assert not test.exception
    assert load_project(path).variable("sommeil_q1").label.status == "validated"
    assert test.success[0].value == "Enregistré."
    assert test.main.children[0].type != "alert"  # under the field, not at the top


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_value_typed_before_the_click_is_kept(app):
    test, path = app
    test.text_input(key="input-sommeil_q1-description").input("Texte tapé juste avant.")
    test.button(key="save-sommeil_q1-description").click().run()
    description = load_project(path).variable("sommeil_q1").description
    assert (description.value, description.status) == ("Texte tapé juste avant.", "corrected")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_threshold_without_source_is_refused_in_the_interface(app):
    test, path = app
    test.number_input(key="threshold-value-sommeil_q1").set_value(14)
    test.text_input(key="threshold-meaning-sommeil_q1").input("Seuil fictif")
    test.button(key="add-threshold-sommeil_q1").click().run()
    assert "source documentée" in test.error[0].value
    assert load_project(path).variable("sommeil_q1").thresholds == []


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_message_is_shown_next_to_its_button(app):
    test, _path = app
    test.button(key="add-threshold-sommeil_q1").click().run()
    assert len(test.error) == 1
    expander = test.expander[0]
    assert any("signification" in e.value for e in expander.error)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_chosen_variable_stays_after_a_decision(app):
    test, _path = app
    test.sidebar.radio(key="filter").set_value("all").run()
    test.sidebar.selectbox(key="variable").select("sommeil_q2").run()
    test.text_input(key="input-sommeil_q2-label").input("Sommeil réparateur")
    test.button(key="save-sommeil_q2-label").click().run()
    assert test.sidebar.selectbox(key="variable").value == "sommeil_q2"
    assert test.header[0].value.startswith("sommeil_q2")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_variable_leaving_the_filter_gives_way_to_the_next(app):
    test, _path = app
    test.button(key="accept-sommeil_q1-label").click().run()
    assert test.sidebar.selectbox(key="variable").value == "sommeil_q1"  # description left
    test.button(key="accept-sommeil_q1-description").click().run()
    assert test.sidebar.selectbox(key="variable").value == "sommeil_q7"
    assert any("suivante : sommeil_q7" in i.value for i in test.info)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_changing_the_filter_gives_no_notice(app):
    test, _path = app
    test.sidebar.radio(key="filter").set_value("sensitive").run()
    assert test.sidebar.selectbox(key="variable").value == "id_participant"
    assert not test.info


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_rejected_label_is_not_offered_again(app):
    test, path = app
    test.sidebar.selectbox(key="variable").select("sommeil_q7").run()
    test.sidebar.radio(key="filter").set_value("all").run()
    test.button(key="reject-sommeil_q7-label").click().run()
    assert test.text_input(key="input-sommeil_q7-label").value == ""
    test.button(key="save-sommeil_q7-label").click().run()
    assert load_project(path).variable("sommeil_q7").label.status == "rejected"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_guessed_label_is_shown_as_a_warning(app):
    test, _path = app
    test.sidebar.selectbox(key="variable").select("sommeil_q7").run()
    assert any("deviné" in e.value for e in test.error)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_groups_view(app):
    test, path = app
    test.sidebar.radio(key="mode").set_value("groups").run()
    assert test.header[0].value.startswith("G1")
    test.text_input(key="instrument-G1").input("Questionnaire fictif")
    test.text_input(key="instrument-source-G1").input("Manuel fictif")
    test.button(key="save-instrument-G1").click().run()
    assert load_project(path).groups[0].instrument_name.source == "Manuel fictif"


# --- Launch: this computer only, no usage statistics. ---


def test_review_command_is_local_without_statistics(tmp_path):
    command, env = review_command(tmp_path / "p.dd.json", 8600)
    joined = " ".join(command)
    assert REVIEW_HOST == "127.0.0.1"
    assert "--server.address 127.0.0.1" in joined
    assert "--browser.gatherUsageStats false" in joined
    assert "--server.port 8600" in joined
    assert "--server.headless true" in joined  # no first-run email prompt
    assert "--client.toolbarMode minimal" in joined  # no "Deploy" button
    assert command[-2:] == ["--", str((tmp_path / "p.dd.json").resolve())]
    assert env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false"
    assert env["STREAMLIT_SERVER_ADDRESS"] == "127.0.0.1"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_interface_tests_still_cannot_reach_outside():
    import socket

    from pytest_socket import SocketConnectBlockedError

    with pytest.raises(SocketConnectBlockedError):
        socket.create_connection(("192.0.2.1", 80), timeout=1)  # documentation address
