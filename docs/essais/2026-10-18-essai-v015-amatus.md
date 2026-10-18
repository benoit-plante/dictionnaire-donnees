# Essai : le recodage, le vérificateur et le paquet sur la base AMATUS (v0.15, étape 7)

**Date :** 2026-10-18

**But :** refaire l'essai des v0.13 et v0.14 sur la base ouverte AMATUS (Cipora et al., 2024) et son article publié (Artemenko et al., 2021), tous deux CC BY 4.0, avec ce que la v0.15 ajoute : la variable `enseignante` recodée dans l'outil, sans aucun fichier dérivé ; le vérificateur des chiffres, passé sur l'ébauche de l'outil puis sur le texte de l'article publié ; le paquet de reproduction. Ce compte rendu cite les chiffres publiés. La base et l'article ont été téléchargés dans un dossier temporaire, supprimé à la fin ; rien n'entre dans le dépôt.

## 1. Le parcours

La base publiée telle quelle (1 106 personnes, femmes et hommes, CSV séparé par des points-virgules). Tout passe par la ligne de commande, chaque commande en 1,1 seconde au plus.

1. `ddict profiler`, `ddict niveaux`, `ddict codes manquant -1` comme en v0.14.
2. **Le recodage**, nouveau : `ddict recoder regrouper amatus.dd.json sample --nom enseignante --groupe german_students non --groupe "german_teachers,belgian_teachers" oui --raison "…"`. L'outil affiche les effectifs avant d'enregistrer : non, 848 ; oui, 258. Les deux essais précédents devaient préparer cette variable hors de l'outil.
3. Le plan H1 à H7, avec les sous-groupes `sex eq f` et, pour H5, `enseignante eq oui`, par l'étiquette du recodage ; règles, gel, amendement de H2 (Mann-Whitney).
4. `ddict plan preenregistrement`, `ddict article` en français et en anglais, le script R maître dans R 4.6.1.
5. `ddict verifier` sur les deux ébauches, puis sur le texte de l'article publié ; `ddict deposer`.

## 2. Les chiffres, sans fichier dérivé

Les mêmes que les essais des v0.13 et v0.14, cette fois depuis la base publiée seule.

| Résultat | Article publié | Outil |
|---|---|---|
| H1 : anxiété, enseignantes et étudiantes (femmes) | *t*(818) = 2,28, *p* = ,023 | *t*(818) = −2,28, *p* = ,011 (unilatéral), *d* = −0,18 |
| H3, H4 : anxiété et plaisir, facilité d'enseigner | *r*(180) = −,470 ; *r*(179) = −,479 | *r*(180) = −,47 ; *r*(179) = −,48 |
| H5 : enseignantes et enseignants | *t*(256) = 4,16, *d* = 0,76 | *t*(256) = 4,16, *d* = 0,76 |
| H6 (logistique), H7 (partielle) | — | RC = 0,92, χ²(1) = 19,43 ; *r* partiel(179) = −,41 |

Le script R maître, avec le recodage dans son script de préparation, s'exécute en 0,37 seconde : sur 96 statistiques communes, les mêmes valeurs que l'outil. Deux exceptions attendues : l'intervalle de la différence du test unilatéral de H1, ouvert d'un côté dans R et bilatéral dans l'outil (il n'est pas comparé dans les tests) ; les *p* de Wald de la logistique, de l'ordre de 10⁻⁶, dont l'écart relatif atteint 10⁻⁵ (écart absolu inférieur à 10⁻¹⁰, la convergence de `glm`).

## 3. Ce que l'essai a trouvé, et corrigé

