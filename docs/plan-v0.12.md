# Plan de la v0.12

> Statut : **validé par l'auteur le 2026-10-16**, avec les décisions D-093 à D-100 (§ 8). Suit la feuille de route [`feuille-de-route-article.md`](feuille-de-route-article.md), § 5. Même cap que la v0.11 : de la base à une ébauche d'article IMRaD **sans aucune IA** ; la v0.12 n'ajoute aucun usage de l'IA, locale ou non ; la règle « Rien ne quitte le poste » reste entière ; l'IA conseillère reste telle quelle.

## 1. Pourquoi cette version

Le carnet de la v0.11 donne les Résultats. La section **Méthode** d'un article, elle, s'écrit encore à la main, alors que l'outil en connaît presque tout : les personnes retirées et pourquoi, les instruments, leur source, leur cotation, leur fidélité, les analyses et leurs options. Il manque deux choses :

1. **Les exclusions.** Aujourd'hui, toutes les lignes de la base entrent dans les analyses. Une équipe retire pourtant presque toujours des personnes : refus de consentement, mineurs, questionnaires trop incomplets, passations bâclées. Ces décisions doivent être écrites, appliquées partout de la même façon (outil, SPSS, R) et comptées.
2. **Le texte.** Trois paragraphes (Participants, Instruments, Analyses) et un diagramme de flux, rédigés par des gabarits à partir du codebook et du carnet. Ce qui manque devient un trou visible, jamais une supposition.

## 2. Ce que l'outil produira

**Participants**
- **Des règles d'exclusion**, écrites par l'équipe et gardées dans le projet comme des décisions, jamais comme une liste de personnes (D-093). Chaque règle a une condition, une raison en clair et un rang. Cinq sortes :
  - une **condition sur une variable** : `consentement = 2`, `age < 18`, `groupe manquant` ;
  - une **complétude** : moins de 80 % des items d'un groupe répondus ;
  - une **durée de passation** sous un seuil choisi par l'équipe (exports de plateforme, dates de début et de fin) ;
  - une **réponse en ligne droite** dans une grille (tous les items à la même valeur) ;
  - des **doublons** sur des variables choisies (par exemple le courriel), en gardant la première réponse.
- **Appliquées partout de la même façon** (D-094) : en mémoire avant chaque analyse, après les codes manquants, les noms, les items inversés et les scores ; dans le script de préparation SPSS et R ; dans le script R maître. Jamais dans la copie documentée, qui reste identique à l'original case par case.
- **Les effectifs par règle**, dans l'ordre : *N* de départ, combien chaque règle retire parmi les personnes encore présentes, *N* analysé.
- **Le diagramme de flux**, en figure APA (D-098) : une image dans Word et, à côté, le tableau de ses effectifs, modifiable.
- **Des signaux de qualité de passation**, proposés par des règles et jamais appliqués seuls (D-095) : la page montre combien de personnes chaque signal toucherait, avec le seuil que l'équipe choisit. Elle n'en propose aucun par défaut. Un signal devient une exclusion quand l'équipe l'ajoute comme règle.
- **La description de l'échantillon** : les variables que l'équipe choisit (par exemple l'âge et le genre), données en *M* et *ÉT* ou en pourcentages, sur l'échantillon analysé.

**Instruments**
- Un paragraphe par groupe coté, rédigé par gabarit (D-097) :
  - le nom de l'instrument et sa source ;
  - le nombre d'items et le format de réponse (les étiquettes des extrémités, tirées des étiquettes de valeurs) ;
  - la cotation : somme ou moyenne, nombre minimal d'items répondus, règle des items manquants (D-068), étendue du score ;
  - les items inversés ;
  - la **fidélité observée sur l'échantillon analysé** : l'alpha de Cronbach et son intervalle de confiance à 95 % (D-096).
- Un nom d'instrument, une source ou une cotation manquants donnent un **trou signalé** : « [à compléter : nom et source de l'instrument du groupe G3] ».

**Analyses**
- Un paragraphe tiré du carnet : les analyses retenues et leurs méthodes (Welch, Tukey, Spearman…), le traitement des manquants (suppression par analyse), les tailles d'effet et leurs intervalles, *p* exacts, le logiciel et ses versions, et le script R qui refait tout.

