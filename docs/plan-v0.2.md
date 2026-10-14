# Plan de la v0.2

> Statut : **validé par l'auteur le 2026-10-13**, avec toutes les recommandations du § 6 (D-011 à D-017).

## 1. Pourquoi cette version

L'essai de la v0.1.2 sur une base publique réelle (152 variables, exportée par R, avec son questionnaire SurveyMonkey) a montré que les limites restantes ne viennent plus de la lecture des fichiers, mais du **sens** des variables :

- le modèle devine mal les sigles : « OCF » devient « offices de contrôle », alors que le questionnaire dit « organismes communautaires Famille » ;
- il invente la signification des codes : « 1 = non, 2 = oui » pour une variable dont le CSV ne dit rien ;
- sans étiquettes dans le fichier (cas de tous les CSV), le texte exact des questions n'apparaît nulle part dans le codebook.

Le questionnaire répond à ces trois problèmes. La v0.2 en fait une **source documentée**, au même titre que le fichier de données. Le principe « aucune invention » s'applique toujours : ce qui vient du questionnaire est une citation exacte, vérifiée par l'outil, et l'IA ne fait que proposer des correspondances.

## 2. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Questionnaire** : lecture (PDF, texte), découpage en questions et options, rattachement aux variables | Le texte exact de chaque question dans le codebook ; un libellé fondé sur la question plutôt que sur le nom |
| B | **Glossaire** des sigles, saisi par l'équipe ou repéré dans le questionnaire | OCF, DPJ, CIUSSS compris par le modèle et expliqués dans le codebook |
| C | **Options de réponse → étiquettes de valeurs proposées**, sous une règle stricte | Le sens des codes 1, 2, 3 dans un CSV, à vérifier |
| D | **Variantes d'écriture** signalées (« Canada » / « canada », « Espagnol » / « Espanol ») | Aide au nettoyage, calculée sans IA |
| E | **Autres formats** : Stata (`.dta`), SAS (`.sas7bdat`), Excel (`.xlsx`) | Plus d'équipes peuvent s'en servir ; peu coûteux (pyreadstat et openpyxl déjà présents) |

**Reportés à la v0.3** : appliquer les décisions à une copie du `.sav` ; installateur Windows en un clic ; jeu de référence pour comparer les modèles. Ces trois chantiers sont utiles, mais indépendants du questionnaire, et la v0.2 est déjà substantielle.

## 3. Conception

### 3.1 Lecture et découpage du questionnaire (sans IA)

- Formats : PDF (exports de SurveyMonkey, LimeSurvey, REDCap) et texte brut (`.txt`, pour un questionnaire copié depuis Word). Le PDF demande une nouvelle dépendance, **pypdf** (BSD-3).
- Le texte est normalisé (espaces, ligatures comme « ﬁ », césures) puis découpé en **questions**, chacune avec son numéro de page et ses **options** de réponse. Repères : une ligne qui finit par « ? » ou « : », les consignes entre parenthèses (« Cochez toutes les réponses applicables »), les listes d'options qui suivent.
- Les grilles (échelles en tableau, comme le CBCL) se découpent mal dans un PDF : l'outil le reconnaît (lignes numérotées, réponses répétées) et les présente comme « grille, à vérifier » plutôt que de produire des questions fausses.
- Le résultat est enregistré dans le fichier projet : nom et empreinte du questionnaire, liste des questions avec leur identifiant (`Q12`), leur page, leur texte et leurs options. Les questions sont affichées dans l'interface pour vérification.
- Commande : `ddict questionnaire projet.dd.json questionnaire.pdf`.

### 3.2 Rattachement des variables aux questions (calcul, puis IA, puis personne)

Une variable correspond soit à une **question** (`freq_ocf` ↔ « Fréquentez-vous un ou des organismes communautaires famille ? »), soit à une **option** d'une question à cocher (`motifs_freq_ocf_repit` ↔ option « Répit parental »).

