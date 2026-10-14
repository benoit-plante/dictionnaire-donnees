# Journal des décisions

Ce journal consigne, dans l'ordre chronologique, les décisions qui structurent le projet dictionnaire-donnees (nom de travail). Une entrée n'est jamais modifiée après coup : si une décision change, on ajoute une nouvelle entrée qui la remplace et on l'indique dans le champ « Remplace ».

## Gabarit d'entrée

```markdown
### D-XXX — Titre court de la décision

- **Date :** AAAA-MM-JJ
- **Statut :** proposée | adoptée | remplacée par D-YYY
- **Remplace :** — (ou D-YYY)
- **Décision :** ce qui est décidé, en une ou deux phrases.
- **Options considérées :**
  1. Option A — résumé
  2. Option B — résumé
- **Justification :** pourquoi cette option plutôt que les autres.
- **Conséquences :** ce que la décision implique ou exclut (facultatif).
- **Références :** documents ou liens utiles (facultatif).
```

---

## Entrées

### D-001 — Démarrage du projet et conception de la v0.1

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** démarrer un outil libre, local et hors ligne de création de dictionnaires de données assistée par IA locale, selon `CONCEPTION.md` (version du 2026-10-13) : sept principes non négociables, architecture en modules, modèle de données, contenu des messages envoyés au modèle, plan de développement de la v0.1 en 14 étapes.
- **Options considérées :** sans objet (décision de démarrage).
- **Justification :** conception validée par l'auteur.
- **Références :** `CONCEPTION.md`.

### D-002 — Licences

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** Apache-2.0 pour le code ; CC BY 4.0 pour la documentation ; CC0 pour les bases fictives et les gabarits.
- **Options considérées :**
  1. Apache-2.0 — permissive, avec clause de brevets.
  2. AGPL-3.0-or-later — cohérence avec outil-qualitatif.
  3. MIT — permissive, plus courte, sans clause de brevets.
- **Justification :** l'outil tourne sur le poste, donc la clause réseau de l'AGPL n'apporterait presque rien ; une licence permissive facilite l'adoption par les universités et les centres de recherche.
- **Conséquences :** toute dépendance doit être compatible avec Apache-2.0 (`dependances.md`).

### D-003 — Nom de travail et dépôt privé jusqu'à la v0.1

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** « dictionnaire-donnees » est un nom de travail ; le paquet Python s'appelle `ddict`, indépendamment du nom final. Le dépôt GitHub reste privé jusqu'à la v0.1 ; le nom final est choisi avant de le rendre public.
- **Options considérées :**
  1. Dépôt public dès le départ.
  2. Dépôt privé jusqu'à la v0.1.
- **Justification :** un historique public ne s'efface pas ; il faut d'abord fixer le nom et vérifier qu'aucune donnée réelle ni aucun chemin personnel n'est entré dans l'historique.

### D-004 — Langues

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** code, commentaires, noms techniques et messages de commit en anglais ; documentation, journal des décisions, interface et messages envoyés au modèle en français, avec des chaînes d'interface traduisibles.
- **Justification :** public francophone ; code lisible par la communauté ; interface bilingue prévue après la v0.1.

### D-005 — Choix techniques de départ

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** Python 3.11+, uv pour l'installation et le développement, pandas, pyreadstat, pydantic, openpyxl, Streamlit (écoute sur 127.0.0.1 et télémétrie désactivée, imposées par l'outil), httpx pour parler à un serveur local compatible OpenAI (pas la bibliothèque `openai`), pytest avec pytest-socket, ruff.
- **Options considérées :** bibliothèque `openai` comme client — écartée : dépendance plus lourde, moins de contrôle sur l'adresse appelée.
- **Justification :** voir `CONCEPTION.md`, § 11.
- **Conséquences :** les dépendances d'exécution sont ajoutées étape par étape et consignées dans `dependances.md`.

### D-006 — Confidentialité des agrégats

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les effectifs inférieurs à 5 (seuil réglable) sont masqués (« < 5 ») dans les messages au modèle, dans le fichier projet et dans les exports ; le client IA refuse toute adresse non locale.
- **Justification :** de petits effectifs peuvent permettre de reconnaître une personne ; un codebook est souvent partagé ou déposé avec les données.

