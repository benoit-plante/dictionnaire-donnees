# Feuille de route : de la base à l'ébauche d'article

> Statut : **proposée le 2026-10-16**, à valider par l'auteur. Elle fait suite à la v0.10.0.
> Choix de l'auteur, le 2026-10-16 : aller le plus loin possible **sans IA**, par le calcul et des gabarits, avant d'ouvrir l'outil à des modèles externes. Les modèles externes viendront **à la fin**, quand l'auteur jugera le niveau déterministe satisfaisant. Jusque-là, les règles du `CLAUDE.md` restent entières : rien ne quitte le poste, et l'IA locale reste facultative.
> Chaque version aura son propre plan (`docs/plan-v0.1x.md`), proposé puis validé, comme les précédentes. Ce document fixe l'ordre et le but de chacune.

---

## 1. Pourquoi cette feuille de route

L'outil mène aujourd'hui d'une base à un codebook décidé, puis à des analyses justes, avec leurs tableaux et figures APA 7. Pour arriver à une **ébauche d'article**, il manque quatre choses :

1. **Une vue d'ensemble des résultats.** Seule la dernière analyse est gardée, en mémoire (D-078), et chaque fichier Word recommence à « Tableau 1 ». Un article réunit dix ou vingt résultats, numérotés à la suite.
2. **La section Méthode.** L'outil connaît les instruments, leurs sources, leur cotation, leur fidélité, les effectifs et les analyses, mais il ne les assemble pas en texte.
3. **Le lien entre ce qui était prévu et ce qui a été fait.** Les objectifs de la conseillère ne sont pas gardés. Il n'y a ni hypothèses, ni plan d'analyse, ni distinction entre confirmatoire et exploratoire.
4. **Une vérification du manuscrit.** Une fois le texte retouché dans Word, rien ne dit si ses chiffres sont encore ceux du calcul.

Tout cela peut se faire **sans modèle de langue**. Le calcul, des règles et des gabarits rédigés d'avance suffisent, comme pour la phrase de résultat APA.

## 2. Le principe : un squelette complet, des trous signalés

À la fin de la phase déterministe, l'outil produira une **ébauche au format IMRaD** dans un seul fichier Word :

| Section | Contenu produit par l'outil | Ce qui reste à écrire |
|---|---|---|
| Introduction | Les hypothèses du plan, numérotées | Le texte : contexte, revue, justification |
| Méthode | Participants (flux, Tableau 1), instruments, procédure de préparation, analyses : **rédigés par gabarits** | La procédure de collecte, l'éthique |
| Résultats | Toutes les analyses retenues : phrases APA, tableaux et figures numérotés à la suite | Les transitions |
| Discussion | Pour chaque hypothèse, le rappel du résultat, **qui décrit sans juger** (D-077) | L'interprétation |
| Références | Les sources des instruments et des cotations, saisies dans le codebook | Les autres références |

Chaque information manquante devient un **trou visible**, par exemple « [à compléter : source de la cotation de G3] ». L'outil ne le remplit jamais par une supposition (principe 4).

Plus tard, les modèles externes n'auront qu'un rôle étroit : rédiger dans ces trous, autour de chiffres que l'outil insère lui-même (§ 9).

## 3. Vue d'ensemble

| Version | But | Ce que l'équipe obtient |
|---|---|---|
| **0.11** | Carnet d'analyses | Toutes les analyses d'une étude gardées, recalculées si le codebook change, réunies dans un document « Résultats » et un script R maître |
| **0.12** | Section Méthode | Exclusions décidées et leur diagramme de flux, qualité de passation, paragraphes Participants, Instruments et Analyses rédigés par gabarits |
| **0.13** | Plan d'analyse | Hypothèses liées aux analyses, préenregistrement, analyses prévues ou exploratoires, correction pour comparaisons multiples, squelette IMRaD complet |
| **0.14** | Catalogue élargi | Test t apparié, régression logistique, modération, corrélation partielle, oméga |
| **0.15** | Vérification et dépôt | Vérificateur des chiffres d'un manuscrit Word, paquet de reproduction |
| plus tard | Moteur R facultatif | Multiniveaux, équations structurelles, analyse factorielle (D-071) |
| **fin** | Modèles externes | À planifier quand l'auteur jugera le déterministe suffisant (§ 9) |

L'ordre des versions 0.13 et 0.14 peut s'inverser si une étude en cours a besoin d'une analyse plus tôt.

---

## 4. v0.11 — Le carnet d'analyses

