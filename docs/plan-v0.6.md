# Plan de la v0.6

> Statut : **validé par l'auteur le 2026-10-14**, avec toutes les recommandations du § 6 (D-038 à D-042).

## 1. Pourquoi cette version

Relier chaque variable à sa question est l'étape qui demande le plus de révision, et celle où l'IA se trompe le plus. Le diagnostic des trois bases fictives (98 variables, corrigé connu) montre trois pertes :

| Cause | Exemples | Combien |
|---|---|---|
| **Variable sans question rattachée quand même** : identifiants et dates de passation reçoivent des questions candidates, et le modèle en choisit une | `date_passation` → « Quelle est votre date de naissance ? », `id_famille`, `participant_id` | 6 variables sur 98, dans les trois bases |
| **Aucune candidate** : la question n'emploie pas les mots du nom de la variable ; le modèle, qui choisit seulement parmi les candidates (D-013), ne peut pas la trouver | `age` (« How old are you? »), `height_cm` (« How tall are you? »), `n_awakenings` (« wake up ») | 3 variables (base anglaise) |
| **Le modèle défait un bon choix du calcul** | `sommeil_q7`, `soutien_partenaire`, `stress_total`, `sleep_q8` | au banc : calcul seul 88 / 98, modèle 81 / 98 |

À l'essai sur une vraie base (v0.4), environ une ligne sur cinq de la liste des décisions groupées était fausse, surtout pour les mêmes cas : variables sans question, scores calculés, options voisines.

## 2. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **« Aucune question » proposée par le calcul** quand des indices la rendent probable : identifiant probable, date de passation ou de réponse (dates récentes, sans question de date dans le questionnaire), score calculé (nom en « total », « score », « moyenne », membre d'aucune grille, ou somme d'items d'un groupe) | Les variables administratives ne sont plus rattachées à tort ; la décision reste à la personne |
| B | **Questions voisines** pour une variable sans candidate : les questions situées, dans l'ordre du questionnaire, entre les rattachements sûrs qui l'entourent (au plus 6) ; envoyées au modèle comme candidates « voisines », et montrées en tête de liste dans l'interface | « How old are you? » devient atteignable, par le modèle comme par la personne |
| C | **Le calcul garde la main quand il est sûr** : quand la première candidate est nettement en tête (règle déjà utilisée pour les ancres), le modèle la voit marquée « calcul sûr », et un désaccord du modèle est signalé plutôt que de remplacer silencieusement le choix du calcul | Moins de bons choix défaits ; les désaccords deviennent visibles |
| D | **Un banc d'essai plus parlant** : le rapport classe chaque rattachement manqué (sans candidate, bonne candidate mal choisie, variable sans question rattachée) | On sait ce qui reste à améliorer |
| E | **Une base de contrôle**, fictive, générée avant tout réglage et mesurée une seule fois à la fin | Vérifier que les gains ne viennent pas d'un réglage sur les trois bases du banc |

**Hors de cette version** : le dépôt des données (DDI, Frictionless), REDCap, la révision groupée des libellés, Linux ; la relecture de la traduction et l'essai sur un vrai Mac de la v0.5 restent en attente et peuvent se faire en parallèle (0.5.x).

## 3. Conception

### 3.1 « Aucune question » proposée (A)

