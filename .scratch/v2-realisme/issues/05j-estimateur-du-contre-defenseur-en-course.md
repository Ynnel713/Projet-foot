# 05j: Estimateur du contre pour un défenseur en course

**Chantier :** `v2-realisme`. **Priorité :** P1 (préalable à tout relèvement de `shooting.BLOCK_CHANCE`). **Catégorie :** tir, numérique.

**Origine :** ticket 18e (12/11/2026). Relever `BLOCK_CHANCE` de 0,6 à 0,75 amène les tirs contrés au repère (17,6 → 22,4 % sur 50 matchs, repère 22,5 %), mais fait échouer `tests/test_v2engine_chance_tir.py::test_goal_and_block_are_judged_together_shot_direction_by_shot_direction` sur la scène du défenseur qui coupe la trajectoire en courant (16 m, défenseur à 7 m de la ligne, 2 m de l'axe, 4 m/s). L'écart existe déjà à 0,6 (graine 7 hors de l'intervalle) : l'estimateur (`shooting._block_covers`) place l'angle couvert par un défenseur en course là où il serait sur la ligne joueur-tireur (approximation documentée), alors que la boucle de match juge le contact pas à pas, en mouvement relatif. Mesure (1 500 tirs, graines 6 et 7) : avec 0,6 → 0,75, les contres observés passent de 409 à 522 et 390 à 492, les buts restent à 252 et 280 → 270 : le défenseur en course contre surtout des tirs que le gardien aurait arrêtés, l'estimateur lui fait couvrir les angles qui marquent (chance de but évaluée 0,158 → 0,146, observée 0,17 à 0,19). Élargir la portée du demi-balayage d'un pas ne corrige pas (essai du 18e : contres surestimés, but inchangé).

**What to build :** Couvertures angulaires d'un défenseur en mouvement calculées angle par angle (instant où le ballon, tiré dans cet écart, passe au plus près de lui à sa position de cet instant, portée `block_reach_m` à ce temps de vol), au lieu d'une position unique ; coût de calcul mesuré (`occasion_quality` est appelée à chaque décision). Puis relever `BLOCK_CHANCE` vers le repère (0,75 mesuré au 18e) si les tests de cohérence tiennent.

**Hors de ce ticket :** but sur ballon dévié (05i) ; calibration finale (`v2-collectif/22c`).

**Attributs :** aucun.

**Blocked by :** 05e, 05c.

**Bloque :** `v2-collectif/22c` (relèvement de `BLOCK_CHANCE`).

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 45 min |
| Tests | 30 min |
| Intégration et vérifications | 35 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible (géométrie d'interception par angle, coût de calcul). À examiner pour découpage avant le code. Temps machine, hors total : `scripts/shot_calibration.py`, série de 50 matchs, suite complète.

## Acceptance criteria

- [x] Scène du défenseur en course (16 m ; 7 m, 2 m, 4 m/s) : chance de but et de contre évaluées dans l'intervalle à 95 % de l'observé sur 1 500 tirs, graines 5 à 9, avec `BLOCK_CHANCE` 0,6 et 0,75 (test `test_a_running_defender_is_judged_like_the_real_trajectory`, 10 cas)
- [x] Scènes à défenseurs immobiles de `test_v2engine_chance_tir.py` inchangées (toutes dans l'intervalle)
- [x] Temps de calcul par match rapporté avant/après : moteur inchangé, temps identique
- [x] Si `BLOCK_CHANCE` est relevée : non relevée (recommandation retenue par délégation du propriétaire, 22/11/2026 : 24,2 % de contrés après le `10k`, dans le repère)
- [x] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md` : moteur inchangé, scènes à graine fixée ; 3 481 passés, 0 ignoré, 14 désélectionnés (3 470 au `10k` + 11 cas)

## Résultat (22/11/2026, `docs/INDICATEURS_V2.md` section 60)

L'écart venait du banc de scènes (`scripts/shot_calibration._scene`), qui avance les défenseurs d'un pas avant de résoudre le tir mais évaluait la chance avec leur place de départ (0,4 m d'écart pour un défenseur à 4 m/s). Corrigé : la chance est évaluée à l'instant de la frappe. L'estimateur existant est alors juste, graines 5 à 9, contre et but, à `BLOCK_CHANCE` 0,6 et 0,75. Une couverture en mouvement relatif (bords par dichotomie dans le repère du défenseur) a été essayée : sur cinq scènes plus dures, aucune différence mesurable (0,007 au plus) ; écartée (coût à chaque décision). Moteur inchangé. 2 tests ajoutés (11 cas).

Durée : estimée 2 h 20, réelle environ 1 h 05 (analyse 30 min, développement et essai écarté 15 min, tests 10 min, intégration et documentation 10 min), écart − 54 % : la cause s'est révélée hors de l'estimateur (banc de scènes), sans code moteur à écrire. Découvert pendant le `05l` (la visée du tireur exposait l'écart). Temps machine hors total : scènes (environ 5 min), suite complète.

## Comments
- 22/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Réserves facultatives : A1 assertion du test de régression plus faible que son commentaire (écart > 0,01 au lieu de « hors de l'intervalle »), non reprise pour ne pas rouvrir la revue ; A2 critère 5 à cocher (fait). À surveiller : relancer `05j-durs.py` avec des défenseurs plus rapides et plus proches si `v2-collectif/22c` en dépend.
