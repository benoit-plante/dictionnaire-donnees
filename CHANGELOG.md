# Changements

## Non publié

Filtres, ordre aléatoire et non applicable (plan : `docs/plan-v0.21.md`, D-163 à D-172 ; feuille de route du cycle de recherche : `docs/feuille-de-route-cycle.md`).

- **Le format du projet 0.12.0** (D-172) : la condition d'une question et d'une section, l'ordre aléatoire, les items de contrôle d'attention, la condition d'une variable, les codes du non applicable et du manquant, la règle d'exclusion des items de contrôle ; rien n'est encore offert dans l'interface. Un projet 0.11.0 s'ouvre tel quel, avec le même codebook et les mêmes empreintes ; un questionnaire conçu garde son empreinte, ses versions envoyées et ses points de relecture gardés. Un projet enregistré par cette version ne s'ouvre plus avec la 0.20.2.

## 0.20.2 — 2026-10-20

Un nouvel accueil et un titre pour chaque projet (plan : `docs/plan-accueil.md`, D-159 à D-162), et les variables écartées du codebook (D-158). Pour l'accueil et le titre, ni le calcul, ni la porte de confidentialité, ni l'IA, ni les fichiers produits ne changent. Le format du projet passe de 0.9.0 à 0.11.0 en une fois (le format 0.10.0 n'a jamais été publié) : un projet enregistré par la 0.20.2 ne s'ouvre plus avec la 0.20.1. Le thème sombre est mis de côté.

- **Le titre d'un projet** (D-161, format du projet 0.11.0) : un titre écrit par l'équipe, montré à la place du nom du fichier dans « Mes projets », en tête de la barre de gauche du projet ouvert et par `ddict projets lister` ; **Renommer** dans le détail du projet, sur l'accueil, et sous le titre d'un projet ouvert ; `ddict projets renommer <projet> "<titre>"` (ou `--effacer`). Aucun fichier n'est renommé ; le titre n'est jamais envoyé à l'IA et n'entre pas dans l'empreinte du codebook. Un projet 0.11.0 ne s'ouvre plus avec la 0.20.1.
- **L'accueil en onglets** (D-160) : la barre de gauche devient le menu de l'accueil (Mes projets, Nouveau projet, Concevoir un questionnaire, Ouvrir un projet, Réglages) ; les projets récents et la recherche dans un dossier sont sous « Ouvrir un projet », la langue sous « Réglages ». Un rechargement garde l'onglet ouvert. **Mes projets** : la liste des projets suivis dans la barre de gauche (nom et phase, ou ce qui ne va pas) ; un clic montre le détail du projet sans l'ouvrir : chemin, phases, avancement du codebook, chaque tâche avec son bouton, plan, carnet, base, questionnaire, fichiers produits à côté, **Ouvrir**, **Ouvrir le dossier**, **Ne plus suivre**, **Le retrouver…**. « Accueil » ramène au projet qu'on quittait.
- **« Essayer l'outil » retiré de l'accueil** (D-159, remplace D-125) : un dossier `Documents\Dictionnaire de données - essai` déjà créé reste là, et son projet s'ouvre comme un autre. `etude-sommeil.sav` n'est plus dans le paquet installé ; il reste dans `exemples\bases-fictives`.
- **Écarter une variable du codebook** (D-158, format du projet 0.10.0) : sur la fiche d'une variable, avec sa raison ; elle reste dans la base et dans le projet, mais quitte le codebook (une section « Variables écartées » la nomme, avec sa raison), le contexte d'analyse (le Data Package garde la colonne, sans rien en dire), les compteurs à documenter, les noms proposés, les choix des analyses, des règles d'exclusion et des recodages, et les messages à l'IA. Refusé tant qu'elle sert, chaque usage dit. Filtre **Écartées** ; **Remettre dans le codebook**. Un projet 0.10.0 ne s'ouvre plus avec la 0.20.1.
- Guides : l'accueil et « Suivre plusieurs projets » réécrits, le renommage, en français et en anglais ; le scénario manuel gagne les étapes 97 à 102 ; `scripts/captures.py` photographie aussi les onglets de l'accueil.
- **Revoir** : un « Garder le projet » de la comparaison avec LimeSurvey se défait par **Revoir**, sans fermer l'outil (vu au second essai de l'auteur, 2026-10-20).

## 0.20.1 — 2026-10-20

Ce que l'essai de l'auteur a montré, le 2026-10-20, sur un questionnaire fictif conçu, importé dans LimeSurvey Cloud 7.6, puis reçu en `.sav`.

- **Le rapport de conformité** dit les textes de la base qui diffèrent du questionnaire (une question reformulée dans LimeSurvey), et retrouve une question dont le code a changé dans LimeSurvey par ses textes, quand ils ne laissent aucun doute : ses variables reprennent alors les décisions prévues (question, groupe, description…), et le rapport les nomme « retrouvées sous un autre nom » (D-157).
- **La relecture** signale, pour un questionnaire en français, l'espace manquante avant « ? », « ! », « : » ou « ; ».
- **L'éditeur** : dans une grille, les énoncés viennent avant les colonnes, comme dans le Word et dans LimeSurvey.
- **Le Word de travail** ne donne plus de code à l'option « Autre » (LimeSurvey n'en a pas), et dit la variable d'un texte d'affichage « toujours vide ».
- **Correction** : une question ouverte deux fois dans l'éditeur, puis enregistrée avec d'autres choix, laissait l'avertissement « Saisie non enregistrée » alors que tout était enregistré (vu à l'essai de l'auteur, 2026-10-20).

