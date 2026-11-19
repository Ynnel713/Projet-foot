# EM-21a — Ballon dessiné, roulement et traînée (V) — 75 min (moyenne) — découpé d'EM-21 le 18/11/2026

**Status:** livré (18/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md`. Ticket chapeau : `21-ballon-dessine-et-filet-anime.md` (origine, périmètre
commun, lien avec l'existant, revue de la création par l'expert).

**Blocked by:** EM-07 (livré).

## Contenu (repris du ticket chapeau)

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

## Décision du propriétaire (18/11/2026)

« Valider tel quel » : panneaux pentagonaux `#1C2128`, un par carreau de 0,5 m (échelle du ballon dessiné), reflet blanc
léger fixe en haut à gauche, contour noir inchangé ; roulement : le motif glisse dans le sens du déplacement de la distance
parcourue, arrêté si le ballon est tenu ou mort ; motif figé quand vitesse × vitesse de lecture ≥ 15 m/s ; traînée au-delà
de 18 m/s de match, longueur = chemin des 0,1 s précédentes, plafonnée à 3 m et à la dernière coupure, triangle blanc de
30 % à 0, masquée par `prefers-reduced-motion`. Mesure à l'appui de la proposition (trace `em04`, 17 204 pas de ballon
libre) : médiane 10,5 m/s ; au-dessus de 15 m/s 18,7 % du temps libre, de 18 m/s 8,6 %, de 25 m/s 1,7 % ; max 30,2 m/s.

**Décision du propriétaire du 18/11/2026, après le rejet de l'expert (passage 1)** : « Motif lié à la position » : le
motif est accroché à la position affichée du ballon (roulement continu partout, virages, réceptions et dribble compris) ;
le ballon tenu roule avec le dribble (remplace « arrêté quand le ballon est tenu ») ; ballon mort immobile donc motif
immobile ; seul saut restant au passage du seuil de figement (15 m/s × vitesse de lecture), masqué par la vitesse et la
traînée. Estimation de 21a révisée de 75 à 100 min avant de reprendre le code.

## Critères d'acceptation (chiffrés avant le code ; roulement révisé après le passage 1)

- [x] C1 : tests node des fonctions pures (`ui/src/utils/v2BallLook.test.js`, 10 tests) : ballon tenu ou mort sans
  traînée ; **roulement continu** : d'une image à la suivante (60 im/s), le décalage du motif avance exactement du
  déplacement projeté du ballon, en diagonale (0,6 ; 0,8) à 8 m/s, à travers une déviation et une réception, sans saut
  au passage du carreau ; le motif avance dans le sens du déplacement ; vitesse lue sur la piste ballon tenu compris,
  nulle sur un ballon mort ou à une coupure ; même instant, même résultat (aucun état) ; figement selon vitesse × vitesse
  de lecture ; traînée nulle sous 18 m/s, vitesse × 0,1 s au-delà, plafonnée à 3 m et à la distance depuis la coupure ;
  distance remise à zéro après un changement de porteur et à la mi-temps.
