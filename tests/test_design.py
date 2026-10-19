"""v0.20, step B3: the questionnaire designed in the tool (`ddict.design`, D-145, D-146) —
sections and questions changed, ids never given again, and the planned variables, groups and
names made again from the questions at each change. A fictional questionnaire; nothing real."""

from dataclasses import replace

import pytest

from ddict import design
from ddict.design import DesignError, Draft, Item
from ddict.project import dumps, fingerprint, load_project, save_project
from ddict.project.model import Provenance, Scoring, TrackedValue
from ddict.questionnaire import link

TODAY = "2026-10-19"
NOW = "2026-10-19T10:00:00"
TEAM = Provenance(kind="team")
MANUAL = Provenance(kind="source", source="Échelle fictive du sommeil, manuel", page=2)
FREQUENCY = (Item("Jamais", "1"), Item("Parfois", "2"), Item("Souvent", "3"), Item("Toujours", "4"))
ROWS = (
    Item("vous êtes-vous réveillé·e la nuit ?", "SQ001", provenance=MANUAL),
    Item("avez-vous bien dormi ?", "SQ002", provenance=MANUAL),
    Item("avez-vous eu du mal à vous endormir ?", "SQ003", provenance=MANUAL),
)


def _genre(section="S1"):
    return Draft(
        kind="single",
        text="Quel est votre genre ?",
        section=section,
        required=True,
        provenance=TEAM,
        options=(
            Item("Femme", "1"),
            Item("Homme", "2"),
            Item("Préfère ne pas répondre", "9"),
            Item("Autre, précisez", other=True),
        ),
    )


def _sleep(rows=ROWS, section="S2"):
    return Draft(
        kind="grid",
        text="Au cours du dernier mois, à quelle fréquence…",
        section=section,
        instruction="Cochez une case par ligne.",
        provenance=MANUAL,
        options=FREQUENCY,
        rows=rows,
    )


@pytest.fixture
def project():
    """Five questions of each kind, in two sections."""
    found = design.new_project("Étude du sommeil", "fr", TODAY)
    design.modify_section(found, "S1", "Vous")
    design.add_section(found, "Votre sommeil", "Répondez pour le dernier mois.")
    design.add_question(found, _genre())
    design.add_question(
        found, Draft(kind="open", text="Quel âge avez-vous ?", section="S1", answer="number")
    )
    design.add_question(
        found,
        Draft(
            kind="display", text="Les questions suivantes portent sur votre sommeil.", section="S2"
        ),
    )
    design.add_question(found, _sleep())
    design.add_question(
        found,
        Draft(
            kind="checkbox",
            text="Qu'est-ce qui vous aide à dormir ?",
            section="S2",
            options=(Item("La lecture", "1"), Item("La musique", "2"), Item("Autre", other=True)),
        ),
    )
    return found


def _names(project):
    return [e.name for e in project.variables]


def test_a_new_project_has_no_database_and_one_section():
    found = design.new_project("Étude", "en", TODAY)
    assert found.source is None and found.variables == [] and found.settings.language == "en"
    assert [s.section_id for s in found.questionnaire.sections] == ["S1"]
    assert found.questionnaire.sha256 == design.content_fingerprint(found.questionnaire)
    with pytest.raises(DesignError, match="nom"):
        design.new_project("  ", "fr", TODAY)


def test_each_kind_plans_its_variables(project):
    assert _names(project) == [
        "Q1", "Q1_other", "Q2", "Q3", "Q4_SQ001", "Q4_SQ002", "Q4_SQ003", "Q5_1", "Q5_2",
        "Q5_other",
    ]  # fmt: skip
    assert [e.position for e in project.variables] == list(range(1, 11))
    # With its "other" answer, coded "-oth-" as LimeSurvey 7.6 exports it, the question is a
    # text in the .sav (docs/essais/2026-10-19-limesurvey-fictif.md).
    genre = project.variable("Q1")
    assert genre.data_type == "text" and genre.question.value == "Q1"
    assert [(v.code, v.label) for v in genre.file.value_labels] == [
        ("1", "Femme"), ("2", "Homme"), ("9", "Préfère ne pas répondre"),
        ("-oth-", "Autre, précisez"),
    ]  # fmt: skip
    assert genre.label.value == "Quel est votre genre ?" and genre.profile is None
    assert project.variable("Q1_other").question.value == "Q1.o4"
    assert project.variable("Q2").data_type == "decimal"
    assert project.variable("Q4_SQ002").file.label == "avez-vous bien dormi ?"
    # A displayed text has an empty column in every export of LimeSurvey 7.6.
    shown = project.variable("Q3")
    assert shown.data_type == "text" and shown.question.value == "Q3"


