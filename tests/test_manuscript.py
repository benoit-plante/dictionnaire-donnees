"""v0.15, step 4: the statistics read in a Word manuscript (D-117; docs/verification-depot.md,
§ 2.1): a fictional corpus of sentences and table cells, in French and in English, with the
traps a manuscript holds (dates, numbers of tables, ranges), and the drafts the tool makes."""

import pytest
from docx import Document

from ddict.analysis import manuscript as m


def _read(sentence: str) -> list[tuple]:
    values, _unread = m.statistics(sentence)
    return [(v.stat, v.value, v.decimals, v.relation, tuple(d.value for d in v.df), v.of)
            for v in values]  # fmt: skip


@pytest.mark.parametrize(
    ("text", "value", "decimals"),
    [("−2,28", -2.28, 2), (",011", 0.011, 3), ("0.25", 0.25, 2), ("1 106", 1106.0, 0),
     ("-,38", -0.38, 2), ("818", 818.0, 0), ("4842,5", 4842.5, 1)],
)  # fmt: skip
def test_numbers_as_written(text, value, decimals):
    found = m.number(text)
    assert (found.value, found.decimals) == (value, decimals)


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        ("t(818) = −2,28, p = ,011, d = −0,18, IC 95 % [−0,33 ; −0,02].",
         [("t", -2.28, 2, "=", (818.0,), ""), ("p", 0.011, 3, "=", (), ""),
          ("d", -0.18, 2, "=", (), ""), ("ci_low", -0.33, 2, "=", (), "d"),
          ("ci_high", -0.02, 2, "=", (), "d")]),
        ("t(818) = -2.28, p = .011, d = -0.18, 95% CI [-0.33, -0.02].",
         [("t", -2.28, 2, "=", (818.0,), ""), ("p", 0.011, 3, "=", (), ""),
          ("d", -0.18, 2, "=", (), ""), ("ci_low", -0.33, 2, "=", (), "d"),
          ("ci_high", -0.02, 2, "=", (), "d")]),
        ("t(140,08) = −1,16, p = ,250", [("t", -1.16, 2, "=", (140.08,), ""),
                                         ("p", 0.25, 3, "=", (), "")]),
        ("F(1,72 ; 346,74) = 28,93, p < ,001, η²p = ,13, ε = 0,86",
         [("F", 28.93, 2, "=", (1.72, 346.74), ""), ("p", 0.001, 3, "<", (), ""),
          ("eta2p", 0.13, 2, "=", (), ""), ("eps", 0.86, 2, "=", (), "")]),
        ("F(1.72, 346.74) = 28.93, partial η² = .13", [("F", 28.93, 2, "=", (1.72, 346.74), ""),
                                                       ("eta2p", 0.13, 2, "=", (), "")]),
        ("F(2, 404) = 28,93, η² partiel = ,13", [("F", 28.93, 2, "=", (2.0, 404.0), ""),
                                                 ("eta2p", 0.13, 2, "=", (), "")]),
        ("χ²(2) = 37,45 ; R² de McFadden = ,12, de Nagelkerke = ,20",
         [("chi2", 37.45, 2, "=", (2.0,), ""), ("R2", 0.12, 2, "=", (), ""),
          ("R2", 0.2, 2, "=", (), "")]),
        ("Nagelkerke R² = .20, X2(1) = 19.43", [("R2", 0.2, 2, "=", (), ""),
                                                ("chi2", 19.43, 2, "=", (1.0,), "")]),
        ("r(180) = −,47 ; ρ = ,05 (n = 223)", [("r", -0.47, 2, "=", (180.0,), ""),
                                              ("rho", 0.05, 2, "=", (), ""),
                                              ("n", 223.0, 0, "=", (), "")]),
        ("M = 19,27 (ÉT = 6,15) pour Non", [("M", 19.27, 2, "=", (), ""),
                                            ("SD", 6.15, 2, "=", (), "")]),
        ("M = 19.27, SD = 6.15, N = 1 106", [("M", 19.27, 2, "=", (), ""),
                                             ("SD", 6.15, 2, "=", (), ""),
                                             ("N", 1106.0, 0, "=", (), "")]),
        ("différence 3,00, IC 95 % [2,28 ; 3,72], d_z = 0,54",
         [("diff", 3.0, 2, "=", (), ""), ("ci_low", 2.28, 2, "=", (), "diff"),
          ("ci_high", 3.72, 2, "=", (), "diff"), ("dz", 0.54, 2, "=", (), "")]),
        ("U = 4842,5, p = ,456, r = −,01", [("U", 4842.5, 1, "=", (), ""),
                                            ("p", 0.456, 3, "=", (), ""),
                                            ("r", -0.01, 2, "=", (), "")]),
        ("RC = 0,92, IC 95 % [0,88 ; 0,95], z = −5,36", [("OR", 0.92, 2, "=", (), ""),
                                                        ("ci_low", 0.88, 2, "=", (), "OR"),
                                                        ("ci_high", 0.95, 2, "=", (), "OR"),
                                                        ("z", -5.36, 2, "=", (), "")]),
        ("W de Mauchly = 0,83, p < ,001", [("W", 0.83, 2, "=", (), ""),
                                           ("p", 0.001, 3, "<", (), "")]),
        ("b = −0,50, ET = 0,09, β = −,32, ΔR² = ,04", [("b", -0.5, 2, "=", (), ""),
                                                      ("SE", 0.09, 2, "=", (), ""),
                                                      ("beta", -0.32, 2, "=", (), ""),
                                                      ("dR2", 0.04, 2, "=", (), "")]),
    ],
)  # fmt: skip
def test_the_statistics_of_a_sentence(sentence, expected):
    assert _read(sentence) == expected