### Ce que l'outil produira

- **Un carnet à côté du projet** (`<projet>-carnet.json`), distinct du fichier projet, qui reste un dictionnaire de données (D-078).
- Chaque analyse lancée peut y être **ajoutée**, avec un identifiant stable (`A1`, `A2`…). Une entrée garde :
  - l'analyse, les variables par rôle et les options ;
  - les numéros, titres et notes changés par une personne (D-086) ;
  - l'empreinte du codebook au moment du calcul, la date, les versions ;
  - les **statistiques agrégées** du résultat (*t*, ddl, *p*, *d* et son IC, *M*, *ÉT*, *n*…), pour comparer et vérifier plus tard ;
  - « retenue pour l'article » (oui ou non) et un rang.
- **Aucune donnée individuelle dans le carnet.** Les points d'un nuage de points n'y entrent pas. Les figures sont redessinées à partir de la base, au moment de l'export.
- **Recalcul plutôt que relecture.** Le document des résultats est toujours produit en recalculant chaque analyse retenue sur la base, avec les décisions en vigueur. Les chiffres du document sont donc ceux du codebook actuel.
- **Analyses périmées.** Si l'empreinte du codebook a changé depuis l'ajout d'une analyse, l'outil la recalcule et dit si ses résultats ont changé, statistique par statistique. Une personne confirme la nouvelle version.
- **Le document des résultats** (Word) : les analyses retenues, dans l'ordre choisi, chacune avec sa phrase APA, ses tableaux et ses figures, **numérotés à la suite** (Tableau 1 à *n*, Figure 1 à *m*). Le classeur des graphiques Excel natifs est commun à tout le document.
- **Le script R maître** : un `.zip` qui exécute le fichier de commandes, le script de préparation, puis toutes les analyses retenues, dans l'ordre du carnet. Il range chaque résultat sous son identifiant (`resultats$A3`).
- **Page « Carnet »** dans l'interface : la liste, l'ordre, retenir ou écarter, voir ce qui a changé, retirer. **Ligne de commande** : `ddict carnet` (lister, ajouter, retirer) et `ddict resultats` (le document et le script maître).

### Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiche du carnet : format, exemple sur la base fictive des analyses, règles de numérotation et d'ordre | Validée par l'auteur |
| 2 | Modèle et fichier du carnet : écriture JSON déterministe, versions du format, ajout et retrait | Aller-retour sans perte, octet pour octet ; aucune donnée individuelle (test à chaînes témoins) |
| 3 | Recalcul et comparaison : analyse périmée détectée, différences par statistique | Un code manquant confirmé après coup change les effectifs, et l'outil le dit ; une décision sans effet ne signale rien |
| 4 | Document des résultats : numérotation continue, ordre, changements des personnes repris | Test commun des formats (D-083) passé sur un document de plusieurs analyses ; renvois de numéros cohérents |
| 5 | Script R maître | Exécuté dans R : mêmes valeurs que l'outil, à 10⁻⁶ près, pour chaque analyse du carnet |
| 6 | Page « Carnet », `ddict carnet`, `ddict resultats` | Parcours dans le navigateur ; mêmes fichiers que la ligne de commande |
| 7 | Guides, journal des changements, version 0.11.0 | Scénario refait ; guides en français et en anglais |

### Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-087 | **Carnet hors du projet** | Un fichier à côté du projet ; le projet reste un dictionnaire. Remplace D-078 en partie : la dernière analyse reste en mémoire, mais on peut l'ajouter au carnet. |
| D-088 | **Ce que garde le carnet** | Les choix, les changements de titres et de notes, l'empreinte et les statistiques agrégées ; aucune donnée individuelle ; effectifs inférieurs à 5 gardés mais signalés, comme dans le rapport. |
| D-089 | **Recalcul à chaque export** | Le document est recalculé sur la base, jamais copié du carnet ; une différence avec le carnet demande une confirmation. |

---

## 5. v0.12 — La section Méthode

### Ce que l'outil produira

**Participants**
- **Règles d'exclusion**, décidées par l'équipe et enregistrées dans le projet comme des décisions, jamais comme des données. Par exemple :
  - « consentement = 2 (non) » ;
  - « moins de 80 % des items répondus » ;
  - « âge < 18 ».

  Elles sont appliquées en mémoire avant les analyses, dans l'ordre déclaré, comme les autres décisions. Elles s'écrivent aussi dans le fichier de commandes et dans le script R.
