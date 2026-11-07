# EM-D2 — Tirs, fautes et corners dans le flux (D) — 90 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : envoyer à l'écran ce que la trace enregistre déjà.
- **Résultat** : listes `shots`, `fouls`, `restarts` (corners) dans `MatchProgressOut`, comme `goals` aujourd'hui (remplies
  pendant le calcul) ; moteur inchangé.
- **Critères** : réponse allégée (taille mesurée) ; tous les événements portent leur minute (filtrage sur le temps lu).
- **Tests** : `pytest` ; mesure de la charge utile (cible : < 2× la taille actuelle).
- **Dépendances** : aucune. **Risques** : poids de la réponse chaque seconde (n'envoyer que les nouveaux événements).

## Comments
