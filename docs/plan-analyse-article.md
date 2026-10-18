# Le plan d'analyse et l'article : la fiche

> Statut : **validée par l'auteur le 2026-10-17** (v0.13, étape 1), avec les dix points du § 14 et leurs recommandations (Feldt, 1965, ajouté à la phrase I6), et deux gabarits de préenregistrement selon l'origine des données (D-109). Plan : [`plan-v0.13.md`](plan-v0.13.md) ; décisions D-101 à D-109 (D-109 remplace D-105). Chiffres : la base fictive des analyses (`etude-analyses.sav`, v0.9) et son corrigé. Les statistiques citées viennent du corrigé ; les *p* et les intervalles ont été calculés à partir de ses valeurs exactes, et seront fixés par les tests de l'étape 3.

Ce document fixe le format du plan, les effets testés et les sens attendus de chaque analyse, le gel et les amendements, le rapprochement du carnet et du plan, la correction pour comparaisons multiples, le préenregistrement et chaque phrase nouvelle de l'article, en français et en anglais. Le code des étapes 2 à 6 le suivra.

## 1. La base fictive et le plan d'exemple

Aucune nouvelle base : celle des analyses (300 personnes, effets plantés, D-075) se prête à un plan. Le plan d'exemple :

| Hypothèse | Énoncé | Analyse | Effet testé | Sens attendu | Caractère | Famille |
|---|---|---|---|---|---|---|
| H1 | Le bien-être au travail est plus élevé dans le groupe d'intervention que dans le groupe contrôle. | Test *t* de Welch : `bienetre_total` (score de G1) selon `groupe` | la différence | Intervention plus élevé → test unilatéral | confirmatoire | F1 |
| H2 | Plus les heures de travail sont nombreuses, plus le stress est élevé. | Corrélation de Pearson : `heures_travail`, `stress` | la paire | positif (rappelé) | confirmatoire | F1 |
| H3 | Le stress diffère selon le niveau d'études. | ANOVA : `stress` selon `niveau_etudes` | l'effet du groupe | — | confirmatoire | F1 |
| H4 | Le soutien des collègues prédit la satisfaction au travail, à charge de travail égale. | Régression : `satisfaction` par `soutien` et `charge` | le prédicteur `soutien` | positif (rappelé) | confirmatoire | — |
| H5 | L'âge est lié au stress. | Corrélation de Pearson : `age`, `stress` | la paire | — | exploratoire | — |

Le carnet d'exemple contient aussi un Tableau 1 (non lié au plan) et, pour les cas plantés du rapprochement (§ 6), une corrélation de Spearman entre `heures_travail` et `stress`, ajoutée sans hypothèse.

**Valeurs attendues** (corrigé) :

| | Statistique | *p* brut | *p* corrigé (Holm, F1) |
|---|---|---|---|
| H1 | *t*(297,29) = 5,00, *d* = 0,58 | < ,001 (unilatéral) | < ,001 |
| H2 | *r*(294) = ,42, IC 95 % [,32 ; ,51] | < ,001 | < ,001 |
| H3 | *F*(2, 293) = 34,88, η² = ,19 | < ,001 | < ,001 |
| H4 | *b* = 0,51 | à fixer | non corrigé (pas de famille) |
| H5 | *r*(289) = ,05, IC 95 % [−,06 ; ,17] | ,382 | non corrigé (exploratoire) |

Sur cette base, les effets plantés sont forts : la correction ne change aucun *p* affiché. Les tests de l'étape 3 ajoutent donc des familles de *p* choisis (§ 7), où elle change tout.

## 2. Le format du plan (D-101)

Dans le projet, format 0.5.0. Un projet 0.4.0 s'ouvre tel quel, avec un plan vide.

```json
"plan": {
  "alpha": 0.05,
  "correction": "holm",
  "missing": "listwise_by_analysis",
  "sample_size": "Toutes les réponses de la base, sans calcul de puissance préalable.",
  "data_origin": "primary",
  "data_status": "before_analysis",
  "next_id": 6,
  "hypotheses": [
    {"id": "H1",
     "statement": "Le bien-être au travail est plus élevé dans le groupe d'intervention que dans le groupe contrôle.",
     "analysis": "t_test",
     "roles": {"outcome": [{"score": "G1"}], "group": [{"variable": "groupe"}]},
     "options": {"method": "welch", "alternative": "greater"},
     "effect": {"kind": "difference"},
     "direction": "first_higher",
     "kind": "confirmatory",
     "family": "F1"},
    {"id": "H2", "statement": "…", "analysis": "correlation",
     "roles": {"variables": [{"variable": "heures_travail"}, {"variable": "stress"}]},
     "options": {"method": "pearson"},
     "effect": {"kind": "pair", "variables": [{"variable": "heures_travail"}, {"variable": "stress"}]},
     "direction": "positive", "kind": "confirmatory", "family": "F1"},
    {"id": "H4", "statement": "…", "analysis": "regression",
     "roles": {"outcome": [{"variable": "satisfaction"}], "predictors": [{"variable": "soutien"}, {"variable": "charge"}]},
     "options": {},
     "effect": {"kind": "predictor", "variable": {"variable": "soutien"}},
     "direction": "positive", "kind": "confirmatory", "family": null}
  ],
  "frozen": null,
  "amendments": []
}
```

