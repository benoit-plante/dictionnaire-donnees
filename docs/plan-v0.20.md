# Plan de la v0.20 — Concevoir le questionnaire

> Statut : **validé par l'auteur le 2026-10-19**, avec toutes les recommandations du § 13 : le module passe après la v0.19 ; le travail est coupé en deux versions (§ 2), la **v0.20** sans sources ni IA (parties A, B, D et E de la demande) et la **v0.21** (sources, vérification mot pour mot, IA ; parties C et F), esquissée au § 11 ; décisions D-143 à D-155 adoptées (D-143, D-144 et D-147 s'appliquent en v0.21). L'auteur utilise **LimeSurvey Cloud, version 7** (§ 5.5). Le numéro 0.20 suppose la v0.19 faite avant ; il change si l'ordre change.

## 0. Avant ou après la v0.19

**Après**, comme le pense l'auteur, pour trois raisons :

1. « Concevoir un questionnaire » est une manière de commencer une étude : sa place est dans « Nouvelle étude ». Le faire avant obligerait à mettre un bouton sur l'accueil, puis à le déplacer.
2. Les sources (v0.21) vont naturellement dans `instruments/` et le dépôt de documents du dossier d'étude ; faites avant, elles auraient leur propre dossier, à fondre ensuite.
3. La version « pour le comité d'éthique » du Word rejoint la fiche éthique.