- [x] C1 bis (contrôle demandé par l'expert) : décalage du motif lu dans le DOM sur un ballon lent en diagonale, à
  30 images consécutives (1/60 s de match), 3,4 m parcourus, 8 passages de carreau et une réception : écart nul entre
  l'avancée du motif et celle du ballon (`em21a-continuite-dom.cjs`).
- [x] C2 : toute la trace `em04` à pas de 0,02 s (`.scratch/v2-ecran-match/mesures/em21a-trace-entiere.mjs`) : 311 995
  instants, 0 traînée au-delà d'une coupure, 0 dépassement juste après les 1 295 coupures suivies d'un ballon libre ;
  traînée sur 8,6 % du temps de ballon libre (attendu 8,6 %), longueur maximale 3 m.
- [x] C3 : fluidité (banc d'EM-01, build de production, x8, 3 passes alternées de 15 s, `em21a-fluidite.txt`) :
  médiane d'image 16,7 ms avant comme après ; script 1,04 → 1,01 ms par image (−2,9 %, dans le bruit ; passage 1 :
  +5,9 %), seuil +15 % ; 305 → 318 nœuds SVG.
- [x] C4 : 5 points de projection à 0 px, aucun défilement aux 5 tailles (`em21a-points.json`) ; `npm test` 28/28 ;
  build OK ; lint 0 erreur (5 avertissements préexistants) ; suite pytest : voir clôture.
- [x] Téléphone (remarque A3 de l'expert) : à 844×390 le ballon fait 2,2 px de rayon (`em21a-telephone.cjs`) ; le motif s'y fond en un disque clair grisé, sans panneau discernable (attendu, capture hors dépôt).
- [x] Déterminisme du rendu : deux passes de captures (ballon rapide x1, lent x1 à deux instants, lent x8) identiques à
  l'octet (`em21a-captures.cjs`) ; décalage du motif mesuré dans le DOM : il change entre deux instants rapprochés en x1,
  reste au centre du ballon (figé) en x8 et sur le ballon rapide.

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 10 min |
| Développement | 30 min |
| Tests | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **75 min** (révisé à 100 min le 18/11/2026 après le rejet de l'expert) |

Confiance : moyenne (hypothèses : voir le ticket chapeau). Temps machine hors total : suite complète, passes de fluidité.

## Comments

- 18/11/2026, implémentation. `ui/src/utils/v2BallLook.js` (fonctions pures `ballMotion`, `panelShift`, `trailLength`,
  constantes validées) et ses tests ; `ui/src/components/match/BallMarker.jsx` (disque, motif en `<pattern>` translaté
  par `patternTransform`, reflet, traînée en triangle à dégradé) ; `V2Pitch.jsx` reçoit `ballLook` et dessine `BallMarker`
  à la place du cercle ; `MatchScreen.jsx` calcule le mouvement dans le repère du moteur et le retourne en 2e période ;
  `index.css` masque la traînée sous `prefers-reduced-motion` ; `package.json` : test ajouté au script `npm test`.
  Découpage d'EM-21 matérialisé en deux fichiers (21a, 21b), le 21 devenant ticket chapeau.
- 18/11/2026, passage 1 de l'expert : **REJECTED**. A1 [bloquant] : le décalage du motif était réduit modulo 0,5 m le
  long de la direction ; le motif se répétant en x et en y de l'écran, le motif sautait de 0,3 à 0,45 m à chaque
  passage du carreau hors de l'axe x (16 fois par seconde à 8 m/s), invisible aux tests, tous selon l'axe x. A2
  [facultatif] : contrôle C2 en partie tautologique (la garantie réelle est la boucle de `ballMotion`, correcte). A3
  [facultatif] : effacement du motif en 844×390 non documenté. Correctif : d'abord le vecteur de déplacement depuis la
  coupure ; le contrôle DOM demandé a alors montré un second saut (motif « arrêté » ramené au repos à chaque réception
  et relance, écart de 0,12 m) ; décision du propriétaire « Motif lié à la position » ; motif accroché à la position
  affichée (`patternOffset(ground, speed, playbackSpeed)`), vitesse lue sur la piste ballon tenu compris (`ballSpeed`).
  Tests du roulement réécrits (diagonale, déviation, réception), contrôle DOM à écart nul.
- 18/11/2026, passage 2, clôture : expert APPROVED (empreinte `9a10e262`) ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `v2-ecran-match/21a/cloture`). Le premier lancement du passage 2 avait échoué sur une limite d'usage de l'API (aucun verdict), relancé à l'identique après la reprise de la session.
  - A1 [facultatif] : le seuil de figement suppose 60 images/s ; sur un écran à 30 Hz, le motif peut sembler se figer ou tourner à l'envers dès 7,5 m/s ; un seuil selon la durée d'image mesurée demanderait une nouvelle décision du propriétaire.
  - A2 [facultatif] : bascule figé/libre au plus toutes les 0,1 s autour de 15 m/s ; une hystérésis (14 et 16 m/s) l'éliminerait si on l'observe.
  - A3 [facultatif] : identifiants fixes `v2-ball-panels`, `v2-ball-shine`, `v2-ball-trail` (collision si deux terrains V2 coexistaient sur une page, pas le cas aujourd'hui).
  - À vérifier à l'écran : le saut au seuil de figement ; le motif sur un appareil à faible fréquence d'image.
- **Durée réelle** : environ 105 min de travail effectif (analyse 15, développement 35, tests et mesures 45, intégration 10 hors clôture), contre 75 min estimées (100 après révision) : + 40 % par rapport à l'estimation initiale. Cause : rejet de l'expert au passage 1 (décalage du motif réduit le long de la direction, saut hors de l'axe x, invisible aux tests axiaux) ; le correctif a révélé un second saut à la réception, d'où une décision du propriétaire, une seconde réécriture du roulement et de ses tests, et une seconde série de mesures. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : trois suites complètes (14 min 07, interrompue, 14 min 42), deux séries de fluidité, quatre passes de captures.
