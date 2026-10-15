# Dictionnaire de données : etude-sommeil.sav

- Fichier : `etude-sommeil.sav` (Etude sommeil (fictive))
- Empreinte SHA-256 : `a189e6bd7c313c8d06d56881042e0db32d66b9ecc1e48c3e06d36b0af7570f25`
- Lignes : 200 ; variables : 34
- Version : finale
- Empreinte du codebook : `3051f62d8cdc` (décisions acceptées)
- Effectifs inférieurs à 5 masqués, ainsi qu'un second effectif quand le premier pourrait être recalculé par soustraction.
- Questionnaire : questionnaire-sommeil.txt
- Empreinte SHA-256 du questionnaire : 307165d2eb4185449fdf95d1a387d5503aafbe76b789e743a50a6c26c300571c
- Variables rattachées à une question : 1

## Vue d'ensemble

| Type | Variables |
|---|---|
| date | 1 |
| date et heure | 1 |
| décimal | 2 |
| entier | 24 |
| mixte | 1 |
| texte | 4 |
| vide | 1 |

- Variables sensibles : 4 (`id_participant`, `courriel`, `date_naissance`, `commentaire`)
- Variables avec signalements : 14

## Glossaire des sigles

| Sigle | Définition | Origine | Statut | Source |
|---|---|---|---|---|
| TCC | thérapie cognitivo-comportementale | Questionnaire | validé | questionnaire-sommeil.txt |

## Groupes de variables

### G1 — 8 items, codes de 1 à 5, préfixe « sommeil_q »

- Variables : `sommeil_q1`, `sommeil_q2`, `sommeil_q3`, `sommeil_q4`, `sommeil_q5`, `sommeil_q6`, `sommeil_q7`, `sommeil_q8`
- Indices du regroupement : préfixe commun, mêmes étiquettes de valeurs, variables voisines
- Items probablement inversés : `sommeil_q3`, `sommeil_q6`
- Alpha de Cronbach observé : 0,363 (150 lignes complètes) ; avec les items probables inversés : 0,912

### G2 — 7 items, codes de 0 à 3, préfixe « anx »

- Variables : `anx1`, `anx2`, `anx3`, `anx4`, `anx5`, `anx6`, `anx7`
- Indices du regroupement : préfixe commun, mêmes étiquettes de valeurs
- Alpha de Cronbach observé : 0,85 (179 lignes complètes)

## Variables

### `id_participant` — Identifiant participant

