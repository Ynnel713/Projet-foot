# 28b: Issues du tir : contré, capté, repoussé, claqué

**Découpé du ticket 28 le 04/11/2026** (audit de granularité). Détail : `28-occasion-et-issue-du-tir.md`, points 5 et 7 (partie tir).

**What to build:**

1. **Issues du tir** : but, à côté, contré, arrêté. L'arrêt se décline selon la situation (force, angle, hauteur, distance) : **capté**, **repoussé** (devant, sur le côté, en l'air : le ballon libre part selon la direction et la force du tir, seconds ballons), **claqué** en corner ou en sortie de but (remises en jeu du ticket 29). Le contre minimal du ticket 33 est remplacé.
2. Notes du gardien : part neutre sans attribut jusqu'à `v2-attributs-restants/03` (A8 n'est pas levée à moitié).
3. **Trace** : pour un tir, tireur, position, qualité de l'occasion (28a), issue, origine (passe au sol, en retrait, en profondeur, centre, dribble, rebond). Le rendu 2D rejoue l'issue enregistrée.

**Attributs :** aucun nouveau (gardien neutre).

**Blocked by:** 28a.

**Bloque :** `v2-hauteur-ballon/02a` (trajectoire qui respecte l'issue), `v2-attributs-restants/10a`, `v2-attributs-restants/11` ; 17, 19, 22a.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Constantes produit (part des parades repoussées, répartition capté / repoussé / claqué) validées par le propriétaire avant le code
- [ ] Les issues existent en match : but, à côté, contré, capté, repoussé, claqué
- [ ] Test de cohérence : l'arrêt claqué en corner est plus fréquent sur un tir puissant et excentré que sur un tir central faible, où le gardien capte ; la direction de la repoussée dépend de la direction du tir
- [ ] Repris du ticket 29 (réserve A2 acceptée le 03/11/2026) : corners 6 à 14 par match et touches 30 à 55 par match (50 matchs, graine d'audit) ; au ticket 29 : 0,84 corner et 22,7 touches
- [ ] En match : tirs cadrés (30-35 %), tirs contrés (20-28 %), conversion (10-11 %), part des buts dans la surface (80-90 %), comparés aux indicateurs à sourcer
- [ ] Indicateurs ajoutés au banc (`scripts/v2_indicators.py`) et définis dans `docs/INDICATEURS_V2.md`
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
