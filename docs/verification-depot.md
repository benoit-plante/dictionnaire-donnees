# Fiche : le recodage, le vérificateur des chiffres et le paquet de reproduction (v0.15)

> Statut : **validée par l'auteur le 2026-10-18 (étape 1 de la v0.15)**, avec les recommandations du § 4 : une classe « signe inversé » pour *t*, *z* et *d* ; les pourcentages lus seulement s'il reste du temps à l'étape 4 ; pas de recodage d'un recodage ; un encadré sur la page « Variables » et la liste sur la page « Groupes » ; `README.md` toujours, dans la langue choisie. Plan : [`plan-v0.15.md`](plan-v0.15.md), décisions D-117 à D-120. Les exemples viennent de la base fictive `etude-suivi` (240 participants, graine fixe) et d'une ébauche d'article que l'outil a produite sur elle avec cinq analyses au carnet (A1 test apparié, A2 régression logistique, A3 corrélation, A4 test *t*, A5 ANOVA à mesures répétées). Les questions à trancher sont rassemblées au § 4.

---

## 1. Le recodage

### 1.1 Ce qu'il fait

Une **variable dérivée**, tirée d'une seule variable source, décrite comme une décision du projet : la règle est gardée, jamais la colonne. La nouvelle colonne est calculée en mémoire à chaque lecture, comme un score.

| Sorte | Source permise | Exemple |
|---|---|---|
| **Regrouper des modalités** | une variable nominale ou ordinale, codée ou écrite en texte (« oui ») | `sexe` (Femme, Homme, Autre identité) → `sexe_2` (Femme ; Homme ou autre identité) |
| **Découper en classes** | une variable d'échelle (numérique) ou un score | `age` → `age_classe` (moins de 30 ; 30 à moins de 45 ; 45 et plus) |

Jamais un identifiant, un texte libre ou une date (même règle que les exclusions, D-093, et les sous-groupes, D-113) ; jamais une liste de personnes.

### 1.2 Ce que garde le projet

