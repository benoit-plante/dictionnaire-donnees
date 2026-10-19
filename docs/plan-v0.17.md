# Plan de la v0.17

> Statut : **validé par l'auteur le 2026-10-18**, avec les recommandations du § 9 : décisions D-129 à D-133 adoptées. Même cap que les v0.11 à v0.16 : **aucune IA ajoutée** ; ni le calcul, ni les exports, ni la confidentialité, ni le format du fichier projet ou du carnet ne changent.

## 1. Pourquoi cette version

Une équipe mène souvent plusieurs études à la fois, ou plusieurs vagues d'une même étude. Deux manques :

1. **Rien ne dit où en est chaque projet.** L'accueil montre les 10 derniers projets ouverts (D-024), avec leur dossier et une date, sans rien de leur avancement. Un projet sort de la liste dès qu'on en ouvre dix autres.
2. **Une décision peut se perdre sans message.** `save_project` et `save_notebook` réécrivent tout le fichier, sans regarder ce qu'il contient sur le disque. Deux onglets sur le même projet, deux personnes sur un dossier OneDrive ou réseau, ou la ligne de commande pendant que l'interface est ouverte : la dernière écriture efface les décisions de l'autre, sans un mot.

Le second manque est le plus grave : il touche des décisions déjà prises. Il passe donc en premier (partie C), avant de mettre plusieurs projets en avant (parties A et B).

## 2. Ce qui ne change pas

- Le format du fichier projet (`.dd.json`) et du carnet (`-carnet.json`) : rien n'y est ajouté. Ce que l'outil retient de l'état du fichier sur le disque vit en mémoire, jamais dans le fichier.
- Le calcul, les exports, la porte de confidentialité, les règles du modèle. Aucun appel au modèle n'est ajouté.
- La liste des projets récents (D-024) : même fichier, même limite de 10, même bouton « Effacer la liste ». Elle reste sous le nouveau tableau, pour ce qui n'est pas suivi.
- Un seul projet par séance (`common.open_project` vide la séance).
- Les tests existants passent sans être modifiés, sauf ceux de l'accueil (le tableau vient en tête) et ceux qui vérifient qu'aucune vue n'enregistre autrement que par la fonction commune (§ 5.2).

## 3. Ce qui change pour la personne

- **Partie C.** Si le projet ou le carnet a été modifié ailleurs depuis qu'elle l'a ouvert, l'outil le dit dès l'affichage suivant, et refuse d'enregistrer par-dessus : « Ce projet a été modifié ailleurs depuis que vous l'avez ouvert (autre onglet, autre personne ou ligne de commande). Votre dernière décision n'est pas enregistrée. » Le message rappelle ce qu'elle venait de saisir ; « Recharger le projet » relit le fichier. La ligne de commande refuse de même, avec un code de sortie non nul. Un enregistrement interrompu (fichier `.tmp` resté) est signalé à l'ouverture.
- **Partie A.** Elle choisit les projets qu'elle suit : chaque projet créé dans l'outil l'est d'office ; « Suivre ce projet » ajoute un projet récent ou le projet ouvert ; « Chercher les projets dans un dossier… » liste ceux d'un dossier, elle coche ceux à suivre. Un projet déplacé reste dans la liste, « introuvable », avec « Le retrouver… » et « Ne plus suivre ».
- **Partie B.** L'accueil commence par « Mes projets » : une ligne par projet suivi, avec sa phase, la complétude de son codebook, ce qui attend, l'état de son plan et de son carnet, la présence de sa base et sa dernière modification. Un clic ouvre le projet sur sa première tâche. Aucune base n'est lue pour faire ce tableau.

## 4. Ce que j'ai vérifié dans le code, en plus de la demande