1. **Candidats calculés** : pour chaque variable, l'outil retient quelques questions candidates par ressemblance entre le nom (et le glossaire) et le texte des questions et options, ainsi que par l'ordre (les variables suivent en général l'ordre du questionnaire).
2. **Choix proposé par l'IA** : le modèle local reçoit, pour un bloc de variables, ses candidates seulement, jamais tout le questionnaire. Les petits modèles ont une fenêtre de contexte limitée, et un questionnaire de 27 pages (environ 8 000 jetons) ne tient pas dans un message. Le modèle répond par des **identifiants** (`Q12`, `Q12.o3` ou « aucune »), jamais par du texte.
3. **Texte garanti exact** : comme la réponse n'est qu'un identifiant, le texte affiché vient toujours du questionnaire lui-même ; l'IA ne peut pas en inventer.
4. **Décision humaine** : dans l'interface, chaque rattachement proposé s'accepte, se change (choix dans la liste des questions) ou se retire, comme un libellé.

Sans IA, les candidats calculés restent proposés à la personne, qui choisit. La chaîne fonctionne donc toujours sans modèle (principe 6).

### 3.3 Glossaire

- Une liste de sigles avec leur sens (« OCF = organismes communautaires Famille »), enregistrée dans le fichier projet, avec sa source pour chaque entrée.
- Deux sources seulement : **la saisie par l'équipe**, et **le repérage sans IA dans le questionnaire** du motif « forme longue (SIGLE) » (« organismes communautaires Famille (OCF) »), proposé puis validé par une personne.
- **L'IA ne propose jamais de définition de sigle** : c'est exactement là qu'elle invente.
- L'outil repère les sigles probables dans les noms de variables (`ocf`, `dpj`, `ciusss`) et signale ceux qui n'ont pas d'entrée.
- Les entrées utiles à un bloc sont jointes au message du modèle ; le glossaire complet figure dans le codebook (nouvel onglet).

### 3.4 Libellés et descriptions avec le questionnaire (prompt `variables-v3`)

Quand une variable est rattachée à une question validée, le modèle reçoit le texte de la question (et, pour une option, l'option) et les entrées du glossaire, et propose un libellé court tiré de ce texte. Un essai consigné dans `docs/essais/` compare v2 et v3 sur la base fictive et, en local seulement, sur la base publique.

### 3.5 Options de réponse → étiquettes de valeurs (règle stricte)

Une étiquette de valeur n'est proposée que si le rattachement est validé **et** que le nombre d'options égale le nombre de codes observés, ces codes étant consécutifs (1…n ou 0…n−1). L'ordre des options est alors supposé suivre celui des codes, ce qui est le cas habituel des plateformes d'enquête, mais n'est pas garanti : la proposition porte la mention « ordre supposé, à vérifier ». Dans tous les autres cas, rien n'est proposé.

### 3.6 Variantes d'écriture (sans IA)

Les catégories d'une variable de texte qui ne diffèrent que par la casse, les accents ou les espaces sont regroupées et signalées. Seules les catégories déjà visibles sont comparées : une catégorie rare masquée (D-006) n'est jamais révélée par ce signal, et les variables sensibles en sont exclues.

### 3.7 Confidentialité

Un questionnaire n'est pas une donnée de participant : son texte peut aller au modèle local. Deux précautions :

- une **page de consentement** contient souvent les noms et coordonnées de l'équipe de recherche. Ce ne sont pas des données de participants, mais ils n'ont rien à faire dans un codebook : l'outil n'exporte que les questions rattachées à des variables ;
- les **items d'instruments protégés** (CBCL, par exemple) sont soumis au droit d'auteur. Voir la décision D-014.

## 4. Étapes

Une étape à la fois, comme pour la v0.1, chacune avec ses tests, et un arrêt pour revue à la fin de chacune.

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Questionnaire fictif de l'étude sur le sommeil (`.txt` et `.pdf`), généré par script, avec ses pièges : question à cocher, grille, sigle défini, page de consentement fictive | Fichiers reproductibles à l'identique ; pièges décrits dans le README des exemples |
| 2 | Lecture et découpage du questionnaire, commande `ddict questionnaire` | Toutes les questions et options du questionnaire fictif retrouvées avec leur page ; la grille reconnue comme telle ; sur le PDF de la base publique, découpage vérifié à la main et consigné |
| 3 | Glossaire : modèle de données, repérage « forme longue (SIGLE) », sigles probables dans les noms, saisie dans l'interface | Les sigles du questionnaire fictif repérés ; aucune définition venant de l'IA (test) |
| 4 | Rattachement : candidats calculés, choix par l'IA, décision dans l'interface | Sur la base fictive : rattachements justes mesurés et consignés ; aucun texte de question qui ne soit pas dans le questionnaire (test) ; fonctionne sans IA |
| 5 | Prompt `variables-v3` (question et glossaire), essai v2 contre v3 | Essai consigné ; « OCF » correctement compris sur la base publique |
| 6 | Options → étiquettes de valeurs proposées (règle stricte) | Proposées seulement dans les cas prévus (tests des cas limites) |
| 7 | Variantes d'écriture | Signalées sur la base fictive enrichie d'un piège ; aucune catégorie masquée révélée (test) |
| 8 | Lecture `.dta`, `.sas7bdat`, `.xlsx` | Les versions Stata, SAS et Excel de la base fictive donnent le même profil que le `.sav` |
| 9 | Exports : texte des questions, glossaire, provenance du questionnaire | Codebook complet sur la base fictive ; rien de la page de consentement exporté (test) |
| 10 | Guide, scénario manuel, version 0.2.0 | Scénario refait dans le navigateur ; essai d'installation et d'utilisation avec un questionnaire |

## 5. Risques

- **Découpage des PDF** : chaque plateforme met en page à sa façon. La v0.2 vise SurveyMonkey (le cas réel dont on dispose) et le texte brut ; les autres plateformes s'ajouteront avec des exemples.
- **Fenêtre de contexte** des petits modèles : les messages sont gardés courts (candidats seulement) et leur taille est mesurée à l'étape 4.
- **Qualité du rattachement** : l'étape 4 mesure la part de rattachements justes ; en dessous d'un seuil jugé utile, l'IA n'est pas activée pour le rattachement et l'interface propose seulement les candidats calculés.

## 6. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-011 | **Périmètre de la v0.2** | A à E comme ci-dessus ; copie du `.sav` corrigée, installateur et jeu de référence en v0.3. |
| D-012 | **Statut du questionnaire** | Source documentée fournie par l'équipe : son texte est conservé dans le fichier projet et peut aller au modèle local ; seules les questions rattachées sont exportées. |
| D-013 | **Rattachement** | Candidats calculés, puis choix de l'IA par identifiant, puis décision humaine. Plutôt que tout laisser à l'IA (risque d'invention) ou tout faire à la main (152 variables, c'est long). |
| D-014 | **Items d'instruments protégés par le droit d'auteur** | Texte des questions exporté par défaut, avec une option pour l'omettre par groupe d'items (`--sans-texte G3`, et une case à cocher dans l'interface) ; le guide rappelle que reproduire les items d'un instrument protégé relève de l'équipe. |
| D-015 | **Glossaire** | Sources : l'équipe et le repérage sans IA dans le questionnaire ; jamais de définition proposée par l'IA. |
| D-016 | **Options → étiquettes de valeurs** | Proposées seulement sous la règle stricte du § 3.5, avec la mention « ordre supposé ». Autre choix possible : reporter cette fonction à la v0.3. |
| D-017 | **Nouvelle dépendance pypdf** (BSD-3) pour lire les PDF | Oui ; les fichiers Word (`.docx`) attendront, le texte copié dans un `.txt` les remplace. |
