# Plan de la v0.3

> Statut : **validé par l'auteur le 2026-10-14**, avec toutes les recommandations du § 6 (D-019 à D-024).

## 1. Pourquoi cette version

La v0.2 a rendu le codebook bien meilleur, mais aussi plus long à produire : une personne tape six ou sept commandes et passe deux fois de PowerShell au navigateur (lire la base, lire le questionnaire, rattacher, réviser, enrichir, réviser, exporter). Pour des équipes qui ne programment pas, **PowerShell est désormais le principal obstacle**, à l'installation comme à l'usage.

La v0.3 le retire de l'usage courant :

- **tout se fait dans l'interface du navigateur**, de l'ouverture de la base au téléchargement du codebook ;
- **l'installation se fait par un double-clic**, et l'outil se lance par une icône.

Les commandes restent, pour qui les préfère, pour les scripts et pour les tests. Les principes ne changent pas : interface accessible depuis l'ordinateur seulement, rien n'est envoyé ailleurs, le modèle ne reçoit jamais de données individuelles, toute proposition attend une personne.

## 2. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Accueil** : créer un projet à partir d'une base, rouvrir un projet récent | Plus de chemins de fichiers à taper |
| B | **Parcours guidé** dans l'interface : base, questionnaire, glossaire, rattachement, révision, enrichissement, export, avec l'état de chaque étape | Plus d'allers-retours entre PowerShell et le navigateur ; l'ordre recommandé est visible |
| C | **IA depuis l'interface** : détection d'Ollama et des modèles installés, aperçu de ce qui serait envoyé, lancement avec barre de progression, arrêt et reprise | L'IA sans ligne de commande, et toujours sans surprise |
| D | **Export depuis l'interface** : codebook Excel et rapport, téléchargés ou écrits à côté du projet | La fin du parcours dans le même onglet |
| E | **Installateur Windows** par double-clic, sans droits d'administrateur, avec icône dans le menu Démarrer et sur le bureau, mise à jour et désinstallation | Plus de PowerShell à l'installation |
| F | **Deux corrections issues des essais de la v0.2** : position des questions candidates pour le rattachement ; étendue observée présentée comme celle d'une échelle | Les deux faiblesses principales relevées dans `docs/essais/` |

**Reportés à la v0.4** : copie corrigée du `.sav` (et aide au nettoyage sur une copie de la base) ; jeu de référence pour comparer les modèles. Les deux restent utiles, mais la v0.3 change déjà l'interface en profondeur : mieux vaut la stabiliser avant d'ajouter des fonctions qui écrivent des données.

## 3. Conception

### 3.1 Lancement

- `ddict` sans argument, ou l'icône installée, démarre l'interface et ouvre le navigateur sur l'**accueil**. `ddict reviser projet.dd.json` reste possible et ouvre directement le projet.
- Toujours sur `127.0.0.1`, télémétrie de Streamlit désactivée, sans bouton « Deploy » (comme en v0.1).
- La fenêtre de console qui fait tourner l'interface reste nécessaire : l'icône l'ouvre réduite, avec un message clair (« Fermez cette fenêtre pour arrêter l'outil »).

### 3.2 Accueil et choix des fichiers

- **Nouveau projet** : choisir la base (`.sav`, `.csv`, `.dta`, `.sas7bdat`, `.xlsx`) ; le fichier projet est créé à côté, comme avec `ddict profiler`.
- **Projets récents** : la liste des derniers projets ouverts, enregistrée sur l'ordinateur (dossier de l'utilisateur, `%APPDATA%\ddict`). Elle ne contient que des chemins, jamais de données ; elle peut être vidée depuis l'accueil.
- **Choix d'un fichier** : la fenêtre « Ouvrir » habituelle de Windows, ouverte par l'outil sur l'ordinateur (bibliothèque `tkinter`, fournie avec Python, déjà vérifiée sur ce poste). Un champ où coller un chemin reste disponible si la fenêtre ne s'ouvre pas. Voir D-020.
- Pas de « glisser-déposer » vers la page : le navigateur enverrait une copie du fichier au serveur local, qui ne saurait plus où écrire le projet, et une grosse base passerait par la mémoire du navigateur.

