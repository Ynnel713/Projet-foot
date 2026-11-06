# 01h: Test V1 du biais du gardien instable (match tiré sans graine)

**Chantier :** `v2-realisme` (constat fait pendant le ticket 01d, hors audit). **Priorité :** P0 (un test qui échoue au hasard bloque la vérification de fin de tour et le verrou). **Catégorie :** correctif de test.

**Constat vérifié :** `tests/test_ball_events.py::TestKeeperBias::test_a_top_keeper_produces_significantly_more_parades_than_a_weak_one` tire son match avec `simulate_match` V1 (`_simulate_n(1)`), qui consomme `random` et `numpy.random` sans graine posée par le test. Le 06/11/2026, la vérification de fin de tour (`verify.sh`) l'a vu échouer (gardien 90 : 0,377 contre 0,435 ± 0,05), alors que la même commande l'avait vu passer deux fois et que 20 matchs à graines fixes (0 à 19) le font tous passer : un match rare suffit à le faire échouer.

**What to build:** Semer `random` et `numpy.random` (graine d'audit 20260923) avant le tirage du match dans ce test. Aucune assertion ni tolérance modifiée.

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** rien.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 5 min |
| Tests unitaires et comportementaux | 5 min |
| Intégration et vérifications | 5 min |
| **Total (travail effectif)** | **30 min** |

Confiance : élevée. Hypothèses : seul le tirage du match est aléatoire (les événements générés sont déjà semés par `random.Random(seed)`).
Temps machine, non compté : suite complète (environ 15 min).

## Tests

- **Unitaires :** le test passe deux fois de suite sur le même match
- **Intégration :** suite complète

## Acceptance criteria

- [x] Match du test tiré à graine fixe (`random` et `numpy.random`), assertions et tolérances inchangées
- [x] Le test passe à chaque exécution (deux exécutions isolées réussies)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Suite V2 verte ; V1 inchangée (aucun fichier source touché) ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 394 passés, 14 désélectionnés, identique)

## Rapport d'implémentation (06/11/2026)

**Livré :** `tests/test_ball_events.py`, test du biais du gardien : `random.seed(20260923)` et `np.random.seed(20260923)` avant `_simulate_n(1)`. Fichier de test seulement (`engine/ball_events.py`, protégé, non touché).

**Mesure préalable :** 20 matchs tirés à graines 0 à 19 : gardien 90 entre 0,404 et 0,473, gardien 20 entre 0,193 et 0,242, 20 réussites sur 20 ; l'échec observé (0,377) vient d'un match rare.

**Durée :** estimée 30 min, réelle environ 30 min (15/5/5/5). Écart 0 %.

## Comments

- 06/11/2026, passage 1 : expert APPROVED (empreinte 3cb8a363). Facultatif : restaurer l'état global des générateurs après le test (bénéfice non démontré). À surveiller : si le moteur Poisson V1 change sa séquence de tirages, choisir une autre graine plutôt qu'élargir les tolérances. QC VALIDÉ. **Clôture VALIDÉ.**
