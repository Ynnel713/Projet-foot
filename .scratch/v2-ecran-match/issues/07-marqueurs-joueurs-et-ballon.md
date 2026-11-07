# EM-07 — Marqueurs joueurs et ballon (V) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : cercles lisibles, relief subtil, équipes distinctes au premier coup d'œil.
- **Résultat** : `PlayerMarker` (couleur d'équipe, anneau, numéro à contraste garanti, relief 10 %), ballon plus visible.
- **Périmètre** : apparence ; rayon, ombre et sélection inchangés. **Composants** : `PlayerMarker`, `PitchView2`.
- **Critères** : numéro lisible à 1366×768 (capture zoomée) pour les 40 clubs de l'échantillon ; aucune équipe confondue
  avec l'autre sur les paires pathologiques ; fluidité ≥ EM-01.
- **Tests** : planche de rendu de toutes les couleurs du banc d'essai ; mesure d'images par seconde.
- **Dépendances** : EM-03, EM-05. **Risques** : coût de rendu des dégradés (utiliser un seul `<defs>` partagé).

## Comments
