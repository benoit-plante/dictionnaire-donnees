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

### D-031 — Périmètre de la v0.5

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.5 rend l'outil utilisable en anglais (interface, codebook, études menées en anglais, guides) et l'installe sous macOS par double-clic. Linux, les exports DDI et Frictionless et le dictionnaire REDCap sont reportés ; seuls le français et l'anglais sont visés.
- **Options considérées :**
  1. Anglais et macOS (ce choix).
  2. Anglais, macOS et Linux.
  3. Dépôt des données (DDI, Frictionless) et REDCap.
- **Justification :** beaucoup d'équipes québécoises sont bilingues et beaucoup de chercheurs travaillent sur un Mac ; l'auteur a retenu ces deux pistes et écarté Linux.
- **Conséquences :** plan en 8 étapes (`docs/plan-v0.5.md`).

### D-032 — Langue de l'interface et langue du projet

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** deux réglages distincts. La langue de l'interface est choisie par chaque personne, sur l'accueil, et gardée dans le dossier de réglages de l'ordinateur (`DDICT_LANG` la remplace). La langue du projet (questionnaire, libellés, consignes au modèle) est choisie par l'équipe et gardée dans le fichier projet (`settings.language`). La langue du codebook se choisit à l'export, par défaut celle de l'interface. Les valeurs écrites par l'équipe ne sont jamais traduites.
- **Options considérées :**
  1. Deux langues distinctes (ce choix).
  2. Une seule langue pour tout.
- **Justification :** une personne peut préférer l'interface en français pour une étude menée en anglais, ou l'inverse ; traduire les valeurs de l'équipe serait une invention.
- **Conséquences :** les textes traduits une seule fois au démarrage le seront à l'affichage.

### D-033 — Outils de traduction

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** Babel (BSD-3-Clause), dépendance de développement seulement, extrait les phrases à traduire et compile le catalogue `.mo` ; à l'exécution, l'outil n'utilise que `gettext`, de la bibliothèque standard. Le `.mo` compilé est gardé dans le dépôt, avec un test qui vérifie qu'il correspond au `.po`.
- **Options considérées :**
  1. Babel en développement (ce choix).
  2. Un format maison (JSON).
  3. Babel aussi à l'exécution.
- **Justification :** gettext est la norme, déjà prévue par D-004 ; Babel fonctionne sous Windows sans outils GNU ; aucune dépendance nouvelle pour les personnes qui installent l'outil.
- **Conséquences :** noté dans `docs/dependances.md` à l'étape 1.

### D-034 — Relecture de la traduction

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** l'assistant écrit la traduction anglaise ; une personne anglophone la relit avant la version. Sans cette relecture, l'anglais est publié comme « à l'essai ».
- **Options considérées :**
  1. Relecture par une personne anglophone (ce choix).
  2. Publication sans relecture.
- **Justification :** une interface mal traduite fait plus de tort qu'une interface en français.
- **Conséquences :** un glossaire des termes anglais (codebook, missing code, value label…) est fixé à l'étape 2.

### D-035 — Essais sous macOS

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les tests et un essai de l'installateur passent sous macOS dans GitHub Actions, lancés à la demande pour limiter les minutes d'un dépôt privé ; un essai réel sur un Mac, par une personne qui en a un, est demandé avant la version. Sans cet essai, macOS est publié comme « à l'essai ».
- **Options considérées :**
  1. Actions à la demande et essai réel (ce choix).
  2. Actions à chaque envoi.
  3. Pas d'essai sous macOS.
- **Justification :** le poste de développement n'a pas de Mac ; Actions vérifie l'installation et le démarrage, pas l'icône ni les avertissements de sécurité de macOS.
- **Conséquences :** un fichier de workflow GitHub Actions est ajouté à l'étape 6.

### D-036 — Langue de la documentation

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les guides d'installation et d'utilisation existent en français et en anglais ; la documentation technique (conception, journal des décisions, plans, essais) reste en français.
- **Options considérées :**
  1. Guides bilingues, documentation technique en français (ce choix).
  2. Tout traduire.
- **Justification :** les guides servent aux personnes qui utilisent l'outil ; la documentation technique sert au développement.
- **Conséquences :** guides anglais dans `docs/en/` à l'étape 7.

