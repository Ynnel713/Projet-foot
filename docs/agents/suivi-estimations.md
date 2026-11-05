# Suivi des estimations de durée

Règle : `CLAUDE.md`, section « Estimer la durée d'un ticket » (05/11/2026). Ce registre transforme les estimations en données : après 20 à 30 tickets clôturés, le ticket `v2-realisme/01g` en tire, par catégorie, le rapport réel / estimé et les postes systématiquement sous-estimés.

## Format d'une ligne

- Durées en minutes de **travail effectif** ; le temps machine (suite complète, séries de matchs) n'y entre pas.
- **Catégorie** : celle du ticket (mesure, placement, décision, exécution, physique, perception, validation, données, documentation) ; « autre » pour un ticket hors chantier `v2-realisme`.
- **Postes** : analyse / développement / tests / intégration, estimé puis réel (`20/45/30/20`).
- **Cause de l'écart** : obligatoire si l'écart dépasse 30 % (périmètre élargi, code mal connu, test difficile, régression, mesure à refaire, revue de l'expert…).

| Date de clôture | Ticket | Catégorie | Estimé (min) | Réel (min) | Écart | Postes estimés | Postes réels | Confiance annoncée | Cause de l'écart |
|---|---|---|---|---|---|---|---|---|---|