- Type : texte
- Niveau de mesure : nominal
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Confidentialité : identifiant probable (nom ou étiquette d'identifiant)
- Variable sensible : aucune statistique sur ses valeurs.

### `courriel` — Courriel

- Type : texte
- Niveau de mesure : nominal
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Confidentialité : identifiant probable (nom ou étiquette d'identifiant, valeurs au format courriel)
- Variable sensible : aucune statistique sur ses valeurs.

### `date_passation` — Date passation

- Type : date et heure
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Dates : 2026-01-08T04:54:00 – 2026-06-03T14:02:00
- Valeurs distinctes : 200
- Confidentialité : ordinaire

### `date_naissance` — DDN

- Type : date
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Confidentialité : quasi-identifiant (nom de date de naissance, dates étalées sur de nombreuses années)
- Variable sensible : aucune statistique sur ses valeurs.

### `age` — Age

> Question (Q3) : Quel âge avez-vous ?

- Type : entier
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Codes manquants déclarés : 999 (confirmé par l'équipe)
- Min 18 ; max 999 ; moyenne 59,105 ; écart-type 117,449 ; médiane 46
- Valeurs distinctes : 58
- Confidentialité : ordinaire

**Signalements**

- Code 999 confirmé comme manquant par l'équipe

### `genre` — Genre

- Type : entier
- Niveau de mesure : nominal
- Valides : 196 ; cases vides : 0 ; manquants déclarés : 4 (2 %)
- Codes manquants déclarés : 9
- Min 1 ; max 3 ; médiane 1
- Valeurs distinctes : 3
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Femme | 114 |  |
| 2 | Homme | masqué |  |
| 3 | Autre identité | masqué |  |
| 9 | Préfère ne pas répondre | 4 | oui |

### `vague` — Vague

- Type : entier
- Niveau de mesure : nominal
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Min 1 ; max 1 ; moyenne 1 ; écart-type 0 ; médiane 1
- Valeurs distinctes : 1
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Vague 1 | 200 |  |

**Signalements**

- Variable constante

### `sommeil_q1` — Q1 endormissement

- Type : entier
- Niveau de mesure : ordinal
- Valides : 194 ; cases vides : 6 ; manquants déclarés : 0 (3 %)
- Min 1 ; max 5 ; moyenne 2,8866 ; écart-type 1,1729 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : 0,563)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 29 |  |
| 2 | Un peu | 41 |  |
| 3 | Moyennement | 64 |  |
| 4 | Beaucoup | 43 |  |
| 5 | Extrêmement | 17 |  |

### `sommeil_q2` — Q2 sommeil reparateur

- Type : entier
- Niveau de mesure : ordinal
- Valides : 190 ; cases vides : 10 ; manquants déclarés : 0 (5 %)
- Min 1 ; max 5 ; moyenne 3,0947 ; écart-type 1,1914 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : 0,577)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 18 |  |
| 2 | Un peu | 46 |  |
| 3 | Moyennement | 52 |  |
| 4 | Beaucoup | 48 |  |
| 5 | Extrêmement | 26 |  |

### `sommeil_q3` — Q3 reveils nocturnes

- Type : entier
- Niveau de mesure : ordinal
- Valides : 191 ; cases vides : 9 ; manquants déclarés : 0 (4,5 %)
- Min 1 ; max 9 ; médiane 3
- Valeurs distinctes : 6
- Groupe : G1 (corrélation avec le reste du groupe : -0,719)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | masqué |  |
| 2 | Un peu | 45 |  |
| 3 | Moyennement | 55 |  |
| 4 | Beaucoup | 44 |  |
| 5 | Extrêmement | 25 |  |
| 9 |  | masqué |  |

**Signalements**

- Code 9 observé sans étiquette
- Valeur 9 probablement manquante, non déclarée
- Item probablement inversé (corrélation avec le reste de l'échelle : -0,719)

### `sommeil_q4` — Q4 satisf sommeil

- Type : entier
- Niveau de mesure : ordinal
- Valides : 192 ; cases vides : 8 ; manquants déclarés : 0 (4 %)
- Min 1 ; max 5 ; moyenne 2,901 ; écart-type 1,2132 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : 0,578)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 32 |  |
| 2 | Un peu | 37 |  |
| 3 | Moyennement | 59 |  |
| 4 | Beaucoup | 46 |  |
| 5 | Extrêmement | 18 |  |

### `sommeil_q5` — Q5 energie matin

- Type : entier
- Niveau de mesure : ordinal
- Valides : 195 ; cases vides : 5 ; manquants déclarés : 0 (2,5 %)
- Min 1 ; max 5 ; moyenne 3,0103 ; écart-type 1,197 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : 0,675)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 27 |  |
| 2 | Un peu | 36 |  |
| 3 | Moyennement | 61 |  |
| 4 | Beaucoup | 50 |  |
| 5 | Extrêmement | 21 |  |

### `sommeil_q6` — Q6 somnolence jour

- Type : entier
- Niveau de mesure : ordinal
- Valides : 197 ; cases vides : 3 ; manquants déclarés : 0 (1,5 %)
- Min 1 ; max 5 ; moyenne 3,0711 ; écart-type 1,1451 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : -0,727)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 10 |  |
| 2 | Un peu | 62 |  |
| 3 | Moyennement | 59 |  |
| 4 | Beaucoup | 36 |  |
| 5 | Extrêmement | 30 |  |

**Signalements**

- Item probablement inversé (corrélation avec le reste de l'échelle : -0,727)

### `sommeil_q7`

- Type : entier
- Niveau de mesure : ordinal
- Valides : 195 ; cases vides : 5 ; manquants déclarés : 0 (2,5 %)
- Min 1 ; max 5 ; moyenne 2,959 ; écart-type 1,205 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : 0,512)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 25 |  |
| 2 | Un peu | 45 |  |
| 3 | Moyennement | 63 |  |
| 4 | Beaucoup | 37 |  |
| 5 | Extrêmement | 25 |  |

### `sommeil_q8` — Q8 routine

- Type : entier
- Niveau de mesure : ordinal
- Valides : 191 ; cases vides : 9 ; manquants déclarés : 0 (4,5 %)
- Min 1 ; max 5 ; moyenne 3,0209 ; écart-type 1,1741 ; médiane 3
- Valeurs distinctes : 5
- Groupe : G1 (corrélation avec le reste du groupe : 0,601)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 | Pas du tout | 20 |  |
| 2 | Un peu | 44 |  |
| 3 | Moyennement | 64 |  |
| 4 | Beaucoup | 38 |  |
| 5 | Extrêmement | 25 |  |

