# Data dictionary: etude-sommeil.sav

- File: `etude-sommeil.sav` (Etude sommeil (fictive))
- SHA-256 fingerprint: `a189e6bd7c313c8d06d56881042e0db32d66b9ecc1e48c3e06d36b0af7570f25`
- Rows: 200; variables: 34
- Version: final
- Codebook fingerprint: `9f7104d5e62e` (accepted decisions)
- Counts below 5 masked, as well as a second count when the first could be worked out by subtraction.
- Questionnaire: questionnaire-sommeil.txt
- SHA-256 fingerprint of the questionnaire: 307165d2eb4185449fdf95d1a387d5503aafbe76b789e743a50a6c26c300571c
- Variables linked to a question: 1

## Overview

| Type | Variables |
|---|---|
| date | 1 |
| date and time | 1 |
| decimal | 2 |
| empty | 1 |
| integer | 24 |
| mixed | 1 |
| text | 4 |

- Sensitive variables: 4 (`id_participant`, `courriel`, `date_naissance`, `commentaire`)
- Variables with flags: 14

## Glossary of acronyms

| Acronym | Definition | Origin | Status | Source |
|---|---|---|---|---|
| TCC | thérapie cognitivo-comportementale | Questionnaire | accepted | questionnaire-sommeil.txt |

## Groups of variables

### G1 — 8 items, codes from 1 to 5, prefix "sommeil_q"

- Variables: `sommeil_q1`, `sommeil_q2`, `sommeil_q3`, `sommeil_q4`, `sommeil_q5`, `sommeil_q6`, `sommeil_q7`, `sommeil_q8`
- Grouping clues: common prefix, same value labels, neighbouring variables
- Items probably reversed: `sommeil_q3`, `sommeil_q6`
- Observed Cronbach's alpha: 0.363 (150 complete rows); with the likely reversed items reversed: 0.912

### G2 — 7 items, codes from 0 to 3, prefix "anx"

- Variables: `anx1`, `anx2`, `anx3`, `anx4`, `anx5`, `anx6`, `anx7`
- Grouping clues: common prefix, same value labels
- Observed Cronbach's alpha: 0.85 (179 complete rows)

## Variables

### `id_participant` — Identifiant participant

- Type: text
- Measurement level: nominal
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Privacy: likely identifier (identifier name or label)
- Sensitive variable: no statistics on its values.

### `courriel` — Courriel

- Type: text
- Measurement level: nominal
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Privacy: likely identifier (identifier name or label, values in email format)
- Sensitive variable: no statistics on its values.

### `date_passation` — Date passation

- Type: date and time
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Dates: 2026-01-08T04:54:00 – 2026-06-03T14:02:00
- Distinct values: 200
- Privacy: ordinary

### `date_naissance` — DDN

- Type: date
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Privacy: quasi-identifier (date of birth name, dates spread over many years)
- Sensitive variable: no statistics on its values.

### `age` — Age

> Question (Q3): Quel âge avez-vous ?

- Type: integer
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Declared missing codes: 999 (confirmed by the team)
- Min 18; max 999; mean 59.105; standard deviation 117.449; median 46
- Distinct values: 58
- Privacy: ordinary

**Flags**

- Code 999 confirmed as missing by the team

### `genre` — Genre

- Type: integer
- Measurement level: nominal
- Valid: 196; empty cells: 0; declared missing: 4 (2%)
- Declared missing codes: 9
- Min 1; max 3; median 1
- Distinct values: 3
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Femme | 114 |  |
| 2 | Homme | masked |  |
| 3 | Autre identité | masked |  |
| 9 | Préfère ne pas répondre | 4 | yes |

### `vague` — Vague

- Type: integer
- Measurement level: nominal
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Min 1; max 1; mean 1; standard deviation 0; median 1
- Distinct values: 1
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Vague 1 | 200 |  |

**Flags**

- Constant variable

### `sommeil_q1` — Q1 endormissement

- Type: integer
- Measurement level: ordinal
- Valid: 194; empty cells: 6; declared missing: 0 (3%)
- Min 1; max 5; mean 2.8866; standard deviation 1.1729; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: 0.563)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 29 |  |
| 2 | Un peu | 41 |  |
| 3 | Moyennement | 64 |  |
| 4 | Beaucoup | 43 |  |
| 5 | Extrêmement | 17 |  |

### `sommeil_q2` — Q2 sommeil reparateur

- Type: integer
- Measurement level: ordinal
- Valid: 190; empty cells: 10; declared missing: 0 (5%)
- Min 1; max 5; mean 3.0947; standard deviation 1.1914; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: 0.577)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 18 |  |
| 2 | Un peu | 46 |  |
| 3 | Moyennement | 52 |  |
| 4 | Beaucoup | 48 |  |
| 5 | Extrêmement | 26 |  |

### `sommeil_q3` — Q3 reveils nocturnes

