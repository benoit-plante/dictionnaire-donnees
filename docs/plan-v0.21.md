# Plan de la v0.21 — Filtres, ordre aléatoire, non applicable

> Statut : **validé par l'auteur le 2026-10-20**, avec la feuille de route du cycle ([`feuille-de-route-cycle.md`](feuille-de-route-cycle.md), étape 1) et toutes les recommandations du § 12 ; décisions D-163 à D-172 adoptées. Les sources, jusqu'ici annoncées comme « v0.21 », deviennent la v0.24 (D-164).
> **Aucune IA dans cette version** : tout est calculé. La porte de confidentialité ne change pas.

## 1. Pourquoi cette version

Un questionnaire de psychologie en ligne pose rarement toutes ses questions à tout le monde : « Combien d'enfants ? » seulement à qui en a, une section « Travail » seulement à qui travaille. Il mélange souvent l'ordre des items d'une échelle, et glisse un ou deux items de contrôle d'attention. Le comité d'éthique demande combien de temps dure la passation.

Aujourd'hui, l'outil ne sait rien de tout cela. Le questionnaire conçu pose tout à tout le monde ; le fichier LimeSurvey écrit `relevance = 1` partout ; et à l'arrivée de la base, une question qu'une personne n'a jamais vue est comptée comme une **valeur manquante**. Le Tableau 1 la range parmi les manquants, une règle de complétude exclut des personnes qui ont répondu à tout ce qu'on leur a demandé, et la Méthode ne peut pas dire pourquoi les *n* varient.

Cette version ajoute, par le calcul : la condition d'une question et d'une section, l'ordre aléatoire, les items de contrôle, la durée estimée, et surtout le **non applicable**, une nature de vide distincte du manquant, de la conception jusqu'à la Méthode.

## 2. Ce qui change pour la personne

