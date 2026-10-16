# Changements

## 0.9.0 — 2026-10-16

Des analyses dans l'outil : un catalogue d'analyses écrites et testées, calculées sur la base avec les décisions de l'équipe, chacune avec son rapport et un script R équivalent ; une IA locale facultative aide à choisir, sans jamais écrire de code (plan : `docs/plan-v0.9.md`, D-069 à D-081).

- **Six analyses** (D-069, D-070, D-077) : Tableau 1, test t (Welch par défaut, Student, Mann-Whitney), ANOVA (Kruskal-Wallis, comparaisons de Tukey), khi-carré (test exact de Fisher), corrélation (Pearson, Spearman) et régression linéaire ; tailles d'effet avec leur intervalle de confiance ; une phrase de résultat au style APA, qui décrit sans juger. Fiches validées : `docs/catalogue-analyses.md`. Calcul par SciPy et statsmodels, deux nouvelles dépendances (BSD).
- **Les décisions appliquées en mémoire** : codes manquants confirmés retirés, nouveaux noms, items inversés et scores selon la cotation, dans l'ordre des fichiers de commandes et du script de préparation ; la base n'est jamais modifiée, et rien des données n'entre dans le projet.
- **Conditions vérifiées avant le calcul** (D-074) : niveau de mesure de chaque rôle, nombre de modalités, au moins 2 personnes par groupe, 10 observations par prédicteur, prédicteurs redondants ; un refus dit sa raison, un avertissement laisse juger (groupe de moins de 5, effectifs attendus faibles, VIF supérieur à 5, normalité, variances).
- **Page « Analyses » et `ddict analyser`** : le rapport Markdown (variables, options, résultats, empreinte du codebook, versions), les tableaux en Excel et le script R équivalent (R de base et haven), écrits à côté du projet ou téléchargés. Seule la dernière analyse est gardée, en mémoire (D-078).
- **Mêmes résultats que R** : chaque analyse est vérifiée contre une base fictive aux effets connus (`etude-analyses.sav`, D-075) et contre son script R exécuté dans R, à 10⁻⁶ près. Sur une vraie base de 252 variables, les six analyses se calculent et leurs scripts R donnent les mêmes valeurs (`docs/essais/2026-10-16-essai-analyses.md`).
- **IA conseillère** (D-073, D-079, D-080) : un objectif écrit en une phrase ; le modèle local propose une à trois analyses du catalogue avec des variables du projet. Il reçoit l'objectif, le catalogue et la liste des variables, jamais une donnée ni une statistique ; sa réponse suit un schéma strict, et les conditions vérifient chaque proposition ; la personne la reprend ou non, et rien n'est calculé sans elle. Au banc de 13 objectifs, qwen2.5 7B propose la bonne analyse et les bonnes variables 9 fois sur 13 ; sur une grande base réelle, il retrouve le type d'analyse deux fois sur trois (`docs/essais/2026-10-16-ia-conseillere.md`). En ligne de commande : `ddict conseiller`.
- **Windows seulement** (D-081) : l'installation sur macOS, ses guides et sa vérification sur GitHub sont retirés.
- Guides : nouvelle section « Analyser la base », en français et en anglais.

## 0.8.0 — 2026-10-15

Du dictionnaire à l'analyse : le codebook devient un contrat d'analyse, utile à une équipe qui analyse elle-même et à une IA qui aide à écrire le code (plan : `docs/plan-v0.8.md`, D-057 à D-068).

