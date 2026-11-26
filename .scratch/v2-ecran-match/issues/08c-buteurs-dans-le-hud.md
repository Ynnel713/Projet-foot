# EM-08c — Buteurs dans le HUD (V) — 75 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md`. Demande du propriétaire (19/11/2026) : « j'aimerais que les buteurs soient
affichés dans le hud avec la minute du but ». Suite d'EM-08 / EM-08b (HUD, score centré sur la ligne médiane).

- **Problème** : le HUD montre le score mais pas qui a marqué ; il faut lire la frise ou attendre la fin.
- **Données** : `trace.goals[]` donne `minute`, `team` (équipe qui marque), `scorer` (dernier joueur à avoir touché le
  ballon, ticket `v2-realisme/19b`, parfois vide) et `own_goal`. Rien à ajouter côté API ni moteur (le ticket EM-17
  « buteur dans les buts » est donc déjà couvert ailleurs ; son statut n'est pas à jour).
- **Dépendances** : EM-08, EM-08b.

## Comments

### 19/11/2026 — décisions, estimation et critères

- **Décisions du propriétaire** (19/11/2026, choix « 3 lignes puis « +n » ») : un buteur par ligne avec ses minutes,
  12 px, sous le nom de son club ; 3 lignes au plus par équipe ; au-delà, « +n autres » et la liste complète au survol ;
  le HUD grandit seulement quand il y a des buts (≈ 14 px par ligne, 42 px au plus). Passe décisive : attendre le
  passeur du moteur (`v2-mise-en-scene/01`). Cartons et remplacements : rien tant que `v2-attributs-restants/09a` et
  `v2-coach-et-gestion-de-match/05a` ne les produisent pas.
- **Choix de détail (à confirmer à l'écran)** :
  - au-delà de 3 buteurs : les 2 premiers (ordre chronologique du premier but) puis « +n autres » en 3e ligne, pour tenir
    les 3 lignes ;
  - minute d'un but = libellé de l'horloge du HUD au même instant (`clock`, ex. 2', 45+3', 90+1') : cohérent avec la
    minute affichée au moment du but ;
  - but contre son camp : « Nom (csc) », sous l'équipe qui en profite ; buteur inconnu : « But » ;
  - masqué sous 500 px de haut (même règle que la frise, EM-04) : le HUD y est déjà au plus juste.
- **Estimation** (travail effectif) : analyse 15 min, développement 25 min, tests et mesures 20 min, intégration et
  clôture 15 min, **total 1 h 15**, confiance moyenne. Temps machine hors total : suite complète, mesures navigateur.
- **Critères d'acceptation** :
  - un buteur n'apparaît qu'une fois son but lu (même règle que le score révélé, jamais en avance, ne recule pas au
    ralenti) ; nombre de minutes affichées = buts révélés de l'équipe (hors « +n ») ;
  - 3 lignes au plus par équipe, mesuré sur PSG–Le Havre 10-0 ; hauteur du HUD : + 0 px sans but, + 14 px par ligne au
    plus ;
  - score toujours centré sur la ligne médiane (écart ≤ 1 px, critère d'EM-08b) à 1024, 1366 et 1920 px ;
  - aucun défilement de page ; aucun texte qui déborde (tronqué par « … », nom complet au survol) ;
  - fluidité ≥ avant (médiane d'image, temps de script) ;
  - `npm test`, lint 0 erreur, build OK ; suite Python 3 437 passés.

### 19/11/2026 — implémentation

- **Code** :
  - `utils/matchHud.js` : `revealedScorers(goals, shownS, minuteLabel, maxLines = 3)` (un buteur par ligne dans l'ordre de
    son premier but, csc à part, au-delà de 3 buteurs les 2 premiers et `hidden`), `scorerText` (nom complet, info-bulle),
    `hudName` (nom sans prénom) ;
  - `components/match/ScoreBlock.jsx` : bloc en grille à trois colonnes (centrage d'EM-08b conservé) ; 2e rangée
    `Scorers` mémoïsée, 12 px sur 14 px, nom tronqué en premier (4,5 rem au moins), minutes ensuite seulement, liste
    complète au survol ; rien sans but ; masqué sous 500 px de haut ;
  - `MatchHud.jsx` transmet `scorers` ; `MatchScreen.jsx` les calcule une fois par but révélé (`useMemo` sur le nombre
    de buts révélés du score ; buts rangés dans l'ordre du match), minute au libellé de l'horloge (`clock`).
- **Écarts aux décisions, décidés en cours de route (à confirmer)** :
  - nom sans prénom (« Kvaratskhelia », « Van Neck ») : avec le nom complet, à 1024 px, le nom de Kvaratskhelia
    disparaissait derrière ses 5 minutes ;
  - sous 1280 px de large, lignes alignées sur l'écusson et non sous le nom (54 px regagnés) ;
  - hauteur d'une ligne : 14 px exactement (marge de 2 px retirée après la 1re mesure, + 16 px par ligne).
- **Tests** : `utils/matchHud.test.js` + 4 tests (buts lus seulement et à la seconde près, regroupement, csc, 3 lignes et
  « +n autres », buteur inconnu, nom sans prénom) ; `npm test` 71 passés.
- **Mesures** (`mesures/em08c-mesure.cjs`, Playwright, traces réelles `em11-om-ol` et `em11-psg-havre` ; résultats
  `em08c-apres.json`, captures `em08c/`, 13 cas) :
  - révélation : 0 buteur à 2,03', « Openda 2' » à 2,05' (but à 2,037') ; minutes affichées = buts révélés ;
  - 3 lignes au plus : PSG–Le Havre 10-0 à 104' : « Kvaratskhelia 5', 22', 45+1', 59', 90+4' », « Dembélé 18', 20',
    23' », « +2 autres » ; OM–OL 6-3 : 3 lignes et 1 ligne ;
  - HUD à 1366×768 : 89 px sans but, 103 avec une ligne, 117 avec deux, 131 avec trois (+ 14 px par ligne) ;
  - centre du score − centre du terrain : 0 px aux 13 cas (1024, 1366, 1920, 844) ; aucun défilement de page ;
  - débordements : aucun, sauf à 1024 px le quintuplé de Kvaratskhelia (minutes tronquées par « … », liste au survol) ;
  - 844×390 : buteurs masqués (hauteur 0), HUD 69 px inchangé.
- **Fluidité** (`mesures/em08c-fluidite.txt`, builds de production avant `e104812` et après, `em11-psg-havre`, ×8, 3 passes
  alternées) : médiane 16,7 ms des deux côtés ; script 1,88 → 1,72 ms par image (bruit ± 0,2 ms). 1er essai sans
  mémoïsation : + 11 %, d'où la mémoïsation. Limite : le banc ne couvre que les 2 premières minutes (avant le 1er but).
- **Vérifications** : lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 437 passés, 0 ignoré, 14 désélectionnés (attendu inchangé).
- **Déterminisme** : affichage seul, sans aléa ni horloge.
- **À vérifier à l'écran** : saut du terrain à chaque nouvelle ligne de buteurs (14 px, jusqu'à 42 px) ; noms sans
  prénom ; lisibilité du gris des noms sur le fond du HUD.

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `b154c303`) : **APPROVED_WITH_RESERVATIONS**. Révélation vérifiée par construction (buts rangés dans
  l'ordre du match, `trace.py:380`), hauteurs et centrage recoupés avec la mesure.
  - A1 [réserve] écarts aux décisions non validés : noms sans prénom, alignement sur l'écusson sous 1280 px.
  - A2 [facultatif] `hudName` : un prénom composé sans trait d'union (« Mohamed Ali Cho » → « Ali Cho ») ; deux buteurs
    de même nom de famille dans une équipe donneraient deux lignes identiques (nom court de l'effectif, plus tard).
  - A3 [facultatif] banc de fluidité sans buteur affiché ; à refaire sur une fenêtre avec 3 buts si ralentissement vu.
- Contrôle qualité : **VALIDÉ**.
- **Réserve acceptée par le propriétaire** : « J'accepte les deux » (19/11/2026 ; noms sans prénom et alignement sur
  l'écusson sous 1280 px).
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 1 h 15 ; réelle environ 1 h 20 de travail effectif (analyse 20, développement 25, tests et mesures
  25, clôture 10), écart + 7 % : deux reprises d'affichage après la 1re mesure (troncature à 1024 px, mémoïsation).
  Temps machine hors total : trois séries de mesures navigateur, deux builds et douze passes de fluidité, suite complète
  (14 min 39).
- 26/11/2026 (audit du mode « moments clés ») : `v2-mise-en-scene/01` est découpé et le moteur n'écrit plus le passeur dans la trace. Le passeur est déduit du journal côté serveur et servi par l'API au ticket `v2-mise-en-scene/01e` ; c'est là qu'il faut le lire. La passe décisive dans le HUD reste à afficher après 01e.
