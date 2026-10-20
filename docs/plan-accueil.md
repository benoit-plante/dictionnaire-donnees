# Plan : l'accueil et le nom d'un projet

> Statut : **validé par l'auteur le 2026-10-20, sauf le thème sombre (partie A), mis de côté** : le § 5 garde son analyse pour plus tard, sans étape ni décision. Décisions D-159 à D-162 (§ 10), adoptées avec les recommandations ; le thème sombre prendra un numéro à sa reprise. Même cap que les v0.16 et v0.17 : ni le calcul, ni la porte de confidentialité, ni l'IA, ni les fichiers produits ne changent. Une seule exception, proposée en D-161 : un champ facultatif dans le fichier projet, pour son titre.

## 1. Pourquoi

1. **L'interface ne s'offre qu'en clair** (mis de côté, § 5). D-123 a imposé le thème clair pour garantir les contrastes ; travailler le soir, ou avec Windows réglé en sombre, donne une fenêtre blanche au milieu d'un écran sombre.
2. **« Essayer l'outil » ne sert plus.** L'outil a une vraie base de projets suivis, et la section prend une place de choix sur l'accueil pour un geste fait une fois.
3. **L'accueil empile tout dans une seule page** : dix sections les unes sous les autres, et un tableau de neuf colonnes serrées qui dit tout de chaque projet sans rien expliquer.
4. **Un projet porte le nom de son fichier** (`etude-sommeil.dd.json` → « etude-sommeil »), souvent celui de la base, que l'équipe n'a pas choisi.

## 2. Ce qui ne change pas

- Le calcul, la porte de confidentialité, les messages à l'IA, les exports (Word, Excel, PDF, figures APA, paquet de dépôt), le carnet et son format.
- **L'accueil ne lit jamais une base** (D-133) : le détail d'un projet se tire du projet et du carnet seulement.
- La liste des projets suivis (`tracked`, D-131), les récents (`recents`, D-024), la recherche dans un dossier (D-132), le contrôle à l'écriture (D-129, D-130).
- La navigation d'un projet ouvert (D-122) : mêmes sections, mêmes pages, même clé `mode`.
- Les fichiers à côté du projet : aucun n'est renommé (D-161).

## 3. Ce que j'ai vérifié, en plus de ce que dit la demande

**Streamlit 1.65 et le thème** (lu dans le paquet installé, `streamlit/config.py`, `runtime/app_session.py` et le code de la page) :