- **Les variables** sont des `VariableRef`, les mêmes que celles du carnet : `{"variable": …}` (nom d'origine), `{"score": …}` (score d'un groupe), `{"reversed": …}` (item inversé). Elles survivent à un renommage.
- **`alpha`** : un nombre strictement entre 0 et 1, tapé par l'équipe ; `null` tant qu'il ne l'est pas. La page propose « 0,05 » dans le champ, sans l'enregistrer.
- **`correction`** : `none`, `holm` (par défaut) ou `bonferroni`. Elle ne s'applique qu'aux familles (§ 7).
- **`missing`** : une seule valeur aujourd'hui, `listwise_by_analysis`. Le champ existe pour qu'une autre méthode s'ajoute sans changer le format.
- **`sample_size`** : un texte libre de l'équipe, 2 000 caractères au plus ; vide permis (il deviendra un trou).
- **`data_origin`** et **`data_status`** : l'origine et l'état des données quand le plan a été écrit, déclarés par l'équipe (§ 8.1) ; `null` tant qu'ils ne le sont pas.
- **`statement`** : 1 000 caractères au plus, non vide.
- **`family`** : un nom court (`F1`, `Principal`…), ou `null`.
- **Identifiants** `H<n>` jamais redonnés, comme les règles d'exclusion. L'ordre de la liste est l'ordre des hypothèses dans l'article ; le changer n'est pas une décision du plan (ni dans son empreinte, ni un amendement après le gel).
- **L'empreinte du plan** : SHA-256 du JSON canonique de `alpha`, `correction`, `missing`, `sample_size`, `data_origin`, `data_status` et `hypotheses`, ces dernières dans l'ordre de leurs identifiants, en hexadécimal comme l'empreinte du codebook. Ni `frozen` ni `amendments` n'y entrent.

**Refus, avec leur raison** (étape 2) :

| Cas | Raison affichée |
|---|---|
| Analyse inconnue, ou Tableau 1 | « Le Tableau 1 décrit l'échantillon ; il ne teste aucune hypothèse. » |
| Rôle mal rempli, variable inconnue, niveau qui ne convient pas, modalités | les raisons des conditions du codebook (D-074), telles quelles |
| Effet testé qui n'existe pas pour l'analyse | « Une ANOVA teste l'effet du groupe ; elle n'a pas de paire. » |
| Paire ou prédicteur qui ne sont pas parmi les variables de l'analyse | « soutien n'est pas un prédicteur de cette régression. » |
| Prédicteur nominal de plus de deux modalités | « Un prédicteur nominal de 3 modalités a 2 coefficients ; une hypothèse ne porte que sur un seul. Testez le modèle, ou choisissez une variable de 2 modalités. » |
| Sens attendu que l'analyse ne permet pas | « Une ANOVA ne teste pas de sens ; laissez le sens attendu vide. » |
| Sens attendu contraire à l'option `alternative` choisie | « Le sens attendu (Contrôle plus élevé) contredit le test unilatéral choisi. » |
| Énoncé vide ou trop long | « Écrivez l'hypothèse (1 000 caractères au plus). » |

Les conditions qui dépendent des données (nombre de modalités observées, au moins 2 personnes par groupe) sont vérifiées sur la base quand elle est là ; sans base, l'hypothèse est gardée avec l'avertissement « conditions à vérifier quand la base sera ouverte ».

## 3. Les effets testés (D-103)

Une hypothèse porte sur un seul *p*. L'effet testé dit lequel, et l'outil le retrouve dans les statistiques gardées par le carnet :

| Analyse et méthode | `effect.kind` | Statistiques de l'effet | *p* |
|---|---|---|---|
| Test *t* (Welch, Student) | `difference` | *t*, ddl, *d* et son IC, moyennes | `p` |
| Mann-Whitney | `difference` | *U*, corrélation bisériale des rangs, médianes | `p` |
| ANOVA | `group` | *F*, ddl, η², ω² | `p` |
| Kruskal-Wallis | `group` | *H*, ddl, ε² | `p` |
| Khi-carré | `association` | χ², ddl, *V* | `p` |
| Fisher | `association` | *V* | `fisher_p` |
| Corrélation | `pair` | *r* ou ρ, IC (Pearson), *n* de la paire | `p_j_i` de la paire |
| Régression | `model` | *R*², *F*, ddl | `Fp` |
| Régression | `predictor` | *b*, son IC, β, *t*, ddl résiduels | `p_i` du coefficient |

- **Une paire** se désigne par ses deux variables, jamais par sa position : changer l'ordre des variables d'une corrélation ne change pas la paire testée. Une corrélation de deux variables a une seule paire, choisie d'office.
- **Un prédicteur** se désigne par sa variable ; l'outil retrouve son coefficient au calcul. Un prédicteur nominal de 2 modalités a un seul coefficient (la seconde modalité contre la première) : il est permis.
- **Les comparaisons de Tukey** ne portent pas d'hypothèse dans cette version : l'effet testé d'une ANOVA est l'effet global.

**Une phrase d'effet**, pour la Discussion et pour les Résultats d'une hypothèse, là où la phrase de l'analyse ne dit pas l'effet testé :

| Effet | Phrase (français) | Phrase (anglais) |
|---|---|---|
| Paire d'une corrélation de plusieurs variables | La corrélation entre {a} et {b} était *r*({ddl}) = {r}, IC 95 % [{bas} ; {haut}], {p}. | The correlation between {a} and {b} was *r*({df}) = {r}, 95% CI [{low}, {high}], {p}. |
| Prédicteur d'une régression | {x} : *b* = {b}, IC 95 % [{bas} ; {haut}], β = {β}, *t*({ddl}) = {t}, {p}. | {x}: *b* = {b}, 95% CI [{low}, {high}], β = {β}, *t*({df}) = {t}, {p}. |

Ailleurs, la phrase de l'analyse (v0.9) dit déjà l'effet testé et sert telle quelle. La paire de Spearman suit la phrase de Spearman existante.

## 4. Le sens attendu (D-103)

