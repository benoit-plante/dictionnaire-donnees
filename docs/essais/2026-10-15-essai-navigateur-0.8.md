# Essai : le parcours de la 0.8 dans le navigateur (v0.8, étape 9)

**Date :** 2026-10-15

**But :** le critère de l'étape 9, ce que les tests automatiques ne couvrent pas : les nouveaux tableaux et formulaires, refaits par l'auteur dans la fenêtre de l'outil, en français puis en anglais.

**Installation :** `installer.bat` depuis le dossier du projet ; outil ouvert par son icône. **Bases :** `etude-sommeil.sav`, `etude-sommeil.csv` et `questionnaire-sommeil.pdf`, copiés dans un dossier d'essai.

| Étape | Résultat |
|---|---|
| Page Base : tableau de complétude (libellé 33 / 34, étiquettes 17 / 21, niveau 27 / 27, cotation 0 / 2, description incomplète) | conforme |
| Niveaux de mesure : `langue_maison` proposé « nominal », accepté dans le tableau | conforme |
| Description de la base enregistrée ; la complétude passe à « dite » | conforme |
| Codes suspects 999, 9 et −9 confirmés manquants | conforme |
| Page Groupes : items inversés confirmés ; cotation refusée sans source, puis enregistrée, avec sa phrase | conforme |
| Export : empreinte, description et complétude dans l'onglet « Informations » | conforme |
| Fichiers de commandes : script de préparation `.sps` et `.R`, avec l'inversion et le score | conforme |
| Contexte d'analyse, sans puis avec les statistiques (aucune variable sensible dans les statistiques) | conforme |
| CSV : encadré sur le format ; niveaux proposés, `genre` sans proposition ; « Accepter » pré-rempli, une ligne vidée, enregistrement | conforme |
| Parcours en anglais (Database, Groups, Export) | aucun texte d'interface en français |

Aucune anomalie.
