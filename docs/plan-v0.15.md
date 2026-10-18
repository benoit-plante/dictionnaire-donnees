# Plan de la v0.15

> Statut : **validé par l'auteur le 2026-10-18**, recodage compris, avec les décisions D-117 à D-120 (§ 8). Suit la feuille de route [`feuille-de-route-article.md`](feuille-de-route-article.md), § 8, et les deux essais sur la base ouverte AMATUS ([`essais/2026-10-18-essai-plan-article-amatus.md`](essais/2026-10-18-essai-plan-article-amatus.md), [`essais/2026-10-18-essai-v014-amatus.md`](essais/2026-10-18-essai-v014-amatus.md)). Même cap que les v0.11 à v0.14 : **aucune IA ajoutée** ; la règle « Rien ne quitte le poste » reste entière. Fiche de l'étape 1 : [`verification-depot.md`](verification-depot.md).

## 1. Pourquoi cette version

L'outil produit une ébauche d'article complète. Trois choses manquent encore entre elle et la soumission :

1. **Les chiffres du texte final.** L'ébauche est retouchée dans Word : phrases déplacées, valeurs recopiées, ancienne version collée. Rien ne dit si ses chiffres sont encore ceux du calcul. Les numéros D-098 et D-099 que la feuille de route prévoyait pour ces choix ont servi depuis ; les décisions de cette version prennent D-117 à D-120.
2. **Le dépôt.** Revues et OSF demandent un paquet de reproduction : codebook, plan, scripts, un README. L'équipe le rassemble aujourd'hui à la main.
3. **Une variable dérivée.** Les deux essais AMATUS ont dû préparer, hors de l'outil, une variable `enseignante` tirée de l'échantillon : l'outil ne sait pas recoder.

## 2. Ce que l'outil produira

- **Le vérificateur des chiffres** : il lit un `.docx` (l'ébauche de l'outil retouchée, ou un manuscrit écrit sans lui), y repère les statistiques écrites au style APA, en français et en anglais, et compare chaque valeur aux analyses du carnet, recalculées sur la base. Chaque valeur est classée : **concorde**, **diffère** (avec la valeur attendue), **signe inversé**, **sans origine**, ou **non reconnue**. Il donne un rapport (Markdown et Excel) et une **copie** du manuscrit avec des commentaires Word aux endroits concernés ; l'original n'est jamais modifié.
- **Le paquet de reproduction** : un `.zip` prêt pour l'OSF ou Borealis, avec le codebook (Excel, Markdown, `datapackage.json`), le préenregistrement, le carnet, le fichier de commandes, le script de préparation, le script R maître, un README de dépôt rédigé par gabarit (ce que l'outil ignore reste un trou) et la liste des fichiers avec leur empreinte. **Jamais la base**, ni aucune valeur individuelle.
- **Le recodage** : une variable dérivée, décrite comme une décision du projet, jamais comme des données. Deux sortes : **regrouper des modalités** (« enseignante = oui pour ces échantillons ») et **découper en classes** une variable numérique ou un score (« âge : moins de 30, 30 à 44, 45 et plus »). Appliquée partout comme les scores : analyses, exclusions, sous-groupes, plan, script de préparation SPSS et R, script R maître ; documentée dans le codebook avec sa règle.

## 3. Conception — le vérificateur

Le détail (formes reconnues, arrondis, rattachement, exemples) est dans la fiche. Principes :

- **Ce qu'il lit** (D-117) : les statistiques au style APA, dans les paragraphes et les tableaux. Tout chiffre ambigu est dit « non reconnu » plutôt que deviné ; un numéro de tableau, une date, une étendue de cotation ne sont jamais pris pour une statistique.
- **À quoi il compare** (D-118) : les analyses du carnet, recalculées sur la base actuelle avec les décisions en vigueur, comme le document (D-089) ; et les faits de la Méthode. Sans la base, il compare aux valeurs gardées dans le carnet, et le rapport le dit en tête.
- **L'arrondi** : une valeur écrite avec *k* décimales concorde si elle est à moins d'une demi-unité de sa *k*-ième décimale de la valeur calculée ; « *p* < ,001 » concorde si le *p* calculé est sous ,001.
- **Rattacher une valeur à une analyse** : par la statistique de test et ses degrés de liberté de la même phrase ou de la même ligne de tableau ; à défaut, par la section (« A3 — … », « H2 — … ») ; jamais au hasard : une valeur qui pourrait venir de deux analyses le dit.
- **Le manuscrit ne quitte pas le poste** et n'est jamais modifié ; le rapport cite des statistiques, pas le texte qui les entoure.

## 4. Conception — le paquet de reproduction

- **Sans la base** (D-119), que l'équipe dépose ou non selon son certificat d'éthique ; sans le fichier projet, dont le profil contient des valeurs observées ; sans base synthétique (D-076). Un test à chaînes témoins vérifie qu'aucune valeur de la base n'entre dans le paquet.
- **Le README de dépôt** dit ce que contient le paquet, comment refaire les analyses une fois la base placée à côté (SPSS ou PSPP puis R), la version de l'outil, l'empreinte du codebook ; les auteurs, la licence et le lieu du dépôt restent des trous.
- Les fichiers sont produits au moment du paquet, comme le document (D-089) : jamais une copie d'un fichier plus ancien.