### `anx1` — ANX inquiet

- Type : entier
- Niveau de mesure : ordinal
- Valides : 197 ; cases vides : 0 ; manquants déclarés : 3 (1,5 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,3147 ; écart-type 0,8586 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,619)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 3 | oui |
| 0 | Jamais | 37 |  |
| 1 | Parfois | 75 |  |
| 2 | Souvent | 71 |  |
| 3 | Presque toujours | 14 |  |

### `anx2` — ANX tendu

- Type : entier
- Niveau de mesure : ordinal
- Valides : 197 ; cases vides : 0 ; manquants déclarés : 3 (1,5 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,3452 ; écart-type 0,8285 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,642)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 3 | oui |
| 0 | Jamais | 30 |  |
| 1 | Parfois | 84 |  |
| 2 | Souvent | 68 |  |
| 3 | Presque toujours | 15 |  |

### `anx3` — ANX controle inquietude

- Type : entier
- Niveau de mesure : ordinal
- Valides : 198 ; cases vides : 0 ; manquants déclarés : 2 (1 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,298 ; écart-type 0,8592 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,64)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 2 | oui |
| 0 | Jamais | 38 |  |
| 1 | Parfois | 77 |  |
| 2 | Souvent | 69 |  |
| 3 | Presque toujours | 14 |  |

### `anx4` — ANX agite

- Type : entier
- Niveau de mesure : ordinal
- Valides : 197 ; cases vides : 0 ; manquants déclarés : 3 (1,5 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,3299 ; écart-type 0,8735 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,575)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 3 | oui |
| 0 | Jamais | 36 |  |
| 1 | Parfois | 77 |  |
| 2 | Souvent | 67 |  |
| 3 | Presque toujours | 17 |  |

### `heures_sommeil` — Nb heures sommeil (moy)

- Type : décimal
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Min 3,5 ; max 9,7 ; moyenne 6,9945 ; écart-type 1,0898 ; médiane 7,1
- Valeurs distinctes : 49
- Confidentialité : ordinaire

### `heures_sommeil_2` — Nb heures sommeil (moy)

- Type : décimal
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Min 3,5 ; max 9,7 ; moyenne 6,9945 ; écart-type 1,0898 ; médiane 7,1
- Valeurs distinctes : 49
- Confidentialité : ordinaire

**Signalements**

- Identique à heures_sommeil

### `nb_reveils` — Nb reveils / nuit

- Type : entier
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Min -9 ; max 5 ; médiane 1
- Valeurs distinctes : 7
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 |  | masqué |  |
| 0 |  | 45 |  |
| 1 |  | 62 |  |
| 2 |  | 48 |  |
| 3 |  | 26 |  |
| 4 |  | 13 |  |
| 5 |  | masqué |  |

**Signalements**

- Valeur -9 probablement manquante, non déclarée

### `aide_medicament` — Aide sommeil: medicament

- Type : entier
- Niveau de mesure : nominal
- Valides : 34 ; cases vides : 166 ; manquants déclarés : 0 (83 %)
- Min 1 ; max 1 ; moyenne 1 ; écart-type 0 ; médiane 1
- Valeurs distinctes : 1
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 |  | 34 |  |

**Signalements**

- Case à cocher probable : une seule valeur observée, les cases vides veulent sans doute dire « non coché »

### `aide_naturel` — Aide sommeil: produit naturel

- Type : entier
- Niveau de mesure : nominal
- Valides : 41 ; cases vides : 159 ; manquants déclarés : 0 (79,5 %)
- Min 1 ; max 1 ; moyenne 1 ; écart-type 0 ; médiane 1
- Valeurs distinctes : 1
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 |  | 41 |  |

**Signalements**

- Case à cocher probable : une seule valeur observée, les cases vides veulent sans doute dire « non coché »

### `aide_tcc` — Aide sommeil: TCC

- Type : entier
- Niveau de mesure : nominal
- Valides : 14 ; cases vides : 186 ; manquants déclarés : 0 (93 %)
- Min 1 ; max 1 ; moyenne 1 ; écart-type 0 ; médiane 1
- Valeurs distinctes : 1
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 |  | 14 |  |

**Signalements**

- Case à cocher probable : une seule valeur observée, les cases vides veulent sans doute dire « non coché »

