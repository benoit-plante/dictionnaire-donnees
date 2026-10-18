# Essai : le catalogue élargi et le sous-groupe sur la base AMATUS (v0.14, étape 7)

**Date :** 2026-10-18

**But :** refaire l'essai de la v0.13 (`2026-10-18-essai-plan-article-amatus.md`) avec ce que la v0.14 ajoute : les sous-groupes choisis dans l'outil, sur la base entière, au lieu d'un fichier dérivé réduit aux femmes ; et, là où l'article les demande, les nouvelles analyses (régression logistique, corrélation partielle). Puis le banc de l'IA conseillère sur le catalogue élargi, et le scénario manuel dans le navigateur. La base et l'article sont publics (CC BY 4.0) : ce compte rendu cite leurs chiffres publiés. Aucune donnée n'entre dans le dépôt ; le travail s'est fait dans un dossier temporaire, supprimé à la fin.

## 1. Le parcours

La base AMATUS entière (1 106 personnes, femmes et hommes), avec une seule colonne ajoutée hors de l'outil : `enseignante` (« oui », « non »), tirée de l'échantillon. L'outil ne recode pas encore ; c'est la seule préparation restante (le fichier dérivé de la v0.13 retirait aussi les hommes). Tout passe par la ligne de commande, chaque commande en moins d'une seconde et demie.

1. `ddict profiler`, puis `ddict niveaux accepter` et `fixer`, et `ddict codes manquant -1` pour les deux questions d'attitude.
2. Le plan, avec `ddict plan ajouter … --sous-groupe sex eq f` : H1 à H4 comme en v0.13 (les femmes), H5, exploratoire, les enseignantes et les enseignants comparés (`--sous-groupe enseignante eq oui`), H6, exploratoire, une régression logistique de la spécialisation en maths, et H7, exploratoire, une corrélation partielle du plaisir d'enseigner, à spécialisation constante.
3. `ddict plan regles`, `figer`, l'amendement de H2 (Mann-Whitney), puis `ddict plan preenregistrement` et `ddict article`, en français et en anglais ; le script R maître lancé dans R 4.6.1.

## 2. Les chiffres, face à l'article publié et à R

