# La section Méthode : la fiche

> Statut : **validé par l'auteur le 2026-10-16** (v0.12, étape 1), avec les huit points du § 9 et leurs recommandations (le tableau des effectifs du flux seulement dans Excel). Plan : [`plan-v0.12.md`](plan-v0.12.md) ; décisions D-093 à D-100. Chiffres : la base fictive de passation (`etude-passation.sav`), qui sera générée à l'étape 2. Les **effectifs** ci-dessous sont ceux que la base plantera ; les **statistiques** (moyennes, alpha) sont illustratives et seront fixées par son corrigé.

Ce document fixe le format des règles d'exclusion, les signaux de qualité, le diagramme de flux et chaque phrase des trois paragraphes de la Méthode, en français et en anglais. Le code des étapes 2 à 8 le suivra.

## 1. La base fictive de passation

400 réponses à un questionnaire fictif, dans un `.sav`, avec des noms lisibles :

| Variable | Contenu |
|---|---|
| `id_participant` | identifiant (exclu des analyses) |
| `courriel` | adresse fictive (`personne042@exemple.org`), sensible |
| `debut`, `fin` | date et heure de début et de fin de la passation |
| `consentement` | 1 = Oui, 2 = Non |
| `age` | âge en années ; 999 = non répondu (code déclaré) |
| `genre` | 1 = Femme, 2 = Homme, 3 = Autre |
| `anx1` à `anx6` | échelle d'anxiété fictive, 1 (Jamais) à 4 (Très souvent) ; `anx3` à inverser ; score = somme, au moins 5 items répondus sur 6, somme proportionnelle |
| `sat1` à `sat8` | grille de satisfaction, 1 (Pas du tout d'accord) à 5 (Tout à fait d'accord) |
| `stress` | score de stress, 0 à 40 |

**Les cas plantés**, dont certains cumulent deux raisons pour vérifier l'ordre :

| Cas | Nombre | Dont aussi |
|---|---|---|
| Refus de consentement (questionnaire vide ensuite) | 12 | 2 ont moins de 18 ans |
| Moins de 18 ans | 9 | 2 ont refusé (ci-dessus) |
| Moins de 5 items d'anxiété répondus | 14 | — |
| Passation de moins de 3 minutes | 10 | 3 répondent aussi en ligne droite |
| Grille de satisfaction en ligne droite | 8 | 3 trop rapides (ci-dessus) |
| Courriel en double (deuxième réponse) | 5 | — |

## 2. Les règles d'exclusion (D-093, D-094)

**Dans le projet** (format 0.4.0), une liste ordonnée :

```json
"exclusions": [
  {"id": "E1", "kind": "condition", "variable": "consentement", "operator": "eq", "value": 2,
   "reason": "Refus de consentement"},
  {"id": "E2", "kind": "condition", "variable": "age", "operator": "lt", "value": 18,
   "reason": "Moins de 18 ans"},
  {"id": "E3", "kind": "completeness", "group": "G1", "min_answered": 5,
   "reason": "Moins de 5 items d'anxiété répondus sur 6"},
  {"id": "E4", "kind": "duration", "start": "debut", "end": "fin", "min_seconds": 180,
   "reason": "Passation de moins de 3 minutes",
   "source": "Seuil fixé par l'équipe, procès-verbal du 2026-10-20"},
  {"id": "E5", "kind": "straightlining", "group": "G2", "reason": "Grille de satisfaction en ligne droite"},
  {"id": "E6", "kind": "duplicate", "variables": ["courriel"], "keep": "first",
   "reason": "Courriel en double"}
]
```

