# Essai : un questionnaire fictif dans LimeSurvey Cloud 7.6 (v0.20, étapes A2 et E2)

Le 2026-10-19, sur l'instance LimeSurvey Cloud de l'auteur (version 7.6.0), avec son accord : un questionnaire **entièrement fictif** a été écrit au format texte à colonnes, importé, réexporté (`.lss` et `.txt`), activé, rempli de cinq réponses inventées (dont une incomplète), puis ses réponses exportées en CSV (codes, puis textes), en Excel et en SPSS (`.sav`). Les fichiers restent **hors du dépôt**, sur le poste de l'auteur : le `.lss` et le `.txt` exportés portent le courriel de l'administrateur et l'adresse de l'instance. Ce document ne garde que les conventions observées ; `scripts/generer_limesurvey_fictif.py` les reproduira pour les tests (étape A1).

## Le questionnaire

Deux groupes, neuf questions, une de chaque nature : `genre` (liste à boutons `L`, obligatoire, avec « autre » ; codes 1, 2, 9), `age` (nombre `N`), `region` (liste déroulante `!`, codes 1 à 3), `journal` (date `D`), `profession` (texte court `S`) ; puis `intro` (texte d'affichage `X`), `sommeil` (tableau `F`, trois énoncés `SQ001` à `SQ003`, quatre réponses 1 à 4, consigne dans l'aide), `aides` (cases à cocher `M`, deux options `SQ001` et `SQ002`, avec « autre »), `nuit` (texte long `T`).

## Le format texte à colonnes (`.txt`)

- **Trois essais d'importation**, deux ratés :
  1. sans `id` : un seul groupe, les questions du second groupe fondues dans le premier ;
  2. avec un `id` à chaque groupe et question, mais les deux groupes au même `type/scale` : même résultat ;
  3. avec `type/scale` 1 et 2 : deux groupes, neuf questions, dix réponses, cinq sous-questions, sans avertissement.
- **La cause, lue dans le code de LimeSurvey** (`application/helpers/admin/import_helper.php`, `TSVImportSurvey`) : pour une ligne `G`, `type/scale` est le **numéro du groupe** ; deux lignes `G` au même numéro sont le même groupe dans deux langues.
- **Colonnes de la version 7.6** : 151, dans cet ordre en tête : `id`, `related_id`, `class`, `type/scale`, `name`, `relevance`, `text`, `help`, `language`, `validation`, `mandatory`, **`encrypted`**, `other`, `default`, `same_default`, **`question_theme_name`**, `same_script`, puis les attributs avancés par ordre alphabétique. Le manuel en ligne ne nomme ni `encrypted` ni `question_theme_name`.
- **L'export** n'a pas de signature UTF-8 (le manuel en annonce une) ; un texte qui contient une espace est entre guillemets.
- **Un code de question ne peut contenir que des lettres et des chiffres** : `aides_sommeil` est devenu `aidessommeil` à l'importation, avec un avertissement.
- **Les options d'une question à cases à cocher sont des sous-questions** (`SQ`), comme les énoncés d'un tableau ; seuls les choix d'une liste ou les colonnes d'un tableau sont des réponses (`A`), rattachées par leur position sous la question (et par l'`id` de la question à l'export).
- **Thèmes donnés par LimeSurvey** à l'importation : `listradio` (`L`), `list_dropdown` (`!`), `multiplechoice` (`M`), `arrays/array` (`F`), `shortfreetext` (`S`), `longfreetext` (`T`), `numerical` (`N`), `date` (`D`), `boilerplate` (`X`).

## Le `.lss`

