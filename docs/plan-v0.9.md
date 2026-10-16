# Plan de la v0.9

> Statut : **proposé le 2026-10-15, en attente de validation par l'auteur** (décisions D-069 à D-076 au § 10). Remplace une première version du même jour, centrée sur du code écrit par une IA (gardée dans l'historique Git), à la demande de l'auteur : des analyses toujours les mêmes, sans IA, que l'IA peut seulement aider à choisir.

## 1. Pourquoi cette version

La v0.8 a fait du codebook un contrat d'analyse. Son essai (étape 8) a montré qu'un petit modèle local ne sait pas écrire une analyse en R, et que de grands modèles en ligne y arrivent, mais avec des variations d'un modèle à l'autre (un groupe vide gardé dans les résultats, par exemple) et un code qu'il faut relire à chaque fois.

Il y a une voie plus sûre, dans l'esprit de l'outil depuis le début (le calcul déterministe d'abord, l'IA propose, une personne décide) : **un catalogue d'analyses courantes, écrites une fois, vérifiées et testées**, que l'outil remplit avec les bonnes variables et exécute sur la base. Les analyses sont toujours les mêmes et toujours justes, quel que soit le modèle, et sans modèle du tout. L'IA, facultative, aide seulement à choisir : à partir des objectifs ou des hypothèses de l'équipe, elle propose une analyse du catalogue et ses variables, ou un plan d'analyse ; une personne confirme.

Le codebook rend ces analyses justes presque d'elles-mêmes : l'outil connaît le niveau de mesure de chaque variable (donc les analyses permises), ses codes manquants (retirés), les scores (calculés par le script de préparation) et la structure de la base (mesures répétées ou non).

Les statistiques ne sont pas réécrites : l'outil s'appuie sur R et sur des paquets éprouvés, largement utilisés en psychologie et en sciences sociales, et appelés par le R de l'utilisateur, comme `haven` aujourd'hui.

## 2. Le chemin

```
objectif de l'équipe (facultatif : l'IA locale propose une analyse et ses variables)
  → analyse du catalogue, variables, options             [choisies ou confirmées par une personne]
  → contrôle des conditions d'application                [d'après le codebook]
  → script R écrit par l'outil, à partir du gabarit      [lisible, gardé avec les résultats]
  → exécution par le R de l'utilisateur, sur une copie   [fichier de commandes et préparation d'abord]
  → résultats dans l'outil, et rapport à télécharger     [avec l'empreinte du codebook]
```

Sans R sur le poste, l'outil écrit le script : la personne l'exécute elle-même, comme les fichiers de commandes de la v0.4.

## 3. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Catalogue d'analyses**, de départ : Tableau 1 (description de l'échantillon), test t (Student ou Welch, et Mann-Whitney), ANOVA à un facteur (et Kruskal-Wallis), khi-carré (et test exact de Fisher), corrélation (Pearson ou Spearman), régression linéaire ; avec tailles d'effet et intervalles de confiance | Les analyses les plus courantes, justes à chaque fois |
| B | **Conditions d'application** tirées du codebook : une variable nominale ne va pas dans une corrélation, un groupe de moins de deux personnes est refusé, des données longitudinales sont signalées pour une analyse qui suppose l'indépendance | Une analyse inadaptée n'est pas lancée par erreur |
| C | **Exécution par le R de l'utilisateur**, sur une copie de la base, après le fichier de commandes et le script de préparation ; résultats structurés | Les analyses appliquées à la base, dans l'outil |
| D | **Page « Analyses »** : choisir une analyse, ses variables et ses options ; voir le script ; lancer ; lire les résultats ; télécharger le rapport et le script | Tout le parcours sans programmer |
| E | **L'IA conseillère**, facultative et locale : à partir des objectifs de l'équipe, elle propose des analyses du catalogue et leurs variables, ou un plan d'analyse ; elle n'écrit jamais de code | Une aide au choix, jamais une analyse faite par l'IA |
| F | **Bases fictives aux effets connus** : des différences, associations et corrélations plantées à l'avance, pour vérifier que chaque analyse les retrouve | Les gabarits testés comme le reste de l'outil |

