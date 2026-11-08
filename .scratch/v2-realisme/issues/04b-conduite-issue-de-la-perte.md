# 04b: Conduite : où va le ballon perdu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une perte de conduite n'est pas toujours une dépossession propre). **Catégorie :** exécution.

**Constat vérifié :** aujourd'hui une perte en conduite n'existe que par tacle gagné : le ballon passe directement au tacleur (`match.py`, branche `result.won`).

**What to build:** Une perte de conduite du 04a donne, selon la situation : dépossession par l'adversaire au contact, ou ballon libre devant le porteur (touche trop longue) à une distance et un angle tirés dans des bornes validées. Le ballon libre est disputé normalement (`BALLON_LIBRE`).

**Attributs :** aucun

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution).

**Bloque :** 04c.

**Status:** livré (08/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : partage dépossession / touche trop longue selon la pression : valeur proposée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** perte sans adversaire au contact : jamais une dépossession ; au contact : les deux issues possibles

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Deux issues tracées
- [x] Part de chaque issue rapportée sur 20 matchs
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- **Constantes (08/11/2026).** Proposées avant le code, acceptées d'office par la consigne du propriétaire du 08/11/2026 (« Considéré que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit si les conditions sont nécessaires »). Dépossession : un adversaire à moins de `DISPOSSESSION_RADIUS_M` = 1,5 m (la portée du tacle, `match.TACKLE_RADIUS_M`, test d'égalité) prend le ballon avec la probabilité de la gêne (70 % à 1,5 m, 100 % au contact) : aucune constante de partage nouvelle. Touche trop longue : le ballon s'arrête devant le porteur à une distance tirée dans `LONG_TOUCH_M` = 1,5 à 4 m, dans un angle de ± `LONG_TOUCH_DEG` = 30° autour de sa direction de conduite (vers le point de conduite, sinon sa vitesse, sinon le but). Chiffres réels de la longueur d'une touche trop longue : non trouvés, bornes d'ordre de grandeur.
- **Réalisation.** `decision.lost_carry_outcome` (flux DUEL) donne l'adversaire qui prend le ballon ou la vitesse de départ du ballon libre (calculée pour qu'il s'arrête, freiné, à la distance tirée). `match._step_ball` traite la dépossession comme un tacle gagné (porteur, délai de réception, hors-jeu effacé) et le ballon libre comme avant (porteur écarté `MISS_RETRY_S`). La perte ne lit plus ni la vitesse de course du porteur, ni Composure, ni First Touch, ni le flux PASSE (réserve A4 du 04a levée, test dédié).
- **Mesure (20 matchs, section 17 de `docs/INDICATEURS_V2.md`).** 86,6 pertes de conduite par match (87,6 au 04a) : 46,2 dépossessions (53,4 %) et 40,4 touches trop longues (46,6 %). Déterminisme : deux exécutions de `measure_v2 2` identiques (hors temps de calcul). Suite complète : 2 551 passés, 14 désélectionnés (2 544 + 7 tests ajoutés, aucun test existant adapté ; `04b-suite.txt`).
- **Durée.** Estimée 1 h 45, réelle environ 1 h 50 (+ 5 %), non chronométrée.
- **Clôture (08/11/2026).** Expert : `APPROVED_WITH_RESERVATIONS` (empreinte 491dbc60…). QC (`valider-etape`) : `VALIDÉ`. Suite complète sur l'état final : 2 551 passés, 14 désélectionnés. Réserves : A1 (la dépossession ne reprend pas les garde-fous du tacle : `engaged`, `tackle_ban_until_s`, `offside_out_until` ; biais faible, à traiter au 04c) ; A2 (la distance tirée est comptée depuis le point où le ballon est lâché, à `CONTROL_RADIUS_M` du porteur : bornes reformulées dans la section 17) ; facultatifs : dépassement du ballon par le porteur écarté 0,5 s (A3, à regarder au 04c avec le devenir de la touche trop longue), code de passation dupliqué avec le tacle gagné (A4). Réserves acceptées d'office par la consigne du propriétaire du 08/11/2026 : « Considéré que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit si les conditions sont nécessaires ».
