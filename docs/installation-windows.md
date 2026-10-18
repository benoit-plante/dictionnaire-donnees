# Installer et utiliser l'outil sous Windows

Ce guide s'adresse aux personnes qui ne programment pas. Il mène de l'installation jusqu'à un codebook complet, produit à partir de la base fictive et de son questionnaire, fournis avec l'outil. Tout se fait par des doubles-clics et dans la fenêtre de l'outil ; aucune commande n'est à taper. Comptez une heure, plus le téléchargement du modèle d'IA si vous choisissez de l'utiliser.

In English: [`en/installation-windows.md`](en/installation-windows.md).

## Ce qu'il faut

- Windows 10 ou 11. Pas besoin de droits d'administrateur.
- Une connexion Internet **pendant l'installation seulement**. Ensuite, l'outil ne communique plus avec Internet : il lit vos fichiers et écrit ses résultats sur votre ordinateur.
- Pour l'IA, facultative : environ 5 Go d'espace libre et 16 Go de mémoire vive (8 Go suffisent, en plus lent). Une carte graphique accélère le travail, mais n'est pas nécessaire ; sans elle, un modèle plus petit est conseillé (section 6).

## 1. Installer

1. Téléchargez l'archive de l'outil depuis la page des versions du projet sur GitHub : le lien **Source code (zip)**, par exemple `dictionnaire-donnees-0.8.0.zip`.
2. Dans l'Explorateur, clic droit sur le fichier téléchargé, **Extraire tout**, puis **Extraire**. Ouvrez le dossier extrait ; s'il ne contient qu'un seul dossier du même nom, ouvrez celui-là : c'est **le dossier de l'outil**, avec `installer.bat`, `docs` et `exemples`.
3. Double-cliquez sur **`installer.bat`**.
   - Si Windows affiche « **Windows a protégé votre ordinateur** », cliquez sur **Informations complémentaires**, puis **Exécuter quand même**. Ce message apparaît pour tout programme téléchargé qui n'est pas signé par un éditeur payant ; l'installateur est un simple script, lisible dans le dossier `windows`.
4. Une fenêtre s'ouvre et suit quatre étapes : uv (le gestionnaire de Python, installé dans votre dossier d'utilisateur), l'outil (une ou deux minutes la première fois), les icônes, puis l'IA locale. Un avertissement en anglais sur le « PATH » peut s'afficher : c'est normal, l'installateur s'en occupe.
5. À l'étape de l'IA, répondez par `o` (oui) ou `n` (non) :
   - si Ollama n'est pas installé, l'installateur propose d'ouvrir sa page de téléchargement ; installez-le, puis relancez `installer.bat` ;
   - si Ollama est installé mais pas le modèle recommandé, il propose de le télécharger (environ 4,7 Go, une seule fois).

   Vous pouvez répondre non et y revenir plus tard : l'outil fonctionne sans IA.
6. « Installation terminée » : appuyez sur Entrée pour fermer la fenêtre. Une icône **Dictionnaire de données** est sur votre bureau et dans le menu Démarrer.

## 2. Ouvrir l'outil

Double-cliquez sur l'icône **Dictionnaire de données**. Après quelques secondes, l'outil s'ouvre dans sa propre fenêtre, sur l'**accueil**. C'est une page locale (adresse `http://127.0.0.1`), accessible depuis votre ordinateur seulement.

**Pour arrêter l'outil, fermez sa fenêtre**, ou cliquez **Quitter l'outil** en bas de la barre latérale. Vos décisions sont enregistrées au fur et à mesure : rien n'est perdu. Un nouveau double-clic sur l'icône pendant que l'outil tourne ouvre une fenêtre de plus.

Si la fenêtre ne peut pas s'ouvrir (sur un ordinateur sans le moteur d'Edge, par exemple), l'outil s'ouvre dans votre navigateur et fonctionne de la même façon ; arrêtez-le alors avec **Quitter l'outil**.

**Langue** : en haut de l'accueil, **Français · English** choisit la langue de l'interface. Le choix s'applique aussitôt et reste mémorisé sur votre ordinateur.

## 3. Premier codebook, à partir de la base fictive

La base fictive est une petite étude inventée sur le sommeil (200 participants fictifs), avec son questionnaire. Elle permet d'essayer l'outil sans aucune donnée réelle.

1. Sur l'accueil, sous **Nouveau projet**, cliquez sur **Choisir une base…**. La fenêtre « Ouvrir » de Windows apparaît (si vous ne la voyez pas, regardez dans la barre des tâches). Allez dans le dossier de l'outil, puis `exemples\bases-fictives`, et choisissez `etude-sommeil.sav`.
2. Cliquez sur **Créer le projet**. L'outil lit la base et crée à côté d'elle le **fichier projet**, `etude-sommeil.dd.json`. Il contient tout ce que l'outil a calculé (types, manquants, modalités, étiquettes) et, plus tard, vos décisions ; il ne contient pas les réponses individuelles des participants. Le fichier de données n'est jamais modifié.
3. La page **Base** résume ce qui a été lu : nombre de variables et de lignes, variables sensibles, signalements. Elle indique aussi la **langue de l'étude** (celle du questionnaire et des libellés), devinée par l'outil et modifiable : le modèle écrit ses propositions dans cette langue.
4. Dans la barre latérale, choisissez **Export**, puis **Écrire le codebook et le rapport**. Deux fichiers apparaissent à côté du projet : `etude-sommeil.xlsx` (le codebook, à ouvrir avec Excel) et `etude-sommeil.md` (le même contenu en texte). Le bouton **Ouvrir le dossier** les montre dans l'Explorateur.

Votre premier codebook est fait, sans IA : tout ce qu'il contient a été calculé exactement à partir du fichier. Les sections suivantes l'enrichissent ; on peut s'arrêter à n'importe laquelle et exporter.

En haut de la barre latérale, le **tableau de bord** dit ce qui attend, dans l'ordre recommandé (« Ajouter le questionnaire de l'étude », « Sigles à valider : 3 »…). Chaque ligne est un bouton qui mène à la bonne page. Le bouton **Accueil** ramène à l'accueil, où vos **projets récents** se rouvrent en un clic.

## 4. Ajouter le questionnaire

Le questionnaire de l'étude dit ce que chaque variable veut dire : le texte exact des questions, le sens des sigles, les options de réponse. L'outil le lit sans IA, en PDF (export de SurveyMonkey, LimeSurvey, REDCap…) ou en texte (`.txt` copié depuis Word).

1. Page **Questionnaire** (ou « Ajouter le questionnaire » dans le tableau de bord) : **Choisir le questionnaire…**, puis `questionnaire-sommeil.pdf` dans `exemples\bases-fictives`, et **Lire le questionnaire**.
2. L'outil affiche le nombre de questions trouvées, les questions à vérifier (par exemple une grille dont les titres de colonnes sont collés), les **sigles définis dans le questionnaire** (« thérapie cognitivo-comportementale (TCC) ») et les sigles des noms de variables qui n'ont pas de définition. **Questions trouvées** les montre toutes.
3. Page **Glossaire** : acceptez, corrigez ou rejetez chaque sigle trouvé, et ajoutez ceux qui manquent (ici, ANX : « anxiété »). **L'IA ne définit jamais un sigle** : c'est là qu'elle se trompe le plus, et le glossaire vient seulement du questionnaire et de vous.

