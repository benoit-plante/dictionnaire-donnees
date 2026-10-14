# Essai : une étude menée en anglais (v0.5, étape 5)

**Date :** 2026-10-14
**Outil :** développement de la v0.5, `ddict evaluate`, prompts `link-v2.en` et `variables-v3.en` (traduction fidèle des prompts français, sans règle ni exemple ajoutés).
**Poste :** Windows 11, carte graphique NVIDIA (8 Go), Ollama.
**Base :** `sleep-study`, version anglaise de l'étude fictive sur le sommeil (mêmes participants, noms, étiquettes, réponses et questionnaire en anglais), 34 variables, corrigé connu.

## Résultats

| | qwen2.5 7B | qwen2.5 3B | Calcul seul |
|---|---|---|---|
| Rattachements justes, étude anglaise | 27 / 34 | 26 / 34 | 29 / 34 |
| Rattachements justes, même étude en français | 30 / 34 | 25 / 34 | 32 / 34 |
| Libellés signalés, étude anglaise | 1 (étendue observée) | 3 (sens de codes) | — |
| Libellés signalés, même étude en français | 3 (sens de codes) | 1 (étendue observée) | — |

Les libellés et descriptions proposés en anglais sont corrects et fidèles aux questions (« Trouble controlling worries », « Whether cognitive behavioural therapy (CBT) is used to help sleep »). Aucune citation, aucun seuil ni nom d'instrument inventé.

## Ce que l'essai apprend

- **Le modèle ne peut pas combler ce que le calcul ne propose pas.** Trois variables de l'étude anglaise ont une question qui n'emploie pas les mots de leur nom : `age` (« How old are you? »), `height_cm` (« How tall are you, in centimetres? »), `n_awakenings` (« How many times do you wake up… »). Le calcul ne trouve pour elles aucune question candidate ; or le modèle choisit seulement parmi les candidates (D-013). Il ne peut donc pas les rattacher, en anglais comme en français. Une personne le fait dans l'interface, où la liste montre toutes les questions. Une piste pour une version future : donner au modèle, pour une variable sans candidate, les questions voisines dans l'ordre du questionnaire.
- **Le reste se comporte comme en français** : mêmes types d'erreurs (variables sans question, une option de liste à cocher), mêmes ordres de grandeur ; qwen2.5 7B reste meilleur que le 3B, qui donne plus volontiers un sens aux codes (`gender`, `wave`, `sleep_q1`).
- **Les signaux d'invention reconnaissent maintenant les formes anglaises** : « threshold », un nom d'instrument écrit à l'anglaise (« Beck Depression Inventory »), sauf s'il figure au glossaire accepté par l'équipe ; « Smith (2019) » et « on a scale from 0 to 10 » l'étaient déjà.

## Recommandation

Inchangée : qwen2.5 7B avec une carte graphique, qwen2.5 3B sans, en anglais comme en français.
