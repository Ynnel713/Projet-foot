# 02a2: Hauteur du ballon dans le moteur : tirs

**Découpé du ticket 02a le 26/11/2026** (décision du propriétaire). Détail : `02-hauteur-du-ballon-moteur.md`, point 4.

**What to build:** les tirs prennent une vraie trajectoire en hauteur, cohérente avec l'issue tirée par `v2-collectif/28b` (`v2engine/shooting.py`) :
1. **Hauteur à la ligne** : tirée dans la loi gaussienne de hauteur qui existe déjà (`SHOT_AIM_HEIGHT_M`, `SHOT_ERROR_SIGMA_RAD`), **conditionnée à l'issue** : tir cadré, haut du ballon sous la barre (`z + 2·BALL_RADIUS_M < 2,44`, convention du 02a1) ; tir « au-dessus », bas du ballon au-dessus de la barre. Aucune constante nouvelle.
2. **Trajectoire** : `vz0` déduit de la hauteur visée à la ligne et du temps de trajet (même physique que le 02a1).
3. Le tir « au-dessus » cesse d'être rejoué à plat comme un tir à côté (`shooting.py:257`).

**Blocked by:** 02a1.

**Bloque :** 03 ; `v2-collectif/28b` réserve A2 (ballon claqué sans hauteur) si elle est reprise ici, à vérifier à l'ouverture.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèse : la physique du 02a1 se réutilise telle quelle.
Temps machine, non compté : une série de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Tirs de 50 matchs : 100 % des cadrés passent la ligne haut du ballon sous 2,44 m ; 100 % des « au-dessus » bas du ballon au-dessus
- [ ] Répartition des issues (cadré, à côté, au-dessus, dévissé) inchangée dans le bruit des séries de référence du 02a1
- [ ] Mêmes empreintes de trace sur deux exécutions à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
