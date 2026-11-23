# 02b: Hauteur du ballon à l'écran

**Découpé du ticket 02 le 04/11/2026** (audit de granularité). Détail : `02-hauteur-du-ballon-moteur.md`, points 6 et 7.

**What to build:**
1. **Trace** (`v2engine/trace.py`, `api/serializers.py`, `api/schemas.py`) : pendant un vol, points `(x, y, z)` de chaque tick moteur (0,1 s) attachés à l'enregistrement d'une seconde.
2. **Écran** : le ballon est projeté avec sa vraie hauteur (projection du ticket 01) ; rayon × `1 + min(0,40 ; 0,05·z)` ; ombre au point `(x, y, 0)`, rayon × `max(0,5 ; 1 − 0,05·z)`, opacité de 0,30 au sol à 0,10 à 10 m. L'écran interpole entre les points de vol, sans calcul physique. Remplace l'affichage provisoire à hauteur fixe d'un mètre du ticket 01.
3. **Documentation** : `docs/PLAN_V2.md`, `docs/INDICATEURS_V2.md` si un indicateur change.

**Blocked by:** 01, 02a.

**Bloque :** aucun.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

Découpage proposé (02b1 rendu, 02b2 fluidité) refusé par le propriétaire le 23/11/2026 (« Un seul ticket »).

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (captures, poids de la trace, mesure de fluidité sur trois versions) | 70 min |
| **Total (travail effectif)** | **3 h** |

Confiance : moyenne. Hypothèses : les anciennes versions (`41e573e`, ticket 01) se lancent encore avec les dépendances actuelles. Temps machine, non compté : mesures de fluidité (3 versions × 30 s, plus construction), suite complète (environ 17 min).