### D-037 — Dépôt public

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** D-003, pour la visibilité du dépôt (le nom reste un nom de travail)
- **Décision :** le dépôt GitHub devient public. « dictionnaire-donnees » reste un nom de travail ; un changement de nom plus tard reste possible (GitHub redirige l'ancienne adresse).
- **Options considérées :**
  1. Rendre le dépôt public (ce choix).
  2. Garder le dépôt privé et payer les minutes macOS de GitHub Actions.
  3. Garder le dépôt privé et vérifier macOS seulement sur un vrai Mac.
- **Justification :** GitHub Actions est gratuit pour un dépôt public, macOS compris, ce qui permet les essais macOS de D-035 ; l'outil est un logiciel libre destiné à être partagé. Avant le changement, l'historique (68 versions) a été vérifié : aucune donnée réelle, aucune base publique d'essai, aucun mot de passe ni clé, seulement des adresses fictives ; un seul chemin personnel (`C:\Users\…`) dans une ancienne version du scénario manuel, sans conséquence. Le nom et l'adresse de l'auteur figurent dans l'historique.
- **Conséquences :** `CLAUDE.md` mis à jour ; les essais macOS de D-035 tournent sans frais ; tout ce qui entre dans le dépôt est public dès l'envoi.

### D-038 — Périmètre de la v0.6

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.6 rend les rattachements plus complets : « aucune question » proposée par le calcul, questions voisines pour les variables sans candidate, calcul sûr signalé au modèle, banc d'essai qui classe les rattachements manqués, base de contrôle. Le dépôt des données, REDCap, la révision groupée des libellés et Linux sont reportés.
- **Options considérées :**
  1. Des rattachements plus complets (ce choix).
  2. Dépôt des données et REDCap.
  3. Révision plus rapide des libellés.
- **Justification :** le rattachement est l'étape qui demande le plus de révision ; le diagnostic des bases fictives montre trois pertes précises (variables sans question rattachées, variables sans candidate, bons choix du calcul défaits par le modèle).
- **Conséquences :** plan en 7 étapes (`docs/plan-v0.6.md`).

### D-039 — « Aucune question » proposée par le calcul

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le calcul met la candidate « aucune question » en tête quand un indice fort la rend probable : identifiant probable, date de passation ou de réponse sans question de date correspondante, score calculé (nom ou somme exacte des items d'un groupe, vérifiée au profilage, dont seul le fait est gardé). Sinon, elle reste en fin de liste. La décision reste à une personne.
- **Options considérées :**
  1. En tête sur indices forts (ce choix).
  2. Toujours en fin de liste, comme avant.
  3. Retirer les questions candidates de ces variables.
- **Justification :** six variables sans question des bases fictives sont rattachées à tort ; retirer les candidates empêcherait de corriger un indice trompeur.
- **Conséquences :** un test vérifie qu'aucune variable qui a une question ne perd sa question en tête.

### D-040 — Questions voisines

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** élargit D-013
- **Décision :** pour une variable sans candidate, le calcul propose les questions situées entre les rattachements sûrs qui l'entourent dans l'ordre du questionnaire, au plus 6, marquées comme voisines pour le modèle et dans l'interface. Le modèle choisit toujours dans la liste qu'il reçoit (D-013), élargie à ces voisines.
- **Options considérées :**
  1. Questions voisines pour les variables sans candidate (ce choix).
  2. Tout le questionnaire pour ces variables.
  3. Statu quo : la personne choisit seule.
- **Justification :** une question peut ne partager aucun mot avec le nom de sa variable (« How old are you? » pour `age`) ; l'ordre du questionnaire, lui, est un indice fiable.
- **Conséquences :** prompt `link-v3` (français et anglais).

### D-041 — Désaccord entre le modèle et un calcul sûr

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** quand la première candidate du calcul est sûre (règle des ancres), le modèle le sait ; s'il choisit autre chose, sa proposition est gardée mais accompagnée d'un signal de désaccord, jamais remplacée en silence.
- **Options considérées :**
  1. Signaler le désaccord (ce choix).
  2. Imposer le choix du calcul.
  3. Statu quo.
- **Justification :** au banc, le modèle défait des choix justes du calcul (calcul seul 88 / 98, modèle 81 / 98) ; imposer le calcul retirerait au modèle les cas où il voit mieux.
- **Conséquences :** le banc mesure les bons choix du calcul défaits, avant et après.

### D-042 — Base de contrôle

- **Date :** 2026-10-14
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** une base fictive nouvelle, générée avec son corrigé avant toute mise au point de la v0.6, est mise de côté : elle est mesurée une seule fois, à la fin, pour la 0.5 et la 0.6, puis rejoint le banc d'essai.
- **Options considérées :**
  1. Une base de contrôle mise de côté (ce choix).
  2. Mesurer seulement sur les trois bases du banc.
- **Justification :** les bases du banc ont servi à régler l'outil depuis la v0.2 ; un progrès mesuré sur elles seules pourrait n'être qu'un réglage sur mesure.
- **Conséquences :** si la 0.6 ne fait pas mieux sur la base de contrôle, les changements sont revus.

### D-043 — Périmètre de la v0.7

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.7 lit juste les exports de plateforme de sondage (SurveyMonkey : `.sav`, `.csv`, `.xlsx`), tire parti de leur structure, et ajoute le renommage des variables, y compris la reprise des noms d'une vague précédente. Les corrections de lecture passent en premier. Le contrat d'analyse passe à la v0.8 ; LimeSurvey, Qualtrics et REDCap sont seulement rendus possibles.
- **Options considérées :**
  1. Exports de plateforme et renommage (ce choix).
  2. Contrat d'analyse d'abord.
- **Justification :** un essai de la v0.6 sur deux exports SurveyMonkey réels montre des erreurs de lecture (en-tête lu comme un participant, faux groupes, faux identifiant, dates en texte, questionnaires mal découpés) et une structure plus fiable que le questionnaire PDF ; beaucoup d'équipes partent de ces exports bruts.
- **Conséquences :** plan en 11 étapes (`docs/plan-v0.7.md`).

### D-044 — Plateformes décrites par leurs conventions

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** une plateforme est une description de ses conventions (variables de plateforme et leurs variantes, motif des noms d'items, en-tête, option « autre », noms fixes) dans `ddict.platforms` ; seule SurveyMonkey est décrite. La plateforme reconnue est gardée dans `source.platform`. Un ensemble de cases à cocher devient un groupe de nature « réponses multiples » (`Group.kind`), sa variable « autre » rattachée hors des membres.
- **Options considérées :**
  1. Une description par plateforme (ce choix).
  2. Du code propre à SurveyMonkey.
- **Justification :** une autre plateforme pourra s'ajouter par une description et ses tests, sans toucher au reste.
- **Conséquences :** quand la structure existe, elle remplace les règles de préfixe et d'étiquettes partagées pour les variables qu'elle couvre ; le rang de plateforme ne fait un rattachement sûr qu'avec la concordance des textes.

### D-045 — L'en-tête du `.xlsx` comme troisième format de questionnaire

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** l'en-tête d'un export `.xlsx` de SurveyMonkey (ses deux premières lignes seulement, jamais les réponses) peut être lu comme questionnaire, au même titre qu'un PDF ou un `.txt` ; il reste la source unique du questionnaire du projet.
- **Options considérées :**
  1. Un troisième format, source unique (ce choix).
  2. Un complément fusionné au PDF.
- **Justification :** l'en-tête est exact là où le PDF est incertain (énoncés, options, consigne des grilles) et ses identifiants coïncident avec les noms des variables ; une fusion ajouterait un appariement incertain. Ce qui lui manque (pages, consentement) n'est pas exporté de toute façon (D-012).
- **Conséquences :** `Questionnaire.format` accepte `xlsx` ; les options des questions à choix restent les étiquettes de valeurs du `.sav`.

### D-046 — Données réelles hors du dépôt

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** des tests marqués `reel` lisent de vrais exports dans un dossier donné par `DDICT_DONNEES_REELLES`, hors du dépôt ; ils sont sautés sans cette variable et exclus de l'intégration continue. Ils ne vérifient que des décomptes et des taux, jamais une valeur, une étiquette ni un texte, et leurs identifiants sont `base1`, `base2`. Les essais les décrivent par des faits de structure, sans nommer d'instrument.
- **Options considérées :**
  1. Tests `reel` à décomptes seulement (ce choix).
  2. Aucun test sur données réelles.
- **Justification :** la base fictive est écrite d'après le cahier des charges et pourrait être plus facile que les vraies ; un message d'échec de pytest montre les valeurs comparées, d'où des assertions sur des nombres seulement.
- **Conséquences :** rien du dossier n'entre dans le dépôt, les tests, les exemples ni les messages de commit ; son chemin n'apparaît nulle part.

### D-047 — Codes manquants probables par leur étiquette ; niveau `scale` douteux

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** élargit D-028
- **Décision :** un code dont l'étiquette dit « Ne sais pas », « Préfère ne pas répondre », « Refus », « Sans objet » ou un équivalent anglais devient un code manquant probable, décidé par une personne comme les autres, et écarté du calcul de l'alpha comme les autres codes suspects. Le niveau de mesure `scale` d'un item étiqueté d'une grille est signalé comme douteux, sans être changé.
- **Options considérées :**
  1. Proposer par l'étiquette, signaler le niveau (ce choix).
  2. Garder la détection par les valeurs seulement.
- **Justification :** dans les exports SurveyMonkey, ces codes suivent l'échelle (6 et 7 après 1-5) et la détection par les valeurs ne les voit pas ; le niveau de mesure relève d'une décision de la v0.8.

### D-048 — Le nouveau nom d'une variable et la version du format

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** `new_name` est une valeur suivie ; le nom d'origine reste la clé de la variable. Deux origines nouvelles peuvent être proposées : `rule` (règles de nommage) et `reference` (vague précédente, table de correspondance). Le préfixe d'un groupe et le radical d'une question sont aussi des valeurs suivies. `schema_version` passe à 0.2.0, sans conversion : tous les champs nouveaux ont une valeur par défaut.
- **Options considérées :**
  1. Origines nouvelles `rule` et `reference` (ce choix).
  2. Permettre les propositions d'origine `computed`.
  3. Remplacer le nom d'origine par le nouveau nom.
- **Justification :** une valeur calculée est tenue pour acquise ; un nom ne l'est jamais sans une personne. Le nom d'origine sert à relire et reconnaître la base.
- **Conséquences :** une version 0.6 ne lit pas un projet 0.2.0 ; l'inverse fonctionne. Le fichier d'origine n'est jamais modifié : les noms acceptés s'appliquent dans le codebook, les fichiers de commandes et la copie documentée (D-025, D-026).

### D-049 — Marque de vague par défaut

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** aucune marque tant que la personne ne donne pas de vague ; ensuite, un suffixe `_t<N>` (`k6_1_t2`), le préfixe `t2_` restant au choix. La marque de la vague précédente est retirée avant d'ajouter la nouvelle.
- **Options considérées :**
  1. Suffixe par défaut (ce choix).
  2. Préfixe par défaut.
- **Justification :** le suffixe garde ensemble, dans une liste triée, les variables d'un même concept, et laisse le début du nom au concept.

### D-050 — Noms fixes des variables de plateforme

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** en français, `respondent_id`, `collector_id`, `nom_collecteur`, `date_debut`, `date_fin`, `adresse_ip`, `courriel`, `prenom`, `nom_famille`, `donnees_personnalisees_1` ; en anglais, `respondent_id`, `collector_id`, `collector_name`, `start_date`, `end_date`, `ip_address`, `email`, `first_name`, `last_name`, `custom_data_1`. La classe de confidentialité reste visible à côté.
- **Options considérées :**
  1. Ces noms (ce choix).
  2. `nom` et `donnees_perso_1`, de la demande initiale.
- **Justification :** `respondent_id` et `collector_id` sont les noms de la plateforme et de ses autres exports, utiles pour joindre des fichiers ; `nom` est ambigu ; « perso » se lit « personnelles », alors que ce sont les données personnalisées de SurveyMonkey.

### D-051 — Place du modèle dans le renommage

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le modèle peut proposer, facultativement et après le calcul, le radical des questions seulement, jamais un préfixe de groupe, le nom d'une variable de plateforme ni un rang ; il ne remplace qu'un radical non décidé. Schéma strict, prompts `rename-v1`, signal « instrument » sur un sigle absent de la question et du glossaire.
- **Options considérées :**
  1. Radicaux seulement, gardé si le banc le justifie (ce choix).
  2. Tous les noms.
  3. Pas de modèle.
- **Justification :** le sigle d'un instrument est un nom d'instrument (principe 4) ; le calcul couvre déjà la plupart des cas.
- **Conséquences :** comme pour D-013, si le banc ne montre pas plus de noms acceptés tels quels qu'avec le calcul seul, la proposition par le modèle n'est pas offerte dans l'interface.

### D-052 — Vague précédente et table de correspondance

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les noms d'une vague précédente se reprennent depuis son fichier projet (recommandé), sa copie documentée `.sav` ou une table CSV : UTF-8, séparateur `,` ou `;`, en-tête `nom_origine,nouveau_nom` (ou `original_name,new_name`). L'outil écrit la même table à l'export. L'appariement se fait par le calcul, avec un score lisible, et ne propose qu'un appariement net ; un rapport donne les variables ajoutées, retirées et les étiquettes de valeurs changées.
- **Options considérées :**
  1. Trois sources, table au format de l'export (ce choix).
  2. Fichier projet seulement.
- **Justification :** la sortie d'une vague sert d'entrée à la suivante ; une table ne contient que des noms et n'apparie que par nom d'origine identique, fragile quand la plateforme renumérote ses questions, ce que le rapport signale.

### D-053 — Pas d'acceptation groupée des rattachements par la structure de plateforme

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la règle de D-029 reste telle quelle : un rattachement ne s'accepte en lot que lorsque le modèle et le calcul s'accordent. Les rattachements sûrs par la structure d'un export de plateforme (numéro et texte concordants) restent des propositions à accepter une par une, ou en lot quand le modèle les confirme.
- **Options considérées :**
  1. Permettre le lot, avec aperçu obligatoire, pour les rattachements sûrs par la structure.
  2. Garder la règle de D-029 (ce choix).
  3. Permettre le lot pour tous les choix sûrs du calcul.
- **Justification :** choix de l'auteur, par prudence : un rattachement entre dans le codebook par la décision d'une personne, variable par variable, sauf quand deux méthodes indépendantes s'accordent.
- **Conséquences :** l'étape 9 de la v0.7 n'ajoute pas de décision groupée pour les rattachements ; l'acceptation groupée des noms (par groupe ou par question), prévue au plan, reste.

### D-054 — Le `.sav` comme format de référence

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le `.sav` devient le format de référence de l'outil : les guides recommandent de l'exporter quand c'est possible, et les efforts d'amélioration portent sur lui et sur la lecture du questionnaire. Les autres formats (CSV, Excel, Stata, SAS) restent lus comme avant, sans nouvelle règle qui leur soit propre.
- **Options considérées :**
  1. Ne lire que le `.sav`.
  2. `.sav` comme référence, les autres formats gardés (ce choix).
  3. Tous les formats au même rang, comme dans la conception.
- **Justification :** le `.sav` contient ce que les autres formats obligent à deviner (étiquettes de valeurs, codes manquants déclarés, niveaux de mesure). Retirer les autres formats ne rendrait pas la lecture d'un `.sav` plus juste : les deux chemins sont séparés, et les erreurs relevées sur les vraies bases venaient de la lecture du questionnaire, des groupes et des noms, pas du format. Les garder sert les équipes sans SPSS et les plateformes qui exportent surtout en CSV ; l'en-tête d'un export Excel aide même à côté du `.sav` (D-045).
- **Conséquences :** l'interface signalera, pour une base qui n'est pas un `.sav`, que certaines informations sont devinées plutôt que lues et sont à vérifier (étape 11 de la v0.7). Une règle propre au CSV ou à Excel ne s'ajoute plus que pour corriger une erreur.

### D-055 — L'outil dans sa propre fenêtre, sans fenêtre noire

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** sous Windows, l'icône lance `ddict-fenetre`, un lanceur sans console : il démarre l'interface sans fenêtre visible et l'affiche dans une fenêtre à elle (pywebview, sur le moteur d'Edge déjà présent dans Windows) ; fermer cette fenêtre arrête l'outil. Un bouton « Quitter l'outil », en bas de la barre latérale, arrête aussi l'outil, partout (fenêtre, navigateur, Mac, ligne de commande). Les messages de démarrage vont dans `journal.txt`, à côté de la liste des projets récents. Sans pywebview ou sans le moteur d'Edge, l'interface s'ouvre dans le navigateur, comme avant. La commande `ddict` et le Mac ne changent pas.
- **Options considérées :**
  1. Pas de fenêtre visible, bouton « Quitter » et arrêt automatique quand plus aucun onglet n'est ouvert.
  2. Fenêtre d'application du navigateur (mode application d'Edge ou de Chrome), avec le même arrêt.
  3. Une vraie fenêtre d'application avec pywebview (ce choix).
  4. Une icône près de l'horloge (pystray, LGPL).
  5. Réécrire l'interface en logiciel classique.
- **Justification :** la seule option où fermer la fenêtre arrête l'outil, comme pour tout logiciel, sans rien qui tourne en arrière-plan. Essai concluant de l'auteur avant la décision : fenêtre « Ouvrir » au premier plan, téléchargements, export et ouverture du dossier fonctionnent ; l'outil s'arrête entièrement à la fermeture. Licences BSD et MIT, compatibles.
- **Conséquences :** nouvelle dépendance de l'option « revision », sous Windows seulement (`docs/dependances.md`). Sur Mac, une vraie application reste à faire, faute de pouvoir l'essayer ailleurs que sur un Mac de GitHub ; le bouton « Quitter l'outil » y sert déjà.

### D-056 — Décider des noms dans le tableau ; « nom de base » au lieu de « radical »

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** sur la page « Noms », les décisions se prennent dans le tableau : une colonne « Décision » (vide, Accepter, Rejeter) à côté de la colonne « Nouveau nom », un seul bouton « Enregistrer ». Le bouton « Choisir « Accepter » pour les N noms proposés » remplit la colonne pour les noms proposés sans problème ; rien n'est enregistré avant que la personne ait relu et cliqué « Enregistrer ». La partie « Une variable » et l'acceptation en lot par grille ou par question sont retirées. La partie commune des noms d'une question s'appelle « nom de base » (« base name »), plus « radical ».
- **Options considérées :**
  1. Colonne « Décision » avec un menu par ligne (ce choix).
  2. Case « Accepter » par ligne, le rejet en effaçant le nom.
  3. Garder les décisions sous le tableau et le lot par grille.
  - Pour le mot : « nom de base » (ce choix), « préfixe » comme pour les grilles, « racine ».
- **Justification :** choix de l'auteur, pour un travail plus direct : tout se voit et se décide au même endroit. La règle de D-029 est tenue : la colonne remplie d'avance est la liste exacte, relue et modifiable ligne par ligne avant tout enregistrement. « Nom de base » se comprend sans vocabulaire de grammaire et reste juste pour une question seule, dont il est le nom entier.
- **Conséquences :** un nom écrit et « Rejeter » sur la même ligne sont refusés ensemble ; une ligne fautive empêche tout l'enregistrement, sans rien changer. Le reste de D-053 tient (pas de lot pour les rattachements par la structure).

### D-057 — Périmètre de la v0.8

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.8 fait du codebook un contrat d'analyse : export « contexte d'analyse », cotation structurée, niveau de mesure modifiable, métadonnées de la base, complétude, script de préparation, empreinte du codebook. La base synthétique et les filtres du questionnaire sont proposés pour la v0.9 ; l'assistant d'analyse reste une piste pour un projet distinct.
- **Options considérées :**
  1. Tout le contrat d'analyse, l'utilité sans IA présentée d'abord (ce choix).
  2. Seulement ce qui sert sans IA ; le contexte compact plus tard.
  3. Une autre priorité (application Mac, autres plateformes, grande base).
- **Justification :** choix de l'auteur. La plupart des fonctions servent une équipe qui analyse elle-même (scores, niveau de mesure, complétude, reproductibilité) ; l'export compact répond à un usage qui existe déjà, une IA qui aide à écrire le code d'analyse, et repose sur les mêmes décisions.
- **Conséquences :** plan en 9 étapes (`docs/plan-v0.8.md`).

### D-058 — Format du contexte d'analyse

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** un `datapackage.json` (Frictionless Table Schema, propriétés propres à l'outil dans l'espace de noms `ddict:`) et un `<base>-contexte.md` compact, une ligne par variable, valeurs acceptées seulement. Les variables y sont désignées par leur nom final, avec leur nom d'origine.
- **Options considérées :**
  1. Frictionless et un Markdown compact (ce choix).
  2. Un format propre à l'outil seulement.
  3. DDI Codebook.
- **Justification :** un standard ouvert, lisible par des programmes et accepté par des dépôts ; le Markdown se colle tel quel dans un modèle. DDI est plus lourd que le besoin.
- **Conséquences :** la version du standard et la licence de son schéma sont vérifiées à l'étape 1.

### D-059 — Statistiques dans le contexte d'analyse

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** absentes par défaut ; ajoutées sur demande (case de la page « Export », `--avec-statistiques`), toujours filtrées par la porte de confidentialité.
- **Options considérées :**
  1. Absentes par défaut (ce choix).
  2. Toujours présentes.
- **Justification :** sans elles, le contexte ne contient que des métadonnées ; ce qui peut sortir du poste relève du certificat d'éthique et de l'équipe.

### D-060 — Cotation structurée

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la cotation d'un groupe devient un objet (items, items inversés et règle d'inversion, somme ou moyenne, nombre minimal d'items répondus, étendue et nom du score), saisi par une personne avec sa source ; le texte libre reste possible en note. Le modèle ne la propose jamais. Un groupe « réponses multiples » n'en a pas.
- **Options considérées :**
  1. Objet structuré, humain et sourcé (ce choix).
  2. Texte libre seulement, comme aujourd'hui.
- **Justification :** un score se calcule alors sans deviner, par un programme ou par un modèle ; une règle de cotation est une information d'instrument, que le modèle ne doit pas inventer (principe 4).

### D-061 — Format du projet 0.3.0

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** le format du projet passe en 0.3.0 ; les projets 0.1.0 et 0.2.0 sont convertis à l'ouverture (le texte de cotation devient une note). Un projet converti ne s'ouvre plus avec une version plus ancienne.
- **Options considérées :**
  1. Conversion à l'ouverture (ce choix).
  2. Garder l'ancien champ à côté du nouveau, sans conversion.
- **Justification :** un seul endroit pour la cotation ; deux champs pour la même chose finiraient par se contredire.
- **Conséquences :** première conversion du format ; testée sur des projets de chaque version, et signalée dans le guide.

### D-062 — Script de préparation

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** l'outil écrit un script de préparation (SPSS et R) qui crée de nouvelles variables (items inversés `_inv`, scores) selon les décisions acceptées, sans modifier les variables d'origine. Il s'exécute après le fichier de commandes, sur les noms finaux, et compare un score recalculé à un score déjà présent dans la base.
- **Options considérées :**
  1. Nouvelles variables, variables d'origine intactes (ce choix).
  2. Pas de script, comme D-025 le prévoyait.
- **Justification :** le calcul des scores avec items inversés est une source d'erreurs fréquente ; aucune valeur d'origine n'est recodée, et l'équipe exécute le script dans son propre logiciel.
- **Conséquences :** élargit D-025, qui excluait tout recodage, même sur une copie : créer de nouvelles variables est désormais permis, recoder les valeurs d'origine ne l'est toujours pas.

### D-063 — Niveau de mesure modifiable

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** chaque variable a un niveau de mesure suivi ; le calcul le propose quand le fichier n'en a pas (CSV, Excel) ou quand le niveau `scale` d'un item étiqueté de grille est douteux (`ordinal`), et une personne décide. Le niveau accepté passe dans les fichiers de commandes, la copie documentée et le contexte d'analyse.
- **Options considérées :**
  1. Modifiable, proposé par le calcul (ce choix).
  2. Seulement signalé, comme en v0.7.
- **Justification :** le choix des analyses repose sur le niveau de mesure ; la v0.7 avait laissé ouverte la question du niveau `scale` des items (D-047).

### D-064 — Métadonnées de la base

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** ce que représente une ligne, la structure (transversale, une vague par fichier, format large, format long) et les variables de plan sont saisis par une personne sur la page « Base ». Seules la structure « une vague par fichier » (d'après la marque de vague) et le format large (d'après des suffixes de temps) peuvent être proposés par le calcul.
- **Options considérées :**
  1. Saisie humaine, deux propositions par le calcul (ce choix).
  2. Tout deviner par le calcul.
- **Justification :** ces faits ne se lisent pas de façon sûre dans les données ; un modèle qui les ignore traite des mesures répétées comme des participants indépendants.

### D-065 — Assistant d'analyse

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** un assistant d'analyse (vérificateur de scripts, boucle d'analyse locale, interprétation, rédaction de la méthode) serait un projet distinct, qui lirait le contexte d'analyse. `dictionnaire-donnees` n'exécute jamais de code d'analyse.
- **Options considérées :**
  1. Projet distinct (ce choix).
  2. L'intégrer à l'outil.