- `DBVersion` 717 ; sections `answers`, `answer_l10ns`, `groups`, `group_l10ns`, `questions`, `subquestions`, `question_l10ns`, `surveys`, `surveys_languagesettings`, `surveys_groups`, `themes`, `themes_inherited`.
- Les textes sont dans les tables `*_l10ns`, reliés par `qid`, `aid` ou `gid` ; une réponse (`answers`) a `qid`, `code`, `sortorder`, `scale_id`.
- `question_order` a des trous (0, 1, 5, 8 dans le second groupe : l'importation du texte à colonnes compte aussi les sous-questions) : l'ordre se trie, il ne se compte pas.

## Les exports de réponses

| | CSV, en-têtes « code » | Excel | SPSS (`.sav`) |
|---|---|---|---|
| Variables de la plateforme | `id`, `submitdate`, `lastpage`, `startlanguage`, `seed`, `startdate`, `datestamp`, `quota_exit` | les mêmes | les mêmes |
| Question simple | `genre` | `genre` | `genre` |
| « Autre » d'un choix unique | `genre[other]` | `genre[other]` | `genre_other` |
| Énoncé d'un tableau | `sommeil[SQ001]` | `sommeil[SQ001]` | `sommeil_SQ001` |
| Option à cocher | `aides[SQ001]` | `aides[SQ001]` | `aides_SQ001` |
| « Autre » d'une question à cocher | `aides[other]` | `aides[other]` | `aides_other` |
| Texte d'affichage | `intro`, une colonne vide | idem | `intro`, `A1`, vide |

- **Codes** : l'option « autre » d'un choix unique est codée `-oth-` ; une case cochée vaut `Y`, une case non cochée est vide (export « codes ») ou « Non » (export « textes complets »), alors qu'une question non vue est vide dans les deux.
- **Le `.sav`** :
  - une question dont un code n'est pas un nombre (`-oth-`) devient une **chaîne** (`genre`, `A5`, étiquettes `'1'`, `'2'`, `'9'` et `'-oth-'` = « Other », en anglais) ;
  - une liste aux codes numériques reste numérique (`region`, `F1.0`, étiquettes) ;
  - une case à cocher est une chaîne avec les étiquettes `Y` = « Oui » et `0` = « Non sélectionné » ;
  - l'étiquette d'un énoncé est « [énoncé] question » ;
  - le niveau de mesure est `unknown` pour les questions à étiquettes, `nominal` pour les autres ;
  - aucun code manquant déclaré ;
  - **la date de soumission d'une réponse incomplète vaut 1582-10-14** (le zéro des dates de SPSS), au lieu d'être vide comme dans le CSV et l'Excel.
- **La réponse incomplète** : `submitdate` vide (CSV, Excel), `lastpage` = 1, les questions des pages non vues vides.
- **La date** (`journal`) : `2026-10-01 00:00:00` dans le CSV ; date et heure (`DATETIME20`) dans le `.sav` ; saisie au format `jj.mm.aaaa` dans le questionnaire.
- **CSV** : signature UTF-8, séparateur virgule, tout entre guillemets sauf les cases vraiment vides.

## Ce que l'outil en tire

1. **Le code d'une question LimeSurvey** est fait de lettres et de chiffres seulement : il ne peut pas être le radical des noms (D-146), qui a ses « _ ». À trancher (proposition à l'auteur) : le code LimeSurvey est le radical sans ses « _ » (`aidessommeil`), ou un code distinct, décidé à part.
2. **Le nom de colonne prévu** dépend du format d'export : `code[SQ001]` dans le CSV et l'Excel, `code_SQ001` dans le `.sav`. Les constantes supposées de `ddict.design` (`SEPARATOR = "_"`, `OTHER_CODE = "other"`) valent pour le `.sav` ; le CSV et l'Excel demandent la forme à crochets. Une case cochée vaut bien `Y` (`CHECKBOX_TYPE = "text"`), mais le `.sav` lui donne des étiquettes.
3. **Le texte d'affichage a une colonne** dans tous les exports : la variable prévue d'un texte d'affichage existe (vide), contrairement à ce que le § 6.3 du plan disait.
4. **Le fichier écrit par l'outil** doit donner un `id` à chaque groupe et question, et numéroter les groupes dans `type/scale`.
5. **À l'arrivée de la base** : une date de soumission à 1582-10-14 est une réponse incomplète, pas une date ; l'étiquette « Other » du `.sav` est en anglais ; « Non sélectionné » (`0`) n'apparaît jamais dans les données.
