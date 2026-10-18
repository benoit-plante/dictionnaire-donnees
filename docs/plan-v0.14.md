# Plan de la v0.14

> Statut : **validé par l'auteur le 2026-10-18**, avec les décisions D-111 à D-115 (§ 8). Suit la feuille de route [`feuille-de-route-article.md`](feuille-de-route-article.md), § 7, et l'essai de la v0.13 sur la base ouverte AMATUS ([`essais/2026-10-18-essai-plan-article-amatus.md`](essais/2026-10-18-essai-plan-article-amatus.md)). Même cap que les v0.11 à v0.13 : **aucune IA ajoutée** ; la règle « Rien ne quitte le poste » reste entière. Fiche de l'étape 1 : [`catalogue-elargi.md`](catalogue-elargi.md).

## 1. Pourquoi cette version

Le catalogue de la v0.9 couvre six analyses. Il en manque de très courantes en psychologie, et l'essai AMATUS a montré une autre limite :

1. **Deux mesures d'une même personne** (avant et après, deux échelles d'une même passation) : aucun test apparié.
2. **Une issue oui/non** (abandon, diagnostic) : pas de régression logistique.
3. **Un effet qui dépend d'une troisième variable** : pas de modération.
4. **Une association à covariables constantes** : pas de corrélation partielle.
5. **Trois temps ou plus** : pas d'ANOVA à mesures répétées.
6. **Un sous-groupe** : les auteurs d'AMATUS n'analysaient que les femmes ; il a fallu préparer un fichier à part, hors de l'outil, et l'article ne pouvait pas le dire.

## 2. Ce que l'outil produira

- **Cinq analyses nouvelles**, chacune au niveau des six premières : conditions et refus, options, calcul, taille d'effet avec son intervalle, phrase qui décrit sans juger, tableau et figure APA en français et en anglais, script R en R de base vérifié à 10⁻⁶ près, place dans le carnet, le plan (effet testé, sens attendu) et l'ébauche d'article.

| Analyse | Effet testé | Calcul |
|---|---|---|
| Test *t* apparié, Wilcoxon des rangs signés | la différence entre les deux mesures | SciPy |
| Régression logistique binaire | le modèle ou un prédicteur (rapport de cotes) | statsmodels |
| Modération | l'interaction ; pentes simples | statsmodels |
| Corrélation partielle | la corrélation à covariables constantes | calcul dans l'outil |
| ANOVA à mesures répétées | l'effet du temps ; Greenhouse-Geisser | statsmodels et calcul dans l'outil |

- **Le sous-groupe** : une analyse, une entrée du carnet ou une hypothèse du plan peut porter sur une partie des personnes, décrite par une condition (« sexe = Femme »). La condition se dit dans la phrase, dans la note du tableau, dans la Méthode et dans le script R.
- **Le sens attendu par les noms des groupes** : « Intervention plus élevé » au lieu de « Le premier groupe plus élevé », sur la page « Plan ».
- Une **base fictive** aux effets plantés (`etude-suivi`), générée avec une graine fixe, et son corrigé.

## 3. Conception — les analyses

Le détail de chaque analyse est dans la fiche de l'étape 1. Principes communs :

- **Les mêmes règles que la v0.9** : cas complets par analyse ; refus avec leur raison ; avertissements que la personne juge ; *p* sans zéro initial ; phrases qui décrivent ; tailles d'effet avec leur IC 95 %.
- **Les mesures d'une même personne** (test apparié, ANOVA à mesures répétées) sont des colonnes d'une même ligne. Elles sont refusées quand la description de la base dit « format long » : une ligne n'y est pas une personne (D-112).
- **Le script R reste en R de base** (D-071, D-077) : `t.test(paired = TRUE)`, `wilcox.test(paired = TRUE)`, `glm(family = binomial)`, `lm`, `anova.mlm` avec `test = "Spherical"` pour Greenhouse-Geisser.
- **L'IA conseillère** reçoit le catalogue élargi ; son banc d'essai est refait avant la publication (D-115).

