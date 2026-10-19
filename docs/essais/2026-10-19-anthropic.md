# Essai : Haiku 5.5 et Sonnet 5.5 par une clé d'API (v0.18, étape D2)

**Date :** 2026-10-19. **Outil :** dictionnaire-donnees 0.17.0 et les étapes A à C de la v0.18 (commit `c911c79` et suivants). **Service :** l'interface Messages d'Anthropic, avec la clé de l'auteur, saisie par lui. **Bases :** les bases fictives du banc seulement (`etude-sommeil`, `enquete-familles`, `sleep-study`, `etude-activite` : 121 variables au corrigé ; l'export SurveyMonkey fictif pour les noms de base ; les 13 + 6 objectifs de la conseillère). Rien de réel n'a été envoyé.

**Réglages :** consignes de niveau 1 (`variables-v4`, `link-v2` et `link-v3`, `rename-v1`, `advise-v3`), blocs de 20 variables (rattachement) et de 25 (libellés), réflexion `low` puis `medium` ; aucun paramètre d'échantillonnage (le service les refuse). Un seul passage par réglage : d'un passage à l'autre, qwen2.5 7B variait d'un ou deux rattachements ; les écarts d'un ou deux points ci-dessous sont de cet ordre.

**Commandes :** `ddict evaluer --modele … --niveau-2` (réflexion `low`), `ddict evaluer --modele …` (réflexion `medium`), `scripts/banc_conseil.py` et `--suivi`.

## Résultats

### Rattachements aux questions (121 variables)

| | Justes | Choix justes du calcul défaits | Durée |
|---|---|---|---|
| Calcul seul | 110 / 121 | — | — |
| qwen2.5 7B (v0.6, essais du 2026-10-14) | 109 / 121 | — | — |
| Haiku 5.5, réflexion `low` | 110 / 121 | 5 | 23 s |
| Haiku 5.5, réflexion `medium` | **113 / 121** | 2 | 38 s |
| Sonnet 5.5, réflexion `low` | **113 / 121** | 2 | 31 s |
| Sonnet 5.5, réflexion `medium` | **113 / 121** | 2 | 24 s |

Les huit manqués des meilleurs passages sont les mêmes : des variables sans question (`q_retiree`, `q_removed`, `vague`, `wave`, laissées sans proposition), une question répétée (`heures_sommeil_2`, `sleep_hours_2`, pour lesquelles le modèle hésite et répond « incertain ») et `height_cm`, placée loin de sa question (piège voulu, hors des candidates). Avec la réflexion `low`, Haiku répond « incertain » pour trois items d'échelle (`anx5` à `anx7`) que le calcul choisissait juste ; la réflexion `medium` le corrige.

### Libellés et descriptions : niveau 1 et niveau 2

Signalements (citation, seuil, nom d'instrument, sens d'un sigle, étendue observée, sens de codes sans étiquette), sur les quatre bases :

| | Niveau 1 (outil) | Niveau 2 (banc seulement, avec les statistiques) |
|---|---|---|
| Haiku 5.5, `low` | 0 | 1 (sens de codes sans étiquette, `sleep-study`) |
| Sonnet 5.5, `low` | 0 | 7 (étendue observée : 1 dans `enquete-familles`, 6 dans `etude-activite`) |
| Haiku 5.5, `medium` | 0 | — |
| Sonnet 5.5, `medium` | 0 | — |

Variables enrichies : 118 à 120 / 121 selon le passage (une variable sans étiquette ni question reste parfois sans libellé, comme la consigne le demande). **Le niveau 1 ne perd rien de mesurable** ; le niveau 2 fait au contraire recopier aux modèles l'étendue observée des réponses dans leurs descriptions, ce que l'outil signale comme une invention possible. Le banc ne mesure pas la justesse d'un libellé (il n'a pas de corrigé pour cela) : à juger dans l'interface.

### Noms de base (export SurveyMonkey fictif, 10 questions)

