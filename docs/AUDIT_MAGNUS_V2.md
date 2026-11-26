# Audit : effet Magnus et frappes enroulées dans la V2 (26/11/2026)

Demande du propriétaire du 26/11/2026 : savoir ce qui existe, ce qui est simulé par triche et ce qui manque sur le spin et les trajectoires courbes, avant de poser les tickets. Lecture seule du code au commit `08cd480`. Aucun code modifié.

## Verdict en une ligne

Rien n'existe : la V2 n'a **aucun état de rotation du ballon** et **aucune trajectoire non rectiligne** ; il n'y a pas non plus de triche qui simulerait une courbe. Coups francs, corners, centres et tirs sont des lignes droites, freinées par une loi exponentielle. Le seul spin du dépôt est celui de la V1 (`src/ligue1sim/animation/ball.py`, fichier protégé, rendu seulement), inutilisable par la V2.

**Contradiction relevée et tranchée** : `docs/TRD_V2.md` excluait encore « l'effet du ballon » (D-V03 révisée le 03/11/2026 : hauteur seulement), alors que la roadmap contenait `v2-realisme/14b` depuis le 05/11/2026. Décision du propriétaire du 26/11/2026 : D-V03 révisée (pas de nouvelle décision), rotation et Magnus dans le périmètre, vent exclu.

## 1. État de spin du ballon

| Où | Ce qu'il y a | Spin ? |
|---|---|---|
| `v2engine/ball_state.py`, `BallState` | `position`, `velocity` (Vec2, à plat), `holder`, `mode` (« sol » / « aérien »), `aerial_left_m` | **non** : ni ω, ni axe, ni hauteur (`z` arrive avec `v2-hauteur-ballon/02a`, à faire) |
| `ball_state.py`, `ShotFlight` | `origin`, `slope` (pente verticale fixée au départ), `elapsed_s`… | non |
| `v2engine/possession.py` | aucun champ du ballon ; seulement les lois de passe | non |
| `v2engine/trace.py`, `BallSnapshot` / `BallPoint` | `position`, `mode`, `holder`, `dead` ; `rotation_s` (l. 66) = rotation **du joueur** avant de frapper (07e) | non |
| `ui/` (EM-21a) | ballon dessiné qui « tourne » : motif lié à la position affichée, décoratif | non (aucune donnée de spin lue) |
| V1, `src/ligue1sim/animation/ball.py` l. 60-70, 285-350 | `spin` + `_MAGNUS_K` réel pour les tirs ; `cross` et `deflect` courbés par un décalage seedé par hash (triche géométrique, documentée) | oui, mais **V1, protégé, rendu seulement** ; référence de coefficients au mieux |

## 2. Trajectoires non rectilignes

