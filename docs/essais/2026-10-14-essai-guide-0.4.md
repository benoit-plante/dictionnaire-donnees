# Essai du guide, version 0.4.0

**Date :** 2026-10-14
**Qui :** l'assistant de code, à la demande de l'auteur, sur l'ordinateur de l'auteur (Windows 11, carte graphique, Ollama avec qwen2.5 7B, R 4.6.1 et haven, PSPP 2.1.2).
**Comment :** le guide `docs/installation-windows.md` suivi dans l'ordre, avec l'outil installé par `installer.bat` et ouvert par son icône, sur une copie de la base fictive et de son questionnaire PDF. Deux écarts : l'installateur a été lancé sans ses questions (`-NoPrompt`), et les fichiers ont été donnés en collant leur chemin plutôt que par la fenêtre « Ouvrir », que l'assistant ne peut pas manipuler.

## Ce qui a été fait

| Étape du guide | Résultat |
|---|---|
| 1. Installer par-dessus la 0.3.0 | **Échec, corrigé** (voir plus bas) ; après correction : « ddict 0.4.0 », icônes recréées |
| 2. Ouvrir par l'icône | Accueil dans le navigateur |
| 3. Créer le projet | 34 variables, 200 lignes, 4 sensibles, 10 signalements |
| 4. Questionnaire et glossaire | 14 questions, Q7 « à vérifier », QFS, EFA et TCC acceptés, ANX ajouté |
| 6. Rattachements par le modèle | 6 blocs réussis ; 32 propositions |
| 7. Décisions groupées | 31 dans la liste ; 1 fausse (`date_passation` → date de naissance), décochée ; 30 acceptées. `id_participant` accepté (aucune question), `date_passation` corrigé à la main |
| 6. Libellés et descriptions | 5 blocs réussis ; un libellé accepté, une description corrigée (« l'participant », faute du modèle) ; les autres laissés en attente pour l'essai |
| 7. Codes suspects | 999 (`age`), 9 (`sommeil_q3`), −9 (`nb_reveils`) confirmés comme manquants ; la page passe d'une variable à l'autre |
| 8. Codebook | Six onglets, écrits à côté du projet |
| 9. Fichiers de commandes, R | Script appliqué comme le guide le dit : métadonnées justes, mais **26 cases perdues, corrigé** (voir plus bas) ; après correction, 0 case différente |
| 9. Fichiers de commandes, SPSS | Syntaxe exécutée dans PSPP sur la base : 0 case différente, codes confirmés et libellé corrigé appliqués |
| 9. Copie documentée | « 200 lignes et 34 variables, identiques case par case » ; la base d'origine a gardé son empreinte |

Temps de relecture de la liste groupée (31 lignes) : 36 secondes pour l'assistant, qui lit beaucoup plus vite qu'une personne. Le temps d'une personne reste à mesurer.

## Deux problèmes trouvés et corrigés

1. **Mise à jour avec l'outil ouvert.** L'outil 0.3.0 tournait (ouvert par l'icône le matin). `uv tool install --reinstall` n'a pas pu remplacer ses fichiers (« Accès refusé »), l'outil ne démarrait plus, et le message parlait de la connexion Internet. L'installateur repère maintenant l'outil ouvert, propose de le fermer, et sinon s'arrête avant de toucher à quoi que ce soit, avec un message clair. Le guide le dit dans « Mettre à jour ».
2. **R efface les codes manquants déclarés.** `haven::read_sav()` remplace par défaut les codes manquants déclarés dans le fichier par `NA` : les 9 « Préfère ne pas répondre » de `genre` et les −9 « Refus » des items d'anxiété devenaient des cases vides, et la copie écrite par R perdait cette distinction (26 cases). Le guide et l'exemple en tête du script R utilisent maintenant `haven::read_sav(…, user_na = TRUE)`, et un test vérifie que la copie garde chaque case.

## Ce qui reste

- Le fichier Stata n'a été vérifié que par sa forme : un essai par une personne qui a Stata est souhaitable.
- Le temps de révision d'une personne avec les décisions groupées.
