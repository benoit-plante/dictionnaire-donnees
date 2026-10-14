# Changements

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
