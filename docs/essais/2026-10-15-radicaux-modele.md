# Essai : radicaux des noms proposés par le modèle (v0.7, étape 10)

**Date :** 2026-10-15
**But :** décider, selon D-051, si la proposition des radicaux par le modèle local est offerte dans l'interface : elle ne l'est que si elle fait mieux que les règles seules.
**Base :** l'export SurveyMonkey fictif, vague 2 (`travail-t2_surveymonkey.sav`), avec l'en-tête de son export Excel comme questionnaire. 10 questions demandent un radical (les grilles prennent un préfixe donné par une personne, jamais par le modèle).
**Mesure :** `ddict.bench.run_naming`, aussi dans `ddict evaluer` ; Ollama sur le poste de développement, température 0. Rien de réel n'a été envoyé.
**Corrigé :** les radicaux qu'une équipe choisirait (`secteur`, `anciennete`, `taches`, `formation_sst`, `pauses`, `consignes_securite`, `situation_danger`, `transport`, `commentaires`, `id_participant`). « Égal au corrigé » est une mesure sévère : un radical différent peut être bon.

## Résultats

| | Radicaux valides | Égaux au corrigé | Proposés par le modèle | Sigle possible | Blocs en échec | Durée |
|---|---|---|---|---|---|---|
| Règles seules | 9 / 10 | 3 / 10 | — | — | — | — |
| qwen2.5 7B (`qwen2.5:7b-instruct-q4_K_M`) | 9 / 10 | 2 / 10 | 7 / 10 | 2 | 0 | 6 s |
| qwen2.5 3B (`qwen2.5:3b-instruct`) | 9 / 10 | 3 / 10 | 0 / 10 | 0 | 1 (réponse invalide) | 7 s |

| Question | Corrigé | Règles seules | qwen2.5 7B |
|---|---|---|---|
| q0001 | `secteur` | `secteur` | `secteur_travail` |
| q0002 | `anciennete` | `temps_emploi_actuel` | `duree_travail` |
| q0005 | `taches` | `taches_semaine` | `taches_semaine` |
| q0006 | `formation_sst` | `formation_sante` | `formation_sante_sect` |
| q0007 | `pauses` | `pauses_journee` | `pauses_jour` |
| q0008 | `consignes_securite` | `consignes_securite` | `consignes_securite` |
| q0009 | `situation_danger` | `situation_recente` | `situation_recente` |
| q0010 | `transport` | `moyens_transport` | `moyen_transport` |
| q0011 | `commentaires` | `commentaires` | `commentaires` |
| q0012 | `id_participant` | — | — |

## Un premier résultat écarté

Une première mesure donnait 6 / 10 au modèle. La consigne prenait alors pour exemple « taches » pour « Quelles tâches faites-vous ? », une question de la base mesurée : le modèle recopiait la réponse. Les exemples de la consigne parlent maintenant de loisirs, et les sigles à ne pas inventer sont « k6 », « phq9 », « stai », étrangers au corrigé. La consigne n'a pas été réglée davantage : sur une seule base de 10 questions, ce serait du réglage sur mesure.

## Décision (D-051)

Le modèle ne fait pas mieux que les règles seules : la proposition des radicaux par le modèle **n'est pas offerte dans l'interface**. Elle reste possible en ligne de commande (`ddict renommer --modele …`, à l'essai), et mesurée par `ddict evaluer`, pour qu'un autre modèle ou une autre consigne puisse la remettre en question sur de nouvelles bases.

Les radicaux des règles restent des propositions, que la personne corrige une fois par question sur la page « Noms ».
