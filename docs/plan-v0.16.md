# Plan de la v0.16

> Statut : **validé par l'auteur le 2026-10-18**, avec les décisions D-121 à D-127 (§ 9). Suit la revue de l'interface faite sur la v0.14.0 (fenêtre de 1400 × 900, `etude-sommeil.sav` avec `questionnaire-sommeil.pdf`, puis `etude-analyses.sav` avec trois analyses au carnet), dont les 24 constats sont repris au § 3. Même cap que les v0.11 à v0.15 : **aucune IA ajoutée** ; la règle « Rien ne quitte le poste » reste entière.

## 1. Pourquoi cette version

Le fond de l'outil est solide ; l'interface est restée une suite de formulaires Streamlit par défaut. La personne doit savoir seule où elle en est, quoi faire ensuite et si son travail est enregistré :

1. **Elle ne voit pas les trois métiers** (documenter, analyser, rédiger) : treize pages au même niveau, sans état, et un tableau de bord qui s'arrête aux libellés.
2. **Un projet neuf paraît terminé, un état normal paraît une faute** : barre pleine dès l'ouverture, page centrale blanche, bandeaux rouges sur un plan vide.
3. **Une proposition s'affiche parfois comme une décision** (items inversés), et une correction peut se perdre (glossaire, un « Enregistrer » par champ). C'est l'écart le plus grave : il touche au principe « l'outil propose, une personne décide ».

## 2. Ce qui ne change pas

Ni le calcul, ni les formats de fichier (projet, carnet, exports), ni les règles de confidentialité, ni la ligne de commande. Le travail se fait dans `src/ddict/review/`, et au besoin dans `workflow.tasks()` et `review_command()`. Deux exceptions, proposées au § 9 : le paquet installé embarque `etude-sommeil.sav` (D-125, `pyproject.toml`), et Playwright entre comme outil de développement (D-127). Les tests existants passent sans être modifiés, sauf ceux qui cliquent dans l'interface.

À garder tel quel : la transparence (« Voir exactement ce qui serait envoyé »), l'origine et le statut de chaque valeur, les colonnes « Dans le fichier » / « Calculé », la question binaire des codes suspects, les cartes du carnet, le résultat APA, le passage automatique à la variable suivante.

## 3. Les constats, et où chacun est vérifié

« AppTest » : un test automatique qui clique dans l'interface, comme `tests/test_advise.py`. « Scénario » : une étape de `docs/scenario-revision.md`, pour ce qu'un test ne voit pas (couleurs, mise en page, la vraie fenêtre).