## 5. Conception — le recodage

- **Une décision, pas des données** (D-120) : la règle (la variable source, les correspondances ou les seuils, le nouveau nom, les étiquettes, le niveau de mesure, la raison) est gardée dans le projet ; la nouvelle colonne est calculée en mémoire, comme un score. Le projet passe au format 0.7.0.
- **Ce qui se recode** : une variable codée (nominale, ordinale) ou numérique, ou un score ; jamais un identifiant, un texte libre ou une date, comme pour les exclusions et les sous-groupes (D-093, D-113).
- **L'ordre d'application** : codes manquants, noms, items inversés, scores, **recodages**, puis règles d'exclusion et sous-groupes, qui peuvent ainsi porter sur une variable recodée.
- **Chaque valeur observée a sa place** : en regroupement, une valeur non attribuée est refusée, à moins que la règle ne la déclare manquante ; en classes, les seuils couvrent toute l'étendue observée. Les effectifs de chaque nouvelle modalité sont montrés avant d'enregistrer.
- **Partout de la même façon** : le script de préparation SPSS (`RECODE … INTO`) et R, le script R maître, le codebook (une variable dérivée avec sa règle), la Méthode (« La variable enseignante a été tirée de sample : … »).

## 6. Étapes

| # | Étape | Critère de réussite |
|---|---|---|
| 1 | Fiche : le vérificateur (formes, arrondis, rattachement, classes, rapport), le paquet (contenu, README), le recodage (règles, ordre, scripts) | Validée par l'auteur ; exemples tirés d'une ébauche produite par l'outil sur la base fictive de suivi |
| 2 | Le recodage : modèle, application en mémoire, refus, effectifs | Les exemples de la fiche retrouvés ; un recodage utilisable dans une analyse, une exclusion, un sous-groupe et une hypothèse |
| 3 | Le recodage dans les scripts, le codebook et la Méthode ; page et `ddict recoder` | Mêmes effectifs dans l'outil, dans R et dans PSPP ; page et commande écrivent la même règle |
| 4 | Lecture des statistiques d'un `.docx` | Sur un corpus fictif, chaque statistique trouvée avec son type, sa valeur et ses décimales ; aucun faux positif sur les dates, les numéros, les étendues |
| 5 | Rapprochement, rapport et copie commentée ; page « Vérifier » et `ddict verifier` | L'ébauche de l'outil : tout « concorde » ; une ébauche altérée : chaque altération trouvée et bien classée ; commentaires lisibles dans Word et LibreOffice |
| 6 | Le paquet de reproduction ; bouton de la page « Carnet » et `ddict deposer` | Le paquet décompressé, la base fictive placée à côté : le script R maître redonne les chiffres du carnet ; aucune valeur de la base dans le paquet |
| 7 | Essai AMATUS sans fichier dérivé (recodage dans l'outil) et vérificateur passé sur l'article publié ; scénario dans le navigateur ; guides, journal des changements, version 0.15.0 | Chiffres de l'article retrouvés et classés ; guides en français et en anglais |

Si la version s'allonge, le paquet de reproduction (étape 6) passe en 0.15.1.

## 7. Risques

- **Un faux sentiment de sécurité** : « tout concorde » ne dit rien des chiffres que le vérificateur n'a pas reconnus. Le rapport compte les « non reconnues » en tête, et dit ce qu'il ne lit pas (figures, images, notes de bas de page).
- **Des valeurs coupées dans Word** : une retouche coupe parfois un nombre en plusieurs morceaux de mise en forme ; la lecture se fait sur le texte du paragraphe, et le commentaire s'accroche au paragraphe quand il ne peut pas s'accrocher au nombre.
- **Le recodage touche à tout** : comme le sous-groupe en v0.14, il vient tôt (étapes 2 et 3), et chaque endroit est vérifié par une seconde voie (R, PSPP).
- **Le paquet et la confidentialité** : le README ne cite aucune statistique ; le carnet n'a que des agrégats (D-088), et ses effectifs inférieurs à 5 restent signalés.

## 8. Décisions

| N° | Décision | Choix |
|---|---|---|
| D-117 | **Ce que lit le vérificateur** | Les statistiques au style APA seulement, dans le texte et les tableaux ; tout chiffre ambigu est « non reconnu » plutôt que deviné. |
| D-118 | **La référence de comparaison** | Les analyses du carnet recalculées sur la base actuelle (comme D-089) et les faits de la Méthode ; sans la base, les valeurs du carnet, et le rapport le dit. |
| D-119 | **Le contenu du paquet** | Sans la base ni le fichier projet ni aucune valeur individuelle ; le carnet, qui n'a que des agrégats ; pas de base synthétique (D-076). |
| D-120 | **Le recodage** | Dans cette version, en premier (étapes 2 et 3), parce qu'il touche à tout : regrouper des modalités et découper en classes, comme une décision du projet appliquée partout. Si la version s'allonge, c'est le paquet de reproduction qui passe en 0.15.1. |
