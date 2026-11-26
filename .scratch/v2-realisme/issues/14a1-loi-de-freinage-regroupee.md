# 14a1: Loi de freinage du ballon regroupée derrière une interface (sans changement de jeu)

**Découpé du ticket 14a le 26/11/2026** (décision du propriétaire : 22 lectures de `BALL_FRICTION_PER_S`, 4 h 40 au total, au-delà du seuil de 2 h). La nouvelle loi est au `14a2`.

**Chantier :** `v2-realisme`. **Catégorie :** physique (refonte sans effet).

**What to build:** un module `v2engine/freinage.py`, seul à connaître la loi de freinage horizontal du ballon, avec les lectures dont le moteur a besoin : vitesse après `t` (`speed_after`), pas du moteur (`step_velocity`), distance après `t` en continu ou au pas du moteur (`distance_after`), position prévue et point d'arrêt (`position_after`, `stop_position`), distance pour ralentir (`distance_to_slow`), vitesse de départ et d'arrivée (`launch_speed`, `arrival_speed`), temps pour ralentir (`time_to_slow`), temps de trajet en continu ou au pas (`travel_time_s`, ex-`hauteur.flight_time_s` et `shooting._flight_time_s`) et temps exact au pas (`stepped_travel_time_s`, ex-`hauteur`). Tous les sites passent par lui ; `meeting_point` et `loose_ball_target` perdent leur paramètre `friction_per_s`. Loi inchangée (exponentielle, 0,6 par seconde).

**Sites (audit du 26/11/2026)** : `possession` (vitesse de passe, portée max, visée), `decision` (touche trop longue), `anticipation` (point de rencontre, ballon libre), `cerveau`, `defense`, `gardien` (appelants), `occasion` (trajectoire du ballon libre), `shooting` (temps de vol et distance du tir pour le gardien), `match` (pas du ballon, durée de vol, hauteur des tirs), `hauteur` (fonctions déplacées), `scripts/v2_indicators.py`.

**Attributs :** aucun. **Constantes :** aucune nouvelle.

**Blocked by:** `v2-realisme/01c` (livré). **Bloque :** 14a2.

**Status:** livré (26/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : les formules au pas du moteur de `shooting` (log) et de `hauteur` (log1p) sont mathématiquement identiques ; si leur fusion change une empreinte, on garde les deux expressions. Temps machine, non compté : empreintes de 4 matchs complets (avant, après, deux fois), suite complète.

## Acceptance criteria

- [x] Plus aucune lecture de `BALL_FRICTION_PER_S` ni de paramètre `friction_per_s` hors de `freinage.py` dans `v2engine/`, `scripts/` et `api/` (test)
- [x] Empreintes de trace complètes (positions de tous les joueurs et du ballon à chaque tick, score, tirs, réceptions) identiques à la référence `0cf8986` sur 4 matchs complets, graines 0 à 3 (`.scratch/v2-realisme/mesures/14a1-empreinte.py`)
- [x] Mêmes empreintes sur deux exécutions
- [x] Tests de cohérence de l'interface (inverses, pas du moteur, ligne droite), indépendants de la loi pour resservir au 14a2
- [x] Suite complète : 3 548 + tests ajoutés, 0 échec ; V1 inchangée
- [x] Durée réelle relevée, comparée à l'estimation (rapport et `docs/agents/suivi-estimations.md`)

## Comments

### 26/11/2026 — implémentation

- **Code** : `v2engine/freinage.py` (nouveau, importe seulement `geometry`) : `BALL_FRICTION_PER_S` et toutes les lectures de la loi (`speed_after`, `step_velocity`, `distance_after` continu ou au pas, `position_after`, `stop_position`, `distance_to_slow`, `launch_speed`, `arrival_speed`, `time_to_slow`, `travel_time_s` continu ou au pas, `shot_travel_time_s`, `stepped_travel_time_s`). Sites branchés : `possession`, `decision`, `anticipation` (`meeting_point` et `loose_ball_target` sans paramètre de freinage), `cerveau`, `defense`, `gardien`, `occasion`, `shooting`, `match`, `scripts/v2_indicators.py`. `hauteur.flight_time_s` et `hauteur.stepped_travel_time_s` déplacés dans `freinage` (`travel_time_s`, `stepped_travel_time_s`).
- **Hypothèse vérifiée en cours** : la fusion du temps de vol des tirs (`shooting`, forme en `log`) avec la forme en `log1p` de `hauteur` changeait les empreintes des 4 matchs (scores identiques, 9 987 valeurs sur 10 000 différentes au dernier bit). Forme du tir gardée à part (`shot_travel_time_s`), fusion au 14a2 où la loi change de toute façon.
- **Empreintes** (`.scratch/v2-realisme/mesures/14a1-empreinte.py` : positions de tous les joueurs et du ballon à chaque tick, `z`, mode, porteur, score, buts, tirs, réceptions ; matchs complets, graines 0 à 3) : référence `0cf8986` rejouée dans un arbre séparé (`14a1-ref2.txt`) et code du ticket (`14a1-apres.txt`) **identiques** : `76d375077c3b370d`, `690076c62782595d`, `226ba1ce1a84b83f`, `2b0edd2d08d436be`.
- **Tests** : `tests/test_v2engine_freinage.py` (25 tests : inverses continus et au pas, pas du moteur, vitesse/distance/temps cohérents, ligne droite, forme du tir, aucune lecture de la loi hors du module) ; 9 fichiers de tests adaptés aux nouvelles signatures (imports, paramètre `friction_per_s` retiré), assertions inchangées.
- **Déterminisme** : deux exécutions du code du ticket, mêmes empreintes (`14a1-apres.txt`, `14a1-apres2.txt`) ; deux exécutions de la référence identiques entre elles.
- **Suite complète** : 3 573 passés, 0 échec, 0 ignoré, 14 désélectionnés (3 548 + 25), 14 min 34 s. V1 non touchée (aucun fichier V1 modifié).
- **Durée réelle** (travail effectif, à l'horloge de la session hors attentes machine, non chronométrée) : analyse 25 min, développement 40 min, tests 25 min, intégration et vérifications 35 min, **total 2 h 05** contre 2 h estimées (+ 4 %). Temps machine hors total : empreintes (3 séries de 4 matchs), suite complète.
- **À vérifier à l'écran** : rien (jeu identique bit à bit).

### 26/11/2026 — clôture (`/valider-ticket-simulafoot`, passage 1)

- Expert : `APPROVED` (empreinte `9e9cb34e…`). QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ`.
- A1 [facultatif] : des tests recalculent encore la loi exponentielle à la main avec `freinage.BALL_FRICTION_PER_S` (`test_v2_hauteur_ballon`, `test_v2_hauteur_tirs`, `test_v2engine_conduite`, `test_v2engine_difficulte`, `test_v2engine_grosses_occasions`) : à faire passer par l'interface au 14a2.
- A2 [facultatif] : `docs/ETUDE_HAUTEUR_V2.md:44` situe encore la constante dans `possession.py` (note d'étude historique).
- Pour le 14a2 (expert) : fusionner `shot_travel_time_s` avec `travel_time_s` ; garder `travel_time_s`, `distance_after` et `stepped_travel_time_s` inverses exacts du pas du moteur avec la nouvelle loi.
