# Conception — outil de dictionnaire de données assisté par IA locale

> Document de conception, version de travail du 2026-10-13. « dictionnaire-donnees » est un nom de travail (voir § 11).
> Rien n'est encore codé. Ce document est à valider avant d'initialiser Git ou d'écrire du code.

---

## 1. Vision

Une équipe de recherche reçoit ou hérite d'une base de données (souvent un `.sav` de SPSS, parfois un `.csv` exporté d'Excel ou de LimeSurvey) et doit en produire le **dictionnaire de données** : ce que contient chaque variable, comment elle est codée, quelles valeurs signifient « manquant », quels items forment une échelle, lesquels sont inversés.

Ce travail est long, répétitif et sujet à l'erreur. L'outil le découpe en deux couches :

1. **Une couche déterministe**, qui calcule et extrait exactement tout ce qui peut l'être (types, manquants, étendues observées, modalités, étiquettes déjà présentes dans le fichier, anomalies de codage). À elle seule, elle produit un dictionnaire utile.
2. **Une couche d'IA locale, facultative**, qui propose ce qui demande de l'interprétation : libellés lisibles, descriptions, regroupements probables en échelles, signalement d'incohérences. Chaque proposition attend une décision humaine.

Le produit final est un codebook Excel et un rapport Markdown, plus un fichier projet qui permet de reprendre le travail.

## 2. Public

- Coordonnateurs et coordonnatrices de recherche, assistants et assistantes de recherche, étudiants et étudiantes aux cycles supérieurs.
- **Pas développeurs** : l'installation et l'utilisation doivent être guidées pas à pas, en français.
- Sous **Windows** surtout, avec ou sans carte graphique ; macOS et Linux doivent fonctionner aussi.
- Souvent soumis à des exigences éthiques (EPTC 2, Loi 25 au Québec) : la confidentialité n'est pas une option.

## 3. Principes non négociables

1. **Le déterministe d'abord.** Tout ce qui se calcule exactement se calcule sans IA : type, valeurs manquantes, min/max, modalités observées, cardinalité, étiquettes de variables et de valeurs déjà présentes dans le fichier.
2. **L'IA est optionnelle.** L'outil est pleinement utile sans modèle ni GPU. L'IA ajoute une couche d'enrichissement.
3. **Toute production de l'IA est une proposition.** Chaque champ suggéré porte un statut (« proposé par IA », « validé », « corrigé », « rejeté ») et la trace du modèle utilisé. Rien n'est accepté sans action humaine.
4. **Aucune invention.** Le modèle n'a jamais le droit de proposer un seuil clinique, une étendue théorique, une référence bibliographique ou un nom d'instrument présenté comme certain. Ces champs restent vides tant qu'une source n'est pas documentée par l'utilisateur. Un seuil sans origine documentée n'a pas le droit d'exister.
5. **Confidentialité par conception.** Rien ne quitte le poste. Le modèle ne reçoit jamais de données brutes individuelles : seulement des métadonnées et des statistiques agrégées. Les colonnes de texte libre et les identifiants probables ne transmettent aucune valeur au modèle.
6. **Neutralité du moteur.** L'IA passe par une API compatible OpenAI configurable (Ollama, LM Studio, serveur llama.cpp).
7. **Aucune donnée réelle dans le dépôt.** Exemples et tests utilisent des bases fictives générées par script.

### Comment le code garantit ces principes (et pas seulement la bonne volonté)

| Principe | Garantie technique |
|---|---|
| 1 | Le profilage ne dépend d'aucun module d'IA ; les tests du profilage tournent sans client IA installé. |
| 2 | Chaîne complète « lire → profiler → exporter » testée sans IA ; le module IA est une dépendance facultative (`pip install ...[ia]`). |
| 3 | Un champ d'origine `ai` ne peut avoir que le statut `proposed` à sa création ; l'export final n'inclut que les valeurs validées ou corrigées. |
| 4 | Les schémas de réponse du modèle **n'ont pas** de champ pour un seuil, une étendue théorique, une référence ou un nom d'instrument (`extra="forbid"` : tout champ imprévu fait rejeter la réponse). Côté humain, ces champs exigent une source non vide pour être enregistrés. Un filtre signale en plus tout texte proposé qui ressemble à une citation (« Auteur, 2003 ») ou à un seuil (« ≥ 14 », « cut-off »). |
| 5 | Tout ce qui part vers le modèle passe par **une seule fonction** (une « porte de confidentialité ») qui construit le message à partir du profil agrégé, jamais à partir du tableau de données. Le client refuse toute adresse qui n'est pas locale (`127.0.0.1`, `localhost`, `::1`). Des tests à « chaînes témoins » le vérifient (§ 9). |
| 6 | Un seul client HTTP générique, configuré par une adresse et un nom de modèle ; aucune bibliothèque propre à un fournisseur. |
| 7 | Les bases de test sont produites par `scripts/generer_bases_fictives.py` avec une graine fixe ; `.gitignore` exclut `*.sav`, `*.csv`, `*.xlsx` hors de `exemples/`. |

