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

## Après : version 0.6 (étape 6, 2026-10-14)

Mesurée une seule fois après les étapes 3 à 5, sans aucun réglage sur cette base. Pour juger de la variation du modèle, trois passages de la 0.6 et trois de la 0.5.0 (extraite à part de l'historique, `git worktree`), même modèle, même poste.

| Rattachements justes | 0.5.0 | 0.6 |
|---|---|---|
| Modèle, passage 1 | 17 / 23 | 20 / 23 |
| Modèle, passage 2 | 17 / 23 | 20 / 23 |
| Modèle, passage 3 | 17 / 23 | 20 / 23 |
| Calcul seul | 15 / 23 | 16 / 23 |

- **Gagnés** : `horodatage` et `score_motivation` (« aucune question » proposée, D-039 : date de passation, et somme exacte des items de l'Échelle fictive de motivation), `remarques`.
- **Encore manqués** : `poids_kg` (« Combien pesez-vous ? ») et `taille_m` (« Combien mesurez-vous ? ») : le calcul leur trouve des candidates, mais pas la bonne, et les questions voisines (D-040) ne s'appliquent qu'aux variables sans candidate ; `vague`, variable constante, reste sans proposition.
- Libellés : 22 variables enrichies sur 23, aucun signalement, comme avec la 0.5.

**Conclusion** : la 0.6 fait mieux que la 0.5 sur une base qui n'a servi à aucun réglage (20 contre 17 sur 23, stable sur trois passages). Conformément à D-042, la base de contrôle rejoint ensuite le banc d'essai.