### D-007 — Portée du masquage des petits effectifs

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le masquage de D-006 s'applique aux effectifs des catégories observées (« < 5 »), pas aux décomptes de manquants, qui restent exacts. Une catégorie de texte rare qui n'est pas une étiquette du fichier (une ville, un nom) est retirée entièrement, et seul le nombre de catégories retirées est indiqué. Pour le modèle, les étendues de dates sont réduites à l'année.
- **Options considérées :**
  1. Masquer aussi les décomptes de manquants inférieurs à 5.
  2. Masquer seulement les effectifs des catégories.
- **Justification :** un décompte de manquants ne désigne pas un groupe de personnes ayant une caractéristique ; le masquer rendrait le codebook moins utile sans gain réel. Une catégorie de texte rare, elle, peut nommer une personne ou un lieu : masquer son effectif ne suffit pas.
- **Conséquences :** appliqué par la porte de confidentialité (`ddict.privacy.gate`), seule source de ce qui part vers le modèle, le fichier projet et les exports.

### D-008 — Suppression secondaire des petits effectifs

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** quand un seul effectif de catégorie valide est masqué (D-006), le plus petit des autres effectifs valides est masqué aussi ; dès qu'un effectif valide est masqué ou qu'une catégorie rare est retirée, la moyenne et l'écart-type de la variable ne sont pas transmis. Les effectifs des codes déclarés manquants restent exacts, puisque ce sont des décomptes de manquants (précision de D-007).
- **Options considérées :**
  1. Masquage simple (D-006 seul).
  2. Suppression secondaire et retrait de la moyenne et de l'écart-type.
- **Justification :** avec le masquage simple, l'effectif caché se retrouve par soustraction du nombre de valeurs valides, ou à partir de la moyenne des codes (constaté sur `genre` dans la base fictive : 196 − 114 − 80 = 2).
- **Conséquences :** appliqué par la porte de confidentialité ; un test vérifie, pour toutes les variables, qu'aucun effectif masqué n'est seul et qu'aucune moyenne n'accompagne un effectif masqué.

### D-009 — L'IA ne signale plus d'incohérences en v0.1 ; prompt variables-v2

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le modèle ne propose plus que des libellés et des descriptions. La demande d'incohérences de codage (« issues ») est retirée du prompt, du schéma de réponse (une réponse qui en contient est refusée) et des messages, qui ne transmettent plus les anomalies calculées. Le prompt `variables-v2` demande de rétablir les accents et, sans étiquette dans le fichier, de ne pas reprendre le libellé d'une variable voisine.
- **Options considérées :**
  1. Garder les incohérences proposées par l'IA, avec un prompt plus strict.
  2. Les retirer pour la v0.1 et laisser l'outil les calculer.
- **Justification :** essai du 2026-10-13 avec Qwen 2.5 7B (`docs/essais/2026-10-13-qwen2.5-7b.md`) : sur 48 incohérences proposées, environ 18 fausses, 17 recopiant une consigne, et les 13 justes répétaient ce que l'outil calcule déjà sans erreur. Un relecteur pressé pourrait valider une affirmation fausse.
- **Conséquences :** les incohérences en attente issues d'un ancien prompt sont retirées au prochain enrichissement ; celles qu'une personne a acceptées restent. Le prompt `variables-v1` reste dans le dépôt pour la traçabilité des essais.

### D-010 — Les jetons de valeur manquante des CSV sont lus comme des cases vides

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** dans un CSV, une cellule qui contient exactement `NA`, `N/A`, `NaN`, `#N/A` ou `NULL` (espaces autour ignorés, casse respectée) est lue comme une case vide. Le nombre de cellules lues ainsi est gardé par variable et par jeton (`missing_tokens` dans le fichier projet) et figure dans le codebook, par exemple « « NA » lu comme vide (211) ».
- **Options considérées :**
  1. Ne rien changer : les jetons restent des valeurs.
  2. Les lire comme vides, en le disant dans le codebook.
  3. Les déclarer comme codes manquants, à la manière de SPSS.
- **Justification :** essai du 2026-10-13 sur une base publique exportée par R (152 variables) : 130 colonnes contenaient `NA`, et seulement 4 étaient vues comme numériques au lieu de 132 ; plus de statistiques ni d'échelles. L'option 3 présenterait comme une déclaration de l'équipe ce qui n'est qu'une convention du logiciel d'export. Le risque de l'option 2 (une vraie valeur `NA`, comme le code ISO de la Namibie) est faible, et le codebook le rend visible.
- **Conséquences :** nouveau champ `file.missing_tokens` (liste de `{token, count}`, vide par défaut : les fichiers projet existants restent lisibles). Les décomptes restent exacts, comme tous les décomptes de manquants (D-007). Les fichiers `.sav` ne sont pas concernés.

