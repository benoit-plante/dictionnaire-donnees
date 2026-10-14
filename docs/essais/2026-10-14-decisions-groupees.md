# Essai : décisions groupées (v0.4, étape 5)

**Date :** 2026-10-14
**Modèle :** qwen2.5:7b-instruct-q4_K_M (Ollama), prompt `link-v2`, blocs de 6 variables.

## La question

Le bouton « Accepter les rattachements où le modèle et le calcul s'accordent » (D-029) ne retient que les rattachements où la proposition du modèle est aussi la première candidate du calcul. Combien de rattachements passent par ce bouton, et combien d'erreurs y passeraient si personne ne lisait l'aperçu ?

## Mesure

| Base | Variables | Proposés par le modèle | En accord (dans l'aperçu) | Dont faux | Hors accord | Dont justes |
|---|---|---|---|---|---|---|
| Étude du sommeil (fictive, CSV) | 34 | 32 | 30 | 1 | 2 | 0 |
| Enquête familles (fictive, CSV) | 30 | 29 | 27 | 3 | 2 | 0 |
| Base publique (152 variables) | 152 | 143 | 102 | environ 20 | 41 | — |

Pour les bases fictives, le décompte vient du corrigé. Pour la base publique, il n'y a pas de corrigé complet : les 102 lignes de l'aperçu ont été relues une à une, comme le ferait une personne ; environ 20 sont fausses, et quelques rattachements aux questions de soutien répétées n'ont pas pu être tranchés. Durée des propositions du modèle : 27 s pour la base du sommeil, 1 min 54 s pour la base publique, sur le poste de développement.

## Les erreurs qui passent par le bouton

- **Variables sans question** : identifiant (`id_famille`), dates de passation ou de réponse, rattachées à une question voisine (« Quelle est votre date de naissance ? »).
- **Scores calculés** (`soutien_social_moyen`, `cbcl_score_emotional`) rattachés à une option ou à un énoncé de grille.
- **Options de listes à cocher voisines** : professionnels du CIUSSS rattachés aux services de la DPJ, options d'une question de suivi rattachées à la question qui la précède (`type_service_prive_ts` → « Avez-vous reçu des services d'un professionnel en pratique privée ? »), deux variables rattachées à la même option.

## Un critère plus strict ?

Exiger en plus que le calcul préfère nettement sa première candidate (score au moins 1,2 fois celui de la deuxième) n'écarte pas assez d'erreurs : sur la base publique, il en reste 7 sur 20, mais 29 rattachements justes sortent de l'aperçu ; à 1,5, il en reste 6, et 56 justes sortent. Le critère de D-029 est gardé tel quel.

## Ce qui a changé

- L'aperçu le dit maintenant : à l'essai, environ un rattachement sur cinq de la liste était faux sur une vraie base, avec les trois cas ci-dessus ; il faut lire chaque ligne.
- Le gain reste net : sur la base publique, 102 décisions prises dans un seul aperçu, en décochant une vingtaine de lignes, au lieu de 102 décisions sur 102 pages.

## Temps de révision

Le temps qu'une personne met à relire l'aperçu n'a pas été mesuré ici ; il le sera lors de l'essai du guide par l'auteur (étape 8).
