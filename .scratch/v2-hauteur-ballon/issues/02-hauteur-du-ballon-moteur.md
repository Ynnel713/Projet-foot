# 02: Hauteur du ballon dans le moteur V2

**What to build:** le moteur V2 calcule la hauteur réelle du ballon (révision de D-V03, `docs/TRD_V2.md`) ; l'écran la
dessine sans rien recalculer. Étude : `docs/ETUDE_HAUTEUR_V2.md`, sections 4 et 5.

1. **État du ballon** (`v2engine/ball_state.py`) : `z` (m), `vz` (m/s). `aerial_left_m` disparaît au profit de `z`.
2. **Départ d'un ballon aérien** (`v2engine/match.py`, `v2engine/restart.py`) : durée de vol `T` déduite de la distance
   et de la vitesse avec le freinage exponentiel (λ = −ln `BALL_FRICTION_PER_S`) : `T = −ln(1 − d·λ / v0) / λ`, puis
   `vz0 = g·T / 2` ; cas `d·λ ≥ v0` (le ballon n'arrive pas) traité explicitement.
3. **Pas du ballon** (`_step_ball`) : chute libre exacte sur le pas (`z += vz·dt − g·dt²/2`, `vz −= g·dt`) ; impact
   coupé à l'instant exact ; rebond `vz ← −0,70·vz`, vitesse horizontale × 0,85 (valeurs V1) ; sous un seuil de `vz`,
   le ballon roule (`z = 0`).
4. **Tirs** : la trajectoire respecte l'issue déjà décidée par le calcul de tir (ticket `v2-collectif/28`) : hauteur à
   la ligne de but sous 2,44 m pour un tir cadré, au-dessus pour un tir « au-dessus ».
5. **Mode calculé** : « aérien » si `z` dépasse un seuil (à proposer), « sol » sinon. Format d'API inchangé.
   Les règles d'interception restent celles du ticket 29 (lues sur le mode) : elles ne changent qu'au ticket 03.
6. **Trace** (`v2engine/trace.py`, `api/serializers.py`, `api/schemas.py`) : `BallSnapshot.z` ; pendant un vol, points
   `(x, y, z)` de chaque tick moteur (0,1 s) attachés à l'enregistrement d'une seconde.
7. **Écran** : le ballon est projeté avec sa vraie hauteur (projection du ticket 01) ; rayon × `1 + min(0,40 ; 0,05·z)` ;
   ombre au point `(x, y, 0)`, rayon × `max(0,5 ; 1 − 0,05·z)`, opacité de 0,30 au sol à 0,10 à 10 m. L'écran interpole
   entre les points de vol, sans calcul physique.
8. **Documentation** : `docs/PLAN_V2.md`, `docs/INDICATEURS_V2.md` si un indicateur change.

**Constantes proposées** (à valider avant le code) : g = 9,81 m/s² ; restitution 0,70 et freinage par rebond 15 % (V1) ;
seuil « aérien » et seuil d'arrêt du rebond à proposer ; affichage ci-dessus.

**Blocked by:** 01 (projection à l'écran), `v2-collectif/28` (issue du tir), `v2-collectif/29` (mode de ballon,
ballon mort).

**Status:** découpé (04/11/2026, audit de granularité) en 02a (physique dans le moteur) et 02b (points de vol dans la trace et rendu à l'écran). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

## Acceptance criteria

- [ ] Point le plus haut = `vz0² / 2g` (écart < 2 %) ; durée de vol = `2·vz0 / g` (écart < 1 tick)
- [ ] Point de chute d'une passe aérienne à ± 1 m de sa cible
- [ ] Rebond : hauteur suivante = 0,49 × la précédente (± 5 %), le ballon finit par rouler
- [ ] `z ≥ 0` sur tous les ticks de 50 matchs
- [ ] Tirs de 50 matchs : 100 % des cadrés passent la ligne sous 2,44 m, 100 % des « au-dessus » au-dessus
- [ ] Mode tracé cohérent avec `z` à chaque enregistrement
- [ ] Ordres de grandeur réels (dégagement de gardien, centre, passe lobée) dans des fourchettes sourcées, ou « non
      trouvé » noté
- [ ] Mêmes empreintes de trace sur deux exécutions à graine fixée
- [ ] Poids de la trace par match mesuré avant/après
- [ ] Comportement sportif inchangé à bruit près sur 50 matchs (`scripts/measure_v2.py`, `scripts/v2_indicators.py`)
- [ ] Suite complète au compte attendu ; V1 inchangée ; à l'écran, centres et dégagements montent et retombent
