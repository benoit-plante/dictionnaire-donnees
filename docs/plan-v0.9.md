# Plan de la v0.9

> Statut : **proposé le 2026-10-15, en attente de validation par l'auteur** (décisions D-069 à D-076 au § 9). Cette version touche deux règles fondatrices : « Rien ne quitte le poste » (règle 3 du `CLAUDE.md`, principe de `CONCEPTION.md`) et « aucune exécution de code d'analyse dans l'outil » (D-065). Rien n'en sera changé sans une décision explicite de l'auteur.

## 1. Pourquoi cette version

La v0.8 a fait du codebook un contrat d'analyse. L'essai de son étape 8 a montré deux choses :

- **un petit modèle local ne sait pas écrire une analyse** : qwen2.5 7B a échoué six fois sur six, faute de savoir programmer en R ;
- **un assistant en ligne y arrive à partir du seul contexte** : trois assistants (Claude Opus 5.5 et Haiku 5.5, Gemini 3.6) ont écrit une analyse juste ou presque, sans jamais voir les données, pour quelques cents au plus.

Aujourd'hui, la personne fait le chemin à la main : copier le contexte dans un assistant, rapporter le code, le relire, l'exécuter dans son logiciel. L'auteur souhaite que l'outil fasse ce chemin : **choisir un modèle, en ligne si l'équipe le permet, obtenir le code, le vérifier, puis l'appliquer à la base, dans l'outil.**

C'est faisable, mais c'est la partie la plus risquée de tout ce que l'outil a envisagé : des métadonnées qui quittent le poste, et du code écrit par une IA exécuté sur de vraies données. Cette version n'a de sens qu'avec des garde-fous à chaque étape du chemin.

## 2. Le chemin proposé

```
question de l'équipe
  → contexte d'analyse (v0.8) + consigne        [porte de confidentialité]
  → modèle local, ou en ligne si permis         [aperçu exact, registre]
  → code R proposé
  → vérificateur de scripts                     [règles bloquantes et avertissements]
  → exécution sur la base synthétique           [automatique, sans risque]
  → relecture et approbation par une personne   [obligatoire]
  → exécution sur la vraie base                 [dossier isolé, copie, délai]
  → résultats affichés sur le poste
  → (facultatif) résultats renvoyés au modèle   [seulement des agrégats filtrés]
```

Le code peut aussi venir d'ailleurs : une personne qui colle le code d'un assistant utilisé à la main (comme à l'essai de l'étape 8) suit le même chemin à partir du vérificateur.

## 3. Contenu proposé

| | Fonction | Ce qu'elle apporte |
|---|---|---|
| A | **Modèles en ligne, sur option** : un service compatible (OpenAI, Anthropic, Google, ou tout service au format OpenAI), désactivé par défaut, activé par projet avec une attestation de l'équipe | Les modèles capables d'écrire du code, sans changer le reste de l'outil |
| B | **Base synthétique** générée à partir du projet seul : même structure, mêmes codes, mêmes manquants, distributions marginales proches ; marquée fictive | Essayer tout code sans toucher aux vraies données |
| C | **Vérificateur de scripts** : analyse du code R avant toute exécution | Le garde-fou qui rend l'exécution défendable |
| D | **Page « Analyse »** : une question, un modèle, le code proposé, son contrôle, son essai sur la base synthétique, l'approbation, l'exécution sur la vraie base, les résultats | Le chemin entier dans l'outil, ou à partir d'un code collé |
| E | **Porte de confidentialité des résultats** : ce qui peut être renvoyé à un modèle | Une boucle de correction sans fuite de données |

**Hors de cette version :** les filtres du questionnaire (prévus plus tôt en v0.9) passent à une version suivante ; l'exécution de Python ou de syntaxe SPSS (R seulement : il est installé chez l'auteur, et haven lit tous les formats de l'outil) ; une vraie application Mac ; la relecture de l'anglais.

## 4. Conception — modèles en ligne (A)

- **Fournisseurs** : un client au format OpenAI (le plus répandu, accepté aussi par plusieurs autres services) et un client Anthropic ; adresse, modèle et clé donnés par la personne. Aucun fournisseur par défaut.
- **Désactivé par défaut**, activé **projet par projet**, après une case où l'équipe atteste que son certificat d'éthique permet d'envoyer à ce service les métadonnées de l'étude. L'attestation est enregistrée dans le projet (qui, quand, quel service).
- **Ce qui part** : exactement ce que reçoit déjà le modèle local, construit par la porte de confidentialité (`ddict.privacy`) ; pour l'analyse, le contexte d'analyse sans statistiques, sauf si l'équipe coche aussi les statistiques. **Jamais une donnée individuelle.** L'aperçu exact est montré avant chaque envoi, et chaque envoi est consigné (service, modèle, empreinte du message, date), comme les appels locaux (`AiRun`).
- **La clé d'accès** reste sur le poste, dans le trousseau du système (Gestionnaire d'identification de Windows, Trousseau du Mac), jamais dans le projet ni dans un fichier du dépôt.
- **Les tests** gardent le réseau bloqué : faux serveurs seulement.

