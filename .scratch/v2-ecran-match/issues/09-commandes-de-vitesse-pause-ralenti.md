# EM-09 — Commandes de vitesse, pause, ralenti (E/V) — 90 min (élevée)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : boutons élégants, état actif évident, cohérents avec le HUD ; comportement strictement inchangé.
- **Résultat** : groupe segmenté, bouton pause de 44 px, barre d'espace, badge RALENTI ; `SPEED_OPTIONS` et la boucle intacts.
- **Composants** : `SpeedControls`. **Critères** : chaque vitesse produit exactement la même durée de lecture qu'avant
  (chronométrage d'une minute de match par vitesse, écart < 2 %) ; pause/reprise inchangées ; cibles ≥ 40 px.
- **Tests** : mesure de lecture par vitesse ; test clavier ; captures.
- **Dépendances** : EM-08. **Risques** : raccourci clavier en conflit avec le navigateur.

## Comments
