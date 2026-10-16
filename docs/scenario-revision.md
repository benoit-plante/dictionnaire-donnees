# Scénario manuel : l'interface, de l'accueil au codebook

À faire dans un vrai navigateur, sur la base fictive, après chaque changement important de l'interface. La logique est couverte par les tests automatiques ; ce scénario vérifie ce que les tests ne voient pas : l'affichage, la lisibilité, les clics rapides, la vraie fenêtre « Ouvrir » et le vrai modèle.

## Préparation

Copier `etude-sommeil.sav` et `questionnaire-sommeil.pdf` (dossier `exemples\bases-fictives`) dans un dossier de travail vide, par exemple `%TEMP%\ddict-scenario`. Puis, au choix :

- double-cliquer sur l'icône **Dictionnaire de données** (outil installé) ;
- ou, depuis le dépôt : `uv run ddict`.

Pour ne pas mêler les projets d'essai à la liste des projets récents, lancer l'outil avec la variable `DDICT_CONFIG_DIR` pointant vers un dossier temporaire.

Le navigateur s'ouvre sur `http://127.0.0.1:8501`. Aucun bouton « Deploy » en haut à droite. Ollama doit tourner pour les étapes 8 à 11, 19, 23 et 24, avec `qwen2.5:7b-instruct-q4_K_M`.

## Étapes et résultats attendus

