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

## Version anglaise de l'étude sur le sommeil (v0.5)

`sleep-study.sav`, `sleep-study.csv` et `questionnaire-sleep.pdf` (et `.txt`), écrits par `scripts/generer_base_anglaise.py` : les mêmes 200 participants fictifs que `etude-sommeil` (même graine, mêmes valeurs), pour une étude menée en anglais. Noms de variables, libellés, étiquettes de valeurs, réponses en texte libre et questionnaire sont en anglais ; le questionnaire a la structure du questionnaire français, question pour question. Le corrigé est `answer_key()` dans le script.

| Différence avec la version française | Où |
|---|---|
| Sigles définis en anglais | FSQ, FAS, CBT (« Cognitive behavioural therapy (CBT) ») |
| Variantes d'écriture par la casse seulement | `home_language` : « French », « french », « FRENCH » |
| Questions sans les mots des noms de variables | `age` (« How old are you? »), `height_cm` (« How tall are you… »), `n_awakenings` (« wake up ») : le calcul seul ne les trouve pas |
| Grille du PDF lisible | les options de Q7, plus courtes, ne se collent pas comme en français |
| Témoin de la page de consentement | `ZQXQUESTEN` |


## Export SurveyMonkey fictif, en deux vagues (v0.7)

Une étude fictive sur la vie au travail, exportée comme le fait SurveyMonkey, écrite par `scripts/generer_base_surveymonkey.py` (graine fixe). Elle reproduit les conventions observées dans deux vrais exports, sans rien en reprendre : tous les énoncés sont inventés. Le corrigé `corrige-surveymonkey.json` donne la structure de chaque variable, les groupes, les rattachements, les noms attendus et les écarts entre les vagues.

| Fichier | Ce qu'il imite |
|---|---|
| `travail-t1_surveymonkey.sav` | Vague 1, export brut, noms de plateforme anciens (`RespondentID`, `StartDate`…) |
| `travail-t2_surveymonkey.sav` | Vague 2, export brut, noms de plateforme récents (`respondent_id`, `date_created`…) |
| `travail-t1_surveymonkey.xlsx` | Vague 1, export Excel : en-tête sur deux lignes, colonnes de plateforme titrées à l'ancienne (« Respondent ID »), réponses en texte |
| `travail-t2_surveymonkey.xlsx` et `.csv` | Vague 2, export Excel et CSV : en-tête sur deux lignes, colonnes de plateforme titrées par les noms récents (`respondent_id`), réponses en texte |
| `questionnaire-travail.txt` | Questionnaire de la vague 2 copié dans un traitement de texte, questions numérotées |
| `questionnaire-travail.pdf` | Le même, mis en page comme un PDF de SurveyMonkey : questions non numérotées, titres de colonnes des grilles sur plusieurs lignes |
| `questionnaire-travail-numerote.pdf` | Le même PDF, questions numérotées (« 1. », « 2. »…) |
| `travail-t1-documente.sav` | Vague 1 telle que l'équipe l'a laissée : renommée (`eft_1_t1`…), codes 6 et 7 déclarés manquants pour la grille du milieu de travail |
| `travail-t1-correspondance.csv` | Table des noms de la vague 1 (`nom_origine,nouveau_nom`, D-052) |

| Piège | Où (vague 2) |
|---|---|
| Variables de la plateforme en tête, dont des identifiants (témoin `ZQXSMID`) et des dates de passation en texte (`A22` ou `A100`) | `CollectorNm` à `custom_1` |
| Questions nommées par leur rang, énoncés et options par le leur | `q0001`, `q0003_0004`, `q0005_other` |
| Questions simples au préfixe commun `q` : ce n'est pas une échelle | `q0001`, `q0002`, `q0006`, `q0007` |
| Grille d'échelle de Likert, niveau `scale`, une série d'étiquettes par item | `q0003_0001` à `q0003_0012` |
| Item contenant le verbe « identifier » | `q0003_0005` |
| Items inversés (une situation satisfaisante) | `q0003_0002`, `q0003_0007`, `q0003_0011` |
| « Ne sais pas » (6) et « Préfère ne pas répondre » (7) non déclarés manquants | `q0004_0001` à `q0004_0005` |
| Trois ensembles à cocher (une étiquette `1 = option`, non coché = vide), chacun avec « autre » : une case de plus dans le `.sav` (`q0005_0006`), absente de l'export Excel, et un texte étiqueté en anglais (`q0005_other`) | `q0005`, `q0008`, `q0010` |
| Cases à cocher annoncées sans « toutes » (« Cochez les… », « Coche les… ») | `q0008`, `q0010` |
| Questions ouvertes (témoin `ZQXSMTXT`) | `q0009`, `q0011` |
| Variable texte finale étiquetée `id` : code de famille et initiales inventées | `q0012` |
| Page d'information avec les coordonnées de l'équipe | témoin `ZQXSMQUEST` |

| Écart entre les vagues | Où |
|---|---|
| Question ajoutée en vague 2, qui décale la numérotation `qNNNN` | `q0002` (ancienneté) |
| Item retiré de la grille de Likert | 10ᵉ item de la vague 1 (`q0002_0010`) |
| Étiquette de valeur changée | `q0007` : « Plus de deux » devient « Trois ou plus » |

## Base de contrôle SurveyMonkey (v0.7)

`trajets_surveymonkey.sav` (et `.xlsx`), `questionnaire-trajets.txt` et le corrigé `corrige-controle-surveymonkey.json`, écrits par `scripts/generer_controle_surveymonkey.py` (graine fixe) : une étude fictive en anglais sur les trajets domicile-travail, mesurée une seule fois avant les corrections qu'elle a fait trouver (`docs/essais/2026-10-15-controle-surveymonkey.md`). Elle contient des types de questions que les deux exports réels de l'essai n'avaient pas : coordonnées, choix unique avec « autre », classement, curseur, zones de texte, grille avec colonne de commentaire, grille de menus déroulants. **Pour ces types, les conventions de SurveyMonkey sont supposées, pas observées** : la base vérifie que l'outil échoue proprement là où il ne sait pas.
