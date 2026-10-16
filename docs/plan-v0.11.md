# Plan de la v0.11

> Statut : **validé par l'auteur le 2026-10-16**, avec les décisions D-087 à D-092 (§ 8). Suit la feuille de route [`feuille-de-route-article.md`](feuille-de-route-article.md), § 4. Cap fixé par l'auteur : aller de la base à une ébauche d'article IMRaD **sans aucune IA** ; la v0.11 n'ajoute aucun usage de l'IA, locale ou non ; la règle « Rien ne quitte le poste » reste entière ; l'IA conseillère reste telle quelle.

## 1. Pourquoi cette version

La page « Analyses » ne garde que la dernière analyse, en mémoire (D-078), et chaque fichier Word recommence à « Tableau 1 ». Un article réunit dix ou vingt résultats, numérotés à la suite, qui doivent rester justes quand le codebook change (un code manquant confirmé après coup, un niveau de mesure corrigé). Il faut donc un **carnet d'analyses** : la liste des analyses d'une étude, gardée à côté du projet, recalculée à chaque export, et réunie dans un document « Résultats » et un script R maître.

## 2. Ce que l'outil produira

- **Le carnet**, `<projet>-carnet.json`, à côté du projet (D-087, D-091). Le fichier projet reste un dictionnaire de données.
- **« Ajouter au carnet »**, sur la page « Analyses », sous le résultat affiché. L'entrée reçoit un identifiant stable (`A1`, `A2`…), jamais réutilisé après un retrait, et garde :
  - l'analyse, ses variables par rôle et ses options ;
  - les titres et les notes changés par une personne (D-086 ; les numéros, voir D-090) ;
  - l'empreinte du codebook, la date et les versions (outil, Python, SciPy, statsmodels) ;
  - les statistiques agrégées du résultat, ses effectifs, sa phrase APA et ses avertissements (effectifs inférieurs à 5 signalés, comme dans le rapport) ;
  - « retenue pour l'article » et un rang.
- **Aucune donnée individuelle** dans le carnet (D-088) : ni ligne de la base, ni identifiant, ni point de nuage, ni valeur observée isolée (l'étendue du Tableau 1 n'y entre pas). Les figures sont redessinées à partir de la base au moment de l'export.
- **La page « Carnet »**, après « Analyses » : la liste des entrées et leur état (à jour, changée, impossible), l'ordre, retenir ou écarter, voir ce qui a changé statistique par statistique, confirmer, retirer, et produire les résultats.
- **Le document des résultats** (`<projet>-resultats.docx`, D-092) : les analyses retenues, dans l'ordre du carnet, chacune avec un intertitre, sa phrase APA, ses tableaux et ses figures au format de la v0.10, **numérotés à la suite** (Tableau 1 à *n*, Figure 1 à *m*, D-090) ; à la fin, l'empreinte du codebook et la liste des analyses (identifiant, analyse, variables). À côté, le **classeur commun** des graphiques Excel natifs (`<projet>-resultats-graphiques.xlsx`), une feuille par figure, aux mêmes numéros.
- **Le script R maître** (`<projet>-resultats-R.zip`) : le fichier de commandes, le script de préparation, puis chaque analyse retenue dans l'ordre du carnet, chacune rangée sous son identifiant (`resultats$A3`). Mêmes valeurs que l'outil, à 10⁻⁶ près.
- **En ligne de commande** : `ddict carnet` (`notebook`) pour lister, ajouter, retirer, réordonner, retenir, écarter et confirmer ; `ddict resultats` (`results`) pour le document, le classeur et le script maître.

## 3. Conception — le carnet

**Le fichier.** Un modèle pydantic (`extra="forbid"`), écrit comme le projet : JSON indenté de 2, clés dans l'ordre du modèle, UTF-8, LF, écriture atomique (fichier temporaire puis remplacement), `allow_nan=False`. Sa propre version de format, `carnet_version` (1.0.0), lue et migrée comme `schema_version` du projet : un carnet d'une version majeure différente ou plus récente est refusé avec sa raison. Il rappelle le projet auquel il appartient (empreinte `sha256` de la base et nom du fichier projet), pour refuser un carnet posé à côté d'un autre projet.

