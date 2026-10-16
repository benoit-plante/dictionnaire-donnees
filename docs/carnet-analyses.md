# Le carnet d'analyses : la fiche

> Statut : **validé par l'auteur le 2026-10-16** (v0.11, étape 1), avec les six points du § 8. Plan : [`plan-v0.11.md`](plan-v0.11.md) ; décisions D-087 à D-092. Chiffres : base fictive des analyses (`etude-analyses.sav`, échelle de bien-être cotée comme le dit le corrigé), et base fictive du sommeil pour le scénario d'une décision changée après coup (§ 6).

Ce document fixe le format du carnet, ce qu'il garde, comment il se recalcule, comment il numérote et comment il nomme ses fichiers. Le code des étapes 2 à 6 le suivra.

## 1. Le fichier

`etude-analyses-carnet.json`, à côté de `etude-analyses.dd.json` (D-091). JSON indenté de 2, clés dans l'ordre ci-dessous, UTF-8, fins de ligne LF, écrit dans un fichier temporaire puis remplacé d'un coup (comme le projet).

```json
{
  "carnet_version": "1.0.0",
  "project": {"file": "etude-analyses.dd.json", "source_sha256": "1262cc40…"},
  "next_id": 6,
  "first_table": 1,
  "first_figure": 1,
  "entries": [ … ]
}
```

- `carnet_version` : la version du format du carnet, distincte de celle du projet (0.3.0) ; un carnet d'une version majeure différente ou plus récente que l'outil est refusé, avec sa raison ; un carnet plus ancien est converti à la lecture.
- `project` : le nom du fichier projet et l'empreinte de la base. Un carnet posé à côté d'un autre projet, ou d'une base réexportée, est lu mais jamais recalculé.
- `next_id` : le numéro du prochain identifiant. Il ne fait que croître : après le retrait de `A5`, la prochaine analyse ajoutée est `A6`, jamais un second `A5`.
- `first_table`, `first_figure` : les numéros de départ du document des résultats (1 par défaut ; 3 si la Méthode a déjà deux tableaux, D-090).
- `entries` : les analyses, dans l'ordre du carnet ; cet ordre est celui du document.

## 2. Une entrée

```json
{
  "id": "A2",
  "analysis": "t_test",
  "variables": {
    "outcome": [{"score": "G1"}],
    "group": [{"variable": "groupe"}]
  },
  "options": {"alternative": "two_sided", "method": "welch"},
  "edits": {
    "table-1": {"title": "Bien-être selon le groupe", "note": null},
    "figure-1": {"title": null, "note": null}
  },
  "retained": true,
  "added": "2026-10-16",
  "computed": {
    "date": "2026-10-16",
    "fingerprint": "a8ed754d4e07…",
    "versions": {"dictionnaire-donnees": "0.11.0", "Python": "3.11.9", "SciPy": "1.17.1", "statsmodels": "0.15.0"},
    "n_used": 300,
    "n_excluded": 0,
    "statistics": {"d": 0.5773, "d_high": 0.8079, "d_low": 0.3458, "df": 297.2859, "diff": 2.4733, "…": "…", "t": 4.9997},
    "sentence": "bienetre_total (score de G1) : M = 17,01 (ÉT = 4,18) pour Intervention et M = 14,54 (ÉT = 4,39) pour Contrôle, t(297,29) = 5,00, p < ,001, d = 0,58, IC 95 % [0,35 ; 0,81].",
    "warnings": []
  },
  "pending": null
}
```

