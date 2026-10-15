# Installer et utiliser l'outil sur un Mac

Ce guide s'adresse aux personnes qui ne programment pas. Il couvre ce qui est propre au Mac : l'installation, l'ouverture et l'arrêt de l'outil, la mise à jour et les problèmes courants. Une fois l'outil ouvert, tout se passe dans votre navigateur, exactement comme sous Windows : la suite est dans le [guide Windows](installation-windows.md), à partir de sa section 3.

In English: [`en/installation-macos.md`](en/installation-macos.md).

> **Version à l'essai sur Mac.** L'installation sur Mac est nouvelle (version 0.5). Elle a été vérifiée sur un Mac de GitHub (macOS 26, puce Apple), pas encore par une personne sur son propre Mac. Si quelque chose ne se passe pas comme décrit ici, notez-le et transmettez-le.

## Ce qu'il faut

- macOS 13 (Ventura) ou plus récent, sur un Mac à puce Apple (M1 et suivants) ou Intel. Pas besoin de droits d'administrateur.
- Une connexion Internet **pendant l'installation seulement**. Ensuite, l'outil ne communique plus avec Internet.
- Pour l'IA, facultative : environ 5 Go d'espace libre et 16 Go de mémoire (8 Go suffisent avec un modèle plus petit). Sur un Mac à puce Apple, le modèle tourne sur la puce, sans carte graphique séparée.

## 1. Installer

1. Téléchargez l'archive de l'outil depuis la page des versions du projet sur GitHub : le lien **Source code (zip)**, par exemple `dictionnaire-donnees-0.7.0.zip`.
2. Dans le Finder, double-cliquez sur le fichier téléchargé : macOS le décompresse à côté. Ouvrez le dossier obtenu : c'est **le dossier de l'outil**, avec `installer.command`, `docs` et `exemples`.
3. Double-cliquez sur **`installer.command`**. La première fois, macOS refuse de l'ouvrir, avec un message comme « Apple n'a pas pu confirmer que “installer.command” ne contient pas de logiciel malveillant » ou « provient d'un développeur non identifié ». C'est normal : ce message apparaît pour tout script téléchargé qui n'est pas signé par un éditeur payant ; l'installateur est un simple fichier texte, lisible dans n'importe quel éditeur.
   - Cliquez sur **Terminé** (ou **OK**), puis ouvrez **Réglages Système > Confidentialité et sécurité**. Plus bas, un message parle de `installer.command` : cliquez sur **Ouvrir quand même**, confirmez avec votre mot de passe ou Touch ID, puis **Ouvrir**.
   - Sur un macOS plus ancien (avant 15), on peut aussi faire **Contrôle-clic** sur `installer.command`, puis **Ouvrir**, et de nouveau **Ouvrir**.
4. Une fenêtre du **Terminal** s'ouvre et suit quatre étapes : uv (le gestionnaire de Python, installé dans votre dossier d'utilisateur), l'outil (une ou deux minutes la première fois), les icônes, puis l'IA locale.
5. À l'étape de l'IA, répondez par `o` (oui) ou `n` (non), puis Retour :
   - si Ollama n'est pas installé, l'installateur propose d'ouvrir sa page de téléchargement ; installez Ollama pour macOS, ouvrez-le une fois, puis relancez `installer.command` ;
   - si Ollama est installé mais pas le modèle recommandé, il propose de le télécharger (environ 4,7 Go, une seule fois).

   Vous pouvez répondre non et y revenir plus tard : l'outil fonctionne sans IA.
6. « Installation terminée » : appuyez sur Retour, puis fermez la fenêtre du Terminal. Une icône **Dictionnaire de données** est sur votre bureau et dans le dossier **Applications** de votre dossier d'utilisateur.

## 2. Ouvrir et arrêter l'outil

Double-cliquez sur l'icône **Dictionnaire de données**. Une fenêtre du Terminal s'ouvre et fait tourner l'outil, puis votre navigateur s'ouvre sur l'**accueil**, à une adresse qui commence par `http://127.0.0.1` : elle n'est accessible que depuis votre ordinateur.