| Analyse | `direction` permis | Effet sur le calcul |
|---|---|---|
| Test *t*, Mann-Whitney | `first_higher`, `second_higher` (les deux modalités dans l'ordre de leurs codes, ou celles choisies par `levels`) | règle `alternative` : `greater` ou `less` ; le test devient unilatéral |
| Corrélation (paire) | `positive`, `negative` | aucun : le test reste bilatéral |
| Régression (prédicteur) | `positive`, `negative` | aucun : le test reste bilatéral |
| ANOVA, Kruskal-Wallis, khi-carré, Fisher, modèle d'une régression | aucun | — |

Choisir un sens pour un test *t* écrit l'option `alternative` ; choisir ensuite une option contraire est refusé (§ 2). Laisser le sens vide garde le test bilatéral, sauf si l'équipe a choisi `alternative` elle-même. Une équipe qui attend un sens mais veut un test bilatéral le choisit elle-même (`alternative` à `two_sided`) : le sens n'est alors que rappelé.

**Le sens observé**, écrit par l'outil dans la Discussion, est un fait tiré du signe de la statistique :

| Effet | Sens observé (français) | (anglais) |
|---|---|---|
| Test *t* | La moyenne observée était plus élevée dans le groupe {a}. | The observed mean was higher in the {a} group. |
| Mann-Whitney | Les rangs observés étaient plus élevés dans le groupe {a}. | The observed ranks were higher in the {a} group. |
| Paire | La corrélation observée était positive. / négative. | The observed correlation was positive. / negative. |
| Prédicteur | Le coefficient observé de {x} était positif. / négatif. | The observed coefficient of {x} was positive. / negative. |

Une statistique exactement nulle donne « était nulle » ; deux moyennes égales, « La moyenne observée était la même dans les deux groupes. » Le sens observé n'est écrit que quand un sens était attendu.

## 5. Le gel et les amendements (D-102)

**Figer le plan** :

1. exige la base ouverte : chaque hypothèse devient une analyse du carnet, et une entrée n'existe qu'avec son calcul (« Ouvrez la base pour figer le plan : chaque hypothèse devient une analyse du carnet. ») ;
2. vérifie chaque hypothèse sur la base (§ 2) ; une seule refusée bloque le gel, avec sa raison ;
3. exige `alpha`, `data_origin` et `data_status` ;
4. écrit `"frozen": {"date": "2026-10-20", "fingerprint": "3f9c…", "prior": [...]}` ;
5. lie chaque hypothèse à une entrée du carnet (§ 6).

`prior` liste les hypothèses dont l'analyse figurait déjà dans le carnet le jour du gel, avec l'identifiant et la date d'ajout de l'entrée : `{"hypothesis": "H2", "entry": "A3", "added": "2026-10-18"}`. L'outil ne sait rien des analyses faites sur la page « Analyses » sans les ajouter au carnet (D-078), ni de celles faites ailleurs : c'est pourquoi la connaissance préalable des données reste un trou du préenregistrement (§ 8).

**Après le gel**, le plan reste modifiable, mais :

- modifier une hypothèse (énoncé, variables, options, effet, sens, caractère, famille), en ajouter une, en retirer une ou changer une règle générale **exige une raison** ;
- chaque modification ajoute un amendement : `{"date": …, "target": "H2" | "rules", "change": "modified" | "added" | "removed", "reason": "…", "before": {…}, "after": {…}}`, où `before` et `after` ne gardent que les champs changés ;
- les amendements ne sont jamais retirés ni modifiés ;
- l'empreinte du plan est recalculée ; `frozen.fingerprint` garde celle du gel.

**Défaire le gel** n'existe pas : un plan figé le reste. Une équipe qui veut repartir à zéro retire le plan entier (avec confirmation), ce qui retire aussi le gel et les amendements, et le dit dans l'historique du projet.

## 6. Le rapprochement du carnet et du plan

Le carnet passe en `carnet_version` 1.2.0 : une entrée peut porter `"hypothesis": "H1"` et, une fois remplacée, `"superseded": {"date": …, "hypothesis": "H2", "change": "modified" | "removed"}`. Un carnet 1.1.0 s'ouvre tel quel. Les variables par rôle se comparent sans tenir compte de leur ordre.

**Une analyse prévue ne se retire pas du carnet** : « A5 est une analyse prévue par le plan : elle ne se retire pas du carnet. Ne la retenez plus, ou modifiez le plan. » L'outil ne perd ainsi jamais la trace de ce qui était prévu.

**Au gel**, pour chaque hypothèse :

- une entrée du carnet de même analyse, mêmes variables par rôle et mêmes options existe déjà → elle est liée (et notée dans `prior`) ;
- sinon, une entrée est ajoutée à la fin du carnet, liée, retenue.

**À un amendement** qui change l'analyse, les variables ou les options d'une hypothèse : l'entrée liée est déliée et n'est plus retenue ; l'hypothèse est liée à une entrée non liée qui calcule déjà exactement ce qu'elle prévoit (une variante, par exemple), sinon à une nouvelle entrée, calculée. L'ancienne reste dans le carnet, avec l'état « remplacée par l'amendement du {date} (H2) ». Une hypothèse retirée par un amendement délie la sienne : « H5 retirée du plan le {date} ». Sans la base, une hypothèse nouvelle attend : « H6 : l'analyse prévue sera calculée quand la base sera ouverte. »

**L'état de chaque entrée**, montré sur la page « Carnet » et par `ddict carnet lister` :

| État | Quand | Dans l'article |
|---|---|---|
| **prévue (H1)** | liée à une hypothèse confirmatoire | Résultats, sous H1 |
| **prévue, exploratoire (H5)** | liée à une hypothèse exploratoire | Résultats, analyses exploratoires |
| **remplacée** | déliée par un amendement | absente |
| **variante de H2** | non liée, même analyse et mêmes variables qu'une hypothèse, mais autres options (ou autre méthode) | Résultats, analyses exploratoires, avec « variante de H2 : corrélation de Spearman au lieu de Pearson » |
| **exploratoire** | non liée, ni variante | Résultats, analyses exploratoires |
| **descriptive** | Tableau 1 | Résultats, en premier |

**Les écarts au plan**, montrés sur la page « Plan » et dits dans l'article :

| Écart | Exemple de texte |
|---|---|
| L'entrée liée n'est plus retenue | « H2 : l'analyse prévue n'est pas retenue dans le carnet. » |
| Aucune entrée liée (la base n'était pas ouverte) | « H6 : l'analyse prévue n'est pas dans le carnet. » |
| L'entrée liée est impossible (variable retirée, niveau changé…) | « H2 : l'analyse prévue ne peut plus être faite : {raison}. » |

Dans l'article, un écart devient un trou : « [à compléter : raison de l'écart au plan pour H2] ». Sans gel, il n'y a ni lien, ni état, ni écart : toutes les entrées gardent leur comportement de la v0.12.

**Cas plantés** (étape 3), sur la base des analyses : une entrée déjà présente au gel (liée, dans `prior`) ; une variante de Spearman (H2) ; une entrée liée qu'on ne retient plus (et qu'on ne peut pas retirer) ; une variable de H4 retirée du codebook (impossible) ; un amendement qui change la méthode de H2 (ancienne entrée remplacée, nouvelle liée).