### D-011 — Périmètre de la v0.2

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.2 comprend le questionnaire comme source documentée, le glossaire des sigles, les étiquettes de valeurs proposées à partir des options de réponse, le signalement des variantes d'écriture et la lecture des fichiers Stata, SAS et Excel. La copie corrigée du `.sav`, l'installateur Windows en un clic et le jeu de référence pour comparer les modèles passent à la v0.3.
- **Options considérées :**
  1. Commencer par les formats, l'installateur et la copie corrigée (recommandation d'avant l'essai sur données réelles).
  2. Commencer par le questionnaire et le glossaire.
- **Justification :** l'essai de la v0.1.2 sur une base publique réelle montre que les erreurs restantes portent sur le sens des variables (sigles mal compris, codes inventés), auquel seul le questionnaire répond. Plan détaillé : `docs/plan-v0.2.md`.
- **Conséquences :** étapes 1 à 10 du plan de la v0.2.

### D-012 — Le questionnaire est une source documentée fournie par l'équipe

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le texte du questionnaire découpé en questions est conservé dans le fichier projet et peut être transmis au modèle local, puisque ce n'est pas une donnée de participant. Seules les questions rattachées à une variable sont exportées.
- **Options considérées :**
  1. Conserver et exporter tout le questionnaire.
  2. Conserver tout, n'exporter que les questions rattachées.
- **Justification :** une page de consentement contient souvent les noms et coordonnées de l'équipe de recherche, qui n'ont pas leur place dans un codebook.
- **Conséquences :** un test vérifie qu'un témoin placé dans la page de consentement du questionnaire fictif n'apparaît dans aucun export.

### D-013 — Rattachement des variables aux questions : calcul, puis IA par identifiant, puis personne

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** l'outil calcule pour chaque variable quelques questions candidates ; le modèle local choisit parmi elles et répond par un identifiant de question ou d'option, jamais par du texte ; une personne accepte, change ou retire chaque rattachement. Sans IA, les candidates calculées sont proposées directement.
- **Options considérées :**
  1. Tout confier à l'IA, questionnaire complet dans le message.
  2. Tout faire à la main.
  3. Candidates calculées, choix de l'IA par identifiant, décision humaine.
- **Justification :** l'option 1 dépasse la fenêtre de contexte des petits modèles et permettrait d'inventer du texte ; l'option 2 est longue pour 150 variables. Avec l'option 3, le texte affiché vient toujours du questionnaire.
- **Conséquences :** la part de rattachements justes est mesurée à l'étape 4 ; en dessous d'un seuil jugé utile, seules les candidates calculées sont proposées.

### D-014 — Items d'instruments protégés par le droit d'auteur

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le texte des questions rattachées est exporté par défaut ; il peut être omis par groupe d'items, dans l'interface et en ligne de commande. Le guide rappelle que la reproduction des items d'un instrument protégé relève de l'équipe.
- **Options considérées :**
  1. Toujours exporter le texte.
  2. Ne jamais l'exporter.
  3. L'exporter par défaut, avec une omission possible par groupe.
- **Justification :** le texte des questions est l'apport principal du questionnaire dans un codebook, mais certains instruments (le CBCL, par exemple) ne peuvent pas être reproduits librement.
- **Conséquences :** réglage par groupe dans le fichier projet ; option d'export.

### D-015 — Sources du glossaire des sigles

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** une entrée du glossaire vient de la saisie de l'équipe ou du repérage sans IA du motif « forme longue (SIGLE) » dans le questionnaire, proposé puis validé par une personne. L'IA ne propose jamais de définition de sigle.
- **Options considérées :**
  1. Laisser l'IA proposer les définitions.
  2. Équipe et repérage dans le questionnaire seulement.
- **Justification :** l'essai sur la base publique montre que c'est précisément sur les sigles que le modèle invente (« OCF » lu comme « offices de contrôle »).
- **Conséquences :** le schéma de réponse du modèle n'a aucun champ pour un sigle ; un test le vérifie.

### D-016 — Étiquettes de valeurs proposées à partir des options de réponse

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** une étiquette de valeur n'est proposée que si le rattachement à la question est validé, que le nombre d'options égale le nombre de codes observés et que ces codes sont consécutifs (1…n ou 0…n−1). La proposition porte la mention « ordre supposé, à vérifier ». Sinon, rien n'est proposé.
- **Options considérées :**
  1. Ne rien proposer en v0.2.
  2. Proposer sous cette règle stricte.