**Une entrée.**

```json
{
  "id": "A3",
  "analysis": "t_test",
  "variables": {
    "outcome": [{"score": "G1"}],
    "group": [{"variable": "groupe"}]
  },
  "options": {"method": "welch", "alternative": "two_sided"},
  "edits": {"table-1": {"title": "Bien-être selon le groupe", "note": null}},
  "retained": true,
  "rank": 2,
  "computed": {
    "fingerprint": "a8ed754d4e07…",
    "date": "2026-10-16",
    "versions": {"dictionnaire-donnees": "0.11.0", "Python": "3.11.9", "SciPy": "1.17.1", "statsmodels": "0.15.0"},
    "n_used": 300, "n_excluded": 0,
    "statistics": {"t": 4.9997, "df": 297.2859, "p": 1.0e-06, "d": 0.5773, "…": "…"},
    "sentence": "bienetre_total (score de G1) : M = 17,01 …",
    "warnings": []
  }
}
```

**Les variables par leur clé du projet** (demande de l'auteur). Le calcul désigne les variables par leur nom final (après renommage) ; le carnet, lui, garde une référence qui survit à un renommage :

- `{"variable": "<nom d'origine>"}` : une variable du fichier ;
- `{"score": "<groupe>"}` : le score de la cotation structurée d'un groupe ;
- `{"reversed": "<nom d'origine de l'item>"}` : un item inversé (`<item>_inv`).

Au recalcul, chaque référence redonne le nom final en vigueur ; une référence qui ne mène plus à rien (variable retirée, cotation supprimée, item plus inversé) rend l'analyse **impossible**, avec sa raison.

**Les statistiques gardées.** Les clés de `AnalysisResult.statistics`, telles quelles. Deux analyses n'en gardent aujourd'hui aucune et sont complétées à l'étape 2 : le **Tableau 1** (par variable et par colonne : *n*, *M*, *ÉT*, effectif de chaque catégorie) et la **corrélation à trois variables ou plus** (par paire : *n*, *r*, *p*, IC). Les médianes de Mann-Whitney et de Kruskal-Wallis sont gardées : ce sont les statistiques que publie l'article (D-088).

**Les numéros, les titres et les notes.** Les titres et les notes changés par une personne sont gardés par élément (`table-1`, `figure-1` de l'analyse), comme aujourd'hui (D-086). Les numéros, eux, sont donnés par l'ordre du carnet (D-090).

## 4. Conception — recalcul, comparaison, confirmation (D-089)

**État d'une entrée**, établi chaque fois que la page « Carnet » s'ouvre ou qu'un export est demandé :

| État | Quand | Ce que l'outil fait |
|---|---|---|
| **À jour** | Même empreinte du codebook qu'au calcul | Rien |
| **Recalculée, inchangée** | Empreinte changée, mais chaque statistique égale (à 10⁻⁹ près, relatif) | L'outil le dit (« rien n'a changé »), met à jour l'empreinte et la date |
| **Changée, à confirmer** | Au moins une statistique ou un effectif différent | Liste statistique par statistique : avant, après, aux décimales de l'APA ; **Confirmer** remplace les statistiques gardées |
| **Impossible** | Référence perdue, niveau de mesure qui ne convient plus, condition D-074 non remplie | Raison affichée ; l'entrée n'est ni supprimée ni recalculée ; elle est écartée du document, et la fin du document le dit |
| **Base introuvable ou modifiée** | Base absente, ou d'une autre empreinte que celle du projet | Le carnet reste lisible (statistiques et phrases gardées) ; rien ne se recalcule ni ne s'exporte ; l'outil le dit, comme la page « Analyses » |

**À l'export**, chaque analyse retenue est recalculée sur la base, avec les décisions en vigueur ; le document n'est jamais une copie du carnet. Une analyse retenue **changée et non confirmée** empêche l'export : la page et la commande disent lesquelles, et ce qui a changé. Ainsi, aucun chiffre ne change dans un document sans qu'une personne l'ait vu.

## 5. Conception — le document des résultats et le script maître

**Le document.** La description neutre de la v0.10 (`ApaDocument`) reçoit des **sections** : une par analyse retenue (identifiant, intertitre, phrase APA, tableaux, figures). Un document d'une seule analyse, celui de la page « Analyses », devient un document d'une section : rien ne change pour lui. Les formats inscrits (Word, graphiques Excel) rendent les sections dans l'ordre ; le **test commun des formats** (D-083) passe sur un document de plusieurs analyses. `describe(…, first_table=…, first_figure=…)` existe déjà : chaque section part du numéro qui suit la précédente.

**Le script maître.** L'en-tête une seule fois (lecture de la base, fichier de commandes, script de préparation, fonction `ddict_num`), puis chaque analyse dans un `local({ … ; resultats })` pour que ses variables de travail (`x`, `test`, `fit`…) ne se mêlent pas, rangée sous `resultats$A3`. Le corps R de la **corrélation à trois variables ou plus** ne calcule aujourd'hui que la première paire : il est corrigé (toutes les paires), et le Tableau 1 et Tukey reçoivent en R les clés ajoutées dans l'outil, pour que la comparaison à 10⁻⁶ porte sur chaque statistique gardée.

**Les fichiers `<projet>-analyse-<n>`** de la page « Analyses » restent tels quels (D-092) : ils servent à une analyse seule, avec ses propres numéros modifiables.

## 6. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiche du carnet : format complet, exemple sur la base fictive des analyses (quatre entrées), ce qui est gardé et ce qui ne l'est jamais, états et confirmation, règles d'ordre et de numérotation, noms des fichiers ; scénario de la décision changée après coup | Validée par l'auteur |
| 2 | Modèle et fichier du carnet : références des variables, statistiques complétées (Tableau 1, corrélation à plusieurs variables), ajout, retrait (identifiants jamais réutilisés), ordre, retenue ; écriture et lecture, version du format | Aller-retour octet pour octet ; références qui survivent à un renommage ; **test à chaînes témoins** (les témoins `ZQX…` des bases fictives, et aucune paire de valeurs d'un nuage de points, aucune étendue observée) |
| 3 | Recalcul, comparaison, confirmation ; analyse impossible ; base introuvable ou modifiée | Sur la base fictive des analyses : un code manquant confirmé après coup change les effectifs d'une analyse et l'outil le dit, statistique par statistique ; un libellé corrigé change l'empreinte sans rien changer, et l'outil le dit ; un niveau de mesure changé rend une analyse impossible, avec sa raison ; une analyse changée non confirmée bloque l'export |
| 4 | Document des résultats : sections, numérotation continue, titres et notes repris, liste finale ; classeur commun des graphiques | Test commun des formats passé sur un document de quatre analyses ; Tableau 1 à *n* et Figure 1 à *m* sans trou ni doublon ; vérifié dans Word et Excel |
| 5 | Script R maître | Exécuté dans R : mêmes valeurs que l'outil, à 10⁻⁶ près, pour chaque statistique gardée de chaque analyse du carnet, y compris une corrélation à trois variables |
| 6 | Page « Carnet », bouton « Ajouter au carnet », `ddict carnet`, `ddict resultats` | Parcours dans le navigateur ; mêmes fichiers depuis la page et la ligne de commande |
| 7 | Essai sur une vraie base (calcul et script R sans erreur, aucun résultat consigné) ; guides, journal des changements, version 0.11.0 | Scénario refait dans le navigateur ; guides en français et en anglais. *Essai : `docs/essais/2026-10-16-essai-carnet.md`.* |

## 7. Risques

- **Un carnet qui ne correspond plus au projet** (projet déplacé, base réexportée) : le carnet rappelle l'empreinte de la base et refuse de recalculer sur une autre ; il reste lisible.
- **Des statistiques qui changent de forme** d'une version de l'outil à l'autre (une clé ajoutée) : la comparaison ne porte que sur les clés communes, et le carnet garde la version de l'outil qui les a calculées.
- **Des valeurs individuelles par une porte dérobée** : une médiane d'un petit groupe, l'effectif d'une catégorie d'une personne. Elles sont gardées comme dans le rapport, signalées sous 5, et la décision de publier reste à l'équipe ; le test à chaînes témoins garde les lignes, les identifiants, les points et les étendues hors du carnet.
- **Un export long** : vingt analyses et leurs figures se recalculent et se dessinent en quelques secondes ; la page montre une barre de progression.
- **Une version chargée** : si elle s'allonge, le script R maître (étape 5) passe en 0.11.1 ; le carnet et le document sont utiles seuls.

## 8. Décisions à prendre

La feuille de route réservait D-087 à D-089 au carnet ; les six décisions ci-dessous prennent D-087 à D-092. Les numéros que la feuille de route proposait pour les versions suivantes (D-090 et au-delà) se décaleront d'autant au moment de leur adoption.

| N° | Décision | Recommandation |
|---|---|---|
| D-087 | **Le carnet hors du projet, et D-078** | Un fichier à côté du projet ; le projet reste un dictionnaire. Remplace D-078 en partie : la dernière analyse reste affichée en mémoire sur la page « Analyses » ; une personne peut l'**ajouter au carnet** ; rien n'y entre sans ce geste. |
| D-088 | **Ce que garde le carnet, et ce qu'il ne garde jamais** | Garde : l'analyse, les variables par leur clé du projet (nom d'origine, groupe d'un score, item inversé), les options, les titres et les notes changés, l'empreinte, la date, les versions, les statistiques agrégées (médianes comprises), les effectifs, la phrase APA, les avertissements (effectifs inférieurs à 5 gardés et signalés), retenue et rang. Ne garde jamais : une ligne de la base, un identifiant, un point de nuage, une étendue observée (minimum, maximum). Vérifié par un test à chaînes témoins. |
| D-089 | **Recalcul à chaque export, et confirmation** | Le document et le script sont toujours recalculés sur la base, avec les décisions en vigueur. Une analyse dont l'empreinte a changé est recalculée : inchangée, l'outil le dit et met l'empreinte à jour ; changée, elle attend la confirmation d'une personne, qui remplace les statistiques gardées, et bloque l'export tant qu'elle est retenue ; impossible, elle est signalée avec sa raison, jamais supprimée, et écartée du document. Base introuvable ou modifiée : carnet lisible, rien ne se recalcule. |
| D-090 | **Numérotation continue et numéros changés à la main** | Dans le document des résultats, les numéros sont toujours donnés par l'ordre des analyses retenues : Tableau 1 à *n*, Figure 1 à *m*, sans trou ni doublon. Pour changer un numéro, une personne change l'ordre. Un numéro de départ par document (« le premier tableau des résultats est le Tableau 3 ») est réglable, pour laisser la place aux tableaux de la Méthode (v0.12). Les numéros changés à la main sur la page « Analyses » valent pour le fichier de cette seule analyse et n'entrent pas au carnet ; les titres et les notes, si. |
| D-091 | **Nom, emplacement et version du fichier carnet** | `<projet>-carnet.json` à côté du fichier projet (même préfixe que les autres fichiers, `etude-carnet.json` pour `etude.dd.json`) ; JSON déterministe comme le projet ; `carnet_version` 1.0.0, sa propre suite de versions et ses migrations ; le carnet rappelle l'empreinte de la base et le nom du projet. |
| D-092 | **Les fichiers `<projet>-analyse-<n>` actuels** | Gardés tels quels : le rapport, les tableaux, le script R et les fichiers APA d'une analyse seule, depuis la page « Analyses ». Le carnet produit ses propres fichiers, remplacés à chaque export (comme le codebook) : `<projet>-resultats.docx`, `<projet>-resultats-graphiques.xlsx`, `<projet>-resultats-R.zip`. |
