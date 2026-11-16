# 04b: Interpolation courbe du ballon et des joueurs à l'écran

**Chantier :** `v2-correctifs-ecran` (audit du 16/11/2026, voir 04a). **Priorité :** P0 (immersion). **Catégorie :** affichage (moteur inchangé).

**Constat vérifié (16/11/2026) :** `interpolatedTick` (`ui/src/components/match/trace.js`) mélange linéairement deux images (`mix(u, v)`). Entre deux images, le ballon et les joueurs vont en ligne droite à vitesse constante, puis changent brusquement de direction et de vitesse sur l'image suivante (chiffres au 04a).

**What to build:**
1. **Ballon** : position lue dans `ball_track` (04a, un point toutes les 0,1 s), interpolée par une spline de **Catmull-Rom centripète** (alpha = 0,5) entre les deux points qui encadrent l'instant, avec les deux points voisins. La variante centripète ne fait pas de boucle ni de dépassement au contact (virage serré). La spline n'est pas appliquée à un instant où le ballon change de porteur, devient mort ou se fait replacer (remise en jeu, but, mi-temps) : à ce moment-là, saut net comme aujourd'hui.
2. **Joueurs** : même spline sur les ticks des joueurs (0,5 s après 04a), avec la même coupure à la mi-temps (déjà dans `interpolatedTick`) et sur les replacements de remise en jeu.
3. Le ballon tenu suit son porteur : position du porteur interpolée, pas la piste du ballon (pas de décalage entre le joueur et son ballon).
4. Le mode du ballon (sol ou aérien) et la règle du but (`v2GoalBall.js`) restent ceux d'aujourd'hui.
5. La lecture ralentie (x0,4, rejeu des buts) et la vitesse x8 restent fluides : coût de calcul par image mesuré.

**Hors de ce ticket :** piste du ballon (04a) ; physique du ballon (`v2-realisme/14a` à `14d`).

**Attributs :** aucun.