| | Égaux au corrigé | Sigle possible signalé |
|---|---|---|
| Règles seules | 3 / 10 | — |
| qwen2.5 7B (essai du 2026-10-15) | 2 / 10 | 2 |
| Haiku 5.5, `low` | **7 / 10** | 1 |
| Haiku 5.5, `medium` | **7 / 10** | 0 |
| Sonnet 5.5, `low` et `medium` | 6 / 10 | 1 |

Pour la première fois, le modèle fait nettement mieux que les règles seules : la condition de D-051 pour offrir les radicaux dans l'interface est remplie.

### Conseillère (première proposition juste, variables comprises)

| | 13 objectifs | 6 objectifs (base de suivi) |
|---|---|---|
| qwen2.5 7B (`advise-v1` puis `advise-v2`) | 11 / 13, puis 10 / 13 | 4 / 6 |
| Haiku 5.5, `low` | **13 / 13** | **6 / 6** |
| Haiku 5.5, `medium` | 12 / 13 (13 / 13 parmi ses propositions) | **6 / 6** |
| Sonnet 5.5, `low` et `medium` | **13 / 13** | **6 / 6** |

Toutes les réponses sont valides ; aucune proposition n'est refusée par les conditions du codebook. Chaque réponse arrive en 1 à 10 secondes.

### Jetons et coût (prix publiés, lus le 2026-10-19)

| Passage | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|
| Banc, réflexion `low`, niveaux 1 et 2 (106 000 jetons en entrée) | 0,028 $ | 0,41 $ |
| Banc, réflexion `medium`, niveau 1 (73 000 jetons en entrée) | 0,022 $ | 0,26 $ |
| Conseillère, 19 objectifs, par réglage (67 000 jetons en entrée) | 0,010 $ à 0,012 $ | 0,18 $ |

Pour une base de 34 variables, les libellés coûtent environ 0,002 à 0,004 $ avec Haiku et 0,03 à 0,04 $ avec Sonnet ; le rattachement, du même ordre. La réflexion `medium` double à peu près les jetons de sortie de Haiku (pas ceux de Sonnet, qui réfléchit peu sur ces tâches). Coût total de l'essai, tests `externe` compris : environ 1,75 $, dont environ 0,60 $ pour des passages refaits (voir ci-dessous).

## Un incident pendant l'essai

Un premier passage « `medium` » a en fait tourné en `low` : le fichier de réglages, écrit par PowerShell 5.1 (`Set-Content -Encoding utf8`), commençait par une signature UTF-8, et l'outil le lisait comme absent. Corrigé dans la foulée : `ia.json` est maintenant lu même avec une signature (un Bloc-notes peut en ajouter une), et le rapport du banc dit ses paramètres (`effort`, `max_tokens`), pour qu'un tel écart se voie. Les chiffres ci-dessus sont ceux des passages refaits.

## Conclusions

1. **Les deux modèles font mieux que le modèle local partout**, et mieux que le calcul seul sur le rattachement (113 contre 110 / 121), les noms de base (7 contre 3 / 10) et la conseillère (13 / 13). Aucun libellé de niveau 1 n'est signalé.
2. **Haiku 5.5 avec la réflexion `medium` égale Sonnet 5.5** sur le rattachement et le dépasse sur les noms de base, pour environ un douzième du coût ; il manque un objectif de la conseillère au premier rang (le bon est parmi ses propositions). Avec la réflexion `low`, il défait trois choix justes du calcul en répondant « incertain ».
3. **Le niveau 1 suffit** (D-136) : le niveau 2 n'améliore aucun résultat mesuré et fait recopier l'étendue observée des réponses.
4. **La conseillère n'a plus besoin de la compression de D-080** avec Anthropic : le message entier (`advise-v3`) donne 13 / 13 et 6 / 6.
5. **Le nombre de candidates du rattachement** (5) n'est en cause que pour `height_cm`, piège voulu : rien ne justifie de l'augmenter.

Décisions à prendre par l'auteur : le modèle et la réflexion par défaut, les radicaux dans l'interface (D-051), le remplacement de D-080 pour Anthropic, le nombre de candidates.
