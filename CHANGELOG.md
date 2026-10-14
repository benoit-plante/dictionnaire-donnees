# Changements

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
