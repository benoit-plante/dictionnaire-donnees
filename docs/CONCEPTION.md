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
- Sous **Windows** seulement (D-081), avec ou sans carte graphique.
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
| `sentinel_decisions` | Pour chaque code sentinelle : code manquant ou vraie valeur, selon l'équipe (v0.4, D-028) ; jamais proposé par l'IA ; le profil n'est pas recalculé, le codebook et les messages au modèle traitent un code confirmé comme un code manquant déclaré | humain |
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

La commande `rattacher` envoie un second type de message (prompt `link-v1`, puis `link-v2` en v0.3 : la page de chaque candidate et, pour une question répétée ou de suivi, la question qui la précède), par blocs de 6 variables : pour chaque variable, son nom, son étiquette, ses étiquettes de valeurs et **ses 5 questions candidates au plus**, calculées sans IA (mots du nom et de l'étiquette, sens des sigles acceptés du glossaire, séries numérotées, familles de noms, ordre du questionnaire). Jamais le questionnaire entier ni ses paragraphes (page de consentement). Le modèle répond pour chaque variable par un identifiant de sa liste, « aucune » ou « incertain » ; tout autre identifiant, ou tout champ de texte, fait refuser le bloc entier. Sans `--modele`, la commande indique seulement combien de variables ont des candidates : le choix se fait dans l'interface.

## 7. Révision (Streamlit)

- **Accueil (v0.3)** : `ddict` lancé seul ouvre l'interface sur l'accueil : nouveau projet à partir d'une base (choisie avec la fenêtre « Ouvrir » du système, ouverte dans un processus à part, ou par son chemin collé ; le fichier projet est écrit à côté de la base, D-020), ouverture d'un projet, projets récents (chemins seulement, dans le dossier de l'utilisateur, effaçables, D-024). Le bouton « Accueil » de la barre latérale y ramène.
- **Pages et tableau de bord (v0.3)** : un projet s'ouvre sur sa page « Base » (résumé du profil, comme `ddict profiler`) ; la page « Questionnaire » lit le questionnaire, montre les questions trouvées et celles à vérifier, et permet de le remplacer, comme `ddict questionnaire`. En tête de la barre latérale, un tableau de bord liste ce qui attend, dans l'ordre recommandé (questionnaire, sigles, rattachements, étiquettes de valeurs, libellés) ; chaque ligne mène à la page et au filtre concernés. Les deux chemins, interface et ligne de commande, passent par les mêmes fonctions (`ddict.workflow`).
- **IA locale (v0.3)** : la page vérifie que le serveur local répond (`GET /models`, avec les mêmes refus que le client : adresse de cet ordinateur seulement, sans proxy ni redirection) et liste les modèles installés ; sans serveur ou sans modèle, elle explique comment installer Ollama et télécharger le modèle, sans jamais le faire elle-même (D-023). Pour le rattachement et pour les libellés, elle montre exactement les messages qui partiraient, puis lance le travail dans l'onglet, bloc par bloc, avec une barre de progression ; « Arrêter » ou un changement de page l'arrêtent après le bloc en cours, les blocs terminés sont enregistrés et une relance reprend là où il s'était arrêté (D-022).
- Liste des variables avec filtres : « à réviser », « anomalies », « texte libre / identifiants », par groupe.
- Fiche d'une variable : ce que dit le fichier, ce qui a été calculé, ce que propose l'IA (en couleur distincte, avec le modèle utilisé), et trois boutons : accepter, corriger, rejeter.
- Champs sourcés (étendue théorique, seuils, nom d'instrument, références) : la sauvegarde est impossible sans source.
- Question du questionnaire (v0.2) : le rattachement proposé s'accepte ou se rejette ; une liste, candidates en tête, permet d'en choisir un autre ou « aucune question ». Filtre « Sans question ».
- Sauvegarde automatique du fichier projet à chaque décision.
- Configuration imposée au lancement : écoute sur `127.0.0.1` seulement (par défaut, Streamlit écoute sur toutes les interfaces, donc serait visible sur le réseau local) et **télémétrie de Streamlit désactivée** (`browser.gatherUsageStats = false`, activée par défaut sinon).

La logique (changer un statut, valider une source) vit dans `project` et se teste sans Streamlit ; l'interface reste mince, ce qui permettrait de la remplacer plus tard sans tout réécrire.

### 7.1 Décisions groupées (v0.4, D-029)

- `logic.agreeing_links` : les rattachements proposés par le modèle qui sont aussi la première candidate du calcul (`link.best_guess`) ; `logic.accept_links` les accepte un par un, avec leur date, et refuse un nom qui n'est plus en accord.
- `logic.group_label_proposals` et `logic.accept_group_labels` : les étiquettes de valeurs proposées pour les membres d'un groupe.
- Interface (`review/ui/bulk_view.py`) : un premier bouton ouvre la liste exacte, toutes les cases cochées ; le bouton « Accepter ces N… » n'existe que dans cette liste. Essai : `docs/essais/2026-10-14-decisions-groupees.md`.

### 7.2 Banc d'essai des modèles (v0.4, étape 6)

- `ddict.bench` : pour chaque base fictive (CSV, puis questionnaire PDF, comme une équipe), les rattachements proposés par le modèle sont comparés au corrigé (`corrige-banc.json`), avec le calcul seul pour comparaison ; puis, après les bons rattachements et les sigles du questionnaire acceptés, les libellés et descriptions proposés sont comptés selon les signaux de l'outil (citation, seuil, instrument, sigle, étendue observée) et selon un sens de code donné pour un code sans étiquette (« 1 = Oui »). Durée de chaque tâche.
- Les projets restent en mémoire ; seul un rapport Markdown est écrit (`banc-essai-<modèle>-<date>.md`). Les bases fictives et le corrigé sont inclus dans le paquet (`ddict/banc/`).
- `ddict evaluer --modele … [--dossier …]`, et une section de la page « IA locale ». Testé avec un faux serveur ; le rapport est reproductible à durées fixées.

### 7.3 Langue de l'interface (v0.5, D-032, D-033)

- `ddict.i18n` : `_` traduit au moment de l'affichage, selon la langue en cours (`set_language`) ; les tables de textes (types, statuts, en-têtes du codebook…) gardent leurs phrases marquées par `N_` et les traduisent à la lecture (`Texts`, `TextList`). Un test refuse toute phrase traduite à l'importation d'un module, qui resterait dans sa première langue.
- `ddict.settings` : la langue de l'interface, choisie sur l'accueil, est gardée sur l'ordinateur (`reglages.json`, à côté des projets récents) ; `DDICT_LANG` la remplace. Elle est relue à chaque affichage d'une page et au lancement d'une commande.
- Catalogue : `src/ddict/locale/en/LC_MESSAGES/ddict.po`, mis à jour et compilé en `ddict.mo` par `scripts/traductions.py` ; les phrases marquées (`_`, `N_`, `field_label`) sont trouvées par l'analyseur de Python, qui voit aussi celles des f-strings (l'extracteur de Babel les manquait), et Babel écrit le `.po` et le `.mo`. Des tests vérifient que le catalogue contient toutes les phrases, qu'elles sont toutes traduites, et qu'aucune page parcourue en anglais ne montre de français hors des données de l'équipe. Termes fixés dans `docs/glossaire-traduction.md`.
- **Langue du codebook** (étape 3) : les écrivains d'exports (`render_markdown`, `write_markdown`, `write_xlsx`, `render_syntax`, `write_syntax`) prennent `language=` (`i18n.in_language`) ; ils écrivent dans cette langue le temps de l'export, puis l'interface revient à la sienne (`i18n.using`). Les nombres suivent la langue (0,363 / 0.363). La description calculée d'un groupe est enregistrée en français (les phrases sources) et recomposée dans la langue de l'affichage (`wording.group_description`) ; une description écrite par une personne reste telle quelle. Rapports de référence : `tests/reference/etude-sommeil.fr.md` et `.en.md`.
- `field_label`, `colon`, `semicolon` et `quoted` suivent la typographie de la langue (« Format : », « Format: »). Les commandes et options ont des équivalents anglais (`ddict export --work`, `--replace`…), à côté des noms français.

### 7.4 Études menées en anglais (v0.5, étape 4)

- **Langue de l'étude** (`settings.language`, `fr` ou `en`) : devinée par `ddict.questionnaire.language` d'après les mots du questionnaire (ou, sans questionnaire, des étiquettes du fichier), à la création du projet et à la lecture du questionnaire ; modifiable sur la page « Base ». Elle choisit la langue des consignes au modèle (étape 5) ; elle est distincte de la langue de l'interface (D-032).
- Le découpage du questionnaire et le glossaire reconnaissent déjà les formes anglaises (« Check all that apply », « If yes », définitions « Cognitive behavioural therapy (CBT) ») ; le calcul des candidates ignore aussi les petits mots anglais.
- Base fictive anglaise : `exemples/bases-fictives/sleep-study.*` et `questionnaire-sleep.*` (`scripts/generer_base_anglaise.py`).
- **Consignes au modèle** (étape 5) : `prompts/link-v2.en.txt` et `variables-v3.en.txt`, traduction fidèle des consignes françaises, choisies d'après la langue de l'étude ; les textes envoyés avec les données (« masked », notes des variables sensibles, description des groupes) suivent aussi cette langue. La version enregistrée est `link-v2.en` / `variables-v3.en` ; une étude en français reçoit exactement les mêmes messages qu'avant. Le modèle peut répondre « none » ou « unsure » comme « aucune » ou « incertain ». Les signaux d'invention reconnaissent « threshold » et les noms d'instruments à l'anglaise, sauf ceux du glossaire accepté. Le banc d'essai compte la base anglaise. Essai : `docs/essais/2026-10-14-etude-anglaise.md`.

### 7.5 macOS (v0.5, retiré)

- L'installation sur macOS (v0.5, D-035) est retirée : l'outil ne vise plus que Windows (D-081). Les scripts `installer.command` et `desinstaller.command`, les guides Mac et le flux GitHub `macos.yml` restent dans l'historique Git.

### 7.6 Des rattachements plus complets (v0.6)

- **Choix sûr du calcul** (D-041, étape 5) : `link.sure_choices` (meilleure cible nette d'une variable, règle des ancres, ou « aucune » sur indice fort) est marqué `"computed": "sure"` dans les candidates envoyées ; si le modèle choisit autre chose, sa proposition est gardée avec le signal `question:computed_disagrees`, effacé par la décision d'une personne.
- **Questions voisines** (D-040, étape 4) : `link.neighbours` donne, pour une variable sans candidate (ni vide ni constante), les questions situées entre les cibles des variables sûres qui l'encadrent (les ancres), au plus 6, les plus proches de sa place attendue. Le calcul seul ne choisit pas parmi elles (`best_guess` reste « aucune ») ; le modèle les reçoit marquées `neighbour`, dans des blocs à part avec la consigne `link-v3` (la règle, donnée à toutes les variables, dérangeait le modèle ailleurs) ; l'interface les met en tête de liste.
- **« Aucune question » proposée** (D-039, étape 3) : `link.no_question_reason` reconnaît un identifiant (nom d'identifiant, sans valeurs de courriel ni de téléphone), une date de passation (dates étalées sur au plus 400 jours, hors date de naissance) ou un score calculé (nom en `total`, `score`, `moyenne`… hors d'un groupe, ou `profile.sum_of_group` : la somme exacte des items d'un groupe, vérifiée au profilage, dont seul le fait est gardé). La candidate « aucune » passe alors en tête ; le modèle la reçoit avec la raison (« (identifiant) ») ; l'interface la montre en tête de liste.

### 7.7 Exports de plateformes de sondage (v0.7)

- **Description de plateforme** (D-044, étape 2) : `ddict.platforms` décrit SurveyMonkey comme des données : ses variables (`CollectorNm`, puis `RespondentID`… ou `respondent_id`…, avec leur titre dans les exports Excel et CSV et leur nom fixe, D-050), le motif `q0003_0004` / `q0008_other` et les cellules de la seconde ligne d'en-tête (`Response`, `Open-Ended Response`, « autre »). Une base est reconnue quand elle a au moins 3 variables de la plateforme et que la moitié au moins de ses autres noms suivent le motif ; la plateforme est gardée dans `source.platform`, et le format du projet passe à 0.2.0 (un projet 0.1.0 se lit tel quel, D-048 ; un projet d'une version plus récente est refusé avec un message clair).
- **En-tête sur deux lignes** : les lecteurs `.xlsx` et `.csv` le reconnaissent par les colonnes de la plateforme, vides en ligne 2 (une ligne de réponses y a l'identifiant du répondant), et nomment les colonnes comme le `.sav` du même export : les titres anciens (« Respondent ID ») vont avec les noms anciens (`RespondentID`), les exports récents titrent leurs colonnes par les noms récents eux-mêmes ; une question reçoit `q<rang>` sous une cellule de réponse, `q<rang>_<rang de la colonne>` sous un énoncé ou une option, `q<rang>_other` sous « autre ». Les données commencent à la ligne 3. La page « Base » et `ddict profiler` disent la plateforme reconnue et conseillent le `.sav`, qui garde les codes et les étiquettes.
- Sur les deux vrais exports de l'essai (D-046) : plateforme reconnue, aucune ligne en trop, aucune colonne sans nom, aucun nom absent du `.sav`.
- **Corrections de l'essai** (étape 3) :
  - préfixe commun (`groups.item_prefix`) : un radical d'au moins 2 lettres suivi d'un séparateur (`ab_1`), ou d'au moins 3 lettres (`anx3`) ; `q1`, `q0001`, `q_2` ne font plus d'échelle ;
  - une variable écartée d'un groupe (confidentialité, constante…) aux mêmes étiquettes de valeurs que sa suite ne la coupe plus en deux ;
  - « identifiant probable » : par les mots du nom comme avant ; par l'étiquette seulement quand elle désigne un identifiant (au plus 3 mots hors petits mots, ou un premier mot d'identifiant qui n'est pas le verbe « identifier ») ;
  - dates et heures à barres obliques écrites en texte (`03/02/2026 07:15:23 AM` : mois d'abord avec l'horloge de 12 heures, jour d'abord avec celle de 24 heures) : des dates, plus du texte libre ;
  - un code **observé** dont l'étiquette dit « Ne sais pas », « Préfère ne pas répondre », « Refus », « Sans objet » (ou l'anglais) est un code manquant probable (D-047), écarté de l'alpha comme les autres ; le codebook le dit (« Code 6 (« Ne sais pas ») probablement manquant, non déclaré ») ;
  - un item d'un groupe déclaré `scale` dont toutes les valeurs observées ont une étiquette reçoit le signal `measure_level_doubtful` ; le niveau n'est pas changé.
- **Structure de plateforme** (étape 4) : `platforms.survey_questions` lit dans les noms les questions de l'export : une question simple (`q0001`, avec son éventuel `q0001_other`), une grille (`q0003_0001`…) ou un ensemble de cases à cocher (des items qui ont tous une seule étiquette de valeur, ou une seule valeur observée dans un export Excel ou CSV). Pour les variables qu'elle couvre, elle remplace le préfixe et les étiquettes partagées : une grille d'au moins 3 énoncés est un groupe (base « structure de la plateforme », préfixe `q0003_`), un ensemble d'au moins 2 options un groupe `multiple_response` (`Group.kind`), sans statistiques d'items, sa variable « autre » dans `Group.attached`, hors des membres. Les noms `q0001`, `q0006`… ne sont plus des séries numérotées pour le calcul des candidates.
- **Rattachements par la structure** (`link.platform_choices`) : chaque question de l'export est appariée, dans l'ordre, à la prochaine question du questionnaire dont le texte concorde (`link.texts_agree` : égal à la casse, aux accents, à la ponctuation et au « … » initial près, très semblable, ou début d'un texte coupé, SPSS coupant les étiquettes de valeurs à 120 octets) ; puis chaque variable à l'énoncé ou à l'option dont le texte concorde avec le sien, la variable « autre » à l'option « autre ». Ce sont des choix sûrs (D-041), en tête des candidates ; les variables de la plateforme, et une question seule qui est un identifiant (`id`), n'ont aucune question. Le rang seul ne décide jamais.
- **L'en-tête de l'export Excel comme questionnaire** (D-045, `questionnaire.header`) : seules les deux premières lignes sont lues ; une question par bloc de la ligne 1 (`Q3` pour `q0003`), ses énoncés (`Q3.r4`) ou options (`Q8.o2`, « autre » en dernier) en ligne 2. La nature d'une question à plusieurs colonnes vient de la base du projet, sinon de sa formulation ou d'une colonne « autre ». Le format du questionnaire est `xlsx`. Les lecteurs Excel et CSV donnent aussi aux variables, comme étiquettes, les textes de l'en-tête que le `.sav` met dans les siennes.
- **Questionnaires de plateforme** (étape 5, `questionnaire.segment`) :
  - questions numérotées (`1.`, `2)`, `Q3.`), dans un `.txt` comme dans un PDF : des numéros en tête de ligne sont des questions quand ils vont 1, 2, 3… une seule fois sur le questionnaire, avec d'autres lignes entre eux (les énoncés d'une grille numérotée se suivent et recommencent à 1), ou quand ils commencent par « Q » ; seules ces lignes sont alors des questions, et leur numéro est retiré du texte ;
  - questions formulées comme une consigne qui finit par un point (« Cochez les consignes reçues. », « Décrivez une situation. ») : un verbe de consigne en tête, suivi de ses options ou d'une autre question ; cases à cocher reconnues aussi par « Cochez les… », « Coche les… », « qui s'appliquent », « all that apply », jamais par « Cochez la case qui… » ;
  - titres de colonnes empilés sur trois lignes, dont les premières, loin à droite, ne portent qu'un mot : des titres, plus de fausse question ;
  - énoncés d'une grille qui sont des questions (« Êtes-vous satisfait·e de l'éclairage ? ») : des énoncés tant qu'ils se lisent comme les précédents ; sous une question qui finit par « ? », il en faut deux de même forme pour commencer une grille (un intertitre suivi d'une question n'en est pas un) ;
  - une grille non numérotée continue sur la page suivante, sans ses titres, tant que les lignes se lisent comme ses énoncés ; un énoncé coupé par la page continue en minuscule ; la ligne qui précède une question est son introduction ;
  - une option longue alignée sur les options qui la précèdent reste une option.
- **Réparation par la structure** (après l'essai de contrôle, `link.repair_from_platform`) : un paragraphe dont les mots concordent, seul, avec une question de la base absente du questionnaire devient cette question (une question ouverte sans « ? », un champ seul sur sa ligne) ; un paragraphe qui concorde avec l'énoncé manquant d'une grille en devient la ligne. Le texte reste celui du questionnaire, marqué `found_by_platform`, et les questions sont renumérotées. Une grille ne continue pas sur une ligne quand les titres de colonnes d'une autre grille suivent. Une grille de plateforme ne forme une échelle que si ses énoncés sont des catégories étiquetées et partagées (pas des coordonnées, un classement ou des menus déroulants) ; une telle question à plusieurs champs reçoit un radical.
- **Vérification par la structure** (`link.check_against_platform`, à la lecture du questionnaire) : grille au nombre d'énoncés différent, ensemble à cocher au nombre d'options différent (l'option « autre » peut être une case du `.sav`, absente de l'export Excel, en plus de son texte), question sans équivalent dans la base, chacun dans les points à vérifier de la question ; une question lue comme un choix unique dont la base dit qu'elle est à cocher le devient, son texte inchangé. La page « Questionnaire » et `ddict questionnaire` disent combien de questions de la base ont, ou n'ont pas, de question concordante (`link.platform_coverage`).
- Sur les deux vrais exports : 7 grilles et 4 ensembles à cocher regroupés ; avec l'en-tête comme questionnaire, toutes les variables de questions rattachées par la structure (104 et 40), avec des textes qui concordent ; avec le PDF de la base 1, 100 rattachements sur 104 variables de questions après l'étape 5 (36 avant), tous concordants ; avec celui de la base 2, numéroté, 40 sur 40 (0 avant).

### 7.8 Renommage (v0.7)

- **Le nouveau nom** (D-048, étape 6) : `VariableEntry.new_name`, valeur suivie ; le nom d'origine (`name`) reste la clé. Deux origines qui proposent, comme `ai` et `questionnaire` : `rule` (règles de nommage) et `reference` (vague précédente). Le préfixe d'un groupe (`Group.name_prefix`) est donné par une personne ; le radical d'une question (`Project.stems`, clé `q0005` pour une plateforme, `Q5` sinon) est proposé par les règles et décidé comme une valeur suivie. Réglages : `settings.naming` (longueur maximale 32, marque de vague, suffixe ou préfixe, D-049).
- **Règles** (`ddict.naming`) : un nom est en minuscules, chiffres et `_` (commence par une lettre, ni `_` final ni `__`), au plus la longueur maximale marque comprise, n'est pas un mot réservé de SPSS, et ne reprend ni le nom en cours d'une autre variable ni le nom d'origine d'une autre, à la casse près.
- **Propositions par le calcul** (`naming.propose`), dans l'ordre : nom fixe d'une variable de plateforme (D-050, langue de l'étude) ; `<préfixe>_<rang>` pour un item d'un groupe dont une personne a donné le préfixe (rang de l'énoncé dans la structure de plateforme, sinon dans le groupe) ; `<radical>`, `<radical>_<rang de l'option>`, `<radical>_autre_txt` pour une question seule, une option à cocher et le texte « autre ». Le radical vient des premiers mots significatifs de la question (au plus trois, 20 caractères, sans les petits mots ni les mots de question ou de consigne : « quel », « combien », « cochez »…), lus dans le questionnaire par un rattachement accepté ou sûr, sinon dans l'étiquette ; deux questions aux mêmes mots reçoivent `_2`. Une proposition invalide n'est pas enregistrée : la variable reste « à nommer ». Une décision (accepter, corriger, rejeter, écrire) n'est jamais réécrite ; une proposition dont la règle ne s'applique plus est retirée.
- **Commande** : `ddict renommer <projet> [--suffixe _t2 | --prefixe t2_]` (`ddict rename … --suffix | --prefix`) propose et dit combien de noms sont proposés, acceptés, à nommer, en conflit.
- Sur les deux vrais exports, les règles seules proposent 50 noms sur 50 (base 2), et 13 sur 114 (base 1), dont les 100 items de grilles attendent le préfixe de leur groupe.
- **Vague précédente** (D-052, étape 7, `ddict.waves`) : `ddict renommer <projet> --reference <projet-t1.dd.json | t1-documente.sav | correspondance.csv>`. Chaque variable est appariée par le calcul, avec des raisons lisibles et pondérées : même variable de plateforme (par son rôle, quel que soit le nom ou la variante), même étiquette (ou, à défaut, même texte de question rattachée), mêmes étiquettes de valeurs, même question que ses voisines appariées (le texte « autre », dont l'étiquette est la même partout), même type. Un appariement n'est proposé que s'il est net (la règle des ancres) ; deux variables aussi bonnes pour la même variable ancienne vont à une personne. Une table de noms n'apparie que par nom d'origine identique, et seulement jusqu'à la première question dont la forme diffère dans l'ancienne vague (énoncés, « autre ») : une question ajoutée y décale la numérotation de toutes les suivantes ; ces appariements sont dits fragiles. Le nom proposé (origine `reference`) est l'ancien, sans sa marque de vague (lue dans les réglages du projet, ou reconnue sur au moins 80 % des noms), avec la marque de la nouvelle vague ; les préfixes des grilles anciennes sont proposés pour les groupes correspondants. Les règles proposent ensuite le reste. Le rapport des écarts (`<projet>-ecarts-vagues.md`) : variables appariées et pourquoi, ajoutées, retirées (avec leur ancienne étiquette), étiquettes de valeurs changées code par code, candidates à départager. `waves.write_name_table` écrit la table de noms qui servira à la vague suivante.
- Sur la base fictive : depuis le fichier projet ou la copie documentée de la vague 1, les 54 noms appariés sont ceux du corrigé ; la question ajoutée, l'item retiré et l'étiquette changée sont trouvés. Depuis la table de noms, aucun nom décalé n'est proposé.
- **Radicaux par le modèle** (D-051, étape 10, `llm.stems`, prompt `rename-v1`, français et anglais) : facultatif, après les règles, pour les radicaux non décidés seulement ; jamais un préfixe de groupe, un nom de variable de plateforme ni un rang. Le message donne, par question, ce que la porte de confidentialité laisse déjà passer : le texte de la question (questionnaire par un rattachement accepté ou sûr, sinon l'étiquette), sa nature, ses options telles que les disent les étiquettes de valeurs, le type et la note d'une variable sensible ; jamais une valeur. Réponse : un radical par question ou « » (incertain), schéma strict ; un radical que les règles refusent fait refuser le bloc. Un radical accepté entre comme proposition (`ai`) ; une partie courte absente du texte de la question et du glossaire accepté reçoit le signal `stem:acronym` (un sigle, peut-être un instrument), effacé par la décision d'une personne. Banc (`bench.run_naming`, dans `ddict evaluer`) : radicaux valides et égaux au corrigé, règles seules contre modèle. Essai du 2026-10-15 (`docs/essais/2026-10-15-radicaux-modele.md`) : qwen2.5 7B, 2 / 10 égaux au corrigé contre 3 / 10 pour les règles seules ; selon D-051, la proposition par le modèle n'est pas offerte dans l'interface, seulement par `ddict renommer --modele` (à l'essai).
- **Interface** (étape 9, `review.names` pour la logique, `review/ui/names_view.py`) : page « Noms », après « Groupes ». Réglages de nommage (marque de vague, place, longueur maximale, de 8 à 64) ; reprise d'une vague précédente (fenêtre « Ouvrir » ou chemin, rapport des écarts écrit à côté du projet) ; bouton « Proposer les noms par les règles » ; acceptation groupée par groupe, par question ou pour les autres variables, avec la liste exacte et une case à décocher par nom (comme D-029) ; tableau filtré (toutes, à nommer, proposés, en conflit, décidés) où le nouveau nom se corrige en place (un tableau par filtre, pour qu'une correction non enregistrée ne tombe jamais sur une autre ligne ; un nom vidé rend le nom d'origine) ; accepter ou rejeter une variable ; tableau des radicaux des questions, corrigés une fois pour toutes leurs variables. Vue « Groupes » : préfixe des noms d'une grille, et acceptation d'un préfixe repris d'une vague précédente. Tableau de bord, une fois le renommage commencé : grilles sans préfixe, noms proposés à valider, noms en conflit, avant les libellés. La page « Export » écrit aussi la table de correspondance. Pas de décision groupée des rattachements par la structure (D-053).

## 8. Exports

- **Codebook `.xlsx`** : un onglet « Variables » (une ligne par variable), un onglet « Valeurs » (une ligne par code et étiquette), un onglet « Groupes », un onglet « Provenance » (statut et origine de chaque champ, modèles utilisés). En-têtes figés, filtres activés.
- **Rapport `.md`** : vue d'ensemble (nombre de variables, manquants, anomalies), puis une section par groupe et par variable.
- **Export final** (par défaut) : seulement les valeurs de fichier, de calcul, validées ou corrigées. **Export de travail** (option) : inclut les propositions en attente, marquées « proposé par IA ».
- Les effectifs inférieurs au seuil sont masqués aussi dans les exports, puisqu'un codebook est souvent partagé ou déposé avec les données.
- **Fichiers de commandes (v0.4, D-025)** : `ddict.export.syntax` écrit une syntaxe SPSS (`.sps`) et un script R (haven, `labelled_spss`), à côté du projet (`etude-metadonnees.*`), par `ddict exporter --syntaxe` ou la page « Export ». Seulement les décisions acceptées, comme l'export final : libellés, étiquettes de valeurs, codes manquants déclarés ou confirmés (D-028), niveaux de mesure du fichier. Aucune valeur n'est recodée (D-025) : les items inversés sont donnés en commentaire. Textes échappés pour chaque langage, UTF-8, fins de ligne LF. Vérification : le script R appliqué au CSV fictif redonne les métadonnées du `.sav` (test avec R) ; la syntaxe SPSS est exécutée dans PSPP (D-027). Pas de fichier Stata (D-030) : il n'a pas pu être essayé dans Stata.
- **Copie documentée (v0.4, D-026)** : `ddict.export.documented` écrit, à côté de la base, `<base>-documente.sav` avec pyreadstat : les cellules de l'original (pour un `.sav`, lues sans conversion des dates et réécrites avec leurs formats SPSS) et les métadonnées acceptées (libellés, étiquettes, codes manquants déclarés ou confirmés, niveaux de mesure ; étiquette du fichier et notes d'un `.sav`). La base est retrouvée à côté du projet, ou donnée, et reconnue par son empreinte. La copie est écrite sous un nom provisoire (`.en-cours`), relue et comparée cellule par cellule ; elle ne prend son nom qu'à zéro écart, sinon elle est supprimée. Jamais d'écrasement sans `--remplacer` ou la case de la page. Si les codes confirmés dépassent ce que SPSS accepte (3 codes, ou un intervalle et un code), seuls ceux du fichier sont écrits, et l'outil le dit. Rien des données n'entre dans le projet.
- **Nouveaux noms (v0.7, étape 8)** : seuls les noms acceptés s'appliquent. Le codebook Excel a alors une colonne « Nom d'origine » à côté de « Nom » (le nouveau nom) et un onglet « Correspondance » (nom d'origine, nouveau nom, statut, origine) ; les autres onglets nomment les variables comme les données renommées. Le rapport Markdown donne le nom d'origine sous chaque variable renommée et une section « Correspondance des noms ». Sans nom accepté, le codebook est celui d'avant. L'export de travail montre les noms proposés, marqués « [proposé] ». La syntaxe SPSS commence par `RENAME VARIABLES ((ancien = nouveau) …)` et le script R par la table `ddict_noms` appliquée à `names(donnees)` (R de base) ; tout le reste porte sur les nouveaux noms. La copie documentée est écrite aux nouveaux noms ; sa vérification compare chaque colonne à la colonne d'origine de la même variable ; deux noms finaux égaux arrêtent la copie. `ddict exporter` écrit aussi la table de correspondance (`<projet>-correspondance.csv`, D-052). Vérification sur la vague 2 fictive renommée : le script R appliqué au `.sav` et la syntaxe exécutée dans PSPP redonnent la copie documentée de l'outil (noms, étiquettes, étiquettes de valeurs, codes manquants ; et les cellules pour R).
- **Depuis l'interface (v0.3)** : la page « Export » choisit la version (finale ou de travail) et les groupes dont le texte est omis (par défaut, ceux cochés dans la vue « Groupes »), puis écrit les deux fichiers à côté du projet ou les fait télécharger ; c'est la même fonction que `ddict exporter` (`ddict.workflow.export_codebook`), et un test vérifie que les deux donnent le même codebook.
- **Questionnaire (v0.2)** : pour chaque variable dont le rattachement est accepté, la référence (`Q7.r3, p. 3`) et le texte exact de la question et de l'énoncé ou de l'option, lu dans le questionnaire ; rien d'autre du questionnaire n'est exporté (page de consentement, consignes : D-012). L'onglet « Informations » donne le nom, le nombre de pages et l'empreinte du questionnaire. Un onglet « Glossaire » (et une section du rapport) donne les sigles acceptés, avec leur origine. L'onglet « Valeurs » dit d'où viennent les étiquettes tirées du questionnaire (D-016). **D-014** : le texte des questions d'un groupe peut être omis, par une case à cocher dans la vue « Groupes » (enregistrée dans le projet) ou pour un export seulement (`ddict exporter --sans-texte G3`) ; la référence de la question reste.

- **Empreinte du codebook (v0.8, étape 2)** : `ddict.project.fingerprint`, SHA-256 d'un JSON compact à clés triées, fait de ce que l'équipe a décidé : pour chaque variable, ce que dit le fichier (libellé, étiquettes de valeurs, manquants déclarés, niveau de mesure) et les valeurs acceptées (classe de confidentialité, question, nouveau nom, étiquettes, libellé, description, signalements, unité, groupe), les codes suspects tranchés, étendues, seuils, références et notes ; les groupes (membres, nature, texte « autre », préfixe, libellé, instrument, items inversés, cotation, étendue, seuils, texte omis) ; le glossaire accepté ; l'empreinte du questionnaire. Ni les propositions en attente ou rejetées, ni les dates, les appels au modèle, les réglages ou les statistiques. Les 12 premiers caractères figurent dans l'onglet « Informations », l'en-tête du rapport et celui des fichiers de commandes ; pas dans la table de correspondance des noms, dont le format reste celui de D-052. Un test fixe la valeur du projet de référence, qui doit être la même sur tout système (vérifiée sous Windows ; le flux macOS, lancé à la main, l'exécute aussi).

- **Niveau de mesure (v0.8, étape 3, D-063, D-067)** : `VariableEntry.measure_level`, valeur suivie, vide tant que le niveau du fichier tient. `ddict.project.measure` propose (origine `rule`, statut proposé) là où le fichier n'en donne pas, et à côté du sien quand il est douteux (le signal de la v0.7 : item étiqueté d'une grille déclaré `scale`) ; jamais par-dessus une décision ; une proposition que plus aucune règle ne fait est retirée. Le niveau **en vigueur** (`measure.level`) est celui que l'équipe a accepté ou choisi, sinon celui du fichier : c'est lui qu'utilisent les fichiers de commandes, la copie documentée, le codebook, les messages au modèle et l'empreinte. L'export de travail montre la proposition, marquée. La page « Base » a un tableau « Niveaux de mesure » (colonne « Décision », niveau modifiable, remplissage « Accepter » à relire, comme D-056) ; le tableau de bord compte les niveaux proposés. Format du projet 0.3.0 (D-061) : un projet 0.1.0 ou 0.2.0 est converti à l'ouverture, les règles proposant ses niveaux ; un test vérifie qu'il ne perd rien.

- **Cotation d'un groupe (v0.8, étape 4, D-060)** : `Group.scoring` est un objet `Scoring`, écrit par une personne avec sa source (jamais proposé, refusé sans source) : items (noms d'origine, membres du groupe), somme ou moyenne, minimum et maximum de l'échelle (pré-remplis d'après les étiquettes acceptées, hors codes manquants), nombre minimal d'items répondus, nom du score (règles de nom de D-048, différent des noms des variables et des autres scores) ; ou une note seule. Les items inversés sont ceux confirmés du groupe, une seule liste ; l'étendue du score est calculée (`ddict.project.scoring.score_range`). Un groupe « réponses multiples » n'en a pas. Ancien texte sourcé converti en note à l'ouverture. Montrée en une phrase dans le rapport et l'onglet « Groupes » ; dans l'empreinte. Formulaire sur la page d'un groupe.
- **Description de la base (v0.8, étape 4, D-064)** : `Project.dataset` : ce qu'est une ligne (participant, observation répétée, dyade, famille, autre), la structure (valeur suivie : transversale, une vague par fichier avec sa vague, format large avec ses suffixes, format long), les variables de plan (identifiant de regroupement, temps, vague, grappe, pondération ; noms d'origine) et une description courte. Écrite par une personne sur la page « Base » ; seule la structure est proposée (`ddict.project.dataset`, origine `rule`) : « une vague par fichier » quand une marque de vague est réglée, « format large » quand des suffixes `_t1`, `_t2`… reviennent sur au moins trois radicaux. Ce qui est dit (structure acceptée seulement) figure dans l'onglet « Informations » et en tête du rapport, et dans l'empreinte.

- **Complétude (v0.8, étape 5)** : `ddict.project.completeness`, calculée à chaque export et page, jamais enregistrée ni comptée dans l'empreinte (un constat, pas une décision). Pour chaque élément, les variables où il est accepté sur celles où il s'applique : question (s'il y a un questionnaire ; « aucune question » compte), libellé, étiquettes de valeurs (variables numériques nominales ou ordinales non sensibles ; niveau en vigueur, sinon proposé), niveau de mesure (sauf identifiants, textes libres, dates de naissance, dates, variables vides ou de types mélangés), nouveau nom (une fois le renommage commencé), cotation (groupes d'échelle) ; et la description de la base (ce qu'est une ligne, structure acceptée). Ce qui manque est nommé, dix noms au plus puis « et N autres ». Section « Complétude » en tête du rapport, lignes « Complétude : … » de l'onglet « Informations », tableau de la page « Base ».

- **Script de préparation (v0.8, étape 7, D-062, D-068)** : `ddict.export.preparation` écrit `<projet>-preparation.sps` et `.R` avec les fichiers de commandes (`ddict exporter --syntaxe`, page « Export »), quand le projet a des items inversés confirmés ou une cotation. À exécuter après le fichier de commandes, sur les noms finaux ; le script R vérifie d'abord que les variables existent. Pour chaque item inversé, une nouvelle variable `<item>_inv` = (min + max) − x, les bornes venant de la cotation, de l'étendue théorique sourcée ou des étiquettes (dit en commentaire ; non inversé si elles sont inconnues ou si le nom est pris). Pour chaque cotation structurée, le score : `SUM.k`, `MEAN.k` ou `MEAN.k(...) * n` (somme proportionnelle) en SPSS, `rowSums`, `rowMeans` en R, manquant sous le nombre minimal d'items répondus ; les codes manquants déclarés sont exclus (SPSS : par la déclaration ; R : `haven::zap_missing`). Un score déjà dans la base (D-039) est comparé, les écarts comptés (SPSS : `FREQUENCIES` d'une variable temporaire supprimée ensuite ; R : `warning`). Aucune variable d'origine n'est modifiée. Vérifié avec R (CSV fictif, scores égaux au calcul indépendant du test) et PSPP (mêmes scores sur le `.sav`).

### 8.1 Contexte d'analyse (v0.8, D-058)

Deux fichiers écrits à côté du projet par `ddict.export.context`, d'une même source, toujours « finaux » (valeurs acceptées seulement). Exemples de référence, produits par un prototype sur deux bases fictives révisées (décisions simulées ci-dessous) : `docs/exemples-contexte/`.

**Standard visé, vérifié le 2026-10-15** : Data Package et Table Schema **v2** (`https://datapackage.org/profiles/2.0/datapackage.json` et `…/tableschema.json`). Un champ y a `categories` (tableau de `{value, label}`), `categoriesOrdered` (booléen) et ses propres `missingValues` (tableau de `{value, label}`, valeurs écrites comme des textes, et qui remplacent la liste générale). Les propriétés propres à un outil sont permises partout ; la convention publiée (recette « Private Properties ») est un **préfixe `_`** : toutes celles de l'outil sont réunies dans un objet `_ddict` (plutôt qu'un espace de noms `ddict:`). Le standard et ses schémas sont sous licence Unlicense (domaine public) : les deux schémas peuvent être gardés dans `tests/` pour valider hors ligne avec `jsonschema` (Draft 7). Les deux exemples y sont valides, et le schéma refuse bien un `categoriesOrdered` non booléen, un code manquant numérique ou un type inconnu.

**`<base>-datapackage.json`**

| Élément | Contenu |
|---|---|
| Paquet | `$schema` (profil 2.0), `name` (nom du projet), `title` (étiquette du fichier, sinon nom) ; `_ddict` : outil et version, empreinte du codebook, langue, métadonnées de la base (`dataset`), règles (codes stables : `missing_values_excluded`, `reverse_items_before_scores`, `sensitive_never_in_outputs`, `undocumented_is_unknown`, `multiple_response_empty_is_unchecked`), complétude, groupes (`id`, `kind`, `items`, `attached`, `scoring`) |
| Ressource | `name`, `path` (nom du fichier, jamais un chemin : la base, ou sa copie documentée quand des variables sont renommées), `type: "table"`, `format: "sav"` et `mediatype` selon la base, `hash` (`sha256:…`) de la base quand c'est elle ; `_ddict.rows`, et `_ddict.renamed_from` (nom et empreinte de la base d'origine) quand la ressource est la copie documentée |
| Champ | `name` (nom final), `title` (libellé accepté), `type` (`integer`, `number`, `string`, `date`, `datetime`, `any` pour une variable vide), `categories` et `categoriesOrdered` (étiquettes acceptées hors codes manquants ; ordonnées si le niveau est ordinal), `missingValues` (codes déclarés et confirmés, avec leur étiquette), `constraints` (étendue **théorique sourcée** seulement) ; `_ddict` : `original_name` (si renommée), `measure_level`, `question` (référence, ou `null` pour « aucune question »), `group`, `privacy` (seulement si sensible) |

**`<base>-contexte.md`**, pour être collé dans un modèle :

1. En-tête : la base (nom, format, lignes, variables, empreinte du fichier), l'empreinte du codebook, ce qu'est une ligne, la structure, les variables de plan, la description ; quand des variables sont renommées, sur quel fichier travailler.
2. **Règles**, numérotées, en phrases : codes manquants exclus, items « inv » inversés avant tout score, variables sensibles jamais dans une sortie, « non documenté » veut dire inconnu (aucun seuil, étendue ou instrument absent du document) ; pour une base avec des questions à cocher, une case vide est une option non cochée sauf si toutes les cases de la question sont vides.
3. **Complétude** : une ligne de rapports (question, libellé, étiquettes de valeurs des variables codées, niveau de mesure, cotation des groupes d'échelle), puis la liste de ce qui n'est pas documenté.
4. **Groupes** : nature, liste des items ; les valeurs communes à tous les items, une seule fois ; pour une question à cocher, le texte de la question et le sens de 1 et du vide, et le texte « autre » ; la cotation, en une phrase, avec sa source, ou « non documentée ».
5. **Variables** : un tableau d'une ligne par variable : nom final (et nom d'origine), libellé (pour une option à cocher : l'option), type, niveau, valeurs (`→ G1` quand elles sont celles du groupe), manquants, groupe, référence de la question, note (`sensible (…)`, `inv`).
6. **Points d'attention** : les anomalies qui comptent pour l'analyse (variable constante, vide, en double, types mélangés, étiquette jamais utilisée, variantes d'écriture), regroupées ; **jamais une valeur observée** (une variante d'écriture est dite, pas citée) ; sans les codes que l'équipe a tranchés ni les signaux déjà décidés.
7. **Texte des questions**, dans l'ordre du questionnaire ; un énoncé n'est repris que si son texte diffère du libellé de sa variable ; omis pour les groupes protégés (D-014).

Taille mesurée, sans le texte des questions (caractères ÷ 4) : **37 tokens par variable** pour l'étude du sommeil, **47** pour l'export SurveyMonkey renommé (objectif : 60 au plus) ; le rapport Markdown actuel en compte 135 à 145.

**Écrit par `ddict.export.context` (étape 6)** : page « Export » (section « Contexte d'analyse », case « Ajouter les statistiques », écriture à côté du projet ou téléchargement) et `ddict exporter --contexte [--avec-statistiques]`. Les exemples de `docs/exemples-contexte/` sont la sortie du module sur les deux projets révisés de `tests/context_examples.py`, comparée octet par octet (`DDICT_REGENERATE=1` après un changement voulu) et validée contre les schémas. Statistiques (D-059) : pour une variable continue, effectif, moyenne, écart-type, étendue observée ; pour une variable codée, l'effectif de chaque code ; jamais pour une variable sensible ; effectifs de moins de 5 masqués, sauf ceux des codes manquants déclarés, exacts comme partout (D-007). Le niveau n'est pas montré pour une date, une variable vide, de types mélangés ou sensible ; un texte déclaré « échelle » (le défaut de SPSS) reçoit la proposition « nominal ». Taille mesurée par un test sur les quatre bases fictives lues et les deux projets révisés, et par un test `reel` (nombre seulement).

**Décisions simulées dans les exemples** (ce qu'une équipe aurait accepté) : rattachements du corrigé ; codes 999 (`age`), 9 (`sommeil_q3`), −9 (`nb_reveils`), et 6, 7 (grille de satisfaction SurveyMonkey) confirmés manquants ; `sommeil_q3` et `sommeil_q6` inversés ; une cotation de G1 avec une source **inventée et marquée comme telle** ; niveaux de mesure tels que l'étape 3 les proposerait ; les noms du corrigé pour la vague 2. Le libellé de `sommeil_q7`, les étiquettes des cases d'aide au sommeil et la cotation de l'échelle d'anxiété sont laissés non documentés, pour montrer la complétude. L'empreinte du codebook y est provisoire (étape 2).

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

**v0.2** (publiée) : questionnaire comme source documentée, glossaire des sigles, autres formats ; plan dans [`plan-v0.2.md`](plan-v0.2.md).

**v0.3** (publiée) : tout le parcours dans l'interface du navigateur et installateur Windows par double-clic ; plan dans [`plan-v0.3.md`](plan-v0.3.md).

**v0.4** : fichiers de commandes (SPSS, R) et copie documentée du `.sav`, codes manquants confirmés, banc d'essai des modèles, décisions groupées ; plan validé dans [`plan-v0.4.md`](plan-v0.4.md).

**v0.11 et suivantes** : de la base à l'ébauche d'article au format IMRaD, d'abord sans IA (carnet d'analyses, section Méthode, plan d'analyse, catalogue élargi, vérification du manuscrit), les modèles externes à la toute fin ; feuille de route proposée dans [`feuille-de-route-article.md`](feuille-de-route-article.md).

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

## 15. Analyses (v0.9)

Le catalogue est `docs/catalogue-analyses.md` (validé, D-077) ; le paquet `ddict.analysis` le met en œuvre (D-069 à D-077).

- **Données prêtes pour l'analyse** (`ddict.analysis.data`, étape 3) : la base est retrouvée à côté du projet et reconnue par son empreinte, lue en mémoire comme pour le profilage, puis les décisions acceptées sont appliquées dans l'ordre des fichiers de commandes et du script de préparation : codes manquants déclarés et confirmés retirés, noms finaux, items inversés (`<item>_inv`), scores des cotations structurées (règle des items manquants comprise ; mêmes valeurs que le script de préparation R, vérifié dans R). Le fichier n'est jamais modifié et rien des données n'entre dans le projet.
- **Catalogue comme données** (`ddict.analysis.catalogue`) : pour chaque analyse, ses rôles, les niveaux permis, le nombre de variables et de modalités, les options (la première par défaut : Welch pour le test t).
- **Conditions** (`ddict.analysis.conditions`) : les variables offertes pour un rôle (niveau en vigueur, ou « échelle » pour un score ; jamais un identifiant, un texte, une date, une variable vide ou de types mélangés). Refus : rôle mal rempli, variable exclue, niveau non décidé (renvoi à la page Base), niveau qui ne convient pas, nombre de modalités observées, un groupe de moins de 2 personnes (test t, ANOVA), moins de 10 observations par prédicteur (une variable nominale compte autant de prédicteurs que de modalités moins une). Avertissements : moins de 5 personnes dans un groupe ou une modalité, une variable ordinale avec Pearson, une base en format long pour une analyse qui suppose l'indépendance, moins de 20 observations par prédicteur.
- **Calcul et résultats** (`ddict.analysis.compute`, `ddict.analysis.results`, étape 4) : chaque analyse vérifie d'abord ses conditions (sinon `AnalysisRefused`, avec les raisons), puis calcule avec SciPy et les formules du catalogue ; elle rend un `AnalysisResult` de même forme pour toutes : variables et options, observations retenues et écartées, tableaux, statistiques brutes, phrase de résultat (style APA, qui décrit sans juger ; dans la langue du codebook), avertissements (ceux des conditions et ceux du calcul : effectifs attendus d'un khi-carré, cases ou modalités de moins de 5). Conventions : virgule décimale en français, deux décimales, trois pour p, p sans zéro initial, signe moins typographique. Un score est nommé « nom (score de G1) ».
- **Script R équivalent** (`ddict.analysis.rscript`) : R de base et haven ; il lit la base, exécute le fichier de commandes et le script de préparation, puis l'analyse, affiche les résultats et les range dans `resultats`. Les tests l'exécutent dans R et comparent ses χ², ddl, p, V, r, intervalles et effectifs à ceux de l'outil (même valeur à 10⁻⁶ près), et l'outil au corrigé de la base des analyses (numpy, à partir des formules).
- **Test t, ANOVA, régression** (`ddict.analysis.models`, étape 5) : test t de Welch (par défaut) ou de Student, les deux modalités dans l'ordre de leurs codes, différence des moyennes et son intervalle, d de Cohen (écart type combiné) et son intervalle par la loi t non centrale (chaque borne cherchée de son côté, avec la queue qui reste petite : une fonction de répartition proche de 1 perd sa précision) ; Mann-Whitney (approximation normale avec correction de continuité, comme `wilcox.test`) et corrélation bisériale de rang ; Levene centré sur la médiane, Shapiro-Wilk par groupe. ANOVA par ses sommes de carrés, η², ω², Tukey (statsmodels) ; Kruskal-Wallis et ε². Régression par statsmodels (OLS) : un prédicteur nominal en indicatrices, le plus petit code en référence ; β sur variables centrées réduites ; VIF ; Shapiro-Wilk des résidus ; refus quand la matrice des prédicteurs n'est pas de plein rang (un prédicteur se déduit exactement des autres). Vérifié contre le corrigé et contre les scripts R équivalents (à 10⁻⁶ près ; `uniroot` réglé à 10⁻¹⁰), et contre les exemples du catalogue.
- **Page « Analyses », rapport et `ddict analyser`** (`ddict.review.ui.analyses_view`, `ddict.analysis.report`, étape 6) : la page retrouve la base (ou la fait choisir), la lit une fois par séance et la prépare de nouveau quand une décision change l'empreinte du codebook ; on y choisit l'analyse, une variable ou plusieurs par rôle (seules celles dont le niveau de mesure convient sont proposées), les options, et, pour un test t sur un groupe de plus de deux modalités, les deux à comparer. Les conditions s'affichent avant le calcul (refus en rouge, bouton désactivé ; avertissements en jaune). Le résultat montre la phrase, les observations retenues et écartées, les avertissements et les tableaux. Trois fichiers : un rapport Markdown (variables, options, résultats, empreinte, date, versions de l'outil, de Python, de SciPy et de statsmodels), ses tableaux en Excel, et un `.zip` avec le script R équivalent, le fichier de commandes et le script de préparation ; écrits à côté du projet, ils portent le premier numéro libre (`<projet>-analyse-<n>`). `ddict analyser <projet> <analyse> --dependante … --groupe …` écrit les mêmes fichiers. Seule la dernière analyse est gardée, en mémoire (D-078).
- **IA conseillère** (`ddict.llm.advise`, `ddict.review.ui.advice_view`, `ddict.llm.advice_bench`, étape 7, D-073, D-079) : facultative et locale. Le message (consigne `advise-v2`, D-080) contient l'objectif écrit par l'équipe, tel quel (1 000 caractères au plus), le catalogue (clés, usages, rôles et niveaux acceptés, méthodes) et les variables utilisables, rangées par niveau de mesure, chacune [nom final, libellé coupé à 60 caractères] ; un groupe d'items est une seule entrée (libellé : le début commun des libellés de ses items, sinon sa description ; niveau ; noms des items ; score s'il est calculé) ; JSON compact ; ni valeur, ni statistique, ni identifiant, texte libre ou date. Un message de plus de 3 300 jetons estimés (3,5 caractères par jeton) n'est pas envoyé : il ne tiendrait pas, avec la réponse, dans les 4 096 jetons du modèle local. L'objectif est rappelé à la fin du message (`objective_again`) : après une longue liste de variables, le modèle le perdait de vue. La réponse suit un schéma strict (`extra="forbid"`) : au plus trois propositions, chacune une analyse du catalogue, des variables par rôle, une méthode de l'analyse ou « » et une raison courte ; aucun champ pour du code, un seuil, un résultat ou une référence. Le schéma envoyé au serveur est plus strict encore, pour que sa grammaire empêche les erreurs vues sur une vraie base : l'identifiant du message imposé ; pour chaque analyse, ses rôles dans l'ordre, chacun une fois, les rôles obligatoires exigés ; pour chaque rôle, seulement les variables dont le niveau convient, en nombre borné ; seulement les méthodes de l'analyse. Une analyse, un rôle, une variable ou une méthode inconnus refusent la réponse (un second essai, puis rien) ; les conditions du codebook sont vérifiées sur chaque proposition et une condition non remplie est signalée. Sur la page « Analyses », un encadré facultatif (absent sans l'option IA) montre ce qui serait envoyé, demande des propositions et les affiche ; « Reprendre cette proposition » remplit les choix de la page, seulement avec des variables que le codebook permet ; rien n'est calculé sans « Lancer l'analyse ». `ddict conseiller <projet> "<objectif>"` (avec `--apercu`) fait de même en ligne de commande. Les propositions restent en mémoire ; l'échange est gardé dans le dossier des envois. Le banc (`scripts/banc_conseil.py`) envoie les objectifs de `objectifs-analyses.json`, écrits pour la base des analyses avec l'analyse et les variables attendues, et compte les propositions justes.

## 16. Tableaux et figures APA 7 (v0.10)

Plan : `docs/plan-v0.10.md` ; fiches validées : `docs/tableaux-figures-apa.md` ; D-082 à D-086.

- **Description neutre** (`ddict.analysis.apa`, étape 2, D-083) : `describe(project, prepared, result, language=…)` rend un `ApaDocument`, ses `ApaTable` (clé stable `table-1`…, numéro, titre, colonnes alignées, en-têtes regroupés `Spanner`, lignes avec retrait, note) et ses `ApaFigure` (type `bars`, `grouped_bars`, `scatter` ou `coefficients`, catégories, séries avec les bornes de leurs barres d'erreur, points, droite, axes, ligne de référence, note). Un texte est une suite de `Run`, romains ou italiques : les symboles statistiques en italique, les lettres grecques en romain ; une note est une phrase entière traduite d'un bloc, avec ses symboles à leur place (`marked`). Les chiffres viennent du résultat de l'analyse (le *t* des coefficients, l'IC de β, les bornes de Tukey et les médianes de Mann-Whitney y sont ajoutés) ou des données préparées, avec les mêmes exclusions que l'analyse (moyennes et leur IC 95 % par la loi *t*, pourcentages par colonne, *M* et *ÉT* de chaque variable d'une corrélation, nuage de points). Conventions APA : deux décimales, trois pour *p*, sans zéro initial pour ce qui ne dépasse pas 1, crochets « [a ; b] » ou « [a, b] » selon la langue. `edited(document, edits)` applique le numéro, le titre et la note qu'une personne a changés (D-086), jamais les chiffres. Vérifié contre les fiches validées, chiffre par chiffre, et contre le résultat de chaque analyse et de chaque option.
- **Formats et Word** (`ddict.analysis.formats`, étape 3, D-083 à D-085) : un `Format` dit sa clé, son libellé, le suffixe du fichier, son type, ce qu'il rend (tableaux, figures) et deux fonctions, `render(document) -> bytes` et `read_text(bytes) -> str` ; `register` l'inscrit dans `FORMATS`, que la page et la ligne de commande lisent d'elles-mêmes ; `available(document)` donne ceux qui ont quelque chose à rendre. Les figures sont dessinées une fois pour tous les formats (`formats.figures`, matplotlib : Arial, gris, sans quadrillage ni cadre haut et droit, 16 cm, 300 points par pouce, virgule décimale en français). Le format Word (`formats.docx`, python-docx) : Times New Roman 12, marges de 2,54 cm ; chaque tableau, un vrai tableau Word sans grille, avec les filets APA par cellule (au-dessus et au-dessous de l'en-tête, filet court sous un en-tête regroupé, en bas) ; numéro en gras, titre en italique, note « *Note.* » ; largeurs de colonnes calculées pour que les chiffres ne se replient jamais (chaque colonne de chiffres d'abord, la première colonne prend le reste, puis les en-têtes) ; chaque figure, une image avec son numéro, son titre et sa note en texte ; à la fin, en petit, la phrase de résultat et l'empreinte du codebook. Le **test commun** (`tests/test_apa_formats.py`) rend chaque analyse et chaque option, en français et en anglais, dans chaque format inscrit, relit le fichier et y retrouve chaque en-tête, chaque cellule, chaque titre et chaque note ; il vérifie aussi que les changements d'une personne (numéro, titre, note) y passent. Vérifié aussi dans Word (conversion en PDF par Word, lue à l'écran). Avec python-docx arrive lxml, qu'openpyxl utilise dès qu'il est présent : les fichiers Excel écrits gardent leur contenu, mais pas leurs octets ; les exemples Excel du dépôt ont été régénérés (contenu identique, cellule par cellule).
- **Graphiques Excel natifs** (`formats.xlsx_charts`, étape 4, D-084) : un classeur `-graphiques.xlsx` par analyse qui a des figures, une feuille par figure : son numéro (gras) et son titre (italique) dans les cellules, puis le petit tableau de ses données, puis la note ; le graphique natif d'openpyxl, tiré de ce tableau, sans titre (il est dans les cellules), axes nommés et visibles, sans quadrillage, graduations sans décimales inutiles. Moyennes : barres verticales grises et barres d'erreur personnalisées (colonnes « IC 95 % (+) » et « (−) ») ; barres groupées : une série par catégorie des lignes, légende en bas ; nuage de points : les points, et la droite comme seconde série de deux points, l'axe horizontal commençant juste sous la plus petite valeur ; coefficients : barres horizontales des β (une barre négative reste grise) avec leur IC, le premier prédicteur en haut. Vérifié dans Excel (graphiques exportés en image par Excel, lus à l'écran) : axes, légende, barres d'erreur ; un document sans figure n'a pas de classeur (`available`).
- **Page et ligne de commande** (`ddict.review.ui.apa_view`, étape 5, D-086) : sous le résultat, la section « Tableaux et figures APA » ; pour chaque tableau et chaque figure, un encadré avec son numéro, son titre et sa note (champs propres à chaque analyse lancée : une nouvelle analyse repart des valeurs calculées) ; seul un champ changé compte (une note gardée telle quelle garde ses italiques) ; un aperçu (le tableau en HTML avec les filets APA seulement, la figure en image) ; un bouton de téléchargement par format de `available(document)`, les fichiers rendus une fois par état et gardés en mémoire. « Écrire à côté du projet » écrit aussi ces formats, avec les changements de la page (`report.write_apa`) : `<projet>-analyse-<n>.docx` et `-graphiques.xlsx` ; le numéro libre tient compte de tous les fichiers d'une analyse. `ddict analyser … --format docx xlsx` (par défaut tous ceux qui ont quelque chose à montrer, `aucun` pour aucun ; un format inconnu est refusé avant tout calcul). Vérifié : la page et la commande écrivent les mêmes fichiers ; un titre changé dans la page passe dans le fichier Word ; parcours dans le navigateur.

## 17. Le carnet d'analyses (v0.11)

Plan : `docs/plan-v0.11.md` ; fiche validée : `docs/carnet-analyses.md` ; D-087 à D-092.

- **Le modèle et le fichier** (`ddict.analysis.notebook`, étape 2) : `Notebook` (version de format `carnet_version` 1.0.0, lien au projet par le nom de son fichier et l'empreinte de la base, `next_id`, numéros de départ du document, entrées dans leur ordre, qui est leur rang) et `Entry` (identifiant `A<n>`, analyse, variables par rôle, options, titres et notes changés par élément, retenue, date d'ajout, dernier calcul confirmé `computed`, calcul en attente `pending`), tous `extra="forbid"`. Les variables sont gardées par leur **clé du projet** (`VariableRef` : nom d'origine, groupe d'un score, nom d'origine d'un item inversé) : `reference()` la tire d'un nom final, `resolve()` redonne le nom final en vigueur ou dit pourquoi elle ne mène plus à rien (`NotebookError` : variable retirée, cotation supprimée, item plus inversé). `computed()` garde les agrégats d'un résultat : statistiques finies triées, effectifs, phrase, avertissements, empreinte complète, date et versions. Le Tableau 1 et la corrélation à plusieurs variables gardent désormais leurs agrégats par position (`v1_m_1`, `v2_k1_total`, `r_2_1`…), jamais l'étendue observée. `add()` donne le prochain identifiant (jamais celui d'une entrée retirée), `remove()`, `move()`, `retain()`. Le fichier `<projet>-carnet.json` s'écrit comme le projet (JSON indenté de 2, ordre du modèle, UTF-8, LF, fichier temporaire puis remplacement) ; `load_notebook()` refuse une autre version majeure ou une version plus récente ; `belongs()` dit si le carnet est celui de la base du projet. Vérifié : l'exemple de la fiche, l'aller-retour octet pour octet, les références qui survivent à un renommage, et le test à chaînes témoins (les témoins `ZQX…` de la base du sommeil n'entrent jamais, ni les points d'un nuage, ni l'étendue observée).
- **Recalcul, comparaison, confirmation** (`ddict.analysis.notebook_check`, étape 3, D-089) : `check()` donne l'état d'une entrée. *À jour* : même empreinte du codebook ; *recalculée, inchangée* : l'empreinte a changé mais chaque statistique et chaque effectif sont égaux (à 10⁻⁹ près, relatif ; une clé que seul un côté possède, ajoutée par une autre version de l'outil, ne compte pas) : l'empreinte et la date de `computed` sont mises à jour ; *changée* : le nouveau calcul attend dans `pending`, et `differences()` le montre statistique par statistique, aux décimales de l'APA (sans zéro initial pour ce qui ne dépasse pas 1), avec plus de décimales quand l'APA montrerait deux nombres égaux ; *impossible* : une clé de variable ne mène plus à rien, ou les conditions du codebook refusent l'analyse (niveau de mesure qui ne convient plus…), avec la raison, sans rien supprimer ; *sans base* : base introuvable, ou carnet fait avec une autre base (`check_all`), rien ne se recalcule. Une décision reprise ramène l'entrée à « à jour » et efface son `pending`. `confirm()` remplace `computed` par `pending`. `blocking()` donne les entrées retenues changées et non confirmées, qui bloquent l'export. `always=True` recalcule même une entrée à jour : un export ne copie jamais le carnet. Vérifié sur le scénario de la fiche (le 999 de l'âge confirmé après coup : *n* de 200 à 197, *r* de ,04 à ,07, *p* de ,572 à ,342), un libellé corrigé (inchangée), une décision reprise, un niveau de mesure changé et une cotation retirée (impossibles), sans base.
- **Le document des résultats** (`ddict.analysis.notebook_export`, étape 4, D-089, D-090, D-092) : `ApaDocument` reçoit des `Section` (une par analyse : identifiant, intertitre « A2 — Test t : comparer deux groupes », phrase APA, tableaux, figures) et des lignes de clôture ; `assembled()` en fait un document dont `tables` et `figures` tiennent tout, dans l'ordre, si bien que le registre des formats et son test commun valent sans changement ; un document d'une seule analyse reste sans section. `results_document()` recalcule chaque analyse retenue (`check_all(always=True)`), refuse l'export (`ExportBlocked`) si une analyse retenue changée attend sa confirmation, numérote à la suite à partir de `first_table` et `first_figure` du carnet (`describe(first_table=…, first_figure=…)`), applique les titres et les notes des personnes (jamais leurs numéros, D-090), écarte une analyse impossible sans laisser de trou et le dit dans la clôture (empreinte, date et versions, liste des analyses avec leurs variables). `write_results()` écrit `<projet>-resultats.docx` et `-resultats-graphiques.xlsx`, remplacés à chaque export. Le format Word rend les sections, chaque intertitre au style APA de niveau 2 (gras, noir, police du document). Vérifié : la numérotation de la fiche, son changement quand l'ordre change, les numéros de départ, une analyse impossible écartée, un changement non confirmé qui bloque puis passe une fois confirmé, le test commun des formats sur un document de plusieurs analyses, en français et en anglais, et le rendu dans Word.
- **Le script R maître** (`rscript.r_master`, `notebook_export.r_bundle`, étape 5) : l'en-tête une seule fois (lecture de la base, fichier de commandes, script de préparation, `ddict_num`), puis chaque analyse retenue, dans l'ordre du carnet, dans son propre espace (`resultats$A2 <- local({ … ; resultats })`), pour que ses variables de travail ne se mêlent pas à celles des autres. Le document et le script partent du même recalcul (`_results`) : une analyse écartée de l'un l'est de l'autre. `<projet>-resultats-R.zip` contient `<projet>-resultats.R`, le fichier de commandes et le script de préparation. Les corps R ont été complétés : la corrélation calcule **toutes les paires** (elle ne calculait que la première, défaut trouvé en préparant le plan), avec les clés par position (`r_2_1`, `low_2_1`…) et, pour deux variables, celles de la v0.9 ; le Tableau 1 donne ses agrégats par position (`v1_m_1`, `v2_k1_total`…, le code d'une colonne écrit comme dans l'outil par `ddict_cle`) ; Tukey donne ses bornes (`tukey_low_…`, `tukey_high_…`). Vérifié dans R sur treize analyses de la base fictive des analyses, toutes les options du catalogue : chaque statistique que R donne est égale à celle de l'outil à 10⁻⁶ près (plus de 150 valeurs comparées).
- **La page et les commandes** (`review/ui/notebook_view.py`, `ddict carnet`, `ddict resultats`, étape 6) : la page « Carnet », après « Analyses », lit le carnet dans son fichier à chaque affichage et l'écrit aussitôt après chaque changement, comme le projet ; son recalcul est gardé pour la séance tant que ni les décisions ni le carnet ne changent, et le carnet est écrit quand le recalcul l'a changé (nouvelle empreinte, calcul en attente). La base se retrouve comme sur la page « Analyses » (`analyses_view.prepared_data`). Le bouton **Ajouter au carnet** de la page « Analyses » garde les titres et les notes de `apa_view.edits()`. Une entrée garde ses rôles dans l'ordre du catalogue, quel que soit l'ordre du choix : la page et la ligne de commande écrivent ainsi les mêmes fichiers (script R identique à l'octet, même texte Word ; vérifié par un test et dans le navigateur). `ddict carnet` n'écrit pas de carnet vide. Essai sur une vraie base : `docs/essais/2026-10-16-essai-carnet.md`.

## 18. La section Méthode (v0.12)

Plan : `docs/plan-v0.12.md` ; fiche validée : `docs/methode-gabarits.md` ; D-093 à D-100. Base fictive : `etude-passation.sav` et son corrigé (`scripts/generer_base_passation.py`, étape 2).

- **Les règles d'exclusion** (étape 3, D-093, D-094). Le projet passe au format 0.4.0 : `exclusions` (`next_id`, `rules`), une liste ordonnée de règles, chacune d'une sorte (`condition`, `completeness`, `duration`, `straightlining`, `duplicate`), avec son identifiant `E<n>` jamais redonné, sa raison et, pour une durée, sa source obligatoire (modèles `extra="forbid"`, union discriminée par `kind`). Un projet 0.3.0 s'ouvre tel quel, sans règle. `ddict.project.exclusions` ajoute, retire et ordonne les règles et dit pourquoi une règle est refusée : une condition sur une valeur d'un identifiant ou d'un texte libre (elle nommerait une personne), une variable ou un groupe inconnus, une comparaison par plus petit ou plus grand sur un texte, une durée entre des variables qui ne sont pas des dates enregistrées comme dates, une complétude qui exige plus d'items que le groupe n'en a, une ligne droite sur une grille de moins de 4 items, une cotation absente pour une condition sur un score. Seule la règle des doublons compare des identifiants, entre les lignes. `ddict.analysis.exclusions` applique les règles dans leur rang, après les codes manquants, les noms, les items inversés et les scores : `ranks()` donne 0 pour une personne gardée, sinon le rang de la première règle qui l'exclut ; une valeur manquante ne remplit jamais une condition, sauf `missing` ; un doublon est une réponse plus tardive qui répète une précédente sur des variables toutes présentes. `apply_decisions` ne garde que les personnes gardées et donne le flux (`PreparedData.flow` : *N* de départ, exclus par règle, *N* analysé) ; les dates y restent des dates. Les règles entrent dans l'empreinte du codebook, seulement quand il y en a : un projet sans règle garde son empreinte. Le script de préparation SPSS et R les écrit à la suite des scores (`ddict_exclusion`, ses effectifs, puis la sélection ; les doublons par tri et `MATCH FILES` en SPSS, dans l'ordre du fichier) ; le script R maître du carnet les applique donc aussi. La copie documentée garde tout le monde. Vérifié sur la base de passation : les effectifs du corrigé dans l'outil, dans PSPP et dans R, dans deux ordres des règles, et le script R maître qui redonne la corrélation de l'outil sur les 347 personnes gardées.
- **Le diagramme de flux** (étape 4, D-098). La description APA reçoit une sorte de figure `flow` : le *N* de départ et, pour chaque règle dans son rang (`FlowStep`), son identifiant, sa raison, les personnes qu'elle a exclues et celles qui restent. `apa.describe_flow(project, prepared.flow)` la construit ; sans règle, pas de diagramme. Dans Word, une image dessinée comme les autres figures (16 cm, 300 points par pouce, Arial) : la boîte des réponses reçues, la boîte de l'échantillon analysé, une flèche de l'une à l'autre et, à droite, une seule boîte des exclusions, leur total puis chaque raison avec son effectif, coupée à 38 caractères sans jamais séparer « (*n* = 14) » ; *N* et *n* en italique ; la hauteur suit le nombre de lignes. Dans Excel, la feuille de la figure porte le tableau de ses effectifs (étape, raison, exclues, restantes), sans graphique. Vérifié : les effectifs du corrigé dans deux ordres, le test commun des formats, le tableau d'Excel, une image identique d'un rendu à l'autre, et le rendu dans Word et Excel.
