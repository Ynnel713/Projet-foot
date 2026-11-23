# 02a2: Hauteur du ballon : courbe des tirs

**Découpé du ticket `02a` le 23/11/2026** (décision du propriétaire). Référence de détail : `02a-hauteur-du-ballon-physique.md` point 4.

**What to build:** un tir a une vraie hauteur pendant son vol (`z`, `vz` du `02a1`) : `vz0` est choisi pour que le ballon passe la ligne de but à la hauteur que fixe déjà l'issue du tir (`SHOT_AIM_HEIGHT_M` + pente, `v2-collectif/28b`, `v2-realisme/05a`) : sous 2,44 m pour un tir cadré, au-dessus pour un tir « au-dessus ». L'issue du tir n'est pas changée. Cohérence à examiner entre la hauteur réelle et la hauteur lue par le gardien et le contre (pente linéaire).

**Attributs :** aucun.

**Blocked by:** `02a1`.

**Bloque :** `02b` (tirs à l'écran), `v2-attributs-restants/10b`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 12 min), suite complète (environ 15 min).

**Constantes :** celles du `02a1` (validées le 23/11/2026) ; aucune nouvelle.

## Acceptance criteria

- [ ] Tirs de 50 matchs : 100 % des cadrés passent la ligne sous 2,44 m, 100 % des « au-dessus » au-dessus
- [ ] Issue des tirs inchangée (mêmes graines)
- [ ] `z ≥ 0` sur tous les pas
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu
