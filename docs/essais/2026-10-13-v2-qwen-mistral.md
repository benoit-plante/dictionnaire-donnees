# Essai du 2026-10-13 : prompt variables-v2, Qwen 2.5 7B et Mistral 7B

Suite de l'essai `2026-10-13-qwen2.5-7b.md`, après D-009 : le modèle ne propose plus que des libellés et des descriptions. Base fictive `etude-sommeil.sav` (29 variables), données entièrement fictives.

## Conditions

| Élément | Qwen | Mistral |
|---|---|---|
| Modèle Ollama | `qwen2.5:7b-instruct-q4_K_M` (4,7 Go) | `mistral:latest` (4,4 Go) |
| Prompt, paramètres | `variables-v2`, température 0, graine 42, blocs de 12 | idem |
| Matériel | RTX 5060 Laptop, 8 Go ; Ollama 0.35.1 | idem |
| Blocs acceptés au premier essai | 3 sur 3 | 3 sur 3 |
| Durée | 53 s (123 s avec v1) | 86 s |
| Signaux d'invention | aucun | aucun |

## Qwen 2.5 7B : nettement mieux qu'avec v1

- Libellés justes et concis : « Réveils nocturnes » (accent rétabli), « Énergie matin », « Difficulté à se relaxer », « Heures de sommeil moyennes ».
- Descriptions courtes et prudentes, souvent avec l'échelle (« sur une échelle de 0 à 3 »).
- Reste un accent oublié : « Sommeil reparateur ».
- Laisse vides les identifiants et `q_retiree` : prudent, conforme à la consigne.
- **Défaut persistant :** `sommeil_q7`, sans étiquette dans le fichier, reprend encore le libellé de sa voisine (« Routine sommeil »), malgré la consigne.

## Mistral 7B : à écarter

- **Erreurs graves :** `date_passation` devient « Date de décès » ; `sommeil_q6` (somnolence) devient « Sommeil jour ».
- **Chiffres inventés :** la description de `genre` annonce « 2 % de hommes », alors que cet effectif est masqué.
- Descriptions qui répètent les statistiques (« entre 18 et 999 ans et une moyenne de 59,1 ans ») ou les consignes (« probablement non transmis »).
- Fautes de français (« la sommeil journalière ») et accents oubliés (« Age »).

## Conclusions

1. Qwen 2.5 7B, avec `variables-v2`, est le modèle à recommander pour la v0.1 sur une carte de 8 Go.
2. Mistral 7B n'est pas recommandé : ses erreurs sont plausibles, donc faciles à valider par mégarde.
3. La consigne « ne reprends pas le libellé d'une variable voisine » ne suffit pas. L'outil signale désormais tout libellé proposé pour une variable sans étiquette dans le fichier (`label:no_file_label`), à vérifier dans le questionnaire.
4. Piste pour un prompt v3 : interdire les chiffres dans les descriptions.
