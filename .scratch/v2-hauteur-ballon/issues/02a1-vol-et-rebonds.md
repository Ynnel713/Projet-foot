# 02a1: Hauteur du ballon dans le moteur : vol et rebonds

**Découpé du ticket 02a le 26/11/2026** (décision du propriétaire, estimation au-delà de 2 h). Formules et étude : `02-hauteur-du-ballon-moteur.md`, points 1 à 3, 5 et 6 ; `docs/ETUDE_HAUTEUR_V2.md`, sections 4 et 5. Les tirs sont dans `02a2`.

**What to build:** le moteur V2 calcule la hauteur réelle du ballon pour tous les ballons sauf les tirs :
1. **État du ballon** (`v2engine/ball_state.py`) : `z` (m) et `vz` (m/s) ; `aerial_left_m` disparaît, ainsi que `AERIAL_LANDING_M` (`restart.py`).
2. **Convention** (décision du propriétaire du 26/11/2026) : `z` est la hauteur du **bas** du ballon (point de contact). Ballon au repos : `z = 0`. Impact au sol : `z = 0`. Un ballon passe sous une barre de hauteur `h` si `z + 2·BALL_RADIUS_M < h` (rayon : `BALL_RADIUS_M = 0.11`, `match.py`).
3. **Départ d'un ballon aérien** (coups de pied arrêtés `match.py:607`, passe en l'air `match.py:892`) : durée de vol déduite de la distance et de la vitesse avec le freinage exponentiel actuel (λ = −ln `BALL_FRICTION_PER_S`) : `T = −ln(1 − d·λ / v0) / λ`, puis `vz0 = g·T / 2`. Dans le moteur, `d·λ / v0` devient `d·(1 − f^dt) / (v0·dt)` pour suivre l'intégration horizontale au pas (réserve A1 de l'expert). Le cas où le ballon n'arrive pas (`d·λ ≥ v0`) est traité explicitement : vol plafonné. **Durée de vol plafonnée à `MAX_FLIGHT_S` = 4,5 s** (sommet au plus 24,8 m) : au-delà, le ballon retombe avant sa cible et rebondit vers elle.
4. **Pas du ballon** (`_step_ball`) : chute libre **exacte** sur le pas (`z + vz·dt − ½·g·dt²`, pas d'Euler : sur un tick de 0,1 s, Euler semi-implicite sous-estime le sommet de 10 % pour `vz0 = 10 m/s`). L'impact est calculé à l'instant exact dans le pas. Rebond : `vz ← −0,70·vz`, vitesse horizontale × 0,85. Si le sommet du rebond suivant est sous 0,15 m, le ballon roule (`z = 0`, `vz = 0`) avec le freinage actuel, inchangé (`BALL_FRICTION_PER_S` ; sa refonte est le ticket `v2-realisme/14a`).
5. **Mode calculé** : `« aérien »` si `z > 0,5 m`, `« sol »` sinon. Format d'API inchangé. Les règles de contact du ticket `v2-collectif/29` restent lues sur le mode jusqu'au ticket 03.
6. **Trace** : `BallSnapshot.z` à chaque enregistrement (format de l'API inchangé ; les points de vol à l'écran sont le ticket 02b).

**Constantes** (validées par le propriétaire le 26/11/2026) : g = 9,81 m/s² ; restitution au sol 0,70 ; vitesse horizontale × 0,85 par rebond ; arrêt des rebonds sous 0,15 m de sommet (toutes reprises de la V1, `src/ligue1sim/animation/ball.py`). **Constante nouvelle, validée le 26/11/2026 en cours de ticket** : `MAX_FLIGHT_S` = 4,5 s (valeur réelle à sourcer : temps de vol d'un long dégagement), provisoire jusqu'au `v2-realisme/14a`. Constat qui l'a motivée (2 matchs) : avec le freinage exponentiel, 3 ballons de 51 à 57 m à 28–30 m/s volaient 5,8 à 6,8 s (sommets de 41 à 57 m) et 6 sur 36 n'arrivaient pas à leur cible. Sur 10 matchs après plafond et correctif A1 : 29 vols plafonnés sur 171 (17 %), dont 16 ballons qui n'arrivent pas (le 33 % d'abord relevé venait de 4 matchs seulement ; détail : réserve A2 dans les Comments). **Constante nouvelle et provisoire** : seuil « aérien » 0,5 m sur le bas du ballon (hauteur du genou), à remplacer par les tranches de hauteur du ticket 03. Pas de traînée quadratique ni d'effet (hors périmètre, tickets `v2-realisme/14a` à `14c`).

**Sites touchés (audit de la phase 0, 26/11/2026)** :

| Catégorie | Sites | Travail |
|---|---|---|
| Lancement (`vz0`) | `match.py:607-609`, `892-893` | durée de vol, cas où le ballon n'arrive pas |
| Pas du ballon | `match.py:977-993` | chute exacte, rebond, mode calculé |
| Mode (test sur `z`) | `match.py:418` (`_received_as`), `992` (origine « centre ») | trivial |
| Temps d'arrivée | `occasion.py:69` | instant où `z` passe sous 0,5 m au lieu de la distance parcourue |
| Remise à zéro | `match.py:344`, `969`, `983` | trivial |
| Trace / API | `match.py:1373`, `1382`, `api/routers/v2.py:276-281` | `z` tracé, format d'API inchangé |

Aucun site ne projette le point d'impact hors du pas du ballon. Branchement estimé à environ 1 h : pas de nouveau découpage.

**Phases internes (un seul ticket, une seule livraison)** :
- **Phase 0** (faite le 26/11/2026) : audit des sites ci-dessus ; estimation verrouillée.
- **Phase 1** : physique du ballon (vol exact, impact, rebond, arrêt) dans une fonction pure, testée unitairement sur des vols (`vz0 > 0`) ; le moteur lance encore tous les ballons à `vz0 = 0` : **empreintes de trace identiques à la référence** (le `z` n'entre dans la trace qu'en phase 2).
- **Phase 2** : branchement des sites, `z` dans la trace, mesure avant/après.

**Changement de jeu attendu (à mesurer, pas à cacher)** : un ballon aérien devient touchable quand son bas passe sous 0,5 m, et non plus à 3 m de son point de chute ; il redevient intouchable pendant un rebond qui dépasse 0,5 m (lob de 8 m de sommet : premier rebond à 3,9 m, environ 1,8 s en l'air).

**Tolérance** (décision du propriétaire du 26/11/2026) : le bruit mesuré entre deux séries de référence de 50 matchs, graines différentes (`scripts.bench_series`, indices 0 à 49 et 50 à 99, état `08cd480` plus le compteur de réceptions par origine) : `.scratch/v2-hauteur-ballon/mesures/02a1-ref-A.json`, `02a1-ref-B.json`, `02a1-bruit-A-B.txt`. Un écart au-delà de ce bruit est documenté et soumis au propriétaire.

**Blocked by:** `v2-collectif/28b` (livré), `v2-collectif/29` (livré).

**Bloque :** 02a2, 02b, 03 ; `v2-attributs-restants/10b`.

**Status:** livré (26/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse (phase 0 comprise) | 25 min |
| Développement | 75 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications (mesures, documentation) | 25 min |
| **Total (travail effectif)** | **2 h 45** |

Confiance : moyenne. Hypothèses : le freinage exponentiel reste la loi horizontale en vol ; `occasion.py:69` se réécrit sans changer son contrat. Au-delà de 2 h : ni la phase 1 ni la phase 2 ne se livrent seules (une physique non branchée ne se mesure pas ; un branchement sans physique n'existe pas), le découpage s'arrête aux phases internes.
Temps machine, non compté : deux séries de référence de 50 matchs (environ 30 min), une série après (environ 15 min), suite complète (environ 12 min).

## Acceptance criteria

- [x] Constantes validées par le propriétaire avant le code (26/11/2026) ; `MAX_FLIGHT_S` validé en cours de ticket (26/11/2026)
- [x] Vol plafonné : sommet ≤ 24,8 m sur tous les ticks de 50 matchs
- [x] Point le plus haut = `vz0² / 2g` (écart < 2 %) ; durée de vol = `2·vz0 / g` (écart < 1 tick)
- [x] Point de chute d'une passe aérienne à ± 1 m de sa cible
- [x] Rebond : hauteur suivante = 0,49 × la précédente (± 5 %) ; le ballon roule quand le sommet suivant passerait sous 0,15 m
- [x] Cas du ballon qui n'arrive pas : test dédié, aucune division par zéro ni logarithme d'un négatif
- [x] Fin de phase 1 : empreintes de trace identiques à la référence `08cd480` à graine fixée
- [x] `z ≥ 0` sur tous les ticks de 50 matchs ; mode tracé cohérent avec `z` (seuil 0,5 m) à chaque enregistrement
- [x] Ordres de grandeur réels (dégagement de gardien, centre, passe lobée : sommet et durée de vol) dans des fourchettes sourcées, ou « non trouvé » noté
- [x] 50 matchs après : passes, interceptions, possession d'équipe, réceptions contrôlées par origine (dont « centre ») dans le bruit mesuré entre les séries A et B ; tout écart au-delà documenté et soumis au propriétaire
- [x] Mêmes empreintes de trace sur deux exécutions à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)

## Résultats (26/11/2026)

**Code** : `v2engine/hauteur.py` (physique pure : chute exacte, rebond, arrêt, durée de vol, plafond, mode) ; `match.py` (lancement `_launch_aerial`, pas du ballon libre, contact seulement si le bas du ballon est à 0,5 m ou moins à l'instant d'entrée dans la portée du joueur, ballon touché ou tenu remis au sol `_ground`) ; `occasion.py` (trajet touchable = instants où `z` passe sous le seuil) ; `ball_state.py` (`z`, `vz` ; `aerial_left_m` retiré) ; `restart.py` (`AERIAL_LANDING_M` retiré) ; `trace.py` (`z` dans `BallSnapshot` et `BallPoint`, format de l'API inchangé). Mesure : compteurs de réceptions par origine et de hauteur (`scripts/v2_indicators.py`, `scripts/measure_v2.py`, `scripts/bench_series.py`).

**Phase 1** : 17 tests unitaires (20 avec le test moteur du point de chute, réserve A1) (`tests/test_v2_hauteur_ballon.py`) ; empreintes de trace identiques à `08cd480` sur 3 matchs de 20 min à graine fixée (moteur lançant tout à `vz0 = 0`).

**Phase 2, invariants (50 matchs, graines 0 à 49)** : 0 tick avec `z < 0` ; 0 tick au mode incohérent avec `z` ; 0 tick au-dessus de 24,9 m ; ballon en l'air 1,5 % des ticks. Déterminisme : mêmes empreintes sur deux exécutions de 2 matchs complets. Après correctif A1 : à nouveau identiques sur deux exécutions (match 0 `acb32a3a4fee9c37`, match 1 `2c47185d3d628ac5`).

**Sommets et durées (2 matchs, avant plafond)** : 27 vols sur 36 entre 2,7 et 12,6 m de sommet pour 25 à 47 m de distance ; 3 vols de 51 à 57 m à 41–57 m et 6 ballons qui n'arrivent pas : origine de `MAX_FLIGHT_S`. Après plafond (4 matchs) : 22 vols plafonnés sur 66 (33 %), dont 12 ballons trop lents pour arriver.

**Ordres de grandeur réels** : sommet et durée de vol mesurés en match **non trouvés**. Majorant : vitesse de frappe de 18 à 35 m/s (revue de biomécanique, PMC3786235), angle de portée maximale d'environ 45° (Linthorne & Patel, JSSM 2011, dégagement du gardien) ; sans traînée, 30 m/s à 45° donne 4,3 s de vol et 23 m de sommet, la traînée ne faisant que réduire ces valeurs : le plafond de 4,5 s (24,8 m) est un majorant physique cohérent.

**Point de chute (réserve A1, corrigée)** : la durée de vol suit maintenant la distance parcourue par le moteur au pas de 0,1 s (Euler explicite sur l'horizontale). Test `test_point_de_chute_dans_le_moteur` : lancé par `_launch_aerial` puis `_step_ball` sans joueur, premier impact à ± 1 m de la cible à 25, 35 et 45 m (avec la loi continue, le test échoue à 45 m : + 1,15 m).

**Tests au niveau du moteur** (le ballon passe par `match.py`, pas seulement par `hauteur.py`) :
- `tests/test_v2_hauteur_ballon.py::test_point_de_chute_dans_le_moteur` (25, 35 et 45 m) : `_launch_aerial` puis `_step_ball` au pas du produit, premier impact à ± 1 m de la cible ;
- `tests/test_v2engine_relance_longue.py::test_lofted_pass_flies_like_a_long_restart_and_is_traced` : la passe en l'air (`_execute`) part au sol avec la vitesse verticale de sa durée de vol au pas du moteur ;
- `tests/test_v2engine_ballon_mort.py::test_ground_player_does_not_touch_an_aerial_ball_except_at_its_landing_point` : un ballon en vol n'est touché qu'en redescendant sous 0,5 m.
Les 17 autres tests de `test_v2_hauteur_ballon.py` portent sur la physique pure (`hauteur.py`). Contrôles sur matchs complets (hors suite) : invariants de hauteur du collecteur (50 matchs), empreintes de trace, espion des durées de vol.

**Vols plafonnés (réserve A2, 10 matchs après correctif, graines 0 à 9)** : 171 vols (17 par match) ; 29 plafonnés (17 %) : 16 ballons qui n'arrivent pas (cible de 30 à 106 m, médiane 46 m ; vitesse 13 à 30 m/s, médiane 22,5) et 13 trop longs (28 à 55 m). Vitesse totale de frappe √(vh² + vz²) au-delà de 35 m/s : 9 vols (5 %), maximum 37,2 m/s ; médiane 27,9 m/s. Script : espion de `hauteur.flight_time_s` (hors dépôt).

**Changement de jeu (tolérance par le bruit mesuré)** : référence A (graines 0 à 49) et B (50 à 99) à `08cd480`, après correctif A1 sur les graines de A (`.scratch/v2-hauteur-ballon/mesures/02a1-tolerance-2.txt`, série `02a1-apres2-A`). La référence A a été relancée avec les nouveaux compteurs (`02a1-ref-A2`) : 0 écart sur les 2 865 indicateurs communs avec A. Sur 2 473 indicateurs, A contre B hors bruit : 64 (2,6 %) ; après contre A : 79 (3,2 %). Première série « après », avant correctif : 72 (2,9 %, `02a1-tolerance.txt`).
- Invariants sur les 50 matchs : 0 tick avec `z < 0`, 0 mode incohérent, 0 tick au-dessus de 24,9 m ; ballon en l'air 1,45 % des ticks.
- Inchangés (dans le bruit) : buts 4,20 → 4,14 par match, passes 1 339 → 1 344, passes réussies 84,2 → 84,1 %, tirs par équipe 14,6 → 13,8, corners 4,1 → 3,8, possession d'équipe 22,2 → 21,9 s, contacts perdus, réceptions au sol, en profondeur, en retrait, de récupération.
- **Hors bruit, attendu** : réceptions contrôlées d'origine « centre » 2,9 → 11,4 par match (10,4 × le bruit). Un ballon reçu pendant ses rebonds compte maintenant comme reçu en l'air (avant, seul le pas d'atterrissage comptait). Changement de classement, pas de volume : le total des réceptions est dans le bruit.
- **Passes longues réussies** : 73,2 → 69,8 % (1,2 × le bruit ; 68,5 %, 1,7 ×, avant correctif A1). Les ballons plafonnés retombent avant la cible et rebondissent, ils sont plus disputés.
- **Réserve A3, ventilée** :
  - tirs d'origine « récupération » : 5,7 → 7,8 % (1,2 × le bruit, B à 6,9 %) ; 9,3 % (2,0 ×) avant correctif : dans le bruit ;
  - tirs à xG < 0,03 (compteur « tirs par tranche d'xG », par origine) : 109 tirs et 1 but (passe au sol) avant, 112 tirs et 3 buts (2 dribbles, 1 passe au sol) après. Aucun but de centre ni de rebond : rien de lié à la hauteur. Le « 3,2 × le bruit » (tireurs moyens, 0 but sur 53 tirs → 1 sur 49) est un artefact de petit effectif : avec 0 but en A et B, le bruit estimé est quasi nul et un seul but le dépasse. Tous tireurs confondus : 0,8 × le bruit. À suivre au `22c`.

## Comments

**26/11/2026, passage 1 de `/valider-ticket-simulafoot`** : expert `APPROVED_WITH_RESERVATIONS`, QC non lancé ; pas de clôture. Réserves :
- **A1** : point de chute 2,6 % au-delà de la cible (loi continue contre intégration au pas du moteur). Corrigée : durée de vol au pas du moteur (`flight_time_s(..., dt)`), test au niveau du moteur à 25, 35 et 45 m.
- **A2** : vol plafonné fréquent, et un ballon qui n'arrive pas part au vol maximal même lent. Re-mesuré sur 10 matchs : 17 % de vols plafonnés (et non 33 %), 5 % au-delà de 35 m/s de vitesse totale. Comportement conforme au ticket (constante validée), à revoir à l'écran au `02b` et rendu caduc par le `v2-realisme/14a` (note ajoutée à ce ticket).
- **A3** : deux écarts hors bruit inexpliqués. Re-mesurés après correctif et ventilés : origine « récupération » revenue dans le bruit (1,2 ×) ; buts à xG < 0,03 = 2 buts de plus sur 50 matchs, issus de dribbles, artefact de petit effectif (détail dans Résultats). À suivre au `22c`.
- **A4** (facultatif, non traité) : ballon touchable les 0,02 à 0,05 premières secondes du vol ; facteur 0,85 appliqué en fin de pas ; un tick de porteur avec ballon en hauteur après un coup franc pour hors-jeu.

**26/11/2026, passage 2 de `/valider-ticket-simulafoot`** : expert `APPROVED_WITH_RESERVATIONS` (rapport sur l'empreinte `e531e8f8…`), QC `VALIDÉ`. Ancienne A1 corrigée, ancienne A3 expliquée ; une réserve restante :
- **A1 (ancienne A2) — vols plafonnés, 17 %** : acceptée par le propriétaire : « Point 1 accepté. Documenter la non-pertinence du plafond de vitesse (5 % du problème). Ajouter dans 02b : clôture conditionnée à 14a. »
  - **Plafond de vitesse non retenu** : borner la vitesse totale de frappe √(vh² + vz²) à 35 m/s ne toucherait que 9 vols sur 171 (5 %), alors que 29 (17 %) sont plafonnés, dont 16 ballons lents qui n'arrivent pas et partent pourtant au vol maximal. Le défaut vient de la loi horizontale (freinage exponentiel, durée de vol infinie ou divergente pour les ballons longs), pas de la vitesse de frappe : il se corrige au `v2-realisme/14a`, pas par une borne ici.
  - `02b` : clôture conditionnée à la livraison du `14a` ; critères « à vérifier à l'écran » ajoutés.
- **Écart « centre » (réceptions 2,9 → 11,4 par match)** : accepté sous condition par le propriétaire : « Point 2 accepté sous condition : spot check de 20 réceptions « centre » sur trace. Documenter le résultat (correct / à investiguer au 02c). »
  - **Résultat du contrôle : à investiguer au 02c** (ticket à créer). 20 réceptions « centre » relues sur la piste du ballon (graines 0 à 2, script hors dépôt `centres.py`) : les 20 sont des ballons en fin de petits rebonds, reçus 4,7 à 10 s après la frappe, à 0,1 à 1,5 m/s, le bas du ballon entre 0 et 0,46 m au point précédent ; 1 à 3 rebonds pour 16 d'entre eux ; 3 non visés, issus de vols plafonnés (sommet 21,7 à 24,8 m). Aucune n'est une réception en l'air au sens du football (tête, poitrine, volée à la première retombée).
  - Cause : `airborne = z > 0 or vz != 0` au début du pas (`_step_loose_ball`) classe en « centre » tout ballon qui sautille encore, même de quelques centimètres ; avant le ticket, seul le pas d'atterrissage d'un ballon en mode aérien comptait. Effets : origine « centre » des réceptions et des tirs surévaluée, contrôle de première interdit sur ces ballons (`first_time = intended and not airborne`). Pistes pour le 02c : « centre » réservé à la première retombée d'un ballon lancé en l'air, ou au bas du ballon au-dessus d'un seuil à l'instant du contact.
- Facultatif, non traité : A2 (écart xG < 0,03, à suivre au `22c`), A3 (`_launch_aerial` lit `TICK_SECONDS` et non le pas d'une simulation lancée avec un autre pas ; sans effet au pas du produit), A4 (simplifications sans effet mesurable, reportées dans les critères d'écran du 02b).
- Clôture : `VALIDÉ` (journal `.claude/qc/journal.jsonl`), réserves acceptées comme ci-dessus.

**Durée** : estimée 2 h 45, réelle environ 4 h 40 (+ 70 %), non chronométrée (horloge de la session hors attentes machine). Postes : analyse 40 min (25), développement 90 min (75), tests 45 min (40), intégration, mesures et revues 105 min (25). Causes : constante nouvelle découverte en cours (`MAX_FLIGHT_S`, vols de 41 à 57 m de sommet) ; tolérance par le bruit mesuré (deux séries de référence, outil de comparaison) ; deux passages de revue avec correctif A1, re-mesures A2 et A3, contrôle des réceptions « centre ». Temps machine hors total : quatre séries de 50 matchs (environ 45 à 75 min chacune), une série perdue (manque de mémoire, deux séries lancées en parallèle), trois suites complètes (15 min chacune).
