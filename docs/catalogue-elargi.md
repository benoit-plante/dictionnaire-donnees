# Catalogue élargi (v0.14)

> Statut : **validé par l'auteur le 2026-10-18 (étape 1 de la v0.14)**, avec les choix proposés au § 9 : Greenhouse-Geisser dans la phrase quand Mauchly donne *p* < ,05 ; la seconde modalité prédite par défaut. Plan : [`plan-v0.14.md`](plan-v0.14.md), décisions D-111 à D-115. Les exemples sont calculés sur la base fictive `etude-suivi` (240 participants, graine fixe, effets plantés ; `scripts/generer_base_suivi.py`, corrigé `corrige-suivi.json`) par un prototype, avec SciPy et statsmodels, puis **refaits dans R** (R 4.6.1, R de base et haven) : mêmes valeurs, aux deux écarts près signalés au § 9.

## 1. Règles communes

Celles du catalogue de la v0.9 ([`catalogue-analyses.md`](catalogue-analyses.md), § 1) valent pour les cinq analyses nouvelles :

- les décisions acceptées appliquées en mémoire (codes manquants, noms, items inversés, scores, règles d'exclusion) ; le fichier d'origine jamais modifié ;
- **cas complets par analyse**, le nombre de lignes écartées donné ;
- nombres à la française, deux décimales, trois pour les *p*, **sans zéro initial** pour *p*, *r*, *R²* et η² ;
- **une phrase qui décrit sans juger** : ni « significatif », ni « effet », ni « confirme » ;
- intervalles de confiance à 95 % ;
- des **refus** avec leur raison, des **avertissements** que la personne juge, un signalement sous 5 personnes ;
- un **script R en R de base** (et haven pour lire la base), avec les mêmes formules que l'outil.

**Les mesures d'une même personne** (test apparié, ANOVA à mesures répétées) sont des colonnes d'une même ligne. Ces deux analyses sont refusées quand la description de la base dit « longitudinale, format long » : une ligne n'y est pas une personne (D-112).

## 2. Test *t* apparié — comparer deux mesures d'une même personne

| | |
|---|---|
| **Rôles** | deux variables continues (`scale` ou score) mesurées chez les mêmes personnes : la **première mesure** et la **seconde mesure** |
| **Conditions (refus)** | les deux variables sont continues et distinctes ; au moins 2 personnes qui ont les deux mesures ; une base décrite en format long |
| **Options** | **test *t* apparié** (par défaut) ou **Wilcoxon des rangs signés** (non paramétrique) ; bilatéral (par défaut) ou unilatéral, réglé par le sens attendu d'une hypothèse |
| **Calcul** | `scipy.stats.ttest_rel` ; Shapiro-Wilk sur les différences ; Wilcoxon : différences nulles écartées, approximation normale avec correction de continuité et correction des ex æquo, comme `wilcox.test` |
| **Taille d'effet** | ***d*<sub>z</sub>** = moyenne des différences / écart-type des différences ; IC 95 % par la loi *t* non centrale (ddl = *n* − 1). Wilcoxon : **corrélation bisériale de rang** *r* = (W₊ − W₋) / (W₊ + W₋), positive quand la première mesure est plus haute |
| **Avertissements** | moins de 5 personnes ; Shapiro-Wilk *p* < ,05 sur les différences avec moins de 30 personnes ; des différences nulles écartées par Wilcoxon (leur nombre) |
| **Équivalent R** | `t.test(x, y, paired = TRUE)`, `wilcox.test(x, y, paired = TRUE, exact = FALSE, correct = TRUE)` ; *d*<sub>z</sub> et son intervalle par la loi *t* non centrale (`pt`, `uniroot`) |

**Exemple** — anxiété au début et à la fin du programme :

| | Début | Fin | Différence |
|---|---|---|---|
| *n* | 228 | 228 | |
| *M* (*ÉT*) | 21,56 (6,38) | 18,56 (6,65) | 3,00, IC 95 % [2,28 ; 3,72] |

*t*(227) = 8,18, *p* < ,001 ; *d*<sub>z</sub> = 0,54, IC 95 % [0,40 ; 0,68]. Wilcoxon : V = 20169, *p* < ,001, *r* = ,56 (une différence nulle écartée). 12 participants écartés (une mesure manquante).

> Anxiété au début du programme (0 à 40) : M = 21,56 (ÉT = 6,38) ; anxiété à la fin du programme (0 à 40) : M = 18,56 (ÉT = 6,65) ; différence 3,00, IC 95 % [2,28 ; 3,72], t(227) = 8,18, p < ,001, d_z = 0,54, IC 95 % [0,40 ; 0,68] (n = 228).

**Tableau** : les deux mesures en colonnes (*n*, *M*, *ÉT*), puis la différence, *t*, ddl, *p*, *d*<sub>z</sub> et son IC. **Figure** : les deux moyennes et leur IC 95 %, reliées par une ligne.

## 3. ANOVA à mesures répétées — comparer trois mesures ou plus d'une même personne

| | |
|---|---|
| **Rôles** | de 3 à 10 variables continues, les **mesures** dans l'ordre du temps |
| **Conditions (refus)** | les variables sont continues et distinctes ; au moins 3 personnes qui ont toutes les mesures ; une base décrite en format long |
| **Options** | comparaisons deux à deux : aucune (par défaut) ou tests *t* appariés corrigés par **Holm** |
| **Calcul** | sommes des carrés (temps, personnes, erreur) ; *F*, ddl, *p* ; **test de sphéricité de Mauchly** ; **epsilon de Greenhouse-Geisser** et *F* corrigé (ddl multipliés par ε) |
| **Taille d'effet** | **η² partiel** = SC<sub>temps</sub> / (SC<sub>temps</sub> + SC<sub>erreur</sub>) |
| **Avertissements** | moins de 5 personnes ; Mauchly *p* < ,05 (la phrase donne alors les ddl et le *p* corrigés) |
| **Équivalent R** | `anova(lm(cbind(t1, t2, t3) ~ 1), X = ~1, test = "Spherical")` (*F*, ε et *p* corrigé de Greenhouse-Geisser) ; `mauchly.test` ; η² partiel par sa formule ; `t.test(paired = TRUE)` et `p.adjust(method = "holm")` |

**Exemple** — anxiété aux trois temps (203 personnes qui ont les trois mesures ; 37 écartées) :

| Temps | *M* (*ÉT*) |
|---|---|
| Début du programme | 21,60 (6,41) |
| Fin du programme | 18,69 (6,67) |
| Trois mois après | 17,86 (6,80) |

*F*(2, 404) = 28,93, *p* < ,001, η² partiel = ,13. Mauchly : W = 0,83, *p* < ,001 ; Greenhouse-Geisser : ε = 0,86, *F*(1,72 ; 346,74), *p* < ,001. Comparaisons (Holm) : début et fin, *t*(202) = 7,32, *p* < ,001 ; début et trois mois, *t*(202) = 6,61, *p* < ,001 ; fin et trois mois, *t*(202) = 1,46, *p* = ,145.

> Anxiété aux trois mesures : F(1,72 ; 346,74) = 28,93, p < ,001, η²p = ,13, ε = 0,86 (Greenhouse-Geisser) ; moyennes : début du programme 21,60 ; fin du programme 18,69 ; trois mois après 17,86 (n = 203).

**Tableau** : *n*, *M*, *ÉT* de chaque mesure ; dans la note, *F*, ddl, *p*, η² partiel, Mauchly et ε ; les comparaisons dans un second tableau. **Figure** : les moyennes et leur IC 95 %, reliées dans l'ordre du temps.

## 4. Régression logistique binaire — prédire une issue oui/non

| | |
|---|---|
| **Rôles** | une **issue** nominale à deux modalités ; un ou plusieurs prédicteurs continus ou catégoriels (indicatrices, la première modalité en référence) |
| **Conditions (refus)** | l'issue a exactement deux modalités observées ; au moins 10 personnes dans la modalité la plus rare par prédicteur ; aucun prédicteur qui se déduit des autres |
| **Options** | la **modalité prédite** : la seconde dans l'ordre des codes, par défaut (1 = Oui face à 0 = Non) |
| **Calcul** | `statsmodels` (`Logit`, maximum de vraisemblance) : *b*, ET, *z*, *p* ; **rapport de cotes** RC = e<sup>*b*</sup> et son IC 95 % (Wald, e<sup>*b* ± 1,96 ET</sup>) ; test du rapport de vraisemblance face au modèle sans prédicteur (χ², ddl, *p*) ; R² de McFadden et de Nagelkerke |
| **Avertissements** | séparation complète ou quasi complète (un coefficient ou une erreur type qui s'emballe : l'estimation n'est pas fiable) ; moins de 20 personnes dans la modalité rare par prédicteur ; un VIF supérieur à 5 |
| **Équivalent R** | `glm(issue ~ ..., family = binomial, control = glm.control(epsilon = 1e-12))` ; `exp(confint.default(...))` ; χ² = déviance nulle − déviance du modèle |

**Exemple** — abandon du programme (Oui) selon la motivation et l'âge (240 personnes, dont 76 Oui) :

| Prédicteur | *b* | ET | *z* | *p* | RC | IC 95 % du RC |
|---|---|---|---|---|---|---|
| Constante | 2,82 | 0,76 | 3,73 | < ,001 | | |
| Motivation | −0,51 | 0,09 | −5,43 | < ,001 | 0,60 | [0,50 ; 0,72] |
| Âge | −0,02 | 0,01 | −1,55 | ,121 | 0,98 | [0,96 ; 1,00] |

χ²(2) = 38,11, *p* < ,001 ; R² de McFadden = ,13, de Nagelkerke = ,21.

> Régression logistique de « A abandonné le programme » (Oui, 76 sur 240) : χ²(2) = 38,11, p < ,001 face au modèle sans prédicteur, R² de Nagelkerke = ,21. Les coefficients et les rapports de cotes sont dans le tableau.

Pour un prédicteur testé (plan) : « Motivation : RC = 0,60, IC 95 % [0,50 ; 0,72], z = −5,43, p < ,001. »

**Tableau** : celui ci-dessus ; dans la note, la modalité prédite, *n*, le χ² et les R². **Figure** : les rapports de cotes et leur IC 95 %, sur une échelle logarithmique, une ligne verticale à 1.

## 5. Modération — un lien qui dépend d'une troisième variable

| | |
|---|---|
| **Rôles** | une variable dépendante continue ; un **prédicteur** continu ; un **modérateur** continu, ou nominal à deux modalités ; facultatif : des covariables |
| **Conditions (refus)** | la variable dépendante et le prédicteur sont continus ; au moins 10 observations par terme du modèle ; le modérateur n'est pas le prédicteur |
| **Options** | centrer le prédicteur et le modérateur continus sur leur moyenne (par défaut, oui) |
| **Calcul** | `statsmodels` (`ols`) sur prédicteur, modérateur, **interaction** (produit) et covariables : *b*, ET, *t*, *p*, IC ; R², **ΔR²** de l'interaction et son *F* ; **pentes simples** du prédicteur à −1 ÉT, à la moyenne et à +1 ÉT du modérateur (ou dans chaque modalité), avec ET, *t*, *p* et IC |
| **Avertissements** | ceux de la régression linéaire (VIF supérieur à 5, résidus non normaux avec moins de 30 observations) |
| **Équivalent R** | `lm(y ~ x_c * w_c)` ; ΔR² par `anova(m0, m)` ; pentes simples par leur formule, *b*<sub>x</sub> + *w* *b*<sub>x×w</sub>, ET = √(V<sub>xx</sub> + *w*² V<sub>ii</sub> + 2*w* V<sub>xi</sub>) |

**Exemple** — épuisement selon la charge de travail, modéré par le soutien des collègues (240 personnes ; variables centrées) :

| Prédicteur | *b* | ET | IC 95 % | *t* | *p* |
|---|---|---|---|---|---|
| Constante | 12,32 | 0,20 | [11,92 ; 12,72] | 60,35 | < ,001 |
| Charge (centrée) | 1,29 | 0,10 | [1,09 ; 1,50] | 12,58 | < ,001 |
| Soutien (centré) | −0,63 | 0,10 | [−0,84 ; −0,43] | −6,16 | < ,001 |
| Charge × soutien | −0,32 | 0,05 | [−0,42 ; −0,21] | −5,89 | < ,001 |

R² = ,49 ; interaction : ΔR² = ,07, *F*(1, 236) = 34,72, *p* < ,001.

| Pente de la charge | *b* | ET | IC 95 % | *t* | *p* |
|---|---|---|---|---|---|
| Soutien bas (−1 ÉT) | 1,93 | 0,16 | [1,62 ; 2,23] | 12,39 | < ,001 |
| Soutien moyen | 1,29 | 0,10 | [1,09 ; 1,50] | 12,58 | < ,001 |
| Soutien haut (+1 ÉT) | 0,66 | 0,14 | [0,38 ; 0,94] | 4,66 | < ,001 |

> L'interaction entre la charge de travail et le soutien des collègues était b = −0,32, IC 95 % [−0,42 ; −0,21], t(236) = −5,89, p < ,001, ΔR² = ,07 (n = 240). La pente de la charge de travail était b = 1,93 à soutien bas (−1 ÉT), 1,29 à soutien moyen et 0,66 à soutien haut (+1 ÉT).

**Tableaux** : les coefficients, puis les pentes simples. **Figure** : trois droites, la valeur prédite selon le prédicteur, à soutien bas, moyen et haut.

## 6. Corrélation partielle — une association à covariables constantes

| | |
|---|---|
| **Rôles** | deux **variables** continues ; de 1 à 5 **covariables**, continues ou nominales à deux modalités |
| **Conditions (refus)** | les deux variables sont continues et distinctes des covariables ; au moins *k* + 4 observations (*k* covariables) |
| **Options** | Pearson (la seule dans cette version) |
| **Calcul** | corrélation des résidus de chaque variable régressée sur les covariables ; *t* = *r* √(ddl / (1 − *r*²)), ddl = *n* − 2 − *k* ; IC 95 % par la transformation de Fisher, ET = 1 / √(*n* − 3 − *k*) ; et la corrélation simple, pour comparaison |
| **Avertissements** | moins de 30 observations ; une variable ordinale |
| **Équivalent R** | `cor(resid(lm(x ~ z)), resid(lm(y ~ z)))` ; *t*, *p* et IC par leurs formules |

**Exemple** — stress et heures de sommeil, à charge de travail constante (240 personnes) :

corrélation simple *r* = −,38, *p* < ,001 ; corrélation partielle *r*(237) = −,12, IC 95 % [−,24 ; ,01], *t* = −1,79, *p* = ,075.

> La corrélation partielle entre le score de stress et les heures de sommeil, à charge de travail perçue constante, était r(237) = −,12, IC 95 % [−,24 ; ,01], p = ,075 ; la corrélation simple était r = −,38 (n = 240).

**Tableau** : pour chaque paire, *r* simple et *r* partiel avec leurs IC ; dans la note, les covariables. **Figure** : le nuage des résidus des deux variables, avec sa droite (comme la corrélation, la figure montre chaque personne).

## 7. Le sous-groupe

Une analyse, une entrée du carnet ou une hypothèse du plan peut porter sur un sous-groupe (D-113).

- **La condition** : une variable, un opérateur (`=`, `≠`, `<`, `≤`, `>`, `≥`, « parmi »), une ou des valeurs, comme une condition d'exclusion. Jamais sur un identifiant ni un texte libre ; jamais une liste de personnes.
- **Quand** : après les règles d'exclusion, pour cette analyse seulement ; le flux des participants ne change pas.
- **Ce qui le dit** : la phrase (« Femmes seulement (sexe = Femme) »), la note du tableau, le paragraphe Analyses de la Méthode (« L'analyse A3 porte sur les femmes seulement (sexe = Femme). ») et le script R (`donnees <- donnees[donnees$sexe == 1, ]`, en tête de l'analyse).
- **Dans le plan** : la condition fait partie de l'hypothèse ; la changer après le gel est un amendement, avec sa raison.

**Exemple** — le test apparié de l'anxiété, femmes seulement (126 personnes) : *t*(125) = 6,08, *p* < ,001, *d*<sub>z</sub> = 0,54, IC 95 % [0,35 ; 0,73] ; mêmes valeurs dans R.

> Femmes seulement (sexe = Femme). Anxiété au début du programme (0 à 40) : M = 21,98 (ÉT = 6,81) ; anxiété à la fin du programme (0 à 40) : M = 19,05 (ÉT = 6,48) ; différence 2,93, IC 95 % [1,98 ; 3,89], t(125) = 6,08, p < ,001, d_z = 0,54, IC 95 % [0,35 ; 0,73] (n = 126).

## 8. Dans le plan et dans l'article

| Analyse | Effet testé | Sens attendu | Test unilatéral |
|---|---|---|---|
| Test *t* apparié, Wilcoxon | la différence entre les deux mesures | « Début plus élevé que Fin », ou l'inverse | oui |
| ANOVA à mesures répétées | l'effet du temps | aucun | non |
| Régression logistique | le modèle, ou un prédicteur | prédicteur : positif (RC > 1) ou négatif (RC < 1) | non |
| Modération | l'interaction | positive ou négative | non |
| Corrélation partielle | la corrélation partielle | positive ou négative | non |

- **Le sens attendu par les noms** : sur la page « Plan », le choix dit « Intervention plus élevé » ou « Début du programme plus élevé » plutôt que « Le premier groupe plus élevé », pour le test *t* comme pour le test apparié.
- **La Méthode** gagne une phrase par analyse nouvelle, sur le modèle des six premières : « Deux mesures d'une même personne ont été comparées par le test *t* apparié ; la taille d'effet est le *d*<sub>z</sub>, avec son intervalle de confiance à 95 %. » ; « Les mesures répétées ont été comparées par une ANOVA à mesures répétées ; les degrés de liberté sont corrigés par l'epsilon de Greenhouse-Geisser quand le test de Mauchly donne *p* < ,05. » ; « Une issue à deux modalités a été prédite par une régression logistique ; les coefficients sont donnés en rapports de cotes, avec leur intervalle de confiance à 95 %. » ; « La modération a été estimée par une régression avec un terme d'interaction, sur variables centrées ; les pentes simples sont données à −1 écart-type, à la moyenne et à +1 écart-type du modérateur. » ; « Les corrélations partielles sont calculées à covariables constantes. »
- **La Discussion** dit le sens observé : « La différence observée allait de Début à Fin (Début plus élevé). », « Le rapport de cotes observé de Motivation était inférieur à 1. », « L'interaction observée était négative. », « La corrélation partielle observée était négative. » ; une valeur nulle au centième près n'a pas de sens.

## 9. Points à valider

1. **Les cinq analyses**, leurs rôles, options et conditions (§ 2 à 6), dont : Wilcoxon comme option du test apparié ; 3 à 10 mesures pour l'ANOVA à mesures répétées ; 1 à 5 covariables pour la corrélation partielle ; un modérateur continu ou à deux modalités.
2. **Les tailles d'effet** : *d*<sub>z</sub> avec IC ; *r* bisériale de rang ; η² partiel sans IC (comme η² dans la v0.9) ; rapports de cotes avec IC de Wald ; ΔR² de l'interaction ; *r* partiel avec IC de Fisher.
3. **Greenhouse-Geisser** : la phrase donne les ddl et le *p* corrigés **quand Mauchly *p* < ,05**, les ddl non corrigés sinon ; le tableau donne toujours les deux. (Autre choix : toujours corriger.)
4. **La modalité prédite** de la régression logistique : la seconde dans l'ordre des codes par défaut, changeable.
5. **Le sous-groupe** (§ 7), sa place après les exclusions, et les mots de la phrase et de la Méthode.
6. **Deux exigences pour le calcul**, vues au prototype : le *p* de Wilcoxon sera calculé dans l'outil par la même formule que `wilcox.test` (celui de SciPy diffère de R à 3 × 10⁻⁴ près, par la correction des ex æquo) ; le script R serrera la convergence de `glm` (`epsilon = 1e-12`), dont le réglage par défaut laisse un écart de 2 × 10⁻⁶ sur une erreur type.
7. **Les phrases** de résultat, de Méthode et de Discussion (§ 2 à 8), en français ; l'anglais suivra au moment du code, comme dans les versions précédentes.
