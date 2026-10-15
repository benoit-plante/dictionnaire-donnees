# Plan de la v0.8

> Statut : **validé par l'auteur le 2026-10-15**, avec toutes les recommandations du § 8 (D-057 à D-065), l'utilité sans IA présentée d'abord. Repris du plan « contrat d'analyse » rédigé avant la v0.7 et reporté par D-043, mis à jour pour ce que la v0.7 a ajouté (exports de plateforme, renommage, format 0.2.0).

## 1. Pourquoi cette version

Jusqu'à la v0.7, l'outil aide à **décrire** une base (le codebook) et à **appliquer** ces décisions aux données (fichiers de commandes, copie documentée). La v0.8 aide à les **utiliser** en analyse : « du dictionnaire à l'analyse ».

**D'abord pour l'équipe qui analyse elle-même, avec ou sans IA.** Certaines informations dont dépend une analyse juste manquent encore au codebook, ou n'y sont qu'en texte libre : la cotation des échelles sous une forme exploitable (quels items, lesquels inverser, somme ou moyenne, combien d'items répondus au minimum), le niveau de mesure d'un CSV (et le niveau `scale` douteux des items de grille, seulement signalé en v0.7), ce que représente une ligne de la base, ce qui reste non documenté. Et le calcul des scores, avec ses items inversés, reste une source d'erreurs fréquente quand on le fait à la main dans SPSS ou R : un script de préparation tiré des décisions de l'équipe la prolonge naturellement des fichiers de commandes de la v0.4.

**Ensuite pour un usage qui existe déjà : l'IA générative qui aide à écrire le code d'analyse**, locale ou infonuagique. Le contenu du codebook est ce qu'il faut à un modèle, et souvent ce qu'il invente quand on ne le lui donne pas : codes et étiquettes, manquants déclarés et codes suspects tranchés par l'équipe, texte exact des questions, items inversés confirmés, étendues et seuils sourcés, glossaire, classe de confidentialité, noms lisibles, sens d'une case vide dans une question à cocher. La forme, elle, n'est pas faite pour ce lecteur. Mesures du 2026-10-15, version 0.7.1, exports de travail (environ 4 caractères par token) :

| Livrable | Étude du sommeil (34 variables) | Export SurveyMonkey fictif (55 variables) | Limite pour l'analyse |
|---|---|---|---|
| Codebook Excel | 22 Ko, 6 onglets | 27 Ko | fait pour des humains, illisible tel quel par un modèle |
| Rapport Markdown | 18 Ko, ≈ 135 tokens par variable | 32 Ko, ≈ 145 tokens par variable | verbeux, statistiques mêlées aux décisions ; ≈ 55 000 tokens pour 400 variables |
| Fichier projet `.dd.json` | 132 Ko, ≈ 970 tokens par variable | 196 Ko, ≈ 890 tokens par variable | format de travail : provenance, propositions rejetées, appels IA |

Un modèle local de 7 à 8 milliards de paramètres (carte de 8 Go) travaille bien avec 8 000 à 16 000 tokens : le codebook d'une vraie base n'y entre pas.

La v0.8 fait donc du codebook un **contrat d'analyse** : ce qu'il faut pour analyser correctement la base, sous des formes utiles à une personne (cotation, script de préparation, niveau de mesure, complétude, empreinte) et à une machine (un export compact, au format standard Frictionless, utile aussi pour un dépôt de données). Les deux usages reposent sur les mêmes décisions de l'équipe.

Le principe de l'outil se prolonge sans changer : **le modèle ne voit jamais les données ; il écrit du code, ce code s'exécute sur le poste, et seuls des agrégats filtrés reviennent.** Un assistant d'analyse qui lirait ce contrat n'est qu'une piste, pour un projet distinct (§ 2.3) : la v0.8 ne dépend pas de lui.

## 2. Contenu proposé

### 2.1 Dans `dictionnaire-donnees` (v0.8)

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Export « contexte d'analyse »** : un `datapackage.json` (Frictionless Table Schema, avec des propriétés d'extension pour ce que le standard ne couvre pas) et un `<base>-contexte.md` compact, une ligne par variable, valeurs acceptées seulement, règles explicites (« 999 → manquant », « case vide d'une question à cocher → non cochée ») | Un fichier à donner tel quel à un modèle, ou à lire par un programme ; le standard Frictionless facilite aussi le dépôt (Borealis) |
| B | **Cotation structurée** des groupes : items, items inversés et règle d'inversion, somme ou moyenne, nombre minimal d'items répondus, étendue du score ; chaque élément avec sa source | Le score se calcule sans deviner, par un programme ou par un modèle |
| C | **Niveau de mesure modifiable** : proposé par le calcul quand le fichier n'en a pas (CSV, Excel) ou quand le niveau déclaré est douteux (item étiqueté d'une grille déclaré `scale`, signalé depuis la v0.7), décidé par une personne | Le choix des analyses repose sur un niveau de mesure connu |
| D | **Métadonnées de la base** : ce que représente une ligne (participant, observation, dyade…), structure longitudinale (une vague par fichier, format large avec suffixes, format long avec variable de temps), variables de plan (vague, grappe, pondération, identifiant de regroupement) | Un modèle ne traite plus des mesures répétées comme des participants indépendants |
| E | **Complétude du codebook** en tête de chaque export : part des variables avec question, libellé, étiquettes, niveau de mesure et nom acceptés ; liste de ce qui reste non documenté | Ce qui est absent est dit absent, et non comblé par le modèle |
| F | **Script de préparation généré sans IA** (SPSS et R) : déclaration des manquants confirmés, inversion des items confirmés, calcul des scores selon la cotation sourcée (B), dans de **nouvelles** variables (`_inv`, score) | La préparation, source d'erreurs fréquentes, ne dépend plus d'un modèle |
| G | **Empreinte du codebook** dans chaque export et en tête de chaque script généré | On sait toujours sur quelles décisions repose un résultat |