- **`find_database` lit la base** : elle en calcule l'empreinte SHA-256 pour vérifier que c'est la bonne (`analysis/data.py`, l. 109). Le tableau ne peut donc pas s'en servir telle quelle. Il reprend sa règle d'emplacement (le nom de `project.source.name` à côté du projet) avec un simple contrôle d'existence : « trouvée » veut dire « un fichier de ce nom est là » ; son identité reste vérifiée à l'ouverture, comme aujourd'hui. L'aide de la colonne le dit.
- **`recents.load()` écarte les fichiers absents** : la liste des suivis ne doit pas le faire (un projet introuvable reste, § 6.1).
- **`recents.add` passe par `Path.resolve()`.** Sous Windows, `resolve()` peut changer un lecteur réseau (`Z:\`) en chemin `\\serveur\partage`. Les suivis gardent le chemin tel qu'il a été choisi, et comparent les chemins par `os.path.normcase(os.path.abspath(…))`.
- **`workflow.tasks(project, project_path)`** regarde déjà, sans la base, le carnet, l'ébauche d'article et son rapport de vérification (dates seulement). Sans `NotebookState` (qui exige la base), elle omet « Chiffres à confirmer au carnet » : le tableau dit l'état du carnet dans sa propre colonne (§ 7.2).
- **Environ trente endroits enregistrent** (`save_project` : 21, `save_notebook` : 10), dont une vingtaine dans `review/ui/`. Le contrôle doit donc vivre dans `save_project` et `save_notebook` eux-mêmes, pas dans chaque vue.
- **Un même statut peut changer sans changer la taille du fichier** : `"validated"` et `"corrected"` ont tous deux 9 lettres. Corriger un libellé déjà validé avec un texte de même longueur ne change pas non plus la taille. D'où le choix du § 5.1.

## 5. Conception — partie C, ne jamais écraser sans prévenir

### 5.1 Le contrôle à l'écriture (D-129)

| Moyen | Faux « modifié » (alarme pour rien) | Changement manqué | Coût |
|---|---|---|---|
| Date et taille | OneDrive, l'antivirus ou une copie peuvent toucher la date sans changer le contenu | Même taille, date identique ou trop grossière (2 s sur certains partages réseau, FAT des clés USB) : `validated` → `corrected` passe inaperçu | Aucun |
| **Empreinte du contenu (SHA-256)** | Aucun : seul un vrai changement d'octets compte | Aucun | Relire le fichier avant d'écrire : moins d'une milliseconde pour 139 Ko, quelques millisecondes pour 2 Mo |

Proposition : **l'empreinte du contenu**, toujours, au moment d'écrire.

- `load_project` lit les octets du fichier, en garde l'empreinte, puis les décode comme aujourd'hui. L'empreinte et le chemin sont attachés à l'objet `Project` comme attribut privé de pydantic (`PrivateAttr`) : ils ne sont ni validés ni écrits dans le fichier. Le format ne change pas.
- `save_project(project, path)` relit le fichier, compare son empreinte à celle retenue. Différente, ou fichier disparu : **rien n'est écrit**, l'exception `ProjectChanged` est levée. Égale : le fichier est écrit comme aujourd'hui (fichier temporaire, puis remplacement), et l'empreinte retenue devient celle de ce qui vient d'être écrit.
- **Un projet neuf** (aucune empreinte retenue) ne s'écrit que si le fichier n'existe pas, ou avec `overwrite=True`, que seules la création confirmée (« Remplacer le projet existant ») et « Recommencer l'essai » passent. Ces deux endroits vérifient déjà l'existence aujourd'hui.
- **Le carnet suit la même règle** (`load_notebook`, `save_notebook`, `NotebookChanged`). Un carnet neuf, pas encore écrit, est refusé si un carnet est apparu entre-temps : c'est le cas de deux sessions qui ajoutent chacune leur première analyse.
- **La date et la taille** ne servent qu'à décider s'il faut relire : pour l'avertissement dès l'affichage (§ 5.2) et pour le cache du tableau (§ 7.3). Une date qui bouge sans changement de contenu (OneDrive) fait relire et recalculer l'empreinte, rien de plus : jamais d'alarme.

Test central, sans Streamlit : deux objets chargés du même fichier ; le premier enregistre ; le second est refusé, et le fichier contient exactement ce que le premier a écrit. Même chose pour le carnet, pour un projet neuf contre un fichier apparu, pour un fichier supprimé, et pour une date changée sans changement de contenu (aucun refus).

### 5.2 Dans l'interface (D-130)

**Un seul chemin pour enregistrer.** `c.save()` et `c.save_notebook(notebook)` dans `review/ui/common.py` ; les vingt appels directs des vues passent par eux. Un test lit les vues et refuse tout `save_project(` ou `save_notebook(` hors de `common.py`, comme celui des boutons de messages (A5 de la v0.16).

**Quand l'enregistrement est refusé :**

1. Rien n'est écrit. L'objet en mémoire a déjà reçu la décision (les fonctions de `logic` modifient le projet avant l'enregistrement) : la séance passe en état « en conflit », et tout enregistrement suivant est refusé de même, puisque l'empreinte retenue est toujours l'ancienne.
2. En tête de chaque page, un bandeau (avertissement, pas une erreur rouge) : « Ce projet a été modifié ailleurs depuis que vous l'avez ouvert (autre onglet, autre personne ou ligne de commande). Votre dernière décision n'est pas enregistrée. » Puis le rappel :
   > Votre décision : **Variables, age** — « Accepter » ; Libellé : « Âge en années ».
3. Le rappel est fait au moment du clic, avant que la décision ne s'applique : l'endroit (`c.Place`, du lot C de la v0.16), le bouton cliqué, et les champs de cet endroit dont la valeur diffère de celle du projet (le mécanisme des brouillons, D-124), avec leur libellé. `c.field` retient pour cela le libellé de chaque champ. Une décision sans champ (« C'est un code manquant », « Ajouter au carnet ») se rappelle par son bouton et son endroit.
4. **« Recharger le projet »** relit le fichier : la séance repart du projet sur le disque, sur la même page. Le rappel reste affiché, dans un encadré « Décision à refaire », jusqu'à ce qu'on le ferme : on refait la décision en connaissance de cause. Les autres brouillons non enregistrés de la séance sont rappelés de même, en texte.
5. **Jamais de fusion automatique**, et le rappel n'est pas remis dans les champs : dans une section de plusieurs champs, il remettrait aussi les anciennes valeurs des champs que l'autre personne vient de changer, et « Enregistrer » les effacerait.

**Prévenir avant la saisie.** À chaque affichage, l'outil regarde la date et la taille du projet et du carnet ; si elles ont bougé, il relit et compare l'empreinte. Changé : le même bandeau, sans « Votre dernière décision n'est pas enregistrée » s'il n'y en a pas, avec « Recharger le projet ». La personne le voit souvent avant d'avoir saisi quoi que ce soit. Le coût est un `stat` par fichier et par affichage.

**Test AppTest** : deux sessions sur le même projet (deux `AppTest`) ; la première accepte un libellé ; la seconde en accepte un autre et voit le bandeau et le rappel ; le fichier garde la décision de la première ; « Recharger le projet » montre la décision de la première et l'encadré « Décision à refaire ». Même chose pour le carnet (deux « Ajouter au carnet »).

### 5.3 La ligne de commande

Chaque commande qui écrit charge, calcule, puis enregistre : le contrôle de `save_project` s'applique sans rien ajouter. `main` attrape `ProjectChanged` et `NotebookChanged`, écrit « Le projet a été modifié ailleurs pendant la commande (interface ouverte ?) : rien n'est enregistré. Relancez la commande. », et rend `EXIT_ERROR`. Test : une commande dont le chargement et l'enregistrement sont séparés par une écriture d'un autre objet est refusée, le fichier intact.

### 5.4 L'enregistrement interrompu et le fichier occupé

- **À l'ouverture**, dans l'interface et la ligne de commande : si `<projet>.dd.json.tmp` ou `<projet>-carnet.json.tmp` existe, l'outil le dit : « Un enregistrement a été interrompu (le …) : le fichier etude.dd.json.tmp est resté. Le projet ouvert est le dernier enregistré en entier ; le fichier .tmp peut être supprimé. » Rien n'est supprimé par l'outil. Le prochain enregistrement réécrit ce fichier temporaire, comme aujourd'hui.
- **Fichier occupé** : sous OneDrive ou sur un partage, le remplacement peut échouer quelques instants (`PermissionError`, le fichier tenu par la synchronisation). Aujourd'hui, c'est une erreur de la page. Proposition : un message (« Le fichier est occupé, peut-être par la synchronisation de OneDrive : rien n'est enregistré, réessayez dans un instant. »), le fichier projet intact, l'empreinte retenue inchangée. *Précisé à l'étape C3 :* l'outil essaie trois fois, à 0,2 s d'intervalle, avant de le dire ; il retire alors son propre fichier temporaire (écrit en entier, ce n'est pas un enregistrement interrompu) ; dans l'interface, le projet est relu depuis le disque, pour que la page ne montre jamais comme décidé ce qui n'est pas écrit, et la saisie reste dans ses champs. Un fichier illisible un instant pendant l'avertissement dès l'affichage ne donne pas d'alarme : l'enregistrement vérifiera.

### 5.5 Ce que je ne propose pas : un verrou consultatif

Un fichier « Ouvert aussi par … depuis … » dirait plus tôt qu'une autre personne travaille. Je ne le recommande pas pour la v0.17 :

- Streamlit ne sait pas qu'un onglet se ferme : le verrou resterait après chaque fermeture de fenêtre, et après chaque plantage. Il faudrait un battement régulier, qui écrit dans le dossier partagé toutes les minutes.
- Sur OneDrive, ce fichier se synchroniserait chez les collègues, avec un nom de personne ou d'ordinateur dedans : une donnée personnelle de plus dans le dossier de l'étude.
- Un verrou faux (resté) apprend vite à ignorer l'avertissement, et le contrôle à l'écriture protège déjà les décisions dans tous les cas.

À reconsidérer après usage, si les refus deviennent fréquents.

## 6. Conception — partie A, les projets suivis

### 6.1 La liste (D-131)

- Module `ddict.tracked`, comme `recents` : même dossier de configuration (`recents.config_dir()`, `DDICT_CONFIG_DIR` pour les tests), fichier `projets-suivis.json`.
- Contenu : `{"format": 1, "projets": ["C:\\…\\etude.dd.json", …]}`, chemins absolus des fichiers projet, triés (sans tenir compte de la casse) pour une écriture déterministe : indentation 2, UTF-8, `ensure_ascii=False`, LF. Jamais de nom d'étude, de phase ni de chiffre : le tableau les relit dans les projets. La version du format permet d'ajouter plus tard sans casser.
- Pas de limite de nombre. Un projet absent reste dans la liste.
- Comme les récents : sur cet ordinateur seulement, jamais dans un projet ni un export ; une écriture qui échoue n'est pas une erreur (la liste est une commodité, le message le dit).
- **On suit** : d'office à la création d'un projet, dans l'interface et par `ddict profiler` ; sauf le projet d'essai de la base fictive, qui reste dans les récents ; par « Suivre ce projet » sur une ligne des récents et dans la barre latérale du projet ouvert ; par la recherche dans un dossier (§ 6.2) ; par `ddict projets suivre`.
- **On arrête de suivre** par « Ne plus suivre » (une ligne du tableau, la barre latérale, `ddict projets retirer`) : le fichier projet n'est jamais touché, ni le carnet, ni les récents.
- **Introuvable** : « Le retrouver… » ouvre la fenêtre « Ouvrir » de Windows sur les `.dd.json` ; le nouveau chemin remplace l'ancien. L'ancien fichier n'étant plus là, l'outil ne peut pas vérifier que c'est le même projet : il refuse seulement un fichier qui n'est pas un projet lisible, et montre le nom de sa base pour que la personne juge. Si le projet choisi est déjà suivi, l'ancienne ligne disparaît simplement.

### 6.2 Chercher les projets dans un dossier (D-132)

- « Chercher les projets dans un dossier… » ouvre la fenêtre « Choisir un dossier » de Windows (`tkinter.filedialog.askdirectory`, ajoutée à `review/ui/dialog.py`).
- **Ce qui est cherché** : les fichiers dont le nom finit par `.dd.json`, dans le dossier et ses sous-dossiers jusqu'à **4 niveaux** sous le dossier choisi (assez pour `Études\2026\Vague 2\donnees\`).
- **Ce qui est ignoré** : les dossiers cachés ou système, ceux dont le nom commence par `.` ou `$` (`$RECYCLE.BIN`, `.git`), `AppData`, `node_modules`, les dossiers d'échanges de l'outil (`*.dd-envois`) ; les raccourcis de dossier, liens et jonctions, jamais suivis (les jonctions de « Documents », comme « Ma musique », feraient tourner en rond) ; les dossiers illisibles, sans erreur ; les fichiers `.tmp`.
- **Limites** : au plus 500 projets trouvés ou 20 000 dossiers parcourus ; au-delà, la recherche s'arrête et le dit (« Recherche arrêtée après 20 000 dossiers : choisissez un dossier plus précis »).
- **Rien n'est lu pendant la recherche** : seuls les noms des fichiers et des dossiers sont parcourus (`os.scandir`). Un fichier OneDrive « disponible en ligne seulement » n'est pas téléchargé.
- **Résultat** : une liste à cocher, nom et dossier, **rien de coché au départ** (D-126) ; les projets déjà suivis sont cochés et grisés, « déjà suivi ». « Suivre ces N projets » ajoute les cochés, rien d'autre.

### 6.3 Ligne de commande

`ddict projets` (`projects`), avec ses actions et leurs équivalents anglais, comme `ddict carnet` :

| Action | Anglais | Effet |
|---|---|---|
| `lister` | `list` | Imprime le tableau de l'accueil (§ 7.1), en texte, une ligne par projet suivi |
| `suivre <projet>` | `follow` | Ajoute un fichier projet (refusé s'il n'existe pas ou n'est pas un `.dd.json`) |
| `retirer <projet>` | `remove` | Retire un projet de la liste, présent ou non |
| `chercher <dossier>` | `search` | Liste les projets trouvés (§ 6.2) ; `--suivre` (`--follow`) les ajoute tous, sinon rien n'est ajouté |

## 7. Conception — partie B, le tableau « Mes projets »

### 7.1 Les colonnes

| Colonne | Contenu | Calculé par |
|---|---|---|
| Projet | Nom du fichier sans `.dd.json`, et son dossier en petit | Le chemin |
| Phase | Documenter, Analyser ou Rédiger (§ 7.2) | Les fichiers à côté du projet |
| Codebook | « 56 % » | `logic.codebook_progress`, le même chiffre que la barre de la barre latérale |
| En attente | « 3 · Sigles à valider : 2 » (le nombre de tâches, et la première) ; « — » si rien n'attend | `workflow.tasks(project, project_path)`, sans l'état recalculé du carnet |
| Plan | « — » ; « en cours (2 hypothèses) » ; « figé le 2026-10-18 » ; « figé, 1 amendement » | `project.plan` |
| Carnet | « — » ; « 3 retenues » ; « 3 retenues · 1 à confirmer · 2 à recalculer » | Le carnet (§ 7.2) |
| Base | « trouvée » ou « introuvable » | Existence du fichier `source.name` à côté du projet |
| Modifié | « 2026-10-18 14:32 » | La plus récente des dates du projet et du carnet |

Trié par « Modifié », le plus récent en haut. Une ligne illisible ou introuvable garde sa place par la date de son fichier, ou va en bas sans date.

Aide des colonnes (le `help` de `column_config`) :

- **Carnet** : « À recalculer : l'empreinte du codebook a changé depuis le dernier calcul de ces analyses. Leurs chiffres ont peut-être changé, peut-être pas : ouvrez le carnet pour le savoir. À confirmer : un nouveau calcul attend votre confirmation. »
- **Base** : « Trouvée : un fichier de ce nom est à côté du projet. Le tableau ne lit pas la base ; l'outil vérifie que c'est la bonne à l'ouverture. »
- **Phase** : la règle du § 7.2 en une phrase.

**Un clic sur une ligne** (`st.dataframe` avec `on_select`, une ligne à la fois) ouvre le projet sur la page de sa première tâche (`Task.mode`, avec son filtre) ; sans tâche, sur la première page de sa phase (Base, Plan ou Méthode). Sous le tableau, pour la ligne choisie : « Ne plus suivre », et pour une ligne introuvable « Le retrouver… ». « Chercher les projets dans un dossier… » vient après le tableau.

### 7.2 La phase d'un projet (D-133)

La phase dit **jusqu'où le projet est allé**, d'après les fichiers que l'outil a écrits, sans lire la base :

- **Rédiger** : l'ébauche d'article (`<projet>-article.docx`) existe à côté du projet ;
- sinon **Analyser** : le plan a au moins une hypothèse, ou le carnet au moins une analyse ;
- sinon **Documenter**.

La phase n'avance qu'avec ce que la personne a fait, et ne recule pas quand une nouvelle proposition attend : un projet en Analyser dont un libellé reste à valider reste en Analyser, et la colonne « En attente » dit la tâche. L'autre règle possible, la section de la première tâche (comme la barre latérale), ferait sauter un projet presque fini en « Documenter » pour un sigle oublié.

**Carnet** : « retenues » compte les analyses retenues pour l'article et non remplacées par un amendement ; « à confirmer », celles (et la Méthode) qui ont un calcul en attente (`pending`) ; « à recalculer », celles dont `computed.fingerprint` diffère de `fingerprint.fingerprint(project)` et qui n'ont pas de calcul en attente. Un carnet illisible ou d'un autre projet (`nb.belongs`) dit « carnet illisible » ou « carnet d'un autre projet », sans erreur.

### 7.3 Lecture et cache

- Module `ddict.overview`, sans Streamlit (la ligne de commande s'en sert) : `row(path) -> ProjectRow`. Il lit le projet (`load_project`) et le carnet (`load_notebook`), jamais la base ; il n'écrit rien, n'ajoute rien aux récents.
- **Aucune erreur ne sort** : introuvable, illisible (`ProjectError`), format trop récent (la raison de `ProjectError`, « écrit par une version plus récente de l'outil (format 0.9.0) : mettez l'outil à jour »), carnet illisible : chaque cas donne une ligne avec sa raison dans la colonne « En attente ».
- **Cache** : par chemin, gardé tant que la date et la taille du projet, du carnet, de l'ébauche d'article et de son rapport de vérification ne changent pas (ces deux derniers servent à `tasks`). Une date qui bouge sans changement fait relire, rien de plus. Le cache est en mémoire, partagé par les sessions, jamais écrit.
- **Durée** : 30 projets de la base des analyses en moins de 2 secondes à la première lecture, puis instantané ; mesuré à l'étape B1. Sur OneDrive, lire un projet « en ligne seulement » le télécharge (quelques dizaines de Ko) ; la base, elle, n'est jamais ouverte (un `stat` ne la télécharge pas).

### 7.4 Ce qui ne sort pas du poste

Le tableau ne montre que des métadonnées déjà dans les projets et les carnets (noms de fichiers, comptes, dates, textes des tâches). Rien n'est envoyé nulle part ; aucun nouveau fichier n'est écrit hors de `projets-suivis.json`.

## 8. Étapes

Chaque étape : tests écrits avec le code, catalogue anglais à jour, arrêt pour revue. Les tests utilisent des projets faits à partir des bases fictives, à différents stades, construits par une fonction de test commune (§ 8.1).

| # | Étape | Critère de réussite |
|---|---|---|
| **C1** | Le contrôle à l'écriture (§ 5.1, 5.3) : empreinte retenue au chargement, contrôle dans `save_project` et `save_notebook`, `ProjectChanged` et `NotebookChanged`, `overwrite` pour la création ; la ligne de commande | Deux objets chargés du même fichier : le second est refusé, le fichier est celui du premier (projet et carnet) ; projet neuf contre fichier apparu, refusé ; fichier supprimé, refusé ; date changée sans changement de contenu, accepté ; une commande `ddict` refusée rend un code non nul et le dit ; le fichier écrit est identique, octet pour octet, à celui d'avant cette version |
| **C2** | Dans l'interface (§ 5.2) : `c.save`, `c.save_notebook`, le bandeau, le rappel, « Recharger le projet », l'avertissement dès l'affichage | Test : aucun enregistrement hors de `common.py` ; AppTest à deux sessions (projet, puis carnet) ; le rappel nomme l'endroit, le bouton et les champs changés ; après rechargement, la décision de l'autre session est affichée, « Décision à refaire » aussi ; une date touchée sans changement ne montre rien |
| **C3** | Enregistrement interrompu et fichier occupé (§ 5.4) | Un `.tmp` présent est signalé à l'ouverture (interface et ligne de commande), jamais supprimé ; un remplacement refusé par Windows donne un message, le projet intact, et l'enregistrement suivant réussit |
| **A1** | La liste des projets suivis (§ 6.1) : `ddict.tracked`, suivi à la création, « Suivre ce projet » (récents, barre latérale), « Ne plus suivre » | Écriture déterministe (deux écritures du même contenu, mêmes octets) ; chemins avec accents et espaces ; un chemin `Z:\…` gardé tel quel ; le projet d'essai n'est pas suivi ; « Ne plus suivre » ne touche aucun fichier projet |
| **B1** | L'état d'un projet sans la base (§ 7.1 à 7.3) : `ddict.overview`, la phase, le cache | Sur les stades du § 8.1, chaque colonne a la valeur attendue ; aucune base ouverte (test : la base remplacée par un fichier illisible ne change rien) ; aucune erreur sur un projet illisible, trop récent ou introuvable ; le cache ne relit pas un fichier inchangé, relit après une écriture ; 30 projets en moins de 2 secondes |
| **B2** | Le tableau « Mes projets » sur l'accueil (§ 7.1) | AppTest : le tableau en tête, trié ; un clic ouvre le projet sur sa première tâche ; « Ne plus suivre » et « Le retrouver… » sur la ligne choisie ; les récents dessous, sans les projets suivis ; sans aucun projet suivi, une phrase et le bouton de recherche, pas de tableau vide |
| **A2** | Introuvable et « Le retrouver… » (§ 6.1) | Un projet déplacé reste, « introuvable » ; retrouvé, sa ligne revient complète ; « Ne plus suivre » le retire |
| **A3** | Chercher les projets dans un dossier (§ 6.2) | Sur un arbre de test : profondeur 4 respectée, dossiers ignorés ignorés, jonction non suivie, limites dites ; rien de coché au départ ; seuls les cochés sont ajoutés ; aucun fichier ouvert pendant la recherche (test : un `.dd.json` illisible est listé quand même) |
| **A4** | `ddict projets` (§ 6.3) | `lister` imprime les mêmes valeurs que le tableau ; `suivre`, `retirer`, `chercher` et leurs noms anglais ; `chercher` n'ajoute rien sans `--suivre` |
| **D1** | Scénario, guides, journal des changements, **version 0.17.0** | Scénario passé dans la fenêtre de l'icône, dont les étapes nouvelles (§ 8.2) ; section « Suivre plusieurs projets » des deux guides |

Si la partie C s'allonge, elle peut sortir seule en 0.16.1 après l'étape C3 : elle ne dépend de rien d'autre.

### 8.1 Les projets de test

Une fonction de test (`tests/projets_stades.py`) construit, dans un dossier temporaire, à partir de `etude-sommeil.sav` et `etude-analyses.sav` (bases fictives, graine fixe) : un projet **neuf** ; un codebook **à moitié révisé** ; un **plan figé** avec un amendement ; un **carnet avec une analyse à recalculer** (une décision prise après le calcul) et une à confirmer ; un **article produit** ; une **base retirée** ; un projet **introuvable** (chemin suivi, fichier supprimé) ; un **format trop récent** (`schema_version` relevé) ; un **fichier abîmé** (JSON coupé) ; un dossier aux noms accentués et avec espaces (`Études 2026\Vague 2`). Aucune donnée réelle.

### 8.2 Le scénario manuel

Étapes ajoutées à `docs/scenario-revision.md` :

- **Deux onglets sur le même projet** : ouvrir le projet dans deux onglets ; accepter un libellé dans le premier ; dans le second, sans recharger, voir le bandeau dès le clic suivant ; y accepter un autre libellé : refus, rappel ; « Recharger le projet » : la décision du premier onglet est là, « Décision à refaire » rappelle celle du second. Même chose avec `ddict carnet ajouter …` lancé pendant que la page « Carnet » est ouverte.
- **Projet déplacé puis retrouvé** : suivre le projet ; fermer l'outil ; déplacer le dossier ; rouvrir : la ligne dit « introuvable » ; « Le retrouver… » : la ligne revient complète ; « Ne plus suivre » sur un autre projet : son fichier est toujours là.
- Un dossier OneDrive, si la personne qui passe le scénario en a un : suivre un projet qui y est, le modifier depuis un autre ordinateur, attendre la synchronisation : le bandeau apparaît ; aucune alarme sans changement.

## 9. Décisions à prendre

| N° | Décision | Ma recommandation |
|---|---|---|
| D-129 | **Le contrôle à l'écriture** : date et taille, ou empreinte du contenu | **L'empreinte SHA-256 du contenu**, retenue au chargement et après chaque écriture, vérifiée dans `save_project` et `save_notebook` avant d'écrire, en mémoire seulement (format inchangé). Date et taille ne servent qu'à savoir s'il faut relire (avertissement dès l'affichage, cache du tableau). Seule l'empreinte ne crie pas pour un OneDrive qui touche la date et ne manque pas `validated` → `corrected`, de même taille. |
| D-130 | **Quand le fichier a changé** | Rien n'est écrit ; bandeau en tête de page, rappel de la décision (endroit, bouton, champs changés), « Recharger le projet » ; le rappel reste en texte après le rechargement, il n'est pas remis dans les champs ; **jamais de fusion** ; avertissement dès l'affichage quand la date ou la taille bougent et que l'empreinte diffère ; ligne de commande : message et code non nul. |
| D-131 | **La liste des projets suivis**, distincte des récents | `%APPDATA%\ddict\projets-suivis.json`, `{"format": 1, "projets": [...]}`, chemins seulement, triés, sans limite ; un projet absent reste (« introuvable ») ; suivi d'office à la création (interface et `ddict profiler`), sauf l'essai sur la base fictive ; « Ne plus suivre » ne touche aucun fichier. |
| D-132 | **La recherche dans un dossier** | `.dd.json` jusqu'à 4 niveaux sous le dossier choisi ; ignorés : cachés, système, `.…`, `$…`, `AppData`, `node_modules`, `*.dd-envois`, liens et jonctions, `.tmp` ; arrêt à 500 projets ou 20 000 dossiers, dit ; aucun fichier ouvert ; rien de coché au départ. |
| D-133 | **La phase d'un projet** | Jusqu'où il est allé : **Rédiger** si l'ébauche d'article existe, sinon **Analyser** si le plan a une hypothèse ou le carnet une analyse, sinon **Documenter**. Elle ne recule pas pour une nouvelle proposition ; « En attente » dit la tâche. |

Pas de verrou consultatif (§ 5.5) : je ne le recommande pas, il n'a donc pas de numéro.

## 10. Risques

- **Le court instant entre le contrôle et l'écriture** : deux enregistrements à la même milliseconde peuvent encore passer tous les deux. Le risque est celui de deux clics simultanés sur deux postes ; l'avertissement dès l'affichage le rend plus rare encore. Le fermer tout à fait exigerait un verrou, écarté (§ 5.5).
- **La décision appliquée en mémoire avant le refus** : l'objet de la séance ne correspond plus au disque. L'état « en conflit » refuse tout enregistrement suivant et pousse à recharger ; le test C2 vérifie qu'aucun chemin d'enregistrement n'y échappe.
- **Les copies de l'objet projet** : une vue qui copierait le projet (`model_copy`, `deepcopy`) emporte ou non l'empreinte selon pydantic. À vérifier à l'étape C1 ; le test « aucun enregistrement hors de `common.py` » limite les endroits à regarder.
- **OneDrive et les partages** : un fichier « en ligne seulement » se télécharge quand on le lit (le tableau lit les projets, jamais les bases) ; un remplacement peut être refusé quelques instants (§ 5.4). La date peut bouger sans changement : seule l'empreinte décide.
- **Les chemins** : lecteur réseau ou UNC, accents, espaces ; comparés par `normcase(abspath)`, jamais par `resolve()`. Deux chemins différents vers le même fichier (lettre de lecteur et UNC) peuvent faire deux lignes : la recherche dans un dossier les signale comme « déjà suivi » seulement si le chemin est le même ; à vérifier au scénario sur un vrai lecteur réseau.
- **Le tableau sur beaucoup de projets** : 30 projets mesurés à moins de 2 secondes ; au-delà de 100, la première lecture devient visible. Le cache évite de recommencer ; un indicateur « Lecture des projets… » la montre.
- **Les noms de dossiers** sont visibles en tête de l'accueil, comme ceux des récents aujourd'hui (D-024) : la liste reste sur l'ordinateur, et « Ne plus suivre » les retire.
