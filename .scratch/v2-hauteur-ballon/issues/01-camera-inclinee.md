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

**Status:** livré (06/11/2026), validé expert + QC (réserves acceptées par le propriétaire : `PLAYER_LIFT`, vrai corner reporté au 02b, fluidité bornée par substitution)

## Réalisé (06/11/2026)

- `ui/src/utils/v2Projection.js` : projection unique `project(x, y, z)` (α = 25°) et matrice SVG du sol `GROUND_MATRIX`.
- `ui/src/routes/V2Match.jsx` : pelouse, lignes, filets et bancs à plat par la matrice ; joueurs (vrais cercles) triés du
  fond vers l'avant avec leur ombre ; poteaux et barre à 2,44 m ; ballon projeté (aérien : rayon 0,6, un mètre, ombre
  au sol ; mort : atténué à 0,6) ; nom du porteur sous son rond ; `viewBox` recalculé (terrain 9 % moins haut).
  `interpolatedTick` garde `mode` et `dead` de l'image de départ.
- `api/routers/v2.py` : `mode` et `dead` dans `BallSnapshotOut` et `_tick_out` ; test
  `test_tick_out_serialises_ball_mode_and_dead_for_every_image` (`tests/test_v2engine_trace.py`).
- **Constante ajoutée, validée par le propriétaire le 06/11/2026** (« Ok avec lui », après l'avis de l'expert réalisme : garder 1,8 m ; si l'ombre est trop discrète sur téléphone, jouer sur l'opacité, pas sur la hauteur) : `PLAYER_LIFT = 1,8 m`. Le rond d'un joueur est dessiné à la hauteur de sa taille ;
  à hauteur du sol il recouvrirait entièrement son ombre (ovale de rayon 0,8 × celui du rond), qui deviendrait invisible.
  Ajustable à l'écran dans `V2Match.jsx`.
- Le texte du ticket parle de « flèches d'intention » : l'écran V2 n'en dessine aucune (l'intention se lit dans le
  panneau sous le terrain). Rien à aligner.

## Acceptance criteria

- [x] Angle et ombres validés par le propriétaire avant le code
- [x] Terrain entièrement visible en largeur téléphone (375 px) et sur bureau (vu dans le navigateur intégré)
- [x] Joueurs dessinés en cercles, le plus proche recouvre le plus lointain (22 cercles de rayon 1,3 et 22 ombres comptés dans le DOM ; tri par `y`)
- [x] Noms, flèches d'intention et sélection au clic alignés sur les joueurs, terrain retourné compris (clic réel sur un joueur à 375 px : sélection obtenue ; 2e période non regardée à l'écran, le demi-tour est appliqué aux coordonnées avant la projection)
- [x] Poteaux et barre visibles en hauteur (vu agrandi sur le but gauche)
- [x] Test d'API : `mode` et `dead` sont sérialisés pour chaque image (repris de `v2-correctifs-ecran/02`)
- [x] ~~À l'écran : corner centré et sortie de but longue montrent le ballon aérien et son ombre~~ : **reporté au ticket 02b** (décision du propriétaire le 06/11/2026, « Ok avec lui », suivant l'avis de l'expert : l'affichage à un mètre est provisoire). Vérifié ici seulement en forçant `mode = aérien` : rayon 0,6, ombre au sol, écart vertical 1 m × sin 25° = 0,4226 m
- [x] Fluidité inchangée : **bornée par substitution, images par seconde réelles non mesurées** (réserve résiduelle acceptée par le propriétaire le 06/11/2026, « Ok avec ta recommandation »). Mesure en direct impossible le 06/11/2026 (Chrome non connecté ; panneau intégré masqué). Mesure en direct impossible le 06/11/2026 (Chrome non connecté ; panneau intégré masqué, aucune image d'animation). **Mesure de substitution** : coût de rendu du terrain (`V2Pitch`, rendu serveur de React en mode production, 22 joueurs, 2 bancs, 3 000 rendus, 3 séries alternées) : version d'origine 0,44 / 0,76 / 0,71 ms (moyenne 0,64) ; version du ticket 0,73 / 0,81 / 0,78 ms (moyenne 0,77) ; soit +0,13 ms par image (+20 %, bruit de mesure important), moins de 1 % d'un budget de 16,7 ms ; nœuds SVG 198 → 231 (+17 %). Non mesurés : peinture et images par seconde réelles sur téléphone (méthode proposée par l'expert : onglet visible, processeur ralenti 6 fois, base `41e573e` contre état du ticket, 30 s, critère 10 %). Mesure réelle reprise dans les critères du ticket 02b (base `41e573e`)
- [x] `npm run build` OK, `npm run lint` sans nouvelle erreur (0 erreur, 5 avertissements existants) ; V1 inchangée (aucun fichier V1 touché)
- [x] Suite complète verte : 2 447 passés, 14 désélectionnés (06/11/2026, 26 min 39 s), soit les 2 446 attendus plus le test d'API

