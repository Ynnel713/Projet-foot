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
| 04 | Célébrations | v2-collectif/29 ; 01 (buteur dans la trace ; depuis le 26/11/2026 : 01e, voir la révision ci-dessous) |

Le chantier n'a pas à précéder la calibration (`v2-collectif/22`) : il ne change pas le nombre ni la forme des actions, sauf le temps mort des célébrations, compté dans le temps additionnel. Il peut avancer en parallèle d'une autre session.

## Révision du 26/11/2026 (audit du mode « moments clés », décisions du propriétaire)

- **Filtre de lecture** : les modes lisent la trace déjà produite ; aucune seconde simulation, aucun snapshot ni rejeu (la trace contient toutes les images et la piste du ballon). Moteur inchangé, sauf l'exception accordée au `01a` (instrumentation en lecture seule de `occasion.py`, jeu inchangé, seule la trace change).
- **Modes et durées à ×1** : Résumé (« Temps forts ») 10 à 15 minutes, remplace 8 à 12 ; Moments clés : Tier 1 seulement, environ 5 à 7 minutes ; Buts.
- **Trois tiers** : Tier 1 toujours (buts, penalties, grosses occasions ; cartons rouges et VAR à la livraison de `v2-attributs-restants/09a`, `v2-realisme/21g`, `21h`) ; Tier 2 sous budget (tirs dangereux, arrêts décisifs, coups francs directs cadrés, belles constructions, poteaux ; la contre-attaque est un modificateur du score, pas un type) ; Tier 3 en surimpression seulement (fautes, corners, hors-jeu, puis cartons jaunes et remplacements).
- **Calcul côté serveur**, en fin de calcul du match ; l'écran ne fait que lire. Vitesses existantes (×1, ×1,5, ×2, ×8, ×32) conservées.
- **Validation en deux passages** : `07a`, puis `07b` après la calibration (`v2-collectif/22c`).

| # | Titre | Bloqué par | Estimation |
|---|---|---|---|
| 01 | Buts et lecteur | découpé en 01a à 01g | — |
| 01a | Séquences d'occasion fiables (réserves 28c A1, A2) | — | 1 h 30 |
| 01b | Taxonomie et score d'intérêt | 01a | 1 h 45 |
| 01c | Fenêtres des moments | 01b | 1 h 45 |
| 01d | Sélection sous budget, mode Buts | 01c | 1 h 15 |
| 01e | Moments dans l'API (passeur déduit) | 01d | 1 h |
| 01f | Lecteur : modes, enchaînement, contexte | 01e, `v2-ecran-match/19` | 2 h |
| 01g | Lecteur : barre et surimpressions | 01f | 1 h 45 |
| 02 | Moments clés | 01d, 01f | 1 h |
| 03 | Résumé | 01d, 01g, 02 | 1 h 45 |
| 07a | Validation des modes | 02, 03 | 1 h 30 |
| 07b | Validation après la calibration | 07a, `v2-collectif/22c` | 50 min |

Total : 16 h 05 de travail effectif ; temps machine à part (séries de 50 matchs, environ 2 h 30 chacune).