def test_grids_and_boxes_become_groups(project):
    scale, boxes = project.groups
    assert (
        scale.question == "Q4"
        and scale.kind == "scale"
        and scale.basis == ["designed_questionnaire"]
    )
    assert scale.members.value == ["Q4_SQ001", "Q4_SQ002", "Q4_SQ003"]
    assert scale.descriptive_label.value == "3 items"
    assert boxes.kind == "multiple_response" and boxes.members.value == ["Q5_1", "Q5_2"]
    assert boxes.attached == ["Q5_other"]
    assert project.variable("Q4_SQ001").group_id.value == scale.group_id
    # The rules propose the measure levels, as for a database (v0.8): never decided.
    assert project.variable("Q4_SQ001").measure_level.status == "proposed"


def test_privacy_from_the_name_and_label(project):
    assert project.variable("Q5_other").privacy.privacy_class.value == "free_text"
    design.add_question(
        project,
        Draft(kind="open", text="Votre courriel", section="S1"),
    )
    design.add_question(
        project,
        Draft(kind="open", text="Décrivez une nuit difficile.", section="S2", answer="long"),
    )
    assert project.variable("Q6").privacy.privacy_class.value == "likely_identifier"
    assert project.variable("Q7").privacy.reasons == ["long_answer_planned"]
    assert project.variable("Q1").privacy.privacy_class.value == "ordinary"


def test_ids_are_never_given_again(project):
    design.remove_question(project, "Q2")
    assert (
        design.add_question(project, Draft(kind="open", text="Votre taille ?", section="S1"))
        == "Q6"
    )
    shorter = (ROWS[0], ROWS[2], Item("vous êtes-vous levé·e tôt ?"))
    old = design.find(project, "Q4")
    kept = tuple(
        Item(r.text, r.code, item_id=row.row_id)
        for r, row in zip(shorter[:2], (old.rows[0], old.rows[2]), strict=True)
    )
    design.modify_question(project, "Q4", _sleep(rows=(*kept, shorter[2])))
    assert [r.row_id for r in design.find(project, "Q4").rows] == ["Q4.r1", "Q4.r3", "Q4.r4"]
    # The new row has no code yet: its variable is named by its id until the team gives one.
    assert "Q4_r4" in _names(project) and "Q4_SQ002" not in _names(project)


def test_a_variable_keeps_its_decisions_through_its_question(project):
    entry = project.variable("Q4_SQ001")
    entry.label = TrackedValue[str](value="Réveils la nuit", origin="human", updated_at=NOW)
    entry.description = TrackedValue[str](value="Fréquence des réveils.", origin="human")
    changed = _sleep(
        rows=tuple(
            Item(r.text.upper(), r.code, item_id=f"Q4.r{n}") for n, r in enumerate(ROWS, start=1)
        )
    )
    design.modify_question(project, "Q4", changed)
    entry = project.variable("Q4_SQ001")
    assert (
        entry.label.value == "Réveils la nuit"
        and entry.description.value == "Fréquence des réveils."
    )
    assert entry.file.label == ROWS[0].text.upper()  # what the questionnaire plans
    assert project.variable("Q4_SQ002").label.value == ROWS[1].text.upper()


def test_the_code_of_a_question_renames_its_variables(project):
    proposed = {s.key: s.stem.value for s in project.stems}
    assert proposed["Q1"] == "genre" and proposed["Q2"] == "age"
    # The rules propose names from proposed stems (D-048); the code waits for a decision.
    assert project.variable("Q1").new_name.status == "proposed" and _names(project)[0] == "Q1"
    project.groups[0].reverse_items = ["Q4_SQ002"]
    project.groups[0].scoring = Scoring(
        items=["Q4_SQ001", "Q4_SQ002", "Q4_SQ003"],
        aggregation="mean",
        scale_min=1,
        scale_max=4,
        score_name="sommeil_moyenne",
        source="Échelle fictive du sommeil, manuel, p. 3 (inventée)",
    )
    changes = design.decide_code(project, "Q4", "write", now=NOW, value="sommeil")
    assert changes.renamed == {f"Q4_SQ00{n}": f"sommeil_SQ00{n}" for n in (1, 2, 3)}
    assert project.groups[0].members.value[0] == "sommeil_SQ001"
    assert project.groups[0].reverse_items == ["sommeil_SQ002"]
    assert project.groups[0].scoring.items == [f"sommeil_SQ00{n}" for n in (1, 2, 3)]
    design.decide_code(project, "Q1", "accept", now=NOW)
    assert _names(project)[:2] == ["genre", "genre_other"]
    assert project.variable("genre").new_name.value == "genre"
    assert project.variable("genre_other").new_name.value == "genre_autre_txt"
    with pytest.raises(DesignError, match="Code refusé"):
        design.decide_code(project, "Q2", "write", now=NOW, value="Âge du participant")


