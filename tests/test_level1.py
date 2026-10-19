"""v0.18 (D-136): level 1, a witness test. A fictional base whose answers give numbers
found nowhere else (values, proportions, minimum, maximum, mean, share of missing values,
years, the observed range of a group's codes): none may be in a message to the model.

The control: the prompt of the local model (level 2, kept for the bench) does send them,
so the witnesses would show if level 1 let them through.
"""

import json

import pandas as pd
import pytest

from ddict import naming
from ddict.io import read_csv
from ddict.llm import build_blocks
from ddict.llm.link import build_link_blocks
from ddict.llm.stems import build_stem_blocks
from ddict.project import TrackedValue, build_project
from ddict.workflow import add_questionnaire

N = 100
# What the answers give, and nothing else in the base does.
WITNESSES = {
    "minimum": "7391",
    "maximum": "7399",
    "mean": "7395",
    "proportion": "0.37",
    "other proportion": "0.63",
    "first year": "1987",
    "last year": "1993",
    "missing": "13.0",
    "observed code": "61",
    "group's range": "codes de 2 à 6",
}
QUESTIONNAIRE = """Étude témoin

Quel est votre score au jeu ?

Quel est votre statut ?
Premier
Second

Quelle est la date de votre visite ?

Comment est votre humeur aujourd'hui ?

Dans quelle mesure les énoncés suivants de l'échelle s'appliquent-ils à vous ?
\tPas du tout\tUn peu\tMoyennement\tBeaucoup\tExtrêmement
1. Je me sens calme.\t\t\t\t\t
2. Je me sens reposé.\t\t\t\t\t
3. Je me sens attentif.\t\t\t\t\t
4. Je me sens patient.\t\t\t\t\t
"""


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    rows = range(N)
    table = pd.DataFrame(
        {
            "participant": [f"P{i:03d}" for i in rows],
            "score": [7391 if i % 2 else 7399 for i in rows],
            "statut": [61 if i < 37 else 62 for i in rows],
            "date_visite": [f"{1987 + i % 7}-03-01" for i in rows],
            "humeur": [None if i < 13 else 1 + i % 3 for i in rows],
            **{f"echelle_{k}": [2 + (i + k) % 5 for i in rows] for k in (1, 2, 3, 4)},
        }
    )
    folder = tmp_path_factory.mktemp("temoins")
    table.to_csv(folder / "temoins.csv", index=False)
    (folder / "questionnaire.txt").write_text(QUESTIONNAIRE, encoding="utf-8")
    found = build_project(read_csv(folder / "temoins.csv"))
    add_questionnaire(found, folder / "questionnaire.txt")
    ids = [q.question_id for q in found.questionnaire.questions]
    for name, rank in (("score", 0), ("statut", 1), ("humeur", 3)):  # as a person links them
        found.variable(name).question = TrackedValue[str](value=ids[rank], origin="human")
    naming.propose(found)
    return found


def _text(blocks):
    return "\n".join(m["content"] for b in blocks for m in b.messages)


def test_the_control_level_2_sends_the_witnesses(project):
    text = _text(build_blocks(project, size=25, version="variables-v3"))
    for name, witness in WITNESSES.items():
        assert witness in text, name


def test_labels_send_no_witness(project):
    text = _text(build_blocks(project, size=25))
    for name, witness in WITNESSES.items():
        assert witness not in text, name
    sent = [
        v for b in build_blocks(project) for v in json.loads(b.messages[1]["content"])["variables"]
    ]
    assert {v["name"] for v in sent} == {v.name for v in project.variables}


def test_links_and_stems_send_no_witness(project):
    links = build_link_blocks(project, size=20)
    stems = build_stem_blocks(project, size=8)
    assert links and stems  # the questionnaire gives both something to send
    text = _text(links + stems)
    for name, witness in WITNESSES.items():
        assert witness not in text, name