Le texte du questionnaire reste dans le fichier projet ; seules les questions rattachées à des variables iront dans le codebook, jamais la page de consentement.

## 5. Relier les variables aux questions

Chaque variable vient d'une question, d'un énoncé de grille ou d'une option d'une question à cocher ; ou d'aucune (un identifiant, une date de passation, un score calculé).

- **Sans IA** : page **Variables**, filtre **Sans question**. Sur la fiche de chaque variable, la section **Question du questionnaire** propose une liste où les questions candidates calculées par l'outil sont en tête ; choisissez, puis **Rattacher**.
  - Pour un identifiant, une date de passation ou un score qui est la somme exacte des items d'une grille, « **Aucune question du questionnaire** » vient en tête : l'outil la juge probable, mais c'est à vous de décider.
  - Certaines questions n'emploient pas les mots du nom de la variable (« Combien pesez-vous ? » pour `poids_kg`). Quand l'outil ne trouve aucune candidate, il place en tête les **questions voisines**, celles qui se trouvent à cet endroit du questionnaire, entre les questions déjà sûres qui l'entourent ; un court texte le rappelle sous la liste.
- **Avec l'IA** (section 6) : le modèle choisit parmi les candidates, puis vous acceptez, corrigez ou rejetez chaque choix, de la même façon. Quand le calcul est sûr de son choix et que le modèle en choisit un autre, la proposition du modèle est gardée mais signalée (« s'écarte du choix sûr du calcul ») : comparez avec la première question de la liste. Ces rattachements ne sont pas repris dans les décisions groupées.

Quand le fichier n'a pas d'étiquettes de valeurs (un CSV, par exemple), l'outil propose « 1 = Pas du tout … 5 = Extrêmement » d'après les options de la question rattachée, seulement dans les cas sûrs. La mention « **ordre supposé, à vérifier** » est sérieuse : vérifiez l'ordre des codes dans votre plateforme d'enquête ou votre script de recodage avant d'accepter. Une base recodée peut avoir 0 = « Autre » là où le questionnaire place « Autre » en dernier.

## 6. Facultatif : l'IA locale

L'IA propose des rattachements aux questions, puis des libellés et des descriptions plus lisibles que les noms de variables. Elle tourne sur votre ordinateur, avec le logiciel libre **Ollama**. Le modèle ne reçoit jamais les réponses des participants, seulement des informations résumées (noms, étiquettes, proportions, questions). Chaque proposition attend votre décision.

**Quel modèle ?** (essai du 2026-10-14, `docs/essais/2026-10-14-trois-modeles.md`) : avec une carte graphique d'au moins 6 Go, **qwen2.5 7B** (`ollama pull qwen2.5:7b-instruct-q4_K_M`, 4,7 Go). Sans carte graphique, **qwen2.5 3B** (`ollama pull qwen2.5:3b-instruct`, 1,9 Go) est plus rapide mais se trompe plus souvent : révisez chaque proposition ; sa licence restreint l'usage commercial. On peut aussi se passer de modèle : le calcul seul propose déjà les questions candidates.

1. Page **IA locale** : l'outil vérifie qu'Ollama répond et montre le modèle choisi. S'il manque quelque chose, la page explique quoi faire ; l'outil ne télécharge jamais de modèle lui-même.
2. **Rattachement aux questions** : **Voir exactement ce qui serait envoyé** montre les messages, sans rien envoyer. Puis **Faire proposer : rattachement aux questions**. Une barre de progression avance bloc par bloc.
3. **Révisez les rattachements** (page Variables, filtre « À réviser » ; ou le tableau de bord) avant d'aller plus loin. L'ordre compte : pour les libellés, le modèle reçoit le texte des questions dont vous avez accepté le rattachement, et le sens des sigles que vous avez acceptés. Un rattachement faux lui donnerait une fausse question.
4. **Libellés et descriptions** : **Faire proposer : libellés et descriptions**, puis révisez-les.

Pendant un travail, **Arrêter** (ou un changement de page) l'interrompt après le bloc en cours. Les blocs terminés sont enregistrés ; relancez pour continuer là où il s'était arrêté. Comptez environ une minute pour la base fictive avec une carte graphique, plusieurs minutes sans.

**Banc d'essai des modèles** (en bas de la même page, ou `ddict evaluer --modele …`) : pour choisir un modèle, **Mesurer ce modèle** l'essaie sur les bases fictives de l'outil (trois en français, une en anglais), dont on connaît les bonnes réponses ; la quatrième, une étude fictive sur l'activité physique, a servi à vérifier la version 0.6 sans aucun réglage. Le rapport dit combien de rattachements sont justes (et ceux du calcul seul, pour comparer), combien de libellés ou de descriptions contiennent peut-être une invention (citation, seuil, nom d'instrument, sens d'un sigle, étendue, sens de codes sans étiquette) et la durée. Vos données ne sont pas utilisées. Le rapport est écrit à côté du projet (`banc-essai-<modèle>-<date>.md`) et peut être téléchargé. Environ trois minutes avec une carte graphique.

## 7. Réviser

