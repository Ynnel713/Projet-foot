# Chantier « mise en scène » du match V2

**Origine (03/11/2026) :** demande du propriétaire, discutée point par point (décisions Q19 à Q29) : plusieurs modes de visionnage, des célébrations variées après un but, des échauffourées.

## Constat (vérifié le 03/11/2026)

- Le V2 n'a qu'un lecteur continu (`ui/src/routes/V2Match.jsx`) : vitesses ×1 à ×16, pause, score révélé au moment du but. Ni saut dans le temps, ni barre de progression, ni mode de visionnage.
- Le V1 a des « temps forts » (buts et occasions tirées au sort) mais son animation et son bouton LIVE sont masqués (`ui/src/config/features.js`, `LIVE_AND_ANIMATION_ENABLED = false`). Le V1 reste gelé : ses tickets de temps forts, y compris `celebration-but/01`, ne sont ni repris ni supprimés.
- Aucune célébration ni échauffourée n'existe, ni en V1 ni en V2.
- La trace V2 (`v2engine/trace.py`) ne contient ni buteur, ni issue des tirs, ni fautes, ni cartons, ni corners. L'API renvoie tout le match d'un coup (`POST /api/v2/matches`).

## Décisions

- **V2 uniquement.** Le moteur produit de vrais moments ; le V1 rejoue un résultat décidé à l'avance.
- **Quatre modes** : Match complet (existant), **Résumé** (environ 10 minutes, 8 à 12 selon l'intérêt du match, avec tout ce qui vaut d'être montré), **Moments clés** (uniquement grosses occasions, buts et cartons rouges), **Buts** (uniquement les buts).
- **Grosse occasion = situation jugée dangereuse**, indépendante de la conclusion : pic de danger au-dessus d'un seuil (définition du ticket `v2-collectif/28`). Elle inclut le centre qui traverse tout le monde jusqu'au joueur du second poteau à deux doigts de pousser le ballon au fond, et le face-à-face conclu par un tacle salvateur.
- **Sans spoiler** dans tous les modes : aucun score ni repère de moment futur avant que le moment soit joué.
- **Le serveur découpe** : la liste des moments (début, fin, type, score d'intérêt, issue) est calculée côté API, une seule fois, avec la trace. L'écran lit les plages. Un seul calcul sert aux trois modes, aux tests et à la relecture.
- **Célébrations et échauffourées sont des comportements du moteur** pendant le ballon mort (ticket `v2-collectif/29`) : des intentions de joueurs affichées par le rendu existant, avec étiquette. Les échauffourées sont au ticket `v2-attributs-restants/09` (discipline).
- **Règle de diversité** (`docs/PLAN_V2.md`) : la variété naît de la situation et des notes des joueurs, jamais d'un tirage dans une liste.

## Tickets

| # | Titre | Bloqué par |
|---|---|---|
| 01 | Buts et lecteur | — |
| 02 | Moments clés | v2-collectif/28 (cartons rouges : v2-attributs-restants/09, ajoutés à leur livraison) |
| 03 | Résumé | v2-collectif/28, 29, 30, 31 ; 04 en option |
| 04 | Célébrations | v2-collectif/29 ; 01 (buteur dans la trace) |

Le chantier n'a pas à précéder la calibration (`v2-collectif/22`) : il ne change pas le nombre ni la forme des actions, sauf le temps mort des célébrations, compté dans le temps additionnel. Il peut avancer en parallèle d'une autre session.
