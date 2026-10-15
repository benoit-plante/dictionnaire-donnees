# Essai : la base de contrôle de la v0.6 (D-042)

**Base :** `etude-activite` (étude fictive française sur l'activité physique, 23 variables, corrigé `exemples/bases-fictives/corrige-controle.json`), générée par `scripts/generer_base_controle.py` avant toute mise au point de la v0.6, et mise de côté : elle n'entre pas dans le banc d'essai pendant la v0.6 et n'a servi à régler aucun changement.

**Modèle :** qwen2.5:7b-instruct-q4_K_M (Ollama), sur le poste de développement (carte graphique NVIDIA, 8 Go).

## Avant : version 0.5.0 (2026-10-14)

| | Rattachements justes |
|---|---|
| Modèle (prompt `link-v2`) | 17 / 23 |
| Calcul seul | 15 / 23 |

Manqués par le modèle : les trois variables administratives (`horodatage`, `vague`) et le score calculé (`score_motivation`), qui n'ont pas de question ; deux questions reformulées (`poids_kg` : « Combien pesez-vous ? », `taille_m` : « Combien mesurez-vous ? ») ; `remarques`.

Libellés : 22 variables enrichies sur 23, aucun signalement.

## Après : version 0.6

À mesurer une seule fois, à la fin de la v0.6 (étape 6), avec le même modèle.
