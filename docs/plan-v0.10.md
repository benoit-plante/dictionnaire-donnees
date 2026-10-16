# Plan de la v0.10

> Statut : **validé par l'auteur le 2026-10-16**, avec les décisions D-082 à D-086 (§ 7). Choix donnés par l'auteur : figures en image dans Word, avec à côté un graphique Excel natif pour les modifier ; Word (.docx) comme seul format de cette version ; d'autres formats faciles à ajouter plus tard. Les modèles infonuagiques pour l'IA conseillère viendront après.

## 1. Pourquoi cette version

La v0.9 calcule six analyses et donne leurs résultats en phrase APA, en tableaux simples (Markdown, Excel) et en script R. Pour un article, un mémoire ou un rapport, il manque **des tableaux et des figures présentés selon les normes APA 7, prêts à coller et modifiables** : aujourd'hui, l'équipe les refait à la main, avec le risque d'une erreur de recopie.

## 2. Ce que l'outil produira

Pour chaque analyse lancée, sur la page « Analyses » ou par `ddict analyser` :

| Analyse | Tableau APA | Figure APA |
|---|---|---|
| Tableau 1 | caractéristiques de l'échantillon, par groupe au besoin | aucune |
| Test t | *n*, *M*, *ÉT* par groupe ; *t*, ddl, *p*, *d* et son IC | moyennes des deux groupes et leur IC 95 % |
| ANOVA | *n*, *M*, *ÉT* par groupe ; *F*, ddl, *p*, η², ω² ; comparaisons de Tukey | moyennes par groupe et leur IC 95 % |
| Khi-carré | tableau croisé (effectifs et pourcentages) ; χ², ddl, *p*, *V* | barres groupées des pourcentages |
| Corrélation | *M*, *ÉT* et matrice des *r* (IC 95 %) | nuage de points avec droite de régression (deux variables) |
| Régression | *b*, *ET*, IC 95 %, β, *t*, *p* ; *R²*, *R²* ajusté, *F* | coefficients standardisés et leur IC 95 % |

