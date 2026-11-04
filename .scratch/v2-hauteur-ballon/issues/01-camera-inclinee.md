# 01: Caméra inclinée (écran V2)

**What to build:** l'écran V2 (`ui/src/routes/V2Match.jsx`) passe d'une vue strictement du dessus à une caméra fixe
légèrement inclinée, sans perspective (étude `docs/ETUDE_HAUTEUR_V2.md`, section 5). Moteur et trace inchangés.

1. **Projection unique** `project(x, y, z)` : `sx = x`, `sy = y·cos α − z·sin α`. Tout ce qui est posé sur le terrain
   y passe : pelouse et lignes, surfaces, joueurs, ballon, noms, flèches d'intention, sélection au clic. Compatible
   avec le terrain retourné (miroir horizontal).
2. **Buts en hauteur** : poteaux et barre transversale (2,44 m) dessinés par la projection.
3. **Joueurs** : vrais cercles (jamais d'ovales), petite ombre ovale au sol sous chacun, dessinés du fond vers l'avant
   (tri par `y`).
4. **Ballon** : projeté ; en attendant le ticket 02, un ballon « aérien » garde l'affichage du ticket
   `v2-correctifs-ecran/02` (hauteur fixe d'un mètre), désormais passé par la projection.
5. Ordre de dessin : pelouse et lignes → ombres → joueurs triés → buts → ballon → noms.
6. **Mode de ballon et ballon mort** (repris du ticket `v2-correctifs-ecran/02`, fusionné ici le 04/11/2026) : l'API
   expose `mode` et `dead` dans `BallSnapshotOut` (`api/routers/v2.py`, `_tick_out`) ; un ballon aérien est dessiné
   plus gros (rayon 0,6 au lieu de 0,4), à un mètre de hauteur passé par la projection, avec son ombre au sol (disque
   noir, opacité 0,3) ; l'interpolation entre deux images garde le mode de l'image de départ. Facultatif : un ballon
   mort légèrement atténué. Cet affichage à hauteur fixe est provisoire : le ticket 02b le remplace par la vraie hauteur.

Pas de rotation 3D de toute l'image (`rotateX` CSS) : elle déformerait les ronds et les noms.

**Constantes validées par le propriétaire (04/11/2026, après prototype comparant 0° à 35°)** : α = 25° depuis la
verticale (terrain écrasé de 9 %, ballon à 10 m remonté de 4,2 m à l'écran) ; ombre de joueur : ovale de rayon
0,8 × rayon du rond, opacité 0,25.

**Blocked by:** aucun depuis le 04/11/2026 : `v2-correctifs-ecran/02` y est fusionné, et les travaux en cours sur l'écran V2 sont commités (`9aa4ff9`, `efa65c2`). Démarrable.

**Bloque :** 02b (vraie hauteur à l'écran).

**Status:** à faire

## Acceptance criteria

- [x] Angle et ombres validés par le propriétaire avant le code
- [ ] Terrain entièrement visible en largeur téléphone (375 px) et sur bureau
- [ ] Joueurs dessinés en cercles, le plus proche recouvre le plus lointain
- [ ] Noms, flèches d'intention et sélection au clic alignés sur les joueurs, terrain retourné compris
- [ ] Poteaux et barre visibles en hauteur
- [ ] Test d'API : `mode` et `dead` sont sérialisés pour chaque image (repris de `v2-correctifs-ecran/02`)
- [ ] À l'écran : corner centré et sortie de but longue montrent le ballon aérien et son ombre ; ballon au sol inchangé
- [ ] Fluidité inchangée : images par seconde mesurées avant/après sur téléphone
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur ; suite V2 verte ; V1 inchangée
