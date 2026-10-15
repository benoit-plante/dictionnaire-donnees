# dictionnaire-donnees

> Nom de travail. Version 0.7.1 : sous Windows, l'outil s'ouvre dans sa propre fenêtre, sans fenêtre noire, et les noms des variables se décident directement dans le tableau. Depuis la 0.7, les exports bruts de SurveyMonkey sont lus juste et les variables se renomment, avec reprise des noms d'une vague à l'autre. Depuis la 0.5, l'outil existe aussi en anglais et s'installe sur un Mac par double-clic. **L'anglais et macOS sont à l'essai** : la traduction n'a pas encore été relue par une personne anglophone, et l'installation sur Mac n'a été vérifiée que sur un Mac de GitHub. À essayer d'abord sur la base fictive et son questionnaire, fournis.

Outil libre et local qui aide les équipes de recherche à produire le **dictionnaire de données** (codebook) d'une base existante (SPSS, CSV, Stata, SAS ou Excel ; le `.sav` de SPSS donne les meilleurs résultats), avec l'aide du questionnaire de l'étude.

- Tout ce qui se calcule exactement (types, manquants, étendues observées, modalités, étiquettes du fichier) est calculé sans IA.
- Le questionnaire (PDF ou texte) donne le texte exact des questions, le sens des sigles et des options de réponse ; il est lu sans IA.
- Une IA locale, facultative, propose des rattachements aux questions, des libellés et des descriptions ; chaque proposition attend une décision humaine. Elle ne définit jamais un sigle.
- Rien ne quitte le poste, et le modèle ne reçoit jamais de données individuelles.

## Commencer

Le guide [`docs/installation-windows.md`](docs/installation-windows.md) mène de l'installation à un codebook complet, sans connaissances en programmation. En bref : décompresser l'archive, double-cliquer sur `installer.bat`, puis sur l'icône **Dictionnaire de données** ; le reste se fait dans le navigateur, sur cet ordinateur seulement. Sur un Mac : [`docs/installation-macos.md`](docs/installation-macos.md) (`installer.command`).

**In English.** A free, local tool that helps research teams write the data dictionary (codebook) of an existing database, with the help of the study's questionnaire; an optional local AI proposes, a person decides, and nothing leaves the computer. The interface, the codebook and the guides exist in English (a trial version: the translation has not yet been reviewed by a native speaker): [`docs/en/installation-windows.md`](docs/en/installation-windows.md) (Windows) and [`docs/en/installation-macos.md`](docs/en/installation-macos.md) (Mac).

Toutes les étapes existent aussi en ligne de commande (`ddict --help`) :

```
ddict                                     # l'interface, sur l'accueil
ddict profiler etude-sommeil.sav          # lire la base, créer le fichier projet
ddict questionnaire etude-sommeil.dd.json questionnaire-sommeil.pdf
ddict rattacher etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M  # IA facultative
ddict enrichir etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M   # facultatif
ddict exporter etude-sommeil.dd.json      # codebook Excel et rapport Markdown
ddict exporter etude-sommeil.dd.json --syntaxe   # et fichiers de commandes SPSS et R
ddict documenter etude-sommeil.dd.json    # copie documentée de la base (.sav)
ddict renommer etude-t2.dd.json --suffixe _t2 --reference etude-t1.dd.json  # noms
ddict evaluer --modele qwen2.5:7b-instruct-q4_K_M  # banc d'essai d'un modèle
```

## Documentation

| Sujet | Fichier |
|---|---|
| Installation et premier codebook, pas à pas | [`docs/installation-windows.md`](docs/installation-windows.md) |
| Installation sur Mac | [`docs/installation-macos.md`](docs/installation-macos.md) |
| Guides in English | [`docs/en/`](docs/en/) |
| Conception, principes, format du fichier projet | [`docs/CONCEPTION.md`](docs/CONCEPTION.md) |
| Décisions prises | [`docs/journal-des-decisions.md`](docs/journal-des-decisions.md) |
| Essais de modèles locaux | [`docs/essais/`](docs/essais/) |
| Changements par version | [`CHANGELOG.md`](CHANGELOG.md) |

## Licence

Code sous licence [Apache 2.0](LICENSE). Documentation sous CC BY 4.0. Bases fictives et gabarits sous CC0.
