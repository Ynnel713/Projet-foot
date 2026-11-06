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
| 06/11/2026 | v2-realisme/01e | mesure | 130 | 115 | − 12 % | 20/60/30/20 | 10/45/25/35 | moyenne | — (sous 30 %) ; analyse plus courte (matchs déjà indépendants), corrections après le passage 1 |