## 7. La correction pour comparaisons multiples (D-104)

- **Une famille** est l'ensemble des hypothèses **confirmatoires** qui portent le même nom de famille. Une hypothèse exploratoire ne peut pas avoir de famille (refus : « Une hypothèse exploratoire n'est pas corrigée ; retirez sa famille. »).
- **On corrige** les *p* des hypothèses de la famille dont l'entrée liée est retenue et calculable. Une hypothèse écartée (non retenue, impossible) sort de la famille, et la Méthode le dit : « La famille F1 comptait 3 hypothèses ; 2 ont pu être testées. »
- **Holm** : les *m* *p* triés en ordre croissant, *p*₍ᵢ₎ corrigé = max sur *j* ≤ *i* de min(1, (*m* − *j* + 1) · *p*₍ⱼ₎). **Bonferroni** : min(1, *m* · *p*). Ce sont les définitions de `p.adjust` de R ; les tests comparent à R à 10⁻¹² près, dont les égalités de *p* et les *p* qui atteignent 1.
- **Exemple illustratif** (trois *p* choisis) : 0,010, 0,020, 0,030 donnent, avec Holm, 0,030, 0,040, 0,040 ; avec Bonferroni, 0,030, 0,060, 0,090.
- **Gardé et confirmé** : le *p* corrigé de chaque entrée liée s'ajoute à ses statistiques (`p_adj`, et `adj_m`, le nombre de *p* corrigés ensemble), comparé comme les autres (D-089). Un *p* corrigé qui apparaît est gardé aussitôt, comme un agrégat seulement nouveau ; un *p* corrigé qui change ou disparaît attend une confirmation, même quand le codebook n'a pas changé (un amendement a changé la correction ou une famille). Ajouter, retirer ou écarter une hypothèse d'une famille change ainsi les *p* corrigés des autres, qui attendent leur confirmation.
- **Dans la phrase** de l'effet testé, juste après le *p* brut : « …, *p* = ,020, *p* corrigé (Holm) = ,040, … » ; en anglais, « …, *p* = .020, Holm-adjusted *p* = .040, … ». Même convention que *p* : trois décimales, sans zéro initial, « < ,001 » en deçà.
- **Dans le tableau** de l'analyse, une colonne « *p* corrigé (Holm) » à droite de *p*, sur la ligne de l'effet testé seulement ; tirets ailleurs. Une note du tableau : « *p* corrigé par la méthode de Holm dans la famille F1 (3 hypothèses). »

## 8. Le préenregistrement (D-109, qui remplace D-105)

### 8.1 Ce que l'équipe déclare : l'origine et l'état des données

Deux champs du plan, déclarés par l'équipe et exigés pour figer le plan. L'outil ne peut vérifier ni l'un ni l'autre : il les écrit toujours comme une déclaration de l'équipe.

- **`data_origin`** : `primary` (données recueillies par l'équipe pour cette étude) ou `secondary` (données existantes, recueillies par d'autres ou pour un autre projet).
- **`data_status`**, l'état des données quand le plan a été écrit, selon les cinq réponses du gabarit OSF Prereg :

| Valeur | Libellé (français) | Libellé d'origine (OSF Prereg) |
|---|---|---|
| `before_creation` | Avant la création des données : elles n'avaient pas encore été recueillies. | Registration prior to creation of data |
| `before_observation` | Avant toute observation : les données existaient, mais personne ne les avait encore observées. | Registration prior to any human observation of the data |
| `before_access` | Avant l'accès : les données existaient, mais ni l'équipe ni ses collaborateurs n'y avaient accédé. | Registration prior to accessing the data |
| `before_analysis` | Avant l'analyse : l'équipe avait accédé aux données, sans faire d'analyse liée au plan. | Registration prior to analysis of the data |
| `after_analysis` | Après une analyse : l'équipe avait déjà analysé une partie des données (statistiques descriptives, analyses préliminaires…). | Registration following analysis of the data |

L'outil travaille toujours sur une base déjà ouverte : un plan déclaré `before_creation` a donc été écrit ailleurs, avant, puis saisi dans l'outil. La Méthode distingue les deux moments : celui que l'équipe déclare et la date du gel dans l'outil (§ 10). Partir d'un export d'essai, puis brancher la vraie base, est reporté (D-109).

### 8.2 Deux gabarits, choisis par l'origine des données

