# EM-10 — Compositions en cartes (V) — 165 min (moyenne) → découpé en 10a et 10b

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **10a** (90 min) : `LineupColumn`, `PlayerCard`, titulaires/remplaçants, symétrie, écrans ≥ 1280 px.
- **10b** (75 min) : compacts 960 à 1279 px et tiroirs < 960 px.
- **Problème** : listes de 11 px, invisibles sous 1024 px. **Résultat** : cartes de 2.2, sans note ni statistique.
- **Critères** : 11 titulaires et jusqu'à 9 remplaçants visibles sans défilement à 1366×768 ; gauche et droite symétriques ;
  noms longs tronqués proprement ; accessible sur 844×390 en un geste.
- **Tests** : captures aux 4 tailles ; contrôle des noms les plus longs de la base.
- **Dépendances** : EM-03, EM-04. **Risques** : entraîneur (conservé, discret) ; numéros des entrants (ticket coach/05).

## Comments