- **Justification :** l'outil reste un outil de documentation ; la v0.8 ne dépend pas de cet assistant, qui n'est qu'une piste.

### D-066 — Propriétés de l'outil dans un objet `_ddict` ; format du contexte d'analyse validé

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** — (précise D-058)
- **Décision :** dans le `datapackage.json`, les propriétés propres à l'outil sont réunies dans un objet `_ddict` (paquet, ressource, champ), selon la convention publiée du standard (préfixe `_`, recette « Private Properties »), et non dans un espace de noms `ddict:` comme D-058 l'écrivait. Le format du contexte d'analyse est celui des exemples de `docs/exemples-contexte/` et de `CONCEPTION.md` § 8.1 : aucune valeur observée (une variante d'écriture est dite, pas citée) ; pour une question à cocher, la question une fois en tête du groupe et l'option sur chaque ligne ; une règle explicite sur le sens d'une case vide.
- **Options considérées :**
  1. Objet `_ddict`, selon la convention du standard (ce choix).
  2. Espace de noms `ddict:`, comme D-058.
- **Justification :** suivre la convention publiée rend le fichier plus prévisible pour les outils Frictionless ; un seul objet regroupe tout ce qui n'est pas standard. Spécification v2 vérifiée le 2026-10-15 ; les exemples sont valides selon ses schémas. Choix validés par l'auteur à la fin de l'étape 1 de la v0.8.