Recherche `magnus|spin|swerve|curl|curve|bend|courb|enroul|bross|effet|rotation|omega` dans `v2engine/` : **0 occurrence liée au ballon** (les « courbes » trouvées sont les courbes d'attributs, `_curve` ; les « rotations » celles des joueurs, 07a/07e).

Le pas du ballon (`match.py`, `_step_free_ball`, l. 921-974) : `end = position + velocity × dt`, puis `velocity × 0,6^dt`. La direction de la vitesse ne change jamais en vol. Seuls changements de direction : contacts (`possession.deflect`), arrêts (`shooting.parry_velocity`), contrôle raté (`missed_control_velocity`) : des chocs, pas des courbes.

## 3. Traitement actuel des frappes concernées

| Frappe | Code | Trajectoire | Constante qui simule une courbe ? |
|---|---|---|---|
| Coup franc direct | `match._play_restart` l. 582 : le preneur reçoit le ballon et décide comme dans le jeu (`decision.choose_action`, `set_piece=True`) ; le tir est un tir ordinaire | droite, `heading × SHOT_SPEED_MPS` (l. 852) | non ; pas de mur (16e à faire) |
| Coup franc centré | passe ordinaire du preneur | droite | non |
| Corner rentrant / sortant | `restart.is_aerial` l. 189 : corner vers la surface = passe « aérienne » ; `pass_velocity` vers le receveur | droite, intouchable jusqu'à `aerial_left_m` | non : rentrant et sortant n'existent pas (16d à faire) |
| Centre enroulé | passe longue ou vers la surface en mode `AERIEN` (`match.py` l. 892) | droite | non (types de centre : `v2-attributs-restants/11`, à faire) |
| Frappe enroulée | `shooting.draw_shot_error` : angle au départ = angle à la ligne ; visée à 2,5 m à l'intérieur d'un poteau tiré au sort (05l) | droite | non : la visée intérieure du 05l est un choix de cible, pas une courbe |
| Passe brossée | `possession.pass_velocity` : direction `aim − passeur` | droite | non |
| Tir dévissé | `shooting.shank_velocity` : tourné de `SHANK_ANGLE_DEG` **au départ** | droite | non (angle de départ, pas de courbe) |

Conclusion : aucune triche à retirer en V2. Le trou est entier et assumé : **sans Magnus, coups francs, corners et centres enroulés sont des lignes droites** ; aucun but « par-dessus le mur et sous la barre » ou « rentrant au premier poteau » n'est possible, et un gardien ou un défenseur n'est jamais trompé par une courbe.

## 4. Décisions qui supposent une trajectoire droite (sites à adapter)

Deux familles : (A) les **prédictions de trajectoire** par formule fermée du freinage exponentiel, que 14a doit de toute façon réécrire ; (B) la **géométrie en segment ou en angle**, qui reste fausse même avec un bon freinage.

### A. Prédictions par formule fermée `(f^t − 1) / ln f` (réécrites par 14a, courbes gratuitement si elles passent par le prédicteur partagé)

| Site | Rôle | Hypothèse |
|---|---|---|
| `anticipation.py:81` `meeting_point` | point où un joueur coupe le ballon (receveur, défenseur) | position(t) = départ + v·(f^t−1)/ln f, direction fixe |
| `anticipation.py:73` `loose_ball_target` | point d'arrêt d'un ballon libre | arrêt sur l'axe de la vitesse |
| `occasion.py:45` `_ball_path` | trajectoire pour la chance d'atteindre le ballon (28c) | idem |
| `possession.py:214` `_launch_speed`, `:219` `max_pass_reach_m`, `:225` `pass_aim` (`travel_s`), `:242` `pass_velocity` | vitesse de départ, portée, temps de vol, direction | direction = cible − passeur |
| `decision.py:550` `lost_carry_outcome` | vitesse d'une touche trop longue | inverse du freinage |
| `shooting.py:347` `_flight_time_s`, `:355` `_flight_distance_m` | temps de vol d'un tir (gardien, contres) | égalité exacte avec la boucle au pas de 0,1 s |
| Consommateurs : `cerveau.py:333`, `:359` ; `defense.py:494` ; `gardien.py:119` (`race`) | course au ballon, interception | via les fonctions ci-dessus |

### B. Géométrie en ligne droite (à reprendre par 14b2 et 14b3)

| Site | Rôle | Hypothèse |
|---|---|---|
| `anticipation.py:48` `pass_readers` | défenseurs qui lisent la passe | couloir autour du segment départ → cible |
| `possession.py:112` `_cut_chance` → `pass_difficulty`, `pass_success_probability` (lus par `decision`, `restart.restart_target`, `occasion`) | chance de couper une passe | distance au segment |
| `decision.py:253` `lane_closed_during_turn` | ligne fermée pendant la rotation | segment |
| `defense.py:433` `_lane`, `SHOT_LANE_RANGE_M` | presseur qui ferme la ligne de passe ou de tir | segment porteur → receveur / but |
| `shooting.py:106` `_goal_angle`, `:115` `_covered_share`, `:217` `_blockers`, `:229` `block_probability`, `:434` `_block_covers` | contres et angle masqué | rayons droits depuis le tireur |
| `shooting.py:362` `_keeper_cover`, `:472` `_goal_angles`, `:486` `_flight_shares`, `:520` `physical_shot_chance`, `:289` `on_target_axes`, `:411` `aim_angles`, `:580` `draw_shot_error` | chance du tir (décision alignée sur la résolution, 05e), portée du gardien, visée | angle au départ = angle sur la ligne de but |
| `match.py:921` (`shot_for`), `:948` (hauteur = `origin.distance × slope`), `:443` `_keeper_reaches`, `:479` `_blocked` | résolution du tir en vol | ligne droite jusqu'au but, distance parcourue = distance à l'origine |
| `match.py:609`, `:893` `aerial_left_m` | point de chute d'une passe aérienne | longueur du segment (remplacé par `z` au 02a) |

Point dur : la **visée inverse**. Aujourd'hui viser = orienter la vitesse vers la cible. Avec de l'effet, le tireur doit partir à côté de la cible pour que la courbe y revienne (enroulée qui part hors du cadre). Il faut résoudre la direction de départ (tir sur le prédicteur), et la décision (05e : chance de décision = chance de résolution) doit lire la même trajectoire.

Non concernés : `decision.arrival_s`, `free_point` (courses des joueurs), `gardien.bisector_point` (position du ballon seulement), `restart.exit_point` (segment d'un pas de 0,1 s : courbure négligeable sur un pas).

## 5. Dépendances techniques : traînée (14a) et Magnus

- **Même solveur, oui.** 14a remplace `v × 0,6^t` par roulement constant + traînée en v². Magnus est une force de plus dans la même équation (`a = −k_D·|v|·v + k_M·ω × v`, `ω` décroissant). Dès qu'il y a Magnus, plus de formule fermée en 2D : il faut **un intégrateur numérique unique**, utilisé à la fois par le pas du ballon et par toutes les prédictions (A), pour que la prédiction égale la réalité (c'est déjà l'exigence de `_flight_time_s`, qui reproduit la boucle au pas près).
- **Les faire ensemble : non.** 14a seul change déjà tout le jeu de passes (vitesses de départ, portées, interceptions) et demande une mesure sur 50 matchs ; y ajouter Magnus mélangerait deux causes dans la même mesure. **Séquencer** : 14a livre le module de trajectoire et le prédicteur partagé (à loi de freinage nouvelle, sans spin), puis 14b1 n'ajoute qu'un terme de force et un état.
- **Condition pour que la dépendance ait un sens** : 14a doit livrer ce prédicteur partagé et migrer tous les sites (A) dessus. Exigence ajoutée au 14a le 26/11/2026 (voir le ticket).
- **Prédictions déjà incohérentes aujourd'hui** (calcul du 26/11/2026) : `meeting_point`, `loose_ball_target`, `_ball_path` et `pass_aim` prennent la formule continue ; la boucle au pas de 0,1 s va 2,58 % plus loin à tout instant ; `_flight_time_s` suit la boucle. Le prédicteur unique change donc ces sites : 14a1 garde chaque formule (empreintes identiques), l'alignement va avec la nouvelle loi (14a2). Détail dans le ticket 14a.
- **Hauteur (02a)** : Magnus d'un ballon avec effet avant/arrière agit sur la verticale (coup franc qui plonge, ballon qui flotte) : il faut `z`, `vz`. L'effet latéral seul pourrait s'en passer, mais 14b était déjà bloqué par 02a ; on garde l'ordre 02a → 14a → 14b1.

## 6. Tests existants

| Test | Ce qu'il référence | Nature |
|---|---|---|
| `tests/test_v2engine_rayon_attributs.py:514` | « Curls Ball » rangé dans la famille des tirs (« aussi centres et coups francs enroulés ») | garde des gestes préférés ; aucune courbe |
| `tests/test_ball.py` (l. 47, 58, 211, 223, 256) | `spin` et Magnus de la V1 | V1 seulement |
| Tests V2 qui figent la ligne droite et le freinage exponentiel : `test_v2engine_anticipation.py` (7 références), `test_v2engine_ballon_mort.py` (5), `test_v2engine_receveur.py` (4), `test_v2engine_difficulte.py` (4), `test_v2engine_cerveau.py` (3), `test_v2engine_relance_longue.py` (3), `test_v2engine_conduite.py` (2), `test_v2engine_grosses_occasions.py` (2) | `meeting_point`, `_flight_time_s`, `_cut_chance`, `BALL_FRICTION_PER_S`… | à adapter par 14a (loi), puis à compléter par 14b2/14b3 (cas avec effet) |

Aucun test V2 ne référence un spin ou une courbe, même en triche.

## Tickets posés

Découpage de `14b` (2 h estimées le 05/11, confiance faible, sous-estimé d'un facteur 4 à 5) en quatre morceaux ; `14b` devient chapeau, toute référence à `14b` sans lettre vaut pour les quatre (convention du dépôt), ce qui garde `16d`, `16e`, `14c`, `14d` et `v2-collectif/22a` bloqués par l'ensemble.

| Ticket | Contenu | Estimation | Confiance | Bloqué par |
|---|---|---|---|---|
| 14b1 | Spin du ballon et force de Magnus dans le solveur (état ω, constantes sourcées et figées, trace) ; aucun ballon n'a d'effet : jeu inchangé | 2 h 25 | moyenne | 14a, `v2-hauteur-ballon/02a` |
| 14b2 | Passes : 5 sites de la famille B (coupe, lecture, ligne fermée, presseur) sur la trajectoire prédite | 1 h 50 | moyenne | 14b1 |
| 14b3 | Tirs : 9 sites de la famille B, visée inverse (± 5 cm, ≤ 6 appels, repli sans effet, coût ≤ + 15 %) | 2 h 40 | faible | 14b1 |
| 14b4 | Qui met de l'effet : table par type de frappe, visée inverse des passes, lecture adverse, « Curls Ball » | 2 h 35 | faible | 14b2, 14b3 |
| **Total** | | **9 h 30** | | |

Ordre dans la roadmap : vague 3 de `docs/PLAN_V2.md` (`02a` → `14a` → `14b1` → `14b2` et `14b3` en parallèle → `14b4` → `14c` → `14d`), avant la calibration `v2-collectif/22a` (déjà bloquée par `14b`, donc par les quatre). Parallèle 14b2 / 14b3 vérifié dans le code : la visée des tirs (`shooting.aim_angles`, `draw_shot_error`, `match.py` l. 852) n'appelle ni `meeting_point` ni `pass_aim` ni aucun site du 14b2 ; la visée inverse des passes, qui en aurait besoin, est au 14b4.

## Repères de la littérature (26/11/2026)

Détail et liens dans le ticket 14b1. C_L 0,23 à 0,29 et C_D 0,25 à 0,30 sur un coup franc direct (Bray et Kerwin 2003) ; C_L qui plafonne vers 0,25 au-delà de 50 à 100 rad/s (Goff et Carré 2010) ; coup franc fort : environ 63 rad/s (10 tr/s), environ 3 m d'écart latéral (Beckham 2001, Goff et Carré) ; 10 tr/s n'est donc pas trop haut pour un coup franc fort, mais c'est le haut de la fourchette ; centres et passes : non trouvé ; décroissance du spin lente devant celle de la vitesse (Tsukada et Sakurai 2008).
