# Essai : trois vagues réelles, chacune reprenant les noms de la précédente (v0.7)

**Date :** 2026-10-15

**But :** vérifier l'étape 7 (D-052) sur de vraies vagues d'une même étude, décrites ici par leurs seuls faits de structure.

**Bases :** trois exports SPSS SurveyMonkey bruts d'une même étude, un par temps de mesure (140, 114 et 88 variables), chacun avec son questionnaire PDF. Chaque vague est renommée par les règles, ses noms acceptés, puis sert de vague précédente à la suivante (`scripts/compter_structure.py`, test `reel`).

**Constat de départ :** les questionnaires changent beaucoup d'un temps à l'autre. Seules 21 variables de la vague 2 ont une étiquette qui concorde avec une variable de la vague 1 ; entre les autres, la meilleure ressemblance de mots reste sous 0,7.

## Résultats

| | Vagues 1 → 2 | Vagues 2 → 3 |
|---|---|---|
| Variables appariées | 31 | 31 |
| Ajoutées / retirées | 83 / 109 | 57 / 83 |
| À départager par une personne | 0 | 0 |
| Variables dont les mots concordent avec la vague précédente | 21 | 26 |
| … laissées sans appariement | 0 | 0 |
| … dont la variable précédente est déjà prise par une autre | 0 | 5 |
| Appariements d'un énoncé avec une question entière, ou d'un « autre » avec un choix | 0 | 0 |
| Étiquettes de valeurs changées | 0 | 0 |

Les 5 variables « déjà prises » sont des énoncés vides de la vague 3 qui répètent mot pour mot des énoncés déjà appariés : une variable précédente ne va qu'à une seule variable, la répétition reste « ajoutée », ce qui est juste.

## Correction faite pendant l'essai

Une étiquette seulement **semblable** (ratio de mots d'au moins 0,7) devient une nouvelle raison, `similar_label` : seule, elle ne propose qu'une candidate à départager, jamais un appariement. Une raison forte (même nom de plateforme, même étiquette, mêmes étiquettes de valeurs, même place parmi des voisines appariées) reste nécessaire pour reprendre un nom, et la place parmi les voisines ne compte que des voisines appariées par une raison forte (sinon deux appariements faibles se seraient renforcés l'un l'autre). Test fictif : `test_a_reworded_question_is_a_candidate_never_a_match`.
