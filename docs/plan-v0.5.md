# Plan de la v0.5

> Statut : **validé par l'auteur le 2026-10-14**, avec macOS seulement (pas Linux) et toutes les autres recommandations du § 6 (D-031 à D-036).

## 1. Pourquoi cette version

L'outil est pensé pour des équipes francophones, sous Windows. Deux limites reviennent :

- **Les équipes québécoises sont souvent bilingues.** Une partie des personnes (étudiantes, collaborateurs hors Québec, équipes des universités anglophones) travaille en anglais, et certaines études ont un questionnaire en anglais. Aujourd'hui, l'interface, le codebook, le guide, la lecture du questionnaire et les consignes au modèle ne sont qu'en français.
- **Beaucoup de chercheurs travaillent sur un Mac.** L'outil y fonctionne déjà en ligne de commande, mais il n'a ni installateur ni icône, et rien n'y a été essayé.

## 2. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Interface en anglais** : toutes les pages, les messages et la ligne de commande, au choix de la personne sur l'accueil | Une personne anglophone utilise l'outil sans aide |
| B | **Codebook en anglais** : en-têtes, notes, provenance, rapport et commentaires des fichiers de commandes, au choix à l'export | Un codebook à partager avec une équipe ou une revue anglophone, même si l'interface est en français |
| C | **Matériel en anglais** : un questionnaire en anglais est découpé et ses sigles repérés (« cognitive behavioural therapy (CBT) »), et le modèle propose les libellés dans la langue du projet | Une étude menée en anglais est documentée en anglais |
| D | **macOS** : un installateur par double-clic, une icône pour ouvrir l'outil, un désinstallateur | Les équipes sur Mac installent l'outil comme sous Windows |
| E | **Guides en anglais et pour macOS** | Chaque personne a un guide pas à pas pour son système et sa langue |

**Deux langues distinctes** : la langue de l'**interface** est un choix de la personne, gardé sur son ordinateur ; la langue du **projet** (celle du questionnaire et des libellés) est un choix de l'équipe, gardé dans le fichier projet (le champ `settings.language` existe déjà). On peut ainsi travailler dans une interface en français sur une étude menée en anglais.

