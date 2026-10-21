# Essai : les filtres et l'ordre aléatoire dans LimeSurvey Cloud 7.6 (v0.21, étape 6)

**Statut : à faire par l'auteur.** Ce document dit quoi vérifier (plan de la v0.21, § 5.7.4) et ce qui est attendu ; il gardera ce que l'essai a montré, sans rien de réel. Les fichiers réexportés restent **hors du dépôt**, sur le poste de l'auteur, comme ceux de la v0.20 (ils portent le courriel de l'administrateur et l'adresse de l'instance).

## Le questionnaire

Entièrement fictif : `tests/projet_filtres.py`, « Familles et quartier (essai des filtres) ». Trois groupes, treize questions numérotées et un texte d'affichage. Le fichier à importer est écrit par l'outil (page « Publier », ou la fonction `design_limesurvey.write`) ; le Word pour le comité dit, en clair, quand chaque question est posée.

| N° | Code | Question | Posée si |
|---|---|---|---|
| 1 | `genre` | Quel est votre genre ? (obligatoire) | toujours |
| 2 | `age` | Quel âge avez-vous ? (nombre) | toujours |
| 3 | `enfants` | Avez-vous des enfants ? (0 Non, 1 Oui, 9 Préfère ne pas répondre) | toujours |
| 4 | `nbenfants` | Combien d'enfants avez-vous ? (nombre) | 3 = Oui |
| 5 | `agesenfants` | Quel âge ont-ils ? | 4 a une réponse (la cascade) |
| 6 | `majeur` | Depuis quand votez-vous ? (date) | 2 ≥ 18 |
| 7 | `emploi` | Situation d'emploi (choix en ordre aléatoire) | toujours |
| 8 | `garde` | Qui garde les enfants pendant le travail ? | 4 ≥ 1 **ou** 7 ∈ {Temps plein, Temps partiel} |
| 9 | `sansenfant` | Souhaitez-vous ajouter quelque chose ? (texte long) | 3 ≠ Oui |
| — | groupe « Votre quartier » | (questions en ordre aléatoire) | 3 ∉ {Préfère ne pas répondre} |
| 10 | `climat` | grille, énoncés en ordre aléatoire ; l'énoncé 3 est un item de contrôle | groupe |
| 11 | `transport` | cases à cocher en ordre aléatoire, avec « Autre » | groupe |
| — | `merci` | texte d'affichage | toujours |
| 12 | `velo` | Kilomètres à vélo (nombre) | 11 : « À vélo » coché |
| 13 | `calme` | Qu'est-ce qui rend votre quartier calme ? | 10, « est calme. » = Tout à fait d'accord |

## À vérifier

1. **L'importation** : acceptée, sans avertissement ; le rapport annonce 3 groupes, 14 questions, 5 sous-questions et 13 réponses. Puis la **logique du questionnaire** : aucune expression en rouge.
2. **Les quatre cas d'une condition**, dans « Prévisualiser le questionnaire » (pas l'aperçu d'un groupe) : question 3 à **Oui** (4 paraît), à **Non**, code « 0 » (4 ne paraît pas), à **Préfère ne pas répondre** (4 ne paraît pas), laissée **sans réponse** (4 ne paraît pas).
3. **La cascade** : 3 à Oui et 4 laissée vide, 5 ne paraît pas ; 3 à Non, 5 ne paraît pas.
4. **Des nombres, pas des textes** : 2 à 9, la question 6 ne paraît pas ; à 18, elle paraît ; à **100**, elle paraît (comparés comme des textes, « 100 » viendrait avant « 18 »).
5. **Un « ou » dont un terme vise une question non posée** : 3 à Non (4 n'est pas posée) et 7 à Temps plein, la question 8 **doit paraître** (c'est ce que `.NAOK` garantit) ; 7 à Sans emploi, elle ne paraît pas.
6. **« ≠ » et le vide** : 3 à Non ou à Préfère ne pas répondre, la question 9 paraît ; 3 à Oui ou sans réponse, elle ne paraît pas.
7. **Le groupe filtré** : 3 à Préfère ne pas répondre, le groupe « Votre quartier » est sauté en entier.
8. **Une option et un énoncé comme cibles** : « À vélo » coché, 12 paraît ; « est calme. » à Tout à fait d'accord, 13 paraît.
9. **L'ordre aléatoire**, d'une prévisualisation du questionnaire à l'autre : les choix de 7, les énoncés de 10, les options de 11 (« Autre » reste à la fin), et l'ordre de 10 et 11 dans leur groupe changent ; « Sans réponse » reste à la fin.
10. **Le réexport** (`.lss` et texte à colonnes) : les expressions reviennent-elles telles qu'écrites, ou LimeSurvey les réécrit-il ? Quelles valeurs portent `answer_order`, `subquestion_order` et `random_group` ? L'outil écrit `random`, `random` et le nom de la section (`S2`), d'après les options de la documentation ; **ce réexport fixe les valeurs**.
11. **Les réponses** : cinq réponses inventées qui passent par les deux branches, exportées en `.sav`, en CSV et en Excel. Une question non posée et une question montrée laissée vide y sont-elles distinguées (NULL et vide) ? La réponse ne change pas le calcul de l'outil (étape 8), mais dit si le rapport de conformité peut aussi comparer ce que LimeSurvey a enregistré.

## Résultats

À remplir après l'essai : ce qui est conforme, ce qui ne l'est pas, les valeurs lues au réexport, et les corrections faites dans l'outil.
