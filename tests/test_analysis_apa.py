"""v0.10, step 2: the APA 7 tables and figures described without a format (D-083), against
the validated sheets (docs/tableaux-figures-apa.md) and against the analyses' own results."""

import pytest

from ddict import i18n
from ddict.analysis.apa import Edit, apa, brackets, describe, edited, plain
from ddict.analysis.compute import run
from test_analysis_data import KEY, _prepared, analyses_project


@pytest.fixture(scope="module")
def ready():
    project = analyses_project()
    return project, _prepared(project, KEY["sav"])


def _doc(ready, key, chosen, options=None, language="fr"):
    project, prepared = ready
    result = run(project, prepared, key, chosen, options)
    return result, describe(project, prepared, result, language=language)


def _cells(table):
    return [[plain(c) for c in row.cells] for row in table.rows]


def _headers(table):
    return [plain(c.header) for c in table.columns]


# --- Numbers. ---


def test_apa_numbers():
    assert apa(0.5773) == "0,58" and apa(0.5773, zero=False) == ",58"
    assert apa(-0.0201, zero=False) == "−,02" and apa(-0.3613, zero=False) == "−,36"
    assert apa(14.2361, zero=False) == "14,24"  # a value above 1 keeps its digits
    assert brackets(0.3458, 0.8079) == "[0,35 ; 0,81]"
    with i18n.using("en"):
        assert brackets(0.3458, 0.8079) == "[0.35, 0.81]"


# --- The validated sheets. ---


def test_table1_as_the_sheet(ready):
    _r, doc = _doc(
        ready,
        "table1",
        {"variables": ["age", "sexe", "niveau_etudes", "bienetre_total"], "group": ["groupe"]},
    )
    table = doc.tables[0]
    assert (table.number, table.title) == (
        1,
        "Caractéristiques des participants selon groupe de l'étude",
    )
    assert _headers(table) == [
        "Caractéristique",
        "Intervention (n = 150)",
        "Contrôle (n = 150)",
        "Total (N = 300)",
    ]
    cells = _cells(table)
    assert cells[0] == ["Âge (années), M (ÉT)", "44,70 (12,77)", "42,41 (12,69)", "43,56 (12,76)"]
    assert cells[2] == ["Femme", "81 (54,0)", "67 (44,7)", "148 (49,3)"]
    assert table.rows[2].indent == 1
    assert cells[-1] == [
        "bienetre_total (score de G1), M (ÉT)",
        "17,01 (4,18)",
        "14,54 (4,39)",
        "15,77 (4,45)",
    ]
    italic = [r.text for r in table.rows[0].cells[0] if r.italic]
    assert italic == ["M", "ÉT"]
    assert plain(table.note).startswith("Âge (années) : 5 valeurs manquantes.")
    assert not doc.figures  # Table 1 has no figure


