# EM-11 — Momentum : histogramme symétrique (V) — 150 min (moyenne) → 11a rendu, 11b données

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **11a** (90 min) : `MomentumTimeline` : barres, axe, repères, curseur, zone future vide, couleurs d'équipe.
- **11b** (60 min) : `momentum.js` extrait, échelle fixe, minute en cours limitée aux images vues (correctif de la réserve A1),
  libellé « Pression territoriale ».
- **Problème** : 1.3. **Résultat** : frise de 150 px pleine largeur, ≈ 10 px par barre.
- **Critères** : aucune barre future ; barres déjà affichées **ne changent jamais de hauteur** quand le match avance ; mêmes
  valeurs que l'ancienne formule à l'échelle près ; pas de calcul par image (recalcul par seconde au plus) ; fluidité ≥ EM-01.
- **Tests** : `node --test` sur `momentum.js` (trace courte synthétique issue d'une vraie trace tronquée) ; mesure.
- **Dépendances** : EM-01, EM-03, EM-04. **Constantes à valider** : échelle fixe, largeur de barre, seuil visuel.
- **Risques** : amplitude trop faible → visuel plat (alors ticket de données EM-D2).

## Comments
