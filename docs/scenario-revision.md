# Scénario manuel : l'interface, de l'accueil au codebook

À faire dans un vrai navigateur, sur la base fictive, après chaque changement important de l'interface. La logique est couverte par les tests automatiques ; ce scénario vérifie ce que les tests ne voient pas : l'affichage, la lisibilité, les clics rapides, la vraie fenêtre « Ouvrir » et le vrai modèle.

## Préparation

Copier `etude-sommeil.sav` et `questionnaire-sommeil.pdf` (dossier `exemples\bases-fictives`) dans un dossier de travail vide, par exemple `%TEMP%\ddict-scenario`. Puis, au choix :

- double-cliquer sur l'icône **Dictionnaire de données** (outil installé) ;
- ou, depuis le dépôt : `uv run ddict`.

Pour ne pas mêler les projets d'essai à la liste des projets récents, lancer l'outil avec la variable `DDICT_CONFIG_DIR` pointant vers un dossier temporaire.

Le navigateur s'ouvre sur `http://127.0.0.1:8501`. Aucun bouton « Deploy » en haut à droite. Ollama doit tourner pour les étapes 8 à 11, avec `qwen2.5:7b-instruct-q4_K_M`.

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
| 10 | Tableau de bord, rattachements ; sur `id_participant`, choisir « Aucune question » puis **Rattacher** ; sur une autre variable, **Accepter** | Enregistré ; passage à la variable suivante, avec un message |
| 11 | « IA locale », **Faire proposer : libellés et descriptions**, puis **Arrêter** pendant le premier bloc | Message « arrêté » ; les blocs terminés sont gardés ; une relance dit « … déjà faits » |
| 12 | Variables : accepter un libellé ; corriger une description et cliquer **Enregistrer** sans appuyer sur Entrée | Texte enregistré, valeur d'origine gardée |
| 13 | Champs documentés : seuil sans source, puis avec | Refus en français, puis seuil enregistré avec sa source |
| 14 | Groupes, G2 : cocher « Ne pas reproduire le texte… », **Enregistrer ce choix** | Enregistré ; la case reste cochée |
| 15 | Export : version finale, **Écrire le codebook et le rapport** | « Fichiers écrits à côté du projet » ; codebook avec les colonnes Question et Texte de la question, « texte omis » pour les `anx*` dont le rattachement est accepté, onglet Glossaire (TCC, ANX), rien de la page de consentement (`ZQXQUEST`, « Laboratoire fictif ») |
| 16 | Export : **Télécharger** le codebook | Le navigateur l'enregistre dans le dossier de téléchargements |
| 17 | Fermer l'onglet, rouvrir par l'icône (ou `uv run ddict`) | L'outil rouvre l'onglet ; toutes les décisions sont là |

À la fin, fermer la fenêtre de l'outil et supprimer le dossier de travail.
