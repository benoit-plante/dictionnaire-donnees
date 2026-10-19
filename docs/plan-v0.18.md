# Plan de la v0.18

> Statut : **validé par l'auteur le 2026-10-19 ; réalisé en version 0.18.0** (les quatre parties ; après le banc, D-140 à D-142), avec les recommandations du § 10 : décisions D-134 à D-139 adoptées (le type, le niveau de mesure et la note de confidentialité restent envoyés ; `http` accepté pour une adresse de cet ordinateur). Choix donnés par l'auteur le 2026-10-19 : l'IA passe par une clé d'API, Anthropic d'abord ; Ollama est retiré ; un champ « adresse » reste pour un serveur institutionnel ; seul le niveau 1 (métadonnées) est envoyé, libellés compris ; une activation par projet, décochée par défaut ; la clé de l'auteur sert aux essais réels, sur les bases fictives seulement. La version **change de moteur, pas de fonctions** : ni le calcul, ni les exports, ni le carnet, ni l'ébauche d'article ne changent. Rien ne se code avant que l'auteur ait validé l'étape A1 (règles et conception).

## 1. Pourquoi cette version

Les essais des v0.2 à v0.9 montrent que le modèle local aide peu : le calcul seul rattache presque aussi bien ou mieux (88 / 98 contre 89 / 98 ; 59 / 64 contre 54 / 64), les radicaux du modèle ne sont pas offerts (D-051), les incohérences ont été retirées (D-009). Seule la conseillère en tire un vrai gain, et seulement avec une carte graphique (11 / 13 avec qwen2.5 7B, 10 / 13 une fois le message compressé par D-080 ; 3 / 13 avec le 3B). Le modèle local impose en plus l'installation d'Ollama et d'un modèle de 4,7 Go, et un contexte de 4 096 jetons qui découpe tout (blocs de 6 à 8 variables, message compressé de D-080).

La v0.18 garde les quatre usages de l'IA (libellés et descriptions, rattachement, radicaux, conseillère) et le banc d'essai, les fait passer par une clé d'API, et **n'envoie plus rien qui vienne des réponses des participants**, pas même agrégé.

## 2. Ce qui ne change pas

- **L'IA reste facultative** (règle 6) : sans clé ni activation, la chaîne lire → profiler → exporter, les analyses, le carnet et l'ébauche d'article fonctionnent comme aujourd'hui, sans réseau. `httpx` et `keyring` restent dans l'extra `ia` ; aucun module hors de `llm/` et des pages d'IA ne les importe.
- **Les règles 1, 2, 4, 5 et 6 du `CLAUDE.md` restent entières.** Seule la règle 3 est reformulée (D-134).
- **La porte de confidentialité** est la seule source des messages. Les schémas gardent `extra="forbid"` et n'ont aucun champ pour un seuil, une étendue théorique, une référence ou un instrument (règle 4). La validation pydantic, la règle « un bloc entier ou rien », les signaux (citation, seuil, sigle, instrument), la trace `ai_runs`, le dossier des envois (`workflow.exchange_dir`) et l'aperçu des messages restent.
- **Toute production de l'IA est une proposition** (règle 5) ; l'export n'inclut que les valeurs décidées.
- **Les tests bloquent le réseau** (`--disable-socket`), sauf les tests `externe` (§ 8.1) ; Streamlit écoute sur 127.0.0.1, télémétrie coupée.
- Les propositions et les `ai_runs` faites avec Ollama dans les projets existants restent telles quelles, comme historique ; rien de ce qu'une personne a décidé n'est remplacé.
- Les anciennes consignes (`variables-v3`, `link-v3`, `rename-v1`, `advise-v2`) restent dans `llm/prompts/` pour les essais.

## 3. Ce qui change pour la personne

- **Page « IA »** (au lieu de « IA locale », entrée « Réglages » du menu par phases, D-122) : le protocole, l'adresse (Anthropic par défaut), la clé, le modèle, un bouton « Tester la connexion », et une section « Ce qui part » qui dit exactement ce qui est envoyé, à qui, et combien de temps le fournisseur le garde.
- **Une case par projet** : « Permettre l'envoi des métadonnées de ce projet à l'IA ». Décochée par défaut ; l'activation est inscrite dans le projet (avec sa date), pour que les collègues la voient. Sans elle, aucun bouton d'IA n'envoie rien et la ligne de commande refuse ; l'aperçu reste toujours permis.
- **Plus d'Ollama** : l'installateur ne le cherche plus, la documentation n'en parle plus, aucune recommandation selon la carte graphique.
- **La même qualité sur tous les postes**, sans carte graphique ; un coût, payé par l'équipe sur sa propre clé (ordre de grandeur au § 8.3, chiffres réels après le banc). Le bouton « Mesurer ce modèle » du banc dépense maintenant de l'argent : il le dit avant de partir.

## 4. Ce que j'ai vérifié, dans le code et chez Anthropic

### 4.1 Chez Anthropic (documentation consultée le 2026-10-19, à revérifier en A2)

