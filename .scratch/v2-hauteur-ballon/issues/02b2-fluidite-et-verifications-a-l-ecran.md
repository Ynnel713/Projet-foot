# 02b2: Hauteur du ballon à l'écran : fluidité, ordre de dessin et vérifications

**Découpé du ticket 02b le 27/11/2026** (décision du propriétaire : « 02b1 + 02b2 »). Reprend du `02b-hauteur-du-ballon-a-l-ecran.md` le critère de fluidité, l'ordre de dessin (point de vigilance et réserve A3 du ticket 01) et la liste « à vérifier à l'écran, hérité du 02a1 ».

**What to build:**
1. **Fluidité** : images par seconde mesurées, 30 s, même match et même vitesse, processeur ralenti 6 fois ; base `41e573e`, intermédiaire = état du ticket 01, final = état du 02b1/02b2 ; baisse de 10 % au plus entre la base et le final. **Décision du propriétaire du 27/11/2026** : mesure en Chromium sans affichage dans la session cloud, notée comme substitut de la mesure « sur navigateur visible » ; le propriétaire peut la refaire sur son poste.
2. **Ordre de dessin** ballon, buts, gardien (`V2Pitch.jsx`) : ballon qui passe derrière la barre ou dans le filet, gardien collé à sa ligne.
3. **Vérifications à l'écran** : liste du `02b` (chandelles, point de chute, rebonds, ballon intouchable au-dessus de 0,5 m, réceptions « centre », simplifications du 02a1), sur des actions repérées dans la trace ; vrai corner centré et vraie sortie de but longue ; opacité de l'ombre des joueurs à 375 px.

**Blocked by:** 02b1.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse 15 min, développement 25 min, tests et mesures 35 min, vérifications 15 min ; total 1 h 30 ; confiance faible (ordre de dessin : ampleur inconnue avant les captures). Temps machine à part : trois mesures de fluidité, suite complète.

**Status:** à faire

## Acceptance criteria

- [ ] Fluidité mesurée (substitut sans affichage, décision du 27/11/2026) aux trois états ; baisse ≤ 10 % entre la base et le final
- [ ] Ordre de dessin revu sur captures : ballon derrière la barre ou dans le filet, gardien sur sa ligne
- [ ] Vrai corner centré et vraie sortie de but longue : ballon aérien et ombre visibles, ballon au sol inchangé
- [ ] Liste « à vérifier à l'écran » du 02b passée en revue, chaque point avec sa capture ou son constat ; les points qui demandent l'œil du propriétaire sont listés pour lui
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur ; suite complète au compte attendu ; V1 inchangée

## Comments

**27/11/2026, repris de la clôture du 02b1 (remarques facultatives de l'expert).**
- A1 : pendant l'entrée dans le but (`ui/src/components/match/trace.js`, branche `scored`), z est interpolé sur les images (0,5 s) et non lu dans la piste (0,1 s) ; à examiner avec l'ordre de dessin du ballon derrière la barre.
- A2 : à 10 m et au-delà, l'ombre (rayon 0,25 m, opacité 0,10) se lit mal sur la pelouse (capture `mesures/02b1-haut-zoom.png`) ; à juger par le propriétaire, avec la lisibilité à 375 px.
- À mesurer : coût de l'ellipse d'ombre ajoutée à chaque image de ballon en l'air (fluidité).
