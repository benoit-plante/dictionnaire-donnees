# Essai : un modèle local écrit une analyse à partir du codebook (v0.8, étape 8)

**Date :** 2026-10-15

**But :** voir si le contexte d'analyse (étape 6) aide un modèle local à écrire une analyse juste, par rapport au rapport Markdown du codebook. Un premier essai, pas un banc.

## Protocole

- **Base :** l'étude fictive du sommeil, révisée comme les exemples (`tests/context_examples.py`) : codes 999 (`age`), 9 (`sommeil_q3`) et −9 (`nb_reveils`) confirmés manquants, 9 du genre déclaré manquant dans le fichier, `sommeil_q3` et `sommeil_q6` inversés, cotation de G1 (somme de 8 items, au moins 7 répondus, somme proportionnelle).
- **Deux conditions, la même consigne :** (A) le rapport Markdown du codebook, version finale (22 697 caractères ; il contient déjà la phrase de cotation de l'étape 4) ; (B) le contexte d'analyse (7 479 caractères, trois fois plus court).
- **Consigne :** écrire un script R qui calcule le score de qualité du sommeil (`score`), sa moyenne selon le genre (`moyennes_genre`) et sa corrélation avec l'âge (`correlation`), à partir d'un objet `donnees` déjà chargé (`haven::read_sav(user_na = TRUE)`, fichier de commandes appliqué).
- **Modèle :** qwen2.5 7B (q4_K_M), Ollama sur ce poste, température 0,3, graines 1 à 3 ; trois essais par condition.
- **Mesure :** le script est exécuté dans R sur la base fictive et ses résultats comparés aux bonnes réponses, calculées indépendamment par `scripts/essai_contexte_modele.py` ; puis chaque script est lu selon la grille ci-dessous.
- **Confidentialité :** le modèle ne reçoit que des documents de métadonnées ; rien ne quitte le poste.

## Résultats

| Vérification | A, rapport (3 essais) | B, contexte (3 essais) |
|---|---|---|
| Le script s'exécute sans erreur | 1 | 0 |
| Résultats justes (score, moyennes, corrélation) | 0 | 0 |
| `sommeil_q3` et `sommeil_q6` inversés | 2 | 2 (et une tentative qui ne fonctionne pas) |
| Code 9 de `sommeil_q3` traité comme manquant | 1 (la personne entière écartée) | 1 (idem) |
| Règle « au moins 7 items, somme proportionnelle » | 0 | 0 (un essai divise par 8 : une moyenne) |
| Tous les items dans le score | 3 | 1 (`sommeil_q7` oublié deux fois) |
| Code 9 du genre exclu | 0 | 0 |
| Code 999 de l'âge exclu | 0 | 0 |
| Variable sensible utilisée | 0 | 0 |
| Invention | 1 (des constantes sans fondement soustraites au score) | 0 |

Les erreurs d'exécution sont surtout des erreurs de programmation R, les mêmes dans les deux conditions : un score calculé hors du tableau puis appelé comme une de ses colonnes, `apply` sur un tableau mixte (qui convertit tout en texte), un usage erroné de `dplyr`. Aucun script ne tient compte de ce que `user_na = TRUE` garde les codes manquants comme des valeurs : ni 9, ni 999, ni −9 ne deviennent `NA` sans `haven::zap_missing`, ce que les deux documents disent pourtant (« codes manquants »), sans le dire en termes de R.

## Constats

1. **Avec qwen2.5 7B, aucune des deux formes ne suffit à obtenir une analyse juste.** Le modèle lit les règles (inversion surtout) un peu mieux dans le contexte, mais l'écart est mince sur six essais, et il commet des erreurs de programmation élémentaires dans les deux conditions.
2. **Le contexte n'introduit aucune erreur de plus, en trois fois moins de texte,** et n'a donné lieu à aucune invention, là où le rapport en a eu une. Pour un modèle à petite fenêtre de contexte, sa taille reste son premier avantage (une vraie base de 400 variables tient dans le contexte, pas dans le rapport).
3. **Le script de préparation de l'étape 7 se justifie pleinement :** l'inversion, la règle des items manquants et le traitement des codes manquants, là où le modèle se trompe le plus, se calculent sans lui. Une suite naturelle : donner au modèle les variables déjà préparées (`sommeil_total`) et ne lui demander que l'analyse.
4. **Les codes manquants dans R :** une règle du contexte pourrait dire comment les retirer quand les données sont lues avec haven (`haven::zap_missing()` avant tout calcul). À décider : c'est une consigne propre à un logiciel, dans un document qui n'en dépend pas.

## Suite

Un banc d'analyse automatisé (bases fictives aux effets connus) ne vaut pas la peine avec un modèle de cette taille : ses erreurs de programmation masqueraient l'effet du document. À refaire avec un modèle plus grand, en local si le matériel le permet, et en donnant les variables préparées. Le script `scripts/essai_contexte_modele.py` refait l'essai avec un autre modèle (`--modele`).

## Complément : un assistant en ligne, utilisé à la main

**Protocole :** la consigne de la condition B (contexte d'analyse et même tâche, écrite par `scripts/essai_contexte_modele.py --consigne`) collée par l'auteur dans une nouvelle conversation d'un assistant en ligne, **Claude Opus 5.5** ; le code rapporté est vérifié par `--code`, exécuté dans R sur la base fictive et noté avec la même grille. L'outil n'a rien envoyé : c'est une personne qui a copié un document de métadonnées d'une étude fictive. Un seul essai ; l'assistant est de la même famille que celui qui a écrit l'outil, mais il ne disposait que de la consigne.

| Vérification | Résultat |
|---|---|
| Le script s'exécute sans erreur | oui |
| Score de chaque participant | juste (égal au calcul indépendant) |
| Moyennes par genre | justes, les trois étiquettes, sans groupe « 9 » |
| Corrélation avec l'âge | juste |
| Inversion, code 9 de `sommeil_q3`, règle des 7 items et somme proportionnelle | appliqués |
| Codes 9 du genre et 999 de l'âge | exclus (`haven::zap_missing`, comme le demandait la règle 1) |
| Variable sensible, invention | aucune |

Le code ajoute de lui-même un contrôle des valeurs hors des codes documentés, qui n'affiche qu'un nombre, conformément à la consigne de ne montrer aucune donnée individuelle.

**Second assistant, Claude Haiku 5.5** (même protocole, nouvelle conversation) : le script s'exécute et **tous les résultats sont justes**, identiques au calcul indépendant (score de chaque participant, trois moyennes par genre sans groupe « 9 », corrélation) ; aucune variable sensible, aucune invention. Il traite les codes manquants autrement : il reprend du contexte les codes eux-mêmes (9 de `sommeil_q3`, 9 du genre, 999 de l'âge) et les remplace par `NA`, au lieu de `haven::zap_missing` ; juste aussi, puisque le contexte les énumère.

**Constat :** avec deux modèles capables d'écrire du code R, de tailles différentes, le contexte d'analyse suffit à une analyse entièrement juste, codes manquants compris, sans la règle propre à R envisagée plus haut. La limite observée avec qwen2.5 7B tenait au modèle, pas au document. Cela reste un essai par modèle, sur une base fictive, avec des modèles de la même famille ; un code produit par un assistant se vérifie toujours avant d'être exécuté sur de vraies données.
