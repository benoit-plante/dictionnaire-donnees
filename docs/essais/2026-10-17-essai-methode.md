# Essai : les exclusions et la Méthode sur une vraie base (v0.12, étape 9)

**Date :** 2026-10-17

**But :** vérifier sur une vraie base que les règles d'exclusion s'écrivent, que leurs effectifs sont les mêmes dans l'outil, dans R et dans PSPP, que le document « Méthode et Résultats » se produit avec son diagramme de flux, et qu'une règle ajoutée après coup est bien vue. Comme le prévoit le plan (§ 6, étape 9), **aucun effectif ni résultat n'est consigné** : seulement des faits de structure et des comparaisons (égal ou non). Aucun nom de variable, aucun libellé, aucun instrument.

## 1. La base

La même base SurveyMonkey réelle que pour les essais de la v0.9 et de la v0.11, hors du dépôt : 252 variables. Le travail s'est fait sur une copie temporaire, supprimée à la fin. Tout passe par la ligne de commande (`ddict profiler`, `ddict exclusions`, `ddict carnet`, `ddict resultats`), comme le ferait une équipe ; seule la cotation d'une grille, nécessaire à l'alpha, a été écrite directement dans le projet, avec une source de l'essai.

Ce que la base offre aux règles :

- les dates de début et de fin, reconnues par la plateforme et proposées pour la durée ; elles sont en texte, et leur format a été détecté ;
- 6 grilles d'au moins 4 items, proposées pour la ligne droite ; une grille de 9 items a été cotée (moyenne, bornes tirées des étiquettes) ;
- 3 variables proposées pour les doublons (répondant, courriel, adresse IP) ;
- 18 variables catégorielles de 2 à 5 modalités.

## 2. Les règles

Une règle de chaque sorte, ajoutée par `ddict exclusions ajouter` : une condition « manquant » sur une variable catégorielle, la complétude de la grille, la durée (avec une source), la ligne droite, les doublons sur l'identifiant du répondant, et une condition sur le score.

| Vérification | Résultat |
|---|---|
| Les six règles acceptées | oui |
| Une condition sur l'identifiant du répondant | refusée (« nommerait une personne ») |
| Une durée sans source | refusée (« donnez sa source ») |
| Réponses reçues = exclues + échantillon analysé | oui |
| Somme des exclusions par règle = exclues | oui |
| Mêmes effectifs dans `ddict exclusions lister` et dans l'outil | oui |
| `ddict exclusions signaux` : aucune règle ajoutée par un signal | oui |
| Une règle déplacée : même échantillon analysé | oui |

Trois des six règles excluent au moins une personne sur cette base.

## 3. Le document « Méthode et Résultats »

Le carnet reçoit les variables qui décrivent l'échantillon (deux variables catégorielles) et deux analyses : un Tableau 1 et une corrélation qui inclut le score.

| Vérification | Résultat |
|---|---|
| `ddict resultats` | écrit en 2 à 3 secondes |
| Intertitres | Méthode, Participants, Instruments, Analyses, Résultats |
| Figure 1 | le diagramme de flux, seule figure du document |
| Tableaux | 2, numérotés à la suite |
| L'alpha du score dans les Instruments | oui |
| Trous « [à compléter : …] » | 2, en français comme en anglais (`--langue en`) |
| Classeur Excel | une feuille, celle du diagramme de flux |

Les deux trous sont ceux qu'on attend sur une base sans décisions : « nom et source de l'instrument » et « ce que mesure le groupe ». Le projet ne les dit pas, et l'outil ne les devine pas.

## 4. R et PSPP

| Vérification | Résultat |
|---|---|
| Script R maître (avec le script de préparation, exclusions comprises) | sans erreur, en 1,3 seconde |
| R : mêmes exclusions par règle, mêmes personnes gardées | oui |
| R : alpha recalculé sur les personnes gardées | même *n* ; écart de 4 × 10⁻¹⁶ |
| PSPP : script de préparation SPSS | sans erreur ni avertissement |
| PSPP : mêmes exclusions par règle | oui |

## 5. Une règle ajoutée après coup

Une septième règle, qui exclut des personnes, est ajoutée une fois le document produit :

1. `ddict resultats` refuse : « À confirmer avant de produire le document : … la Méthode (M) » ;
2. `ddict carnet lister` montre « M. Méthode — changée, à confirmer » ;
3. `ddict carnet confirmer --tout`, puis le document se produit.

Le carnet ne contient aucune des valeurs de texte de la base (chaînes d'au moins 6 caractères).

## Ce que montre l'essai

1. **Les six sortes de règles tiennent sur une vraie base**, avec des dates en texte, et les refus protègent les identifiants.
2. **Les effectifs du flux sont les mêmes partout** : dans l'outil, dans la ligne de commande, dans R et dans PSPP ; l'alpha de R est celui de l'outil.
3. **Aucun chiffre de la Méthode ne change sans une personne** : une règle ajoutée bloque le document jusqu'à sa confirmation.
4. **Les trous restent des trous** : ce que le projet ne dit pas (l'instrument, sa source, ce qu'il mesure) est signalé, jamais deviné.
