# Essai : l'outil dans sa propre fenêtre, sans fenêtre noire (D-055)

**Date :** 2026-10-15

**But :** vérifier sur un vrai poste Windows 11 ce que les tests ne vérifient qu'avec une fausse fenêtre : l'icône créée par l'installateur, l'arrêt par le bouton et par la fermeture de la fenêtre.

## Avant la décision : essai de pywebview

Un lanceur d'essai, hors du dépôt, ouvrait l'interface dans une fenêtre pywebview (moteur d'Edge, déjà installé). L'interface a démarré en 7 secondes. Dans la fenêtre, l'auteur a vérifié :
- la fenêtre « Ouvrir » : elle apparaît au premier plan ;
- l'ouverture d'un projet et les pages ;
- l'export, « Ouvrir le dossier » et « Télécharger ».

À la fermeture de la fenêtre, aucun processus de l'outil ne restait et le port local ne répondait plus.

## Après l'intégration

Installation par `installer.bat` depuis le dossier du projet, par-dessus la version installée.

| Vérification | Résultat |
|---|---|
| L'icône ouvre l'outil dans sa fenêtre, sans fenêtre noire ni onglet de navigateur | conforme |
| « Quitter l'outil » : message « L'outil est arrêté. », puis la fenêtre se ferme seule | conforme |
| Fermer la fenêtre arrête l'outil ; l'icône le redémarre ensuite normalement | conforme |
| Un second double-clic, outil ouvert : une fenêtre de plus sur le même outil | conforme |