### D-067 — L'origine « règle » pour toute règle de l'outil qui propose

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** — (élargit D-048)
- **Décision :** l'origine `rule`, créée pour les noms proposés par les règles de nommage (D-048), sert à toute règle déterministe de l'outil qui fait une proposition ; d'abord les niveaux de mesure (D-063). Elle s'affiche « règle ».
- **Options considérées :**
  1. Élargir `rule` (ce choix).
  2. Une origine nouvelle pour les niveaux de mesure.
- **Justification :** une proposition par le calcul a les mêmes propriétés quelle que soit la règle (déterministe, à accepter par une personne) ; une origine de plus ajouterait un cas sans rien apporter. `computed` reste une valeur acquise, jamais une proposition.
- **Conséquences :** l'export et la page « Noms » écrivent « règle » au lieu de « règle de nommage ». Règles des niveaux (étape 3 de la v0.8) : item d'un groupe d'échelle, étiqueté ou à peu de valeurs entières → ordinal ; option de case à cocher, code étiqueté, ou au plus deux valeurs → nominal ; texte de catégories → nominal ; nombre sans étiquettes → échelle ; au plus 10 entiers sans étiquettes hors groupe → aucune proposition (des codes que seule l'équipe connaît) ; jamais pour un identifiant, un texte libre, une date de naissance, une date, une variable vide ou de types mélangés.

