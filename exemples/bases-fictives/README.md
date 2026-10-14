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

## Autres formats (v0.2)

La même base existe en Stata (`etude-sommeil.dta`, avec étiquettes et étiquettes de valeurs), en Excel (`etude-sommeil.xlsx`, sans étiquettes) et en SAS (`etude-sommeil.sas7bdat`, étiquettes de variables seulement). Les manquants déclarés de SPSS (−9, 9) y sont des valeurs ordinaires, comme dans le CSV. Le fichier SAS est écrit par `scripts/generer_sas.R` (R et le paquet haven), à relancer après `generer_bases_fictives.py` si la base change : un test le signale.

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

## Seconde base fictive : enquête auprès de familles (v0.4)

`enquete-familles.csv` (150 familles fictives, 30 variables) et son questionnaire `questionnaire-familles.pdf` (et `.txt`), écrits par `scripts/generer_enquete_familles.py` (graine fixe). Elle diffère volontairement de l'étude sur le sommeil, sur laquelle l'outil a été réglé : le banc d'essai des modèles la mesure sur un questionnaire qu'il n'a jamais vu. Le corrigé est dans le script : `answer_key()` (question de chaque variable) et `TRUE_VALUE_LABELS` (sens réel des codes).

**Corrigé du banc d'essai** : `corrige-banc.json`, écrit par `scripts/generer_corrige_banc.py` à partir des corrigés des deux générateurs, donne la question de chaque variable des deux bases (`etude-sommeil.csv` et `enquete-familles.csv`) telle que l'outil la nomme (`Q7.r3`, `Q10.o2`, ou `none`). Ce fichier, les deux CSV et les deux questionnaires PDF sont inclus dans le paquet installé (`ddict/banc/`), pour que `ddict evaluer` fonctionne sans le dépôt.

| Piège | Où |
|---|---|
| CSV exporté par R : aucune étiquette, cases manquantes écrites `NA` | toute la base |
| Question répétée mot pour mot, une fois par source de soutien | « À quelle fréquence cette personne vous apporte-t-elle du soutien ? » → `soutien_*_freq` |
| Questions de suivi (« Si oui, … ») à cocher, une variable par option | `type_garde_*` après `garde_utilise`, `pro_clsc_*` après `clsc_consulte` |
| Sigles définis dans le questionnaire | CPE, CLSC, EFSP |
| Sigles dans les noms | `type_garde_cpe`, `clsc_consulte`, `pro_clsc_ts` |
| Grille codée de 0 à 4 ; échelle de 0 à 10 | `stress_1` à `stress_6` ; `satisfaction_vie_familiale` |
| Codes qui ne suivent pas l'ordre des options (recodage alphabétique) : les étiquettes proposées d'après les options seraient fausses | `langue_maison` (1 = Anglais, 2 = Autre, 3 = Français) |
| Variables sans question (identifiant, date, score calculé) | `id_famille`, `date_reponse`, `stress_total` |
| Identifiant et texte libre | `id_famille` (témoin `ZQXFAMID`), `commentaire` (témoin `ZQXFAMTXT`) |
| Page de consentement avec les coordonnées de l'équipe, coupée après un deux-points dans le PDF | témoin `ZQXFAMQUEST` |