- Le calcul ajoute la candidate « aucune question » **en tête** quand un indice fort la rend probable, et seulement alors ; sinon, elle reste en fin de liste, comme aujourd'hui.
- Indices : classe de confidentialité « identifiant probable » ; variable de type date dont les valeurs sont récentes (année de collecte) quand aucune question du questionnaire ne demande une date de ce genre ; score calculé (nom contenant `total`, `score`, `moy`, `mean`, `sum`, ou somme exacte des items d'un groupe, vérifiable sur les données au moment du profil).
- Le modèle la voit comme une candidate parmi les autres ; la règle du prompt sur « aucune » ne change pas.
- La somme des items se calcule au profilage, comme les autres statistiques ; seul le fait (« somme exacte des items du groupe G3 ») est gardé, jamais les valeurs.

### 3.2 Questions voisines (B)

- Pour une variable sans candidate, le calcul retient les questions situées entre la question de la variable sûre qui la précède dans le fichier et celle de la variable sûre qui la suit (les « ancres » existantes), au plus 6, dans l'ordre.
- Envoyées au modèle avec la mention `"neighbour": true` ; le prompt (link-v3, fr et en) explique qu'aucun mot ne les relie au nom de la variable et qu'il faut lire la question.
- Dans l'interface, elles apparaissent en tête de la liste « Rattacher à », sous un intertitre « Questions voisines ».

### 3.3 Le calcul garde la main quand il est sûr (C)

- Une candidate est « sûre » selon la règle des ancres déjà en place (score suffisant et nettement devant la deuxième).
- Le modèle reçoit `"computed": "sure"` pour cette candidate. S'il en choisit une autre, la proposition du modèle est gardée, mais un signal « désaccord avec le calcul » l'accompagne, et les décisions groupées (D-029) l'excluent déjà puisqu'elles exigent l'accord.
- Mesure : le nombre de bons choix du calcul défaits par le modèle, avant et après.

### 3.4 Base de contrôle (E)

- Une quatrième base fictive, différente des trois du banc (par exemple une étude fictive en français sur l'activité physique, avec questions reformulées, variables administratives et un score calculé), générée par script avec son corrigé **avant** les étapes A à C.
- Elle n'entre pas dans le banc pendant la mise au point ; elle est mesurée une seule fois, à la fin, pour la version précédente (0.5) et la nouvelle (0.6). Ensuite seulement, elle rejoint le banc.

## 4. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Base de contrôle et son corrigé, mise de côté ; mesure de la 0.5 sur elle | Fichiers reproductibles (test) ; résultat 0.5 consigné, sans réglage |
| 2 | Banc d'essai : classement des rattachements manqués | Rapport reproductible avec les trois catégories (test, faux serveur) |
| 3 | « Aucune question » proposée par le calcul | Les 6 variables sans question des bases du banc ont « aucune » en tête (test) ; aucune vraie question retirée de la tête |
| 4 | Questions voisines, prompt link-v3, interface | `age`, `height_cm`, `n_awakenings` ont leur question parmi les candidates (test) |
| 5 | Le calcul sûr signalé au modèle ; signal de désaccord | Banc avec qwen2.5 7B : moins de bons choix du calcul défaits |
| 6 | Mesure finale sur la base de contrôle et le banc, essai consigné | 0.6 meilleure que 0.5 sur la base de contrôle ; essai dans `docs/essais/` |
| 7 | Guide, journal des changements, version 0.6.0 | Scénario refait dans le navigateur |

## 5. Risques

- **Sur-réglage** : les trois bases du banc ont servi à régler l'outil depuis la v0.2. La base de contrôle, mise de côté dès l'étape 1, est la garde : si la 0.6 ne fait pas mieux sur elle, les changements sont revus.
- **« Aucune question » en tête à tort** : une vraie question rétrogradée serait une régression. Les indices sont stricts, la candidate reste une proposition, et un test vérifie qu'aucune variable du corrigé ayant une question ne la perd en tête.
- **Questions voisines trop nombreuses** : elles allongent les messages ; au plus 6, seulement pour les variables sans candidate.
- **Base publique** : les cas difficiles (questions répétées) ne sont pas visés ici ; une mesure de contrôle y est faite à l'étape 6, sans corrigé complet.

## 6. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-038 | **Périmètre de la v0.6** | Des rattachements plus complets (A à E) ; le reste reporté. |
| D-039 | **« Aucune question » proposée par le calcul** | Oui, en tête seulement sur indices forts ; la somme des items d'un groupe se vérifie au profilage et seul le fait est gardé. |
| D-040 | **Questions voisines hors des candidates calculées** | Oui, pour les variables sans candidate seulement, au plus 6, marquées comme voisines pour le modèle et dans l'interface ; D-013 est élargi en ce sens. |
| D-041 | **Désaccord entre le modèle et un calcul sûr** | Le modèle reste libre ; son désaccord est signalé, jamais caché. |
| D-042 | **Base de contrôle** | Une base fictive générée avant tout réglage, mesurée une fois à la fin (0.5 contre 0.6), puis ajoutée au banc. |
