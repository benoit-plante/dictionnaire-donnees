# Plan de la v0.7

> Statut : **validé par l'auteur le 2026-10-15**, avec toutes les recommandations du § 8 (D-043 à D-052).

## 1. Pourquoi cette version

Jusqu'ici, l'outil a été essayé sur des bases dont l'équipe avait déjà renommé les variables (`sommeil_q1`, `anx3`). Beaucoup d'équipes partent pourtant d'un **export brut de plateforme de sondage**, surtout SurveyMonkey, où les variables s'appellent `q0003_0004`. Deux exports réels (114 variables et 50 variables), passés dans la v0.6 hors du dépôt, montrent deux choses :

- **la v0.6 lit mal ces fichiers** : la deuxième ligne d'en-tête du `.xlsx` est lue comme un participant, `q0001`, `q0002`, `q0006` et `q0007` forment un faux groupe, une grille de 20 items est coupée en deux, un item qui contient le verbe « identifier » est classé « identifiant probable », les dates de passation restent du texte, les codes « Ne sais pas » et « Préfère ne pas répondre » passent inaperçus, le PDF donne 15 questions pour 10 et le `.txt` numéroté n'en donne aucune ;
- **ces fichiers ont pourtant une structure sûre** : le nom `q0003_0004` dit que la variable est le 4ᵉ énoncé de la 3ᵉ question, et l'en-tête du `.xlsx` donne la consigne de chaque question et le texte de chaque énoncé ou option. Cette structure est plus fiable que le découpage du PDF.

Une fois les variables reconnues, rattachées et groupées, il reste à leur donner un **nom lisible** ; pour une étude longitudinale, le même nom qu'à la vague précédente. C'est aujourd'hui un travail manuel, long et source d'erreurs dans SPSS ou R.

Le plan « contrat d'analyse » (export pour l'IA d'analyse, cotation structurée) passe à la v0.8. Il n'est pas dans `docs/` : rien à renommer ni à renuméroter ; ses décisions prendront les numéros libres après ce plan.

## 2. Contenu proposé

