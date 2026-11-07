# EM-04 — Mise en page en trois zones et responsive (E) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : HUD / centre / zone basse ; terrain dominant ; adaptation 844×390 à 1920×1080.
- **Problème** : terrain petit, compositions masquées sous 1024 px, en-tête global qui mange 56 px.
- **Résultat** : grille CSS à trois zones, en-tête global masqué sur `/v2`, colonnes de compositions à 200 à 230 px, repli
  tiroirs sous 960 px ; coquilles vides stylées pour les zones (contenu inchangé à ce stade).
- **Périmètre** : structure uniquement. **Composants** : `V2Match.jsx`, `AppShell.jsx`, `index.css`.
- **Critères** : captures aux 4 tailles (844×390, 1024×768, 1366×768, 1920×1080) ; surface du terrain ≥ +30 % à 1280×720
  (mesurée) ; aucun défilement de page ; autres routes gardent leur en-tête.
- **Tests** : captures avant/après ; contrôle manuel des autres routes ; build, lint.
- **Dépendances** : EM-01. **Risques** : `AppShell` partagé.

## Comments
