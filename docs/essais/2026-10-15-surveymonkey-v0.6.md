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

Deux exports SurveyMonkey réels, gardés hors du dépôt (D-046), mesurés le 2026-10-15 par `scripts/compter_structure.py` et `tests/test_reel.py`. Chacun a son `.sav`, son `.xlsx` et son questionnaire PDF ; aucun `.txt`. Seuls des décomptes sont donnés.

| | Base 1 | Base 2 |
|---|---|---|
| Variables, lignes | 114, 69 | 50, 22 |
| Variables de plateforme | 10 (noms anciens) | 10 |
| Questions de plateforme (d'après les noms) | 11 : 7 grilles, 4 simples | 13 : 4 ensembles à cocher, 9 simples |
| Groupes trouvés par la v0.6 | 8 : 6 grilles entières, 1 grille coupée en deux | 1, qui mêle des questions simples (préfixe `q`) |
| Ensembles à cocher regroupés | — | 0 sur 4 |
| Items de grille classés « identifiant probable » | 1 | — |
| Items de grille au niveau `scale`, signalés | 100, 0 | — |
| Dates de passation lues comme dates | 0 sur 2 (classées texte libre) | 0 sur 2 (classées texte libre) |
| Valeurs de date lisibles, et leur format | 100 %, `MM/JJ/AAAA hh:mm:ss AM` | 100 %, même format |
| Codes à étiquette « Ne sais pas »… signalés | 0 sur 14 | 0 sur 2 |
| `.xlsx` : lignes en trop, colonnes sans nom, noms absents du `.sav` | 1, 93, 113 | 1, 23, 36 |
| Questionnaire PDF : questions trouvées | 15 (7 ouvertes, 4 à choix unique, 4 grilles de 35 énoncés en tout, 3 à vérifier) | 0 |
| Questionnaire PDF : lignes lues, lignes numérotées | 479, 0 | 70, 13 |

Après les étapes 2 et 3 de la v0.7 :

| | Base fictive | Base 1 | Base 2 |
|---|---|---|---|
| Plateforme reconnue ; `.xlsx` lu comme le `.sav` | oui ; oui | oui ; oui | oui ; oui |
| Groupes qui mêlent des questions | 0 | 0 | 0 (1 avant) |
| Grilles entières, coupées | 2, 0 | 7, 0 (6, 1 avant) | — |
| Items de grille « identifiant probable » | 0 | 0 (1 avant) | — |
| Dates de passation lues comme dates, classées texte libre | 2, 0 | 2, 0 | 2, 0 |
| Codes « Ne sais pas »… observés, signalés | 10, 10 | 6, 6 | 0, 0 |
| Items `scale` de grille signalés | 12 sur 12 | 100 sur 100 | — |

Après l'étape 4 (structure de plateforme) :

| | Base fictive | Base 1 | Base 2 |
|---|---|---|---|
| Ensembles à cocher en groupes « réponses multiples » | 3 sur 3 | — | 4 sur 4 |
| En-tête `.xlsx` comme questionnaire : variables de questions rattachées par la structure, textes concordants | 52 sur 52, tous | 104 sur 104, tous | 40 sur 40, tous |
| Questionnaire PDF : rattachements par la structure, textes concordants | 21, tous | 36, tous | 0 (PDF non lu) |

Deux faits appris sur la base 2 pendant l'étape 4 : une question à choix unique peut avoir sa variable « autre », et SPSS coupe les étiquettes de valeurs à 120 octets, si bien qu'une option longue ne concorde avec le questionnaire que par son début.

Après l'étape 5 (lecture des questionnaires) :

| | Base fictive (PDF, PDF numéroté, `.txt` numéroté) | Base 1 (PDF) | Base 2 (PDF numéroté) |
|---|---|---|---|
| Questions trouvées | 11, 11, 11 (11 attendues) | 8 (15 avant) : 7 grilles de 102 énoncés, 1 choix unique | 13 (0 avant) |
| Grilles et ensembles à cocher retrouvés | tous | 7 grilles sur 7 | 4 ensembles sur 4, dont 1 reconnu d'après la base |
| Questions de la base sans question concordante | 0 | 3 (absentes du PDF, qui commence par une page de titre) | 0 |
| Rattachements par la structure, textes concordants | tous | 100 sur 104, tous | 40 sur 40, tous |
| Points à vérifier signalés par la structure | 0 | 3 grilles au nombre d'énoncés différent (20 pour 19, 30 pour 28, 10 pour 11) | 0 |

Ce que les vrais PDF ont appris, mesuré par la seule forme des lignes (page, retrait, nombre de cellules, longueur, ponctuation finale, sans aucun mot) :

- une grille de SurveyMonkey continue sur la page suivante sans ses titres de colonnes, et un énoncé peut y être coupé par la page ;
- les titres de colonnes longs s'empilent sur trois lignes, la première ne portant qu'un mot loin à droite : c'était la « fausse question faite d'un morceau d'en-tête » ;
- les 7 « questions ouvertes » étaient les énoncés d'une grille, qui finissent par « ? » ;
- la base 2 a un PDF à questions numérotées, des options de plus de 100 caractères, et une question à cocher dont la formulation ne le dit pas ;
- dans le `.sav`, l'option « Autre » d'une question à cocher est aussi une case à cocher (sa dernière), en plus de sa variable de texte ; l'export Excel n'a que le texte. La base fictive le reproduit depuis l'étape 5.

Les écarts restants de la base 1 (un ou deux énoncés de trop, un de moins) sont signalés à la personne par la structure, et ne produisent aucun rattachement faux : un rattachement exige que les textes concordent.

Ce que la mesure précise par rapport à l'essai de l'auteur :

- Les « 8 grilles » de la base 1 sont 7 grilles d'après les noms. La v0.6 en fait 8 groupes parce qu'une grille est coupée en deux.
- Le format des dates de passation est le même dans les deux bases, et c'est celui de la base fictive : toutes les valeurs sont lisibles.
- Le questionnaire PDF de la base 2 a des **questions numérotées** (13 lignes numérotées, autant que de questions de plateforme), et la v0.6 n'y trouve aucune question, comme dans le `.txt` numéroté de l'essai. L'étape 5 doit donc accepter les questions numérotées dans un PDF aussi, et la base fictive recevra un PDF numéroté.
- Les codes « Ne sais pas »… comptés plus haut comprenaient des étiquettes jamais choisies et, dans la base 2, des faux positifs du script de décompte (« na » au milieu d'un mot, « refus » dans une longue phrase d'option). Le décompte ne retient plus que les étiquettes courtes de codes observés : 6 dans la base 1, 0 dans la base 2.
- La base 1 n'a pas de faux groupe par le préfixe et la base 2 n'a pas de grille : ces constats ne valent que pour l'autre base. Pour les vraies bases, les tests de constats ne sont donc pas « stricts » : un test sans objet est sauté, un constat absent d'une base n'est pas une erreur.