Deux réserves. **La v0.19 n'a pas encore de plan** (`docs/plan-v0.19.md` n'existe pas, et aucun document n'en parle) : ce plan-ci ne peut donc pas s'appuyer sur ses choix, et je les note comme hypothèses (§ 5.4). Je propose que le plan de la v0.19 réserve deux choses : une étape « Concevoir le questionnaire » dans « Nouvelle étude », et le dossier `instruments/` pour les sources. Ensuite, le découpage du § 2 réduit le lien : **la v0.20 n'a pas besoin du dossier d'étude** (elle n'a pas de sources). Si la v0.19 prend du retard, la v0.20 peut passer avant elle avec un seul bouton sur l'accueil, à déplacer ensuite.

## 1. Pourquoi cette version

Aujourd'hui, l'outil part d'une base qui existe déjà et devine après coup quelle variable répond à quelle question (rattachement, D-013 ; structure de plateforme, v0.7). Pour une étude qui n'a pas encore de questionnaire, tout ce travail peut être évité : si le questionnaire est construit dans l'outil, chaque variable est connue **avant** la collecte, avec son nom, ses codes et sa question. Quand la base arrive, l'outil ne devine plus : il vérifie que la base est conforme à ce qui était prévu.

Le principe : **l'IA recopie, le calcul vérifie, une personne décide.** La v0.20 en fait la partie « le calcul vérifie, une personne décide », sans IA ; la v0.21 ajoute « l'IA recopie ».

## 2. Le découpage proposé

La demande, entière, fait environ 25 étapes, près du double de la v0.18 (14). Je propose deux versions, chacune utile seule :

| Version | Contenu | Ce qu'une équipe peut faire à la fin |
|---|---|---|
| **v0.20** | A (lire un `.lss`, LimeSurvey dans `platforms`), B (projet sans base, questionnaire structuré, variables prévues), D (phase « Concevoir » : Questionnaire, Relecture, Publier), E (aperçu, Word, fichier LimeSurvey, boucle, « La base est arrivée »). **Aucune IA, aucune source déposée.** | Taper son questionnaire, le relire, produire le Word et le fichier LimeSurvey, l'importer, comparer le réexport, documenter la base dès son arrivée. |
| **v0.21** | C (sources, pages exclues, vérification mot pour mot) et F (extraction d'un instrument, questions propres à l'étude, relecture des formulations, banc). | Déposer ses sources ; voir chaque item « retrouvé, p. 4 » ; faire extraire un instrument par l'IA, vérifié avant d'être montré. |

Pourquoi C avec F, et non avec la v0.20 : la vérification mot pour mot sert surtout à juger ce que l'IA propose, et la page « Sources » porte « Ce qui part » ; les deux se conçoivent et se testent ensemble (chaînes témoins sur les pages exclues). En v0.20, la provenance d'un item tapé reste dite par l'équipe (« Manuel, p. 4 », un texte), sans vérification ; la v0.21 la vérifie. La partie C ne demande pas l'IA : elle reste dans le paquet de base, et seul F demande l'option `ia`.

## 3. Ce qui ne change pas

- **Les six règles du `CLAUDE.md`** restent entières en v0.20 ; seule la règle 4 recevra, en v0.21, l'exception proposée au § 11.1 (D-143), après validation.
- **Un projet existant s'ouvre tel quel** et se comporte comme aujourd'hui : même navigation, même page d'ouverture (« Base »), même codebook, même empreinte du codebook (§ 6.8).
- La chaîne lire → profiler → exporter, le rattachement, le renommage, les analyses, le carnet, l'ébauche d'article, le contrôle à l'écriture (D-129, D-130) et l'IA de la v0.18.
- Le Word et le fichier LimeSurvey sont produits **par le calcul**, jamais par l'IA.
- Aucune nouvelle dépendance hors de `lxml`, déjà installé par python-docx, à déclarer directement (D-155).

## 4. Ce qui change pour la personne

- **Sur l'accueil** (ou dans « Nouvelle étude », § 0) : « Concevoir un questionnaire ». On choisit un dossier et un nom ; le projet est créé sans base et s'ouvre sur sa page « Questionnaire ».
- **Une phase « Concevoir »** en tête du menu, pour ces projets seulement : **Questionnaire** (l'éditeur), **Relecture** (les points à voir), **Publier** (aperçu, Word, LimeSurvey, « Marquer comme envoyé », comparaison du réexport). La page **Sources** s'y ajoute en v0.21.
- **Le dictionnaire de données existe avant la collecte** : chaque question donne ses variables prévues (nom, étiquette, codes) ; les pages Glossaire, Variables (libellés, descriptions), Groupes, Noms, Plan et Export sont ouvertes ; les autres disent « En attente de la base ». Le codebook Excel et Markdown s'exporte sans statistiques ; **le plan d'analyse peut être figé avant la collecte**, ce qui est le cas normal d'un préenregistrement (§ 6.7).
- **Quand la base arrive**, un bouton l'ouvre : chaque variable trouve sa question par son nom prévu, et un **rapport de conformité** dit ce qui diffère.
- **Une base LimeSurvey existante** se documente mieux : le `.lss` est lu comme questionnaire, avec les codes exacts, et chaque variable est rattachée par la structure.
- **« Mes projets »** dit l'étape : Concevoir, En collecte, puis Documenter, Analyser, Rédiger (D-154).

## 5. Ce que j'ai vérifié

### 5.1 Les affirmations de la demande, dans le code

| Affirmation | Constat |
|---|---|
| `questionnaire/read.py` lit `.pdf` ou `.txt` (`FORMATS`) ; `header.py` lit l'en-tête `.xlsx` (D-045) | Exact (`read.py:20`). |
| `segment.py` donne quatre natures : `single`, `checkbox`, `grid`, `open` | Exact (`segment.py:401-416` ; `Question.kind`, `model.py:383`). |
| `link.texts_agree` compare deux textes à la casse, aux accents et à la ponctuation près | **Incomplet, et c'est important.** `texts_agree` (`link.py:458`) accepte aussi deux textes « très semblables » (`SequenceMatcher`, ratio ≥ 0,9) et un texte qui est **le début** de l'autre (20 caractères au moins), parce que SPSS coupe les étiquettes. Pour rattacher une variable, c'est voulu. Pour vérifier un item **mot pour mot**, c'est dangereux : mesuré avec la fonction actuelle, « Je ne suis pas satisfait de mon sommeil » concorde avec « Je suis satisfait de mon sommeil » (0,90), et « Au cours du dernier mois, je ne me suis pas senti nerveux et stressé » avec la même phrase sans la négation (0,95) ; plus la phrase est longue, plus une négation retirée passe ; un item coupé passerait aussi pour retrouvé. La vérification de la v0.21 **ne doit pas** utiliser `texts_agree` ; elle peut réutiliser `normalized_text` (`link.py:452`), en plus strict (§ 11.3, D-147). |
| `ddict.platforms` ne décrit que SurveyMonkey (D-044), fait pour en décrire d'autres | Exact. *(détails au § 5.3)* |
| Navigation : quatre phases, `FIRST = "base"` | Exact (`navigation.py:43`). |
| La page « Plan » a le modèle d'une liste ordonnée | Exact *(détails au § 5.3)*. |
| La page « IA » a « Ce qui part » | Exact. |
| Un projet est toujours construit à partir d'une base (`SourceInfo`, empreinte ; D-091) | Exact pour le projet (`Project.source: SourceInfo`, obligatoire, `model.py:805`), mais **D-091 porte sur le carnet** : c'est le carnet qui rappelle l'empreinte de la base et refuse une autre base. Le projet construit à partir d'une base vient de la conception (§ 5.4) et de `project/build.py`. Ce que le projet sans base change : § 6.1 (D-145) ; le carnet, lui, ne change pas (il n'existe qu'avec une base). |
| python-docx est une dépendance (D-082) | Exact (`pyproject.toml`, `python-docx>=1.2.0`). |
| L'XML de LimeSurvey se lit et s'écrit avec lxml, déjà présent | **Présent, mais pas comme dépendance directe** : lxml vient avec python-docx (`docs/dependances.md` le note : « requis par python-docx ») ; aucun module de `src/` ne l'importe. Le déclarer dans `pyproject.toml` (D-155). |

### 5.2 Ce que la demande ne disait pas et qui compte

- **Figer le plan exige aujourd'hui la base** : `plan_notebook.freeze` refuse sans base ouverte (« Ouvrez la base pour figer le plan : chaque hypothèse devient une analyse du carnet. », `plan_notebook.py:102`). Pour une étude conçue dans l'outil, le plan se fige **avant** la collecte : c'est le sens d'un préenregistrement. `planning.freeze` (sans le carnet) n'a pas ce besoin. Proposition au § 6.7 (D-153).
- **Le modèle `Question` dit « ses mots, jamais réécrits »** (`model.py:379`) : c'est un relevé d'un fichier. Il n'a ni codes de réponse, ni consigne, ni « obligatoire », ni sections, ni provenance. Le questionnaire conçu l'étend (§ 6.2) ; les identifiants y restent ceux d'aujourd'hui (`Q7`, `Q7.r3`, `Q10.o2`), mais ne sont jamais redonnés, comme `H<n>` dans le plan.
- **Le fichier projet écrit tous les champs, y compris leurs valeurs par défaut** (`store.dumps`, `model_dump` sans `exclude_defaults`) : un projet 0.8.0 ouvert puis enregistré en 0.9.0 gagne les nouveaux champs de chaque question. Rien n'est perdu ; la taille augmente un peu. Le test d'aller-retour le couvre.
- **Le Word de l'outil** (`analysis/formats/docx.py`) fixe l'auteur mais pas les dates des propriétés du document : pour « mêmes octets à chaque production », il faut fixer aussi `created`, `modified`, `revision` et `last_modified_by` (comme `deposit.steady_xlsx` le fait pour Excel, D-119).
- *(L'inventaire de ce qui suppose une base, fait dans tout le code, est au § 5.3.)*

### 5.3 Ce qui suppose une base dans le code

Aucun chemin « sans base » n'existe aujourd'hui : `Project.source` et, pour chaque variable, `file`, `profile` et `privacy` sont obligatoires, et la seule façon de faire un projet est `build_project(data)` (`project/build.py:192`), appelé par `workflow.profile_database` (ligne de commande `profiler`, accueil `home_view._create`, essai `review/trial.py`). Ce qui doit changer, par module :

| Où | Ce qui suppose la base | Ce qui change |
|---|---|---|
| `project/model.py` | `SourceInfo` obligatoire ; `Profile` (type déduit, effectifs obligatoires) ; `Questionnaire.file_name`, `sha256`, `format` obligatoires | § 6.1 et 6.2 ; un questionnaire conçu a pour nom celui du projet, et pour empreinte celle de son contenu |
| `export/xlsx.py:50`, `markdown.py:24`, `context.py:221` et `:622`, `syntax.py:87`, `:215`, `:232`, `preparation.py:156` | En-têtes et « Informations » lisent nom, empreinte, lignes, colonnes, format, encodage ; `MEDIATYPES[source.format]` | Une branche « dictionnaire prévu » ; le contexte d'analyse et le `datapackage.json` sans ressource tant qu'il n'y a pas de base ; le lecteur R des fichiers de commandes attend la base |
| Statistiques des codebooks (xlsx `:106-135`, md `:113-125`, `context.py:403`, `:547`, `variables_view.py:244`) | Effectifs écrits même nuls | Rien écrit pour une variable prévue (`profile is None`) |
| Type `empty` (`measure.py:20`, `completeness.py:52`, `conditions.py:70`, `link.py:734`, `wording.TYPES`) | Une variable vide est exclue partout et affichée « vide » | **D'où `profile = None` plutôt qu'un profil vide** : une variable prévue n'est pas une variable vide. Son type prévu (nombre, texte, date) vient de la nature de sa question |
| `questionnaire/labels.py:26` | Les étiquettes tirées des options demandent les codes observés | Inutile pour une variable prévue : ses étiquettes viennent des codes du questionnaire |
| `questionnaire/link.py:763` `drop_stale_links` | **Retire tous les rattachements quand l'empreinte du questionnaire change** | À changer : pour un questionnaire conçu, l'empreinte change à chaque modification ; les rattachements y suivent les identifiants stables, seuls ceux dont la cible a disparu sont retirés |
| `privacy/classify.py:143`, `groups/find.py:292` | Classement et groupes calculés sur le tableau | Pour une variable prévue : classe par le nom et l'étiquette seulement (identifiant, date de naissance), à confirmer comme aujourd'hui ; groupes donnés par le questionnaire (§ 6.4) ; recalculés à l'arrivée de la base |
| `analysis/data.py:109` `find_database`, `notebook.py:270` `belongs` | La base à côté du projet, reconnue par son empreinte ; le carnet par la même empreinte | Inchangé : sans base, pas de carnet ; à l'arrivée, `source` est écrite une fois, avant tout carnet |
| `plan_notebook.py:102`, `plan_view._ready` (`:627`), `_frozen` (`:675`) | Figer exige la base | § 6.7 (D-153) |
| `workflow.tasks` (`:340`) | Première tâche « Ajouter le questionnaire » ; codes suspects | Les tâches de conception (§ 8.6) remplacent la première ; les tâches de base attendent la base |
| `notebook_view.dashboard_state` (`:105`), `analyses_view.prepared_data` (`:64`) | Lisent la base à chaque affichage | Ne rien chercher quand `source is None` |
| `overview.py:150`, `:175`, `:249`, `app.py:250`, `base_view.py:293`, `home_view.py:253` | Nom de la base dans « Mes projets », la barre latérale, l'accueil | Le nom du projet ; « Base : pas encore » |
| `platforms` (`Place.question: int`), `naming.py:193` (`f"q{rank:04d}"`) | Une question de plateforme est un rang numérique (SurveyMonkey) | LimeSurvey désigne ses questions par des **codes** : `Place` et la clé de radical acceptent un code (§ 7.2) |
| `workflow.py:136`, `questionnaire_view.py:31` et `:164`, `link.py:125`, `:307`, `:495` | Les quatre natures | Le texte d'affichage (`display`) n'a aucune variable ni cible : écarté de `link.targets` et des comptes, nommé dans les deux tables de textes |

Le format : un projet 0.9.0 est refusé par une version 0.19 (`ProjectNewer`, comme pour chaque version mineure) ; l'inverse fonctionne.

### 5.4 Hypothèses sur la v0.19

Faute de plan de la v0.19, je suppose : un dossier d'étude avec un sous-dossier `instruments/` et un fichier `etude.json` qui nomme les projets de l'étude ; un parcours « Nouvelle étude ». Si ces choix diffèrent, seuls le § 0, l'endroit du bouton « Concevoir un questionnaire » (§ 8.1) et l'endroit des sources (v0.21) changent.

### 5.5 Chez LimeSurvey et SurveyMonkey (documentation consultée le 2026-10-19)

**Les deux formats d'importation de LimeSurvey :**

| | `.lss` (XML) | Structure en texte à colonnes (`.txt`, « Tab Separated Values ») |
|---|---|---|
| Documentation | Le manuel dit seulement que c'est un XML des groupes, questions, sous-questions, réponses et conditions, réimportable ; **aucune description publique du schéma** (une question du forum à ce sujet est restée sans réponse). | **Documenté** : une ligne par groupe, question, sous-question, réponse ; colonnes `id`, `related_id` (depuis 3.14.0, optionnelles, pour les quotas), `class`, `type/scale`, `name`, `relevance`, `text`, `help`, `language`, `validation`, `mandatory`, `other`, `default`, `same_default`, puis les attributs avancés. Classes : `S`, `SL`, `G`, `Q`, `SQ`, `A`, `C`… UTF-8 ; la parenté est donnée par la position, sans identifiants. |
| Stabilité | Le contenu a changé de forme avec LimeSurvey 4 : les textes sont passés dans des tables à part (`question_l10ns`, `answer_l10ns`, `group_l10ns`), selon les utilisateurs du forum ; un `.lss` de LimeSurvey 4 importé dans une version 3 pose problème. | Pas d'identifiants à calculer (le manuel le dit : « calculés à l'importation ») ; « ne fonctionne bien qu'avec le nommage par codes de questions » (le nôtre). |
| Lecture | Ce que LimeSurvey **exporte** par défaut : il faut le lire de toute façon (partie A, et la boucle). | LimeSurvey l'exporte aussi. |

**Recommandation (D-148) : écrire le format texte à colonnes**, documenté, sans identifiants, le même d'une version de LimeSurvey à l'autre ; **lire les deux** (le `.lss` pour les bases existantes et le réexport, le `.txt` pour le même usage). L'essai d'importation réel de l'auteur tranche : si le `.txt` coince, l'outil écrit un `.lss` dans la forme exacte de ce que la version de l'auteur exporte. **L'auteur utilise LimeSurvey Cloud, version 7** (réponse du 2026-10-19) : le format écrit et les conventions lues sont vérifiés sur cette version ; une autre version n'est pas garantie, et la page le dit. Sur LimeSurvey Cloud, l'importation passe par l'administration du compte (« Créer un questionnaire », « Importer ») : les étapes exactes sont écrites à l'étape E2, d'après l'essai de l'auteur.

Les codes de types que j'utiliserais (à confirmer sur le `.lss` exporté par l'auteur, ce n'est pas vérifié) : `L` liste (boutons), `!` liste déroulante, `M` cases à cocher (avec `other` = `Y`), `F` tableau, `S` texte court, `T` texte long, `N` nombre, `D` date, `X` texte d'affichage ; `mandatory` = `Y`. Les limites des codes (lettres et chiffres seulement ? longueur maximale des codes de sous-questions et de réponses ?) sont **à vérifier** sur l'instance de l'auteur avant d'écrire la vérification correspondante.

**SurveyMonkey** : son centre d'aide (« Importing surveys ») ne décrit **aucune importation par fichier** ; seulement « coller » le texte d'un document (avec une version « par l'IA » qui devine les types), et un module pour Google Forms. Il dit qu'on ne peut téléverser ni un Word, ni un PDF, ni un questionnaire d'une autre plateforme. À vérifier par l'auteur sur son compte. D'où (§ 10.6) : la page « Publier » propose le Word de travail à recopier, et rappelle que l'export de SurveyMonkey se lit déjà (D-044).

Sources : [Tab Separated Value survey structure](https://www.limesurvey.org/manual/Tab_Separated_Value_survey_structure) ; [Exporter un questionnaire](https://www.limesurvey.org/manual/Exporter_un_questionnaire) ; [Import a Survey](https://help.limesurvey.org/portal/en/kb/articles/import-a-survey) ; [forum : structure de l'export `.lss`](https://forums.limesurvey.org/forum/development/154666-where-do-i-find-information-about-limesurvey-s-lss-export-and-the-xml-structure) ; [forum : tables `l10ns`](https://forums.limesurvey.org/forum/development/157239-lsg-format) ; [SurveyMonkey, Importing surveys](https://help.surveymonkey.com/en/surveymonkey/create/importing-surveys/).

## 6. Conception — partie B, ce dont tout dépend

### 6.1 Le projet sans base (D-145)

Format du projet **0.9.0** :

- `Project.source: SourceInfo | None = None`. `None` veut dire « pas encore de base ». Un projet 0.8.0 a toujours une source : il s'ouvre tel quel.
- `Project.design: Design | None = None`, présent seulement pour un projet créé par « Concevoir un questionnaire », et gardé après l'arrivée de la base (la phase reste lisible, § 8.2). Il contient : la date de création, les sections, les publications (« Marquer comme envoyé », § 10.5), les points de relecture gardés tels quels (§ 9.3), le dernier numéro donné aux questions, sections, énoncés et options (jamais redonné).
- `VariableEntry.profile: Profile | None` : `None` pour une variable **prévue** (aucune statistique, rien à profiler). Une variable prévue a un `file` qui dit ce que le questionnaire prévoit que la base dira (étiquette = texte de la question ou de l'énoncé ; étiquettes de valeurs = les choix et leurs codes), et une question rattachée d'office (origine `computed`, statut `none` : c'est un fait, pas une proposition).
- Le fichier projet est écrit dans le dossier choisi, `<nom>.dd.json` (D-020 le mettait à côté de la base) ; il est suivi d'office (D-131).

Ce que ça change à **D-091** : rien au carnet. Le carnet rappelle l'empreinte de la base ; sans base, il n'y a pas de carnet (aucune analyse ne se calcule). Le plan, lui, vit dans le projet et s'écrit sans base (§ 6.7).

*Option écartée* : un projet « vide » avec une fausse `SourceInfo` (empreinte vide, 0 ligne). Moins de code changé, mais chaque endroit qui lit la source croirait à une base de 0 ligne ; les erreurs seraient silencieuses au lieu d'être refusées par le type.

### 6.2 Le questionnaire structuré (D-146)

**Dans le projet**, `project.questionnaire`, pas dans `etude.json` : les variables, les groupes, les noms et l'empreinte du codebook s'y réfèrent, et un seul fichier s'enregistre d'un coup sous le contrôle de D-129. `etude.json` (v0.19) peut nommer le projet qui le porte.

**Le même modèle `Question`**, étendu par des champs facultatifs (un questionnaire lu d'un fichier les laisse vides) :

| Élément | Champs ajoutés |
|---|---|
| `Questionnaire` | `format` accepte `designed` (conçu dans l'outil) et `lss` (lu d'un export LimeSurvey) ; pour `designed`, `sha256` est l'empreinte du contenu structuré, recalculée à chaque changement (l'empreinte du codebook la reprend déjà) ; `sections: list[Section]` |
| `Section` (nouveau) | `section_id` (`S1`…, jamais redonné), `title`, `instruction` ; l'ordre des sections est celui de la liste |
| `Question` | `section` ; `instruction` (consigne) ; `required` ; `answer` pour une question ouverte : `short`, `long`, `number`, `date` ; `layout` pour un choix unique : `radio` ou `dropdown` ; `provenance` |
| `kind` | une cinquième valeur, `display` (texte d'affichage, sans variable), seulement dans un questionnaire conçu ou lu d'un `.lss` ; chaque endroit qui lit `kind` est revu (§ 5.3) |
| `QuestionOption` | `code` (le code de réponse, décidé avant la collecte) ; `other` (l'option « autre », avec son texte) ; `provenance` |
| `GridRow` | `code` (code de la sous-question) ; `provenance` |
| `Provenance` (nouveau) | `kind` : `team` (tapé par l'équipe), `source` (tiré d'une source : en v0.20 un texte écrit par l'équipe, « Manuel, p. 4 » ; en v0.21 une source déposée et sa page, vérifiées), `ai` (rédigé par l'IA, v0.21) |

Ce qui **n'entre pas** dans le questionnaire, parce qu'un champ existe déjà ailleurs (pas de second modèle) :

- **Le code de la question et le radical des noms** : `Project.stems`, clé `Q7` (D-048), une valeur suivie, comme aujourd'hui.
- **Les items inversés, le nom de l'instrument, sa référence et sa cotation** : le groupe (`Group.reverse_items`, `instrument_name` sourcé, `scoring`, D-060). Une grille marquée « instrument » **est** un groupe dès sa création (§ 6.4) ; l'éditeur écrit directement dans le groupe, la colonne « inversé » du tableau des énoncés aussi.
- **Le préfixe d'une grille** : `Group.name_prefix` (D-048).

Les identifiants (`Q7`, `Q7.r3`, `Q10.o2`, `S2`) sont donnés à la création et **jamais redonnés** ; le numéro affiché (« 7. ») se calcule par l'ordre. Monter une question ne change donc ni ses variables ni ses rattachements.

### 6.3 Les variables prévues

`ddict.design.plan_variables(project)`, une seule fonction pour l'interface et la ligne de commande, appelée après chaque changement du questionnaire :

| Nature | Variables prévues |
|---|---|
| Choix unique | une ; étiquettes de valeurs = les choix et leurs codes ; avec « autre », une variable de texte de plus |
| Cases à cocher | une par option ; « autre » donne la case et son texte |
| Grille | une par énoncé, mêmes étiquettes de valeurs pour toutes |
| Ouverte | une (texte court, long, nombre ou date : le type prévu) |
| Texte d'affichage | aucune |

Deux noms par variable, comme pour une base renommée (D-048) :

- `name`, la clé : **le nom que la plateforme donnera** à la colonne, d'après ses conventions vérifiées (§ 7.2). Tant que la convention de LimeSurvey n'est pas vérifiée sur l'export de l'auteur, c'est le code de la question, de la sous-question et de la réponse joints par la convention supposée, et la page le dit (« convention non vérifiée »).
- `new_name`, proposé par les règles de D-048 (`<radical>`, `<radical>_<code>`, `<préfixe>_<rang>`, `<radical>_autre_txt`), à accepter comme aujourd'hui sur la page « Noms ». Si la plateforme permet des codes qui donnent directement le nom final, les deux coïncident et rien n'est à renommer.

Les variables gardent leur place par leur **question** (`Q7.r3`), pas par leur nom : changer un code renomme la variable, et `plan_variables` reporte le nouveau nom partout où l'ancien était cité (membres et cotation des groupes, références du plan, recodages, exclusions), dans un seul changement enregistré. Une question retirée retire ses variables ; si une décision portait sur elles (libellé, plan), la page le dit avant de retirer (« 2 hypothèses du plan citent cette variable »).

### 6.4 Un instrument devient un groupe, sans étape de plus

Une grille marquée « instrument » crée son groupe (nature `scale`, membres = ses variables prévues, base « questionnaire conçu »). Ses items inversés, son nom d'instrument (humain, sourcé), sa référence et sa cotation (D-060) sont ceux du groupe, saisis dans le formulaire de la question ou sur la page « Groupes » : c'est le même champ. Les règles humaines restent : nom, cotation et étendue exigent une source (règle 4) ; aucun champ n'est pré-rempli par un calcul (D-126). Une grille non marquée « instrument » donne aussi un groupe (comme la structure de plateforme, D-044), sans cotation proposée. Un ensemble de cases à cocher donne un groupe `multiple_response`, son « autre » attaché hors des membres, comme aujourd'hui.

### 6.5 Les noms et les codes

Les codes sont décidés **avant la collecte**, par l'équipe : un code vide est un point de relecture (§ 9.3), jamais rempli d'office. Le bouton « Reprendre la numérotation 1 à N » met 1, 2, 3… dans les codes vides du tableau, sans enregistrer (D-126). Les noms viennent des règles de D-048 et se décident sur la page « Noms », comme pour une base existante.

### 6.6 Le dictionnaire de données avant la collecte

Le codebook Excel et Markdown s'exporte sans base : les colonnes de statistiques sont vides, l'onglet « Informations » dit « Dictionnaire prévu, avant la collecte (aucune base) » et donne l'empreinte du questionnaire. La complétude ne compte que ce qui s'applique sans base (question, libellé, étiquettes de valeurs, nom, cotation). Ce qui ne s'exporte pas sans base, et le dit : la copie documentée, les fichiers de commandes appliqués à une base (ils s'écrivent, mais leur vérification attend la base), le contexte d'analyse avec statistiques, le paquet de dépôt. La liste exacte suit l'inventaire du § 5.3.

### 6.7 Le plan d'analyse avant la collecte (D-153)

Le plan s'écrit sur les variables prévues et **se fige sans base** : `plan_notebook.freeze` fige alors le plan seul (date, empreinte), sans entrée du carnet ; à l'arrivée de la base, `plan_notebook.sync` crée l'entrée de chaque hypothèse, comme après un amendement (« attend la base » existe déjà). L'état des données « pas encore collectées » est une des cinq réponses d'OSF Prereg déjà au plan. Les conditions des analyses sont déjà vérifiées sans base (« Conditions à vérifier quand la base sera ouverte », v0.13).

### 6.8 Ce qui ne change pas pour un projet existant

Un projet 0.8.0 se lit tel quel ; ouvert, il a une source et pas de `design` ; sa navigation, sa page d'ouverture, son codebook et son **empreinte du codebook** sont les mêmes (un test compare l'empreinte d'un projet de référence avant et après la migration, et les octets du codebook).

## 7. Conception — partie A, LimeSurvey

### 7.1 Le `.lss` comme questionnaire

`ddict.questionnaire.lss`, avec `lxml` (analyseur sans entités externes ni réseau : `resolve_entities=False`, `no_network=True`), lit les deux formes connues (textes dans les tables de base avant LimeSurvey 4, tables `*_l10ns` ensuite), et le format texte à colonnes avec le même résultat. Il donne un `Questionnaire` de format `lss` :

- groupes → sections ; questions dans l'ordre (groupe, puis ordre de la question) ;
- le code de chaque question (`title`), de chaque sous-question et de chaque réponse, **exacts** ;
- la nature : `L`, `!` → choix unique ; `M` (et `P`, avec commentaires) → cases à cocher, `other` ; `F` et les autres tableaux → grille ; `S`, `T`, `U` → ouverte (court, long) ; `N` → nombre ; `D` → date ; `X` → texte d'affichage. Les types sans équivalent (classement, téléversement, équation…) gardent leur texte et un point à vérifier « type LimeSurvey non pris en charge » ; les types aux codes implicites (`Y` oui/non, `G` genre, `5` cinq points) sont lus, leurs codes **marqués à vérifier** tant que l'export de l'auteur ne les a pas montrés ;
- les textes en HTML deviennent du texte (balises retirées, entités décodées) ; une expression `{…}` reste telle quelle, avec un point à vérifier ;
- un questionnaire en plusieurs langues : la langue de l'étude si elle y est, sinon la langue de base du questionnaire ;
- jamais lus : les réglages du questionnaire (administrateur, courriel, adresse du serveur), les quotas, les jetons, les conditions.

Les codes de réponses lus dans le `.lss` donnent les étiquettes de valeurs proposées (comme D-016, origine `questionnaire`), mais **sans** la mention « ordre supposé » : ici les codes sont lus, pas supposés.

### 7.2 LimeSurvey dans `ddict.platforms`

Une deuxième description, à côté de SurveyMonkey : variables de la plateforme (`id`, `submitdate`, `lastpage`, `startlanguage`, `seed`, `startdate`, `datestamp`, `ipaddr`, `refurl`, `token` : leur présence dépend des réglages du questionnaire), le motif des noms de sous-questions, de l'option « autre » et des commentaires, et la forme de l'en-tête des exports CSV et Excel (codes ou textes). **Aucune de ces conventions n'est écrite tant qu'elle n'est pas vérifiée** sur un export de l'auteur ; chacune porte dans le code la date et l'export qui l'ont montrée.

**La marche à suivre pour l'auteur** (écrite à l'étape A2, en français) : créer dans LimeSurvey le questionnaire fictif que je fournis (une copie du fichier de l'étape E3 si elle est faite, sinon une liste de 10 questions à taper : une de chaque nature, une grille avec un item inversé, des cases avec « autre », une question obligatoire) ; répondre soi-même cinq fois avec des réponses inventées ; exporter le `.lss`, les réponses en CSV (en-têtes « code de question », puis « texte »), en Excel et en SPSS (`.sav`), avec et sans « réponses complètes seulement ».

**Ces exports n'entrent pas dans le dépôt** : un `.lss` contient le nom et le courriel de l'administrateur et l'adresse du serveur. Ils restent hors du dépôt (comme D-046), lus par des tests marqués `limesurvey` qui ne gardent que des comptes ; ce qu'ils montrent est reproduit par `scripts/generer_limesurvey_fictif.py` (graine fixe), dont les fichiers servent aux tests ordinaires.

### 7.3 Le rattachement par la structure

Avec un `.lss` comme questionnaire et une base LimeSurvey, le code de chaque question donne le nom de ses variables : `link.platform_choices` les apparie **par le code** (et non plus par le rang et la concordance des textes, comme pour SurveyMonkey), et ce sont des choix sûrs (D-041). Une variable dont le code n'est dans aucune question reste à rattacher comme aujourd'hui ; un texte qui ne concorde pas (questionnaire modifié après l'export) devient un point à vérifier.

## 8. Conception — partie D, l'interface

### 8.1 Créer le projet

« Concevoir un questionnaire » (accueil, ou étape de « Nouvelle étude ») : dossier (fenêtre « Choisir un dossier », D-132), nom du projet, langue de l'étude. En ligne de commande : `ddict questionnaire creer <dossier> --nom … --langue fr` (`ddict questionnaire create`).

### 8.2 La phase « Concevoir » (D-149)

Visible **pour les projets qui ont un `design`** seulement, en tête du menu ; elle reste après l'arrivée de la base, en lecture et modification (une modification après publication est dite, § 10.5). La page d'ouverture devient une fonction, `navigation.first(project)` : « Questionnaire » (de Concevoir) tant qu'il n'y a pas de base, « Base » ensuite et pour tout autre projet.

*L'autre choix*, visible pour tous : il servirait à une équipe qui documente sa vague 1 et veut préparer la vague 2 en modifiant le questionnaire. Mais pour une base existante, une phase « Concevoir » vide en tête du menu brouille le chemin, et le questionnaire d'une base existante est une source lue, pas un document à modifier. Je recommande plutôt, plus tard, « Préparer la vague suivante », qui crée un projet de conception à partir d'un projet documenté.

Pour un projet de conception, l'ancienne page « Questionnaire » de Documenter (lire un PDF) est retirée du menu : le questionnaire est celui de Concevoir.

### 8.3 Sans base

| Page | Sans base |
|---|---|
| Base, Analyses, Carnet, Méthode, Vérifier | « En attente de la base », et un bouton vers l'étape suivante (« Ouvrir la base » quand le projet est publié ; sinon « Publier le questionnaire ») |
| Glossaire, Groupes, Noms, Plan, Export | Ouvertes ; les parties qui demandent des statistiques le disent dans leur section |
| Variables | Ouverte pour les libellés, descriptions et unités ; ni statistiques ni codes suspects |

### 8.4 La page « Questionnaire » (l'éditeur)

Sur le modèle de la page « Plan » : la liste des sections et de leurs questions, une ligne par question (numéro, nature, début du texte, nom, provenance, problèmes), avec monter, descendre, modifier, retirer ; une **seule question ouverte à la fois** ; un filtre par section et par problème. Le formulaire dépend de la nature (choix unique, cases à cocher, grille, ouverte, texte d'affichage) ; les choix et les énoncés sont dans un `st.data_editor` (code, texte, « autre », inversé pour une grille marquée instrument, provenance). Un seul « Enregistrer » par question (D-124), brouillon gardé si l'on change de question ou de page, `c.save` et le contrôle à l'écriture (D-129, D-130). Pour la rapidité d'un questionnaire de plus de 100 questions : la liste ne dessine que des lignes de texte et leurs boutons, le seul tableau modifiable est celui de la question ouverte ; un test mesure le temps d'affichage d'un questionnaire fictif de 150 questions.

### 8.5 La page « Relecture »

Une seule liste de points, chacun avec son bouton vers la question (`c.go_to`, la question ouverte). Un point se règle en corrigeant la question, ou se ferme par « Garder tel quel » ; un point gardé est retenu avec l'empreinte du texte concerné et **revient si ce texte change**. Les points de la v0.20, tous calculés :

- question sans code, choix ou énoncé sans code, codes en double dans une question ;
- nom invalide ou en conflit (`naming.problems`), radical non décidé ;
- catégories numériques qui se chevauchent ou laissent un trou (« 18-25 », « 25-35 ») ;
- question obligatoire sans choix de non-réponse (« Préfère ne pas répondre », la liste de D-047), et choix unique sans ce choix : un point d'information (l'EPTC 2 laisse le droit de ne pas répondre) ;
- grille sans consigne, grille sans titres de colonnes, texte vide ;
- grille marquée instrument sans nom d'instrument sourcé, item d'instrument sans provenance ;
- ce que LimeSurvey refusera (codes trop longs ou de caractères refusés, à vérifier au § 5.5).

Une échelle « déséquilibrée » ne se calcule pas de façon fiable (il faudrait comprendre les mots) : elle va à la relecture par l'IA, en v0.21.

### 8.6 « Mes projets » et le tableau de bord (D-154)

La phase d'un projet (D-133) gagne deux valeurs avant les trois existantes : **Concevoir** (un `design`, pas de publication), **En collecte** (une publication marquée, pas encore de base), puis Documenter, Analyser, Rédiger. Toujours sans lire aucune base (seulement le projet). Tâches du tableau de bord : questions sans nom ou sans code, points de relecture ouverts, questionnaire modifié depuis sa dernière publication, réexport de LimeSurvey à comparer (publié dans LimeSurvey, rien comparé depuis) ; en v0.21, items introuvables.

## 9. Conception — partie E, publier

### 9.1 L'aperçu

Dans la page « Publier » : le questionnaire à peu près comme le verra une personne qui répond (boutons, cases, tableaux, champs, désactivés) ; la page dit que c'est une approximation et que seul LimeSurvey fait foi. « Montrer les noms » ajoute noms et codes.

### 9.2 Le Word (D-152)

python-docx, par le calcul, deux versions :

| Version | Contenu |
|---|---|
| **Pour le comité d'éthique** | Titre, sections et leurs consignes, questions numérotées, choix avec ○ (un choix) ou ☐ (plusieurs), grilles en tableaux avec leurs titres de colonnes, champs à remplir, textes d'affichage, « * » pour une question obligatoire (avec la phrase qui l'explique). Ni nom, ni code, ni provenance. Dans la langue de l'étude. |
| **De travail** | Le même, plus : sous chaque question, son code, sa nature et son type LimeSurvey, « obligatoire » ; les codes des choix ; les codes des énoncés et « (inversé) » ; la provenance (tapé par l'équipe, source et page, rédigé par l'IA) ; le groupe et l'instrument ; à la fin, les points de relecture ouverts et gardés. Libellés de l'outil dans la langue de l'interface. |

Pied de page : « Questionnaire « … », version N du 2026-11-02 — empreinte 3f9a… ». La date est celle du dernier changement du questionnaire (gardée dans le projet), jamais celle du jour : **mêmes octets à chaque production** (propriétés du document fixées, § 5.2 ; test qui produit deux fois et compare). Écrit dans un fichier provisoire puis mis en place ; ouvert dans Word, il est refusé avec « Fermez … dans Word, puis recommencez », sans fichier à moitié écrit.

### 9.3 Le fichier LimeSurvey (D-148)

Écrit par le calcul dans le format recommandé (§ 5.5). Le tronc commun : choix unique (liste, boutons ; liste déroulante), cases à cocher avec « autre », grille (tableau), texte court et long, nombre, date, texte d'affichage ; obligatoire ou non ; sections en groupes ; une langue, celle de l'étude. **Pas** de branchements, de randomisation ni de quotas. Avant l'écriture, un résumé dit ce qui est inclus et ce qui ne l'est pas (provenance, items inversés, cotation, instrument, consignes de section si LimeSurvey les place autrement) ; une question qui empêcherait l'importation (code invalide, en double) refuse l'écriture et renvoie à la relecture. Les étapes d'importation dans LimeSurvey, pas à pas en français et en anglais, sont dans la page et le guide ; elles sont corrigées après l'importation réelle de l'auteur.

### 9.4 Boucler : comparer le réexport

Déposer le `.lss` (ou le `.txt`) réexporté de LimeSurvey : l'outil le lit (§ 7.1) et le compare au questionnaire du projet, par les codes : question ajoutée ou retirée dans LimeSurvey, texte changé (après `normalized_text`, et la différence montrée mot à mot), code changé (« probablement le même : même texte, autre code »), nature changée, choix ou énoncé ajouté, retiré, recodé, obligatoire changé. **Rien n'est changé seul** : chaque différence se règle par une décision, « Reprendre dans le projet » ou « Garder le projet » (LimeSurvey est alors à corriger, et la page le rappelle).

### 9.5 « Marquer comme envoyé » (D-150)

« Envoyé au comité » ou « Publié dans LimeSurvey », avec la date : le projet garde une copie du questionnaire structuré à ce moment et son empreinte. Une modification après publication reste permise, avec un avertissement clair (« Ce questionnaire a été publié dans LimeSurvey le … : LimeSurvey doit être mis à jour ») et un nouveau fichier proposé. Je recommande **de ne pas exiger de raison** : la page « Publier » montre, calculées, les différences depuis chaque version envoyée (la liste dont un comité a besoin pour un amendement), et le Word de travail peut les porter. Une raison tapée reste possible, facultative. Pour comparaison, le plan figé exige une raison parce que c'est un engagement scientifique que personne d'autre ne garde ; ici, le comité et LimeSurvey gardent chacun la version reçue.

### 9.6 SurveyMonkey

Aucune importation par fichier documentée (§ 5.5). La page propose le Word de travail à recopier et rappelle que l'export de SurveyMonkey se lit déjà (D-044) ; le rattachement par la structure de SurveyMonkey fera le reste à l'arrivée de la base.

### 9.7 « La base est arrivée »

Sur la page « Base » en attente, ou par `ddict profiler <base> --projet <projet.dd.json>` : la base est lue et profilée comme aujourd'hui ; chaque variable est appariée à la variable prévue du même nom (après les conventions de la plateforme), et reprend ses décisions (question, libellé, description, groupe, nom, unité, étiquettes de valeurs prévues). Les appariements réutilisent la mécanique des vagues (D-052, `ddict.waves`), qui reporte déjà les décisions d'un projet à l'autre et écrit un rapport des écarts. **Rapport de conformité** (page et `<projet>-conformite.md`) : variables prévues absentes, variables en trop (hors variables de la plateforme), codes observés hors des codes prévus (les codes seulement, jamais leurs effectifs), étiquettes différentes, type différent (texte au lieu de nombre). Rien n'est changé sans décision ; le projet passe à « Documenter ».

## 10. Ligne de commande

`ddict questionnaire creer` ; `ddict questionnaire word [--travail]` ; `ddict questionnaire limesurvey` ; `ddict questionnaire marquer --comite|--limesurvey --date` ; `ddict questionnaire comparer <export.lss>` ; `ddict profiler <base> --projet <projet>` pour l'arrivée de la base. L'édition des questions se fait dans l'interface seulement ; la ligne de commande produit, compare et lit.

## 11. La v0.21 en esquisse : sources, vérification mot pour mot, IA

Conçue en détail dans son propre plan ; seules ses décisions de principe sont à prendre maintenant.

### 11.1 L'exception à la règle 4 (D-143)

**`CLAUDE.md`, règle 4, nouvelle formulation proposée :**

> 4. **Aucune invention.** Les schémas de réponse du modèle n'ont aucun champ pour un seuil, une étendue théorique, une référence ou un nom d'instrument (`extra="forbid"`). Ces champs sont humains et exigent une source. **Une seule exception, l'extraction d'un instrument d'une source déposée par l'équipe (D-143)** : le modèle peut y relever un nom d'instrument, une consigne, des items, des choix de réponse, une cotation ou une référence, chacun avec sa page, et seulement si le calcul retrouve ce texte mot pour mot à cette page ; un texte introuvable ne peut pas être accepté. Rien ne vient de la mémoire du modèle. Les seuils restent humains. Les schémas des libellés, du rattachement, des radicaux et de la conseillère ne changent pas.

**`CONCEPTION.md`, principe 4 :** la même exception en une phrase, et dans le tableau des garanties : « Schéma d'extraction (v0.21) : chaque texte relevé porte sa page et passe la vérification mot pour mot avant d'être montré ; un nombre d'une cotation proposée (bornes, items inversés, nombre d'items) doit figurer dans l'extrait vérifié qui la justifie, sinon la cotation est refusée. »

Deux précisions que je propose : **la cotation** est une structure (somme, items inversés, bornes), pas un texte ; le modèle la propose avec l'extrait qui la dit, l'extrait est vérifié mot pour mot, et chaque nombre de la structure doit se lire dans l'extrait. **Les seuils cliniques** restent hors de l'exception (le plus risqué, et le moins utile pour construire un questionnaire).

### 11.2 Ce qui part vers le modèle (D-144)

Les sources sont des métadonnées (règle 3) ; elles partent par la porte de confidentialité, pour un projet qui le permet (D-138). Partent **seulement les pages choisies** par la personne pour une extraction (au plus 10 par requête), en **texte** extrait sur le poste par pypdf (jamais le PDF : il porte ses propriétés, ses calques, ses images) ; **jamais une page exclue**, même choisie ; jamais une page sans texte. Au dépôt, une phrase rappelle de ne jamais déposer un document qui contient des réponses de participants. Test à chaînes témoins : un témoin sur une page exclue du faux protocole n'entre dans aucun message.

### 11.3 La vérification mot pour mot (D-147)

Par le calcul, sans `texts_agree` (§ 5.1). Un texte est **retrouvé, p. N** s'il est une sous-chaîne du texte de la page après une normalisation fixe et montrée :

- **tolérés et montrés** : espaces multiples et fins de ligne ; coupure par un trait d'union en fin de ligne (« satis-␤faction ») ; coupure entre deux pages (dite « p. 4-5 »), après retrait des en-têtes et pieds de page répétés et des numéros de page ; apostrophes et guillemets typographiques (’ « » “ ”) ; ligatures (ﬁ) ; numérotation devant l'item dans la source (« 3. », « a) ») ;
- **tolérés comme différences, montrés en surbrillance** : casse, accents, ponctuation finale ; le texte est alors « retrouvé avec différences », et la personne choisit le texte de la source ou le sien ;
- **jamais tolérés** : un mot ajouté, retiré ou changé, un chiffre différent, un texte coupé ; aucune ressemblance approchée.

Tests écrits d'abord, sur des PDF fictifs produits par `scripts/` : item dans un tableau (cellules sur deux lignes, lues dans le désordre par pypdf : peut-être « introuvable », et la page le dit honnêtement), item coupé entre deux pages avec un pied de page entre les deux, numérotation devant l'item, apostrophes typographiques, négation retirée (doit échouer), mot changé (doit échouer).

### 11.4 Le reste de la v0.21

Dépôt d'une source (type, langue, licence notée et jamais jugée ; PDF sans texte signalé dès le dépôt ; pages exclues) ; extraction d'un instrument (schéma strict, consignes `extract-v1` en français et en anglais, vue côte à côte, item introuvable exclu d'office de l'acceptation groupée et nommé) ; questions propres à l'étude rédigées par l'IA à partir du protocole, marquées « rédigé par l'IA », jamais dans une grille marquée instrument ; relecture des formulations (question double, double négation, jargon, question qui oriente, consigne absente, échelle déséquilibrée), comme propositions ; une échelle traduite exige une source dans la langue de l'étude ; le banc (`bench.py`) sur des sources fictives, avec zéro item inventé après vérification comme critère.

## 12. Étapes de la v0.20

| # | Étape | Critère de réussite |
|---|---|---|
| B1 | Règles et décisions : journal (D-145 à D-155 adoptées), `CONCEPTION.md` (§ 5.4, nouvelle § 25) | Relus et validés par l'auteur avant tout code |
| B2 | Format 0.9.0 : `source` facultative, `design`, `Section`, `Provenance`, champs de `Question`, `profile` facultatif ; migration | Un projet 0.8.0 s'ouvre tel quel, même empreinte du codebook, même codebook octet pour octet ; aller-retour octet pour octet d'un projet 0.9.0 sans base ; chaque endroit qui lit `profile`, `source` ou `kind` (§ 5.3) couvert par un test sans base |
| B3 | `ddict.design` : ajouter, modifier, retirer, ordonner sections et questions ; identifiants jamais redonnés ; `plan_variables` ; groupes des grilles et des cases ; report d'un code changé | Tests sans Streamlit sur un questionnaire fictif de chaque nature : variables, étiquettes, groupes, noms proposés par D-048 ; un code changé renomme partout (groupe, cotation, plan) ; une question retirée et ce qui la citait |
| B4 | Le dictionnaire et le plan avant la collecte : codebook sans base, complétude, plan figé sans base, `sync` à l'arrivée | Codebook Excel et Markdown d'un projet sans base, relus ; un plan figé sans base, puis la base : chaque hypothèse reçoit son entrée |
| A1 | Lecture `.lss` et `.txt` de LimeSurvey | Fichiers fictifs de `scripts/generer_limesurvey_fictif.py` : chaque nature, codes exacts, HTML retiré, deux langues, types non pris en charge signalés ; un XML piégé (entité externe) refusé |
| A2 | LimeSurvey dans `platforms` (**arrêt : l'auteur produit l'export fictif**, marche à suivre fournie) | Conventions vérifiées sur l'export de l'auteur (tests `limesurvey`, comptes seulement), reproduites par le générateur ; base reconnue, en-tête lu |
| A3 | Rattachement par les codes | Sur la base fictive LimeSurvey : toutes les variables de questions rattachées par la structure, choix sûrs |
| D1 | Navigation : phase « Concevoir », `navigation.first`, pages en attente de la base, création du projet (accueil ou « Nouvelle étude »), `ddict questionnaire creer` | AppTest : un projet de conception s'ouvre sur « Questionnaire » ; un projet existant sur « Base » et sans la phase ; chaque page en attente a son bouton ; aucun écran blanc |
| D2 | L'éditeur | AppTest : chaque nature ajoutée, modifiée, montée, retirée ; brouillon gardé ; contrôle à l'écriture ; filtre ; 150 questions affichées sous le temps fixé |
| D3 | Relecture | Chaque point calculé sur un questionnaire fictif piégé ; « Garder tel quel » revient quand le texte change ; boutons vers la question |
| D4 | « Mes projets » et tableau de bord | Les deux nouvelles phases, sans lire de base (`tests/projets_stades.py` étendu) ; les tâches de conception |
| E1 | Aperçu et Word (deux versions) | Mêmes octets deux fois de suite ; contenu de chaque version relu par un test (aucun code dans la version du comité) ; fichier ouvert dans Word refusé proprement |
| E2 | Fichier LimeSurvey et résumé avant l'export ; étapes d'importation (**arrêt : l'auteur importe pour de vrai**) | Le fichier écrit est relu par A1 et redonne le questionnaire ; importé dans LimeSurvey par l'auteur, chaque question conforme ; corrections consignées dans `docs/essais/` |
| E3 | Comparer le réexport ; « Marquer comme envoyé » ; différences depuis une version | Chaque sorte de différence trouvée sur des réexports fictifs modifiés ; aucune modification sans décision ; puis sur le réexport réel de l'auteur |
| E4 | « La base est arrivée » et rapport de conformité | Base fictive simulée à partir du questionnaire fictif, avec une variable en trop, une absente, un code hors des codes prévus, une étiquette changée : les quatre trouvés ; décisions reprises ; phase « Documenter » |
| F1 | Version 0.20.0 : captures (`scripts/captures.py`) des trois pages, guide (« Concevoir un questionnaire », français et anglais, avec les étapes d'importation), scénario manuel, CHANGELOG | Scénario joué par l'auteur dans la fenêtre de l'icône (§ 12.2) |

**Fait en B2** (format 0.9.0) : `Project.source` et `VariableEntry.profile` facultatifs ; `VariableEntry.planned` (le type prévu ; `data_type` et `suspect_codes` lisent la base ou le plan) ; `Provenance`, `Section`, `Publication`, `KeptPoint`, `Design` ; les champs ajoutés aux questions, choix et énoncés ; la nature `display`, écartée des cibles du rattachement ; `platforms.of(project)`, seul endroit qui donne la plateforme de la base ; `NoDatabase`, levée par les fichiers de commandes, le script de préparation et le contexte d'analyse sans base (leur forme sans base vient en B4) ; `no_base` pour la base introuvable, la copie documentée et le carnet. Le codebook Excel et Markdown sans base dit « pas encore de base (dictionnaire prévu, avant la collecte) », sans statistiques. Un projet 0.8.0 donne le même projet, la même empreinte et le même rapport Markdown ; **une seule différence dans le codebook Excel** : la ligne « Format du projet » dit 0.9.0, comme à chaque version du format. Les pages de l'interface sans base (Base, Variables…) attendent D1 : seuls la barre latérale et « Projet retrouvé » de l'accueil sont déjà prêts. Tests : `tests/test_sans_base.py`, projet de conception fictif écrit à la main dans `tests/projet_concu.py` (B3 le fera par la fonction de l'outil).

L'ordre B → A → D → E : B porte tout le reste ; A vient tôt parce que l'export de l'auteur demande du temps (A2 peut attendre pendant que D avance) ; E2 et E3 attendent l'importation réelle.

### 12.1 Les données de test

Rien de réel : `scripts/generer_questionnaire_concu.py` (un projet de conception fictif, chaque nature, une fausse échelle de 6 items dont 2 inversés, une grille de satisfaction, des cases avec « autre », 150 questions pour la rapidité), `scripts/generer_limesurvey_fictif.py` (`.lss`, `.txt`, base de réponses fictives et ses écarts), graines fixes. Aucun instrument réel, même libre de droits. Un test vérifie que tout, sauf l'IA, fonctionne sans l'option `ia`.

### 12.2 Le scénario manuel

Dans la fenêtre de l'icône : concevoir le questionnaire fictif (des questions tapées, une fausse échelle marquée instrument, ses items inversés), relire, produire le Word et le fichier LimeSurvey, l'importer dans LimeSurvey, le réexporter et comparer (une question modifiée dans LimeSurvey exprès), marquer comme publié, modifier une question et voir l'avertissement, simuler une base de réponses fictive et la documenter. En v0.21 s'ajoutent les sources et l'instrument extrait.

## 13. Décisions à prendre

| N° | Décision | Ma recommandation |
|---|---|---|
| — | **Avant ou après la v0.19** | Après (§ 0) ; le plan de la v0.19 réserve l'étape « Concevoir » et `instruments/`. |
| — | **Le découpage** | v0.20 sans sources ni IA (A, B, D, E) ; v0.21 sources, vérification et IA (C, F) (§ 2). |
| D-143 | **L'exception à la règle 4** (v0.21) | La formulation du § 11.1 ; seuils exclus ; la cotation justifiée par un extrait vérifié dont chaque nombre se lit. |
| D-144 | **Ce qui part vers le modèle** (v0.21) | Les pages choisies, en texte, au plus 10 par requête ; jamais une page exclue ; projet permis seulement ; test à chaînes témoins. |
| D-145 | **Le projet sans base** | Format 0.9.0 : `source` et `profile` facultatifs, `design` ; projet écrit dans le dossier choisi ; D-091 (le carnet) inchangé ; un projet 0.8.0 identique. |
| D-146 | **Le questionnaire structuré** | Dans le projet, pas dans `etude.json` ; le modèle `Question` étendu (sections, codes, consigne, obligatoire, provenance, `display`) ; identifiants jamais redonnés ; code de question = radical de `stems`, inversés et instrument = le groupe. |
| D-147 | **La vérification mot pour mot** (v0.21) | Sous-chaîne après la normalisation du § 11.3 ; casse, accents et ponctuation finale tolérés mais montrés ; jamais de ressemblance approchée ni de texte coupé. |
| D-148 | **Le format d'importation LimeSurvey** | Écrire le format texte à colonnes (documenté, sans identifiants) ; lire `.lss` et `.txt` ; l'importation réelle, dans LimeSurvey Cloud 7, tranche. |
| D-149 | **La phase « Concevoir »** | Projets créés par « Concevoir un questionnaire » seulement, gardée après la base ; page d'ouverture « Questionnaire » sans base, « Base » ensuite ; plus tard, « Préparer la vague suivante ». |
| D-150 | **Modifier après publication** | Avertissement et nouveau fichier proposé, différences calculées depuis chaque version envoyée ; raison facultative, pas exigée. |
| D-151 | **L'éditeur** | Dans l'outil seulement pour cette version. Un aller-retour par un Word à styles (Question, Option, Grille…) ferait deux sources de vérité, et un style mal appliqué se lirait comme une autre nature ; à reconsidérer si les équipes le demandent, en lecture seule (importer un questionnaire déjà écrit), jamais en aller-retour. |
| D-152 | **Le Word** | Deux versions (§ 9.2) ; pied de page avec version, date du dernier changement et empreinte ; mêmes octets. |
| D-153 | **Figer le plan sans base** | Permis : le plan seul est figé ; les entrées du carnet sont créées à l'arrivée de la base par `sync`. |
| D-154 | **Les phases de « Mes projets »** | Concevoir, En collecte, puis Documenter, Analyser, Rédiger (D-133 étendue) ; toujours sans lire de base. |
| D-155 | **lxml déclaré directement** | Déjà installé (python-docx), BSD-3-Clause ; déclaré dans `pyproject.toml` puisque l'outil l'importe ; ligne mise à jour dans `docs/dependances.md`. Analyseur sans entités externes ni réseau. |

## 14. Risques

- **Les conventions de LimeSurvey diffèrent selon la version ou les réglages** (noms des colonnes des sous-questions, de « autre », variables présentes) : rien n'est écrit sans l'export de l'auteur ; chaque convention porte sa date et sa version ; une base qui ne suit pas la convention retombe sur le rattachement ordinaire.
- **L'importation du fichier écrit échoue** : l'étape E2 est un arrêt ; le `.lss` dans la forme de la version de l'auteur est la solution de repli.
- **Le projet sans base touche beaucoup de code** (`profile` et `source` facultatifs) : l'inventaire du § 5.3 fixe la liste, et l'étape B2 n'est finie que lorsque chaque endroit a un test sans base ; le type facultatif fait échouer bruyamment ce qui serait oublié, au lieu d'une base fantôme de 0 ligne.
- **Un code changé après coup** casse des références : un seul endroit les reporte (§ 6.3), testé ; après publication, l'avertissement le dit.
- **Un questionnaire de 150 questions est lent dans Streamlit** : une seule question ouverte, un seul tableau modifiable, mesure dans un test.
- **La v0.19 choisit autrement** (dossier, étude) : seuls le bouton de création et l'endroit des sources changent (§ 5.4).
- **Un `.lss` contient des renseignements personnels** (administrateur, courriel, serveur) : jamais lus dans le projet, jamais dans le dépôt ; les fichiers de test sont produits par script.