| Champ | Ce qu'il garde |
|---|---|
| `id` | `A1`, `A2`… stable, jamais réutilisé |
| `analysis` | La clé du catalogue (`table1`, `t_test`, `anova`, `chi_square`, `correlation`, `regression`) |
| `variables` | Par rôle, chaque variable par **sa clé du projet**, qui survit à un renommage : `{"variable": "<nom d'origine>"}`, `{"score": "<groupe>"}` (le score de sa cotation), `{"reversed": "<nom d'origine de l'item>"}` (l'item inversé `_inv`) |
| `options` | Toutes les options, défauts compris (`method`, `alternative`, `post_hoc`, et `levels` pour un test *t* sur deux modalités choisies) |
| `edits` | Par élément de l'analyse (`table-1`, `figure-1`…), le titre et la note changés par une personne ; `null` garde la valeur calculée. **Pas de numéro** (D-090) |
| `retained` | Retenue pour l'article (oui ou non) ; seules les analyses retenues entrent au document et au script maître |
| `added` | La date de l'ajout |
| `computed` | Le dernier calcul confirmé : date, empreinte du codebook, versions, effectifs, statistiques agrégées, phrase APA, avertissements |
| `pending` | Un recalcul qui a changé quelque chose et attend une confirmation (même forme que `computed`), ou `null` (§ 5) |

L'ordre des entrées dans `entries` est leur rang : pas de champ `rank` séparé, qui pourrait contredire la liste.

## 3. Les statistiques gardées, et ce qui n'entre jamais

**Gardé** (D-088) : les clés de `statistics` de chaque analyse, telles que l'outil les calcule déjà (*t*, ddl, *p*, *d* et son IC, *M*, *ÉT*, *n* de chaque groupe ; *F*, η², ω², Tukey ; χ², *V* ; *r* et son IC ; *b*, *ET*, IC, β, *t*, *p*, *R*², VIF…), médianes comprises. Deux analyses n'en gardent aujourd'hui aucune ; elles reçoivent des clés **par position**, pour survivre à un renommage :

| Analyse | Clés ajoutées (exemple) |
|---|---|
| Tableau 1 | Pour la variable *i* (dans l'ordre choisi) et la colonne *c* (le code du groupe, ou `total`) : `v1_n_total`, `v1_m_1`, `v1_sd_2` (variable d'échelle) ; `v2_k1_total` (effectif du code 1) pour une variable catégorielle |
| Corrélation à trois variables ou plus | Pour la paire *i*, *j* : `r_2_1`, `p_2_1`, `n_2_1`, `low_2_1`, `high_2_1` (IC de Pearson) |

**Jamais gardé** :

- une ligne de la base, ou la valeur d'une personne pour une variable ;
- un identifiant, un texte libre, une date ;
- un point d'un nuage de points (les paires *x*, *y*) : la figure est redessinée à partir de la base, au moment de l'export ;
- l'étendue observée du Tableau 1 (minimum, maximum), qui est la valeur de deux personnes ; elle reste dans le rapport d'une analyse seule.

**Petits effectifs** : un effectif inférieur à 5 (une catégorie du Tableau 1, une case d'un khi-carré, un groupe) est gardé, comme dans le rapport, et l'avertissement qui le signale est gardé avec lui. Décider de le publier reste à l'équipe.

**Le test à chaînes témoins** : on ajoute au carnet une analyse de chaque type sur les bases fictives qui portent des témoins (`ZQXID-…`, `zqxmail…`, `ZQXTXT…`), puis on vérifie qu'aucun témoin n'apparaît dans le fichier ; et, pour une corrélation à deux variables, qu'aucune paire de valeurs de la base n'y figure, et pour un Tableau 1, ni minimum ni maximum observés.

## 4. L'exemple : quatre analyses de la base fictive

| Ordre | Id | Analyse | Variables | Retenue |
|---|---|---|---|---|
| 1 | A2 | Test *t* | `bienetre_total` (score de G1) selon `groupe` | oui |
| 2 | A3 | ANOVA, Tukey | `stress` selon `niveau_etudes` | oui |
| 3 | A1 | Tableau 1 | `age`, `sexe`, `niveau_etudes`, `bienetre_total`, par `groupe` | oui |
| 4 | A4 | Corrélation | `heures_travail`, `stress`, `soutien` | non |

`A5` (un khi-carré) a été ajouté puis retiré : `next_id` vaut 6.

**Numérotation du document** (D-090), dans l'ordre des analyses retenues :

| Analyse | Tableaux | Figures |
|---|---|---|
| A2, test *t* | Tableau 1 | Figure 1 |
| A3, ANOVA | Tableau 2 (moyennes), Tableau 3 (Tukey) | Figure 2 |
| A1, Tableau 1 | Tableau 4 | — |

Remonter `A1` en tête donne : Tableau 1 (A1), Tableau 2 (A2), Tableaux 3 et 4 (A3), Figures 1 et 2. Avec `first_table` à 3, les numéros vont de 3 à 6. A4, non retenue, n'apparaît ni dans le document ni dans le script maître.

## 5. Recalcul, comparaison et confirmation (D-089)

À l'ouverture de la page « Carnet », et à chaque export, l'outil compare l'empreinte du codebook en vigueur à celle de `computed` :

| État | Quand | Affiché |
|---|---|---|
| **À jour** | Même empreinte | « À jour » |
| **Recalculée, inchangée** | Empreinte changée, chaque statistique et chaque effectif égaux (à 10⁻⁹ près, relatif) | « Recalculée : rien n'a changé. » ; l'empreinte et la date de `computed` sont mises à jour |
| **Changée, à confirmer** | Une statistique ou un effectif différent | La liste des différences (§ 6), et **Confirmer** ; le nouveau calcul attend dans `pending` |
| **Impossible** | Une référence ne mène plus à rien (variable retirée, cotation supprimée, item plus inversé), un niveau de mesure qui ne convient plus, une condition D-074 non remplie | La raison ; l'entrée n'est ni supprimée ni changée |
| **Base introuvable ou modifiée** | Base absente, ou d'une autre empreinte que celle du projet | « La base est introuvable » ou « La base a changé » ; tout est lisible, rien ne se recalcule |

- **Confirmer** remplace `computed` par `pending`.
- **Exporter** : chaque analyse retenue est recalculée. Si l'une d'elles est changée et non confirmée, l'export est refusé, avec la liste de ces analyses. Une analyse impossible est écartée du document, et la fin du document dit laquelle et pourquoi.
- Les clés qui n'existent que d'un côté (une statistique ajoutée par une nouvelle version de l'outil) ne comptent pas comme une différence.

## 6. Le scénario : une décision changée après coup

Sur la base fictive du sommeil, où le code 999 de l'âge est suspect, non déclaré dans le fichier :

1. L'équipe ajoute au carnet la corrélation entre l'âge et les heures de sommeil, **avant** de décider du code 999 : *r*(198) = ,04, IC 95 % [−,10 ; ,18], *p* = ,572 (*n* = 200).
2. Elle confirme ensuite, sur la page de la variable, que 999 est un code manquant. L'empreinte du codebook change.
3. La page « Carnet » montre l'analyse **changée, à confirmer** :

   | Statistique | Avant | Après |
   |---|---|---|
   | *n* | 200 | 197 |
   | *r* | ,04 | ,07 |
   | IC 95 % | [−,10 ; ,18] | [−,07 ; ,21] |
   | *p* | ,572 | ,342 |

4. Elle confirme ; le document des résultats donne désormais *n* = 197.

Et une décision sans effet sur les chiffres (un libellé corrigé) change l'empreinte, mais l'analyse est « recalculée : rien n'a changé ». Un niveau de mesure passé de « échelle » à « ordinal » rend un test *t* sur cette variable **impossible**, avec sa raison.

Les différences s'affichent aux décimales de l'APA ; une différence invisible à ces décimales (au-delà de 10⁻⁹) est montrée avec plus de décimales, pour que « changée » ne s'affiche jamais à côté de deux nombres identiques.

## 7. Les fichiers produits (D-092)

| Fichier | Contenu |
|---|---|
| `etude-analyses-carnet.json` | Le carnet |
| `etude-analyses-resultats.docx` | Les analyses retenues, dans l'ordre : pour chacune, un intertitre (« A2 — Test *t* : comparer deux groupes »), la phrase APA, ses tableaux et ses figures, numérotés à la suite ; à la fin, l'empreinte du codebook, la date, les versions et la liste des analyses (identifiant, analyse, variables), et celles qui ont été écartées parce qu'impossibles |
| `etude-analyses-resultats-graphiques.xlsx` | Une feuille par figure du document, aux mêmes numéros, avec son graphique Excel natif |
| `etude-analyses-resultats-R.zip` | `etude-analyses-resultats.R` (le script maître), le fichier de commandes et le script de préparation |

Ces fichiers sont remplacés à chaque export. Les fichiers `etude-analyses-analyse-<n>` de la page « Analyses » restent, inchangés.

**Le script maître**, en R de base et haven : la lecture de la base, le fichier de commandes, le script de préparation, puis, pour chaque analyse retenue et dans l'ordre :

```r
# A2 — Test t : comparer deux groupes
resultats$A2 <- local({
  # … le corps de l'analyse, celui du script d'une analyse seule …
  resultats
})
```

Chaque analyse travaille dans son propre espace (`local`), pour que ses variables de travail ne se mêlent pas à celles des autres. Le corps de la corrélation à trois variables ou plus calculera toutes les paires (aujourd'hui, la première seulement).

## 8. Points à valider

1. Le scénario de la décision changée sur la **base fictive du sommeil** (codes suspects à confirmer), plutôt que de modifier la base des analyses et son corrigé.
2. L'**ordre des entrées comme rang**, sans champ `rank` séparé.
3. Les **clés par position** pour le Tableau 1 et la corrélation à plusieurs variables (`v1_m_1`, `r_2_1`).
4. Les **médianes gardées** comme statistiques, et l'**étendue observée** jamais gardée.
5. La comparaison **à 10⁻⁹ près** pour dire « rien n'a changé ».
6. Un **intertitre par analyse** dans le document (« A2 — Test *t* : comparer deux groupes »), que l'équipe retire ou garde dans Word.
