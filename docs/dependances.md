# Dépendances

Toute nouvelle dépendance est ajoutée à ce tableau après vérification de sa licence et de sa compatibilité avec Apache-2.0 (D-002). Une dépendance **d'exécution** est distribuée avec l'outil ; une dépendance **de développement** ne sert qu'à le construire ou à le tester et n'est pas distribuée.

## Dépendances d'exécution

| Paquet | Rôle | Licence | Compatible Apache-2.0 | Ajouté à l'étape |
|---|---|---|---|---|
| pandas | Tableaux de données | BSD-3-Clause | Oui | 1 |
| numpy | Calcul numérique (requis par pandas et pyreadstat) | BSD-3-Clause | Oui | 1 |
| python-dateutil | Dates (requis par pandas) | Apache-2.0 ou BSD-3-Clause | Oui | 1 |
| six | Compatibilité Python (requis par python-dateutil) | MIT | Oui | 1 |
| tzdata | Fuseaux horaires (requis par pandas) | Apache-2.0 | Oui | 1 |
| pyreadstat | Lecture des fichiers SPSS, Stata (v0.2) et SAS (v0.2) | Apache-2.0 | Oui | 1 |
| narwhals | Couche commune entre bibliothèques de tableaux (requis par pyreadstat) | MIT | Oui | 1 |
| pydantic | Modèle et validation du fichier projet, puis des réponses du modèle | MIT | Oui | 6 |
| pydantic-core | Noyau compilé (requis par pydantic) | MIT | Oui | 6 |
| annotated-types | Contraintes de types (requis par pydantic) | MIT | Oui | 6 |
| typing-extensions | Compléments de typage (requis par pydantic) | PSF-2.0 | Oui | 6 |
| typing-inspection | Inspection des types (requis par pydantic) | MIT | Oui | 6 |
| openpyxl | Écriture du codebook Excel ; lecture des bases Excel (v0.2) | MIT | Oui | 7 |
| et-xmlfile | Écriture XML en flux (requis par openpyxl) | MIT | Oui | 7 |
| pypdf | Lecture du texte des questionnaires PDF (D-017) | BSD-3-Clause | Oui | v0.2, 2 |
| scipy | Tests statistiques des analyses du catalogue (khi-carré, corrélations, Fisher… ; D-071) | BSD-3-Clause | Oui | v0.9, 4 |
| statsmodels | ANOVA (Tukey), régression linéaire, facteurs d'inflation de la variance (D-071) | BSD-3-Clause | Oui | v0.9, 5 |
| patsy, formulaic | Formules de modèles (requis par statsmodels) | BSD-2-Clause, MIT | Oui | v0.9, 5 |
| interface-meta, wrapt | Utilitaires (requis par formulaic) | MIT, BSD-2-Clause | Oui | v0.9, 5 |
| python-docx | Tableaux et figures APA dans un fichier Word (D-082) | MIT | Oui | v0.10, 3 |
| lxml | XML du fichier Word (requis par python-docx) | BSD-3-Clause | Oui | v0.10, 3 |
| matplotlib | Figures APA en image (D-082) | Licence matplotlib (fondée sur la PSF, permissive) | Oui | v0.10, 3 |
| pillow | Images (requis par matplotlib) | MIT-CMU (HPND) | Oui | v0.10, 3 |
| contourpy, cycler, kiwisolver | Calculs de tracé (requis par matplotlib) | BSD-3-Clause | Oui | v0.10, 3 |
| fonttools, pyparsing | Polices et analyse de texte (requis par matplotlib) | MIT | Oui | v0.10, 3 |
| packaging | Numéros de version (requis par matplotlib et statsmodels) | Apache-2.0 ou BSD-2-Clause | Oui | v0.10, 3 |

### Option « ia » : enrichissement par un modèle local

Installée seulement sur demande (`pip install "ddict[ia]"`, ou `uv sync --extra ia`). Sans elle, l'outil profile et exporte normalement.

| Paquet | Rôle | Licence | Compatible Apache-2.0 | Ajouté à l'étape |
|---|---|---|---|---|
| httpx | Appels au serveur local compatible OpenAI | BSD-3-Clause | Oui | 10 |
| httpcore | Transport HTTP (requis par httpx) | BSD-3-Clause | Oui | 10 |
| h11 | Protocole HTTP/1.1 (requis par httpcore) | MIT | Oui | 10 |
| anyio | Entrées-sorties (requis par httpx) | MIT | Oui | 10 |
| idna | Noms de domaine (requis par httpx) | BSD-3-Clause | Oui | 10 |
| certifi | Certificats racines (requis par httpx) | MPL-2.0 | Oui, distribué sans modification | 10 |

### Option « revision » : interface de révision dans le navigateur

Installée seulement sur demande (`pip install "ddict[revision]"`, ou `uv sync --extra revision`). Sans elle, le fichier projet reste modifiable par les autres commandes.

| Paquet | Rôle | Licence | Compatible Apache-2.0 | Ajouté à l'étape |
|---|---|---|---|---|
| streamlit | Interface de révision locale | Apache-2.0 | Oui | 12 |
| starlette, uvicorn, httptools, websockets, python-multipart, itsdangerous | Serveur web local (requis par streamlit) | BSD-3-Clause, MIT ou Apache-2.0 | Oui | 12 |
| altair, pydeck | Graphiques (requis par streamlit) | BSD-3-Clause, Apache-2.0 | Oui | 12 |
| jinja2, markupsafe, jsonschema, referencing, jsonschema-specifications, rpds-py, attrs | Gabarits et schémas (requis par altair) | BSD-3-Clause ou MIT | Oui | 12 |
| pyarrow | Échange de tableaux (requis par streamlit) | Apache-2.0 | Oui | 12 |
| pillow | Images (requis par streamlit) | MIT-CMU | Oui | 12 |
| protobuf | Messages entre serveur et navigateur (requis par streamlit) | BSD-3-Clause | Oui | 12 |
| requests, urllib3, charset-normalizer | Client HTTP (requis par streamlit ; l'outil ne s'en sert pas) | Apache-2.0, MIT | Oui | 12 |
| click, toml, watchdog, packaging | Ligne de commande, configuration, surveillance de fichiers | BSD-3-Clause, MIT, Apache-2.0 | Oui | 12 |
| pywebview (Windows seulement) | La fenêtre de l'outil, sans console : l'interface s'y affiche avec le moteur d'Edge (WebView2) déjà présent dans Windows, et fermer la fenêtre arrête l'outil (D-055) | BSD-3-Clause | Oui | v0.7.1 |
| pythonnet, clr-loader | Accès de pywebview au moteur d'Edge (requis par pywebview sous Windows) | MIT | Oui | v0.7.1 |
| bottle, proxy-tools | Petit serveur et utilitaires internes (requis par pywebview ; l'outil ne s'en sert pas) | MIT | Oui | v0.7.1 |

## Dépendances de développement

| Paquet | Rôle | Licence | Ajouté à l'étape |
|---|---|---|---|
| pytest | Tests | MIT | 0 |
| pytest-socket | Blocage du réseau dans les tests | MIT | 0 |
| ruff | Lint et formatage | MIT | 0 |
| babel | Extraction des phrases à traduire et compilation du catalogue anglais (`scripts/traductions.py`) ; l'outil lit le catalogue avec `gettext`, de la bibliothèque standard (D-033) | BSD-3-Clause | v0.5, 1 |

| hatchling | Construction du paquet | MIT | 0 |
| httpx | Faux serveur des tests du client IA (aussi dans l'option « ia ») | BSD-3-Clause | 10 |
| streamlit | Tests de l'interface de révision (aussi dans l'option « revision ») | Apache-2.0 | 12 |
| jsonschema | Validation du `datapackage.json` du contexte d'analyse contre les schémas Frictionless v2 gardés dans `tests/schemas/` (domaine public, Unlicense) | MIT | v0.8, 6 |
| playwright | Captures d'écran automatiques de l'interface (`scripts/captures.py`, D-127), avec le Microsoft Edge du poste : aucun navigateur téléchargé ; hors de `pytest` | Apache-2.0 | v0.16, B4 |
| greenlet, pyee | Requis par playwright | MIT et PSF-2.0, MIT | v0.16, B4 |

**Outils facultatifs, hors Python**, sur le poste de développement seulement ; ni l'outil ni ses tests ordinaires n'en dépendent, et chaque test qui les utilise est sauté s'ils manquent :

- **R et son paquet haven** (R : GNU GPL ; haven : MIT). Ils écrivent la version SAS de la base fictive (`scripts/generer_sas.R`), que Python ne sait pas écrire ; le fichier produit est gardé dans le dépôt (v0.2, étape 8). Depuis la v0.4 (étape 3), un test exécute aussi le script R produit par l'outil sur la base fictive CSV.
- **PSPP** (GNU GPL, D-027 ; essayé avec PSPP 2.1.2 pour Windows). Un test y exécute la syntaxe SPSS produite par l'outil (v0.4, étape 3).

## Contenus tiers

Textes repris ou adaptés dans les documents que l'outil produit ; aucun code.

| Contenu | Usage | Licence | Compatible Apache-2.0 | Ajouté |
|---|---|---|---|---|
| Questions du gabarit de préenregistrement pour l'analyse de données secondaires (van den Akker et al., 2021, *Meta-Psychology*, 5, https://doi.org/10.15626/MP.2020.2625) | Les 25 questions et la déclaration d'intégrité, traduites en français et abrégées, dans le préenregistrement de données secondaires (D-109) ; attribution et mention de l'adaptation en tête du document | CC BY 4.0 (vérifiée le 2026-10-17 sur la page de la revue et dans l'article) | Oui, avec attribution | v0.13, 1 |
| Questions du gabarit OSF Prereg (Bowman et al., 2020, MetaArXiv, https://doi.org/10.31222/osf.io/epgjd) | Les questions et les cinq réponses sur l'état des données, traduites en français et abrégées, dans le préenregistrement de données primaires et dans le champ `data_status` du plan (D-109) ; mention d'origine en tête du document | CC0 1.0 (vérifiée le 2026-10-17 dans les métadonnées de l'OSF) | Oui | v0.13, 1 |