### `aide_aucune` — Aide sommeil: aucune

- Type : entier
- Niveau de mesure : nominal
- Valides : 130 ; cases vides : 70 ; manquants déclarés : 0 (35 %)
- Min 1 ; max 1 ; moyenne 1 ; écart-type 0 ; médiane 1
- Valeurs distinctes : 1
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 1 |  | 130 |  |

**Signalements**

- Case à cocher probable : une seule valeur observée, les cases vides veulent sans doute dire « non coché »

### `anx5` — ANX irritable

- Type : entier
- Niveau de mesure : ordinal
- Valides : 198 ; cases vides : 0 ; manquants déclarés : 2 (1 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,298 ; écart-type 0,8473 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,655)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 2 | oui |
| 0 | Jamais | 34 |  |
| 1 | Parfois | 87 |  |
| 2 | Souvent | 61 |  |
| 3 | Presque toujours | 16 |  |

### `anx6` — ANX peur

- Type : entier
- Niveau de mesure : ordinal
- Valides : 194 ; cases vides : 0 ; manquants déclarés : 6 (3 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,2474 ; écart-type 0,8084 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,583)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 6 | oui |
| 0 | Jamais | 36 |  |
| 1 | Parfois | 83 |  |
| 2 | Souvent | 66 |  |
| 3 | Presque toujours | 9 |  |

### `anx7` — ANX difficulte relaxer

- Type : entier
- Niveau de mesure : ordinal
- Valides : 197 ; cases vides : 0 ; manquants déclarés : 3 (1,5 %)
- Codes manquants déclarés : -9
- Min 0 ; max 3 ; moyenne 1,2995 ; écart-type 0,8551 ; médiane 1
- Valeurs distinctes : 4
- Groupe : G2 (corrélation avec le reste du groupe : 0,556)
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| -9 | Refus | 3 | oui |
| 0 | Jamais | 37 |  |
| 1 | Parfois | 78 |  |
| 2 | Souvent | 68 |  |
| 3 | Presque toujours | 14 |  |

### `satisfaction_globale` — Satisfaction globale 0-10

- Type : entier
- Niveau de mesure : échelle
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Min 0 ; max 10 ; médiane 6
- Valeurs distinctes : 11
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| 0 | Pas du tout satisfait | masqué |  |
| 1 |  | masqué |  |
| 2 |  | 6 |  |
| 3 |  | 16 |  |
| 4 |  | 25 |  |
| 5 |  | 32 |  |
| 6 |  | 42 |  |
| 7 |  | 38 |  |
| 8 |  | 22 |  |
| 9 |  | 9 |  |
| 10 | Tout à fait satisfait | 8 |  |
| 99 | Ne sait pas | 0 |  |

**Signalements**

- Étiquette 99 jamais utilisée

### `taille_cm` — Taille (cm)

- Type : mixte
- Niveau de mesure : nominal
- Valides : 200 ; cases vides : 0 ; manquants déclarés : 0 (0 %)
- Valeurs distinctes : 43
- Confidentialité : ordinaire

**Signalements**

- Types mélangés (7 valeurs non numériques)

### `q_retiree` — Question retiree v2

- Type : vide
- Niveau de mesure : échelle
- Valides : 0 ; cases vides : 200 ; manquants déclarés : 0 (100 %)
- Valeurs distinctes : 0
- Confidentialité : ordinaire

**Signalements**

- Variable entièrement vide

### `langue_maison` — Langue maison

- Type : texte
- Niveau de mesure : échelle
- Valides : 198 ; cases vides : 2 ; manquants déclarés : 0 (1 %)
- Valeurs distinctes : 8
- Confidentialité : ordinaire

| Code | Étiquette | Effectif | Manquant déclaré |
|---|---|---|---|
| Anglais |  | 30 |  |
| Espagnol |  | 7 |  |
| Francais |  | 12 |  |
| Français |  | 110 |  |
| anglais |  | 9 |  |
| français |  | 25 |  |

**Signalements**

- Variantes d'écriture d'une même réponse : « Français », « français », « Francais »
- Variantes d'écriture d'une même réponse : « Anglais », « anglais »
- 2 catégories rares retirées (confidentialité)

### `commentaire` — Commentaires

- Type : texte
- Niveau de mesure : nominal
- Valides : 60 ; cases vides : 140 ; manquants déclarés : 0 (70 %)
- Confidentialité : texte libre (nom de texte libre, textes longs)
- Variable sensible : aucune statistique sur ses valeurs.
