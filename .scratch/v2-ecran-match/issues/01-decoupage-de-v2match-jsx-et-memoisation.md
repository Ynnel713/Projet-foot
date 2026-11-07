# EM-01 — Découpage de `V2Match.jsx` et mémoïsation (S) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : un assembleur léger + composants dédiés ; l'écran de réglage (choix des clubs) séparé de l'écran de lecture.
- **Problème** : 840 lignes, redessin complet à chaque image.
- **Résultat** : aucun changement visible ; composants `React.memo` ; boucle de lecture déplacée telle quelle dans un hook.
- **Périmètre** : déplacement et mémoïsation seulement ; pas de style.
- **Composants** : `V2Match.jsx`, nouveaux fichiers de `components/match/`, `hooks/useMatchPlayback.js`.
- **Critères** : sur trace enregistrée, score, minutes de but, instants de ralenti et mi-temps **identiques** à l'ancien
  code ; médiane de durée d'image ≤ celle d'avant (build de production, x8) ; `npm run build` OK ; `npm run lint` : pas
  d'avertissement nouveau.
- **Tests** : comparaison des sorties (score, buts révélés) sur 3 traces ; mesure d'images par seconde avant/après ;
  capture avant/après identique.
- **Dépendances** : EM-00. **Risques** : boucle de lecture (fermetures sur les refs) → déplacement sans réécriture.

## Comments
