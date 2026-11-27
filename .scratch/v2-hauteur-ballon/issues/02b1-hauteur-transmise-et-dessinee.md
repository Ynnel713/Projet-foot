# 02b1: Hauteur du ballon transmise par l'API et dessinée (taille et ombre)

**Découpé du ticket 02b le 27/11/2026** (décision du propriétaire, estimation au-delà de 2 h : « 02b1 + 02b2 »). Constantes d'écran : celles du `02b-hauteur-du-ballon-a-l-ecran.md`, point 2 (fixées au découpage du ticket 02 le 04/11/2026). Mesure de fluidité et vérifications à l'écran : `02b2`.

**What to build:**
1. **Trace et API** : le moteur relève déjà `z` (hauteur du bas du ballon) à chaque pas de 0,1 s (`BallPoint.z`, `BallSnapshot.z`, ticket 02a1). `api/routers/v2.py` le transmet : champ `z` (m, au centimètre) dans `BallSnapshotOut` et `BallPointOut`.
2. **Lecture à l'écran** (`ui/src/utils/v2Spline.js`, `components/match/trace.js`) : hauteur du ballon libre interpolée **linéairement** entre les deux points de piste qui encadrent l'instant (pas de 0,1 s : écart à la parabole au plus g·dt²/8 ≈ 1,2 cm ; pas de Catmull-Rom sur z, qui pourrait passer sous le sol) ; ballon tenu : z = 0 ; sans piste, interpolation des images ; coupures (ballon mort, mi-temps) : z du point de départ.
3. **Dessin** (`V2Pitch.jsx`, `BallMarker.jsx`) : ballon projeté à sa vraie hauteur (`project(x, y, z)`), rayon `BALL_R × (1 + min(0,40 ; 0,05·z))` ; ombre au point `(x, y, 0)`, rayon `BALL_R × max(0,5 ; 1 − 0,05·z)`, opacité de 0,30 à z = 0 à 0,10 à z = 10 m (linéaire, bornée), dessinée dès que z > 0. Remplace la hauteur fixe `BALL_AIR_Z = 1` et le rayon fixe `BALL_AIR_R = 0,6` du ticket 01. Base des deux rayons : `BALL_R` (0,5 m, ballon au sol), pour qu'un ballon qui décolle ne change pas de taille d'un coup (à 2 m de haut, rayon 0,55 m ; à 4 m, 0,60 m, l'ancien rayon fixe).
4. **Documentation** : `docs/PLAN_V2.md`, ce ticket.

**Blocked by:** 01 (livré), 02a1 et 02a2 (livrés) ; clôture conditionnée au `v2-realisme/14a` (14a1, 14a2a, 14a2b livrés).

**Bloque :** 02b2.

**Estimation** (27/11/2026) : analyse 20 min, développement 45 min, tests 30 min, intégration et vérifications 25 min ; total 2 h ; confiance moyenne. Hypothèses : le moteur relève déjà z à chaque pas (vérifié : `match.py:1416`, `trace.record_ball(..., z=ball.z)`) ; aucune mesure de jeu (aucun changement moteur). Temps machine à part : suite complète (environ 13 min), build et lint.

**Status:** livré (27/11/2026), validé expert + QC

## Acceptance criteria

- [x] API : `z` présent dans les images et la piste, au centimètre, égal à `BallSnapshot.z` / `BallPoint.z` arrondi (test) ; aucun autre champ changé
- [x] Poids de la réponse d'un match complet mesuré avant / après (graine fixée) ; hausse attendue au plus 10 % : 35 747 882 → 36 307 630 octets (+ 1,6 %)
- [x] Écran, fonctions pures testées sous `node --test` : z interpolé linéairement entre deux points de piste (point milieu = moyenne) ; z = 0 pour un ballon tenu ; jamais négatif ; rayon = 0,5 m à z = 0, 0,6 m à 4 m, 0,7 m au-delà de 8 m ; ombre 0,5 m et opacité 0,30 à z = 0, 0,25 m et 0,10 à 10 m et au-delà
- [x] `BALL_AIR_Z` et `BALL_AIR_R` supprimés ; ballon au sol inchangé à l'écran (z = 0 : même rayon 0,5 m, pas d'ombre)
- [x] Capture d'écran (Chromium sans affichage) d'un ballon en vol haut sur un vrai match : ballon remonté et agrandi, ombre au sol plus petite et plus pâle
- [x] Mêmes empreintes de trace sur deux exécutions à graine fixée (moteur inchangé)
- [x] `npm run build` OK, `npm run lint` sans nouvelle erreur, `npm test` vert ; suite complète au compte attendu ; V1 inchangée

## Comments