## 0.20.0 — 2026-10-19

Concevoir le questionnaire dans l'outil, avant la collecte (plan : `docs/plan-v0.20.md`, D-143 à D-156). Le numéro 0.19 est sauté : le dossier d'étude, prévu en v0.19, viendra plus tard. Aucune IA ajoutée, aucune source déposée (elles viennent ensuite) ; la chaîne lire → profiler → exporter d'une base existante ne change pas.

- **Le projet sans base** (D-145, format 0.9.0) : un projet créé par **Concevoir un questionnaire** (accueil, ou `ddict questionnaire creer`) a un questionnaire structuré et des **variables prévues**, sans profil ; les pages qui montrent la base l'attendent, avec un bouton vers le questionnaire. La page « Base » s'ouvre : sa description, ses niveaux de mesure et ses variables sensibles se décident avant la collecte.
- **La phase « Concevoir »** (D-149), en tête du menu de ces projets : **Questionnaire** (l'éditeur : sections, questions de chaque nature, choix et énoncés avec leurs codes, provenance des textes, code de la question), **Relecture** (les points calculés, « Garder tel quel »), **Publier**. « Mes projets » donne les phases « Concevoir » et « En collecte » ; le tableau de bord commence par les points de relecture.
- **Le Word** (D-152), en deux versions, pour le comité d'éthique et de travail ; mêmes octets pour le même questionnaire ; `ddict questionnaire word`.
- **Le fichier pour LimeSurvey** (D-148), la structure en texte à colonnes de LimeSurvey Cloud 7.6, relu par l'outil pour vérifier qu'il redonne le questionnaire ; ce qui empêcherait l'importation refuse l'écriture ; les étapes d'importation ; `ddict questionnaire limesurvey`. Importé pour de vrai dans LimeSurvey Cloud 7.6 (`docs/essais/2026-10-19-limesurvey-importation.md`) : chaque question conforme, les limites de codes confirmées, le réexport sans différence.
- **La boucle** (D-150) : **Marquer comme envoyé** garde une copie ; ce qui a changé depuis chaque version envoyée est montré, et un avertissement le dit ; le réexport de LimeSurvey se compare au projet par les codes, chaque question réglée par « Reprendre dans le projet » ou « Garder le projet ».
- **La base est arrivée** : page « Base » ou `ddict profiler <base> --projet <projet>` ; chaque variable reprend les décisions de sa variable prévue ; un **rapport de conformité** (variables absentes, non prévues, codes hors des codes prévus, étiquettes, types), sur la page et en Markdown à côté du projet.
- **LimeSurvey lu** (D-148, D-155, D-156) : la structure `.lss` ou `.txt` comme questionnaire ; ses exports de réponses (CSV, Excel, `.sav`) reconnus, rattachés par les codes des questions. lxml déclaré comme dépendance directe.
- Guides : « Concevoir un questionnaire, avant la collecte », en français et en anglais ; le scénario manuel gagne les étapes 90 à 96 ; `scripts/captures.py` photographie aussi les pages de Concevoir.

## 0.18.0 — 2026-10-19

L'IA par une clé d'API (plan : `docs/plan-v0.18.md`, D-134 à D-142). La version change de moteur, pas de fonctions : les quatre usages de l'IA (libellés et descriptions, rattachement, noms de base, conseillère) et le banc d'essai restent ; ni le calcul, ni les exports, ni le carnet, ni l'ébauche d'article ne changent.

- **Aucune donnée de participant ne quitte le poste** (D-134, D-136) : la règle « Rien ne quitte le poste » devient celle-ci. L'IA est un service externe qui ne reçoit que des **métadonnées** : noms, étiquettes des variables et des valeurs, codes manquants déclarés, texte des questions acceptées, sigles acceptés, type et niveau de mesure. Plus de codes observés ni de proportions, de manquants, de minimum, de maximum, de moyenne ni d'années, et plus l'étendue observée des codes d'un groupe, que la conseillère envoyait encore. Un test à chaînes témoins le vérifie sur les quatre usages.
- **Anthropic, ou le serveur d'une université** (D-135) : deux protocoles, une adresse en HTTPS (ou sur cet ordinateur), sans proxy ni redirection. **Ollama est retiré** : de l'installateur, de l'interface, de la ligne de commande et des guides. Par défaut `claude-haiku-5-5`, avec une réflexion moyenne (D-140).
- **La clé d'API** (D-137) : gardée dans le gestionnaire d'identifiants de Windows, saisie dans un champ masqué de la page « IA » ou par `ddict ia cle` (jamais en argument), jamais écrite ailleurs ni affichée ; « Oublier la clé ». Le désinstalleur demande avant de l'effacer.
- **Une case par projet** (D-138) : « Permettre l'envoi des métadonnées de ce projet à l'IA », non cochée par défaut, enregistrée dans le projet avec sa date (format 0.8.0 ; un projet de la 0.17 s'ouvre non permis). Sans elle, rien ne part ; l'aperçu des messages reste toujours possible. `ddict ia autoriser` et `ddict ia interdire`.
- **La page « IA »** (au lieu de « IA locale ») : service, adresse, modèle, réflexion, clé, **Tester la connexion** (rien d'un projet n'est envoyé, rien n'est facturé), et **Ce qui part** : la liste, et la conservation chez Anthropic avec sa source.
- **Des blocs plus grands** (25 variables pour les libellés, 20 pour le rattachement) ; **la conseillère** envoie à Anthropic le message entier, libellés et items compris (D-142) ; **les noms de base** se font proposer sur la page « Noms » (D-141). Le numéro de chaque requête, ses jetons et, en cas de refus, l'explication du service sont gardés dans le dossier des envois.
- **Le banc d'essai** compte les jetons et le coût de chaque passage, demande confirmation avant de dépenser, et mesure sur demande les libellés au niveau 2 (`ddict evaluer --niveau-2`, le banc seulement). Essai du 2026-10-19 (`docs/essais/2026-10-19-anthropic.md`) : 113 rattachements justes sur 121 (110 pour le calcul seul), aucun libellé signalé, 7 noms de base sur 10 égaux au corrigé (3 pour les règles), la conseillère juste 13 fois sur 13 ; environ 0,02 $ le banc entier avec Haiku 5.5.
- **Ligne de commande** : le service, l'adresse et le modèle viennent des réglages de la page « IA » (`--protocole`, `--adresse`, `--modele` pour les changer) ; `ddict rattacher` et `ddict renommer` appellent l'IA avec `--ia`.
- Guides : « Obtenir une clé d'API » (avec une limite de dépenses), « Ce qui part » ; le scénario manuel gagne les étapes 83 à 89.

## 0.17.0 — 2026-10-19

Plusieurs projets, et aucune décision perdue (plan : `docs/plan-v0.17.md`, D-129 à D-133). Ni le calcul, ni les exports, ni le format du fichier projet, ni les règles de confidentialité ne changent ; aucune IA ajoutée.

- **Jamais écraser sans prévenir** (D-129, D-130) : l'outil retient l'empreinte (SHA-256) du projet et du carnet tels qu'il les a lus, et refuse d'enregistrer si le fichier a changé depuis : autre onglet, autre personne sur un dossier partagé, ligne de commande. Dans l'interface, un bandeau le dit dès l'affichage suivant ; une décision refusée est rappelée (la page, le bouton et ce qu'il décidait, ce qui était tapé), et la page revient au projet tel qu'il a été lu, sans rien montrer de décidé qui ne soit écrit ; **Recharger le projet** lit le projet tel qu'il est, et la décision reste affichée, « Décision à refaire ». Rien n'est jamais fusionné à la place de la personne. En ligne de commande, un message et le code de sortie 2. Une date de fichier qui bouge sans changement de contenu ne dit rien. Le fichier écrit est le même, octet pour octet.
- **Un enregistrement interrompu** laisse un fichier `.tmp` : il est signalé à l'ouverture du projet (interface et ligne de commande), jamais supprimé par l'outil. **Un fichier tenu un instant** par OneDrive ou un antivirus : trois essais, puis « Le fichier est occupé… : rien n'est enregistré », le projet intact.
- **Mes projets** (D-131, D-133) : l'accueil commence par un tableau des projets suivis, le plus récent en haut : phase (Documenter, Analyser, Rédiger, d'après les fichiers du projet), codebook documenté, ce qui attend, plan, carnet (retenues, à confirmer, à recalculer), base trouvée ou non, date. Lu dans les projets et les carnets, jamais dans les bases ; 30 projets en une demi-seconde. Un clic sur le nom ouvre le projet là où quelque chose attend.
- **Suivre un projet** (D-131) : d'office à la création (accueil et `ddict profiler`), sauf l'essai sur la base fictive ; « Suivre ce projet » à côté d'un projet récent et dans la barre latérale ; « Ne plus suivre », qui ne touche aucun fichier. La liste est gardée sur l'ordinateur (`%APPDATA%\ddict\projets-suivis.json`), chemins seulement, sans limite ; un projet déplacé reste, « Introuvable », et **Le retrouver…** donne son nouveau chemin.
- **Chercher les projets dans un dossier** (D-132) : sur 4 niveaux, sans ouvrir aucun fichier (un fichier OneDrive en ligne seulement n'est pas téléchargé) ; dossiers cachés, système et de programmes passés, jonctions jamais suivies ; rien de coché au départ.
- **`ddict projets`** (`ddict projects`) : `lister`, `suivre`, `retirer`, `chercher` (`--suivre`) ; en anglais `list`, `follow`, `remove`, `search` (`--follow`).
- Le désinstalleur demande avant d'effacer les listes des projets récents et suivis.
- Guides : « Suivre plusieurs projets », en français et en anglais ; le scénario manuel gagne les étapes 76 à 82.

## 0.16.0 — 2026-10-18

L'interface guide la personne de la base à l'article (plan : `docs/plan-v0.16.md`, D-121 à D-128). Ni le calcul, ni les formats de fichier, ni les règles de confidentialité ne changent ; aucune IA ajoutée. Trois lots : des corrections locales, la navigation et la progression, un seul geste pour décider et enregistrer.

- **Rien de proposé ne s'affiche comme décidé** (D-126) : les items inversés, la cotation (items, calcul, bornes, items répondus au minimum, règle des manquants), l'étendue théorique, les seuils et la question à rattacher partent vides ; un bouton « Reprendre… » nomme ce que l'outil propose et le met dans le champ, sans rien enregistrer.
- **Le glossaire** (D-121) : « Accepter » prend la définition affichée, corrigée ou non ; « Rejeter » juste à côté ; « Tout accepter (N)… » montre la liste exacte avant d'accepter.
- **Aucun écran blanc** : la page « Variables » s'ouvre sur un filtre qui contient des variables, et un filtre vide le dit au centre avec les filtres non vides ; sur « Plan », ce qui manque pour figer est une liste à cocher, plus des erreurs rouges.
- **Le thème** (D-123, D-128) : clair, bleu ardoise pour les actions, le rouge réservé aux erreurs, toutes les couleurs de texte au-dessus de 4,5:1 ; les explications qui portent une décision en texte normal.
- **Des boutons dans les messages** qui renvoient à une autre page, déjà remplie (« Définir anx » ouvre le glossaire avec le sigle).
- **Analyses** : sous « Lancer l'analyse », la barre « Ajouter au carnet · Word · Excel · Script R », puis le résultat ; une analyse déjà au carnet le dit (« Déjà au carnet : A3 »), même dans une autre séance.
- **L'accueil** (D-125) : les projets récents en tête, avec leur dossier et leur date ; « Essayer avec la base fictive » copie la base et son questionnaire dans `Documents\Dictionnaire de données - essai` et ouvre le projet.
- **Finitions** : « Choisir… » au lieu de « Choose an option » ; « — » au lieu de « None » ; largeurs de colonnes ; bornes entières (« 1 », pas « 1.00 ») ; groupes nommés par ce qu'ils sont ; « Précédente » et « Suivante » sur la page « Variables » ; l'aide de « Premier tableau » et « Première figure » ; plus d'avertissement `use_container_width`.
- **Corrections** : le paquet de reproduction donne les mêmes octets quelle que soit l'heure ; la page « Plan » ne plante plus sans la base quand un score figure parmi les variables.
- **La navigation par phases** (D-122) : un menu Documenter, Analyser, Rédiger, puis Réglages pour l'IA locale, au lieu de treize boutons au même niveau ; chaque page dit ce qui y attend, ou ✓ ; chaque page garde son adresse au rechargement.
- **Une progression honnête** : « Codebook documenté à N % », partie par partie, jamais pleine sur un projet neuf ; le tableau de bord continue jusqu'à l'article (plan à figer, chiffres à confirmer au carnet, analyses impossibles, trous de la Méthode, ébauche à vérifier).
- **Les pages longues en onglets** : Base (le résumé d'abord), un groupe, le résultat d'une analyse ; l'onglet ouvert reste après une action, et un bouton d'une autre page ouvre le bon onglet.
- **Captures d'écran automatiques** pour le développement (D-127) : `scripts/captures.py` photographie chaque page à 1400 × 900 et 900 × 600 avec le Microsoft Edge du poste (Playwright, outil de développement seulement).
- **Une carte de décision sur toutes les pages** (D-121) : la valeur, son origine et son statut, le champ, puis « Accepter », qui prend la valeur affichée, corrigée ou non, et « Rejeter », côte à côte ; une fois décidée, « Enregistrer ». Pour le libellé, l'unité, la description, la question, les étiquettes de valeurs, la confidentialité, un sigle, et, sur la fiche d'une variable, le niveau de mesure et le nouveau nom proposés.
- **Un seul « Enregistrer » par section, et rien de perdu** (D-124) : les textes d'une variable, chaque onglet d'un groupe, la description de la base ; « Modifications non enregistrées » à côté du bouton ; ce qui est tapé et laissé sans être enregistré devient un brouillon, signalé sur la page d'arrivée (« Revenir », « Abandonner ») et remis dans ses champs à sa place ; « Quitter l'outil » demande confirmation. Une seule action pour proposer les noms.
- **Les variables qui conviennent d'abord** : dans chaque liste d'une analyse ou d'une hypothèse, celles qui conviennent au rôle en tête, puis les autres avec leur raison (« 3 modalités : choisir les deux comparées », « niveau ordinal », « niveau échelle ») ; aucune analyse ne devient possible là où elle ne l'était pas.
- Guides en français et en anglais ; le scénario manuel gagne les étapes 64 à 75.

## 0.15.0 — 2026-10-18

Recoder une variable, vérifier les chiffres d'un manuscrit, préparer le dépôt (plan : `docs/plan-v0.15.md`, D-117 à D-120 ; fiche validée : `docs/verification-depot.md`). Aucune IA dans cette version.

- **Le recodage** (D-120) : une variable dérivée, gardée comme une décision du projet avec sa raison, jamais comme une colonne. Regrouper des modalités (« Femme » ; « Homme ou autre identité »), y compris des catégories écrites en texte, ou découper un nombre ou un score en classes (« moins de 30 », « 30 à moins de 45 », « 45 et plus »). Une valeur observée sans groupe refuse le recodage ; les effectifs de chaque nouvelle modalité sont montrés avant d'enregistrer. Calculé en mémoire après les scores et avant les exclusions : une analyse, une règle d'exclusion, un sous-groupe ou une hypothèse peuvent porter sur lui. Il entre dans les scripts de préparation SPSS (`RECODE … INTO`) et R, le script R maître, le codebook (feuille « Recodages »), le contexte d'analyse et la Méthode. Le projet passe au format 0.7.0 (un projet plus ancien s'ouvre tel quel). Un encadré « Recoder cette variable » sur la page « Variables », la liste sur la page « Groupes », et `ddict recoder` (`lister`, `regrouper`, `decouper`, `retirer` ; en anglais `ddict recode`, `list`, `group`, `cut`, `remove`).
- **Le vérificateur des chiffres** (D-117, D-118) : il lit un manuscrit Word, l'ébauche retouchée ou un article écrit sans l'outil, y repère les statistiques écrites au style APA, en français ou en anglais, et compare chacune à ce que l'outil écrit lui-même, recalculé sur la base (sans la base, au carnet). Chaque valeur : concorde, diffère (avec la valeur attendue), signe inversé, sans origine, non reconnue. Un rapport en Markdown et en Excel, une copie `-verifie.docx` avec un commentaire Word sur chaque valeur qui ne concorde pas ; le manuscrit n'est jamais modifié. Page « Vérifier », après « Carnet », et `ddict verifier` (en anglais `ddict verify`).
- **Le paquet de reproduction** (D-119) : `<projet>-depot.zip`, prêt pour l'OSF ou Borealis, avec le codebook, le préenregistrement, le carnet, les fichiers de commandes, les scripts de préparation, le script R maître, un README à compléter et les empreintes des fichiers. Jamais la base, ni le fichier projet, ni les envois à l'IA. Bouton sur la page « Carnet » et `ddict deposer` (en anglais `ddict deposit`).
- **Corrections après l'essai et le scénario** : un sous-groupe se donne par l'étiquette d'une variable recodée, et la Méthode l'écrit par cette étiquette ; dans la phrase anglaise de l'ANOVA à mesures répétées, les moyennes ont la ponctuation anglaise.
- Essai sur la base ouverte AMATUS sans fichier dérivé, et le vérificateur passé sur l'article publié : les chiffres concordants, les signes inversés et le test bilatéral de l'article sont trouvés (`docs/essais/2026-10-18-essai-v015-amatus.md`).
- Guides : « Recoder, vérifier les chiffres, préparer le dépôt », en français et en anglais ; le scénario manuel gagne les étapes 59 à 63.

## 0.14.0 — 2026-10-18

Le catalogue élargi : cinq analyses de plus, écrites et vérifiées d'avance comme les six premières, le sous-groupe d'une analyse et le sens attendu nommé par les groupes (plan : `docs/plan-v0.14.md`, D-111 à D-116 ; fiche validée : `docs/catalogue-elargi.md`). Aucune nouvelle IA ; le conseiller facultatif connaît les nouvelles analyses.

- **Le test *t* apparié** et son pendant sans normalité, **Wilcoxon des rangs signés** : deux mesures d'une même personne ; *d*<sub>z</sub> et son intervalle ; *p* de Wilcoxon calculé comme R.
- **L'ANOVA à mesures répétées** : de 3 à 10 mesures, η² partiel, test de sphéricité de Mauchly et correction de Greenhouse-Geisser ; comparaisons deux à deux corrigées par Holm ; une figure des moyennes reliées.
- **La régression logistique binaire** : la modalité prédite au choix, les coefficients, les rapports de cotes et leur intervalle (Wald), le χ² face au modèle sans prédicteur, les *R*² de McFadden et de Nagelkerke ; une séparation complète est dite ; la figure montre les rapports de cotes sur une échelle logarithmique autour de 1.
- **La corrélation partielle** : deux variables, de 1 à 5 covariables, le *r* partiel, son intervalle (Fisher) et la corrélation simple.
- **La modération** : l'interaction de deux prédicteurs, centrés par défaut, Δ*R*², les pentes simples à −1 ÉT, à la moyenne et à +1 ÉT, avec leur figure.
- Chacune a sa phrase, son tableau et sa figure APA, son script R (R de base, vérifié à 10⁻⁶ près), sa phrase de Méthode, sa place dans le plan (effets `partial` et `interaction`), le préenregistrement et l'article.
- **Le sous-groupe** (D-113, D-116) : une analyse, une analyse du carnet ou une hypothèse peut ne porter que sur une partie des personnes (`sexe = Femme`, `age ≥ 40`, `sexe parmi …`), après les règles d'exclusion ; la phrase, chaque note de tableau et de figure, la Méthode, le préenregistrement et le script R le disent. Jamais par un identifiant, un texte libre ou une date. Le projet passe au format 0.6.0 et le carnet en version 1.3.0 (les plus anciens s'ouvrent tels quels). Un *p* corrigé est toujours confirmé quand il change (D-116).
- **Le sens attendu nommé** : sur la page « Plan », « Femme plus élevé que Homme », ou les noms des deux mesures d'un test apparié, au lieu de « le premier groupe ».
- **En ligne de commande** : `apparie`, `anova_rm`, `logistique`, `partielle`, `moderation` (en anglais `paired`, `rm_anova`, `logistic`, `partial`, `moderation`), avec `--premiere`, `--seconde`, `--mesures`, `--covariables`, `--focal`, `--moderateur`, `--evenement`, `--centrer`, et `--sous-groupe sexe eq 1` pour `ddict analyser`, `ddict carnet ajouter` et `ddict plan ajouter`.
- **L'IA conseillère** connaît les analyses nouvelles ; `scripts/banc_conseil.py --suivi` l'évalue sur six objectifs écrits pour la base de suivi.
- Une base fictive de suivi (`etude-suivi.sav`, 240 participants, trois temps de mesure) et son corrigé, pour les tests et pour essayer.
- **Corrections après l'essai et le scénario** : les tableaux et les figures d'une analyse sur sous-groupe décrivent bien les personnes du sous-groupe (la note d'un test t donnait les effectifs de toute la base) ; le conseiller refusait toute proposition qui nommait un rôle ou une méthode des nouvelles analyses ; le sens d'un test apparié parle de « la première mesure », plus de « groupe » ; l'axe logarithmique des figures est gradué en valeurs simples (0,5 ; 0,7 ; 1).
- Second essai sur la base ouverte AMATUS : les sous-groupes de l'article, choisis dans l'outil, redonnent ses chiffres, et R ceux de l'outil (`docs/essais/2026-10-18-essai-v014-amatus.md`).
- Guides : « Les analyses du catalogue élargi et le sous-groupe », en français et en anglais ; le scénario manuel gagne les étapes 54 à 58.

## 0.13.0 — 2026-10-18

Le plan d'analyse, le préenregistrement et l'ébauche d'article : les hypothèses écrites avant l'analyse, le gel et les amendements, puis un article IMRaD de la page de titre aux Références (plan : `docs/plan-v0.13.md`, D-101 à D-110 ; fiche validée : `docs/plan-analyse-article.md`). Aucune IA dans cette version.

- **Le plan d'analyse** (D-101, D-103) : les hypothèses de l'équipe, chacune liée à une analyse du catalogue, à ses variables et à l'effet qui y répond (la différence, la corrélation d'une paire, le modèle ou un prédicteur d'une régression), avec son sens attendu, son caractère (confirmatoire ou exploratoire) et sa famille ; les règles générales : seuil α tapé par l'équipe (jamais d'office), correction (Holm par défaut, Bonferroni ou aucune), justification de la taille d'échantillon, origine des données et leur état quand le plan a été écrit, déclarés par l'équipe. Le projet passe au format 0.5.0 (un projet plus ancien s'ouvre tel quel).
- **Le gel et les amendements** (D-102) : le plan figé reçoit sa date et son empreinte, et chaque hypothèse devient une analyse du carnet ; ensuite, toute modification exige une raison et devient un amendement, gardé pour toujours ; l'analyse d'origine reste au carnet, écartée. Le carnet dit l'état de chaque analyse face au plan : prévue, remplacée par un amendement, variante, exploratoire.
- **Le sens attendu et la correction** (D-103, D-104) : pour un test t, un sens attendu rend le test unilatéral ; les *p* d'une même famille sont corrigés par Holm ou Bonferroni, vérifiés contre `p.adjust` de R.
- **Le préenregistrement** (D-109) : OSF Prereg pour des données primaires, van den Akker et al. (2021) pour des données secondaires, en Word et en Markdown, écrit à partir du plan et du codebook seulement : aucun effectif ni résultat ; ce que l'outil ne peut savoir reste un trou. L'outil ne dépose rien et ne dit jamais qu'une étude a été préenregistrée.
- **L'ébauche d'article** (D-106, D-107) : page de titre et résumé en trous, Introduction avec les hypothèses, Méthode avec un paragraphe « Plan d'analyse » (origine et état déclarés, gel, α, correction, familles, amendements), Résultats par hypothèse avec le *p* corrigé, puis les analyses exploratoires, Discussion qui rappelle le sens attendu et le sens observé sans jamais juger (ni « soutenue », ni « significatif »), Références tirées des sources du codebook. Le document s'appelle `<projet>-article.docx`, avec `-article-graphiques.xlsx` et `-article-R.zip`.
- **La page « Plan »**, avant « Analyses », et **en ligne de commande** `ddict plan` (`lister`, `ajouter`, `modifier` ou `amender`, `retirer`, `deplacer`, `regles`, `figer`, `effacer --confirmer`, `preenregistrement`) et `ddict article` ; en anglais, `list`, `add`, `modify` ou `amend`, `remove`, `move`, `rules`, `freeze`, `clear --confirm`, `preregistration` et `ddict paper`. `ddict resultats` reste un autre nom de `ddict article` pour cette version. La page et les commandes écrivent les mêmes fichiers.
- **Les catégories écrites en texte** (D-110) : dans un CSV, une variable aux valeurs « oui », « non » entre dans les analyses dès que son niveau est nominal ; une case vide y est une valeur manquante ; `--modalites` accepte les codes de texte. Le script R lit le CSV comme l'outil : séparateur, marque décimale, encodage, cases vides, colonnes de texte (un CSV séparé par des points-virgules ne se lisait pas).
- **Corrections après l'essai et le scénario** : la page « Plan » choisit les deux modalités comparées d'un groupe à plus de deux modalités, comme `--modalites` ; elles sont nommées par leurs étiquettes (« Femme, Homme ») dans le plan, les amendements et le rapport d'analyse ; le formulaire ne se replie plus après une modification enregistrée ; une différence nulle au centième près n'a plus de « groupe plus élevé » dans la Discussion ; la liste des analyses en anglais a sa ponctuation anglaise ; plus de « Choose options » en anglais dans les listes.
- **Les niveaux de mesure et les codes manquants en ligne de commande** : `ddict niveaux` (`lister`, `accepter`, `rejeter`, `fixer` ; en anglais `ddict levels`, `list`, `accept`, `reject`, `set`) et `ddict codes` (`lister`, `manquant`, `valeur`, `annuler` ; en anglais `list`, `missing`, `value`, `undo`), avec les fonctions des pages « Base » et « Variables ».
- **Après le second essai** : dans le tableau d'une corrélation, le *n*, la moyenne et l'écart-type de chaque variable portent sur les personnes qui entrent dans une corrélation du tableau (plus de *n* = 820 à côté de *N* = 182) ; un même code manquant partagé par plusieurs variables se dit une fois, « Le code -1 (a, b) », dans la Méthode comme dans le préenregistrement.
- Essai sur la base ouverte AMATUS et son article publié (Artemenko et al., 2021) : les chiffres de l'outil sont ceux de l'article et de R (`docs/essais/2026-10-18-essai-plan-article-amatus.md`).
- Guides : « Le plan d'analyse, le préenregistrement et l'article », en français et en anglais ; le scénario manuel gagne les étapes du plan.

## 0.12.0 — 2026-10-17

La section Méthode : qui a été exclu et pourquoi, la qualité de la passation, l'échantillon, les instruments et les analyses, rédigés à partir des décisions de l'équipe (plan : `docs/plan-v0.12.md`, D-093 à D-100 ; fiche validée : `docs/methode-gabarits.md`). Aucune IA dans cette version.

- **Les règles d'exclusion** (D-093) : des décisions du projet, écrites par une personne, chacune avec sa raison en clair et son rang. Cinq sortes : condition sur une variable ou sur un score, complétude d'un groupe, durée de passation (son seuil exige une source), grille en ligne droite, doublons. Jamais une liste de personnes : une condition qui nommerait une valeur d'un identifiant, d'un courriel ou d'un texte libre est refusée. Le projet passe au format 0.4.0 (un projet plus ancien s'ouvre tel quel).
- **Appliquées partout de la même façon** (D-094) : dans leur rang, après les codes manquants, les noms, les items inversés et les scores ; avant chaque analyse de l'outil, dans le script de préparation SPSS et R (`ddict_exclusion`) et dans le script R maître ; jamais dans la copie documentée. Les mêmes effectifs dans l'outil, dans R et dans PSPP.
- **Le diagramme de flux** (D-098) : une figure APA dans Word, la Figure 1 du document, et le tableau de ses effectifs dans Excel.
- **Les signaux de qualité de la passation** (D-095) : durées (aussi sur des dates en texte, dont le format est détecté), grilles en ligne droite et doublons, avec le nombre de personnes que chacun toucherait. Aucun seuil par défaut, jamais appliqués seuls ; **En faire une règle** remplit le formulaire, la raison reste à écrire.
- **La fidélité** (D-096) : l'alpha de Cronbach de chaque score, recalculé sur l'échantillon analysé, avec son intervalle de confiance à 95 % (Feldt), vérifiés dans R. L'oméga est reporté.
- **Les paragraphes de la Méthode** (D-097) : Participants, Instruments et Analyses, rédigés par des phrases fixes, en français et en anglais ; un fait que le codebook ne donne pas devient un trou « [à compléter : …] », surligné dans Word, jamais deviné ; aucune formulation qui juge.
- **Le document « Méthode et Résultats »** (D-099) : les mêmes trois fichiers que la v0.11, la section Méthode avant les Résultats, tableaux et figures numérotés à la suite sur tout le document.
- **Les chiffres de la Méthode, gardés et confirmés** (D-100) : le carnet garde aussi les effectifs du flux, la description de l'échantillon et les alphas ; une règle ajoutée rend la Méthode et les analyses « changées, à confirmer », et le document attend une personne. Bouton **Tout confirmer**. Le carnet passe en version 1.1.0 (un carnet 1.0.0 s'ouvre tel quel).
- **La page « Méthode »**, après « Carnet » : les règles et leurs effectifs, le formulaire **Ajouter une règle**, le diagramme de flux, les signaux, les variables de l'échantillon et l'aperçu des paragraphes avec leurs trous. **En ligne de commande** : `ddict exclusions` (`lister`, `ajouter`, `retirer`, `deplacer`, `signaux`) et `ddict carnet echantillon` ; en anglais, `list`, `add`, `remove`, `move`, `signals` et `ddict notebook sample`. La page et les commandes écrivent les mêmes fichiers.
- **Une correction en passant** : la phrase de résultat d'une corrélation écrit *r* sans zéro initial, comme les tableaux (« r(195) = ,07 »).
- **Corrections après l'essai** : une règle qui n'exclut personne reste dans le diagramme mais pas dans la phrase des Participants (« Aucune n'a été exclue par les règles d'exclusion » si aucune n'exclut) ; les pourcentages d'une même variable ont tous une décimale, ou aucun (« 56,9 % ; 42,0 % », plus « 56,9 % ; 42 % ») ; `ddict` ne plante plus quand sa sortie est redirigée vers un fichier (`> journal.txt`) : elle s'écrit alors en UTF-8.
- Une base fictive de passation (`etude-passation.sav`) et son corrigé, aux effectifs connus, pour les tests. Essai sur une vraie base : `docs/essais/2026-10-17-essai-methode.md`.
- Guides : « La Méthode : exclusions, diagramme de flux et paragraphes », en français et en anglais.

## 0.11.0 — 2026-10-16

Le carnet d'analyses : les analyses d'une étude, dans l'ordre de l'article, recalculées quand le codebook change, réunies dans un document des résultats et un script R maître (plan : `docs/plan-v0.11.md`, D-087 à D-092 ; fiche validée : `docs/carnet-analyses.md`). Aucune IA dans cette version.

- **Le carnet** (D-087, D-088, D-091) : `<projet>-carnet.json`, à côté du projet, qui reste un dictionnaire de données. Une analyse y entre par le bouton **Ajouter au carnet** de la page « Analyses », avec les titres et les notes changés de ses tableaux et figures. Il garde ce qui a été demandé (analyse, variables par leur clé du projet, qui survit à un renommage, options), si l'analyse est retenue, et son dernier calcul confirmé : des agrégats seulement, jamais une ligne de la base, un point d'un nuage ni une étendue observée.
- **Recalculé quand une décision change** (D-089) : chaque analyse est « à jour », « recalculée, sans changement », « changée, à confirmer » (avec ce qui a changé, aux décimales de l'APA, et la nouvelle phrase) ou « impossible à calculer » (avec sa raison). Un changement non confirmé d'une analyse retenue bloque le document ; une analyse impossible en est écartée, et la fin du document le dit.
- **La page « Carnet »** : l'ordre (monter, descendre), retenir ou écarter, confirmer, retirer, les numéros du premier tableau et de la première figure, et **Produire les résultats**. Sans la base, le carnet s'affiche tel qu'il est.
- **Le document des résultats** (D-090, D-092) : `<projet>-resultats.docx`, un intertitre par analyse, sa phrase, ses tableaux et figures APA numérotés à la suite dans l'ordre du carnet ; à la fin, l'empreinte du codebook, la date, les versions et la liste des analyses. Avec `-resultats-graphiques.xlsx` (graphiques Excel natifs) et `-resultats-R.zip`, le **script R maître**, qui refait toutes les analyses retenues et range leurs valeurs dans `resultats$A1`, `resultats$A2`… Tout est recalculé au moment de l'export, jamais recopié du carnet.
- **En ligne de commande** : `ddict carnet` (`lister`, `ajouter`, `retirer`, `deplacer`, `retenir`, `ecarter`, `confirmer`, `numeros`) et `ddict resultats` ; en anglais, `ddict notebook` et `ddict results`. La page et les commandes écrivent les mêmes fichiers.
- **Scripts R complétés** : la corrélation de plus de deux variables calcule désormais toutes les paires (elle ne calculait que la première) ; le Tableau 1 et les comparaisons de Tukey donnent toutes leurs valeurs. Vérifié dans R : treize analyses de la base fictive, plus de 150 valeurs égales à 10⁻⁶ près ; sur une vraie base de 252 variables, dix analyses, 119 valeurs égales à 10⁻⁷ près (`docs/essais/2026-10-16-essai-carnet.md`).
- Guides : « Le carnet d'analyses et le document des résultats », en français et en anglais.

## 0.10.0 — 2026-10-16

Les résultats des analyses en tableaux et figures APA 7, modifiables (plan : `docs/plan-v0.10.md`, D-082 à D-086 ; fiches validées : `docs/tableaux-figures-apa.md`).

- **Un tableau et une figure APA par analyse** : Tableau 1 (caractéristiques des participants, par groupe et au total), test *t* (en-têtes regroupés par groupe, *t*, *p*, *d* et son IC), ANOVA (*n*, *M*, *ÉT* et l'IC de chaque moyenne ; comparaisons de Tukey), khi-carré (tableau croisé en pourcentages de colonne), corrélation (matrice avec *M*, *ÉT* et les IC), régression (*b*, son IC, *ET*, β, *t*, *p*). Figures : moyennes et leur IC 95 %, barres groupées, nuage de points avec sa droite, coefficients standardisés et leur IC. Normes APA 7 : numéro en gras, titre en italique, filets horizontaux seulement, symboles en italique, *p* exacts sans astérisques (D-086), en français ou en anglais.
- **Word** (`.docx`, D-085) : de vrais tableaux Word, des figures nettes ; colonnes de chiffres qui ne se replient pas. **Excel** (D-084) : le graphique natif de chaque figure, avec ses données, à modifier puis coller dans Word.
- **Modifiable dans l'outil** (D-086) : le numéro, le titre et la note de chaque tableau et de chaque figure, avec un aperçu, sur la page « Analyses » ; les chiffres viennent du calcul. Téléchargement, ou écriture à côté du projet avec le rapport ; `ddict analyser --format docx xlsx`.
- **D'autres formats faciles à ajouter** (D-083) : une description neutre des tableaux et des figures, un module par format inscrit dans une liste, et un test commun que chaque format doit réussir (chaque chiffre, titre et note retrouvé dans le fichier).
- Deux nouvelles dépendances (D-082) : python-docx (MIT) et matplotlib (licence permissive). Avec python-docx arrive lxml, qu'openpyxl utilise : les fichiers Excel de l'outil gardent leur contenu, pas leurs octets.
- Les tests n'utilisent plus jamais les réglages du poste, même avant leur propre isolement.
- Guides : « Les tableaux et les figures APA », dans la section « Analyser la base », en français et en anglais.

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
