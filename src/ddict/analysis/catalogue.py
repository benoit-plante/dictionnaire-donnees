"""The catalogue of analyses as data (v0.9, step 3): for each analysis, its roles, the
measure levels each role takes, how many variables and modalities, and its options. The
fiches are `docs/catalogue-analyses.md` (validated, D-077)."""

from __future__ import annotations

from dataclasses import dataclass, field

from ddict.i18n import N_, Texts

SCALE, ORDINAL, NOMINAL = "scale", "ordinal", "nominal"
CATEGORICAL = (NOMINAL, ORDINAL)


@dataclass(frozen=True)
class Role:
    key: str
    levels: tuple[str, ...]
    least: int = 1  # variables, at least
    most: int = 1  # variables, at most
    modalities: tuple[int, int] | None = None  # observed modalities, at least and at most


@dataclass(frozen=True)
class Analysis:
    key: str
    roles: tuple[Role, ...]
    options: dict[str, tuple[str, ...]] = field(default_factory=dict)  # first is the default
    independent: bool = True  # assumes independent observations
    same_person: bool = False  # v0.14 (D-112): columns of one row, refused in long format

    def role(self, key: str) -> Role:
        return next(r for r in self.roles if r.key == key)


CATALOGUE = {
    a.key: a
    for a in (
        Analysis(
            "table1",
            (
                Role("variables", (SCALE, ORDINAL, NOMINAL), least=1, most=30),
                Role("group", CATEGORICAL, least=0, most=1, modalities=(2, 6)),
            ),
            independent=False,
        ),
        Analysis(
            "t_test",
            (Role("outcome", (SCALE,)), Role("group", CATEGORICAL, modalities=(2, 20))),
            {
                "method": ("welch", "student", "mann_whitney"),
                "alternative": ("two_sided", "greater", "less"),
            },
        ),
        Analysis(
            "paired",
            (Role("first", (SCALE,)), Role("second", (SCALE,))),
            {
                "method": ("paired_t", "wilcoxon"),
                "alternative": ("two_sided", "greater", "less"),
            },
            independent=False,
            same_person=True,
        ),
        Analysis(
            "anova",
            (Role("outcome", (SCALE,)), Role("group", CATEGORICAL, modalities=(3, 10))),
            {"method": ("anova", "kruskal_wallis"), "post_hoc": ("none", "tukey")},
        ),
        Analysis(
            "chi_square",
            (
                Role("rows", CATEGORICAL, modalities=(2, 10)),
                Role("columns", CATEGORICAL, modalities=(2, 10)),
            ),
            {"method": ("pearson", "fisher")},
        ),
        Analysis(
            "correlation",
            (Role("variables", (SCALE, ORDINAL), least=2, most=10),),
            {"method": ("pearson", "spearman")},
        ),
        Analysis(
            "regression",
            (Role("outcome", (SCALE,)), Role("predictors", (SCALE, ORDINAL, NOMINAL), most=10)),
        ),
    )
}

TITLES = Texts(
    {
        "table1": N_("Tableau 1 : décrire l'échantillon"),
        "t_test": N_("Test t : comparer deux groupes"),
        "paired": N_("Test t apparié : comparer deux mesures d'une même personne"),
        "anova": N_("ANOVA : comparer plusieurs groupes"),
        "chi_square": N_("Khi-carré : associer deux variables catégorielles"),
        "correlation": N_("Corrélation : relier des variables continues"),
        "regression": N_("Régression linéaire : prédire une variable continue"),
    }
)
ROLES = Texts(
    {
        "variables": N_("Variables"),
        "group": N_("Variable de groupe"),
        "outcome": N_("Variable dépendante"),
        "rows": N_("Variable en lignes"),
        "columns": N_("Variable en colonnes"),
        "predictors": N_("Prédicteurs"),
        "first": N_("Première mesure"),
        "second": N_("Seconde mesure"),
    }
)
PURPOSES = Texts(
    {
        "table1": N_(
            "Décrit les participants : moyenne et écart-type des variables continues, "
            "effectifs et pourcentages des catégories, au besoin par groupe."
        ),
        "t_test": N_(
            "Compare la moyenne d'une variable continue entre deux groupes, par exemple "
            "intervention et contrôle."
        ),
        "paired": N_(
            "Compare deux mesures d'une même personne, par exemple avant et après une intervention."
        ),
        "anova": N_("Compare la moyenne d'une variable continue entre trois groupes ou plus."),
        "chi_square": N_(
            "Regarde si deux variables catégorielles sont associées, par exemple le secteur "
            "d'emploi et le télétravail."
        ),
        "correlation": N_("Mesure la force du lien entre deux variables continues ou plus."),
        "regression": N_(
            "Estime comment plusieurs prédicteurs, ensemble, expliquent une variable continue."
        ),
    }
)
OPTIONS = Texts(
    {
        "method": N_("Méthode"),
        "alternative": N_("Hypothèse"),
        "post_hoc": N_("Comparaisons deux à deux"),
        "levels": N_("Modalités comparées"),
    }
)
CHOICES = Texts(
    {
        "welch": N_("Welch (variances inégales permises)"),
        "student": N_("Student (variances égales)"),
        "mann_whitney": N_("Mann-Whitney (sans supposer la normalité)"),
        "paired_t": N_("Test t apparié"),
        "wilcoxon": N_("Wilcoxon des rangs signés (sans supposer la normalité)"),
        "two_sided": N_("Bilatérale"),
        "greater": N_("Unilatérale : le premier groupe plus élevé"),
        "less": N_("Unilatérale : le premier groupe moins élevé"),
        "anova": N_("ANOVA de Fisher"),
        "kruskal_wallis": N_("Kruskal-Wallis (sans supposer la normalité)"),
        "none": N_("Aucune"),
        "tukey": N_("Tukey"),
        "pearson": N_("Pearson"),
        "fisher": N_("Test exact de Fisher"),
        "spearman": N_("Spearman"),
    }
)
