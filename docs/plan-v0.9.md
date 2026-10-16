# Plan de la v0.9

> Statut : **validé par l'auteur le 2026-10-15**, avec toutes les recommandations du § 10 (D-069 à D-076). Remplace deux premières versions du même jour (gardées dans l'historique Git) : l'une centrée sur du code écrit par une IA, l'autre sur des analyses calculées par R en arrière-plan. À la demande de l'auteur : des analyses toujours les mêmes, sans IA, **calculées dans l'outil sans rien installer d'autre**, que l'IA peut seulement aider à choisir.

## 1. Pourquoi cette version

La v0.8 a fait du codebook un contrat d'analyse. Son essai (étape 8) a montré qu'un petit modèle local ne sait pas écrire une analyse en R, et que de grands modèles en ligne y arrivent, mais avec des variations d'un modèle à l'autre (un groupe vide gardé dans les résultats, par exemple) et un code qu'il faut relire à chaque fois.

Il y a une voie plus sûre, dans l'esprit de l'outil depuis le début (le calcul déterministe d'abord, l'IA propose, une personne décide) : **un catalogue d'analyses courantes, écrites une fois, vérifiées et testées, calculées dans l'outil**. La personne choisit une analyse et ses variables, clique, et lit les résultats dans la fenêtre de l'outil ; elle n'ouvre aucun autre logiciel et n'installe rien de plus. Les analyses sont toujours les mêmes et toujours justes, quel que soit le modèle, et sans modèle du tout. L'IA, facultative, aide seulement à choisir : à partir des objectifs ou des hypothèses de l'équipe, elle propose une analyse du catalogue et ses variables, ou un plan d'analyse ; une personne confirme.

Le codebook rend ces analyses justes presque d'elles-mêmes : l'outil connaît le niveau de mesure de chaque variable (donc les analyses permises), ses codes manquants (retirés), les scores (selon la cotation) et la structure de la base (mesures répétées ou non).

Les statistiques ne sont pas réécrites : l'outil s'appuie sur des bibliothèques Python éprouvées et libres (SciPy, statsmodels), très utilisées en recherche. Pour la transparence et la reproductibilité, chaque analyse est aussi donnée sous forme de **script R équivalent**, à exécuter dans R ou à joindre à un article ; des tests vérifient que les deux donnent les mêmes résultats.

## 2. Le chemin

```
objectif de l'équipe (facultatif : l'IA locale propose une analyse et ses variables)
  → analyse du catalogue, variables, options     [choisies ou confirmées par une personne]
  → contrôle des conditions d'application        [d'après le codebook]
  → calcul dans l'outil (Python)                 [sur les données lues, jamais modifiées]
  → résultats dans l'outil                       [tableaux, tailles d'effet, phrase APA]
  → rapport et script R équivalent à télécharger [avec l'empreinte du codebook]
```

## 3. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Catalogue d'analyses**, de départ : Tableau 1 (description de l'échantillon), test t (Student ou Welch, et Mann-Whitney), ANOVA à un facteur (et Kruskal-Wallis), khi-carré (et test exact de Fisher), corrélation (Pearson ou Spearman), régression linéaire ; avec tailles d'effet et intervalles de confiance | Les analyses les plus courantes, justes à chaque fois |
| B | **Conditions d'application** tirées du codebook : une variable nominale ne va pas dans une corrélation, un groupe de moins de deux personnes est refusé, des données longitudinales sont signalées pour une analyse qui suppose l'indépendance | Une analyse inadaptée n'est pas lancée par erreur |
| C | **Calcul dans l'outil**, sur les données lues comme pour le profilage, avec les décisions acceptées appliquées en mémoire (codes manquants retirés, items inversés, scores selon la cotation) ; le fichier d'origine n'est jamais modifié | Les analyses appliquées à la base, sans autre logiciel |
| D | **Page « Analyses »** : choisir une analyse, ses variables et ses options ; lancer ; lire les résultats ; télécharger le rapport et le script R équivalent ; et `ddict analyser` en ligne de commande | Tout le parcours sans programmer |
| E | **L'IA conseillère**, facultative et locale : à partir des objectifs de l'équipe, elle propose des analyses du catalogue et leurs variables, ou un plan d'analyse ; elle n'écrit jamais de code | Une aide au choix, jamais une analyse faite par l'IA |
| F | **Bases fictives aux effets connus** : des différences, associations et corrélations plantées à l'avance, pour vérifier que chaque analyse les retrouve | Les analyses testées comme le reste de l'outil |

