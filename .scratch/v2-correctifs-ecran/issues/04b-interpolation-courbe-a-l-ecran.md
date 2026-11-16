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

**Status:** à faire

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

- [ ] Test (`node --test`) : la spline passe exactement par les points de la piste ; pas de dépassement de plus de 0,3 m sur un virage de 90° à 15 m/s
- [ ] Test : coupure nette sur changement de porteur, remise en jeu et mi-temps (pas de glissade d'un point à l'autre)
- [ ] Mesure sur un match réel, rejouée à 10 im/s comme l'écran : virages de plus de 20° sans joueur à 2 m, ramenés de 94 sur 589 images (avant) à 10 au plus pour la même période ; sauts de vitesse x1,6 rapportés avant et après
- [ ] Ballon tenu : écart entre le ballon et son porteur à l'écran inférieur à 0,5 m
- [ ] `npm run build` OK ; `npm run lint` : 0 erreur, pas de nouvel avertissement ; `npm test` OK
- [ ] À vérifier à l'écran : passes, contrôles ratés, déviations, rejeu des buts au ralenti, vitesse x8
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite complète : compte comparé à l'attendu de `CLAUDE.md`
