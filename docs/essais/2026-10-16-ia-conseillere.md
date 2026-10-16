# Essai : l'IA conseillère propose des analyses du catalogue (v0.9, étape 7)

**Date :** 2026-10-16

**But :** mesurer si un modèle local, guidé par le catalogue et la liste des variables, propose la bonne analyse et les bonnes variables pour un objectif écrit en une phrase (D-073, D-079).

## Protocole

- **Base :** la base fictive des analyses (`etude-analyses.sav`), son échelle de bien-être cotée comme le dit son corrigé (score `bienetre_total`, groupe G1).
- **Objectifs :** 13 objectifs écrits d'avance dans `exemples/bases-fictives/objectifs-analyses.json`, chacun avec l'analyse et les variables attendues : 2 tests t, 2 ANOVA, 2 khi-carrés, 3 corrélations (dont une avec une variable ordinale, où Spearman est attendue), 1 régression, 2 Tableaux 1, et 1 objectif hors catalogue (des mesures répétées dans le temps, que la base ne contient pas), pour lequel aucune proposition n'est attendue.
- **Message :** consigne `advise-v1`, l'objectif tel quel, le catalogue, les 19 variables utilisables (nom, libellé, niveau de mesure, groupe) ; ni valeur, ni statistique. L'identifiant est exclu. Environ 5 500 caractères.
- **Réponse :** schéma strict, au plus trois propositions ; variables énumérées dans le schéma.
- **Modèles :** qwen2.5 7B (q4_K_M) et qwen2.5 3B, Ollama 0.35.1 sur ce poste (contexte de 4 096 jetons), température et graine fixes de l'outil.
- **Mesure (`scripts/banc_conseil.py`) :** la première proposition a-t-elle la bonne analyse ? Est-elle juste, variables comprises ? Une des propositions est-elle juste ? Les lignes et les colonnes d'un khi-carré, comme les variables d'une corrélation, comptent comme un ensemble. Le banc a été lancé deux fois ; les deux passages donnent les mêmes résultats.
- **Confidentialité :** métadonnées seulement ; rien ne quitte le poste.

## Résultats

| | qwen2.5 7B | qwen2.5 3B |
|---|---|---|
| Réponses valables (schéma et noms respectés) | 13 sur 13 | 10 sur 13 |
| Première proposition : bonne analyse | 11 sur 13 | 4 sur 13 |
| Première proposition juste, variables comprises | **11 sur 13** | 3 sur 13 |
| Une des propositions juste | 12 sur 13 | 5 sur 13 |
| Propositions que les conditions du codebook signalent | 1 | 2 |
| Temps par objectif | 5 à 11 s | 4 à 12 s |

### Les écarts du 7B

- **« Le stress augmente-t-il avec le nombre d'heures de travail ? »** Il propose d'abord une régression du stress sur les heures, puis la corrélation attendue. La régression est défendable : la formulation « augmente avec » suggère un sens.
- **L'objectif hors catalogue** (suivre le stress de chaque personne sur trois temps) : il propose une ANOVA du stress selon le groupe, qui ne répond pas à la question. Le modèle dit rarement qu'aucune analyse ne convient : la personne doit le juger.
- **La variable ordinale** (fréquence de l'activité physique et stress) : la bonne corrélation, mais avec la méthode de Pearson ; la page affiche alors l'avertissement « variable ordinale ; la corrélation de Spearman convient mieux ». Sa seconde proposition, un khi-carré entre le sport et le stress (une variable continue), est signalée par les conditions du codebook.
- Il choisit parfois Student plutôt que Welch, la méthode par défaut du catalogue ; la personne peut la changer avant de lancer l'analyse.

### Le 3B

Il confond les rôles (une variable continue comme variable de groupe, un rôle « outcome » donné au Tableau 1, refusé par l'outil), répète la même proposition et propose souvent un test t sur le groupe de l'étude quel que soit l'objectif. Trois réponses sur treize sont refusées par la validation.

## Ce que montre l'essai

1. **Le 7B est un conseiller utile** sur des objectifs simples : la bonne analyse et les bonnes variables 11 fois sur 13 au premier rang, et toujours dans le schéma. Le 3B ne l'est pas ; le 7B reste le modèle recommandé.
2. **Les garde-fous servent** : aucune analyse, variable ou méthode inventée n'est passée (refusées par la validation chez le 3B) ; les conditions du codebook ont signalé les propositions inadaptées ; rien n'est calculé sans la personne.
3. **La personne garde le jugement** : le modèle propose une analyse même quand aucune ne convient, et choisit parfois une méthode moins adaptée. C'est le rôle des avertissements de la page et de la phrase « à vérifier ».
4. **Limite :** le message grandit avec le nombre de variables ; avec un contexte de 4 096 jetons, une base de plus de 150 variables environ risque de le dépasser. À vérifier sur une vraie base (étape 8).