**Reportés** : Linux (l'outil y fonctionne en ligne de commande, sans installateur) ; export DDI Codebook et Frictionless, dictionnaire REDCap ; autres langues que le français et l'anglais.

## 3. Conception

### 3.1 Interface en anglais (A)

- Les textes de l'interface sont déjà marqués pour la traduction (gettext, D-004) : environ 520 phrases. La traduction anglaise est écrite dans un fichier `.po`, compilé en `.mo` et livré avec l'outil.
- **Choix de la langue** : un sélecteur « Français / English » sur l'accueil, gardé dans le dossier de réglages de l'ordinateur (là où sont les projets récents). La variable `DDICT_LANG` le remplace pour la ligne de commande et les essais.
- Plusieurs textes sont aujourd'hui traduits une seule fois, au démarrage (les noms de types, de statuts, d'origines). Ils seront traduits au moment de l'affichage, pour que le changement de langue s'applique sans relancer l'outil.
- **Test** : chaque phrase marquée a sa traduction ; une page parcourue en anglais ne montre aucun texte français (hors données de l'équipe).
- La traduction est écrite par l'assistant ; **une personne anglophone la relit** avant la version (D-034).

### 3.2 Codebook en anglais (B)

- La page « Export » et `ddict exporter --langue en` choisissent la langue du codebook, par défaut celle de l'interface. Elle s'applique aux en-têtes, aux noms des onglets, aux notes calculées (« Code 999 confirmé comme manquant par l'équipe »), à la provenance, au rapport Markdown et aux commentaires des fichiers de commandes.
- Les valeurs de l'équipe (libellés, descriptions, texte des questions) ne sont jamais traduites : elles restent dans la langue où elles ont été écrites.

### 3.3 Matériel en anglais (C)

- **Langue du projet** : proposée à la création d'après la base et le questionnaire, modifiable sur la page « Base ».
- **Questionnaire** : le découpage reconnaît les formes anglaises (« Check all that apply », « If yes, … », « Select one »), et le glossaire les définitions anglaises (« cognitive behavioural therapy (CBT) »).
- **Consignes au modèle** : des versions anglaises des prompts (`link-v2.en`, `variables-v3.en`), choisies selon la langue du projet ; les signaux d'invention reconnaissent les formes anglaises (« according to Smith (2019) », « cut-off of 16 »).
- **Base fictive anglaise** : une version anglaise de l'étude sur le sommeil (questionnaire et étiquettes), générée par script avec son corrigé, pour les tests et le banc d'essai.

### 3.4 macOS (D)

- **Installateur** : `installer.command` (double-clic sous macOS), qui fait ce que fait `installer.bat` : uv, l'outil avec ses options, une icône (une petite application dans le dossier Applications de l'utilisateur), la vérification d'Ollama, l'outil ouvert fermé avant une mise à jour. `desinstaller.command`.
- **Ce qui dépend du système**, déjà prévu en partie : dossier de réglages (`~/Library/Application Support/ddict`), fenêtre « Ouvrir » (tkinter), ouverture du dossier (`open`).
- **Vérification** : le poste de développement n'a pas de Mac. Les tests passeront sous macOS dans **GitHub Actions**, avec un essai de l'installateur (installation, `ddict --version`, l'interface qui répond). Le dépôt étant privé, les minutes macOS coûtent dix fois plus que celles de Windows ou Linux : l'essai macOS est lancé à la demande (D-035). Un **essai réel sur un Mac**, par une personne qui en a un, est demandé avant la version.
- **Ollama** existe pour macOS et Linux ; sur un Mac à puce Apple, le modèle tourne sur la puce, sans carte graphique : le banc d'essai le mesurera.

### 3.5 Guides (E)

- `docs/installation-windows.md` reste le guide de référence, en français. S'y ajoutent `docs/installation-macos.md` (français) et les deux guides en anglais (`docs/en/…`).
- La documentation technique (conception, journal des décisions, plans) reste en français.

## 4. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Langue de l'interface : fichiers de traduction, choix sur l'accueil, textes traduits à l'affichage | Changer de langue sur l'accueil change toute l'interface sans relancer l'outil (test) |
| 2 | Traduction anglaise de l'interface et de la ligne de commande | Chaque phrase a sa traduction ; parcours en anglais sans texte français (test) |
| 3 | Codebook, rapport et fichiers de commandes en anglais | Codebook anglais de la base fictive, comparé à un fichier de référence |
| 4 | Langue du projet ; base fictive et questionnaire anglais ; découpage et glossaire en anglais | Le questionnaire anglais donne les mêmes questions que le français ; sigles anglais repérés (tests) |
| 5 | Prompts anglais et signaux d'invention en anglais | Banc d'essai sur la base anglaise, consigné dans `docs/essais/` |
| 6 | Installateur et désinstallateur macOS ; tests dans GitHub Actions | Tests et essai de l'installateur réussis sous macOS (Actions) |
| 7 | Guide macOS, guides anglais | Relus ; liens entre les guides |
| 8 | Relecture de la traduction, essai sur un Mac, version 0.5.0 | Traduction relue par une personne anglophone ; guide macOS suivi sur un vrai Mac |

## 5. Risques

- **Qualité de la traduction** : une interface mal traduite fait plus de tort qu'une interface en français. D'où la relecture par une personne anglophone (étape 8), et un glossaire des termes (codebook, missing code, value label…) fixé dès l'étape 2.
- **macOS sans Mac** : Actions vérifie que l'outil s'installe et démarre, pas que l'icône, la fenêtre « Ouvrir » ou les avertissements de sécurité de macOS (Gatekeeper, « développeur non identifié ») se comportent bien. L'essai réel sur un Mac reste nécessaire ; s'il n'est pas possible, macOS sera publié comme « à l'essai ».
- **Coût des minutes Actions** sur un dépôt privé, surtout macOS : essai macOS à la demande seulement.
- **Modèle en anglais** : qwen2.5 est meilleur en anglais qu'en français ; le banc d'essai le dira, et la recommandation de modèle pourra différer selon la langue.
- **Taille de la version** : si elle s'avère trop grande, les étapes 4 et 5 (matériel en anglais) peuvent passer à la v0.6 sans toucher au reste.

## 6. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-031 | **Périmètre de la v0.5** | A à E, avec macOS seulement (choix de l'auteur : Linux reporté) ; DDI, Frictionless et REDCap reportés ; seulement le français et l'anglais. |
| D-032 | **Deux langues distinctes** | Langue de l'interface choisie par la personne et gardée sur l'ordinateur ; langue du projet choisie par l'équipe et gardée dans le fichier projet. Les valeurs de l'équipe ne sont jamais traduites. |
| D-033 | **Outils de traduction** | Babel (BSD-3), pour le développement seulement, extrait les phrases et compile le `.mo` ; l'outil n'utilise à l'exécution que `gettext`, de la bibliothèque standard. Le `.mo` compilé est gardé dans le dépôt, avec un test qui vérifie qu'il est à jour. |
| D-034 | **Relecture de la traduction** | L'assistant traduit ; une personne anglophone relit avant la version. Sans relecture, l'anglais est publié comme « à l'essai ». |
| D-035 | **Essais macOS** | Tests et essai de l'installateur dans GitHub Actions, macOS à la demande pour limiter les minutes ; essai réel sur un Mac par une personne qui en a un. |
| D-036 | **Langue de la documentation** | Guides en français et en anglais ; documentation technique (conception, décisions, plans, essais) en français seulement. |
