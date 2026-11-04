# 02b: Hauteur du ballon à l'écran

**Découpé du ticket 02 le 04/11/2026** (audit de granularité). Détail : `02-hauteur-du-ballon-moteur.md`, points 6 et 7.

**What to build:**
1. **Trace** (`v2engine/trace.py`, `api/serializers.py`, `api/schemas.py`) : pendant un vol, points `(x, y, z)` de chaque tick moteur (0,1 s) attachés à l'enregistrement d'une seconde.
2. **Écran** : le ballon est projeté avec sa vraie hauteur (projection du ticket 01) ; rayon × `1 + min(0,40 ; 0,05·z)` ; ombre au point `(x, y, 0)`, rayon × `max(0,5 ; 1 − 0,05·z)`, opacité de 0,30 au sol à 0,10 à 10 m. L'écran interpole entre les points de vol, sans calcul physique. Remplace l'affichage provisoire à hauteur fixe d'un mètre du ticket 01.
3. **Documentation** : `docs/PLAN_V2.md`, `docs/INDICATEURS_V2.md` si un indicateur change.

**Blocked by:** 01, 02a.

**Bloque :** aucun.

**Status:** à faire

## Acceptance criteria

- [ ] Points de vol présents dans la trace et sérialisés par l'API (test)
- [ ] Poids de la trace par match mesuré avant/après
- [ ] À l'écran, centres et dégagements montent et retombent ; ombre au sol cohérente avec la hauteur
- [ ] Mêmes empreintes de trace sur deux exécutions à graine fixée
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur ; suite complète au compte attendu ; V1 inchangée
