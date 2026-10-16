# Contexte d'analyse : etude-sommeil.sav

- Base : `etude-sommeil.sav` (SPSS), 200 lignes, 34 variables. Empreinte du fichier : `a189e6bd7c31`.
- Codebook : empreinte `e32f2238c27f`, dictionnaire-donnees 0.8.0. Seules les décisions acceptées par l'équipe y figurent.
- Une ligne représente : un participant
- Structure : transversale
- Description de la base : Étude fictive sur le sommeil, une seule passation.

## Règles

1. Les codes de la colonne « Manquants » sont des valeurs manquantes : les exclure de tout calcul.
2. Inverser les items marqués « inv » avant tout score, selon la cotation de leur groupe.
3. Les variables marquées « sensible » ne doivent apparaître dans aucune sortie (ni valeurs, ni listes).
4. « Non documenté » veut dire inconnu : ne pas le deviner. Ne citer aucun seuil, étendue ou instrument absent de ce document.

## Complétude

Question rattachée 34 / 34 · Libellé 33 / 34 · Étiquettes de valeurs (variables codées) 17 / 21 · Niveau de mesure 27 / 27 · Cotation (groupes d'échelle) 1 / 2 · Description de la base dite.
Non documenté : Libellé : sommeil_q7 ; Étiquettes de valeurs (variables codées) : aide_medicament, aide_naturel, aide_tcc, aide_aucune ; Cotation (groupes d'échelle) : G2.

## Groupes

**G1** (échelle, 8 variables) : `sommeil_q1`, `sommeil_q2`, `sommeil_q3`, `sommeil_q4`, `sommeil_q5`, `sommeil_q6`, `sommeil_q7`, `sommeil_q8`.
Valeurs de tous ses items : 1 Pas du tout ; 2 Un peu ; 3 Moyennement ; 4 Beaucoup ; 5 Extrêmement.
Cotation : sommeil_total = somme des 8 items, après inversion de sommeil_q3, sommeil_q6 (6 - x) ; au moins 7 items répondus, sinon manquant ; items manquants : somme proportionnelle (moyenne des items répondus multipliée par 8) ; étendue 8 – 40 (source : Manuel fictif de l'échelle de sommeil, p. 4 (référence inventée pour l'exemple)).

**G2** (échelle, 7 variables) : `anx1`, `anx2`, `anx3`, `anx4`, `anx5`, `anx6`, `anx7`.
Valeurs de tous ses items : 0 Jamais ; 1 Parfois ; 2 Souvent ; 3 Presque toujours.
Cotation : non documentée.

## Variables

| Variable | Libellé | Type | Niveau | Valeurs | Manquants | Groupe | Question | Note |
|---|---|---|---|---|---|---|---|---|
| `id_participant` | Identifiant participant | texte |  |  |  |  | aucune | sensible (identifiant) |
| `courriel` | Courriel | texte |  |  |  |  | Q5 | sensible (identifiant) |
| `date_passation` | Date passation | date et heure |  |  |  |  | aucune |  |
| `date_naissance` | DDN | date |  |  |  |  | Q2 | sensible (quasi-identifiant) |
| `age` | Age | entier | échelle |  | 999 |  | Q3 |  |
| `genre` | Genre | entier | nominal | 1 Femme ; 2 Homme ; 3 Autre identité | 9 |  | Q4 |  |
| `vague` | Vague | entier | nominal | 1 Vague 1 |  |  | aucune |  |
| `sommeil_q1` | Q1 endormissement | entier | ordinal | → G1 |  | G1 | Q7.r1 |  |
| `sommeil_q2` | Q2 sommeil reparateur | entier | ordinal | → G1 |  | G1 | Q7.r2 |  |
| `sommeil_q3` | Q3 reveils nocturnes | entier | ordinal | → G1 | 9 | G1 | Q7.r3 | inv |
| `sommeil_q4` | Q4 satisf sommeil | entier | ordinal | → G1 |  | G1 | Q7.r4 |  |
| `sommeil_q5` | Q5 energie matin | entier | ordinal | → G1 |  | G1 | Q7.r5 |  |
| `sommeil_q6` | Q6 somnolence jour | entier | ordinal | → G1 |  | G1 | Q7.r6 | inv |
| `sommeil_q7` | non documenté | entier | ordinal | → G1 |  | G1 | Q7.r7 |  |
| `sommeil_q8` | Q8 routine | entier | ordinal | → G1 |  | G1 | Q7.r8 |  |
| `anx1` | ANX inquiet | entier | ordinal | → G2 | -9 | G2 | Q12.r1 |  |
| `anx2` | ANX tendu | entier | ordinal | → G2 | -9 | G2 | Q12.r2 |  |
| `anx3` | ANX controle inquietude | entier | ordinal | → G2 | -9 | G2 | Q12.r3 |  |
| `anx4` | ANX agite | entier | ordinal | → G2 | -9 | G2 | Q12.r4 |  |
| `heures_sommeil` | Nb heures sommeil (moy) | décimal | échelle |  |  |  | Q8 |  |
| `heures_sommeil_2` | Nb heures sommeil (moy) | décimal | échelle |  |  |  | Q8 |  |
| `nb_reveils` | Nb reveils / nuit | entier | échelle |  | -9 |  | Q9 |  |
| `aide_medicament` | Aide sommeil: medicament | entier | nominal |  |  |  | Q10.o1 |  |
| `aide_naturel` | Aide sommeil: produit naturel | entier | nominal |  |  |  | Q10.o2 |  |
| `aide_tcc` | Aide sommeil: TCC | entier | nominal |  |  |  | Q10.o3 |  |
| `aide_aucune` | Aide sommeil: aucune | entier | nominal |  |  |  | Q10.o4 |  |
| `anx5` | ANX irritable | entier | ordinal | → G2 | -9 | G2 | Q12.r5 |  |
| `anx6` | ANX peur | entier | ordinal | → G2 | -9 | G2 | Q12.r6 |  |
| `anx7` | ANX difficulte relaxer | entier | ordinal | → G2 | -9 | G2 | Q12.r7 |  |
| `satisfaction_globale` | Satisfaction globale 0-10 | entier | échelle | 0 Pas du tout satisfait ; 10 Tout à fait satisfait ; 99 Ne sait pas |  |  | Q11 |  |
| `taille_cm` | Taille (cm) | mixte |  |  |  |  | Q6 |  |
| `q_retiree` | Question retiree v2 | vide |  |  |  |  | aucune |  |
| `langue_maison` | Langue maison | texte | nominal |  |  |  | Q14 |  |
| `commentaire` | Commentaires | texte |  |  |  |  | Q13 | sensible (texte libre) |

## Points d'attention

- `vague` : variable constante.
- `heures_sommeil_2` : identique à heures_sommeil.
- `satisfaction_globale` : étiquette 99 jamais utilisée.
- `taille_cm` : types mélangés (7 valeurs non numériques).
- `q_retiree` : variable entièrement vide.
- `langue_maison` : variantes d'écriture d'une même réponse.

## Texte des questions

- **Q2** Quelle est votre date de naissance ? (JJ/MM/AAAA)
- **Q3** Quel âge avez-vous ?
- **Q4** Quel est votre genre ?
- **Q5** Votre adresse courriel (pour vous envoyer un rappel) :
- **Q6** Quelle est votre taille, en centimètres ?
- **Q7** Au cours du dernier mois, dans quelle mesure les énoncés suivants s'appliquent-ils à vous ?
  - Q7.r1 (`sommeil_q1`) : J'ai de la difficulté à m'endormir le soir.
  - Q7.r2 (`sommeil_q2`) : Mon sommeil est réparateur.
  - Q7.r3 (`sommeil_q3`) : Je me réveille plusieurs fois pendant la nuit sans pouvoir me rendormir facilement.
  - Q7.r4 (`sommeil_q4`) : Je suis satisfait.e de la qualité de mon sommeil.
  - Q7.r5 (`sommeil_q5`) : J'ai de l'énergie dès le réveil.
  - Q7.r6 (`sommeil_q6`) : Je somnole pendant la journée, même après une bonne nuit.
  - Q7.r7 (`sommeil_q7`) : J'évite les écrans dans l'heure qui précède le coucher.
  - Q7.r8 (`sommeil_q8`) : Je suis une routine régulière avant de me coucher.
- **Q8** En moyenne, combien d'heures dormez-vous par nuit ?
- **Q9** Combien de fois vous réveillez-vous au cours d'une nuit habituelle ?
- **Q10** Qu'utilisez-vous pour vous aider à dormir ? (Cochez toutes les réponses applicables)
  - Q10.o1 (`aide_medicament`) : Un médicament prescrit
  - Q10.o2 (`aide_naturel`) : Un produit naturel (tisane, mélatonine)
  - Q10.o3 (`aide_tcc`) : Une thérapie cognitivo-comportementale (TCC)
  - Q10.o4 (`aide_aucune`) : Rien de cela
- **Q11** Dans l'ensemble, quelle est votre satisfaction à l'égard de votre sommeil ? (0 = Pas du tout satisfait, 10 = Tout à fait satisfait)
- **Q12** Au cours des deux dernières semaines, à quelle fréquence avez-vous ressenti ce qui suit ?
  - Q12.r1 (`anx1`) : Je me suis senti.e inquiet.e.
  - Q12.r2 (`anx2`) : Je me suis senti.e tendu.e.
  - Q12.r3 (`anx3`) : J'ai eu du mal à contrôler mes inquiétudes.
  - Q12.r4 (`anx4`) : Je me suis senti.e agité.e.
  - Q12.r5 (`anx5`) : Je me suis senti.e irritable.
  - Q12.r6 (`anx6`) : J'ai eu peur que quelque chose de terrible arrive.
  - Q12.r7 (`anx7`) : J'ai eu de la difficulté à me détendre.
- **Q13** Avez-vous d'autres commentaires sur votre sommeil ?
- **Q14** Quelle langue parlez-vous le plus souvent à la maison ?
