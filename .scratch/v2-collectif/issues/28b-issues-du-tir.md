# 28b: Issues du tir : contré, capté, repoussé, claqué

**Découpé du ticket 28 le 04/11/2026** (audit de granularité). Détail : `28-occasion-et-issue-du-tir.md`, points 5 et 7 (partie tir).

**What to build:**

1. **Issues du tir** : but, à côté, contré, arrêté. L'arrêt se décline selon la situation (force, angle, hauteur, distance) : **capté**, **repoussé** (devant, sur le côté, en l'air : le ballon libre part selon la direction et la force du tir, seconds ballons), **claqué** en corner ou en sortie de but (remises en jeu du ticket 29). Le contre minimal du ticket 33 est remplacé.
2. Notes du gardien : part neutre sans attribut jusqu'à `v2-attributs-restants/03` (A8 n'est pas levée à moitié).
3. **Trace** : pour un tir, tireur, position, qualité de l'occasion (28a), issue, origine (passe au sol, en retrait, en profondeur, centre, dribble, rebond). Le rendu 2D rejoue l'issue enregistrée.

**Attributs :** aucun nouveau (gardien neutre).

**Blocked by:** 28a.

**Bloque :** `v2-hauteur-ballon/02a` (trajectoire qui respecte l'issue), `v2-attributs-restants/10a`, `v2-attributs-restants/11` ; 17, 19, 22a.

**Status:** livré (05/11/2026), validé expert + QC

## Acceptance criteria

- [x] Constantes produit (part des parades repoussées, répartition capté / repoussé / claqué) validées par le propriétaire avant le code (par délégation, 05/11/2026)
- [x] Les issues existent en match : but, à côté, contré, capté, repoussé, claqué
- [x] Test de cohérence : l'arrêt claqué en corner est plus fréquent sur un tir puissant et excentré que sur un tir central faible, où le gardien capte ; la direction de la repoussée dépend de la direction du tir
- [x] (amendé le 05/11/2026, réserve A1 de l'expert acceptée par délégation du propriétaire : « Je valide automatiquement toutes les recommandations et avis d'expert » ; mesuré 14,5 corners et 24,7 touches, cibles reportées aux tickets 11 et 22a, corners à remesurer après le 22a) Repris du ticket 29 (réserve A2 acceptée le 03/11/2026) : corners 6 à 14 par match et touches 30 à 55 par match (50 matchs, graine d'audit) ; au ticket 29 : 0,84 corner et 22,7 touches
- [x] (amendé le 05/11/2026, même réserve A1 acceptée par délégation : cadrés 32,8 % atteint ; contrés 18,1 %, conversion 5,7 %, buts dans la surface 54,7 % reportés aux tickets 22a et 22c, cause antérieure : 37,6 tirs par équipe) En match : tirs cadrés (30-35 %), tirs contrés (20-28 %), conversion (10-11 %), part des buts dans la surface (80-90 %), comparés aux indicateurs à sourcer
- [x] Indicateurs ajoutés au banc (`scripts/v2_indicators.py`) et définis dans `docs/INDICATEURS_V2.md`
- [x] Déterminisme à graine fixée (`test_shot_trace_is_reproducible_at_fixed_seed`) ; suite complète verte (2 378 passés, 13 désélectionnés, 05/11/2026) ; V1 inchangée (aucun fichier V1 ni fichier protégé dans le diff)

## Constantes (proposées le 05/11/2026 ; validées par délégation du propriétaire)

**Ce qui existe déjà et ne change pas** : contré (géométrie du cône, `BLOCK_WIDTH_M` 1 m, `BLOCK_CHANCE` 0,6, ticket 28a ; le « contre minimal » du 33 est déjà remplacé par le cône) ; à côté (`SHOT_WIDE_SHARE` 0,64 des tirs non convertis, ticket 29) ; but (`shot_probability`, 28a). Le 28b ne touche qu'au **tir cadré non converti**, aujourd'hui toujours remis au gardien.

**Sources** : Opta classe chaque arrêt en *caught, collected, parried safe, parried danger, fumble, fingertip* ([définitions Opta](https://www.statsperform.com/opta-event-definitions/)) mais ne publie pas de répartition ; aucune étude publique trouvée sur la part des arrêts suivis d'un second ballon ([StatsBomb, gardiens](https://blogarchive.statsbomb.com/articles/soccer/intro-to-goalkeeper-analysis/) : non). Origine des corners : environ 20 % viennent d'un arrêt dévié par le gardien (relevé de 200 matchs PL et Championship, [blog de paris](https://leaguebettips.com/articles/corners-betting-football/), sans méthode publiée : ordre de grandeur). Le reste est **non trouvé, ordre de grandeur**.

| Constante | Valeur | Rôle |
|---|---|---|
| `SAVE_DIFFICULTY_REF` | 0,30 | Chance de but (28a) au-delà de laquelle l'arrêt est « difficile » au maximum : difficulté = min(1, chance / 0,30) |
| `SAVE_HELD_SHARE` | (0,70 ; 0,25) | Part des arrêts **captés** : 70 % pour un tir facile (chance ≈ 0), 25 % pour un tir difficile, interpolation linéaire en difficulté |
| `SAVE_OUT_SHARE` | (0,25 ; 0,60) | Parmi les arrêts **non captés**, part **claquée hors du terrain** : 25 % pour un tir central, 60 % pour un tir excentré ; excentrement = \|écart latéral du tireur au centre du but\| / 20 m, borné à 1. Le reste est **repoussé** en jeu |
| `PARRY_SPEED_SHARE` | (0,25 ; 0,50) | Repoussé ou claqué : vitesse du ballon après la parade, en part de la vitesse du tir, tirée au hasard dans l'intervalle |
| `PARRY_ANGLE_DEG` | (25 ; 80) | Repoussé : le ballon repart vers le côté **d'où vient le tir prolongé** (un tir vers le poteau gauche est repoussé à gauche), entre 25° et 80° de l'axe de la ligne de but vers le terrain ; tir central (excentrement < 0,1) : côté tiré au hasard, angle 25° à 90° (jusqu'à « devant », dans l'axe) |
| `TIP_WIDE_M` | (0,5 ; 3) m | Claqué : point de sortie visé derrière la ligne, au-delà du poteau du côté où file le tir (ajoutée au code, ordre de grandeur) |
| `SAVE_EXCENTRIC_REF_M` | 20 m | Écart latéral du tireur à l'axe qui fait un tir « le plus excentré » (explicite la formule ci-dessus) |
| `DRIBBLE_ORIGIN_M`, `DEEP_ORIGIN_M` | 5 m, 10 m | Origine d'un tir, trace seulement : « dribble » si le tireur a porté le ballon plus de 5 m depuis son contrôle ; passe « en profondeur » si elle a fait gagner 10 m ou plus vers le but, « en retrait » si elle en a fait perdre, « centre » si elle est arrivée en l'air (ordres de grandeur, ajoutées au code) |
| `PARRY_BAN_S` | `MISS_RETRY_S` (existante) | Le gardien ne peut pas reprendre immédiatement le ballon qu'il vient de repousser (même mécanisme que le contre) |

Un ballon claqué derrière la ligne de but est toujours un corner (loi 17, le gardien touche en dernier) : pas de constante ; une sortie en touche, rare, émerge de la direction donnée par `PARRY_ANGLE_DEG`.

**Pourquoi ces valeurs** : un tir lointain et central (le plus fréquent aujourd'hui) est capté à près de 70 % : le gardien a le temps et le ballon arrive dans l'axe. Un tir proche et dangereux n'est capté qu'une fois sur quatre : réflexe, parade du bout des gants. Un tir excentré est plus souvent claqué en corner, car le gardien pousse vers l'extérieur plutôt que de risquer de remettre le ballon dans l'axe. Ordre de grandeur attendu sur le moteur actuel : environ 45 % des arrêts captés, 30 % repoussés, 25 % claqués en corner, soit 1 à 3 corners par match venant des arrêts (environ 20 % des corners réels, cohérent avec la source ci-dessus) ; le reste des corners viendra des tirs contrés, des dégagements et des centres.

**Hors de ce ticket** : la force du tir (constante 30 m/s) et sa hauteur n'existent pas encore ; la difficulté passe par la chance de but et l'excentrement. Elles s'ajouteront avec `v2-hauteur-ballon/02a` et `v2-attributs-restants/10a`. Les notes du gardien (Handling pour capter, Reflexes, Kicking/Punching pour claquer) restent au ticket `v2-attributs-restants/03b` : part neutre ici (A8).

## Durées estimées

| Travail | Durée |
|---|---|
| Code (`shooting.py` : issue de l'arrêt ; `match.py` : capté, repoussé, claqué ; trace : origine et issue du tir) | ≈ 2 h |
| Tests (scène contrôlée : claqué plus fréquent sur un tir excentré et dangereux, direction de la repoussée ; déterminisme) | ≈ 45 min |
| Indicateurs au banc et `INDICATEURS_V2.md` | ≈ 30 min |
| Mesure en match, 50 matchs (graine d'audit) | ≈ 2 h 45 |
| Suite complète | ≈ 80 min (≈ 40 min seule, plus si une mesure tourne en même temps) |
| Clôture `/valider-ticket-simulafoot` (expert + QC) | ≈ 30 min |
| **Total** | **≈ 7 h 30**, dont ≈ 4 h de calcul pendant lesquelles tu n'as rien à faire |

## Réalisation (05/11/2026)

- `shooting.py` : `save_shares`, `save_outcome` (capté, repoussé, claqué selon la difficulté et l'excentrement), `parry_velocity` (direction et vitesse du ballon repoussé ou claqué). Gardien neutre (A8).
- `match.py` : un tir cadré non converti n'est plus toujours remis au gardien. Capté : le gardien a le ballon ; repoussé : ballon libre, le gardien ne peut le reprendre qu'après `MISS_RETRY_S` ; claqué : le ballon file derrière la ligne, corner (dernier toucheur : le gardien). Parade instantanée, au gardien (ponytail : la trajectoire jusqu'à lui viendra avec la hauteur du ballon, `v2-hauteur-ballon/02a`). Origine du tir suivie dans `BallState` (`pass_from`, `rebound`, `came_from`).
- `trace.py` : `ShotEvent` (tireur, lieu, qualité de l'occasion du 28a, issue, origine), `MatchTrace.shots` ; penaltys tracés aussi.
- Banc : `Collector.on_shot_event`, indicateurs « Issues du tir », « Buts dans la surface », « Issues des arrêts », « Origine des tirs », « Qualité moyenne de l'occasion » (`docs/INDICATEURS_V2.md`).
- Rendu 2D (point 3) : il rejoue l'issue enregistrée par la trajectoire du ballon de la trace (`Tick.ball`), sans code nouveau ; `MatchTrace.shots` n'est pas exposé par l'API (A6 de l'expert, facultatif : à brancher avec la narration ou `v2-hauteur-ballon/02b`).
- Ballon claqué : environ 39 % franchissent la ligne entre les poteaux (gardien devant sa ligne) ; lu comme un ballon claqué au-dessus de la barre, corner (réserve A2 de l'expert, documentée dans `parry_velocity`, vraie hauteur avec `v2-hauteur-ballon/02a`).
- Tests : `tests/test_v2engine_issues_tir.py` (6) ; `test_missed_shot_gives_ball_to_the_opposing_keeper` adapté (arrêt forcé à « capté »).
- Correctif en passant (`match.py`) : la trace des situations enregistrait d'office la situation au début de chaque période, même inchangée (introduit avec le ticket `v2-coach-et-gestion-de-match/03`, 614b1d5). La nouvelle suite de tirages du 28b a fait tomber `test_trace_records_only_changes` sur ce doublon à la mi-temps ; la trace ne garde plus que les changements, d'une période à l'autre aussi. Simulation inchangée.

## Mesure en match (05/11/2026, 50 matchs, graine d'audit 20260923, avant = 924b350, après = arbre de travail)

| Indicateur | Avant | Après | Cible |
|---|---|---|---|
| Corners par match | 12,5 | 14,5 | 6 à 14 (dépassée de 0,5) |
| Touches par match | 24,9 | 24,7 | 30 à 55 (non atteinte, inchangée) |
| Sorties de but par match | 30,3 | 31,1 | |
| Tirs tracés par équipe (contrés compris) | — | 37,6 | réel environ 12 |
| Tirs cadrés (part) | — | 32,8 % | 30 à 35 % ✓ |
| Tirs contrés (part) | — | 18,1 % | 20 à 28 % (légèrement sous) |
| Tirs à côté (part) | — | 49,1 % | |
| Conversion des tirs | — | 5,7 % | 10 à 11 % (non atteinte) |
| Buts dans la surface (part) | — | 54,7 % | 80 à 90 % (non atteinte) |
| Qualité moyenne de l'occasion | — | 0,053 | |
| Arrêts par match | — | 20,3 | |
| Arrêts captés / repoussés / claqués | — | 62 % / 23 % / 15 % | ordre de grandeur attendu 45 / 30 / 25 |
| Origine des tirs : dribble / récupération / passe au sol / en profondeur / en retrait / rebond / centre | — | 52 / 20 / 12 / 9 / 5 / 1,8 / 0,2 % | |
| Buts par match | 4,44 | 4,30 | |
| Temps de calcul par match (s) | 388 | 386 | |

Les autres indicateurs du banc bougent dans le bruit d'une autre suite de tirages (passes, pressing, bloc, appels : écarts de 1 à 3 %). « Coups francs du dernier tiers frappés au but » passe de 23 % à 6 % sur 2 à 4 cas par lot : bruit, le code des coups francs n'est pas touché.

**Lecture** : le 28b fait ce qu'il doit (arrêts déclinés, corners +2 par match venant des parades claquées, seconds ballons après les parades repoussées). La référence du ticket 29 (0,84 corner) était périmée : le moteur en donnait déjà 12,5 avant le 28b. Les critères non atteints (touches, conversion, buts dans la surface, contrés) ne dépendent pas des issues du tir mais du volume et de l'éloignement des tirs (37,6 tirs par équipe, trois fois le réel) : réserves reportées aux tickets 22a (volumes) et 22c (tirs, buts), comme celles du 28a ; touches au ticket 11 et 22a. Captés plus nombreux qu'attendu (62 % contre 45 %) parce que la plupart des tirs sont lointains et faciles (qualité moyenne 0,053) : la répartition suivra quand le volume de tirs lointains baissera.

## Comments

- 05/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (A1 critères de match non atteints, reportés 22a, 22c, 11 ; A2 ballon claqué entre les poteaux, documenté ; A3 case de déterminisme non cochée, cochée ; facultatifs A4 commentaire de test corrigé, A5 repoussée un peu longue, A6 tirs absents de l'API). Réserves acceptées par délégation du propriétaire : « Je valide automatiquement toutes les recommandations et avis d'expert ». QC REFUSÉ (critères non atteints sans acceptation écrite, case non cochée, rejeu 2D non précisé) : corrigé dans le ticket. Clôture non prononcée, nouveau passage.
- 05/11/2026, passages 2 et 3 : QC VALIDÉ (motifs du REFUSÉ levés). Expert APPROVED_WITH_RESERVATIONS au passage 2, confirmé au passage 3 sur la liste des fichiers revus réduite au code, aux tests et au banc (ticket et `docs/` en suivi documentaire), empreinte e29a4bf3. Réserves : A1 cibles de match reportées aux tickets 22a, 22c et 11 (remesurer corners et répartition des arrêts après le 22a) ; A2 ballon claqué entre les poteaux, lu comme au-dessus de la barre (`v2-hauteur-ballon/02a`). Acceptées par délégation du propriétaire : « Je valide automatiquement toutes les recommandations et avis d'expert ». Facultatifs : A3 origine d'un tir périmée après un tacle (`came_from`), A4 repoussée un peu longue, A5 tirs absents de l'API. **Clôture VALIDÉ.**
