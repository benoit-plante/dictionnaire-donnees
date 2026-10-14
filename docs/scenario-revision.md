# Scénario manuel : révision d'un projet

À faire dans un vrai navigateur, sur la base fictive, après chaque changement important de l'interface de révision. La logique est couverte par les tests automatiques (`tests/test_review.py`) ; ce scénario vérifie ce que les tests ne voient pas : l'affichage, la lisibilité, le confort.

## Préparation (PowerShell)

```
cd C:\Users\benoi\Claude\Projects\dictionnaire-donnees
mkdir $env:TEMP\ddict-revision
copy exemples\bases-fictives\etude-sommeil.sav $env:TEMP\ddict-revision\
uv run ddict profiler $env:TEMP\ddict-revision\etude-sommeil.sav
uv run ddict questionnaire $env:TEMP\ddict-revision\etude-sommeil.dd.json exemples\bases-fictives\questionnaire-sommeil.pdf
uv run ddict rattacher $env:TEMP\ddict-revision\etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
uv run ddict enrichir $env:TEMP\ddict-revision\etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M
uv run ddict reviser $env:TEMP\ddict-revision\etude-sommeil.dd.json
```

Le navigateur s'ouvre sur `http://127.0.0.1:8501`. La console affiche « cet ordinateur seulement ». Aucun bouton « Deploy » en haut à droite.

## Étapes et résultats attendus

| # | Action | Attendu |
|---|---|---|
| 1 | Regarder la barre latérale | Nom du fichier, barre de progression, filtre « À réviser » choisi, première variable proposée |
| 2 | Sur `sommeil_q1`, cliquer « Accepter » sous le libellé | « Enregistré. » sous le libellé ; statut « IA — validé (modèle, run-…) » ; on reste sur `sommeil_q1`, dont la description attend encore |
| 3 | Sur la description, taper un autre texte puis cliquer « Enregistrer » (sans appuyer sur Entrée) | Le texte tapé est enregistré (statut « corrigé », valeur d'origine gardée) ; `sommeil_q1` n'a plus rien à réviser : l'interface passe à la variable suivante et le dit |
| 4 | Choisir `sommeil_q7` | Encadré rouge : libellé deviné, la variable n'a pas d'étiquette dans le fichier |
| 5 | Cliquer « Rejeter » sous ce libellé | Statut « rejeté » ; l'encadré rouge disparaît ; le champ de saisie se vide |
| 6 | Dans « Champs documentés », saisir un seuil et sa signification **sans source**, cliquer « Ajouter le seuil » | Message en français sous le bouton : une source documentée est obligatoire ; rien n'est ajouté ; la section reste ouverte et garde la saisie |
| 7 | Recommencer avec une source | Le seuil apparaît avec sa source ; les champs du seuil se vident |
| 8 | Filtre « Sensibles », choisir `courriel`, cliquer « Confirmer la classe » | Classe « identifiant probable », statut « validé » ; aucune statistique ni valeur affichée |
| 9 | « Afficher : Groupes », choisir G1 | Alpha observé et alpha avec items inversés ; `sommeil_q3`, `sommeil_q6` signalés et cochés |
| 10 | Saisir un nom d'instrument sans source, enregistrer | Erreur ; puis avec une source : enregistré |
| 11 | Fermer l'onglet, Ctrl+C dans la console, relancer `ddict reviser` | Toutes les décisions sont toujours là |
| 12 | « Afficher : Glossaire » | QFS, EFA et TCC « à valider », avec leur page ; ANX parmi les sigles probables sans définition |
| 13 | Accepter TCC, rejeter EFA ; dans « Ajouter un sigle », taper ANX et sa définition **sans pause** entre les deux champs, puis « Ajouter » | Statuts « validé » et « rejeté » ; ANX ajouté avec l'origine « Équipe », champs vidés, ANX retiré des sigles sans définition |
| 14 | Filtre « À réviser », choisir `id_participant` ; sous « Question du questionnaire », cliquer « Accepter » | « Aucune question du questionnaire », statut « validé » |
| 15 | Choisir `genre` ; dans « Rattacher à », choisir `Q4 — Quel est votre genre ?` puis cliquer « Rattacher » **sans pause** | Le texte exact de la question s'affiche, avec « p. 2 » ; statut « corrigé » si le modèle avait proposé autre chose |
| 16 | Choisir `sommeil_q1`, accepter son rattachement à `Q7.r1` | Aucune étiquette de valeurs proposée : le `.sav` a les siennes, et les colonnes de la grille sont collées dans le PDF. Pour voir une proposition, refaire la préparation avec `etude-sommeil.csv` et `questionnaire-sommeil.txt` : « Étiquettes de valeurs tirées des options de réponse », 1 = Pas du tout … 5 = Extrêmement, « ordre supposé, à vérifier », boutons pour accepter ou rejeter |
| 17 | Filtre « Sans question » | Les variables sans rattachement décidé ; `genre` n'y est plus |
| 18 | « Afficher : Groupes », G2 : cocher « Ne pas reproduire le texte des questions de ce groupe », « Enregistrer ce choix » | « Enregistré. » ; la case reste cochée après un rechargement |
| 19 | `uv run ddict exporter $env:TEMP\ddict-revision\etude-sommeil.dd.json`, ouvrir le codebook et le rapport | Le libellé accepté de `sommeil_q1` y figure ; les propositions non décidées n'y sont pas ; colonnes « Question » et « Texte de la question » remplies pour les rattachements acceptés, « texte omis » pour `anx1` à `anx7` ; onglet « Glossaire » avec TCC et ANX ; aucune trace de la page de consentement (`ZQXQUEST`, « Laboratoire fictif ») |

À la fin, supprimer le dossier `$env:TEMP\ddict-revision`.