- **`id`** : `E1`, `E2`… ; comme les analyses du carnet, un numéro retiré ne revient pas. Le **rang** est l'ordre de la liste.
- **`condition`** : une variable par son nom d'origine (ou un score par son groupe : `{"score": "G1"}`), un opérateur (`eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, `missing`) et une valeur, sauf pour `missing`. Les codes manquants sont retirés avant : avec `age < 18`, le 999 d'un âge non répondu ne compte ni comme mineur ni comme majeur ; une valeur manquante ne remplit jamais une condition, sauf `missing`.
- **`completeness`** : un nombre minimal d'items répondus dans un groupe (plutôt qu'un pourcentage : « au moins 5 sur 6 » se lit mieux et ne s'arrondit pas).
- **`duration`** : deux variables de date (pour un export de plateforme, l'outil propose celles de début et de fin qu'il a reconnues), un seuil en secondes et sa **source**, obligatoire. Une durée manquante ou négative ne compte pas comme trop courte : elle est signalée à part.
- **`straightlining`** : toutes les réponses d'une grille identiques, seulement chez qui a répondu à tous ses items ; offert pour une grille d'au moins 4 items.
- **`duplicate`** : une ou plusieurs variables ; la première réponse dans l'ordre de la base est gardée, les suivantes sont exclues. C'est la seule règle qui peut porter sur un identifiant ou un courriel : elle compare les lignes entre elles et ne nomme jamais une valeur.
- **Refusé, avec sa raison** : une `condition` sur un identifiant ou un texte libre (« `id_participant = 123` nommerait une personne ; une exclusion décrit une règle, pas une liste ») ; une variable inconnue ; un seuil de durée sans source.

**Les effectifs**, dans l'ordre E1 à E6 :

| Étape | Raison | Exclues | Restantes |
|---|---|---|---|
| | Réponses reçues | | 400 |
| E1 | Refus de consentement | 12 | 388 |
| E2 | Moins de 18 ans | 7 | 381 |
| E3 | Moins de 5 items d'anxiété répondus sur 6 | 14 | 367 |
| E4 | Passation de moins de 3 minutes | 10 | 357 |
| E5 | Grille de satisfaction en ligne droite | 5 | 352 |
| E6 | Courriel en double | 5 | 347 |
| | **Échantillon analysé** | **53** | **347** |

Les deux mineurs qui ont refusé leur consentement sont comptés en E1, jamais deux fois. Mettre E5 avant E4 donne 8 en E5 et 7 en E4 : les effectifs par règle changent, jamais le *N* analysé (347).

**Dans les scripts.** Le script de préparation SPSS et R calcule `ddict_exclusion` (0 = gardée, sinon le numéro de la première règle, 1 pour E1…), en affiche les effectifs (`FREQUENCIES` ; `table()`), puis ne garde que les 0 (`SELECT IF (ddict_exclusion = 0).` ; `donnees <- donnees[donnees$ddict_exclusion == 0, ]`). Mêmes effectifs que l'outil : c'est le critère de l'étape 3.

## 3. Les signaux de qualité (D-095)

Sur la page « Méthode », une section **Qualité de passation**, qui ne retire personne :