**Partie A — Lire juste les exports de plateforme** (en premier : elle rend l'outil juste sur ces fichiers, même sans renommage)

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A1 | **Reconnaître un export SurveyMonkey** (`.sav`, `.csv`, `.xlsx`), gardé dans `source.platform` ; conventions décrites comme des données, pour qu'une autre plateforme s'ajoute plus tard sans toucher au reste | Tout le reste de l'outil sait à quoi il a affaire |
| A2 | **En-tête sur deux lignes** (`.xlsx`, et `.csv` de même forme) : les colonnes reçoivent les noms du `.sav`, la ligne 2 n'est jamais lue comme une donnée ; l'outil conseille le `.sav` quand il existe | Effectifs et types justes |
| A3 | **Structure de plateforme** : rang de la question, rang de l'énoncé ou de l'option, variable « autre » ; une grille = un groupe, un ensemble de cases à cocher = un groupe « réponses multiples » ; `q0003_0004` → 4ᵉ énoncé de la 3ᵉ question, rattachement sûr quand les textes concordent | Groupes et rattachements justes sans IA |
| A4 | **L'en-tête du `.xlsx` comme questionnaire** (en-tête seulement, jamais les réponses) | Consigne des grilles, énoncés et options, lus sans découpage incertain |
| A5 | **Corrections tirées de l'essai** (§ 3.4), chacune avec son test | Les faux groupes, faux identifiants, dates, codes « Ne sais pas » et questionnaires mal découpés de l'essai disparaissent |

**Partie B — Renommer les variables**

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| B1 | **Nouveau nom** : valeur suivie (origine, statut), le nom d'origine restant la clé ; réglages de nommage du projet ; règles de validité | Un nom proposé, validé par une personne, traçable |
| B2 | **Propositions par le calcul** : noms fixes des variables de plateforme, `<préfixe>_<rang>` pour un groupe dont une personne a donné le préfixe, `<radical>_<rang>` et `<radical>_autre_txt` pour les cases à cocher, radical tiré des mots de la question | La plupart des noms proposés sans IA |
| B3 | **Reprendre les noms d'une vague précédente** : appariement par le calcul, score lisible, rapport des écarts entre vagues | Le cas le plus fréquent des études longitudinales |
| B4 | **Exports renommés** : codebook (« Nom », « Nom d'origine », onglet « Correspondance »), `RENAME VARIABLES` en tête de la syntaxe SPSS, renommage en tête du script R, copie documentée aux nouveaux noms | Le fichier d'origine n'est jamais touché ; les noms acceptés s'appliquent partout où s'appliquent déjà les décisions |
| B5 | **Page « Noms »** et commande `ddict renommer` / `ddict rename` | Tout le parcours dans l'interface ou en ligne de commande |
| B6 | **Proposition par le modèle**, facultative, pour les radicaux seulement | À garder seulement si le banc montre qu'elle fait mieux que le calcul |

**Hors de cette version** : LimeSurvey, Qualtrics et REDCap (la description de plateforme les permettra) ; le changement du niveau de mesure `scale` des items (signalé seulement, décision de la v0.8) ; le contrat d'analyse (v0.8) ; tout recodage (D-025 tient) ; Linux.

## 3. Conception — partie A

### 3.1 Description d'une plateforme (A1)

- Nouveau module `ddict.platforms` : une plateforme est une **description** (classe de données figée), pas du code propre : nom (`surveymonkey`), variables de plateforme connues avec leurs variantes de nom (`RespondentID` / `respondent_id`…), leur rôle (identifiant du répondant, du collecteur, date de début, adresse IP, courriel, prénom, nom, donnée personnalisée, nom du collecteur), leur classe de confidentialité et leur nom fixe en français et en anglais (D-050) ; motif des noms d'items (`q(?P<question>\d{4})(?:_(?P<item>\d{4})|_(?P<other>other))?`) ; jetons de la ligne 2 d'un en-tête (`Response`, `Open-Ended Response`) ; formes de l'option « autre » (`Other (please specify)`, `Autre (veuillez préciser)`).
- **Reconnaissance** : une base est un export de la plateforme quand la plupart de ses variables de plateforme connues sont présentes (une variante ou l'autre) et que la plupart des autres noms suivent le motif. Seuils fixés sur la base fictive, vérifiés sur les deux vraies.
- `SourceInfo.platform` (`"surveymonkey"` ou absent) et, par variable, sa place dans la structure (§ 3.3), calculée à la lecture et recalculée à la réouverture, jamais saisie.
- Ajouter une plateforme plus tard = écrire une nouvelle description et ses tests ; le reste de l'outil ne lit que la description.

### 3.2 En-tête sur deux lignes (A2)

- Détection : sous une ligne 1 dont les cellules sont vides après la première colonne de chaque question, une ligne 2 faite de `Response`, `Open-Ended Response` ou de textes, avec les colonnes de plateforme vides en ligne 2.
- Noms : les variables de plateforme reçoivent leur nom de la variante récente du `.sav` (`respondent_id`…) ; les autres `q<rang de la question>` (une colonne `Response` ou `Open-Ended Response`), `q<rang>_<rang de la colonne>`, ou `q<rang>_other` quand la ligne 2 est une forme connue de « autre ». Le rang compte les questions de la ligne 1 dans l'ordre. **À vérifier sur les vrais fichiers** : que ces noms sont exactement ceux du `.sav` de la même étude (test `reel` qui ne compte que les écarts). Cas ambigu connu : une question à cocher d'une seule option ressemble à une question simple ; elle est nommée comme une question simple et signalée.
- Les données commencent à la ligne 3. Un message (interface et ligne de commande) dit que le `.sav` est préférable : il a les codes et les étiquettes.
- Le lecteur CSV applique la même règle : à notre connaissance, l'export CSV de SurveyMonkey a le même en-tête. Testé sur un CSV fictif ; l'essai réel n'en avait pas.

### 3.3 Structure de plateforme (A3)

- Pour chaque variable : rang de la question, rang de l'énoncé ou de l'option, ou « autre » ; et la nature de la question, lue dans le `.sav` : **grille** (énoncés à deux étiquettes de valeurs ou plus), **cases à cocher** (une seule étiquette de valeur par variable, `1 = texte de l'option`, non coché = vide), **question simple**.
- **Groupes** : quand la structure existe, elle remplace les règles de préfixe et d'étiquettes partagées pour les variables qu'elle couvre. Une grille d'au moins 3 énoncés = un groupe (base : « structure de plateforme »). Un ensemble de cases à cocher = un groupe de nature « réponses multiples » (nouveau champ `Group.kind`, `scale` par défaut), sans alpha ni corrélations item-total, avec sa variable « autre » rattachée (`Group.attached`, hors des membres : c'est du texte libre).
- **Rattachements** : la question de plateforme de rang 3 est mise en correspondance avec une question du questionnaire par le texte (l'étiquette de `q0003_0001` contre les énoncés, l'étiquette d'une case à cocher contre la question), dans l'ordre. Quand les textes concordent (comparaison normalisée : casse, accents, ponctuation, `…` initial), `q0003_0004` → `Q3.r4` est un **choix sûr du calcul** au sens de D-041 ; sinon, un signal `question:platform_disagrees` est montré et rien n'est sûr. Le rang de plateforme ne suffit jamais seul : un questionnaire peut compter autrement (blocs de texte, pages).

### 3.4 L'en-tête du `.xlsx` comme questionnaire (A4)

- Lecture des deux premières lignes seulement (`openpyxl` en lecture seule, arrêt après la ligne 2). Chaque bloc de la ligne 1 devient une question `Q<rang de plateforme>` : texte de la ligne 1 ; colonnes de la ligne 2 en énoncés (`Q3.r1`…) pour une grille, en options (`Q8.o1`…, l'option « autre » en dernier) pour des cases à cocher ; `Response` et `Open-Ended Response` ne sont pas des options. Les options d'une question à choix ne sont pas dans l'en-tête : elles restent les étiquettes de valeurs du `.sav`.
- C'est une source documentée au sens de D-012, enregistrée avec son nom et son empreinte (`Questionnaire.format = "xlsx"`). D-045 : un **troisième format** de questionnaire, source unique du projet comme aujourd'hui, plutôt qu'un complément fusionné au PDF.
- Avec la base `.sav` et l'en-tête `.xlsx` de la même étude, les identifiants coïncident (`q0003_0004` ↔ `Q3.r4`) et la concordance des textes est vérifiée comme au § 3.3.

### 3.5 Corrections tirées de l'essai (A5)

| Correction | Où | Règle |
|---|---|---|
| Préfixe commun | `groups/find.py` | Un radical d'une seule lettre (`q`) ne fait jamais un préfixe d'échelle ; il faut un radical de 2 lettres au moins suivi d'un séparateur (`anx_3`), ou de 3 lettres au moins (`anx3`). Pour les noms de plateforme, la structure remplace la règle |
| Identifiant par l'étiquette | `privacy/classify.py` | Les mots du nom et ceux de l'étiquette sont séparés : par le nom, la règle actuelle ; par l'étiquette, seulement quand elle *désigne* un identifiant (étiquette courte qui commence par « Identifiant », « ID », « Numéro de participant / de dossier / du répondant », « Code du participant », « Respondent ID »…), jamais pour un mot au milieu d'une phrase |
| Grille coupée | `groups/find.py` | Une variable écartée d'un groupe par sa classe de confidentialité, mais aux mêmes étiquettes de valeurs, ne ferme pas la suite : le groupe continue sans elle, et sa base le dit |
| Dates de passation en texte | `profile/compute.py` | Formats de date et heure à barres obliques, avec heure sur 24 h ou AM/PM, et formats ISO avec secondes ; mesure sur les vrais fichiers du **taux** de valeurs reconnues, sans aucune valeur affichée |
| Codes « Ne sais pas » | `profile/compute.py` | Un code dont l'**étiquette** dit « Ne sais pas », « Je ne sais pas », « NSP », « Préfère ne pas répondre », « Refus », « Sans objet », « Ne s'applique pas » ou leurs équivalents anglais (« Don't know », « Prefer not to answer / say », « Refused », « Not applicable », « N/A ») devient un code manquant probable, avec la raison « étiquette » ; décidé comme les autres (D-028). Conséquence voulue : il est écarté du calcul de l'alpha, comme les autres codes suspects |
| Niveau `scale` douteux | construction du projet | Un item d'un groupe dont toutes les valeurs observées ont une étiquette et dont le niveau déclaré est `scale` reçoit le signal « niveau de mesure douteux » ; le niveau n'est pas changé (v0.8) |
| `.txt` numéroté | `questionnaire/segment.py` | `1.`, `1)`, `Q1.`, `Q1)` en tête d'une ligne qui se termine comme une question (`?`, `:`) ou dont la numérotation continue d'une question à l'autre par-dessus des options : une question, pas un énoncé de grille. Question à cocher reconnue aussi par « Coche », « Cochez » (sauf « une seule ») |
| PDF SurveyMonkey | `questionnaire/segment.py` | En-têtes de colonnes empilés sur plusieurs lignes (« Pas du » / « tout ») réunis colonne par colonne. Quand une structure de plateforme existe, le nombre de questions et d'énoncés trouvés est comparé à elle ; une question sans équivalent dans la base est signalée (`not_in_platform_structure`), un écart de nombre d'énoncés aussi, plutôt que de proposer de fausses questions |

## 4. Conception — partie B

### 4.1 Le nouveau nom (B1)

- `VariableEntry.new_name : TrackedValue[str]`, vide par défaut. Le nom d'origine (`name`) reste la clé : c'est par lui que la base est relue, reconnue et comparée.
- Deux nouvelles origines qui peuvent être proposées, comme `questionnaire` (D-018) : `rule` (règles de nommage du § 4.2) et `reference` (vague précédente ou table de correspondance, § 4.3). `computed` reste une valeur acquise : un nom ne l'est jamais sans une personne.
- `Group.name_prefix : TrackedValue[str]` : le préfixe d'un groupe (`k6`), saisi par une personne, ou repris d'une vague précédente (`reference`). Jamais proposé par le modèle (principe 4).
- `Project.stems` : le **radical** d'une question (`taches`), une fois par question, partagé par ses variables ; clé = la question de plateforme (`q0008`) ou la question rattachée (`Q8`). Corrigé à un seul endroit ; les noms qui en dérivent et ne sont pas encore acceptés suivent ; un nom déjà accepté reçoit le signal « radical changé ».
- `Settings.naming` : longueur maximale (32 par défaut, limite de Stata), marque de vague (`_t2`), position (suffixe ou préfixe, D-049). Règles fixes, vérifiées à chaque saisie : minuscules, chiffres et `_`, commence par une lettre, ni accent ni `_` final ; pas un mot réservé de SPSS (`ALL`, `AND`, `BY`, `EQ`, `GE`, `GT`, `LE`, `LT`, `NE`, `NOT`, `OR`, `TO`, `WITH`) ; unique, sans distinction de casse, parmi les noms finaux (nouveau nom accepté, sinon nom d'origine) ; un nouveau nom égal au nom d'origine d'une autre variable est refusé.
- `schema_version` passe à `0.2.0` (D-048) : tous les champs nouveaux ont une valeur par défaut, donc un projet 0.1.0 se lit sans conversion. Le chargeur dira clairement qu'un fichier vient d'une version plus récente de l'outil.

### 4.2 Propositions par le calcul (B2)

Dans cet ordre ; une variable reçoit la première règle qui s'applique.

| Cas | Proposition (origine `rule`) |
|---|---|
| Variable de plateforme | Nom fixe (D-050), dans la langue du projet ; la classe de confidentialité reste visible à côté |
| Membre d'un groupe dont le préfixe est accepté | `<préfixe>_<rang>` : rang de l'énoncé dans la structure de plateforme, sinon ordre dans le groupe |
| Option d'un ensemble à cocher | `<radical>_<rang de l'option>` ; la variable « autre » : `<radical>_autre_txt` (`_other_txt` en anglais) |
| Question seule | `<radical>` ; le radical vient des mots significatifs de la question rattachée acceptée (mots vides français et anglais retirés, sans accents, au plus 3 mots, au plus 20 caractères), sinon de l'étiquette |
| Rien de possible | Aucune proposition : la variable est « à nommer » ; l'export garde son nom d'origine |

La marque de vague s'ajoute à tout nom proposé ; la longueur est vérifiée marque comprise. Une proposition invalide (trop longue, collision) n'est pas enregistrée : la variable reste « à nommer », avec la raison.

### 4.3 Reprendre les noms d'une vague précédente (B3)

- **Sources** : le fichier projet (`.dd.json`) de la vague précédente (noms d'origine, noms acceptés, étiquettes, étiquettes de valeurs, texte des questions rattachées, préfixes des groupes) ; sa copie documentée (`.sav` : noms déjà renommés, étiquettes, étiquettes de valeurs) ; ou une table de correspondance (D-052).
- **Appariement** variable par variable, par le calcul, avec un score fait de critères lisibles : étiquettes de valeurs identiques ; texte de l'étiquette ou de la question identique ou proche (normalisé : casse, accents, ponctuation, `…` initial) ; même rang dans une grille appariée ; même type. Le meilleur appariement est proposé seulement s'il est **net** (même règle que les ancres) et si la variable de la vague précédente n'est pas mieux appariée ailleurs ; sinon, la liste des candidates est montrée. Le nom d'origine n'est jamais un critère seul : la numérotation de SurveyMonkey change dès qu'une question est ajoutée.
- **Nom proposé** (origine `reference`) : le nom de la vague précédente, sans sa marque de vague s'il en a une (lue dans ses réglages, ou reconnue comme `_t1` / `t1_` commune à presque tous les noms), avec la marque de la vague actuelle.
- **Préfixes** : ceux des groupes de la vague précédente sont proposés pour les groupes appariés (la majorité de leurs membres appariés au même groupe).
- **Rapport des écarts** : variables ajoutées (sans équivalent), retirées (absentes), étiquettes de valeurs changées pour une paire appariée. Montré sur la page « Noms », imprimé par la commande, et écrit à côté du projet (`<projet>-ecarts-vagues.md`) : c'est un résultat en soi pour l'équipe. Il ne contient que des métadonnées.

### 4.4 Exports (B4)

- Codebook Excel et Markdown : colonne « Nom » (nouveau nom accepté, sinon d'origine) et « Nom d'origine », onglet « Correspondance » (nom d'origine, nouveau nom, statut, origine). Seulement quand le projet a au moins un nouveau nom : un projet sans renommage donne exactement le codebook d'aujourd'hui (rapports de référence inchangés).
- Syntaxe SPSS : `RENAME VARIABLES (ancien = nouveau …).` en premier, puis le reste sur les nouveaux noms. Script R : renommage en premier, en R de base (`names(donnees)[match(...)] <- ...`), sans nouvelle dépendance. Vérification comme en v0.4 : le script R appliqué au CSV fictif redonne la copie documentée ; la syntaxe s'exécute dans PSPP.
- Copie documentée : écrite aux nouveaux noms ; la comparaison cellule par cellule passe par la correspondance des noms.
- Export final et fichiers de commandes : seulement les noms **acceptés** ; l'export de travail montre les propositions, marquées. Le même fichier de correspondance (D-052) est écrit à côté du codebook, pour servir de référence à la vague suivante.

### 4.5 Interface et ligne de commande (B5)

- Page « Noms », après « Groupes » dans la barre latérale : tableau (nom d'origine, étiquette, question, nom proposé, origine, statut, problème) ; filtres « à nommer », « proposés », « en conflit » ; correction en place, validée à la saisie ; acceptation groupée par groupe ou par question, avec la liste exacte et des cases à décocher (D-029). Réglages de nommage et import de la vague précédente sur la même page.
- Vue « Groupes » : saisie du préfixe d'un groupe.
- Tableau de bord : questionnaire, sigles, rattachements, groupes (préfixes), codes suspects, étiquettes de valeurs, **noms**, libellés.
- `ddict renommer <projet> [--reference <projet-t1.dd.json | t1-documente.sav | correspondance.csv>] [--suffixe _t2 | --prefixe t2_] [--modele …]` ; en anglais `ddict rename … --reference --suffix --prefix --model`. Sans `--modele`, le calcul seul ; la commande imprime les nombres de noms proposés, à nommer, en conflit, et les écarts entre vagues.

### 4.6 Proposition par le modèle (B6)

- Pour les **radicaux** des questions seulement (D-051), facultative, après le calcul : le modèle reçoit, par la porte de confidentialité, ce qu'elle envoie déjà (texte de la question rattachée acceptée, étiquette, type, étiquettes de valeurs) et répond un radical par question.
- Schéma strict (`extra="forbid"`, motif `^[a-z][a-z0-9_]{0,19}$`), validé par les règles du § 4.1, statut « proposé » ; un radical qui ressemble à un sigle absent du texte de la question et du glossaire accepté est signalé (signal « instrument », principe 4).
- Prompts `rename-v1.fr.txt` et `rename-v1.en.txt`. Le banc mesure, sur la base fictive SurveyMonkey, le taux de radicaux valides et le taux acceptés tels quels (égaux au corrigé), pour le calcul seul et pour le modèle.

## 5. Données d'essai

**Dans le dépôt** — `scripts/generer_base_surveymonkey.py`, graine fixe, **items inventés** :

- Vague 1 et vague 2 d'une étude fictive, chacune avec ses variables de plateforme (variante ancienne des noms pour la vague 1, récente pour la vague 2), un identifiant de participant au format « code de famille et initiales » (initiales inventées), une grille d'échelle de Likert (étiquettes de valeurs répétées par variable, `F8.2`, niveau `scale`), une grille avec « Ne sais pas » (6) et « Préfère ne pas répondre » (7) non déclarés, trois ensembles à cocher avec « autre », des questions ouvertes, des dates en texte, une variable texte finale étiquetée `id`, et un item d'échelle dont l'étiquette contient le verbe « identifier ».
- Vague 2 : `.sav`, `.xlsx` et `.csv` à deux lignes d'en-tête, questionnaire `.txt` numéroté et PDF proche de SurveyMonkey (grilles à en-têtes sur plusieurs lignes). Par rapport à la vague 1 : une question ajoutée (qui décale la numérotation `qNNNN`), un item retiré, une étiquette de valeur changée.
- Vague 1 déjà renommée : sa copie documentée (`.sav`, noms en `_t1`) et sa table de correspondance (`.csv`) ; son fichier projet est construit dans les tests à partir du corrigé, pour suivre le format du projet sans fichier figé.
- Corrigé `corrige-surveymonkey.json` : groupes (nature, membres, variable « autre »), rattachements, noms attendus (avec les préfixes donnés), écarts entre vagues attendus.

**Hors du dépôt** — les deux vrais exports, dans un dossier donné par `DDICT_DONNEES_REELLES` :

- tests marqués `reel` (marqueur déclaré, `--strict-markers`), sautés sans la variable, jamais lancés par l'intégration continue ;
- ils ne comparent que des nombres : chaque vérification passe par une fonction qui rend des décomptes (questions, groupes, écarts de noms, taux de dates reconnues), et l'assertion porte sur ces nombres, pour que pytest n'affiche jamais une valeur, une étiquette ou un texte en cas d'échec ; les identifiants de tests sont `base1`, `base2`, jamais le nom des fichiers ;
- rien de ce dossier n'est copié dans le dépôt, `tests/`, `exemples/` ni un message de commit ; le chemin n'apparaît nulle part ;
- l'essai consigné dans `docs/essais/` décrit les bases seulement par ces faits de structure, sans nommer d'instrument.

## 6. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Base fictive SurveyMonkey, ses fichiers et son corrigé ; marqueur `reel` et fonctions de décompte ; mesure de la 0.6 sur la base fictive et sur les vraies (décomptes seulement) | Fichiers reproductibles (test) ; chaque constat du cahier des charges reproduit par la base fictive (un test par constat, en échec attendu) ; mesure 0.6 consignée |
| 2 | Description de plateforme, reconnaissance, `source.platform` ; en-tête sur deux lignes (`.xlsx`, `.csv`) | Fictifs reconnus ; noms du `.xlsx` = noms du `.sav` ; autant de lignes que de participants (tests) ; `reel` : plateforme reconnue, zéro écart de noms entre `.xlsx` et `.sav` |
| 3 | Corrections : préfixe, identifiant par l'étiquette, grille non coupée, dates en texte, codes manquants par l'étiquette, niveau `scale` douteux | Un test par correction sur la base fictive ; bancs et rapports de référence des autres bases inchangés ; `reel` : taux de dates reconnues, plus de faux identifiant, grille de 20 items entière |
| 4 | Structure de plateforme : groupes (grilles, réponses multiples avec « autre »), rattachements sûrs par concordance ; en-tête `.xlsx` comme questionnaire | Groupes et rattachements du corrigé retrouvés sans IA (test) ; `reel` : 8 grilles sur la première base, ensembles à cocher regroupés sur la seconde |
| 5 | Questionnaire : `.txt` numéroté, cases à cocher par la formulation, PDF à en-têtes empilés, contrôle par la structure | Questions du corrigé retrouvées dans le `.txt` et le PDF fictifs ; `reel` : 10 questions sur 10 au PDF ou écarts signalés, aucune fausse question proposée ; 13 sur 13 au `.txt` numéroté |
| 6 | Nouveau nom : modèle de données, `schema_version` 0.2.0, réglages, règles de validité, propositions par le calcul ; `ddict renommer` sans référence | Noms du corrigé obtenus pour la vague 1 une fois les préfixes donnés (test) ; projets 0.1.0 des bases fictives relus sans perte ; chaque règle de validité testée |
| 7 | Vague précédente : trois sources, appariement, préfixes repris, rapport des écarts ; table de correspondance exportée et relue | Vague 2 contre vague 1 fictives : noms appariés justes, question ajoutée, item retiré et étiquette changée retrouvés (test) ; mêmes propositions depuis le projet, la copie documentée ou la table, quand la source le permet |
| 8 | Exports renommés : codebook, syntaxe SPSS, script R, copie documentée | Script R appliqué au CSV fictif = copie documentée ; syntaxe exécutée dans PSPP ; copie vérifiée cellule par cellule ; codebook inchangé sans renommage (rapports de référence) |
| 9 | Page « Noms », préfixe dans la vue « Groupes », tableau de bord, décisions groupées | Logique testée sans Streamlit ; scénario refait dans le navigateur ; parcours en anglais sans texte français |
| 10 | Radicaux par le modèle : prompts `rename-v1`, schéma, banc | Faux serveur : réponses invalides refusées (tests) ; banc avec qwen2.5 7B consigné ; le modèle reste proposé seulement s'il fait mieux que le calcul seul |
| 11 | Essai sur les deux vraies bases (faits de structure), guides, journal des changements, version 0.7.0 | Essai dans `docs/essais/` sans aucun contenu réel ; guides à jour en français et en anglais |

## 7. Risques

- **Conventions variables** : deux variantes de noms déjà vues ; il peut y en avoir d'autres selon l'âge du compte, la langue ou les options d'export. La description de plateforme les accueille sans code nouveau, et un fichier non reconnu est lu comme aujourd'hui, sans structure.
- **Rang de plateforme et numérotation du questionnaire** : ils peuvent différer (blocs de texte, pages, questions ajoutées). Le rang ne fait jamais seul un rattachement sûr : il faut la concordance des textes.
- **Base fictive trop facile** : elle est écrite d'après le cahier des charges ; les tests `reel` sont la garde, comme la base de contrôle en v0.6.
- **Fuite de données réelles** : par un message d'échec de pytest, un identifiant de test, un journal, un essai ou un message de commit. D'où les décomptes seulement, les identifiants `base1` et `base2`, et une relecture de chaque fichier ajouté avant chaque commit (le dépôt est public, D-037).
- **Codes manquants par l'étiquette à tort** : une étiquette « Sans objet » peut être une vraie réponse dans certaines études ; c'est une proposition, décidée par une personne (D-028).
- **Renommage et anciens outils** : une version 0.6 ne lit pas un projet 0.2.0 (champs inconnus refusés). Le guide le dit ; l'inverse fonctionne.
- **Radical inventé par le modèle** : un sigle d'instrument dans un radical serait une invention ; signal « instrument » et préfixes de groupe réservés aux personnes.
- **Taille de la version** : onze étapes. Si elle s'allonge, l'étape 10 (modèle) passe à une 0.7.x ; la partie A, livrée en premier, est utile seule.

## 8. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-043 | **Périmètre de la v0.7** | Exports de plateforme (partie A, en premier) et renommage (partie B) ; le contrat d'analyse passe à la v0.8 ; LimeSurvey, Qualtrics et REDCap seulement rendus possibles. |
| D-044 | **Plateformes décrites par leurs conventions** | Une description par plateforme dans `ddict.platforms`, SurveyMonkey seul implanté ; `source.platform` dans le projet ; nouvelle nature de groupe « réponses multiples » (`Group.kind`), avec la variable « autre » rattachée hors des membres. |
| D-045 | **L'en-tête du `.xlsx` comme source du questionnaire** | **Un troisième format** (`pdf`, `txt`, `xlsx`), source unique du projet comme aujourd'hui, plutôt qu'un complément fusionné au PDF. Il est exact là où le PDF est incertain (énoncés, options, consigne des grilles) et ses identifiants coïncident avec les noms ; une fusion avec le PDF ajouterait un appariement de plus, donc une source d'erreur de plus. Ce qui manque à l'en-tête (pages, consentement, consignes générales) n'est pas exporté de toute façon (D-012), et les options des questions à choix restent les étiquettes du `.sav`. Le PDF reste possible pour qui n'a pas l'export `.xlsx`, contrôlé par la structure de plateforme. |
| D-046 | **Données réelles hors du dépôt** | Tests marqués `reel`, dossier donné par `DDICT_DONNEES_REELLES`, sautés sans lui et hors de l'intégration continue ; décomptes seulement, jamais une valeur, une étiquette ni un texte ; essais décrits par des faits de structure. |
| D-047 | **Codes manquants probables par leur étiquette ; niveau `scale` douteux** | Oui : l'étiquette (« Ne sais pas », « Préfère ne pas répondre », « Refus », « Sans objet » et l'anglais) fait un code manquant probable, décidé comme les autres (élargit D-028), écarté de l'alpha comme les autres codes suspects. Le niveau `scale` d'un item étiqueté d'une grille est signalé, pas changé. |
| D-048 | **Le champ `new_name` et la version du format** | Valeur suivie `new_name`, le nom d'origine restant la clé ; deux origines nouvelles qui peuvent être proposées, `rule` et `reference` (plutôt que d'ouvrir `computed` aux propositions, ce qui changerait le sens des valeurs calculées) ; préfixe de groupe et radical de question comme valeurs suivies ; `schema_version` 0.2.0 sans conversion, tous les champs nouveaux ayant une valeur par défaut. |
| D-049 | **Marque de vague par défaut** | Aucune marque tant que la personne ne donne pas de vague ; quand elle en donne une, **suffixe `_t<N>`** (`k6_1_t2`). Le suffixe garde ensemble, dans une liste triée, les variables d'un même concept et laisse le début du nom au concept ; le préfixe `t2_` reste au choix. La marque de la vague précédente est retirée avant d'ajouter la nouvelle. |
| D-050 | **Noms fixes des variables de plateforme** | Français : `respondent_id`, `collector_id`, `nom_collecteur`, `date_debut`, `date_fin`, `adresse_ip`, `courriel`, `prenom`, `nom_famille`, `donnees_personnalisees_1`. Anglais : `respondent_id`, `collector_id`, `collector_name`, `start_date`, `end_date`, `ip_address`, `email`, `first_name`, `last_name`, `custom_data_1`. `respondent_id` et `collector_id` restent en anglais dans les deux langues : ce sont les noms de la plateforme et de ses autres exports, utiles pour joindre des fichiers. Deux écarts avec la demande : `nom_famille` plutôt que `nom` (qui se lit aussi « nom de la variable » ou « name »), et `donnees_personnalisees_1` plutôt que `donnees_perso_1` (« perso » se lit « personnelles », or ce sont les données *personnalisées* de SurveyMonkey). |
| D-051 | **Place du modèle dans le renommage** | Facultatif, après le calcul, pour les **radicaux de questions seulement** ; jamais pour un préfixe de groupe, une variable de plateforme ni un rang. Il ne remplace qu'un radical non décidé. Comme pour D-013, le banc décide : s'il ne fait pas mieux que le calcul seul en noms acceptés tels quels, il n'est pas proposé dans l'interface. |
| D-052 | **Vague précédente et table de correspondance** | Trois sources : fichier projet (recommandée : la plus riche), copie documentée `.sav`, table CSV. Table : UTF-8, séparateur `,` ou `;` détecté, en-tête obligatoire `nom_origine,nouveau_nom` (ou `original_name,new_name`), une ligne par variable ; c'est aussi le format que l'outil écrit à l'export, pour que la sortie d'une vague serve d'entrée à la suivante. Une table ne donne que des noms : elle n'apparie que par nom d'origine identique, ce que le rapport signale comme fragile quand la numérotation de la plateforme a changé. |