**Constantes d'affichage** (étude `docs/ETUDE_HAUTEUR_V2.md` section 5, validées par le propriétaire le 23/11/2026, « Validées telles quelles ») : ballon × `1 + min(0,40 ; 0,05·z)` ; ombre au sol × `max(0,5 ; 1 − 0,05·z)` ; opacité de l'ombre de 0,30 au sol à 0,10 à 10 m (linéaire, puis constante). **Mesure de fluidité** : Chromium sans affichage de la session cloud, processeur ralenti 6 fois (choix du propriétaire du 23/11/2026, à la place d'un navigateur visible, limite notée).

**Critères chiffrés** (posés avant le code) : hauteur `z` sur chaque point de la piste et chaque image (API, test) ; écran : hauteur interpolée linéairement entre deux points de piste (test), constantes d'affichage (test) ; ballon dans le filet dessiné sous le filet, ballon en l'air devant le but dessiné par-dessus ; poids de la réponse d'un match mesuré avant/après (hausse attendue sous 10 %) ; images par seconde : baisse de 10 % au plus de `41e573e` à l'état final ; mêmes empreintes de trace sur deux exécutions ; `npm run build`, `npm run lint` (0 erreur), `npm test` ; suite complète au compte attendu.

## Acceptance criteria

- [x] Fluidité : images par seconde réelles mesurées, processeur ralenti 6 fois, 30 s, même match et même vitesse ; base = `41e573e`, intermédiaire = état du ticket 01, final = état du 02b — **mesurées dans Chromium sans affichage** (choix du propriétaire du 23/11/2026) ; **baisse de 10 % au plus non tenue (− 18 à − 22 % selon la série), due à des tickets d'écran antérieurs, pas au 02b** (47,8 → 49,0 images par seconde) : accepté par le propriétaire le 23/11/2026 (« Accepter, ticket de suite »), ticket `v2-ecran-match/22`
- [x] Points de vol présents dans la trace et sérialisés par l'API (test)
- [x] Poids de la trace par match mesuré avant/après
- [x] À l'écran, centres et dégagements montent et retombent ; ombre au sol cohérente avec la hauteur
- [x] Sur un vrai corner centré et une vraie sortie de but longue : ballon aérien et son ombre visibles, ballon au sol inchangé (**inclut le critère reporté du ticket 01**) ; ordre de dessin du ballon réellement en hauteur revu (réserve A3 de l'expert) ; opacité de l'ombre des joueurs revue à 375 px (gardée, voir Résultats)
- [x] Mêmes empreintes de trace sur deux exécutions à graine fixée
- [x] `npm run build` OK, `npm run lint` sans nouvelle erreur ; suite complète au compte attendu ; V1 inchangée

**Point de vigilance (reporté de la réouverture du ticket 01, 09/11/2026, demande du propriétaire)** : quand le ballon aura
sa vraie hauteur, revoir l'**ordre de dessin ballon, buts, gardien**. Aujourd'hui (`V2Pitch`), les buts sont dessinés
après les joueurs et le ballon après les buts : un ballon qui passe derrière la barre ou dans le filet, ou un gardien
collé à sa ligne (partie du rond côté filet vue à travers le filet semi-transparent), peut être dessiné dans le mauvais
ordre. Depuis le 09/11/2026 le but est une cage en volume (filets latéraux et toit à 2,44 m) et α = 35°.

## Résultats (23/11/2026)

- Code : `api/routers/v2.py` : `z` (hauteur au centimètre) sur chaque point de la piste (`BallPointOut`, un par pas de 0,1 s : la piste existait depuis `v2-correctifs-ecran/04a`, les « points de vol » du point 1 sont donc ces points) et sur le ballon de chaque image (`BallSnapshotOut`). Écran : `ui/src/utils/v2BallHeight.js` (constantes validées : grossissement, ombre, opacité) ; `v2Spline.ballFromTrack` / `displayBall` : hauteur en ligne droite entre deux points de piste, sans calcul physique, 0 au pied du porteur ou pour une piste sans hauteur ; `trace.js` : hauteur sur l'image, et dans un but entre deux images ; `V2Pitch` : ballon à sa vraie hauteur, rayon × `ballScale`, ombre au sol dès que le ballon quitte le sol ; le ballon aérien provisoire du ticket 01 (1 m, rayon 0,6 m) disparaît.
- **Ordre de dessin** (réserve A3 du 01, point de vigilance) : revu et gardé (ballon après les buts, joueurs avant). Constat : le ballon n'est jamais derrière une ligne de but dans la trace (le moteur le pose sur la ligne quand il sort ; un but entre deux images l'amène au centre de la ligne, `v2GoalBall.js`) : il est donc toujours devant le filet, au-dessus de la barre compris ; une règle « sous le filet » a été écrite puis retirée, faute de cas réel. Gardien collé à sa ligne : au plus près dans le match (1,32 m de sa ligne), son rond n'est pas recouvert par le filet (capture `02b-captures/gardien-ligne.png`).
- Tests : Python `tests/test_v2engine_trace.py` (hauteur sur l'image, sur chaque point de piste, arrondi au centimètre ; deux tests adaptés au nouveau champ) ; JS `v2BallHeight.test.js` (constantes) et `v2Spline.test.js` (interpolation de la hauteur, ballon tenu au sol, piste ancienne ; deux attendus complétés de `z`). `npm test` : 85 passés.
- Captures (`.scratch/v2-hauteur-ballon/mesures/02b-captures/`, match Auxerre – Monaco, graine 20261123) : corner de la 5e minute au départ (ballon au sol, ombre sous lui) et au sommet (5,5 m : ballon × 1,27, ombre × 0,73 à 0,19 d'opacité, 3,2 m sous le ballon à l'écran) ; sortie de but longue de la 61e au sommet (19,6 m : ballon au plafond × 1,4, ombre au plancher × 0,5 à 0,10, presque invisible) ; corner à 375 px. Ombre des joueurs à 375 px : discrète comme tout le terrain à cette taille, gardée (changement de constante non demandé). À noter : un ballon très haut près du bord lointain sort du cadre en haut (19,6 m sur la ligne de touche lointaine : environ 11 m au-dessus du bord) ; non corrigé (cadre de la vue, ticket d'écran).
- Poids de la trace d'un match (réponse complète de l'API, même match) : 35,9 Mo sans la hauteur, 36,5 Mo avec (+ 1,6 %).
- Fluidité (`.scratch/v2-hauteur-ballon/mesures/02b-fluidite.js` et `.txt`, build de production, API simulée, même trace, ×1, processeur ralenti 6 fois, lecture vérifiée en cours) : `41e573e` 59,5 ; ticket 01 (`f42dc68`) 58,5 ; 02b 46,2 (première série, trois lectures de 30 s alternées avec ces deux versions : 44,1, 45,9, 48,7 ; baisse de 22 % depuis la base) ; seconde série alternée avec la version juste avant le 02b : `b43d942` 47,8, 02b 49,0 (le 02b ne coûte rien). Recherche de la cause : `443e8c9` 59,3 ; EM-04 (`618c78c`) 55,4 ; EM-07 (`c057086`) 52,6 ; EM-21a (`6de4140`) 46,9. Décision du propriétaire : accepter, ticket `v2-ecran-match/22` créé. Limite : Chromium sans affichage, pas un navigateur visible.
- Déterminisme : deux enregistrements du même match (graine 20261123) donnent la même réponse, octet pour octet (sha256 `b80055356a73acf1…`).
- Suite complète : 3 619 passés, 0 ignoré, 14 désélectionnés (3 618 + 1) ; `npm run build` OK ; `npm run lint` 0 erreur, 5 avertissements (inchangés) ; V1 non touchée.
- Durée réelle : environ 1 h 25 (analyse 20, développement 25, tests 15, intégration et vérifications 25), − 53 % sur 3 h : la piste du ballon à chaque pas existait déjà (point 1 réduit à un champ), le rejeu de développement servait les captures, la mesure de fluidité a été automatisée en une fois (API simulée dans le navigateur) ; la recherche de cause de la baisse de fluidité (non prévue) est comprise. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : enregistrements (2 × 2 min), constructions et mesures de fluidité (environ 25 min), suite complète (16 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED (empreinte `b618c13c…`), aucune action obligatoire ; facultatifs A1 (ballon très haut près de la touche lointaine hors du cadre en haut : marge haute ou débordement du SVG, ticket d'écran), A2 (`docs/PLAN_V2.md` hors de la liste revue : suivi documentaire admis par le verrou). QC VALIDÉ (réserves non bloquantes : ballon hors cadre noté ; trois premières lectures du build final plus basses, 44,1 à 48,7, non reprises dans la synthèse : corrigé, deux séries citées). Clôture VALIDÉ. Critère de fluidité non tenu accepté par le propriétaire le 23/11/2026 (« Accepter, ticket de suite »), ticket `v2-ecran-match/22`.
