# EM-02 — Couleurs de maillot dans l'API (D) — 60 min (élevée)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : fournir à l'écran `primary` et `secondary` de chaque club du match.
- **Problème** : la V2 n'a aucune couleur de club (`/api/v2/lineup` n'en donne pas).
- **Résultat** : `LineupOut` gagne `color` et `secondary` (via `kits.CLUB_KIT`, lecture seule) ; clubs sans kit : gris du kit
  par défaut, repéré par un indicateur `known_kit`.
- **Périmètre** : sérialisation ; ni moteur ni données joueurs.
- **Composants** : `api/routers/v2.py` (`LineupOut`, `numbered_lineup`), `tests/`.
- **Critères** : PSG renvoie ses deux couleurs ; club inconnu renvoie le défaut et `known_kit=false` ; route existante
  inchangée pour les autres champs.
- **Tests** : tests `pytest` de la route (club connu, club sans kit, 404).
- **Dépendances** : aucune. **Risques** : nul pour le moteur ; la suite complète dure environ 40 min (temps machine).

## Comments
