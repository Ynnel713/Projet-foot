# Rapport d'audit du moteur narratif

Brief "constraint priority" (23/09/2026), Tâche 3 -- `scripts/narrative_audit.py`, seed fixe `20260923` (déterministe, voir docstring du script).

**Priorité des contraintes formalisée** (voir `engine/narrative.py`, PRIORITÉ DES CONTRAINTES) : les règles anti-répétition/écart minimum ne gouvernent QUE les occasions inventées (`generated_events`), jamais les buts réels (`existing_events`, hors périmètre). **Conséquence : aucun match n'est plus rejeté** -- `build_timeline` ne lève plus jamais d'exception. Écart avec l'audit précédent : ce rapport traite exactement `n`=1000 matchs (contre ~92-96% de `n` avant, le reste étant alors exclu par collision de minute ou règle anti-répétition structurellement insatisfiable).

**1000 timelines construites sur 1000 matchs simulés -- 0 rejeté.**

## Distribution du nombre d'occasions par match

- Moyenne : 15.25
- Écart-type : 3.05
- Min : 10
- Max : 22

## Distribution des gabarits utilisés

- `contre_attaque` : 2311 (15.15%)
- `debordement_centre_tete` : 2251 (14.76%)
- `percee_individuelle` : 1961 (12.86%)
- `construction_placee` : 1675 (10.98%)
- `decalage_enroulee` : 1592 (10.44%)
- `recuperation_haute` : 1577 (10.34%)
- `profondeur_1v1` : 1136 (7.45%)
- `une_deux` : 958 (6.28%)
- `corner` : 846 (5.55%)
- `coup_franc` : 387 (2.54%)
- `but_gag` : 301 (1.97%)
- `penalty` : 255 (1.67%)

## Distribution des issues

- `arret` : 4959 (32.52%)
- `hors_cadre` : 3074 (20.16%)
- `but` : 2837 (18.60%)
- `tacle` : 1889 (12.39%)
- `poteau` : 1256 (8.24%)
- `degagement` : 1235 (8.10%)

## Distribution temporelle (par tranche de 15 minutes)

- 1-15min : 2562
- 16-30min : 2501
- 31-45min : 2519
- 46-60min : 2557
- 61-75min : 2420
- 76-90min : 2691

## Vérification des propriétés anti-répétition sur `generated_events` uniquement (taux de violation, attendu 0)

- Répétition immédiate (gabarit, déclinaison) : 0/1000 (0.00%)
- Répétition immédiate du joueur principal : 0/1000 (0.00%)
- Écart minimum entre occasions non respecté : 0/1000 (0.00%)
- Pattern cyclique (periode <=5) sur les gabarits : 0/1000 (0.00%)

## Vérification de l'invariant score (taux de violation, attendu 0)

- Score/buts incohérents avec les données d'entrée : 0/1000 (0.00%)
- Tri chronologique non strict : 0/1000 (0.00%)