**Hors de cette version :** les modèles en ligne (la règle « Rien ne quitte le poste » reste entière : choisir dans une liste est à la portée du modèle local, comme pour les rattachements ; l'essai le dira) ; l'exécution de code écrit par une IA, la base synthétique et le vérificateur de scripts (à revoir plus tard) ; les analyses avancées (modèles multiniveaux, équations structurelles, analyses factorielles), pour lesquelles R reste la référence (§ 7) ; les filtres du questionnaire.

## 4. Conception — le catalogue (A, B)

Chaque analyse est décrite comme des données (comme les plateformes de la v0.7) :

| Élément | Exemple (test t) |
|---|---|
| Rôles des variables | une variable dépendante continue (`scale`, ou score) ; une variable de groupe nominale ou ordinale à deux modalités |
| Conditions | la variable dépendante n'est ni un identifiant ni un texte ; deux groupes, au moins 2 personnes chacun ; pas de mesures répétées dans la même colonne |
| Options | Welch (par défaut) ou Student ; bilatéral ou unilatéral ; version non paramétrique (Mann-Whitney) |
| Sorties | effectifs, moyennes et écarts-types par groupe ; t, ddl, p ; d de Cohen et son intervalle de confiance ; phrase de résultat au format APA |
| Hypothèses vérifiées et signalées | normalité dans chaque groupe (indication), égalité des variances (Levene) |

- **Les variables** sont proposées à partir du codebook (noms finaux, libellés, niveaux en vigueur) ; seules celles qui conviennent à un rôle sont offertes. Un score défini par une cotation est offert comme une variable.
- **Un contrôle refusé** dit pourquoi, en clair ; un contrôle douteux (hypothèse fragile, petits groupes) est un avertissement, la personne décide.

## 5. Conception — le calcul et les résultats (C, D)

- **Les données** sont lues comme pour le profilage (`ddict.io`), dans la mémoire de l'outil, le temps du calcul ; rien n'en est enregistré dans le projet (règle 2 : le projet ne garde que des agrégats).
- **Les décisions acceptées sont appliquées en mémoire**, dans le même ordre que les fichiers de commandes et le script de préparation : codes manquants déclarés et confirmés retirés, nouveaux noms, items inversés (`<item>_inv`), scores selon la cotation (règle des items manquants comprise). Une seule fonction, testée contre le script de préparation R de la v0.8 (mêmes scores).
- **Le calcul** passe par SciPy et statsmodels ; les tailles d'effet et leurs intervalles sont calculés dans l'outil selon les formules usuelles, documentées.
- **Les résultats** s'affichent dans l'outil : tableaux, statistiques, tailles d'effet, hypothèses vérifiées, phrase APA. Un **rapport** (Markdown, et le tableau en Excel) se télécharge, avec l'empreinte du codebook, la date, la version de l'outil et des bibliothèques.
- **Le script R équivalent** est écrit pour chaque analyse (lecture de la base, fichier de commandes, script de préparation, analyse en R de base, tailles d'effet avec `effectsize`) : il reproduit les résultats hors de l'outil. Un test, là où R est installé, l'exécute sur chaque base fictive et compare ses résultats à ceux de l'outil.
- **Confidentialité :** les résultats restent sur le poste ; ce sont ceux de l'analyse de l'équipe (un Tableau 1 peut montrer de petits effectifs, signalés quand ils sont sous 5, à l'équipe de décider avant de publier). Rien n'est envoyé à un modèle.

## 6. Conception — l'IA conseillère (E)

- **Facultative et locale**, par le client existant (règle 3 inchangée).
- **Ce qu'elle reçoit**, par la porte de confidentialité : l'objectif écrit par l'équipe, le catalogue (noms, rôles, conditions) et la liste des variables avec leur libellé, leur niveau et leur groupe, comme pour les libellés aujourd'hui. Aucune donnée, aucune statistique.
- **Ce qu'elle répond**, dans un schéma strict (`extra="forbid"`) : des analyses **du catalogue** et des variables **du projet**, désignées par leurs identifiants, avec une courte justification. Une analyse ou une variable inconnue est refusée ; une proposition qui ne respecte pas les conditions est signalée.
- **Toujours une proposition** (principe 5) : la personne la confirme, la change ou la rejette ; rien ne se calcule sans elle.
- Un **banc** mesure, sur des objectifs écrits pour les bases fictives, la part de propositions justes, avec le modèle local, comme pour les rattachements.

## 7. Conception — les bibliothèques, et la suite pour les analyses avancées (D-071)

| Rôle | Choix proposé | Licence (à vérifier à l'étape 1) |
|---|---|---|
| Tests (t, Mann-Whitney, khi-carré, Fisher, corrélations, Levene, Shapiro-Wilk, Kruskal-Wallis) | **SciPy** | BSD |
| ANOVA, régression linéaire, diagnostics | **statsmodels** | BSD |
| Tableau 1, tailles d'effet et intervalles | **calculés dans l'outil** (pandas, SciPy) | — |
| Script R équivalent (téléchargé, pas exécuté par l'outil) | R de base et **effectsize** | GPL (R), GPL-3 (effectsize), appelés par le R de l'utilisateur |

Deux nouvelles dépendances d'exécution (SciPy, statsmodels), notées dans `docs/dependances.md`. L'outil reste installable sans R.

**Les analyses avancées, plus tard.** Python couvre bien le catalogue de départ, mais R reste la référence pour les analyses avancées courantes en psychologie :

| Analyse | En Python | En R |
|---|---|---|
| Modèles multiniveaux linéaires | statsmodels (`MixedLM`) : intercepts et pentes aléatoires, REML | lme4, nlme : la référence |
| Multiniveaux pour une issue binaire ou de comptage | limité (approches bayésiennes approchées) | lme4 (`glmer`), glmmTMB |
| Équations structurelles, analyse factorielle confirmatoire | semopy (MIT) : utilisable, moins éprouvé | lavaan : la référence (estimateurs robustes, données manquantes par maximum de vraisemblance, invariance entre groupes) |
| Analyse factorielle exploratoire, oméga | factor_analyzer, calculs à la main | psych |
| Mesures répétées, médiation | statsmodels (`AnovaRM`, `Mediation`) | afex, lavaan, mediation |

Une version suivante pourra ajouter ces analyses, soit en Python quand la bibliothèque est assez éprouvée, soit par un **moteur R facultatif** (calcul par le R de l'utilisateur quand il est installé, ou script R à exécuter à la main). La structure du catalogue (une analyse décrite comme des données, son calcul et son script R) le permet sans rien changer au reste.

## 8. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiches du catalogue (rôles, conditions, options, sorties, formules des tailles d'effet) et licences des bibliothèques ; un exemple de résultat et de rapport par analyse | Validés par l'auteur |
| 2 | Bases fictives aux effets connus (F) et leur corrigé | Fichiers reproductibles (graine fixe) ; effets plantés retrouvés (test) |
| 3 | Données prêtes pour l'analyse : décisions acceptées appliquées en mémoire ; catalogue comme données, conditions d'application (B) | Scores égaux à ceux du script de préparation R ; chaque condition testée, une analyse inadaptée refusée avec sa raison |
| 4 | Calcul et scripts R équivalents, d'abord pour le Tableau 1, la corrélation et le khi-carré | Résultats égaux au corrigé ; script R exécuté dans R : mêmes résultats que l'outil |
| 5 | Test t, ANOVA, régression linéaire, tailles d'effet, hypothèses signalées | Idem, sur chaque base fictive |
| 6 | Page « Analyses », rapport et script téléchargeables ; `ddict analyser` | Parcours dans le navigateur ; mêmes résultats que la ligne de commande |
| 7 | IA conseillère locale, schéma strict, banc des propositions | Faux serveur : propositions hors catalogue refusées (tests) ; banc avec qwen2.5 7B consigné |
| 8 | Essai : des objectifs à un rapport, sur une base fictive, avec et sans IA ; puis sur une vraie base (calcul sans erreur seulement, aucun résultat consigné) | Essai dans `docs/essais/` |
| 9 | Guides, journal des changements, version 0.9.0 | Scénario refait dans le navigateur ; guides en français et en anglais |

## 9. Risques

- **Une analyse juste mais mal choisie** (une moyenne sur une variable ordinale, des mesures répétées traitées comme indépendantes) : conditions tirées du codebook et avertissements ; la décision reste à l'équipe.
- **Un faux sentiment d'automatisme** : l'outil fait des analyses justes, pas une démarche de recherche ; le guide le dit, et le rapport rappelle les hypothèses vérifiées et celles qui ne le sont pas.
- **Deux calculs à garder concordants** (Python dans l'outil, script R téléchargé) : comparés par les tests sur chaque base fictive, là où R est installé (chez l'auteur, et sur le Mac de GitHub si R y est ajouté).
- **Des résultats sur de petits groupes partagés trop vite** : petits effectifs signalés dans le rapport.
- **Une base volumineuse** : le calcul se fait en mémoire, comme le profilage ; mesuré sur une grande base fictive.
- **Version trop chargée** : si elle s'allonge, l'IA conseillère (étape 7) passe en 0.9.x ; le catalogue et son calcul (étapes 2 à 6) sont utiles seuls.

## 10. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-069 | **Périmètre de la v0.9** | Un catalogue d'analyses écrites et testées, calculées dans l'outil, avec un script R équivalent, et une IA conseillère locale et facultative ; modèles en ligne, code écrit par une IA, base synthétique, vérificateur, analyses avancées et filtres du questionnaire reportés. |
| D-070 | **Calculer des analyses dans l'outil** (remplace en partie D-065) | Oui, mais seulement les analyses du catalogue, écrites et testées ; jamais du code écrit par une IA ; sur les données lues en mémoire, le fichier d'origine jamais modifié. |
| D-071 | **Bibliothèques** | SciPy et statsmodels (BSD) pour le calcul, nouvelles dépendances d'exécution ; tailles d'effet et Tableau 1 calculés dans l'outil ; script R équivalent en R de base et effectsize, appelés par le R de l'utilisateur. Les analyses avancées viendront plus tard, en Python ou par un moteur R facultatif. |
| D-072 | **Résultats et reproductibilité** | Rapport et script R équivalent gardés ensemble, avec l'empreinte du codebook et les versions ; des tests vérifient que le script R donne les mêmes résultats que l'outil ; rien n'est envoyé à un modèle. |
| D-073 | **L'IA conseillère** | Locale et facultative ; elle propose des analyses du catalogue et des variables du projet, dans un schéma strict ; elle n'écrit jamais de code ; toujours une proposition. |
| D-074 | **Conditions d'application** | Une analyse inadaptée selon le codebook (niveau, nombre de groupes, mesures répétées) est refusée avec sa raison ; une hypothèse fragile est un avertissement. |
| D-075 | **Bases fictives aux effets connus** | Le corrigé des analyses, comme celui des rattachements : chaque analyse doit retrouver les effets plantés. |
| D-076 | **Reportés** | Modèles en ligne, exécution de code écrit par une IA, base synthétique, vérificateur de scripts, analyses avancées (multiniveaux, équations structurelles, analyses factorielles), filtres du questionnaire. |
