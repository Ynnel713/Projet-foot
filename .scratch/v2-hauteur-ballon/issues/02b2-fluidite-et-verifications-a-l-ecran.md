# 02b2: Hauteur du ballon à l'écran : fluidité, ordre de dessin et vérifications

**Découpé du ticket 02b le 27/11/2026** (décision du propriétaire : « 02b1 + 02b2 »). Reprend du `02b-hauteur-du-ballon-a-l-ecran.md` le critère de fluidité, l'ordre de dessin (point de vigilance et réserve A3 du ticket 01) et la liste « à vérifier à l'écran, hérité du 02a1 ».

**What to build:**
1. **Fluidité** : images par seconde mesurées, 30 s, même match et même vitesse, processeur ralenti 6 fois ; base `41e573e`, intermédiaire = état du ticket 01, final = état du 02b1/02b2 ; baisse de 10 % au plus entre la base et le final. **Décision du propriétaire du 27/11/2026** : mesure en Chromium sans affichage dans la session cloud, notée comme substitut de la mesure « sur navigateur visible » ; le propriétaire peut la refaire sur son poste.
2. **Ordre de dessin** ballon, buts, gardien (`V2Pitch.jsx`) : ballon qui passe derrière la barre ou dans le filet, gardien collé à sa ligne.
3. **Vérifications à l'écran** : liste du `02b` (chandelles, point de chute, rebonds, ballon intouchable au-dessus de 0,5 m, réceptions « centre », simplifications du 02a1), sur des actions repérées dans la trace ; vrai corner centré et vraie sortie de but longue ; opacité de l'ombre des joueurs à 375 px.

**Blocked by:** 02b1.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse 15 min, développement 25 min, tests et mesures 35 min, vérifications 15 min ; total 1 h 30 ; confiance faible (ordre de dessin : ampleur inconnue avant les captures). Temps machine à part : trois mesures de fluidité, suite complète.

**Status:** livré (27/11/2026), validé expert + QC (critère de fluidité non tenu, perte antérieure au 02b, accepté par le propriétaire : ticket `v2-ecran-match/22`)

## Acceptance criteria

- [ ] Fluidité mesurée (substitut sans affichage, décision du 27/11/2026) aux trois états ; baisse ≤ 10 % entre la base et le final : **non tenu** (59,9 → 47,3 images/s, − 21 %) ; perte antérieure au 02b (avant le 02b : 45,9 ; le 02b ne coûte rien de mesurable) ; **décision du propriétaire du 27/11/2026 (« ok »)** : clôture avec ce critère non tenu, cause recherchée au ticket neuf `v2-ecran-match/22`
- [x] Ordre de dessin revu sur captures : ballon derrière la barre ou dans le filet, gardien sur sa ligne
- [x] Vrai corner centré et vraie sortie de but longue : ballon aérien et ombre visibles, ballon au sol inchangé
- [x] Liste « à vérifier à l'écran » du 02b passée en revue, chaque point avec sa capture ou son constat ; les points qui demandent l'œil du propriétaire sont listés pour lui
- [x] `npm run build` OK, `npm run lint` sans nouvelle erreur ; suite complète au compte attendu ; V1 inchangée

## Comments

