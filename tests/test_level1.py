"""v0.18 (D-136): level 1, a witness test. A fictional base whose answers give numbers
found nowhere else (values, proportions, minimum, maximum, mean, share of missing values,
years, the observed range of a group's codes): none may be in a message to the model.

The control: the prompt of the local model (level 2, kept for the bench) does send them,
so the witnesses would show if level 1 let them through.
"""

import json

import pandas as pd
import pytest

from ddict.io import read_csv
from ddict.llm import build_blocks
from ddict.project import build_project

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
    path = tmp_path_factory.mktemp("temoins") / "temoins.csv"
    table.to_csv(path, index=False)
    return build_project(read_csv(path))


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
