# dictionnaire-donnees

> Nom de travail. Version 0.1.2 : première version utilisable, à essayer d'abord sur la base fictive fournie.

Outil libre et local qui aide les équipes de recherche à produire le **dictionnaire de données** (codebook) d'une base existante (`.sav` de SPSS ou `.csv`).

- Tout ce qui se calcule exactement (types, manquants, étendues observées, modalités, étiquettes du fichier) est calculé sans IA.
- Une IA locale, facultative, propose des libellés, des descriptions et des regroupements en échelles ; chaque proposition attend une décision humaine.
- Rien ne quitte le poste, et le modèle ne reçoit jamais de données individuelles.

## Commencer

Le guide [`docs/installation-windows.md`](docs/installation-windows.md) mène de l'installation à un premier codebook, sans connaissances en programmation. En bref :

```
uv tool install ".[ia,revision]"          # depuis le dossier de l'outil
ddict profiler etude-sommeil.sav          # lire la base, créer le fichier projet
ddict enrichir etude-sommeil.dd.json --modele qwen2.5:7b-instruct-q4_K_M   # facultatif
ddict reviser etude-sommeil.dd.json       # décider dans le navigateur
ddict exporter etude-sommeil.dd.json      # codebook Excel et rapport Markdown
```

## Documentation

| Sujet | Fichier |
|---|---|
| Installation et premier codebook | [`docs/installation-windows.md`](docs/installation-windows.md) |
| Conception, principes, format du fichier projet | [`docs/CONCEPTION.md`](docs/CONCEPTION.md) |
| Décisions prises | [`docs/journal-des-decisions.md`](docs/journal-des-decisions.md) |
| Essais de modèles locaux | [`docs/essais/`](docs/essais/) |
| Changements par version | [`CHANGELOG.md`](CHANGELOG.md) |

## Licence

Code sous licence [Apache 2.0](LICENSE). Documentation sous CC BY 4.0. Bases fictives et gabarits sous CC0.