@pytest.mark.parametrize(
    "sentence",
    [
        "Le Tableau 2 et la Figure 3 montrent les résultats de H1 et de A3.",
        "Les données ont été recueillies du 1er au 18 octobre 2026 (voir p. 278).",
        "Anxiété au début du programme (0 à 40), mesurée en 2024.",
        "Les participantes (56,9 %) étaient plus nombreuses ; 42,0 % étaient des hommes.",
        "La différence était de 3 points, soit 12 % de l'étendue.",
        "Produit le 2026-10-18 par dictionnaire-donnees 0.15.0 (Python 3.11.9).",
        "[à compléter : titre] Empreinte du codebook : ef32215fd68b.",
    ],
)
def test_no_statistic_in_ordinary_numbers(sentence):
    values, unread = m.statistics(sentence)
    assert values == [] and unread == []


def test_an_unknown_symbol_is_listed_not_guessed():
    values, unread = m.statistics("Q = 3,21 et Kappa = ,62, t(98) = 2,41.")
    assert [v.stat for v in values] == ["t"]
    assert unread == ["Q = 3,21", "Kappa = ,62"]


def test_a_rule_threshold_is_not_a_result():
    values, _unread = m.statistics("Les valeurs de p sont exactes (p < ,001 en deçà).")
    assert [(v.stat, v.threshold) for v in values] == [("p", True)]
    values, _unread = m.statistics("t(227) = 8,18, p < ,001.")
    assert [v.threshold for v in values] == [False, False]


def test_sentences_are_cut_but_never_at_a_decimal_point():
    assert m.sentences("t(818) = -2.28, p = .011. The mean was M = 19.27. Then") == [
        "t(818) = -2.28, p = .011.",
        "The mean was M = 19.27.",
        "Then",
    ]


