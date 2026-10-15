# Installer et utiliser l'outil sous Windows

Ce guide s'adresse aux personnes qui ne programment pas. Il mène de l'installation jusqu'à un codebook complet, produit à partir de la base fictive et de son questionnaire, fournis avec l'outil. Tout se fait par des doubles-clics et dans la fenêtre de l'outil ; aucune commande n'est à taper. Comptez une heure, plus le téléchargement du modèle d'IA si vous choisissez de l'utiliser.

Sur un Mac : [`installation-macos.md`](installation-macos.md). In English: [`en/installation-windows.md`](en/installation-windows.md) (Windows), [`en/installation-macos.md`](en/installation-macos.md) (macOS).

## Ce qu'il faut

- Windows 10 ou 11. Pas besoin de droits d'administrateur.
- Une connexion Internet **pendant l'installation seulement**. Ensuite, l'outil ne communique plus avec Internet : il lit vos fichiers et écrit ses résultats sur votre ordinateur.
- Pour l'IA, facultative : environ 5 Go d'espace libre et 16 Go de mémoire vive (8 Go suffisent, en plus lent). Une carte graphique accélère le travail, mais n'est pas nécessaire ; sans elle, un modèle plus petit est conseillé (section 6).

## 1. Installer

1. Téléchargez l'archive de l'outil depuis la page des versions du projet sur GitHub : le lien **Source code (zip)**, par exemple `dictionnaire-donnees-0.7.0.zip`.
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

## 8. Exporter

Page **Export** :

- **Version finale** : seulement ce qui vient du fichier, du calcul, ou de vos décisions. **Version de travail** : avec les propositions en attente, marquées comme telles.
- **Groupes dont le texte des questions n'est pas reproduit** : par défaut, ceux que vous avez cochés dans « Groupes ».
- **Langue du codebook** : français ou anglais, par défaut celle de l'interface. Elle vaut pour les en-têtes, les notes, la provenance, le rapport et les commentaires des fichiers de commandes ; ce que l'équipe a écrit (libellés, descriptions, texte des questions) n'est jamais traduit. En ligne de commande : `ddict exporter projet.dd.json --langue en`.
- **Écrire le codebook et le rapport** (à côté du projet), ou **Télécharger** (dans votre dossier de téléchargements).

Le codebook contient les libellés, le texte des questions rattachées, le glossaire (onglet « Glossaire »), les étiquettes de valeurs acceptées et la provenance de chaque valeur. Les effectifs de moins de 5 y sont masqués.

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
3. **Les propositions**, par des règles, sans IA : les variables de la plateforme reçoivent un nom fixe (`respondent_id`, `date_debut`…) ; les items d'une grille, `<préfixe>_<rang>` ; les options d'une question à cocher, `<radical>_<rang>` et `<radical>_autre_txt` ; une question seule, un radical tiré des mots de sa question. Le **radical** d'une question se corrige une seule fois, dans **Radicaux des questions** en bas de la page, et toutes ses variables suivent. Une variable sans proposition possible reste « à nommer » et garde son nom d'origine à l'export.
4. **Décidez.** Le tableau montre, pour chaque variable, le nom proposé, son origine, son statut et un éventuel problème ; filtres « À nommer », « Proposés », « En conflit », « Décidés ». Corrigez un nom directement dans la colonne **Nouveau nom**, puis **Enregistrer les noms modifiés** : chaque nom est vérifié (minuscules, chiffres et `_`, une lettre au début, pas de mot réservé de SPSS, pas deux fois le même nom). Sous le tableau, **Une variable** permet d'accepter ou de rejeter un nom. **Accepter en lot les noms proposés de** une grille ou d'une question, puis **Voir la liste…** : décochez ce qui ne convient pas, puis **Accepter ces N noms**.

**Reprendre les noms d'une vague précédente.** Ouvrez **Reprendre les noms d'une vague précédente** et choisissez le fichier de la vague 1 : son fichier projet (`.dd.json`, le plus complet), sa copie documentée (`.sav`) ou sa table de noms (`-correspondance.csv`, écrite par l'outil à l'export, ou la vôtre, avec l'en-tête `nom_origine,nouveau_nom`). **Reprendre les noms** apparie chaque variable par son étiquette, ses étiquettes de valeurs et sa question, jamais par son seul numéro : SurveyMonkey renumérote les questions dès qu'une question est ajoutée. Le nom de la vague 1 est proposé avec la marque de la vague actuelle (`k6_1_t1` → `k6_1_t2`), et les préfixes des grilles sont repris. Une question reformulée n'est jamais appariée seule : elle vous est montrée comme candidate. Un **rapport des écarts** est écrit à côté du projet (`<projet>-ecarts-vagues.md`) : variables ajoutées, retirées, étiquettes de valeurs changées. Une table de noms n'apparie que par nom d'origine identique ; si la numérotation a changé, le rapport le signale.

**À l'export**, les noms acceptés s'appliquent partout : le codebook a une colonne « Nom d'origine » et un onglet « Correspondance » ; le fichier SPSS commence par `RENAME VARIABLES`, le script R par le renommage ; la copie documentée est écrite aux nouveaux noms. La table `<projet>-correspondance.csv` est écrite à côté du codebook : c'est elle, ou le fichier projet, qui servira à la vague suivante. La version finale ne contient que les noms acceptés.

En ligne de commande : `ddict renommer projet.dd.json --suffixe _t2 --reference vague1.dd.json`.

## Mettre à jour ou désinstaller

- **Mettre à jour** : téléchargez et décompressez la nouvelle archive, puis double-cliquez sur son `installer.bat`. Si l'outil est ouvert, l'installateur propose de le fermer (répondez `o`) : il ne peut pas le remplacer pendant qu'il tourne. Vos fichiers projet sont conservés. Un projet ouvert avec la version 0.7 ne s'ouvre plus avec une version plus ancienne (son format a changé) ; l'inverse fonctionne.
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
ddict documenter etude-sommeil.dd.json        # copie documentée de la base (.sav)
ddict renommer etude-t2.dd.json --suffixe _t2 --reference etude-t1.dd.json   # noms
ddict evaluer --modele qwen2.5:7b-instruct-q4_K_M   # banc d'essai d'un modèle
```

Les commandes et leurs options ont aussi des noms anglais (`ddict export --work`, `--replace`…). `--apercu` (à `rattacher` ou `enrichir`, sans `--modele`) écrit les messages qui seraient envoyés dans le dossier `etude-sommeil.dd-envois\apercu`, sans rien envoyer. `ddict exporter --sans-texte G2` omet le texte des questions d'un groupe pour un seul export.

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
| R : « there is no package called 'haven' » | Dans R, une seule fois : `install.packages("haven")`. |
| L'outil semble figé | Fermez sa fenêtre, puis double-cliquez de nouveau sur l'icône. Les décisions déjà prises sont enregistrées. |

Pour toute autre difficulté, notez ce que vous avez fait et le message obtenu, et transmettez-les à la personne qui vous a fourni l'outil.