- Les sections `theme.light` et `theme.dark` (et leurs `sidebar`) existent. Quand les deux sont déclarées, la page choisit **d'elle-même** : le dernier choix fait dans le menu « ⋮ » de Streamlit (« System · Light · Dark », en anglais), gardé dans le stockage du navigateur sous une clé qui contient **l'adresse de la page** (`stActiveTheme-/base-v2` n'est pas `stActiveTheme-/-v2`), sinon le réglage du système. Ce menu s'affiche même avec `toolbarMode minimal` dès qu'il y a deux thèmes. L'outil (Python) ne peut ni lire ni écrire ce choix sans JavaScript ajouté à la page.
- Le serveur envoie le thème **à chaque exécution complète** de la page (le message `new_session`), lu à ce moment dans la configuration ; la page le réapplique dès qu'il diffère (`processThemeInput`, comparaison d'une empreinte du thème). Changer la configuration du serveur pendant qu'il tourne (`streamlit.config.set_option`, une fonction interne de Streamlit, non documentée pour les applications) change donc le thème au clic suivant, **sans redémarrer, sans perdre la séance**.
- Le texte d'un bouton principal (`type="primary"`) est **toujours blanc** sur la couleur principale, et la couleur principale sert aussi de couleur de texte à une vingtaine d'endroits (onglet choisi, choix d'un `segmented_control`, survol). Conséquence au § 5.3.
- `theme.linkColor`, `redTextColor`, `greenTextColor`, `borderColor` et les couleurs des graphiques existent en 1.65.

**Les couleurs écrites en dur** : il y en a moins que prévu. Sur les sept endroits avec `unsafe_allow_html` ou un code `#xxxxxx` dans `ddict/review` :

| Endroit | Ce qu'il fait | En sombre |
|---|---|---|
| `apa_view._table_html` (l. 94–133), et les notes (l. 176–190) | Filets du tableau APA en `currentColor`, sans couleur de fond | Suit le texte : lisible |
| `apa_view` l. 181, `method_view` l. 368 | Figures APA, images PNG sur fond blanc | Une carte blanche dans la page sombre : lisible ; c'est la figure telle qu'elle sera dans le Word (§ 5.5) |
| `method_view.HOLE` (l. 62, 512) | Trou de la Méthode : fond jaune `#FFF59D`, texte noir `#000` | Les deux couleurs sont fixées ensemble : 18,8:1 sur les deux fonds. Gardé, ou passé par le thème (§ 5.4) |
| `method_view` l. 542 | Paragraphes de la Méthode en HTML, sans couleur | Suit le texte |

Les ✓ de la navigation, les « pastilles » d'état et l'aperçu du questionnaire conçu (`publish_view._preview`) sont du texte ou des champs de Streamlit : ils suivent le thème. Il n'y a aucun graphique Altair, Plotly ou `st.*_chart` dans l'interface : les graphiques des analyses sont les figures APA, des images.

**La base fictive dans le paquet** : `etude-sommeil.sav` n'y est que pour l'essai (`pyproject.toml`, commentaire « v0.16 (D-125) »). Mais `questionnaire-sommeil.pdf` sert aussi au **banc d'essai** des modèles (`corrige-banc.json` le nomme, avec `etude-sommeil.csv`) : il reste dans le paquet.

**Le nom d'un projet et les fichiers produits** : seize sortes de fichiers prennent le radical du projet (`workflow.project_stem`). Plusieurs **nomment d'autres fichiers dans leur contenu** : chaque script R d'analyse fait `source("etude-metadonnees.R")` et `source("etude-preparation.R")` (`rscript._header`) ; le script R du carnet prend son nom du lien du carnet (`notebook.project.file`) ; le paquet de dépôt range `codebook/etude.xlsx` et son mode d'emploi dit « exécutez `etude.sps` ». Renommer les fichiers casserait ces renvois dans les fichiers déjà écrits, sauf à réécrire des fichiers produits (§ 8.3).

**La version** : la partie « Non publié » du journal des changements change déjà le format du projet (D-158, 0.10.0). La règle « 0.20.2 si le format ne change pas » ne départage donc plus rien (§ 10, D-162).

## 4. Ce qui change pour la personne

- **Partie B.** L'accueil n'a plus de section « Essayer l'outil ». Un dossier `Documents\Dictionnaire de données - essai` déjà créé reste là, et son projet s'ouvre comme n'importe quel autre.
- **Partie A (mise de côté).** Dans les réglages de l'accueil, et en bas de la barre de gauche d'un projet : **Clair · Sombre · Comme Windows**. Le choix s'applique au clic suivant, sans rien perdre de ce qui est tapé, et reste sur cet ordinateur. Les fichiers produits restent en clair.
- **Partie C.** La barre de gauche de l'accueil devient son menu : **Mes projets**, **Nouveau projet**, **Concevoir un questionnaire**, **Ouvrir un projet**, **Réglages**, et « Quitter l'outil » en bas. « Mes projets » montre une liste courte à gauche et, à droite, le détail du projet choisi, avec ses tâches (chacune ouvre le projet à la bonne page), son plan, son carnet, sa base, ses fichiers et les actions.
- **Partie D.** Un projet peut recevoir un **titre** (« Sommeil et anxiété, cohorte 2026 »), montré partout à la place du nom du fichier. Les fichiers ne bougent pas.

## 5. Partie A — le thème sombre (mise de côté)

> Mise de côté par l'auteur le 2026-10-20. L'analyse reste ici pour la reprise ; ses recommandations ne sont pas des décisions, et les étapes A1 à A3 ne sont pas faites. L'accueil n'a donc pas de choix du thème, et ses captures sont en clair.

### 5.1 Trois façons de l'appliquer (point 2 de la demande)

| Façon | Ce qu'elle coûte |
|---|---|
| **1. Deux thèmes déclarés, la page choisit** (`theme.light` + `theme.dark`) | Rien à redémarrer. Mais le choix se fait dans le menu « ⋮ » de Streamlit, en anglais, et l'outil ne peut ni le dicter ni le lire : la préférence de `settings.py` n'aurait aucun effet. Le choix est gardé par adresse de page (une page rechargée sur `/plan` peut revenir dans l'autre thème) et par navigateur ; dans la fenêtre de l'icône (pywebview), il faudrait vérifier qu'il survit à la fermeture. |
| **2. Redémarrer le serveur** avec d'autres `--theme.*` | Toutes les séances perdues : le projet ouvert se ferme, l'onglet ouvert, les **brouillons de D-124** (gardés dans la séance) et le rappel de D-130 disparaissent ; la fenêtre affiche « Connection lost » le temps du redémarrage ; une deuxième fenêtre ouverte sur le même serveur perd aussi les siens. Contraire à « le choix ne doit jamais faire perdre une saisie ». |
| **3. Changer la configuration du serveur en marche** (`config.set_option` sur les clés `theme.*`), puis `st.rerun()` | Rien à redémarrer, la séance et les brouillons restent : la page est la même, les champs aussi. Un seul thème est envoyé à la fois : pas de menu « ⋮ », aucun choix caché dans le navigateur. « Comme Windows » se lit dans le registre de Windows (`HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`, valeur `AppsUseLightTheme`, module `winreg` de Python), à chaque exécution : un changement dans Windows s'applique au clic suivant. **Le prix : une fonction interne de Streamlit**, qui peut changer à une mise à jour ; un test la surveille (§ 9). La configuration vaut pour tout le serveur : deux fenêtres ouvertes prennent le même thème, ce qui est le sens d'une préférence « de ce poste ». |

**Recommandation : la façon 3.** Au démarrage, `review_command()` passe déjà le thème choisi en options `--theme.*` (pas de clignotement blanc à l'ouverture) ; ensuite, `theme.apply(choix)` règle la configuration à chaque exécution, avant de dessiner la page, si elle diffère. Si une mise à jour de Streamlit cassait la façon 3, le test le dirait, et l'outil retomberait sur le thème du démarrage (le choix s'appliquerait alors au prochain lancement) : jamais d'erreur à l'écran.

À vérifier dans la fenêtre à l'étape A2, avant toute autre chose : qu'un changement de thème au milieu d'une saisie ne perd rien (champ quitté par le clic sur le choix du thème, comme pour un changement de page), et qu'il s'applique dès le `st.rerun()`. Si l'une des deux échoue, je m'arrête et je reviens vers vous.

### 5.2 Le choix, et où il se fait (point 1)

- `settings.py` : `theme()` rend `"light"`, `"dark"` ou `"system"` ; `save_theme()` écrit dans `reglages.json`, comme la langue. **Par défaut : clair**, pour qu'une personne qui ne choisit rien ne voie rien changer (D-123 reste vrai pour elle) ; « Comme Windows » serait l'autre défaut possible.
- Sur l'accueil, onglet **Réglages** (partie C), sous la langue.
- **Une fois un projet ouvert : oui, je le recommande**, en bas de la barre de gauche, juste au-dessus de « Quitter l'outil », un petit choix à trois icônes (soleil, lune, écran) avec leur nom en aide. Raison : revenir à l'accueil ferme le projet (`c.close_project` vide la séance), donc ses brouillons ; changer de thème ne doit pas l'exiger. La langue, elle, reste sur l'accueil seulement.

### 5.3 Les couleurs du thème sombre (point 3)

Contrastes WCAG 2.1 calculés comme pour D-123 ; une légende (`st.caption`) est le texte à 60 % d'opacité (D-128).

| Rôle | Couleur | Sur le fond (#0E1117) | Dans la barre de gauche (#1C2129) |
|---|---|---|---|
| Fond | #0E1117 (celui de Streamlit) | — | — |
| Fond secondaire, barre de gauche | #1C2129 (un peu plus clair que le fond) | — | — |
| **Texte** | **#F2F4F7** | **17,15:1** | **14,67:1** |
| **Légendes** (texte à 60 %) | ≈ #989B9F | **6,62:1** | **6,15:1** |
| **Principale** (boutons, choix, barre de progression) | **#3777B2**, le même bleu que #1F4E79, éclairci | 4,00:1 | 3,42:1 |
| Texte blanc d'un bouton principal | blanc sur #3777B2 | **4,73:1** | — |
| **Liens** (`linkColor`) | **#8DBDE8** | **9,52:1** | **8,14:1** |
| **Rouge des erreurs** (`redColor`, `redTextColor`) | **#F97066** | **6,78:1** | **5,80:1** |
| **Texte des succès** (`greenTextColor`) | **#6CCB8A** | **9,49:1** | **8,12:1** |

**Une limite à connaître** : avec un texte de bouton toujours blanc, aucune couleur principale ne peut atteindre 4,5:1 à la fois contre le blanc et contre un fond sombre (il faudrait une luminance entre 0,175 et 0,183 sur un fond noir pur ; impossible sur #0E1117). J'ai privilégié le texte des boutons principaux (4,73:1) ; la couleur principale reste au-dessus de 3:1, le seuil WCAG des éléments d'interface, mais **en dessous de 4,5:1 là où Streamlit l'emploie comme couleur de texte** (onglet choisi, choix d'un `segmented_control`, survol) : 4,00:1 sur le fond. Ces textes sont aussi marqués autrement (soulignement de l'onglet, fond du choix). L'autre voie, une principale claire (#6CA6D9, 7,28:1 sur le fond), mettrait le texte blanc des boutons principaux à 2,59:1 : pire. L'étape A2 mesure tout dans le navigateur, comme D-128 l'avait fait, et corrige ce tableau si la page diffère du calcul.

Le thème clair ne change pas (D-123, D-128) ; `THEME` garde ses valeurs, et le module gagne `DARK`.

**Le test** (`tests/test_theme.py`, étendu) calcule, pour les deux thèmes, à partir des dictionnaires du module : texte et légendes sur le fond et dans la barre de gauche (≥ 4,5:1), blanc sur la principale (≥ 4,5:1), principale sur les deux fonds (≥ 3:1), liens, rouge et vert sur le fond (≥ 4,5:1), et que le rouge n'est la couleur d'aucun autre rôle. La limite ci-dessus y est écrite, avec sa raison, pour que personne ne la « corrige » à l'aveugle.

### 5.4 Les couleurs écrites en dur (point 4)

- Le trou de la Méthode : fond jaune et texte noir fixés ensemble, lisible sur les deux fonds (18,8:1). Je propose de le garder tel quel, déplacé dans `theme.py` (`HIGHLIGHT`) pour qu'il n'y ait plus de couleur hors de ce module.
- Un test refuse tout code `#xxxxxx`, `rgb(` ou `:red[` dans `src/ddict/review/` hors de `theme.py`.
- Le scénario passe chaque page en sombre (§ 9) : pastilles, ✓, aperçu du questionnaire, tableaux (`st.dataframe`, `st.data_editor`), tableau APA, figures.

### 5.5 Ce qui reste en clair (point 5)

Les fichiers produits ne connaissent pas le thème : rien dans `export/`, `analysis/` ni `design_word` ne lit `settings`. Un test le vérifie en produisant le Word d'une analyse, son classeur et une figure en clair puis en sombre : mêmes octets. Les figures APA montrées dans l'interface restent sur fond blanc, comme dans le Word.

## 6. Partie B — retirer « Essayer l'outil »

### 6.1 Le sort de chaque morceau (points 6 et 7)

| Morceau | Proposition |
|---|---|
| Section « Essayer l'outil » et « Recommencer l'essai » (`home_view._trial`, `_start_trial`) | **Retirées** |
| `ddict/review/trial.py` | **Retiré** : rien d'autre ne s'en sert (`trial.documents()` non plus) |
| `tests/test_trial.py` | **Retiré** |
| `tests/test_tracked.py`, deux tests (« l'essai n'est pas suivi ») | **Retirés** ; la règle qu'ils gardaient disparaît avec l'essai |
| `DDICT_TRIAL_DIR` dans `tests/conftest.py` et `scripts/captures.py` | **Retiré** |
| `etude-sommeil.sav` dans le paquet installé (`pyproject.toml`) | **Retiré du paquet** (79 Ko) ; il reste dans `exemples/bases-fictives/` pour les tests, les captures et le guide |
| `questionnaire-sommeil.pdf` dans le paquet | **Gardé** : le banc d'essai des modèles s'en sert |
| Un dossier `Documents\Dictionnaire de données - essai` existant | L'outil n'y touche pas ; son projet s'ouvre par « Ouvrir un projet » ou les récents, et peut être suivi |
| Textes traduits (`locale/en`) | Retirés du catalogue avec le code |
| Guide (§ 3 de `installation-windows.md`, et sa version anglaise ; § « Quels projets sont suivis ») | Le paragraphe « Le plus court » disparaît ; la marche « Pour le faire vous-même » (Choisir une base → `exemples\bases-fictives\etude-sommeil.sav`) devient la seule ; la phrase « le projet d'essai n'est pas suivi » est retirée |
| Scénario manuel (étapes 1 et 65, note du début sur `DDICT_TRIAL_DIR`) | Étape 1 réécrite avec la partie C ; étape 65 remplacée par « l'accueil n'offre plus d'essai » |
| Captures | Refaites à la partie C |

Le journal des décisions garde D-125 tel quel ; **D-159** dit qu'il est remplacé.

## 7. Partie C — la page d'accueil

### 7.1 Le menu dans la barre de gauche (point 8)

**Recommandation (D-160) : `st.navigation` avec des pages-fonctions**, comme un projet ouvert (D-122), au lieu d'un choix maison dans la barre de gauche :

- la barre de gauche a la même allure dans l'accueil et dans un projet (même liste, même mise en évidence de la page ouverte) ;
- chaque onglet a son adresse (`/projets`, `/nouveau`, `/concevoir`, `/ouvrir`, `/reglages`) : un rechargement de la page garde l'onglet, alors qu'un choix maison reviendrait toujours à « Mes projets » (un rechargement crée une séance neuve) ;
- les tests choisissent l'onglet par une clé de séance, `home_tab`, distincte de `mode` (celle des pages d'un projet), comme ils choisissent une page aujourd'hui.

**Le piège de « Page not found »** (v0.16) : Streamlit ne sert la page par défaut qu'à la racine ; une page par défaut demandée par son nom répond « Page not found ». La même règle que `app._root_page` s'applique : la page par défaut est l'onglet de la séance, jamais celui que l'adresse nomme. Deux cas de plus, à tester à l'étape C2 :
- « Accueil » depuis un projet ouvert sur `/plan` : l'adresse nomme une page qui n'existe pas dans l'accueil ; l'accueil s'ouvre sur « Mes projets », sans message ;
- un rechargement sur `/nouveau` : l'onglet reste « Nouveau projet ».

`_root_page` est généralisée pour servir les deux navigations, plutôt que copiée.

**Les onglets** : Mes projets (par défaut), Nouveau projet, Concevoir un questionnaire, Ouvrir un projet, Réglages. « Quitter l'outil » reste en bas de la barre, sous le menu. Un bouton d'un onglet qui mène à un autre (« Chercher les projets dans un dossier… » quand aucun projet n'est suivi) passe par le même mécanisme que `c.go_to` (une clé `goto`, `st.switch_page`). L'onglet ouvert reste après une action : les boutons rappellent la page où ils sont.

**L'avertissement sur l'anglais** reste en tête de chaque onglet quand l'interface est en anglais (il dit que la traduction n'est pas relue : il doit se voir, pas seulement dans les réglages). Le titre « Dictionnaire de données » et la phrase « Tout se passe sur cet ordinateur… » passent en tête de la barre de gauche, au-dessus du menu.

### 7.2 Mes projets : une liste et un détail (point 9)

Les deux mises en page :

```
A. Liste dans la fenêtre (recommandée)          B. Liste dans la barre de gauche
┌────────────┬─────────────────────────────┐    ┌────────────┬─────────────────────────────┐
│ Dictionn.  │ Mes projets                 │    │ Dictionn.  │ Sommeil et anxiété 2026     │
│            │ ┌─────────┐┌──────────────┐ │    │            │ …\Recherche\Sommeil         │
│ ▸ Mes proj.│ │Sommeil ●││ Sommeil et   │ │    │ ▸ Mes proj.│ Concevoir › … › Analyser ›  │
│   Nouveau  │ │ Analyser││ anxiété 2026 │ │    │   Sommeil ●│ Codebook ████████░░ 82 %    │
│   Concevoir│ │Familles ││ Analyser     │ │    │   Familles │ En attente (2)              │
│   Ouvrir   │ │ Concev. ││ ██████░ 82 % │ │    │   Suivi ⚠  │  [Plan à figer]             │
│   Réglages │ │Suivi ⚠  ││ En attente…  │ │    │   Nouveau  │ …                           │
│            │ │ Introuv.││ …            │ │    │   Concevoir│                             │
│ ─────────  │ └─────────┘└──────────────┘ │    │   Ouvrir   │                             │
│ Quitter    │                             │    │ Quitter    │                             │
└────────────┴─────────────────────────────┘    └────────────┴─────────────────────────────┘
```

**Recommandation : A, la liste dans la fenêtre**, comme vous le pensiez. Trois raisons : à 900 × 600, Streamlit replie la barre de gauche, et une liste qui y vivrait disparaîtrait avec elle ; la barre de gauche garde le même rôle dans l'accueil et dans un projet (le menu) ; une liste de vingt projets n'allonge pas la barre au point de cacher « Quitter l'outil ». Proportions : un tiers pour la liste, deux tiers pour le détail ; en dessous de 640 px, Streamlit empile les deux.

La liste : un bouton par projet, la dernière modification d'abord (l'ordre d'aujourd'hui, `overview.rows`) ; sur sa ligne, le nom et la phase, et une icône d'attention pour un fichier introuvable, illisible ou écrit par une version plus récente (le texte exact au détail). Un clic montre le détail, sans ouvrir le projet. Le projet choisi est gardé dans la séance (`home-chosen`) ; au départ, le premier de la liste ; en revenant d'un projet par « Accueil », ce projet-là.

### 7.3 Le détail d'un projet (point 10)

Tiré de `ProjectRow`, sans jamais lire la base :

| Partie du détail | D'où | Nouveau ? |
|---|---|---|
| Nom (le titre, partie D), dossier entier, date de modification | `row.name`, `row.folder`, `row.modified` | Le titre (§ 8) |
| Phase, et la suite : « Concevoir › En collecte › **Documenter** › Analyser › Rédiger » (les deux premières seulement pour un projet conçu dans l'outil) | `row.phase`, `PHASES` | Rien |
| Avancement du codebook, la barre de la barre de gauche | `row.codebook` | Rien |
| Les tâches qui attendent, **toutes**, chacune un bouton qui ouvre le projet à sa page | `row.tasks` ; `_take_up` généralisé à une tâche donnée (`c.open_project` puis `c.go_to_task`) | Rien |
| Le plan : hypothèses, figé le …, amendements | `row.hypotheses`, `row.frozen`, `row.amendments` | Rien |
| Le carnet : retenues, à confirmer, à recalculer (ou illisible, d'un autre projet) | `row.notebook`, `row.retained`… | Rien |
| La base : son nom, trouvée ou non à côté | `row.source`, `row.base` | Rien |
| Le questionnaire : son nom, trouvé ou non à côté, ou « conçu dans l'outil » | `project.questionnaire.file_name`, `project.design` | **`questionnaire`**, **`questionnaire_found`**, **`designed`** dans `ProjectRow` |
| Les fichiers produits trouvés à côté, par leur nom ; « Ouvrir le dossier » (Explorateur, `os.startfile`, comme `export_view`) | `overview.produced(path)` | **Nouvelle fonction** |
| Actions : Ouvrir, Renommer, Ne plus suivre, Retrouver (introuvable seulement) | `tracked`, `_find_again` | Renommer (§ 8) |

Un projet introuvable, illisible ou trop récent montre ce qu'on sait (chemin, message d'aujourd'hui) et ses seules actions possibles : Retrouver ou Ne plus suivre, Ouvrir le dossier s'il existe.

**Ce que coûte le calcul.** Les trois champs du questionnaire viennent du projet déjà lu par `overview._read` : rien de plus, gardés dans le cache comme le reste. `overview.produced(path)` lit **une fois la liste des noms du dossier** (`os.scandir`, sans ouvrir aucun fichier, donc sans télécharger un fichier OneDrive « en ligne seulement ») et garde ceux qui portent le radical du projet suivi d'un suffixe connu de l'outil (`-carnet.json`, `-article.docx`, `-preenregistrement.*`, `-depot.zip`, `.xlsx`/`.md` du codebook, `-travail.*`, `-contexte.md`, `-datapackage.json`, `-metadonnees.*`, `-preparation.*`, `-analyse-N.*`, `-correspondance.csv`, `-ecarts-vagues.md`, le dossier `.dd-envois`, le Word et le fichier LimeSurvey d'un questionnaire conçu). **Calculée pour le projet choisi seulement**, à chaque affichage du détail : un dossier de quelques milliers de fichiers se lit en quelques millisecondes ; sur un lecteur réseau lent, c'est le seul coût nouveau, et il ne touche qu'un projet. Les suffixes viennent des constantes des modules qui écrivent ces fichiers, pas d'une liste recopiée.

### 7.4 Aucune fonction perdue (point 11)

| Ce que l'accueil fait aujourd'hui | Onglet | Clé de séance ou de bouton |
|---|---|---|
| Tableau des projets suivis, ouvrir un projet à sa première tâche | Mes projets (liste + détail ; « Ouvrir » au détail) | `home-project-{i}` **sélectionne** au lieu d'ouvrir ; `home-open-chosen` ouvre |
| Ne plus suivre | Mes projets (détail) | `home-unfollow` (sans index : un seul détail) |
| Retrouver un projet déplacé | Mes projets (détail d'un projet introuvable) | `home-find` |
| Chercher les projets dans un dossier, suivre ceux trouvés | Ouvrir un projet (et un bouton depuis « Mes projets » vide) | `home-search`, `home-found-*`, `home-follow-found` : inchangées |
| Projets récents, les suivre, effacer la liste | Ouvrir un projet | `home-recent-{i}`, `home-follow-{i}`, `home-clear` : inchangées |
| Ouvrir un fichier projet (fenêtre « Ouvrir » ou chemin collé) | Ouvrir un projet | `browse-home-project`, `home-project`, `home-open` : inchangées |
| Nouveau projet à partir d'une base ; projet existant : l'ouvrir ou le remplacer | Nouveau projet | `home-database`, `home-create`, `home-open-existing`, `home-replace` : inchangées |
| Concevoir un questionnaire | Concevoir un questionnaire | `home-design-*` : inchangées |
| Changer de langue | Réglages | `interface-language` : inchangée |
| Avertissement de l'anglais | En tête de chaque onglet | — |
| Essayer l'outil | **Retiré** (partie B) | `home-trial*` disparaissent |

Messages : les textes d'aujourd'hui restent mot pour mot, sauf les deux qui renvoient au « menu ⋮ de sa ligne » (« Si ce n'est pas le bon, retirez-le avec « Ne plus suivre »… ») et l'en-tête du tableau, qui disparaît. Tests touchés : `tests/test_home_projects.py` (le clic sélectionne, l'ouverture passe par le détail), `tests/test_home.py` (choisir l'onglet par `home_tab`), `tests/test_tracked.py` (essai retiré).

### 7.5 La maquette avant le code (point 12)

Étape C1 : une première version **sans logique** des cinq onglets et du détail (des données tirées de `tests/projets_stades.py` : un projet complet, un en conception, un introuvable), et `scripts/captures.py` étendu à l'accueil, en clair, à 1400 × 900 et 900 × 600 (10 images). Je vous les montre et j'attends votre avis avant d'écrire la logique.

## 8. Partie D — le nom d'un projet

### 8.1 Ce que « nom » veut dire (point 13)

| Façon | Pour | Contre |
|---|---|---|
| **1. Un titre dans le projet** | Aucun fichier ne bouge : rien ne casse, ni le carnet, ni les scripts déjà écrits, ni les projets suivis et récents, ni un lecteur réseau. Un seul enregistrement, protégé par D-129 et D-130. Le dossier d'étude (v0.19) pourra nommer les fichiers par le code de l'étude sans que le titre s'en mêle. | Le nom du fichier et le titre peuvent différer (le détail montre les deux). Changement de format : 0.11.0. |
| **2. Renommer les fichiers** | Le dossier dit le même nom que l'interface. | Les fichiers déjà écrits nomment d'autres fichiers dans leur contenu (§ 3) : les scripts R d'analyse ne trouveraient plus `etude-metadonnees.R` ; il faudrait les réécrire, donc changer des fichiers produits, ou les laisser cassés. Windows n'a pas de renommage groupé : un fichier ouvert dans Word ou verrouillé par OneDrive au milieu de la série oblige à défaire ce qui est fait, et ce retour peut échouer à son tour. Le dossier d'étude prévu en v0.19 redéfinira le nom des fichiers : ce travail serait refait. |
| **3. Les deux** | Le choix à la personne. | Tous les contre de la façon 2, plus une option à expliquer. |

**Recommandation (D-161) : la façon 1, un titre.** Le renommage des fichiers est remis au dossier d'étude, qui définira comment les fichiers d'une étude se nomment ; s'il faut alors renommer, ce sera dans ce cadre.

### 8.2 Le titre

- **Le format** : `Project.title: str | None = None`, juste après `schema_version` dans le fichier. `SCHEMA_VERSION` passe à **0.11.0**. Un projet 0.10.0 ou plus ancien s'ouvre tel quel (sans titre) ; un projet 0.11.0 ouvert par la 0.20.1 est signalé « écrit par une version plus récente » comme aujourd'hui (`ProjectNewer`), dans « Mes projets » et à l'ouverture.
- **Humain seulement** : écrit par une personne, jamais proposé par l'IA, jamais envoyé au modèle (la porte de confidentialité ne le lit pas ; un test le vérifie sur les quatre messages). Il n'entre pas dans l'empreinte du codebook (`fingerprint` liste ses champs un par un ; un test le vérifie) : renommer ne met aucune analyse « à recalculer ».
- **Validation** : rogné ; vide, il est effacé et le nom du fichier revient ; au plus 120 caractères ; une seule ligne. Aucun caractère interdit : ce n'est pas un nom de fichier.
- **Où il se montre** : la liste et le détail de « Mes projets » (`ProjectRow.name` rend le titre, sinon le radical du fichier ; `ProjectRow.file_name` garde le radical), en tête de la barre de gauche d'un projet ouvert (le titre, et en dessous la base, `dataset_title`), le titre de l'onglet du navigateur, `ddict projets lister`. **Pas dans les fichiers produits** dans ce plan (les exports ne changent pas) ; le mettre en tête du codebook ou de l'article serait une décision à part.
- **La recherche dans un dossier** (D-132) montre toujours les noms des fichiers : elle n'ouvre aucun fichier, et ne peut donc pas lire un titre.
- **Un projet conçu dans l'outil** garde le nom de son questionnaire (`questionnaire.file_name`, celui du Word) : le titre du projet ne le change pas.

### 8.3 Si vous préférez renommer les fichiers (point 14)

Pour mémoire, ce qu'il faudrait, au cas où vous retiendriez la façon 2 ou 3 : la liste complète « ancien nom → nouveau nom » avant tout ; refus d'un nom pris, réservé (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`, avec ou sans extension), d'un caractère interdit (`<>:"/\|?*`, fin en point ou espace) ou d'un chemin de plus de 259 caractères ; refus tant qu'un `.tmp` d'un enregistrement interrompu est là ; essai de chaque renommage dans l'ordre, et à la première erreur, retour en arrière de ceux déjà faits (et, si le retour échoue, la liste exacte de l'état laissé) ; jamais la base ni le questionnaire ; le lien du carnet réécrit par `save_notebook` ; `tracked.replace` et les récents mis à jour ; la question des scripts R déjà écrits tranchée (les réécrire, ou les laisser). Une étape de plus, la plus risquée du plan.

### 8.4 Où renommer (point 15)

- **Dans le détail du projet** (« Mes projets ») : « Renommer » ouvre, sous le nom, un champ et « Enregistrer le titre » ; « Revenir au nom du fichier » l'efface. Le projet est lu, le titre posé, puis `save_project`, qui refuse si le fichier a changé depuis la lecture (D-129) ; le message de refus est celui de D-130.
- **Une fois le projet ouvert** : un petit bouton crayon à côté du titre, en tête de la barre de gauche, qui ouvre le même champ dans une fenêtre surgissante (`st.popover`) ; enregistré par `c.save` (D-130), avec son rappel.
- **En ligne de commande** : `ddict projets renommer FICHIER "Titre"` (et `--effacer`), dans `cli_projects` à côté de `lister` ; simple avec un titre.
- **Un projet ouvert dans une autre fenêtre** : l'outil ne peut pas le savoir (aucun verrou, par choix : D-130). Avec un titre, ce n'est pas un danger : l'autre fenêtre voit « Ce projet a été modifié ailleurs » à son prochain affichage, et rien de ce qu'elle décide n'écrase le titre sans prévenir. Le guide le dit.

## 9. Étapes

Chaque étape : tests écrits avec le code, catalogue anglais à jour, `ruff` et `pytest` passés, arrêt pour revue.

| # | Étape | Critère de réussite |
|---|---|---|
| **B1** | Retirer l'essai (§ 6) ; D-159 au journal | Plus aucune mention de `trial`, `DDICT_TRIAL_DIR` ni « Essayer » dans `src/`, `tests/`, `scripts/` ; le paquet construit (`uv build`) ne contient plus `etude-sommeil.sav` et contient `questionnaire-sommeil.pdf` ; le banc passe ; guide et scénario corrigés |
| **C1** | **Maquette** de l'accueil, sans logique (§ 7.5) | Captures montrées ; **arrêt pour votre avis** |
| **C2** | La navigation de l'accueil (§ 7.1) | Cinq onglets ; rechargement sur chaque adresse sans « Page not found » ; « Accueil » depuis `/plan` ouvre « Mes projets » ; l'onglet reste après une action ; tests existants passés avec les seules clés du § 7.4 changées |
| **C3** | Mes projets : liste et détail (§ 7.2, 7.3) ; `ProjectRow` complété, `overview.produced` | Détail d'un projet complet, d'un projet en conception (D-154) et d'un projet introuvable ; chaque tâche ouvre sa page ; aucun fichier ouvert hors du projet et du carnet (test : la base absente ou illisible ne change rien) ; D-160 au journal |
| **C4** | Les autres onglets ; la liste du § 7.4 vérifiée fonction par fonction | Un test par ligne du § 7.4 |
| **D1** | Le titre : format 0.11.0, `ProjectRow.name`, barre de gauche, ligne de commande ; D-161 au journal | Un projet 0.10.0 s'ouvre ; un 0.11.0 est « plus récent » pour la 0.20.1 (fichier de test) ; le titre n'entre ni dans l'empreinte ni dans un message à l'IA ; enregistrement refusé si le fichier a changé |
| **D2** | Renommer depuis le détail et depuis le projet ouvert | AppTest : renommer, rouvrir, le carnet et ses analyses sont là, rien « à recalculer » |
| **E1** | Captures, guide (accueil réécrit, renommage ; français et anglais), scénario (étapes 97 et suivantes), journal des changements, `CONCEPTION.md` (une section), version | Scénario passé dans la fenêtre de l'icône |

**Le scénario manuel**, nouvelles étapes : parcourir les cinq onglets, recharger sur chacun ; détail d'un projet complet, d'un projet en conception et d'un projet introuvable (le retrouver) ; renommer un projet depuis le détail, l'ouvrir, son carnet et ses analyses sont là ; le renommer depuis la barre de gauche ; vérifier que l'essai a disparu ; ouvrir le dossier `Documents\Dictionnaire de données - essai` d'une version précédente, s'il existe.

## 10. Décisions à prendre

| N° | Décision | Ma recommandation |
|---|---|---|
| **D-159** | **Retirer l'essai** (remplace D-125) | Retirer la section, `trial.py`, ses tests et `DDICT_TRIAL_DIR` ; retirer `etude-sommeil.sav` du paquet ; **garder `questionnaire-sommeil.pdf`**, dont le banc se sert ; ne pas toucher aux dossiers d'essai existants. |
| **D-160** | **La structure de l'accueil** | `st.navigation` avec cinq pages (Mes projets, Nouveau projet, Concevoir un questionnaire, Ouvrir un projet, Réglages), « Quitter l'outil » en bas ; la liste des projets **dans la fenêtre**, à gauche du détail ; le détail du § 7.3, les fichiers produits calculés pour le projet choisi seulement. |
| **D-161** | **Renommer = un titre** | Un titre facultatif dans le projet, format **0.11.0**, montré dans l'interface et la ligne de commande, jamais dans les fichiers produits ni envoyé au modèle, hors de l'empreinte ; **aucun fichier renommé** ; le renommage des fichiers remis au dossier d'étude. |
| **D-162** | **Le numéro de version** | La partie « Non publié » change déjà le format (D-158, 0.10.0) : la 0.20.2 ne sera pas « sans changement de format », quoi qu'on fasse. Je propose **une seule version, 0.20.2**, avec D-158, les parties B, C et D et le format 0.11.0 (le format 0.10.0 n'ayant jamais été publié, une personne passe de 0.9.0 à 0.11.0 en une fois). Autre voie : publier la 0.20.2 après la partie C (format 0.10.0), puis le titre en 0.20.3 (format 0.11.0), pour essayer l'accueil plus tôt. |

## 11. Risques

- **La navigation de l'accueil** : deux navigations différentes dans la même application (accueil et projet), avec les pièges d'adresse de la v0.16. L'étape C2 teste chaque rechargement, dans la fenêtre de l'icône aussi.
- **Les tests de l'accueil** : `test_home.py` et `test_home_projects.py` changent (le clic sélectionne au lieu d'ouvrir) ; les tests de logique (`test_overview.py`, `test_tracked.py`) restent le filet.
- **Un lecteur réseau lent** : `overview.produced` lit la liste d'un dossier à chaque affichage du détail ; si c'est lent à l'essai, il se garde en mémoire comme les lignes (date du dossier).
- **Le titre et le nom du fichier divergent** : le détail montre les deux ; le guide explique que le titre ne renomme rien.