def test_a_rename_the_plan_would_not_follow_is_refused(project):
    project.dataset.design.weight = "Q2"
    before = dumps(project)
    with pytest.raises(DesignError) as refused:
        design.decide_code(project, "Q2", "accept", now=NOW)
    assert "la description de la base cite Q2" in refused.value.reasons
    with pytest.raises(DesignError):
        design.remove_question(project, "Q2")
    assert dumps(project) == before  # refused: nothing changed


def test_what_a_question_needs_is_refused_and_changes_nothing(project):
    before = dumps(project)
    for draft, why in (
        (Draft(kind="single", text="Vous fumez ?", section="S1"), "au moins un choix"),
        (Draft(kind="grid", text="Grille", section="S2", options=FREQUENCY), "au moins un énoncé"),
        (Draft(kind="open", text="", section="S1"), "texte de la question est vide"),
        (Draft(kind="open", text="?", section="S9"), "Section inconnue"),
        (Draft(kind="display", text="Merci", section="S2", options=FREQUENCY), "n'a pas de choix"),
    ):
        with pytest.raises(DesignError, match=why):
            design.add_question(project, draft)
    assert dumps(project) == before


def test_two_items_with_the_same_code_keep_two_names(project):
    twice = (ROWS[0], Item(ROWS[1].text, "SQ001", item_id="Q4.r2"), ROWS[2])
    design.modify_question(
        project, "Q4", _sleep(rows=(Item(ROWS[0].text, "SQ001", item_id="Q4.r1"), *twice[1:]))
    )
    assert _names(project)[4:7] == ["Q4_SQ001", "Q4_r2", "Q4_SQ003"]


def test_moving_sections_and_questions(project):
    design.move_question(project, "Q2", 1)
    assert [q.question_id for q in project.questionnaire.questions] == [
        "Q2",
        "Q1",
        "Q3",
        "Q4",
        "Q5",
    ]
    design.move_section(project, "S2", 1)
    assert [q.question_id for q in project.questionnaire.questions] == [
        "Q3",
        "Q4",
        "Q5",
        "Q2",
        "Q1",
    ]
    assert _names(project)[0] == "Q3" and project.variable("Q2").position == 8
    moved = _genre(section="S2")
    kept = tuple(replace(o, item_id=f"Q1.o{n}") for n, o in enumerate(moved.options, start=1))
    design.modify_question(project, "Q1", replace(moved, options=kept))
    assert [q.question_id for q in project.questionnaire.questions][-1] == "Q2"
    with pytest.raises(DesignError, match="Retirez ou déplacez"):
        design.remove_section(project, "S1")
    design.remove_question(project, "Q2")
    design.remove_section(project, "S1")
    with pytest.raises(DesignError, match="au moins une section"):
        design.remove_section(project, "S2")


def test_links_survive_a_change_of_the_questionnaire(project):
    previous = project.questionnaire.model_copy(deep=True)
    design.modify_question(project, "Q2", Draft(kind="open", text="Votre âge ?", section="S1"))
    assert previous.sha256 != project.questionnaire.sha256
    assert link.drop_stale_links(project, previous) == 0
    assert project.variable("Q2").question.value == "Q2"


def test_the_fingerprint_follows_the_content(project):
    before = fingerprint.fingerprint(project)
    project.questionnaire.file_name = "Autre nom"
    design.modify_section(project, "S1", "Vous")  # the same content: the same fingerprint
    assert project.questionnaire.sha256 == design.content_fingerprint(project.questionnaire)
    assert fingerprint.fingerprint(project) == before
    design.modify_section(project, "S1", "Vous-même")
    assert fingerprint.fingerprint(project) != before


def test_what_removing_a_question_would_take_with_it(project):
    group = project.groups[0]
    group.scoring = Scoring(
        items=list(group.members.value),
        aggregation="sum",
        scale_min=1,
        scale_max=4,
        score_name="sommeil_total",
        source="Échelle fictive du sommeil, manuel, p. 3 (inventée)",
    )
    assert design.citations(project, "Q4") == [
        f"le groupe {group.group_id} a une cotation ou un nom d'instrument"
    ]
    design.modify_question(
        project,
        "Q4",
        _sleep(
            rows=tuple(Item(r.text, r.code, item_id=f"Q4.r{n}") for n, r in enumerate(ROWS[:2], 1))
        ),
    )
    assert project.groups[0].scoring.items == ["Q4_SQ001", "Q4_SQ002"]
    design.remove_question(project, "Q4")
    assert [g.question for g in project.groups] == ["Q5"]


def test_a_designed_project_saves_and_reads_back_byte_for_byte(project, tmp_path):
    path = tmp_path / "Étude conçue.dd.json"
    save_project(project, path)
    reloaded = load_project(path)
    assert dumps(reloaded) == dumps(project)
    design.add_question(reloaded, Draft(kind="open", text="Votre ville ?", section="S1"))
    save_project(reloaded, path)
    texts = [q.text for q in load_project(path).questionnaire.questions]
    assert texts.index("Votre ville ?") == 2  # at the end of its section, S1