### 2.2 Plus tard (proposé pour la v0.9, à confirmer après la v0.8)

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| H | **Base synthétique** générée à partir du codebook seul : même structure, mêmes codes, mêmes taux de manquants, distributions marginales proches ; marquée fictive dans son nom et son étiquette | On écrit et débogue le code d'analyse, avec n'importe quel assistant, sans exposer les données ; le script final s'exécute sur la vraie base, sur le poste |
| I | **Filtres du questionnaire** (« si oui à Q5, passez à Q8 ») : saisis par une personne, ou repérés dans le questionnaire et proposés | Les manquants structurels sont distingués des non-réponses |

La base synthétique (H) dépend de l'export (A) et de la cotation (B) ; les filtres (I) demandent un travail de lecture du questionnaire qui mérite sa propre version.

### 2.3 Hors de cet outil : un assistant d'analyse distinct

Ces fonctions consomment le contexte d'analyse (A) mais n'appartiennent pas à un outil de documentation. Elles formeraient un projet séparé, dans l'esprit d'outils autonomes qui partagent un format :

| Fonction | Rôle de l'IA | Note |
|---|---|---|
| **Vérificateur de scripts** : un script R, SPSS ou Python est confronté au codebook (variable avec code 999 non traité, items sommés sans inversion, variable nominale traitée comme continue, variable sensible dans une sortie) | Faible : l'essentiel se fait par analyse du code ; le modèle tranche les cas ambigus | Le garde-fou qui rend l'usage de l'IA défendable, comme la porte de confidentialité ici |
| **Boucle d'analyse locale** : le modèle écrit le code, le poste l'exécute, les sorties passent par une porte de confidentialité (seuil, masquage par soustraction) avant de revenir au modèle | Central | Exige un modèle local ; la porte de `ddict.privacy` peut servir de modèle |
| **Interprétation des sorties** dans les unités et étiquettes réelles, avec le sens des items inversés | Central | Évite les erreurs de sens sur les échelles inversées |
| **Rédaction de la section Méthode** et du gabarit du tableau 1 à partir des seuls éléments sourcés | Central | Un instrument sans source reste un trou signalé, jamais une citation inventée |
| **Recherche de variables en langage courant** (« quelles variables mesurent le soutien social ? ») | Faible : modèle d'*embeddings* local | Pourrait aussi revenir dans `dictionnaire-donnees` plus tard |
| **Vérification d'un plan d'analyse** : concepts des hypothèses reliés aux variables, faisabilité selon les lignes complètes | Central | Soutien au préenregistrement |
| **Harmonisation entre études** : appariement de deux codebooks, changements signalés | Faible pour les cas évidents, proposition pour les cas douteux | Entre vagues d'une même étude, c'est déjà fait par la v0.7 (D-052) |
| **Plan de gestion des données, README de dépôt** | Moyen | Alimentés par le contexte d'analyse |