| Origine | Gabarit | Référence | Licence |
|---|---|---|---|
| Primaires | **OSF Prereg** (§ 8.4) | Bowman, S., DeHaven, A. C., Errington, T. M., Hardwicke, T. E., Mellor, D. T., Nosek, B. A., & Soderberg, C. K. (2020). *OSF Prereg Template*. MetaArXiv. https://doi.org/10.31222/osf.io/epgjd | **CC0 1.0** (domaine public), vérifiée le 2026-10-17 dans les métadonnées de l'OSF |
| Secondaires | **Analyse de données secondaires** (§ 8.5) | van den Akker, O. R., Weston, S. J., Campbell, L., Chopik, W. J., Damian, R. I., Davis-Kean, P. E., Hall, A. N., Kosie, J. E., Kruse, E., Olsen, J., Ritchie, S. J., Valentine, K. D., van ’t Veer, A. E., & Bakker, M. (2021). Preregistration of secondary data analysis: A template and tutorial. *Meta-Psychology*, *5*. https://doi.org/10.15626/MP.2020.2625 | **CC BY 4.0**, vérifiée le 2026-10-17 sur la page de la revue et dans l'article |

Les deux licences permettent de reprendre et de traduire les questions ; CC BY exige de citer la source et de dire qu'elles ont été adaptées. Par cohérence, les deux documents portent en tête la même mention : « Questions adaptées de {référence courte}, sous licence {licence} ; traduction et réponses préremplies par dictionnaire-donnees {version}. » Les deux sont notés dans `docs/dependances.md` (contenus tiers). Les questions sont traduites en français par nous ; l'anglais garde le texte d'origine, abrégé.

### 8.3 Règles communes

- **Aucun effectif ni résultat** : ni *N*, ni effectif par règle, ni alpha observé, ni statistique. Un test vérifie que le document ne contient aucun nombre qui ne vienne du plan ou du codebook.
- **Le mot « préenregistrement »** n'apparaît que dans le titre du gabarit ; l'outil n'écrit nulle part que l'étude a été préenregistrée.
- **Sans gel**, le document s'écrit quand même, avec en tête : « [à compléter : ce plan n'est pas encore arrêté dans l'outil] ».
- **Fichiers** : `<projet>-preenregistrement.docx` et `.md`, remplacés à chaque export. Les trous sont surlignés dans Word, écrits `[à compléter : …]` dans le Markdown.
- **Les réponses préremplies communes**, reprises par les deux gabarits :
  - *Hypothèses* : pour chaque hypothèse, son identifiant, son énoncé, son caractère, son sens attendu et son effet testé (plan).
  - *Variables mesurées* : les variables des hypothèses, par rôle (issue, prédicteur, groupe…), avec leur libellé (plan, codebook).
  - *Scores* : pour chaque score des hypothèses, l'instrument, sa source, ses items, sa cotation, ses items inversés (phrases I1 à I5 de la v0.12, sans l'alpha).
  - *Exclusions* : les règles d'exclusion, dans leur ordre, avec leur raison et leur condition en clair, **sans effectif**.
  - *Manquants* : les codes manquants des variables des hypothèses (et des items de leurs scores), au futur : « Les codes {codes} seront traités comme des valeurs manquantes. » ; la phrase A2 au futur : « Les valeurs manquantes seront retirées analyse par analyse : chaque analyse portera sur les personnes qui ont répondu à toutes ses variables. » ; un trou pour ce que l'équipe sait des taux de manquants.
  - *Modèles* : pour chaque hypothèse, sans temps de verbe (les phrases A3 de la v0.12 sont au passé), l'analyse et ses options avec les libellés du catalogue, les variables par rôle, l'effet testé, uni- ou bilatéral : « H1. Test t : comparer deux groupes ; méthode : Welch (variances inégales permises) ; variable dépendante : bienetre_total ; variable de groupe : groupe ; effet testé : la différence entre les deux groupes ; test unilatéral, le premier groupe plus élevé. »
  - *Sens attendu* : il nomme les groupes quand l'outil les connaît (les modalités choisies, ou les deux étiquettes de valeurs de la variable de groupe) : « Intervention plus élevé que Contrôle » ; sinon « le premier groupe, dans l'ordre des codes, plus élevé ».
  - *Critères d'inférence* : « Le seuil α est fixé à {α}. Les valeurs de *p* seront {corrigées par la méthode de Holm dans chaque famille : F1 (H1, H2, H3) / pas corrigées pour comparaisons multiples}. Les tailles d'effet seront données avec leur intervalle de confiance à 95 %. »
  - *Exploratoire* : les hypothèses exploratoires du plan, puis « Toute autre analyse sera présentée comme exploratoire. »
  - *Analyses déjà faites* : s'il y en a, « Le carnet de l'outil contenait déjà, le jour où le plan a été arrêté, les analyses prévues pour {H2 (A3, ajoutée le 18 octobre 2026)}. » (`prior`), toujours suivie d'un trou pour ce que l'équipe a vu ailleurs.

### 8.4 Données primaires : OSF Prereg