| Défaut | Effet | Correction |
|---|---|---|
| Un sous-groupe sur une variable recodée, donné par son étiquette, était refusé | « --sous-groupe enseignante eq oui » : « enseignante prend des nombres ou ses étiquettes » ; H5 impossible | les étiquettes du recodage sont reconnues |
| La Méthode écrivait le code d'une variable recodée | « L'analyse A5 porte sur un sous-groupe : enseignante = 2 » | « enseignante = oui » |
| Le lecteur ne connaissait pas « p corrigé (Holm) », « Holm-adjusted p », « r partiel », « Partial r » | 5 « non reconnues » dans l'ébauche de l'outil | ces écritures sont lues, dans le texte et les en-têtes de tableau |
| Ni « ηp2 » (un exposant aplati par le PDF) ni « α » | non reconnues dans l'article publié | lues |
| Sans intertitre « A1 — … », un *t* au signe inversé ne désignait aucune analyse | « t(818) = 2.28 » : « sans origine » | une statistique avec les mêmes degrés de liberté dans une seule analyse la désigne : « signe inversé » |
| La Discussion, qui répète les chiffres, passait avant l'analyse ; un seuil de la Méthode servait de référence | « r(180) = −.470 » rattaché à la Discussion ; « p < .001 » rattaché au seuil de règle | les sections d'analyse et d'hypothèse passent d'abord ; un seuil n'est jamais une référence |
| Une phrase de deux analyses était rattachée en bloc à une seule ; les compagnons d'un test inconnu concordaient ailleurs par hasard | *r*(179) de H4 comparé à H3 ; le « p < .001 » d'une ANOVA à deux facteurs « concorde » | chaque valeur suit le test qui la précède ; à côté d'un test sans origine, une valeur est sans origine |

Chacun a désormais son test (`tests/test_recode.py`, `test_manuscript.py`, `test_verify.py`).

## 4. Le vérificateur

| Manuscrit | Valeurs lues | Résultat |
|---|---|---|
| Ébauche de l'outil, en français | 179 | toutes concordent |
| Ébauche de l'outil, en anglais | 179 | toutes concordent |
| Texte de l'article publié, copié du PDF dans un Word | 141 | 12 concordent, 2 signes inversés, 1 diffère, 86 sans origine, 40 non reconnues |

Sur l'article publié, le rapport dit exactement ce qu'un lecteur attentif verrait :

- **H5 concorde entièrement** : *t*(256) = 4.16, *p* < .001, *d* = 0.76 et les deux moyennes avec leur écart-type ;
- **H3 et H4 concordent**, chacune avec sa propre analyse, dans la même phrase ;
- **H1** : *t*(818) = 2.28 et *d* = 0.18, **signe inversé** (l'outil soustrait le second groupe du premier, l'article l'inverse) ; *p* = .023 **diffère** (l'outil écrit ,011 : l'article fait un test bilatéral, le plan un test unilatéral) ;
- **sans origine** : ce que l'outil ne calcule pas, l'ANOVA à deux facteurs (*F*(1, 219)), les tests sur d'autres sous-échantillons, les statistiques descriptives des Participants, des intervalles de crédibilité ;
- **non reconnues** : les facteurs de Bayes (BF₁₀, BF₀₁), les étendues (« Range = 18 »), la fidélité test-retest (« rtt = .85 »).

La copie commentée, ouverte dans Word et dans LibreOffice, porte un commentaire sur chaque valeur qui ne concorde pas ; le manuscrit n'est pas modifié.

## 5. Le paquet de reproduction

`amatus-depot.zip` : README, empreintes, codebook (Excel, Markdown, `datapackage.json`), préenregistrement, carnet, fichiers de commandes SPSS et R, scripts de préparation (avec le recodage), script R maître ; 13 fichiers. Aucune base (ni CSV ni `.sav`), aucun fichier projet. Le codebook dit des deux identifiants « Variable sensible : aucune statistique sur ses valeurs » : aucune valeur n'y figure.

## 6. Ce que l'outil ne fait toujours pas

- L'**ANOVA à deux facteurs**, la **régression ordinale**, les **facteurs de Bayes** et la **corrélation polychorique** de l'article.
- Le vérificateur ne lit ni les **pourcentages**, ni les **figures**, ni les **notes de bas de page** ; un article publié en PDF doit d'abord être copié dans un Word.
