# Essai : le plan, le préenregistrement et l'article sur une base ouverte (v0.13, étape 7)

**Date :** 2026-10-18

**But :** refaire, avec l'outil, les analyses d'un article publié à partir de sa base ouverte : écrire le plan, le figer, l'amender, produire le préenregistrement et l'ébauche d'article, puis comparer chiffres et texte à l'article publié. Contrairement aux essais sur une base privée, la base et l'article sont publics (CC BY 4.0) : ce compte rendu cite leurs chiffres publiés. Aucune donnée n'entre dans le dépôt ; le travail s'est fait dans un dossier temporaire, supprimé à la fin.

## 1. La base et l'article

- **La base :** AMATUS (Cipora et al., 2024), sur OSF (osf.io/gszpb), CC BY 4.0 : 1 106 personnes, étudiants allemands et enseignants du primaire allemands et belges ; 187 variables, dont l'anxiété mathématique (AMAS) et ses sous-échelles, et, pour les enseignants, le plaisir et la facilité d'enseigner les maths (codes 1 à 5, et −1 pour « pas encore enseigné »). Un CSV séparé par des points-virgules et un codebook Excel.
- **L'article :** Artemenko et al. (2021), en accès libre, CC BY 4.0. Il compare l'anxiété mathématique des enseignantes à celle des étudiantes, puis selon la spécialisation et l'expérience, et la relie aux attitudes envers l'enseignement des maths. Il annonce ses attentes (p. 278), sans plan déposé.

Les auteurs n'analysent que les femmes. L'outil ne filtre pas les personnes : comme le ferait une équipe dans R, un fichier dérivé a été préparé hors de l'outil, les femmes seulement (820), avec une variable `enseignante` (« oui », « non ») tirée de l'échantillon.

## 2. Le parcours

Tout passe par la ligne de commande. Au premier passage, deux décisions n'avaient pas de commande et ont été écrites par les fonctions des pages : les niveaux de mesure (page Base) et le code −1 déclaré manquant (page Variables) ; au second passage (§ 8), `ddict niveaux` et `ddict codes` les prennent.

