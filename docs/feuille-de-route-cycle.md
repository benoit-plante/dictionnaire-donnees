# Feuille de route : tout le cycle de recherche

> Statut : **validée par l'auteur le 2026-10-20**, avec toutes les recommandations, la numérotation du § 3 (D-164) et le texte de D-163 resserré par les objections du § 13.4 (consignée au journal ; les formulations du § 13.2 sont écrites au début de la v0.27). Elle fait suite à la v0.20.2.
> Point de départ : l'auteur a relu l'outil avec les yeux d'une chercheuse en psychologie qui mène une étude par questionnaire en ligne (LimeSurvey, environ 300 personnes, deux vagues). L'outil va de la conception du questionnaire au manuscrit vérifié, mais il manque des étapes du cycle. Cette feuille de route fixe leur ordre, leur numéro de version, la place du dossier d'étude et des sources, et ce que l'IA peut y faire.
> Chaque version aura son propre plan (`docs/plan-v0.xx.md`), proposé puis validé, comme les précédentes. Le plan de la première est [`plan-v0.21.md`](plan-v0.21.md).

---

## 1. Pourquoi cette feuille de route

Ce que l'outil fait déjà, dans l'ordre d'une étude : concevoir le questionnaire et le publier pour LimeSurvey (v0.20), documenter la base à son arrivée, décider les exclusions et la Méthode (v0.12), écrire le plan d'analyse et le figer (v0.13), analyser (v0.9, v0.14), réunir l'ébauche d'article et la vérifier (v0.11, v0.13, v0.15).

Ce qui manque, vu par la chercheuse :

| Moment de l'étude | Ce qui manque | Étape |
|---|---|---|
| Concevoir | Les filtres (« posée si »), l'ordre aléatoire, le « non applicable », les items de contrôle d'attention, la durée de passation à annoncer au comité | 1 |
| Concevoir | Combien de personnes recruter, et pourquoi | 2 |
| Demander l'éthique | Le plan de gestion des données ; la base qu'on pourra partager, et son risque de réidentification | 3 |
| Collecter | Voir la collecte avancer ; faire un pilote et en tirer les leçons | 4 |
| Rédiger | Une aide de l'IA autour des résultats (Discussion, résumé vulgarisé, retour aux participants, affiche) | 5 |
| Analyser, rédiger, déposer | Deux vagues réunies, les données manquantes, les réponses ouvertes, la psychométrie, la sensibilité, la liste JARS, les déclarations, la réponse aux évaluateurs, la conservation | 6 |

## 2. Le principe

**L'IA recopie ou propose, le calcul vérifie, une personne décide.** C'est le principe de la v0.20, élargi : l'IA peut aussi *proposer* (une grille de codage, un texte en langage simple), et ce qu'elle propose passe toujours par un contrôle calculé avant d'être montré, puis par une décision humaine.

Deux niveaux d'envoi, et deux seulement :

| Niveau | Ce qui part | Activation | Depuis |
|---|---|---|---|
| **Métadonnées** (le niveau 1 de D-136) | Le questionnaire, le codebook, le plan, les sources déposées (pages choisies, D-144), le texte écrit par l'équipe | Par projet (D-138) | v0.18 |
| **Résultats à publier** (§ 13) | En plus, les statistiques que l'outil écrit lui-même dans l'ébauche, cellules de moins de 5 masquées | Par projet, **puis document par document** | étape 5 |

Rien d'autre ne part jamais : ni une ligne, ni une valeur observée, ni un texte libre, ni une figure, ni une analyse non retenue. J'évite d'appeler le second niveau « niveau 2 » : ce nom désigne, dans le banc et dans D-136, les agrégats bruts du profil (codes observés, proportions), qui ne partent toujours pas.

## 3. Vue d'ensemble et numérotation proposée

Je propose de **numéroter les versions dans l'ordre où elles seront publiées**, à partir de la prochaine, et de ne plus réserver de numéro d'avance (D-164, § 12). La v0.21 prévue (sources) et le dossier d'étude (ancienne v0.19) prennent leur place dans cet ordre.