Ces pistes sont notées ici pour garder la cohérence du format ; elles ne font pas partie de la v0.8.

**Aussi hors de cette version**, déjà notés ailleurs : une vraie application Mac sans Terminal (D-055) ; LimeSurvey, Qualtrics et REDCap ; les grilles de menus déroulants de SurveyMonkey ; la relecture de l'anglais par une personne anglophone.

## 3. Conception

### 3.1 Export « contexte d'analyse » (A)

**Deux fichiers, une même source** (`ddict.export.context`) :

- `datapackage.json` : une ressource (la base, par son nom et son empreinte, jamais son chemin) et son Table Schema. Champs standard utilisés : `name`, `title` (libellé), `description`, `type`, `format`, `constraints` (étendue **théorique sourcée** seulement, jamais l'étendue observée), `missingValues`, `categories` et `categoriesOrdered` pour les étiquettes de valeurs. Les propriétés propres à l'outil vont dans un espace de noms (`ddict:original_name`, `ddict:question`, `ddict:question_text`, `ddict:group`, `ddict:measure_level`, `ddict:unit`, `ddict:privacy_class`, `ddict:scoring`, `ddict:dataset`, `ddict:multiple_response`). La version du standard visée (Data Package 2.0 de 2024, qui a ajouté `categories` et les `missingValues` par champ, à notre connaissance) est **à vérifier à l'étape 1** contre la spécification publiée.
- `<base>-contexte.md` : pensé pour être collé dans un modèle. En tête : la base, ses métadonnées (D), la complétude (E), l'empreinte du codebook (G), les règles générales (« les codes listés en manquants sont à traiter comme manquants ; les items inversés confirmés sont à inverser avant tout score ; dans une question à cocher, une case vide est une option non cochée, sauf si toutes les cases de la question sont vides »). Puis les groupes avec leur cotation (B), puis un tableau d'une ligne par variable : nom, libellé, type, niveau de mesure, unité, codes et étiquettes, codes manquants, groupe, référence de la question. Le texte complet des questions vient dans une section à part, omis pour les groupes protégés (D-014).

**Les noms (v0.7)** : le contexte décrit les variables par leur **nom final** (le nouveau nom accepté, sinon le nom d'origine), avec le nom d'origine en propriété. Quand des variables sont renommées, l'en-tête dit sur quel fichier travailler : la copie documentée, ou la base après le fichier de commandes (qui renomme en premier, v0.7). La ressource désigne alors la copie documentée par son nom ; son empreinte n'est connue que si elle a été écrite (sinon : « à écrire »).

**Ce qui n'y est pas** : propositions en attente ou rejetées, statuts, appels IA, provenance détaillée (elle reste dans l'Excel), observations individuelles.

**Statistiques descriptives** : absentes par défaut. Une case de la page « Export » (et `--avec-statistiques`, `--with-statistics`) les ajoute, déjà filtrées par la porte de confidentialité comme dans les autres exports. Sans elles, le contexte ne contient que des métadonnées ; c'est la version à envisager avec un modèle hors du poste, sous réserve de ce que permet le certificat d'éthique de l'étude.

**Taille visée** : au plus 60 tokens par variable en moyenne dans le Markdown, sans le texte des questions, mesuré sur les bases fictives (compte approché : caractères divisés par 4, sans dépendance de découpage en tokens) et, par un test `reel`, sur les vraies bases (le seul nombre de tokens par variable, D-046).

**Une seule version** : le contexte d'analyse est toujours « final » (valeurs acceptées seulement). Ce qui n'est pas décidé apparaît comme non documenté (E). Il suit la langue du codebook choisie à l'export, comme les autres exports (v0.5).

### 3.2 Cotation structurée (B)

Le champ `scoring` d'un groupe (texte sourcé) devient un objet, toujours humain et sourcé (principe 4) :

```json
{
  "items": ["sommeil_q1", "…", "sommeil_q8"],
  "reverse_items": ["sommeil_q3", "sommeil_q6"],
  "reverse_rule": "max_plus_min_minus_x",
  "aggregation": "sum",
  "min_items_answered": 7,
  "score_range": {"min": 8, "max": 40},
  "score_name": "sommeil_total",
  "source": "Manuel de l'instrument, p. 4"
}
```

- Les items sont désignés par leur **nom d'origine** dans le projet (la clé, D-048) ; les exports et le script les écrivent sous leur nom final.
- `aggregation` : `sum` ou `mean` ; `reverse_rule` : `max_plus_min_minus_x` (seule règle pour commencer, avec le minimum et le maximum de l'échelle tirés des étiquettes de valeurs acceptées, ou saisis) ; `min_items_answered` facultatif (sans lui, le score exige tous les items).
- Le texte libre actuel reste possible (`note`) pour une cotation qui n'entre pas dans ce cadre ; le script de préparation (F) ne calcule alors pas ce score et le dit.
- Le modèle ne propose jamais de cotation (principe 4) ; le calcul peut seulement pré-remplir les items et les items inversés **confirmés** déjà présents dans le projet.
- Un groupe « réponses multiples » (D-044) n'a pas de cotation : ses options ne forment pas une échelle.
- Le fichier projet passe en `schema_version` 0.3.0 : les projets 0.1.0 et 0.2.0 s'ouvrent et se convertissent (le texte libre devient `note`). C'est la première conversion du format : jusqu'ici, les champs nouveaux avaient tous une valeur par défaut (D-048).

### 3.3 Niveau de mesure modifiable (C)

- Nouveau champ `measure_level` suivi (`TrackedValue`) dans chaque variable, d'origine `file` quand le fichier en a un.
- Le calcul propose (origine `computed`, statut proposé, accepté par une personne comme les étiquettes tirées du questionnaire, D-016) :
  - sans niveau dans le fichier : `nominal` pour un code étiqueté sans ordre évident ou une variable binaire, `ordinal` pour des codes étiquetés membres d'un groupe d'items, `scale` pour un entier ou un décimal sans étiquettes ; un texte libre ou un identifiant n'en reçoit pas ;
  - avec un niveau douteux (le signal de la v0.7 : item d'une grille dont toutes les valeurs observées ont une étiquette, déclaré `scale`) : `ordinal`, à côté du niveau du fichier, qui reste tant qu'une personne n'a pas décidé.
- Les fichiers de commandes, la copie documentée et le contexte d'analyse utilisent le niveau accepté.

### 3.4 Métadonnées de la base (D)

Un objet `dataset` dans le projet, rempli par une personne sur la page « Base » :

- `unit_of_observation` : participant, observation répétée, dyade, famille, autre (texte) ;
- `structure` : transversale ; longitudinale, une vague par fichier (avec la vague de ce fichier) ; longitudinale en format large (avec les suffixes de temps, par exemple `_t1`, `_t2`) ; longitudinale en format long (avec la variable de temps) ;
- `design_variables` : identifiant de regroupement, variable de temps, vague, grappe, pondération (des noms de variables) ;
- `description` : texte libre court.

Le calcul peut **proposer** : la structure « une vague par fichier » quand une marque de vague est réglée sur la page « Noms » (v0.7) ; le format large quand des suffixes de temps reviennent sur des noms semblables. Une personne décide.

### 3.5 Complétude (E)

Calculée à l'export, sans être enregistrée : pour chaque élément (question, libellé, étiquettes de valeurs pour les variables codées, niveau de mesure, nom quand un renommage est commencé, cotation pour les groupes d'échelle), le nombre de variables où il est accepté, sur le nombre où il s'applique. Affichée en tête de chaque export, et sur la page « Base » ; le tableau de bord continue de dire ce qui attend une décision.

### 3.6 Script de préparation (F)

- Nouveau fichier par logiciel, à côté des fichiers de commandes : `<base>-preparation.sps` et `<base>-preparation.R`. Il s'exécute **après** le fichier de commandes (ou sur la copie documentée), donc sur les noms finaux ; son en-tête le dit et vérifie que les variables attendues existent.
- Contenu, dans l'ordre : création d'une variable inversée `<item>_inv` pour chaque item inversé confirmé ; calcul des scores selon la cotation structurée (B), avec la règle d'items minimum ; les codes manquants sont déjà déclarés par le fichier de commandes et exclus des calculs.
- **Aucune variable d'origine n'est modifiée.** D-025 interdit de recoder les valeurs, même sur une copie ; ici, on crée de nouvelles variables, que l'équipe exécute dans son logiciel. Ce point élargit D-025 et demande une décision (D-062).
- Quand la base contient déjà un score (`sum_of_group`, D-039), le script compare le score recalculé à celui de la base et signale les écarts, sans rien remplacer.
- Vérification comme pour la v0.4 : le script R appliqué au CSV fictif donne les scores attendus du corrigé ; la syntaxe SPSS est exécutée dans PSPP.

### 3.7 Empreinte du codebook (G)

- Empreinte SHA-256 du contenu décidé (les valeurs acceptées, noms compris, dans l'ordre déterministe du fichier projet, sans les dates de modification), courte (12 caractères) pour l'affichage.
- Écrite dans l'onglet « Informations », l'en-tête du rapport, le contexte d'analyse, la table de correspondance des noms et le commentaire d'en-tête de chaque script généré.
- Deux codebooks qui portent les mêmes décisions ont la même empreinte.

### 3.8 Validation du `datapackage.json`

Les tests valident le fichier contre le schéma JSON publié de la spécification, gardé dans `tests/` (le réseau est bloqué pendant les tests), avec `jsonschema` (MIT) en dépendance de développement seulement. La licence du schéma est à vérifier à l'étape 1 avant de le copier ; à défaut, le test vérifie les champs utilisés un par un. Aucune nouvelle dépendance d'exécution.

## 4. Données d'essai

- **Bases fictives existantes** : l'étude du sommeil (avec son corrigé, complété des scores attendus et de leur cotation inventée, sourcée par une référence fictive clairement marquée comme telle), l'enquête auprès de familles (CSV sans niveaux de mesure : propositions du § 3.3), l'export SurveyMonkey fictif (questions à cocher, renommage, vagues).
- **Vraies bases** (D-046) : seulement le nombre de tokens par variable du contexte et la part de niveaux de mesure proposés ; aucune valeur, étiquette ni texte.

## 5. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Vérifier la spécification Frictionless visée et la licence de son schéma ; fixer le format du contexte d'analyse dans `CONCEPTION.md` | Exemple complet du `datapackage.json` et du Markdown pour la base du sommeil et pour l'export SurveyMonkey renommé, validé par l'auteur |
| 2 | Empreinte du codebook (G) | Même empreinte pour deux projets aux mêmes décisions, différente après une décision (test) |
| 3 | Niveau de mesure modifiable (C) ; format 0.3.0 et conversion des projets 0.1.0 et 0.2.0 | Les variables des CSV fictifs reçoivent une proposition ; les items de grille SurveyMonkey reçoivent `ordinal` ; les projets des versions précédentes s'ouvrent sans perte (test) |
| 4 | Cotation structurée (B) et métadonnées de la base (D), dans le modèle et l'interface | Saisie et relecture dans le navigateur ; une cotation sans source est refusée (test) |
| 5 | Complétude (E) dans les exports et sur la page « Base » | Chiffres justes sur les bases fictives à moitié révisées (test) |
| 6 | Export « contexte d'analyse » (A), interface et ligne de commande | Fichiers de référence comparés octet par octet ; `datapackage.json` valide ; ≤ 60 tokens par variable en moyenne ; `reel` : le nombre de tokens par variable des vraies bases consigné |
| 7 | Script de préparation (F) | Scores du CSV fictif égaux au corrigé avec R ; syntaxe exécutée dans PSPP ; écart signalé avec un score présent dans la base (test) |
| 8 | Essai : un modèle local écrit une analyse simple à partir du seul contexte d'analyse, sur la base du sommeil | Essai consigné dans `docs/essais/` : erreurs du modèle avec le rapport Markdown actuel, puis avec le contexte d'analyse |
| 9 | Guides, journal des changements, version 0.8.0 | Scénario refait dans le navigateur ; guides à jour en français et en anglais |

L'étape 8 n'est pas un banc automatisé : c'est un premier essai, qui dira si un banc d'analyse (bases fictives aux effets connus, comme le corrigé des rattachements) vaut la peine plus tard.

## 6. Risques

- **Un contexte d'analyse pris pour une autorisation de tout envoyer.** Le contexte sans statistiques ne contient que des métadonnées, mais le texte des questions, les noms de variables et la description de la base peuvent rester sensibles pour certaines études. Le guide le dit clairement : ce qui peut sortir du poste relève du certificat d'éthique et de l'équipe, pas de l'outil.
- **Une cotation saisie fausse se propage partout** (script de préparation, contexte, futur assistant). La source est obligatoire, et le script compare le score recalculé à un score déjà présent dans la base quand il existe (D-039).
- **Première conversion du format du projet** (0.3.0). Un projet converti ne s'ouvre plus avec la 0.7 ; le guide le dit, et la conversion est testée sur des projets de chaque version.
- **Noms et fichiers** : avec le renommage, le contexte et le script désignent les noms finaux, alors que la base d'origine garde les siens. L'en-tête de chaque fichier dit lequel utiliser ; le script vérifie la présence des variables avant tout calcul.
- **Le standard Frictionless évolue.** Les propriétés d'extension sont dans un espace de noms ; le Markdown, lui, ne dépend d'aucun standard.
- **Version trop chargée.** Si l'étape 4 s'allonge, les métadonnées de la base (D) passent en 0.8.x ; l'export (A), la cotation (B) et le script de préparation (F) forment le cœur.

## 7. Ce qui ne change pas

- Le modèle ne reçoit jamais de données individuelles ; l'outil n'écrit des données de participants que dans la copie documentée (D-026), et la future base synthétique ne sera générée qu'à partir du fichier projet, jamais du tableau.
- L'IA reste facultative : tout ce plan fonctionne sans modèle installé.
- Aucune valeur d'origine n'est recodée ; le fichier d'origine n'est jamais modifié.

## 8. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-057 | **Périmètre de la v0.8** | Le codebook comme contrat d'analyse (A à G) ; la base synthétique et les filtres du questionnaire proposés pour la v0.9 ; l'assistant d'analyse comme projet distinct. |
| D-058 | **Format du contexte d'analyse** | Frictionless Table Schema avec propriétés d'extension, plus un Markdown compact ; pas de format maison seul, pas de DDI pour l'instant. Variables désignées par leur nom final, avec le nom d'origine. |
| D-059 | **Statistiques dans le contexte d'analyse** | Absentes par défaut, ajoutées sur demande, toujours filtrées par la porte de confidentialité. |
| D-060 | **Cotation structurée** | Objet structuré, humain et sourcé ; le modèle ne la propose jamais ; le texte libre reste possible en note ; aucune cotation pour un groupe « réponses multiples ». |
| D-061 | **Format du projet 0.3.0** | Conversion à l'ouverture des projets 0.1.0 et 0.2.0 (le texte de cotation devient une note) ; un projet converti ne s'ouvre plus avec une version plus ancienne. |
| D-062 | **Script de préparation** | Oui, avec de nouvelles variables (`_inv`, scores) et sans modifier les variables d'origine ; D-025 est élargi en ce sens. Exécuté après le fichier de commandes, sur les noms finaux. |
| D-063 | **Niveau de mesure** | Modifiable ; proposé par le calcul quand le fichier n'en a pas ou quand le niveau `scale` d'un item de grille est douteux (la question laissée ouverte par la v0.7) ; décidé par une personne. |
| D-064 | **Métadonnées de la base** | Saisies par une personne ; seules la structure « une vague par fichier » (d'après la marque de vague) et la structure en format large peuvent être proposées par le calcul. |
| D-065 | **Assistant d'analyse** | Projet distinct, qui lit le contexte d'analyse ; aucune exécution de code d'analyse dans `dictionnaire-donnees`. |