- **Justification :** l'essai sur la base publique montre que, sans cette information, le modèle invente le sens des codes ; la règle couvre le cas habituel des plateformes d'enquête sans prétendre deviner les autres.
- **Conséquences :** tests des cas limites (codes non consécutifs, nombre différent, rattachement non validé).

### D-017 — Dépendance pypdf pour lire les questionnaires PDF

- **Date :** 2026-10-13
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** ajouter pypdf (licence BSD-3) pour extraire le texte des questionnaires PDF. Les fichiers Word attendront : un `.txt` copié depuis Word les remplace.
- **Options considérées :**
  1. pypdf, en Python pur.
  2. pdfminer.six (MIT), plus précis sur la mise en page mais plus lourd.
  3. Pas de PDF, texte seulement.
- **Justification :** les plateformes d'enquête exportent leurs questionnaires en PDF ; pypdf s'installe sans compilation et a suffi pour extraire le questionnaire réel de l'essai.
- **Conséquences :** ajoutée à l'étape 2 et notée dans `docs/dependances.md`.

### D-018 — Origine « questionnaire » pour les valeurs suivies

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les valeurs suivies du fichier projet ont une cinquième origine, `questionnaire` : une valeur calculée à partir du questionnaire sous une règle stricte, comme les étiquettes de valeurs tirées des options de réponse (D-016). Comme une valeur de l'IA, elle entre avec le statut « proposé » et n'est reprise dans le codebook et dans les messages au modèle qu'une fois acceptée par une personne.
- **Options considérées :**
  1. Origine `computed` : mais une valeur calculée est tenue pour acquise, et serait exportée sans décision.
  2. Origine `ai` : fausse, aucun modèle n'intervient, et la trace renverrait à un appel qui n'existe pas.
  3. Une origine propre, `questionnaire`, qui peut être proposée.
- **Justification :** l'essai de l'étape 6 montre qu'une proposition fondée sur l'ordre des options peut être fausse (codes recodés) ; elle doit attendre une personne, et le codebook doit pouvoir dire d'où elle vient.
- **Conséquences :** le format du fichier projet accepte cette origine (champ `value_labels` d'une variable) ; les règles de décision (accepter, rejeter, valeur acceptée) traitent `questionnaire` comme `ai`.

### D-019 — Périmètre de la v0.3

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.3 retire PowerShell de l'usage courant : accueil (nouveau projet, projets récents), parcours guidé en pages avec un tableau de bord, IA lancée depuis l'interface, export depuis l'interface, installateur Windows par double-clic, et deux corrections issues des essais de la v0.2 (questions répétées dans le rattachement, étendue observée présentée comme celle d'une échelle). La copie corrigée du `.sav`, l'aide au nettoyage et le jeu de référence pour comparer les modèles passent à la v0.4.
- **Options considérées :**
  1. Interface complète et installateur (ce choix).
  2. Copie corrigée du `.sav` d'abord.
  3. Tout à la fois.
- **Justification :** après la v0.2, six ou sept commandes et deux allers-retours entre PowerShell et le navigateur sont le principal obstacle pour des équipes qui ne programment pas. L'interface change en profondeur : mieux vaut la stabiliser avant d'ajouter des fonctions qui écrivent des données.
- **Conséquences :** plan en 8 étapes (`docs/plan-v0.3.md`) ; les commandes restent disponibles.

### D-020 — Choix des fichiers dans l'interface

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les fichiers (base, questionnaire) se choisissent avec la fenêtre « Ouvrir » du système, ouverte par l'outil sur l'ordinateur (`tkinter`, fourni avec Python), avec un champ où coller un chemin en secours. Le fichier n'est jamais envoyé par le navigateur.
- **Options considérées :**
  1. Fenêtre « Ouvrir » du système, et champ de chemin en secours.
  2. Envoi du fichier par le navigateur (glisser-déposer).
  3. Champ de chemin seulement.
- **Justification :** l'envoi par le navigateur ferait perdre l'emplacement du fichier, où le projet doit être écrit, et ferait passer une grosse base par la mémoire du navigateur ; taper un chemin est justement ce que la v0.3 veut éviter.
- **Conséquences :** la fenêtre est placée au premier plan ; le champ de chemin reste visible.

