# 04c: Validation : risque annoncé, probabilité calculée, résultat observé

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (garantit que la décision et la résolution restent alignées). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur ne compare la chance de garder le ballon évaluée par le porteur à ce qui arrive ensuite.

**What to build:** Indicateur de calibration : pour chaque conduite, risque évalué au moment du choix et issue sur l'intervalle ; courbe par tranche de pression et par tranche de Dribbling. Rapport sur 50 matchs ; à refaire après 04e, 07 et 11.

**Attributs :** aucun

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution); 04b (Conduite : où va le ballon perdu); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 18a.

**Status:** livré (08/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : lecture de la trace des décisions.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** courbe de calibration exacte sur données synthétiques
- **Statistiques (séries de matchs) :** 50 matchs : écart par tranche inférieur à 3 points

## Acceptance criteria

- [x] Indicateur défini et ajouté au banc
- [x] Écart risque évalué / observé sous 3 points par tranche de pression (50 matchs)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- **Indicateur (08/11/2026).** À chaque tirage de perte de conduite (`measure_v2.dribble_lost`), le banc note le risque évalué (`decision.dribble_loss_probability`, la fonction de l'évaluation) et la perte tirée, par tranche de gêne (6 tranches, `CARRY_PRESSURE_BINS`) et de Dribbling (4 tranches, `CARRY_DRIBBLING_BINS`). Seconde colonne : la perte avec tacle gagné sur ce porteur avant sa décision suivante. Tranches proposées avant le code, acceptées d'office par la consigne du propriétaire du 08/11/2026. Aucun changement de moteur. Réserves A1 et A3 du 04b : non traitées ici (le banc ne voit pas les garde-fous du tacle depuis `lost_carry_outcome`), signalées dans `docs/INDICATEURS_V2.md` section 18.
- **Mesure (50 matchs, graine d'audit 20260923, section 18).** Écart perte tirée / risque évalué : au plus 0,40 point par tranche de gêne (tranche de 8 intervalles par match, dans le bruit), au plus 0,24 par tranche de Dribbling ; avec le tacle gagné, au plus 0,40. 2 241 intervalles et 86,5 pertes par match ; 3,8 tacles gagnés par match tombent dans un intervalle de conduite ouvert. L'accord est attendu (même fonction, 04a) : l'indicateur est un garde-fou, pas une preuve de réalisme.
- **Tests.** 3 tests ajoutés (`tests/test_v2_indicators.py`) : bornes des tranches, courbe exacte sur tirages synthétiques (et écart égal au risque évalué si le moteur perdait deux fois plus), tacle compté une fois et seulement dans l'intervalle. Déterminisme : deux exécutions de `measure_v2 2` identiques, hors temps de calcul (`04c-det1.txt`, `04c-det2.txt`). Suite complète : 2 554 passés, 14 désélectionnés (2 551 + 3, aucun test existant adapté ; `04c-suite.txt`).
- **Durée.** Estimée 1 h 35, réelle environ 1 h 40 (+ 5 %), non chronométrée.
- **Clôture (08/11/2026).** Expert : `APPROVED_WITH_RESERVATIONS` (empreinte 78b7ed57…). QC (`valider-etape`) : `VALIDÉ`. Suite complète sur l'état final : 2 554 passés, 14 désélectionnés. Réserves : A1 (colonne « avec tacle » : le tick +0,5 s est exclu de la fenêtre, au plus 0,8 tacle par match manqué, environ +0,1 point ; documenté en section 18, correctif d'une ligne si cette colonne devient une mesure) ; facultatifs : A2 (l'indicateur ne distingue un écart de réalisme d'un écart de cohérence qu'après 04e, 07 ou 11, où il est à refaire), A3 (séparateur décimal « 0.1 » dans les clés). QC, réserves non bloquantes : durée non chronométrée, indicateur peu discriminant par construction, `data/joueurs.xlsx` à ne pas commiter. Réserve A1 acceptée d'office par la consigne permanente du propriétaire du 08/11/2026 : « Considéré que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit si les conditions sont nécessaires ». Réserves A1 et A3 du 04b (garde-fous du tacle absents de la dépossession) : toujours ouvertes, hors périmètre de ce ticket (validation sans changement de moteur).