- **Contexte d'analyse** (D-058, D-066) : page Export ou `ddict exporter --contexte`, un `-contexte.md` compact à coller dans un assistant (environ 40 tokens par variable, trois fois moins que le rapport) et un `-datapackage.json` au format Frictionless v2, valide selon ses schémas. Valeurs acceptées seulement, aucune valeur observée ; statistiques seulement sur demande (`--avec-statistiques`, D-059). À l'essai, trois assistants en ligne ont écrit une analyse juste à partir du seul contexte ; le petit modèle local, non (`docs/essais/2026-10-15-contexte-analyse-modele.md`).
- **Cotation des échelles** (D-060, D-068) : sur la page d'un groupe, items, somme ou moyenne, bornes de l'échelle, nombre minimal d'items répondus et règle des items manquants (somme proportionnelle ou somme des items répondus), nom du score, source obligatoire ; l'étendue du score est calculée. Jamais proposée par l'IA.
- **Script de préparation** (D-062) : avec les fichiers de commandes, un `-preparation.sps` et `.R` qui créent les items inversés (`_inv`) et les scores dans de nouvelles variables, sans modifier les variables d'origine ; un score déjà dans la base est comparé. Vérifié avec R et PSPP.
- **Niveaux de mesure décidés par l'équipe** (D-063, D-067) : proposés par des règles quand le fichier n'en donne pas ou quand le sien est douteux (item de grille ou texte déclaré « échelle »), décidés dans un tableau sur la page Base ; le niveau en vigueur passe dans les fichiers de commandes, la copie documentée et les codebooks.
- **Description de la base** (D-064) : ce qu'est une ligne, la structure (transversale, une vague par fichier, format large ou long), les variables de plan ; seule la structure est proposée.
- **Complétude** en tête des codebooks et sur la page Base : ce qui est décidé, sur ce qui s'applique, et ce qui reste à documenter.
- **Empreinte du codebook** dans les exports et les fichiers de commandes : un code qui change dès qu'une décision change.
- **Format du projet 0.3.0** (D-061) : les projets des versions précédentes sont convertis à l'ouverture ; un projet ouvert avec la 0.8 ne s'ouvre plus avec une version plus ancienne.
- Guides : cotation, niveaux de mesure, description, complétude, contexte d'analyse, script de préparation, et une section « Utiliser le contexte d'analyse avec une IA », en français et en anglais.

## 0.7.1 — 2026-10-15

- **Noms décidés dans le tableau** (D-056) : colonne « Décision » (Accepter, Rejeter) à côté du nom, un seul bouton « Enregistrer », et « Choisir « Accepter » pour les N noms proposés » qui remplit la colonne pour relecture. « Radical » devient « nom de base ».
- **Plus de fenêtre noire sous Windows** (D-055) : l'icône ouvre l'outil dans sa propre fenêtre, et fermer cette fenêtre arrête l'outil. Bouton « Quitter l'outil » en bas de la barre latérale, partout (aussi dans le navigateur et sur Mac). Sans le moteur d'Edge, l'outil s'ouvre dans le navigateur comme avant ; ses messages de démarrage vont dans `journal.txt`, à côté de la liste des projets récents.

## 0.7.0 — 2026-10-15

Les exports bruts de SurveyMonkey sont lus juste, et les variables se renomment, d'une vague à l'autre (plan : `docs/plan-v0.7.md`, D-043 à D-054). Mis au point sur deux vraies bases, hors du dépôt et décrites par leurs seuls faits de structure, puis vérifié sur une base de contrôle écrite après coup et sur trois vagues réelles d'une même étude (`docs/essais/`).

