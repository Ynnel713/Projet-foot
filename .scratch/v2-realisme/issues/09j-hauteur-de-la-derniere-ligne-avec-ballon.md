# 09j: Hauteur de la dernière ligne avec ballon

**Chantier :** `v2-realisme` (audit du 16/11/2026, retour du propriétaire après un match à l'écran : « les défenseurs centraux de l'équipe qui a le ballon jouent quasiment au niveau du gardien »). **Priorité :** P0 (problème tactique majeur, directive du propriétaire du 16/11/2026). **Catégorie :** placement.

**Constat vérifié (16/11/2026) :**
- Avec ballon, aucune règle ne fixe la hauteur de la dernière ligne. `Bloc.reference` (`v2engine/bloc.py`) centre le bloc sur le centre de la forme du coup d'envoi (rangée dans sa propre moitié, `formation._DEPTH_SPAN_M = 40`). Le bloc suit la moitié du déplacement du ballon (`BLOCK_SHIFT[0] = 0.5`), plus une avance fixe de 8 m (`POSSESSION_ADVANCE_M`). Sans ballon, au contraire, le bloc se cale sur la hauteur de sa dernière ligne (`LINE_HEIGHT_M = 35`, ticket `v2-collectif/05`).
- Le ticket 02h l'avait relevé (« défenseurs centraux plus hauts sans ballon, 29,5 m, qu'avec, 26,6 m »), sans créer de ticket.
- Mesure : moyennes sur la 1re période de deux matchs (graines 20260923 et 20260924, clubs[0]-clubs[1] et clubs[2]-clubs[3]). Distances depuis le but de l'équipe qui a le ballon, gardien porteur exclu :

| Ballon | Centraux | Milieux (MDC, MC, MOC) | Attaque | Écart défense-milieu |
|---|---|---|---|---|
| 17 m | 8,0 à 8,2 | 23 à 26 | 44 à 46 | 15 à 18 |
| 33 m | 12,6 à 15,9 | 30 à 32 | 48 à 51 | 16 à 17 |
| 47 m | 18,5 à 21,2 | 36 à 37 | 51 à 55 | 16 à 17 |
| 62 m | 25,1 à 26,0 | 43 | 58 à 62 | 17 à 18 |
| 76 m | 31,1 à 33,1 | 49 à 52 | 66 à 71 | 18 à 19 |
| 92 m | 39,5 à 42,3 | 57 à 61 | 75 à 82 | 17 à 18 |

- Ce n'est pas seulement la défense qui reste basse : **tout le bloc reste derrière le ballon** (attaque au niveau du ballon, voire derrière). Faire suivre la ligne de milieu par la défense ne suffirait pas, puisque le milieu est lui aussi bas (36 m quand le ballon est à 47 m).

**What to build:** avec ballon, le bloc se cale sur une hauteur de dernière ligne `H`, comme sans ballon (même mécanique : `cx = H - shape.back * sx`) :

`H = clamp(LINE_HEIGHT_WITH_BALL_M + (ballon - 52,5) x LINE_BALL_FOLLOW, LINE_MIN_WITH_BALL_M, LINE_MAX_WITH_BALL_M)`, où `ballon` est la distance du ballon au but de l'équipe.

