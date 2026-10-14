# Essai : questions répétées et listes d'options semblables (v0.3, étape 6)

**Date :** 2026-10-14
**Modèle :** qwen2.5:7b-instruct-q4_K_M (Ollama), prompt `link-v2`.

## Le problème

L'essai de l'étape 4 de la v0.2 (`2026-10-14-rattachement.md`) avait relevé deux confusions sur la base publique :

- **une même question répétée** : « À quelle fréquence cette personne vous apporte du soutien ? » revient six fois, une par source de soutien (autre parent, conjoint·e, famille…) ;
- **des listes d'options semblables** : les professionnels consultés au CIUSSS et en pratique privée.

Dans les deux cas, ce qui distingue les questions est **la question qui les précède** (« Votre conjoint·e », « Avez-vous reçu des services d'un professionnel en pratique privée ? »).

## Changements

1. **Calcul des candidates** : les mots de la question précédente comptent, avec un poids de 0,4, entre celui de la question elle-même (0,5) et celui des paragraphes de la page (0,2). La rareté d'un mot se mesure maintenant sur les mots propres des questions seulement, pour que ce contexte ne fasse pas paraître un mot courant (« satisfaction »).
2. **Message au modèle** (prompt `link-v2`) : chaque candidate porte sa page, et, **seulement pour une question répétée ou une question de suivi** (« Si oui, … »), la question qui la précède (`after`). Donner `after` pour toutes les candidates a d'abord été essayé : le modèle s'en trouvait détourné ailleurs (par exemple `besoin_finance_ocf` rattaché à « Avez-vous besoin d'aide… » au lieu de la question sur les OCF). Le prompt explique `after` avec un exemple inventé.

## Mesure sur la base publique

Corrigé établi à la main pour les 27 variables difficiles : 13 variables `soutien_*` et 14 `type_service_ciusss_*` ou `type_service_prive_*`. Les fichiers restent hors du dépôt.

| | Avant | Après |
|---|---|---|
| Calcul seul, bonne question en tête | 5 / 27 | 10 / 27 |
| Bonne question parmi les candidates | 15 / 27 | 19 / 27 |
| Choix du modèle | 9 / 27 | 14 / 27 |

Ailleurs (les 125 autres variables), d'après ma lecture : environ 6 rattachements meilleurs (`lien_enfant`, `date_immigration`, `motifs_freq_ocf_repit`, `besoin_finance`, `ethnie_other`…) et environ 4 moins bons (`besoin_emotionel_ocf`, `soutien_social_moyen` et `_pondere`, scores calculés désormais rattachés à une option, `satisfaction_int_score`). **Gain net : environ 7 rattachements justes de plus sur 152.** Le modèle varie d'un essai à l'autre sur les cas limites ; l'écart est modeste et doit être lu ainsi.

Ce qui reste difficile : `soutien_autre_parent` est attiré par une grille du questionnaire qui parle aussi de « l'autre parent » ; les questions de suivi dont la bonne option n'est pas parmi les 5 candidates.

## Base fictive

Pas de recul : le modèle trouve 31 / 34 (`.sav`) et 30 / 34 (`.csv`) ; le calcul seul 32 / 34. `q_retiree`, qui n'a pas de question, n'a plus de fausse candidate.

## Signal « étendue observée »

Une proposition qui présente le minimum et le maximum observés comme les bornes d'une échelle (« Mesure le niveau de détresse sur une échelle de 0 à 21 », pour un K6 qui va de 0 à 24) est maintenant signalée : « présente l'étendue observée comme celle de l'échelle : à vérifier dans le manuel ». Pas de signal quand les étiquettes de valeurs définissent les codes, ni quand une étendue théorique est déjà documentée avec sa source. Sur les textes de l'essai du prompt v3, les trois cas relevés (K6, GF6, CBCL) sont signalés, et « âge de 18 à 75 ans » ne l'est pas.
