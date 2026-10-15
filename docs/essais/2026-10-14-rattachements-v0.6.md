# Essai : des rattachements plus complets (v0.6)

**Bases :** les trois bases du banc d'essai (`etude-sommeil`, `enquete-familles`, `sleep-study`, 98 variables, corrigé connu). La base de contrôle est mesurée à part (`2026-10-14-base-controle.md`).
**Modèle :** qwen2.5:7b-instruct-q4_K_M (Ollama), sur le poste de développement.

## Référence, avant les changements (étape 2)

Version 0.5 avec le classement des rattachements manqués du banc :

| | Rattachements justes |
|---|---|
| Modèle | 82 / 98 |
| Calcul seul | 88 / 98 |

| Pourquoi le modèle manque | Nombre | Variables |
|---|---|---|
| Bonne question absente des candidates | 3 | `age`, `height_cm`, `n_awakenings` |
| Bonne candidate mal choisie | 4 | `sommeil_q7`, `pro_clsc_ts`, `soutien_partenaire`, `sleep_q8` |
| Variable sans question rattachée | 4 | `date_passation`, `date_reponse`, `id_famille`, `date_completed` |
| Sans proposition (variables sans question et sans candidate) | 5 | `q_retiree`, `vague`, `stress_total`, `q_removed`, `wave` |
| Choix justes du calcul défaits par le modèle | 3 | `sommeil_q7`, `soutien_partenaire`, `sleep_q8` |

(D'une exécution à l'autre, le modèle varie d'un ou deux rattachements : 81 et 82 / 98.)

## Après chaque étape

À compléter aux étapes 3 à 5.
