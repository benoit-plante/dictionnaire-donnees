# Catalogue des analyses (v0.9)

> Statut : **validé par l'auteur le 2026-10-15 (étape 1 de la v0.9)**, avec les cinq points du § 9 ; le script R en R de base est consigné dans D-077. Les exemples sont calculés sur les bases fictives révisées (`tests/context_examples.py`) par un prototype, avec SciPy et statsmodels ; le test t a été refait dans R (mêmes t, ddl et p).

## 1. Règles communes

**Les données.** L'outil lit la base comme pour le profilage et applique en mémoire les décisions acceptées, dans l'ordre des fichiers de commandes et du script de préparation : codes manquants déclarés et confirmés retirés, nouveaux noms, items inversés, scores selon la cotation (règle des items manquants comprise). Le fichier d'origine n'est jamais modifié ; rien des données n'est enregistré dans le projet.

**Les observations retenues.** Pour chaque analyse, les lignes où une variable de l'analyse manque sont écartées (cas complets pour l'analyse) ; le nombre de lignes écartées est donné.

**Les conventions de présentation**, à valider :

- nombres à la française (virgule décimale) ; deux décimales pour les statistiques, trois pour les p ;
- **p sans zéro initial**, comme le veut le style APA (`p = ,861` ; `p < ,001` sous un millième) ;
- **la phrase de résultat décrit, elle ne juge pas** : elle donne la direction, la statistique, p et la taille d'effet, sans les mots « significatif » ou « effet » ; l'interprétation reste à l'équipe ;
- intervalles de confiance à 95 %.

**Les conditions et les avertissements.** Une condition non remplie **refuse** l'analyse, avec sa raison ; une hypothèse fragile donne un **avertissement**, et la personne décide. Un groupe ou une case de moins de 5 personnes est signalé dans les résultats (ce sont les résultats de l'équipe, à elle de décider avant de publier).

**Le script R équivalent.** Pour chaque analyse, un script en **R de base** (et `haven` pour lire la base) : lecture, fichier de commandes, script de préparation, puis l'analyse, avec les mêmes formules que l'outil pour les tailles d'effet. Aucun autre paquet à installer. *Ajustement proposé par rapport à D-071*, qui prévoyait `effectsize` : ce paquet n'est pas installé chez l'auteur, et un script sans dépendance se refait partout.

## 2. Tableau 1 — décrire l'échantillon

| | |
|---|---|
| **Rôles** | des variables à décrire (au moins une) ; facultatif : une variable de groupe (nominale ou ordinale, au plus 6 modalités) |
| **Conditions (refus)** | ni identifiant, ni texte libre, ni date de naissance |
| **Calcul** | variable continue (`scale`, score) : n, moyenne, écart-type, minimum, maximum ; variable nominale ou ordinale : effectif et pourcentage de chaque modalité, et des manquants |
| **Avertissements** | une modalité de moins de 5 personnes |
| **Équivalent R** | `mean`, `sd`, `range`, `table`, `prop.table` |

**Exemple** (étude du sommeil, 200 participants) :

| Variable | n | M (ÉT) ou effectif (%) | Étendue |
|---|---|---|---|
| Âge | 197 | 44,79 (16,67) | 18 – 75 |
| Heures de sommeil | 200 | 6,99 (1,09) | 3,5 – 9,7 |
| Score de qualité du sommeil (`sommeil_total`) | 192 | 23,58 (7,52) | 8 – 40 |
| Genre : Femme | | 114 (57,0 %) | |
| Genre : Homme | | 80 (40,0 %) | |
| Genre : Autre identité | | 2 (1,0 %) ⚠ moins de 5 | |
| Genre : manquant (code 9) | | 4 (2,0 %) | |

## 3. Test t — comparer deux groupes

| | |
|---|---|
| **Rôles** | une variable dépendante continue (`scale` ou score) ; une variable de groupe nominale ou ordinale, dont on garde **deux modalités** (les deux seules, ou deux choisies) |
| **Conditions (refus)** | la variable dépendante est continue et n'est ni un identifiant ni un texte ; au moins 2 personnes par groupe ; pas une base en format long où une même personne serait dans les deux groupes |
| **Options** | **Welch** (par défaut : ne suppose pas des variances égales) ou Student ; bilatéral (par défaut) ou unilatéral ; **Mann-Whitney** (non paramétrique) |
| **Calcul** | `scipy.stats.ttest_ind` ; Levene (`scipy.stats.levene`, centré sur la médiane) ; Shapiro-Wilk par groupe ; `scipy.stats.mannwhitneyu` |
| **Taille d'effet** | **d de Cohen** = (M₁ − M₂) / ÉT combiné, ÉT combiné = √[((n₁−1)s₁² + (n₂−1)s₂²) / (n₁+n₂−2)] ; IC 95 % par la loi t non centrale. Mann-Whitney : **corrélation bisériale de rang** r = 2U₁ / (n₁n₂) − 1, U₁ étant la statistique du premier groupe (positive quand il est plus haut) |
| **Avertissements** | un groupe de moins de 5 personnes ; Shapiro-Wilk p < ,05 avec un petit groupe (moins de 30) ; Levene p < ,05 avec l'option Student |
| **Équivalent R** | `t.test(…, var.equal = FALSE)`, `wilcox.test` ; d et son intervalle par la loi t non centrale (`pt`, `uniroot`) |