- **Exports SurveyMonkey reconnus** (`.sav`, `.xlsx`, `.csv`) : la deuxième ligne d'en-tête d'un `.xlsx` ou d'un `.csv` n'est plus lue comme un participant, et ses colonnes reçoivent les noms du `.sav` (D-044). Les conventions de la plateforme sont décrites comme des données, pour qu'une autre plateforme s'ajoute plus tard.
- **Structure du sondage** lue dans les noms (`q0003_0004`, 4ᵉ énoncé de la 3ᵉ question) : chaque grille est un groupe, chaque question à cocher un groupe « réponses multiples » avec sa variable « autre » ; une variable est rattachée à sa question quand leurs textes concordent. Sur une vraie base, 103 variables de questions sur 104 rattachées par la structure, toutes au texte concordant, sans IA.
- **L'en-tête de l'export Excel comme questionnaire**, troisième format avec le PDF et le texte (D-045) ; questionnaires `.txt` numérotés, PDF à titres de colonnes sur plusieurs lignes et grilles sur plusieurs pages mieux lus, et contrôlés par la structure de la base.
- **Corrections tirées des vraies bases** : plus de faux groupe formé par le préfixe `q`, une grille n'est plus coupée par un item écarté, un item qui contient le verbe « identifier » n'est plus un identifiant, les dates de passation en texte sont reconnues, les codes « Ne sais pas » ou « Préfère ne pas répondre » sont proposés comme codes manquants (D-047), et le niveau `scale` d'un item étiqueté est signalé.
- **Renommer les variables** : page « Noms » et `ddict renommer` (D-048 à D-050). Noms proposés par des règles (noms fixes des variables de plateforme, `<préfixe>_<rang>` pour une grille dont l'équipe a donné le préfixe, radical tiré des mots de la question), marque de vague (`_t2`), vérification de chaque nom, corrections dans le tableau et acceptation par grille ou par question avec la liste exacte.
- **Reprendre les noms d'une vague précédente**, depuis son fichier projet, sa copie documentée ou une table de noms (D-052) : appariement par les étiquettes, les étiquettes de valeurs et la question, jamais par le seul numéro ; une question reformulée est montrée comme candidate, jamais appariée seule. Rapport des variables ajoutées, retirées et des étiquettes de valeurs changées.
- **Exports aux nouveaux noms** : colonne « Nom d'origine » et onglet « Correspondance » du codebook, `RENAME VARIABLES` en tête de la syntaxe SPSS, renommage en tête du script R, copie documentée aux nouveaux noms, et la table de noms qui servira à la vague suivante. Vérifié avec R et PSPP.
- **Radicaux proposés par le modèle** (D-051) : mesurés au banc, ils ne font pas mieux que les règles ; ils restent en ligne de commande seulement (`ddict renommer --modele`).
- **Le `.sav` comme format de référence** (D-054) : les guides le recommandent, et la page « Base » dit, pour un autre format, ce que l'outil a dû deviner.
- **Format du projet 0.2.0** : un projet des versions précédentes s'ouvre tel quel ; un projet ouvert avec la 0.7 ne s'ouvre plus avec une version plus ancienne.
- Guides : exports SurveyMonkey et nouvelle section « Renommer les variables », en français et en anglais.

## 0.6.0 — 2026-10-14

Des rattachements aux questions plus complets, et moins à corriger (plan : `docs/plan-v0.6.md`, D-038 à D-042). Au banc d'essai avec qwen2.5 7B, 89 rattachements justes sur 98 au lieu de 82 ; sur une base de contrôle qui n'a servi à aucun réglage, 20 sur 23 au lieu de 17 (`docs/essais/2026-10-14-base-controle.md`).

- **« Aucune question » proposée** en tête de liste quand des indices forts la rendent probable : identifiant probable, date de passation récente, score calculé (nom en « total », « score »… ou somme exacte des items d'une grille, vérifiée au profilage ; seul le fait est gardé). Ces variables ne sont plus rattachées à tort (D-039).
- **Questions voisines** : pour une variable sans question candidate (« How old are you? » pour `age`), les questions situées à cet endroit du questionnaire, au plus 6, sont proposées en tête de liste et envoyées au modèle comme voisines (prompt `link-v3`) (D-040).
- **Désaccord signalé** : quand le calcul est sûr de son choix et que le modèle en choisit un autre, la proposition du modèle est gardée mais signalée, et laissée hors des décisions groupées (D-041).
- **Banc d'essai** : le rapport classe chaque rattachement manqué (aucune candidate, mauvais choix, variable sans question rattachée, sans réponse), et une quatrième base fictive, sur l'activité physique, s'y ajoute après avoir servi de contrôle (D-042).
- Guides : rattachements (« aucune question », questions voisines, désaccords), en français et en anglais.

## 0.5.0 — 2026-10-14

L'outil existe aussi en anglais et s'installe sur un Mac (plan : `docs/plan-v0.5.md`, D-031 à D-037). **L'anglais et macOS sont à l'essai** : la traduction n'a pas encore été relue par une personne anglophone (D-034), et l'installation sur Mac a été vérifiée sur un Mac de GitHub, pas encore par une personne sur son propre Mac (D-035).

- **Interface en anglais** : « Français · English » sur l'accueil, appliqué aussitôt et gardé sur l'ordinateur ; toute l'interface et la ligne de commande traduites, avec des noms anglais pour les commandes et les options (`ddict export --work`, `--replace`…). Glossaire des termes : `docs/glossaire-traduction.md` ; tableur de relecture : `scripts/tableur_relecture.py`.
- **Codebook en anglais** : la langue du codebook se choisit à l'export (`--langue en`), indépendamment de celle de l'interface ; elle vaut pour les en-têtes, les notes, la provenance, le rapport et les commentaires des fichiers de commandes. Ce que l'équipe a écrit n'est jamais traduit. Les nombres, les deux-points et les guillemets suivent la langue.
- **Études menées en anglais** : chaque projet a sa langue (D-032), devinée d'après le questionnaire ou les étiquettes et modifiable sur la page « Base » ; les consignes au modèle et ce qui est envoyé avec les données suivent cette langue ; les signaux d'invention reconnaissent l'anglais. Une version anglaise de l'étude fictive sur le sommeil s'ajoute aux exemples et au banc d'essai.
- **macOS** : `installer.command` et `desinstaller.command`, une icône dans Applications et sur le bureau ; essai automatique sur un Mac de GitHub (`.github/workflows/macos.yml`, lancé à la main).
- **Mise à jour et désinstallation** : un outil ouvert est fermé d'abord, avec l'accord de la personne (Windows et Mac).
- **Le dépôt GitHub est public** (D-037).
- Guides : `docs/installation-macos.md`, et les guides en anglais dans `docs/en/`.

## 0.4.0 — 2026-10-14

Les décisions passent du codebook aux données, et le choix du modèle se fait en connaissance de cause (plan : `docs/plan-v0.4.md`, D-025 à D-029).

- **Codes suspects confirmés** : une valeur comme 999 ou −9, isolée loin des autres, se confirme comme code manquant ou comme vraie valeur, par une personne seulement (D-028). Le codebook, les fichiers de commandes, la copie documentée et les messages au modèle en tiennent compte ; filtre « Codes suspects » et ligne du tableau de bord.
- **Fichiers de commandes** SPSS (`.sps`) et R (`.R`, haven) qui appliquent à vos données les décisions acceptées : libellés, étiquettes de valeurs, codes manquants, niveaux de mesure. Aucune valeur n'est recodée ; les items inversés sont suggérés en commentaire. Le script R appliqué au CSV fictif redonne les métadonnées du `.sav` ; la syntaxe SPSS est vérifiée avec PSPP (D-027). Pas de fichier Stata, faute d'avoir pu l'essayer dans Stata (D-030). Page « Export », ou `ddict exporter --syntaxe`.
- **Copie documentée de la base** (`.sav`), à côté de l'original, vérifiée case par case avant d'être annoncée, jamais écrite par-dessus sans accord ; aussi à partir d'un CSV, d'un fichier Stata, SAS ou Excel (D-026). Page « Export », ou `ddict documenter`.
- **Décisions groupées** avec aperçu obligatoire : accepter d'un coup les rattachements où le modèle et le calcul s'accordent, ou les étiquettes de valeurs d'un groupe, après avoir vu la liste exacte et décoché ce qui ne convient pas (D-029). À l'essai, environ un rattachement sur cinq de la liste était faux sur une vraie base : l'aperçu le dit.
- **Banc d'essai des modèles** : sur deux bases fictives au corrigé connu, mesure des rattachements justes, des inventions signalées et de la durée d'un modèle installé. Page « IA locale », ou `ddict evaluer`. Une **seconde base fictive** (enquête auprès de familles, CSV sans étiquettes) s'ajoute à l'étude sur le sommeil.
- **Recommandation de modèle** selon le matériel, d'après l'essai de trois modèles : qwen2.5 7B avec une carte graphique, qwen2.5 3B sans, ou aucun modèle.
- Guide : nouvelle section « Appliquer vos décisions à vos données » ; scénario manuel prolongé.
- **Script R** : l'exemple et le guide lisent un fichier SPSS avec `haven::read_sav(…, user_na = TRUE)` ; sans cette option, R effaçait les codes manquants déjà déclarés (trouvé à l'essai du guide, `docs/essais/2026-10-14-essai-guide-0.4.md`).
- **Installateur** : si l'outil est ouvert pendant une mise à jour, il propose de le fermer d'abord ; auparavant, la mise à jour échouait à moitié et l'outil ne démarrait plus (trouvé à l'essai de 0.4.0).

