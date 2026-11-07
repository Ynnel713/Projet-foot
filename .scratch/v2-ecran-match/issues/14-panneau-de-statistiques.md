# EM-14 — Panneau de statistiques (V/E) — 150 min (moyenne) → 14a calculs, 14b panneau

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **14a** (60 min) : `matchStats.js` : tirs, tirs cadrés, corners, fautes, hors-jeu, possession ; tous filtrés sur le temps lu.
- **14b** (90 min) : `StatsDrawer` + bouton du HUD, lignes symétriques aux couleurs d'équipe ; le match continue.
- **Critères** : valeurs = somme des événements de la trace jusqu'à `seen` (test de cohérence, pas de futur) ; panneau
  ouvert, HUD et terrain visibles ; aucune valeur inventée (cartons : « — » tant que 09a n'existe pas).
- **Tests** : `node --test` ; captures avec panneau ouvert à x1 et x8.
- **Dépendances** : EM-D2, EM-08, EM-03. **À valider avant code** : définitions de « tir cadré » (issues but, capté, repoussé,
  claqué ; hors cadre : à côté, contré) et de la possession (équipe du dernier porteur).
- **Risques** : définitions discutables (c'est un calcul nouveau, donc soumis à votre accord, d'où la contrainte).

## Comments
