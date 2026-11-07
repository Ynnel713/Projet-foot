# EM-05 — Terrain : pelouse, marquages, suppression du cadre rouge (V) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : terrain qualitatif intégré à l'interface, sans bordure rouge.
- **Problème** : piste rouge épaisse, vert saturé, marges et zone de bancs qui rétrécissent le jeu.
- **Résultat** : nouvelles teintes et lignes de 2.2, marge réduite à 3 m, sol sombre, vignette, dégradé de profondeur
  unique ; coordonnées inchangées (`viewBox` recadré, `project` intact).
- **Périmètre** : dessin du terrain seulement (le dessin des bancs est le ticket EM-06).
- **Composants** : `PitchView2` (ex-V2Pitch), `index.css`.
- **Critères** : joueurs et ballon tombent exactement sur les mêmes points qu'avant (test de projection de 5 points :
  coins, centre, points de penalty) ; plus aucune zone rouge ; lignes visibles à 844×390 (≥ 1 px).
- **Tests** : test unitaire de `project` (inchangé) ; captures avant/après aux 4 tailles.
- **Dépendances** : EM-04. **Risques** : confusion lignes/gazon sur petit écran (épaisseur minimale).

## Comments