- **Variables** : le filtre (« À réviser », « Avec signalements », « Sensibles », « Sans question », « Toutes ») et la liste des variables. Sur chaque fiche : ce que dit le fichier, ce qui a été calculé, la question rattachée, et chaque proposition à **Accepter**, **Rejeter**, ou corriger puis **Enregistrer**. Chaque décision est enregistrée aussitôt dans le fichier projet.
- **Encadré rouge** : la proposition demande une attention particulière : un libellé deviné pour une variable sans étiquette, le sens d'un sigle que personne n'a donné à l'IA, ou l'étendue observée présentée comme celle d'une échelle.
- **Signalements** : anomalies calculées, dont les **variantes d'écriture** d'une même réponse (« Français », « français », « Francais »), à corriger dans vos données si vous le souhaitez.
- **Décisions groupées** : en haut de la page « Variables », **Accepter les rattachements où le modèle et le calcul s'accordent (N)…** ouvre la liste exacte de ces rattachements, chacun avec sa question. Lisez chaque ligne et décochez ce qui ne convient pas (à l'essai, environ un sur cinq était faux sur une vraie base), puis **Accepter ces N rattachements**. Sur la page d'un groupe, **Accepter les étiquettes de valeurs de ce groupe (N)…** fait de même pour les étiquettes tirées des options.
- **Codes suspects** (filtre du même nom, ou le tableau de bord) : une valeur comme 999 ou −9, isolée loin des autres, est peut-être un code manquant que le fichier ne déclare pas. Seule votre équipe le sait : **C'est un code manquant** ou **C'est une vraie valeur**. Le codebook le dira ; **Revenir sur cette décision** l'annule.
- **Champs documentés** : étendue théorique, seuils, références et notes. Ils sont réservés aux personnes, et l'étendue comme les seuils exigent une source (manuel, article).
- **Groupes** : les échelles repérées par l'outil, leur alpha de Cronbach et les items probablement inversés. Confirmer une inversion la **documente** dans le codebook ; l'outil ne recode jamais les données. Pour un **instrument protégé par le droit d'auteur** (CBCL, BDI…), cochez « Ne pas reproduire le texte des questions de ce groupe » : le codebook donnera la référence de chaque question (`Q12.r3, p. 4`), sans son texte. Reproduire les items d'un instrument protégé relève de votre équipe.
- **Cotation d'une échelle** (page « Groupes », section « Cotation ») : les items du score, somme ou moyenne, le minimum et le maximum de l'échelle (pré-remplis d'après les étiquettes), le nombre minimal d'items répondus et, pour une somme qui en accepte de manquants, la règle (somme proportionnelle ou somme des items répondus), le nom du score et **une source obligatoire**. Les items inversés sont ceux confirmés plus haut ; l'étendue du score est calculée. Une cotation qui n'entre pas dans ce cadre s'écrit en note. L'IA ne propose jamais de cotation.
- **Niveaux de mesure** (page « Base ») : quand le fichier n'en donne pas (CSV, Excel), ou quand celui du fichier est douteux (un item de grille déclaré « échelle »), l'outil propose un niveau. Décidez dans le tableau, comme pour les noms : **Accepter**, **Rejeter**, ou un autre niveau, puis **Enregistrer**. Pour quelques codes sans étiquettes (1, 2, 3, 9), il ne propose rien : seule votre équipe sait ce qu'ils veulent dire.
- **Description de la base** (page « Base ») : ce qu'est une ligne (un participant, une observation répétée…), la structure (transversale, une vague par fichier, format large ou long), les variables de plan et une description courte. L'outil propose seulement la structure (une vague par fichier quand une marque de vague est réglée ; format large quand des suffixes `_t1`, `_t2` reviennent).
- **Complétude** (page « Base », et en tête des codebooks) : pour chaque élément, ce que votre équipe a décidé sur ce qui s'applique, et la liste de ce qui reste à documenter.

## 8. Exporter

Page **Export** :

- **Version finale** : seulement ce qui vient du fichier, du calcul, ou de vos décisions. **Version de travail** : avec les propositions en attente, marquées comme telles.
- **Groupes dont le texte des questions n'est pas reproduit** : par défaut, ceux que vous avez cochés dans « Groupes ».
- **Langue du codebook** : français ou anglais, par défaut celle de l'interface. Elle vaut pour les en-têtes, les notes, la provenance, le rapport et les commentaires des fichiers de commandes ; ce que l'équipe a écrit (libellés, descriptions, texte des questions) n'est jamais traduit. En ligne de commande : `ddict exporter projet.dd.json --langue en`.
- **Écrire le codebook et le rapport** (à côté du projet), ou **Télécharger** (dans votre dossier de téléchargements).

Le codebook contient les libellés, le texte des questions rattachées, le glossaire (onglet « Glossaire »), les étiquettes de valeurs acceptées et la provenance de chaque valeur. Les effectifs de moins de 5 y sont masqués. L'onglet « Informations » et l'en-tête du rapport donnent l'**empreinte du codebook**, un code de 12 caractères qui change dès qu'une décision change : notez-la avec vos résultats.

**Le contexte d'analyse** (section du même nom, en bas de la page) : le codebook en format compact, pour un programme ou pour une IA qui aide à écrire le code d'analyse. **Écrire le contexte à côté du projet** donne `etude-sommeil-contexte.md` (à coller dans un assistant) et `etude-sommeil-datapackage.json` (format standard Frictionless, utile aussi pour un dépôt de données). Seulement ce qui est accepté ; aucune donnée des participants ; les statistiques seulement si vous cochez la case. Voir la section 12.

## 9. Appliquer vos décisions à vos données

Le codebook documente ; vos données, elles, n'ont pas changé. Pour y faire entrer ce que vous avez accepté (libellés, étiquettes de valeurs, codes manquants, y compris ceux confirmés par l'équipe, niveaux de mesure), deux voies, sur la page **Export**.

**Les fichiers de commandes, la voie recommandée.** **Écrire les fichiers de commandes à côté du projet** (ou les télécharger) donne deux fichiers : `etude-sommeil-metadonnees.sps` (SPSS) et `.R` (R). Il n'y a pas de fichier pour Stata, qui n'a pas pu être essayé (D-030) : avec Stata, utilisez la copie documentée ci-dessous. Ils ne contiennent que vos décisions acceptées et ne changent aucune valeur : vous les ouvrez dans votre propre logiciel, vous pouvez les lire avant de les exécuter, et ils restent comme trace de ce qui a été fait. Les items inversés que vous avez indiqués y sont seulement suggérés, en commentaire.

- **R** (avec le paquet haven, installé une fois par `install.packages("haven")`), dans RStudio ou la console R, dans le dossier du projet :

  ```r
  donnees <- haven::read_sav("etude-sommeil.sav", user_na = TRUE)   # ou read.csv(...), haven::read_dta(...)
  source("etude-sommeil-metadonnees.R", encoding = "UTF-8")
  haven::write_sav(donnees, "etude-sommeil-avec-metadonnees.sav")   # facultatif : une copie
  ```

  `user_na = TRUE` est important pour un fichier SPSS : sans lui, haven remplace par des cases vides les codes manquants déjà déclarés (un 9 « Préfère ne pas répondre » devient une case vide, et la copie perd cette information). Les niveaux de mesure ne sont pas appliqués par R : haven ne les écrit pas.
- **SPSS** : ouvrez la base, puis **Fichier > Ouvrir > Syntaxe…**, choisissez le `.sps`, et **Exécuter > Tout**. Enregistrez ensuite la base sous un nouveau nom.

**Le script de préparation, pour vos scores.** Quand vous avez confirmé des items inversés ou écrit une cotation, le même bouton écrit aussi `etude-sommeil-preparation.sps` et `.R`. À exécuter **après** le fichier de commandes : ils créent de **nouvelles variables**, les items inversés (`sommeil_q3_inv`) et les scores (`sommeil_total`), selon votre cotation ; aucune variable d'origine n'est modifiée, et les codes manquants sont exclus des calculs. Si la base contient déjà un score du même groupe, le script compte les écarts avec celui qu'il calcule. En R : `source("etude-sommeil-preparation.R", encoding = "UTF-8")` juste après le fichier de commandes.

**La copie documentée, si vous voulez un fichier prêt à l'emploi.** **Écrire la copie documentée** (ou `ddict documenter etude-sommeil.dd.json`) écrit à côté de la base `etude-sommeil-documente.sav`, au format SPSS, avec vos décisions. Elle fonctionne aussi à partir d'une base CSV, Stata, SAS ou Excel. Avant de l'annoncer, l'outil la relit et la compare à l'original case par case ; au moindre écart, il la supprime et vous le dit. Votre fichier d'origine n'est jamais modifié, et une copie existante n'est remplacée que si vous cochez la case. La base doit se trouver à côté du projet ; sinon, **Choisir la base…** (ou `--base`). La copie contient les données des participants : rangez-la comme l'original.

## 10. Avec vos propres données