- **Le format de réponse contraint** : `POST /v1/messages`, `output_config: {"format": {"type": "json_schema", "schema": …}}`, sans en-tête bêta ; le JSON arrive dans le bloc `text` de `content`, à trouver par son type. Pris en charge par Haiku 5.5, Sonnet 5.5 et Opus 5.5.
- **Ce que le schéma n'accepte pas** (erreur 400) : `minimum`, `maximum`, `multipleOf`, `minLength`, `maxLength`, les contraintes de tableau autres que `minItems` à 0 ou 1 (donc `maxItems`), les schémas récursifs, `additionalProperties` autre que `false` (obligatoire sur chaque objet). Accepté : `enum`, `const`, `anyOf`, `$ref` et `$defs`, `default`, `required`. **Non documentés** : `title` (que pydantic écrit partout) et `prefixItems` (que la conseillère utilise) ; le premier contact réel (étape A5) le tranche.
- **Des limites de taille** : 24 paramètres facultatifs et 16 paramètres à types multiples (`anyOf`) par requête ; au-delà, « Schema is too complex for compilation ». Un schéma neuf est compilé à la première requête (jusqu'à 180 s), puis gardé 24 h.
- **Haiku 5.5 et Sonnet 5.5 refusent la température** (et `top_p`, `top_k`) : toute valeur autre que celle par défaut donne une erreur 400. *L'ébauche disait « la température 0 reste » : c'est faux.* Il n'y a pas non plus de graine. Le client Anthropic n'envoie donc aucun paramètre d'échantillonnage.
- **La réflexion est active par défaut** sur ces deux modèles : la réponse peut commencer par des blocs `thinking` (d'où la lecture par type), ces jetons sont facturés comme sortie et comptent dans `max_tokens`. On la règle par `output_config.effort` (`low` à `max` ; défaut `medium` sur Haiku 5.5, `high` sur Sonnet 5.5). Je propose `effort: "low"` par défaut, inscrit dans la trace ; le banc compare `low` et `medium`.
- **Pas de rôle `system` dans `messages`** en première position : la consigne passe dans le champ `system` de la requête. Nos blocs ont la forme `({"role": "system"}, {"role": "user"})` : le client Anthropic la convertit au moment de l'envoi ; le bloc, son empreinte (`message_sha256`) et le dossier des envois ne changent pas.
- **`stop_reason`** : `refusal` (réponse 200, facturée, sortie possiblement hors schéma) et `max_tokens` (sortie tronquée). Haiku 5.5 n'a pas de modèle de repli côté serveur ; je propose de ne jamais utiliser le paramètre `fallbacks` (il ferait répondre un autre modèle que celui choisi, à l'insu de la trace) : un refus compte comme une réponse invalide.
- **Erreurs HTTP** : 400 (requête ou schéma refusé), 401 et 403 (clé refusée), 404 (modèle inconnu), 429 (limite, en-tête `retry-after`), 500 et 529 (surcharge). Chaque réponse porte un en-tête `request-id`, à garder dans le dossier des envois.
- **`GET /v1/models`** est paginé (`limit` jusqu'à 1 000, `has_more`, `after_id`).
- **Conservation** (page mise à jour le 2026-07-01, https://privacy.claude.com/en/articles/7996866-how-long-does-anthropic-store-my-organizations-data) : pour l'API, entrées et sorties supprimées dans les 30 jours, sauf exceptions (entente contraire comme le « zéro conservation », respect de la politique d'usage, obligation légale) ; un contenu signalé pour la politique d'usage peut être gardé jusqu'à 2 ans (scores de classement : 7 ans). La page « IA » le dit tel quel, avec le lien et la date de vérification, sans rien promettre de plus.
- **Prix** (au 2026-10-06) : Haiku 5.5, 0,10 $ / 0,50 $ par million de jetons (entrée / sortie) jusqu'à 100 000 jetons de message ; Sonnet 5.5, 2 $ / 10 $.

### 4.2 Dans le code (après la v0.17)

- **Deux fuites de niveau 2 que l'ébauche ne voyait pas** :
  1. La description calculée d'un groupe (« 6 items, codes de 1 à 5, préfixe « PSQI » ») vient de `groups/find.py` (l. 339) : `codes de … à …` est le **minimum et le maximum observés** dans les réponses aux items. Elle part dans le message des libellés (`variable_payload`, `group.description`) et dans celui de la conseillère (`advise._content`, quand les libellés des items n'ont pas de début commun), même après qu'une personne l'a acceptée. Au niveau 1, cette partie est retirée ; le nombre d'items et le préfixe restent.
  2. Les clés de `observed` (les codes observés eux-mêmes, pas seulement leurs proportions) : retirées avec le reste.
- **Ce qui est calculé des données sans dire ce qu'une personne a répondu** : le type déduit (`inferred_type`, aussi dans les messages du rattachement et des radicaux), la classe de confidentialité (la note « texte libre : aucune valeur transmise ») et le niveau de mesure en vigueur ; la conseillère choisit aussi ses variables admissibles d'après le type. Ils restent envoyés (§ 6, D-136) : ils décrivent le format de la colonne et la protègent, comme un codebook.
- **Le schéma de la conseillère** (`advise.advice_schema`) utilise `prefixItems`, `minItems` jusqu'à 4 (rôles obligatoires) et `maxItems`, et un `anyOf` de 11 analyses : il faut une forme « envoyée » propre (§ 5.2), et la validation locale doit vérifier ce que la grammaire garantissait (chaque rôle obligatoire présent une fois, au plus `role.most` variables, au plus 3 propositions). Les trois autres schémas (pydantic) ne posent que `maxLength` (libellé 80, description 300, radical 20) ; les raisons de la conseillère, `maxLength` 400.
- **La ligne de commande** : l'option s'appelle déjà `--adresse` (`--address`), avec `--modele` (`--model`) et `--apercu` (`--preview`) ; **il n'existe pas de `--serveur`**, donc pas d'ancien nom à garder. Commandes concernées : `enrichir`, `rattacher`, `renommer`, `conseiller`, `evaluer`.
- **Les échecs qui arrêtent le travail** : `STOPPING_FAILURES = {"connection", "timeout", "http_404"}` est dans `llm/enrich.py` (l. 32), pas dans `run.py` ; les conseils affichés viennent de `workflow.failure_advice`.
- **La trace** : `AiRun.parameters` est un dictionnaire libre ; il recevra `{"effort": "low", "max_tokens": …}` au lieu de `{"temperature": 0, "seed": 42}`, sans changer le format.
- **Ce que la v0.17 impose** : la case d'activation est une décision enregistrée dans le projet ; elle passe par `c.save()` (seul chemin d'écriture de l'interface, D-130, test qui refuse tout `save_project(` hors de `common.py`) et par le contrôle d'empreinte (D-129) : une activation faite dans un autre onglet est refusée et rappelée comme toute décision. `ddict ia autoriser` écrit par `save_project`, avec le même contrôle. La page « IA locale » est l'entrée « Réglages » de `review/navigation.py` (l. 40).
- **Le fichier projet** n'a aucun réglage d'IA (`Settings` : seuil d'effectifs, valeurs observées, langue, noms). L'activation ajoute un champ à défaut : schéma 0.7.0 → 0.8.0, et un projet 0.7.0 se lit tel quel (champ absent = non activé), comme pour 0.4.0 et 0.5.0.
- **Où Ollama et « l'IA locale » apparaissent**, hors archives : `llm/client.py`, `llm/defaults.py`, `llm/advise.py` (et sa limite de 3 300 jetons), `llm/link.py`, `llm/messages.py`, `llm/advice_bench.py`, `review/navigation.py`, `review/ui/ai_view.py`, `advice_view.py`, `questionnaire_view.py`, `analyses_view.py`, `cli.py` (textes d'aide : « serveur local », `qwen2.5:7b-instruct-q4_K_M`), `workflow.py`, `windows/installer.ps1` (étape 4), `windows/desinstaller.ps1`, `docs/installation-windows.md` et `docs/en/`, `CONCEPTION.md` (titre, § 1, § 3, § 6, § 11), `CLAUDE.md` (présentation et règle 3), `README.md` (présentation, l. 3 et 9), `docs/dependances.md`, `docs/glossaire-traduction.md`, `docs/feuille-de-route-article.md` (§ 9), la traduction `.po` (23 lignes) et `.mo`, `scripts/banc_conseil.py`, `scripts/essai_contexte_modele.py`, et les tests `test_client`, `test_ai_page`, `test_advise`, `test_enrich`, `test_stems`, `test_bench`, `test_link`, `test_navigation`, `test_go_buttons`, `test_sure_choice`.
- **Le désinstalleur** demande déjà avant d'effacer `%APPDATA%\ddict` (listes des projets récents et suivis) ; ce dossier contiendra aussi `ia.json`, la question le dira. La clé, elle, est dans le gestionnaire d'identifiants : une question à part, par `cmdkey /delete:…` (pas besoin de Python, l'outil est déjà retiré à ce moment).
- **Le scénario manuel** (`docs/scenario-revision.md`) suppose Ollama dans sa préparation et aux étapes 8 à 11, 19, 23, 24, 26 et 30, et nomme « IA locale » aux étapes 69 et 70. L'étape 9 attend « 6 blocs réussis », qui change avec la taille des blocs.
- **Le guide** : je n'ai trouvé aucun fichier de guide à part ; je comprends « le guide » comme la section « Commencer » du `README.md` et le guide d'installation. À corriger si l'auteur pense à autre chose.

## 5. Conception — partie A, le moteur

### 5.1 Deux protocoles, une seule interface (D-135)

`llm/client.py` garde l'interface que `run_block` utilise : `complete(messages, schema) -> str`, `endpoint`, `model`, `parameters`, et une fonction `list_models()`, derrière deux classes :

| Classe | Protocole | Adresse par défaut | Paramètres envoyés | Pour |
|---|---|---|---|---|
| `AnthropicClient` | `POST {adresse}/v1/messages`, `GET {adresse}/v1/models` ; en-têtes `x-api-key`, `anthropic-version: 2023-06-01` | `https://api.anthropic.com` | `max_tokens`, `output_config.effort` ; aucune température | Le cas normal |
| `OpenAICompatibleClient` | `/chat/completions` et `/models`, `Authorization: Bearer` (le client actuel) | aucune : l'adresse est obligatoire | température 0 et graine, comme aujourd'hui | Un serveur institutionnel |

Les deux restent écrits avec httpx, sans bibliothèque propre au fournisseur (principe 6 de la conception). Les deux gardent les protections actuelles : proxy de l'environnement ignoré (`trust_env=False`), aucune redirection suivie, aucun identifiant dans l'adresse. La clé n'est lue dans le gestionnaire d'identifiants qu'au moment de l'envoi, ne figure dans aucune représentation de l'objet ni aucun message d'erreur (le corps d'une réponse d'erreur est coupé à 200 caractères, comme aujourd'hui).

`check_local()` devient `check_endpoint()` : **HTTPS obligatoire** ; une adresse de cet ordinateur écrite telle quelle (`localhost`, boucle locale) peut rester en `http`, sans que l'outil installe, détecte ou documente un serveur local (option à trancher, D-135).

`run_block` (« un nouvel essai, puis échec ; un bloc entier ou rien ») ne change pas. Nouveaux codes de `ModelCallError`, chacun avec son conseil dans `failure_advice` :

| Code | Cause | Effet |
|---|---|---|
| `auth` | 401, 403 : clé refusée ou absente | Arrêt immédiat |
| `bad_request` | 400 : schéma ou requête refusés | Arrêt immédiat (un nouvel essai donnerait la même erreur) ; le détail va au dossier des envois |
| `http_404` | modèle inconnu | Arrêt, comme aujourd'hui |
| `rate_limit` | 429 | Une attente selon `retry-after` (au plus 60 s), un seul nouvel envoi, puis arrêt |
| `overloaded` | 529, 500 | Idem |
| `refusal`, `truncated` | `stop_reason` | Comptent comme une réponse invalide (un nouvel essai, puis échec du bloc) |

`STOPPING_FAILURES` (dans `enrich.py`) s'élargit à `auth`, `bad_request`, `rate_limit`, `overloaded`. L'identifiant `request-id` de chaque réponse est gardé dans le dossier des envois, à côté de la réponse.

### 5.2 Le schéma envoyé et le schéma vérifié

`wire_schema(schema)` retire du schéma envoyé `maxLength`, `minLength`, `maxItems`, `minimum`, `maximum`, `multipleOf`, ramène tout `minItems` supérieur à 1 à 1, et vérifie que chaque objet porte `additionalProperties: false` (sinon : erreur de programmation, un test échoue). La conseillère reçoit en plus une forme propre : `prefixItems` remplacé par `items: {"anyOf": [rôles de l'analyse]}`, ce qui reste sous la limite de 16 paramètres à types multiples (12 au plus) ; le test le compte.

Les bornes retirées sont rappelées en une phrase dans la consigne (« libellé de 80 caractères au plus »). La réponse est toujours validée par le modèle pydantic complet et, pour la conseillère, par une vérification locale de ce que la grammaire garantissait (§ 4.2) : un libellé de 81 caractères ou un rôle obligatoire manquant refuse le bloc, comme aujourd'hui. **La validation locale reste la seule garantie.**

Le client compatible OpenAI continue d'envoyer le schéma complet (les serveurs actuels l'acceptent).

**Fait en A5, écart avec ce qui précède** : avec `prefixItems` changé en `anyOf`, le schéma de la conseillère restait dans les limites documentées (10 paramètres à types multiples), mais Anthropic l'a refusé, avec Haiku 5.5 comme avec Sonnet 5.5 : « The compiled grammar is too large ». La conseillère envoie donc à Anthropic une **forme plate** (`advice_schema(…, flat=True)`) : une seule liste des analyses possibles, des rôles, des méthodes et des variables utilisables, sans `anyOf`. Ce que la grammaire ne garantit plus est vérifié sur le poste : un rôle ou une méthode que l'analyse n'a pas et une variable non offerte refusent la réponse (`parse_advice`) ; un niveau de mesure qui ne convient pas ou un rôle manquant sont montrés par les conditions du codebook (`checked`) avant qu'une personne confirme. Le serveur compatible OpenAI garde le schéma strict. Les trois autres schémas sont acceptés tels que `wire_schema` les envoie. Les erreurs du serveur (son message, la clé effacée) sont maintenant gardées dans le dossier des envois.

Tests : pour chacun des quatre schémas, `wire_schema` ne contient que des mots-clés de la liste permise (vérifiée hors ligne) et au plus 24 paramètres facultatifs et 16 à types multiples ; une réponse qui dépasse une borne retirée est refusée par la validation.

### 5.3 La clé (D-137)

- Gardée dans le **gestionnaire d'identifiants de Windows**, par la bibliothèque `keyring` (dans l'extra `ia` ; licences de `keyring` et de ce qu'elle tire sous Windows à vérifier en A3 et à noter dans `docs/dependances.md`), une entrée par adresse, nommée `ddict:<adresse>` (par exemple `ddict:https://api.anthropic.com`, utilisateur `api-key`) : c'est elle que le désinstalleur efface (`cmdkey /delete:ddict:…`). Fait en A3 : le module `llm/keys.py` appelle directement le gestionnaire de Windows de `keyring` (une configuration de `keyring` sur le poste ne peut pas envoyer la clé ailleurs, dans un fichier en clair par exemple), et efface l'ancienne entrée avant d'écrire la nouvelle (sinon `keyring` en garderait une copie sous le nom `api-key@ddict:…`).
- Saisie par la page « IA » (champ masqué) ou par `ddict ia cle` (`ddict ai key`), qui la demande sans l'afficher (`getpass`). **Jamais en argument de commande** (PowerShell garde l'historique) ni en variable d'environnement.
- **Jamais** dans le fichier projet, `ia.json`, le dossier des envois, un message d'erreur, un journal, le rapport du banc ni le dépôt. La page et `ddict ia tester` disent « enregistrée » ou « absente », jamais un caractère de la clé.
- `ddict ia oublier` (`ddict ai forget`) et le bouton « Oublier la clé » l'effacent.
- **Les tests n'approchent jamais le vrai gestionnaire** : un gestionnaire en mémoire (`keyring.set_keyring`) les remplace, sauf les tests `externe`. Un test à chaîne témoin fait traverser une fausse clé connue (visiblement fausse, `sk-ant-FAUSSE-…`) par un enrichissement complet contre le faux serveur, une clé refusée et une erreur 500, puis la cherche dans tous les fichiers écrits, dans les sorties et dans les messages d'erreur.

### 5.4 Les réglages hors projet

`%APPDATA%\ddict\ia.json` (ou `DDICT_CONFIG_DIR`, par `recents.config_dir()`), comme les listes de projets : `{"format": 1, "protocole": "anthropic", "adresse": "https://api.anthropic.com", "modele": "…"}`. Ni clé, ni nom d'étude. JSON déterministe. Absent : Anthropic, et pas de modèle choisi (la page propose le modèle recommandé).

### 5.5 L'activation par projet (D-138)

`Settings.ai = {"allowed": true, "since": "2026-10-19"}` (schéma 0.8.0 ; défaut `allowed: false`). Le refus est vérifié à un seul endroit, avant tout envoi (dans la fonction qui crée le client pour un projet), et non dans la porte de confidentialité : l'aperçu (`--apercu`, bouton « Voir ce qui partirait ») reste toujours permis, puisqu'il n'envoie rien. Dans l'interface, la case passe par `c.save()` ; en ligne de commande, `ddict ia autoriser <projet>` et `ddict ia interdire <projet>` (`ai allow`, `ai deny`). Une commande d'IA sur un projet non activé s'arrête avec un message qui donne la commande à lancer, et un code de sortie non nul.

## 6. Conception — partie B, les quatre usages au niveau 1 (D-136)

**Le niveau 1 : rien de ce que les participants ont répondu.** Partent : les noms et leurs voisins, les étiquettes de variables et de valeurs, les codes manquants déclarés dans le fichier ou confirmés par l'équipe, les textes des questions acceptées, les sigles acceptés du glossaire, le nombre d'items et le préfixe d'un groupe, le catalogue d'analyses et l'objectif écrit par l'équipe ; et le type de la colonne, le niveau de mesure et la note de confidentialité (§ 4.2). Ne partent plus : les codes observés et leurs proportions, le pourcentage de manquants, le minimum, le maximum, la moyenne, les années d'une date, et l'étendue des codes observés dans la description d'un groupe.

| Usage | Consigne | Changement |
|---|---|---|
| Libellés et descriptions | `variables-v4` | `variable_payload` perd `observed`, `pct_missing`, `min`, `max`, `mean`, `years` ; la description de groupe perd `codes de … à …`. Blocs de 25 variables (réglable, `--taille-bloc`). La consigne ne parle plus de statistiques et rappelle les bornes de longueur. |
| Rattachement | `link-v4` | Contenu inchangé (déjà niveau 1). Blocs de 20 variables. Le nombre de candidates reste 5 ; l'augmenter est une mesure du banc, pas un réglage de cette version. |
| Radicaux | `rename-v2` | Contenu inchangé ; bornes rappelées. Reste en ligne de commande ; le banc décide s'il revient dans l'interface (règle de D-051). |
| Conseillère | `advise-v3` | Sans la compression de D-080 ni le seuil de 3 300 jetons : libellés entiers, items des groupes avec leurs libellés, description de groupe sans étendue observée. Une seule borne : 100 000 caractères, au-delà rien ne part. D-080 n'est formellement remplacée qu'après le banc (§ 10). |

**Fait en B3** : `advise-v3` va à Anthropic seulement (avec le schéma plat de A5) : libellés entiers, chaque item d'un groupe avec son libellé, une seule borne de 100 000 caractères. Un serveur compatible OpenAI garde `advise-v2`, le message compact de D-080, qui tient dans un petit contexte. Avec les deux consignes, la description d'un groupe n'a plus son étendue de codes observés : la conseillère l'envoyait quand les libellés des items n'avaient pas de début commun, même après qu'une personne l'avait acceptée.

**Fait en B2, écart avec le tableau** : les consignes du rattachement (`link-v2`, et `link-v3` pour les questions voisines) et des radicaux (`rename-v1`) disaient déjà « Tu reçois des métadonnées, jamais de données individuelles », sans aucune statistique, et la seule borne retirée du schéma envoyé (le radical, 20 caractères au plus) y était déjà écrite. Elles restent donc telles quelles : `link-v4` et `rename-v2` auraient été des copies, et auraient fait refaire sans raison les blocs déjà faits. Seule la taille des blocs change pour la clé d'API (`API_LINK_BLOCK_SIZE`, 20). À savoir : les candidates d'un rattachement et la raison « aucune question » (« date de passation », « score calculé ») sont choisies en partie à l'aide des réponses (une date dont l'étendue est courte, une colonne égale à la somme d'un groupe, les réponses en texte d'un export CSV rapprochées des options), comme le type ; elles ne portent ni réponse ni nombre.

Les messages restent identiques d'une exécution à l'autre (test existant). **Un test à chaînes témoins** construit une base fictive dont les valeurs, les proportions, le minimum, le maximum, la moyenne et les années sont des nombres reconnaissables (p. ex. 7 391), construit les messages des quatre usages, et vérifie qu'aucun n'y figure.

## 7. Conception — partie C, interface, installation, documentation

- **Page « IA »** (`ai_view.py` réécrite ; entrée « IA » du menu « Réglages ») : protocole (Anthropic, ou serveur compatible OpenAI), adresse, clé (masquée, « Enregistrée » si présente, « Oublier la clé »), modèle (liste lue par `list_models`, le modèle recommandé en tête), effort, « Tester la connexion » (un `GET /v1/models`, aucun contenu de projet, rien de facturé). Puis la section **« Ce qui part »** : le niveau 1 en une liste, le fournisseur, la conservation (§ 4.1), le lien vers sa politique, la date de vérification. Le banc reste sur cette page ; avant de le lancer, l'estimation de son coût et une confirmation.
- **La case d'activation** est dans la barre latérale du projet, avec le même texte que la page ; tant qu'elle est décochée, les boutons d'IA (Questionnaire, Variables, Analyses) sont remplacés par une phrase qui y renvoie.
- **Les renvois** « Réglages de l'IA locale » (Questionnaire, Analyses, Variables) deviennent « Réglages de l'IA ».
- **Ligne de commande** : `--adresse`, `--modele`, `--apercu` gardent leur nom ; ajout de `--protocole anthropic|openai` (`--protocol`) ; l'adresse, le protocole et le modèle viennent de `ia.json` quand l'option manque ; `ddict ia cle | oublier | tester | autoriser | interdire` (`ddict ai key | forget | test | allow | deny`). Textes d'aide sans « serveur local » ni exemple qwen.
- **Installateur** : l'étape 4 (Ollama) est retirée, et remplacée par une phrase qui renvoie à la page « IA » ; l'installateur ne demande pas la clé. **Désinstalleur** : la question sur `%APPDATA%\ddict` nomme aussi les réglages de l'IA ; une question à part pour effacer la clé (`cmdkey`), même règle que les listes. `test_installer` suit.
- **Documentation** : `installation-windows.md` (fr et en) remplace la section Ollama par « Obtenir une clé d'API » (création du compte, de la clé, **limite de dépenses** dans la console d'Anthropic, saisie par la page ou `ddict ia cle`) et « Ce qui part » ; `CONCEPTION.md` (titre, § 1, § 3 principes 5 et 6 et leur tableau de garanties, § 6.1 et 6.2, § 11, nouvelle § 24) ; `CLAUDE.md` (présentation et règle 3) ; `README.md` ; `docs/dependances.md` ; `docs/glossaire-traduction.md` ; `docs/feuille-de-route-article.md` § 9 (la reformulation de la règle et le niveau 1 sont faits ; le reste demeure une piste) ; traduction `.po` et `.mo` ; scénario manuel (§ 9.2). Les essais, les anciens plans, le journal et le CHANGELOG ne sont pas réécrits : ce sont des archives ; `scripts/essai_contexte_modele.py` aussi (il appartient à l'essai de D-080).

## 8. Conception — partie D, les essais avec la clé de l'auteur, le banc

### 8.1 Les tests `externe` (D-139)

- Un marqueur `externe`, comme `reel` (D-046) : sauté sauf si `DDICT_TESTS_EXTERNES=1` **et** qu'une clé est enregistrée (le test dit « présente » ou « absente », rien de plus). Jamais en intégration continue.
- `--disable-socket` reste partout ailleurs ; ces tests seuls ouvrent le réseau, vers l'adresse d'Anthropic seulement (marqueurs `enable_socket` et `allow_hosts` de pytest-socket ; le mécanisme exact, sûr avec une adresse qui change d'IP, est vérifié en A5).
- Ils n'utilisent **que les bases fictives** du paquet. Peu nombreux : les quatre schémas acceptés (A5), un appel par usage (D1), une fausse clé refusée avec un message clair.
- **La clé de l'auteur ne transite jamais par Claude** : quand une étape en a besoin, Claude s'arrête et donne la commande (`uv run ddict ia cle`) ; l'auteur la lance dans son PowerShell et confirme. Les tests la lisent dans le gestionnaire d'identifiants. Pour lancer les tests `externe`, Claude donne la commande exacte ; l'auteur la lance, ou Claude la lance après son accord.

### 8.2 Le banc

`ddict evaluer` sur les quatre usages, avec **Haiku 5.5 et Sonnet 5.5** (effort `low`, et `medium` pour le meilleur des deux), comparés au calcul seul et aux mesures de qwen2.5 7B déjà publiées :

1. Rattachements justes (corrigé des bases fictives, 64 et 98 variables) ;
2. Libellés : signaux (citation, seuil, instrument, sigle, sens de code) et acceptés tels quels, **au niveau 1 et au niveau 2** (le niveau 2 n'existe que dans le banc, pour mesurer ce qu'on perd : il réutilise `variables-v3` ; jamais dans l'outil) ;
3. Radicaux : égaux au corrigé ;
4. Conseillère : les 13 objectifs de `scripts/banc_conseil.py`.

Avec la durée, les jetons (entrée, sortie, dont réflexion) et le coût de chaque passage, lus dans `usage`. Consigné dans `docs/essais/2026-10-xx-anthropic.md`. Le modèle par défaut est choisi d'après ce banc (§ 10).

### 8.3 Ordre de grandeur des coûts

Au niveau 1, une variable pèse environ 60 à 120 jetons dans le message (JSON indenté) ; chaque bloc ajoute sa consigne (1 000 à 2 000 jetons) ; la réponse, réflexion comprise, compte quelques milliers de jetons par bloc. Pour les libellés d'une base de 300 variables (12 blocs de 25) : de l'ordre de 0,01 à 0,05 $ avec Haiku 5.5, de 0,30 à 1 $ avec Sonnet 5.5. **Ce sont des estimations** ; le banc mesure les vrais chiffres, que la page « IA » et la documentation reprendront.

## 9. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| A1 | Règles et décisions : `CLAUDE.md` (présentation, règle 3), `CONCEPTION.md` (titre, § 1, § 3, § 6.1), journal (D-134 à D-139) | Relus et validés par l'auteur avant tout code |
| A2 | `AnthropicClient`, `OpenAICompatibleClient`, `check_endpoint`, `wire_schema`, erreurs, `request-id` | Contre un faux serveur (faux transport httpx) pour les deux protocoles : réponse juste (blocs `thinking` puis `text`), consigne passée en `system`, aucune température, champ en trop, borne dépassée, `refusal`, `max_tokens`, 400, 401, 404, 429 avec `retry-after`, 529, redirection, identifiant dans l'adresse et `http` non local refusés ; `wire_schema` des quatre usages dans les limites |
| A3 | Clé (`keyring`) et réglages `ia.json` ; `ddict ia cle / oublier / tester` | Gestionnaire en mémoire dans les tests ; test à chaîne témoin de la fausse clé (fichiers, sorties, erreurs) ; licences notées ; nom de l'entrée fixé |
| A4 | Activation par projet, schéma 0.8.0 ; `ddict ia autoriser / interdire` | Un projet 0.7.0 s'ouvre « non activé » ; aller-retour octet pour octet d'un projet 0.8.0 ; aucun envoi sans activation, l'aperçu toujours ; contrôle d'empreinte (D-129) sur `autoriser` |
| A5 | **Premier contact réel** (arrêt : l'auteur saisit sa clé) | Test `externe` : les quatre schémas envoyés sont acceptés par Haiku 5.5 et Sonnet 5.5 (`title`, `prefixItems` tranchés) ; une fausse clé donne `auth` ; réseau limité à l'adresse d'Anthropic vérifié |
| B1 | Libellés `variables-v4` au niveau 1, description de groupe sans étendue | Test à chaînes témoins des libellés ; messages identiques d'une exécution à l'autre |
| B2 | Rattachement `link-v4`, radicaux `rename-v2` | Tests existants adaptés ; tailles de blocs ; chaînes témoins |
| B3 | Conseillère `advise-v3`, schéma envoyé propre, vérification locale élargie | Libellés entiers ; seuil de 100 000 caractères ; un rôle obligatoire manquant ou une 4ᵉ proposition refusent la réponse ; chaînes témoins sur les quatre usages réunies |
| C1 | Page « IA », case d'activation, renvois, menu | Tests AppTest : enregistrer et oublier une clé (gestionnaire simulé), tester la connexion (faux serveur), aucun bouton d'envoi sans activation, activation refusée quand le fichier a changé ailleurs (D-130), confirmation avant le banc |
| C2 | Retrait d'Ollama : installateur, désinstalleur, CLI, textes, `.po` et `.mo` | Plus aucune mention d'Ollama ni de qwen hors des archives (`docs/essais`, anciens plans, journal, CHANGELOG, `scripts/essai_contexte_modele.py`) ; test qui le vérifie |
| C3 | Documentation : installation (fr, en), « Ce qui part », conception, README, scénario manuel | Relue par l'auteur |
| D1 | Tests `externe` des quatre usages, avec la clé de l'auteur | Réponses valides sur la base fictive, Haiku 5.5 et Sonnet 5.5 |
| D2 | Banc ; essai consigné ; choix du modèle par défaut | Rapport dans `docs/essais/` ; décisions de l'auteur (§ 10) |
| D3 | Version 0.18.0 : CHANGELOG, README, scénario manuel joué, essai d'installation de bout en bout | Une personne installe, saisit une clé, active un projet et obtient des libellés sur la base fictive |

L'ordre A → B → C → D tient l'outil utilisable à chaque étape : tant que C2 n'est pas fait, l'ancien parcours reste en place. A5 vient tôt parce que seul le vrai service dit si un schéma est accepté (une erreur 400 ne se voit pas contre le faux serveur).

### 9.1 Les tests à adapter

`test_client` (deux protocoles), `test_ai_page`, `test_advise`, `test_enrich`, `test_link`, `test_stems`, `test_bench`, `test_navigation`, `test_go_buttons`, `test_sure_choice`, `test_installer`, et les tests du format projet (0.8.0). Les fausses réponses existantes sont réutilisées ; le faux serveur apprend à répondre au format d'Anthropic.

### 9.2 Le scénario manuel

La préparation ne demande plus Ollama mais une clé enregistrée (la clé de l'auteur, sur la base fictive). Les étapes 8 à 11, 19, 23, 24, 26 et 30 sont réécrites pour la page « IA » et l'activation (l'étape 9 attend le nouveau nombre de blocs) ; les étapes 69 et 70 disent « IA » au lieu de « IA locale ». Nouvelles étapes après la 82 : activer un projet, puis le désactiver ; un projet non activé n'offre aucun bouton d'envoi mais montre l'aperçu ; une clé refusée donne un message clair ; « Oublier la clé » ; une activation dans un autre onglet est refusée et rappelée.

## 10. Décisions à prendre

| N° | Décision | Ma recommandation |
|---|---|---|
| D-134 | **La règle 3 et les principes 5 et 6** | Règle 3 du `CLAUDE.md` : « **Aucune donnée de participant ne quitte le poste.** L'IA est un service externe, activé explicitement projet par projet, qui ne reçoit que des métadonnées (le questionnaire et le codebook), jamais rien de ce que les participants ont répondu, pas même agrégé. Le client IA n'accepte qu'une adresse en HTTPS, sans proxy ni redirection ; la clé reste dans le gestionnaire d'identifiants de Windows. Les tests bloquent le réseau (pytest-socket), sauf les tests `externe`. Streamlit écoute sur 127.0.0.1, télémétrie désactivée. » Principe 5 : « Confidentialité par conception. Aucune donnée de participant ne quitte le poste. L'IA, un service externe activé projet par projet, ne reçoit que des métadonnées ; jamais une valeur, une statistique ni un effectif tirés des réponses. » Principe 6 : « Neutralité du moteur. L'IA passe par une adresse configurable, en deux protocoles (Anthropic par défaut, ou un serveur compatible OpenAI), sans bibliothèque propre à un fournisseur. » La présentation du `CLAUDE.md` et le titre de la conception perdent « locale ». *Remplace en partie :* D-073 (« locale »). |
| D-135 | **Les moteurs** : Anthropic, ou un serveur compatible OpenAI ; plus d'Ollama | Deux classes derrière une même interface, httpx seulement ; HTTPS obligatoire ; **`http` accepté pour une adresse de cet ordinateur écrite telle quelle, sans le documenter** (il ne traverse aucun réseau et ne coûte rien à garder ; l'exiger partout empêcherait un serveur de développement sans gagner en sûreté). Côté Anthropic : aucun paramètre d'échantillonnage (refusé), `effort` explicite (`low` par défaut), pas de `fallbacks`. *Remplace :* D-023. |
| D-136 | **Niveau 1 seulement** | Aucun envoi de ce que les participants ont répondu, pas même agrégé : ni codes observés, proportions, manquants, minimum, maximum, moyenne, années, ni étendue observée d'un groupe. **Gardés** : le type de la colonne, le niveau de mesure et la note de confidentialité (calculés des données, mais ils décrivent la colonne, pas une réponse, et la note protège). Le banc mesure la perte ; un niveau 2 ne serait reconsidéré que sur une perte nette, par une nouvelle décision. |
| D-137 | **La clé dans le gestionnaire d'identifiants de Windows** (`keyring`) | Saisie par la page ou `ddict ia cle` (`getpass`), jamais en argument ni en variable d'environnement ; jamais écrite ailleurs ; « enregistrée » ou « absente », jamais affichée ; les tests utilisent un gestionnaire en mémoire. Nouvelle dépendance `keyring` (MIT, à confirmer avec ce qu'elle tire), dans l'extra `ia`. |
| D-138 | **L'activation par projet**, schéma 0.8.0 | `Settings.ai = {"allowed", "since"}`, décochée par défaut ; un projet 0.7.0 se lit « non activé » ; écrite par `c.save()` et le contrôle d'empreinte ; vérifiée à un seul endroit avant tout envoi ; l'aperçu toujours permis. |
| D-139 | **Les tests `externe`** | Sautés sans `DDICT_TESTS_EXTERNES=1` et sans clé enregistrée ; bases fictives seulement ; réseau ouvert vers l'adresse d'Anthropic pour ces tests seuls ; jamais en intégration continue ; la clé saisie par l'auteur lui-même. |

**Tranché après le banc (D2, le 2026-10-19)** : D-140 (`claude-haiku-5-5`, réflexion `medium`), D-141 (les radicaux dans l'interface, page « Noms »), D-142 (la conseillère sans compression avec Anthropic) ; le nombre de candidates reste 5. Ce qui était prévu : le modèle par défaut (Haiku 5.5 ou Sonnet 5.5) et l'effort ; le retour des radicaux dans l'interface (règle de D-051) ; le remplacement formel de D-080 par la borne de 100 000 caractères ; le nombre de candidates du rattachement.

## 11. Risques

- **Un comité d'éthique qui refuse tout envoi externe** : l'outil reste entier sans IA ; l'activation est projet par projet ; la page « IA » et la documentation disent exactement ce qui part, pour que l'équipe le soumette.
- **Un schéma refusé par le service** (mot-clé non documenté, schéma trop complexe) : vu dès A5 par un test réel ; `wire_schema` le simplifie, la validation locale reste.
- **Le prix, les modèles ou les règles d'Anthropic changent** : le modèle est un réglage, la liste vient de `GET /v1/models`, le banc se relance ; la date de vérification de « Ce qui part » est affichée.
- **Une clé qui fuit** : elle ne sort du gestionnaire d'identifiants que pour l'en-tête de la requête ; le test à chaîne témoin le garde ; la documentation conseille une limite de dépenses.
- **Un coût inattendu** : réflexion facturée comme sortie ; effort `low` par défaut, blocs plus grands, confirmation avant le banc ; les jetons de chaque bloc sont gardés dans le dossier des envois.
- **Des propositions de qualité différente de celles d'Ollama dans un même projet** : chaque proposition garde son modèle dans sa trace ; rien n'est remplacé qu'une personne a décidé.