## 4. Conception — le sous-groupe

- Une condition sur une variable, avec les opérateurs des règles d'exclusion (`eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`) ; jamais sur un identifiant ni un texte libre ; jamais une liste de personnes (D-113).
- Appliquée après les règles d'exclusion, pour cette analyse seulement : le flux des participants ne change pas.
- Gardée avec l'analyse dans le carnet et avec l'hypothèse dans le plan ; changer la condition d'une hypothèse figée est un amendement.

## 5. Conception — les textes

- Résultats : la phrase et la note du tableau disent le sous-groupe (« Femmes seulement (sexe = Femme), n = 223 »).
- Méthode, paragraphe Analyses : une phrase par analyse nouvelle, comme pour les six premières ; le sous-groupe de chaque analyse qui en a un.
- Discussion : le sens observé pour les nouveaux effets (la différence apparié, le rapport de cotes, l'interaction, la corrélation partielle) ; l'ANOVA à mesures répétées n'a pas de sens attendu.

## 6. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiche : les cinq analyses, le sous-groupe, les phrases et les tableaux ; la base fictive `etude-suivi` aux effets plantés et son corrigé | Validée par l'auteur ; exemples calculés par un prototype et refaits dans R |
| 2 | Test *t* apparié et Wilcoxon, avec le refus en format long | Effets plantés retrouvés ; égal à R à 10⁻⁶ près ; test commun des formats |
| 3 | Corrélation partielle et modération | Égales à R ; pentes simples vérifiées |
| 4 | Régression logistique | Égale à `glm(binomial)` ; issue sans deux modalités refusée ; séparation signalée |
| 5 | ANOVA à mesures répétées | *F*, ηp², Mauchly et epsilon de Greenhouse-Geisser égaux à R de base |
| 6 | Le sous-groupe dans l'analyse, le carnet, le plan, l'article et R ; le sens attendu par les noms des groupes | Mêmes effectifs dans l'outil et dans R ; condition dite dans la Méthode |
| 7 | Pages et commandes ; banc de la conseillère ; essai AMATUS refait sur les femmes dans l'outil ; guides, journal des changements, version 0.14.0 | Scénario refait dans le navigateur ; guides en français et en anglais |

Si la version s'allonge, l'ANOVA à mesures répétées (étape 5) passe en 0.14.1.

## 7. Risques

- **R de base seulement** : Greenhouse-Geisser et les pentes simples s'écrivent à la main ; chacune est vérifiée contre une autre voie de calcul.
- **La régression logistique et ses cas limites** : séparation complète, issue rare ; signalés, jamais cachés.
- **Le sous-groupe touche à tout** : carnet, plan, Méthode, R. C'est l'étape la plus transversale ; elle vient après les analyses, qui n'en dépendent pas.
- **La conseillère** : un catalogue plus long rend son message plus long ; il doit tenir dans le contexte du modèle (D-080).
- **La taille de la version** : le report de l'ANOVA à mesures répétées est prévu.

## 8. Décisions

| N° | Décision | Choix |
|---|---|---|
| D-111 | **Les analyses de la v0.14** | Test *t* apparié et Wilcoxon, régression logistique binaire, modération, corrélation partielle, ANOVA à mesures répétées. Médiation, multiniveau, équations structurelles et analyse factorielle attendent un moteur R facultatif. |
| D-112 | **Les mesures d'une même personne** | Des colonnes d'une même ligne ; refusées quand la base est décrite en format long. |
| D-113 | **Le sous-groupe** | Une condition par analyse ou par hypothèse, avec les opérateurs des exclusions ; jamais sur un identifiant ni un texte libre ; jamais une liste de personnes ; dit dans la phrase, la note, la Méthode et R. |
| D-114 | **L'ANOVA à deux facteurs** | Reportée. |
| D-115 | **L'IA conseillère** | Elle reçoit le catalogue élargi ; son banc d'essai est refait avant la publication. |

Reste à trancher, à l'étape 6 : faire confirmer, ou non, chaque *p* corrigé qui change (question ouverte depuis la v0.13).
