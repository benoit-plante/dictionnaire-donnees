# Contexte d'analyse : travail-t2_surveymonkey.sav

- Base : `travail-t2_surveymonkey.sav` (SPSS), 110 lignes, 55 variables. Empreinte du fichier : `777728a6c138`.
- Codebook : empreinte `a8d2266ad3df`, dictionnaire-donnees 0.9.0. Seules les décisions acceptées par l'équipe y figurent.
- Une ligne représente : un participant
- Structure : longitudinale, une vague par fichier ; vague t2
- Variables de plan : identifiant de regroupement : id_participant_t2
- Description de la base : Enquête fictive sur le travail, deuxième vague.
- Noms : les noms ci-dessous sont les nouveaux noms (nom d'origine entre parenthèses). Travailler sur la copie documentée `travail-t2_surveymonkey-documente.sav`, ou sur la base après le fichier de commandes, qui renomme en premier.

## Règles

1. Les codes de la colonne « Manquants » sont des valeurs manquantes : les exclure de tout calcul.
2. Inverser les items marqués « inv » avant tout score, selon la cotation de leur groupe.
3. Les variables marquées « sensible » ne doivent apparaître dans aucune sortie (ni valeurs, ni listes).
4. « Non documenté » veut dire inconnu : ne pas le deviner. Ne citer aucun seuil, étendue ou instrument absent de ce document.
5. Question à cocher (groupe « réponses multiples ») : une case vide est une option non cochée, sauf si toutes les cases de la question sont vides (question sans réponse).

## Complétude

Question rattachée 55 / 55 · Libellé 55 / 55 · Étiquettes de valeurs (variables codées) 39 / 40 · Niveau de mesure 44 / 44 · Nouveau nom 55 / 55 · Cotation (groupes d'échelle) 0 / 2 · Description de la base dite.
Non documenté : Étiquettes de valeurs (variables codées) : collector_id_t2 ; Cotation (groupes d'échelle) : G1, G2.

## Groupes

**G1** (échelle, 12 variables) : `eft_1_t2`, `eft_2_t2`, `eft_3_t2`, `eft_4_t2`, `eft_5_t2`, `eft_6_t2`, `eft_7_t2`, `eft_8_t2`, `eft_9_t2`, `eft_11_t2`, `eft_12_t2`, `eft_13_t2`.
Valeurs de tous ses items : 1 Jamais ; 2 Rarement ; 3 Parfois ; 4 Souvent ; 5 Toujours.
Cotation : non documentée.

**G2** (échelle, 5 variables) : `milieu_1_t2`, `milieu_2_t2`, `milieu_3_t2`, `milieu_4_t2`, `milieu_5_t2`.
Valeurs de tous ses items : 1 Très insatisfait·e ; 2 Plutôt insatisfait·e ; 3 Ni l'un ni l'autre ; 4 Plutôt satisfait·e ; 5 Très satisfait·e.
Cotation : non documentée.

**G3** (réponses multiples, 6 variables) : `taches_1_t2`, `taches_2_t2`, `taches_3_t2`, `taches_4_t2`, `taches_5_t2`, `taches_6_t2`.
Question : Quelles tâches faites-vous dans une semaine habituelle ? (Cochez toutes les réponses qui s'appliquent) Chaque option : 1 = cochée, vide = non cochée ; le libellé de la ligne est l'option.
Texte « autre » : `taches_autre_txt_t2`.

**G4** (réponses multiples, 7 variables) : `consignes_securite_1_t2`, `consignes_securite_2_t2`, `consignes_securite_3_t2`, `consignes_securite_4_t2`, `consignes_securite_5_t2`, `consignes_securite_6_t2`, `consignes_securite_7_t2`.
Question : Cochez les consignes de sécurité que vous avez reçues à votre arrivée. Chaque option : 1 = cochée, vide = non cochée ; le libellé de la ligne est l'option.
Texte « autre » : `consignes_securite_autre_txt_t2`.

**G5** (réponses multiples, 5 variables) : `transport_1_t2`, `transport_2_t2`, `transport_3_t2`, `transport_4_t2`, `transport_5_t2`.
Question : Coche les moyens de transport que tu utilises pour te rendre au travail. Chaque option : 1 = cochée, vide = non cochée ; le libellé de la ligne est l'option.
Texte « autre » : `transport_autre_txt_t2`.

## Variables

| Variable | Libellé | Type | Niveau | Valeurs | Manquants | Groupe | Question | Note |
|---|---|---|---|---|---|---|---|---|
| `nom_collecteur_t2` (CollectorNm) | CollectorNm | texte | nominal |  |  |  | aucune |  |
| `respondent_id_t2` (respondent_id) | respondent_id | entier |  |  |  |  | aucune | sensible (identifiant) |
| `collector_id_t2` (collector_id) | collector_id | entier | nominal |  |  |  | aucune |  |
| `date_debut_t2` (date_created) | date_created | date et heure |  |  |  |  | aucune |  |
| `date_fin_t2` (date_modified) | date_modified | date et heure |  |  |  |  | aucune |  |
| `adresse_ip_t2` (ip_address) | ip_address | texte |  |  |  |  | aucune | sensible (identifiant) |
| `courriel_t2` (email_address) | email_address | texte |  |  |  |  | aucune | sensible (identifiant) |
| `prenom_t2` (first_name) | first_name | texte |  |  |  |  | aucune | sensible (identifiant) |
| `nom_famille_t2` (last_name) | last_name | texte |  |  |  |  | aucune | sensible (identifiant) |
| `donnees_personnalisees_1_t2` (custom_1) | custom_1 | vide |  |  |  |  | aucune |  |
| `secteur_t2` (q0001) | Dans quel secteur travaillez-vous ? | entier | nominal | 1 Santé et services sociaux ; 2 Éducation ; 3 Commerce ; 4 Industrie ; 5 Administration |  |  | Q1 |  |
| `anciennete_t2` (q0002) | Depuis combien de temps occupez-vous votre emploi actuel ? | entier | nominal | 1 Moins d'un an ; 2 De 1 à 5 ans ; 3 De 6 à 10 ans ; 4 Plus de 10 ans |  |  | Q2 |  |
| `eft_1_t2` (q0003_0001) | J'ai eu trop de tâches à accomplir en peu de temps. | entier | ordinal | → G1 |  | G1 | Q3.r1 |  |
| `eft_2_t2` (q0003_0002) | J'ai pu prendre mes pauses comme prévu. | entier | ordinal | → G1 |  | G1 | Q3.r2 |  |
| `eft_3_t2` (q0003_0003) | Je me suis senti·e soutenu·e par mes collègues. | entier | ordinal | → G1 |  | G1 | Q3.r3 |  |
| `eft_4_t2` (q0003_0004) | J'ai eu de la difficulté à décrocher après le travail. | entier | ordinal | → G1 |  | G1 | Q3.r4 |  |
| `eft_5_t2` (q0003_0005) | J'ai pu identifier les sources de tension dans mon équipe. | entier | ordinal | → G1 |  | G1 | Q3.r5 |  |
| `eft_6_t2` (q0003_0006) | J'ai reçu des consignes contradictoires. | entier | ordinal | → G1 |  | G1 | Q3.r6 |  |
| `eft_7_t2` (q0003_0007) | Je me suis senti·e reconnu·e pour mon travail. | entier | ordinal | → G1 |  | G1 | Q3.r7 |  |
| `eft_8_t2` (q0003_0008) | J'ai manqué d'information pour bien faire mon travail. | entier | ordinal | → G1 |  | G1 | Q3.r8 |  |
| `eft_9_t2` (q0003_0009) | J'ai eu le sentiment de bien faire mon travail. | entier | ordinal | → G1 |  | G1 | Q3.r9 |  |
| `eft_11_t2` (q0003_0010) | J'ai été interrompu·e souvent dans mes tâches. | entier | ordinal | → G1 |  | G1 | Q3.r10 |  |
| `eft_12_t2` (q0003_0011) | J'ai eu assez d'autonomie dans l'organisation de mon travail. | entier | ordinal | → G1 |  | G1 | Q3.r11 |  |
| `eft_13_t2` (q0003_0012) | J'ai pensé à quitter mon emploi. | entier | ordinal | → G1 |  | G1 | Q3.r12 |  |
| `milieu_1_t2` (q0004_0001) | Êtes-vous satisfait·e de l'éclairage ? | entier | nominal | → G2 | 6, 7 | G2 | Q4.r1 |  |
| `milieu_2_t2` (q0004_0002) | Êtes-vous satisfait·e du niveau de bruit ? | entier | nominal | → G2 | 6, 7 | G2 | Q4.r2 |  |
| `milieu_3_t2` (q0004_0003) | Êtes-vous satisfait·e de la température ? | entier | nominal | → G2 | 6, 7 | G2 | Q4.r3 |  |
| `milieu_4_t2` (q0004_0004) | Êtes-vous satisfait·e de l'équipement fourni ? | entier | nominal | → G2 | 6, 7 | G2 | Q4.r4 |  |
| `milieu_5_t2` (q0004_0005) | Êtes-vous satisfait·e de l'espace de rangement ? | entier | nominal | → G2 | 6, 7 | G2 | Q4.r5 |  |
| `taches_1_t2` (q0005_0001) | Accueil de la clientèle | entier | nominal | 1 Accueil de la clientèle |  | G3 | Q5.o1 |  |
| `taches_2_t2` (q0005_0002) | Travail à l'ordinateur | entier | nominal | 1 Travail à l'ordinateur |  | G3 | Q5.o2 |  |
| `taches_3_t2` (q0005_0003) | Manutention | entier | nominal | 1 Manutention |  | G3 | Q5.o3 |  |
| `taches_4_t2` (q0005_0004) | Entretien ménager | entier | nominal | 1 Entretien ménager |  | G3 | Q5.o4 |  |
| `taches_5_t2` (q0005_0005) | Supervision d'une équipe | entier | nominal | 1 Supervision d'une équipe |  | G3 | Q5.o5 |  |
| `taches_6_t2` (q0005_0006) | Autre (veuillez préciser) | entier | nominal | 1 Autre (veuillez préciser) |  | G3 | Q5.o6 |  |
| `taches_autre_txt_t2` (q0005_other) | Other (please specify) | texte | nominal |  |  | G3 | Q5.o6 |  |
| `formation_sst_t2` (q0006) | Avez-vous reçu une formation en santé et sécurité au travail au cours de la dernière année ? | entier | nominal | 1 Oui ; 2 Non |  |  | Q6 |  |
| `pauses_t2` (q0007) | Combien de pauses prenez-vous dans une journée de travail habituelle ? | entier | nominal | 1 Aucune ; 2 Une ; 3 Deux ; 4 Trois ou plus |  |  | Q7 |  |
| `consignes_securite_1_t2` (q0008_0001) | Plan d'évacuation | entier | nominal | 1 Plan d'évacuation |  | G4 | Q8.o1 |  |
| `consignes_securite_2_t2` (q0008_0002) | Port de l'équipement de protection | entier | nominal | 1 Port de l'équipement de protection |  | G4 | Q8.o2 |  |
| `consignes_securite_3_t2` (q0008_0003) | Utilisation des produits dangereux | entier | nominal | 1 Utilisation des produits dangereux |  | G4 | Q8.o3 |  |
| `consignes_securite_4_t2` (q0008_0004) | Premiers soins | entier | nominal | 1 Premiers soins |  | G4 | Q8.o4 |  |
| `consignes_securite_5_t2` (q0008_0005) | Signalement des accidents | entier | nominal | 1 Signalement des accidents |  | G4 | Q8.o5 |  |
| `consignes_securite_6_t2` (q0008_0006) | Ergonomie du poste de travail | entier | nominal | 1 Ergonomie du poste de travail |  | G4 | Q8.o6 |  |
| `consignes_securite_7_t2` (q0008_0007) | Autre (veuillez préciser) | entier | nominal | 1 Autre (veuillez préciser) |  | G4 | Q8.o7 |  |
| `consignes_securite_autre_txt_t2` (q0008_other) | Other (please specify) | texte | nominal |  |  | G4 | Q8.o7 |  |
| `situation_danger_t2` (q0009) | Décrivez une situation récente où vous vous êtes senti·e en danger au travail. | texte |  |  |  |  | Q9 | sensible (texte libre) |
| `transport_1_t2` (q0010_0001) | Voiture | entier | nominal | 1 Voiture |  | G5 | Q10.o1 |  |
| `transport_2_t2` (q0010_0002) | Transport en commun | entier | nominal | 1 Transport en commun |  | G5 | Q10.o2 |  |
| `transport_3_t2` (q0010_0003) | Vélo | entier | nominal | 1 Vélo |  | G5 | Q10.o3 |  |
| `transport_4_t2` (q0010_0004) | Marche | entier | nominal | 1 Marche |  | G5 | Q10.o4 |  |
| `transport_5_t2` (q0010_0005) | Autre (veuillez préciser) | entier | nominal | 1 Autre (veuillez préciser) |  | G5 | Q10.o5 |  |
| `transport_autre_txt_t2` (q0010_other) | Other (please specify) | texte | nominal |  |  | G5 | Q10.o5 |  |
| `commentaires_t2` (q0011) | Avez-vous d'autres commentaires ? | texte |  |  |  |  | Q11 | sensible (texte libre) |
| `id_participant_t2` (q0012) | id | texte |  |  |  |  | aucune | sensible (identifiant) |

## Points d'attention

- `nom_collecteur_t2`, `collector_id_t2` : variable constante.
- `donnees_personnalisees_1_t2` : variable entièrement vide.
- `milieu_3_t2`, `milieu_5_t2` : étiquette 1 jamais utilisée.

## Texte des questions

- **Q1** Dans quel secteur travaillez-vous ?
- **Q2** Depuis combien de temps occupez-vous votre emploi actuel ?
- **Q3** Au cours du dernier mois, à quelle fréquence avez-vous vécu les situations suivantes au travail ?
- **Q4** Dans quelle mesure êtes-vous satisfait·e des aspects suivants de votre milieu de travail ?
- **Q5** Quelles tâches faites-vous dans une semaine habituelle ? (Cochez toutes les réponses qui s'appliquent)
- **Q6** Avez-vous reçu une formation en santé et sécurité au travail au cours de la dernière année ?
- **Q7** Combien de pauses prenez-vous dans une journée de travail habituelle ?
- **Q8** Cochez les consignes de sécurité que vous avez reçues à votre arrivée.
- **Q9** Décrivez une situation récente où vous vous êtes senti·e en danger au travail.
- **Q10** Coche les moyens de transport que tu utilises pour te rendre au travail.
- **Q11** Avez-vous d'autres commentaires ?
