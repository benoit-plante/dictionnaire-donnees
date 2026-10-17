# Plan de la v0.13

> Statut : **validé par l'auteur le 2026-10-17**, avec les décisions D-101 à D-108 (§ 9) ; D-105 remplacée le même jour par D-109 (deux gabarits de préenregistrement, selon l'origine des données). Suit la feuille de route [`feuille-de-route-article.md`](feuille-de-route-article.md), § 6. Même cap que les v0.11 et v0.12 : de la base à une ébauche d'article IMRaD **sans aucune IA**. La v0.13 n'ajoute aucun usage de l'IA, locale ou non ; la règle « Rien ne quitte le poste » reste entière ; l'IA conseillère reste telle quelle.

## 1. Pourquoi cette version

Le carnet (v0.11) donne les Résultats, et la v0.12 rédige la Méthode. Il manque encore le lien entre **ce qui était prévu** et **ce qui a été fait** :

1. **Les hypothèses ne sont gardées nulle part.** L'objectif tapé pour la conseillère reste en mémoire (D-079). Rien ne distingue une analyse prévue d'une analyse exploratoire.
2. **Aucune correction pour comparaisons multiples.** Une équipe qui teste six hypothèses doit corriger ses *p* à la main.
3. **Pas de préenregistrement.** L'outil connaît presque tout ce qu'un formulaire de préenregistrement demande (variables, cotation, exclusions, analyses), mais ne l'écrit pas.
4. **Pas d'article.** Le document s'arrête à « Méthode et Résultats ». L'Introduction, la Discussion et les Références manquent, même sous forme de trous.

## 2. Ce que l'outil produira

**Le plan d'analyse**
- **Des hypothèses**, écrites par l'équipe et numérotées H1, H2… Chacune a :
  - son **énoncé**, tapé tel quel ;
  - une **analyse du catalogue**, ses variables par rôle et ses options, choisies à la main ;
  - l'**effet testé** : la statistique qui répond à l'hypothèse, parmi celles de l'analyse (§ 4) ;
  - un **sens attendu**, facultatif (positif, négatif, tel groupe plus élevé), qui règle le test unilatéral quand l'analyse le permet (D-103) ;
  - un **caractère** : confirmatoire ou exploratoire ;
  - une **famille**, facultative, pour la correction.
- **Les règles générales** : le seuil α tapé par l'équipe, la correction (aucune, Holm ou Bonferroni), le traitement des manquants (aujourd'hui, une seule possibilité : suppression par analyse) et une justification de la taille d'échantillon, en texte (le calcul de puissance est reporté, D-108).
- **Un plan figé** : une date et une empreinte, comme le codebook. Le plan reste modifiable après coup, mais chaque modification devient un **amendement** gardé, daté, avec sa raison, et dit dans la Méthode.
- **Une honnêteté sur les dates** (D-102) : la base existe déjà quand l'outil s'ouvre. Le plan ne prétend donc jamais avoir été écrit avant les données. La Méthode dit la date du plan et, quand c'est le cas, qu'une analyse prévue avait déjà été calculée dans le carnet avant que le plan soit figé.

**Dans le carnet**
- Chaque hypothèse crée son entrée dans le carnet, liée au plan. Chaque entrée est rapprochée du plan :
  - **prévue** (H2) : mêmes variables et mêmes options que l'hypothèse ;
  - **écart au plan** : une variable, une option ou l'effet testé a changé ; l'écart est dit en clair ;
  - **exploratoire** : aucune hypothèse ne la prévoit.
- **La correction pour comparaisons multiples**, dans chaque famille déclarée : les *p* bruts et corrigés, côte à côte dans les tableaux et la phrase de résultat (D-104).

**Le préenregistrement**
- Un document Word et Markdown, rempli à partir du plan et du codebook, selon un gabarit (D-105). Ce qui manque reste un trou signalé.

**L'article**
- Le document devient une **ébauche IMRaD complète** (D-106) :
  - une page de titre et un résumé, en trous ;
  - **Introduction** : un trou pour le texte, puis les hypothèses du plan, numérotées ;
  - **Méthode** : celle de la v0.12, plus un paragraphe sur le plan (date, préenregistrement, amendements, analyses exploratoires, correction) ;
  - **Résultats** : rangés par hypothèse, puis les analyses exploratoires, puis les autres (Tableau 1…) ;
  - **Discussion** : pour chaque hypothèse, le rappel du résultat, sa phrase et le sens observé ; jamais « soutenue » ni « rejetée » (D-107), puis un trou pour l'interprétation ;
  - **Références** : les sources du codebook, telles que l'équipe les a écrites (D-106).