## 5. Conception — base synthétique (B)

- Générée **à partir du fichier projet seulement**, jamais du tableau (règle 2) : pour chaque variable, sa structure (type, codes et étiquettes, manquants déclarés et leur taux), une distribution marginale tirée du profil enregistré (effectifs des codes, masqués sous 5 et alors approchés ; moyenne, écart-type et étendue observée pour une variable continue). Les variables sensibles reçoivent des valeurs inventées de même forme (identifiants « FICTIF-001 »).
- Les liens entre variables ne sont pas reproduits, sauf la structure des groupes (items d'une échelle tirés autour d'un même niveau, pour qu'un score ait un sens) : la base sert à faire tourner le code, pas à en tirer des conclusions.
- Marquée fictive dans son nom (`-synthetique.sav`) et son étiquette de fichier ; graine fixe, donc reproductible.
- Utile seule aussi : une équipe peut la donner à n'importe qui pour mettre au point un script.

## 6. Conception — vérificateur de scripts (C)

Une analyse statique du code R (sans l'exécuter), en deux niveaux :

| Niveau | Règle |
|---|---|
| **Bloquant** | accès au réseau (`download.file`, `url(`, `httr`, `curl`, `socketConnection`…) ; commandes du système (`system`, `shell`, `processx`…) ; écriture ou suppression hors du dossier de travail (`unlink`, `file.remove`, `write*` avec un chemin absolu ou `..`) ; installation de paquets ; affichage de lignes de données (`print(donnees)`, `head`, `View`, `donnees[i, ]` sans agrégation) ; une variable sensible du projet dans le code |
| **Avertissement** | une variable à codes manquants utilisée sans `zap_missing`, `is.na` ni ses codes ; un item inversé confirmé additionné sans son inversion ; un score recalculé alors que le script de préparation le donne ; un niveau nominal traité comme continu (moyenne d'un code) |

Un script bloqué ne s'exécute pas ; les avertissements sont montrés à la personne, qui décide. Le vérificateur est imparfait par nature (un code peut contourner une règle) : c'est une aide, pas une garantie, et le guide le dit.

## 7. Conception — exécution et résultats (D, E)

- **Toujours d'abord sur la base synthétique**, automatiquement : un code qui échoue ou bloque n'atteint jamais la vraie base.
- **Puis sur la vraie base seulement après l'approbation d'une personne**, qui a vu le code, le rapport du vérificateur et le résultat sur la base synthétique (principe 5 : toute production de l'IA est une proposition).
- **Exécution** : `Rscript --vanilla` dans un dossier de travail à part, sur une **copie** de la base (la copie documentée quand elle existe), avec un délai maximal ; le fichier d'origine n'est jamais touché. **Limite à dire clairement** : sous Windows, sans conteneur, ce n'est pas un vrai bac à sable ; un code malveillant qui échapperait au vérificateur aurait les droits de la personne. D'où les règles bloquantes, l'essai synthétique et l'approbation.
- **Résultats** : le code doit ranger ses résultats dans une liste `resultats` (tableaux et nombres). Ils sont affichés sur le poste tels quels. **Pour les renvoyer à un modèle** (correction d'une erreur, interprétation), seuls passent ceux qui franchissent la porte : agrégats seulement, effectifs de moins de 5 masqués, aucune colonne d'une variable sensible, aucun vecteur de la longueur de la base ; et une erreur R est renvoyée sans les valeurs qu'elle pourrait citer.
- **Trace** : le code exécuté, le rapport du vérificateur, l'empreinte du codebook et la date sont gardés à côté du projet, pour savoir ce qui a produit quel résultat.

## 8. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Modèle de menace et conception détaillée (ce qui peut mal tourner, à chaque flèche du chemin) ; consignés dans `CONCEPTION.md` | Validés par l'auteur ; chaque risque a sa parade ou est dit comme limite |
| 2 | Base synthétique (B) | Générée depuis le projet seul (test : aucune valeur du tableau n'y figure hors des codes étiquetés) ; le script de préparation et l'analyse de l'essai 8 y tournent |
| 3 | Vérificateur de scripts (C) | Chaque règle testée sur des scripts écrits pour l'enfreindre ; les scripts justes de l'essai 8 passent sans blocage |
| 4 | Exécution isolée et résultats (D, E), à partir d'un code collé | Le code d'Opus de l'essai 8 donne dans l'outil les mêmes résultats qu'à l'essai ; un code bloqué ne s'exécute jamais ; la porte des résultats testée |
| 5 | Modèles en ligne (A) : clients, clé dans le trousseau, attestation, aperçu, registre | Faux serveurs : rien ne part sans attestation ; le message envoyé est exactement l'aperçu ; la clé n'est écrite nulle part ailleurs (test) |
| 6 | Page « Analyse » : question, modèle, code, contrôle, essai synthétique, approbation, exécution | Parcours complet sur la base fictive, avec le modèle local et un faux serveur en ligne |
| 7 | Boucle de correction facultative : erreur ou résultat renvoyé au modèle, filtré | Une erreur R corrigée par le modèle sans qu'aucune valeur ne parte (test) |
| 8 | Essai : de la question au résultat, sur la base fictive, avec un modèle en ligne choisi par l'auteur | Essai consigné dans `docs/essais/` |
| 9 | Guides, journal des changements, version 0.9.0 | Scénario refait dans le navigateur ; guides en français et en anglais |

## 9. Risques

- **Exécution de code écrit par une IA** : effacement, écriture ou envoi de données. Parades : vérificateur bloquant, base synthétique d'abord, approbation humaine, copie de la base, dossier isolé, délai ; limite dite (pas de vrai bac à sable sous Windows).
- **Fuite de métadonnées vers un service en ligne** : désactivé par défaut, attestation par projet, aperçu exact, registre ; la décision reste celle de l'équipe et de son comité d'éthique.
- **Fuite de résultats** dans la boucle de correction : porte des résultats, agrégats seulement.
- **Base synthétique prise pour de vraies données** : marquée fictive partout ; liens entre variables non reproduits, dit dans le guide.
- **Faux sentiment de sécurité** : le vérificateur et la porte réduisent les risques, ils ne les suppriment pas ; le guide le dit.
- **Coût et variabilité des modèles en ligne** : quelques cents par analyse à l'essai ; le registre garde le modèle utilisé.
- **Version trop chargée** : si elle s'allonge, la boucle de correction (étape 7) passe en 0.9.x ; la base synthétique, le vérificateur et l'exécution à partir d'un code collé (étapes 2 à 4) forment un premier ensemble utile, même sans modèle en ligne.

## 10. Décisions à prendre

| N° | Décision | Recommandation |
|---|---|---|
| D-069 | **Périmètre de la v0.9** | Modèles en ligne sur option, base synthétique, vérificateur, exécution dans l'outil avec approbation, porte des résultats ; filtres du questionnaire reportés ; R seulement. |
| D-070 | **Modèles en ligne** (remplace en partie la règle « Rien ne quitte le poste ») | Permis sur option seulement : désactivés par défaut, activés par projet avec l'attestation de l'équipe ; seul part ce que construit la porte de confidentialité ; aperçu et registre. La règle 3 du `CLAUDE.md` est réécrite en ce sens, et les données individuelles ne quittent toujours jamais le poste. |
| D-071 | **Clé d'accès** | Dans le trousseau du système, par la bibliothèque `keyring` (MIT) ; jamais dans le projet. Autre choix : une variable d'environnement, plus simple mais moins sûre pour une personne qui ne programme pas. |
| D-072 | **Exécution de code dans l'outil** (remplace D-065) | R seulement, toujours sur la base synthétique d'abord, sur la vraie base après approbation d'une personne, dans un dossier isolé sur une copie ; la limite de l'isolement est dite. Autre choix : garder D-065 et faire de l'assistant un projet distinct qui lirait le contexte d'analyse. |
| D-073 | **Vérificateur de scripts** | Règles bloquantes (réseau, système, fichiers hors du dossier, affichage de lignes, variables sensibles) et avertissements (codes manquants, inversions, niveaux) ; une aide, pas une garantie. |
| D-074 | **Base synthétique** | Depuis le projet seul ; distributions marginales et structure des groupes ; marquée fictive ; graine fixe. |
| D-075 | **Ce qui peut revenir à un modèle** | Seulement les résultats rangés dans `resultats` qui passent la porte : agrégats, effectifs d'au moins 5, aucune variable sensible, aucun vecteur de la longueur de la base. |
| D-076 | **Filtres du questionnaire** | Reportés à une version suivante. |