La démarche est la même avec votre fichier : SPSS (`.sav`), CSV (y compris ceux d'Excel en français, avec point-virgule et virgule décimale), Stata (`.dta`), SAS (`.sas7bdat`) ou Excel (`.xlsx` : la première feuille, avec les noms des variables sur la première ligne). Et avec votre questionnaire, en PDF ou en texte, en français ou en anglais : pour une étude menée en anglais, vérifiez sur la page **Base** que la langue de l'étude est « English ».

**Le format qui donne les meilleurs résultats : le `.sav`.** Un fichier SPSS contient ce que les autres formats obligent l'outil à deviner : les étiquettes des valeurs (« 1 = Jamais »), les codes de valeurs manquantes déclarés et le niveau de mesure. Si votre plateforme de sondage (SurveyMonkey, Qualtrics, LimeSurvey…) ou votre logiciel peut exporter en `.sav`, choisissez ce format, même si vous n'utilisez pas SPSS : l'outil le lit sans lui. Avec un autre format, tout fonctionne, mais vérifiez avec plus de soin les codes manquants et les étiquettes de valeurs proposés. L'export Excel d'une plateforme reste utile à côté du `.sav` : choisissez-le comme questionnaire, sur la page **Questionnaire**, si vous n'avez pas de PDF.

- Travaillez dans un dossier prévu pour ces données, selon les règles de votre équipe et de votre comité d'éthique. Le fichier projet, les codebooks et le dossier `.dd-envois` (ce qui a été envoyé au modèle) restent à côté des données.
- L'outil ne modifie jamais votre fichier de données.
- Les variables qui ressemblent à des identifiants, à du texte libre ou à des dates de naissance sont repérées automatiquement : seules leurs métadonnées sont utilisées, et les effectifs de moins de 5 sont masqués.
- Sur une grande base, les rattachements proposés par l'IA sont souvent justes, mais pas toujours : les questions répétées à l'identique (« À quelle fréquence cette personne vous apporte du soutien ? », une fois par personne) sont le cas le plus difficile. Vérifiez-les avant les libellés.
- La liste des projets récents est gardée sur votre ordinateur (dossier `%APPDATA%\ddict`) et ne contient que des chemins de fichiers ; **Effacer la liste**, sur l'accueil, la vide.

**Un export brut de SurveyMonkey** (variables nommées `q0003_0004`, en `.sav`, `.xlsx` ou `.csv`) est reconnu : la page **Base** affiche « Export SurveyMonkey reconnu. ». L'outil lit alors la structure du sondage dans les noms : `q0003_0004` est le 4ᵉ énoncé de la 3ᵉ question. Chaque grille devient un groupe, chaque question à cocher un groupe « réponses multiples » avec sa variable « autre », et une variable est rattachée à sa question du questionnaire quand leurs textes concordent. Dans un `.xlsx` ou un `.csv`, la deuxième ligne d'en-tête n'est jamais lue comme un participant. Les codes dont l'étiquette dit « Ne sais pas » ou « Préfère ne pas répondre » sont proposés comme codes manquants, à confirmer par l'équipe.

## 11. Renommer les variables

Un export de plateforme donne des noms comme `q0003_0004`, et une étude longitudinale veut les mêmes noms d'une vague à l'autre. La page **Noms** (après **Groupes** dans la barre latérale) propose de nouveaux noms ; vous les décidez. Le nom d'origine reste celui de votre fichier, qui n'est jamais modifié.

1. **Donnez le préfixe des grilles.** Page **Groupes**, sur chaque grille : **Préfixe des noms de ses items** (par exemple `k6`), puis **Enregistrer le préfixe**. Ses items seront nommés `k6_1`, `k6_2`… L'outil ne propose jamais de préfixe lui-même : le sigle d'un instrument est votre décision.
2. **Réglages de nommage** (page **Noms**) : la **marque de vague** (`_t2`, ou vide pour une étude à un seul temps), sa place (à la fin ou au début) et la longueur maximale des noms (32, la limite de Stata, convient à SPSS, R et Stata). **Enregistrer et proposer les noms**.
3. **Les propositions**, par des règles, sans IA : les variables de la plateforme reçoivent un nom fixe (`respondent_id`, `date_debut`…) ; les items d'une grille, `<préfixe>_<rang>` ; les options d'une question à cocher, `<nom de base>_<rang>` et `<nom de base>_autre_txt` ; une question seule, un nom de base tiré des mots de sa question. Le **nom de base** d'une question se corrige une seule fois, dans **Noms de base des questions** en bas de la page, et toutes ses variables suivent. Une variable sans proposition possible reste « à nommer » et garde son nom d'origine à l'export.
4. **Décidez dans le tableau.** Il montre, pour chaque variable, le nom proposé, son origine, son statut et un éventuel problème ; filtres « À nommer », « Proposés », « En conflit », « Décidés ». Sur chaque ligne, choisissez **Accepter** ou **Rejeter** dans la colonne **Décision**, ou écrivez un autre nom dans la colonne **Nouveau nom** (il compte alors comme décidé), puis cliquez **Enregistrer**. Chaque nom est vérifié (minuscules, chiffres et `_`, une lettre au début, pas de mot réservé de SPSS, pas deux fois le même nom). Pour aller plus vite, **Choisir « Accepter » pour les N noms proposés** remplit la colonne **Décision** : relisez le tableau, changez ce qui ne convient pas, puis **Enregistrer**. Rien n'est enregistré avant ce clic.

**Reprendre les noms d'une vague précédente.** Ouvrez **Reprendre les noms d'une vague précédente** et choisissez le fichier de la vague 1 : son fichier projet (`.dd.json`, le plus complet), sa copie documentée (`.sav`) ou sa table de noms (`-correspondance.csv`, écrite par l'outil à l'export, ou la vôtre, avec l'en-tête `nom_origine,nouveau_nom`). **Reprendre les noms** apparie chaque variable par son étiquette, ses étiquettes de valeurs et sa question, jamais par son seul numéro : SurveyMonkey renumérote les questions dès qu'une question est ajoutée. Le nom de la vague 1 est proposé avec la marque de la vague actuelle (`k6_1_t1` → `k6_1_t2`), et les préfixes des grilles sont repris. Une question reformulée n'est jamais appariée seule : elle vous est montrée comme candidate. Un **rapport des écarts** est écrit à côté du projet (`<projet>-ecarts-vagues.md`) : variables ajoutées, retirées, étiquettes de valeurs changées. Une table de noms n'apparie que par nom d'origine identique ; si la numérotation a changé, le rapport le signale.

**À l'export**, les noms acceptés s'appliquent partout : le codebook a une colonne « Nom d'origine » et un onglet « Correspondance » ; le fichier SPSS commence par `RENAME VARIABLES`, le script R par le renommage ; la copie documentée est écrite aux nouveaux noms. La table `<projet>-correspondance.csv` est écrite à côté du codebook : c'est elle, ou le fichier projet, qui servira à la vague suivante. La version finale ne contient que les noms acceptés.

En ligne de commande : `ddict renommer projet.dd.json --suffixe _t2 --reference vague1.dd.json`.

## 12. Utiliser le contexte d'analyse avec une IA

Le contexte d'analyse (section 8) est fait pour être donné tel quel à un assistant qui écrit le code de votre analyse. **Le modèle ne voit jamais vos données** : il reçoit la description de la base, écrit du code, et c'est votre ordinateur qui exécute ce code sur les vraies données.

- **Ce que vous envoyez relève de votre équipe et de votre certificat d'éthique**, pas de l'outil. Le contexte sans statistiques ne contient que des métadonnées, mais le texte des questions, les noms de variables ou la description de l'étude peuvent être sensibles. L'outil, lui, n'envoie rien : c'est vous qui copiez le fichier.
- **Choisissez un assistant qui sait écrire du code.** À l'essai (base fictive, `docs/essais/2026-10-15-contexte-analyse-modele.md`), trois assistants en ligne ont écrit une analyse juste à partir du seul contexte ; le petit modèle local de l'outil (qwen2.5 7B) a échoué, faute de savoir programmer en R. Le modèle local reste utile pour les libellés et les rattachements, pas pour écrire une analyse.
- **Donnez-lui les scores déjà calculés** quand c'est possible : le script de préparation (section 9) fait sans IA ce qu'une IA rate le plus souvent (items inversés, items manquants, codes manquants).
- **Relisez et vérifiez toujours le code avant de l'exécuter** sur vos données : à l'essai, un assistant a gardé un groupe vide « Préfère ne pas répondre » dans ses résultats. Notez l'empreinte du codebook avec le code et les résultats.

## 13. Analyser la base

La page **Analyses** (après **Noms** dans la barre latérale) calcule, sur votre base et avec vos décisions acceptées, six analyses écrites et vérifiées d'avance : **Tableau 1** (décrire l'échantillon), **test t** (comparer deux groupes), **ANOVA** (plusieurs groupes), **khi-carré** (deux variables catégorielles), **corrélation** et **régression linéaire**. Le détail de chacune (conditions, options, formules, exemples) est dans [`catalogue-analyses.md`](catalogue-analyses.md). Rien n'est envoyé hors de votre ordinateur, et votre fichier n'est jamais modifié.

**Avant de commencer**, vos décisions comptent : les codes manquants confirmés (999, −9) sont retirés, les nouveaux noms appliqués, les items inversés et les scores calculés selon votre cotation (section 7). Le **niveau de mesure** de chaque variable (page **Base**) décide des analyses où elle peut entrer : une variable sans niveau décidé n'est proposée nulle part. Les identifiants, les textes libres et les dates sont toujours exclus. Depuis la 0.13, une catégorie écrite en toutes lettres dans un CSV (« oui », « non ») entre dans les analyses dès que son niveau est « nominal » ; une case vide y compte comme une valeur manquante.

1. **Retrouver la base.** La page cherche la base à côté du projet et vérifie que c'est bien celle d'où vient le projet. Sinon, **Choisir la base…**. Elle est lue une fois, en mémoire, le temps de la séance.
2. **Choisir l'analyse**, puis ses variables, rôle par rôle (par exemple **Variable dépendante** et **Variable de groupe**) : chaque liste ne propose que les variables dont le niveau convient. Avec la base fictive : **Test t**, variable dépendante `sommeil_total`, variable de groupe `genre`. Comme `genre` a trois modalités, choisissez les deux à comparer dans **Modalités comparées** : Femme et Homme.
3. **Les options** ont la valeur recommandée par défaut (par exemple Welch, qui ne suppose pas des variances égales) ; changez-les seulement si vous savez pourquoi.
4. **Les conditions s'affichent avant le calcul.** En rouge, un **refus**, avec sa raison (moins de 2 personnes dans un groupe, trop peu d'observations par prédicteur…) : le bouton reste grisé. En jaune, un **avertissement** (un groupe de moins de 5 personnes, une variable ordinale dans une corrélation de Pearson) : l'analyse reste permise, à vous de juger.
5. **Lancer l'analyse.** Le résultat donne une phrase au style APA, qui décrit sans juger (pas de « significatif ») ; par exemple : « M = 23,69 (ÉT = 7,86) pour Femme et M = 23,50 (ÉT = 7,18) pour Homme, t(172,26) = 0,18, p = ,861, d = 0,03, IC 95 % [−0,27 ; 0,32] ». Puis les personnes retenues et écartées, les avertissements et les tableaux.

