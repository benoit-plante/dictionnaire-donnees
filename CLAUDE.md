# CLAUDE.md — dictionnaire-donnees

Instructions pour Claude Code. Lire ce fichier au début de chaque séance.

## Le projet

Outil **libre, local et hors ligne** qui aide les équipes de recherche en psychologie et en sciences sociales à produire le dictionnaire de données d'une base existante (`.sav`, `.csv`). Le calcul déterministe d'abord ; une IA facultative, activée projet par projet et qui ne reçoit que des métadonnées, propose, une personne décide. « dictionnaire-donnees » est un nom de travail (D-003). Conception complète : `docs/CONCEPTION.md`.

L'auteur n'est pas développeur de métier : expliquer les choix techniques simplement et le guider pour chaque commande à exécuter.

## Règles non négociables

1. **Aucune donnée réelle dans le dépôt.** Exemples et tests utilisent des bases fictives générées par `scripts/` avec une graine fixe. Ne jamais demander de données réelles.
2. **Le modèle ne reçoit jamais de données individuelles.** Tout message destiné au modèle est construit par la porte de confidentialité (module `privacy`) à partir du profil agrégé, jamais à partir du tableau. Aucune valeur de texte libre ni d'identifiant probable ; effectifs < 5 masqués (D-006).
3. **Aucune donnée de participant ne quitte le poste.** L'IA est un service externe, activé explicitement projet par projet, qui ne reçoit que des métadonnées (le questionnaire et le codebook), jamais rien de ce que les participants ont répondu, pas même agrégé (D-134, D-136). Le client IA n'accepte qu'une adresse en HTTPS (ou une adresse de cet ordinateur), sans proxy ni redirection ; la clé d'API reste dans le gestionnaire d'identifiants de Windows, jamais ailleurs (D-137). Les tests bloquent le réseau (pytest-socket), sauf les tests `externe` (D-139). Streamlit écoute sur 127.0.0.1, télémétrie désactivée.
4. **Aucune invention.** Les schémas de réponse du modèle n'ont aucun champ pour un seuil, une étendue théorique, une référence ou un nom d'instrument (`extra="forbid"`). Ces champs sont humains et exigent une source.
5. **Toute production de l'IA est une proposition** (statut `proposed`) ; l'export final n'inclut que les valeurs validées ou corrigées.
6. **L'IA est facultative** : la chaîne lire → profiler → exporter fonctionne sans aucune dépendance IA installée.

## Conventions

- Python 3.11+, paquet dans `src/ddict/` ; environnement géré par uv (`uv sync`, `uv run pytest`, `uv run ruff check`, `uv run ruff format`).
- Développement sous Windows (PowerShell) ; l'outil ne vise que Windows (D-081). Utiliser `pathlib`, ouvrir les fichiers avec `encoding="utf-8"` et `newline="\n"` explicitement.
- Code, commentaires, docstrings, noms de champs et messages de commit en anglais ; documentation, journal des décisions, interface et prompts en français (D-004).
- Écriture JSON déterministe : ordre des clés fixe, indentation 2, UTF-8, `ensure_ascii=False`, LF.
- Licence Apache-2.0 (D-002). Vérifier la licence de toute nouvelle dépendance et la noter dans `docs/dependances.md`.

## Façon de travailler

- Une étape du plan (`docs/CONCEPTION.md`, § 13) à la fois. Proposer un plan court avant de coder, puis s'arrêter à la fin de l'étape pour une revue.
- Écrire les tests en même temps que le code ; une étape est terminée quand son critère de réussite passe.
- Une décision structurante (dépendance, changement de format, écart avec la conception) est proposée à l'auteur et, une fois acceptée, consignée dans `docs/journal-des-decisions.md` selon le gabarit, sans modifier les entrées existantes.
- Ajouter les fichiers à Git par leur nom (pas de `git add -A`).
- Pousser automatiquement vers le dépôt GitHub (branche `main`) après chaque commit, une fois les tests et ruff passés : l'auteur l'a autorisé. Les étiquettes de version, les publications de version et tout changement de visibilité du dépôt restent soumis à une demande explicite. Le dépôt est public depuis le 2026-10-14 (D-037) : tout ce qui y entre, historique compris, est visible de tous ; rien de réel, aucun chemin personnel.