**Interface et ligne de commande**
- Une page **« Plan »**, avant « Analyses » : les règles générales, les hypothèses (ajouter, ordonner, retirer), leurs conditions vérifiées, le bouton **Figer le plan**, les amendements, et l'export du préenregistrement.
- En ligne de commande : `ddict plan lister | ajouter | retirer | deplacer | regles | figer | amender | preenregistrement`, et `ddict article`.

## 3. Conception — le plan dans le projet

**Dans le projet** (D-101), format 0.5.0 (migration automatique d'un projet 0.4.0) :

```json
"plan": {
  "alpha": 0.05,
  "correction": "holm",
  "missing": "listwise_by_analysis",
  "sample_size": "Toutes les réponses reçues entre mars et mai 2026.",
  "next_id": 3,
  "hypotheses": [
    {"id": "H1", "statement": "Le bien-être diffère selon le groupe d'intervention.",
     "analysis": "t_test", "roles": {"outcome": [{"group": "G1"}], "group": [{"name": "groupe"}]},
     "options": {"method": "welch", "alternative": "greater"}, "effect": "difference",
     "direction": "first_higher", "kind": "confirmatory", "family": "F1"},
    {"id": "H2", "statement": "Le sommeil est lié au bien-être.",
     "analysis": "correlation", "roles": {"variables": [{"name": "sommeil"}, {"group": "G1"}]},
     "options": {"method": "pearson"}, "effect": "r_2_1",
     "direction": "positive", "kind": "confirmatory", "family": "F1"}
  ],
  "frozen": {"date": "2026-10-20", "fingerprint": "sha256:…"},
  "amendments": [
    {"date": "2026-11-02", "hypothesis": "H2", "reason": "Spearman : distribution du sommeil très asymétrique",
     "before": {"options": {"method": "pearson"}}, "after": {"options": {"method": "spearman"}}}
  ]
}
```

- **Des variables par leur clé du projet** (`VariableRef` du carnet) : nom d'origine, groupe d'un score, item inversé. Elles survivent à un renommage.
- **Une hypothèse mal liée est refusée avec sa raison** : analyse inconnue, rôle mal rempli, effet testé qui n'existe pas pour cette analyse, sens attendu que l'analyse ne peut pas tester, et toutes les conditions du codebook (D-074). Le Tableau 1 ne peut pas porter une hypothèse : il ne teste rien.
- **Le seuil α est tapé par l'équipe.** La page propose ,05 dans le champ ; rien n'est enregistré sans une personne.
- **L'empreinte du plan** couvre les règles générales et les hypothèses, pas les amendements. Elle est distincte de celle du codebook : écrire le plan ne rend aucune analyse « changée, à confirmer ».
- **Figer** n'interdit rien : après le gel, toute modification d'une hypothèse demande une raison et devient un amendement. Retirer une hypothèse figée aussi.
- **Ce qui ne va jamais dans le plan** : aucune valeur des données, aucun résultat. Le plan est une décision ; le carnet garde les résultats (D-087).

## 4. Conception — l'effet testé et la correction

Une hypothèse porte sur **un seul *p***. L'effet testé dit lequel :

| Analyse | Effets testés possibles | *p* utilisé |
|---|---|---|
| Test *t* (Welch, Student) | la différence des moyennes | celui du test *t* |
| Mann-Whitney | la différence des rangs | celui du test *U* |
| ANOVA, Kruskal-Wallis | l'effet du groupe | celui du test global |
| Khi-carré, Fisher | l'association | celui du test |
| Corrélation | une paire (`r_2_1`…) | celui de la paire |
| Régression | le modèle, ou un prédicteur | celui du *F* global, ou du coefficient |

- **Holm ou Bonferroni**, dans chaque famille déclarée, sur les *p* des hypothèses de la famille dont l'analyse a pu être calculée. Les deux sont vérifiés contre `p.adjust` de R, à 10⁻¹² près.
- Une hypothèse sans famille, ou seule dans sa famille, n'est pas corrigée. Une analyse exploratoire ne l'est jamais : elle n'appartient à aucune famille.
- Le *p* corrigé s'ajoute aux statistiques gardées par le carnet (`p_adj`), confirmé comme les autres : ajouter une hypothèse à une famille change les *p* corrigés des autres, et le carnet le montre avant l'export.
- Les tableaux gardent le *p* brut et ajoutent une colonne « *p* corrigé (Holm) ». La phrase de résultat donne les deux : « *t*(96,4) = 2,31, *p* = ,023, *p* corrigé (Holm) = ,046 ».

## 5. Conception — gabarits et trous

Comme en v0.12 (D-097) : des phrases fixes, en français et en anglais, traduites d'un bloc ; un champ absent devient un trou « [à compléter : …] », surligné en jaune dans Word ; aucun mot qui juge ; chaque fait du texte a une origine dans le plan, le codebook ou le carnet, vérifiée par un test phrase par phrase.

Exemples à valider dans la fiche (étape 1) :

- Méthode, plan : « Le plan d'analyse a été arrêté le 20 octobre 2026 ({lieu du préenregistrement}). Il prévoyait deux hypothèses confirmatoires ; les *p* ont été corrigés par la méthode de Holm au sein de chaque famille. »
- Méthode, amendement : « Une modification a été apportée au plan le 2 novembre 2026, pour H2 : corrélation de Spearman au lieu de Pearson ({raison}). »
- Méthode, date : « L'analyse prévue pour H1 avait été calculée avant que le plan soit arrêté. »
- Discussion, rappel : « H1 prévoyait un bien-être plus élevé dans le groupe d'intervention. La moyenne observée était plus élevée dans ce groupe, *t*(96,4) = 2,31, *p* corrigé = ,046, *d* = 0,47. [à compléter : interprétation] »

Le **sens observé** est un fait (« plus élevée », « positive ») ; dire s'il **confirme** l'hypothèse est un jugement, laissé à l'équipe (D-107).

## 6. Conception — le préenregistrement

*Remplacé par D-109 : deux gabarits, OSF Prereg pour des données primaires et van den Akker et al. pour des données secondaires ; voir la fiche, § 8.* Version d'origine : un seul gabarit dans cette version (D-105), conçu pour une **base existante** : les rubriques du gabarit OSF pour l'analyse de données secondaires (Van den Akker et al., 2021), dont la licence sera vérifiée à l'étape 1 et notée dans `docs/dependances.md`. Le gabarit AsPredicted, pensé pour une collecte à venir, attend.

Rempli à partir de l'outil :

| Rubrique | Source |
|---|---|
| Hypothèses | le plan |
| Variables et leur cotation | le codebook (instruments, cotations, items inversés, codes manquants) |
| Exclusions | les règles de la v0.12, avec leurs raisons (jamais leurs effectifs : le préenregistrement précède les résultats) |
| Analyses | le plan : analyse, variables, options, effet testé, sens, α, correction |
| Manquants | le plan |
| Taille d'échantillon | le texte du plan |
| Connaissance préalable des données | **un trou toujours** : seule l'équipe peut dire ce qu'elle a déjà vu |

Le préenregistrement est écrit à côté du projet (`<projet>-preenregistrement.docx` et `.md`). L'outil ne le dépose nulle part.

## 7. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiche : format du plan, effets testés par analyse, gabarit de préenregistrement (licence vérifiée), gabarits de l'article en français et en anglais, sur la base fictive des analyses | Validée par l'auteur |
| 2 | Plan dans le projet (format 0.5.0, migration) : hypothèses, conditions, empreinte, gel, amendements | Une hypothèse mal liée est refusée avec sa raison ; un projet 0.4.0 s'ouvre tel quel ; une modification après le gel exige une raison |
| 3 | Rapprochement du carnet et du plan ; correction pour comparaisons multiples | *p* corrigés égaux à `p.adjust` de R ; prévue, écart et exploratoire retrouvés sur des cas plantés |
| 4 | Préenregistrement (Word et Markdown) | Chaque champ rempli retrouvé dans le plan ou le codebook ; trous signalés ; aucun effectif ni résultat |
| 5 | Article IMRaD : Introduction, paragraphe du plan, Résultats par hypothèse, Discussion, Références | Test commun des formats ; aucun mot qui juge ; références tirées des sources seulement ; vérifié dans Word |
| 6 | Page « Plan », `ddict plan`, `ddict article` | Parcours dans le navigateur ; mêmes fichiers depuis la page et la ligne de commande |
| 7 | Essai sur une vraie base (faits de structure seulement) ; guides, journal des changements, version 0.13.0 | Scénario refait dans le navigateur ; guides en français et en anglais |

Si la version s'allonge, le préenregistrement (étape 4) passe en 0.13.1 : le plan, la correction et l'article suffisent seuls.

## 8. Risques

- **Un faux préenregistrement.** Un plan écrit après avoir vu les données, présenté comme confirmatoire. L'outil ne peut pas le savoir, mais il ne ment pas : il dit la date du plan, ce qui avait déjà été calculé, et laisse toujours en trou la connaissance préalable des données.
- **Des *p* corrigés qui changent sans qu'on le voie.** Ils sont gardés et confirmés comme les autres statistiques (D-089).
- **Un texte qui juge.** Le rappel décrit le sens observé, jamais l'issue de l'hypothèse ; un test cherche les mots interdits (« soutenue », « confirmée », « rejetée », « significatif ») dans les deux langues.
- **Des références mal formées.** L'outil recopie les sources telles quelles et ne les reformate pas en APA : il ne connaît ni les auteurs ni l'année avec certitude.
- **Un document trop long à relire.** Les trous sont surlignés ; l'article reste une ébauche, et le guide le dit.

## 9. Décisions à prendre

La feuille de route réservait D-093 à D-095 à la v0.13 ; la v0.12 les a pris. Les décisions ci-dessous prennent D-101 à D-108.

| N° | Décision | Recommandation |
|---|---|---|
| D-101 | **Où vit le plan** | Dans le projet (format 0.5.0) : ce sont des décisions de l'équipe, pas des résultats. Variables par leur clé du projet. Une empreinte propre, hors de celle du codebook. |
| D-102 | **Gel, amendements et honnêteté sur les dates** | Figer donne une date et une empreinte ; ensuite, toute modification est un amendement daté, avec sa raison, dit dans la Méthode. La Méthode dit si une analyse prévue avait été calculée avant le gel. Le mot « préenregistré » n'est jamais écrit par l'outil : c'est l'équipe qui dépose. |
| D-103 | **Effet testé et sens attendu** | Une hypothèse porte sur un seul *p*, désigné par son effet testé (§ 4). Le sens attendu règle le test unilatéral seulement là où le catalogue l'offre déjà (test *t*) ; ailleurs, le test reste bilatéral et le sens n'est que rappelé. |
| D-104 | **Correction pour comparaisons multiples** | Holm par défaut quand une famille est déclarée, Bonferroni au choix ; aucune correction sans famille ni pour l'exploratoire ; *p* bruts et corrigés tous deux dans les tableaux et la phrase ; vérifiés contre `p.adjust`. |
| D-105 | **Le gabarit de préenregistrement** | Un seul : les rubriques OSF pour données secondaires, adaptées à une base existante, si sa licence le permet (sinon, nos propres rubriques). La connaissance préalable des données est toujours un trou. |
| D-106 | **L'article** | Le document « Méthode et Résultats » devient `<projet>-article.docx`, une ébauche IMRaD complète (D-099 l'annonçait), avec ses deux compagnons renommés (`-article-graphiques.xlsx`, `-article-R.zip`) ; `ddict resultats` reste un alias de `ddict article` pendant une version. Les Références recopient les sources du codebook telles quelles, triées, sans reformatage. |
| D-107 | **La Discussion** | Pour chaque hypothèse : son énoncé, le sens observé, la phrase de résultat ; jamais « soutenue », « rejetée » ou « significatif » écrits par l'outil ; l'interprétation reste un trou. |
| D-108 | **Reportés après la v0.13** | Le calcul de puissance (la taille d'échantillon reste un texte), le gabarit AsPredicted, une conseillère qui propose des hypothèses (la conseillère actuelle peut toujours remplir les choix de la page « Analyses »). |
