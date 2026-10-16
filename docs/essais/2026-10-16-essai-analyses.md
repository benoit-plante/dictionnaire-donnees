# Essai : des objectifs au rapport, sur une base fictive puis sur une vraie base (v0.9, étape 8)

**Date :** 2026-10-16

**But :** refaire tout le parcours de la v0.9 (choisir une analyse, avec ou sans l'IA conseillère, la lancer, écrire le rapport et le script R, refaire l'analyse dans R) ; puis vérifier sur une vraie base que chaque analyse du catalogue se calcule sans erreur, et que son script R donne les mêmes valeurs. Sur la vraie base, seuls des faits de structure et des agrégats sont consignés : aucun résultat, aucun nom de variable, aucun libellé, aucun instrument.

## 1. Base fictive, dans le navigateur

Base des analyses (`etude-analyses.sav`), projet neuf, échelle de bien-être cotée comme le dit le corrigé ; interface lancée par `ddict reviser`, page « Analyses ».

- **Sans IA :** régression linéaire de la satisfaction sur le soutien et la charge, choisie à la main ; résultat affiché (R² = 0,47, coefficients du corrigé), puis « Écrire à côté du projet » : rapport Markdown, tableaux Excel, script R, fichier de commandes et script de préparation.
- **Avec l'IA :** l'objectif « Les hommes et les femmes ont-ils le même niveau de bien-être ? » tapé dans l'encadré ; qwen2.5 7B répond en une quinzaine de secondes ; première proposition : un test t du score de bien-être selon le sexe (méthode de Student). « Reprendre cette proposition » remplit les choix ; rien n'est calculé avant « Lancer l'analyse » ; le résultat (aucune différence, comme le corrigé le prévoit) et ses fichiers sont écrits. Le message envoyé et la réponse reçue sont dans le dossier des envois.
- **Dans R :** les deux scripts écrits par la page s'exécutent dans le dossier du projet et redonnent les valeurs de l'outil.

## 2. Vraie base

Une base SurveyMonkey réelle, hors du dépôt : 252 variables, 980 lignes, un questionnaire PDF, sans export Excel.

### Structure (tests `reel`)

- 12 tests passent, 3 sont sans objet (pas d'export Excel, une seule vague).
- Trois échecs au départ venaient du **compteur** des tests, pas de l'outil : 33 questions à une seule ligne étaient comptées comme des grilles. Isolées (aucune suite de plus de deux questions de même échelle), elles ne forment pas de groupe, et l'outil a raison de ne pas en faire. Corrigé dans `scripts/compter_structure.py` : une grille compte au moins deux items. Les 6 grilles de la base sont alors entières, et le PDF en lit 6.

### Les six analyses

Le projet est construit sans décision (niveaux de mesure du fichier) ; 103 variables d'échelle et 93 catégorielles peuvent servir. Pour chaque analyse, les premières variables que les conditions acceptent sont prises ; le calcul se fait dans l'outil, puis le script R écrit est exécuté dans R sur une copie temporaire de la base (supprimée ensuite), et les valeurs comparées.

| Analyse | Calcul | Script R | Valeurs comparées | Plus grand écart relatif |
|---|---|---|---|---|
| Tableau 1 | sans erreur | sans erreur | 18 | 4 × 10⁻¹⁵ |
| Test t | sans erreur | sans erreur | 17 | 5 × 10⁻¹² |
| ANOVA | sans erreur | sans erreur | 9 | 3 × 10⁻¹³ |
| Khi-carré | sans erreur | sans erreur | 5 | 1 × 10⁻¹⁵ |
| Corrélation | sans erreur | sans erreur | 5 | 1 × 10⁻¹⁵ |
| Régression | sans erreur | sans erreur | 26 | 1 × 10⁻¹³ |

Lecture et préparation de la base : 3 secondes ; chaque calcul, moins d'un dixième de seconde. Pour l'ANOVA, les conditions ont écarté 131 couples de variables avant d'en accepter un : elles font leur travail sur une base réelle.

### L'IA conseillère

- Au format de la v1, le message aurait compté environ 10 000 jetons : bien plus que les 4 096 que lit le modèle local. D'où D-080 : variables par niveau, [nom, libellé], groupes d'items en une entrée, libellés coupés. Le message compte alors environ 3 000 jetons estimés.
- **Premier envoi :** plus de dix minutes sans réponse. Le schéma ne bornait pas la longueur des listes de variables, et le modèle en écrivait sans fin parmi 196 noms permis. Les listes sont maintenant bornées dans le schéma (au plus 30 variables par rôle, au plus 2 rôles) : chaque réponse arrive en moins d'une minute, le plus souvent en 5 secondes.
- **Puis trois façons de mal répondre, chacune refusée par la validation** (rien n'a été proposé à tort) :
  1. l'identifiant du message remplacé par celui d'un groupe d'items : il est maintenant imposé dans le schéma ;
  2. un rôle qu'une analyse n'a pas (une variable dépendante pour un Tableau 1) : le schéma envoyé décrit maintenant chaque analyse avec ses propres rôles et méthodes, et, pour chaque rôle, seulement les variables dont le niveau convient ;
  3. un rôle répété et un rôle obligatoire oublié, signalé par les conditions : les rôles sont maintenant écrits dans l'ordre, chacun une fois, les obligatoires exigés.
- **Enfin, l'objectif perdu de vue :** trois objectifs différents recevaient la même ANOVA. L'objectif est maintenant rappelé à la fin du message, après la liste des variables.

Résultat, avec trois objectifs généraux (décrire les participants ; comparer deux groupes sur une mesure continue ; relier deux mesures continues) : trois réponses valables en 4 à 5 secondes ; l'analyse proposée convient à l'objectif deux fois sur trois (test t, corrélation) ; pour « décrire les participants », une ANOVA au lieu d'un Tableau 1. Aucune proposition refusée par les conditions.

Sur la base fictive, le banc des 13 objectifs donne, avec ces changements, 9 propositions justes au premier rang sur 13 (11 avec la v1 du message, 10 avec la v2 avant ces changements). Les écarts : une régression au lieu d'une corrélation (défendable), des Tableaux 1 avec une variable de groupe ou des variables de plus, et une proposition pour l'objectif hors catalogue.

## Ce que montre l'essai

1. **Le calcul et le script R tiennent sur une vraie base** : six analyses, mêmes valeurs dans R à 10⁻¹¹ près, en quelques secondes.
2. **Les garde-fous de l'IA ont tenu à chaque étape** : aucune réponse hors du catalogue ou du projet n'est passée ; chaque erreur du modèle a été refusée, puis rendue impossible par le schéma envoyé.
3. **L'IA conseillère reste modeste sur une grande base** : utile pour retrouver le type d'analyse d'un objectif simple, moins sûre pour choisir les variables. La page le dit (« propositions à vérifier ») ; c'est la personne qui choisit. Pour un usage courant, choisir soi-même reste la voie principale ; le guide le dira.
4. **À suivre :** la qualité des propositions sur une grande base pourrait s'améliorer avec un modèle plus grand ou un contexte plus large (réglage d'Ollama) ; hors du périmètre de la v0.9.