## 4. Architecture

```
            ┌──────────┐   ┌───────────┐   ┌──────────────┐
 .sav/.csv →│ lecture  │ → │ profilage │ → │  regroupement │ (déterministe)
            └──────────┘   └───────────┘   └──────┬───────┘
                                                  │ profil agrégé seulement
                                     ┌────────────▼────────────┐
                                     │ porte de confidentialité │
                                     └────────────┬────────────┘
                                                  │ (facultatif)
                                     ┌────────────▼────────────┐
                                     │ enrichissement IA (local)│
                                     └────────────┬────────────┘
                                                  ▼
                      fichier projet JSON ⇄ révision (Streamlit) → export .xlsx / .md
```

Les données brutes ne sortent jamais du module de lecture et du module de profilage : les autres modules ne voient que le **profil** (métadonnées et agrégats).

| Module | Rôle | Entrée → sortie |
|---|---|---|
| `io` (lecture) | Lire `.sav` (pyreadstat : étiquettes de variables et de valeurs, manquants déclarés, niveau de mesure, formats) et `.csv` (détection de l'encodage, du séparateur `,` ou `;` et de la virgule décimale, fréquents dans les CSV d'Excel en français). | fichier → tableau + métadonnées du fichier |
| `profile` (profilage) | Calculer, pour chaque variable, toutes les statistiques déterministes (§ 5.2) et les anomalies de codage. | tableau + métadonnées → profil |
| `privacy` (confidentialité) | Classer les variables (texte libre, identifiant probable, date, quasi-identifiant) ; masquer les petits effectifs ; construire la vue agrégée autorisée pour l'IA et pour l'export. | profil → vue filtrée |
| `groups` (regroupement) | Proposer des groupes déterministes : préfixe commun (`bdi_1`…`bdi_21`), même jeu d'étiquettes de valeurs, contiguïté ; calculer pour chaque groupe les corrélations item-total (signe négatif → item inversé probable). | profil + tableau → groupes candidats |
| `llm` (enrichissement) | Construire les messages par petits blocs, appeler le serveur local, valider la réponse (pydantic), enregistrer la trace. | vue filtrée → propositions |
| `project` (projet) | Modèle de données, statuts, sauvegarde et chargement du fichier projet JSON, versions du schéma. | — |
| `review` (révision) | Interface Streamlit : parcourir les variables et les groupes, accepter, corriger, rejeter ; saisir les champs humains avec leur source. Logique dans `project`, interface mince. | projet → projet |
| `export` | Codebook `.xlsx` (openpyxl) et rapport `.md`. | projet → fichiers |
| `cli` | Commandes : `profiler`, `enrichir`, `reviser`, `exporter`. | — |

Les corrélations item-total du module `groups` sont un point délicat : elles demandent le tableau de données, donc elles sont calculées **avant** la porte de confidentialité, dans la couche déterministe ; seul leur signe (et leur valeur arrondie) va plus loin.

## 5. Modèle de données

### 5.1 Une valeur suivie

Tout champ susceptible d'être modifié est enregistré avec sa provenance :

```json
{
  "value": "Satisfaction à l'égard du sommeil",
  "origin": "ai",
  "status": "corrected",
  "proposed_value": "Satisfaction du sommeil",
  "ai_run": "run-0003",
  "source": null,
  "updated_at": "2026-10-13T14:02:11"
}
```

- `origin` : `file` (lu dans le fichier), `computed` (calculé), `ai` (proposé par le modèle), `questionnaire` (v0.2 : tiré du questionnaire sous une règle stricte, et comme `ai` seulement proposé tant qu'une personne ne l'a pas accepté), `human` (saisi par une personne).
- `status` : `none` (valeur de fichier ou de calcul, rien à décider), `proposed`, `validated`, `corrected`, `rejected`.
- `proposed_value` : la valeur d'origine conservée quand une personne la corrige (on peut toujours voir ce que l'IA ou le fichier disait).
- `ai_run` : renvoie à la trace de l'appel (modèle, paramètres, version du prompt).
- `source` : obligatoire pour les champs « sourcés » (§ 5.3).