**Constantes validées par le propriétaire le 16/11/2026 (« je valide ») :** Catmull-Rom **centripète, alpha = 0,5** (directive du propriétaire : « Catmull-Rom ou Bézier » ; Catmull-Rom passe par les points réels du moteur, une courbe de Bézier ne passerait que près d'eux) ; coupure de la spline sur changement de porteur, ballon mort, remise en jeu, but et mi-temps.

**Blocked by:** 04a.

**Bloque :** aucun.

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (dont vérification à l'écran) | 30 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : fonction pure de spline ajoutée à côté de `interpolatedTick` et testée avec `node --test` (comme `teamColors.test.js`) ; pas de bibliothèque ajoutée ; captures d'écran par Playwright sur un match réel. Légèrement au-dessus du seuil de 2 h, mais le ticket est indivisible : la spline et ses coupures vont ensemble.
Temps machine, non compté : build et lint de l'UI ; suite complète.

## Acceptance criteria

- [x] Test (`node --test`) : la spline passe exactement par les points de la piste ; pas de dépassement de plus de 0,3 m sur un virage de 90° à 15 m/s
- [x] Test : coupure nette sur changement de porteur, remise en jeu et mi-temps (pas de glissade d'un point à l'autre)
- [x] Mesure sur un match réel, rejouée à 10 im/s comme l'écran : virages de plus de 20° sans joueur à 2 m, ramenés de 94 sur 589 images (avant) à 10 au plus pour la même période ; sauts de vitesse x1,6 rapportés avant et après
- [x] Ballon tenu : écart entre le ballon et son porteur à l'écran inférieur à 0,5 m
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, pas de nouvel avertissement ; `npm test` OK
- [ ] À vérifier à l'écran : passes, contrôles ratés, déviations, rejeu des buts au ralenti, vitesse x8
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Suite complète : compte comparé à l'attendu de `CLAUDE.md`

## Réalisation (16/11/2026)

**Périmètre élargi avant le code (annoncé, estimation 2 h 05 → 2 h 20) :** la piste du ballon (04a) ne disait pas quand le ballon est mort ; or le moteur le pose d'un coup au point de remise (sortie, but, coup franc). Champ `dead` ajouté à `BallPoint` (`v2engine/trace.py`), à `record_ball` (`v2engine/match.py`, même valeur que `BallSnapshot.dead`) et à `BallPointOut` (`api/routers/v2.py`). Moteur inchangé : seule la trace enregistrée s'enrichit.

- `ui/src/utils/v2Spline.js` (nouveau, fonctions pures) : `catmullRom` centripète (alpha 0,5, forme de Barry-Goldman ; écart de nœud jamais nul pour un ballon arrêté) ; `ballCut` (porteur qui change, ballon mort, mi-temps) ; `playersCut` (ballon mort d'un côté seulement : le moteur pose le preneur au point de remise ; mi-temps) ; `ballFromTrack` (piste à 0,1 s ; à une coupure : saut net pour un ballon mort ou la mi-temps, ligne droite sur un pas de 0,1 s au changement de porteur ; voisin au-delà d'une coupure remplacé par le point qu'il borde) ; `displayBall` (ballon tenu sur la position affichée de son porteur ; sans piste qui couvre l'instant, interpolation des images comme avant) ; `playersBetween` (courbe sur les images à 0,5 s, ligne droite à une coupure).
- `ui/src/components/match/trace.js` : `interpolatedTick` s'en sert. Inchangés : règle du but entre deux images (`v2GoalBall.js`, prioritaire), mode et ballon mort lus sur l'image de départ, cap du corps.
- `ui/src/utils/v2Spline.test.js` (5 tests `node --test`), branché sur `npm test`.

**Mesures (graine 20260923, clubs[0] contre clubs[1], 1re période rejouée à 10 im/s par `interpolatedTick` ; « avant » : la même trace à 1 image par seconde, sans piste, interpolation linéaire ; scripts hors dépôt `dump_04b.py` et `m/measure.mjs`) :**

| | Avant | Après |
|---|---|---|
| Virages de plus de 20° du ballon libre en mouvement, sans joueur à 2 m | 69 | **6** |
| Sauts de vitesse x1,6 entre deux images consécutives | 278 | 191 |
| dont sans joueur à 2 m | 198 | 34 |
| Écart maximal entre le ballon tenu et son porteur | 0 m | 0 m |
| Coût de `interpolatedTick` par image | 10 µs | 8 µs |

Le décompte « avant » (69) diffère des 94 du constat : ici, images à 10 im/s, ballon libre à plus de 0,5 m/s sur deux images consécutives. Les sauts de vitesse qui restent ont lieu surtout au contact d'un joueur (passe qui part, contrôle, contre) : ce sont ceux du moteur. Tests : dépassement dans un virage de 90° à 15 m/s inférieur à 0,3 m ; la courbe passe exactement par les points.

**Vérifications :** `npm test` 18/18 ; `npm run build` OK ; `npm run lint` 0 erreur, 5 avertissements (inchangé) ; tests V2 ciblés 154 passés. Essai Playwright sur un vrai match en rejeu direct : démarrage, lecture x1 puis x8 à 60 images par seconde, aucune erreur de console ; ballon tenu dessiné sur son porteur.

**À vérifier à l'écran par le propriétaire :** passes, contrôles ratés, déviations, rejeu des buts au ralenti, vitesse x8.

**Durée :** estimée 2 h 05, réestimée 2 h 20 avant le code (champ `dead` de la piste) ; réelle environ 30 min de travail effectif (analyse 8, développement 10, tests 5, intégration et vérifications 7), à l'horloge de la session, non chronométrée ; écart − 79 %. Cause : la courbe et ses coupures tiennent dans un module de fonctions pures testé directement par `node --test`, sans adapter les composants d'écran ; la mesure a réutilisé la trace et la méthode du 04a ; l'estimation prévoyait des captures et réglages à l'écran plus longs. Temps machine hors total : un match de 90 min (trace de mesure), suite complète 12 min 34, essai Playwright (environ 2 min).

## Comments

- **16/11/2026, passage 1** — Expert : `APPROVED_WITH_RESERVATIONS`. QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ` (réserves acceptées par le propriétaire). Anomalies bloquantes : aucune.
  - Réserve A1 (joueurs : ligne droite sur 0,5 s à une remise en jeu, au lieu d'une coupure nette ; un preneur posé au point de remise peut glisser, et sur un coup franc le ballon le suit) : **acceptée par le propriétaire** (« Accepter A1 (Recommandé) » : clôture maintenant, coups francs ajoutés aux vérifications à l'écran, petit ticket de suivi si la glissade se voit).
  - A2 facultatif : la mesure échantillonne sur les points de la piste ; une variante à 60 im/s quantifierait les sauts affichés entre deux points.
  - A3 facultatif : `"dead":false` ajoute environ 0,7 Mo de JSON par match (option : `exclude_defaults`).
  - Réserves non bloquantes du QC : scripts de mesure hors dépôt ; ligne droite de 0,1 s au changement de porteur (documentée).
  - À surveiller à l'écran (expert) : départ des tirs (saut de moins d'un mètre, `CONTROL_RADIUS_M`), coups francs et remises en jeu.