| Partie | Question (abrégée) | Réponse préremplie |
|---|---|---|
| Informations sur l'étude | Titre | trou |
| | Auteurs | trou |
| | Description | trou |
| | Hypothèses | commune |
| Plan de l'étude | Type d'étude (expérience, observation, méta-analyse, autre) | trou (l'outil ne le sait pas) |
| | Insu | trou |
| | Devis | la structure de la base (D-064 : une ligne par personne, format large, vagues), puis un trou |
| | Répartition aléatoire | trou |
| Échantillonnage | Données existantes | le libellé de `data_status`, suivi de « (Déclaré par l'équipe.) » |
| | Explication sur les données existantes | analyses déjà faites (commune), puis un trou |
| | Procédure de collecte | le questionnaire documenté, s'il y en a un (D-012), puis un trou |
| | Taille d'échantillon | le texte `sample_size`, ou un trou |
| | Justification de la taille d'échantillon | trou (le calcul de puissance est reporté, D-108) |
| | Règle d'arrêt | trou |
| Variables | Variables manipulées | trou (l'outil ne sait pas si une variable a été manipulée) |
| | Variables mesurées | commune |
| | Indices | scores (commune) |
| Plan d'analyse | Modèles statistiques | commune |
| | Transformations | « Les scores sont calculés comme décrit sous « Indices ». » (sans répéter la description) ; un trou pour le reste |
| | Critères d'inférence | commune |
| | Exclusion de données | exclusions (commune) ; « Le plan ne prévoit aucun retrait de valeurs extrêmes. » |
| | Données manquantes | commune |
| | Analyses exploratoires | commune |
| Autre | Autre | trou |

### 8.5 Données secondaires : van den Akker et al. (2021)

| Q | Question (abrégée) | Réponse préremplie |
|---|---|---|
| 1 | Titre de l'étude | trou |
| 2 | Auteurs | trou |
| 3 | Questions de recherche | trou |
| 4 | Hypothèses | commune |
| 5 | Description des données | la structure de la base (D-064), le nombre de variables, puis un trou |
| 6 | Accès public aux données | trou |
| 7 | Comment obtenir les données | trou |
| 8 | Date de téléchargement ou d'accès | trou |
| 9 | Procédure de collecte | le questionnaire documenté, s'il y en a un, puis un trou |
| 10 | Codebook | « Le dictionnaire de données joint ({projet}.xlsx) décrit chaque variable. » |
| 11 | Variables manipulées | trou |
| 12 | Variables mesurées | variables mesurées et scores (communes) |
| 13 | Unités et critères d'inclusion et d'exclusion | exclusions (commune) ; puis le texte `sample_size` ou un trou |
| 14 | Données manquantes | commune |
| 15 | Valeurs extrêmes | « Le plan ne prévoit aucun retrait de valeurs extrêmes. » |
| 16 | Pondérations | « Aucune pondération n'est utilisée. » (l'outil n'en applique pas) |
| 17 | Travaux antérieurs sur ces données | trou |
| 18 | Connaissance préalable des données | le libellé de `data_status`, suivi de « (Déclaré par l'équipe.) » ; analyses déjà faites (commune) ; **toujours un trou** |
| 19 | Modèle statistique par hypothèse | commune |
| 20 | Taille d'effet prévue | trou |
| 21 | Puissance statistique | trou (D-108) |
| 22 | Critères d'inférence | commune |
| 23 | Violation des conditions | trou |
| 24 | Robustesse | trou |
| 25 | Analyses exploratoires | commune |
| Partie 6 | Déclaration d'intégrité | le texte du gabarit, tel quel (traduit), que l'équipe garde ou retire |

## 9. L'article (D-106)

**Le document** `<projet>-article.docx` (et `-article-graphiques.xlsx`, `-article-R.zip`), dans cet ordre :

| Partie | Niveau APA | Contenu |
|---|---|---|
| Page de titre | — | « [à compléter : titre] », « [à compléter : auteurs et affiliations] », puis un saut de page |
| Résumé | 1 | « [à compléter : résumé] », « Mots-clés : [à compléter : mots-clés] », puis un saut de page |
| *(titre de l'article)* | 1 | l'Introduction, sans intertitre « Introduction » (APA 7) |
| Méthode | 1 | Participants, Instruments, Analyses (v0.12), puis **Plan d'analyse** (nouveau, § 10) |
| Résultats | 1 | dans l'ordre du § 11 |
| Discussion | 1 | § 12 |
| Références | 1 | § 13, sur une nouvelle page |

La numérotation continue des tableaux et des figures (v0.12) vaut sur tout le document. La fin du document (empreinte, date, versions, analyses, règles d'exclusion) reçoit en plus l'empreinte du plan, la date du gel et la liste des amendements.

**L'Introduction** :

| # | Phrase (français) | Phrase (anglais) | Origine |
|---|---|---|---|
| N1 | [à compléter : contexte, revue des travaux et justification de l'étude] | [to be completed: background, literature review and rationale] | toujours |
| N2 | Les hypothèses suivantes ont été formulées : | The following hypotheses were formulated: | omise sans hypothèse confirmatoire |
| N3 | H1. {énoncé} (une ligne par hypothèse confirmatoire, dans l'ordre du plan) | H1. {statement} | plan |
| N4 | Les questions suivantes ont été examinées de façon exploratoire : / H5. {énoncé} | The following questions were examined in an exploratory way: / H5. {statement} | omise sans hypothèse exploratoire |

Sans plan figé, l'Introduction n'a que N1.

## 10. Le paragraphe « Plan d'analyse » de la Méthode

Seulement avec un plan figé.

| # | Phrase (français) | Phrase (anglais) | Origine |
|---|---|---|---|
| PL1 | Les données sont {primaires, recueillies par l'équipe pour cette étude / secondaires}. Selon l'équipe, le plan d'analyse a été écrit {avant la création des données / avant que quiconque ait observé les données / avant d'accéder aux données / après avoir accédé aux données, avant de les analyser / après une première analyse des données}. Il a été arrêté dans l'outil le {date}. [à compléter : lieu et identifiant du préenregistrement, s'il y en a un] | The data are {primary, collected by the team for this study / secondary}. According to the team, the analysis plan was written {before the data were created / before anyone observed the data / before accessing the data / after accessing the data, before analysing them / after a first analysis of the data}. It was finalised in the tool on {date}. [to be completed: registry and identifier of the preregistration, if any] | `data_origin`, `data_status`, `frozen.date` |
| PL2 | Il comptait {k} hypothèses confirmatoires et {e} exploratoires. | It included {k} confirmatory and {e} exploratory hypotheses. | plan (les nombres écrits en lettres jusqu'à neuf, règle APA) |
| PL3 | Le seuil α était fixé à {α}. | The α level was set at {α}. | plan |
| PL4 | Les valeurs de *p* ont été corrigées par la méthode de Holm (1979) au sein de chaque famille d'hypothèses : {F1 (H1, H2, H3)}. / … de Bonferroni … | *p* values were adjusted with the Holm (1979) method within each family of hypotheses: {F1 (H1, H2, H3)}. / … Bonferroni … | plan ; omise sans famille ou avec `none` |
| PL5 | Le test de H1 était unilatéral, dans le sens attendu. / Les tests de H1 et H3 étaient unilatéraux… | The test of H1 was one-sided, in the expected direction. / The tests of H1 and H3 were one-sided… | omise sans test unilatéral |
| PL6 | Le plan a été modifié {n} fois après avoir été arrêté : le {date}, pour {H2 ou les règles générales} ({résumé du changement}) : {raison} ; … | The plan was modified {n} times after being finalised: on {date}, for {H2 or the general rules} ({summary of the change}): {reason}; … | amendements ; omise sans amendement |
| PL7 | Le jour où le plan a été arrêté, le carnet d'analyses contenait déjà l'analyse prévue pour {H2}. | On the day the plan was finalised, the analysis notebook already contained the planned analysis for {H2}. | `prior` ; omise si vide |
| PL8 | Les autres analyses sont présentées comme exploratoires. | Other analyses are presented as exploratory. | omise s'il n'y a ni variante ni entrée exploratoire |

Le **résumé du changement** d'un amendement est écrit par l'outil à partir de `before` et `after`, champ par champ, séparés par des virgules : « méthode : Spearman au lieu de Pearson » (une option, par son libellé du catalogue), « prédicteurs : soutien au lieu de soutien, charge » (les variables d'un rôle), « énoncé reformulé », « confirmatoire au lieu de exploratoire », « famille : F2 au lieu de F1 », « effet testé modifié », « sens attendu modifié », « hypothèse ajoutée », « hypothèse retirée » ; pour les règles générales, « correction : Bonferroni au lieu de Holm », « seuil α : ,01 au lieu de ,05 », « taille d'échantillon reformulée ». La raison suit, telle que l'équipe l'a écrite, sa première lettre en minuscule.

**Exemple** (plan d'exemple figé, un amendement) :

> Les données sont primaires, recueillies par l'équipe pour cette étude. Selon l'équipe, le plan d'analyse a été écrit après avoir accédé aux données, avant de les analyser. Il a été arrêté dans l'outil le 20 octobre 2026. [à compléter : lieu et identifiant du préenregistrement, s'il y en a un] Il comptait quatre hypothèses confirmatoires et une exploratoire. Le seuil α était fixé à ,05. Les valeurs de *p* ont été corrigées par la méthode de Holm (1979) au sein de chaque famille d'hypothèses : F1 (H1, H2, H3). Le test de H1 était unilatéral, dans le sens attendu. Le plan a été modifié une fois après avoir été arrêté : le 2 novembre 2026, pour H2 (méthode : Spearman au lieu de Pearson) : distribution des heures de travail très asymétrique. Le jour où le plan a été arrêté, le carnet d'analyses contenait déjà l'analyse prévue pour H3. Les autres analyses sont présentées comme exploratoires.

α suit l'APA : sans zéro initial.

## 11. Les Résultats rangés par le plan

Avec un plan figé, dans cet ordre :

1. **Les entrées descriptives** (Tableau 1), dans l'ordre du carnet, sans intertitre propre (comme en v0.12).
2. **Une section par hypothèse confirmatoire**, dans l'ordre du plan, au niveau 2 : « H1 — {énoncé} ». Elle contient l'entrée liée (sa phrase, ses tableaux, ses figures). Quand la phrase de l'analyse ne dit pas l'effet testé (paire d'une corrélation de plusieurs variables, prédicteur), la phrase d'effet (§ 3) la suit. Une hypothèse sans entrée calculable garde son intertitre et reçoit le texte de son écart (§ 6) et son trou.
3. **« Analyses exploratoires »**, au niveau 2, si elle n'est pas vide : les hypothèses exploratoires du plan (au niveau 3, « H5 — {énoncé} »), puis les variantes et les autres entrées exploratoires, dans l'ordre du carnet, au niveau 3 avec leur intertitre de la v0.11. Une variante commence par « Variante de H2 : {différence}. »

Sans plan figé : l'ordre du carnet, comme en v0.12.

L'intertitre d'une entrée (« A2 — Test t : … ») disparaît sous une hypothèse : l'intertitre est celui de l'hypothèse. Les identifiants `A<n>` restent dans la fin du document, pour retrouver chaque analyse dans le script R.

## 12. La Discussion (D-107)

| # | Phrase (français) | Phrase (anglais) | Origine |
|---|---|---|---|
| D1 | [à compléter : rappel du but de l'étude] | [to be completed: reminder of the study's aim] | toujours |
| D2 | **H1.** {énoncé} | **H1.** {statement} | plan, une par hypothèse (confirmatoires, puis exploratoires) |
| D3 | Le sens attendu était : {groupe Intervention plus élevé / une corrélation positive / un coefficient positif}. {Sens observé, § 4}. | The expected direction was: {higher in the Intervention group / a positive correlation / a positive coefficient}. {Observed direction}. | plan, carnet ; omise sans sens attendu |
| D4 | {phrase de l'effet testé, avec *p* corrigé} | {effect sentence, with adjusted *p*} | carnet |
| D5 | [à compléter : interprétation de H1] | [to be completed: interpretation of H1] | toujours, après chaque hypothèse |
| D6 | [à compléter : interprétation des analyses exploratoires] | … | s'il y a des entrées exploratoires hors plan |
| D7 | [à compléter : limites] | [to be completed: limitations] | toujours |
| D8 | [à compléter : conclusion] | [to be completed: conclusion] | toujours |

- Une hypothèse dont l'analyse n'a pas pu être faite : D3 et D4 deviennent le texte de son écart.
- **Mots interdits**, cherchés par un test dans tout le document produit par l'outil (trous exclus), en français et en anglais : *soutenu·e*, *appuyé·e*, *confirmé·e*, *infirmé·e*, *rejeté·e*, *réfuté·e*, *significatif·ve*, *non significatif*, *tendance*, *marginal*, *prouve*, *démontre* ; *supported*, *confirmed*, *rejected*, *refuted*, *significant*, *trend*, *marginal*, *proves*, *demonstrates*. La liste vit dans le code des tests, et s'étend sans changer le format.
- Sans plan figé : D1, D7 et D8 seulement, avec « [à compléter : discussion des résultats] » entre D1 et D7.

**Exemple** (H1, H2 et H3 du plan d'exemple ; *d* et son intervalle tels que le corrigé les fixera) :

> [à compléter : rappel du but de l'étude]
>
> **H1.** Le bien-être au travail est plus élevé dans le groupe d'intervention que dans le groupe contrôle. Le sens attendu était : groupe Intervention plus élevé. La moyenne observée était plus élevée dans le groupe Intervention. Score de bien-être (score de G1) : *M* = 17,01 (*ÉT* = …) pour Intervention et *M* = 14,54 (*ÉT* = …) pour Contrôle, *t*(297,29) = 5,00, *p* < ,001, *p* corrigé (Holm) < ,001, *d* = 0,58, IC 95 % […]. [à compléter : interprétation de H1]
>
> **H2.** Plus les heures de travail sont nombreuses, plus le stress est élevé. Le sens attendu était : une corrélation positive. La corrélation observée était positive. La corrélation entre heures de travail par semaine et score de stress (0 à 40) était *r*(294) = ,42, IC 95 % [,32 ; ,51], *p* < ,001, *p* corrigé (Holm) < ,001. [à compléter : interprétation de H2]
>
> **H3.** Le stress diffère selon le niveau d'études. Score de stress (0 à 40) selon plus haut niveau d'études : *F*(2, 293) = 34,88, *p* < ,001, *p* corrigé (Holm) < ,001, η² = ,19, ω² = ,19 ; moyennes : … [à compléter : interprétation de H3]

## 13. Les Références

1. **« [à vérifier : les sources ci-dessous viennent du codebook, telles que l'équipe les a écrites ; certaines ne sont peut-être pas des références bibliographiques (une page du questionnaire, par exemple). Mettez-les au format APA et ajoutez les autres références.] »**, surligné.
2. Les sources du codebook, sans doublon, dans l'ordre alphabétique (sans tenir compte des accents ni de la casse), chacune telle quelle : sources des noms d'instruments, des cotations, des étendues théoriques et des seuils des variables dont parle l'article, et celle du questionnaire documenté.
3. **Les références fixes de l'outil**, seulement pour ce que le texte de l'outil cite :
   - Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, *6*(2), 65–70. (si PL4 nomme Holm)
   - Feldt, L. S. (1965). The approximate sampling distribution of Kuder-Richardson reliability coefficient twenty. *Psychometrika*, *30*(3), 357–370. https://doi.org/10.1007/BF02289499 (si I6 donne un intervalle ; I6 devient « … (IC 95 % selon Feldt, 1965, [,81 ; ,86] …) »)

Les logiciels (Python, SciPy, statsmodels, R) restent nommés avec leurs versions dans la phrase A5, sans référence ajoutée (point 9 du § 14).

## 14. Points à valider

1. **Le plan d'exemple** (§ 1) sur la base des analyses, sans nouvelle base ; la correction vérifiée sur des familles de *p* choisis, puisque les effets plantés sont trop forts pour qu'elle change un *p* affiché.
2. **Le format du plan** (§ 2) : un `alpha` tapé (la page propose 0,05 sans l'enregistrer), une seule méthode pour les manquants, la taille d'échantillon en texte.
3. **Une paire et un prédicteur désignés par leurs variables** (§ 3), et le refus d'un prédicteur nominal de plus de deux modalités.
4. **Le sens attendu** (§ 4) : unilatéral pour le test *t* et Mann-Whitney seulement ; rappelé ailleurs ; le sens observé écrit seulement quand un sens était attendu.
5. **Le gel sans retour** (§ 5) : un plan figé le reste ; on peut seulement retirer le plan entier. Toute modification après le gel exige une raison.
6. **Le lien au carnet au gel** (§ 6) : une entrée identique déjà présente est liée et notée dans `prior` ; un amendement remplace l'entrée liée plutôt que de la modifier ; les états « variante » et « exploratoire ».
7. **La correction** (§ 7) : une famille réservée aux hypothèses confirmatoires ; une hypothèse écartée sort de sa famille ; la colonne du *p* corrigé sur la seule ligne de l'effet testé.
8. **Le préenregistrement** (§ 8) : l'origine et l'état des données déclarés par l'équipe et exigés pour figer ; OSF Prereg pour des données primaires, van den Akker et al. pour des données secondaires, traduits par nous, avec la même mention d'origine en tête ; la connaissance préalable toujours en trou ; aucun nombre venu des données.
9. **Les références** (§ 13) : les sources du codebook recopiées sous un avertissement surligné ; les références fixes de Holm et de Feldt seulement quand le texte les cite ; pas de référence pour les logiciels. Recommandation : **ajouter Feldt (1965) à I6**, puisque l'intervalle en vient.
10. **L'article** (§ 9 à § 12) : la page de titre et le résumé en trous ; l'Introduction sans intertitre (APA 7) ; « Plan d'analyse » comme quatrième intertitre de la Méthode ; les Résultats par hypothèse, l'intertitre `A<n>` retiré sous une hypothèse ; la Discussion et ses mots interdits.
