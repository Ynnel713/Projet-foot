# 02a1: Hauteur du ballon : vol des passes et remises aériennes

**Découpé du ticket `02a` le 23/11/2026** (décision du propriétaire, estimation de 3 h au-delà du seuil de 2 h). Référence de détail : `02a-hauteur-du-ballon-physique.md`, `02-hauteur-du-ballon-moteur.md`, `docs/ETUDE_HAUTEUR_V2.md` sections 4 et 5.

**What to build:** le ballon a une vraie hauteur dans le moteur V2 (révision de D-V03) :
1. **État** (`BallState`) : `z` (m), `vz` (m/s) ; `aerial_left_m` disparaît.
2. **Départ d'une passe ou remise aérienne** : durée de vol `T = −ln(1 − d·λ / v0) / λ` (λ = −ln `BALL_FRICTION_PER_S`, d distance au point visé), plafonnée à `MAX_FLIGHT_S` (cas `d·λ ≥ v0` compris : le ballon retombe avant sa cible) ; `vz0 = g·T / 2`.
3. **Pas du ballon** : chute libre exacte sur le pas, impact coupé à l'instant exact ; rebond `vz ← −0,70·vz`, vitesse horizontale × 0,85 ; rebond de sommet sous 15 cm : le ballon roule (`z = 0`).
4. **Mode calculé** : « aérien » si `z` dépasse `AERIAL_HEIGHT_M` (2,5 m), « sol » sinon, à chaque pas ; un ballon au-dessus de 2,5 m n'est touché par personne (règle du ticket 29 lue sur la hauteur, rebonds compris, jusqu'au ticket 03). La lecture d'occasion (`occasion.reach_probability`) suit la même règle.
5. **Trace** : `BallSnapshot.z` et `BallPoint.z` ; format de l'API inchangé (affichage : `02b`).
6. Tirs : inchangés ici (`02a2`) ; ballon tenu, contré, dévié : au sol (`z = 0`), sauf contrôle raté en l'air : il retombe d'où il a été touché (réserve A3, choix du propriétaire du 23/11/2026).

**Attributs :** aucun.

**Blocked by:** `v2-collectif/29` (livré), `v2-collectif/28b` (livré).

**Bloque :** `02a2`, `02b`, `03`.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : l'origine « centre » d'un tir et la lecture d'occasion passent à la hauteur sans refonte. Temps machine, non compté : séries avant/après de 50 matchs (environ 2 × 12 min), suite complète (environ 15 min).

