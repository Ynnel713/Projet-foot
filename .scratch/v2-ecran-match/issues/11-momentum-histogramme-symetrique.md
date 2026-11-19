# EM-11 — Momentum : histogramme symétrique (V) — 150 min (moyenne) → 11a rendu, 11b données

**Status:** livré (19/11/2026) : 11a et 11b validés expert + QC

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

### 19/11/2026 — 11a livré

- 11a livré (19/11/2026), validé expert + QC : voir `11a-frise-de-momentum-rendu.md`. Frise de 72 px (et non 150 px :
  décision EM-04), pleine largeur, domaine fixe de 105 minutes ; constantes de 11b validées le même jour (échelle fixe
  0,6, seuil de 1 px, minutes terminées seulement, libellé « Pression territoriale »). Reporté en 11b : réserve A1 de
  11a (barre de la minute en cours au-delà du curseur, critère du banc sur la fin de barre).


### 19/11/2026 — 11b livré, EM-11 terminé

- 11b livré (19/11/2026), validé expert + QC : voir `11b-frise-de-momentum-donnees.md`. `utils/momentum.js` extrait,
  échelle fixe 0,6, minutes terminées seulement (réserve A1 de 11a corrigée), dernière minute bornée à la fin du match,
  libellé « Pression territoriale » (info-bulle et `aria-label`).
