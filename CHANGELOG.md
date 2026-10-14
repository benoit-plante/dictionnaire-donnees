# Changements

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
