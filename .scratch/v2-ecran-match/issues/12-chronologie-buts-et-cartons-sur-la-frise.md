# EM-12 — Chronologie : buts et cartons sur la frise (V) — 90 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : buts (minute, équipe) et cartons rouges (emplacement) sur l'axe du momentum.
- **Résultat** : `EventMarker` ; info-bulle (« 23' · équipe », + buteur après EM-D1) ; plus d'emoji.
- **Critères** : marqueur n'apparaît qu'à sa minute de lecture ; nombre de marqueurs = buts révélés ; cartons : composant
  prêt, testé sur propriété simulée **dans les tests seulement**, rien d'affiché tant que 09a n'existe pas.
- **Tests** : trace enregistrée ; test du composant carton avec propriétés de test.
- **Dépendances** : EM-11. **Risques** : buts rapprochés (chevauchement) → décalage vertical.

## Comments