**Les fichiers de l'analyse.** **Écrire à côté du projet** donne `etude-sommeil-analyse-1.md` (le rapport : variables, options, résultats, empreinte du codebook, date et versions des bibliothèques), `etude-sommeil-analyse-1.xlsx` (les tableaux) et `etude-sommeil-analyse-1.R` (le script R équivalent), avec le fichier de commandes et le script de préparation qu'il exécute ; l'analyse suivante prend le numéro 2. On peut aussi les **télécharger** ; le script R se télécharge en `.zip` avec ses deux fichiers. Seule la dernière analyse reste affichée : gardez les rapports qui vous servent, ou ajoutez l'analyse au carnet (section 14).

**Refaire l'analyse dans R.** Placez le script et ses deux fichiers dans le dossier de la base, puis, dans R : `source("etude-sommeil-analyse-1.R", encoding = "UTF-8")`. Il n'utilise que R de base et haven, et donne les mêmes résultats que l'outil (vérifié par des tests, à 10⁻⁶ près).

**Les tableaux et les figures APA.** Sous le résultat, la section **Tableaux et figures APA** présente l'analyse au format APA 7 : un tableau (« **Tableau 1** » en gras, le titre en *italique*, des filets horizontaux seulement, les symboles en italique, une note « *Note.* ») et, sauf pour le Tableau 1, une figure (moyennes et leur intervalle de confiance à 95 %, barres groupées d'un khi-carré, nuage de points d'une corrélation, coefficients standardisés d'une régression). Le détail de chaque tableau et de chaque figure est dans [`tableaux-figures-apa.md`](tableaux-figures-apa.md).

- **Numéro, titre et note** se changent dans l'encadré de chaque tableau et de chaque figure (par exemple « Tableau 3 » pour suivre votre article) ; l'aperçu suit. Les chiffres, eux, ne se changent pas : ils viennent du calcul.
- **Word (tableaux et figures APA)** : un fichier `.docx`. Chaque tableau y est un vrai tableau Word, à modifier comme les autres ; chaque figure, une image nette, avec son numéro, son titre et sa note en texte. À la fin, en petit, la phrase de résultat et l'empreinte du codebook, pour mémoire.
- **Excel (graphiques modifiables)** : un classeur, une feuille par figure, avec ses données et le **graphique Excel natif**. Changez-y les couleurs, les axes ou les étiquettes, puis copiez le graphique dans Word : il y reste modifiable. Pour un graphique de régression, les coefficients y sont des barres horizontales avec leur intervalle.
- **Écrire à côté du projet** écrit aussi ces deux fichiers (`etude-sommeil-analyse-1.docx` et `etude-sommeil-analyse-1-graphiques.xlsx`), avec vos numéros, titres et notes. En ligne de commande : `ddict analyser … --format docx xlsx` (par défaut, les deux ; `--format aucun` pour aucun).
- Les figures montrent des données de l'étude (un nuage de points montre chaque personne) : comme pour les tableaux, c'est à l'équipe de décider ce qui peut être publié.

**Ces résultats viennent de vos données** : rangez les rapports comme les données, et décidez avant de publier ce que peuvent montrer les petits effectifs (signalés sous 5).