**Constantes** (validées par le propriétaire le 23/11/2026) : g = 9,81 m/s² ; restitution 0,70 et freinage par rebond 15 % (V1, `animation/ball.py`) ; fin des rebonds sous 15 cm de sommet (V1, réglage B1) ; durée de vol plafonnée à 4 s (sommet ≈ 19,6 m) ; seuil « aérien » 2,5 m, rebonds réels (un rebond au-dessus de 2,5 m passe au-dessus des joueurs). Repères réels (temps de vol et sommet d'un dégagement, d'un centre, d'une passe lobée) : non trouvés (articles de biomécanique inaccessibles depuis la session) ; ordres de grandeur du modèle : passe de 25 m, 2,2 s et 6 m ; 40 m, 2,9 s et 10 m ; 50 m, 3,7 s et 17 m.

**Critères chiffrés** (posés avant le code) :
- vol seul : sommet = `vz0² / 2g` (écart < 2 %) ; durée de vol = `2·vz0 / g` (écart < 1 tick) ;
- point de chute d'une passe aérienne non plafonnée à ± 1 m de son point visé ; plafonnée : `T` = 4 s, avant la cible ;
- rebond : sommet suivant = 0,49 × le précédent (± 5 %) ; le ballon finit par rouler (`z = 0`, `vz = 0`) ;
- scène : un joueur sous la trajectoire (ballon au-dessus de 2,5 m) ne touche pas le ballon, le receveur au point de chute le touche ;
- 50 matchs : `z ≥ 0` sur tous les pas ; mode tracé = « aérien » si et seulement si `z > 2,5 m` ;
- comportement sportif dans le bruit sur 50 matchs mêmes graines (buts, tirs, passes réussies, relances longues gardées), écart apparié avec intervalle ;
- mêmes empreintes de trace sur deux exécutions à graine fixée ; suite complète au compte attendu ; V1 inchangée.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Vol, point de chute et rebond conformes aux critères chiffrés (scènes)
- [x] `z ≥ 0` et mode cohérent avec `z` sur 50 matchs
- [x] Comportement sportif dans le bruit sur 50 matchs pour les volumes (buts, tirs, passes) ; écarts significatifs listés ci-dessous (ballons longs, origine « centre » attendus ; tirs cadrés et contrés à revoir)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu

## Résultats (23/11/2026)

- Code : `v2engine/vol.py` (constantes, `flight_time_s`, `launch_vz`, `step_height` : chute libre exacte, impact coupé à l'instant exact, rebonds, arrêt ; `height_at`, `is_aerial_height`) ; `BallState.z`, `vz` (fin de `aerial_left_m`, et de `restart.AERIAL_LANDING_M`) ; `possession.pass_launch` (vitesse et point visé, mêmes tirages que `pass_velocity`, devenu son enveloppe) ; `match._loft` au départ d'une passe ou remise en l'air (durée de vol calée sur l'avance pas à pas du moteur : la loi continue faisait retomber le ballon 1 à 1,5 m trop loin au-delà de 40 m) ; `_step_loose_ball` : hauteur avancée à chaque pas, vitesse horizontale × 0,85 par rebond, mode calculé, contact refusé si le ballon passe au-dessus de 2,5 m au contact et l'est encore en fin de pas ; ballon tenu, contrôlé, remis en jeu, sorti ou sifflé : au sol ; contrôle raté en l'air : le ballon garde la hauteur du contact et ne monte plus (réserve A3 de l'expert, choix du propriétaire du 23/11/2026, au lieu de « au sol » du point 6) ; origine « centre » d'un tir : ballon touché en l'air ou sur un rebond ; `occasion.reach_probability` : points de trajectoire sous 2,5 m seulement ; trace : `BallSnapshot.z`, `BallPoint.z` (API inchangée, affichage au `02b`). Bancs (`scripts/measure_v2.py`, `measure_v2_decisions.py`) rebranchés sur `pass_launch`.
- Scènes (`tests/test_v2engine_hauteur_ballon.py`, 15 cas) : constantes ; sommet `vz0²/2g` à moins de 2 %, durée `2·vz0/g` à moins d'un pas ; rebonds à 0,49 du précédent (± 5 %), le ballon finit par rouler ; impact coupé dans le pas, hauteur jamais négative ; durée de vol (loi continue et pas à pas) et plafond de 4 s ; point de chute à ± 1 m du point visé (20, 30, 40, 45 m) ; vol plafonné retombant avant sa cible ; mode suivant la hauteur ; joueur sous la trajectoire non touché, receveur au point de chute ; passe au sol jamais en l'air ; contrôle raté en l'air : le ballon retombe d'où il a été touché (réserve A3) ; match de 15 minutes : hauteur jamais négative, mode tracé cohérent, porteur au sol. Tests adaptés : `test_v2engine_ballon_mort` (scène du joueur sous le ballon), `test_v2engine_relance_longue`, `test_v2engine_relance_au_pied` (départ en l'air), `test_v2_indicators` (crochets du banc).
- Séries (50 matchs appariés, `bench_series` ; avant : `3e0cdec`), détail `docs/INDICATEURS_V2.md` § 71 : buts 4,62 → 5,14 (+ 0,52 [− 0,29 ; + 1,33]), tirs par équipe 14,4 → 14,7, passes réussies 84,2 % inchangées, dans le bruit ; passes longues réussies 73,1 → 70,1 % (− 2,9 points, significatif, attendu : rebonds au-dessus des joueurs) ; tirs nés d'un centre 0,1 → 1,2 % (attendu) ; tirs cadrés 36,0 → 40,8 %, contrés 24,6 → 21,4 %, arrêts + 1,06 par match, corners − 0,68 (significatifs, inattendus : le tir ne lit pas la hauteur ; effet indirect des situations ou hasard, 166 indicateurs significatifs sur 2 808 pour environ 140 attendus ; à revoir au `02a2` et au `v2-collectif/22c`). Vols : 17,3 par match ; 25 à 40 m, 2,5 s et 7,4 m (médianes) ; 40 m et plus, 3,5 s et 14,6 m ; plafond 19,6 m jamais dépassé ; hauteur jamais négative, 0 mode incohérent.
- Durée réelle : environ 2 h 35 (analyse 30, développement 50, tests 30, intégration et vérifications 45), + 29 % ; durée de vol recalée sur l'avance pas à pas du moteur (point de chute trop long au-delà de 40 m, trouvé par les scènes), bancs rebranchés sur `pass_launch`, remise en jeu posée au sol (oubli trouvé à la relecture) ; à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : deux séries `measure_v2` interrompues à 30 min (limite des tâches de fond, séries séquentielles concurrentes), deux séries `bench_series` de 50 matchs (2 × 48 min), série des vols (30 min), deux suites complètes (environ 18 min chacune).
- Déterminisme : matchs 0 et 1 rejoués, mêmes empreintes de la piste du ballon (`6c5c0d0a…`, `bf29f2e0…`) ; même score moyen (5,14) sur les deux séries « après ».

## Comments

- 23/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte `f9a30d1f…`). Réserves : A1, tirs cadrés + 5,3 points, contrés − 3,7, arrêts + 1,06, corners − 0,68 sans mécanisme démontré (contrôle au `02a2` ou au `v2-collectif/22c`) ; A2, « relances longues gardées » non mesuré directement (colonne « gardé » du script de série à `nan`), passes longues réussies − 2,9 points (script à corriger avant le ticket 03) ; A3, contrôle raté en l'air gardant sa vitesse verticale. Facultatifs : A4, contact accepté en descente jusqu'à environ 1,4 m au-dessus du seuil ; A5, `occasion._ball_path` sans la perte de 15 % par rebond. Propriétaire : « J'accepte A1 », « J'accepte A2 », A3 : « Il retombe d'où il est ». A3 corrigée (le ballon garde la hauteur du contact, vitesse verticale ramenée à 0 au plus) et testée.
- 23/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS (empreinte `a5148e8a…`), A1 et A2 acceptées, A3 corrigée, aucune action obligatoire ; facultatifs A4, A5, A6 (point 6 du texte harmonisé, fait). QC VALIDÉ (remarques non bloquantes : contact en fin de pas descendant sans test dédié ; dernière assertion du test du joueur sous la trajectoire presque tautologique). Clôture VALIDÉ. Points à surveiller (expert) : 97 % des ballons longs au-delà de 40 m rebondissent avant d'être touchés (ticket 03), rebond à 49 % haut pour du gazon, trajectoires plus hautes qu'une passe tendue réelle (freinage au sol appliqué dans l'air), séries de 50 matchs faites avant la correction A3 (effet attendu négligeable, à remesurer avec le `02a2`).
