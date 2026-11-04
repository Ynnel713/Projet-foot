# 02: Affichage du mode de ballon (suivi du ticket v2-collectif/29, réserve A1)

**What to build:** le moteur trace depuis le ticket v2-collectif/29 le mode du ballon (`BallSnapshot.mode` : « sol » ou « aérien ») et le ballon mort (`BallSnapshot.dead`), mais l'écran ne les montre pas : l'écran V2 était en cours de modification par une autre session au moment du ticket 29.

1. **API** : exposer `mode` et `dead` dans `BallSnapshotOut` (`api/routers/v2.py`, `_tick_out`).
2. **Écran** (`ui/src/routes/V2Match.jsx`) : un ballon aérien est dessiné plus gros (rayon 0,6 au lieu de 0,4), décalé vers le haut d'un mètre, avec son ombre au sol (disque noir, opacité 0,3) ; l'interpolation entre deux images garde le mode de l'image de départ.
3. Facultatif : un ballon mort peut être légèrement atténué.

**Blocked by:** commit des modifications en cours de l'écran V2 et de `api/routers/v2.py` (feuille de match), pour ne pas mélanger deux travaux dans un commit.

**Status:** fusionné (04/11/2026) dans `.scratch/v2-hauteur-ballon/issues/01-camera-inclinee.md` (point 6 et deux critères repris) : même fichier, et l'affichage à hauteur fixe n'était qu'une étape avant la vraie hauteur. Audit de granularité.

**Origine (03/11/2026) :** réserve A1 de l'expert sur le ticket v2-collectif/29, acceptée par le propriétaire (« Oui j'accepte »).

## Acceptance criteria

- [ ] Test d'API : `mode` et `dead` sont sérialisés pour chaque image
- [ ] À l'écran : corner centré et sortie de but longue montrent le ballon aérien et son ombre ; ballon au sol inchangé
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur
