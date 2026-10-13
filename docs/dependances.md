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
| pyreadstat | Lecture et écriture des fichiers SPSS | Apache-2.0 | Oui | 1 |
| narwhals | Couche commune entre bibliothèques de tableaux (requis par pyreadstat) | MIT | Oui | 1 |

## Dépendances de développement

| Paquet | Rôle | Licence | Ajouté à l'étape |
|---|---|---|---|
| pytest | Tests | MIT | 0 |
| pytest-socket | Blocage du réseau dans les tests | MIT | 0 |
| ruff | Lint et formatage | MIT | 0 |
| hatchling | Construction du paquet | MIT | 0 |
