# Rapport d'audit du moteur narratif

Brief "narrative engine foundations" (23/09/2026), Tâche 6 -- `scripts/narrative_audit.py`, seed numpy fixe `20260923` (déterministe, voir docstring du script).

**1000 timelines construites avec succès sur 1172 matchs simulés tentés.**

## Matchs exclus (dette du moteur de résultats, voir docs/narrative_timeline_schema.md)

- Collisions de minute entre deux buts réels (`MinuteCollisionError`) : 40 (3.41%)
- Règles anti-répétition structurellement insatisfiables (`AntiRepetitionUnsatisfiableError`) : 46 (3.92%)

## Distribution du nombre d'occasions par match

- Moyenne : 15.28
- Écart-type : 3.07
- Min : 10
- Max : 22

## Distribution des gabarits utilisés

- `contre_attaque` : 2313 (15.14%)
- `debordement_centre_tete` : 2217 (14.51%)
- `percee_individuelle` : 1981 (12.96%)
- `construction_placee` : 1656 (10.84%)
- `recuperation_haute` : 1617 (10.58%)
- `decalage_enroulee` : 1615 (10.57%)
- `profondeur_1v1` : 1123 (7.35%)
- `une_deux` : 938 (6.14%)
- `corner` : 860 (5.63%)
- `coup_franc` : 390 (2.55%)
- `but_gag` : 326 (2.13%)
- `penalty` : 244 (1.60%)

## Distribution des issues

- `arret` : 5041 (32.99%)
- `hors_cadre` : 3122 (20.43%)
- `but` : 2687 (17.59%)
- `tacle` : 1904 (12.46%)
- `degagement` : 1268 (8.30%)
- `poteau` : 1258 (8.23%)

## Distribution temporelle (par tranche de 15 minutes)

- 1-15min : 2607
- 16-30min : 2489
- 31-45min : 2530
- 46-60min : 2571
- 61-75min : 2495
- 76-90min : 2588

## Vérification des propriétés anti-répétition (taux de violation, attendu 0)

- Répétition immédiate (gabarit, déclinaison) : 0/1000 (0.00%)
- Répétition immédiate du joueur principal : 0/1000 (0.00%)
- Écart minimum entre occasions non respecté : 0/1000 (0.00%)
- Pattern cyclique (periode <=5) sur les gabarits : 0/1000 (0.00%)

## Vérification de l'invariant score (taux de violation, attendu 0)

- Score/buts incohérents avec les données d'entrée : 0/1000 (0.00%)
- Tri chronologique non strict : 0/1000 (0.00%)