### D-021 — Forme de l'installateur Windows

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** un `installer.bat` dans l'archive installe uv et l'outil dans le dossier de l'utilisateur, sans droits d'administrateur, et crée les icônes ; un `desinstaller.bat` les retire. Internet est nécessaire pendant l'installation seulement.
- **Options considérées :**
  1. Script `installer.bat` (ce choix).
  2. Programme `.exe` empaqueté (PyInstaller, Inno Setup).
  3. Version « portable » hors ligne.
- **Justification :** l'option 2 est plus lourde à construire et à maintenir, et elle est bloquée par SmartScreen comme un script tant qu'elle n'est pas signée (certificat payant). L'option 3 pourra suivre si des établissements sans accès Internet le demandent.
- **Conséquences :** le guide montre comment passer l'avertissement « Windows a protégé votre ordinateur » ; essai sur une session Windows vierge, sans droits d'administrateur.

### D-022 — Tâches longues dans l'interface

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le rattachement et l'enrichissement par le modèle tournent dans l'onglet, avec une barre de progression bloc par bloc et un bouton « Arrêter » ; les blocs terminés sont enregistrés à mesure et une relance reprend où l'on s'était arrêté.
- **Options considérées :**
  1. Dans l'onglet, avec la reprise bloc par bloc qui existe déjà (ce choix).
  2. Processus en arrière-plan, suivi par la page.
- **Justification :** l'option 2 est plus complexe et plus difficile à arrêter proprement ; la reprise par bloc existe depuis la v0.1.
- **Conséquences :** l'écran dit qu'un changement de page arrête le travail en cours, sans rien perdre des blocs terminés.

### D-023 — Téléchargement du modèle

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** l'outil ne télécharge ni n'installe jamais de modèle. Il vérifie qu'Ollama répond sur l'ordinateur, liste les modèles installés et explique la marche à suivre ; le téléchargement reste une action explicite de la personne, ou de l'installateur qui le lui demande.
- **Options considérées :**
  1. Détection et explication seulement (ce choix).
  2. Bouton de téléchargement dans l'interface.
- **Justification :** l'outil ne communique avec rien d'autre que l'ordinateur (principe 3) ; un téléchargement de plusieurs gigaoctets doit être un choix conscient.
- **Conséquences :** la détection passe par l'adresse locale d'Ollama, avec le même refus de toute adresse non locale que le client actuel.

### D-024 — Liste des projets récents

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la liste des derniers projets ouverts est enregistrée dans le dossier de l'utilisateur (`%APPDATA%\ddict` sous Windows), avec les chemins seulement, jamais de données, et peut être effacée depuis l'accueil.
- **Options considérées :**
  1. Liste enregistrée, effaçable (ce choix).
  2. Pas de liste : choisir le fichier à chaque fois.
- **Justification :** rouvrir un projet en un clic est le cas le plus fréquent ; les noms de dossiers peuvent dire quelque chose d'une étude, d'où la possibilité de tout effacer.
- **Conséquences :** le fichier reste sur l'ordinateur ; il n'entre ni dans le projet ni dans les exports.

