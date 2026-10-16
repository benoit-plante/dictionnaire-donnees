# Tableaux et figures APA 7 : les fiches

> Statut : **proposé à l'auteur le 2026-10-16** (v0.10, étape 1), à valider avec le prototype Word. Chiffres : base fictive des analyses (`etude-analyses.sav`), échelle de bien-être cotée comme le dit le corrigé.

Ce document fixe, une fois pour toutes, ce que chaque analyse du catalogue produit comme tableau et comme figure, et les règles APA 7 retenues. Le code (étapes 2 à 5) suivra ces fiches ; un format futur (D-083) aussi.

## 1. Règles communes

**Tableaux** :

- Au-dessus : « **Tableau 1** » en gras, puis, à la ligne, le titre en *italique*, en casse de phrase en français (« *Bien-être selon le groupe* »), en casse de titre en anglais.
- Filets horizontaux seulement : au-dessus et au-dessous de l'en-tête, au bas du tableau ; un filet court sous un en-tête qui regroupe des colonnes. Aucun filet vertical, aucune trame.
- Police du document (Times New Roman 12 ou Calibri 11 : celle de Word, modifiable), simple interligne dans le tableau.
- Première colonne alignée à gauche, les autres centrées ; les catégories d'une variable en retrait sous elle.
- Symboles statistiques en *italique* (*n*, *M*, *ÉT*, *t*, *F*, *p*, *r*, *b*, *d*, *V*) ; lettres grecques en romain (η², ω², β, χ²).
- Deux décimales ; trois pour *p* ; *p* sans zéro initial (,001), « < ,001 » sous ce seuil ; pas de zéro initial pour ce qui ne dépasse pas 1 en valeur absolue (*r*, β, *p*, *V*, η²), un zéro initial ailleurs (*d* = 0,58). Le signe moins est le vrai signe « − ».
- Intervalles de confiance : « [0,35 ; 0,81] » en français, « [0.35, 0.81] » en anglais ; l'en-tête dit « IC 95 % » ou « 95% CI ».
- Au-dessous : « *Note.* » en italique, puis la note générale (abréviations, *n*, ce que montrent les valeurs). **Pas d'astérisques de signification** (D-086) : les *p* exacts sont dans le tableau.

**Figures** :