**Le document**
- Le document de la v0.11 devient **« Méthode et Résultats »** (D-099) : une section Méthode (Participants avec le diagramme de flux, Instruments, Analyses), puis la section Résultats du carnet. Les tableaux et les figures sont numérotés à la suite sur tout le document : le diagramme de flux devient la Figure 1, et les Résultats suivent.
- **Les chiffres de la Méthode sont gardés et confirmés comme ceux des Résultats** (D-100) : le carnet garde les effectifs par règle, la description de l'échantillon et les alphas. Si une décision les change, la page « Carnet » le dit, et le document attend une confirmation.
- Les gabarits existent en français et en anglais, en phrases entières traduites d'un bloc. Aucune formulation qui juge (pas d'« excellente fidélité »). Les trous sont **surlignés en jaune** dans Word.

**Interface et ligne de commande**
- **Une page « Méthode »**, après « Carnet » : les règles d'exclusion (ajouter, ordonner, retirer), leurs effectifs, le diagramme de flux, les signaux de qualité, les variables qui décrivent l'échantillon, et un aperçu des trois paragraphes avec leurs trous.
- **En ligne de commande** : `ddict exclusions` (`exclusions`) pour lister, ajouter, retirer et ordonner les règles et voir leurs effectifs ; `ddict resultats` produit le document « Méthode et Résultats ».

## 3. Conception — les règles d'exclusion

