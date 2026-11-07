# EM-08 — HUD supérieur : identité du match (V) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : écussons, noms, score central très visible, minute, période, état.
- **Résultat** : `MatchHud`/`ScoreBlock` aux jetons du design system ; écussons `ClubBadge` à 40 à 48 px ; lignes techniques
  (« transition défensive », « calcul… ») retirées de l'écran principal (hors-jeu : repris par la frise).
- **Composants** : `MatchHud`, `ScoreBlock`, `ClubCrest`. **Critères** : score lisible à 2 m (≥ 56 px à 1366×768) ; minute
  avec temps additionnel (45+2') identique à la logique `clock()` ; score jamais en avance sur la lecture (test sur trace).
- **Tests** : sortie de `clock()` comparée avant/après sur 3 traces ; captures des 6 états.
- **Dépendances** : EM-01, EM-03, EM-04. **Risques** : noms de clubs longs (troncature, tailles).

## Comments
