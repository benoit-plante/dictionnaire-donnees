# Essai : rattachement des variables aux questions (v0.2, étape 4)

**Date :** 2026-10-14
**Modèle :** qwen2.5:7b-instruct-q4_K_M (Ollama 0.35.1, contexte de 4 096 jetons par défaut), prompt `link-v1`, température 0.
**Commande :** `ddict rattacher projet.dd.json [--modele …]` (D-013).

## Base fictive (avec corrigé)

Le corrigé est `questionnaire_key()` du script de génération : 29 variables posées dans le questionnaire, 4 qui n'y sont pas (`id_participant`, `date_passation`, `vague`, `q_retiree`).

### Calcul seul, sans IA

| Base | Questionnaire | Bonne question en tête, sur les 29 variables posées |
|---|---|---|
| `.sav` (étiquettes) | PDF | 29 |
| `.sav` | texte | 29 |
| `.csv` (sans étiquettes) | PDF | 29 |
| `.csv` | texte | 29 |

Le calcul retrouve les énoncés de grille par la numérotation (`sommeil_q1`…`q8`, `anx1`…`anx7`), les options cochées (`aide_tcc`, et `aide_aucune` par l'ordre), et `taille_cm` malgré son ordre différent de celui du fichier. Il ne sait pas reconnaître une variable sans question : il propose toujours sa meilleure candidate, sauf pour `vague` (aucune). Un test automatique garde ce résultat.

### Choix par le modèle

| Base | Bons | Faux | Sans proposition |
|---|---|---|---|
| `.sav`, blocs de 12 | 31 / 33 | 1 (`genre` → une option au lieu de la question) | 1 (`vague`, sans candidate) |
| `.csv`, blocs de 12 | 31 / 33 | 0 | 2 (`vague`, `q_retiree`) |
| `.sav`, blocs de 6 | 30 / 33 | 2 (`date_passation`, `q_retiree`) | 1 |
| `.csv`, blocs de 6 | 30 / 33 | 1 (`date_passation`) | 2 |

Le modèle apporte ce que le calcul ne peut pas savoir : il répond souvent « aucune » pour l'identifiant et la date de passation. Il garde les bons choix du calcul sur tout le reste.

**Taille des messages.** Un bloc de 12 variables, 5 candidates chacune, fait 3 654 jetons, presque toute la fenêtre de 4 096 jetons d'Ollama : un questionnaire aux questions plus longues la dépasserait, et Ollama couperait le message sans rien dire. Les blocs de rattachement sont donc de **6 variables** par défaut, et le texte des questions est abrégé à 150 caractères dans les candidates (la réponse est un identifiant ; le texte complet reste lu dans le questionnaire).

## Base publique (sans corrigé)

152 variables, questionnaire SurveyMonkey de 80 questions ; glossaire : OCF et MF acceptés, DPJ et CIUSSS saisis comme le ferait l'équipe. Les fichiers restent hors du dépôt. Faute de corrigé, les rattachements ont été jugés un à un à la lecture du questionnaire.

| | |
|---|---|
| Durée | 1 min 50 s, 24 blocs de 6 variables, tous réussis |
| Rattachements justes | environ 94 sur 152 (62 %) |
| Sans question, et laissés sans proposition ou « aucune » à raison | 10 (scores calculés : K6, WEMWBS, GF6, CBCL…) |
| Faux | environ 48 |

Ce qui marche : les questions sociodémographiques, les options des questions à cocher (`motifs_non_freq_ocf_*`, `motivations_non_freq_ocf_*`, `ethnie_0001`…`0007`, `situation_professionnelle_*`), la série besoin / satisfaction / OCF des pages 9 à 14.

Ce qui échoue :

- **les questions répétées à l'identique** : « À quelle fréquence cette personne vous apporte-t-elle du soutien ? » revient six fois, une par source de soutien. Le modèle choisit presque toujours la première ;
- **des listes d'options presque pareilles** (professionnels du CIUSSS ou du privé) : l'option est souvent prise dans la mauvaise question ;
- les variables recodées ou calculées dont le nom ressemble à une question (`satisfaction_ocf`, `cbcl_score_emotional`).

Deux corrections ont été faites pendant l'essai :

- **Les options d'une question à choix unique ne sont plus candidates d'une variable isolée.** Le modèle choisissait « Oui » au lieu de la question elle-même (`service_dpj`). Elles restent candidates des séries et des familles, pour les questions à choix unique dont chaque option est une variable (`situation_professionnelle_*`).
- **Synonyme genre / sexe.** Le questionnaire demande « Quel est votre sexe ? ».

## Conclusion

Le rattachement par le modèle reste activé : il est juste sur la base fictive et sur la majorité de la base réelle, et chaque proposition est une proposition, avec le texte exact de la question sous les yeux de la personne. Les erreurs réelles sont des confusions entre questions voisines, faciles à voir et à corriger dans l'interface, où les candidates calculées sont en tête de liste.

Pour une version suivante : montrer au modèle la position des candidates dans le questionnaire, pour distinguer les questions répétées.