**Exemple** — score de qualité du sommeil, femmes et hommes (Welch) :

| | Femmes | Hommes |
|---|---|---|
| n | 109 | 77 |
| M (ÉT) | 23,69 (7,86) | 23,50 (7,18) |

t(172,26) = 0,18, p = ,861 ; différence des moyennes 0,20, IC 95 % [−2,00 ; 2,39] ; d = 0,03, IC 95 % [−0,27 ; 0,32]. Levene : p = ,377 ; Shapiro-Wilk : p = ,089 et ,182. 14 participants écartés (score ou genre manquant, ou autre identité).

> Score de qualité du sommeil : M = 23,69 (ÉT = 7,86) pour Femme et M = 23,50 (ÉT = 7,18) pour Homme, t(172,26) = 0,18, p = ,861, d = 0,03, IC 95 % [−0,27 ; 0,32].

## 4. ANOVA à un facteur — comparer plusieurs groupes

| | |
|---|---|
| **Rôles** | une variable dépendante continue ; une variable de groupe nominale ou ordinale, de 3 à 10 modalités |
| **Conditions (refus)** | comme le test t ; au moins 2 personnes dans chaque groupe gardé |
| **Options** | ANOVA classique ; **Kruskal-Wallis** (non paramétrique) ; comparaisons deux à deux (Tukey) |
| **Calcul** | `statsmodels` (`ols` puis `anova_lm`) ; Levene ; `scipy.stats.kruskal` ; Tukey (`statsmodels.stats.multicomp`) |
| **Tailles d'effet** | **η²** = SC inter / SC totale ; **ω²** = (SC inter − ddl inter × CM résiduel) / (SC totale + CM résiduel). Kruskal-Wallis : **ε²** = H / (n − 1). Sans intervalle de confiance dans la v0.9 |
| **Avertissements** | un groupe de moins de 5 personnes ; Levene p < ,05 |
| **Équivalent R** | `aov`, `TukeyHSD`, `kruskal.test` ; η², ω² et ε² par les mêmes formules |

**Exemple** — score de qualité du sommeil selon le genre (3 groupes) :

F(2, 185) = 1,05, p = ,351 ; η² = 0,01, ω² = 0,00. Moyennes : femmes 23,69 (n = 109), hommes 23,50 (n = 77), autre identité 15,86 (n = 2 ⚠). Levene : p = ,277 ; Kruskal-Wallis : H(2) = 2,42, p = ,298.

> ⚠ Le groupe « Autre identité » compte 2 personnes : sa moyenne est très incertaine, et l'analyse repose presque entièrement sur les deux autres groupes.

> Score de qualité du sommeil selon le genre : F(2, 185) = 1,05, p = ,351, η² = ,01, ω² = ,00 ; moyennes : Femme 23,69 (n = 109) ; Homme 23,50 (n = 77) ; Autre identité 15,86 (n = 2).

## 5. Khi-carré — associer deux variables catégorielles

| | |
|---|---|
| **Rôles** | deux variables nominales ou ordinales, de 2 à 10 modalités chacune |
| **Conditions (refus)** | ni identifiant ni texte libre ; au moins deux modalités observées pour chacune |
| **Options** | khi-carré de Pearson (sans correction de continuité) ; **test exact de Fisher** pour un tableau 2 × 2 |
| **Calcul** | `scipy.stats.chi2_contingency` ; `scipy.stats.fisher_exact` |
| **Taille d'effet** | **V de Cramér** = √[χ² / (n × (min(lignes, colonnes) − 1))], sans correction ; pour un 2 × 2, aussi φ |
| **Avertissements** | plus de 20 % des effectifs attendus sous 5, ou un attendu sous 1 (proposer Fisher pour un 2 × 2) ; une case observée de moins de 5 |
| **Équivalent R** | `chisq.test(…, correct = FALSE)`, `fisher.test` |

**Exemple** — secteur et formation en santé et sécurité au travail (enquête SurveyMonkey fictive, vague 2) :