## 0.3.0 — 2026-10-14

Tout le parcours se fait dans le navigateur, et l'outil s'installe par un double-clic (plan : `docs/plan-v0.3.md`, D-019 à D-024).

- **Installateur Windows** : `installer.bat` installe uv et l'outil dans le dossier de l'utilisateur, sans droits d'administrateur, crée l'icône « Dictionnaire de données » (menu Démarrer et bureau), vérifie Ollama et ne télécharge le modèle que si la personne le demande ; `desinstaller.bat` retire l'outil sans toucher aux projets (D-021).
- **Accueil** : `ddict` seul, ou l'icône, ouvre l'interface. Nouveau projet à partir d'une base choisie avec la fenêtre « Ouvrir » de Windows (D-020), ouverture d'un projet, projets récents effaçables (D-024). Un nouveau double-clic sur l'icône rouvre l'onglet au lieu d'échouer.
- **Pages** : Base (résumé du profil), Questionnaire (lecture, questions trouvées, remplacement), Glossaire, IA locale, Variables, Groupes, Export ; un **tableau de bord** dit ce qui attend, dans l'ordre recommandé, et mène à la bonne page.
- **IA depuis l'interface** : détection d'Ollama et des modèles (adresse de l'ordinateur seulement), aperçu exact de ce qui serait envoyé, rattachement et libellés lancés bloc par bloc avec une barre de progression, bouton « Arrêter » et reprise (D-022, D-023).
- **Export depuis l'interface** : version finale ou de travail, texte omis par groupe, fichiers écrits à côté du projet ou téléchargés ; même codebook que `ddict exporter`.
- **Rattachement** (prompt `link-v2`) : les questions répétées à l'identique et les questions de suivi se distinguent par la question qui les précède. Sur la base publique d'essai, 14 des 27 cas difficiles sont justes au lieu de 9.
- **Nouveau signal** : une description qui présente l'étendue observée comme celle de l'échelle.
- Guide réécrit sans ligne de commande ; scénario manuel refait depuis l'accueil.

## 0.2.0 — 2026-10-14

Le questionnaire de l'étude devient une source documentée (plan : `docs/plan-v0.2.md`, D-011 à D-018).

- **Questionnaire** : `ddict questionnaire` lit un questionnaire PDF (SurveyMonkey, LimeSurvey, REDCap…) ou texte et le découpe en questions, options et grilles, sans IA ; les grilles douteuses sont marquées « à vérifier » (D-012, D-017 : nouvelle dépendance pypdf).
- **Glossaire des sigles** : définitions repérées dans le questionnaire (« thérapie cognitivo-comportementale (TCC) ») ou saisies par l'équipe, jamais par l'IA ; sigles probables des noms de variables signalés (D-015). Nouvelle vue « Glossaire » dans l'interface.
- **Rattachement des variables aux questions** : `ddict rattacher` calcule des questions candidates (mots, sigles, séries numérotées, familles de noms, ordre), le modèle local peut choisir parmi elles par identifiant, une personne décide dans l'interface (D-013). Filtre « Sans question ».
- **Prompt `variables-v3`** : le modèle reçoit le texte exact des questions dont le rattachement est accepté et le glossaire accepté. Sur la base publique d'essai, « OCF » est compris dans 30 variables sur 46 (aucune avec v2) et aucun sens de code n'est plus inventé. Un libellé qui donne le sens d'un sigle absent du glossaire est signalé. Blocs de 8 variables par défaut.
- **Étiquettes de valeurs tirées des options de réponse**, sous une règle stricte et avec la mention « ordre supposé, à vérifier » (D-016) ; nouvelle origine « questionnaire » des valeurs suivies (D-018).
- **Variantes d'écriture** d'une même réponse signalées (« Français », « français », « Francais »), à partir des catégories visibles seulement.
- **Nouveaux formats** : Stata (`.dta`), SAS (`.sas7bdat`) et Excel (`.xlsx`).
- **Exports** : texte exact des questions rattachées, onglet « Glossaire », provenance du questionnaire et des étiquettes ; rien de la page de consentement. Texte des items d'un instrument protégé omis à la demande (case à cocher par groupe, ou `ddict exporter --sans-texte G3`, D-014).
- Guide mis à jour avec l'ordre recommandé : questionnaire, glossaire et rattachements révisés, puis enrichissement.
- Essais consignés dans `docs/essais/` (découpage d'un questionnaire réel, rattachement, v2 contre v3, étiquettes de valeurs, variantes).

## 0.1.2 — 2026-10-13

Corrections après un essai sur une base publique réelle (152 variables, exportée par R).

- Les valeurs `NA`, `N/A`, `NaN`, `#N/A` et `NULL` des CSV sont lues comme des cases vides, et le codebook indique combien (D-010). Sur la base d'essai, 129 variables sont maintenant reconnues comme numériques au lieu de 4.
- Les dates écrites `jj/mm/aaaa` (ou `mm/jj/aaaa` quand les valeurs l'imposent) sont reconnues.
- Une variable qui n'a qu'une valeur et des cases vides est présentée comme une case à cocher probable, plutôt que comme une variable constante.
- Confidentialité, moins de fausses alertes : « reconnaissance » n'est plus pris pour une date de naissance ; une case à cocher nommée « identification » n'est plus un identifiant ; des réponses longues réparties en quelques catégories fréquentes ne sont plus du texte libre ; le pays de naissance a sa propre raison (« nom de lieu de naissance »).
- IA : un bloc n'est plus rejeté quand le modèle répond aussi pour une variable voisine qu'on lui avait montrée ; un nom comme « EQ-5D » est signalé comme nom d'instrument ; l'encadré « libellé deviné » n'apparaît plus quand le fichier n'a aucune étiquette (CSV), où il signalait toutes les variables.
- Le décompte « avec signalements » affiché par `ddict profiler` est le même que celui du filtre de l'interface.

## 0.1.1 — 2026-10-13

Corrections du guide d'installation, après un premier essai en conditions réelles.

- Le guide explique comment trouver le dossier de l'outil quand Windows l'extrait dans un dossier du même nom, et comment vérifier qu'on est au bon endroit.
- La base fictive se copie avec l'Explorateur, sans chemin à taper.
- Le guide précise que confirmer une inversion documente les items sans recoder les données.
- Nouveau cas dans « En cas de problème » : installation lancée hors du dossier de l'outil.

## 0.1.0 — 2026-10-13

Première version utilisable.

- Lecture des fichiers SPSS (`.sav`, `.zsav`) avec leurs étiquettes, leurs manquants déclarés et leurs niveaux de mesure, et des fichiers `.csv`, y compris ceux d'Excel en français (point-virgule, virgule décimale, Windows-1252).
- Profil de chaque variable, calculé sans IA : type, valides, manquants, étendue observée, modalités et effectifs, codes sans étiquette, doublons.
- Classement de confidentialité (identifiant probable, texte libre, quasi-identifiant) ; effectifs de moins de 5 masqués, y compris par soustraction (D-006 à D-008).
- Repérage des échelles et des items probablement inversés, avec l'alpha de Cronbach (sans IA).
- Fichier projet JSON qui garde l'origine et le statut de chaque valeur (fichier, calcul, IA, personne ; proposé, validé, corrigé, rejeté).
- Enrichissement facultatif par un modèle local (Ollama, LM Studio, llama.cpp) : libellés et descriptions proposés par blocs, reprise après interruption, aperçu de ce qui serait envoyé, adresses non locales refusées (D-009).
- Interface de révision dans le navigateur, accessible depuis l'ordinateur seulement.
- Exports : codebook Excel et rapport Markdown, avec la virgule décimale.
- Guide d'installation sous Windows : `docs/installation-windows.md`.