- **Pour arrêter l'outil**, cliquez **Quitter l'outil** en bas de la barre latérale, ou fermez cette fenêtre du Terminal (ou, dans le Terminal, Contrôle-C). Si le Terminal demande s'il faut mettre fin au processus, répondez **Terminer**. Fermer l'onglet du navigateur ne l'arrête pas : un nouveau double-clic sur l'icône rouvre simplement l'onglet.
- Au premier lancement, macOS peut demander si le Terminal peut accéder au dossier **Documents** : l'outil y démarre, pour que la fenêtre « Ouvrir » commence là. Vous pouvez accepter ou refuser ; l'outil fonctionne dans les deux cas.
- **Langue** : en haut de l'accueil, **Français · English** choisit la langue de l'interface.

## 3. La suite

Tout le reste se fait dans le navigateur, comme sous Windows : suivez le [guide Windows](installation-windows.md) à partir de la section 3 (premier codebook avec la base fictive, questionnaire, rattachements, IA locale, révision, export, fichiers de commandes, vos propres données, noms des variables). Quelques différences :

- La fenêtre « Ouvrir » est celle du Mac ; les fichiers d'exemple sont dans le dossier de l'outil, puis `exemples/bases-fictives`. Si la fenêtre n'apparaît pas, elle est peut-être derrière le navigateur.
- Pour coller un chemin dans le champ sous le bouton : dans le Finder, sélectionnez le fichier, puis **Option-Commande-C** (« Copier en tant que nom de chemin »).
- **Ouvrir le dossier** (page Export) ouvre le Finder.
- Ollama tourne dans la barre des menus, en haut de l'écran : s'il ne répond pas, ouvrez-le depuis le dossier Applications.
- La liste des projets récents et la langue choisie sont gardées dans `~/Library/Application Support/ddict` ; **Effacer la liste**, sur l'accueil, vide la liste.

## Mettre à jour ou désinstaller

- **Mettre à jour** : téléchargez et décompressez la nouvelle archive, puis double-cliquez sur son `installer.command` (avec, la première fois, le passage par **Confidentialité et sécurité** de la section 1). Si l'outil est ouvert, l'installateur propose de le fermer (répondez `o`) : il ne peut pas le remplacer pendant qu'il tourne. Vos fichiers projet sont conservés.
- **Désinstaller** : double-cliquez sur `desinstaller.command`, dans le dossier de l'outil. Il retire l'outil et ses icônes, sans toucher à vos projets, codebooks ou données ; il demande avant d'effacer la liste des projets récents. uv et Ollama restent installés.

## Pour qui préfère la ligne de commande

Après l'installation, ouvrez une nouvelle fenêtre du Terminal : la commande `ddict` y est disponible, avec les mêmes sous-commandes que sous Windows (`ddict --help` les liste ; voir la section du même nom du guide Windows).

## En cas de problème

| Ce qui arrive | Que faire |
|---|---|
| « Apple n'a pas pu confirmer… » ou « développeur non identifié » au double-clic sur `installer.command` | **Réglages Système > Confidentialité et sécurité > Ouvrir quand même** (section 1). |
| « Vous n'avez pas l'autorisation » ou rien ne se passe au double-clic | L'archive a perdu le droit d'exécution du script. Dans le Terminal, tapez `chmod +x ` (avec l'espace), glissez `installer.command` dans la fenêtre, puis Retour ; relancez-le. |
| L'installateur s'arrête sur un message rouge | Vérifiez la connexion Internet, puis relancez-le. Si le message persiste, notez-le et transmettez-le. |
| « L'outil est encore ouvert » | Fermez la fenêtre du Terminal où tourne l'outil, puis relancez l'installateur. |
| Le navigateur ne s'ouvre pas au double-clic sur l'icône | Ouvrez-le vous-même à l'adresse `http://127.0.0.1:8501`. |
| Page IA locale : « Ollama ne répond pas » | Ouvrez Ollama depuis le dossier Applications, attendez son icône dans la barre des menus, puis **Vérifier de nouveau**. |
| L'outil semble figé | Fermez la fenêtre du Terminal de l'outil, puis double-cliquez de nouveau sur l'icône. Les décisions déjà prises sont enregistrées. |

Pour les autres messages (export, copie documentée, R), voir le tableau du [guide Windows](installation-windows.md#en-cas-de-problème). Pour toute autre difficulté, notez ce que vous avez fait et le message obtenu, et transmettez-les à la personne qui vous a fourni l'outil.