def test_t_test_as_the_sheet(ready):
    result, doc = _doc(ready, "t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]})
    table = doc.tables[0]
    assert _headers(table) == [
        "Variable",
        "M",
        "ÉT",
        "M",
        "ÉT",
        "t(297,29)",
        "p",
        "d",
        "IC 95 % de d",
    ]
    assert [plain(s.label) for s in table.spanners] == ["Intervention", "Contrôle"]
    assert [(s.first, s.last) for s in table.spanners] == [(1, 2), (3, 4)]
    assert _cells(table)[0][1:] == [
        "17,01",
        "4,18",
        "14,54",
        "4,39",
        "5,00",
        "< ,001",
        "0,58",
        "[0,35 ; 0,81]",
    ]
    assert "Test t de Welch" in plain(table.note)
    figure = doc.figures[0]
    assert (figure.kind, figure.categories) == ("bars", ("Intervention", "Contrôle"))
    s = result.statistics
    assert figure.series[0].values == pytest.approx((s["m1"], s["m2"]))
    low, high = figure.series[0].low[0], figure.series[0].high[0]
    assert low < s["m1"] < high and high - s["m1"] == pytest.approx(s["m1"] - low)
    assert "intervalle de confiance à 95 % de la moyenne" in plain(figure.note)


def test_anova_as_the_sheet(ready):
    _r, doc = _doc(
        ready, "anova", {"outcome": ["stress"], "group": ["niveau_etudes"]}, {"post_hoc": "tukey"}
    )
    first, tukey = doc.tables
    assert _cells(first) == [
        ["Secondaire", "103", "22,28", "4,90", "[21,32 ; 23,24]"],
        ["Collégial", "97", "19,00", "5,69", "[17,85 ; 20,15]"],
        ["Universitaire", "96", "15,89", "5,60", "[14,75 ; 17,02]"],
    ]
    assert plain(first.note) == "F(2, 293) = 34,88, p < ,001, η² = ,19, ω² = ,19."
    assert (first.number, tukey.number) == (1, 2)
    assert _cells(tukey) == [
        ["Collégial − Secondaire", "−3,28", "[−5,08 ; −1,48]", "< ,001"],
        ["Universitaire − Secondaire", "−6,39", "[−8,20 ; −4,59]", "< ,001"],
        ["Universitaire − Collégial", "−3,11", "[−4,94 ; −1,28]", "< ,001"],
    ]
    assert doc.figures[0].series[0].values == pytest.approx((22.28, 19.00, 15.89), abs=0.005)


def test_chi_square_as_the_sheet(ready):
    _r, doc = _doc(ready, "chi_square", {"rows": ["teletravail"], "columns": ["secteur"]})
    table = doc.tables[0]
    assert _headers(table)[1:] == ["Public n (%)", "Privé n (%)", "Communautaire n (%)"]
    assert _cells(table) == [
        ["Oui", "77 (67,0)", "62 (45,9)", "13 (26,0)"],
        ["Non", "38 (33,0)", "73 (54,1)", "37 (74,0)"],
        ["Total", "115", "135", "50"],
    ]
    assert plain(table.note) == (
        "Pourcentages calculés dans chaque colonne. χ²(2, N = 300) = 25,59, p < ,001, "
        "V de Cramér = ,29."
    )
    figure = doc.figures[0]
    assert figure.kind == "grouped_bars" and figure.categories == (
        "Public",
        "Privé",
        "Communautaire",
    )
    assert [s.name for s in figure.series] == ["Oui", "Non"]
    totals = [sum(s.values[i] for s in figure.series) for i in range(3)]
    assert totals == pytest.approx([100, 100, 100])


def test_correlation_as_the_sheet(ready):
    _r, doc = _doc(ready, "correlation", {"variables": ["heures_travail", "stress", "soutien"]})
    table = doc.tables[0]
    assert _headers(table) == ["Variable", "n", "M", "ÉT", "1", "2", "3"]
    assert _cells(table) == [
        ["1. Heures de travail par semaine", "300", "38,22", "5,82", "—", "", ""],
        ["2. Score de stress (0 à 40)", "296", "19,13", "5,99", ",42 [,32 ; ,51]", "—", ""],
        [
            "3. Soutien des collègues (0 à 10)",
            "300",
            "5,98",
            "1,87",
            ",01 [−,10 ; ,12]",
            "−,02 [−,13 ; ,10]",
            "—",
        ],
    ]
    note = plain(table.note)
    assert "(n de 296 à 300)" in note
    assert note.endswith("Ligne 2 : p < ,001. Ligne 3 : p = ,851 et p = ,745.")
    assert not doc.figures  # three variables: no figure


def test_a_scatter_for_two_variables(ready):
    result, doc = _doc(ready, "correlation", {"variables": ["heures_travail", "stress"]})
    figure = doc.figures[0]
    assert figure.kind == "scatter" and len(figure.points) == result.statistics["n"] == 296
    assert plain(figure.note) == "N = 296. r = ,42, IC 95 % [,32 ; ,51]."


def test_regression_as_the_sheet(ready):
    result, doc = _doc(
        ready, "regression", {"outcome": ["satisfaction"], "predictors": ["soutien", "charge"]}
    )
    table = doc.tables[0]
    assert _headers(table) == ["Prédicteur", "b", "IC 95 % de b", "ET", "β", "t", "p"]
    assert _cells(table) == [
        ["Constante", "1,88", "[1,34 ; 2,42]", "0,28", "", "6,82", "< ,001"],
        [
            "Soutien des collègues (0 à 10)",
            "0,51",
            "[0,44 ; 0,58]",
            "0,04",
            ",60",
            "14,24",
            "< ,001",
        ],
        [
            "Charge de travail perçue (0 à 10)",
            "−0,29",
            "[−0,36 ; −0,22]",
            "0,03",
            "−,36",
            "−8,59",
            "< ,001",
        ],
    ]
    assert plain(table.note).startswith("N = 300. R² = ,47, R² ajusté = ,47, F(2, 297) = 134,30")
    figure = doc.figures[0]
    s = result.statistics
    assert figure.kind == "coefficients" and figure.reference == 0
    assert figure.series[0].values == pytest.approx((s["beta_1"], s["beta_2"]))
    for value, low, high in zip(
        figure.series[0].values, figure.series[0].low, figure.series[0].high, strict=True
    ):
        assert low < value < high


# --- Every option of the catalogue. ---


def test_the_other_methods(ready):
    result, doc = _doc(
        ready,
        "t_test",
        {"outcome": ["bienetre_total"], "group": ["groupe"]},
        {"method": "mann_whitney"},
    )
    assert _headers(doc.tables[0])[1:4] == ["Mdn", "Mdn", "U"]
    assert _cells(doc.tables[0])[0][3] == apa(result.statistics["U"], 1)
    assert not doc.figures  # no bars of means for a test on ranks
    _r, doc = _doc(
        ready,
        "anova",
        {"outcome": ["stress"], "group": ["niveau_etudes"]},
        {"method": "kruskal_wallis"},
    )
    assert plain(doc.tables[0].note).startswith("H(2) = ")
    _r, doc = _doc(ready, "correlation", {"variables": ["stress", "sport"]}, {"method": "spearman"})
    assert plain(doc.tables[0].note).startswith("Corrélations de Spearman.")
    assert doc.figures[0].line is None
    _r, doc = _doc(
        ready, "regression", {"outcome": ["satisfaction"], "predictors": ["soutien", "secteur"]}
    )
    assert "Référence pour Secteur d'emploi : Public." in plain(doc.tables[0].note)
    _r, doc = _doc(
        ready,
        "t_test",
        {"outcome": ["stress"], "group": ["niveau_etudes"]},
        {"levels": "1,3", "method": "student"},
    )
    assert _headers(doc.tables[0])[5] == "t(197)"
    assert [plain(s.label) for s in doc.tables[0].spanners] == ["Secondaire", "Universitaire"]


def test_in_english(ready):
    _r, doc = _doc(
        ready, "t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]}, language="en"
    )
    table = doc.tables[0]
    assert _headers(table)[2] == "SD" and _headers(table)[-1] == "95% CI of d"
    assert _cells(table)[0][-1] == "[0.35, 0.81]"
    assert "Welch's t test" in plain(table.note)


# --- What a person may change (D-086). ---


def test_number_title_and_note_only(ready):
    _r, doc = _doc(ready, "anova", {"outcome": ["stress"], "group": ["niveau_etudes"]})
    changed = edited(
        doc,
        {
            "table-1": Edit(number=4, title="Stress et études", note="Ma note."),
            "figure-1": Edit(number=2),
        },
    )
    table = changed.tables[0]
    assert (table.number, table.title, plain(table.note)) == (4, "Stress et études", "Ma note.")
    assert table.rows == doc.tables[0].rows  # the numbers do not change
    assert changed.figures[0].number == 2 and changed.figures[0].title == doc.figures[0].title
    assert edited(doc, {"table-1": Edit(title="  ")}).tables[0].title == doc.tables[0].title