| # | Action | Attendu |
|---|---|---|
| 1 | Regarder l'accueil | « Dictionnaire de données » ; sections Nouveau projet, Ouvrir un projet, Projets récents |
| 2 | **Choisir une base…** | La fenêtre « Ouvrir » de Windows s'affiche devant le navigateur ; y choisir `etude-sommeil.sav` : son chemin remplit le champ |
| 3 | **Créer le projet** | Page « Base » : 34 variables, 200 lignes, 4 sensibles, 10 avec signalements ; tableau de bord : « Ajouter le questionnaire de l'étude », « Sigles sans définition : 2 » |
| 4 | Tableau de bord, « Ajouter le questionnaire » ; coller le chemin de `questionnaire-sommeil.pdf` puis cliquer **Lire le questionnaire** **sans pause** | « Questionnaire lu. » ; 14 questions ; « À vérifier : Q7 » ; QFS, EFA et TCC à valider ; tableau de bord à jour |
| 5 | « Sigles à valider : 3 » ; accepter TCC, rejeter EFA ; ajouter ANX (« anxiété ») en tapant les deux champs **sans pause** | Statuts validé, rejeté ; ANX « Équipe » ; « Sigles à valider : 1 » |
| 6 | **Accueil**, puis le projet dans « Projets récents » | Le projet se rouvre sur « Base » |
| 7 | Accueil, recréer le même projet | « Un projet existe déjà » ; « Ouvrir le projet existant » l'ouvre sans rien perdre |
| 8 | Page « IA locale » | Modèle recommandé choisi ; « Voir exactement ce qui serait envoyé » montre le bloc `l-001` |
| 9 | **Faire proposer : rattachement aux questions** | Barre de progression bloc par bloc ; « 6 blocs réussis » ; tableau de bord : « Rattachements proposés à réviser : 32 » |
| 10 | Tableau de bord, rattachements ; sur `id_participant`, choisir « Aucune question » puis **Rattacher** ; sur une autre variable, **Accepter** | « Aucune question du questionnaire » est déjà en tête, avec « … semble être un identifiant » sous la liste (v0.6) ; enregistré ; passage à la variable suivante, avec un message |
| 11 | « IA locale », **Faire proposer : libellés et descriptions**, puis **Arrêter** pendant le premier bloc | Message « arrêté » ; les blocs terminés sont gardés ; une relance dit « … déjà faits » |
| 12 | Variables : accepter un libellé ; corriger une description et cliquer **Enregistrer** sans appuyer sur Entrée | Texte enregistré, valeur d'origine gardée |
| 13 | Champs documentés : seuil sans source, puis avec | Refus en français, puis seuil enregistré avec sa source |
| 14 | Groupes, G2 : cocher « Ne pas reproduire le texte… », **Enregistrer ce choix** | Enregistré ; la case reste cochée |
| 15 | Export : version finale, **Écrire le codebook et le rapport** | « Fichiers écrits à côté du projet » ; codebook avec les colonnes Question et Texte de la question, « texte omis » pour les `anx*` dont le rattachement est accepté, onglet Glossaire (TCC, ANX), rien de la page de consentement (`ZQXQUEST`, « Laboratoire fictif ») |
| 16 | Export : **Télécharger** le codebook | Le navigateur l'enregistre dans le dossier de téléchargements |
| 17 | Fermer l'onglet, rouvrir par l'icône (ou `uv run ddict`) | L'outil rouvre l'onglet ; toutes les décisions sont là |
| 18 | Tableau de bord, « Codes suspects à confirmer : 3 » ; sur `age`, **C'est un code manquant** | La page passe à la variable suspecte suivante, avec un message ; « Codes suspects à confirmer : 2 » |
| 19 | Variables (rattachements proposés à l'étape 9) : **Accepter les rattachements où le modèle et le calcul s'accordent (N)…** ; décocher une ligne ; **Accepter ces N rattachements** | La liste montre chaque variable avec sa question, toutes cochées ; le compte du bouton baisse d'un à la décoche ; « N rattachements acceptés. » ; la ligne décochée attend toujours |
| 20 | Avec un projet fait à partir de `etude-sommeil.csv` (sans étiquettes) et de `questionnaire-sommeil.txt` (dans le PDF, la grille Q7 est « à vérifier » : pas d'étiquettes proposées), rattachements acceptés : Groupes, G1, **Accepter les étiquettes de valeurs de ce groupe (N)…**, puis accepter | « Étiquettes de N variables acceptées. » |
| 21 | Export : **Écrire les fichiers de commandes à côté du projet** | Deux fichiers `-metadonnees.sps` et `.R`, pas de `.do` ; `MISSING VALUES age (999).` dans le `.sps` |
| 22 | Export : **Écrire la copie documentée** ; puis cocher « la remplacer » et recommencer | « … identiques case par case » ; le bouton se grise tant que la case n'est pas cochée ; `etude-sommeil.sav` inchangé |
| 23 | IA locale : **Mesurer ce modèle** | Barre de progression ; « Rapport écrit à côté du projet » ; le rapport s'affiche (quatre bases, rattachements justes et pourquoi les autres sont manqués, signalements, durées) ; environ trois minutes |
| 24 | Projet fait à partir de `sleep-study.sav` et `questionnaire-sleep.pdf`, rattachement par le modèle ; Variables, filtre « Avec signalements » : `age`, puis une variable signalée « s'écarte du choix sûr du calcul » | `age` : « How old are you? » proposée, et sous la liste « les questions voisines… » ; la variable en désaccord porte le signal en rouge ; le bouton des décisions groupées ne la compte pas |
| 25 | Projet `etude-sommeil` (codes 999 de `age` confirmés à l'étape 18) ; Groupes, G1, section « Cotation » : somme des 8 items, au moins 7 répondus, somme proportionnelle, nom `sommeil_total`, une source ; **Enregistrer la cotation** | Cotation enregistrée ; étendue du score calculée |
| 26 | Page « Analyses » | La base est retrouvée à côté du projet ; encadré « Demander une proposition à l'IA locale (facultatif) » fermé ; bouton **Lancer l'analyse** grisé, sans message rouge |
| 27 | **Test t** ; variable dépendante `sommeil_total`, variable de groupe `genre` | Message rouge « 3 modalités ; choisissez-en deux » ; liste **Modalités comparées** |
| 28 | Modalités comparées : Femme et Homme ; **Lancer l'analyse** | Phrase « … t(172,26) = 0,18, p = ,861, d = 0,03, IC 95 % [−0,27 ; 0,32]. » ; 14 personnes écartées ; tableau des deux groupes |
| 29 | **Écrire à côté du projet** ; dans R, dans le dossier du projet, `source("etude-sommeil-analyse-1.R", encoding = "UTF-8")` | `-analyse-1.md`, `.xlsx`, `.R`, `-metadonnees.R`, `-preparation.R` écrits ; R affiche le même t |
| 30 | Encadré de l'IA ; objectif « Les hommes et les femmes dorment-ils aussi bien ? » ; **Demander une proposition** ; **Reprendre cette proposition** | Une à trois propositions avec leur raison, en quelques secondes ; la proposition remplit les choix de la page ; rien n'est calculé avant **Lancer l'analyse** ; l'échange est dans `etude-sommeil.dd-envois` |
| 31 | Après l'étape 28 : section « Tableaux et figures APA » | Aperçu du **Tableau 1** (en-têtes « Femme » et « Homme » au-dessus de *M* et *ÉT*, *t*(172,26), note en italique) et de la **Figure 1** (deux barres et leurs intervalles) ; boutons « Word (tableaux et figures APA) » et « Excel (graphiques modifiables) » |
| 32 | Encadré du Tableau 1 : numéro 2, titre « Qualité du sommeil selon le genre » | L'aperçu affiche « Tableau 2 » et le nouveau titre ; les chiffres ne changent pas |
| 33 | **Écrire à côté du projet** ; ouvrir le `.docx` dans Word et le classeur `-graphiques.xlsx` dans Excel | Le Word montre le tableau 2 avec son titre, la figure et leurs notes ; dans Excel, le graphique se modifie (couleur d'une barre) et se colle dans Word |
| 34 | Page « Analyses » : **Corrélation**, variables `heures_sommeil` et `nb_reveils` ; **Lancer l'analyse** ; section « Carnet d'analyses », **Ajouter au carnet** | Phrase « … r(198) = ,05, IC 95 % [−,09 ; ,19], p = ,492. » ; « Ajoutée au carnet : A1 » ; le bouton devient « Déjà dans le carnet (A1) », grisé ; `etude-sommeil-carnet.json` à côté du projet |
| 35 | Tableau de bord, « Codes suspects à confirmer » ; variable `nb_reveils` (liste **Variable**) ; **C'est un code manquant** pour −9 | « Codes suspects à confirmer : 1 » |
| 36 | Page « Carnet » | A1 « changée, à confirmer » ; « Ce qui a changé » : n_used 200 → 196, n_excluded 0 → 4, r ,05 → ,01, p ,492 → ,847… (chaque valeur une seule fois) ; « Nouveau calcul : … r(194) = ,01 … » ; « À confirmer avant de produire les résultats : A1 » ; **Produire les résultats** grisé |
| 37 | **Confirmer le nouveau calcul** | A1 « à jour », phrase r(194) = ,01 ; **Produire les résultats** actif |
| 38 | **Produire les résultats** ; ouvrir le `.docx` dans Word ; décompresser `-resultats-R.zip` dans le dossier de la base et, dans R, `source("etude-sommeil-resultats.R", encoding = "UTF-8")` | « Fichiers écrits à côté du projet » : `-resultats.docx`, `-resultats-graphiques.xlsx`, `-resultats-R.zip` ; le Word montre l'intertitre « A1 — Corrélation : relier des variables continues », la phrase, le Tableau 1, la Figure 1 et, à la fin, l'empreinte, la version 0.11.0 et la liste des analyses ; dans R, `resultats$A1` donne n = 196 et r = ,0139 |

À la fin, fermer la fenêtre de l'outil et supprimer le dossier de travail.