Tout le bloc monte avec elle (milieu et attaque compris), avec les décalages des rôles (02d) à l'intérieur. L'écart défense-milieu est ensuite tenu entre 10 et 15 m (cible 12 m). Cette contrainte est celle du ticket 09e (« distances entre les lignes en possession ») : elle y est reportée, voir la note du 16/11/2026 dans 09e. `POSSESSION_ADVANCE_M` (utilisé seulement à `bloc.py:291`) est remplacé par ce calage. Les deux corrections de la hauteur sans ballon (`Bloc.update` : modulation selon la pression sur le porteur, plafond lié à l'attaquant adverse le plus avancé `TRAP_DEPTH_M` avec rabaissement selon Pace) ne s'appliquent **pas** avec ballon : se protéger du contre relève de la défense préventive (09g). Le retard de réaction des joueurs au Teamwork faible (`line_lag_s`) s'applique aussi avec ballon.

Valeurs que la formule donnerait, à comparer aux centraux mesurés :

| Ballon | H proposée | Centraux aujourd'hui |
|---|---|---|
| 17 m | 22,3 m | 8 m |
| 33 m | 30,3 m | 13 à 16 m |
| 47 m | 37,3 m | 18 à 21 m |
| 62 m | 44,8 m | 25 à 26 m |
| 76 m | 51,8 m | 31 à 33 m |
| 92 m | 55 m (plafond) | 40 à 42 m |

**Hors de ce ticket :** placement de construction depuis le gardien et les centraux (25b, qui pourra baisser `H` sur sortie de but) ; écarts entre les lignes (09e) ; défense préventive face au contre (09g) ; hauteur sans ballon (déjà en place).

**Attributs :** Teamwork (retard de la ligne perçue, déjà en place via `line_lag_s`) ; aucun nouvel attribut.

**Constantes validées par le propriétaire le 16/11/2026 (« je valide ») :**
- `LINE_HEIGHT_WITH_BALL_M` = **40 m** : dernière ligne quand le ballon est au rond central (sans ballon : 35 m).
- `LINE_BALL_FOLLOW` = **0,5** : la ligne monte de 0,5 m quand le ballon avance de 1 m (même suivi que `BLOCK_SHIFT[0]`).
- `LINE_MIN_WITH_BALL_M` = **15 m** : plancher, ballon dans son propre tiers (25b l'affinera pour la construction).
- `LINE_MAX_WITH_BALL_M` = **55 m** : plafond (2,5 m au-delà de la ligne médiane), atteint dès que le ballon est à 82,5 m de son but, soit 22,5 m du but adverse.
- Écart défense-milieu : **10 à 15 m, cible 12 m** (directive du propriétaire), reporté au 09e.
- Chiffres réels : ordres de grandeur courants (ligne défensive vers 35 à 50 m de son but en possession installée), **non vérifiés dans une source**. Le ticket `27b` (distributions de référence du suivi) donnera les vrais chiffres ; recalibrer alors si besoin.

**Risque :** le bloc qui monte change les volumes. Le ticket 02d a mesuré qu'1 m de bloc en plus donne environ 1,4 tir par équipe. Tirs, buts et récupérations hautes sont mesurés avant et après ; une recalibration (famille 18) peut être nécessaire, sous un ticket séparé.

**Blocked by:** 02d (livré), 02e (livré).

**Bloque :** 09e (l'écart entre lignes se règle sur le bloc remonté), 09h, 25b.

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 45 min |
| Intégration et vérifications (mesures avant et après) | 35 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : moyenne. Hypothèses : la mécanique de calage sur la ligne existe déjà sans ballon dans `Bloc.reference` et se réutilise ; pas de changement de `formation.py`. Au-dessus du seuil de 2 h : découpage examiné. L'écart entre les lignes est sorti vers 09e ; le reste (formule, bornes, mesures) est indivisible.
Temps machine, non compté : suite complète ; mesures `scripts/measure_v2.py` et `scripts/v2_indicators.py` avant et après (séries de matchs).

## Acceptance criteria

- [x] Test de scène : ballon à 17, 47, 76 et 92 m de son but, porteur non gardien : dernière ligne de référence à 22,3 / 37,3 / 51,8 / 55 m (à 0,5 m près)
- [x] Test : plancher de 15 m et plafond de 55 m respectés
- [x] Mesure sur le banc (mêmes graines que le constat) : centraux à 32 m au moins de leur but quand le ballon est entre 40 et 55 m (aujourd'hui 18,5 à 21,2 m)
- [x] Mesure : centraux plus hauts avec ballon que sans ballon, à position du ballon égale (inverse du constat du 02h) — **partiel, accepté par le propriétaire le 16/11/2026** (réserve A2 de l'expert, « J'accepte A1, A2 et A3 ») : 5 tranches sur 6 ; tranche 10-25 m 18,4 contre 18,9 m, renvoyée au 25b et au 18l
- [x] Tirs, buts, xG, récupérations hautes et hors-jeu par match rapportés avant et après ; tout écart de plus de 10 % est signalé au propriétaire
- [x] Sans ballon : comportement inchangé (mêmes hauteurs de ligne qu'avant, test existant)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (16/11/2026)

- `v2engine/bloc.py` : constantes `LINE_HEIGHT_WITH_BALL_M` (40), `LINE_BALL_FOLLOW` (0,5), `LINE_MIN_WITH_BALL_M` (15), `LINE_MAX_WITH_BALL_M` (55) ; `with_ball_line(team, ball_x)` ; `Bloc.update` calcule à chaque tick la ligne avec ballon de chaque équipe (`lines_ball`) et sa courte mémoire (`line_history_ball`), sans pression ni attaquant adverse ; `_line_for(..., with_ball)` applique le même retard `line_lag_s` ; `Bloc.reference` cale le bloc avec ballon sur cette ligne (`cx = H - shape.back * sx`, forme décalée par les rôles du 02d). Sans mise à jour préalable (scène de test), la ligne du ballon donné. `POSSESSION_ADVANCE_M` supprimé. `Bloc.lines` (sans ballon) inchangé : `cerveau.py` (gardien, 03c) et le banc le lisent toujours.
- Tests : 4 ajoutés (`tests/test_v2engine_bloc.py` : ligne aux 4 positions du ticket pour les deux équipes, plancher et plafond, ni pression ni attaquant adverse avec ballon, retard au Teamwork faible) ; 2 adaptés :
  - `test_the_block_moves_up_when_the_team_has_the_ball` : le décalage fixe de 8 m n'existe plus ; le bloc avec ballon reste plus haut que sans.
  - `test_roles_redistribute_inside_the_block_without_moving_or_resizing_it` : le bloc avec ballon se cale désormais sur sa dernière ligne, comme sans ballon (prescrit par le ticket), et non plus sur son centre : l'invariant devient « dernière ligne sur `H`, longueur et largeur inchangées ». Conséquence : un rôle qui recule derrière les centraux (latéral défensif, −3 m) devient la dernière ligne et les centraux sont 3 m plus haut.
  - `tests/test_v2engine_garde_attributs.py` (Stamina) : scène de 60 à 120 s. Stamina agit toujours (première divergence graine 21 en 60 s, graine 2 à 67 s de jeu en 120 s) ; la ligne remontée retarde le premier sprint qui puise dans la réserve.

**Mesures :**

Hauteurs moyennes depuis son but, 1re période des deux matchs du constat (graines 20260923 et 20260924, clubs[0]-clubs[1] et clubs[2]-clubs[3], script hors dépôt `lignes_09j.py`) ; colonnes : ballon, centraux, milieux, attaque :

| Ballon | Avec ballon avant | Avec ballon après | Sans ballon après |
|---|---|---|---|
| 10-25 m | 18,4 / 8,4 / 25,3 / 44,9 | 19,4 / 18,4 / 31,8 / 47,4 | 19,3 / 18,9 / 28,1 / 41,1 |
| 25-40 m | 33,0 / 13,2 / 30,7 / 48,8 | 33,6 / 29,3 / 43,5 / 58,6 | 33,0 / 28,5 / 38,5 / 48,8 |
| 40-55 m | 47,3 / 19,3 / 36,6 / 53,4 | 47,5 / **37,3** / 51,7 / 66,4 | 48,2 / 34,2 / 47,3 / 54,7 |
| 55-70 m | 62,0 / 25,7 / 43,0 / 60,8 | 61,9 / 42,0 / 58,5 / 70,0 | 61,5 / 37,4 / 53,6 / 60,5 |
| 70-85 m | 76,2 / 31,6 / 49,4 / 68,9 | 76,1 / 48,3 / 66,5 / 78,0 | 75,9 / 46,6 / 63,2 / 72,6 |
| 85-105 m | 91,9 / 39,7 / 56,9 / 79,2 | 90,4 / 53,7 / 72,2 / 88,5 | 89,4 / 52,6 / 69,1 / 83,0 |

- Centraux à 37,3 m (≥ 32) quand le ballon est entre 40 et 55 m. Avec ballon plus hauts que sans dans 5 tranches sur 6 ; **écart** dans la tranche 10-25 m (18,4 contre 18,9 m) : renvoyé au placement de construction (25b) et au suivi 18l. Écart défense-milieu 13 à 18 m : réglé au 09e.

Série de 20 matchs (`scripts.bench_series`, graines du banc, indicatif), avant (`443e8c9`) et après ; écarts de plus de 10 % signalés au propriétaire le 16/11/2026 :

| Par match | Avant | Après |
|---|---|---|
| Buts | 4,35 | 6,8 (+56 %) |
| Hors-jeu | 0,7 | 4,1 |
| xG neutre / après frappe | 5,03 / 4,54 | 6,45 / 6,56 |
| Tirs par équipe | 21,0 | 22,2 (non significatif) |
| Tirs de près (16 m) par équipe | 4,75 | 7,25 |
| Tirs après récupération dans le camp adverse (faute d'indicateur « récupérations hautes ») | 24,45 | 12,75 |
| Passes | 1 089 | 1 280 |
| Pertes de balle | 215 | 259 |
| Pressings suivis d'une récupération en 5 s (part) | 0,192 | 0,221 |

Décision du propriétaire (16/11/2026) : « Clôturer + ticket suivi » : recalibration et analyse des buts en plus au ticket `18l` (après 09e et 25b).

Suite complète : 3 181 passés, 0 ignoré, 14 désélectionnés (3 177 + 4 ; une première exécution avait 1 échec, la garde Stamina, adaptée ci-dessus) ; `CLAUDE.md` mis à jour.

Déterminisme : deux exécutions à graine fixée (30 min de jeu) : mêmes empreintes (événements `c01257b02933d347`, ticks `2f83a619f2e3533d`).

**Durée :** estimée 2 h 30 ; réelle environ 1 h 10 de travail effectif (analyse 20, développement 15, tests 15, intégration et vérifications 20), à l'horloge de la session, non chronométrée ; écart − 53 %. Cause : la mécanique de calage existait déjà sans ballon et s'est réutilisée telle quelle (une fonction, deux champs) ; les mesures « avant » ont tourné pendant le développement. Temps machine hors total : deux séries de 20 matchs (16 et 17 min), deux mesures de lignes, deux suites complètes (13 min 37 chacune), recherche de la divergence Stamina (environ 10 min).

## Comments

- **16/11/2026, passage 1** — Expert : `APPROVED_WITH_RESERVATIONS`. QC : `REFUSÉ` (critère « centraux plus hauts avec ballon que sans » décoché, sans accord du propriétaire tracé dans le ticket). Réserves de l'expert, **acceptées par le propriétaire le 16/11/2026 (« J'accepte A1, A2 et A3 (Recommandé) »)** :
  - A1 : buts 4,35 → 6,8 par match (+56 %), renvoyés au ticket 18l (série de 50 matchs, après 09e, 25b, éventuellement 09g) ; décision antérieure du propriétaire : « Clôturer + ticket suivi ».
  - A2 : critère « plus hauts avec ballon que sans » partiel (tranche 10-25 m : 18,4 contre 18,9 m ; cible plus haute par construction, écart dynamique), renvoyé au 25b et au 18l.
  - A3 : ligne haute sans protection contre le contre (prescrit par le ticket) : 09g à planifier avant ou pendant le 18l.
  - A4 facultatif : garde Stamina passée de 60 à 120 s ; à surveiller si elle redevient fragile.
- **16/11/2026, passage 2** — QC : `VALIDÉ` (accord du propriétaire tracé). Clôture journalisée : `VALIDÉ` (expert APPROVED_WITH_RESERVATIONS, réserves A1 à A3 acceptées par le propriétaire, QC VALIDÉ). Code inchangé depuis le passage 1.
