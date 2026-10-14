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