1. `ddict profiler` sur le CSV : 188 variables, 820 lignes, en 2,8 secondes ; le code −1 des six questions d'attitude est signalé comme code manquant probable ; 17 variables de texte, dont `enseignante`, reçoivent le niveau « nominal » proposé.
2. Le plan, avec `ddict plan ajouter` : H1, les enseignantes plus anxieuses que les étudiantes (test t de Student, unilatéral, comme l'article sans le sens) ; H2, les enseignantes en poste moins anxieuses que celles en formation ; H3 et H4, famille F1, l'anxiété liée négativement au plaisir puis à la facilité d'enseigner les maths ; H5 et H6, exploratoires, deux régressions du plaisir d'enseigner.
3. `ddict plan regles` : α = ,05, Holm, données secondaires, état « après une analyse » (les résultats publiés étaient connus), puis `ddict plan figer`.
4. Un amendement de H2 (Mann-Whitney au lieu de Welch), refusé sans raison, accepté avec elle.
5. `ddict plan preenregistrement` et `ddict article`, en français et en anglais ; le script R maître lancé dans R 4.6.1.

## 3. Ce que l'essai a trouvé, et corrigé

Le premier passage s'est arrêté net : aucune hypothèse ne pouvait s'écrire.

| Défaut | Effet | Correction |
|---|---|---|
| Une catégorie écrite en texte (« oui », « non ») recevait le niveau « nominal », puis était refusée dans toute analyse | H1, H2 et les régressions impossibles | elle entre une fois nominale ; le texte libre reste exclu par sa classe de confidentialité (D-110) |
| Une case de texte vide comptait comme une catégorie dans l'analyse, pas dans le profil | « teacher_experience : 3 modalités » pour deux | la case vide est manquante, comme dans le profil |
| Le script R lisait tout CSV avec la virgule pour séparateur | le script R maître s'arrêtait à la lecture | lecture selon la détection de l'outil (séparateur, décimale, encodage, cases vides, colonnes de texte) |
| La liste des analyses de l'article écrivait « Dependent variable : … » en anglais | typographie française en anglais | la ponctuation suit la langue |

Les deux premiers défauts n'apparaissaient sur aucune base fictive : leurs groupes sont des codes numériques étiquetés. `tests/test_text_categories.py` les couvre désormais, sur une base fictive dérivée, séparée par des points-virgules, aux catégories en texte avec accents et traits d'union ; le script R y donne les mêmes valeurs que l'outil.

## 4. Les chiffres, face à l'article publié

| Résultat | Article publié | Outil | R (script maître) |
|---|---|---|---|
| H1 : anxiété, enseignantes et étudiantes | *t*(818) = 2,28, *p* = ,023 (bilatéral) | *t*(818) = −2,28, *p* = ,011 (unilatéral), *d* = −0,18 | mêmes *t*, ddl et *p* |
| H3 : anxiété et plaisir d'enseigner | *r*(180) = −,470, *p* < ,001 | *r*(180) = −,47, *p* < ,001 ; *p* corrigé (Holm) < ,001 | même *r*, même *n* |
| H4 : anxiété et facilité d'enseigner | *r*(179) = −,479, *p* < ,001 | *r*(179) = −,48, *p* < ,001 ; *p* corrigé (Holm) < ,001 | même *r*, même *n* |
| H2 : en poste et en formation | ANOVA, effet de l'expérience *F*(1, 219) = 0,06, *p* = ,812 | *U* = 4842,5, *p* = ,456 (unilatéral), *r* = −,01 | mêmes *U* et *p* |

| Vérification | Résultat |
|---|---|
| *p* corrigés de Holm (famille F1) égaux à ceux de `p.adjust` dans R | oui, écart relatif inférieur à 10⁻¹³ |
| Le code −1 déclaré manquant change la corrélation | oui : *r*(221) = −,30 avec −1 compté comme une valeur, *r*(180) = −,47 une fois manquant |
| Script R maître de l'article | sans erreur, en 0,3 seconde |
| Signe de *t* et de *d* | négatif : l'outil soustrait le second groupe du premier, dans l'ordre des codes (« non » avant « oui ») ; le texte dit bien que la moyenne est plus élevée chez « oui » |

Les écarts avec l'article tiennent aux choix d'analyse, pas au calcul : un test unilatéral au lieu de bilatéral (H1), et, pour H2, un test de rangs sur les enseignantes au lieu d'une ANOVA à deux facteurs.

## 5. Les documents

| Vérification | Résultat |
|---|---|
| Préenregistrement, gabarit | van den Akker et al. (2021), 25 questions, puisque les données sont secondaires |
| Préenregistrement, nombres tirés des données | aucun (seuls le nombre de variables du codebook, les dates, α et les sources) |
| L'outil dit que l'étude a été préenregistrée | jamais |
| Article, intertitres | Résumé, titre, Méthode (Participants, Analyses, Plan d'analyse), Résultats (H1 à H4, puis « Analyses exploratoires » : H5, H6), Discussion, Références |
| Article, trous | 17, en français comme en anglais : titre, auteurs, résumé, mots-clés, contexte, lieu du préenregistrement, interprétation de chaque hypothèse, rappel du but, limites, conclusion, références à vérifier |
| Mots qui jugent (« soutenue », « significatif », « supported »…) | aucun, en français ni en anglais |
| Paragraphe du plan | origine et état déclarés « selon l'équipe », date du gel, quatre hypothèses confirmatoires et deux exploratoires, Holm dans F1, tests unilatéraux de H1 et H2, l'amendement et sa raison |
| Références | Holm (1979) seulement : le codebook n'avait aucune source |
| Durées | chaque commande en moins d'une seconde ; l'article en 0,9 seconde |

## 6. Ce que l'outil ne fait pas, et que l'article publié fait

- **Un sous-groupe** : les auteurs n'analysent que les femmes ; l'outil analyse toute la base, d'où le fichier dérivé.
- **L'ANOVA à deux facteurs** (spécialisation × expérience) : le catalogue n'a qu'un facteur.
- **La régression ordinale** du plaisir et de la facilité d'enseigner (des items de 1 à 5) : l'outil fait une régression linéaire, ce que H5 et H6 rendent visible.
- **Les facteurs de Bayes**, la **corrélation polychorique** et les **centiles des normes** (Tableau 4).
- **Les exclusions faites en amont** (Tableau 1 de l'article) : la base publiée est déjà nettoyée ; l'outil dit « 820 personnes ont répondu », sans le savoir.

## 7. Ce qui restait à reprendre

Trois points notés au premier passage ont été corrigés, puis l'essai refait (§ 8) :

- les niveaux de mesure et les codes manquants ne se décidaient que sur les pages : `ddict niveaux` (`lister`, `accepter`, `rejeter`, `fixer`) et `ddict codes` (`lister`, `manquant`, `valeur`, `annuler`) le font désormais, avec les fonctions des pages ;
- dans le tableau d'une corrélation, la ligne de chaque variable donnait son *n* propre (820 pour l'anxiété) à côté de *N* = 182 : le *n*, la moyenne et l'écart-type de chaque variable portent maintenant sur les personnes qui entrent dans une corrélation du tableau ;
- la Méthode écrivait « Les codes -1 (preference_teaching_mathematics) ; -1 (ease_teaching_mathematics) » : un même code se dit une fois, « Le code -1 (preference_teaching_mathematics, ease_teaching_mathematics) », dans la Méthode comme dans le préenregistrement.

Un quatrième point, une analyse remplacée par un amendement qui serait restée « Retenue pour le document », venait d'une lecture trop rapide : l'interrupteur porte ce libellé qu'il soit ouvert ou fermé, et l'analyse était bien écartée.

Restent, sans correction :

- Sans étiquettes, les variables gardent leur nom de fichier dans le texte (« score_AMAS_total ») : c'est le travail du dictionnaire, que l'essai a sauté.
- Un CSV de plateforme à deux lignes d'en-tête (SurveyMonkey) n'est pas encore lu par le script R comme par l'outil.

## 8. Le second passage

Le même parcours, refait sur une nouvelle copie de la base après les corrections, cette fois entièrement en ligne de commande :

| Vérification | Résultat |
|---|---|
| `ddict niveaux accepter` (5 variables) et `ddict niveaux fixer` (2 variables, échelle) | acceptés, en 0,1 seconde chacun |
| `ddict codes manquant -1` sur les deux questions d'attitude | accepté ; `ddict codes manquant 1` refusé (« 1 n'est pas un code suspect de cette variable ») |
| La corrélation avant et après le code −1 | *r*(221) = −,30, puis *r*(180) = −,47, comme au premier passage |
| Plan, gel, amendement, préenregistrement, article | les mêmes refus, les mêmes six hypothèses, les mêmes chiffres |
| Tableau de H3 | *n* = 182 sur les deux lignes, comme *N* dans la note |
| Méthode et préenregistrement | « Le code -1 (preference_teaching_mathematics, ease_teaching_mathematics) a été traité » (« sera traité ») |
| Préenregistrement, nombres tirés des données ; mots qui jugent | aucun ; aucun |
| Script R maître | sans erreur, en 0,3 seconde ; mêmes *t*, *r*, *U* et *p* ; *p* de Holm égaux à `p.adjust` |

## Ce que montre l'essai

1. **Les chiffres de l'outil sont ceux de l'article publié**, et ceux de R, dès que la base est lue et décrite comme l'ont fait les auteurs (femmes seulement, −1 manquant).
2. **Une vraie base CSV a montré ce que les bases fictives cachaient** : des catégories en texte et un séparateur point-virgule, maintenant pris en charge et testés.
3. **Le plan et l'article disent ce qui a été fait, rien de plus** : l'état des données déclaré par l'équipe, l'amendement et sa raison, aucun jugement sur les hypothèses, et des trous pour tout ce qui revient aux auteurs.

## Références

Artemenko, C., Masson, N., Georges, C., Nuerk, H.-C., & Cipora, K. (2021). Not all elementary school teachers are scared of math. *Journal of Numerical Cognition*, *7*(3), 275–294. https://doi.org/10.5964/jnc.6063

Cipora, K., Lunardon, M., Masson, N., Georges, C., Nuerk, H.-C., & Artemenko, C. (2024). The AMATUS dataset: Arithmetic performance, mathematics anxiety and attitudes in primary school teachers and university students. *Journal of Open Psychology Data*, *12*(1), Article 10. https://doi.org/10.5334/jopd.115
