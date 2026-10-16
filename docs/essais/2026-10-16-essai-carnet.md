# Essai : le carnet d'analyses sur une vraie base (v0.11, étape 7)

**Date :** 2026-10-16

**But :** vérifier sur une vraie base que le carnet tient : chaque analyse du catalogue s'y ajoute, le document des résultats se produit, le script R maître s'exécute dans R et redonne les valeurs de l'outil ; puis qu'une décision prise après coup est bien vue. Comme pour la v0.9, seuls des faits de structure et des agrégats sont consignés : aucun résultat, aucun nom de variable, aucun libellé, aucun instrument.

## 1. La base

La même base SurveyMonkey réelle que pour l'essai de la v0.9 (`2026-10-16-essai-analyses.md`), hors du dépôt : 252 variables, 980 lignes. Le travail s'est fait sur une copie temporaire, supprimée à la fin. Le projet est construit sans décision : ce sont les niveaux de mesure du fichier qui s'appliquent.

## 2. Le carnet

Dix analyses ont été ajoutées, une pour chaque analyse du catalogue et chacune de ses méthodes : Tableau 1 ; test t (Welch, Mann-Whitney) ; ANOVA (avec les comparaisons de Tukey, Kruskal-Wallis) ; khi-carré (Pearson, test exact de Fisher) ; corrélation (Pearson et Spearman, trois variables) ; régression linéaire. Pour chacune, ce sont les premières variables que les conditions acceptent.

- Le carnet compte 10 analyses et 16 635 caractères.
- Aucune des valeurs de texte de la base (chaînes d'au moins 6 caractères) ne s'y retrouve : il ne garde que des agrégats.
- Lecture et préparation de la base : 2 secondes.

## 3. Le document des résultats et le script R maître

| Étape | Résultat |
|---|---|
| Document des résultats (Word, graphiques Excel, script R) | écrit en 1,1 seconde |
| Word | 10 intertitres, 11 tableaux, 5 figures ; tableaux numérotés de 1 à 11, sans trou |
| Script R maître, exécuté dans R sur la copie de la base | sans erreur, en 0,9 seconde |
| Valeurs comparées entre l'outil et R | 119, sur les 10 analyses |
| Plus grand écart relatif | 4 × 10⁻⁸ (les *p* de Tukey) ; 5 × 10⁻¹² au plus pour les autres analyses |

## 4. Une décision prise après coup

Aucune variable du carnet n'avait de code manquant suspect. Deux autres décisions ont donc été essayées :

1. **Un libellé corrigé** : les 10 analyses sont « recalculées, sans changement » (un libellé ne change aucun chiffre), et le document se produit.
2. **Un niveau de mesure changé** (la variable dépendante du test t, passée à « nominal ») : 5 analyses deviennent « impossibles à calculer », 5 restent sans changement. Le document se produit avec les 5 analyses calculables, et sa fin nomme celles qui sont écartées, avec leur raison. Aucune analyse n'a été retirée du carnet.

Le scénario du code manquant confirmé après coup (une analyse « changée, à confirmer », qui bloque le document jusqu'à sa confirmation) est vérifié sur la base fictive du sommeil, par les tests et dans le navigateur (scénario manuel, étapes 34 à 38).

## Ce que montre l'essai

1. **Le carnet tient sur une vraie base** : dix analyses, un document de onze tableaux numérotés à la suite, et un script R maître qui redonne les valeurs de l'outil à 10⁻⁷ près, le tout en quelques secondes.
2. **Le carnet ne garde aucune donnée individuelle** : aucune valeur de texte de la base ne s'y retrouve.
3. **Une analyse devenue impossible n'empêche pas le document** : elle en est écartée, la fin du document le dit, et le carnet la garde.