def _docx(tmp_path):
    document = Document()
    document.add_heading("A1 — Test t", level=2)
    document.add_paragraph("Les femmes avaient M = 20,85 (ÉT = 7,25). Le test : t(818) = −2,28.")
    rows = [
        ["", "Non", "Non", "Oui", "Oui", "", "", "", ""],
        ["Variable", "M", "ÉT", "M", "ÉT", "t(818)", "p", "d", "IC 95 % de d"],
        ["Anxiété", "19,65", "6,51", "20,85", "7,25", "−2,28", "< ,001", "−0,18",
         "[−0,33 ; −0,02]"],
    ]  # fmt: skip
    table = document.add_table(rows=3, cols=9)
    for i, row in enumerate(rows):
        for j, text in enumerate(row):
            table.cell(i, j).text = text
    matrix = document.add_table(rows=3, cols=5)
    cells = [["Variable", "n", "M", "1", "2"], ["1. Stress", "240", "19,59", "—", ""],
             ["2. Sommeil", "240", "6,97", "−,38 [−,49 ; −,27]", "—"]]  # fmt: skip
    for i, row in enumerate(cells):
        for j, text in enumerate(row):
            matrix.cell(i, j).text = text
    path = tmp_path / "manuscrit.docx"
    document.save(str(path))
    return path


def test_a_document_paragraphs_and_tables(tmp_path):
    blocks = m.read(_docx(tmp_path))
    assert [b.where for b in blocks] == [
        "§ 2, phrase 1", "§ 2, phrase 2", "Tableau 1, ligne 1", "Tableau 2, ligne 1",
        "Tableau 2, ligne 2",
    ]  # fmt: skip
    assert {b.section for b in blocks} == {"A1 — Test t"}
    row = blocks[2]
    assert row.label == "Anxiété"
    assert [(v.stat, v.value, tuple(d.value for d in v.df), v.of) for v in row.values] == [
        ("M", 19.65, (), ""), ("SD", 6.51, (), ""), ("M", 20.85, (), ""), ("SD", 7.25, (), ""),
        ("t", -2.28, (818.0,), ""), ("p", 0.001, (), ""), ("d", -0.18, (), ""),
        ("ci_low", -0.33, (), "d"), ("ci_high", -0.02, (), "d"),
    ]  # fmt: skip
    assert row.values[5].relation == "<"
    pair = blocks[4].values
    assert [(v.stat, v.value, v.qualifier) for v in pair if v.stat == "r"] == [("r", -0.38, "1")]


def test_the_drafts_of_the_tool(tmp_path):
    """The draft of an article the tool makes, in French and in English: every statistic of
    the results read, nothing left unread."""
    from ddict.analysis import notebook as nb
    from ddict.analysis import notebook_export as export
    from ddict.analysis.compute import run
    from ddict.analysis.data import apply_decisions
    from ddict.io import read_database
    from ddict.project import build_project
    from test_recode import EXAMPLES, KEY

    data = read_database(EXAMPLES / KEY["sav"])
    project = build_project(data)
    prepared = apply_decisions(project, data.table)
    path = tmp_path / "etude-suivi.dd.json"
    notebook = nb.new_notebook(project, path)
    for key, chosen in [
        ("paired", {"first": ["anxiete_t1"], "second": ["anxiete_t2"]}),
        ("logistic", {"outcome": ["abandon"], "predictors": ["motivation", "stress"]}),
        ("correlation", {"variables": ["stress", "sommeil", "charge"]}),
        ("rm_anova", {"measures": ["anxiete_t1", "anxiete_t2", "anxiete_t3"]}),
    ]:
        nb.add(notebook, project, run(project, prepared, key, chosen), today="2026-10-18")
    for language in ("fr", "en"):
        export.write_results(project, prepared, notebook, path, language=language,
                             today="2026-10-18")  # fmt: skip
        blocks = m.read(export.results_paths(path)["docx"])
        assert [u for b in blocks for u in b.unread] == []
        values = [v for b in blocks for v in b.values]
        stats = {v.stat for v in values}
        assert {"t", "dz", "chi2", "OR", "r", "F", "eta2p", "eps", "W", "M", "SD"} <= stats
        first = next(b for b in blocks if b.section.startswith("A1") and b.kind == "sentence")
        assert [v.stat for v in first.values] == [
            "M", "SD", "M", "SD", "diff", "ci_low", "ci_high", "t", "p", "dz", "ci_low",
            "ci_high", "n",
        ]  # fmt: skip
        assert sum(1 for b in blocks if b.kind == "row" and b.section.startswith("A3")) == 3