| Secteur | Formation : oui | Non |
|---|---|---|
| Santé et services sociaux | 21 | 5 |
| Éducation | 23 | 10 |
| Commerce | 14 | 8 |
| Industrie | 8 | 9 |
| Administration | 10 | 2 ⚠ |

χ²(4) = 6,98, p = ,137 ; V = 0,25. 1 effectif attendu sur 10 sous 5 (minimum 3,7) : sous le seuil de 20 %.

> Association entre le secteur et la formation en santé et sécurité au travail : χ²(4) = 6,98, p = ,137, V = ,25 (n = 110).

## 6. Corrélation — relier deux variables continues

| | |
|---|---|
| **Rôles** | deux variables continues ou ordinales (ou plusieurs : matrice) |
| **Conditions (refus)** | ni nominale, ni identifiant, ni texte ; au moins 3 paires complètes |
| **Options** | **Pearson** (par défaut) ou **Spearman** (rangs, pour une variable ordinale ou une relation monotone) |
| **Calcul** | `scipy.stats.pearsonr` (IC par la transformation de Fisher), `scipy.stats.spearmanr` |
| **Taille d'effet** | r (ou ρ) lui-même |
| **Avertissements** | une variable ordinale avec Pearson (proposer Spearman) ; moins de 30 paires |
| **Équivalent R** | `cor.test(…, method = "pearson")` ou `"spearman"` |

**Exemple** — score de qualité du sommeil et âge (189 paires) :

r = 0,04, IC 95 % [−0,10 ; 0,18], p = ,585 ; Spearman : ρ = 0,03, p = ,732.

> La corrélation entre le score de qualité du sommeil et l'âge était r(187) = ,04, IC 95 % [−,10 ; ,18], p = ,585.

## 7. Régression linéaire — prédire une variable continue

| | |
|---|---|
| **Rôles** | une variable dépendante continue ; un ou plusieurs prédicteurs continus ou catégoriels (codés en indicatrices, la première modalité en référence) |
| **Conditions (refus)** | la variable dépendante est continue ; au moins 10 observations par prédicteur ; aucun prédicteur qui se déduit exactement des autres |
| **Calcul** | `statsmodels` (`ols`) : coefficients, erreurs types, t, p, IC 95 % ; coefficients standardisés (β) ; R², R² ajusté, F ; facteurs d'inflation de la variance (VIF) ; normalité des résidus (Shapiro-Wilk) |
| **Avertissements** | un VIF supérieur à 5 ; résidus nettement non normaux avec moins de 30 observations ; moins de 20 observations par prédicteur |
| **Équivalent R** | `lm`, `summary`, `confint` ; β en standardisant les variables ; VIF par sa formule |

**Exemple** — score de qualité du sommeil selon l'âge et les heures de sommeil (189 observations) :

| Prédicteur | b | ET | IC 95 % | β | t | p |
|---|---|---|---|---|---|---|
| Constante | −10,75 | 2,64 | [−15,95 ; −5,54] | | −4,07 | < ,001 |
| Âge | −0,00 | 0,02 | [−0,05 ; 0,04] | −0,01 | −0,17 | ,863 |
| Heures de sommeil | 4,93 | 0,35 | [4,24 ; 5,63] | 0,72 | 13,94 | < ,001 |

R² = 0,51, R² ajusté = 0,51, F(2, 186) = 97,43, p < ,001. VIF : 1,00 et 1,00 ; résidus : Shapiro-Wilk p = ,396.

> Le modèle expliquait 51,2 % de la variance du score de qualité du sommeil, F(2, 186) = 97,43, p < ,001, R² ajusté = ,51 (n = 189). Les coefficients sont dans le tableau.

## 8. Le rapport téléchargé

Pour chaque analyse lancée, un rapport Markdown (et le tableau en Excel) :

- l'analyse, ses variables et ses options ;
- les observations retenues et écartées ;
- les résultats, la phrase de résultat, les hypothèses vérifiées et les avertissements ;
- l'**empreinte du codebook**, la date, les versions de l'outil, de Python, de SciPy et de statsmodels ;
- le **script R équivalent**, à côté (`<projet>-analyse-<n>.R`).

## 9. Points à valider

1. Les six analyses de départ et leurs options.
2. Les conventions : p sans zéro initial ; une phrase de résultat qui décrit sans juger (pas de « significatif ») ; Welch par défaut.
3. Les tailles d'effet : d (avec IC), r (avec IC), V, η² et ω² (sans IC dans la v0.9), ε², corrélation bisériale de rang.
4. Le script R équivalent **en R de base seulement**, sans `effectsize` (ajustement de D-071).
5. Les seuils des conditions et des avertissements (2 personnes par groupe au minimum ; signalement sous 5 ; 20 % d'attendus sous 5 ; 10 observations par prédicteur ; VIF > 5).