| # | Constat | Étape | Vérifié par |
|---|---|---|---|
| 1 | 13 pages au même niveau, sans état | B1 | AppTest (sections, états) + scénario (barre latérale) |
| 2 | Tableau de bord limité aux libellés | B2 | Test de `tasks()` + AppTest |
| 3 | Barre pleine sur un projet neuf | B2 | Test de la complétude + AppTest |
| 4 | Page « Variables » blanche si le filtre est vide | A3 | AppTest |
| 5 | Trois erreurs rouges sur un plan vide | A3 | AppTest (aucun `st.error` sur un plan neuf) |
| 6 | Items inversés pré-remplis par les probables | A1 | AppTest |
| 7 | Glossaire : « Accepter » ignore le champ | A2 | AppTest |
| 8 | Un « Enregistrer » par champ, saisie perdue sans avertissement | C2 | AppTest (avertissement) + scénario (fenêtre) |
| 9 | Deux boutons pour proposer les noms | C2 | AppTest |
| 10 | Pas d'acceptation groupée au glossaire | A2 | AppTest |
| 11 | Messages sans bouton pour y aller | A5 | AppTest (le bouton mène à la page, champ rempli) |
| 12 | Rouge partout, contraste 3,3:1 | A4 | Test des couleurs passées par `review_command()` (contraste calculé) + scénario |
| 13 | `st.caption` gris à 3,7:1 pour des explications décisives | A4 | Scénario (lecture) ; test : aucune des phrases listées n'est un `caption` |
| 14 | Pages longues sans onglets | B3 | AppTest (onglets, résumé d'abord) + scénario |
| 15 | « Ajouter au carnet » caché, doublons possibles | A6 | AppTest (« déjà au carnet : A3 » après réouverture) |
| 16 | Projets récents en dernier ; base fictive absente | A7 | AppTest |
| 17 | « Choose an option », « None » | A8 | AppTest (aucun texte anglais par défaut) |
| 18 | Colonnes tronquées | A8 | Scénario (1400 × 900 et 900 × 600) |
| 19 | Bornes « 1.00 », « 5.00 » | A8 | AppTest (pas, format) + scénario |
| 20 | Groupes nommés « G1 », « G2 » | A8 | AppTest |
| 21 | `use_container_width` (5 usages) | A8 | Test : le mot n'apparaît plus dans `src/` ; aucun avertissement de Streamlit |
| 22 | Variables de groupe d'un test *t* sans indication | C3 | Tests de l'ordre et des raisons + AppTest |
| 23 | Pas de « Précédente » / « Suivante » | A8 | AppTest |
| 24 | « Premier tableau » sans explication | A8 | AppTest (texte d'aide présent) |

## 4. Ce qui change pour la personne

- **Lot A.** Rien de proposé n'est déjà coché ou rempli dans un champ de décision : un bouton le reprend, à la demande. Au glossaire, on corrige la définition puis on clique « Accepter ». Aucune page blanche, aucune erreur rouge pour un état de départ. Un bleu ardoise sombre remplace le rouge, qui ne signale plus que les erreurs. Chaque message qui renvoie ailleurs porte son bouton. Sur « Analyses », les actions suivent le bouton « Lancer l'analyse ». L'accueil commence par les projets récents et propose d'essayer l'outil sur la base fictive.
- **Lot B.** La barre latérale montre trois sections, Documenter, Analyser, Rédiger, et l'état de chaque page. La barre de progression dit la complétude du codebook. Le tableau de bord continue au-delà des libellés : plan, analyses à confirmer, Méthode, vérification. Les pages longues ont des onglets.
- **Lot C.** Partout où une proposition attend, la même carte : la valeur, son origine, son statut, le champ, « Accepter » et « Rejeter ». Une section, un « Enregistrer » ; un avertissement quand on quitte une saisie non enregistrée. Dans une analyse, les variables qui conviennent viennent en tête, les autres avec leur raison.

## 5. Conception — lot A, corrections locales

### 5.1 Rien de proposé ne s'affiche comme décidé (constat 6, D-126)

J'ai passé en revue tous les champs des vues (`review/ui/*.py`) dont la valeur de départ ne vient pas d'une décision enregistrée :

| Page, champ | Valeur de départ aujourd'hui | Nature | Proposition |
|---|---|---|---|
| Groupes, « Items inversés confirmés » (`groups_view.py`, l. 52) | Les items probables, si aucun n'est confirmé | Calcul, affiché comme décidé | **Vide** ; bouton « Reprendre les items probables (sommeil_q3, sommeil_q6) » |
| Groupes, Cotation, « Minimum » / « Maximum de l'échelle » (l. 109, 113) | Le plus petit et le plus grand code étiqueté (`scoring.scale_bounds`) | Calcul, dans un champ qui exige une source | **Vides** ; bouton « Reprendre les bornes des étiquettes (1 à 5) » |
| Groupes, Cotation, « Items du score » (l. 97) | Tous les items du groupe | Calcul | **Vide** ; bouton « Prendre les 8 items du groupe » |
| Groupes, Cotation, « Calcul » et « Valeurs manquantes » (l. 104, 126) | « Somme » et « somme proportionnelle » | Choix de méthode fait d'office | **Aucun choix** au départ ; l'enregistrement le demande |
| Groupes, Cotation, « Items répondus, au minimum » (l. 119) | 0 (« tous les items ») | Choix fait d'office | **Vide** ; l'enregistrement le demande |
| Variables, « Étendue théorique » (l. 405–406) | Min 0, max 1 | Nombres arbitraires dans un champ sourcé (règle 4) | **Vides** |
| Variables, « Seuil » (l. 433) | 0 | Nombre arbitraire dans un champ sourcé | **Vide** |
| Variables, « Rattacher à » (l. 179) | La première question candidate du calcul, quand rien n'est proposé ni décidé | Calcul, sans statut affiché | Aucune question choisie ; candidates en tête, et la première nommée sous la liste (« proposée par le calcul : Q3 ») |

Ce qui est déjà juste et reste tel quel : « Structure » de la page « Base » (une valeur proposée n'y est pas reprise : c'est le modèle à suivre), la classe de confidentialité et le libellé de la fiche (la valeur affichée porte son origine et son statut, ce que le lot C généralise), la correction de Holm du plan (une valeur du modèle de projet décidée en v0.13, non une saisie), le type d'export, la langue, le filtre de la page « Vérifier » (des réglages d'affichage), les titres et notes APA (une mise en forme modifiable).

### 5.2 Glossaire (7, 10)

« Accepter » prend la définition affichée dans le champ : identique à la proposition, elle est validée ; changée, elle est enregistrée comme corrigée, la proposition d'origine gardée. « Accepter » et « Rejeter » côte à côte, sous le champ ; plus de « Enregistrer » pour un sigle proposé (il reste pour changer un sigle déjà décidé). « Tout accepter (N) » ouvre, comme `bulk_view`, la liste exacte cochée, puis « Accepter ces N sigles ». La règle « accepter la valeur affichée » vit dans `review/logic.py`, testée sans Streamlit (D-121) ; le lot C en fait un composant.

### 5.3 Aucun écran blanc (4, 5)

- **Variables** : si le filtre choisi est vide, la zone principale le dit (« Aucune variable à réviser. ») et propose les filtres non vides en boutons, avec leur compte. À l'ouverture, le filtre est celui de la première tâche du tableau de bord qui mène à « Variables », sinon « Toutes ».
- **Plan** : ce qui manque pour figer devient une liste neutre « Pour figer le plan » (cases cochées ou non, en lecture seule), tirée de `planning.freeze_refusals`. Le rouge reste pour un refus après un clic.

### 5.4 Thème (12, 13, D-123)

Passé par `review_command()` en options `--theme.*`, comme les options de sécurité : il s'applique quel que soit le dossier de lancement, sans fichier `.streamlit/config.toml`. Contrastes calculés selon WCAG 2.1 (seuil AA : 4,5:1) :

| Rôle | Couleur | Sur blanc | Sur le gris de la barre latérale (#F0F2F6) |
|---|---|---|---|
| Aujourd'hui : principale (rouge Streamlit) | #FF4B4B | 3,30:1 | 2,95:1 |
| Aujourd'hui : `st.caption` | #808495 | 3,72:1 | 3,31:1 |
| **Principale proposée** (bleu ardoise sombre) | **#1F4E79** | **8,66:1** | **7,73:1** |
| **Rouge des erreurs** | **#B42318** | **6,57:1** | **5,87:1** |
| Texte (inchangé) | #31333F | 12,53:1 | 11,18:1 |
| **Gris du texte secondaire** | **#555867** | **7,05:1** | **6,29:1** |

Thème clair imposé (`--theme.base light`) : les contrastes ci-dessus valent pour lui, et la fenêtre de l'icône ne change pas d'allure selon le réglage de Windows. Les explications qui portent une décision (« Réservée aux personnes, avec une source… », « Le carnet garde… », et la liste établie à l'étape A4 parmi les 101 `st.caption`) passent en texte normal. Pour les autres, je vérifierai à l'étape A4 si `theme.grayTextColor` assombrit `st.caption` ; sinon, une petite fonction commune `c.note()` les écrit en texte normal plus petit, sans CSS.

### 5.5 Boutons dans les messages (11)

Une fonction commune `c.go_to(page, **rempli)` : chaque message qui renvoie à une autre page porte un bouton qui y mène, champ rempli (« Définir anx » ouvre le glossaire avec le sigle dans « Ajouter un sigle »). Elle passe aujourd'hui par le choix de page actuel ; au lot B, seule elle change.

### 5.6 Analyses (15)

Sous « Lancer l'analyse », une barre : « Ajouter au carnet · Word · Excel · Script R », puis le résultat. Une analyse identique (même analyse, mêmes variables, mêmes options, même sous-groupe) déjà au carnet est reconnue en lisant le carnet, pas seulement la séance : « Déjà au carnet : A3 », bouton grisé. Rien ne change dans le carnet lui-même.

### 5.7 Accueil (16, D-125)

Projets récents en tête : nom, dossier, date de dernière modification du fichier projet. Puis « Nouveau projet », « Ouvrir un projet ». Un bouton **Essayer avec la base fictive** copie `etude-sommeil.sav` et `questionnaire-sommeil.pdf` dans un dossier de travail, crée le projet et l'ouvre ; si le dossier contient déjà le projet, il le rouvre (« Recommencer l'essai » efface et recopie, après confirmation). Emplacement proposé : `Documents\Dictionnaire de données - essai\`, le dossier Documents étant pris de Windows (il peut être déplacé vers OneDrive ; les fichiers sont fictifs, rien de personnel n'y entre). Le paquet installé n'embarque aujourd'hui que `etude-sommeil.csv`, sans étiquettes : il faut y ajouter `etude-sommeil.sav` (79 Ko).

### 5.8 Finitions (17 à 21, 23, 24)

`placeholder` traduit partout (« Choisir… ») ; « — » au lieu de « None » dans les tableaux (la valeur affichée, la valeur gardée restant vide) ; largeurs de colonnes réglées (`column_config`) pour 1400 et 900 px ; bornes entières (`step=1`, `format="%d"`) quand les codes de l'échelle sont entiers ; groupes nommés par leur description dans le sélecteur (« G1 — 8 items, codes de 1 à 5, préfixe sommeil_q ») ; `use_container_width` remplacé par `width` ; « Précédente » / « Suivante » en haut de la fiche, dans l'ordre du filtre ; sous « Premier tableau » et « Première figure », une phrase et un exemple (« 3 si l'introduction a déjà deux tableaux : le premier tableau des résultats sera le Tableau 3 »).

## 6. Conception — lot B, navigation et progression

### 6.1 Navigation par phases (1, D-122)

Streamlit 1.65 (installé) a `st.navigation` avec sections et `st.Page` ; rien à mettre à jour. Sections : **Documenter** (Base, Questionnaire, Glossaire, Variables, Groupes, Noms, Export), **Analyser** (Plan, Analyses, Carnet), **Rédiger** (Méthode, Vérifier), puis **Réglages** (IA locale, avec le banc d'essai), hors des étapes. Les pages qui se servent du modèle (Variables, Questionnaire, Analyses) portent un lien « Réglages de l'IA locale ». Chaque titre porte son état, recalculé à chaque affichage : « Variables (12) », « Plan ✓ ».

Les tests choisissent aujourd'hui la page par `session_state["mode"]` (une quarantaine de fichiers) ; le routeur garde cette clé : la page ouverte par défaut est celle qu'elle nomme, et elle suit la page affichée. Les tests existants n'ont donc pas à changer pour la navigation. Limite connue : l'outil de test de Streamlit (AppTest) ne sait pas « cliquer » dans la barre de navigation vers une page qui n'est pas un fichier ; les tests de la navigation passent par cette clé et par les boutons des pages.

### 6.2 Progression honnête (2, 3)

La barre devient la complétude du codebook (`completeness.parts`, déjà sur la page « Base ») : « Codebook : 41 éléments décidés sur 212 ». Le tableau de bord s'étend, toujours dans l'ordre recommandé : après les tâches actuelles, le plan (pas d'hypothèse, plan à figer), le carnet (analyses changées à confirmer, analyses devenues impossibles), la Méthode (trous à combler), la vérification (une ébauche existe et n'a pas été vérifiée). Le carnet exige de relire la base et de recalculer : ce calcul est gardé en mémoire tant que ni le projet, ni le carnet, ni la base ne changent, pour que chaque clic ne le relance pas. `tasks()` reçoit cet état en paramètre facultatif ; sans lui, elle rend ce qu'elle rend aujourd'hui. Ce qui ne se sait pas sans nouvel état enregistré n'est pas ajouté, et je le signalerai.

### 6.3 Onglets (14)

Base : Résumé (d'abord), Description, Niveaux de mesure, Sensibles. Groupes : Items, Cotation, Instrument, Recodages. Résultat d'analyse : Résultat, Tableaux et figures, Fichiers. Un message garde sa place près de son bouton, dans son onglet ; Streamlit ne sait pas ouvrir un onglet par le code : après une action, l'onglet affiché reste celui de l'action (à vérifier à l'étape B3, sinon le message est répété en tête).

## 7. Conception — lot C, un seul geste

### 7.1 La carte de décision (D-121)

`c.decision_card(...)` dans `review/ui/common.py` : la valeur, son origine et son statut, le champ modifiable, « Accepter » (prend la valeur affichée : identique, validée ; changée, corrigée, l'origine gardée) et « Rejeter », côte à côte. Utilisée pour le rattachement, le libellé, la description, les étiquettes, le sigle, le niveau de mesure et le nom. La règle est dans `review/logic.py` (une fonction par sorte de valeur, testée sans Streamlit) ; `link_question` et `set_privacy` la suivent déjà.

### 7.2 Un enregistrement par section, et l'avertissement (8, 9, D-124)

Ce que Streamlit permet vraiment :

- **Dans un `st.form`**, rien n'est envoyé au serveur avant le clic : l'outil ne peut pas savoir qu'une saisie attend. Un avertissement est alors impossible sans code JavaScript ajouté à la page.
- **Hors formulaire**, chaque champ envoie sa valeur quand on le quitte (Entrée, Tab, clic ailleurs, y compris un clic dans la barre de navigation). L'outil peut comparer chaque champ à la valeur enregistrée, garder la saisie quand on change de page, et le dire.
- **Fermer la fenêtre** : rien, ni dans Streamlit ni sans JavaScript, ne peut l'empêcher ou le signaler.

Proposition : une section, un encadré, un seul « Enregistrer » ; **sans `st.form`** là où une saisie peut se perdre (Variables, Groupes, Noms, Base). Une saisie différente de la valeur enregistrée marque la section « non enregistré » près de son bouton ; quitter la page ou la variable la garde comme brouillon et affiche, sur la page d'arrivée, « Saisie non enregistrée sur Groupes, G1, Cotation : Revenir · Abandonner ». « Quitter l'outil » prévient aussi. Les formulaires d'ajout (une règle, une hypothèse, un sigle) restent des `st.form` : ils se vident après l'ajout, rien n'y est à garder. Noms : une seule action, « Proposer les noms » (enregistre les règles puis propose).

### 7.3 Variables admissibles (22)

Dans chaque liste de variables d'une analyse, celles que `conditions.check` accepterait pour ce rôle d'abord, les autres à la suite avec leur raison, tirée des mêmes refus (« 3 modalités ; il en faut deux », « niveau ordinal »). L'ordre et la raison sont seuls nouveaux ; la vérification au lancement reste la même : aucune analyse ne devient possible là où elle ne l'est pas aujourd'hui (test : pour chaque analyse du catalogue et chaque base fictive, le jeu des analyses lancées est inchangé).

## 8. Étapes

Chaque étape : tests écrits avec le code, catalogue anglais à jour, arrêt pour revue. Chaque vérification visuelle se fait aussi dans la fenêtre de l'icône (pywebview, 1400 × 900 et au minimum 900 × 600).

| # | Étape | Critère de réussite |
|---|---|---|
| **A1** | Champs pré-remplis (§ 5.1) | Sur un projet neuf de `etude-sommeil.sav`, aucun champ du tableau du § 5.1 n'a de valeur ; chaque bouton « Reprendre… » remplit le champ sans rien enregistrer ; enregistrer la cotation sans calcul choisi est refusé en français |
| **A2** | Glossaire (§ 5.2) | Une définition corrigée puis acceptée est gardée, statut « corrigé », proposition d'origine conservée ; « Tout accepter (N) » ; tests de la règle dans `logic` |
| **A3** | Aucun écran blanc (§ 5.3) | Projet neuf : « Variables » s'ouvre sur un filtre non vide ; un filtre vide le dit au centre avec des boutons ; « Plan » neuf sans aucun `st.error` |
| **A4** | Thème (§ 5.4) | Options `--theme.*` dans `review_command()`, testées ; contraste de chaque couleur ≥ 4,5:1, calculé par le test ; plus aucun rouge hors erreur dans le scénario |
| **A5** | Boutons dans les messages (§ 5.5) | Chaque message qui nomme une autre page a son bouton (liste dans le test) ; « Définir anx » ouvre le glossaire avec `anx` rempli |
| **A6** | Analyses (§ 5.6) | Barre d'actions sous « Lancer l'analyse » ; après réouverture du projet, la même analyse dit « Déjà au carnet : A3 » |
| **A7** | Accueil (§ 5.7) | Projets récents en tête avec dossier et date ; « Essayer avec la base fictive » ouvre un projet de 34 variables, depuis le dépôt et depuis le paquet installé |
| **A8** | Finitions (§ 5.8) | Les constats 17 à 21, 23 et 24 vérifiés (tableau du § 3) ; aucun avertissement de Streamlit à l'affichage |
| **A9** | Scénario, guides, journal des changements ; **0.16.0 possible ici** | Scénario mis à jour et passé dans la fenêtre de l'icône ; guides en français et en anglais |
| **B1** | Navigation par phases (§ 6.1) | Trois sections et Réglages ; état de chaque page ; tests existants inchangés |
| **B2** | Progression et tableau de bord (§ 6.2) | Projet neuf : barre presque vide ; `etude-analyses.sav` avec trois analyses dont une changée : « Analyses à confirmer : 1 » mène au carnet ; un clic qui ne change rien ne relance pas le recalcul |
| **B3** | Onglets (§ 6.3) | Base, Groupes, résultat d'analyse en onglets, résumé d'abord ; messages visibles après chaque action |
| **B4** | Scénario pour la navigation ; captures automatiques si D-127 est retenue | Scénario passé |
| **C1** | La carte de décision (§ 7.1) | Utilisée pour les sept sortes de valeurs ; corriger puis « Accepter » donne « corrigé » partout |
| **C2** | Un enregistrement par section, l'avertissement, une action pour les noms (§ 7.2) | Saisie non enregistrée, changement de page : le brouillon est retrouvé par « Revenir » ; « Abandonner » le jette |
| **C3** | Variables admissibles (§ 7.3) | Ordre et raisons ; jeu des analyses lancées inchangé sur toutes les bases fictives |
| **C4** | Scénario, guides, journal des changements, version | Scénario passé dans la fenêtre de l'icône |

Si les lots B et C s'allongent, la 0.16.0 sort à l'étape A9 avec le lot A seul, et B et C suivent en 0.16.1 et 0.16.2.

## 9. Décisions à prendre

| N° | Décision | Ma recommandation |
|---|---|---|
| D-121 | **Le modèle de décision unique** : « Accepter » prend la valeur affichée (identique : validée ; changée : corrigée, l'origine gardée), « Rejeter » à côté ; plus de bouton « Enregistrer » pour une proposition | **Oui**, partout. Il supprime le cas où une correction est perdue, et rejoint ce que font déjà le rattachement et la confidentialité. Le geste change sur toutes les pages : le scénario et les guides le disent. |
| D-122 | **La navigation par phases** et la place de « IA locale » | **Oui**, avec `st.navigation` (Streamlit 1.65 suffit) : Documenter, Analyser, Rédiger, puis Réglages pour l'IA locale et le banc d'essai, avec un lien depuis les pages qui s'en servent. |
| D-123 | **Le thème** | Principale **#1F4E79** (8,66:1), erreurs **#B42318** (6,57:1), texte secondaire **#555867** (7,05:1), thème clair imposé, le tout par `review_command()`. |
| D-124 | **L'enregistrement par section, et l'avertissement** | Un « Enregistrer » par section, **sans `st.form`** là où une saisie peut se perdre, car un formulaire cache la saisie à l'outil ; brouillon gardé et avertissement au changement de page ou de variable, et à « Quitter l'outil ». La fermeture de la fenêtre reste sans avertissement. Les formulaires d'ajout restent des `st.form`. |
| D-125 | **« Essayer avec la base fictive »** | **Oui**, dans `Documents\Dictionnaire de données - essai\` (le dossier Documents de Windows), rouvert s'il existe ; `etude-sommeil.sav` ajouté au paquet installé (79 Ko). |
| D-126 | **Les champs pré-remplis** (§ 5.1) | Une règle : **aucun champ de décision n'est pré-rempli par un calcul** ; un bouton « Reprendre… » nomme ce que le calcul propose et le met dans le champ, sans enregistrer. Les huit champs du § 5.1 la suivent ; les réglages d'affichage n'en sont pas. |
| D-127 | **Captures d'écran automatiques** (Playwright, Apache-2.0) | **Oui, comme outil de développement seulement** (groupe `dev`, jamais dans le paquet installé), au lot B : un script hors de `pytest` lance l'outil sur la base fictive et enregistre les pages à 1400 × 900 et 900 × 600. Il télécharge un navigateur à l'installation ; les tests restent sans réseau. À refuser si ce téléchargement gêne : le scénario manuel suffit. |

## 10. Risques

- **Le changement de geste** (D-121) : une personne habituée clique « Accepter » en pensant valider la proposition alors qu'elle a touché le champ. La carte dit, dès que le champ diffère, « Accepter enregistrera votre correction ».
- **Les tests qui cliquent** : glossaire, variables, groupes, noms (une dizaine de fichiers) changent avec le geste. Les tests de logique, eux, ne bougent pas : ils sont le filet.
- **La vitesse** : l'état des pages et le tableau de bord étendu se recalculent à chaque clic ; le recalcul du carnet est gardé en mémoire (§ 6.2), et l'étape B2 le mesure sur `etude-analyses.sav`.
- **Le brouillon hors formulaire** (D-124) : chaque saisie relance l'affichage de la page. Le scénario reprend les étapes « sans pause » (4, 5, 12, 40) pour vérifier qu'aucun clic rapide n'est perdu.
- **Le lot A avant la navigation** : les boutons du lot A passent par `c.go_to` ; au lot B, seule cette fonction change.
- **Les onglets** : Streamlit ne choisit pas l'onglet ouvert par le code ; un message ne doit pas finir dans un onglet caché (étape B3).
