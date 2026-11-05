# 01e: Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (nécessaire aux calibrations provisoires (500 matchs), à la calibration finale et à la validation indépendante). **Catégorie :** mesure.

**Constat vérifié :** le banc publie des moyennes sans intervalle de confiance ; les comparaisons de 20 matchs sont souvent dans le bruit (écart-type des buts d'environ 0,4 noté dans `docs/INDICATEURS_V2.md`).

**What to build:** Exécuter une série en plusieurs processus (une graine par match, résultats agrégés), afficher pour chaque indicateur moyenne, écart-type et intervalle de confiance à 95 %, et comparer deux séries appariées (même graine, deux versions ou deux profils). Estimer et afficher la durée machine avant le lancement.

**Attributs :** aucun

**Blocked by:** 01b (Flux aléatoires : duels, passes, tirs, placement, arbitrage).

**Bloque :** 06c, 13i, 18b, 18d.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 1 h |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : les matchs sont indépendants (aucun état partagé entre processus) ; machine Windows, `multiprocessing` en mode spawn.
Temps machine, non compté : suite complète (environ 40 min) ; essai de 100 matchs.

## Tests

- **Unitaires (scène contrôlée) :** agrégation sur données connues : moyenne et intervalle exacts
- **Intégration :** même graine, 1 processus contre 4 : résultats identiques

## Acceptance criteria

- [ ] Intervalles de confiance affichés pour chaque indicateur
- [ ] Résultats identiques quel que soit le nombre de processus
- [ ] Durée machine estimée avant lancement
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
