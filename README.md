# dictionnaire-donnees

> Nom de travail. Version 0.4.0 : les décisions passent du codebook à vos données (fichiers de commandes SPSS, R et Stata, copie documentée), et un banc d'essai aide à choisir le modèle. À essayer d'abord sur la base fictive et son questionnaire, fournis.

Outil libre et local qui aide les équipes de recherche à produire le **dictionnaire de données** (codebook) d'une base existante (SPSS, CSV, Stata, SAS ou Excel), avec l'aide du questionnaire de l'étude.

- Tout ce qui se calcule exactement (types, manquants, étendues observées, modalités, étiquettes du fichier) est calculé sans IA.
- Le questionnaire (PDF ou texte) donne le texte exact des questions, le sens des sigles et des options de réponse ; il est lu sans IA.
- Une IA locale, facultative, propose des rattachements aux questions, des libellés et des descriptions ; chaque proposition attend une décision humaine. Elle ne définit jamais un sigle.
- Rien ne quitte le poste, et le modèle ne reçoit jamais de données individuelles.

## Commencer

Le guide [`docs/installation-windows.md`](docs/installation-windows.md) mène de l'installation à un codebook complet, sans connaissances en programmation. En bref : décompresser l'archive, double-cliquer sur `installer.bat`, puis sur l'icône **Dictionnaire de données** ; le reste se fait dans le navigateur, sur cet ordinateur seulement.

Toutes les étapes existent aussi en ligne de commande (`ddict --help`) :

```
ddict                                     # l'interface, sur l'accueil
ddict profiler etude-sommeil.sav          # lire la base, créer le fichier projet
ddict questionnaire etude-sommeil.dd.json questionnaire-sommeil.pdf
ddict rattacher etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M  # IA facultative
ddict enrichir etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M   # facultatif
ddict exporter etude-sommeil.dd.json      # codebook Excel et rapport Markdown
ddict exporter etude-sommeil.dd.json --syntaxe   # et fichiers de commandes SPSS, R, Stata
ddict documenter etude-sommeil.dd.json    # copie documentée de la base (.sav)
ddict evaluer --modele qwen2.5:7b-instruct-q4_K_M  # banc d'essai d'un modèle
```

## Documentation

| Sujet | Fichier |
|---|---|
| Installation et premier codebook, pas à pas | [`docs/installation-windows.md`](docs/installation-windows.md) |
| Conception, principes, format du fichier projet | [`docs/CONCEPTION.md`](docs/CONCEPTION.md) |
| Décisions prises | [`docs/journal-des-decisions.md`](docs/journal-des-decisions.md) |
| Essais de modèles locaux | [`docs/essais/`](docs/essais/) |
| Changements par version | [`CHANGELOG.md`](CHANGELOG.md) |

## Licence

Code sous licence [Apache 2.0](LICENSE). Documentation sous CC BY 4.0. Bases fictives et gabarits sous CC0.
