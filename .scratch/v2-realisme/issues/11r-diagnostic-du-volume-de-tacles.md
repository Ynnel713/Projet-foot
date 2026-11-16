# 11r: Diagnostic du volume de tacles (sous le repère réel 30 à 40)

**Chantier :** `v2-realisme` (suite du 11p, décision du propriétaire du 16/11/2026 : « Garder + ticket volume »). **Priorité :** P1. **Catégorie :** diagnostic.

**Constat vérifié (11p, 50 matchs appariés) :** 22,5 tacles par match, sous le repère réel de 30 à 40 (`docs/INDICATEURS_V2.md`, réserve du ticket 22). Avant le 11h : 37,3. Le 11h (facteur de tentative selon l'angle et Decisions hors urgence) explique la baisse ; la règle du tacleur le mieux placé (11p) n'a pas remonté le volume (+ 0,44, non significatif) : l'hypothèse d'un tirage bridé par le plus proche est réfutée.

**What to build:** diagnostic d'abord, sans changer le moteur (leçon du 11j : diagnostic sur le moteur courant avant de coder). Mesurer, sur le moteur courant : temps d'exposition des défenseurs à portée de tacle (par angle, urgence ou non), taux de tentative effectif par seconde d'exposition, part des expositions avec plusieurs défenseurs à portée, durée des confrontations (sortie par `CONFRONTATION_END_M`, interdiction après un tacle raté, déséquilibre du 12c). En déduire où se perd le volume (exposition trop courte, taux trop bas hors urgence, ou expositions trop rares), et proposer au propriétaire une ou plusieurs options chiffrées, avec leurs constantes, avant tout code.

**Attributs :** aucun nouveau a priori (Aggression : fréquence ; Decisions : discernement du 11h).

**Constantes :** aucune ; à proposer au propriétaire à l'issue du diagnostic. Chiffre réel : tacles par match 30 à 40 (repère du ticket 22).

**Lien avec l'existant :** 11h (facteur de tentative), 11p (choix du tacleur), 21c (volume de fautes, retour vers 21-26).

**Blocked by:** 11p (validé).

**Bloque :** rien.

**Status:** à faire (diagnostic ; à placer par le propriétaire)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (instrumentation du banc) | 30 min |
| Tests | 15 min |
| Intégration et vérifications (analyse, options pour le propriétaire) | 30 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : instrumentation par le banc seul (`scripts/measure_v2.py`), comme au 11e.
Temps machine, non compté : série de 50 matchs ; suite complète.

## Acceptance criteria

- [ ] Temps d'exposition, taux de tentative effectif et part des expositions multiples mesurés sur 50 matchs
- [ ] Cause principale du volume bas identifiée et chiffrée
- [ ] Options chiffrées proposées au propriétaire avant tout code moteur
- [ ] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`)