| Résultat | Article publié | Outil (sous-groupe choisi dans l'outil) | R (script maître) |
|---|---|---|---|
| H1 : anxiété, enseignantes et étudiantes (femmes) | *t*(818) = 2,28, *p* = ,023 (bilatéral) | *t*(818) = −2,28, *p* = ,011 (unilatéral), *d* = −0,18 | *t* = −2,280787, 818 ddl, *p* = ,0114 |
| H3 : anxiété et plaisir d'enseigner | *r*(180) = −,470 | *r*(180) = −,47 ; *p* corrigé (Holm) < ,001 | même *r* |
| H4 : anxiété et facilité d'enseigner | *r*(179) = −,479 | *r*(179) = −,48 ; *p* corrigé (Holm) < ,001 | même *r* |
| H5 : enseignantes et enseignants | *t*(256) = 4,16, *d* = 0,76 | *t*(256) = 4,16, *d* = 0,76 | *t* = 4,159564, *d* = 0,7562601 |
| H2 (amendée) : en poste et en formation | ANOVA, *F*(1, 219) = 0,06 | *U* = 4842,5, *p* = ,456 | mêmes *U* et *p* |
| H6 : anxiété et spécialisation en maths (logistique) | — | RC = 0,92, χ²(1) = 19,43, *n* = 223 | RC = 0,9172131, χ² = 19,4334, *n* = 223 |
| H7 : plaisir d'enseigner, à spécialisation constante (partielle) | — | *r* partiel(179) = −,41 | *r* = −0,4117907, 179 ddl |

Les chiffres de la v0.13 reviennent à l'identique, cette fois depuis la base entière : le sous-groupe de l'outil fait le même tri que le fichier dérivé. H5, impossible en v0.13 (le fichier ne gardait que les femmes), redonne le *t* et le *d* de l'article. Le script R maître refait chaque sélection et tourne sans erreur en 0,35 seconde.

## 3. Ce que l'essai a trouvé, et corrigé

| Défaut | Effet | Correction |
|---|---|---|
| Les tableaux et les figures relisaient la base entière, sans le sous-groupe | note du tableau de H1 : « non : *n* = 848 ; oui : *n* = 258 » (1 106 personnes, hommes compris) à côté de *t*(818) ; effectifs, moyennes et points faux dans les tableaux et les figures qui relisent la base (vérifié pour le test t, l'apparié, les mesures répétées, la corrélation et la modération) | les tableaux et les figures lisent les personnes du sous-groupe ; la note dit « non : *n* = 597 ; oui : *n* = 223 » ; un test compare, pour chaque analyse, la description sur sous-groupe à celle de la même analyse faite sur ses seules personnes |
| L'IA conseillère refusait toute proposition qui nommait un rôle ou une méthode de la v0.14 | banc de suivi : 1 réponse valide sur 6 | les rôles et les méthodes permis viennent du catalogue, comme les analyses ; le test du corrigé tourne aussi sur les objectifs de suivi |
| Le test apparié disait « le premier groupe plus élevé » | deux mesures appelées groupes, sur la page « Analyses » et dans le rapport | « la première mesure plus élevée » |
| L'axe logarithmique de la figure d'une régression logistique, dans l'outil et dans Word, s'écrivait « 5 × 10⁻¹, 6 × 10⁻¹… », illisible | graduations superposées | des valeurs simples (0,5 ; 0,7 ; 1), choisies selon l'étendue |

Les deux premiers défauts échappaient aux tests : ceux du sous-groupe vérifiaient la phrase et les statistiques, pas les effectifs des notes ; celui du conseiller ne tournait que sur les anciens objectifs.

## 4. Les documents

| Vérification | Résultat |
|---|---|
| Préenregistrement, nombres tirés des données | aucun, en français comme en anglais |
| L'outil dit que l'étude a été préenregistrée | jamais |
| Préenregistrement et article, mots qui jugent | aucun |
| Article, intertitres | Méthode (Participants, Analyses, Plan d'analyse), Résultats (H1 à H4, puis « Analyses exploratoires » : H5 à H7), Discussion, Références |
| Article, trous | 18 |
| Méthode | une phrase par analyse sur sous-groupe : « L'analyse A1 porte sur un sous-groupe : sex = f. » |
| Résultats | chaque phrase commence par « Sous-groupe (sex = f). », chaque note de tableau et de figure aussi |
| Graphique Excel des rapports de cotes, rendu par LibreOffice | axe logarithmique de 0,1 à 10, ligne à 1, intervalle asymétrique gardé (+0,038, −0,036) |

## 5. Le banc de l'IA conseillère

Le modèle `qwen2.5:7b-instruct-q4_K_M`, température 0, sur les deux jeux d'objectifs (`scripts/banc_conseil.py`, `--suivi` pour le second, D-115) :

| Objectifs | Réponses valides | Bonne analyse en premier, bonnes variables | Bonne analyse parmi les propositions |
|---|---|---|---|
| Base des analyses, 13 objectifs (catalogue élargi offert) | 12 | 10 | 11 |
| Base de suivi, 6 objectifs (apparié, mesures répétées, logistique, modération, partielle, apparié chez les femmes) | 6 (après correction ; 1 avant) | 4 | 5 |

Sur les anciens objectifs, le catalogue élargi ne dégrade pas le modèle (11 sur 13 parmi ses propositions, comme en v0.13). Sur les nouveaux, les deux écarts sont des écarts de jugement : pour la modération, il ajoute deux covariables que l'objectif ne demande pas ; pour la corrélation partielle, il la propose en second, derrière une corrélation simple des trois variables. L'objectif « chez les femmes seulement » reçoit le bon test apparié ; le sous-groupe ne fait pas partie de la proposition (D-115), il reste à choisir.

## 6. Le scénario dans le navigateur

Sur la base fictive de suivi, ouverte depuis la liste des projets récents (étapes 54 à 58 de `docs/scenario-revision.md`) : test apparié chez les femmes (*t*(125) = 6,08, *n* = 126 ; 114 écartées, « valeurs manquantes, ou hors du sous-groupe ») ; tableau APA à *n* = 126 avec sa note ; régression logistique et sa figure ; hypothèse appariée sur la page « Plan », dont le sens attendu nomme les deux mesures, avec son sous-groupe. Deux défauts d'affichage y ont été vus et corrigés (§ 3 : « premier groupe », axe logarithmique).

## 7. Ce que l'outil ne fait toujours pas

- **Recoder** une variable (ici, `enseignante` tirée de l'échantillon) : le seul fichier dérivé restant.
- **L'ANOVA à deux facteurs**, la **régression ordinale**, les **facteurs de Bayes**, la **corrélation polychorique** et les **centiles des normes** de l'article.
- Un sens attendu pour une régression logistique reste noté au plan, mais le test reste bilatéral (comme pour les prédicteurs d'une régression linéaire, D-103).
