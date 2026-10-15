# Essai : la page « Noms » dans le navigateur (v0.7)

**Date :** 2026-10-15

**But :** le critère de l'étape 9 que les tests automatiques ne couvrent pas : le tableau modifiable de la page « Noms » et le parcours complet, refaits par l'auteur dans le navigateur, en français puis en anglais.

**Installation :** `installer.bat` lancé depuis le dossier du projet, par-dessus une 0.5 installée ; outil ouvert par son icône.

**Bases :** les deux vagues fictives SurveyMonkey (`travail-t1_surveymonkey.sav`, `travail-t2_surveymonkey.sav`), copiées dans un dossier d'essai.

## Parcours et résultats

| Étape | Résultat |
|---|---|
| Vague 1 : export reconnu, préfixes `eft` et `milieu` donnés dans « Groupes », marque `_t1`, noms proposés | conforme |
| Correction dans le tableau : nom invalide refusé, nom déjà pris refusé, nom correct enregistré | conforme |
| Acceptation en lot d'une grille, une ligne décochée restée proposée | conforme |
| Accepter et rejeter une variable | conforme |
| Radical corrigé une fois, les noms non décidés suivent | conforme |
| Tableau de bord sans ligne « noms » une fois tout décidé ; codes « Ne sais pas » confirmés comme manquants | conforme |
| Export : colonne « Nom d'origine », onglet « Correspondance », table `-correspondance.csv` | conforme |
| Vague 2 : noms repris du projet de la vague 1, nom corrigé et radical changé repris, `eft_11_t2` malgré la renumérotation, rapport des écarts (ajout, retrait, étiquette changée), préfixe repris dans « Groupes » | conforme |
| Parcours en anglais (Names, Groups, Database, tableau de bord) | aucun texte d'interface en français |

Aucune anomalie de l'outil. Une précision pour le guide de l'essai : un nom déjà pris est refusé dès l'enregistrement, il n'attend pas dans le filtre « En conflit » (ce filtre sert aux conflits nés d'une proposition, par exemple après la reprise d'une vague).