**Demander une proposition à l'IA locale (facultatif).** En haut de la page, l'encadré **Demander une proposition à l'IA locale** : écrivez votre objectif en une phrase (« Les hommes et les femmes ont-ils la même qualité de sommeil ? »), puis **Demander une proposition**. Le modèle choisi sur la page **IA locale** reçoit cet objectif tel quel, la liste des analyses et celle des variables (nom, libellé, niveau, groupe) : **aucune donnée, aucune statistique** ; **Voir ce qui serait envoyé** montre le message exact. N'écrivez aucune donnée de participant dans l'objectif. Il répond en quelques secondes par une à trois propositions, chacune avec sa raison ; **Reprendre cette proposition** remplit les choix de la page, et rien n'est calculé avant **Lancer l'analyse**.

Ce qu'il faut en attendre (essais `docs/essais/2026-10-16-ia-conseillere.md` et `2026-10-16-essai-analyses.md`) : sur la base fictive, la bonne analyse et les bonnes variables 9 fois sur 13 ; sur une vraie base de 250 variables, le bon type d'analyse deux fois sur trois, mais des variables moins sûres. Le modèle propose une analyse même quand aucune ne convient, et choisit parfois une méthode moins adaptée (Student plutôt que Welch). **C'est une aide pour retrouver le type d'analyse ; le choix reste le vôtre.** Pour une très grande base, l'outil peut refuser d'envoyer le message, trop long pour le modèle : choisissez alors l'analyse vous-même.

## 14. Le carnet d'analyses et l'ébauche d'article

Un article réunit souvent dix ou vingt résultats, numérotés à la suite, qui doivent rester justes quand le codebook change. Le **carnet** garde les analyses de l'étude, dans l'ordre de votre article, et les réunit dans une ébauche d'article. Il ne fait appel à aucune IA. Le détail est dans [`carnet-analyses.md`](carnet-analyses.md).

1. **Ajouter une analyse.** Sur la page **Analyses**, après **Lancer l'analyse**, la section **Carnet d'analyses** a un bouton **Ajouter au carnet**. L'analyse va à la fin du carnet, retenue, avec les titres et les notes que vous avez changés dans les tableaux et figures APA (pas leurs numéros : le carnet numérote dans son ordre). Le bouton devient « Déjà dans le carnet (A1) ».
2. **La page Carnet** (après **Analyses**) liste les analyses dans leur ordre : numéro (A1, A2…), titre, variables, phrase de résultat et état. **Monter** et **Descendre** changent l'ordre ; **Retenue pour le document** écarte une analyse du document sans la retirer ; **Retirer** la supprime (son numéro ne revient pas).
3. **Quand une décision change** (un code manquant confirmé, un niveau de mesure corrigé), chaque analyse est recalculée à l'ouverture de la page :
   - **à jour** ou **recalculée, sans changement** : rien à faire ;
   - **changée, à confirmer** : la page montre ce qui a changé (par exemple « n_used : 200 → 196 », « r : ,05 → ,01 ») et la nouvelle phrase. **Confirmer le nouveau calcul** l'adopte. Tant qu'une analyse retenue attend sa confirmation, l'ébauche d'article ne se produit pas ;
   - **impossible à calculer** : la raison s'affiche (une variable retirée, un niveau de mesure qui ne convient plus). L'analyse reste dans le carnet, mais elle est écartée du document, et la fin du document le dit.
4. **L'ébauche d'article.** Réglez au besoin le **Premier tableau** et la **Première figure** (par exemple 3, si deux tableaux précèdent dans votre article), puis **Produire l'ébauche d'article**. Trois fichiers sont écrits à côté du projet, et remplacés à chaque fois :
   - `etude-sommeil-article.docx` : depuis la 0.13, une ébauche d'article APA, de la page de titre aux Références (section 16) : la Méthode (section 15), puis un intertitre par analyse (« A2 — Test t : comparer deux groupes »), ou par hypothèse quand l'étude a un plan, avec sa phrase de résultat et ses tableaux et figures APA, numérotés à la suite sur tout le document ; à la fin, l'empreinte du codebook, la date, les versions et la liste des analyses ;
   - `etude-sommeil-article-graphiques.xlsx` : le graphique Excel natif de chaque figure ;
   - `etude-sommeil-article-R.zip` : le **script R maître**, qui refait toutes les analyses retenues, dans l'ordre, avec le fichier de commandes et le script de préparation. Décompressez-le dans le dossier de la base, puis, dans R : `source("etude-sommeil-article.R", encoding = "UTF-8")`. Il donne les mêmes valeurs que l'outil (vérifié par des tests, à 10⁻⁶ près), rangées dans `resultats$A1`, `resultats$A2`…

Chaque analyse est **recalculée** sur la base au moment de produire le document : rien n'est recopié du carnet. Le carnet, `etude-sommeil-carnet.json`, est à côté du projet ; il ne garde que des agrégats (effectifs, moyennes, statistiques, phrases), jamais une ligne de la base. Sans la base, la page affiche le carnet tel qu'il est, sans le recalculer, et **Choisir la base…** la retrouve.

En ligne de commande : `ddict carnet ajouter` (mêmes options que `ddict analyser`), `lister`, `deplacer A3 1`, `retenir A2`, `ecarter A2`, `retirer A2`, `confirmer A1` (ou `--tout`), `numeros --tableau 3 --figure 2` ; puis `ddict article` écrit les trois fichiers (`ddict resultats`, son ancien nom, marche encore dans cette version). La page et les commandes lisent et écrivent le même carnet.

## 15. La Méthode : exclusions, diagramme de flux et paragraphes

La section Méthode d'un article dit qui a été exclu et pourquoi, décrit l'échantillon et les instruments, et nomme les analyses. La page **Méthode** (après **Carnet**) prépare tout cela à partir de vos décisions, sans aucune IA. Elle ne décide rien à votre place : chaque règle d'exclusion est la vôtre, écrite avec sa raison. Le détail des phrases est dans [`methode-gabarits.md`](methode-gabarits.md).

1. **Les règles d'exclusion.** Ouvrez **Ajouter une règle** et choisissez la **Sorte de règle** :
   - **Condition sur une variable** : par exemple `age` « < plus petit que » 18 ; ou « manquant » ;
   - **Condition sur un score** : sur le score d'un groupe coté (page « Groupes », section « Cotation », voir la section 7) ;
   - **Complétude d'un groupe** : exclure qui a répondu à moins de … items ;
   - **Durée de passation** : entre une date de début et une date de fin, sous un seuil en secondes. L'outil ne propose aucun seuil : c'est un choix de l'équipe, et la **Source** est exigée (un procès-verbal, un article) ;
   - **Grille en ligne droite** : tous les items d'une grille répondus avec la même valeur ;
   - **Doublons** : une réponse qui en répète une antérieure sur les variables choisies (la première est gardée).

   Écrivez la **Raison, telle que publiée** (« Moins de 18 ans »), puis **Ajouter la règle**. Les règles s'appliquent dans leur ordre : une personne est comptée par la première règle qui l'exclut. **Monter** et **Descendre** changent l'ordre (et donc les effectifs de chaque règle, jamais l'échantillon analysé) ; **Retirer** supprime une règle. L'outil refuse une condition qui nommerait une personne (une valeur d'un identifiant, d'un courriel, d'un texte libre) : une règle décrit qui exclure, jamais une liste de personnes.
