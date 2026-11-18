# EM-06 — Bancs et bord de terrain (V) — 90 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : bancs compacts et cohérents avec le nouveau terrain (décision propriétaire en 4).
- **Problème** : zone de 7 m dessinée en gris, rustique, qui prend de la hauteur.
- **Résultat** : bancs resserrés à la ligne de touche (zone de 4,5 m proposée), sièges aux couleurs d'équipe, échauffement
  conservé (comportement et constantes `WARMING_UP`, `BENCH_GAP` inchangés).
- **Composants** : `Bench` (dans `PitchView2`). **Critères** : numéros lisibles ; échauffement dès la 2e période identique ;
  hauteur du dessin −6 % minimum ; **reporté d'EM-04 (décision du propriétaire du 18/11/2026)** : surface dessinée du
  terrain ≥ +30 % à 1280×720 par rapport à l'état d'avant EM-04 (820×505 px, `.scratch/v2-ecran-match/mesures/em04-avant.json`),
  mesurée par `.scratch/v2-ecran-match/mesures/em04-mesure.cjs` ; **reporté d'EM-05 (remarque A1 de l'expert, 18/11/2026)** :
  depuis la marge de 3 m, les remplaçants à l'échauffement (y jusqu'à W + 4,3 m, `V2Pitch.jsx`) sortent de la pelouse
  (W + 3 m) ; les ramener sur l'herbe ou redéfinir la zone des bancs, et corriger le commentaire « entre la ligne de
  touche et la piste » (plus de piste).
- **Tests** : captures x1 en 1re et 2e période ; build, lint.
- **Dépendances** : EM-05, EM-03. **Risques** : constantes validées le 04/11 (modifier la zone demande leur accord).

## Comments
