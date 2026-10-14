# Essai : trois modèles au banc d'essai (v0.4, étape 7)

**Date :** 2026-10-14
**Outil :** dictionnaire-donnees 0.3.0 (développement de la v0.4), `ddict evaluer`, prompts `link-v2` et `variables-v3`.
**Poste :** Windows 11, carte graphique NVIDIA, Ollama. Les durées sont celles de ce poste, avec la carte graphique ; elles ne valent pas pour un ordinateur sans carte graphique, qui n'a pas été mesuré ici.

## Modèles

| Modèle | Taille sur le disque | Licence |
|---|---|---|
| `qwen2.5:3b-instruct` | 1,9 Go | Qwen Research (usage de recherche) |
| `qwen2.5:7b-instruct-q4_K_M` | 4,7 Go | Apache-2.0 |
| `mistral:latest` (7B) | 4,4 Go | Apache-2.0 |

Le modèle de 3B a été téléchargé pour cet essai, avec l'accord de l'auteur ; l'outil lui-même ne télécharge rien.

## Résultats

Sur les deux bases fictives (64 variables, corrigé connu). Le calcul seul (sans modèle) trouve 59 / 64.

| | qwen2.5 3B | qwen2.5 7B | mistral 7B |
|---|---|---|---|
| Rattachements justes | 46 / 64 | **54 / 64** | 23 / 64 |
| Blocs de rattachement en échec | 0 | 0 | 5 (réponses aux mauvais noms) |
| Libellés signalés : étendue observée | 4 | 0 | 11 |
| Libellés signalés : sens de codes sans étiquette | 4 | 3 | 0 |
| Citations, seuils, instruments, sigles | 0 | 0 | 0 |
| Durée totale du banc | 1 min 05 s | 1 min 56 s | 4 min 02 s |

Ce que cachent les chiffres :

- **Sens de codes.** Avec qwen2.5 3B, `langue_maison` reçoit « 1 = français, 2 = anglais, 3 = autre » : c'est le piège de la base des familles, recodée par ordre alphabétique (1 = Anglais) ; et une échelle de cinq degrés est inventée pour `soutien_partenaire`, qui est un oui ou non. Avec qwen2.5 7B, les trois cas (`genre`, `sommeil_q1`, `satisfaction_globale`) reprennent les options du questionnaire dans l'ordre supposé : vraisemblables, mais non vérifiés, et signalés à bon droit.
- **mistral** renvoie, pour les grilles, d'autres noms de variables que ceux demandés : l'outil refuse ces réponses (`names_mismatch`), d'où ses rattachements manqués. Ses descriptions présentent souvent l'étendue observée comme celle de l'échelle.
- **Le calcul seul fait mieux que chaque modèle sur ces deux bases**, dont les questionnaires sont simples. Sur la base publique, où des questions se répètent à l'identique, le modèle avait fait mieux que le calcul sur les cas difficiles (14 / 27 contre 10 / 27, essai du 2026-10-14 sur les questions répétées). Le modèle aide surtout sur les questionnaires longs et répétitifs.
- Une même mesure refaite varie d'un ou deux rattachements (54 et 55 / 64 pour qwen2.5 7B).

## Recommandation

| Matériel | Modèle |
|---|---|
| Carte graphique (au moins 6 Go de mémoire vidéo) | **qwen2.5 7B** (`qwen2.5:7b-instruct-q4_K_M`), le modèle recommandé par défaut. |
| Sans carte graphique, au moins 8 Go de mémoire | **qwen2.5 3B** (`qwen2.5:3b-instruct`) est utilisable, plus rapide, mais il se trompe plus souvent de rattachement et donne plus volontiers un sens aux codes : révisez chaque proposition. Sa licence (Qwen Research) restreint l'usage commercial ; un usage de recherche est permis. |
| Tout ordinateur | **Sans modèle** : le calcul seul propose déjà les questions candidates, et la révision reste possible. |

mistral 7B n'est pas recommandé avec les prompts actuels.

Chacun peut refaire cette mesure sur son ordinateur : page « IA locale », **Mesurer ce modèle**, ou `ddict evaluer --modele …`.
