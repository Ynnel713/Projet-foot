# 02a: Hauteur du ballon dans le moteur : physique

**Découpé du ticket 02 le 04/11/2026** (audit de granularité). Formules, constantes proposées et étude : `02-hauteur-du-ballon-moteur.md`, points 1 à 5, et `docs/ETUDE_HAUTEUR_V2.md`, sections 4 et 5.

**What to build:** le moteur V2 calcule la hauteur réelle du ballon (révision de D-V03) :
1. **État du ballon** (`v2engine/ball_state.py`) : `z`, `vz` ; `aerial_left_m` disparaît au profit de `z`.
2. **Départ d'un ballon aérien** : durée de vol déduite de la distance et de la vitesse avec le freinage exponentiel ; cas où le ballon n'arrive pas traité explicitement.
3. **Pas du ballon** (`_step_ball`) : chute libre exacte sur le pas, impact coupé à l'instant exact, rebond (valeurs V1), puis le ballon roule.
4. **Tirs** : la trajectoire respecte l'issue décidée par `v2-collectif/28b` (sous 2,44 m à la ligne pour un tir cadré, au-dessus pour un tir « au-dessus »).
5. **Mode calculé** : « aérien » si `z` dépasse un seuil, « sol » sinon ; format d'API inchangé ; les règles d'interception du ticket 29 restent lues sur le mode jusqu'au ticket 03.
6. **Trace** : `BallSnapshot.z` à chaque enregistrement.

**Blocked by:** `v2-collectif/28b` (issue du tir), `v2-collectif/29` (livré).

**Bloque :** 02b, 03 ; `v2-attributs-restants/10b` (ajouté le 10/11/2026, audit de la roadmap).

**Status:** découpé (23/11/2026, décision du propriétaire) en `02a1` (vol des passes et remises aériennes : hauteur, rebonds, mode calculé, hauteur tracée) et `02a2` (courbe des tirs cohérente avec leur issue) : estimé à 3 h, au-delà du seuil de 2 h. Constantes validées le 23/11/2026 : g 9,81 m/s², restitution 0,70, freinage par rebond 15 %, fin des rebonds sous 15 cm (V1), durée de vol plafonnée à 4 s, seuil « aérien » 2,5 m avec rebonds réels. Ticket chapeau : ne pas l'implémenter tel quel. **Clos le 23/11/2026** : `02a1` et `02a2` livrés, validés expert + QC.

## Acceptance criteria

- [ ] Constantes (g, restitution, freinage par rebond, seuils « aérien » et d'arrêt du rebond) validées par le propriétaire avant le code
- [ ] Point le plus haut = `vz0² / 2g` (écart < 2 %) ; durée de vol = `2·vz0 / g` (écart < 1 tick)
- [ ] Point de chute d'une passe aérienne à ± 1 m de sa cible
- [ ] Rebond : hauteur suivante = 0,49 × la précédente (± 5 %), le ballon finit par rouler
- [ ] `z ≥ 0` sur tous les ticks de 50 matchs ; mode tracé cohérent avec `z` à chaque enregistrement
- [ ] Tirs de 50 matchs : 100 % des cadrés passent la ligne sous 2,44 m, 100 % des « au-dessus » au-dessus
- [ ] Ordres de grandeur réels (dégagement de gardien, centre, passe lobée) dans des fourchettes sourcées, ou « non trouvé » noté
- [ ] Comportement sportif inchangé à bruit près sur 50 matchs (`scripts/measure_v2.py`, `scripts/v2_indicators.py`)
- [ ] Mêmes empreintes de trace sur deux exécutions à graine fixée ; suite complète au compte attendu ; V1 inchangée