- **Durée de passation** : la médiane et les 5ᵉ et 10ᵉ centiles des durées (des agrégats), un champ **Seuil (secondes)**, vide au départ, et, une fois rempli, « 10 personnes ont mis moins de 180 secondes ». Puis **Ajouter comme règle d'exclusion**, qui demande la source du seuil.
- **Réponses en ligne droite** : pour chaque grille d'au moins 4 items, « Grille de satisfaction (G2) : 8 personnes ont donné la même réponse aux 8 items ». **Ajouter comme règle**.
- **Doublons** : pour les variables proposées (identifiants, courriel, adresse IP, celles qu'une plateforme désigne), « Courriel : 5 réponses répètent une réponse précédente ». **Ajouter comme règle**.

Aucun signal n'a de seuil par défaut, et aucun ne s'applique sans être ajouté comme règle.

## 4. Le diagramme de flux (D-098)

Une figure APA, dessinée comme les autres (image dans Word, police du document), de haut en bas :

```
┌──────────────────────────────┐
│ Réponses reçues (N = 400)    │
└──────────────┬───────────────┘
               │──────▶ ┌─────────────────────────────────────────┐
               │        │ Exclues (n = 53)                        │
               │        │   Refus de consentement (n = 12)        │
               │        │   Moins de 18 ans (n = 7)               │
               │        │   Moins de 5 items d'anxiété … (n = 14) │
               │        │   Passation de moins de 3 minutes (n = 10) │
               │        │   Grille … en ligne droite (n = 5)      │
               │        │   Courriel en double (n = 5)            │
               │        └─────────────────────────────────────────┘
               ▼
┌──────────────────────────────┐
│ Échantillon analysé (N = 347)│
└──────────────────────────────┘
```

- **Une seule boîte d'exclusions**, les règles dans leur ordre : lisible jusqu'à une dizaine de règles, ce qui suffit à une étude transversale.
- *Titre* : « Flux des participants » ; *note* : « Les exclusions sont appliquées dans l'ordre ; une personne n'est comptée que par la première raison qui l'exclut. »
- **Le tableau de ses effectifs** (le tableau du § 2), dans le classeur Excel seulement (une feuille « Flux »), modifiable : dans Word, la figure suffit et ne consomme pas de numéro de tableau (§ 9, point 3).
- **Sans règle d'exclusion**, pas de diagramme : la phrase des Participants donne seulement le *N*.

## 5. Le paragraphe Participants

Chaque phrase, avec l'origine de ses champs. Les trous sont surlignés en jaune dans Word.

| # | Phrase (français) | Phrase (anglais) | Origine |
|---|---|---|---|
| P1 | Au total, {N} personnes ont répondu au questionnaire. | In total, {N} people answered the questionnaire. | lignes de la base |
| P2 | {n} ont été exclues, pour les raisons suivantes, dans cet ordre : {raison} (*n* = {n}) ; … (Figure {k}). | {n} were excluded, for the following reasons, in this order: {reason} (*n* = {n}); … (Figure {k}). | règles et leurs effectifs |
| P3 | L'échantillon analysé compte {N} personnes. | The analysed sample includes {N} people. | effectifs |
| P4 | Elles sont décrites par les variables suivantes : {libellé} (*M* = {M}, *ÉT* = {ÉT}) ; {libellé} ({modalité}, {p} % ; …). | They are described by the following variables: {label} (*M* = {M}, *SD* = {SD}); {label} ({category}, {p}%; …). | variables choisies sur la page « Méthode », calculées sur l'échantillon analysé |

- P2 est omise sans règle d'exclusion ; P4, sans variable choisie.
- Dans P4, un effectif plus petit que le *N* analysé est donné : « Âge (années) (*M* = 34,6, *ÉT* = 11,2, *n* = 341) ».
- Les pourcentages ont une décimale au plus, sans décimale s'ils sont entiers ; les catégories suivent l'ordre des codes.
- Ni minimum ni maximum : comme dans le carnet (D-088), aucune valeur observée isolée. L'équipe peut ajouter l'étendue dans Word.

**Exemple** (statistiques illustratives) :

> Au total, 400 personnes ont répondu au questionnaire. 53 ont été exclues, pour les raisons suivantes, dans cet ordre : refus de consentement (*n* = 12) ; moins de 18 ans (*n* = 7) ; moins de 5 items d'anxiété répondus sur 6 (*n* = 14) ; passation de moins de 3 minutes (*n* = 10) ; grille de satisfaction en ligne droite (*n* = 5) ; courriel en double (*n* = 5) (Figure 1). L'échantillon analysé compte 347 personnes. Elles sont décrites par les variables suivantes : âge (années) (*M* = 34,6, *ÉT* = 11,2, *n* = 341) ; genre (femme, 52,4 % ; homme, 45,5 % ; autre, 2,0 %).

Le libellé est celui du codebook, avec une minuscule initiale ; la raison, celle de la règle, avec une minuscule initiale. Le texte se retouche ensuite dans Word.

## 6. Le paragraphe Instruments

Un paragraphe par groupe qui a une cotation, dans l'ordre des groupes.

| # | Phrase (français) | Phrase (anglais) | Origine |
|---|---|---|---|
| I1 | L'instrument {instrument} ({source}) mesure {libellé du groupe} au moyen de {k} items, notés de {min} ({étiquette min}) à {max} ({étiquette max}). | The {instrument} ({source}) measures {group label} with {k} items, rated from {min} ({min label}) to {max} ({max label}). | nom et source de l'instrument ; libellé du groupe ; items et bornes de la cotation ; étiquettes de valeurs du premier item |
| I2 | Les items {liste} sont inversés avant le calcul du score. / L'item {item} est inversé avant le calcul du score. | Items {list} are reversed before the score is computed. / Item {item} is reversed before the score is computed. | items inversés confirmés |
| I3 | Le score ({nom}) est la {somme / moyenne} des items, de {min} à {max}. | The score ({name}) is the {sum / mean} of the items, from {min} to {max}. | cotation ; étendue calculée |
| I4 | Il est calculé quand au moins {m} items sur {k} sont répondus ; un item manquant est remplacé par la moyenne des items répondus de la personne. / … ; c'est alors la somme des items répondus. | It is computed when at least {m} of the {k} items are answered; a missing item is replaced by the mean of the person's answered items. / …; it is then the sum of the answered items. | nombre minimal et règle des items manquants (D-068) ; omise sans nombre minimal |
| I5 | La cotation suit {source de la cotation}. | Scoring follows {scoring source}. | source de la cotation ; omise si c'est la même que celle de l'instrument |
| I6 | Sur l'échantillon analysé, l'alpha de Cronbach est de {α} (IC 95 % [{bas} ; {haut}], *n* = {n}). | In the analysed sample, Cronbach's alpha is {α} (95% CI [{low}, {high}], *n* = {n}). | alpha et son IC de Feldt (D-096), sur qui a répondu à tous les items |

**Les trous** (D-097) :

| Manque | Trou |
|---|---|
| Nom ou source de l'instrument | I1 devient : « [à compléter : nom et source de l'instrument du groupe G1] mesure {libellé} au moyen de {k} items… » |
| Libellé du groupe non validé | « … mesure [à compléter : ce que mesure le groupe G1] au moyen de… » |
| Étiquettes des extrémités | « notés de 1 à 4 » sans parenthèses, et « [à compléter : étiquettes des extrémités] » |
| Cotation en simple note (sans items) | I1 à I6 deviennent : « [à compléter : description de l'instrument du groupe G1] » suivi de la note de cotation entre guillemets |
| Moins de 2 personnes avec tous les items | I6 : « [à compléter : fidélité, trop peu de réponses complètes] » |

**Exemple** (alpha illustratif) :

> L'instrument Échelle d'anxiété fictive (Laboratoire fictif, 2024) mesure l'anxiété au cours du dernier mois au moyen de 6 items, notés de 1 (jamais) à 4 (très souvent). L'item anx3 est inversé avant le calcul du score. Le score (anx_total) est la somme des items, de 6 à 24. Il est calculé quand au moins 5 items sur 6 sont répondus ; un item manquant est remplacé par la moyenne des items répondus de la personne. Sur l'échantillon analysé, l'alpha de Cronbach est de ,84 (IC 95 % [,81 ; ,86], *n* = 339).

L'alpha suit l'APA : sans zéro initial, deux décimales.

## 7. Le paragraphe Analyses

Tiré du codebook pour la préparation, et du carnet pour les analyses retenues.

| # | Phrase (français) | Phrase (anglais) | Origine |
|---|---|---|---|
| A1 | Les codes {code} ({variable}) ; … ont été traités comme des valeurs manquantes. | Codes {code} ({variable}); … were treated as missing values. | codes manquants déclarés et confirmés ; omise s'il n'y en a pas |
| A2 | Les valeurs manquantes ont été retirées analyse par analyse : chaque analyse porte sur les personnes qui ont répondu à toutes ses variables. | Missing values were removed analysis by analysis: each analysis includes the people who answered all its variables. | toujours |
| A3 | Une phrase par méthode employée, dans l'ordre du catalogue (ci-dessous). | One sentence per method used, in the catalogue's order (below). | analyses retenues du carnet |
| A4 | Les valeurs de *p* sont données exactes, à trois décimales (*p* < ,001 en deçà). | *p* values are given exactly, to three decimals (*p* < .001 below that). | toujours |
| A5 | Les analyses ont été faites avec dictionnaire-donnees {version} (Python {v}, SciPy {v}, statsmodels {v}) ; un script R joint ({fichier}) les refait et donne les mêmes valeurs. | The analyses were run with dictionnaire-donnees {version} (Python {v}, SciPy {v}, statsmodels {v}); an attached R script ({file}) redoes them and gives the same values. | versions ; nom du script maître |

**Les phrases des méthodes (A3)**, seulement pour celles que le carnet emploie :

| Méthode | Phrase (français) |
|---|---|
| Tableau 1 | Les caractéristiques des participants sont décrites par la moyenne et l'écart-type, ou par l'effectif et le pourcentage. |
| Test t de Welch | Deux moyennes ont été comparées par le test *t* de Welch, qui ne suppose pas des variances égales ; la taille d'effet est le *d* de Cohen, avec son intervalle de confiance à 95 %. |
| Test t de Student | … par le test *t* de Student, qui suppose des variances égales ; … |
| Mann-Whitney | … par le test de Mann-Whitney ; la taille d'effet est la corrélation bisériale des rangs. |
| ANOVA | Plusieurs moyennes ont été comparées par une analyse de variance à un facteur ; les tailles d'effet sont η² et ω². |
| Tukey | Les groupes ont été comparés deux à deux par la méthode de Tukey. |
| Kruskal-Wallis | … par le test de Kruskal-Wallis ; la taille d'effet est ε². |
| Khi-carré | L'association entre deux variables catégorielles a été testée par le khi-carré de Pearson ; la taille d'effet est le *V* de Cramér. |
| Fisher | … par le test exact de Fisher. |
| Corrélation | Les liens entre variables continues sont décrits par la corrélation de Pearson, avec son intervalle de confiance à 95 %. / … de Spearman. |
| Régression | {issue} a été prédite par une régression linéaire ; les coefficients sont donnés bruts (*b*, avec leur intervalle de confiance à 95 %) et standardisés (β). |

Les phrases anglaises suivent le même tableau ; elles seront données avec le code, traduites d'un bloc, et relues avec le reste de l'anglais.

**Exemple** (carnet : un Tableau 1, un test t de Welch, une corrélation de Pearson) :

> Les codes 999 (age) ont été traités comme des valeurs manquantes. Les valeurs manquantes ont été retirées analyse par analyse : chaque analyse porte sur les personnes qui ont répondu à toutes ses variables. Les caractéristiques des participants sont décrites par la moyenne et l'écart-type, ou par l'effectif et le pourcentage. Deux moyennes ont été comparées par le test *t* de Welch, qui ne suppose pas des variances égales ; la taille d'effet est le *d* de Cohen, avec son intervalle de confiance à 95 %. Les liens entre variables continues sont décrits par la corrélation de Pearson, avec son intervalle de confiance à 95 %. Les valeurs de *p* sont données exactes, à trois décimales (*p* < ,001 en deçà). Les analyses ont été faites avec dictionnaire-donnees 0.12.0 (Python 3.11.9, SciPy 1.17.1, statsmodels 0.15.0) ; un script R joint (etude-passation-resultats.R) les refait et donne les mêmes valeurs.

## 8. Le document « Méthode et Résultats » (D-099, D-100)

- **Intertitres APA** : « Méthode » et « Résultats » au niveau 1 (centrés, gras) ; « Participants », « Instruments » et « Analyses » au niveau 2 ; les analyses des Résultats gardent leur intertitre de la v0.11 (« A2 — Test t : … »), au niveau 2.
- **Numérotation continue** : le diagramme de flux est la Figure 1 ; les Résultats suivent (`first_table`, `first_figure` du carnet s'ajoutent toujours à ce qui précède).
- **Gardés et confirmés** dans le carnet, sous une entrée `methode` (`carnet_version` 1.1.0) : le *N* de départ, les effectifs par règle, le *N* analysé, la description de l'échantillon (*M*, *ÉT*, *n*, pourcentages), et pour chaque groupe l'alpha, son intervalle et son *n*. Comparés comme une analyse ; un changement attend sa confirmation et bloque le document.
- **Aucune donnée individuelle** dans le carnet ni dans le document (test à chaînes témoins) : ni courriel, ni identifiant, ni date de passation, ni durée isolée.
- **La fin du document** garde l'empreinte, la date, les versions et la liste des analyses ; elle ajoute la liste des règles d'exclusion, avec leur source quand elles en ont une.

## 9. Points à valider

1. **La base fictive de passation** (§ 1) : sa composition et ses cas plantés.
2. **La règle de durée sur deux variables choisies** (§ 2), proposées automatiquement pour un export de plateforme : elle sert aussi à une base qui ne vient pas d'une plateforme.
3. **Le tableau des effectifs du flux** : numéroté dans Word (il devient le Tableau 1 de la Méthode), ou seulement dans le classeur Excel, la figure suffisant dans l'article. Recommandation : **seulement dans Excel**, pour ne pas consommer un numéro de tableau avec des chiffres que la figure donne déjà ; Word garde la figure.
4. **La phrase de description (P4)**, une liste de libellés et de statistiques, sans étendue : moins élégante qu'une phrase rédigée, mais juste quel que soit le libellé.
5. **Le paragraphe Instruments** (I1 à I6), y compris la tournure « L'instrument {nom} ({source}) mesure… », qui évite d'accorder un article au nom de l'instrument.
6. **Seuls les groupes cotés** ont un paragraphe Instruments ; un groupe sans cotation n'en a pas.
7. **Le paragraphe Analyses** (A1 à A5) et les phrases des méthodes.
8. **Les trous** : leur texte « [à compléter : …] », surligné en jaune.