## Comments

**06/11/2026, passage 1.** Expert : `APPROVED_WITH_RESERVATIONS`. Contrôle qualité : `BLOQUÉ`. Décision de clôture : `BLOQUÉ` (« expert APPROVED_WITH_RESERVATIONS, QC BLOQUÉ »), journalisée.
- Expert, aucune erreur de calcul ni de géométrie trouvée (projection, `viewBox`, tri, ombres, demi-tour de la 2e période lu dans le code).
- Réserve A1 de l'expert : `PLAYER_LIFT = 1,8 m` ajoutée sans validation du propriétaire.
- Réserve A2 de l'expert : critères « vrai corner et sortie de but longue à l'écran » et « images par seconde sur téléphone » non vérifiés.
- Facultatifs de l'expert : A3 (ballon toujours dessiné au-dessus des joueurs, à revoir au 02b) ; A4 (pas de test JS de `project`, pas d'infrastructure de test côté UI).
- Contrôle qualité : aucun défaut démontrable (donc pas `REFUSÉ`), mais les deux critères non vérifiés et la constante non validée ne se tranchent pas par lecture. Il n'a pu exécuter ni build, ni lint, ni suite (lecture seule).
- Réserves acceptées par le propriétaire : aucune à ce jour (passage 1).

**06/11/2026, décisions du propriétaire après l'avis de l'expert réalisme.** Le propriétaire a demandé l'avis de l'expert réalisme, puis répondu « Ok avec lui » à la recommandation : garder `PLAYER_LIFT = 1,8 m` ; reporter au 02b le critère du vrai corner (avec la mention « inclut le critère reporté du 01 ») ; mesurer la fluidité avant de clore. Fluidité : mesure de substitution faite (voir le critère), à soumettre à l'expert et au contrôle qualité (passage 2).

**06/11/2026, passage 2.** Expert : `APPROVED_WITH_RESERVATIONS` (la mesure de substitution suffit à lever la fluidité comme condition de clôture, risque borné à moins de 2 % du budget d'image ; réserve résiduelle : images par seconde réelles non mesurées, à faire accepter par le propriétaire et à reporter au 02b, fait). Contrôle qualité : `BLOQUÉ` (aucun défaut démontrable ; le critère de fluidité n'est pas établi par la mesure de substitution : peinture et images par seconde non couvertes, écart dans le bruit des séries). Décision de clôture : `BLOQUÉ` (« expert APPROVED_WITH_RESERVATIONS, QC BLOQUÉ »), journalisée. Sortie possible : mesure en direct des images par seconde, ou acceptation explicite par le propriétaire de la mesure de substitution. Détail à corriger au prochain passage : le commentaire de `PLAYER_LIFT` dit encore « pas encore validée par le propriétaire ».

**06/11/2026, décisions du propriétaire à l'issue du passage 2.** Le propriétaire a choisi d'accepter la mesure de substitution (« Ok avec ta recommandation », à la suite de la recommandation : accepter la substitution et garder la mesure réelle au 02b). Réserves acceptées, une par une : (1) `PLAYER_LIFT = 1,8 m` gardée (« Ok avec lui », 06/11/2026) ; (2) critère du vrai corner reporté au 02b (« Ok avec lui ») ; (3) images par seconde réelles non mesurées, fluidité bornée par substitution, mesure réelle reprise au 02b (« Ok avec ta recommandation »). Commentaire périmé de `PLAYER_LIFT` corrigé : changement de commentaire seulement, nouvelle empreinte, passage 3.

**06/11/2026, passage 3.** Expert : `APPROVED_WITH_RESERVATIONS` (confirmé sur la nouvelle empreinte `476731ac…` ; seul changement de code : le commentaire de `PLAYER_LIFT`). Contrôle qualité : `VALIDÉ` (aucun défaut démontrable). Décision de clôture : **`VALIDÉ`** (« expert APPROVED_WITH_RESERVATIONS (réserves acceptées par le propriétaire), QC VALIDÉ »), journalisée. Réserves acceptées par le propriétaire, avec ses mots : `PLAYER_LIFT = 1,8 m` gardée (« Ok avec lui ») ; vrai corner reporté au 02b (« Ok avec lui ») ; images par seconde réelles non mesurées, fluidité bornée par substitution, mesure réelle au 02b (« Ok avec ta recommandation »). Facultatifs repris : ordre de dessin du ballon en hauteur (au 02b), absence de test JS de `project`, 2e période (demi-tour) à regarder à l'écran au prochain contrôle visuel.

**Durée.** Estimée 210 min de travail effectif (30/120/30/30). Réelle environ 120 min (15/40/15/50), non chronométrée : écart de − 43 %. Cause : écran codé d'un seul jet (matrice SVG pour le sol, une fonction de projection), mais trois passages de clôture. Temps machine hors total : suite complète 26 min 39 s, mesure de rendu environ 8 min.