- Au-dessus : « **Figure 1** » en gras, puis le titre en *italique* ; au-dessous, « *Note.* » et la note (ce que montrent les barres d'erreur, *n*).
- Police sans empattement (Arial) de 8 à 14 points dans l'image ; axes nommés, avec leur unité ; pas de quadrillage, pas de cadre en haut ni à droite, pas de titre dans l'image (il est dans le texte, modifiable).
- Gris et noir, lisibles en noir et blanc ; barres d'erreur : IC 95 %, dit dans la note.
- Image de 300 points par pouce, de la largeur d'une colonne de texte (16 cm) ; à côté, le graphique Excel natif et ses données (D-084).

**Ce qui se modifie dans l'outil** (D-086) : le numéro, le titre et la note ; jamais les chiffres.

**Variables** : désignées par leur libellé accepté (« Âge (années) ») ; un score, par son nom (« bienetre_total ») tant que l'équipe ne lui a pas donné de libellé.

## 2. Tableau 1 — décrire l'échantillon

**Tableau 1**
*Caractéristiques des participants selon le groupe*

| Caractéristique | Intervention (*n* = 150) | Contrôle (*n* = 150) | Total (*N* = 300) |
|---|---|---|---|
| Âge (années), *M* (*ÉT*) | 44,70 (12,77) | 42,41 (12,69) | 43,56 (12,76) |
| Sexe, *n* (%) | | | |
|     Femme | 81 (54,0) | 67 (44,7) | 148 (49,3) |
|     Homme | 69 (46,0) | 83 (55,3) | 152 (50,7) |
| Plus haut niveau d'études, *n* (%) | | | |
|     Secondaire | 49 (32,7) | 54 (36,0) | 103 (34,3) |
|     Collégial | 51 (34,0) | 48 (32,0) | 99 (33,0) |
|     Universitaire | 50 (33,3) | 48 (32,0) | 98 (32,7) |
| bienetre_total, *M* (*ÉT*) | 17,01 (4,18) | 14,54 (4,39) | 15,77 (4,45) |

*Note.* Âge : 5 valeurs manquantes. Pourcentages calculés sur l'effectif de chaque colonne.

- Une colonne par groupe, et une colonne « Total » ; sans groupe, une seule colonne. Pas de colonne « Étendue » (elle reste dans le rapport).
- Les valeurs manquantes d'une variable sont dites dans la note, pas en ligne.
- Une catégorie de moins de 5 personnes garde son signe ⚠ dans l'outil, mais pas dans le tableau Word : la note le dit (« Moins de 5 personnes : Région : Ouest. »), et c'est à l'équipe de décider de la publier.
- **Pas de figure.**

## 3. Test t — comparer deux groupes

**Tableau 2**
*Bien-être selon le groupe*

| Variable | Intervention *M* | Intervention *ÉT* | Contrôle *M* | Contrôle *ÉT* | *t*(297,29) | *p* | *d* | IC 95 % de *d* |
|---|---|---|---|---|---|---|---|---|
| bienetre_total | 17,01 | 4,18 | 14,54 | 4,39 | 5,00 | < ,001 | 0,58 | [0,35 ; 0,81] |

*Note.* Intervention : *n* = 150 ; contrôle : *n* = 150. Test *t* de Welch (variances inégales permises). *d* de Cohen calculé avec l'écart-type combiné.

- Dans Word, « Intervention » et « Contrôle » sont des en-têtes qui regroupent leurs colonnes *M* et *ÉT* (un filet court sous chacun).
- Mann-Whitney : colonnes *Mdn* par groupe, *U*, *p*, *r* (bisériale de rang), sans IC.

**Figure 1**
*Bien-être moyen selon le groupe*

Barres verticales grises, une par groupe (axe horizontal : le groupe ; axe vertical : la variable, de 0 au maximum de l'échelle quand il est connu), avec les **barres d'erreur de l'IC 95 % de la moyenne**.

*Note.* Les barres d'erreur représentent l'intervalle de confiance à 95 % de la moyenne. Intervention : *n* = 150 ; contrôle : *n* = 150.

## 4. ANOVA — comparer plusieurs groupes

**Tableau 3**
*Stress selon le plus haut niveau d'études*

| Niveau d'études | *n* | *M* | *ÉT* | IC 95 % de *M* |
|---|---|---|---|---|
| Secondaire | 103 | 22,28 | 4,90 | [21,32 ; 23,24] |
| Collégial | 97 | 19,00 | 5,69 | [17,85 ; 20,15] |
| Universitaire | 96 | 15,89 | 5,60 | [14,75 ; 17,02] |

*Note.* *F*(2, 293) = 34,88, *p* < ,001, η² = ,19, ω² = ,19.

**Tableau 4** (avec l'option Tukey)
*Comparaisons deux à deux du stress (Tukey)*

| Comparaison | Différence | IC 95 % | *p* |
|---|---|---|---|
| Collégial − Secondaire | −3,28 | [−5,08 ; −1,48] | < ,001 |
| Universitaire − Secondaire | −6,39 | [−8,20 ; −4,59] | < ,001 |
| Universitaire − Collégial | −3,11 | [−4,94 ; −1,28] | < ,001 |

*Note.* Différences de moyennes ; intervalles et *p* ajustés par la méthode de Tukey.

- Kruskal-Wallis : colonnes *n*, *Mdn*, et la note *H*(2) = …, *p*, ε².

**Figure 2**
*Stress moyen selon le plus haut niveau d'études*

Comme la figure du test *t* : une barre par groupe, dans l'ordre des codes, avec l'IC 95 % de la moyenne.

## 5. Khi-carré — associer deux variables catégorielles

**Tableau 5**
*Télétravail selon le secteur d'emploi*

| Télétravail | Public *n* (%) | Privé *n* (%) | Communautaire *n* (%) |
|---|---|---|---|
| Oui | 77 (67,0) | 62 (45,9) | 13 (26,0) |
| Non | 38 (33,0) | 73 (54,1) | 37 (74,0) |
| Total | 115 | 135 | 50 |

*Note.* Pourcentages calculés dans chaque colonne. χ²(2, *N* = 300) = 25,59, *p* < ,001, *V* de Cramér = ,29.

- Les pourcentages vont dans le sens de la lecture : par colonne (la variable en colonnes est celle qui « explique ») ; la note le dit. Test exact de Fisher : *p* exact dans la note.

**Figure 3**
*Pourcentage de télétravail selon le secteur d'emploi*

Barres groupées : un groupe de barres par catégorie de la variable en colonnes (le secteur), une barre par catégorie de la variable en lignes (Oui, Non), en pourcentage de la colonne (axe vertical de 0 à 100 %) ; légende sous l'axe, gris clair et gris foncé.

*Note.* *N* = 300.

## 6. Corrélation — relier des variables continues

**Tableau 6**
*Statistiques descriptives et corrélations*

| Variable | *n* | *M* | *ÉT* | 1 | 2 | 3 |
|---|---|---|---|---|---|---|
| 1. Heures de travail par semaine | 300 | 38,22 | 5,82 | — | | |
| 2. Score de stress (0 à 40) | 296 | 19,13 | 5,99 | ,42 [,32 ; ,51] | — | |
| 3. Soutien des collègues (0 à 10) | 300 | 5,98 | 1,87 | ,01 [−,10 ; ,12] | −,02 [−,13 ; ,10] | — |

*Note.* Corrélations de Pearson ; entre crochets, l'IC 95 %. Chaque corrélation est calculée sur les personnes qui ont les deux valeurs (*n* de 296 à 300). Les *p* : ligne 2, *p* < ,001 ; ligne 3, *p* = ,851 et *p* = ,745.

- Matrice en triangle inférieur, *r* sans zéro initial. Les *p* exacts vont dans la note (une matrice n'a pas de place pour eux sans astérisques, D-086) ; avec deux variables seulement, une ligne : *n*, *r*, IC 95 %, *p*.
- Spearman : ρ au lieu de *r*, sans IC.

**Figure 4** (deux variables seulement)
*Stress selon les heures de travail*

Nuage de points (cercles gris pleins, petits, un peu transparents quand ils se superposent), avec la droite de régression en noir ; axes : les deux variables, avec leur libellé.

*Note.* *N* = 296. *r* = ,42, IC 95 % [,32 ; ,51].

- Plus de deux variables : pas de figure (une matrice de nuages de points sortira peut-être plus tard, comme un format de plus).

## 7. Régression linéaire — prédire une variable continue

**Tableau 7**
*Régression de la satisfaction au travail sur le soutien et la charge de travail*

| Prédicteur | *b* | IC 95 % de *b* | *ET* | β | *t* | *p* |
|---|---|---|---|---|---|---|
| Constante | 1,88 | [1,34 ; 2,42] | 0,28 | | 6,82 | < ,001 |
| Soutien des collègues (0 à 10) | 0,51 | [0,44 ; 0,58] | 0,04 | ,60 | 14,24 | < ,001 |
| Charge de travail perçue (0 à 10) | −0,29 | [−0,36 ; −0,22] | 0,03 | −,36 | −8,59 | < ,001 |

*Note.* *N* = 300. *R*² = ,47, *R*² ajusté = ,47, *F*(2, 297) = 134,30, *p* < ,001. *b* : coefficient non standardisé ; β : coefficient standardisé ; *ET* : erreur type.

- Un prédicteur nominal : une ligne par modalité, la référence dite dans la note (« Référence : Public »).

**Figure 5**
*Coefficients standardisés de la régression de la satisfaction au travail*

Un point par prédicteur (axe horizontal : β, avec une ligne verticale pointillée à 0 ; axe vertical : les prédicteurs, dans l'ordre du tableau), avec la barre horizontale de son IC 95 %.

*Note.* Les barres d'erreur représentent l'IC 95 % de β. *N* = 300.

## 8. Le fichier Word

- Un fichier par analyse, `<projet>-analyse-<n>.docx`, à côté du rapport (même numéro) : les tableaux, puis les figures, chacun avec son numéro, son titre et sa note ; à la fin, la phrase de résultat et l'empreinte du codebook, en petit, pour mémoire.
- Format de page : lettre, marges de 2,54 cm, police du document par défaut ; les tableaux tiennent dans la largeur, sinon ils passent en page paysage.
- À côté, `<projet>-analyse-<n>-graphiques.xlsx` : une feuille par figure, avec ses données et le graphique Excel natif (barres d'erreur comprises).
- Les numéros commencent à 1 dans chaque fichier ; l'équipe les change dans la page (ou dans Word) pour suivre son document.

## 9. Points à valider

1. Le Tableau 1 avec une colonne « Total », sans colonne « Étendue ».
2. Le test *t* en une ligne avec en-têtes regroupés (et non un tableau de groupes en lignes).
3. Les barres d'erreur : **IC 95 % de la moyenne** (et non l'erreur type).
4. Les *p* d'une matrice de corrélations dans la note, faute d'astérisques.
5. Des **barres** pour les moyennes (plutôt que des points) : plus courantes en psychologie, et faciles à modifier dans Excel.
6. La figure de régression : les β et leur IC (plutôt que les valeurs prédites).