### D-025 — Périmètre de la v0.4

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.4 fait passer les décisions du codebook aux données et aide à choisir un modèle : fichiers de commandes (SPSS, R, Stata), codes manquants confirmés, copie documentée du `.sav`, banc d'essai des modèles avec une seconde base fictive, décisions groupées avec aperçu. Pas de recodage des valeurs, même sur une copie. L'installateur macOS et Linux et l'interface en anglais sont reportés.
- **Options considérées :**
  1. Ces cinq fonctions (ce choix).
  2. Seulement les fichiers de commandes.
  3. Ajouter le recodage (items inversés, variantes d'écriture) sur une copie.
- **Justification :** reporter à la main les décisions validées dans SPSS, R ou Stata est long et source d'erreurs ; le choix du modèle se faisait à l'aveugle ; la révision des rattachements est longue sur une grande base. Le recodage change les données elles-mêmes : c'est une analyse, que l'équipe fait et documente dans son propre logiciel.
- **Conséquences :** plan en 8 étapes (`docs/plan-v0.4.md`).

### D-026 — L'outil écrit une copie documentée du `.sav`, jamais l'original

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** sur demande seulement, l'outil écrit une nouvelle copie de la base au format `.sav`, avec les métadonnées acceptées et des données identiques à l'original. Il la relit et la compare cellule par cellule avant de l'annoncer ; au moindre écart, il la supprime et le dit. L'original n'est jamais ouvert en écriture, et une copie existante n'est pas écrasée sans accord. Les fichiers de commandes restent la voie recommandée.
- **Options considérées :**
  1. Fichiers de commandes seulement : l'outil n'écrit jamais de données.
  2. Fichiers de commandes et copie facultative vérifiée (ce choix).
  3. Modifier la base en place.
- **Justification :** certaines équipes veulent un fichier prêt à l'emploi ; la vérification cellule par cellule rend une copie fausse impossible à manquer. L'option 3 contredit le principe qu'un fichier original n'est jamais modifié.
- **Conséquences :** c'est la première fonction qui écrit des données de participants : elles restent sur l'ordinateur, à côté de l'original, et rien n'en entre dans le projet ni ne va au modèle.

### D-027 — PSPP comme outil de développement

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** PSPP (GNU GPL) sert à vérifier la syntaxe SPSS produite par l'outil, sur le poste de développement seulement, comme R et haven pour la base SAS. Ni l'outil ni ses tests ordinaires n'en dépendent : le test qui l'utilise est sauté si PSPP manque.
- **Options considérées :**
  1. PSPP sur le poste de développement (ce choix).
  2. Aucune vérification de la syntaxe SPSS.
  3. Une licence SPSS.
- **Justification :** une syntaxe jamais exécutée risque d'échouer chez l'équipe ; PSPP est libre et lit l'essentiel de la syntaxe SPSS. Le fichier Stata sera vérifié par une personne qui a Stata.
- **Conséquences :** noté dans `docs/dependances.md` à l'étape 3.

### D-028 — Codes manquants confirmés par une personne

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** un code sentinelle repéré par le calcul (999, −9…) devient un code manquant quand une personne le confirme sur la fiche de la variable ; elle peut aussi dire que c'est une vraie valeur. L'IA ne le propose jamais. Les statistiques du profil ne sont pas recalculées : elles décrivent le fichier tel qu'il est ; le codebook et les fichiers de commandes disent que le code est confirmé par l'équipe.
- **Options considérées :**
  1. Décision humaine à partir du calcul (ce choix).
  2. Déclarer automatiquement les codes sentinelles.
  3. Ne rien changer : les déclarer reste à faire dans le logiciel de l'équipe.
- **Justification :** un 999 peut être une vraie valeur (un montant, une durée) ; seule l'équipe le sait. Sans cette décision, les fichiers de commandes ne pourraient pas déclarer les codes manquants des CSV.
- **Conséquences :** une valeur suivie de plus par variable dans le fichier projet.

### D-029 — Décisions groupées, avec aperçu obligatoire

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** l'interface peut accepter plusieurs propositions d'un coup, après avoir montré la liste exacte des variables concernées, dont chacune peut être décochée. C'est permis seulement pour les rattachements où le modèle et le calcul s'accordent, et pour les étiquettes de valeurs d'un même groupe d'items. Chaque décision est enregistrée une par une, avec sa date.
- **Options considérées :**
  1. Décisions groupées avec aperçu et décoche (ce choix).
  2. Une décision à la fois seulement.
  3. Accepter tout ce que propose le modèle.
- **Justification :** sur une grande base, la révision une à une est longue, alors que l'accord du modèle et du calcul est un bon indice ; l'aperçu garde chaque décision visible. L'option 3 ferait des propositions des décisions sans regard humain.
- **Conséquences :** l'essai de l'étape 5 mesure le temps gagné et les erreurs qui passent par ce bouton.

### D-030 — Pas de fichier de commandes Stata

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** — (restreint D-025 : les fichiers de commandes sont SPSS et R)
- **Décision :** l'outil n'écrit pas de fichier de commandes Stata (`.do`). Les fichiers de commandes sont une syntaxe SPSS et un script R. La lecture des bases Stata (`.dta`) reste, ainsi que la copie documentée à partir d'une base Stata.
- **Options considérées :**
  1. Retirer le fichier Stata (ce choix).
  2. Le garder, avec la mention « non essayé dans Stata ».
  3. Attendre l'essai d'une personne qui a Stata avant de publier.
- **Justification :** ni l'auteur ni le poste de développement n'ont Stata ; la syntaxe SPSS est vérifiée avec PSPP et le script R avec R, mais le fichier Stata ne l'était que par sa forme. Un fichier jamais exécuté risquerait d'échouer chez l'équipe. Une équipe qui travaille avec Stata peut utiliser la copie documentée (`.sav`, que Stata lit avec `import spss`).
- **Conséquences :** code, tests, guide, conception et journal des changements mis à jour ; un fichier Stata pourra revenir si une personne qui a Stata peut l'essayer.