Statuts affichés : `proposed` = « proposé par IA », `validated` = « validé », `corrected` = « corrigé », `rejected` = « rejeté ».

### 5.2 Une entrée du dictionnaire (une variable)

| Champ | Description | Origine |
|---|---|---|
| `name` | Nom de la variable | fichier |
| `position` | Rang dans le fichier | fichier |
| `storage_type` | Type de stockage (numérique, chaîne, largeur) | fichier |
| `spss_format` | Format d'affichage SPSS (`F8.2`, `A50`, `DATE11`…) | fichier (.sav) |
| `measure_level` | Niveau de mesure déclaré (nominal, ordinal, échelle) | fichier (.sav) |
| `file_label` | Étiquette de variable présente dans le fichier | fichier (.sav, .dta, .sas7bdat) |
| `value_labels` | Étiquettes de valeurs présentes dans le fichier | fichier (.sav, .dta) |
| `declared_missing` | Valeurs ou plages manquantes déclarées par l'utilisateur dans SPSS | fichier (.sav) |
| `missing_tokens` | Jetons de valeur manquante d'un CSV (`NA`, `#N/A`…) lus comme vides, avec leur nombre (D-010) | fichier (.csv) |
| `inferred_type` | Type déduit : entier, décimal, booléen, catégoriel, date, date-heure, texte court, texte libre | calcul |
| `n_rows`, `n_valid`, `n_system_missing`, `n_declared_missing`, `pct_missing` | Décomptes | calcul |
| `n_distinct` | Cardinalité | calcul |
| `min`, `max`, `mean`, `sd`, `median`, `q1`, `q3` | Pour les numériques | calcul |
| `date_min`, `date_max` | Pour les dates | calcul |
| `length_min`, `length_max` | Pour les textes (longueur, jamais le contenu) | calcul |
| `observed_values` | Modalités observées et effectifs, si cardinalité ≤ seuil (20 par défaut) ; effectifs < 5 affichés « < 5 » | calcul |
| `unlabeled_codes` | Valeurs observées sans étiquette alors que la variable en a | calcul |
| `unused_labels` | Étiquettes sans aucune observation | calcul |
| `suspect_missing_codes` | Valeurs sentinelles probables non déclarées (`-9`, `99`, `999`, `-1`…, isolées loin du reste) | calcul |
| `flags` | Constante, quasi constante, entièrement manquante, types mélangés, doublon de colonne | calcul |
| (signal) variantes d'écriture | Catégories visibles d'une variable de texte qui ne diffèrent que par la casse, les accents ou les espaces (v0.2) ; calculées à l'affichage à partir des catégories visibles, jamais des données, donc sans révéler une catégorie masquée | calcul |
| `privacy_class` | `free_text`, `likely_identifier`, `quasi_identifier`, `date_of_birth_like`, `ordinary`, avec les raisons | calcul, confirmé par un humain |
| `group_id` | Groupe (échelle ou instrument probable) | calcul ou IA, validé par un humain |
| `item_total_r` | Corrélation item-total dans le groupe (arrondie) | calcul |
| `reverse_suspect` | Item inversé probable, avec la raison (corrélation négative, libellé) | calcul et/ou IA |
| `question` | Question d'où vient la variable (v0.2, D-013) : identifiant `Q8`, `Q7.r3` (énoncé de grille), `Q10.o2` (option) ou `none` ; le texte affiché est toujours lu dans le questionnaire | IA ou humain (valeur suivie), à partir des candidates calculées |
| `value_labels` | Étiquettes de valeurs tirées des options de la question rattachée, quand le fichier n'en a pas, sous la règle stricte de D-016 ; mention « ordre supposé, à vérifier » | questionnaire (proposition), validé par un humain |
| `label` | Libellé lisible final | fichier, IA ou humain (valeur suivie) |
| `description` | Description en une ou deux phrases | IA ou humain (valeur suivie) |
| `ai_notes` | Incohérences signalées par l'IA (texte court, statut propre) | IA (valeur suivie) |
| `unit` | Unité (ans, minutes, $…) | humain (ou IA proposée) |
| `theoretical_range` | Étendue théorique de l'échelle | **humain seulement, source obligatoire** |
| `thresholds` | Seuils cliniques : liste de `{valeur, signification, source}` | **humain seulement, source obligatoire** |
| `references` | Références bibliographiques | **humain seulement** |
| `notes` | Notes libres de l'équipe | humain |