**Hors de cette version :** les modèles en ligne (la règle « Rien ne quitte le poste » reste entière : choisir dans une liste est à la portée du modèle local, comme pour les rattachements ; l'essai le dira) ; l'exécution de code écrit par une IA, la base synthétique et le vérificateur de scripts (de la première version du plan, à revoir plus tard) ; les modèles mixtes pour les données longitudinales et les analyses factorielles (une version suivante) ; les filtres du questionnaire ; Python et la syntaxe SPSS pour les analyses (R seulement).

## 4. Conception — le catalogue (A, B)

Chaque analyse est décrite comme des données (comme les plateformes de la v0.7), et son gabarit R est un texte fixe, rempli par l'outil :

| Élément | Exemple (test t) |
|---|---|
| Rôles des variables | une variable dépendante continue (`scale`, ou score) ; une variable de groupe nominale ou ordinale à deux modalités |
| Conditions | la variable dépendante n'est ni un identifiant ni un texte ; deux groupes, au moins 2 personnes chacun ; pas de mesures répétées dans la même colonne |
| Options | Welch (par défaut) ou Student ; bilatéral ou unilatéral ; version non paramétrique (Mann-Whitney) |
| Sorties | effectifs, moyennes et écarts-types par groupe ; t, ddl, p ; d de Cohen et son intervalle de confiance ; phrase de résultat au format APA |
| Hypothèses vérifiées et signalées | normalité dans chaque groupe (indication), égalité des variances (Levene) |

- **Les variables** sont proposées à partir du codebook (noms finaux, libellés, niveaux en vigueur) ; seules celles qui conviennent à un rôle sont offertes.
- **Les codes manquants** sont retirés par le fichier de commandes ; **les scores** viennent du script de préparation ; le script d'analyse ne fait que l'analyse.
- **Un contrôle refusé** dit pourquoi, en clair ; un contrôle douteux (hypothèse fragile, petits groupes) est un avertissement, la personne décide.

## 5. Conception — l'exécution et les résultats (C, D)

- **R** est cherché sur le poste comme pour les tests (`Rscript`, ou `R/R-*/bin` sous Windows) ; les paquets nécessaires sont vérifiés avant de lancer, et la commande pour les installer est donnée s'ils manquent (l'outil ne les installe pas lui-même).
- **Le script complet** est écrit dans un dossier « analyses » à côté du projet : lecture de la base (ou de sa copie documentée), fichier de commandes, script de préparation, puis l'analyse. Il reste lisible et réutilisable tel quel, avec l'empreinte du codebook en tête : l'analyse est reproductible hors de l'outil.
- **L'exécution** se fait par `Rscript` sur une copie, avec un délai maximal ; le fichier d'origine n'est jamais touché. Le code exécuté est **celui de l'outil**, vérifié et testé, jamais du code écrit par une IA.
- **Les résultats** sont écrits par le script dans des fichiers structurés (tableaux CSV et un fichier de résultats), lus par l'outil et affichés : tableaux, statistiques, tailles d'effet, phrase APA. Un **rapport** (Markdown, et le tableau en Excel) se télécharge, avec le script, l'empreinte et la date.
- **Confidentialité :** les résultats restent sur le poste ; ce sont ceux de l'analyse de l'équipe (un Tableau 1 peut montrer de petits effectifs, signalés quand ils sont sous 5, à l'équipe de décider avant de publier). Rien n'est envoyé à un modèle.

## 6. Conception — l'IA conseillère (E)

- **Facultative et locale**, par le client existant (règle 3 inchangée).
- **Ce qu'elle reçoit**, par la porte de confidentialité : l'objectif écrit par l'équipe, le catalogue (noms, rôles, conditions) et la liste des variables avec leur libellé, leur niveau et leur groupe, comme pour les libellés aujourd'hui. Aucune donnée, aucune statistique.
- **Ce qu'elle répond**, dans un schéma strict (`extra="forbid"`) : des analyses **du catalogue** et des variables **du projet**, désignées par leurs identifiants, avec une courte justification. Une analyse ou une variable inconnue est refusée ; une proposition qui ne respecte pas les conditions est signalée.
- **Toujours une proposition** (principe 5) : la personne la confirme, la change ou la rejette ; rien ne s'exécute sans elle.
- Un **banc** mesure, sur des objectifs écrits pour les bases fictives, la part de propositions justes, avec le modèle local, comme pour les rattachements.

## 7. Conception — les paquets R (D-071)

Critères : justesse reconnue, large usage en psychologie et en sciences sociales, maintenance active, licence libre, et des résultats lisibles sans programmer. Appelés par le R de l'utilisateur, jamais intégrés à l'outil. Licences vérifiées à l'étape 1 et notées dans `docs/dependances.md`.

| Rôle | Choix proposé | Autre choix |
|---|---|---|
| Tests et régression | **R de base** (`stats` : `t.test`, `aov`, `chisq.test`, `cor.test`, `lm`) : code transparent, que toute personne qui connaît R peut relire | `jmv` : les analyses de jamovi, résultats identiques à ce logiciel connu en psychologie, mais en une fonction qui cache le calcul |
| Tailles d'effet et intervalles | **effectsize** | calcul dans le gabarit |
| Tableau 1 | **gtsummary** | tableau construit dans le gabarit |
| Hypothèses (Levene) | **car** ou calcul dans le gabarit | — |

## 8. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiches du catalogue (rôles, conditions, options, sorties) et choix des paquets, avec leurs licences ; un exemple de résultat et de rapport par analyse | Validés par l'auteur |
| 2 | Bases fictives aux effets connus (F) et leur corrigé | Fichiers reproductibles (graine fixe) ; effets plantés retrouvés par un calcul indépendant (test) |
| 3 | Catalogue comme données, conditions d'application (B) | Chaque condition testée : une analyse inadaptée est refusée avec sa raison |
| 4 | Exécution par R, scripts et résultats structurés (C), d'abord pour le Tableau 1, la corrélation et le khi-carré | Résultats égaux au corrigé et à un calcul indépendant ; base d'origine intacte ; sans R, le script est écrit |
| 5 | Test t, ANOVA, régression linéaire, tailles d'effet, hypothèses signalées | Idem, sur chaque base fictive |
| 6 | Page « Analyses », rapport et script téléchargeables | Parcours dans le navigateur ; mêmes résultats que la ligne de commande (`ddict analyser`) |
| 7 | IA conseillère locale, schéma strict, banc des propositions | Faux serveur : propositions hors catalogue refusées (tests) ; banc avec qwen2.5 7B consigné |
| 8 | Essai : des objectifs à un rapport, sur une base fictive, avec et sans IA ; puis sur une vraie base (exécution sans erreur seulement, aucun résultat consigné) | Essai dans `docs/essais/` |
| 9 | Guides, journal des changements, version 0.9.0 | Scénario refait dans le navigateur ; guides en français et en anglais |

## 9. Risques

- **Une analyse juste mais mal choisie** (une moyenne sur une variable ordinale, des mesures répétées traitées comme indépendantes) : conditions tirées du codebook et avertissements ; la décision reste à l'équipe.
- **Un faux sentiment d'automatisme** : l'outil fait des analyses justes, pas une démarche de recherche ; le guide le dit, et le rapport rappelle les hypothèses vérifiées et celles qui ne le sont pas.
- **R ou un paquet absent, ou d'une autre version** : vérification avant de lancer, commande d'installation donnée, version des paquets écrite dans le rapport.
- **Des résultats sur de petits groupes partagés trop vite** : petits effectifs signalés dans le rapport.
- **Version trop chargée** : si elle s'allonge, l'IA conseillère (étape 7) passe en 0.9.x ; le catalogue et son exécution (étapes 2 à 6) sont utiles seuls.

## 10. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-069 | **Périmètre de la v0.9** | Un catalogue d'analyses écrites et testées, exécutées par le R de l'utilisateur, et une IA conseillère locale et facultative ; modèles en ligne, code écrit par une IA, base synthétique, vérificateur, modèles mixtes et filtres du questionnaire reportés. |
| D-070 | **Exécuter des analyses dans l'outil** (remplace en partie D-065) | Oui, mais seulement les gabarits de l'outil, vérifiés et testés ; jamais du code écrit par une IA ; par le R de l'utilisateur, sur une copie ; sans R, le script est écrit pour être exécuté à la main. |
| D-071 | **Paquets R** | R de base pour les tests et la régression (code transparent), effectsize, gtsummary ; appelés par le R de l'utilisateur, jamais intégrés ; licences notées. Autre choix : `jmv`, pour des résultats identiques à jamovi. |
| D-072 | **Résultats et reproductibilité** | Résultats structurés écrits par le script ; rapport et script complet gardés ensemble, avec l'empreinte du codebook et la version des paquets ; rien n'est envoyé à un modèle. |
| D-073 | **L'IA conseillère** | Locale et facultative ; elle propose des analyses du catalogue et des variables du projet, dans un schéma strict ; elle n'écrit jamais de code ; toujours une proposition. |
| D-074 | **Conditions d'application** | Une analyse inadaptée selon le codebook (niveau, nombre de groupes, mesures répétées) est refusée avec sa raison ; une hypothèse fragile est un avertissement. |
| D-075 | **Bases fictives aux effets connus** | Le corrigé des analyses, comme celui des rattachements : chaque gabarit doit retrouver les effets plantés. |
| D-076 | **Reportés** | Modèles en ligne, exécution de code écrit par une IA, base synthétique, vérificateur de scripts, modèles mixtes, filtres du questionnaire. |