- **Dans l'éditeur du questionnaire**, chaque question et chaque section reçoit un bloc « Posée si » (facultatif) : une ou plusieurs lignes « question, opérateur, valeur », reliées par « et » ou par « ou ». La valeur se choisit parmi les choix de la question (jamais tapée pour une question à choix). Une case « Ordre aléatoire » pour les énoncés d'une grille, les choix d'une question, les questions d'une section. Une case « Item de contrôle » pour une question à choix unique ou un énoncé de grille, avec sa ou ses bonnes réponses.
- **Sur la page « Relecture »**, des points nouveaux (condition sur une question qui vient après, valeur qui n'est pas un choix, cycle…), et en tête **la durée estimée de passation**, avec sa formule.
- **Dans le Word**, chaque filtre en clair (« Si vous avez répondu « Oui » à la question 3 ») et chaque ordre aléatoire ; le Word pour le comité donne la durée estimée.
- **Dans le fichier LimeSurvey**, les conditions et l'ordre aléatoire sont écrits ; un réexport est relu et comparé, conditions comprises.
- **À l'arrivée de la base**, chaque question filtrée distingue, pour chaque personne, « non applicable » (pas posée) et « manquant » (posée, sans réponse) ; le rapport de conformité dit les réponses présentes sous une condition fausse, en agrégats.
- **Dans le codebook**, « Posée si … » pour chaque variable d'une question filtrée ; et, si l'équipe les choisit, les codes du non applicable et du manquant pour SPSS et R.
- **En aval** : la règle de complétude ne compte que les items posés ; le Tableau 1, la description de l'échantillon et la Méthode disent « question posée à *n* personnes » ; une phrase de la Méthode explique le non applicable.
- **Les items de contrôle** donnent, à l'arrivée de la base, une règle d'exclusion **proposée** sur la page « Méthode », jamais appliquée seule.
- **Une base sans questionnaire conçu** (SurveyMonkey, un `.sav` existant) : la page d'une variable permet de déclarer sa condition à la main ; le même calcul suit.

## 3. Ce qui ne change pas

- Les six règles du `CLAUDE.md`. Les conditions, l'ordre aléatoire et les items de contrôle sont des métadonnées ; aucun message à l'IA ne change dans cette version (un test à chaîne témoin le vérifie : une condition n'entre dans aucun message des quatre usages). Si elles partent un jour vers l'IA (la relecture des filtres, en v0.24), ce sera au niveau des métadonnées, par la décision de cette version-là.
- **Un projet 0.11.0 s'ouvre tel quel**, sans condition : même codebook, même empreinte du codebook, même empreinte du questionnaire conçu, mêmes publications sans avertissement (§ 5.9).
- Le calcul des analyses : le non applicable sort de chaque analyse comme le manquant (suppression analyse par analyse) ; ce qui change, ce sont les dénominateurs affichés et les phrases.
- La copie documentée reste identique à l'original, case par case (D-026) : les codes du non applicable n'y sont jamais écrits.
- Aucune nouvelle dépendance.

## 4. Ce que j'ai vérifié

### 4.1 Les constats de la demande, dans le code

| Constat | Vérifié |
|---|---|
| `Question` n'a aucun champ de condition ni d'ordre aléatoire | **Exact** (`project/model.py:463-491`) ; `Section` non plus (`:494`). |
| `design_limesurvey.py` écrit `relevance = 1` partout et dit « No branching, randomisation or quota » | **Exact** : la docstring (`:7`) et `"relevance": "1"` pour les groupes, questions et sous-questions (`:273`, `:282`, `:296`). Les colonnes nécessaires existent déjà dans la liste des 151 colonnes de LimeSurvey 7.6 : `relevance`, `answer_order`, `subquestion_order`, `random_order`, `random_group` (`:52-79`). |
| `questionnaire/lss.py` ne lit jamais les conditions | **Exact**, et dit (`:8-9`). |
| Les règles de complétude ne savent pas qu'un item peut ne pas avoir été posé | **Exact** : `items.notna().sum(axis=1) < rule.min_answered` (`analysis/exclusions.py:105`). La ligne droite (`:110`) aussi, mais elle ne retient que qui a répondu à tous les items : une personne à qui la grille n'a pas été posée n'y est jamais comptée, ce qui est juste. |
| Les manquants connaissent les codes et les plages, aucune nature « non applicable » | **Exact** : `MissingRange`, `MissingToken`, `SentinelDecision` (`model.py:149-167`) ; `data.decided` remplace les codes manquants par un vide (`analysis/data.py:141`), sans autre nature. |

### 4.2 Ce que la demande ne disait pas et qui compte

1. **L'empreinte du questionnaire conçu changerait pour tous les projets existants.** `design.content_fingerprint` (`design.py:132`) sérialise chaque question entière (`model_dump`). Un champ nouveau, même vide (`condition: null`), changerait l'empreinte au premier changement enregistré, et chaque publication marquée (`Publication.fingerprint`, comparée à `questionnaire.sha256` dans `design_compare.py:330`) se dirait « modifiée depuis l'envoi » pour une question qui n'a pas changé. **Les champs nouveaux n'entrent dans cette empreinte que lorsqu'ils sont remplis** (§ 5.9, D-172), et un test le vérifie sur le projet de conception fictif de la v0.20.
2. **Le Tableau 1 calcule les pourcentages sur tout l'effectif de la colonne** (`count_pct(…, len(p))`, `apa.py:333` et suiv.), et compte en note chaque vide comme « valeur manquante ». Pour « Nombre d'enfants », posée à 164 personnes sur 300, les pourcentages seraient calculés sur 300 et 136 « valeurs manquantes » annoncées. D'où le dénominateur « posée à » (§ 5.8.5).
3. **Une condition s'évalue sur les codes tels qu'enregistrés, avant le retrait des codes manquants.** « Préfère ne pas répondre » est un choix (code 9, déclaré manquant) : LimeSurvey pose la question suivante si sa condition est « Q3 ≠ 1 », puisque 9 ≠ 1. Si l'outil évaluait la condition après avoir retiré le 9 (comme `data.decided` le fait pour tout le reste), il conclurait « non posée » à tort. Le calcul du non applicable lit donc la base avant les décisions de manquants, puis les autres décisions s'appliquent comme aujourd'hui.
4. **Une valeur manquante ne remplit jamais une condition d'exclusion** (`analysis/exclusions.py:57-71`), sauf l'opérateur `missing`, qui teste `blank()`. Avec le non applicable, `missing` doit vouloir dire « posée, sans réponse » ; un non applicable ne remplit aucune condition (§ 5.8.5).
5. **La phrase P4 de la Méthode** (`method._describe`, `method.py:60`) donne déjà *n* quand il est plus petit que le *N* analysé ; elle ne dit pas pourquoi. Le gabarit gagne « parmi les *n* personnes à qui la question a été posée » (§ 5.8.6).

### 4.3 Chez LimeSurvey (documentation consultée le 2026-10-20)

- **Une question non pertinente** (sa condition est fausse) est cachée et **sa valeur est mise à NULL dans la base** de LimeSurvey. Une question montrée et laissée sans réponse, ou le choix « Sans réponse » que LimeSurvey ajoute à une question facultative, est une chaîne vide. **Si l'export (`.sav`, CSV, Excel) distingue ou non NULL et vide n'est pas documenté : à vérifier par l'auteur** (§ 5.7.4). L'outil ne s'y fie pas : il recalcule le non applicable à partir de la condition, ce qui marche aussi pour SurveyMonkey et un `.sav` existant.
- **Dans une expression, une seule variable non pertinente rend toute l'expression fausse**, y compris dans un « ou » ; le suffixe `.NAOK` (« Not Applicable is OK ») fait lire la variable non pertinente comme vide. D'où la forme d'expression du § 5.7.1, qui met `.NAOK` partout et teste le vide explicitement : sans cela, « Q3 = Oui **ou** Q5 = 1 » serait faux pour une personne à qui Q3 n'a pas été posée, même avec Q5 = 1.
- **`is_empty()` est vrai pour une valeur vide ou 0** : il ne convient pas aux codes de choix (« 0 = Non » est courant). L'outil teste `!= ""`, à vérifier dans LimeSurvey 7.6.
- **Mettre un nombre entre guillemets force une comparaison alphabétique** (`> "50"`) : les nombres d'une question numérique sont écrits sans guillemets, les codes de choix avec.
- **La condition d'une section** (`relevance` de la ligne du groupe) et celle de la question sont combinées par « et » ; la pertinence se propage d'elle-même (une question qui dépend d'une question non posée n'est pas posée).
- **L'ordre aléatoire** : `answer_order` (choix d'une liste ; valeurs « Normal », « Random », « Alphabetically », « Random A-Z/Z-A » ; depuis LimeSurvey 5.5.0), `subquestion_order` (sous-questions : énoncés d'une grille, options à cocher ; depuis 6.16.0), `random_group` (les questions qui portent le même nom de groupe d'ordre aléatoire sont mélangées entre elles). L'ancien `random_order` existe encore dans l'export. **La valeur exacte à écrire dans le texte à colonnes** (« random », « 1 »…) n'est pas documentée : elle se lit dans un réexport de l'auteur (§ 5.7.4). La documentation conseille de juger l'ordre aléatoire dans « Prévisualiser le questionnaire », pas dans la prévisualisation d'un groupe.

Sources : [ExpressionScript – Presentation](https://www.limesurvey.org/manual/ExpressionScript_-_Presentation) ; [QS:Answer order](https://www.limesurvey.org/manual/QS:Answer_order) ; [QS:Random group](https://www.limesurvey.org/manual/QS:Random_group) ; [Tab Separated Value survey structure](https://www.limesurvey.org/manual/Tab_Separated_Value_survey_structure).

## 5. Conception

### 5.1 La condition (D-165)

**La forme.** Une condition est une liste de 1 à 10 **termes**, reliés **tous par « et » ou tous par « ou »** :

```python
class Term(Strict):
    target: str  # "Q3" (une question), "Q7.r2" (un énoncé), "Q10.o2" (une option à cocher)
    operator: Literal["eq", "ne", "in", "not_in", "lt", "le", "gt", "ge", "checked", "answered"]
    value: Code | list[Code] | None = None


class Condition(Strict):
    combine: Literal["all", "any"] = "all"
    terms: list[Term] = Field(min_length=1, max_length=10)
```

Et `Question.condition`, `Section.condition` : `Condition | None`. La condition **effective** d'une question est celle de sa section **et** la sienne : cela donne déjà « (A ou B) et C » quand la section porte « A ou B ». Je recommande de **ne pas aller plus loin** dans cette version (ni parenthèses, ni « ou » entre plusieurs « et ») : la plupart des questionnaires de psychologie n'utilisent que « si Q = valeur », parfois deux termes. Le format laisse la place d'ajouter plus tard une liste de conditions reliées par « ou », sans changer celles d'aujourd'hui.

**Les cibles et les opérateurs, selon la nature de la question visée** :

| Cible | Opérateurs | Valeur |
|---|---|---|
| Choix unique, énoncé de grille | `eq`, `ne`, `in`, `not_in`, `answered` | un ou des codes de ses choix, choisis dans une liste |
| Option à cocher (`Q10.o2`) | `checked` | aucune |
| Nombre | `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `answered` | un nombre tapé |
| Texte court ou long, date | `answered` seulement | aucune |

Les cibles se désignent par **les identifiants** (`Q3`, `Q7.r2`), jamais redonnés (D-146), et non par les codes : un code changé ne casse pas la condition. L'interface et le Word montrent le numéro, le code et le texte.

**Le sens, une seule règle : un terme sur une réponse vide, ou sur une question non posée, est faux**, quel que soit l'opérateur (sauf, bien sûr, `answered`, faux lui aussi). Ainsi « Q3 ≠ Oui » n'est pas vrai pour qui n'a pas répondu à Q3. C'est la règle que l'outil écrit pour LimeSurvey (§ 5.7.1) et qu'il applique à l'arrivée de la base : les deux disent la même chose. Pas d'opérateur « sans réponse » ni « non coché » dans cette version : LimeSurvey ne distingue pas, dans une expression, « non posée » de « posée sans réponse » sans fonctions de plus.

**Ce qui est refusé à l'enregistrement** (la question ne change pas) : une cible inconnue, une cible qui est la question elle-même ou un de ses énoncés, un opérateur que la nature de la cible n'admet pas, un code qui n'est pas un choix de la cible, un nombre pour une cible qui n'est pas un nombre, une liste vide pour `in`. **Ce qui est un point de relecture** (§ 5.5) : tout ce qui est permis mais douteux.

**La condition en clair**, une seule fonction (`skip.text`) pour l'éditeur, la Relecture, le Word, le codebook et la Méthode, en français et en anglais :

| Terme | Pour le comité (dans la langue de l'étude) | Pour l'équipe et le codebook |
|---|---|---|
| `Q3 eq 1` | Si vous avez répondu « Oui » à la question 3 | Posée si Q3 (enfants) = 1 (Oui) |
| `Q5 in [1, 2]` | Si vous avez répondu « Temps plein » ou « Temps partiel » à la question 5 | Posée si Q5 (emploi) ∈ {1 (Temps plein), 2 (Temps partiel)} |
| `Q2 ge 18` | Si votre réponse à la question 2 est 18 ou plus | Posée si Q2 (age) ≥ 18 |
| `Q10.o2 checked` | Si vous avez coché « Vélo » à la question 10 | Posée si Q10 (transport) : Vélo coché |
| `Q7.r2 eq 4` | Si vous avez répondu « Plutôt d'accord » à l'énoncé « … » de la question 7 | Posée si Q7_SQ002 = 4 (Plutôt d'accord) |
| `Q4 answered` | Si vous avez répondu à la question 4 | Posée si Q4 (nb_enfants) a une réponse |

Les termes se relient par « et » (« and ») ou « ou » (« or ») ; une section : « Cette section s'adresse aux personnes qui ont répondu … » (« This section is for people who answered … »).

### 5.2 L'ordre aléatoire (D-166)

Trois cases, chacune un booléen :

| Où | Champ | Ce qui est mélangé | LimeSurvey |
|---|---|---|---|
| Une section | `Section.shuffle` | ses questions | le même `random_group` (le code de la section) sur chacune de ses questions |
| Une grille | `Question.shuffle` | ses énoncés | `subquestion_order` |
| Un choix unique | `Question.shuffle` | ses choix | `answer_order` |
| Des cases à cocher | `Question.shuffle` | ses options | `subquestion_order` |

L'option « Autre » reste à la fin (LimeSurvey la place toujours en dernier). **Hors de cette version** : l'ordre aléatoire des sections (non documenté pour les groupes dans LimeSurvey), des colonnes d'une grille (une échelle se lit dans l'ordre), et le tirage d'un sous-ensemble de questions. **L'ordre aléatoire n'entre dans aucun calcul** : les noms des variables, les codes et les colonnes de la base ne changent pas avec l'ordre de présentation. Il est dit dans le Word (les deux versions : le comité doit le savoir), dans le codebook (« Ordre de présentation : aléatoire ») et dans la Méthode (§ 5.8.6).

### 5.3 Les items de contrôle d'attention (D-170)

- **Le marquage**, dans le questionnaire : `Question.attention: list[str] | None` pour une question à choix unique, `GridRow.attention: list[str] | None` pour un énoncé de grille, la liste étant **les codes des bonnes réponses** (au moins un, chacun un choix de la question). Un énoncé de contrôle dans une grille est le cas le plus courant (« Pour cet énoncé, choisissez Plutôt d'accord »).
- **Il n'entre dans aucun score** : la variable d'un énoncé de contrôle est rattachée au groupe de sa grille **hors des membres**, comme l'« autre » d'une question à cocher (`Group.attached`) ; il n'entre donc ni dans la cotation, ni dans l'alpha, ni dans la ligne droite, ni dans la complétude. Un groupe dont un membre est un item de contrôle est refusé.
- **À l'arrivée de la base, une règle d'exclusion proposée**, d'une **sorte nouvelle**, `attention` :

```python
class AttentionCheck(Strict):
    variable: str  # nom d'origine
    correct: list[Code]  # bonnes réponses


class AttentionRule(Strict):
    id: str
    kind: Literal["attention"] = "attention"
    checks: list[AttentionCheck] = Field(min_length=1)
    min_failed: int = Field(default=1, ge=1)  # exclue à partir de ce nombre d'échecs
    empty: Literal["failed", "ignored"]  # un item laissé sans réponse : échec, ou ignoré
    reason: NonEmptyText
    source: str | None = None
```

  Pourquoi pas la sorte `condition` : elle ne porte que sur une variable, une valeur manquante ne la remplit jamais, et elle n'a pas de « n'est pas parmi » ; « échoue à au moins 1 des 2 items » demanderait deux règles qui comptent deux fois les personnes qui échouent aux deux, et le diagramme de flux les donnerait séparément. La sorte nouvelle se lit d'un coup : « A échoué à au moins 1 des 2 items de contrôle (Q7_SQ007, Q10) ». **Le vide n'a pas de valeur par défaut** : l'équipe choisit « échec » ou « ignoré », comme un seuil (une réponse sautée à un item de contrôle est-elle de l'inattention ? les deux se défendent). Un item non posé (non applicable) n'est jamais un échec.

  **Proposée, jamais appliquée seule** (D-095) : la page « Méthode » montre, parmi les personnes gardées, « 12 personnes ont échoué à au moins un item de contrôle ; 5 aux deux », et « En faire une règle », qui remplit le formulaire sans rien appliquer. Pour une base sans questionnaire conçu, le formulaire permet de choisir les variables et leurs bonnes réponses à la main. Refusée : une variable inconnue, un identifiant ou un texte libre, une bonne réponse qui n'est pas un code de la variable, un `min_failed` plus grand que le nombre d'items.

  Partout comme les autres sortes : `exclusions.rule_text`, le diagramme de flux, les scripts de préparation SPSS et R (un compteur d'échecs, puis `ddict_exclusion`), l'empreinte, la phrase P2, le préenregistrement.

### 5.4 La durée estimée de passation (D-171)

**La formule**, calculée sur le questionnaire seul :

> durée = mots lus ÷ vitesse de lecture + Σ temps de réponse

- **Mots lus** : titres et consignes de section, texte et consigne de chaque question, choix (une fois par question), énoncés d'une grille et ses titres de colonnes (une fois), textes d'affichage ; les mots comptés comme le fait Word (suites séparées par des espaces).
- **Vitesse de lecture** : une valeur par langue de l'étude, **tirée d'une source publiée et citée dans la formule** : les textes standardisés du test IReST (Trauzettel-Klosinski et Dietz, 2012), la même tâche dans 17 langues, **195 mots par minute en français, 228 en anglais**. *Vérifié à l'étape 1* : ces valeurs sont celles du tableau de l'article, mais **mesurées à voix haute**, non en lecture silencieuse comme cette section le disait d'abord ; une lecture silencieuse est plus rapide, la durée est donc plutôt surestimée, ce qui convient à une durée annoncée au comité (D-171). La méta-analyse de Brysbaert (2019), 238 mots par minute en lecture silencieuse d'un texte informatif en anglais, ne donne pas de valeur mesurée pour le français.
- **Temps de réponse**, après la lecture : 3 secondes par réponse fermée (une question à choix, un énoncé de grille, une question à cocher entière), 10 secondes par réponse ouverte courte, nombre ou date, 60 secondes par réponse longue. **Je n'ai pas trouvé de source primaire vérifiable pour ces trois temps** : ce sont des repères de l'outil, dits comme tels partout où la durée paraît, et recalibrés par le pilote (v0.26), qui comparera la durée réelle médiane à l'estimation.
- **Une fourchette, pas un nombre** : sans filtre, une seule durée ; avec des filtres, du chemin le plus court (aucune question filtrée posée) au plus long (toutes posées), calculés sans énumérer les chemins (chaque question filtrée comptée ou non). Arrondie à la minute : « environ 11 à 14 minutes ».

**Où elle paraît** : en tête de la page « Relecture », avec la formule et ses termes (mots, vitesse et sa source, nombre de réponses de chaque sorte) ; dans le Word pour le comité, une phrase en tête (« Durée estimée : environ 11 à 14 minutes. »), et la formule dans le Word de travail ; sur la page « Méthode », **à côté** du champ « Seuil (secondes) » de la durée de passation, en texte (« Repère : durée estimée de 11 à 14 minutes »), **sans bouton qui la reprend** : un seuil reste tapé et sourcé par l'équipe (D-095, principe 4).

### 5.5 La page « Relecture » : les points nouveaux

Tous calculés (`design_points`), chacun avec son bouton vers la question :

| Point | Pourquoi |
|---|---|
| Condition sur une question qui vient après, ou dans une section qui vient après | Elle ne peut pas encore avoir de réponse : la question ne serait jamais posée |
| Cycle (Q4 dépend de Q5, qui dépend de Q4, directement ou par une section) | Jamais posée ; normalement impossible si le point précédent est réglé, mais une section filtrée sur sa propre question en crée un |
| Cible retirée depuis (une condition qui vise une question, un énoncé ou une option disparus) | Le retrait l'avait dit (`design.citations`) ; la condition reste à corriger |
| Valeur qui n'est plus un choix de la cible (un choix retiré ou recodé après coup) | La condition ne serait jamais vraie |
| Condition sur une question facultative | Un vide la rend fausse : « si Q3 = Oui » ne pose pas Q4 à qui a sauté Q3 ; c'est peut-être voulu (point d'information) |
| Question obligatoire sous une condition jamais vraie (contradiction : « Q2 ≥ 18 et Q2 < 18 », un `in` vide de choix existants, un terme sur une question elle-même jamais posée) | Une question obligatoire jamais posée ; la contradiction se calcule terme par terme sur une même cible |
| Section entière filtrée sans texte d'affichage | Une personne ne voit pas pourquoi elle saute ; un point d'information |
| Ordre aléatoire d'une section qui contient un texte d'affichage, un item de contrôle ou une question qui sert de condition à une autre de la section | Le texte d'affichage ou la question filtre se retrouverait au mauvais endroit |
| Ordre aléatoire des choix avec un choix de non-réponse parmi eux (« Préfère ne pas répondre », la liste de D-047) | Il serait mélangé avec les autres ; le « Sans réponse » de LimeSurvey, lui, reste à la fin |
| Item de contrôle facultatif, ou sous une condition | Un vide ou une question non posée brouillent l'échec ; point d'information |
| Item de contrôle dont une bonne réponse n'est plus un choix | Toujours un échec |

### 5.6 Le Word, l'aperçu et le codebook prévu

- **Le Word pour le comité** : sous le numéro d'une question filtrée, en italique, « Si vous avez répondu « Oui » à la question 3 : » ; sous le titre d'une section filtrée, « Cette section s'adresse aux personnes qui … » ; « (Les énoncés de cette question sont présentés dans un ordre aléatoire.) », « (Les choix sont présentés dans un ordre aléatoire.) », « (Les questions de cette section sont présentées dans un ordre aléatoire.) » ; en tête, la durée estimée. Un item de contrôle paraît comme une question ordinaire (c'est ce que voit la personne) ; le Word de travail le marque.
- **Le Word de travail** : en plus, la condition pour l'équipe (« Posée si Q3 (enfants) = 1 (Oui) »), « Item de contrôle : bonne réponse 4 (Plutôt d'accord) », et la formule de la durée.
- **L'aperçu** de la page « Publier » montre les mêmes mentions, sans rien cacher : tout le questionnaire, filtres dits en clair.
- **Le codebook** (Excel, Markdown, contexte d'analyse) : une colonne « Posée si » pour chaque variable d'une question filtrée, la condition effective en clair pour l'équipe ; « Ordre de présentation : aléatoire » ; « Item de contrôle (bonne réponse : …) » ; et, s'ils sont choisis, les codes du non applicable et du manquant (§ 5.8.4).

### 5.7 LimeSurvey

#### 5.7.1 Écrire

Chaque terme devient une expression qui teste le vide d'abord, avec `.NAOK` partout (§ 4.3) :

| Terme | Expression écrite |
|---|---|
| `Q3 eq 1` | `(enfants.NAOK != "" and enfants.NAOK == "1")` |
| `Q5 in [1, 2]` | `(emploi.NAOK != "" and (emploi.NAOK == "1" or emploi.NAOK == "2"))` |
| `Q5 not_in [3]` | `(emploi.NAOK != "" and emploi.NAOK != "3")` |
| `Q2 ge 18` | `(age.NAOK != "" and age.NAOK >= 18)` |
| `Q10.o2 checked` | `(transport_SQ002.NAOK == "Y")` |
| `Q7.r2 eq 4` | `(climat_SQ002.NAOK != "" and climat_SQ002.NAOK == "4")` |
| `Q4 answered` | `(nbenfants.NAOK != "")` |

Les termes se joignent par ` and ` ou ` or ` ; la condition d'une section va dans la colonne `relevance` de sa ligne `G`, celle d'une question dans la colonne `relevance` de sa ligne `Q`. Les codes sont ceux que l'outil écrit déjà (D-156 : le radical sans ses « _ » ; `code_SQ001`), donc des lettres et des chiffres : aucun texte, aucun accent, aucune accolade n'entre dans une expression. L'ordre aléatoire va dans `answer_order`, `subquestion_order` et `random_group` (§ 5.2), à la valeur que le réexport de l'auteur montrera. Le résumé avant l'écriture dit le nombre de conditions et d'ordres aléatoires écrits ; l'item de contrôle reste dans l'outil (LimeSurvey n'a pas cette notion) et le résumé le dit.

#### 5.7.2 Lire

`lss.read_limesurvey` lit la colonne `relevance` (texte à colonnes) ou les champs `relevance` des questions et des groupes (`.lss`), et l'ordre aléatoire. **Seules les expressions de la forme exacte du § 5.7.1 sont lues** (une grammaire fermée : termes, `and` ou `or` d'un seul niveau, codes connus du questionnaire, valeurs entre guillemets pour un choix, nombre nu pour un nombre) ; `1` et le vide veulent dire « toujours posée ». **Toute autre expression est refusée et listée**, jamais devinée : la question est lue sans condition, avec un point à vérifier « condition LimeSurvey non lue : … » qui montre l'expression telle quelle. Le tableau `conditions` de l'ancien éditeur de conditions de LimeSurvey n'est pas lu : LimeSurvey le traduit lui-même en `relevance`, que l'outil lit.

Pour **une base LimeSurvey existante** documentée avec son `.lss` (v0.20, A3), une condition lue devient la condition des variables de la question (§ 5.8.7, origine `lss`), à accepter comme le reste du questionnaire lu.

#### 5.7.3 Comparer le réexport

`design_compare` gagne trois sortes de différences : **condition changée** (montrée en clair des deux côtés), **condition non lue** (l'expression de LimeSurvey hors de la grammaire : « Reprendre dans le projet » est alors impossible pour la condition, la page dit de la corriger dans LimeSurvey ou dans l'outil), **ordre aléatoire changé**. « Reprendre dans le projet » reprend la condition lue avec le reste de la question, comme aujourd'hui (décision par question entière).

#### 5.7.4 Ce que l'auteur devra vérifier dans LimeSurvey Cloud 7.6

Par une vraie importation, comme pour la v0.20 (étape 6, arrêt) :

1. **L'importation** du fichier avec des conditions de question et de section : acceptée, sans avertissement ; la « logique du questionnaire » (le fichier de logique de LimeSurvey) ne montre aucune erreur de syntaxe (en rouge).
2. **Les quatre cas d'une condition**, dans « Prévisualiser le questionnaire » : la question filtre répondue avec le bon code, avec un autre code, **avec le code « 0 »** (s'il y en a un), laissée sans réponse (« Sans réponse ») ; puis une question filtrée par une question elle-même non posée (la cascade) ; puis « âge ≥ 18 » avec 9 et 18 (comparaison de nombres, pas de textes).
3. **Un « ou »** dont un terme vise une question non posée : la question doit être posée quand l'autre terme est vrai (c'est ce que `.NAOK` doit garantir).
4. **L'ordre aléatoire** : les énoncés d'une grille, les choix d'une liste, les options à cocher et les questions d'une section changent d'ordre d'une prévisualisation du questionnaire à l'autre ; « Autre » et « Sans réponse » restent à la fin.
5. **Le réexport** (`.lss` et texte à colonnes) : les expressions reviennent-elles telles qu'écrites (ou LimeSurvey les réécrit-il) ? Quelles valeurs portent `answer_order`, `subquestion_order` et `random_group` ? C'est ce réexport qui fixe la valeur écrite.
6. **Les réponses** : cinq réponses inventées qui passent par les deux branches, exportées en `.sav`, en CSV et en Excel ; une question non posée et une question laissée vide y sont-elles distinguées (NULL et vide) ? La réponse ne change pas le calcul de l'outil, mais elle dira si le rapport de conformité peut aussi comparer ce que LimeSurvey a enregistré.

Ces exports restent hors du dépôt, comme ceux de la v0.20 ; ce qu'ils montrent est reproduit par `scripts/generer_limesurvey_fictif.py`.

### 5.8 Le non applicable (D-167)

#### 5.8.1 La nature

Pour chaque personne et chaque variable d'une question filtrée, trois cas, calculés par une seule fonction (`skip.asked`), sur la base telle qu'enregistrée, avant le retrait des codes manquants (§ 4.2, point 3) :

| Condition effective | Valeur | Nature |
|---|---|---|
| vraie | présente | réponse |
| vraie | vide | **manquant** (posée, sans réponse) |
| fausse | vide | **non applicable** (pas posée) |
| fausse | présente | **anomalie** (réponse sous une condition fausse) |

La condition se calcule de proche en proche, dans l'ordre du questionnaire : une question non posée a une valeur vide pour les conditions qui la visent, donc un terme sur elle est faux (la cascade de LimeSurvey). Une anomalie compte, pour les conditions qui la visent, comme la réponse qu'elle porte (c'est ce qui est dans la base), et elle est dite.

#### 5.8.2 Dans le modèle

Rien n'est gardé par personne : le non applicable est **recalculé en mémoire** à chaque préparation, comme les scores, à partir des conditions du projet. Le projet garde seulement les conditions (§ 5.8.7) et les codes choisis (§ 5.8.4). Le profil d'une variable ne change pas (il décrit le fichier : un vide est un vide) ; les nombres « posée à », « non applicable », « manquant » et « anomalies » se calculent à la demande, comme le rapport de conformité.

#### 5.8.3 À l'arrivée de la base : le rapport de conformité

Le rapport (`arrival.conformity`, page « Base » et `<projet>-conformite.md`) gagne une section « Questions filtrées » : pour chaque question filtrée, posée à *n*, non applicable *n*, manquant *n* ; et une section « Réponses sous une condition fausse », par variable, avec leur nombre (moins de 5 : « < 5 », D-006, le rapport étant un export). Jamais une personne, une ligne ni une valeur. Une anomalie a d'ordinaire une cause que l'équipe connaît : une condition changée en cours de collecte (les versions marquées envoyées le disent, D-150), une base fusionnée à la main, une condition mal recopiée. Le rapport le rappelle en une phrase, sans rien corriger.

#### 5.8.4 Les codes pour SPSS et R

`Settings.blank_codes = {"not_applicable": code | null, "missing": code | null}`, **vides par défaut** : aucun code d'office, comme pour les seuils. L'équipe les choisit sur la page « Export » (par exemple −8 et −9, mais la page n'en propose aucun), pour tout le projet :

- **le non applicable** : écrit dans les cellules non applicables des variables numériques filtrées ;
- **le manquant** : écrit dans les cellules vides posées des variables numériques du questionnaire.

Ils s'écrivent **dans le script de préparation** SPSS et R (le calcul du non applicable y est réécrit à partir des conditions, `RECODE` et `DO IF` en SPSS, `ifelse` en R), déclarés manquants (`MISSING VALUES` ; `na_values` de `labelled_spss`) et étiquetés (« Non applicable », « Sans réponse ») dans le fichier de commandes. Jamais dans la copie documentée (D-026). Les variables de texte gardent leur vide (le codebook le dit). **Refusé**, pour une variable : un code qui est déjà un choix, une étiquette de valeur ou un code observé ; un code égal à un code manquant déjà déclaré ; un dépassement des trois codes manquants discrets de SPSS (`_spss_missing`, `export/syntax.py:165`), dit avec la variable. Sans codes choisis, les scripts ne distinguent pas les deux natures, et la page « Export » le dit en une phrase ; le calcul de l'outil, lui, les distingue toujours.

#### 5.8.5 En aval

- **La préparation** (`data.decided`) rend, avec la table, un masque du non applicable par variable (`PreparedData.not_applicable`) ; un score dont tous les items sont non applicables est non applicable.
- **La règle de complétude** compte les items répondus **parmi les items posés** ; une personne à qui le groupe n'a pas été posé n'est pas exclue par elle (le non applicable n'est pas un manque). Une règle de complétude sur un groupe dont les items ont des conditions différentes est refusée dans cette version (pour un questionnaire conçu, les items d'une grille partagent toujours la condition de leur question).
- **Les conditions d'exclusion** : `missing` veut dire « posée, sans réponse » ; un non applicable ne remplit aucune condition, ni `missing`. Sans condition dans le projet, rien ne change.
- **Le Tableau 1** : pour une variable filtrée, les pourcentages sont calculés parmi les personnes qui ont répondu, et la note dit « Nombre d'enfants : question posée à 164 personnes ; 5 sans réponse. » (« Number of children: asked of 164 people; 5 did not answer. ») au lieu de « 136 valeurs manquantes ».
- **Les analyses** : le calcul ne change pas (le non applicable sort comme le manquant). La page « Analyses », le rapport et la note de chaque tableau disent, pour une variable filtrée, « posée seulement si … ; l'analyse porte sur les personnes à qui elle a été posée ». Sur la page « Plan », une hypothèse qui croise une variable filtrée reçoit la même information, jamais un refus.
- **Le carnet** : les nombres « posée à » sont des agrégats nouveaux de l'analyse ; nouveaux, ils sont gardés aussitôt (D-100), et un projet sans condition n'en a pas.

#### 5.8.6 La Méthode : les phrases proposées

| # | Français | Anglais | Quand |
|---|---|---|---|
| A2b (après A2) | Certaines questions n'étaient posées qu'aux personnes dont les réponses précédentes remplissaient une condition (questions filtrées). Une question qui n'a pas été posée est dite non applicable : elle n'est jamais comptée comme une valeur manquante, et chaque analyse porte sur les personnes à qui ses questions ont été posées. | Some questions were asked only of respondents whose previous answers met a condition (filtered questions). A question that was not asked is treated as not applicable: it is never counted as a missing value, and each analysis includes the people who were asked its questions. | une variable dont parle la Méthode est filtrée |
| A2c | Les questions filtrées sont les suivantes : {libellé} (posée si {condition}) ; … | The filtered questions are: {label} (asked if {condition}); … | idem |
| P4 (nombre) | {libellé} (*M* = {M}, *ÉT* = {ÉT}, *n* = {n}, parmi les {posée} personnes à qui la question a été posée) | {label} (*M* = {M}, *SD* = {SD}, *n* = {n}, of the {asked} people who were asked the question) | la variable est filtrée |
| P4 (catégories) | {libellé} (question posée à {posée} personnes : {modalité}, {p} % ; …) | {label} (asked of {asked} people: {category}, {p}%; …) | idem ; pourcentages parmi les répondants |
| P1b (après P1) | Le questionnaire comprenait {k} items de contrôle de l'attention. / … un item de contrôle de l'attention. | The questionnaire included {k} attention-check items. / … one attention-check item. | un item est marqué, ou une règle `attention` existe |
| I2b (après I2) | Les items étaient présentés dans un ordre aléatoire, tiré pour chaque personne. | The items were presented in a random order, drawn for each respondent. | la grille du groupe coté est en ordre aléatoire |

{condition} est la forme pour l'équipe, sans les codes (« nombre d'enfants : posée si enfants = Oui ») ; {k} en lettres jusqu'à neuf, comme PL3. Aucune phrase ne juge. La règle `attention` paraît dans P2 par sa raison, comme toute règle.

#### 5.8.7 Une condition déclarée à la main (D-168)

Pour une base sans questionnaire conçu, la page d'une variable reçoit un bloc « Posée si », sur le modèle de celui de l'éditeur, mais **sur des variables** : `VariableEntry.asked_if = {condition, origin, date}`, où les termes visent des noms d'origine (un code, une étiquette de valeur, un nombre, « a une réponse »). L'**origine** dit d'où elle vient : `team` (tapée par une personne, une décision : elle s'enregistre telle quelle, elle n'est jamais proposée par un calcul ni par l'IA), `designed` (calculée par `plan_variables` à partir du questionnaire conçu, un fait, comme la question rattachée d'office) ou `lss` (lue dans un `.lss`, proposée tant qu'une personne ne l'a pas acceptée, comme le reste du questionnaire lu). Une même condition peut se copier sur plusieurs variables d'un coup (les items d'une grille). Les refus sont ceux du § 5.1, plus : un identifiant ou un texte libre en cible, sauf avec `answered` (une condition ne nomme jamais la valeur d'un texte libre). En ligne de commande : `ddict conditions lister | poser | retirer`.

Pour un projet conçu, une fois la base arrivée, les variables gardent la condition qu'elles avaient à l'arrivée ; un changement du questionnaire ensuite ne la change pas (règle de la v0.20, E4), et le rapport de conformité dit la différence.

### 5.9 Le format 0.12.0 et l'empreinte (D-172)

Champs nouveaux, tous facultatifs, avec une valeur par défaut :

| Modèle | Champ |
|---|---|
| `Term`, `Condition` (nouveaux) | § 5.1 |
| `Section` | `condition`, `shuffle` |
| `Question` | `condition`, `shuffle`, `attention` |
| `GridRow` | `attention` |
| `VariableEntry` | `asked_if` (`AskedIf` : `condition`, `origin`, `date`) |
| `Settings` | `blank_codes` (`not_applicable`, `missing`) |
| `ExclusionRule` | la sorte `attention` (`AttentionRule`, `AttentionCheck`) |

Un projet 0.11.0 s'ouvre tel quel ; un projet 0.12.0 est « écrit par une version plus récente » pour la 0.20.2 (`ProjectNewer`).

**L'empreinte du codebook doit inclure les conditions** : elles changent les dénominateurs, les *n* que la Méthode dit, la règle de complétude et les phrases ; le carnet doit voir qu'elles ont changé (D-089). Comme les exclusions et les recodages, **seulement quand il y en a** :

- une condition déclarée sur une variable (`asked_if`) entre dans l'empreinte de la variable, seulement si elle existe ;
- les codes du non applicable et du manquant y entrent seulement s'ils sont choisis ;
- les conditions, l'ordre aléatoire et les items de contrôle d'un questionnaire conçu y entrent par l'empreinte du questionnaire, que l'empreinte du codebook reprend déjà ; **`design.content_fingerprint` n'y met un champ nouveau que s'il est rempli**, pour qu'un questionnaire sans condition garde son empreinte et ses publications (§ 4.2, point 1) ;
- la règle `attention` y entre comme toute règle d'exclusion.

L'ordre aléatoire change donc l'empreinte d'un questionnaire conçu (c'est un changement du questionnaire, que le comité et LimeSurvey doivent connaître), mais pas les chiffres d'une analyse : le carnet recalcule, ne trouve aucune différence, et ne demande rien (D-089 ne demande une confirmation que pour un chiffre changé).

## 6. Ligne de commande

`ddict conditions lister | poser | retirer` (une condition à la main, § 5.8.7 : `--variable`, `--terme VARIABLE OPÉRATEUR [VALEUR…]` répétable, `--ou`) ; `ddict codes vides --non-applicable CODE --manquant CODE` (et `--effacer`) ; `ddict exclusions ajouter --attention VARIABLE=CODE[,CODE…] … --echecs N --vide echec|ignore` ; `ddict questionnaire duree <projet>` (la durée estimée et sa formule). L'édition des conditions d'un questionnaire conçu se fait dans l'interface, comme le reste de l'éditeur (D-151) ; `ddict questionnaire limesurvey`, `word` et `comparer` en tiennent compte sans option nouvelle.

## 7. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Décisions et fiche : D-163 à D-172 au journal ; conception (§ 25 corrigé pour la numérotation, nouvelle § 27) ; vitesses de lecture vérifiées dans leurs sources ; phrases du § 5.8.6 et du § 5.1 relues | Validés par l'auteur avant tout code |
| 2 | Format 0.12.0 : modèles du § 5.9, migration, empreinte | Un projet 0.11.0 s'ouvre tel quel : même codebook octet pour octet (sauf la ligne « Format du projet »), même empreinte du codebook, même empreinte du questionnaire conçu après un changement puis son retour, aucune publication marquée « modifiée » ; aller-retour octet pour octet d'un projet 0.12.0 |
| 3 | `ddict.project.skip` et `ddict.design` : poser, changer, retirer une condition, un ordre aléatoire, un item de contrôle ; refus du § 5.1 ; condition effective ; `skip.text` en français et en anglais ; `skip.asked` sur un tableau ; `plan_variables` reporte la condition sur les variables prévues ; le retrait d'une question dit les conditions qui la visent | Tests sans Streamlit : chaque opérateur sur chaque nature ; chaque refus ; la condition en clair de chaque ligne du tableau du § 5.1 ; sur des tableaux construits à la main, les quatre cas du § 5.8.1, la cascade, un « ou » avec un terme non posé, un code manquant déclaré dans la question filtre (§ 4.2, point 3) |
| 4 | Éditeur et Relecture : le bloc « Posée si » (lignes de termes, « et » ou « ou »), les cases d'ordre aléatoire et d'item de contrôle ; les points du § 5.5 ; la durée estimée en tête de la Relecture | AppTest : une condition posée, changée, retirée sur une question et une section, enregistrée par `c.save` avec brouillon et contrôle à l'écriture ; chaque point calculé sur un questionnaire fictif piégé ; la durée du questionnaire fictif égale au corrigé ; vérifié dans le navigateur |
| 5 | Word, aperçu, codebook prévu : filtres et ordres aléatoires en clair, item de contrôle (Word de travail), durée ; colonne « Posée si » | Mêmes octets deux fois de suite ; le Word du comité sans code ni nom ; chaque condition du questionnaire fictif dite comme le tableau du § 5.1, en français et en anglais ; rendu vérifié dans Word |
| 6 | LimeSurvey, écrire : expressions du § 5.7.1, ordre aléatoire, résumé (**arrêt : l'auteur importe pour de vrai**, liste du § 5.7.4) | Le fichier écrit, relu par l'étape 7, redonne les conditions et les ordres ; importé par l'auteur, les cas du § 5.7.4 conformes ; corrections consignées dans `docs/essais/` |
| 7 | LimeSurvey, lire et comparer : la grammaire fermée, les expressions refusées et listées, les trois sortes de différences | Chaque forme écrite relue à l'identique ; une expression hors grammaire (une fonction, des parenthèses imbriquées, une accolade, un code inconnu) refusée et listée, jamais devinée ; le réexport réel de l'auteur relu sans différence, puis avec une condition changée dans LimeSurvey |
| 8 | Arrivée de la base : non applicable, manquant, anomalies, rapport de conformité ; conditions à la main (page de la variable, `ddict conditions`) | Sur la base fictive du § 8 : chaque nombre du corrigé, dans le rapport et la page ; une anomalie de moins de 5 dite « < 5 » ; les mêmes nombres sur l'export SurveyMonkey fictif avec des conditions posées à la main ; aucun témoin individuel dans le rapport |
| 9 | En aval : préparation et masques, complétude, conditions d'exclusion, Tableau 1, analyses, Méthode (§ 5.8.6), codes du non applicable et du manquant dans les scripts SPSS et R, codebook | Les effectifs de la complétude et du Tableau 1 égaux au corrigé ; la Méthode phrase par phrase, en français et en anglais ; les mêmes effectifs et les mêmes codes dans l'outil, dans PSPP et dans R ; un projet sans condition donne les mêmes fichiers qu'en 0.20.2 |
| 10 | Items de contrôle : la sorte `attention`, son signal, « En faire une règle », les scripts, le diagramme de flux, le préenregistrement | Les échecs du corrigé (un, deux, vide compté ou ignoré) dans l'outil, dans PSPP et dans R ; aucune règle appliquée sans être ajoutée ; un groupe qui contiendrait un item de contrôle refusé ; la page et la ligne de commande donnent la même règle |
| 11 | Version 0.21.0 : guides (« Filtres, ordre aléatoire et non applicable », français et anglais), scénario manuel (§ 9), captures, CHANGELOG | Scénario joué par l'auteur dans la fenêtre de l'icône |

**Fait en 1** : D-163 à D-172 au journal (D-163 avec les resserrements du § 13.4 de la feuille de route ; ses formulations de la règle 3, de la règle 2 et du principe 5 attendent la v0.27, comme D-143 pour la règle 4) ; conception, § 12 et § 25 (les sources en v0.24) et nouvelle § 27 ; vitesses de lecture vérifiées dans le tableau de l'IReST (195 et 228 mots par minute, mais à voix haute : § 5.4 et D-171 le disent) ; phrases du § 5.1 et du § 5.8.6 validées avec le plan.

**Fait en 2** (format 0.12.0) : `Term`, `Condition`, `BlankCodes`, `AttentionCheck`, `AttentionRule` ; les champs du § 5.9, chacun à la fin de son modèle pour garder l'ordre des clés ; des refus dans les modèles pour ce qui n'a pas de sens (un opérateur sans sa valeur ou avec une valeur en trop, plus de 10 termes, l'ordre aléatoire d'une question ouverte, un item de contrôle ailleurs que sur un choix unique ou un énoncé de grille, deux codes égaux pour les vides, plus d'échecs exigés que d'items, une règle d'attention sans le sort du vide). **Précision** : la condition d'une variable est une valeur suivie (`TrackedValue[Condition]`), et les trois origines de D-168 sont celles qui existent déjà : `human` pour une condition tapée, `computed` pour une condition tirée du questionnaire conçu, `questionnaire` (proposée) pour une condition lue dans un `.lss` ; l'empreinte ne compte qu'une condition acceptée. `design.question_content` et `section_content`, partagées par l'empreinte du questionnaire conçu et par celle des points de relecture gardés (`design_points.fingerprint`, **qui avait le même piège** : chaque point « gardé tel quel » se serait rouvert), laissent de côté un champ nouveau vide. Les trois endroits qui traitaient « toute autre règle » comme un doublon (`analysis/exclusions.hits`, les deux scripts de préparation) et `rule_text` nomment désormais chaque sorte et refusent une règle `attention` jusqu'à l'étape 10, au lieu de la prendre pour un doublon. Le projet de référence est régénéré. Tests : `tests/test_format_0_12.py` (un projet 0.11.0 relu identique, avec le même rapport Markdown et la même empreinte ; un questionnaire conçu marqué envoyé, relu en 0.11.0, changé puis rétabli, sans avertissement ; les points gardés ; chaque refus des modèles ; l'aller-retour octet pour octet d'un projet qui a tous les champs).

**Fait en 3** (fonctions, sans interface) : `ddict.project.skip` (les natures de cible et leurs opérateurs, les refus, la condition effective, la condition en clair pour le comité et pour l'équipe, `asked`, `holds` et `natures` sur un tableau) ; dans `ddict.design`, `set_condition`, `set_shuffle`, `set_attention` (refusés par `DesignError`, le projet inchangé). **Trois précisions.** (1) **La condition d'une variable est une liste de conditions, toutes vraies** (`TrackedValue[list[Condition]]`), et non une seule : la condition effective d'une question est celle de sa section **et** la sienne, et « (A ou B) et C » ne tient pas dans une seule condition ; une condition tapée à la main sera une liste d'une condition. Le format 0.12.0, pas encore publié, est corrigé sur place. (2) **La forme pour l'équipe d'un énoncé de grille** est « Q7 (climat_SQ002) = 4 (Plutôt d'accord) », sur le modèle de « Q3 (enfants) », au lieu de « Q7_SQ002 » du tableau du § 5.1 ; tant que le code de la question n'est pas décidé, ni lui ni le nom ne paraissent (« Q1 = 1 (Oui) »), pour ne jamais montrer un identifiant à côté d'un numéro qui diffère. (3) En anglais, « Si vous avez répondu à la question 4 » devient « If you gave an answer to question 4 ». Le reste comme prévu : la cascade vient d'elle-même (une question non posée est vide, une anomalie compte comme sa réponse) ; « coché » est vrai pour une case remplie autre que « N » ou 0 ; une modification de la question garde sa condition, son ordre aléatoire et ses items de contrôle tant que sa nature les admet ; un énoncé de contrôle est rattaché au groupe de sa grille hors des membres ; `plan_variables` reporte la condition effective sur les variables prévues (origine `computed`, une condition tapée reste), sur les noms des variables et avec les codes tels que la variable les tient (1, pas « 1 »), et ne reporte rien tant qu'une cible a disparu ; `citations` dit les conditions qui visent une question avant son retrait. Tests : `tests/test_skip.py` (116).

**Fait en 4** (éditeur et Relecture) : le bloc « Posée si » est un tableau (question visée, opérateur, valeur) dans le formulaire d'une question et dans « Modifier » d'une section, enregistré avec le reste par le même « Enregistrer » (brouillon et contrôle à l'écriture comme le reste du formulaire) ; les codes des choix visés s'affichent sous le tableau ; les bonnes réponses d'un énoncé de contrôle sont une colonne du tableau des énoncés. `design_duration` calcule la durée (une fourchette avec des filtres) ; `design_points` gagne les points du § 5.5, et un point peut viser une section (son empreinte : la section et ses questions). **Deux précisions.** (1) **« Condition jamais vraie » est dit pour toute question**, obligatoire ou non : une question jamais posée est une erreur dans les deux cas. (2) Un point sur une condition est gardé tant que **la question qui porte la condition** ne change pas ; un changement de la question visée ne le rouvre pas (il ouvre, le cas échéant, ses propres points). Vérifié dans le navigateur (Edge, 1400 × 900) : la liste, le formulaire d'une question filtrée, la section filtrée, la Relecture et sa formule ; deux pluriels corrigés à cette occasion. Tests : `tests/test_design_conditions.py` (24 : la durée du questionnaire fictif comptée à la main, 82 mots, cinq réponses fermées et une courte ; chaque point sur son piège) et `tests/test_design_conditions_ui.py` (14).

**Fait en 5** (Word, aperçu, codebook prévu) : les deux Word disent la durée estimée en tête, la condition d'une question avant elle (« Si vous avez répondu « Oui » à la question 3 : »), celle d'une section sous son titre, et chaque ordre aléatoire ; le Word de travail ajoute la condition pour l'équipe, les items de contrôle et leurs bonnes réponses, et la formule de la durée ; l'aperçu de la page « Publier » dit la même chose (« Montrer les noms » : les mots de l'équipe). Le codebook (Excel, Markdown, contexte d'analyse) gagne « Posée si » et « Présentation » (ordre aléatoire, item de contrôle), **seulement quand un projet en a** : un projet sans condition garde ses colonnes et ses fichiers. **Une précision** : dans le codebook, une option à cocher se dit « transport_2 coché » (la variable est l'option). Le Word d'un questionnaire conçu sans condition gagne seulement sa durée estimée. Tests : `tests/test_conditions_outputs.py` (7). **Le rendu dans Word reste à vérifier par l'auteur.**

**Fait en 6** (LimeSurvey, écrire) : `design_limesurvey.expression` écrit chaque terme sous la forme du § 5.7.1 (le vide testé d'abord, `.NAOK` partout, un code entre guillemets, un nombre nu), dans la colonne `relevance` de la ligne `G` d'une section et de la ligne `Q` d'une question ; les sous-questions restent à `1`. L'ordre aléatoire : `answer_order` pour les choix d'une liste, `subquestion_order` pour les énoncés d'une grille et les options à cocher, `random_group` (l'identifiant de la section, « S2 ») pour les questions d'une section ; **les valeurs écrites (`random`) sont celles des options de la documentation, à confirmer par le réexport de l'auteur**. Une condition qui vise ce qui a été retiré refuse l'écriture ; une valeur qui n'est plus un choix ne la refuse pas (la Relecture le dit). Le résumé dit le nombre de conditions et d'ordres aléatoires, et que les items de contrôle restent dans l'outil ; l'importation pas à pas gagne la logique du questionnaire et la prévisualisation de chaque branche. Le questionnaire de l'essai : `tests/projet_filtres.py` ; ce qu'il faut vérifier : `docs/essais/2026-10-21-limesurvey-filtres.md`. Tests : `tests/test_limesurvey_conditions.py` (15). **Arrêt : l'auteur importe pour de vrai** ; le critère « relu par l'étape 7 » attend l'étape 7.

**Fait en 7** (LimeSurvey, lire et comparer) : `questionnaire/relevance.py`, la grammaire fermée du § 5.7.2 (des jetons, puis chaque terme comparé aux cinq formes que l'outil écrit) ; `lss.read_limesurvey` lit la `relevance` des questions et des groupes (`grelevance` dans un `.lss`) et l'ordre aléatoire (`answer_order`, `subquestion_order`, l'ancien `random_order`, `random_group` ; dans un `.lss`, la table `question_attributes`). Une expression hors de la grammaire est refusée et **gardée telle quelle** (`condition_unread`, champ nouveau du format 0.12.0, pas encore publié, vide sinon et hors des empreintes tant qu'il est vide), avec le point à vérifier « condition LimeSurvey non lue » ; un ordre d'une autre valeur, ou un groupe d'ordre aléatoire partagé par une partie seulement d'une section, est un point à vérifier. `design_compare` compare les conditions par les codes qu'elles visent, comme LimeSurvey les nomme, et gagne les trois sortes de différences (condition changée, dite en clair des deux côtés ; condition non lue ; ordre aléatoire changé), pour une question et pour une section (appariée par son rang). « Reprendre dans le projet » reprend la condition et l'ordre avec le reste ; il est **refusé avant tout changement** quand la condition de LimeSurvey n'est pas lue, ou vise ce que le projet n'a pas. **Une précision** : « parmi » un seul code s'écrit comme « = », et « pas parmi » un seul code comme « ≠ » ; relus, ils reviennent en « = » et « ≠ », et la comparaison les tient pour égaux. Le report d'une condition lue sur les variables d'une base existante (§ 5.7.2, dernier alinéa) vient avec l'étape 8. Tests : `tests/test_lss_conditions.py` (38 : chaque forme relue, le questionnaire de l'essai relu sans différence, 18 expressions refusées, un `.lss`, la comparaison et la reprise, la page). **Le réexport réel de l'auteur reste à relire.**

**Fait en 8** (arrivée de la base, conditions à la main) : `skip.counts` donne, pour chaque variable à condition acceptée, posée à, non applicable, manquant et anomalies, sur la base telle qu'enregistrée ; une case laissée vide n'est un manque que si aucune case de la question n'est cochée (sinon « non cochée », une réponse), comme le codebook le dit. Une variable garde à l'arrivée la condition qu'elle avait. Le rapport de conformité (et la page « Base ») gagne « Questions filtrées » (un tableau par variable : posée à, non applicable, manquant) et « Réponses sous une condition fausse », chaque effectif de 1 à 4 dit « < 5 ». `ddict.project.asked` : la condition d'une variable tapée par l'équipe, les refus du § 5.1 et du § 5.8.7, l'acceptation d'une condition lue ; `asked.propose_from_lss` propose, à la lecture d'une structure LimeSurvey pour une base déjà là, les conditions des questions sur les noms des variables (par leur lien, sinon par le lien que leur code rend sûr). Le bloc « Posée si » de la page d'une variable, avec ses nombres, « La même condition pour » et, pour une condition lue, « Accepter » et « Rejeter » ; `ddict conditions lister | poser | retirer | accepter | rejeter`. `scripts/generer_base_filtres.py` écrit la base du § 8 (le fichier LimeSurvey, 300 réponses en `.sav` et CSV de LimeSurvey, les mêmes en `.sav` de SurveyMonkey, le corrigé compté personne par personne). **Trois précisions.** (1) Les sections « Bien-être » et « Habitudes » sont aussi posées si le consentement est donné : un refus termine le questionnaire, et le § 8 dit tout S2 à S5 non applicable. (2) Le rapport donne un tableau **par variable** plutôt que par question : les manquants diffèrent d'un énoncé à l'autre d'une grille. (3) Le projet du questionnaire n'est pas dans `exemples/` (un `.dd.json` reste hors du dépôt, `.gitignore`) : la fonction `project()` du script le construit ; l'export Excel de LimeSurvey n'est pas écrit (le `.sav` et le CSV suffisent aux comptes). Tests : `tests/test_filtres_arrival.py` (7 : les fichiers réécrits à l'identique, chaque nombre du corrigé sur le `.sav` et le CSV, le rapport sans témoin individuel, la page « Base ») et `tests/test_asked.py` (12 : les mêmes nombres sur l'export SurveyMonkey avec des conditions posées à la main, chaque refus, la ligne de commande, les conditions proposées par la structure LimeSurvey puis acceptées, la page d'une variable).

**Fait en 9** (en aval) : la préparation garde un masque de ce qui n'a pas été posé (`PreparedData.not_applicable`, recalculé en mémoire sur la base telle qu'enregistrée ; un score dont tous les items sont non posés l'est aussi) ; la complétude compte parmi les items posés et n'exclut pas qui n'a pas reçu le groupe ; « manquant » veut dire posée et laissée vide ; une complétude sur des items aux conditions différentes est refusée. Le Tableau 1 calcule une question filtrée parmi les personnes qui l'ont reçue et y ont répondu, et la note dit « question posée à 160 personnes ; 5 sans réponse ». La note de chaque tableau d'analyse dit « posée seulement si … ; l'analyse porte sur les personnes à qui elle a été posée ». La Méthode gagne A2b, A2c, les deux formes filtrées de P4, P1b et I2b ; le carnet garde les nombres « posée à » (`v{i}_asked`), seulement quand il y en a. Les codes du non applicable et du manquant (`ddict.project.blank`) : la page « Export » (un volet, offert dès qu'il y a une condition) et `ddict codes vides` (une action de la commande `codes` qui existait déjà), refusés selon le § 5.8.4 ; les scripts SPSS et R recalculent qui a reçu chaque question (`ddict_posee`, sur les valeurs telles qu'enregistrées : `VALUE()` en SPSS, les valeurs brutes en R), s'en servent pour la complétude et les conditions d'exclusion, écrivent les codes, les déclarent manquants et les étiquettent ; le codebook dit les codes quand ils sont choisis. **Quatre précisions.** (1) **Une réponse donnée sous une condition fausse est traitée comme non posée en aval** (complétude, Tableau 1, Méthode) : le Tableau 1 la laisse hors du tableau et la note la compte ; la valeur reste dans la base et dans les analyses, et le rapport de conformité la signale. (2) Une option à cocher ne reçoit jamais le code du manquant : une case vide y veut dire « non cochée ». (3) Les scripts n'écrivent rien de nouveau tant que ni règle ni code ne s'en sert : un projet sans condition donne les mêmes fichiers. (4) **Pas encore fait** : l'information sur la page « Plan » pour une hypothèse qui croise une variable filtrée. Vérifié dans PSPP et dans R : mêmes exclusions et mêmes nombres de cellules codées que l'outil. Tests : `tests/test_filtres_downstream.py` (9) et `tests/test_filtres_scripts.py` (7).

**Fait en 10** (items de contrôle) : la règle `attention` compte les échecs de chaque personne (posé et répondu autrement que juste ; laissé vide, si la règle le dit un échec ; un item non posé n'est jamais un échec) et exclut à partir de `min_failed` ; refusée pour une variable inconnue, un identifiant ou un texte libre, une bonne réponse qui n'est pas un code de la variable, plus d'échecs exigés que d'items, ou sans le sort du vide. Le signal de la page « Méthode » et de `ddict exclusions signaux`, parmi les personnes gardées, sur les items que le questionnaire marque : combien ont échoué à au moins un, à tous, combien en ont laissé un vide ; « En faire une règle » remplit le formulaire (la sorte « Items de contrôle » : les variables, leurs bonnes réponses, le nombre d'échecs, le sort du vide, sans choix d'office), rien n'est appliqué sans « Ajouter la règle ». `ddict exclusions ajouter --attention VARIABLE=CODE[,CODE…] … --echecs N --vide echec|ignore`. Les scripts SPSS et R comptent les échecs (`ddict_echecs`), puis `ddict_exclusion`. Le diagramme de flux, la phrase P2, le préenregistrement et l'empreinte la prennent comme toute règle ; P1b compte les items d'une règle quand le questionnaire n'en marque aucun. Un énoncé de contrôle n'est jamais membre du groupe de sa grille (étape 3) : un groupe ne se modifie pas à la main, la règle tient donc par construction. Fait aussi, reste de l'étape 9 : sur la page « Plan », une hypothèse qui croise une variable filtrée reçoit « posée seulement si … ; l'analyse portera sur les personnes à qui elle a été posée ». **Une précision** : le signal compte « au moins un » échec en ignorant le vide, et donne à part qui en a laissé un vide, pour que l'équipe choisisse le sort du vide en le voyant. Vérifié dans PSPP et dans R (deux règles, mêmes exclusions). Tests : `tests/test_attention.py` (20 : les quatre variantes du corrigé, le signal, chaque refus, la phrase, la ligne de commande, la page sans rien appliquer, PSPP, R, P1b sans questionnaire, la page « Plan »).

L'ordre suit la dépendance : le format (2) porte tout ; les fonctions (3) avant l'interface (4) ; le Word (5) n'attend pas LimeSurvey ; l'écriture LimeSurvey (6) vient tôt, parce que l'importation réelle de l'auteur prend du temps et que les étapes 7 à 10 avancent pendant ce temps.

## 8. Les données de test

Rien de réel. `scripts/generer_base_filtres.py`, graine fixe, écrit avec les fonctions de l'outil un **projet de conception fictif** (aucun instrument réel), son fichier LimeSurvey, une **base de 300 réponses fictives** au format de LimeSurvey 7.6 (`.sav`, CSV, Excel, les questions non posées laissées vides), et son **corrigé** (JSON).

Le questionnaire :

| Section | Questions | Ce qu'elle exerce |
|---|---|---|
| S1 Consentement | Q1 consentement (1 Oui, 2 Non), obligatoire | — |
| S2 Profil, **posée si Q1 = 1** | Q2 âge (nombre) ; Q3 « Avez-vous des enfants ? » (1 Oui, 2 Non, 9 Préfère ne pas répondre, déclaré manquant) ; Q4 « Combien d'enfants vivent avec vous ? » (nombre), **posée si Q3 = 1** ; Q5 « Occupez-vous un emploi ? » (1 Temps plein, 2 Temps partiel, 3 Non) ; Q6 moyens de transport (cases, avec « autre »), **choix en ordre aléatoire** | section filtrée ; filtre simple ; code manquant dans la question filtre |
| S3 Travail, **posée si Q5 ∈ {1, 2}** | Q7 grille fictive « Climat au travail », 6 énoncés de 1 à 5 **plus un énoncé de contrôle** (« Pour cet énoncé, choisissez Plutôt d'accord », bonne réponse 4), **énoncés en ordre aléatoire**, marquée instrument (cotation fictive) ; Q8 « Travaillez-vous de nuit ? », **posée si Q2 ≥ 18 et Q5 = 1** | section filtrée par `in` ; deux termes ; item de contrôle dans une grille aléatoire |
| S4 Bien-être | Q9 grille fictive de 8 énoncés, 2 inversés, **énoncés en ordre aléatoire** ; Q10 item de contrôle à choix unique (« Pour montrer que vous lisez, choisissez Jamais ») ; Q11 commentaires (texte long) | second item de contrôle |
| S5 Habitudes, **questions en ordre aléatoire** | trois questions à choix unique | ordre aléatoire d'une section |

Les cas plantés (à fixer dans le corrigé ; chiffres indicatifs) : 10 refus de consentement (tout S2 à S5 non applicable) ; parmi les autres, Q3 = Non pour environ 120 personnes, Q3 sans réponse pour 6 (Q4 non applicable par la règle du vide) et Q3 = 9 pour 4 (Q4 non applicable : 9 ≠ 1) ; 5 personnes à qui Q4 a été posée sans y répondre (manquant) ; **3 réponses à Q4 sous Q3 = Non** (anomalie, dite « < 5 ») et **7 réponses à Q7 sous Q5 = 3** (anomalie dite par son nombre) ; quelques moins de 18 ans parmi les Q5 = 1 (Q8 non posée) ; une complétude de Q7 qui n'exclut aucune des personnes qui ne travaillent pas, et 6 qui ont répondu à moins de 5 énoncés posés ; 12 échecs à l'énoncé de contrôle, 9 à Q10, 5 aux deux, 3 sans réponse à Q10 ; 8 passations trop courtes (dates de début et de fin). Le corrigé donne, par variable : posée, non applicable, manquant, anomalies ; les effectifs de chaque règle dans deux ordres ; les dénominateurs du Tableau 1 ; la durée estimée (chemin court et long) ; les phrases de la Méthode.

Les tests ordinaires utilisent ces fichiers ; les tests marqués `limesurvey` relisent les exports de l'auteur, hors du dépôt, en ne gardant que des comptes.

## 9. Le scénario manuel

Dans la fenêtre de l'icône, à la suite des étapes 102 :

| Étape | Geste | Attendu |
|---|---|---|
| 103 | Concevoir un questionnaire : une question « enfants » (Oui, Non), une question « nombre d'enfants » **posée si enfants = Oui** ; une section « Travail » **posée si emploi ∈ {Temps plein, Temps partiel}** ; une question à deux termes (âge ≥ 18 et emploi = Temps plein) | Chaque condition se lit en clair sous la question et sous la section |
| 104 | Une grille de 6 énoncés en **ordre aléatoire**, avec un **énoncé de contrôle** (bonne réponse « Plutôt d'accord ») ; une question de contrôle à choix unique | La grille ne compte que ses 6 énoncés dans son groupe |
| 105 | Page « Relecture » ; puis poser exprès une condition sur une question qui vient après, et une valeur retirée | La durée estimée en tête, avec sa formule ; les deux points, chacun avec son bouton |
| 106 | Page « Publier » : les deux Word | Filtres en clair, ordres aléatoires, durée dans le Word du comité ; condition, item de contrôle et formule dans le Word de travail |
| 107 | Écrire le fichier LimeSurvey, l'importer dans LimeSurvey Cloud, prévisualiser les deux branches | Les questions filtrées paraissent et disparaissent comme prévu ; l'ordre change d'une prévisualisation à l'autre |
| 108 | Changer une condition dans LimeSurvey, réexporter, comparer | La différence « condition changée » ; « Reprendre dans le projet » |
| 109 | Recevoir la base fictive (page « Base », « La base est arrivée ») ; ouvrir le rapport de conformité | Questions filtrées (posée, non applicable, manquant) ; réponses sous une condition fausse, « < 5 » pour la plus petite |
| 110 | Page « Méthode » : une règle de complétude sur la grille « Climat au travail » ; le signal des items de contrôle, « En faire une règle », choisir le sort des vides | La complétude n'exclut aucune personne sans emploi ; la règle d'attention ajoutée seulement après « Ajouter » |
| 111 | Tableau 1 avec le nombre d'enfants ; l'aperçu de la Méthode | « question posée à … personnes » dans la note et dans P4 ; A2b et A2c ; P1b ; I2b |
| 112 | Page « Export » : choisir −8 et −9 ; produire les fichiers de commandes ; ouvrir le script de préparation dans PSPP ou R | Les cellules non applicables à −8, les vides posés à −9, déclarés manquants et étiquetés ; un code refusé s'il est déjà un choix |
| 113 | Projet d'une base SurveyMonkey fictive : poser une condition à la main sur la page d'une variable | Le rapport et le Tableau 1 en tiennent compte comme pour un questionnaire conçu |

## 10. Risques

- **LimeSurvey interprète une expression autrement que l'outil** (le vide, le code « 0 », les nombres, `.NAOK`) : l'étape 6 est un arrêt, avec la liste du § 5.7.4 ; une forme qui coince est corrigée dans les deux sens (écriture et lecture), jamais devinée.
- **Les valeurs de l'ordre aléatoire dans le texte à colonnes** ne sont pas documentées : elles viennent du réexport de l'auteur. Si l'importation les ignore, l'ordre aléatoire se règle à la main dans LimeSurvey, et la page le dit.
- **Une condition changée en cours de collecte** donne des anomalies et des non applicables faux pour les réponses d'avant : le rapport de conformité le rappelle, et les versions marquées envoyées (D-150) aident à le voir ; le calcul selon la version de chaque réponse (par la date) est hors de cette version.
- **Une base SurveyMonkey ou un `.sav` existant** : une condition tapée à la main peut ne pas être celle que la plateforme appliquait ; les anomalies du rapport sont alors le premier signe, et c'est leur rôle.
- **La version est grande** (11 étapes) : si elle déborde, la durée estimée (§ 5.4) et les items de contrôle (étape 10) peuvent passer en 0.21.1, sans rien casser ; le non applicable, lui, est le cœur.
- **Les temps de réponse de la durée estimée** n'ont pas de source primaire : ils sont dits comme des repères, jamais comme une mesure, et le pilote (v0.26) les recalibrera.
- **L'empreinte** : un champ nouveau qui entrerait vide dans l'empreinte du questionnaire ferait croire à toutes les équipes qui ont marqué un envoi que leur questionnaire a changé ; le test de l'étape 2 le garde.

## 11. Hors de cette version

Conditions sur un énoncé ou une option d'une même question (`array_filter` de LimeSurvey : ne montrer dans Q8 que les options cochées en Q7) ; parenthèses et « ou » entre plusieurs « et » ; ordre aléatoire des sections et tirage d'un sous-ensemble ; quotas ; conditions selon la version de chaque réponse ; la relecture des filtres par l'IA (v0.24).

## 12. Décisions à prendre

| N° | Décision | Ma recommandation |
|---|---|---|
| D-163 | **Le niveau « résultats à publier »** | Texte de la feuille de route du cycle, § 13.1, après réponse à mes objections (§ 13.4). Consigné au journal à l'étape 1 ; la règle 3 du `CLAUDE.md` et le principe 5 reformulés **au début de la v0.27**, quand le code existe (comme D-143 l'a fait pour la règle 4). |
| D-164 | **La numérotation des versions** | Les versions sont numérotées dans l'ordre de leur publication, sans numéro réservé : 0.21 filtres, 0.22 puissance, 0.23 dossier d'étude, 0.24 sources (l'ancienne v0.21 : D-143, D-144 et D-147 s'y appliquent), puis 0.25 à 0.32 (feuille de route du cycle, § 3). |
| D-165 | **La forme de la condition** | Des termes (cible par identifiant, opérateur selon la nature de la cible, valeur choisie parmi les choix), reliés tous par « et » ou tous par « ou » ; la section et la question combinées par « et » ; un terme sur un vide ou une question non posée est faux ; ni parenthèses ni « ou » de « et » dans cette version (§ 5.1). |
| D-166 | **Ce que couvre l'ordre aléatoire** | Les questions d'une section, les énoncés d'une grille, les choix et les options d'une question ; pas les sections, ni les colonnes d'une grille, ni un tirage ; « Autre » à la fin ; aucun effet sur les noms, les codes ni les calculs (§ 5.2). |
| D-167 | **Le non applicable et ses codes** | Une nature calculée en mémoire à partir des conditions, sur la base telle qu'enregistrée, jamais gardée par personne ; distincte du manquant partout en aval ; anomalies en agrégats ; deux codes facultatifs pour tout le projet, choisis par l'équipe sans valeur proposée, écrits dans les scripts de préparation et le fichier de commandes, jamais dans la copie documentée (§ 5.8). |
| D-168 | **Les conditions déclarées à la main** | Sur la page de la variable, sur des variables, avec leur origine (`team`, `designed`, `lss`) ; même calcul ensuite ; refus d'une valeur de texte libre ou d'identifiant (§ 5.8.7). |
| D-169 | **La lecture des conditions d'un `.lss`** | Une grammaire fermée, exactement les formes que l'outil écrit ; toute autre expression refusée et listée, la question lue sans condition avec un point à vérifier ; le tableau `conditions` non lu (§ 5.7.2). |
| D-170 | **L'item de contrôle** | Marqué sur une question à choix unique ou un énoncé de grille, avec ses bonnes réponses ; hors des membres de son groupe ; une sorte de règle nouvelle, `attention` (échecs à compter, sort du vide choisi par l'équipe sans valeur par défaut), proposée sur la page « Méthode », jamais appliquée seule (§ 5.3). |
| D-171 | **La durée estimée** | Mots lus ÷ vitesse de lecture sourcée (IReST, Trauzettel-Klosinski et Dietz, 2012 : 195 et 228 mots par minute, à voix haute, vérifié à l'étape 1) + temps de réponse par sorte de réponse (3 s, 10 s, 60 s), dits comme des repères de l'outil ; une fourchette du chemin le plus court au plus long ; montrée, jamais reprise dans un seuil (§ 5.4). Autres choix possibles : la lecture seule (sourcée, mais sous-estime) ; des temps de réponse tapés par l'équipe avec leur source. |
| D-172 | **Le format 0.12.0 et l'empreinte** | Champs facultatifs du § 5.9 ; un projet 0.11.0 identique ; les conditions, les codes et la règle `attention` dans l'empreinte du codebook seulement quand ils existent ; l'empreinte du questionnaire conçu n'y met un champ nouveau que rempli (§ 5.9). |
