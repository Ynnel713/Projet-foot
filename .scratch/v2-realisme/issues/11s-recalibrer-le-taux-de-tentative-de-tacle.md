# 11s: Recalibrer le taux de base de tentative de tacle après le 11h

**Chantier :** `v2-realisme` (suite du 11r, décision du propriétaire du 16/11/2026 : option A). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11r, 50 matchs) :** 22,5 tacles par match, sous le repère réel 30 à 40. Au taux de base (0,03/s, `duel._ATTEMPT_BASELINE`, calibré sur 30-40 avant le 11h), 38,6 tacles seraient attendus ; le facteur 11h (moyenne 0,61) en retire 16,1. Exposition (1 234 s par match) et règles de blocage (3 %) ne sont pas en cause.

**What to build:** `_ATTEMPT_BASELINE` 0,03 → 0,047/s et `_ATTEMPT_AMPLITUDE` 0,021 → 0,033 (écart Aggression x2 gardé), commentaire de `duel.py` mis à jour (calibrage après le 11h). Aucun autre changement.

**Attributs :** Aggression seule (fréquence), inchangé (R1).

**Constantes (validées le 16/11/2026) :** base 0,047/s, amplitude 0,033. Chiffre réel : tacles par match 30 à 40 (premierleague.com, repère du ticket 22).

**Lien avec l'existant :** 11h (facteur gardé), 11p, 21c (fautes : environ 10,4 → 16 sur tacle, vers 21-26 au total).

**Blocked by:** 11r.

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 10 min |
| Tests (adapter les tests qui lisent la base) | 20 min |
| Intégration et vérifications (série appariée, rapport) | 40 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : quelques tests figent 0,03 ; la série « avant » est celle du 11r/11p (mêmes graines).
Temps machine, non compté : série de 50 matchs ; suite complète.

## Acceptance criteria

- [ ] Tacles par match dans 30 à 40 sur 50 matchs appariés
- [ ] Part des tacles par derrière hors urgence sans hausse significative (proportions du 11h gardées)
- [ ] Fautes, buts, tirs rapportés (écart apparié) ; profil Aggression 99/11 : écart de fréquence gardé
- [ ] Déterminisme à graine fixée ; suite complète comparée à l'attendu
- [ ] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`)