Une nouvelle section `recodes` du projet (format 0.7.0 ; un projet plus ancien s'ouvre tel quel) :

```json
{
  "recodes": {
    "next_id": 3,
    "rules": [
      {
        "id": "R1",
        "kind": "groups",
        "source": {"variable": "sexe"},
        "name": "sexe_2",
        "label": "Sexe, en deux groupes",
        "level": "nominal",
        "groups": [
          {"code": 1, "label": "Femme", "values": [1]},
          {"code": 2, "label": "Homme ou autre identité", "values": [2, 3]}
        ],
        "missing_values": [],
        "reason": "Trop peu de personnes d'une autre identité pour un groupe à part."
      },
      {
        "id": "R2",
        "kind": "classes",
        "source": {"variable": "age"},
        "name": "age_classe",
        "label": "Âge, en trois classes",
        "level": "ordinal",
        "cuts": [30, 45],
        "labels": ["moins de 30", "30 à moins de 45", "45 et plus"],
        "reason": "Classes d'âge du rapport de l'organisme."
      }
    ]
  }
}
```

- **Regrouper** : chaque groupe reçoit un code (1, 2…), une étiquette et la liste des valeurs sources qu'il réunit. Les valeurs sources peuvent être du texte (une catégorie écrite en toutes lettres dans un CSV, D-110). `missing_values` déclare des valeurs sources qui deviennent manquantes.
- **Découper** : des seuils croissants ; une classe va **de son seuil inclus au seuil suivant exclu** (« 30 à moins de 45 »). Les codes sont 1, 2, 3… dans l'ordre ; les étiquettes sont proposées ainsi par l'outil, et se changent.
- La **raison** est obligatoire, comme pour une règle d'exclusion. Un seuil n'exige pas de source : c'est une décision de l'équipe, pas une étendue théorique (règle 4 du `CLAUDE.md`, qui vise ce que l'IA proposerait).
- Le **nom** suit les règles des noms finaux (D-050) : unique dans le projet, pas un nom pris par une variable, un score ou un autre recodage.

### 1.3 Refus et contrôles, avant d'enregistrer

| Cas | Conduite |
|---|---|
| Une valeur source observée n'est dans aucun groupe ni dans `missing_values` | refus : « Valeurs sans groupe : 3 (Autre identité, 14 personnes). » |
| Une valeur dans deux groupes | refus |
| Seuils non croissants, ou un seul groupe ou une seule classe | refus |
| Une classe vide sur la base | avertissement, le recodage reste permis |
| Une nouvelle modalité de moins de 5 personnes | avertissement, comme ailleurs (D-006) |
| Source : identifiant, texte libre ou date | refus |
| Source déjà recodée (un recodage d'un recodage) | refus dans cette version ; on recode la source d'origine |

Avant d'enregistrer, la page montre l'effectif de chaque nouvelle modalité, calculé sur la base après les codes manquants (pas encore les exclusions) :

| R1 `sexe_2` | *n* | | R2 `age_classe` | *n* |
|---|---|---|---|---|
| Femme | 133 | | moins de 30 | 49 |
| Homme ou autre identité | 107 | | 30 à moins de 45 | 79 |
| | | | 45 et plus | 112 |

Les codes manquants de la source restent manquants ; une valeur hors des seuils n'existe pas (les classes couvrent tout, la première commence à −∞ et la dernière finit à +∞).

### 1.4 Où il s'applique

**L'ordre** : codes manquants, noms finaux, items inversés, scores, **recodages**, puis règles d'exclusion et sous-groupes. Une exclusion, un sous-groupe, une analyse ou une hypothèse peuvent donc porter sur une variable recodée, et une variable recodée peut venir d'un score.

| Endroit | Ce qui change |
|---|---|
| Analyses, carnet, plan | la variable recodée est proposée dans les listes selon son niveau ; un recodage changé après coup rend les analyses qui l'utilisent « changées, à confirmer » (D-089) ; modifier ou retirer un recodage dont dépend une hypothèse figée est un amendement |
| Script de préparation SPSS | voir ci-dessous ; exécuté après les scores, avant `ddict_exclusion` |
| Script de préparation R et script R maître | idem |
| Codebook (Excel, Markdown, `datapackage.json`) | une ligne par variable recodée, marquée « dérivée », avec sa source, sa règle en clair, ses étiquettes et sa raison |
| Méthode, paragraphe Analyses | « La variable sexe_2 a été tirée de sexe : Femme (1) ; Homme ou autre identité (2, 3). La variable age_classe a été tirée de age : moins de 30, 30 à moins de 45, 45 et plus. » |
| Copie documentée de la base (`ddict documenter`) | non : elle reste la base d'origine, documentée ; les recodages sont dans le script de préparation |

**SPSS** (le script de préparation) :

```
* R1 : Trop peu de personnes d'une autre identité pour un groupe à part.
RECODE sexe (1=1) (2, 3=2) (ELSE=SYSMIS) INTO sexe_2.
VARIABLE LABELS sexe_2 'Sexe, en deux groupes'.
VALUE LABELS sexe_2 1 'Femme' 2 'Homme ou autre identité'.
* R2 : Classes d'âge du rapport de l'organisme.
COMPUTE age_classe = $SYSMIS.
IF (NOT MISSING(age) AND age < 30) age_classe = 1.
IF (age >= 30 AND age < 45) age_classe = 2.
IF (age >= 45) age_classe = 3.
VARIABLE LABELS age_classe 'Âge, en trois classes'.
VALUE LABELS age_classe 1 'moins de 30' 2 '30 à moins de 45' 3 '45 et plus'.
```

**R** (R de base) :

```r
# R1 : Trop peu de personnes d'une autre identité pour un groupe à part.
donnees[["sexe_2"]] <- haven::labelled(c(1, 2, 2)[match(ddict_valeurs(donnees[["sexe"]]), c(1, 2, 3))], labels = c("Femme" = 1, "Homme ou autre identité" = 2), label = "Sexe, en deux groupes")
# R2 : Classes d'âge du rapport de l'organisme.
donnees[["age_classe"]] <- haven::labelled(findInterval(ddict_valeurs(donnees[["age"]]), c(30, 45)) + 1, labels = c("moins de 30" = 1, "30 à moins de 45" = 2, "45 et plus" = 3), label = "Âge, en trois classes")
```

`findInterval` garde les valeurs manquantes et met un seuil dans la classe qui commence par lui, comme l'outil.

### 1.5 La page et la commande

- **Page « Variables »**, pour une variable source : un encadré « Recoder cette variable » (regrouper ou découper selon son niveau), les groupes ou les seuils, le nom, l'étiquette, la raison, l'aperçu des effectifs, **Enregistrer le recodage**. La liste des recodages, avec **Modifier** et **Retirer**, sur la page « Groupes », à côté des scores.
- **Ligne de commande**, `ddict recoder` (en anglais `ddict recode`) :

```
ddict recoder lister etude-suivi.dd.json
ddict recoder regrouper etude-suivi.dd.json sexe --nom sexe_2 --groupe 1 Femme --groupe "2,3" "Homme ou autre identité" --raison "…"
ddict recoder decouper etude-suivi.dd.json age --nom age_classe --seuils 30 45 --raison "…"
ddict recoder retirer etude-suivi.dd.json R2
```

---

## 2. Le vérificateur des chiffres

### 2.1 Ce qu'il lit

- Un fichier `.docx` : le texte des **paragraphes** et des **cellules de tableau**, dans l'ordre du document. Pas les images, les figures, les zones de texte, les en-têtes et pieds de page, les notes de bas de page ni les commentaires : le rapport le dit en tête.
- Les statistiques au **style APA**, en français et en anglais (D-117) :

| Statistique | Formes reconnues (français / anglais) | Exemple de l'ébauche |
|---|---|---|
| *t* avec ddl | `t(227) = 8,18` / `t(227) = 8.18` ; ddl décimaux de Welch `t(140,08)` | A1 : *t*(227) = 8,18 |
| *F* avec ddl | `F(2, 404) = 28,93` ; ddl corrigés `F(1,72 ; 346,74)` / `F(1.72, 346.74)` | A5 |
| χ² avec ddl | `χ²(2) = 37,45`, aussi `X2(2)`, `chi2(2)`, `khi²(2)` | A2 |
| *r*, ρ | `r = −,38`, `r(238) = −,38`, `ρ = …` | A3 |
| *p* | `p = ,250`, `p < ,001`, `p < ,05`, `p = 0,25`, `p = .25` | A4 |
| *M*, *ÉT* / *SD* | `M = 19,27 (ÉT = 6,15)`, `M = 19.27, SD = 6.15` | A4 |
| *d*, *d*<sub>z</sub>, *g* | `d = −0,16`, `d_z = 0,54`, `dz = 0,54` | A1, A4 |
| η², η²p, ε², ω² | `η²p = ,13`, `η² partiel = ,13`, `partial η² = .13` | A5 |
| *b*, β, *z*, ET/SE | `b = −0,50, ET = 0,09`, `β = …`, `z = −5,36` | A2 (tableau) |
| RC / OR | `RC = 0,61`, `OR = 0.61` | A2 (tableau) |
| IC | `IC 95 % [2,28 ; 3,72]`, `95% CI [2.28, 3.72]` : la borne basse et la borne haute, rattachées à la statistique qui les précède | A1 |
| *R*², Δ*R*² | `R² = ,20`, `R² de Nagelkerke = ,20`, `Nagelkerke R² = .20` | A2 |
| *N*, *n* | `N = 240`, `(n = 228)`, `n = 164` | partout |
| ε (Greenhouse-Geisser), *W* de Mauchly, *U*, *V*, *H* | `ε = 0,86`, `W = 0,83`, `U = 4842,5`, `V = …`, `H(2) = …` | A5 |

- **Dans un tableau**, l'en-tête dit la statistique de chaque colonne (`M`, `ÉT`, `t(227)`, `p`, `RC`, `IC 95 % du RC`…), et les cellules donnent les valeurs ; une matrice de corrélations (colonnes `1`, `2`, `3`) donne des *r* avec leur intervalle entre crochets. La première colonne (la variable, le prédicteur) sert au rattachement (§ 2.3).
- **Les nombres qu'il ne prend jamais pour une statistique** : les numéros de tableau, de figure, d'hypothèse et d'analyse (« Tableau 2 », « H1 », « A3 »), les années et les dates, les étendues entre parenthèses d'un libellé (« (0 à 40) »), les pourcentages (dans cette version), les nombres de pages et de références.
- **Non reconnue** : une écriture APA incomplète ou ambiguë (« t = 8,18 » sans ddl hors d'une phrase rattachée, « la différence était de 3 », un nombre suivi d'un symbole inconnu). Elle est comptée et listée, jamais devinée.

Les deux marques décimales sont acceptées dans les deux langues (un manuscrit anglais rédigé par une équipe francophone en garde parfois). Le zéro initial (« 0,25 » ou « ,25 ») et le signe moins (« − » ou « - ») ne comptent pas comme des différences : ce sont des questions de style, que le vérificateur ne juge pas.

### 2.2 Les valeurs de référence (D-118)

Pour chaque analyse retenue du carnet, recalculée sur la base avec les décisions en vigueur :

- ses **statistiques** à pleine précision (celles que le carnet garde : `t`, `df`, `p`, `d`, `d_low`, `d_high`, `m1`, `sd1`…) ;
- chaque **nombre de ses tableaux, de sa phrase et de ses notes**, tels que l'outil les écrit (par exemple les *M* et *ÉT* de chaque variable d'une matrice de corrélations, qui ne sont pas dans les statistiques gardées) ;
- son **sous-groupe** et ses effectifs (`n_used`).

Et pour la Méthode : les effectifs du flux, la description de l'échantillon (*M*, *ÉT*, *n*, pourcentages), les alphas et leur intervalle.

Sans la base (fichier absent ou d'une autre empreinte), la référence est le dernier calcul confirmé du carnet ; le rapport commence par « Base introuvable : comparaison aux valeurs gardées dans le carnet, sans recalcul. » Une analyse « changée, à confirmer » est comparée à son nouveau calcul et marquée comme telle.

### 2.3 Rattacher une valeur à une analyse

1. **Les blocs.** Le texte est découpé en blocs : une phrase d'un paragraphe, ou une ligne d'un tableau (avec l'en-tête de ses colonnes). Une phrase se termine par un point suivi d'un espace et d'une majuscule, ou par la fin du paragraphe ; un point décimal anglais ne coupe jamais une phrase.
2. **L'ancre.** Dans un bloc, la statistique de test avec ses degrés de liberté (*t*(ddl), *F*(ddl, ddl), χ²(ddl), *r*(ddl), *H*(ddl)), ou un *U*, un *V*, un *z*, désigne l'analyse dont la même statistique concorde, ddl compris. Les autres valeurs du bloc sont comparées à **cette** analyse.
3. **La section.** Sans ancre (une ligne de tableau de moyennes, « *M* = 21,6 »), le bloc est rattaché à l'analyse de la section où il se trouve, quand l'ébauche de l'outil la nomme (« A1 — … », « H2 — … ») ; sinon, à l'analyse dont le tableau contient la même étiquette de ligne.
4. **Sinon, toutes les analyses.** Une valeur seule est cherchée parmi toutes les références. Trouvée dans une seule analyse : elle concorde avec elle. Trouvée dans plusieurs : elle concorde, et le rapport nomme les analyses possibles. Trouvée nulle part : **sans origine**.

Une ancre qui ne concorde avec aucune analyse, mais dont le type existe dans une seule analyse de la même section, est **différente** de celle-ci (« *t*(227) = 8,19 » sous « A1 — … ») ; sans section, elle est **sans origine**.

### 2.4 L'arrondi et les classes

Une valeur écrite *v* avec *k* décimales **concorde** avec la valeur calculée *e* si |*v* − *e*| ≤ 0,5 × 10<sup>−*k*</sup> (plus une marge de 10⁻⁹ pour les nombres représentés en machine). Ainsi *p* = ,2499 concorde avec « ,250 », « ,25 » et « ,2 » ; *t* = 8,1807 avec « 8,18 » mais pas « 8,19 » ; *ddl* = 140,08 avec « 140 ».

| Classe | Quand | Exemple (ébauche altérée) |
|---|---|---|
| **concorde** | la règle d'arrondi est respectée ; « *p* < ,001 » quand *p* calculé < ,001 ; « *p* < ,05 » quand *p* < ,05 | « *t*(140) = −1,16 » (A4) ; « χ²(2) = 37,5 » (A2) ; « *p* = ,25 » (A4) |
| **diffère** | la valeur est rattachée, mais hors de l'arrondi ; « *p* = ,000 » (le rapport propose « *p* < ,001 ») ; « *p* < ,05 » quand *p* ≥ ,05 | « *t*(227) = 8,19 » : attendu 8,18 (A1) ; « *M* = 19,72 » : attendu 19,27 (A4) ; « *F*(2, 404) = 31,02 » : attendu 28,93 (A5, ancienne version collée) |
| **signe inversé** | seulement le signe diffère, pour *t*, *z* et *d*, dont le signe dépend de l'ordre des groupes que l'auteur a pu inverser | « *d* = 0,16 » : calculé −0,16 (A4) |
| **sans origine** | aucune analyse du carnet ni la Méthode n'a cette valeur | « *t*(98) = 2,41, *p* = ,018 » |
| **non reconnue** | une écriture que le vérificateur ne sait pas lire sans deviner | « la différence était de 3 points » |

Une valeur rattachée à une analyse « changée, à confirmer » garde sa classe, avec la mention « analyse à confirmer » (c'est l'ancienne « périmée » de la feuille de route).

### 2.5 Ce qu'il produit

- **Le rapport** (`<manuscrit>-verification.md` et `.xlsx`, à côté du manuscrit) : en tête, le nombre de valeurs par classe, la base utilisée (recalcul ou carnet), ce qui n'a pas été lu ; puis une ligne par valeur, triée par emplacement :

| Emplacement | Statistique | Écrit | Attendu | Analyse | Classe |
|---|---|---|---|---|---|
| § 12, phrase 1 | *t* (227) | 8,19 | 8,18 | A1 | diffère |
| Tableau 4, ligne 1, col. *M* | *M* | 19,72 | 19,27 | A4 | diffère |
| § 15, phrase 1 | *d* | 0,16 | −0,16 | A4 | signe inversé |
| § 21, phrase 2 | *t* (98) | 2,41 | — | — | sans origine |

  Le rapport cite la statistique, jamais le texte qui l'entoure ; il ne contient aucune donnée individuelle.
- **La copie commentée** (`<manuscrit>-verifie.docx`) : le manuscrit tel quel, avec un commentaire Word sur chaque valeur qui ne concorde pas (« Diffère : l'outil calcule 8,18 (A1, *t*). »), auteur « dictionnaire-donnees ». Quand Word a coupé le nombre en plusieurs morceaux de mise en forme, le commentaire s'accroche au paragraphe. Les valeurs qui concordent ne reçoivent aucun commentaire. **Le manuscrit d'origine n'est jamais modifié.**
- **La page « Vérifier »** (après « Carnet ») : choisir le manuscrit (la fenêtre « Ouvrir »), **Vérifier**, le résumé par classe, le tableau des valeurs filtrable par classe, les deux fichiers à écrire à côté du manuscrit ou à télécharger. **En ligne de commande** : `ddict verifier etude-suivi.dd.json manuscrit.docx` (en anglais `ddict verify`), qui affiche le résumé et écrit les deux fichiers.

### 2.6 Le critère de l'étape 5, sur la base fictive

| Manuscrit | Attendu |
|---|---|
| L'ébauche d'article de l'outil, telle quelle, en français puis en anglais | toutes les valeurs reconnues « concorde » ; aucune « sans origine » ; les seules « non reconnues » sont listées et justifiées dans le test |
| La même, altérée par un script de test : un *t* changé d'un centième, un *M* aux chiffres permutés, un *d* sans son signe, un *F* d'une version précédente, une phrase inventée, un *p* écrit « ,000 », un *ddl* de Welch arrondi à l'entier | chaque altération trouvée et classée comme au § 2.4 ; le *ddl* arrondi concorde |
| Le texte d'une base sans rapport (une autre base fictive) | tout « sans origine » ou « non reconnue », aucun « concorde » |

---

## 3. Le paquet de reproduction

### 3.1 Contenu

`<projet>-depot.zip`, produit au moment de la demande (D-089), jamais à partir de fichiers anciens :

| Fichier | Contenu |
|---|---|
| `README.md` | le README de dépôt (§ 3.2), dans la langue choisie |
| `codebook/<projet>.xlsx`, `codebook/<projet>.md` | le codebook, export final |
| `codebook/<projet>-datapackage.json` | la description Frictionless (v0.8) |
| `plan/<projet>-preenregistrement.docx`, `.md` | si le plan existe ; le plan et ses amendements y sont |
| `analyses/<projet>-carnet.json` | le carnet : choix, empreintes, agrégats (D-088) |
| `scripts/<projet>.sps`, `scripts/<projet>-metadonnees.R` | le fichier de commandes (étiquettes, codes manquants, noms), en SPSS et en R |
| `scripts/<projet>-preparation.sps`, `.R` | items inversés, scores, recodages, exclusions |
| `scripts/<projet>-article.R` | le script R maître, qui exécute le fichier de commandes et le script de préparation |
| `EMPREINTES.txt` | chaque fichier du paquet avec son empreinte SHA-256, l'empreinte du codebook et celle de la base d'origine (une empreinte ne permet pas de retrouver la base) |

**Jamais** (D-119) : la base, le fichier projet (son profil contient des valeurs observées, des minimums et des maximums), le dossier des envois à l'IA, l'ébauche d'article, une base synthétique.

### 3.2 Le README de dépôt

Rédigé par gabarit, en français ou en anglais ; ce que l'outil ne sait pas reste un trou « [à compléter : …] » :

> **[à compléter : titre de l'étude]** — matériel de reproduction
>
> Ce dépôt contient le dictionnaire de données, le plan d'analyse et les scripts qui refont les analyses de l'article **[à compléter : référence de l'article]**. Il ne contient pas les données : **[à compléter : où et à quelles conditions les obtenir]**.
>
> **Contenu.** `codebook/` : le dictionnaire des 13 variables (Excel, Markdown, `datapackage.json`). `plan/` : le préenregistrement, écrit avant l'analyse le 2026-10-18 selon l'équipe, et ses amendements. `analyses/` : le carnet des 5 analyses. `scripts/` : les fichiers de commandes SPSS et R, le script de préparation et le script R maître.
>
> **Refaire les analyses.** Placez la base `etude-suivi.sav` dans le dossier `scripts/`. Dans R, avec le paquet haven : `source("etude-suivi-article.R", encoding = "UTF-8")`. Le script exécute le fichier de commandes, le script de préparation, puis les 5 analyses ; chaque résultat est rangé sous son identifiant (`resultats$A1`). Dans SPSS ou PSPP, exécutez `etude-suivi.sps` puis `etude-suivi-preparation.sps`.
>
> **Versions.** Produit par dictionnaire-donnees 0.15.0 ; empreinte du codebook `ef32215fd68b` ; empreintes des fichiers dans `EMPREINTES.txt`.
>
> **Licence** : [à compléter]. **Auteurs** : [à compléter]. **Contact** : [à compléter].

Le README ne cite **aucune statistique** : seulement des nombres de variables, d'analyses, des dates et des versions.

### 3.3 La page et la commande

Sur la page « Carnet », sous l'ébauche d'article : **Préparer le paquet de reproduction**, qui écrit `<projet>-depot.zip` à côté du projet et affiche la liste de ses fichiers. Le bouton est grisé tant qu'une analyse est « à confirmer », comme l'ébauche. En ligne de commande : `ddict deposer etude-suivi.dd.json` (en anglais `ddict deposit`).

### 3.4 Le critère de l'étape 6

Le paquet décompressé dans un dossier vide, la base fictive placée dans `scripts/` : le script R maître s'exécute sans erreur et redonne les chiffres du carnet à 10⁻⁶ près. Un test à chaînes témoins (une base fictive dont chaque valeur de texte et chaque nombre peu probable sont repérables) vérifie qu'aucune valeur de la base n'est dans le paquet.

---

## 4. Questions à trancher

1. **Le signe inversé** (§ 2.4) : une classe à part pour *t*, *z* et *d*, ou simplement « diffère » ? Recommandation : la classe à part, puisque le signe dépend de l'ordre des groupes, que l'article publié d'AMATUS écrit sans signe.
2. **Les pourcentages** : hors du vérificateur dans cette version (ils sont surtout dans la Méthode et le Tableau 1, souvent recalculés à la main) ? Recommandation : les lire à l'étape 4 seulement s'il reste du temps ; sinon, ils sont dits « non lus ».
3. **Un recodage d'un recodage** (§ 1.3) : refusé dans cette version ? Recommandation : oui ; on recode la source d'origine.
4. **Où recoder dans l'interface** : un encadré de la page « Variables » pour créer, la liste sur la page « Groupes » à côté des scores ? Ou une page « Recodages » à part ? Recommandation : l'encadré et la liste, sans nouvelle page.
5. **Le nom du paquet** : `LISEZMOI.md` en français, `README.md` en anglais, ou `README.md` toujours (le nom que les dépôts reconnaissent) ? Recommandation : `README.md` toujours, son contenu dans la langue choisie.
