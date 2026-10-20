# Essai : le fichier écrit par l'outil, importé dans LimeSurvey Cloud 7.6 (v0.20, étapes E2 à E4)

Le 2026-10-20, sur l'instance LimeSurvey Cloud de l'auteur (version 7.6.0), avec son accord : le fichier que l'outil écrit pour un questionnaire **entièrement fictif** (celui des tests, `tests/projet_concu.py`, plus une question de chaque type du tronc commun : liste déroulante, date, texte court, choix unique avec un « autre » renommé, texte long sur deux lignes avec `&` et `<` dans sa consigne) a été importé, relu dans l'aperçu, réexporté, modifié dans LimeSurvey puis réexporté encore ; le questionnaire a été activé et rempli de trois réponses inventées, exportées en SPSS (`.sav`). Deux petits fichiers « sondes » ont mesuré les limites des codes. Les fichiers restent hors du dépôt, sur le poste de l'auteur. Ce document ne garde que ce qui a été observé.

## L'importation

- Menus de la version 7.6 : liste des questionnaires, menu **+**, **Importer** ; la fenêtre « Importer un questionnaire » (fichier `.lss`, `.txt` ou `.lsa`, groupe « Importer sur le groupe de questionnaires par défaut », case « Convertir les liens de ressource et les champs d'expression ? » cochée), bouton **Importer un questionnaire** (et non « Importer » : l'étape de l'outil est corrigée).
- **Rapport** : 2 groupes, 10 questions, 5 sous-questions, 11 réponses, aucun avertissement : exactement ce que la page « Publier » annonçait.
- **Aperçu** : chaque question comme conçue (obligatoire, nombre, liste déroulante « Veuillez choisir... », date au format `jj.mm.aaaa`, consigne de section, texte d'affichage, grille et sa consigne, cases à cocher et « Autre : », le texte « Ailleurs, précisez » de l'option « autre » d'un choix unique, le saut de ligne, `&` et `<` affichés tels quels).
- **Ce que LimeSurvey ajoute de lui-même** : une colonne « Sans réponse » aux grilles et un choix « Sans réponse » aux listes qui ne sont pas obligatoires ; la phrase « Cochez tout ce qui s'applique » sous une question à cocher ; « Veuillez sélectionner une réponse ci-dessous » sous un choix unique. L'étape « aperçu » de l'outil le dit maintenant.

## Les limites des codes (sondes)

| Essai | Résultat |
|---|---|
| Code de question de 20 caractères | Importé |
| Code de question de 21 caractères | **L'importation s'arrête** sur « 500 : Erreur interne au serveur - Erreur dans la base de données ! » ; un questionnaire partiel reste, avec les seules questions d'avant |
| Code de choix de 5 caractères (`ABCDE`) | Importé |
| Code de choix de 6 caractères (`ABCDEF`) | **Le choix disparaît sans un mot** : le rapport compte 2 réponses, l'export et l'aperçu n'en ont qu'une |
| Options à cocher codées par des chiffres (`1`, `2`) | Gardées telles quelles ; les colonnes du `.sav` sont `Q5_1`, `Q5_2` |

Les limites que l'outil vérifie avant d'écrire (20 pour une question, 5 pour un choix) sont donc les bonnes, et nécessaires : au-delà, LimeSurvey échoue ou perd un choix sans prévenir.

## Le réexport et la comparaison (E3)

- Le réexport en texte à colonnes du questionnaire importé, relu par l'outil et comparé au projet : **aucune différence**.
- Le texte d'une question modifié dans l'éditeur de LimeSurvey 7 : LimeSurvey l'écrit en HTML, `<p>Quel est votre &acirc;ge ?</p>` ; l'outil le lit « Quel est votre âge ? », trouve la différence (« Question changée », mot à mot), et une fois reprise dans le projet, plus aucune.
- La structure se lit sans téléchargement depuis une page de l'administration (export « texte à colonnes ») ; le courriel de l'administrateur y figure, et n'a pas été gardé.

## L'arrivée de la base (E4)

- Activation : un clic sur « Activer », sans confirmation ; trois réponses inventées ; export « SPSS (.sav) » depuis « Exporter les résultats » (l'export « SPSS » du menu donne une syntaxe et un fichier de données, pas un `.sav`).
- `ddict profiler reponses.sav --projet …` : 23 variables, les 15 prévues toutes trouvées par leur nom (`genre`, `Q4_SQ001`, `Q5_1`, `Q5_other`, `Q9_other`…), LimeSurvey reconnu, ses 8 variables propres (`id`, `submitdate`…) hors du rapport.
- **Deux faux écarts, corrigés** : l'option « autre » d'un choix unique est étiquetée « Other », en anglais, dans le `.sav` (déjà vu le 2026-10-19) ; et sa colonne, de codes `1` et `-oth-`, est du texte « mixte ». Ni l'un ni l'autre n'est une différence avec le questionnaire : le rapport ne les dit plus. Une date que personne n'a remplie (colonne vide) n'est pas un type différent.