**27/11/2026, repris de la clôture du 02b1 (remarques facultatives de l'expert).**
- A1 : pendant l'entrée dans le but (`ui/src/components/match/trace.js`, branche `scored`), z est interpolé sur les images (0,5 s) et non lu dans la piste (0,1 s) ; à examiner avec l'ordre de dessin du ballon derrière la barre.
- A2 : à 10 m et au-delà, l'ombre (rayon 0,25 m, opacité 0,10) se lit mal sur la pelouse (capture `mesures/02b1-haut-zoom.png`) ; à juger par le propriétaire, avec la lisibilité à 375 px.
- À mesurer : coût de l'ellipse d'ombre ajoutée à chaque image de ballon en l'air (fluidité).

**27/11/2026, implémentation.**
- **Fluidité** (Chromium sans affichage, processeur ralenti 6 fois par CDP, vitesse ×1, images comptées par `requestAnimationFrame` sur 30 s après 10 s de lecture ; même match pour tous les états : réponses d'API figées et interceptées, graine 20260923, AEK Athens - Al-Ahli SFC, 12 240 images ; builds de production servis par `vite preview` ; scripts `mesures/02b2-fps.js`, `02b2-fixture-fps.py`, résultats `02b2-fps-resultats.jsonl`) : base `41e573e` 59,9 ; ticket 01 `f42dc68` 59,9 ; avant le 02b `1923ec0` 45,9 (4 passages alternés : 46,0, 46,2, 43,9, 47,6) ; final 47,3 (46,2, 49,2, 46,8, 47,1). Lots : un premier lot de 3 passages par état (base 59,9 ; ticket 01 59,9 ; avant le 02b 48,5 : 53,2, 46,3, 46,0 ; final 46,4), puis, pour départager avant le 02b et le final, 4 passages alternés de chacun (valeurs retenues ci-dessus, la dispersion du premier lot, dont un 53,2 isolé, ne permettant pas de conclure). La base plafonne à 60 images/s (cadence de l'écran) : − 21 % est une borne basse de la perte réelle. Le 02b (02b1 + 02b2) ne coûte rien de mesurable ; la perte de 21 % est antérieure (entre `f42dc68` et `1923ec0`) : ticket neuf `v2-ecran-match/22`.
- **Ordre de dessin** (`ui/src/utils/v2DrawOrder.js`, nouveau, testé ; `V2Pitch.jsx`) : la caméra ne tourne qu'autour de x, la profondeur est y et z. Ballon derrière une ligne de but et sous le toit : dessiné entre les parties du but qui sont derrière lui et celles qui le couvrent (cadre, toit s'il est entre les poteaux, filet latéral de devant s'il est derrière lui, filet du fond s'il est au-delà) ; ailleurs, par-dessus tout, comme avant. Joueurs : ceux entrés dans un filet (derrière une ligne de but) sous les buts, les autres par-dessus (le rond d'un gardien collé à sa ligne n'est plus vu à travers le filet). `GoalFrame` dessine ses parties à la demande (deux passes autour d'un ballon dans le but).
- **A1 de l'expert au 02b1** (`trace.js`) : ballon qui entre dans le but, hauteur lue dans la piste (0,1 s) plutôt qu'entre les images (0,5 s).
- **Vérifications à l'écran** (banc hors dépôt : vraie trace, `interpolatedTick`, `V2Pitch` ; graine 20260923, Ligue 1 [0] contre [1] ; captures `mesures/02b2-*.png`, profils `02b2-vols.txt`, prises `02b2-prises.txt`) :
  - corner centré (minute 59,08) : sommet 7,96 m, ballon et ombre visibles (`corner-sommet`, `corner-descente`) ; autre corner (91,59) : sommet 14,6 m, haut pour un corner (point de réalisme moteur, pas d'écran) ;
  - sortie de but longue (28,04) : sommet 17,2 m (`degagement-haut`) ; aucun ballon du match au-dessus de 17,23 m (le plafond de 24,8 m du 02a1 n'est plus atteint) ;
  - rebonds : sommets successifs 7,96 → 3,89 → 1,90 → 0,94 → 0,45 m (rapport 0,49) après le corner ; 7,31 → 3,58 → 1,74 → 0,86 → 0,42 → 0,20 m après la sortie de but de la minute 53,56 ; visibles (`rebond-1`, `rebond-3`) ; après le dégagement de la minute 28,04 : 17,23 → 8,44 → 2,95 m (troisième sommet plus bas que 0,49, à relire au moteur) ;
  - ballon touché au-dessus de 0,5 m : 1 prise de balle libre sur 1 405 (minute 37,135, ballon qui remonte après un rebond, 0,43 → 0,77 → 1,01 m, pris à 1,01 m) : écart à la règle provisoire du 02a1, côté moteur, signalé au `02c`/`03` ;
  - ballon dans le but (49,23) : barre, toit et filet de devant dessinés par-dessus le ballon (`but-filet`, refaite au passage 2 : au passage 1, le constat « derrière le cadre » était faux, voir clôture) ; gardien collé à sa ligne (63,48) : rond entier par-dessus le filet (`gardien-ligne-terrain`) ;
  - 375 px (`tel-corner`, `tel-degagement`) : ballon à 8 m de 2,5 px, ombre invisible ; **décision du propriétaire du 27/11/2026** : constantes de l'ombre gardées ;
  - non vérifiés ici, à l'œil du propriétaire sur l'écran réel : point de chute d'une passe aérienne sur sa cible, réceptions « centre » (ticket `02c` en cours sur une autre branche), simplifications A4 du 02a1 (ballon touchable dans ses premières centièmes de seconde, tick de porteur avec un ballon en hauteur) ; opacité de l'ombre des joueurs à 375 px (lisible sur les captures).
- **Tests** (passage 1 ; après correction, voir la clôture ci-dessous : 8 tests, `npm test` 97 passés) : `ui/src/utils/v2DrawOrder.test.js` (5 tests, ajouté à `npm test`) ; `npm test` 94 passés ; lint 0 erreur, 5 avertissements ; build OK. Aucun fichier Python modifié.

**27/11/2026, clôture, passage 1 (`/valider-ticket-simulafoot`).** Expert : REJECTED. Pas de QC (le rejet de l'expert suffit à refuser).
- A1 [bloquant] : pendant un but, `v2GoalBall.js` pose le ballon exactement sur la ligne (x = 0 ou L) ; le test strict « derrière la ligne » le laissait devant, donc par-dessus la barre, comme avant le ticket ; le critère d'ordre de dessin était coché sur un constat de capture faux (ma lecture de `but-filet`). Corrigé : pour le ballon, « sur ou derrière la ligne » (`behindGoalLine(..., onLine)`), test unitaire x = ligne de but, capture refaite.
- A2 [facultatif] : ballon derrière la ligne juste au-delà du poteau lointain, couvert par le toit en vraie géométrie. Corrigé : le toit couvre le ballon si son point projeté sur lui, y + (barre − z)·tan 35°, est entre les poteaux (testé).
- A3 [facultatif] : joueur derrière la ligne, sorti côté caméra (au-delà du poteau proche), dessiné sous le filet de devant. Corrigé : `playerUnderGoal` (testé).
- A4 [facultatif] : branche `scored` de `trace.js` sans test unitaire (`trace.js` importe `pitchGeometry.json`, non chargé par `node --test` sans attribut d'import). Non traité ; couvert par la capture `but-filet`.
- Mesures de fluidité : lots retenus précisés (ci-dessus).
- Après correction : `npm test` 97 passés, lint 0 erreur (5 avertissements), build OK.

**27/11/2026, clôture, passage 2.** Expert : APPROVED (A1 à A3 corrigées et testées ; capture du but conforme). QC : VALIDÉ. Clôture : VALIDÉ.
- Remarques facultatives restantes : ballon sur ou derrière une ligne et sous 2,44 m dessiné avant les joueurs du terrain (cas rare, ballon hors jeu ; tri par profondeur y·sin + z·cos si cela se voit) ; ballon sur la ligne hors des poteaux sous le cadre (effet négligeable) ; A4 (test de la branche `scored` de `trace.js`).
- À suivre côté moteur (`02c`, `03`) : prise de balle à 1,01 m (minute 37,135), troisième rebond du dégagement de la minute 28,04.
- **Durée** : estimée 1 h 30 (15/25/35/15) ; réelle environ 2 h 45 (20/40/75/30), + 83 %. Écart > 30 % : la mesure de fluidité a révélé une régression antérieure, qu'il a fallu situer (deux états mesurés en plus, passages alternés), et le rejet de l'expert au passage 1 (ballon de but sur la ligne) a demandé une correction, des tests et une capture de plus.
