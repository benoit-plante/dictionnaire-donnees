# Installer et utiliser l'outil sous Windows

Ce guide s'adresse aux personnes qui ne programment pas. Il mène de l'installation jusqu'à un codebook complet, produit à partir de la base fictive et de son questionnaire, fournis avec l'outil. Comptez une heure, plus le téléchargement du modèle d'IA si vous choisissez de l'utiliser.

Toutes les commandes se tapent dans **PowerShell**, la fenêtre de commandes de Windows. Copiez-les telles quelles, puis appuyez sur Entrée.

## Ce qu'il faut

- Windows 10 ou 11.
- Une connexion Internet **pendant l'installation seulement**. Ensuite, l'outil ne communique plus avec Internet : il lit vos fichiers et écrit ses résultats sur votre ordinateur.
- Pour l'IA, facultative : environ 5 Go d'espace libre et 16 Go de mémoire vive (8 Go suffisent, en plus lent). Une carte graphique accélère le travail, mais n'est pas nécessaire.

## 1. Ouvrir PowerShell

Cliquez sur **Démarrer**, tapez `PowerShell`, puis cliquez sur **Windows PowerShell**. Une fenêtre bleue ou noire s'ouvre : c'est là que vous taperez les commandes.

## 2. Installer uv

uv est un petit outil libre qui installe Python et l'outil à votre place, sans réglage. Tapez :

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Fermez PowerShell, puis rouvrez-le** : Windows doit relire la liste des programmes installés. Vérifiez ensuite :

```
uv --version
```

Une ligne comme `uv 0.9.…` doit s'afficher.

## 3. Installer l'outil