| Version | But | Étape | IA |
|---|---|---|---|
| **0.21** | Filtres, ordre aléatoire, non applicable, items de contrôle, durée estimée | 1 | aucune |
| **0.22** | Taille d'échantillon et puissance, par le calcul | 2 | aucune |
| **0.23** | Le dossier d'étude (l'ancienne v0.19) | — | aucune |
| **0.24** | Les sources, la vérification mot pour mot, l'extraction d'un instrument (l'ancienne v0.21) ; en plus : une taille d'effet relevée dans un article, la relecture des filtres, des items de contrôle proposés, une traduction proposée | 1, 2 | métadonnées |
| **0.25** | La base désidentifiée, le risque de réidentification, le plan de gestion des données ; la lettre d'information et le consentement en langage simple | 3 | métadonnées |
| **0.26** | Le suivi de la collecte et le pilote | 4 | aucune |
| **0.27** | Le niveau « résultats à publier » : Discussion, résumé vulgarisé, retour aux participants, affiche ; la fiche pour le comité d'éthique | 5 | résultats à publier |
| **0.28** | Deux vagues appariées et réunies ; le portrait des données manquantes et le test MCAR de Little | 6 | aucune |
| **0.29** | Les réponses ouvertes et « Autre, précisez » | 6 | métadonnées |
| **0.30** | Le moteur R facultatif : oméga, AFC, invariance, imputation multiple | 6 | aucune |
| **0.31** | Analyses de sensibilité, liste JARS-Quant, déclarations (usage de l'IA, CRediT), réponse aux évaluateurs | 6 | métadonnées ou résultats |
| **0.32** | Conservation et export DDI Codebook | 6 | aucune |

Les versions 0.21 et 0.22 ne dépendent de rien d'autre : elles peuvent commencer tout de suite. Une version trop chargée se coupe en 0.xx.1, comme jusqu'ici.

## 4. Ce qui dépend de quoi

```
0.21 filtres ─────────────┬──────────────────────────────► 0.26 suivi et pilote
                          │                                  ▲   (durée réelle contre durée estimée,
0.22 puissance (calcul) ──┼──► 0.24 taille d'effet relevée   │    filtres qui se comportent mal)
                          │         ▲                        │
0.23 dossier d'étude ─────┼──► 0.24 sources ──► 0.25 PGD, lettre, consentement (IA)
        │                 │                                  │
        └─ pilote et étude principale, deux projets d'une même étude ─┘
0.11–0.15 carnet, ébauche, vérificateur ─────────────────► 0.27 résultats à publier
0.21 non applicable ─► 0.28 manquants (un « non applicable » n'est pas un manquant)
```

- **Le dossier d'étude (0.23)** est le cadre de tout ce qui produit plusieurs fichiers ou plusieurs projets : le pilote et l'étude principale, les deux vagues, la base désidentifiée, le plan de gestion des données (qui décrit les dossiers réels), les sources dans `instruments/`. D-161 lui confie aussi le nom des fichiers d'une étude. Il doit donc venir **avant 0.24** (les sources y vont, plan-v0.20 § 0) et **avant 0.25 et 0.26**. Il ne bloque ni 0.21 ni 0.22.
- **Les sources (0.24)** portent tout ce que l'IA tire d'un document : l'instrument (D-143), mais aussi **la taille d'effet relevée dans un article** pour la puissance, et **le protocole** dont partent le plan de gestion des données, la lettre d'information et le consentement. La puissance par le calcul (0.22) n'en dépend pas : l'équipe tape sa taille d'effet et sa source, comme un seuil. Le relevé par l'IA s'ajoute en 0.24.
- **La relecture par l'IA des filtres et des items de contrôle** (étape 1) va avec la relecture des formulations déjà prévue pour l'ancienne v0.21 (plan-v0.20 § 11.4) : même page, même consigne de niveau 1, même banc. Elle est en 0.24.
- **Le pilote (0.26)** vérifie ce que 0.21 a prévu : un filtre qui laisse des « réponses présentes sous une condition fausse », une durée réelle loin de la durée estimée.
- **Les manquants (0.28)** supposent que le « non applicable » existe (0.21) : sinon, le portrait compterait comme manquante chaque question qu'une personne n'a pas eue.
- **Le niveau « résultats à publier » (0.27)** ne dépend que de ce qui existe : le carnet et ses confirmations (D-089, D-100), l'ébauche (D-106) et le lecteur de statistiques du vérificateur (D-117, D-118).

---

## 5. Étape 1 (v0.21) — Filtres, ordre aléatoire, non applicable

Plan détaillé : [`plan-v0.21.md`](plan-v0.21.md).

- **Ce que l'outil produira** : la condition d'une question et d'une section, structurée (jamais un texte à interpréter) ; l'ordre aléatoire des questions d'une section, des énoncés d'une grille, des choix d'une question ; les items de contrôle d'attention et leurs bonnes réponses ; la durée estimée de passation ; le tout écrit pour LimeSurvey, lu d'un `.lss`, dit dans le Word, le codebook et la Méthode. À l'arrivée de la base, le **non applicable**, distinct du manquant, pour chaque personne et chaque question filtrée.
- **Ce qu'il calcule** : les points de relecture (condition sur une question qui vient après, code inconnu, valeur hors des choix, cycle, condition jamais vraie…) ; pour chaque personne, si chaque question lui a été posée ; les anomalies (réponse présente sous une condition fausse), en agrégats ; les dénominateurs « posée à » ; la règle d'exclusion proposée pour les items de contrôle ; la durée estimée.
- **L'IA** : aucune dans cette version. En 0.24, au niveau métadonnées : relire la cohérence des filtres (une condition qui contredit le texte de la question : « Combien d'enfants ? » posée si « Avez-vous des enfants ? = Non »), proposer des items de contrôle (« pour cet énoncé, choisissez Plutôt d'accord »), proposer une traduction marquée **« proposition, non validée »**. Une traduction proposée n'est jamais une adaptation transculturelle : elle ne peut pas entrer dans une grille marquée instrument (la v0.21 prévue exigeait déjà une source dans la langue de l'étude pour une échelle traduite), et le Word de travail la marque.
- **Décisions** : D-165 à D-172 (plan-v0.21, § 12).
- **Risques** : la logique de LimeSurvey sur les valeurs vides et les questions non posées (une seule variable non posée rend toute l'expression fausse, même dans un « ou ») ; des réponses non posées et des réponses laissées vides que l'export ne distingue peut-être pas (à vérifier par l'auteur) ; la taille de la version (une douzaine d'étapes).

## 6. Étape 2 (v0.22) — Taille d'échantillon et puissance

Reportée en D-108 ; la taille d'échantillon reste aujourd'hui un texte du plan (`Plan.sample_size`).

- **Ce que l'outil produira** : sur la page « Plan », pour chaque hypothèse confirmatoire, le *N* nécessaire (ou la puissance atteinte pour un *N* donné, ou la plus petite taille d'effet détectable), à partir de son analyse, de α, de la puissance visée et d'une **taille d'effet tapée par l'équipe avec sa source** ; puis le *N* à recruter, gonflé par les exclusions attendues et, pour deux vagues, par l'attrition attendue, toutes deux tapées avec leur source. Le texte du plan, du préenregistrement (question « Sample size » d'OSF Prereg, « Sample size rationale ») et de la Méthode, par gabarit.
- **Ce qu'il calcule** : les tests de la v0.9 et de la v0.14 dont la puissance a une forme connue : *t* indépendant et apparié, corrélation (transformation de Fisher), ANOVA à un facteur, khi-carré, régression (*f*² d'un prédicteur ou du modèle) ; statsmodels, déjà installé (`statsmodels.stats.power`), sans nouvelle dépendance ; vérifié contre `power.t.test`, `power.anova.test` et `power.prop.test` de R de base, et contre des formules écrites à la main. Pour une famille corrigée par Holm, la puissance au α de Bonferroni de la famille (prudente), dite comme telle. Les analyses sans forme simple (régression logistique, modération, mesures répétées avec sphéricité) disent « pas de calcul de puissance dans l'outil » plutôt qu'une approximation.
- **L'IA** : aucune en 0.22. En 0.24, au niveau métadonnées : **relever une taille d'effet dans un article déposé**, avec sa page, vérifiée mot pour mot (D-147), et chacun de ses nombres lu dans l'extrait ; le calcul fait le *N*. C'est un prolongement de D-143, qui ne nomme pas les tailles d'effet : il faudra une décision à part.
- **Décisions** : la taille d'effet, champ humain sourcé comme un seuil (règle 4) ; aucune valeur par défaut, pas même « moyen » de Cohen (les conventions de Cohen, 1988, restent un choix possible de l'équipe, avec cette source) ; la puissance visée tapée, comme α ; la correction appliquée au calcul.
- **Risques** : une taille d'effet tirée d'une petite étude publiée est souvent surestimée : la page le dit en une phrase, sans juger le choix ; un calcul approché présenté comme exact (d'où le refus des analyses sans forme simple).

## 7. Le dossier d'étude (v0.23)

L'ancienne v0.19, jamais planifiée. Hypothèses de plan-v0.20 § 5.4 : un dossier d'étude, `etude.json` qui nomme ses projets, un sous-dossier `instruments/`, un parcours « Nouvelle étude » qui accueille « Concevoir un questionnaire ».

- **Ce qu'il apporte à ce cycle** : la place du pilote et de l'étude principale, de la vague 1 et de la vague 2 (des projets d'une même étude) ; les dossiers que décrit le plan de gestion des données ; le nom des fichiers d'une étude (D-161) ; `instruments/` pour les sources ; la fiche éthique, qui rejoint le Word pour le comité.
- **L'IA** : aucune.
- **Décision à prendre en son temps** : l'arborescence, et ce que devient un projet existant qu'on range dans une étude (rien n'est déplacé sans demande).

## 8. Les sources (v0.24, l'ancienne v0.21)

Plan-v0.20 § 11, décisions D-143, D-144 et D-147, inchangées sauf leur numéro de version. S'y ajoutent, parce qu'ils partagent la même mécanique (une source déposée, des pages choisies, la vérification mot pour mot) :

- la taille d'effet relevée dans un article (§ 6) ;
- la relecture des filtres et les items de contrôle proposés (§ 5) ;
- la traduction proposée d'une question propre à l'étude (§ 5).

Si la version devient trop lourde, ces trois ajouts passent en 0.24.1.

## 9. Étape 3 (v0.25) — Base désidentifiée et plan de gestion des données

- **Ce que l'outil produira** :
  - **la base à partager**, une copie (comme la copie documentée, D-026, l'original jamais touché) d'où sont retirés les identifiants et les textes libres, où les dates sont ramenées au mois ou à l'année, et où les quasi-identifiants choisis par l'équipe sont regroupés (par les recodages de D-120 : classes d'âge, petites catégories réunies) ou plafonnés ; avec son codebook et ses fichiers de commandes ;
  - **le rapport de risque de réidentification**, en agrégats seulement : sur les quasi-identifiants choisis, le nombre de combinaisons portées par moins de *k* personnes (*k*-anonymat), avant et après chaque traitement ;
  - **le plan de gestion des données**, en Word, par gabarit (les rubriques du modèle de l'Alliance de recherche numérique du Canada, à confirmer), rempli de ce que l'outil sait (formats, codebook, décisions de désidentification, dossiers du dossier d'étude, conservation) et de trous pour le reste.
- **Ce qu'il calcule** : le *k*-anonymat et les combinaisons uniques (pandas, sans nouvelle dépendance), vérifiés sur une base fictive aux combinaisons plantées ; la comparaison avec `sdcMicro` (R, GPL-2, exécuté par l'utilisateur, jamais distribué) reste un essai.
- **L'IA**, au niveau métadonnées, à partir du protocole déposé (sources de 0.24) : proposer les rubriques du plan de gestion, la lettre d'information et le formulaire de consentement **en langage simple**. Ce sont des propositions, marquées comme telles jusque dans le Word ; aucune n'est un texte juridique validé, et la page le dit (le comité et le gabarit de l'établissement font foi).
- **Décisions** : les quasi-identifiants (humains, jamais devinés : le classement de confidentialité les propose comme aujourd'hui) ; le *k* (tapé avec sa source, comme un seuil) ; les textes libres jamais dans la base partagée par défaut ; le gabarit du plan de gestion.
- **Risques** : un faux sentiment de sécurité (le *k*-anonymat ne protège pas de tout ; le rapport le dit en une phrase) ; une base partagée qui contredit le formulaire de consentement (le plan de gestion rappelle ce que les personnes ont accepté, tapé par l'équipe).

## 10. Étape 4 (v0.26) — Le suivi de la collecte et le pilote

- **Ce que l'outil produira** :
  - **le suivi** : à chaque export partiel lu, des indicateurs de déroulement seulement : réponses reçues par jour, complètes et partielles, abandons par page (`lastpage` de LimeSurvey), durée médiane, échecs aux items de contrôle, anomalies de filtres, *N* atteint contre le *N* visé (0.22) ; pour la vague 2, combien de personnes de la vague 1 ont répondu, par appariement des codes, sans jamais garder les codes ;
  - **le pilote** : un projet marqué « pilote » dans l'étude, et son rapport : manquants par item, filtres qui se comportent mal, durée réelle contre durée estimée (qui recalibre le repère de 0.21), items sans variance, effets plancher et plafond, items de contrôle trop durs ou trop faciles ; ce qui change entre le questionnaire pilote et le questionnaire final, par les différences de version de D-150.
- **Ce qu'il calcule** : des agrégats seulement, rien de gardé d'un export à l'autre que ces agrégats et leur date.
- **L'IA** : aucune.
- **Décisions** : **aucune statistique de résultat pendant la collecte** (ni moyenne d'une variable dépendante, ni test) : regarder ses résultats en cours de route, c'est l'arrêt optionnel, qui fausse les *p* ; le suivi ne montre que le déroulement. Le pilote est un projet à part, ou des personnes retirées de la base principale par une règle : à trancher.
- **Risques** : un export partiel qui écrase la base du projet (le carnet est lié à l'empreinte d'une base, D-091 : le suivi ne crée pas de carnet) ; un suivi qui glisse vers les résultats.

## 11. Étape 5 (v0.27) — Le niveau « résultats à publier »

La décision de principe est prise par l'auteur ; le texte proposé pour le journal, la règle 3 et la conception, et mes objections, sont au § 13.

- **Ce que l'outil produira** : pour un document activé (Discussion, résumé vulgarisé, retour aux participants, affiche), le message construit à partir des statistiques de l'ébauche, montré mot pour mot dans « Ce qui part », la proposition de l'IA, et la vérification de chacun de ses nombres ; la **fiche pour le comité d'éthique** (Word, français et anglais).
- **Ce qu'il calcule** : ce qui part (et seulement cela), le masquage, la vérification des nombres de la réponse contre ce qui est parti.
- **Décisions** : D-163 (§ 13) ; puis, dans le plan de la version, le schéma de chaque document et sa consigne.
- **Risques** : § 13.4.

## 12. Étape 6 (v0.28 à v0.32) — Ensuite

| Version | Ce que l'outil produira | Calcul | IA | À décider | Risque |
|---|---|---|---|---|---|
| **0.28** Vagues et manquants | Appariement des vagues par un code (D-052 existe pour les décisions ; ici les personnes), base réunie en format large ou long, attrition décrite ; portrait des manquants par variable, par personne et par motif ; test MCAR de Little | pandas et numpy (estimation EM de la moyenne et de la covariance), vérifié contre une formule écrite à la main et, en essai, `naniar::mcar_test` | aucune | Le code d'appariement (jamais gardé dans le projet) ; ce qui se dit dans la Méthode | Un test de Little lu comme une preuve de MCAR : la phrase de gabarit dit « ne permet pas de rejeter » |
| **0.29** Réponses ouvertes | Une grille de codage (catégories et définitions), le codage **fait par une personne, sur le poste**, réponse par réponse ; accord entre deux codeurs (kappa) ; les variables codées entrent au codebook ; « Autre, précisez » recodé dans les choix existants | Kappa de Cohen, effectifs des catégories (masqués sous 5 dans les exports) | Métadonnées : une grille proposée à partir du **texte de la question seulement**, jamais d'une réponse | La grille est une proposition ; les réponses ne quittent jamais le poste | Une grille trop pauvre faute d'avoir vu les réponses : l'équipe la complète en codant |
| **0.30** Moteur R facultatif | Oméga, AFC, invariance de mesure entre groupes ou vagues, imputation multiple | R de l'utilisateur, appelé par l'outil seulement s'il est installé (D-071 l'avait prévu) ; `lavaan`, `semTools`, `mice` (licences à vérifier) | aucune | Le moteur R : appelé par l'outil, ou script seulement ; ce qui se passe sans R | Une dépendance lourde et des versions de paquets qui changent les résultats : version notée dans le carnet |
| **0.31** Rédiger et déposer | Analyses de sensibilité (une analyse refaite sans une règle d'exclusion, avec et sans imputation) gardées au carnet comme variantes ; la liste JARS-Quant de l'APA, cochée par ce que l'outil sait déjà, et ses trous ; déclaration d'usage de l'IA tirée du dossier des envois ; rôles CRediT tapés ; réponse aux évaluateurs | Calcul pour la liste JARS et la déclaration d'usage de l'IA (je recommande **le calcul, sans IA**, pour ces deux-là : tout est déjà dans le projet et le dossier des envois) | Réponse aux évaluateurs : les commentaires des évaluateurs sont des métadonnées, mais la réponse parle des résultats, donc **niveau « résultats à publier »**, un document de plus à activer | Où vit la réponse aux évaluateurs (un document du projet ?) | Une déclaration d'usage de l'IA incomplète : elle ne connaît que les envois de l'outil, et le dit |
| **0.32** Conserver | Paquet de conservation (formats ouverts, empreintes, codebook, DDI Codebook 2.5 en XML) ; durée de conservation tapée | Écriture déterministe du DDI, validée contre le schéma XML officiel | aucune | La version de DDI (Codebook 2.5 ou Lifecycle) | Un schéma DDI vaste : seul ce que l'outil sait est écrit, le reste omis |

---

## 13. La décision du niveau « résultats à publier » (proposition)

L'auteur a pris la décision de principe (ses points sont repris tels quels). Voici le texte que je propose de consigner, puis les formulations, les tests et mes objections. **Rien n'est encore écrit au journal, au `CLAUDE.md` ni à la conception** : je le fais une fois le texte validé.

### 13.1 Texte proposé pour le journal

```markdown
### D-163 — Un second niveau d'envoi : les résultats à publier

- **Date :** 2026-10-20
- **Statut :** adoptée
- **Remplace :** D-134 (en partie : « pas même agrégé », pour les documents activés de ce niveau seulement)
- **Décision :** Un second niveau d'envoi vers l'IA, « résultats à publier », s'ajoute au niveau des métadonnées (D-136, inchangée pour ses quatre usages). Il est activé document par document (la Discussion, un résumé vulgarisé, un retour aux participants, une affiche…), pour un projet qui permet déjà l'IA (D-138), toujours désactivé par défaut ; chaque activation garde sa date et une raison facultative (« comité consulté le … »), et se retire. Il ne transmet que les statistiques qui figureront dans l'article : celles que l'outil écrit lui-même dans l'ébauche, à partir des analyses retenues et confirmées du carnet, avec les phrases, tableaux et notes qui les portent ; jamais un tableau brut, une valeur observée d'une variable, un minimum ou un maximum, un texte libre, un identifiant, une figure ou ses points, ni une analyse non retenue, et rien tant qu'un chiffre du carnet attend sa confirmation. Toute cellule de moins de 5 (le seuil réglable de D-006) est masquée : un effectif, un pourcentage dérivé, une case de tableau croisé, une étape du diagramme de flux, et toute statistique calculée sur moins de 5 personnes ; une cellule qui se retrouverait par soustraction est masquée aussi. Le message est montré mot pour mot dans « Ce qui part » avant chaque envoi et gardé dans le dossier des envois. L'outil produit par le calcul une fiche pour le comité d'éthique (Word, français et anglais). Ce que l'IA rend est une proposition (règle 5) ; tout nombre de sa réponse doit figurer dans ce qui est parti, sinon il est signalé et la proposition ne peut être acceptée telle quelle.
- **Options considérées :**
  1. Un second niveau, activé document par document, limité aux statistiques de l'ébauche (ce choix).
  2. Le niveau des métadonnées seulement (D-136) : l'IA rédige autour de renvois (`{{A3.t}}`) sans voir les chiffres.
  3. Un niveau ouvert à tous les agrégats du profil, comme le banc (codes observés, proportions).
- **Justification :** Décidé par l'auteur le 2026-10-20. Une Discussion, un résumé vulgarisé ou un retour aux participants ne s'écrivent pas sans les résultats ; ces statistiques sont destinées à être publiées, et rien n'en part qui ne serait pas dans l'article. L'option 2 donne des textes qui ne peuvent pas dire ce que les chiffres montrent. L'option 3 ferait partir ce que l'article ne publiera jamais. L'activation par document laisse au comité d'éthique un périmètre exact à approuver.
- **Conséquences :** La règle 3 du `CLAUDE.md` et le principe 5 de la conception sont reformulés, avec une ligne du tableau des garanties ; la règle 2 nomme la seconde source autorisée de la porte de confidentialité. Une seule fonction construit les messages de ce niveau, à partir de l'ébauche, jamais de la base. Codé à l'étape 5 de la feuille de route du cycle (v0.27) ; d'ici là, rien ne change dans l'outil.
- **Références :** `docs/feuille-de-route-cycle.md`, § 11 et 13 ; D-006, D-089, D-100, D-117, D-118, D-134, D-136, D-138.
```

### 13.2 Les formulations proposées

**`CLAUDE.md`, règle 3** (nouvelle formulation ; ce qui change est en gras) :

> 3. **Aucune donnée de participant ne quitte le poste.** L'IA est un service externe, activé explicitement projet par projet, qui ne reçoit que des métadonnées (le questionnaire et le codebook), jamais rien de ce que les participants ont répondu, pas même agrégé (D-134, D-136). **Une seule exception, le niveau « résultats à publier » (D-163) : pour un document activé un par un (Discussion, résumé vulgarisé, retour aux participants, affiche…), partent aussi les statistiques que l'outil écrit lui-même dans l'ébauche, à partir des analyses retenues et confirmées, cellules de moins de 5 masquées ; jamais une valeur observée, un minimum ou un maximum, un texte libre, un identifiant, une figure ni une analyse non retenue. Tout nombre de la réponse doit figurer dans ce qui est parti.** Le client IA n'accepte qu'une adresse en HTTPS (ou une adresse de cet ordinateur), sans proxy ni redirection ; la clé d'API reste dans le gestionnaire d'identifiants de Windows, jamais ailleurs (D-137). Les tests bloquent le réseau (pytest-socket), sauf les tests `externe` (D-139). Streamlit écoute sur 127.0.0.1, télémétrie désactivée.

**`CLAUDE.md`, règle 2** (une précision, sinon elle contredirait la règle 3) :

> 2. **Le modèle ne reçoit jamais de données individuelles.** Tout message destiné au modèle est construit par la porte de confidentialité (module `privacy`) à partir du profil agrégé **ou, pour le niveau « résultats à publier », des statistiques de l'ébauche (D-163)**, jamais à partir du tableau. Aucune valeur de texte libre ni d'identifiant probable ; effectifs < 5 masqués (D-006).

**`CONCEPTION.md`, principe 5** (phrase ajoutée après « pas même agrégés ») :

> Une seule exception, le niveau « résultats à publier » (D-163) : pour un document activé un par un, en plus des métadonnées, les statistiques que l'outil écrit lui-même dans l'ébauche, à partir des analyses retenues et confirmées, cellules de moins de 5 masquées ; tout nombre de la réponse doit se retrouver dans ce qui est parti.

**Ligne ajoutée au tableau « Comment le code garantit ces principes »** (sous la ligne 5) :

> | 5 (résultats à publier) | Une seule fonction construit ces messages, à partir de l'ébauche que l'outil écrit lui-même (`notebook_export`), jamais de la base ni du profil ; elle refuse un document non activé, un projet non permis (D-138) et un carnet qui attend une confirmation. Le masquage est appliqué dans cette fonction, cellules retrouvables par soustraction comprises, avant l'aperçu comme avant l'envoi : l'aperçu montre exactement ce qui part. Chaque nombre de la réponse est lu par le lecteur de statistiques du vérificateur (D-117) et par une recherche de tout chiffre, puis comparé à ce qui est parti ; un nombre absent fait signaler la proposition, qui ne peut alors être acceptée telle quelle. Des tests à chaînes témoins vérifient qu'une cellule de 4, une analyse non retenue, une valeur observée et un texte libre n'entrent dans aucun message, et qu'un document non activé n'envoie rien. |

### 13.3 Les tests à chaînes témoins, le moment venu

Sur une base fictive faite pour eux (graine fixe), avec un carnet retenu et confirmé :

1. **Une cellule de 4 ne part jamais.** Une catégorie de Tableau 1 portée par exactement 4 personnes, nommée par une étiquette témoin, dans un effectif qui rend son pourcentage reconnaissable (4 sur 347 : « 1,2 % ») ; une case de 4 dans un tableau croisé ; une règle d'exclusion qui retire 4 personnes. Aucun message ne contient l'effectif, le pourcentage ni l'étape exacte ; chacun dit « < 5 ». Et la soustraction ne les rend pas : quand une seule case d'une ligne est masquée, une seconde l'est aussi (ou le total), et le test recalcule la case masquée à partir de tout ce qui est parti sans y parvenir.
2. **Une statistique sur moins de 5 personnes ne part jamais.** La moyenne d'un sous-groupe de 3 personnes : absente.
3. **Une analyse non retenue ne part jamais.** Une entrée du carnet non retenue, au libellé témoin et à la statistique témoin (*t* = 7,777) : ni l'un ni l'autre dans aucun message.
4. **Un document non activé n'envoie rien.** Avec un faux client qui compte ses appels : zéro appel, rien au dossier des envois ; l'aperçu reste permis et dit « non activé ». Même chose pour un projet qui ne permet pas l'IA (D-138) avec un document activé, et pour un carnet qui attend une confirmation.
5. **Rien de la base.** Une valeur maximale témoin (987,654) d'une variable décrite au Tableau 1, une phrase témoin d'un texte libre, un identifiant témoin, les points d'un nuage : absents de tout message.
6. **Un nombre inventé est signalé.** Une fausse réponse qui écrit « *r* = ,41 » quand ,38 est parti, puis « 12 % de plus » (un nombre dérivé), puis « trois cent quarante » en lettres : chacun signalé, et l'acceptation telle quelle refusée.
7. **Ce que montre « Ce qui part » est ce qui part.** L'aperçu et l'envoi d'un faux client, octet pour octet.

### 13.4 Mes objections, avant de consigner

1. **D-136 n'est pas touchée, mais D-134 l'est.** D-136 ne parle que des quatre usages d'aujourd'hui, qui restent au niveau des métadonnées : elle reste vraie. D-134, elle, dit « jamais rien de ce que les participants ont répondu, pas même agrégé » : une statistique de l'article est un agrégat de ce qu'ils ont répondu. Le journal doit donc dire honnêtement « Remplace : D-134 (en partie) » ; c'est ce que fait le texte du § 13.1. Formulé comme une simple précision de D-136, il donnerait au comité une lecture fausse de la règle.
2. **Le masquage d'une case ne suffit pas : la soustraction la retrouve.** Un Tableau 1 qui donne 347 personnes, « Femme 201 » et « Homme 142 » laisse lire « Autre < 5 » = 4. Pareil pour le diagramme de flux (*N* reçu, *N* analysé et toutes les étapes sauf une). Il faut un **masquage secondaire** : quand une seule case d'une ligne, d'une colonne ou d'un flux est masquée, en masquer une seconde (la plus petite) ou le total. Je l'ai mis dans le texte proposé ; dites-moi si vous le voulez.
3. **Moins de 5 personnes, ce n'est pas qu'un effectif.** Une moyenne ou un écart-type calculés sur 3 personnes (un sous-groupe, une cellule d'ANOVA) en disent presque autant qu'une valeur individuelle. Je propose de masquer **toute statistique calculée sur moins de 5 personnes**, pas seulement les effectifs ; c'est aussi dans le texte proposé.
4. **« Tout nombre de sa réponse » demande plus que le lecteur du vérificateur.** Le lecteur de D-117 ne lit un nombre qu'après un symbole connu (*t*, *p*, *M*…). Une Discussion écrit aussi « deux hypothèses », « 12 % de plus », « trois fois plus », des années (« depuis 2020 »), des pages. Je propose : (a) le lecteur de statistiques pour les statistiques ; (b) en plus, **tout chiffre** de la réponse doit se retrouver dans ce qui est parti (virgule ou point décimal, zéro initial, espaces fines normalisés) ; (c) les nombres en lettres d'une liste fermée (un à vingt, cent, mille…) sont signalés s'ils ne correspondent à rien parti ; (d) un nombre dérivé (« 12 % de plus ») est signalé même juste, car c'est un calcul de l'IA que l'outil n'a pas fait. Les années d'une référence posent la question de la règle 4 : l'IA ne cite que la bibliographie de l'équipe, et tout ce qui ressemble à une citation est déjà signalé (§ 6.4 de la conception).
5. **Les figures.** Une affiche, c'est surtout des figures, et une figure est dessinée à partir de la base (un nuage de points montre chaque personne). Je propose que **rien d'une figure ne parte**, ni l'image ni ses points ; l'IA ne reçoit que le titre et la note de la figure, et propose le texte de l'affiche ; les figures restent celles de l'outil.
6. **Les chiffres non confirmés.** Si le carnet attend une confirmation (D-089, D-100), l'ébauche n'est pas exportable ; le message ne doit pas partir non plus, sinon l'IA écrirait sur des chiffres qu'aucune personne n'a vus. C'est dans le texte proposé.
7. **Ce qui n'est pas de la confidentialité, mais compte pour le comité.** Des résultats non publiés envoyés à un fournisseur posent une question d'embargo et de propriété intellectuelle, distincte de la vie privée ; et le fournisseur garde les messages un certain temps. La fiche pour le comité doit dire la durée de conservation du fournisseur configuré (la page « IA » la dit déjà, D-134) et que l'équipe reste responsable de l'accord de ses coauteurs.
8. **Un document « retour aux participants » parle à des participants.** Le masquage protège le message envoyé à l'IA ; mais le texte rendu sera lu par les personnes de l'étude, dans une petite communauté parfois. La relecture humaine reste la seule garantie ; la page peut rappeler de vérifier qu'aucun groupe de moins de 5 n'y est décrit, ce que le contrôle des nombres fait déjà en partie.
9. **Le nom.** Je recommande « résultats à publier » partout (interface, fiche, journal), jamais « niveau 2 », pour ne pas confondre avec le niveau 2 du banc (D-136), qui reste interdit.

Aucune de ces objections ne remet en cause la décision ; les points 2, 3, 5 et 6 la resserrent et sont déjà dans le texte proposé, à retirer si vous ne les voulez pas.

---

## 14. Risques de l'ensemble

- **Une feuille de route longue** (douze versions) : chaque version reste utile seule, et l'ordre peut changer après 0.22 sans rien casser, sauf les dépendances du § 4.
- **Les numéros qui bougent** : la proposition du § 3 évite d'en réserver d'avance ; les documents qui parlent de « v0.21 » pour les sources (conception § 25, plan-v0.20 § 11, D-143) sont mis à jour à la première étape de la v0.21 (le journal par une nouvelle entrée, D-164, jamais en modifiant les anciennes).
- **L'IA qui s'étend** : chaque usage nouveau a sa consigne, son schéma strict, son banc sur des données fictives et son test à chaînes témoins, comme en v0.18 ; chaque usage au niveau « résultats à publier » est un document de plus à activer.
- **Deux langues à entretenir** : chaque gabarit nouveau (puissance, non applicable, plan de gestion, fiche éthique) existe en français et en anglais dès son étape.

## 15. Ce que l'auteur valide maintenant

1. L'ordre des étapes et la numérotation du § 3 (D-164) : 0.21 filtres, 0.22 puissance, 0.23 dossier d'étude, 0.24 sources, puis 0.25 à 0.32.
2. La place du dossier d'étude avant les sources, et des usages de l'IA de l'étape 1 et de la puissance dans la version des sources (§ 4, § 8).
3. Le texte de D-163 (§ 13.1), les formulations du § 13.2 et la réponse à mes objections (§ 13.4).
4. Les recommandations « calcul plutôt qu'IA » pour la liste JARS et la déclaration d'usage de l'IA, et « résultats à publier » pour la réponse aux évaluateurs (§ 12).
5. Le plan de la v0.21 ([`plan-v0.21.md`](plan-v0.21.md)) et ses décisions D-165 à D-172.