### D-068 — La règle d'une somme avec des items manquants, dans la cotation

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** — (précise D-060)
- **Décision :** une cotation par somme qui accepte des items manquants (nombre minimal d'items répondus inférieur au nombre d'items) dit sa règle pour eux : **somme proportionnelle** (moyenne des items répondus multipliée par le nombre d'items, par défaut) ou **somme des items répondus**. Choisie par l'équipe avec la source de la cotation ; dite dans la phrase de cotation, le contexte d'analyse et appliquée par le script de préparation (`MEAN.k(...) * n` ou `SUM.k(...)` en SPSS, `rowMeans(...) * n` ou `rowSums(...)` en R).
- **Options considérées :**
  1. Un champ de la cotation, somme proportionnelle par défaut (ce choix).
  2. Toujours la somme proportionnelle.
  3. Toujours la somme des items répondus.
- **Justification :** les manuels d'échelles diffèrent ; la règle d'un instrument est une information sourcée, que ni l'outil ni le modèle ne doivent deviner (principe 4). La somme proportionnelle, la plus courante, garde l'étendue du score quel que soit le nombre de réponses.

### D-069 — Périmètre de la v0.9

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la v0.9 ajoute un catalogue d'analyses courantes (Tableau 1, test t, ANOVA, khi-carré, corrélation, régression linéaire, avec leurs versions non paramétriques et leurs tailles d'effet), écrites et testées, calculées dans l'outil, avec un script R équivalent, et une IA conseillère locale et facultative qui aide à les choisir.
- **Options considérées :**
  1. Un catalogue d'analyses calculées dans l'outil (ce choix).
  2. Le même catalogue calculé par R en arrière-plan.
  3. Du code écrit par une IA, locale ou en ligne, vérifié puis exécuté (première version du plan).