1. Téléchargez l'archive de l'outil (fichier `.zip`, par exemple `dictionnaire-donnees-0.2.0.zip`) depuis la page des versions du projet sur GitHub, puis décompressez-la : clic droit sur le fichier, **Extraire tout**, puis **Extraire**.
2. Trouvez **le dossier de l'outil** : c'est celui qui contient le fichier `pyproject.toml` et les dossiers `docs` et `exemples`. Windows le place souvent à l'intérieur d'un autre dossier du même nom, par exemple `Téléchargements\dictionnaire-donnees-0.2.0\dictionnaire-donnees-0.2.0`. Si le dossier extrait ne contient qu'un seul dossier, ouvrez-le : c'est celui-là.
3. Dans PowerShell, placez-vous dans le dossier de l'outil : tapez `cd "`, glissez le dossier depuis l'Explorateur dans la fenêtre PowerShell (son chemin s'écrit tout seul), tapez `"` puis Entrée. Vérifiez ensuite que vous êtes au bon endroit :

   ```
   dir pyproject.toml
   ```

   Si PowerShell répond qu'il ne trouve pas le chemin, vous êtes un niveau trop haut : tapez `dir`, puis `cd` suivi du nom du dossier affiché, et vérifiez de nouveau.
4. Installez l'outil avec ses deux options (l'IA locale et l'interface de révision) :

   ```
   uv tool install ".[ia,revision]"
   uv tool update-shell
   ```

   La première commande télécharge Python et les bibliothèques nécessaires ; cela prend une ou deux minutes. La seconde rend la commande `ddict` utilisable partout.
5. **Fermez PowerShell, puis rouvrez-le**, et vérifiez :

   ```
   ddict --version
   ```

   La réponse doit être `ddict` suivi du numéro de la version téléchargée, par exemple `ddict 0.2.0`.

## 4. Premier codebook, à partir de la base fictive

La base fictive est une petite étude inventée sur le sommeil (200 participants fictifs), avec son questionnaire. Elle permet d'essayer l'outil sans aucune donnée réelle.

1. Créez un dossier de travail et placez-vous dedans :

   ```
   mkdir "$HOME\Documents\essai-ddict"
   cd "$HOME\Documents\essai-ddict"
   explorer .
   ```

   L'Explorateur s'ouvre sur ce dossier, vide pour l'instant. Dans une autre fenêtre de l'Explorateur, ouvrez le dossier de l'outil (section 3, étape 2), puis `exemples\bases-fictives`. Copiez les fichiers `etude-sommeil.sav` et `questionnaire-sommeil.pdf` dans le dossier `essai-ddict`.

2. Faites lire la base par l'outil :

   ```
   ddict profiler etude-sommeil.sav
   ```

   L'outil crée `etude-sommeil.dd.json`, le **fichier projet**. Il contient tout ce que l'outil a calculé (types, manquants, modalités, étiquettes) et, plus tard, vos décisions. Il ne contient pas les réponses individuelles des participants.

3. Produisez le codebook :

   ```
   ddict exporter etude-sommeil.dd.json
   ```

   Deux fichiers apparaissent dans le dossier `essai-ddict` : `etude-sommeil.xlsx` (le codebook, à ouvrir avec Excel) et `etude-sommeil.md` (le même contenu en texte, lisible avec le Bloc-notes).

Votre premier codebook est fait, sans IA : tout ce qu'il contient a été calculé exactement à partir du fichier. Les sections suivantes l'enrichissent ; on peut s'arrêter à n'importe laquelle et exporter.

## 5. Ajouter le questionnaire

Le questionnaire de l'étude dit ce que chaque variable veut dire : le texte exact des questions, le sens des sigles, les options de réponse. L'outil le lit sans IA, en PDF (export de SurveyMonkey, LimeSurvey, REDCap…) ou en texte (`.txt` copié depuis Word).

```
ddict questionnaire etude-sommeil.dd.json questionnaire-sommeil.pdf
```

L'outil affiche le nombre de questions trouvées, les questions à vérifier (par exemple une grille dont les titres de colonnes sont collés), les **sigles définis dans le questionnaire** (« thérapie cognitivo-comportementale (TCC) ») et les sigles des noms de variables qui n'ont pas de définition. Le texte du questionnaire reste dans le fichier projet ; seules les questions rattachées à des variables iront dans le codebook, jamais la page de consentement.

Il faut ensuite relier chaque variable à sa question :

```
ddict rattacher etude-sommeil.dd.json
```

Sans IA, l'outil calcule pour chaque variable quelques questions candidates, que vous choisirez dans l'interface (section 7). Avec l'IA (section 6), ajoutez `--modele qwen2.5:7b-instruct-q4_K_M` : le modèle choisit parmi ces candidates, et vous acceptez ou corrigez chaque choix.

## 6. Facultatif : l'IA locale

L'IA propose des rattachements aux questions, puis des libellés et des descriptions plus lisibles que les noms de variables. Elle tourne sur votre ordinateur, avec le logiciel libre **Ollama**. Le modèle ne reçoit jamais les réponses des participants, seulement des informations résumées (noms, étiquettes, proportions, questions). Chaque proposition attend votre décision. **Elle ne définit jamais un sigle** : c'est là qu'elle se trompe le plus, et le glossaire vient seulement du questionnaire et de vous.

1. Installez Ollama depuis [ollama.com](https://ollama.com) (bouton **Download for Windows**), puis lancez-le : son icône apparaît près de l'horloge.
2. Téléchargez le modèle recommandé (environ 4,7 Go, une seule fois) :

   ```
   ollama pull qwen2.5:7b-instruct-q4_K_M
   ```

3. Faites proposer les rattachements aux questions :

   ```
   ddict rattacher etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
   ```

4. **Révisez d'abord le glossaire et les rattachements** dans l'interface (section 7), puis revenez ici. L'ordre compte : pour les libellés, le modèle reçoit le texte des questions dont vous avez accepté le rattachement, et le sens des sigles que vous avez acceptés. Un rattachement faux lui donnerait une fausse question.
5. Faites proposer les libellés et les descriptions :

   ```
   ddict enrichir etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
   ```

   Les variables sont traitées par blocs de 8 ; chaque bloc affiche « réussi ». Comptez environ une minute pour la base fictive avec une carte graphique, plusieurs minutes sans. Si vous interrompez (Ctrl+C), relancez la même commande : les blocs terminés ne sont pas refaits.

Pour voir **exactement** ce qui serait envoyé au modèle, sans rien envoyer, ajoutez `--apercu` à `rattacher` ou à `enrichir` (sans `--modele`) : les messages sont écrits dans le dossier `etude-sommeil.dd-envois\apercu`.

## 7. Réviser dans le navigateur

```
ddict reviser etude-sommeil.dd.json
```

Votre navigateur s'ouvre sur l'interface de révision. Elle n'est accessible que depuis votre ordinateur. PowerShell affiche quelques lignes, dont certaines en anglais ; c'est normal. Laissez cette fenêtre ouverte pendant la révision.

- **À gauche** : ce qu'on affiche (« Variables », « Groupes » ou « Glossaire »), le filtre (« À réviser » montre les variables qui ont des propositions en attente ; « Sans question » celles qui ne sont pas encore rattachées) et la liste des variables.
- **Glossaire** : accepter, corriger ou rejeter chaque sigle trouvé dans le questionnaire, et ajouter ceux qui manquent (l'outil liste les sigles probables des noms de variables sans définition). À faire en premier.
- **Question du questionnaire**, sur la fiche de chaque variable : le texte exact de la question rattachée, à accepter ou rejeter ; une liste permet d'en choisir une autre, les questions candidates en tête, ou « Aucune question » (identifiant, date de passation, score calculé).
- **Étiquettes de valeurs tirées des options de réponse** : quand le fichier n'a pas d'étiquettes (un CSV, par exemple), l'outil propose « 1 = Pas du tout … 5 = Extrêmement » d'après les options de la question, seulement dans les cas sûrs. La mention « ordre supposé, à vérifier » est sérieuse : **vérifiez l'ordre des codes dans votre plateforme d'enquête ou votre script de recodage avant d'accepter**. Une base recodée peut avoir 0 = « Autre » là où le questionnaire place « Autre » en dernier.
- **Pour chaque proposition de l'IA** : « Accepter », « Rejeter », ou corriger le texte puis « Enregistrer ». Chaque décision est enregistrée aussitôt dans le fichier projet.
- **Encadré rouge** : la proposition demande une attention particulière, par exemple un libellé deviné pour une variable sans étiquette, ou le sens d'un sigle que personne n'a donné à l'IA.
- **Signalements** : anomalies calculées, dont les **variantes d'écriture** d'une même réponse (« Français », « français », « Francais »), à corriger dans vos données si vous le souhaitez.
- **Champs documentés** : étendue théorique, seuils, références et notes. Ils sont réservés aux personnes, et l'étendue comme les seuils exigent une source (manuel, article).
- **Afficher : Groupes** : les échelles repérées par l'outil, leur alpha de Cronbach et les items probablement inversés. Confirmer une inversion la **documente** dans le codebook ; l'outil ne recode jamais les données. Le recodage (par exemple 6 − x pour une échelle de 1 à 5) reste à faire dans votre logiciel d'analyse. Pour un **instrument protégé par le droit d'auteur** (CBCL, BDI…), cochez « Ne pas reproduire le texte des questions de ce groupe » : le codebook donnera la référence de chaque question (`Q12.r3, p. 4`), sans son texte. Reproduire les items d'un instrument protégé relève de votre équipe.

Quand vous avez terminé, fermez l'onglet, revenez dans PowerShell et appuyez sur **Ctrl+C**. Produisez ensuite le codebook à jour :

```
ddict exporter etude-sommeil.dd.json
```

Le codebook ne contient que ce qui vient du fichier, ce qui a été calculé et ce que vous avez accepté ou saisi : libellés, texte des questions rattachées, glossaire (onglet « Glossaire »), étiquettes de valeurs acceptées. Les propositions sans décision n'y figurent pas. Pour omettre le texte des questions d'un groupe dans un seul export, sans changer le projet : `ddict exporter etude-sommeil.dd.json --sans-texte G2`.

## 8. Avec vos propres données

La démarche est la même avec votre fichier : SPSS (`.sav`), CSV (y compris les CSV enregistrés par Excel en français, avec point-virgule et virgule décimale), Stata (`.dta`), SAS (`.sas7bdat`) ou Excel (`.xlsx` : la première feuille, avec les noms des variables sur la première ligne). Et avec votre questionnaire, en PDF ou en texte.

- Travaillez dans un dossier prévu pour ces données, selon les règles de votre équipe et de votre comité d'éthique. Le fichier projet, les codebooks et le dossier `.dd-envois` (ce qui a été envoyé au modèle) doivent rester avec les données.
- L'outil ne modifie jamais votre fichier de données.
- Les variables qui ressemblent à des identifiants, à du texte libre ou à des dates de naissance sont repérées automatiquement : seules leurs métadonnées sont utilisées, et les effectifs de moins de 5 sont masqués.
- Sur une grande base, les rattachements proposés par l'IA sont souvent justes, mais pas toujours : les questions répétées à l'identique (« À quelle fréquence cette personne vous apporte du soutien ? », une fois par personne) sont le cas le plus difficile. Vérifiez-les avant d'enrichir.

## Mettre à jour ou désinstaller

Pour une nouvelle version, décompressez la nouvelle archive, placez-vous dans le dossier de l'outil comme à la section 3 (celui qui contient `pyproject.toml`), puis :

```
uv tool install --reinstall ".[ia,revision]"
```

Vos fichiers projet sont conservés. Pour désinstaller l'outil :

```
uv tool uninstall ddict
```

## En cas de problème

| Message | Que faire |
|---|---|
| « … does not appear to be a Python project » pendant l'installation | Vous n'êtes pas dans le dossier de l'outil, souvent un niveau trop haut : voir la section 3, étapes 2 et 3. |
| « ddict n'est pas reconnu… » (ou « uv n'est pas reconnu… ») | Fermez et rouvrez PowerShell. Si le message persiste, refaites `uv tool update-shell`, puis rouvrez PowerShell. |
| « Le serveur http://127.0.0.1:11434/v1 ne répond pas. Ollama est-il lancé ? » | Lancez Ollama depuis le menu Démarrer, attendez son icône près de l'horloge, puis relancez la commande. |
| « Le modèle … est introuvable sur le serveur » | Le modèle n'est pas téléchargé, ou son nom est mal tapé : faites `ollama pull` avec exactement le même nom. |
| « L'option IA n'est pas installée » | Refaites l'étape 3 en gardant `".[ia,revision]"` dans la commande. |
| Le navigateur ne s'ouvre pas pendant la révision | Ouvrez-le vous-même à l'adresse `http://127.0.0.1:8501`. |
| « Port 8501 is already in use », ou l'interface affichée est celle d'un autre projet | Une révision est déjà ouverte dans une autre fenêtre PowerShell : arrêtez-la (Ctrl+C), ou utilisez un autre port avec `--port 8502`. |
| « Le projet n'a pas de questionnaire » | Lisez-le d'abord : `ddict questionnaire projet.dd.json questionnaire.pdf` (section 5). |
| « Le projet a déjà un questionnaire » | Pour en lire une nouvelle version, ajoutez `--remplacer`. Les rattachements qui renvoyaient à l'ancienne version sont retirés, et l'outil le dit. |
| « Groupe inconnu » avec `--sans-texte` | Les groupes s'appellent G1, G2… : voir « Afficher : Groupes » dans l'interface, ou l'onglet « Groupes » du codebook. |
| Une grille du questionnaire est « à vérifier » | Ses titres de colonnes sont collés dans le PDF : l'outil ne propose alors pas d'étiquettes de valeurs pour ses variables. Un `.txt` copié depuis Word évite le problème. |
| « Le projet … existe déjà » | `ddict profiler` refuse d'écraser votre travail. Pour repartir de zéro, ajoutez `--remplacer` (vos décisions seront perdues). |

Pour toute autre difficulté, notez la commande tapée et le message obtenu, et transmettez-les à la personne qui vous a fourni l'outil.