**Normes APA 7.** Tableau : « **Tableau 1** » en gras, titre en italique à la ligne suivante, filets horizontaux seulement (au-dessus et au-dessous de l'en-tête, en bas), aucun filet vertical, statistiques en italique, *p* sans zéro initial, colonnes de nombres alignées, « *Note.* » en italique sous le tableau (note générale, puis notes de probabilité). Figure : « **Figure 1** » en gras, titre en italique, axes nommés avec leurs unités, sans quadrillage ni cadre superflu, police sans empattement, note sous la figure. En français (virgule décimale, « Tableau », « *ÉT* ») ou en anglais (« Table », « *SD* »), selon la langue choisie, comme le codebook.

**Éditable.** Dans la page : le numéro, le titre et la note de chaque tableau et de chaque figure se modifient avant l'export (le contenu chiffré, non : il vient du calcul). Puis :

- **Word (.docx)** : chaque tableau est un vrai tableau Word, mis en forme APA, que l'on modifie comme tout tableau ; chaque figure est une image nette (300 points par pouce), avec son numéro, son titre et sa note en texte modifiable.
- **À côté, le graphique Excel natif** de chaque figure (un `.xlsx` par analyse, une feuille par figure, avec ses données) : on y change les couleurs, les axes ou les étiquettes, puis on le copie dans Word, où il reste modifiable (D-084).

## 3. Conception — ajouter un format facilement (D-083)

Deux couches, et rien d'autre à toucher pour un nouveau format :

1. **Une description neutre** (`ddict.analysis.apa`) : pour un tableau, son numéro, son titre, ses colonnes (avec les en-têtes regroupés), ses lignes (avec leur retrait et leur alignement), les cellules en italique, ses notes ; pour une figure, son numéro, son titre, son type (moyennes et IC, barres groupées, nuage de points, coefficients), ses séries, ses axes, ses barres d'erreur et sa note. Elle est calculée une seule fois, à partir du résultat de l'analyse, et elle ne sait rien d'aucun format.
2. **Un exportateur par format**, chacun dans son propre module (`ddict.analysis.formats.docx`, `.xlsx_chart`…), inscrit dans une liste avec son nom, son extension et ce qu'il sait rendre (tableaux, figures, ou les deux). La page et `ddict analyser --format docx` proposent d'eux-mêmes tous les formats de la liste.

Un **test commun** passe sur chaque format inscrit : tous les chiffres de la description se retrouvent dans le fichier, avec les mêmes décimales ; les numéros, les titres et les notes aussi ; rien n'est inventé. Un format futur (LaTeX, HTML, PowerPoint, Markdown APA, figure en R…) devient un module de plus et passe ce test.

## 4. Les bibliothèques (D-082)

- **python-docx** (licence MIT) : écrire le fichier Word, ses tableaux et ses styles.
- **matplotlib** (sa propre licence, fondée sur celle de Python, permissive et compatible avec Apache-2.0 ; ses dépendances, dont Pillow, aussi) : dessiner les figures en image, dans un style APA réglé une fois.
- **openpyxl**, déjà utilisé : les graphiques Excel natifs.

Toutes trois s'installent avec l'outil, sans rien d'autre ; à noter dans `docs/dependances.md`.

## 5. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiches : un tableau et une figure modèles par analyse, en français et en anglais, sur la base fictive des analyses ; règles APA 7 retenues | Validées par l'auteur |
| 2 | Description neutre (`apa.py`) des tableaux et des figures, à partir des résultats de la v0.9 | Chaque chiffre égal à celui du résultat (tests) ; numéros, titres, notes |
| 3 | Liste des formats et test commun ; exportateur Word (tableaux, figures en image) | Test commun passé ; mise en forme APA vérifiée dans le fichier (filets, italiques, alignement) |
| 4 | Graphiques Excel natifs des figures | Test commun passé ; graphique présent et lié à ses données |
| 5 | Page « Analyses » : aperçu des tableaux et des figures, numéro, titre et note modifiables, téléchargements ; `ddict analyser --format` | Parcours dans le navigateur ; mêmes fichiers que la ligne de commande |
| 6 | Vérification dans Word et Excel, par l'auteur, sur la base fictive ; corrections | Rendu jugé conforme à l'APA par l'auteur. *Le 2026-10-16, l'auteur a demandé de passer à l'étape 7 sans cette vérification ; ses retours restent attendus. Le rendu a été vérifié dans Word et Excel par l'outil (conversion en PDF et export des graphiques) aux étapes 3 à 5.* |
| 7 | Guides, journal des changements, version 0.10.0 | Scénario refait dans le navigateur ; guides en français et en anglais |

## 6. Risques

- **Le rendu dans Word** se vérifie mal par des tests seuls : l'étape 6 demande l'œil de l'auteur, dans son Word.
- **Les normes APA** laissent des choix (une colonne d'IC ou deux, l'astérisque des seuils) : l'étape 1 les fixe une fois, avec l'auteur. Pas d'astérisques de signification par défaut : l'outil donne les *p* exacts, comme sa phrase de résultat, qui décrit sans juger.
- **Les nuages de points** montrent des données individuelles : ils restent sur le poste, comme tous les résultats ; le guide rappelle de juger ce qui peut être publié.

## 7. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-082 | **Bibliothèques** | python-docx (MIT) et matplotlib (licence permissive), nouvelles dépendances ; openpyxl pour les graphiques Excel. |
| D-083 | **Formats extensibles** | Une description neutre des tableaux et des figures, un exportateur par format inscrit dans une liste, un test commun à tous les formats. |
| D-084 | **Figures éditables** | Image nette dans le fichier Word ; à côté, le graphique Excel natif, avec ses données, pour le modifier et le coller dans Word (choix de l'auteur). |
| D-085 | **Formats de la v0.10** | Word (.docx) seulement, plus le classeur des graphiques natifs ; les autres formats (images seules, Markdown APA, LaTeX, PowerPoint…) viendront comme des modules de plus (choix de l'auteur). |
| D-086 | **Ce qui se modifie dans l'outil** | Le numéro, le titre et la note ; jamais les chiffres, qui viennent du calcul. Pas d'astérisques de signification par défaut. |
