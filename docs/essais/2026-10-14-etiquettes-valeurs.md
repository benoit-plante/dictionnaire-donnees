# Essai : étiquettes de valeurs tirées des options de réponse (v0.2, étape 6)

**Date :** 2026-10-14
**Règle (D-016) :** une proposition seulement si
- le fichier ne donne pas d'étiquettes ;
- une personne a accepté le rattachement à une question qui a des options (ou à un énoncé de grille, dont les options sont les colonnes) ;
- les codes observés, hors manquants déclarés, sont 1…n ou 0…n−1 ;
- il y a autant d'options que de codes.

Les options sont données aux codes dans leur ordre, avec la mention « ordre supposé, à vérifier ». Aucun modèle n'intervient.

## Base fictive

**CSV, avec le questionnaire texte et les rattachements du corrigé acceptés :** des étiquettes sont proposées pour `sommeil_q1`, `q2` et `q4` à `q8`. Elles sont **identiques aux étiquettes du `.sav`** : 1 = Pas du tout … 5 = Extrêmement.

Rien n'est proposé ailleurs, et c'est voulu (un test par cas) :

| Variable | Pourquoi |
|---|---|
| `sommeil_q3` | codes 1 à 5 et 9 (code non étiqueté) : pas consécutifs |
| `genre` | codes 1, 2, 3 et 9 |
| `anx1` à `anx7` | codes −9 et 0 à 3 : dans un CSV, −9 n'est pas déclaré manquant |
| `satisfaction_globale` | 12 options (0 à 10 et « Ne sait pas »), 11 codes |
| `aide_*` | rattachées à une option : la variable est une case cochée ou non |
| questions ouvertes, variables sans question | pas d'options |

Avec le **questionnaire PDF**, rien n'est proposé pour la grille du sommeil : deux titres de colonnes y sont collés (« MoyennementBeaucoup »), la question est marquée « à vérifier », et le nombre de colonnes n'est pas sûr. Avec le **`.sav`**, rien non plus : le fichier a déjà ses étiquettes.

## Base publique

Sont acceptés les 98 rattachements où le modèle et le calcul s'accordent (comme à l'étape 5). **18 propositions.** L'ordre supposé a été vérifié avec les données, par des décomptes seulement, quand une autre variable le permettait :

- **Juste : `service_dpj`, `service_ciusss`, `service_prive` (1 = Oui, 2 = Non).** Les personnes qui ont coché un type de service ont presque toutes le code 1 (DPJ : 13 sur 14 ; CIUSSS : 353 sur 353 ; privé : 169 sur 171). Sans le questionnaire, le modèle avait inventé l'inverse (« 1 = non, 2 = oui », essai de la v0.1.2).
- **Faux : `langue_maternelle`.** Codes 0, 1 et 2, options « Français », « Anglais », « Autre (précisez) ». La règle propose 0 = Français, mais la précision « autre langue » n'est remplie que pour le code 0 : la base a été recodée, et 0 veut dire « Autre ». C'est exactement le cas que la mention « ordre supposé, à vérifier » doit faire voir.
- Les autres, les échelles « Pas du tout … Très souvent » et « Vraiment insatisfait·e … Vraiment satisfait·e », sont plausibles, mais n'ont pas pu être vérifiées.

Les variables recodées par l'équipe (`type_famille_final`, `education_final`, `revenu_familial`…) contiennent du texte et ne reçoivent aucune proposition. Les cases à cocher (code 1 seul) n'en reçoivent pas non plus.

## Conclusion

La règle stricte ne propose rien de faux sur la base fictive. Sur la base publique, elle donne le bon sens des codes là où le modèle l'inventait, mais une proposition sur 18 vérifiables est fausse, à cause d'un recodage. Le guide (étape 10) devra le dire : une proposition ne s'accepte qu'après avoir vérifié l'ordre des codes dans la plateforme d'enquête ou le script de recodage.
