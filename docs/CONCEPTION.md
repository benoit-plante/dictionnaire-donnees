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

### 7.5 macOS (v0.5, étape 6)

- `installer.command` et `desinstaller.command` (bash, fins de ligne LF, marqués exécutables dans le dépôt) font sous macOS ce que font `installer.bat` et `desinstaller.bat` : uv, l'outil, l'outil ouvert fermé avec l'accord de la personne, l'icône, Ollama. L'icône est un fichier `.command` dans Applications et sur le bureau : un double-clic ouvre une fenêtre de Terminal qui fait tourner l'outil, et fermer la fenêtre l'arrête. Réglages dans `~/Library/Application Support/ddict`.
- Vérification (D-035) : `.github/workflows/macos.yml`, lancé à la main. Premier passage réussi le 2026-10-14 sur macOS 26 (Apple Silicon) : tests, installation, interface qui répond, installateur arrêté proprement quand l'outil est ouvert, désinstallation. Ce passage a fait trouver deux écarts du générateur d'exemples entre Windows et macOS (marque de système dans le zip, sauts de ligne dans une cellule), corrigés. Restent à voir sur un vrai Mac : l'icône, la fenêtre « Ouvrir » et les avertissements de sécurité de macOS.

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
