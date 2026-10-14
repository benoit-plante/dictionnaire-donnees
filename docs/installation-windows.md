# Installer et utiliser l'outil sous Windows

Ce guide s'adresse aux personnes qui ne programment pas. Il mène de l'installation jusqu'à un codebook complet, produit à partir de la base fictive et de son questionnaire, fournis avec l'outil. Tout se fait par des doubles-clics et dans votre navigateur ; aucune commande n'est à taper. Comptez une heure, plus le téléchargement du modèle d'IA si vous choisissez de l'utiliser.

## Ce qu'il faut

- Windows 10 ou 11. Pas besoin de droits d'administrateur.
- Une connexion Internet **pendant l'installation seulement**. Ensuite, l'outil ne communique plus avec Internet : il lit vos fichiers et écrit ses résultats sur votre ordinateur.
- Pour l'IA, facultative : environ 5 Go d'espace libre et 16 Go de mémoire vive (8 Go suffisent, en plus lent). Une carte graphique accélère le travail, mais n'est pas nécessaire.

## 1. Installer

1. Téléchargez l'archive de l'outil depuis la page des versions du projet sur GitHub : le lien **Source code (zip)**, par exemple `dictionnaire-donnees-0.3.0.zip`.
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

Double-cliquez sur l'icône **Dictionnaire de données**. Votre navigateur s'ouvre sur l'**accueil** de l'outil, à une adresse qui commence par `http://127.0.0.1` : elle n'est accessible que depuis votre ordinateur.

Une petite fenêtre noire, réduite dans la barre des tâches, fait tourner l'outil. **Pour arrêter l'outil, fermez cette fenêtre.** Fermer l'onglet du navigateur ne l'arrête pas : un nouveau double-clic sur l'icône rouvre simplement l'onglet.

## 3. Premier codebook, à partir de la base fictive

La base fictive est une petite étude inventée sur le sommeil (200 participants fictifs), avec son questionnaire. Elle permet d'essayer l'outil sans aucune donnée réelle.

1. Sur l'accueil, sous **Nouveau projet**, cliquez sur **Choisir une base…**. La fenêtre « Ouvrir » de Windows apparaît (si vous ne la voyez pas, regardez derrière le navigateur). Allez dans le dossier de l'outil, puis `exemples\bases-fictives`, et choisissez `etude-sommeil.sav`.
2. Cliquez sur **Créer le projet**. L'outil lit la base et crée à côté d'elle le **fichier projet**, `etude-sommeil.dd.json`. Il contient tout ce que l'outil a calculé (types, manquants, modalités, étiquettes) et, plus tard, vos décisions ; il ne contient pas les réponses individuelles des participants. Le fichier de données n'est jamais modifié.
3. La page **Base** résume ce qui a été lu : nombre de variables et de lignes, variables sensibles, signalements.
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
- **Avec l'IA** (section 6) : le modèle choisit parmi les candidates, puis vous acceptez, corrigez ou rejetez chaque choix, de la même façon.

Quand le fichier n'a pas d'étiquettes de valeurs (un CSV, par exemple), l'outil propose « 1 = Pas du tout … 5 = Extrêmement » d'après les options de la question rattachée, seulement dans les cas sûrs. La mention « **ordre supposé, à vérifier** » est sérieuse : vérifiez l'ordre des codes dans votre plateforme d'enquête ou votre script de recodage avant d'accepter. Une base recodée peut avoir 0 = « Autre » là où le questionnaire place « Autre » en dernier.

## 6. Facultatif : l'IA locale

L'IA propose des rattachements aux questions, puis des libellés et des descriptions plus lisibles que les noms de variables. Elle tourne sur votre ordinateur, avec le logiciel libre **Ollama**. Le modèle ne reçoit jamais les réponses des participants, seulement des informations résumées (noms, étiquettes, proportions, questions). Chaque proposition attend votre décision.

1. Page **IA locale** : l'outil vérifie qu'Ollama répond et montre le modèle choisi. S'il manque quelque chose, la page explique quoi faire ; l'outil ne télécharge jamais de modèle lui-même.
2. **Rattachement aux questions** : **Voir exactement ce qui serait envoyé** montre les messages, sans rien envoyer. Puis **Faire proposer : rattachement aux questions**. Une barre de progression avance bloc par bloc.
3. **Révisez les rattachements** (page Variables, filtre « À réviser » ; ou le tableau de bord) avant d'aller plus loin. L'ordre compte : pour les libellés, le modèle reçoit le texte des questions dont vous avez accepté le rattachement, et le sens des sigles que vous avez acceptés. Un rattachement faux lui donnerait une fausse question.
4. **Libellés et descriptions** : **Faire proposer : libellés et descriptions**, puis révisez-les.

Pendant un travail, **Arrêter** (ou un changement de page) l'interrompt après le bloc en cours. Les blocs terminés sont enregistrés ; relancez pour continuer là où il s'était arrêté. Comptez environ une minute pour la base fictive avec une carte graphique, plusieurs minutes sans.

## 7. Réviser

- **Variables** : le filtre (« À réviser », « Avec signalements », « Sensibles », « Sans question », « Toutes ») et la liste des variables. Sur chaque fiche : ce que dit le fichier, ce qui a été calculé, la question rattachée, et chaque proposition à **Accepter**, **Rejeter**, ou corriger puis **Enregistrer**. Chaque décision est enregistrée aussitôt dans le fichier projet.
- **Encadré rouge** : la proposition demande une attention particulière : un libellé deviné pour une variable sans étiquette, le sens d'un sigle que personne n'a donné à l'IA, ou l'étendue observée présentée comme celle d'une échelle.
- **Signalements** : anomalies calculées, dont les **variantes d'écriture** d'une même réponse (« Français », « français », « Francais »), à corriger dans vos données si vous le souhaitez.
- **Champs documentés** : étendue théorique, seuils, références et notes. Ils sont réservés aux personnes, et l'étendue comme les seuils exigent une source (manuel, article).
- **Groupes** : les échelles repérées par l'outil, leur alpha de Cronbach et les items probablement inversés. Confirmer une inversion la **documente** dans le codebook ; l'outil ne recode jamais les données. Pour un **instrument protégé par le droit d'auteur** (CBCL, BDI…), cochez « Ne pas reproduire le texte des questions de ce groupe » : le codebook donnera la référence de chaque question (`Q12.r3, p. 4`), sans son texte. Reproduire les items d'un instrument protégé relève de votre équipe.

## 8. Exporter

Page **Export** :

- **Version finale** : seulement ce qui vient du fichier, du calcul, ou de vos décisions. **Version de travail** : avec les propositions en attente, marquées comme telles.
- **Groupes dont le texte des questions n'est pas reproduit** : par défaut, ceux que vous avez cochés dans « Groupes ».
- **Écrire le codebook et le rapport** (à côté du projet), ou **Télécharger** (dans votre dossier de téléchargements).

Le codebook contient les libellés, le texte des questions rattachées, le glossaire (onglet « Glossaire »), les étiquettes de valeurs acceptées et la provenance de chaque valeur. Les effectifs de moins de 5 y sont masqués.

## 9. Avec vos propres données

La démarche est la même avec votre fichier : SPSS (`.sav`), CSV (y compris ceux d'Excel en français, avec point-virgule et virgule décimale), Stata (`.dta`), SAS (`.sas7bdat`) ou Excel (`.xlsx` : la première feuille, avec les noms des variables sur la première ligne). Et avec votre questionnaire, en PDF ou en texte.

- Travaillez dans un dossier prévu pour ces données, selon les règles de votre équipe et de votre comité d'éthique. Le fichier projet, les codebooks et le dossier `.dd-envois` (ce qui a été envoyé au modèle) restent à côté des données.
- L'outil ne modifie jamais votre fichier de données.
- Les variables qui ressemblent à des identifiants, à du texte libre ou à des dates de naissance sont repérées automatiquement : seules leurs métadonnées sont utilisées, et les effectifs de moins de 5 sont masqués.
- Sur une grande base, les rattachements proposés par l'IA sont souvent justes, mais pas toujours : les questions répétées à l'identique (« À quelle fréquence cette personne vous apporte du soutien ? », une fois par personne) sont le cas le plus difficile. Vérifiez-les avant les libellés.
- La liste des projets récents est gardée sur votre ordinateur (dossier `%APPDATA%\ddict`) et ne contient que des chemins de fichiers ; **Effacer la liste**, sur l'accueil, la vide.

## Mettre à jour ou désinstaller

- **Mettre à jour** : téléchargez et décompressez la nouvelle archive, puis double-cliquez sur son `installer.bat`. Vos fichiers projet sont conservés.
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
```

`--apercu` (à `rattacher` ou `enrichir`, sans `--modele`) écrit les messages qui seraient envoyés dans le dossier `etude-sommeil.dd-envois\apercu`, sans rien envoyer. `ddict exporter --sans-texte G2` omet le texte des questions d'un groupe pour un seul export.

## En cas de problème

| Ce qui arrive | Que faire |
|---|---|
| « Windows a protégé votre ordinateur » au double-clic sur `installer.bat` | **Informations complémentaires**, puis **Exécuter quand même** (section 1). |
| `installer.bat` s'arrête sur un message rouge | Vérifiez la connexion Internet, puis relancez-le. Si le message persiste, notez-le et transmettez-le. Certains postes d'établissement interdisent les scripts : adressez-vous au soutien informatique. |
| « Ce dossier ne contient pas l'outil » | `installer.bat` a été copié hors de l'archive : lancez celui du dossier de l'outil décompressé (section 1, étape 2). |
| La fenêtre « Ouvrir » ne s'affiche pas | Elle est peut-être derrière le navigateur : regardez dans la barre des tâches. Sinon, collez le chemin du fichier dans le champ sous le bouton (clic droit sur le fichier dans l'Explorateur, **Copier en tant que chemin d'accès**). |
| Le navigateur ne s'ouvre pas au double-clic sur l'icône | Ouvrez-le vous-même à l'adresse `http://127.0.0.1:8501`. |
| « Un projet existe déjà pour cette base » | L'outil n'écrase pas votre travail : **Ouvrir le projet existant**, ou **Remplacer le projet** si vous voulez vraiment repartir de zéro (vos décisions seront perdues). |
| Page IA locale : « Ollama ne répond pas » | Lancez Ollama depuis le menu Démarrer, attendez son icône près de l'horloge, puis **Vérifier de nouveau**. |
| Page IA locale : aucun modèle installé | Relancez `installer.bat` et répondez `o` pour télécharger le modèle, ou suivez les indications de la page. |
| Une grille du questionnaire est « à vérifier » | Ses titres de colonnes sont collés dans le PDF : l'outil ne propose alors pas d'étiquettes de valeurs pour ses variables. Un `.txt` copié depuis Word évite le problème. |
| « Impossible d'écrire les fichiers » à l'export | Le codebook est probablement ouvert dans Excel : fermez-le, puis recommencez. |
| L'outil semble figé | Fermez la petite fenêtre noire de la barre des tâches, puis double-cliquez de nouveau sur l'icône. Les décisions déjà prises sont enregistrées. |

Pour toute autre difficulté, notez ce que vous avez fait et le message obtenu, et transmettez-les à la personne qui vous a fourni l'outil.
