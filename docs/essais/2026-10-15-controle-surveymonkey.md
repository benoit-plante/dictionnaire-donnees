# Essai : base de contrôle SurveyMonkey et diagnostic de la base 1 (v0.7)

**Date :** 2026-10-15

## 1. Base de contrôle

**But :** les corrections de la partie A ont été mises au point sur deux exports réels et sur la base fictive écrite d'après eux. Comme en v0.6 (D-042), une base nouvelle, écrite après coup, est mesurée une seule fois avec le code tel quel, avant toute correction.

**Base :** `trajets_surveymonkey.sav` (et `.xlsx`, questionnaire `.txt` numéroté), écrite par `scripts/generer_controle_surveymonkey.py` : une étude fictive en anglais, noms de plateforme récents, 95 lignes, avec des types de questions absents des deux exports réels : coordonnées (quatre champs texte), choix unique avec « autre », grille d'accord, classement, curseur, deux zones de texte numériques, cases à cocher avec « autre », grille avec colonne de commentaire, grille de menus déroulants, question ouverte. **Pour ces types, les noms, étiquettes et cellules d'en-tête de SurveyMonkey sont supposés, pas observés.**

### Mesure unique, avec le code de la fin de l'étape 10

| | Résultat |
|---|---|
| Plateforme reconnue, `.xlsx` lu sans ligne en trop | oui |
| Groupes attendus trouvés | 3 / 3 |
| Faux groupes « échelle » | **2** : les coordonnées (champs texte) et le classement (des rangs) |
| Identifiants probables parmi les coordonnées | nom, courriel, téléphone (la ville ne l'est pas) |
| Rattachements par la structure, en-tête `.xlsx` | 30 / 31 ; le « faux » est l'option « autre » d'un choix unique, numérotée 1 dans l'en-tête, qui n'en connaît pas les choix |
| Rattachements par la structure, `.txt` numéroté | 31 / 31 |
| Noms de l'`.xlsx` absents du `.sav` | 5 : la grille de menus déroulants (noms à trois niveaux dans le `.sav`) et la colonne de commentaire d'une grille (en-tête « Comments ») |
| Radicaux proposés | mots de question anglais gardés (`main_way_getting`, `there_anything_else`) ; coordonnées, classement et zones de texte « à nommer » |

### Corrections faites ensuite

- Une grille ne forme une échelle que si ses énoncés sont des catégories étiquetées : au moins deux étiquettes de valeurs dans un `.sav` ; dans un export Excel ou CSV, quelques textes, partagés d'un énoncé à l'autre (les colonnes d'une grille de menus déroulants n'ont pas les mêmes options).
- Une question à plusieurs champs qui n'est pas une échelle (coordonnées, classement, zones de texte) reçoit un radical, comme une question à cocher ; le texte d'une question n'est pris dans les étiquettes que si ses variables le partagent.
- Les mots de question et de consigne anglais sont écartés des radicaux.

### Après les corrections

3 groupes justes et aucun faux groupe, dans le `.sav` comme dans l'`.xlsx` ; mêmes rattachements ; radicaux `age_group`, `work`, `contact_information`, `commute`, `commuting`. **Laissé tel quel, faute de convention connue :** les noms à trois niveaux (`q0010_0001_0001`) restent hors structure, sans groupe ni rattachement par la structure ; la colonne de commentaire d'une grille, sans forme connue de « autre », reçoit dans l'`.xlsx` un nom d'énoncé. Un vrai export avec ces types de questions dira quoi faire.

## 2. Diagnostic du PDF de la base 1

Par la seule forme des lignes et des décomptes (D-046), pour les écarts restants de l'étape 5 :

| Écart | Cause | Correction |
|---|---|---|
| 2 questions de la base sans question du PDF | deux questions ouvertes de la page 1, l'une finissant par une parenthèse, l'autre d'un seul mot, lues comme des paragraphes ; chacune concorde avec le texte de sa variable | `link.repair_from_platform` : un paragraphe qui concorde, seul, avec une question de la base qui manque au questionnaire devient cette question (texte inchangé, marqué « trouvée par la structure de la base ») |
| Une grille avec une ligne de trop (20 pour 19) | la première ligne des consignes de la grille suivante, en haut de page, prise pour un énoncé | une grille ne continue pas sur une ligne quand des titres de colonnes suivent la ligne d'après (ou la suivante, sur la même page) |
| Une grille avec une ligne de moins (10 pour 11) | son dernier énoncé, en haut de la page suivante, pris pour l'introduction de la question qui suit | la même réparation : un paragraphe qui concorde, seul, avec l'énoncé manquant devient la ligne de la grille |
| Une grille avec deux lignes de trop (30 pour 28) | un intertitre et une phrase avant la grille suivante | la même règle que pour les consignes |

Après : les 7 grilles ont exactement leur nombre d'énoncés, 10 questions de la base sur 11 ont leur question (la 11ᵉ est la variable ajoutée `id`, vide, absente du PDF), et 103 rattachements par la structure sur 104 variables de questions, tous concordants. Les six questionnaires fictifs plus anciens sont lus exactement comme avant.