2. **Le diagramme de flux** montre les **Réponses reçues**, les **Exclues** (règle par règle) et l'**Échantillon analysé**, avec l'image qui sera la Figure 1 du document.
3. **Les signaux de qualité de la passation** montrent combien de personnes une règle toucherait, sans jamais l'appliquer : les durées (avec le seuil que vous tapez), les grilles en ligne droite et les doublons. **En faire une règle** remplit le formulaire **Ajouter une règle**, plus haut ; il reste à écrire la raison et à ajouter la règle.
4. **La description de l'échantillon** : choisissez les variables qui décrivent les participants (par exemple l'âge et le genre).
5. **L'aperçu des paragraphes** montre les trois paragraphes de la Méthode, **Participants**, **Instruments** et **Analyses**, tels qu'ils seront dans le document. Ce que le codebook ne dit pas devient un trou surligné en jaune, « [à compléter : nom et source de l'instrument du groupe G1] » : l'outil ne devine jamais un nom d'instrument ni une source. Complétez-les dans Word, ou dans le projet (page « Groupes », nom de l'instrument avec sa source) pour qu'ils soient remplis à chaque document.

**Les chiffres de la Méthode sont gardés par le carnet**, comme ceux d'une analyse. Quand une règle change, la page **Carnet** montre « M. Méthode — changée, à confirmer » et ce qui a changé ; une nouvelle règle change aussi les analyses, recalculées sur le nouvel échantillon. **Tout confirmer** adopte tous les nouveaux calculs d'un coup ; d'ici là, le document ne se produit pas.