### 5.3 Un groupe (échelle ou instrument probable)

| Champ | Description | Origine |
|---|---|---|
| `group_id` | Identifiant | calcul |
| `members` | Variables du groupe, dans l'ordre | calcul ou IA, validé par un humain |
| `basis` | Raisons du regroupement (préfixe, jeu d'étiquettes commun, contiguïté, proposition IA) | calcul / IA |
| `descriptive_label` | Libellé descriptif neutre (« 21 items, réponses 0-3, préfixe bdi ») | calcul ou IA |
| `ai_hypothesis` | Hypothèse de l'IA sur ce que mesure le groupe, **toujours affichée comme hypothèse** et jamais recopiée automatiquement dans `instrument_name` | IA (valeur suivie) |
| `instrument_name` | Nom de l'instrument | **humain seulement, source obligatoire** |
| `reverse_items` | Items inversés confirmés | humain (à partir des signaux) |
| `scoring` | Règle de calcul du score, `theoretical_range`, `thresholds` | **humain seulement, source obligatoire** |
| `cronbach_alpha` | Cohérence interne observée, à titre indicatif | calcul |

### 5.4 Le fichier projet

Un seul fichier JSON (`mon-projet.dd.json`), écrit de façon déterministe (clés dans un ordre fixe, indentation 2, UTF-8, fins de ligne LF) pour qu'il se compare bien d'une version à l'autre :

- `schema_version` ;
- `source` : nom du fichier, empreinte SHA-256, nombre de lignes et de colonnes (pour détecter qu'on rouvre le projet avec une base modifiée) — **jamais les données** ;
- `settings` : seuils (cardinalité, petits effectifs), langue ;
- `variables` (§ 5.2) et `groups` (§ 5.3) ;
- `ai_runs` : pour chaque passage de l'IA, l'adresse du serveur, le nom exact du modèle, les paramètres (température, graine), la version du prompt, l'empreinte du message envoyé, la date, le résultat (réussi, réponse invalide, refusé) ;
- `questionnaire` (v0.2, D-012) : nom et empreinte du questionnaire de l'étude, ses questions découpées (identifiant `Q7`, page, texte exact, type, options, lignes de grille, points à vérifier) et ses autres paragraphes ; absent tant qu'aucun questionnaire n'a été lu.
- `glossary` (v0.2, D-015) : sigles et leur définition, chacun avec son origine (questionnaire ou équipe, jamais l'IA), son statut (à valider, validé, corrigé, rejeté) et l'endroit du questionnaire où il est défini.

Le fichier projet ne contient aucune valeur individuelle : seulement des métadonnées et des agrégats, avec les petits effectifs masqués. Il reste néanmoins à traiter comme un document de recherche (les étiquettes et les étendues peuvent être sensibles).

Le texte exact envoyé au modèle est conservé à côté, dans `mon-projet.dd-envois/` : chacun peut vérifier ce qui a été transmis.

## 6. Ce qui est envoyé au modèle

### 6.1 Contenu autorisé et contenu exclu

| Envoyé | Jamais envoyé |
|---|---|
| Nom de la variable et ses voisines immédiates (contexte) | Toute ligne ou valeur individuelle |
| Étiquette de variable du fichier | Toute valeur d'une colonne de texte libre (ni extrait, ni exemple) |
| Étiquettes de valeurs | Toute valeur d'un identifiant probable (seulement son nom et « identifiant probable ») |
| Type déduit, niveau de mesure | Les effectifs inférieurs au seuil (remplacés par « < 5 ») |
| Pourcentage de manquants, cardinalité | Les dates exactes (seulement l'année pour les étendues de dates) |
| Min, max, moyenne arrondis (numériques non sensibles) | Le chemin et le nom du fichier source |
| Codes observés et proportions arrondies (catégorielles) | Les notes internes de l'équipe |
| Anomalies calculées (codes sans étiquette, sentinelles probables, signe de la corrélation item-total) | — |

Les variables classées comme quasi-identifiants (code postal, date de naissance, âge exact très élevé, etc.) n'envoient que leur nom, leur étiquette et leur type.

### 6.2 Découpage

- **Libellés, descriptions, incohérences** : blocs de 10 à 15 variables consécutives (réglable), pour tenir dans le contexte d'un modèle de 7-8 milliards de paramètres quantifié et limiter les erreurs.
- **v0.2, prompt `variables-v3`** : blocs de 8 variables par défaut (`--taille-bloc`), pour laisser à la réponse sa place dans les 4 096 jetons d'Ollama. Chaque variable dont le rattachement est accepté par une personne reçoit le texte exact de sa question (`question.text`, et `question.item` pour un énoncé ou une option) ; le bloc reçoit les sigles acceptés du glossaire qui le concernent (`glossary`). Un rattachement seulement proposé n'est pas transmis. Une proposition qui donne le sens d'un sigle absent du glossaire est signalée (essai : `docs/essais/2026-10-14-prompt-v3.md`).
- **Regroupement** : le module `groups` propose d'abord des candidats déterministes ; l'IA reçoit ensuite, groupe candidat par groupe candidat, la liste compacte des noms et étiquettes, et répond « garder, scinder, fusionner avec le voisin » plus une hypothèse.

### 6.3 Exemple de message (bloc de variables)

Message système (fixe, versionné dans le dépôt sous `src/.../llm/prompts/`, avec un numéro de version) :

```
Tu aides une équipe de recherche à documenter une base de données.
Tu reçois des métadonnées et des statistiques agrégées, jamais de données individuelles.
Pour chaque variable, propose un libellé court en français et une description d'une phrase,
et signale les incohérences de codage visibles dans les statistiques fournies.
Règles :
- N'invente jamais de seuil clinique, d'étendue théorique, de référence ou de nom d'instrument.
- Si l'information ne permet pas de conclure, laisse le champ vide.
- Réponds uniquement en JSON, selon le schéma fourni.
```

Message utilisateur :

```json
{
  "block": "b-004",
  "variables": [
    {
      "name": "sommeil_q3",
      "neighbors": ["sommeil_q2", "sommeil_q4"],
      "file_label": "Q3 satisf sommeil",
      "type": "ordinal",
      "value_labels": {"1": "Pas du tout", "2": "Un peu", "3": "Moyennement", "4": "Beaucoup", "5": "Extrêmement"},
      "observed": {"1": 0.08, "2": 0.21, "3": 0.33, "4": 0.27, "5": 0.09, "9": "< 5"},
      "pct_missing": 2.1,
      "anomalies": ["code 9 observé sans étiquette", "corrélation item-total négative"]
    },
    {
      "name": "commentaire_fin",
      "file_label": "Commentaires",
      "type": "free_text",
      "note": "texte libre : aucune valeur transmise"
    }
  ]
}
```

Réponse attendue (contrainte par le schéma JSON, transmise au serveur par `response_format`) :

```json
{
  "block": "b-004",
  "variables": [
    {
      "name": "sommeil_q3",
      "label": "Satisfaction à l'égard du sommeil",
      "description": "Degré de satisfaction de la personne répondante à l'égard de son sommeil, sur une échelle de 1 à 5.",
      "issues": ["Le code 9 n'a pas d'étiquette : valeur manquante possible à déclarer.",
                 "Corrélation négative avec le reste du groupe : item possiblement inversé."]
    },
    {
      "name": "commentaire_fin",
      "label": "Commentaires libres de fin de questionnaire",
      "description": "",
      "issues": []
    }
  ]
}
```

### 6.4 Validation de la réponse

1. Le JSON doit correspondre exactement au schéma pydantic (aucun champ en trop).
2. Les noms de variables retournés doivent être exactement ceux envoyés (ni oubli, ni variable inventée).
3. Longueurs bornées (libellé ≤ 80 caractères, description ≤ 300).
4. Filtre « aucune invention » : tout texte qui ressemble à une citation, à un seuil ou à un nom d'instrument présenté comme certain est **signalé** dans l'interface (il reste une proposition que la personne peut rejeter).
5. En cas d'échec : un nouvel essai, puis le bloc est marqué « échec » dans `ai_runs`. Aucune réponse partielle n'est acceptée.

Paramètres par défaut : température 0, graine fixe. Même ainsi, un modèle local n'est pas parfaitement reproductible ; d'où la trace complète dans `ai_runs`.

Avant tout envoi, la commande `enrichir --apercu` affiche les messages qui partiraient, sans rien envoyer.

### 6.5 Rattachement aux questions (v0.2, D-013)

La commande `rattacher` envoie un second type de message (prompt `link-v1`), par blocs de 6 variables : pour chaque variable, son nom, son étiquette, ses étiquettes de valeurs et **ses 5 questions candidates au plus**, calculées sans IA (mots du nom et de l'étiquette, sens des sigles acceptés du glossaire, séries numérotées, familles de noms, ordre du questionnaire). Jamais le questionnaire entier ni ses paragraphes (page de consentement). Le modèle répond pour chaque variable par un identifiant de sa liste, « aucune » ou « incertain » ; tout autre identifiant, ou tout champ de texte, fait refuser le bloc entier. Sans `--modele`, la commande indique seulement combien de variables ont des candidates : le choix se fait dans l'interface.

## 7. Révision (Streamlit)

- Liste des variables avec filtres : « à réviser », « anomalies », « texte libre / identifiants », par groupe.
- Fiche d'une variable : ce que dit le fichier, ce qui a été calculé, ce que propose l'IA (en couleur distincte, avec le modèle utilisé), et trois boutons : accepter, corriger, rejeter.
- Champs sourcés (étendue théorique, seuils, nom d'instrument, références) : la sauvegarde est impossible sans source.
- Question du questionnaire (v0.2) : le rattachement proposé s'accepte ou se rejette ; une liste, candidates en tête, permet d'en choisir un autre ou « aucune question ». Filtre « Sans question ».
- Sauvegarde automatique du fichier projet à chaque décision.
- Configuration imposée au lancement : écoute sur `127.0.0.1` seulement (par défaut, Streamlit écoute sur toutes les interfaces, donc serait visible sur le réseau local) et **télémétrie de Streamlit désactivée** (`browser.gatherUsageStats = false`, activée par défaut sinon).

La logique (changer un statut, valider une source) vit dans `project` et se teste sans Streamlit ; l'interface reste mince, ce qui permettrait de la remplacer plus tard sans tout réécrire.

## 8. Exports

- **Codebook `.xlsx`** : un onglet « Variables » (une ligne par variable), un onglet « Valeurs » (une ligne par code et étiquette), un onglet « Groupes », un onglet « Provenance » (statut et origine de chaque champ, modèles utilisés). En-têtes figés, filtres activés.
- **Rapport `.md`** : vue d'ensemble (nombre de variables, manquants, anomalies), puis une section par groupe et par variable.
- **Export final** (par défaut) : seulement les valeurs de fichier, de calcul, validées ou corrigées. **Export de travail** (option) : inclut les propositions en attente, marquées « proposé par IA ».
- Les effectifs inférieurs au seuil sont masqués aussi dans les exports, puisqu'un codebook est souvent partagé ou déposé avec les données.
- **Questionnaire (v0.2)** : pour chaque variable dont le rattachement est accepté, la référence (`Q7.r3, p. 3`) et le texte exact de la question et de l'énoncé ou de l'option, lu dans le questionnaire ; rien d'autre du questionnaire n'est exporté (page de consentement, consignes : D-012). L'onglet « Informations » donne le nom, le nombre de pages et l'empreinte du questionnaire. Un onglet « Glossaire » (et une section du rapport) donne les sigles acceptés, avec leur origine. L'onglet « Valeurs » dit d'où viennent les étiquettes tirées du questionnaire (D-016). **D-014** : le texte des questions d'un groupe peut être omis, par une case à cocher dans la vue « Groupes » (enregistrée dans le projet) ou pour un export seulement (`ddict exporter --sans-texte G3`) ; la référence de la question reste.

## 9. Stratégie de tests

- **Bases fictives générées par script**, avec une graine fixe, contenant volontairement des pièges : items inversés, codes 99 et -9 non déclarés, étiquettes inutilisées, identifiant, courriels et noms fictifs dans une colonne de texte libre, date de naissance, variable constante, CSV en Windows-1252 avec `;` et virgule décimale, échelle dont les items ne sont pas contigus.
- **Valeurs attendues connues** : comme les bases sont générées, chaque statistique attendue est connue d'avance et testée.
- **Fichiers de référence** (« golden files ») : profil JSON et rapport Markdown comparés octet par octet ; deux exécutions donnent le même fichier.
- **Tests à chaînes témoins** pour la confidentialité : la base fictive contient des chaînes uniques (`TEMOIN-7f3a…`) dans le texte libre et les identifiants ; on vérifie qu'elles n'apparaissent **jamais** dans un message destiné au modèle, ni dans le fichier projet, ni dans les exports.
- **Réseau bloqué** dans les tests (pytest-socket). Le client IA est testé contre un faux serveur en mémoire qui renvoie des réponses valides, invalides, avec champs en trop, avec variables inventées.
- **Test du refus d'adresse** : le client refuse une adresse non locale.
- **Test sans IA** : la chaîne complète tourne sans les dépendances facultatives installées.
- **Essais manuels avec un vrai modèle** (Ollama sur la machine de développement) : marqués `llm`, exclus de l'intégration continue.
- ruff pour le style ; intégration continue GitHub Actions sous Windows, puis Linux.

## 10. Structure du dépôt

```
dictionnaire-donnees/
├── pyproject.toml
├── README.md                  # installation pas à pas, en français
├── LICENSE
├── CLAUDE.md                  # règles pour l'assistant de code
├── docs/
│   ├── CONCEPTION.md
│   ├── journal-des-decisions.md
│   ├── installation-windows.md
│   ├── confidentialite.md     # ce qui est envoyé au modèle, ce qui ne l'est jamais
│   └── dependances.md         # licences des dépendances
├── scripts/
│   └── generer_bases_fictives.py
├── exemples/                  # bases fictives générées et codebooks d'exemple
├── src/ddict/                 # nom de module neutre, indépendant du nom final
│   ├── io/  profile/  privacy/  groups/  llm/  project/  review/  export/
│   └── cli.py
└── tests/
```

## 11. Choix techniques

| Choix | Recommandation | Raison |
|---|---|---|
| Python 3.11+, `pyproject.toml` | Garder | — |
| pandas + pyreadstat | Garder | pyreadstat rend directement les étiquettes et les manquants déclarés de SPSS ; il lit aussi `.dta` (Stata) et `.sas7bdat` presque gratuitement, utile pour la feuille de route. |
| pydantic | Garder | Sert à la fois aux schémas de réponse de l'IA et au fichier projet. |
| openpyxl | Garder | — |
| Streamlit | Garder pour la v0.1, **avec deux réglages obligatoires** (écoute locale, télémétrie coupée) | Rapide à construire ; son modèle « tout se réexécute à chaque clic » devient lent au-delà de quelques centaines de variables, d'où une interface mince. |
| Client compatible OpenAI | **httpx directement** plutôt que la bibliothèque `openai` | Moins de dépendances, contrôle total de l'adresse (refus du non-local), aucun comportement caché. Les trois serveurs visés acceptent `response_format` avec un schéma JSON. |
| Installation | **uv** (outil d'Astral) | Une commande installe Python et l'outil, sans connaître pip ni les environnements virtuels ; prépare le futur installateur Windows. |
| pytest, pytest-socket, ruff | Garder | — |
| Modèle de départ | Un modèle « instruct » de 7-8 milliards de paramètres en quantification Q4, qui tient dans 8 Go de VRAM ; le choix exact est documenté dans le journal des décisions après essai | — |

Toutes les dépendances ci-dessus sont sous licences permissives (BSD, MIT, Apache 2.0), compatibles avec Apache 2.0 comme avec AGPL.

## 12. Feuille de route

**v0.2** ajoute la lecture de Stata (`.dta` : étiquettes et étiquettes de valeurs ; les manquants étendus `.a` à `.z` sont lus comme vides), SAS (`.sas7bdat` : étiquettes seulement, le catalogue de formats n'est pas lu) et Excel (`.xlsx` : première feuille, noms en première ligne ; chaque cellule est lue comme le texte d'un CSV, pour qu'un classeur et son export CSV donnent le même profil).

**v0.1** (§ 13) : `.sav` et `.csv`, profilage complet, regroupement déterministe, enrichissement IA facultatif, révision Streamlit, fichier projet, exports `.xlsx` et `.md`, interface en français.

**v0.2** : questionnaire comme source documentée, glossaire des sigles, autres formats ; plan proposé dans [`plan-v0.2.md`](plan-v0.2.md).

**Plus tard** (hors v0.1) :
- bases SQL ;
- export Frictionless Table Schema ;
- installateur Windows en un clic ;
- interface bilingue (chaînes traduisibles dès la v0.1 pour le permettre) ;
- jeu de référence pour comparer les modèles (bases fictives annotées à la main, mesure de la qualité des libellés et des regroupements) ;
- lecture `.dta`, `.sas7bdat`, `.xlsx` ;
- import et export du dictionnaire de données REDCap ;
- export DDI Codebook ;
- application des décisions à la base (déclarer les manquants, appliquer les étiquettes) dans une **copie** du fichier `.sav`.

## 13. Plan de développement de la v0.1

Chaque étape se termine par une revue ; une étape est finie quand son critère passe.

| # | Étape | Critère de réussite |
|---|---|---|
| 0 | Squelette : `pyproject.toml`, structure, ruff, pytest, pytest-socket, `CLAUDE.md`, journal des décisions | `uv run pytest` et `uv run ruff check` passent sur un test vide, sous Windows. |
| 1 | Générateur de bases fictives (`.sav` et variantes `.csv`) avec les pièges du § 9 | Deux exécutions produisent des fichiers identiques (même empreinte) ; un test vérifie la présence de chaque piège. |
| 2 | Lecture `.sav` | Étiquettes de variables et de valeurs, manquants déclarés et niveaux de mesure de la base fictive retrouvés exactement. |
| 3 | Lecture `.csv` | Les variantes UTF-8 / Windows-1252, `,` / `;`, point / virgule décimale donnent le même tableau. |
| 4 | Profilage déterministe | Chaque statistique du § 5.2 égale la valeur attendue connue ; codes non étiquetés, sentinelles et variable constante détectés. |
| 5 | Classement de confidentialité et masquage des petits effectifs | L'identifiant, le texte libre et la date de naissance fictifs sont classés correctement ; effectifs < 5 masqués. |
| 6 | Fichier projet : modèle, statuts, sauvegarde, rechargement | Aller-retour sans perte, octet pour octet ; un champ sourcé sans source est refusé ; une base modifiée est détectée à la réouverture. |
| 7 | Exports `.xlsx` et `.md` + commandes `profiler` et `exporter` | **Jalon « utile sans IA »** : de la base fictive au codebook complet, sans aucune dépendance IA installée ; aucune chaîne témoin dans les sorties. |
| 8 | Regroupement déterministe et signaux d'items inversés | Les échelles fictives sont retrouvées, y compris l'échelle non contiguë ; les items inversés fictifs ont une corrélation item-total négative. |
| 9 | Porte de confidentialité et construction des messages (`enrichir --apercu`) | Aucune chaîne témoin dans aucun message ; les messages sont identiques d'une exécution à l'autre. |
| 10 | Client IA, schémas, validation, contre un faux serveur | Réponses invalides, champs en trop, variables inventées : toutes rejetées et tracées ; adresse non locale refusée. |
| 11 | Enrichissement par blocs, reprise après interruption | Interrompre puis relancer ne refait pas les blocs réussis ; essai manuel avec Ollama sur la base fictive, résultats consignés. |
| 12 | Interface de révision Streamlit | Scénario manuel écrit : accepter, corriger, rejeter, saisir un seuil avec source, fermer, rouvrir ; la logique est couverte par des tests sans Streamlit ; écoute locale et télémétrie coupée vérifiées. |
| 13 | Documentation utilisateur et version 0.1.0 | Une personne non développeuse installe l'outil sous Windows en suivant `installation-windows.md` et produit un codebook à partir de la base fictive. |

## 14. Décisions qui reviennent à l'auteur

| Décision | Recommandation |
|---|---|
| **Nom du projet** | Garder un nom de travail (`dictionnaire-donnees`, module `ddict`) jusqu'à la v0.1 et choisir le nom final avant de rendre le dépôt public, après vérification sur GitHub et PyPI. Viser un nom court, prononçable en français et en anglais. |
| **Licence** | **Apache 2.0** pour le code, comme envisagé : l'outil tourne sur le poste, donc la clause réseau de l'AGPL n'apporterait presque rien, et une licence permissive facilite l'adoption par des universités et des centres de recherche. CC BY 4.0 pour la documentation, CC0 pour les bases fictives et les gabarits. Seul argument contraire : la cohérence avec outil-qualitatif (AGPL), si les deux projets doivent un jour partager du code. |
| **Dépôt public dès le départ ou privé jusqu'à la v0.1** | **Privé jusqu'à la v0.1**, puis public. Cela laisse le temps de fixer le nom et la licence, et de vérifier qu'aucune donnée réelle ni aucun chemin personnel n'est entré dans l'historique Git (un historique public ne s'efface pas). |
| **Distribution** | uv pour l'installation de la v0.1 (§ 11). |
| **Seuil de petits effectifs** | 5 par défaut, réglable. |
| **Langue des prompts** | Français, ce qui aligne la langue des libellés produits sur celle de l'interface. |
| **Lien avec outil-qualitatif** | Projets séparés, sans code partagé pour la v0.1 ; les bonnes pratiques (journal des décisions, JSON déterministe, réseau bloqué dans les tests) sont reprises. |
