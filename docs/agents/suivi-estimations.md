# Suivi des estimations de durée

Règle : `CLAUDE.md`, section « Estimer la durée d'un ticket » (05/11/2026). Ce registre transforme les estimations en données : après 20 à 30 tickets clôturés, le ticket `v2-realisme/01g` en tire, par catégorie, le rapport réel / estimé et les postes systématiquement sous-estimés.

## Format d'une ligne

- Durées en minutes de **travail effectif** ; le temps machine (suite complète, séries de matchs) n'y entre pas.
- **Catégorie** : celle du ticket (mesure, placement, décision, exécution, physique, perception, validation, données, documentation) ; « autre » pour un ticket hors chantier `v2-realisme`.
- **Postes** : analyse / développement / tests / intégration, estimé puis réel (`20/45/30/20`).
- **Cause de l'écart** : obligatoire si l'écart dépasse 30 % (périmètre élargi, code mal connu, test difficile, régression, mesure à refaire, revue de l'expert…).

| Date de clôture | Ticket | Catégorie | Estimé (min) | Réel (min) | Écart | Postes estimés | Postes réels | Confiance annoncée | Cause de l'écart |
|---|---|---|---|---|---|---|---|---|---|
| 05/11/2026 | v2-realisme/01f | mesure | 110 | 70 | − 36 % | 20/50/30/10 | 15/20/20/15 | élevée | Boucle de match déjà écrite dans un test existant ; aide de test seule, développement surestimé ; 20 min de corrections après la revue de l'expert (notes à champ dédié, mode de transition) |
| 05/11/2026 | v2-realisme/01a | mesure | 135 | 140 | + 4 % | 30/45/30/30 | 30/30/30/50 | moyenne | — (sous 30 %) ; intégration plus longue (contrôle A/A et 60 matchs de mesure supplémentaires), développement plus court |
| 06/11/2026 | v2-realisme/01b | mesure | 130 | 130 | 0 % | 20/50/30/30 | 15/35/30/50 | moyenne | — (sous 30 %) ; développement plus court (migration par script), intégration plus longue (2 tests dépendants de la graine, correction après le passage 1, mesure refaite) |
| 06/11/2026 | v2-realisme/01c | documentation | 110 | 100 | − 9 % | 30/60/0/20 | 25/55/0/20 | moyenne | — (sous 30 %) ; sources en partie en accès payant (Bradley 2009), contournées par des sources ouvertes |
| 06/11/2026 | v2-realisme/01d | mesure | 120 | 115 | − 4 % | 20/50/30/20 | 15/35/30/35 | élevée | — (sous 30 %) ; observateurs du banc déjà en place, développement plus court ; correction du jeu effectif après la revue |
| 06/11/2026 | v2-realisme/01h | correctif de test | 30 | 30 | 0 % | 15/5/5/5 | 15/5/5/5 | élevée | — |
| 06/11/2026 | v2-realisme/17a | documentation | 75 | 60 | − 20 % | 30/30/0/15 | 25/20/0/15 | élevée | — (sous 30 %) ; durée réelle estimée, non chronométrée ; scan par arbre syntaxique plus rapide que prévu |
| 06/11/2026 | v2-realisme/01e | mesure | 130 | 115 | − 12 % | 20/60/30/20 | 10/45/25/35 | moyenne | — (sous 30 %) ; analyse plus courte (matchs déjà indépendants), corrections après le passage 1 |
| 06/11/2026 | v2-realisme/02a | placement | 105 | 60 | − 43 % | 25/30/30/20 | 10/10/25/15 | élevée | écart > 30 % : changement de dix lignes, fabrique de scènes (01f) déjà en place ; durée réelle estimée, non chronométrée |
| 06/11/2026 | v2-realisme/02b | placement | 110 | 125 | + 14 % | 20/40/30/20 | 15/40/40/30 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; deux passes de l'expert et correction de l'ordre de la lineup |
| 06/11/2026 | v2-realisme/02c | données | 130 | 115 | − 12 % | 20/60/35/15 | 15/50/35/15 | élevée | — (sous 30 %) ; durée réelle estimée, non chronométrée ; deux passes de l'expert (underscores et repli silencieux), suite complète lancée deux fois |
| 06/11/2026 | v2-realisme/02d | placement | 120 | 95 | − 21 % | 25/45/30/20 | 20/30/25/20 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; mesure par rôle écrite en un script |
| 06/11/2026 | v2-hauteur-ballon/01 | autre | 210 | 120 | − 43 % | 30/120/30/30 | 15/40/15/50 | moyenne | écart > 30 % : écran codé d'un seul jet (matrice SVG pour le sol, une fonction de projection), trois passages de clôture inclus dans l'intégration ; durée réelle estimée, non chronométrée |
| 06/11/2026 | v2-realisme/02e | placement | 110 | 100 | − 9 % | 20/40/30/20 | 25/25/25/25 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; mesure sans ballon ajoutée au script de mesure par rôle |
| 06/11/2026 | v2-realisme/02f | décision | 120 | 90 | − 25 % | 25/45/30/20 | 20/30/25/15 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; règle provisoire écrite en une fonction, option du banc ajoutée |
| 06/11/2026 | v2-realisme/02g | décision | 150 | 165 | + 10 % | 25/50/30/20 (+25 réserves) | 30/90/25/20 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; deux boucles de diagnostic de l'alternance non prévues |
| 07/11/2026 | v2-realisme/02h | validation | 90 | 125 | + 39 % | 15/40/20/15 | 20/45/25/35 | élevée | écart > 30 % : second passage de mesure (indicateur de passages scindé par direction, part des instants au-dessus du plafond) après la première série, deux séries de 50 matchs ; durée réelle estimée, non chronométrée |
| 07/11/2026 | v2-realisme/03a | placement | 110 | 115 | + 5 % | 20/40/30/20 | 20/25/30/40 | élevée | — (sous 30 %) ; durée réelle estimée, non chronométrée ; développement plus court (branches existantes réutilisées), intégration plus longue (deux échecs de suite, diagnostic des 48 m) |
| 07/11/2026 | v2-realisme/03b | placement | 120 | 100 | − 17 % | 20/45/35/20 | 15/35/30/20 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; la géométrie de la bissectrice s'est écrite d'un seul jet, la scène d'arrivée en 3 s a réutilisé `tests/scenes.py` |
| 07/11/2026 | v2-realisme/03c | placement | 105 | 85 | − 19 % | 15/40/30/20 | 10/25/30/20 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; géométrie et scène de test déjà posées par le 03b |
| 07/11/2026 | v2-realisme/03d | décision | 125 | 135 | + 8 % | 20/50/35/20 | 25/55/40/35 | moyenne | — (sous 30 %) ; durée réelle estimée, non chronométrée ; les 215 sorties par match de HEAD (passes de son équipe) ont ajouté une correction et deux séries de mesure |
