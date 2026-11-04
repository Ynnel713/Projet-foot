# 03: Habillage de l'écran V2 (compositions, ralenti des buts, mi-temps, momentum, bancs)

**What to build:** retours du propriétaire sur l'écran V2 (03/11/2026), codés dans une session précédente sans ticket ;
ce ticket les documente et les clôture. Moteur inchangé : tout est de l'affichage, plus une route d'API en lecture.

1. **Compositions numérotées** : route `GET /api/v2/lineup?club=…` (`api/routers/v2.py`, `numbered_lineup`), même
   onze que `simulate_match` (`pick_best_formation`, déterministe). Numéros d'affichage (les données n'en ont pas) :
   gardien 1, puis de la défense à l'attaque jusqu'à 11 ; remplaçants à partir de 12, au plus 9 dont un gardien.
   L'écran les montre de part et d'autre du terrain (écrans larges), avec formation et entraîneur, et écrit le numéro
   dans le rond de chaque joueur (rond agrandi de 1,1 à 1,3 m pour le loger).
2. **Vitesses** 1 / 1,5 / 2 / 4 / 8 fois le temps réel, x1 par défaut (avant : 1 / 4 / 8 / 16, x8).
3. **Ralenti de chaque but** : 2 s après le but, retour 8 s avant, rejeu à 0,4 fois le temps réel, puis la lecture
   reprend ; bouton « RALENTI ⏭ » pour le passer. Le score ne recule pas pendant le ralenti.
4. **Changement de camp à la mi-temps** : l'écran tourne la scène d'un demi-tour à partir de la 45e minute (le moteur
   garde son repère) ; l'en-tête indique la période.
5. **Barre de momentum** au-dessus du terrain : une barre par minute jouée, vers le haut quand domicile pousse.
   Poussée = position du ballon dans la longueur, accentuée près des buts (dx·|dx|), plus 0,15 à l'équipe qui a le
   ballon ; échelle calculée sur les seules minutes déjà jouées (rien n'est révélé de la suite).
6. **Bancs** sous le terrain, de part et d'autre de la ligne médiane : entraîneur et remplaçants assis ; en 2e période,
   3 remplaçants de champ trottinent le long de la ligne de touche (décoratif, fonction du temps lu).

Hors périmètre : affichage du ballon aérien (ticket 02) ; détail des décisions « meilleur choix / erreur »
(ticket `v2-collectif/33`). Leurs hunks, présents dans les mêmes fichiers, ne font pas partie de ce ticket.

**Constantes** (`V2Match.jsx`, `v2.py`), validées par délégation du propriétaire (04/11/2026, « Mène-le jusqu'au
commit ») : `SPEED_OPTIONS = [1, 1.5, 2, 4, 8]`, `DEFAULT_SPEED = 1` ; `REPLAY_BEFORE_S = 8`, `REPLAY_AFTER_S = 2`,
`REPLAY_SPEED = 0.4` ; `HALF_TIME_MIN = 45` ; `MOMENTUM_MINUTES = 90`, `POSSESSION_BONUS = 0.15` ; `_BENCH_SIZE = 9` ;
`BENCH_ZONE = 7`, `BENCH_GAP = 4`, `SEAT = 1.6`, `WARMING_UP = 3` ; rayon du joueur 1,3.

Textes des nouveaux éléments aux jetons de la refonte (`text-data`, `text-caption`, ticket `refonte-ui/08`).

**Status:** livré (04/11/2026), validé expert + QC (réserve A1 acceptée par délégation du propriétaire, voir Comments)

## Acceptance criteria

- [x] Test : onze numérotés 1 à 11, gardien en 1 ; 9 remplaçants numérotés 12 à 20 dont un seul gardien ; aucun
      titulaire sur le banc (`tests/test_v2engine_trace.py`)
- [x] Route `/api/v2/lineup` : 200 pour un club connu, 404 pour un club inconnu (test 404 ajouté ; 200 vérifié à la
      main : Paris Saint-Germain, onze 1 à 11, Luis Enrique)
- [x] À l'écran (AEK Athènes - Al-Ahli, x8) : compositions, numéros, momentum, bancs visibles ; ralenti déclenché sur
      4 buts puis lecture reprise, score sans recul ; à la 45e, « 2e période » et gardien domicile de x 5 à x 100 ;
      3 remplaçants par équipe s'échauffent
- [x] `npm run build` OK, `npm run lint` sans nouvelle erreur (0 erreur, 5 avertissements) ; suite complète sur
      `af1588b` + ticket : 2 331 passés, 5 ignorés, 13 désélectionnés, 0 échec (+2 tests) ; V1 inchangée

## Comments

- 04/11/2026 : vérifié dans un arbre isolé (dernier commit + seuls fichiers du ticket), l'arbre principal portant
  alors le ticket 33 en cours. Première suite sur `245959b` : 2 316 passés, 5 ignorés, 13 désélectionnés. Lot replacé
  ensuite sur `af1588b` (refonte-ui/08 et v2-collectif/33 commités entre-temps, un conflit de style résolu).
- 04/11/2026, clôture (passage 1) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ.
  - A1 [réserve] la barre de momentum de la minute en cours moyenne aussi les images reçues mais pas encore vues
    (jusqu'à ~60 s d'avance). Acceptée par délégation du propriétaire (« Considère que je valide automatiquement
    toutes les reco d'experts », 03/11/2026 ; « je te laisse finaliser les 2 tickets », 04/11/2026). Correctif repris
    au ticket 02 (moyenne de la minute en cours limitée aux images déjà vues).
  - A2 [facultatif] but dans les 2 dernières secondes calculées jamais rejoué au ralenti (cas rare).
  - À surveiller : numéros des entrants (ticket `v2-coach-et-gestion-de-match/05`) ; `HALF_TIME_MIN` à remplacer par
    `trace.second_half_start_minute` (ticket `v2-coach-et-gestion-de-match/07`, en cours).