- **Justification :** choix de l'auteur, après l'essai de la v0.8 : des analyses toujours les mêmes et toujours justes, sans dépendre d'un modèle, dans l'esprit de l'outil (le calcul déterministe d'abord, l'IA propose, une personne décide) ; rien d'autre à installer pour une équipe qui ne programme pas.
- **Conséquences :** plan en 9 étapes (`docs/plan-v0.9.md`).

### D-070 — Calculer des analyses dans l'outil

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** D-065 en partie
- **Décision :** l'outil calcule les analyses de son catalogue, écrites et testées, sur les données lues en mémoire, les décisions acceptées appliquées ; le fichier d'origine n'est jamais modifié. Il n'exécute jamais de code écrit par une IA.
- **Options considérées :**
  1. Les analyses du catalogue seulement (ce choix).
  2. Aucune analyse dans l'outil (D-065 tel quel).
  3. Le code écrit par une IA, après vérification et approbation.
- **Justification :** le code exécuté est celui de l'outil, vérifié par des tests sur des bases aux effets connus ; le risque d'exécuter un code inconnu disparaît.
- **Conséquences :** D-065 tient pour tout le reste : pas d'exécution de code d'analyse écrit ailleurs ; un assistant d'analyse plus large reste une piste.

### D-071 — Bibliothèques des analyses

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** SciPy et statsmodels (licences BSD) pour le calcul, nouvelles dépendances d'exécution ; Tableau 1 et tailles d'effet calculés dans l'outil ; pour chaque analyse, un script R équivalent (R de base et effectsize) à télécharger, exécuté par le R de l'utilisateur, jamais par l'outil. Les analyses avancées (multiniveaux, équations structurelles, analyses factorielles) viendront plus tard, en Python quand une bibliothèque est assez éprouvée, ou par un moteur R facultatif.
- **Options considérées :**
  1. Calcul en Python, script R équivalent (ce choix).
  2. Calcul par R en arrière-plan (R de base, effectsize, gtsummary).
  3. Calcul par R avec `jmv` (résultats identiques à jamovi).
