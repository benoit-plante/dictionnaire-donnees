# Scénario manuel : révision d'un projet

À faire dans un vrai navigateur, sur la base fictive, après chaque changement important de l'interface de révision. La logique est couverte par les tests automatiques (`tests/test_review.py`) ; ce scénario vérifie ce que les tests ne voient pas : l'affichage, la lisibilité, le confort.

## Préparation (PowerShell)

```
cd C:\Users\benoi\Claude\Projects\dictionnaire-donnees
mkdir $env:TEMP\ddict-revision
copy exemples\bases-fictives\etude-sommeil.sav $env:TEMP\ddict-revision\
uv run ddict profiler $env:TEMP\ddict-revision\etude-sommeil.sav
uv run ddict enrichir $env:TEMP\ddict-revision\etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
uv run ddict reviser $env:TEMP\ddict-revision\etude-sommeil.dd.json
```

Le navigateur s'ouvre sur `http://127.0.0.1:8501`. La console affiche « cet ordinateur seulement ».

## Étapes et résultats attendus

| # | Action | Attendu |
|---|---|---|
| 1 | Regarder la barre latérale | Nom du fichier, barre de progression, filtre « À réviser » choisi, première variable proposée |
| 2 | Sur `sommeil_q1`, cliquer « Accepter » sous le libellé | « Enregistré. » ; statut « IA — validé (modèle, run-…) » ; la variable quitte le filtre « À réviser » |
| 3 | Sur la description, taper un autre texte puis cliquer « Enregistrer » (sans appuyer sur Entrée) | Le texte tapé est enregistré, statut « corrigé », valeur d'origine affichée |
| 4 | Choisir `sommeil_q7` | Encadré rouge : libellé deviné, la variable n'a pas d'étiquette dans le fichier |
| 5 | Cliquer « Rejeter » sous ce libellé | Statut « rejeté » ; l'encadré rouge disparaît |
| 6 | Dans « Champs documentés », saisir un seuil et sa signification **sans source**, cliquer « Ajouter le seuil » | Message d'erreur : une source documentée est obligatoire ; rien n'est ajouté |
| 7 | Recommencer avec une source | Le seuil apparaît avec sa source |
| 8 | Filtre « Sensibles », choisir `courriel`, cliquer « Confirmer la classe » | Classe « identifiant probable », statut « validé » ; aucune statistique ni valeur affichée |
| 9 | « Afficher : Groupes », choisir G1 | Alpha observé et alpha avec items inversés ; `sommeil_q3`, `sommeil_q6` signalés et cochés |
| 10 | Saisir un nom d'instrument sans source, enregistrer | Erreur ; puis avec une source : enregistré |
| 11 | Fermer l'onglet, Ctrl+C dans la console, relancer `ddict reviser` | Toutes les décisions sont toujours là |
| 12 | `uv run ddict exporter $env:TEMP\ddict-revision\etude-sommeil.dd.json`, ouvrir le rapport | Le libellé accepté de `sommeil_q1` y figure ; les propositions non décidées n'y sont pas |

À la fin, supprimer le dossier `$env:TEMP\ddict-revision`.
