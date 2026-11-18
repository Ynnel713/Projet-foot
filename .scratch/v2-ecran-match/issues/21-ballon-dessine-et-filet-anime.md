# EM-21 — Ballon dessiné et filet animé sur un but (V) — 135 min (moyenne) → découpé en 21a et 21b — ajouté le 18/11/2026

**Status:** à faire (créé le 18/11/2026 à la demande du propriétaire ; découpé dès la création en 21a et 21b ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

**Origine :** question du propriétaire du 18/11/2026, après EM-07 (« le ballon ainsi que les filets sont-ils améliorables esthétiquement, notamment le mouvement des filets sur un but ? ») ; réponse : en partie prévu ailleurs (voir « Lien avec l'existant »), le reste n'est prévu nulle part ; décision : « Oui, crée-le de suite ».

- **Objectif** : un ballon qui ressemble à un ballon et dont on perçoit le roulement et la vitesse, et un filet qui réagit
  quand un but est marqué, sans attendre les tickets moteur.
- **Problème** : le ballon est un disque blanc à contour noir (`V2Pitch.jsx`, 0,5 m au sol depuis EM-07, 0,6 m en
  l'air) ; aucun signe de roulement ni de vitesse ; le filet (`GoalFrame`, polygones fixes et mémoïsés) ne bouge pas, y
  compris quand le ballon y entre.
- **Périmètre** : rendu seulement (`ui/src/components/match/V2Pitch.jsx`, `GoalFrame`, composant `BallMarker` à créer).
  Aucune donnée d'API nouvelle : la vitesse et la distance parcourue sont dérivées de la piste du ballon `ball_track`
  (un point toutes les 0,1 s, `trace.js`, ticket `v2-correctifs-ecran/04a`) ; le but vient de `trace.goals` (minute,
  équipe). Le résultat sportif n'est pas touché (habillage seulement).

## 21a — Ballon dessiné, roulement et traînée (75 min)

- **Résultat** :
  1. **Motif** : panneaux sombres et reflet léger, dans un seul `<defs>` partagé ; à 844×390 (rayon ≈ 2 px) le motif
     s'efface au profit du disque (à vérifier).
  2. **Roulement** : vue d'en haut, un ballon qui roule voit son motif **défiler dans le sens du déplacement** à
     l'intérieur du disque (translation du motif modulo sa période, découpée par le disque), et non tourner dans le plan
     de l'écran (une toupie serait fausse). Le décalage est calculé **depuis la piste jusqu'à l'instant lu** (distance
     cumulée sur `ball_track`), jamais accumulé image par image : même instant de lecture, même rendu, quel que soit le
     nombre d'images par seconde. Ballon immobile ou tenu par un joueur : pas de défilement.
  3. **Crénelage** : au-delà d'un déplacement par image supérieur à une demi-période du motif (≈ dès 20 m/s en x1,
     toujours en x8), le motif est figé (ou estompé) et la traînée porte seule la vitesse ; sinon le motif semblerait
     figé ou tournant à l'envers.
  4. **Traînée** : courte trace derrière le ballon au-delà d'un seuil de vitesse, longueur proportionnelle à la vitesse,
     plafonnée. **Jamais à travers une coupure** de trajectoire : ballon replacé au centre après un but, demi-tour de la
     mi-temps (`rotated`), ballon mort replacé (`dead`), ballon pris par un porteur ; réutiliser les coupures de
     `utils/v2Spline.js`.
- **Constantes à proposer avant le code** : motif (nombre et teinte des panneaux, reflet), période du motif, seuil de
  vitesse de la traînée (m/s), longueur maximale (m), seuil de figement du motif ; `prefers-reduced-motion` : pas de
  traînée.
- **Critères (à chiffrer à l'ouverture)** :
  - aucun défilement quand le ballon ne bouge pas ou est tenu ; sens du défilement égal au sens du déplacement (test node
    sur une passe enregistrée) ;
  - même rendu à un instant donné quel que soit le pas des images (test node : décalage du motif calculé pour un même
    instant avec deux pas d'images différents) ;
  - traînée absente sous le seuil, présente au-delà (frappe de la trace `em04`) ; **aucune traînée** sur un but, à la
    mi-temps ni sur une remise en jeu de la trace `em04` ;
  - fluidité ≥ EM-07 sur le banc d'EM-01 (médiane d'image ≤ 16,7 ms + 0,5 ms ; temps de script par image +15 % au plus) ;
  - 5 points de projection à 0 px (`em05-mesure.cjs`), aucun défilement de page ; build, lint, `npm test`.

## 21b — Filet qui ondule sur un but (60 min)

- **Résultat** : à l'instant du but lu dans la trace, le filet du but concerné ondule (déformation du toit et des filets
  latéraux par une enveloppe amortie), puis revient à sa forme. Animation décorative déclenchée par l'événement de la
  trace, pas un calcul physique : le creusement au point d'entrée réel, selon la vitesse du ballon, reste au ticket
  `v2-mise-en-scene/05`.
  - **But à animer** : celui **de la vue**, pas celui de l'équipe dans le repère du moteur. En 2e période la scène est
    retournée (`rotated`, `trace.js` ; `MatchScreen.jsx`) : le but visé par l'équipe à domicile est alors dessiné en
    x = 0. Le choisir par équipe et période, ou par la cible du ballon après rotation (`utils/v2GoalBall.js` vise
    x = L pour le domicile dans le repère du moteur).
  - **Base de temps** : le **temps de match lu** (`seconds`), pas le temps réel : rendu déterministe (même instant,
    même image), rejoué naturellement pendant le ralenti du but, jamais avant que la lecture n'atteigne le but (US-29).
    Conséquence assumée : l'ondulation est brève en x8 (1,5 s de match ≈ 0,19 s réelle).
  - **Durée** : ≤ 2 s de match (`REPLAY_AFTER_S` de `useMatchPlayback.js`), sinon le retour au ralenti la coupe.
  - `GoalFrame` est mémoïsé : ne lui passer une phase que pendant l'ondulation, pour garder le mémo le reste du temps.
- **Constantes à proposer avant le code** : amplitude, durée (≤ 2 s de match), amortissement ; `prefers-reduced-motion` :
  pas d'ondulation.
- **Critères (à chiffrer à l'ouverture)** :
  - ondulation du seul but concerné, **dans chaque période** (test node sur un but de chaque période), déclenchée à
    l'image du but (± une image), terminée dans la durée validée ; aucune ondulation sans but ni avant que la lecture
    n'atteigne le but ;
  - rendu déterministe (deux passes identiques au même instant) ; fluidité ≥ EM-07 ; build, lint, `npm test`.
- **À vérifier à l'écran** : sur téléphone, la cage fait 6×4 px tant qu'EM-20 n'est pas fait : l'ondulation y sera peu
  visible.

- **Dépendances** : EM-07 (livré). Indépendant d'EM-20 (lisibilité de la cage) : si EM-20 est fait d'abord,
  l'ondulation porte sur sa cage ombrée. **Risques** : coût de rendu de la traînée et du filet déformé (mesurer) ;
  ordre de dessin ballon, buts, gardien (point de vigilance du ticket `v2-hauteur-ballon/02b`).

## Lien avec l'existant

- `v2-mise-en-scene/05` (gestes visibles, à faire) : **filet qui se creuse au point d'entrée du ballon, selon sa vitesse**.
  Bloqué par `v2-realisme/04j`, `v2-realisme/03l` et `v2-hauteur-ballon/02b` (donc 02a). EM-21 n'en prend pas la place :
  il donne une réaction de filet décorative dès maintenant ; le 05 la remplacera par la vraie déformation au point d'entrée.
- `v2-hauteur-ballon/02b` (à faire, bloqué par 02a) : vraie hauteur du ballon à l'écran, taille et ombre selon la hauteur.
  EM-21 garde le ballon au sol / aérien d'aujourd'hui (0,5 / 0,6 m) ; ses motif, roulement et traînée s'appliqueront
  tels quels au ballon en hauteur.
- EM-20 (proposé, feu vert requis) : lisibilité de la cage (faces ombrées, épaisseur minimale), pas son mouvement.
- EM-07 (livré) : taille du ballon au sol 0,5 m, à conserver.

## Estimation

| Poste | 21a | 21b |
|---|---|---|
| Analyse | 10 min | 10 min |
| Développement | 30 min | 25 min |
| Tests (fonctions pures, captures, fluidité) | 20 min | 15 min |
| Intégration et vérifications | 15 min | 10 min |
| **Total (travail effectif)** | **75 min** | **60 min** |

Confiance : moyenne. Total 135 min (120 min à la première rédaction ; relevé après la revue de l'expert : défilement du
motif et anti-crénelage, coupures de trajectoire, choix du but par période). Hypothèses : la distance cumulée et la vitesse
se dérivent de `ball_track` (pas de 0,1 s) ; l'ondulation tient en une déformation des polygones de `GoalFrame` par une
enveloppe amortie, sans bibliothèque d'animation. Temps machine hors total : suite complète, passes de fluidité.

## Comments

- 18/11/2026, création, revue de l'expert (passage 1, `projet/em21-creation`) : APPROVED_WITH_RESERVATIONS. Réserves
  A1 à A5 intégrées ci-dessus avant tout code, à la place d'une acceptation en l'état : A1 but à animer en 2e période
  (scène retournée) ; A2 roulement en défilement du motif, calculé depuis la piste, et anti-crénelage ; A3 aucune
  traînée à travers une coupure ; A4 base de temps = temps de match lu, durée ≤ 2 s de match ; A5 pas de `ball_track`
  corrigé (0,1 s, et non 0,5 s). A6 (facultatif) : fichier réel cité (`V2Pitch.jsx`), mémo de `GoalFrame` préservé,
  compte des tickets du chantier corrigé dans `docs/PLAN_V2.md`. Découpage en 21a et 21b dès la création, sur sa
  recommandation.
