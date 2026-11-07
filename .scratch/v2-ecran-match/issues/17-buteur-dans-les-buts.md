# EM-D1 — Buteur dans les buts (D) — 75 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : nom du buteur sur chaque but de la trace.
- **Problème** : `GoalEvent` = minute + équipe ; le buteur n'est pas envoyé.
- **Résultat** : `GoalEventOut.player` rempli côté API en appariant le but au dernier tir de l'équipe d'issue « but » (ou
  penalty) avant la minute du but ; moteur **inchangé**. Si l'appariement ne peut être garanti, ticket moteur séparé.
- **Critères** : sur 50 matchs, 100 % des buts ont un buteur de la bonne équipe ; aucun doublon ; si la règle échoue, le
  ticket s'arrête et ouvre le ticket moteur.
- **Tests** : `pytest` sur traces simulées ; vérification sur 50 matchs (temps machine).
- **Recoupement** : le ticket `v2-mise-en-scene/01` (point 1, « trace enrichie ») prévoit déjà le buteur **et le passeur** dans la trace. À faire une seule fois : si `v2-mise-en-scene/01` passe en premier, ce ticket disparaît ; sinon il en livre la moitié « buteur », et `v2-mise-en-scene/01` ajoute le passeur.
- **Dépendances** : aucune. **Risques** : but contre son camp (aucun mécanisme dans la V2 à ce jour : à confirmer).

## Comments