**Dans le projet**, format 0.4.0 (migration automatique d'un projet 0.3.0, comme les fois précédentes) :

```json
"exclusions": [
  {"id": "E1", "kind": "condition", "variable": "consentement", "operator": "eq", "value": 2,
   "reason": "Refus de consentement"},
  {"id": "E2", "kind": "condition", "variable": "age", "operator": "lt", "value": 18,
   "reason": "Moins de 18 ans"},
  {"id": "E3", "kind": "completeness", "group": "G1", "min_share": 0.8,
   "reason": "Moins de 80 % des items de bien-être répondus"},
  {"id": "E4", "kind": "duration", "max_seconds": 180, "reason": "Passation de moins de 3 minutes",
   "source": "Seuil fixé par l'équipe, procès-verbal du 2026-10-20"},
  {"id": "E5", "kind": "straightlining", "group": "G2", "reason": "Grille en ligne droite"},
  {"id": "E6", "kind": "duplicate", "variables": ["courriel"], "keep": "first",
   "reason": "Doublon de courriel"}
]
```

- **Des variables par leur nom d'origine** (comme le carnet), pour survivre à un renommage. Un score se désigne par son groupe.
- **Opérateurs** : `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, `missing`. Une valeur manquante ne remplit jamais une condition, sauf `missing`.
- **Interdit** : une condition qui nomme une valeur d'un identifiant (`id_participant = 123` serait une liste de personnes déguisée) ou d'un texte libre. Refus avec sa raison. Seule la règle des doublons peut porter sur un identifiant, comme un courriel : elle compare les lignes entre elles, sans jamais nommer une valeur.
- **Un seuil de durée exige une source**, comme les seuils du codebook (principe 4) : c'est un choix de l'équipe, pas de l'outil.
- **Ordre** : les règles s'appliquent dans leur rang ; une personne n'est comptée que par la première règle qui la retire. Changer l'ordre change les effectifs par règle, jamais le *N* analysé.
- **L'empreinte du codebook** inclut les règles : ajouter une règle rend donc les analyses du carnet « changées, à confirmer » (D-089). La page « Carnet » reçoit un bouton **Tout confirmer**, pour ce cas.

**Dans les scripts.** Le script de préparation crée une variable `ddict_exclusion` (0 pour une personne gardée, sinon le numéro de la première règle qui la retire), affiche ses effectifs, puis ne garde que les personnes à 0 (`SELECT IF` en SPSS, sous-ensemble en R). Les doublons et la durée s'écrivent en SPSS et en R de base, sans extension.

## 4. Conception — fidélité, gabarits et trous

**Alpha et son intervalle** (D-096). L'alpha est recalculé sur l'échantillon analysé, après les exclusions, les codes manquants et les items inversés, sur les personnes qui ont répondu à tous les items du score. Son intervalle de confiance à 95 % suit Feldt (1965), une formule fermée, vérifiable en R de base (`qf`). L'alpha observé que la page « Groupes » montre déjà (avant décisions) ne change pas. L'**oméga** est reporté (D-096).

**Gabarits** (D-097). Chaque paragraphe est une suite de phrases fixes, chacune avec ses champs : « Le bien-être a été mesuré par {instrument} ({source}), {k} items notés de {min} ({étiquette min}) à {max} ({étiquette max}). » Une phrase dont un champ manque n'est jamais tronquée ni devinée : le champ devient un trou, « [à compléter : …] ». La fiche (étape 1) donne chaque phrase en français et en anglais, sur la base fictive, avant toute ligne de code.

**Tout fait du texte a une origine** : un champ du codebook, un effectif calculé ou une entrée du carnet. Un test le vérifie phrase par phrase.

## 5. Conception — une base fictive de passation

Une nouvelle base fictive au format SurveyMonkey, générée par `scripts/` avec une graine fixe, avec son corrigé (`corrige-passation.json`) : 400 réponses, un consentement, l'âge, une échelle cotée, une grille, les dates de début et de fin. Les cas y sont **plantés** : refus de consentement, mineurs, réponses incomplètes, passations trop courtes, grilles en ligne droite, doublons, dont certains cumulent plusieurs raisons (pour vérifier l'ordre). Le corrigé donne les effectifs attendus pour chaque ordre des règles, et l'alpha et son intervalle.

## 6. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiche : format des règles, signaux de qualité, diagramme de flux, gabarits des trois paragraphes en français et en anglais, trous, sur la base fictive de passation | Validée par l'auteur |
| 2 | Base fictive de passation et son corrigé | Générée à l'identique deux fois (graine fixe) ; corrigé vérifié indépendamment du code de l'outil |
| 3 | Règles d'exclusion dans le projet (format 0.4.0, migration), appliquées en mémoire et dans les scripts de préparation SPSS et R | Mêmes effectifs par règle dans l'outil, PSPP et R, égaux au corrigé ; une condition sur une valeur d'identifiant est refusée ; la copie documentée ne change pas |
| 4 | Effectifs par règle et diagramme de flux (figure Word, tableau modifiable) | Égaux au corrigé ; test commun des formats (D-083) passé |
| 5 | Signaux de qualité (durée, ligne droite, doublons) | Cas plantés retrouvés ; aucun signal sans seuil choisi par l'équipe ; aucun appliqué sans règle |
| 6 | Fidélité : alpha sur l'échantillon analysé et son IC de Feldt | Égaux au corrigé et à R, à 10⁻⁶ près |
| 7 | Paragraphes, trous et document « Méthode et Résultats » ; chiffres de la Méthode gardés et confirmés dans le carnet | Chaque fait du texte retrouvé dans le codebook ou le carnet (test) ; un champ vide donne un trou ; numérotation continue sur tout le document ; vérifié dans Word |
| 8 | Page « Méthode », bouton « Tout confirmer », `ddict exclusions`, `ddict resultats` | Parcours dans le navigateur ; mêmes fichiers depuis la page et la ligne de commande |
| 9 | Essai sur une vraie base (aucun effectif ni résultat consigné, faits de structure seulement) ; guides, journal des changements, version 0.12.0 | Scénario refait dans le navigateur ; guides en français et en anglais. *Essai : `docs/essais/2026-10-17-essai-methode.md`.* |

Si la version s'allonge, les signaux de qualité (étape 5) passent en 0.12.1 : les règles d'exclusion écrites à la main suffisent pour la Méthode.

**Une correction en passant** (fil ouvert depuis la v0.9) : la phrase de résultat d'une corrélation écrit *r* avec un zéro initial (« r(194) = 0,01 »), alors que les tableaux, à juste titre, n'en mettent pas (« ,01 »). La phrase sera corrigée à l'étape 7, puisque la Méthode et les Résultats se lisent désormais côte à côte. Seule la phrase change ; aucune statistique gardée par le carnet ne bouge.

## 7. Risques

- **Une règle d'exclusion qui devient une liste de personnes** : refusée quand elle nomme une valeur d'identifiant ; ailleurs, c'est à l'équipe de juger, et le guide le dit.
- **Des exclusions qui changent tout le carnet** : chaque analyse devient « changée, à confirmer » ; **Tout confirmer** l'évite, et la page montre ce qui a changé avant.
- **Des seuils de qualité choisis par l'outil** : aucun seuil par défaut ; une durée exige une source.
- **Un texte raide** : les gabarits sont validés par l'auteur avant le code (étape 1), et le texte se modifie dans Word.
- **Des petits effectifs dans le diagramme de flux** (deux doublons, une personne mineure) : ils sont ce que l'article publie ; ils ne vont jamais au modèle, et le guide rappelle de juger avant de publier.
- **Une version chargée** : neuf étapes ; voir le report possible de l'étape 5.

## 8. Décisions à prendre

La feuille de route réservait D-090 à D-092 à la v0.12 ; la v0.11 ayant pris D-087 à D-092, les décisions ci-dessous prennent D-093 à D-100. Les numéros proposés pour les versions suivantes se décaleront d'autant.

| N° | Décision | Recommandation |
|---|---|---|
| D-093 | **Les règles d'exclusion** | Des décisions du projet (format 0.4.0), écrites par une personne, avec une raison et un rang : condition sur une variable, complétude d'un groupe, durée, ligne droite, doublons. Jamais une liste de personnes : refus d'une condition qui nomme une valeur d'un identifiant ou d'un texte libre (seule la règle des doublons compare des identifiants entre eux, sans nommer de valeur). Un seuil de durée exige une source. |
| D-094 | **Où et quand s'appliquent les exclusions** | Après les codes manquants, les noms, les items inversés et les scores (une règle peut porter sur un score) ; en mémoire avant chaque analyse, dans les scripts de préparation SPSS et R et dans le script R maître ; jamais dans la copie documentée. Les règles entrent dans l'empreinte du codebook. |
| D-095 | **Les signaux de qualité de passation** | Calculés par des règles, montrés avec leurs effectifs, jamais appliqués seuls ; aucun seuil par défaut ; chacun devient une exclusion quand l'équipe l'ajoute comme règle. |
| D-096 | **La fidélité dans la Méthode** | L'alpha de Cronbach recalculé sur l'échantillon analysé, avec son intervalle de confiance de Feldt, vérifiés dans R. L'oméga est reporté : il demanderait une analyse factorielle (une nouvelle dépendance, ou un code d'estimation à écrire) et, pour le vérifier, un paquet R qui n'est pas installé ; il reviendra avec le moteur R facultatif (D-071) ou le catalogue élargi. |
| D-097 | **Les gabarits de la Méthode** | Phrases fixes, en français et en anglais, traduites d'un bloc ; tout champ manquant donne un trou « [à compléter : …] », surligné dans Word ; aucune formulation qui juge ; chaque fait du texte a une origine dans le codebook ou le carnet. |
| D-098 | **Le diagramme de flux** | Une figure APA dessinée (image dans Word, comme les autres figures) et, à côté, le tableau de ses effectifs, modifiable dans Word et dans Excel. Pas de graphique Excel natif : Excel n'a pas de type de graphique pour un diagramme de flux. |
| D-099 | **Le document « Méthode et Résultats »** | Les mêmes trois fichiers que la v0.11 (`-resultats.docx`, `-resultats-graphiques.xlsx`, `-resultats-R.zip`), pour ne pas multiplier les fichiers ; le Word reçoit la section Méthode avant les Résultats, avec une numérotation continue sur tout le document. Un nom de fichier d'article viendra avec le squelette IMRaD de la v0.13. |
| D-100 | **Les chiffres de la Méthode, gardés et confirmés** | Le carnet garde aussi les agrégats de la Méthode (effectifs par règle, description de l'échantillon, alphas et leurs intervalles), comparés et confirmés comme une analyse (D-089) : aucun chiffre de la Méthode ne change dans le document sans qu'une personne l'ait vu. Le carnet passe en `carnet_version` 1.1.0 (un carnet 1.0.0 s'ouvre tel quel). |
