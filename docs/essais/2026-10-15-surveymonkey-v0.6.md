# Essai : la v0.6 sur un export SurveyMonkey (v0.7, étape 1)

**Date :** 2026-10-15
**But :** mesurer ce que fait la v0.6 avec un export brut de SurveyMonkey, avant toute correction de la v0.7, sur la base fictive qui reproduit les constats de l'essai de l'auteur sur deux vrais exports (`docs/plan-v0.7.md`, § 1).
**Outil de mesure :** `scripts/compter_structure.py`, qui ne rend que des décomptes et des taux (D-046) ; la structure attendue est lue dans les noms (`q0003_0004`), indépendamment de l'outil.

## Base fictive, vague 2

`travail-t2_surveymonkey.sav` (52 variables, 110 lignes), avec son export `.xlsx` et ses questionnaires `.pdf` et `.txt`. Structure attendue : 10 variables de plateforme, 12 questions, dont 2 grilles (12 et 5 énoncés), 3 ensembles à cocher et 7 questions simples ou ouvertes ; 11 questions au questionnaire (la variable `id` n'en a pas).

| Constat de l'essai réel | Mesure de la v0.6 sur la base fictive | Attendu |
|---|---|---|
| Plateforme reconnue | non | oui |
| Ligne 2 de l'en-tête `.xlsx` lue comme un participant | 1 ligne en trop, 30 colonnes `colonne_…`, 51 noms absents du `.sav` | 0, 0, 0 (hors `CollectorNm`, absent de l'export Excel) |
| Faux groupe par le préfixe `q` | 1 groupe mêle plusieurs questions | 0 |
| Grille coupée en deux | 1 grille coupée sur 2, 1 entière | 2 entières |
| Ensembles à cocher regroupés | 0 sur 3 | 3 |
| Item d'échelle classé « identifiant probable » (verbe « identifier ») | 1 | 0 |
| Dates de passation | 0 sur 2 lues comme dates, 2 classées texte libre ; 100 % des valeurs lisibles au format `MM/JJ/AAAA hh:mm:ss AM` | 2 dates |
| Codes « Ne sais pas » et « Préfère ne pas répondre » | 0 signalés sur 10 | 10 |
| Niveau `scale` des items étiquetés | 0 signalé sur 12 | 12 |
| Questionnaire PDF | 13 questions (6 ouvertes, 6 à choix unique, 1 à cocher), 0 grille | 11 questions, 2 grilles, 3 à cocher |
| Questionnaire `.txt` numéroté | 5 questions, toutes ouvertes ; 0 à cocher | 11 questions, 2 grilles, 3 à cocher |

Chaque ligne est un test en échec attendu (`tests/test_surveymonkey.py`) ; l'étape qui corrige un constat en fait un test ordinaire.

Écart avec l'essai réel : le `.txt` numéroté fictif donne 5 questions au lieu de 0. Le constat est le même (les questions numérotées ne sont pas reconnues comme telles), mais le chemin d'erreur diffère sans doute ; les tests `reel` le diront.

## Vraies bases

À mesurer avec `tests/test_reel.py` et `scripts/compter_structure.py` quand le dossier `DDICT_DONNEES_REELLES` sera disponible. Seuls des décomptes seront consignés ici.
