# Essai : découpage d'un questionnaire réel (v0.2, étape 2)

**Date :** 2026-10-13
**Questionnaire :** export PDF SurveyMonkey (27 pages) de l'étude dont la base publique a servi à l'essai de la v0.1.2. Le fichier reste hors du dépôt ; ce compte rendu ne donne que des décomptes et des types de mise en page, sans reproduire le questionnaire.
**Commande :** `ddict questionnaire` (lecture pypdf en mode mise en page, découpage sans IA).

## Résultat

| | |
|---|---|
| Questions trouvées | 80 |
| À choix unique | 51 (dont 31 échelles présentées en colonnes) |
| Ouvertes | 15 |
| À cocher (« Cochez toutes les réponses applicables ») | 8 |
| Grilles | 6, avec 72 énoncés au total |
| Grilles marquées « à vérifier » | 4 (énoncés non numérotés) |

Vérification page par page, à la main, contre le PDF :

- toutes les questions des pages 4 à 27 sont trouvées, avec leurs options complètes et dans l'ordre ;
- les questions sans point d'interrogation (« Langue maternelle », titres de rangées d'une échelle de soutien) sont reconnues grâce au décalage de leurs options ;
- les échelles dont les titres de colonnes tiennent sur deux lignes (« Vraiment » au-dessus de « insatisfait·e ») donnent les bonnes options ;
- la grille de 36 items répartie sur trois pages, sans titres de colonnes répétés, est reconstituée en entier grâce à sa numérotation ;
- les grilles introduites par une consigne plutôt que par une question reçoivent la consigne comme texte de question ; leurs énoncés sont retrouvés.

## Erreurs restantes

| Erreur | Nombre | Conséquence |
|---|---|---|
| Ligne de la page de consentement finissant par « : » (introduction d'une liste) prise pour une question ouverte | 2 | Question sans variable ; elle ne sera rattachée à rien et n'est donc pas exportée (D-012) |
| Question de consentement formulée comme une affirmation (« J'accepte que… ») avec Oui / Non, non reconnue | 1 | Reste un paragraphe ; pas de variable correspondante dans la base |

Aucune question portant sur une variable de la base n'est manquée.

## Constat sur le questionnaire lui-même

Trois questions annoncent une échelle « 0 = … / 10 = … » mais n'offrent que les cases 1 à 10. L'outil reproduit ce qui est imprimé, sans le corriger : c'est une incohérence que l'équipe voudra connaître (et que l'étape 6 devra traiter avec prudence).

## Règles ajoutées pendant l'essai

Chacune est couverte par un test sur des lignes reproduisant la mise en page rencontrée :

1. une ligne sans « ? » suivie de ses propres options décalées est une question, même juste après une autre question ;
2. les champs de saisie (« Date », « JJ/MM/AAAA », « Année/Mois ») ne sont ni des questions ni des paragraphes, et une ligne suivie d'un tel champ est une question ;
3. les titres de colonnes sur plusieurs lignes sont assemblés colonne par colonne, à partir de la ligne qui en compte le plus ;
4. les énoncés de grille commençant par « … » sont des lignes de grille ;
5. une consigne suivie de titres de colonnes est la question d'une grille ; ses énoncés non numérotés sont acceptés et marqués « à vérifier » ;
6. une grille numérotée continue sur la page suivante tant que les numéros augmentent ;
7. « (ex. » en fin de ligne et une parenthèse restée ouverte ne terminent pas une phrase ; un « ? » seul sur sa ligne rejoint la ligne précédente.