- **Justification :** choix de l'auteur : tout se fait dans l'outil sans installer R ; R reste la référence pour la reproduction et pour les analyses avancées, d'où le script équivalent et la porte laissée à un moteur R.
- **Conséquences :** les licences sont vérifiées à l'étape 1 et notées dans `docs/dependances.md` ; des tests comparent les résultats de l'outil à ceux du script R, là où R est installé.

### D-072 — Résultats et reproductibilité des analyses

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** les résultats s'affichent dans l'outil ; un rapport et le script R équivalent se téléchargent ensemble, avec l'empreinte du codebook, la date et les versions de l'outil et des bibliothèques ; rien n'est envoyé à un modèle ; les effectifs sous 5 sont signalés.
- **Options considérées :**
  1. Rapport et script ensemble (ce choix).
  2. Résultats affichés seulement.
- **Justification :** une analyse se refait hors de l'outil et se rattache aux décisions sur lesquelles elle repose.

### D-073 — L'IA conseillère des analyses

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** facultative et locale (la règle « Rien ne quitte le poste » reste entière), l'IA reçoit par la porte de confidentialité l'objectif de l'équipe, le catalogue et les variables (libellé, niveau, groupe), et propose des analyses du catalogue et des variables du projet, dans un schéma strict ; elle n'écrit jamais de code ; toute proposition est confirmée, changée ou rejetée par une personne.
- **Options considérées :**
  1. Locale, choix dans le catalogue (ce choix).
  2. Modèles en ligne permis sur option.
  3. Pas d'IA pour les analyses.
