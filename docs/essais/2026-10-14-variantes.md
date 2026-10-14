# Essai : variantes d'écriture (v0.2, étape 7)

**Date :** 2026-10-14
**Règle :** les catégories visibles d'une variable de texte qui ne diffèrent que par la casse, les accents ou les espaces sont regroupées et signalées (« Variantes d'écriture d'une même réponse : « Français », « français », « Francais » »). Aucune autre ressemblance n'est cherchée : « Espagnol » et « Espanol » restent deux réponses. Seules les catégories déjà visibles dans le projet sont comparées, jamais les données.

## Base fictive

Une variable a été ajoutée, `langue_maison`, réponse tapée librement à « Quelle langue parlez-vous le plus souvent à la maison ? » :

- Français (110), français (25), Francais (12), Anglais (30), anglais (9), Espagnol (7) ;
- deux orthographes rares, Créole (3) et créole (2) ;
- 2 réponses vides.

Résultat, sur le `.sav` comme sur le CSV : deux groupes signalés, le plus fréquent d'abord. « Créole » et « créole », masqués par la porte de confidentialité (moins de 5), n'apparaissent ni dans le fichier projet, ni dans le codebook, ni dans le rapport, ni dans les messages au modèle (test). Le codebook dit seulement « 2 catégories rares retirées », comme avant.

## Base publique

Rien n'est signalé. Les variantes existent bien dans les données (décomptes faits localement, sans afficher de valeur) :

| Cas | Variables | Pourquoi rien n'est signalé |
|---|---|---|
| Une des orthographes a moins de 5 réponses | `ethnie_other`, `langue_maison_other`, `langue_maternelle_autre`, `soutien_autre_precision` | la catégorie rare est retirée ; la signaler la révélerait |
| Les deux orthographes ont 5 réponses ou plus | `pays_naissance`, `pays_naissance_enfant` | quasi-identifiants : aucune catégorie n'est montrée |

C'est le prix de la règle sur les petits effectifs (D-006). Le signal est utile sur les grandes bases et les réponses fréquentes. Les petites variantes relèvent du nettoyage des données lui-même, que l'équipe fait sur ses propres fichiers. Une aide au nettoyage qui travaillerait sur une copie de la base, sans rien écrire dans le projet ni rien envoyer au modèle, est une piste pour la v0.3, avec l'application des décisions à une copie du `.sav`.
