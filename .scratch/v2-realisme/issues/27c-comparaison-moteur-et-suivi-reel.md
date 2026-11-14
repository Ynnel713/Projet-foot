# 27c: Comparer le moteur aux trajectoires réelles

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « validation sur données réelles de trajectoires » : sans elle, le moteur peut être cohérent mais faux). **Priorité :** P1. **Catégorie :** validation.

**Constat vérifié (14/11/2026) :** voir 27a ; la calibration tactique (`v2-collectif/22b`) n'a aujourd'hui que des repères agrégés.

**What to build:** une option du banc (`scripts/measure_v2.py`) qui calcule les mêmes distributions que 27b sur 50 matchs simulés et les compare au réel (écart de médiane, recouvrement des quartiles, distance entre distributions). Rapport : liste des indicateurs hors de la plage réelle, avec le mécanisme du moteur le plus probablement en cause. Aucun réglage dans ce ticket : les écarts deviennent des entrées de la calibration tactique (22b) ou des tickets.

**Attributs :** aucun.

**Blocked by:** 27b ; 25h (indicateurs du jeu sans ballon).

**Bloque :** `v2-collectif/22b`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : 27b livré avec les fonctions partagées.
Temps machine, non compté : 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Rapport publié : chaque indicateur avec moteur, réel et écart
- [ ] Aucun réglage du moteur dans ce ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
