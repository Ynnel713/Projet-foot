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

**Status:** à faire

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

- [ ] Test de scène : ballon à 17, 47, 76 et 92 m de son but, porteur non gardien : dernière ligne de référence à 22,3 / 37,3 / 51,8 / 55 m (à 0,5 m près)
- [ ] Test : plancher de 15 m et plafond de 55 m respectés
- [ ] Mesure sur le banc (mêmes graines que le constat) : centraux à 32 m au moins de leur but quand le ballon est entre 40 et 55 m (aujourd'hui 18,5 à 21,2 m)
- [ ] Mesure : centraux plus hauts avec ballon que sans ballon, à position du ballon égale (inverse du constat du 02h)
- [ ] Tirs, buts, xG, récupérations hautes et hors-jeu par match rapportés avant et après ; tout écart de plus de 10 % est signalé au propriétaire
- [ ] Sans ballon : comportement inchangé (mêmes hauteurs de ligne qu'avant, test existant)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