- **Justification :** choisir dans une liste est à la portée d'un modèle local, comme pour les rattachements ; un banc le mesurera.

### D-074 — Conditions d'application des analyses

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** une analyse inadaptée selon le codebook (niveau de mesure, nombre de groupes, mesures répétées, identifiant ou texte) est refusée avec sa raison ; une hypothèse fragile (normalité, égalité des variances, petits groupes) est un avertissement, la personne décide.
- **Options considérées :**
  1. Refus et avertissements (ce choix).
  2. Avertissements seulement.
- **Justification :** le codebook sait ce que chaque variable permet ; une analyse juste sur une variable mal choisie reste une erreur.

### D-075 — Bases fictives aux effets connus

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** des bases fictives, générées avec une graine fixe, contiennent des différences, associations et corrélations plantées à l'avance ; chaque analyse du catalogue doit les retrouver, et son script R équivalent aussi.
- **Options considérées :**
  1. Bases aux effets connus (ce choix).
  2. Comparaison avec R seulement.
- **Justification :** le corrigé des analyses, comme celui des rattachements depuis la v0.2.

### D-076 — Reportés après la v0.9

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** sont reportés : les modèles en ligne, l'exécution de code écrit par une IA, la base synthétique, le vérificateur de scripts, les analyses avancées (multiniveaux, équations structurelles, analyses factorielles) et les filtres du questionnaire.
- **Options considérées :** sans objet.
- **Justification :** garder la v0.9 centrée sur un catalogue juste et utile seul.

### D-077 — Le script R équivalent en R de base ; conventions du catalogue d'analyses

- **Date :** 2026-10-15
- **Statut :** adoptée
- **Remplace :** — (précise D-071)
- **Décision :** le script R équivalent de chaque analyse est écrit en R de base, avec `haven` pour lire la base, sans `effectsize` : les tailles d'effet y sont calculées par les mêmes formules que l'outil. Le catalogue (`docs/catalogue-analyses.md`) est validé : six analyses (Tableau 1, test t, ANOVA, khi-carré, corrélation, régression linéaire) et leurs options, Welch par défaut ; p sans zéro initial (style APA) ; une phrase de résultat qui décrit sans juger (pas de « significatif ») ; d et r avec leur intervalle de confiance, V, η², ω², ε² et corrélation bisériale de rang sans intervalle ; seuils : 2 personnes par groupe au minimum, signalement sous 5, 20 % d'effectifs attendus sous 5, 10 observations par prédicteur, VIF supérieur à 5.
- **Options considérées :**
  1. R de base seulement (ce choix).
  2. R de base et `effectsize`, comme D-071 le prévoyait.
- **Justification :** `effectsize` n'est pas installé chez l'auteur ; un script sans dépendance se refait sur tout poste où R et `haven` sont installés, et ses formules sont lisibles. Conventions et seuils validés par l'auteur à la fin de l'étape 1.

### D-078 — Seule la dernière analyse est gardée, en mémoire

- **Date :** 2026-10-16
- **Statut :** adoptée
- **Remplace :** —
- **Décision :** la page « Analyses » ne garde que la dernière analyse lancée, en mémoire, le temps de la séance ; le projet n'enregistre ni résultat ni historique des analyses. L'équipe conserve les rapports qu'elle écrit à côté du projet ou télécharge : un rapport Markdown, ses tableaux en Excel, et un fichier `.zip` qui contient le script R équivalent avec le fichier de commandes et le script de préparation qu'il exécute. Écrits à côté du projet, les fichiers d'une analyse portent le premier numéro libre (`<projet>-analyse-<n>`).
- **Options considérées :**
  1. Dernière analyse en mémoire seulement (ce choix).
  2. Un historique des analyses dans le projet.
- **Justification :** le projet reste un dictionnaire de données, qui ne garde que des agrégats et des décisions (règle 2) ; des résultats calculés sur les données n'y ont pas leur place. Un historique pourra venir plus tard si le besoin se présente.

### D-079 — L'IA conseillère : l'objectif envoyé tel quel, les propositions en mémoire

- **Date :** 2026-10-16
- **Statut :** adoptée
- **Remplace :** — (précise D-073)
- **Décision :** l'objectif d'analyse écrit par l'équipe est envoyé tel quel au modèle local, avec le catalogue et la liste des variables utilisables (nom final, libellé, niveau de mesure, groupe), sans aucune donnée ni statistique ; identifiants, textes libres et dates en sont exclus, comme des analyses. Une mise en garde demande de n'écrire aucune donnée de participant dans l'objectif, limité à 1 000 caractères. Les propositions du modèle restent en mémoire, comme les résultats (D-078), et ne sont pas enregistrées dans le projet ; le message envoyé et la réponse reçue sont gardés dans le dossier des envois à côté du projet, comme pour les autres usages de l'IA.
- **Options considérées :**
  1. Objectif envoyé tel quel, propositions en mémoire, échange gardé (ce choix).
  2. Propositions enregistrées dans le projet, avec les autres exécutions de l'IA.
- **Justification :** l'objectif est un texte de l'équipe, non une donnée de participant ; c'est toutefois le premier texte libre envoyé tel quel, d'où la mise en garde et la trace complète de l'échange. Garder les propositions hors du projet le laisse un dictionnaire de données.