- **Effectifs par règle**, calculés : combien de personnes chaque règle retire, dans l'ordre.
- **Diagramme de flux des participants**, en figure APA (Word et graphique modifiable), tiré de ces effectifs.
- **Qualité de passation** des exports de plateforme, proposée par des règles et décidée par une personne (origine « règle », D-067) :
  - durée de passation très courte (seuil choisi par l'équipe, jamais par l'outil) ;
  - réponses en ligne droite dans une grille ;
  - doublons probables.

  Chaque signal peut devenir une règle d'exclusion.

**Instruments**
- Un paragraphe par groupe coté, rédigé par gabarit à partir du codebook :
  - nom de l'instrument et sa source ;
  - nombre d'items, format de réponse (étiquettes des extrémités) ;
  - cotation (somme ou moyenne, règle des items manquants, D-068), étendue du score ;
  - items inversés ;
  - **fidélité observée** : l'alpha existe déjà ; on y ajoute son intervalle de confiance et l'oméga si D-091 est adoptée.
- Un instrument sans source ou sans cotation donne un trou signalé, jamais une supposition.

**Analyses**
- Un paragraphe tiré du carnet :
  - méthodes et options (Welch, Tukey, Spearman…) ;
  - traitement des manquants (suppression par analyse) ;
  - tailles d'effet et leurs intervalles ;
  - logiciel et versions ;
  - script R équivalent.

**Gabarits**
- En français et en anglais, sous forme de phrases entières traduites d'un bloc, comme les notes APA.
- Le texte se modifie ensuite librement dans Word.

**Le document de la v0.11** devient « Méthode et Résultats ».

### Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiches : gabarits des trois paragraphes et du diagramme de flux, sur la base fictive, en français et en anglais | Validées par l'auteur |
| 2 | Règles d'exclusion dans le projet (format 0.4.0), appliquées en mémoire, dans les fichiers de commandes et le script R | Mêmes effectifs dans l'outil, SPSS (PSPP) et R |
| 3 | Effectifs par règle et diagramme de flux | Chiffres égaux au corrigé d'une base fictive aux exclusions plantées |
| 4 | Qualité de passation (durée, ligne droite, doublons), proposée par des règles | Cas plantés retrouvés dans une base SurveyMonkey fictive ; aucune proposition sans seuil choisi par l'équipe |
| 5 | Fidélité : IC de l'alpha, et oméga si adopté | Égaux à R (`psych` ou formules) sur les bases fictives |
| 6 | Paragraphes rédigés et trous signalés ; document « Méthode et Résultats » | Chaque fait du texte retrouvé dans le codebook ou le carnet (test) ; un champ vide donne un trou, jamais un texte |
| 7 | Guides, journal des changements, version 0.12.0 | Scénario refait ; guides en français et en anglais |

### Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-090 | **Règles d'exclusion** | Des décisions du projet, écrites par une personne, appliquées en mémoire et dans les scripts ; jamais une liste de participants. |
| D-091 | **Oméga** | Oméga total d'un modèle à un facteur, calculé dans l'outil et comparé à R ; sinon, alpha et son IC seulement. |
| D-092 | **Gabarits de la Méthode** | Phrases fixes, traduites d'un bloc ; trou signalé pour toute information manquante ; aucune formulation qui juge (« excellente fidélité »). |

---

## 6. v0.13 — Le plan d'analyse et le squelette d'article

### Ce que l'outil produira

- **Des hypothèses**, écrites par l'équipe et numérotées (H1, H2…). Chacune est liée à :
  - une analyse du catalogue, ses variables par rôle et ses options, choisies à la main. La conseillère locale existante peut proposer, facultativement, comme aujourd'hui ;
  - un caractère, confirmatoire ou exploratoire ;
  - une famille de comparaisons, pour la correction.
- **Les règles générales du plan** : seuil alpha, correction pour comparaisons multiples (aucune, Bonferroni ou Holm, appliquée dans le carnet à la famille déclarée), traitement des manquants.
- **Un plan figé** : une empreinte et une date, comme le codebook. Changer le plan après coup reste possible, mais l'écart est gardé et dit.
- **Un préenregistrement** exporté en Word ou Markdown, selon un gabarit au choix (AsPredicted, OSF Prereg), rempli à partir du plan et du codebook. Les trous restent signalés.
- **Dans le carnet**, chaque analyse est rapprochée du plan : prévue (H2), écart au plan (variable ou option changée), ou exploratoire.
- **La Méthode** dit ce qui était prévu, ce qui a changé et ce qui est exploratoire. **Les Résultats** sont rangés par hypothèse, puis les analyses exploratoires.
- **Le squelette IMRaD complet** (§ 2) : Introduction (hypothèses), Méthode, Résultats, Discussion (rappel par hypothèse, sans jugement), Références (sources du codebook).

### Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiches : format du plan, gabarits de préenregistrement, squelette IMRaD | Validées par l'auteur |
| 2 | Plan dans le projet : hypothèses, liens au catalogue, conditions vérifiées (D-074), empreinte | Une hypothèse mal liée est refusée avec sa raison |
| 3 | Rapprochement du carnet et du plan ; correction pour comparaisons multiples | *p* corrigés égaux à `p.adjust` de R ; écarts au plan détectés sur des cas plantés |
| 4 | Préenregistrement exporté | Chaque champ rempli retrouvé dans le plan ou le codebook ; trous signalés |
| 5 | Squelette IMRaD | Test commun des formats ; aucune phrase qui juge ; références tirées des sources seulement |
| 6 | Page « Plan » et ligne de commande | Parcours dans le navigateur |
| 7 | Guides, journal des changements, version 0.13.0 | Scénario refait ; guides en français et en anglais |

### Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-093 | **Où vit le plan** | Dans le projet : ce sont des décisions de l'équipe, pas des résultats. |
| D-094 | **Corrections pour comparaisons multiples** | Holm par défaut quand une famille est déclarée ; aucune sinon ; *p* bruts et corrigés tous deux dans les tableaux. |
| D-095 | **Discussion** | Rappel des résultats par hypothèse, avec la phrase de résultat ; jamais « soutenue » ou « rejetée » écrit par l'outil. |

---

## 7. v0.14 — Le catalogue élargi

Les analyses les plus demandées en psychologie qui manquent au catalogue, chacune au même niveau d'exigence que la v0.9 : une fiche validée, une base fictive aux effets connus, un script R équivalent vérifié à 10⁻⁶ près, un tableau et une figure APA, et le test commun des formats.

| Analyse | Pourquoi | Bibliothèque |
|---|---|---|
| Test *t* apparié et Wilcoxon des rangs signés | Deux mesures d'une même personne (format large, vagues renommées en v0.7) | SciPy |
| Régression logistique binaire | Issue oui/non ; rapports de cotes et leurs IC | statsmodels |
| Modération | Interaction dans la régression, variables centrées, pentes simples | statsmodels |
| Corrélation partielle | Associations à covariables constantes | calculs dans l'outil |
| ANOVA à mesures répétées | Trois temps ou plus | statsmodels (`AnovaRM`), à vérifier contre R |

La médiation, les modèles multiniveaux, les équations structurelles et l'analyse factorielle restent pour le **moteur R facultatif** (D-071), à planifier séparément.

### Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-096 | **Analyses de la v0.14** | Les cinq ci-dessus ; les autres attendent le moteur R. |
| D-097 | **Mesures répétées et structure de la base** | Ces analyses ne sont offertes que si la description de la base (D-064) dit « format large » ou si les vagues sont réunies ; refus avec sa raison sinon. |

---

## 8. v0.15 — Vérification du manuscrit et paquet de reproduction

### Vérificateur des chiffres

- L'outil lit un manuscrit `.docx`, même retouché à la main, et y repère les statistiques écrites au style APA, en français et en anglais : *t*(ddl), *F*(ddl, ddl), χ²(ddl), *r*, *p*, *M*, *ÉT*/*SD*, *d*, β, *b*, IC [a ; b], *N* et *n*.
- Il compare chaque valeur aux statistiques du carnet, aux décimales près, et la classe : **concorde**, **diffère** (avec la valeur attendue), **sans origine** (aucune analyse du carnet n'a ce chiffre) ou **périmée** (l'analyse a changé depuis).
- Il donne un rapport, et une copie du manuscrit avec des commentaires Word aux endroits concernés. Le manuscrit d'origine n'est jamais modifié.
- C'est entièrement déterministe, et utile même pour un article écrit sans l'outil.

### Paquet de reproduction

- Un `.zip` prêt pour un dépôt (OSF, Borealis) :
  - codebook (Excel et Markdown) et `datapackage.json` (v0.8) ;
  - plan et préenregistrement ;
  - fichier de commandes, script de préparation et script R maître ;
  - un README de dépôt rédigé par gabarit.
- **Sans la base**, que l'équipe dépose ou non selon son certificat d'éthique.

### Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-098 | **Ce que lit le vérificateur** | Les statistiques au style APA seulement ; tout chiffre ambigu est dit « non reconnu » plutôt que deviné. |
| D-099 | **Base synthétique dans le paquet** | Reportée (D-076) ; à rediscuter avec les modèles externes, où elle a le plus d'usage. |

---

## 9. La fin : les modèles externes

**À planifier seulement quand l'auteur jugera le niveau déterministe satisfaisant.** Ce qui suit n'est qu'une liste de pistes, pour que les choix des versions 0.11 à 0.15 ne les ferment pas.

> **Fait en v0.18** (`docs/plan-v0.18.md`, D-134 à D-139) : la règle est reformulée (« Aucune donnée de participant ne quitte le poste »), l'envoi externe est activé projet par projet, et seul le **niveau 1** existe dans l'outil, pour les quatre usages d'avant (libellés, rattachement, radicaux, conseillère), par une clé d'API (Anthropic, ou le serveur d'une université). Le niveau 2 n'existe que dans le banc. Le reste de cette section (rédaction de l'article, bibliographie, code hors catalogue) demeure une piste.

- **La règle à reformuler.** Aujourd'hui : « Rien ne quitte le poste ». Proposition : « **Aucune donnée ne quitte le poste** », avec un envoi externe activé explicitement, projet par projet. Cela changera la règle 3 du `CLAUDE.md`, `check_local()` et D-073.
- **Des niveaux d'envoi**, choisis par l'équipe selon son certificat d'éthique :
  - 0 : rien ;
  - 1 : métadonnées (contexte d'analyse, plan, squelette) ;
  - 2 : en plus, des résultats agrégés filtrés par la porte de confidentialité ; jamais un nuage de points ni un effectif inférieur à 5.
- **Le modèle n'écrit jamais un chiffre.** Il rédige avec des renvois au carnet (`{{A3.t}}`, `{{A3.d_IC}}`), et l'outil insère les valeurs. C'est le prolongement de D-086. Le vérificateur de la v0.15 contrôle ensuite le résultat.
- **Le modèle ne cite que la bibliographie de l'équipe** (import Zotero ou BibTeX). Toute autre affirmation est marquée « à sourcer ».
- **Le modèle ne remplit que les trous du squelette** : Introduction, Discussion, transitions. Les sections rédigées par gabarit restent celles de l'outil.
- **Deux modes possibles** :
  - un paquet de rédaction à coller dans un assistant, puis réimporté et vérifié, sans clé d'API ;
  - un client externe intégré.
- **Journal des envois** (le dossier des envois existe déjà) et **déclaration d'usage de l'IA** produite à partir de ce journal.
- **Code hors catalogue** : un modèle externe peut l'écrire, la personne l'exécute dans son propre R, et le résultat peut entrer au carnet, marqué « hors catalogue ». L'outil n'exécute toujours aucun code d'IA (D-070).

**Critère pour ouvrir cette phase** (à préciser par l'auteur) : sur une vraie base, l'ébauche déterministe donne une Méthode et des Résultats complets, sans trou autre que ceux qui demandent un jugement, et le vérificateur trouve tous les chiffres du document.

---

## 10. Risques

- **Un texte de gabarit raide.** Des phrases fixes se lisent comme un formulaire. Elles sont modifiables dans Word, et les fiches de chaque version les font valider par l'auteur avant le code.
- **Un faux sentiment d'article fini.** Le squelette ne remplace ni la revue de littérature ni l'interprétation. Les trous restent visibles jusque dans le fichier Word.
- **Le carnet et la base qui divergent.** On recalcule à chaque export (D-089), et une analyse périmée est signalée.
- **Des données individuelles qui fuient par les figures ou le carnet.** Le carnet ne garde que des agrégats (test à chaînes témoins) ; les figures sont redessinées sur le poste.
- **Deux langues à entretenir.** Chaque gabarit existe en français et en anglais, ce qui double la relecture. La traduction anglaise attend toujours une relecture (D-034).
- **Des versions trop chargées.** Chaque version est utile seule. En cas de dépassement, la dernière étape fonctionnelle passe à la version mineure suivante (0.1x.1), comme prévu pour la conseillère en v0.9.

## 11. Ce que l'auteur valide maintenant

1. L'ordre des versions, en particulier 0.13 (plan) avant 0.14 (catalogue).
2. Le principe du squelette IMRaD à trous signalés (§ 2).
3. Le carnet hors projet, avec recalcul à chaque export (D-087 à D-089), pour lancer le plan détaillé de la v0.11.