- Type: integer
- Measurement level: ordinal
- Valid: 191; empty cells: 9; declared missing: 0 (4.5%)
- Min 1; max 9; median 3
- Distinct values: 6
- Group: G1 (correlation with the rest of the group: -0.719)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | masked |  |
| 2 | Un peu | 45 |  |
| 3 | Moyennement | 55 |  |
| 4 | Beaucoup | 44 |  |
| 5 | Extrêmement | 25 |  |
| 9 |  | masked |  |

**Flags**

- Code 9 observed without a label
- Value 9 probably missing, not declared
- Item probably reversed (correlation with the rest of the scale: -0.719)

### `sommeil_q4` — Q4 satisf sommeil

- Type: integer
- Measurement level: ordinal
- Valid: 192; empty cells: 8; declared missing: 0 (4%)
- Min 1; max 5; mean 2.901; standard deviation 1.2132; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: 0.578)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 32 |  |
| 2 | Un peu | 37 |  |
| 3 | Moyennement | 59 |  |
| 4 | Beaucoup | 46 |  |
| 5 | Extrêmement | 18 |  |

### `sommeil_q5` — Q5 energie matin

- Type: integer
- Measurement level: ordinal
- Valid: 195; empty cells: 5; declared missing: 0 (2.5%)
- Min 1; max 5; mean 3.0103; standard deviation 1.197; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: 0.675)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 27 |  |
| 2 | Un peu | 36 |  |
| 3 | Moyennement | 61 |  |
| 4 | Beaucoup | 50 |  |
| 5 | Extrêmement | 21 |  |

### `sommeil_q6` — Q6 somnolence jour

- Type: integer
- Measurement level: ordinal
- Valid: 197; empty cells: 3; declared missing: 0 (1.5%)
- Min 1; max 5; mean 3.0711; standard deviation 1.1451; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: -0.727)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 10 |  |
| 2 | Un peu | 62 |  |
| 3 | Moyennement | 59 |  |
| 4 | Beaucoup | 36 |  |
| 5 | Extrêmement | 30 |  |

**Flags**

- Item probably reversed (correlation with the rest of the scale: -0.727)

### `sommeil_q7`

- Type: integer
- Measurement level: ordinal
- Valid: 195; empty cells: 5; declared missing: 0 (2.5%)
- Min 1; max 5; mean 2.959; standard deviation 1.205; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: 0.512)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 25 |  |
| 2 | Un peu | 45 |  |
| 3 | Moyennement | 63 |  |
| 4 | Beaucoup | 37 |  |
| 5 | Extrêmement | 25 |  |

### `sommeil_q8` — Q8 routine

- Type: integer
- Measurement level: ordinal
- Valid: 191; empty cells: 9; declared missing: 0 (4.5%)
- Min 1; max 5; mean 3.0209; standard deviation 1.1741; median 3
- Distinct values: 5
- Group: G1 (correlation with the rest of the group: 0.601)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 | Pas du tout | 20 |  |
| 2 | Un peu | 44 |  |
| 3 | Moyennement | 64 |  |
| 4 | Beaucoup | 38 |  |
| 5 | Extrêmement | 25 |  |

### `anx1` — ANX inquiet

- Type: integer
- Measurement level: ordinal
- Valid: 197; empty cells: 0; declared missing: 3 (1.5%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.3147; standard deviation 0.8586; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.619)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 3 | yes |
| 0 | Jamais | 37 |  |
| 1 | Parfois | 75 |  |
| 2 | Souvent | 71 |  |
| 3 | Presque toujours | 14 |  |

### `anx2` — ANX tendu

- Type: integer
- Measurement level: ordinal
- Valid: 197; empty cells: 0; declared missing: 3 (1.5%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.3452; standard deviation 0.8285; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.642)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 3 | yes |
| 0 | Jamais | 30 |  |
| 1 | Parfois | 84 |  |
| 2 | Souvent | 68 |  |
| 3 | Presque toujours | 15 |  |

### `anx3` — ANX controle inquietude

- Type: integer
- Measurement level: ordinal
- Valid: 198; empty cells: 0; declared missing: 2 (1%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.298; standard deviation 0.8592; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.64)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 2 | yes |
| 0 | Jamais | 38 |  |
| 1 | Parfois | 77 |  |
| 2 | Souvent | 69 |  |
| 3 | Presque toujours | 14 |  |

### `anx4` — ANX agite

- Type: integer
- Measurement level: ordinal
- Valid: 197; empty cells: 0; declared missing: 3 (1.5%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.3299; standard deviation 0.8735; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.575)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 3 | yes |
| 0 | Jamais | 36 |  |
| 1 | Parfois | 77 |  |
| 2 | Souvent | 67 |  |
| 3 | Presque toujours | 17 |  |

### `heures_sommeil` — Nb heures sommeil (moy)

- Type: decimal
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Min 3.5; max 9.7; mean 6.9945; standard deviation 1.0898; median 7.1
- Distinct values: 49
- Privacy: ordinary

### `heures_sommeil_2` — Nb heures sommeil (moy)

- Type: decimal
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Min 3.5; max 9.7; mean 6.9945; standard deviation 1.0898; median 7.1
- Distinct values: 49
- Privacy: ordinary

**Flags**

- Identical to heures_sommeil