**27/11/2026, implémentation.**
- **Code** : `api/routers/v2.py` : champ `z` (m, `round(…, 2)`) dans `BallSnapshotOut` et `BallPointOut`. `ui/src/utils/v2Spline.js` : `ballFromTrack` rend `z`, linéaire entre les deux points de piste (coupure nette : z du point de départ ; jamais négatif), `displayBall` rend `z` (0 pour un ballon tenu ; 0 si la trace n'en porte pas). `ui/src/components/match/trace.js` : z des images, linéaire, pour le repli sans piste et le ballon qui entre dans le but. `ui/src/utils/v2BallHeight.js` (nouveau) : `ballRadius(z)`, `ballShadow(z)` (constantes du 02b, point 2 ; `BALL_R` déplacé ici depuis `V2Pitch`). `V2Pitch.jsx` : `BALL_AIR_R` et `BALL_AIR_Z` supprimés, ballon à `z`, ombre `data-ball-shadow` dès que z > 0 (avant : seulement en mode « aérien », taille et opacité fixes).
- **Tests** : `tests/test_v2engine_trace.py` : `test_ball_height_is_sent_to_the_screen_to_the_centimetre` (nouveau), z ajouté à la comparaison piste / images du pas et au dump exact de `test_ball_track_out_rounds_for_a_lighter_response`. `ui/src/utils/v2BallHeight.test.js` (nouveau, ajouté à `npm test`), `v2Spline.test.js` (3 tests de hauteur, deux comparaisons exactes de `displayBall` complétées par `z: 0`). `npm test` : 89 passés. Suite complète : **3 598 passés, 0 ignoré, 14 désélectionnés** (3 597 + 1). `npm run lint` : 0 erreur, 5 avertissements (inchangé) ; `npm run build` OK.
- **Mesures** (graine 20260923, `load_clubs` Ligue 1 [0] contre [1], match complet par `create_match`, scripts hors dépôt `poids_api.py`, `dump_trace.py`) : réponse 35 747 882 → 36 307 630 octets (+ 1,6 %), mêmes 11 640 images et 58 200 points de piste, même score (1-0). Déterminisme : deux exécutions après changement, même sha256 de la réponse (`31f96fa79fffd900`) ; moteur non modifié.
- **Captures** (Chromium sans affichage, banc hors dépôt : vraie trace, `interpolatedTick`, `V2Pitch`) : ballon le plus haut du match (minute 28,07, z 17,2 m) : rayon 0,7 m, ombre au sol rayon 0,25 m, opacité 0,10, 107 px (CSS, largeur 1 200 px) sous le ballon ; images : `mesures/02b1-haut-*.png`, `02b1-moyen-zoom.png`, `02b1-sol-zoom.png` ; scripts `02b1-poids-api.py`, `02b1-dump-trace.py`, résultats `02b1-poids.txt` ; minute 5,13 (z 4,6 m) : rayon 0,615 m, ombre 0,385 m, opacité 0,21 ; minute 10 (ballon tenu, z 0) : rayon 0,5 m, pas d'ombre. 842 points de piste au-dessus du sol sur le match.
- **Point à voir à l'écran (02b2)** : au-delà d'une dizaine de mètres, l'ombre (rayon 0,25 m, opacité 0,10) est à peine visible sur la pelouse ; c'est la constante du ticket, à juger par le propriétaire.
- **Durée** : estimée 2 h (20/45/30/25) ; réelle environ 2 h 10 (20/40/30/40), + 8 % ; intégration plus longue que prévu (banc de capture hors dépôt pour une vraie trace, deux mesures de poids).

**27/11/2026, clôture (`/valider-ticket-simulafoot`, passage 1).** Expert : APPROVED. QC : VALIDÉ. Clôture : VALIDÉ.
- A1 [facultatif] : pendant l'entrée dans le but (`trace.js`), z vient des images (0,5 s) et non de la piste ; écart possible de quelques dizaines de centimètres pendant 0,5 s. Reporté au 02b2 (avec l'ordre de dessin derrière la barre).
- A2 [facultatif] : ombre peu lisible à 10 m et au-delà (constante validée) ; à juger par le propriétaire au 02b2.
- Non rejoués par les relecteurs : `npm test`, lint, build (exécutés par la session, résultats ci-dessus).

**27/11/2026, clôture, passage 2.** La liste revue du passage 1 incluait les fichiers de suivi (`docs/`, `.scratch/`), exclus de la revue par le verrou : le passage du statut à « livré » changeait l'empreinte. Liste réduite aux 10 fichiers de code, inchangés depuis le passage 1 (l'expert a vérifié l'identité des hunks). Expert : APPROVED ; QC : VALIDÉ (inchangé) ; clôture : VALIDÉ.
