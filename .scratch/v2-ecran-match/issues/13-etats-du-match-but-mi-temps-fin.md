# EM-13 — États du match : but, mi-temps, fin (E/V) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Résultat** : `MatchBanner` pour but (2 s), mi-temps (3 s, durée actuelle), fin (panneau de fin, bouton Stats et Retour) ;
  badge RALENTI ; coup d'envoi.
- **Critères** : durées du bandeau de mi-temps et du ralenti **inchangées** ; le bandeau ne bloque ni la lecture ni la
  pause ; états vérifiés à x1 et x8.
- **Tests** : trace enregistrée à `t=44`, `t=goal-1`, `t=fin` ; captures des 6 états.
- **Dépendances** : EM-08, EM-12. **Risques** : bandeau qui masque l'action au x8 (durée en temps réel).

## Comments