### `nb_reveils` — Nb reveils / nuit

- Type: integer
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Min -9; max 5; median 1
- Distinct values: 7
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 |  | masked |  |
| 0 |  | 45 |  |
| 1 |  | 62 |  |
| 2 |  | 48 |  |
| 3 |  | 26 |  |
| 4 |  | 13 |  |
| 5 |  | masked |  |

**Flags**

- Value -9 probably missing, not declared

### `aide_medicament` — Aide sommeil: medicament

- Type: integer
- Measurement level: nominal
- Valid: 34; empty cells: 166; declared missing: 0 (83%)
- Min 1; max 1; mean 1; standard deviation 0; median 1
- Distinct values: 1
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 |  | 34 |  |

**Flags**

- Likely checkbox: only one value observed, empty cells probably mean "not checked"

### `aide_naturel` — Aide sommeil: produit naturel

- Type: integer
- Measurement level: nominal
- Valid: 41; empty cells: 159; declared missing: 0 (79.5%)
- Min 1; max 1; mean 1; standard deviation 0; median 1
- Distinct values: 1
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 |  | 41 |  |

**Flags**

- Likely checkbox: only one value observed, empty cells probably mean "not checked"

### `aide_tcc` — Aide sommeil: TCC

- Type: integer
- Measurement level: nominal
- Valid: 14; empty cells: 186; declared missing: 0 (93%)
- Min 1; max 1; mean 1; standard deviation 0; median 1
- Distinct values: 1
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 |  | 14 |  |

**Flags**

- Likely checkbox: only one value observed, empty cells probably mean "not checked"

### `aide_aucune` — Aide sommeil: aucune

- Type: integer
- Measurement level: nominal
- Valid: 130; empty cells: 70; declared missing: 0 (35%)
- Min 1; max 1; mean 1; standard deviation 0; median 1
- Distinct values: 1
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 1 |  | 130 |  |

**Flags**

- Likely checkbox: only one value observed, empty cells probably mean "not checked"

### `anx5` — ANX irritable

- Type: integer
- Measurement level: ordinal
- Valid: 198; empty cells: 0; declared missing: 2 (1%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.298; standard deviation 0.8473; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.655)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 2 | yes |
| 0 | Jamais | 34 |  |
| 1 | Parfois | 87 |  |
| 2 | Souvent | 61 |  |
| 3 | Presque toujours | 16 |  |

### `anx6` — ANX peur

- Type: integer
- Measurement level: ordinal
- Valid: 194; empty cells: 0; declared missing: 6 (3%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.2474; standard deviation 0.8084; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.583)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 6 | yes |
| 0 | Jamais | 36 |  |
| 1 | Parfois | 83 |  |
| 2 | Souvent | 66 |  |
| 3 | Presque toujours | 9 |  |

### `anx7` — ANX difficulte relaxer

- Type: integer
- Measurement level: ordinal
- Valid: 197; empty cells: 0; declared missing: 3 (1.5%)
- Declared missing codes: -9
- Min 0; max 3; mean 1.2995; standard deviation 0.8551; median 1
- Distinct values: 4
- Group: G2 (correlation with the rest of the group: 0.556)
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| -9 | Refus | 3 | yes |
| 0 | Jamais | 37 |  |
| 1 | Parfois | 78 |  |
| 2 | Souvent | 68 |  |
| 3 | Presque toujours | 14 |  |

### `satisfaction_globale` — Satisfaction globale 0-10

- Type: integer
- Measurement level: scale
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Min 0; max 10; median 6
- Distinct values: 11
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| 0 | Pas du tout satisfait | masked |  |
| 1 |  | masked |  |
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

**Flags**

- Label 99 never used

### `taille_cm` — Taille (cm)

- Type: mixed
- Measurement level: nominal
- Valid: 200; empty cells: 0; declared missing: 0 (0%)
- Distinct values: 43
- Privacy: ordinary

**Flags**

- Mixed types (7 non-numeric values)

### `q_retiree` — Question retiree v2

- Type: empty
- Measurement level: scale
- Valid: 0; empty cells: 200; declared missing: 0 (100%)
- Distinct values: 0
- Privacy: ordinary

**Flags**

- Entirely empty variable

### `langue_maison` — Langue maison

- Type: text
- Measurement level: scale
- Valid: 198; empty cells: 2; declared missing: 0 (1%)
- Distinct values: 8
- Privacy: ordinary

| Code | Label | Count | Declared missing |
|---|---|---|---|
| Anglais |  | 30 |  |
| Espagnol |  | 7 |  |
| Francais |  | 12 |  |
| Français |  | 110 |  |
| anglais |  | 9 |  |
| français |  | 25 |  |

**Flags**

- Spelling variants of the same answer: "Français", "français", "Francais"
- Spelling variants of the same answer: "Anglais", "anglais"
- 2 rare categories removed (privacy)

### `commentaire` — Commentaires

- Type: text
- Measurement level: nominal
- Valid: 60; empty cells: 140; declared missing: 0 (70%)
- Privacy: free text (free text name, long texts)
- Sensitive variable: no statistics on its values.
