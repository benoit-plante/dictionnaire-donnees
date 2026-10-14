# Plan de la v0.4

> Statut : **proposé**, à valider par l'auteur (décisions du § 6).

## 1. Pourquoi cette version

Jusqu'ici, l'outil **décrit** une base : le codebook dit ce que chaque variable veut dire, mais la base elle-même reste telle quelle. Les équipes doivent ensuite reporter à la main, dans SPSS, R ou Stata, les libellés, les étiquettes de valeurs et les codes manquants qu'elles viennent de valider. C'est long, et c'est là que les erreurs reviennent.

Deux constats des essais s'ajoutent :

- **Le choix du modèle se fait à l'aveugle.** Les essais ont été faits avec un seul modèle (qwen2.5 7B), sur une base fictive et une base publique. Une équipe sans carte graphique voudra peut-être un modèle plus petit ; rien ne lui dit ce qu'elle y perd.
- **La révision des rattachements est longue sur une grande base** (152 variables pour la base publique), alors que l'essai de l'étape 4 de la v0.2 montrait que les rattachements où le modèle et le calcul s'accordent sont presque toujours justes.

## 2. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Fichiers de commandes** (syntaxe SPSS `.sps`, script R, fichier Stata `.do`) qui appliquent aux données de l'équipe les décisions acceptées : libellés, étiquettes de valeurs, codes manquants, niveaux de mesure | Les décisions passent du codebook aux données, dans le logiciel de l'équipe, sans que l'outil écrive de données |
| B | **Codes manquants confirmés** : un code sentinelle repéré (999, −9) devient « manquant » quand une personne le confirme | Ce qui manquait aux fichiers de commandes, et une décision qu'on prend aujourd'hui hors de l'outil |
| C | **Copie documentée du `.sav`**, facultative : une nouvelle copie de la base avec les métadonnées acceptées, données identiques | Pour les équipes qui veulent un fichier prêt à l'emploi ; l'original n'est jamais modifié |
| D | **Banc d'essai des modèles** : une seconde base fictive avec son corrigé, et une page qui mesure un modèle installé (rattachements justes, inventions signalées, durée) | Choisir son modèle en connaissance de cause, sur son propre ordinateur |
| E | **Décisions groupées**, avec aperçu : accepter d'un coup les rattachements où le modèle et le calcul s'accordent, ou les étiquettes de valeurs d'un même groupe | Moins de clics sur une grande base, sans décision invisible |

**Pas de recodage des valeurs**, même sur une copie. Inverser des items, regrouper des variantes d'écriture ou remplacer des codes changent les données elles-mêmes : c'est une analyse, que l'équipe fait et documente dans son propre logiciel. Les fichiers de commandes peuvent en revanche **proposer en commentaire** le recodage des items inversés confirmés, sans l'exécuter.

**Reportés** : installateur pour macOS et Linux (l'outil y fonctionne déjà par la ligne de commande) ; interface en anglais.

## 3. Conception

### 3.1 Fichiers de commandes (A)

- Produits par la page « Export », à côté du codebook, et par `ddict exporter --syntaxe`. Un fichier par logiciel : `etude-sommeil-metadonnees.sps`, `.R`, `.do`.
- Ils ne contiennent **que des décisions acceptées** : libellés, étiquettes de valeurs (du fichier ou acceptées), codes manquants déclarés ou confirmés, niveaux de mesure. Rien de proposé, rien de calculé qui ne soit une décision, aucune valeur de participant.
- En tête, des commentaires disent d'où vient chaque fichier (projet, date, version de l'outil) et rappellent de l'appliquer à une copie.
- Le texte des libellés est échappé pour chaque langage (apostrophes, guillemets, accents), et chaque fichier déclare son encodage (UTF-8).
- **Vérification** : le script R est exécuté dans les tests de développement avec R et haven, déjà installés sur le poste de l'auteur, sur la base fictive, et le résultat relu par pyreadstat. Ni SPSS ni Stata ne sont disponibles : la syntaxe SPSS sera vérifiée avec **PSPP** (logiciel libre, GNU GPL), un outil de développement à installer (D-027), et le fichier Stata par sa forme seulement, puis par l'auteur ou un collègue qui a Stata.

### 3.2 Codes manquants confirmés (B)

