# 03f: Gardien : en mouvement ou sur ses appuis au moment du tir

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un gardien pris à contre-pied doit encaisser plus). **Catégorie :** exécution.

**Constat vérifié :** la chance du tir ne tient compte que de la position du gardien, pas de sa vitesse au moment de la frappe (`shooting.keeper_position_factor`).

**What to build:** Avec l'arrêt par portée du 05b, la portée latérale disponible du gardien dépend de sa vitesse au moment du tir : déjà lancé du bon côté, il gagne ; à contre-pied, il perd (portée réduite d'une part proportionnelle à sa vitesse dans le mauvais sens).

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux); 05b (Arrêt : le gardien atteint ou non le ballon).

**Bloque :** 03l (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : portée de base du 05b.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Constantes (proposées le 22/11/2026, retenues par délégation permanente du propriétaire du 05/11/2026)

- Aucune constante nouvelle. Pendant sa réaction, le gardien garde son élan de la frappe (même modèle que l'adversaire de `decision.REACTION_S`) : portée vers le point de passage décalée de `vitesse vers le ballon × min(temps de vol, KEEPER_REACTION_S)` (0,30 s), en plus du plongeon du 05b ; à contre-pied, baisse d'autant, jamais sous 0. Le décalage n'est pas plafonné par `KEEPER_DIVE_REACH_M` (le corps a déjà bougé).
- Chiffres réels : part de la vitesse gardée pendant la réaction d'un gardien, non trouvée (toute, comme au `decision`) ; vitesse latérale d'un gardien au moment d'un tir, non trouvée. Moteur, 170 tirs de 6 matchs : vitesse en travers de l'axe du tir médiane 0,24 m/s, 90e centile 0,93 m/s, maximum 6,7 m/s (décalage de portée au 90e centile ± 0,28 m).

## Résultat (22/11/2026, `docs/INDICATEURS_V2.md` section 64)

- `shooting.keeper_reach_m(elapsed, toward)` et `shooting.keeper_toward_mps` (vitesse projetée sur la direction du point de passage) ; `ShotFlight.keeper_velocity` (vitesse à la frappe), `ShotEvent.keeper_toward_mps` tracé ; même loi à la résolution (`match._keeper_reaches`), à l'évaluation (`_keeper_cover` : chaque bord a l'élan vers lui, en travers de l'axe pour la tangence, le long de la ligne pour le bord sur la ligne), à l'xG après frappe et au banc (`scripts/v2_indicators.py`). Commentaire trompeur `match.py` « visée selon le gardien » corrigé (réserve A4 du 05l). Réserve A1 de l'expert (passage 1) corrigée : à la résolution, l'écart et l'élan se prennent depuis ses appuis de la frappe (`ShotFlight.keeper_from`), comme à l'évaluation ; la dérive de son inertie pendant le vol n'est plus comptée en plus de l'élan.
- 50 matchs appariés (moteur final, après A1) : buts 4,20 → 4,06, − 0,14 [− 0,77 ; + 0,49] (bruit) ; part des cadrés jugés arrêtés 61,0 → 59,9 % ; sur les mêmes tirs, l'élan donne 7 arrêts et en retire 6 (contre-pied) sur 501 cadrés jugés. Les tirs où le gardien est lancé vers le ballon sont moins arrêtés (44,8 %) : effet de sélection, il rattrape sa place (écart médian 1,42 m contre 0,98 m). Avant A1 : buts 4,32, 5 gagnés et 8 perdus sur 519.
- Tests : `tests/test_v2engine_appuis_gardien.py` (10, dont la dérive pendant le vol non comptée, réserve A1) ; bouchon de `keeper_reach_m` adapté à la nouvelle signature (`tests/test_v2engine_journal.py`).

Durée : estimée 1 h 45, réelle environ 1 h 50 (analyse 20 min, développement 30 min, tests 25 min, intégration, séries, revue et documentation 35 min), écart + 5 % (sous 30 %), dont 25 min pour la réserve A1. Durée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : relevé de 6 matchs, trois séries de 50 matchs (14 min chacune), trois suites complètes (16 à 17 min).

## Tests

- **Unitaires (scène contrôlée) :** même tir, gardien immobile, lancé du bon côté, à contre-pied : chance d'arrêt décroissante dans cet ordre

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Effet de la vitesse du gardien sur l'arrêt mesuré en scène contrôlée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 3 509 passés, 0 ignoré, 14 désélectionnés (3 499 au `27d` + 10 tests ; un premier passage avait 1 échec, bouchon de `keeper_reach_m` à l'ancienne signature, corrigé)

## Comments
- 22/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; pas de clôture (réserve A1 non acceptée par le propriétaire dans la conversation : corrigée).
  - A1 [réserve] double comptage partiel de l'élan en match (écart pris depuis la position dérivée par l'inertie pendant le vol) : corrigée, écart et élan depuis `flight.keeper_from` ; test de la dérive ajouté.
  - A2 [facultatif] portée nulle près du corps à contre-pied rapide (> 3,33 m/s) : non repris (plancher = constante produit à proposer) ; rare (90e centile 0,93 m/s).
  - A3 [facultatif] décalage non plafonné par `KEEPER_DIVE_REACH_M` : choix documenté, à surveiller.
- 22/11/2026, passage 2 (après correction A1) : expert APPROVED (A1 corrigée et vérifiée ; A2, A3 facultatives) ; QC VALIDÉ ; clôture VALIDÉ. À surveiller à la calibration : part des cadrés arrêtés (59,9 %, repère environ 70 %) ; le 03l s'appuie sur cette portée.
- 22/11/2026, passage 3 : la clôture du passage 2 couvrait à tort les fichiers de suivi (`docs/`, `.scratch/`), exclus de la revue ; empreinte refaite sur les 7 fichiers de code et de tests, inchangés ; expert APPROVED (code identique au passage 2) ; QC VALIDÉ (passage 2) ; clôture VALIDÉ.