### 3.3 Parcours guidé

L'interface est réorganisée en pages, dans la barre latérale :

1. **Base** : résumé du profil (variables, sensibles, signalements), comme la sortie de `ddict profiler`.
2. **Questionnaire** : choisir le fichier ; questions trouvées, questions à vérifier, sigles repérés. Remplacer le questionnaire, avec l'avertissement sur les rattachements retirés.
3. **Glossaire** : la vue actuelle.
4. **Rattachement** : candidates calculées ; bouton « Faire proposer par le modèle » ; puis la révision, variable par variable, comme aujourd'hui.
5. **Variables** : la révision actuelle (libellés, descriptions, étiquettes de valeurs, champs documentés, confidentialité).
6. **Groupes** : la vue actuelle.
7. **Enrichissement** : bouton « Faire proposer libellés et descriptions », avec le rappel de l'ordre recommandé (glossaire et rattachements révisés d'abord).
8. **Export** : version finale ou de travail, groupes dont le texte est omis, boutons de téléchargement.

Un **tableau de bord** en tête de la barre latérale dit où en est le projet : « 3 sigles à valider », « 12 rattachements à réviser », « 40 propositions en attente ». Chaque ligne mène à la page concernée. L'ordre est conseillé, jamais imposé.

La logique reste hors de l'interface (modules `project`, `questionnaire`, `llm`, `review.logic`) et testée sans navigateur ; `app.py` (826 lignes aujourd'hui) est découpé en un fichier par page.

### 3.4 IA depuis l'interface

- Une page **Modèle local** vérifie qu'Ollama répond sur cet ordinateur et liste les modèles installés (appel local `/api/tags`, avec le même refus de toute adresse non locale que le client actuel). Si Ollama manque, elle explique comment l'installer ; l'outil ne télécharge ni n'installe rien lui-même (D-023).
- **Aperçu** : avant le premier envoi, un bouton montre exactement les messages qui partiraient, comme `--apercu`.
- **Lancement** : dans la page, avec une barre de progression bloc par bloc et un bouton « Arrêter ». Les blocs terminés sont enregistrés à mesure ; relancer reprend où l'on s'était arrêté (déjà le cas en ligne de commande). Voir D-022.

### 3.5 Installateur Windows

- L'archive contient `installer.bat`. Un double-clic :
  1. installe uv dans le dossier de l'utilisateur, sans droits d'administrateur ;
  2. installe l'outil et ses options ;
  3. crée l'icône « Dictionnaire de données » dans le menu Démarrer et sur le bureau ;
  4. propose, en le demandant, de vérifier Ollama et d'afficher la marche à suivre pour le modèle.
- `desinstaller.bat` retire l'outil et les icônes, sans toucher aux fichiers projet. Une nouvelle archive se met à jour par le même `installer.bat`.
- Une connexion Internet reste nécessaire **pendant l'installation seulement**.
- **Avertissements de Windows** : un fichier téléchargé et non signé déclenche l'écran « Windows a protégé votre ordinateur » (SmartScreen). Le guide montre quoi faire (« Informations complémentaires », puis « Exécuter quand même »). Signer l'installateur demande un certificat payant ; voir D-021.
- **Essai** : sur une session Windows qui n'a jamais eu l'outil ni uv. Windows 11 Famille n'a pas « Windows Sandbox » ; il faudra un second compte d'utilisateur, sans droits d'administrateur, créé par l'auteur, ou un autre ordinateur.

### 3.6 Corrections issues des essais

- **Rattachement** (essai du 2026-10-14) : les questions répétées à l'identique (« À quelle fréquence cette personne vous apporte du soutien ? ») sont confondues. Le message au modèle donnera la position de chaque candidate et la question qui la précède (« après : Votre conjoint·e »), sans autre texte du questionnaire. Mesure : l'essai sur la base publique est refait.
- **Étendue observée** (essai du prompt v3) : une description qui présente l'étendue observée comme celle de l'échelle (« sur une échelle de 0 à 21 ») est signalée, comme un seuil ou un nom d'instrument.