- Sur la fiche d'une variable, chaque code sentinelle repéré (« Valeur 999 probablement manquante, non déclarée ») reçoit les boutons « C'est un code manquant » et « C'est une vraie valeur ».
- La décision est une valeur suivie de plus dans le fichier projet (origine calcul, décision humaine), comme les autres. Elle n'est jamais proposée par l'IA.
- Les statistiques du profil ne changent pas (elles décrivent le fichier tel qu'il est) ; le codebook dit « code manquant confirmé par l'équipe ».

### 3.3 Copie documentée du `.sav` (C)

- Seulement pour une base `.sav`, ou sur demande pour une base CSV, Stata ou Excel (la copie est alors un `.sav`).
- Écrite à côté de l'original sous un nouveau nom (`etude-sommeil-documente.sav`) ; si ce nom existe, l'outil ne l'écrase pas sans le demander. L'original n'est jamais ouvert en écriture.
- **Données identiques** : avant d'annoncer la copie, l'outil la relit et compare chaque cellule avec l'original ; au moindre écart, la copie est supprimée et l'outil le dit.
- C'est la première fois que l'outil écrit des données de participants. Elles restent sur l'ordinateur, à côté de l'original, et rien d'elles n'entre dans le projet ni ne va au modèle (D-026).

### 3.4 Banc d'essai des modèles (D)

- **Une seconde base fictive**, différente de l'étude sur le sommeil pour ne pas mesurer un modèle sur ce qui a servi à régler l'outil : par exemple une enquête fictive auprès de familles, en CSV sans étiquettes, avec des questions répétées (une par membre de la famille), plusieurs questions à cocher, des scores calculés et des sigles. Générée par script, avec son questionnaire PDF et son corrigé (question de chaque variable, sigles, ordre des codes).
- **Une page « Banc d'essai »** dans l'interface, et `ddict evaluer --modele …` : sur les deux bases fictives, l'outil mesure pour un modèle installé les rattachements justes, les libellés qui inventent (signaux : citation, seuil, instrument, sigle, étendue), les sens de codes inventés et la durée. Le résultat est un petit rapport, enregistré dans un dossier choisi.
- Rien n'est téléchargé par l'outil : la page mesure les modèles qu'Ollama a déjà (D-023).
- L'essai de la version compare qwen2.5 7B, mistral 7B (déjà installés) et, si l'auteur accepte de le télécharger, un petit modèle pour ordinateur sans carte graphique (environ 2 Go).

### 3.5 Décisions groupées (E)

- Sur la page « Variables », un bouton « Accepter les rattachements où le modèle et le calcul s'accordent » ouvre d'abord la **liste exacte** des variables concernées, avec la question de chacune ; on peut en décocher ; puis « Accepter ces N rattachements ».
- De même pour les étiquettes de valeurs d'un même groupe d'items (toutes les variables d'une échelle partagent souvent les mêmes options).
- Chaque décision reste enregistrée une par une, avec sa date, comme si elle avait été prise à la main ; rien n'est accepté sans avoir été montré.

## 4. Étapes

Une étape à la fois, avec ses tests, et un arrêt pour revue à la fin de chacune.

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Seconde base fictive (CSV, questionnaire PDF, corrigé), générée par script | Fichiers reproductibles à l'identique ; pièges décrits dans le README des exemples |
| 2 | Codes manquants confirmés (modèle, interface, codebook) | Décision enregistrée et exportée ; jamais proposée par l'IA (test) |
| 3 | Fichiers de commandes R, SPSS et Stata | Le script R appliqué à la base fictive CSV redonne les métadonnées du `.sav` (test, avec R) ; la syntaxe SPSS passe dans PSPP |
| 4 | Copie documentée du `.sav` | Données identiques cellule par cellule (test) ; l'original intact (empreinte) ; pas d'écrasement sans accord |
| 5 | Décisions groupées, avec aperçu | Seules les variables montrées et cochées sont décidées (test) ; essai sur la base publique : temps de révision consigné |
| 6 | Banc d'essai : mesure, page et commande | Rapport reproductible sur les deux bases fictives (avec un faux serveur dans les tests) |
| 7 | Essai de trois modèles, consigné dans `docs/essais/` | Comparaison publiée ; recommandation de modèle selon le matériel |
| 8 | Guide, scénario manuel, version 0.4.0 | Scénario refait dans le navigateur ; essai du guide par l'auteur, jusqu'au script R appliqué |

## 5. Risques

- **Écrire des données** (C) est un changement de nature : un bogue pourrait produire une copie fausse. D'où la comparaison cellule par cellule avant d'annoncer la copie, et la recommandation de préférer les fichiers de commandes.
- **Syntaxes de logiciels qu'on n'a pas** : SPSS et Stata ne sont pas disponibles pour les tests. PSPP couvre l'essentiel de la syntaxe SPSS ; pour Stata, un essai par une personne qui l'a sera demandé avant la version.
- **Sur-réglage** : l'outil a été réglé sur l'étude du sommeil et la base publique. La seconde base fictive (D) sert aussi à vérifier que le rattachement tient sur un questionnaire qu'il n'a jamais vu.
- **Décisions groupées** : le confort ne doit pas devenir de l'acceptation aveugle. L'aperçu obligatoire et la décoche individuelle sont la garde ; l'essai mesure aussi combien d'erreurs passent par ce bouton.

## 6. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-025 | **Périmètre de la v0.4** | A à E ; pas de recodage des valeurs ; installateur macOS et Linux et interface en anglais reportés. |
| D-026 | **L'outil écrit-il des données ?** | Oui, seulement une copie documentée du `.sav`, facultative, vérifiée cellule par cellule, jamais l'original. Les fichiers de commandes restent la voie recommandée : l'équipe applique les décisions dans son propre logiciel. |
| D-027 | **PSPP comme outil de développement** | Oui, pour vérifier la syntaxe SPSS (GNU GPL, installé sur le poste de développement seulement, comme R pour la base SAS). Ni l'outil ni ses tests ordinaires n'en dépendent : le test est sauté si PSPP manque. |
| D-028 | **Codes manquants confirmés** | Décision humaine seulement, à partir des codes sentinelles calculés ; jamais proposée par l'IA ; le profil n'est pas recalculé. |
| D-029 | **Décisions groupées** | Permises avec un aperçu obligatoire et une décoche possible, enregistrées une par une ; limitées aux rattachements où modèle et calcul s'accordent, et aux étiquettes de valeurs d'un même groupe. |