**Partout de la même façon.** Les règles s'appliquent avant chaque analyse de l'outil, dans le script de préparation SPSS et R (une variable `ddict_exclusion` : 0 pour une personne gardée, sinon le rang de la règle qui l'exclut) et dans le script R maître. La copie documentée de la base (section 9) n'en garde aucune trace : elle reste identique à l'original. La fidélité des scores (alpha de Cronbach et son intervalle de confiance à 95 %) est recalculée sur l'échantillon analysé.

En ligne de commande : `ddict exclusions lister`, `ajouter` (`--condition age lt 18`, `--score G1 lt 10`, `--completude G1 5`, `--duree debut fin 180 --source "…"`, `--ligne-droite G2`, `--doublons courriel`, toujours avec `--raison "…"`), `retirer E2`, `deplacer E3 1` et `signaux` (`--debut`, `--fin`, `--duree-min`, `--doublons`) ; `ddict carnet echantillon etude-sommeil.dd.json age genre` choisit les variables de l'échantillon. La page et les commandes écrivent les mêmes règles.

## 16. Le plan d'analyse, le préenregistrement et l'article

Une étude confirmatoire écrit ses hypothèses avant d'analyser, et son article dit ensuite ce qui était prévu et ce qui a changé. La page **Plan** (avant **Analyses**) garde ce plan : les hypothèses de l'équipe, chacune liée à une analyse du catalogue, les règles générales, le gel et les amendements. Elle ne fait appel à aucune IA, et rien n'est envoyé hors de votre ordinateur. Le détail est dans [`plan-analyse-article.md`](plan-analyse-article.md).

1. **Les règles générales**, enregistrées aussitôt :
   - le **Seuil α**, tapé par l'équipe : la page n'en propose aucun d'office ;
   - la **Correction pour comparaisons multiples** (Holm par défaut, Bonferroni ou aucune), appliquée au sein de chaque famille d'hypothèses ;
   - la **Justification de la taille d'échantillon**, en texte ;
   - l'**Origine des données** (primaires ou secondaires) et leur **État quand le plan a été écrit** (avant leur création, avant toute observation, avant l'accès, avant l'analyse, après une analyse). C'est une déclaration de l'équipe : l'article l'écrit « selon l'équipe ».
2. **Ajouter une hypothèse** : son énoncé, tel que l'équipe l'écrit, l'analyse et ses variables rôle par rôle, comme sur la page **Analyses** (section 13), puis :
   - l'**Effet testé** : pour une régression, le modèle entier ou un prédicteur ; pour une corrélation de plus de deux variables, la paire ;
   - le **Sens attendu** (le premier ou le second groupe plus élevé, dans l'ordre des codes ; positif ou négatif). Pour un test t, il rend le test unilatéral ;
   - le **Caractère** : confirmatoire (par défaut) ou exploratoire ;
   - la **Famille (correction)**, par exemple F1 : les hypothèses d'une même famille voient leurs *p* corrigés ensemble.

   Les conditions de l'analyse sont vérifiées sur la base, comme sur la page **Analyses**. **Monter** et **Descendre** fixent l'ordre de l'article ; **Retirer** supprime une hypothèse (son numéro ne revient pas).
3. **Figer le plan.** Le plan reçoit sa date et son empreinte, et chaque hypothèse devient une analyse du carnet (section 14). Le bouton dit ce qui l'empêche : aucune hypothèse, α non tapé, origine ou état non dit. Ensuite, **toute modification exige une raison**, tapée en tête de page, et devient un **amendement**, gardé pour toujours : l'article le cite avec sa date et sa raison. L'analyse d'origine reste dans le carnet, écartée, et la nouvelle prend sa place. La page **Carnet** dit l'état de chaque analyse face au plan : « prévue (H1) », « remplacée par l'amendement du … », « variante de H1 », « exploratoire ».
4. **Le préenregistrement.** **Écrire le préenregistrement à côté du projet** donne `etude-sommeil-preenregistrement.docx` et `.md`. Le gabarit suit l'origine des données : OSF Prereg pour des données primaires, celui de van den Akker et al. (2021) pour des données secondaires. Il est écrit à partir du plan et du codebook seulement, **jamais de la base** : aucun effectif, aucun résultat. Ce que l'outil ne peut pas savoir (ce que l'équipe connaissait déjà des données, le lieu du dépôt) reste un trou surligné, à compléter dans Word. L'outil ne dépose rien et ne dit jamais que l'étude a été préenregistrée.
5. **L'ébauche d'article** (page **Carnet**, section 14) suit le plan quand il est figé :
   - l'Introduction annonce les hypothèses, et la Méthode gagne un paragraphe **Plan d'analyse** (origine et état déclarés, date du gel, α, correction et familles, tests unilatéraux, amendements) ;
   - les Résultats suivent les hypothèses, avec, pour une hypothèse d'une famille, le *p* corrigé à côté du *p* brut ; puis les « Analyses exploratoires » ;
   - la Discussion rappelle chaque hypothèse, le sens attendu et le sens observé, puis laisse un trou pour son interprétation.

   **L'outil n'écrit jamais qu'une hypothèse est « soutenue » ou « rejetée »**, ni « significatif » : il décrit ce qui a été observé, et le jugement revient aux auteurs. Le titre, les auteurs, le résumé, le contexte, les limites et la conclusion restent des trous.

En ligne de commande : `ddict plan lister`, `ajouter` (les variables comme pour `ddict carnet ajouter`, et `--paire A B`, `--predicteur X` ou `--modele`, `--sens positif`, `--famille F1`, `--exploratoire`), `modifier H2 --methode spearman --raison "…"` (ou `amender`), `retirer H2`, `deplacer H3 1`, `regles --alpha 0.05 --correction holm --origine primaires --etat avant-analyse --taille "…"`, `figer`, `effacer --confirmer` et `preenregistrement` ; puis `ddict article`. La page et les commandes écrivent le même plan, le même préenregistrement et le même article.

Un essai sur une base ouverte et son article publié est décrit dans [`essais/2026-10-18-essai-plan-article-amatus.md`](essais/2026-10-18-essai-plan-article-amatus.md) : les chiffres de l'outil y sont ceux de l'article et de R.

## Mettre à jour ou désinstaller

- **Mettre à jour** : téléchargez et décompressez la nouvelle archive, puis double-cliquez sur son `installer.bat`. Si l'outil est ouvert, l'installateur propose de le fermer (répondez `o`) : il ne peut pas le remplacer pendant qu'il tourne. Vos fichiers projet sont conservés. Un projet ouvert avec la version 0.8 ne s'ouvre plus avec une version plus ancienne (son format a changé) ; l'inverse fonctionne.
- **Désinstaller** : double-cliquez sur `desinstaller.bat`, dans le dossier de l'outil. Il retire l'outil et ses icônes, sans toucher à vos projets, codebooks ou données ; il demande avant d'effacer la liste des projets récents. uv et Ollama restent installés.

## Pour qui préfère la ligne de commande

Toutes les étapes existent aussi en commandes, dans PowerShell (`ddict --help` les liste) :

```
ddict                                         # ouvrir l'interface sur l'accueil
ddict profiler etude-sommeil.sav              # lire la base, créer le fichier projet
ddict questionnaire etude-sommeil.dd.json questionnaire-sommeil.pdf
ddict rattacher etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
ddict enrichir etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
ddict reviser etude-sommeil.dd.json           # ouvrir directement un projet
ddict exporter etude-sommeil.dd.json          # codebook Excel et rapport
ddict exporter etude-sommeil.dd.json --syntaxe   # et les fichiers de commandes SPSS et R
ddict exporter etude-sommeil.dd.json --contexte  # et le contexte d'analyse (--avec-statistiques)
ddict documenter etude-sommeil.dd.json        # copie documentée de la base (.sav)
ddict renommer etude-t2.dd.json --suffixe _t2 --reference etude-t1.dd.json   # noms
ddict analyser etude-sommeil.dd.json test_t --dependante sommeil_total --groupe genre --modalites 1,2
ddict carnet ajouter etude-sommeil.dd.json correlation --variables heures_sommeil nb_reveils
ddict carnet lister etude-sommeil.dd.json      # le carnet, recalculé
ddict exclusions ajouter etude-sommeil.dd.json --condition age lt 18 --raison "Moins de 18 ans"
ddict exclusions lister etude-sommeil.dd.json   # les règles et le diagramme de flux
ddict carnet echantillon etude-sommeil.dd.json age genre   # les variables de l'échantillon
ddict plan ajouter etude-sommeil.dd.json test_t --enonce "Les femmes dorment mieux." --dependante sommeil_total --groupe genre --modalites 1,2 --sens premier
ddict plan regles etude-sommeil.dd.json --alpha 0.05 --origine primaires --etat avant-analyse
ddict plan figer etude-sommeil.dd.json         # le plan arrêté ; ensuite, --raison à chaque changement
ddict plan preenregistrement etude-sommeil.dd.json   # le préenregistrement (Word et Markdown)
ddict article etude-sommeil.dd.json           # l'ébauche d'article et le script R maître
ddict conseiller etude-sommeil.dd.json "Comparer le sommeil des femmes et des hommes." --modele qwen2.5:7b-instruct-q4_K_M
ddict evaluer --modele qwen2.5:7b-instruct-q4_K_M   # banc d'essai d'un modèle
```

Les commandes et leurs options ont aussi des noms anglais (`ddict export --work`, `--replace`…). `--apercu` (à `rattacher` ou `enrichir`, sans `--modele`) écrit les messages qui seraient envoyés dans le dossier `etude-sommeil.dd-envois\apercu`, sans rien envoyer. `ddict exporter --sans-texte G2` omet le texte des questions d'un groupe pour un seul export. `ddict analyser` écrit le rapport, les tableaux et le script R à côté du projet (analyses : `tableau1`, `test_t`, `anova`, `khi2`, `correlation`, `regression`) ; `ddict conseiller` affiche les propositions du modèle sans rien calculer (`--apercu` pour voir le message seulement).

## En cas de problème

| Ce qui arrive | Que faire |
|---|---|
| « Windows a protégé votre ordinateur » au double-clic sur `installer.bat` | **Informations complémentaires**, puis **Exécuter quand même** (section 1). |
| `installer.bat` s'arrête sur un message rouge | Vérifiez la connexion Internet, puis relancez-le. Si le message persiste, notez-le et transmettez-le. Certains postes d'établissement interdisent les scripts : adressez-vous au soutien informatique. |
| « Ce dossier ne contient pas l'outil » | `installer.bat` a été copié hors de l'archive : lancez celui du dossier de l'outil décompressé (section 1, étape 2). |
| La fenêtre « Ouvrir » ne s'affiche pas | Elle est peut-être derrière la fenêtre de l'outil : regardez dans la barre des tâches. Sinon, collez le chemin du fichier dans le champ sous le bouton (clic droit sur le fichier dans l'Explorateur, **Copier en tant que chemin d'accès**). |
| Rien ne s'ouvre au double-clic sur l'icône | Attendez une dizaine de secondes. Sinon, ouvrez le journal de l'outil : collez `%APPDATA%\ddict\journal.txt` dans la barre d'adresse de l'Explorateur, puis Entrée. Il contient ses messages de démarrage (aucune donnée) : transmettez-le. |
| « Un projet existe déjà pour cette base » | L'outil n'écrase pas votre travail : **Ouvrir le projet existant**, ou **Remplacer le projet** si vous voulez vraiment repartir de zéro (vos décisions seront perdues). |
| Page IA locale : « Ollama ne répond pas » | Lancez Ollama depuis le menu Démarrer, attendez son icône près de l'horloge, puis **Vérifier de nouveau**. |
| Page IA locale : aucun modèle installé | Relancez `installer.bat` et répondez `o` pour télécharger le modèle, ou suivez les indications de la page. |
| Une grille du questionnaire est « à vérifier » | Ses titres de colonnes sont collés dans le PDF : l'outil ne propose alors pas d'étiquettes de valeurs pour ses variables. Un `.txt` copié depuis Word évite le problème. |
| « Impossible d'écrire les fichiers » à l'export | Le codebook est probablement ouvert dans Excel : fermez-le, puis recommencez. |
| Copie documentée : « La base … est introuvable à côté du projet » | Placez la base dans le dossier du projet, ou **Choisir la base…**. |
| Copie documentée : « n'est plus le fichier d'où vient le projet » | La base a changé depuis la création du projet (nouvelle exportation, données corrigées). Créez un nouveau projet à partir de la base actuelle. |
| « Le plan est arrêté : donnez la raison de cette modification » | Après le gel, chaque changement est un amendement : tapez sa raison en tête de la page **Plan** (ou `--raison "…"`), puis recommencez. |
| R : « there is no package called 'haven' » | Dans R, une seule fois : `install.packages("haven")`. |
| L'outil semble figé | Fermez sa fenêtre, puis double-cliquez de nouveau sur l'icône. Les décisions déjà prises sont enregistrées. |

Pour toute autre difficulté, notez ce que vous avez fait et le message obtenu, et transmettez-les à la personne qui vous a fourni l'outil.