## 4. Étapes

Une étape à la fois, avec ses tests, et un arrêt pour revue à la fin de chacune.

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Interface découpée en pages, sans changement de comportement | Tous les tests passent ; scénario manuel de la v0.2 refait dans le navigateur |
| 2 | Accueil : nouveau projet, projets récents, fenêtre « Ouvrir » de Windows, `ddict` sans argument | Créer et rouvrir un projet sans taper de chemin ; liste des récents vidée sur demande |
| 3 | Pages Base et Questionnaire, tableau de bord | Le parcours de la base fictive jusqu'au glossaire, sans PowerShell |
| 4 | IA depuis l'interface : détection, aperçu, lancement, progression, arrêt et reprise | Rattachement et enrichissement de la base fictive depuis le navigateur ; interruption puis reprise sans bloc refait ; aucune adresse non locale possible (test) |
| 5 | Page Export, téléchargement | Codebook identique à celui de `ddict exporter` (test) |
| 6 | Corrections issues des essais (rattachement, étendue observée) | Essai de rattachement refait et consigné ; signal testé |
| 7 | Installateur, icônes, désinstallation, mise à jour | Installation sur une session Windows vierge, sans droits d'administrateur, jusqu'au premier codebook |
| 8 | Guide réécrit (sans PowerShell hors dépannage), scénario manuel, version 0.3.0 | Guide suivi de bout en bout par l'auteur |

## 5. Risques

- **Streamlit et les tâches longues** : un enrichissement dure plusieurs minutes. Pendant ce temps, l'onglet est occupé ; si la personne change de page, le travail s'arrête, mais les blocs terminés sont gardés. À vérifier dans le navigateur à l'étape 4, et à dire clairement à l'écran.
- **Fenêtre « Ouvrir »** : elle s'ouvre sur l'ordinateur, côté serveur ; si elle apparaît derrière le navigateur, la personne peut croire que rien ne se passe. L'outil la place au premier plan, et le champ de chemin reste en secours.
- **SmartScreen et politiques d'établissement** : certains postes universitaires ou hospitaliers interdisent les scripts ou les programmes non signés. Le guide dira à qui s'adresser ; un installateur signé ou une version « portable » sans installation pourront suivre.
- **Taille du chantier** : l'interface change plus qu'à aucune version précédente. D'où l'étape 1, purement mécanique, et le scénario refait à chaque étape.

## 6. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-019 | **Périmètre de la v0.3** | A à F ; copie corrigée du `.sav` et jeu de référence en v0.4. |
| D-020 | **Choix des fichiers dans l'interface** | Fenêtre « Ouvrir » de Windows par `tkinter`, avec un champ de chemin en secours ; pas d'envoi du fichier par le navigateur. |
| D-021 | **Forme de l'installateur** | Un `installer.bat` (uv dans le dossier de l'utilisateur, sans droits d'administrateur, Internet pendant l'installation). Plutôt qu'un `.exe` empaqueté (PyInstaller ou Inno Setup) : plus lourd à construire et à maintenir, et aussi bloqué par SmartScreen tant qu'il n'est pas signé. Une version hors ligne ou signée pourra suivre si des établissements le demandent. |
| D-022 | **Tâches longues dans l'interface** | Dans l'onglet, avec progression et bouton « Arrêter », en s'appuyant sur la reprise bloc par bloc qui existe déjà ; plutôt qu'un processus en arrière-plan, plus complexe et plus difficile à arrêter proprement. |
| D-023 | **Téléchargement du modèle** | Jamais par l'outil : il détecte Ollama et les modèles, et explique ; le téléchargement reste une action explicite de la personne (ou de l'installateur, qui le demande). |
| D-024 | **Liste des projets récents** | Enregistrée dans `%APPDATA%\ddict`, chemins seulement, effaçable depuis l'accueil. |
