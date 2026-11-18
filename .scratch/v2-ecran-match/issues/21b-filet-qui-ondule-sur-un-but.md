# EM-21b — Filet qui ondule sur un but (V) — 60 min (moyenne) — découpé d'EM-21 le 18/11/2026

**Status:** livré (18/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md`. Ticket chapeau : `21-ballon-dessine-et-filet-anime.md` (origine, périmètre
commun, lien avec l'existant, revue de la création par l'expert).

**Blocked by:** EM-07 (livré).

## Contenu (repris du ticket chapeau)

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

## Décision du propriétaire (18/11/2026)

« Valider tel quel » : au but lu dans la trace, le fond du filet concerné recule puis oscille,
d(t) = A · e^(−t/τ) · cos(2π·f·t), A = 0,8 m au milieu du fond (40 % de la profondeur de 2 m), 0,3 m aux coins ;
f = 2 Hz, τ = 0,5 s ; durée 2 s de match, sur le temps de match lu (rejouée au ralenti du but, brève en x8) ; toit et
filets latéraux suivent le fond, poteaux et barre fixes ; pas d'ondulation sous `prefers-reduced-motion`.

## Critères d'acceptation (chiffrés avant le code)

- [x] C1 : tests node (`ui/src/utils/v2NetWave.test.js`, 5 tests) : recul maximal (k = 1) à l'instant du but puis
  amorti (|k| ≤ e^(−t/τ), borne tirée de la constante) ; temps additionnel de la 1re période pendant un calcul en direct
  (début de 2e période encore inconnu) : filet de la 1re période ; rien avant le but ni après 2 s (borne testée à 1e-9 s près : le calcul
  en minutes n'est exact qu'à 1e-14 près en flottant) ; filet de la vue dans chaque période (domicile x = 105 en 1re,
  x = 0 en 2e ; extérieur l'inverse) ; deux buts rapprochés : le plus récent l'emporte.
- [x] C2 : toute la trace `em04` à pas de 0,02 s (`.scratch/v2-ecran-match/mesures/em21b-trace-entiere.mjs`, côté
  attendu recalculé indépendamment) : 311 976 instants, ondulation active 18 s = 9 buts × 2 s, 0 mauvais côté,
  0 but manqué, 0 ondulation hors fenêtre.
- [x] C3 : DOM (`em21b-dom.cjs`, `em21b-dom.json`) : 0,05 s après le but domicile de la 4e minute (1re période), le
  fond du filet de droite recule de 0,586 m au milieu et 0,22 m aux coins (A·k, k = 0,73), celui de gauche ne bouge
  pas ; 0,05 s après le but domicile de la 76e minute (2e période, scène retournée), c'est le filet de gauche ; les
  deux au repos 2,5 s après ; deux passes identiques. Recul maximal 2,8 m : le filet reste dans la marge de 3 m.
- [x] C4 : fluidité (`em21b-fluidite.txt`) : médiane 16,7 ms avant comme après, script +0,7 % (aucun but dans la
  fenêtre de 15 s : coût de l'ondulation non chronométré, un seul cadre de but recalculé pendant 2 s de match) ;
  5 points de projection à 0 px, aucun défilement (`em21b-points.json`) ; `npm test` 32/32, build OK, lint 0 erreur
  (5 avertissements préexistants) ; `npm test` 33/33 après le correctif du passage 1 ; suite pytest : voir clôture.

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 10 min |
| Développement | 25 min |
| Tests | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **60 min** |

Confiance : moyenne (hypothèses : voir le ticket chapeau). Temps machine hors total : suite complète, passes de fluidité.

## Comments

- 18/11/2026, implémentation. `ui/src/utils/v2NetWave.js` (fonction pure `netWave`, constantes validées) et ses tests ;
  `V2Pitch.jsx` : `GoalFrame` reçoit `mid` et `corner` (recul du fond, valeurs simples pour garder la mémoïsation au
  repos), toit en pentagone dont le milieu du fond recule davantage, prop `wave` et aide `bulge` ; `MatchScreen.jsx` :
  `netWave` sur le temps de match lu, désactivé sous `prefers-reduced-motion` (lu une fois) ; `package.json` : test
  ajouté au script `npm test`.
- 18/11/2026, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS. A1 [réserve] : pendant un calcul en direct, un but en
  temps additionnel de la 1re période pouvait faire onduler le filet opposé (`netWave` recevait `halfStart`, qui se
  replie sur 45 quand le début de 2e période est inconnu, alors que la scène n'est retournée qu'une fois ce début
  connu). Corrigé plutôt qu'accepté : `MatchScreen` passe `trace.second_half_start_minute ?? Infinity` (même prédicat
  que `clock`), test ajouté (but à la 46e minute sans début de 2e période connu : filet de la 1re période). A2
  [facultatif] : borne du test d'amortissement tirée de `WAVE_DECAY_S` (marge de 0,4 % auparavant). C2 et C3 refaits,
  identiques.
- 18/11/2026, passage 2, clôture : expert APPROVED (empreinte `6913e2d5`), aucune anomalie ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `v2-ecran-match/21b/cloture`).
  - QC, remarque non bloquante : `netWave` suppose `trace.goals` dans l'ordre chronologique (ordre fourni par le moteur), aucun test sur un tableau désordonné.
  - À surveiller (expert) : garder `netWave` aligné sur `clock` si une autre règle de période est introduite.
  - À vérifier à l'écran : ondulation peu visible sur téléphone (cage ≈ 6×4 px) tant qu'EM-20 n'est pas fait ; saut d'impact à x1 sur grand écran ; préférence « moins d'animations » lue une fois (recharger si elle change pendant le match).
- **Durée réelle** : environ 55 min de travail effectif (analyse 10, développement 15, tests et mesures 20, intégration 10 hors clôture), contre 60 min estimées : − 8 %. Le correctif de la réserve A1 (une ligne et un test) est compris. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : deux suites complètes (14 min 14, 13 min 38), une série de fluidité, passes DOM.
