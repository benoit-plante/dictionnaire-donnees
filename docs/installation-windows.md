# Installer et utiliser l'outil sous Windows

Ce guide s'adresse aux personnes qui ne programment pas. Il mène de l'installation jusqu'à un premier codebook, produit à partir de la base fictive fournie avec l'outil. Comptez une demi-heure, plus le téléchargement du modèle d'IA si vous choisissez de l'utiliser.

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

1. Téléchargez l'archive de l'outil (fichier `.zip`) depuis la page des versions du projet sur GitHub, puis décompressez-la : clic droit sur le fichier, **Extraire tout**. Vous obtenez un dossier comme `dictionnaire-donnees-0.1.0`.
2. Dans PowerShell, placez-vous dans ce dossier. Si vous l'avez extrait dans Téléchargements :

   ```
   cd "$HOME\Downloads\dictionnaire-donnees-0.1.0"
   ```

   Si le dossier est ailleurs, tapez `cd "`, glissez le dossier dans la fenêtre PowerShell (son chemin s'écrit tout seul), tapez `"` puis Entrée.
3. Installez l'outil avec ses deux options (l'IA locale et l'interface de révision) :

   ```
   uv tool install ".[ia,revision]"
   uv tool update-shell
   ```

   La première commande télécharge Python et les bibliothèques nécessaires ; cela prend une ou deux minutes. La seconde rend la commande `ddict` utilisable partout.
4. **Fermez PowerShell, puis rouvrez-le**, et vérifiez :

   ```
   ddict --version
   ```

   La réponse doit être `ddict 0.1.0`.

## 4. Premier codebook, à partir de la base fictive

La base fictive est une petite étude inventée sur le sommeil (200 participants fictifs). Elle permet d'essayer l'outil sans aucune donnée réelle.

1. Créez un dossier de travail et copiez-y la base :

   ```
   mkdir "$HOME\Documents\essai-ddict"
   copy "$HOME\Downloads\dictionnaire-donnees-0.1.0\exemples\bases-fictives\etude-sommeil.sav" "$HOME\Documents\essai-ddict\"
   cd "$HOME\Documents\essai-ddict"
   ```

2. Faites lire la base par l'outil :

   ```
   ddict profiler etude-sommeil.sav
   ```

   L'outil crée `etude-sommeil.dd.json`, le **fichier projet**. Il contient tout ce que l'outil a calculé (types, manquants, modalités, étiquettes) et, plus tard, vos décisions. Il ne contient pas les réponses individuelles des participants.

3. Produisez le codebook :

   ```
   ddict exporter etude-sommeil.dd.json
   ```

   Deux fichiers apparaissent : `etude-sommeil.xlsx` (le codebook, à ouvrir avec Excel) et `etude-sommeil.md` (le même contenu en texte, lisible avec le Bloc-notes). Pour ouvrir le dossier dans l'Explorateur :

   ```
   explorer .
   ```

Votre premier codebook est fait, sans IA : tout ce qu'il contient a été calculé exactement à partir du fichier.

## 5. Facultatif : faire proposer des libellés par une IA locale

L'IA propose des libellés et des descriptions plus lisibles que les noms de variables. Elle tourne sur votre ordinateur, avec le logiciel libre **Ollama**. Le modèle ne reçoit jamais les réponses des participants, seulement des informations résumées (noms, étiquettes, proportions). Chaque proposition attend ensuite votre décision.

1. Installez Ollama depuis [ollama.com](https://ollama.com) (bouton **Download for Windows**), puis lancez-le : son icône apparaît près de l'horloge.
2. Téléchargez le modèle recommandé (environ 4,7 Go, une seule fois) :

   ```
   ollama pull qwen2.5:7b-instruct-q4_K_M
   ```

3. Pour voir **exactement** ce qui serait envoyé au modèle, sans rien envoyer :

   ```
   ddict enrichir etude-sommeil.dd.json --apercu
   ```

   Les messages sont écrits dans le dossier `etude-sommeil.dd-envois\apercu`.
4. Lancez l'enrichissement :

   ```
   ddict enrichir etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
   ```

   Les variables sont traitées par blocs de 12 ; chaque bloc affiche « réussi ». Comptez environ une minute pour la base fictive avec une carte graphique, plusieurs minutes sans. Si vous interrompez (Ctrl+C), relancez la même commande : les blocs terminés ne sont pas refaits.

## 6. Réviser dans le navigateur

```
ddict reviser etude-sommeil.dd.json
```

Votre navigateur s'ouvre sur l'interface de révision. Elle n'est accessible que depuis votre ordinateur. PowerShell affiche quelques lignes, dont certaines en anglais ; c'est normal. Laissez cette fenêtre ouverte pendant la révision.

- **À gauche** : le filtre (« À réviser » montre les variables qui ont des propositions en attente) et la liste des variables.
- **Pour chaque proposition** : « Accepter », « Rejeter », ou corriger le texte puis « Enregistrer ». Chaque décision est enregistrée aussitôt dans le fichier projet.
- **Encadré rouge** : la proposition demande une attention particulière, par exemple un libellé deviné pour une variable sans étiquette dans le fichier.
- **Champs documentés** : étendue théorique, seuils, références et notes. Ils sont réservés aux personnes, et l'étendue comme les seuils exigent une source (manuel, article).
- **Afficher : Groupes** : les échelles repérées par l'outil, leur alpha de Cronbach et les items probablement inversés.

Quand vous avez terminé, fermez l'onglet, revenez dans PowerShell et appuyez sur **Ctrl+C**. Produisez ensuite le codebook à jour :

```
ddict exporter etude-sommeil.dd.json
```

Le codebook ne contient que ce qui vient du fichier, ce qui a été calculé et ce que vous avez accepté ou saisi. Les propositions sans décision n'y figurent pas.

## 7. Avec vos propres données

La démarche est la même, avec votre fichier `.sav` ou `.csv` (y compris les CSV enregistrés par Excel en français, avec point-virgule et virgule décimale).

- Travaillez dans un dossier prévu pour ces données, selon les règles de votre équipe et de votre comité d'éthique. Le fichier projet, les codebooks et le dossier `.dd-envois` (ce qui a été envoyé au modèle) doivent rester avec les données.
- L'outil ne modifie jamais votre fichier de données.
- Les variables qui ressemblent à des identifiants, à du texte libre ou à des dates de naissance sont repérées automatiquement : seules leurs métadonnées sont utilisées, et les effectifs de moins de 5 sont masqués.

## Mettre à jour ou désinstaller

Pour une nouvelle version, décompressez la nouvelle archive, placez-vous dans son dossier avec `cd`, puis :

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
| « ddict n'est pas reconnu… » (ou « uv n'est pas reconnu… ») | Fermez et rouvrez PowerShell. Si le message persiste, refaites `uv tool update-shell`, puis rouvrez PowerShell. |
| « Le serveur http://127.0.0.1:11434/v1 ne répond pas. Ollama est-il lancé ? » | Lancez Ollama depuis le menu Démarrer, attendez son icône près de l'horloge, puis relancez la commande. |
| « Le modèle … est introuvable sur le serveur » | Le modèle n'est pas téléchargé, ou son nom est mal tapé : faites `ollama pull` avec exactement le même nom. |
| « L'option IA n'est pas installée » | Refaites l'étape 3 en gardant `".[ia,revision]"` dans la commande. |
| Le navigateur ne s'ouvre pas pendant la révision | Ouvrez-le vous-même à l'adresse `http://127.0.0.1:8501`. |
| « Port 8501 is already in use », ou l'interface affichée est celle d'un autre projet | Une révision est déjà ouverte dans une autre fenêtre PowerShell : arrêtez-la (Ctrl+C), ou utilisez un autre port avec `--port 8502`. |
| « Le projet … existe déjà » | `ddict profiler` refuse d'écraser votre travail. Pour repartir de zéro, ajoutez `--remplacer` (vos décisions seront perdues). |

Pour toute autre difficulté, notez la commande tapée et le message obtenu, et transmettez-les à la personne qui vous a fourni l'outil.
