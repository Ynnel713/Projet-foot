# EM-21b — Filet qui ondule sur un but (V) — 60 min (moyenne) — découpé d'EM-21 le 18/11/2026

**Status:** à faire (constantes à proposer avant le code)

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
