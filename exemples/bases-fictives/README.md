# Bases fictives

Ces fichiers sont **entièrement inventés** : une étude fictive sur le sommeil, 200 participants fictifs, générée par `scripts/generer_bases_fictives.py` avec une graine fixe. Deux exécutions du script produisent exactement les mêmes fichiers ; un test le vérifie, et vérifie aussi que les fichiers déposés ici correspondent au script.

Pour les régénérer après une modification du script :

```
uv run python scripts/generer_bases_fictives.py
```

Licence : CC0 (domaine public).

## Fichiers

| Fichier | Ce qu'il imite |
|---|---|
| `etude-sommeil.sav` | Fichier SPSS avec étiquettes de variables et de valeurs, manquants déclarés, niveaux de mesure |
| `etude-sommeil.csv` | CSV ordinaire : UTF-8, virgule comme séparateur, point décimal |
| `etude-sommeil_excel-fr.csv` | Excel en français, « CSV (séparateur : point-virgule) » : Windows-1252, `;`, virgule décimale, fins de ligne Windows |
| `etude-sommeil_excel-utf8.csv` | Excel en français, « CSV UTF-8 » : comme le précédent, en UTF-8 avec marque d'ordre des octets |
| `questionnaire-sommeil.pdf` | Questionnaire de l'étude exporté d'une plateforme d'enquête : questions non numérotées, grilles en tableau dont les lignes longues sont coupées |
| `questionnaire-sommeil.txt` | Le même questionnaire copié depuis un traitement de texte : un paragraphe par ligne, tabulations entre les cellules des tableaux |

## Pièges volontaires

| Piège | Variables |
|---|---|
| Identifiants probables | `id_participant`, `courriel` |
| Quasi-identifiant | `date_naissance` |
| Texte libre (avec `;`, guillemets et saut de ligne) | `commentaire` |
| Items inversés | `sommeil_q3`, `sommeil_q6` |
| Code observé sans étiquette | `sommeil_q3` (9) |
| Valeurs sentinelles non déclarées | `age` (999), `nb_reveils` (-9) |
| Manquants déclarés dans SPSS | `anx1` à `anx7` (-9), `genre` (9) |
| Étiquette jamais utilisée | `satisfaction_globale` (99) |
| Petit effectif (< 5) | `genre` (3) |
| Variable constante | `vague` |
| Variable entièrement vide | `q_retiree` |
| Colonnes en double | `heures_sommeil`, `heures_sommeil_2` |
| Types mélangés (nombres et « NSP ») | `taille_cm` |
| Variable sans étiquette | `sommeil_q7` |
| Échelle non contiguë | `anx1` à `anx4`, puis `anx5` à `anx7` plus loin |
| Nombres décimaux | `heures_sommeil` |
| Question à cocher : une variable par option (1 ou vide) | `aide_medicament`, `aide_naturel`, `aide_tcc`, `aide_aucune` |
| Variantes d'écriture d'une même réponse (casse, accents) | `langue_maison` : « Français », « français », « Francais » ; « Anglais », « anglais » |
| Variantes rares, à ne jamais révéler (< 5 chacune) | `langue_maison` : « Créole » (3), « créole » (2) |

## Pièges du questionnaire

Le rattachement attendu de chaque variable à sa question est donné par `questionnaire_key()` dans le script.

| Piège | Où |
|---|---|
| Question à cocher : chaque option correspond à une variable | « Qu'utilisez-vous pour vous aider à dormir ? » → `aide_*` |
| Grilles (énoncés en lignes, réponses en colonnes) | `sommeil_q1` à `sommeil_q8`, `anx1` à `anx7` |
| Sigles définis dans le texte | QFS, EFA, TCC (« thérapie cognitivo-comportementale (TCC) ») |
| Sigle dans un nom de variable | `aide_tcc` |
| Libellé connu seulement par le questionnaire | `sommeil_q7`, sans étiquette dans le fichier |
| Question sans variable | « Acceptez-vous de participer à cette étude ? » |
| Variables sans question | `id_participant`, `date_passation`, `vague`, `q_retiree` |
| Une question, deux variables | `heures_sommeil`, `heures_sommeil_2` |
| Ordre différent de celui du fichier | `taille_cm`, demandée en page 2 mais placée vers la fin du fichier |
| Page de consentement avec les coordonnées de l'équipe | témoin `ZQXQUEST`, qui ne doit apparaître dans aucun export (D-012) |

Les identifiants, les courriels et les commentaires contiennent des **chaînes témoins** (`ZQXID`, `zqxmail`, `ZQXTXT`) : un test de confidentialité échoue si l'une d'elles apparaît dans un message destiné au modèle, dans un fichier projet ou dans un export.
