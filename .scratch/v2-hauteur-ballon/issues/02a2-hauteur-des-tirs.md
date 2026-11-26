# 02a2: Hauteur du ballon dans le moteur : tirs

**Découpé du ticket 02a le 26/11/2026** (décision du propriétaire). Détail : `02-hauteur-du-ballon-moteur.md`, point 4.

**What to build:** les tirs prennent une vraie trajectoire en hauteur, cohérente avec l'issue tirée par `v2-collectif/28b` (`v2engine/shooting.py`) :
1. **Hauteur à la ligne** : tirée dans la loi gaussienne de hauteur qui existe déjà (`SHOT_AIM_HEIGHT_M`, `SHOT_ERROR_SIGMA_RAD`), **conditionnée à l'issue** : tir cadré, haut du ballon sous la barre (`z + 2·BALL_RADIUS_M < 2,44`, convention du 02a1) ; tir « au-dessus », bas du ballon au-dessus de la barre. Aucune constante nouvelle.
2. **Trajectoire** : `vz0` déduit de la hauteur visée à la ligne et du temps de trajet (même physique que le 02a1).
3. Le tir « au-dessus » cesse d'être rejoué à plat comme un tir à côté (`shooting.py:257`).

**Blocked by:** 02a1.

**Bloque :** 03 ; `v2-collectif/28b` réserve A2 (ballon claqué sans hauteur) si elle est reprise ici, à vérifier à l'ouverture.

**Status:** livré (26/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèse : la physique du 02a1 se réutilise telle quelle.
Temps machine, non compté : une série de 50 matchs, suite complète.

## Acceptance criteria

- [x] Tirs de 50 matchs : 100 % des cadrés passent la ligne haut du ballon sous 2,44 m ; 100 % des « au-dessus » bas du ballon au-dessus (547 sur 547 et 202 sur 202)
- [x] Répartition des issues (cadré, à côté, au-dessus, dévissé) inchangée dans le bruit des séries de référence du 02a1 (0,0 à 0,2 × le bruit, voir Résultats)
- [x] Mêmes empreintes de trace sur deux exécutions à graine fixée (matchs 0 et 1 relancés : `00a20cbeb887b8b6`, `03dfa0fb5693e17a`, identiques) ; suite complète au compte attendu (3 548 passés = 3 519 + 29 nouveaux, 0 ignoré, 14 désélectionnés, 15 min 06 s) ; V1 inchangée (aucun fichier V1 ni protégé touché)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (voir Comments et `docs/agents/suivi-estimations.md`)

## Résultats (26/11/2026)

**Réalisé.** `v2engine/shooting.py` : `line_height_m` (hauteur du bas du ballon à la ligne, conditionnée à l'issue) et `ground_strike_m` (point où une visée sous le sol touche le sol). `v2engine/hauteur.py` : `stepped_travel_time_s` (temps exact du moteur, pas de 0,1 s) et `launch_vz_to` (`vz0 = (z + ½·g·T²)/T`). `v2engine/match.py` : `vz0` posé au départ du tir ; but jugé sur la hauteur réelle à la ligne (`z + 2·BALL_RADIUS_M < GOAL_HEIGHT_M`) ; ballon remis au sol après un but, une parade repoussée et un contre. `v2engine/trace.py` : `ShotEvent.line_z_m` (non exposé par l'API). 29 tests (`tests/test_v2_hauteur_tirs.py`).

**Principe.** L'issue reste tirée par le 35b (aucune constante, aucun tirage de plus, flux aléatoire inchangé) ; la hauteur est **transportée par quantile** : sous la barre, l'angle tiré est replacé au même quantile dans la gaussienne tronquée « haut du ballon sous la barre » ; au-dessus, la hauteur est gardée. L'ordre des tirs est conservé et la bande 2,22-2,44 m (bas du ballon sous la barre, haut au-dessus) n'est jamais produite. Les cas de barre sont renvoyés au `v2-collectif/35c`.

**Visées sous le sol** (question du propriétaire, réponses A, B, C) : la première version ramenait ces tirs à `z = 0` à la ligne, sur un arc sans rebond (réponse B, pic construit). Corrigé : le tir retombe là où la droite visée coupe le sol (`ground_strike_m`), puis le 02a1 le fait rebondir (restitution 0,70) ou rouler. On est maintenant en réponse C : trajectoire correcte, proportion due à la loi du 35b, documentée dans le 35b comme choix à revoir.

**Mesure, 50 matchs** (graines 0 à 49, `.scratch/v2-hauteur-ballon/mesures/02a2-apres-A.json`, relevé des hauteurs par espion sur `line_height_m`) :
- 1 399 tirs : contrés 321, à côté 286, but 218, capté 205, au-dessus 202, repoussé 89, claqué 43, dévissé 34, en vol à la fin 1.
- Cadrés : 547 sur 547 haut du ballon sous 2,44 m ; au-dessus : 202 sur 202 bas du ballon au-dessus. Hauteur moteur à la ligne contre hauteur prévue : écart maximal 3,5e-14 m. Aucun pas de trace avec `z < 0` ; sommet maximal en vol 17,2 m.
- Bande 2,22-2,44 m à la ligne : 0 tir ; 2 tirs entre 2,20 et 2,22 m (pas de pic).
- Visées sous le sol : 475 tirs en vol sur 1 340 (35,4 %) ; 195 franchissent la ligne, 188 en roulant (`z = 0`), 7 en rebond.
- Histogramme des hauteurs à la ligne (695 tirs qui la franchissent, pas de 0,2 m) : `z = 0` (roule) 188 ; 0-0,2 : 21 ; 0,2-0,4 : 15 ; 0,4-0,6 : 27 ; 0,6-0,8 : 20 ; 0,8-1,0 : 19 ; 1,0-1,2 : 20 ; 1,2-1,4 : 23 ; 1,4-1,6 : 9 ; 1,6-1,8 : 18 ; 1,8-2,0 : 16 ; 2,0-2,2 : 19 ; 2,2-2,4 : 2 ; 2,4-2,6 : 18 ; 2,6-2,8 : 19 ; 2,8-3,0 : 25 ; ≥ 3 : 236. Creux 1,4-1,6 m (9 tirs contre 15 à 27 ailleurs, question du propriétaire) : même mélange que les cases voisines (5 buts, 4 à côté ; seuls les buts et les tirs à côté franchissent la ligne), aucune frontière de la loi à cet endroit (transport par quantile monotone et continu) ; avec 19 tirs en moyenne par case, la probabilité qu'au moins une des 9 cases tombe à 9 ou moins est d'environ 8 % : bruit. Le pic à 0 est physique (ballons qui roulent, rebond suivant sous 0,15 m de sommet) et vient de la loi du 35b, pas du 02a2.

**Répartition des issues contre le bruit.** Bruit par indicateur : 1,96·√(sA²/50 + sB²/50), écarts-types par match des séries de référence `02a1-ref-A` (graines 0 à 49) et `02a1-ref-B` (50 à 99) ; écart jugé : 02a2 contre `02a1-apres2-A`, mêmes graines (`02a2-tolerance.txt`). Cadrés 38,9 → 39,4 % (0,1 ×), à côté 20,4 → 20,5 % (0,0 ×), au-dessus 14,1 → 14,3 % (0,1 ×), dévissés 2,6 → 2,5 % (0,1 ×), contrés 24,0 → 23,3 % (0,2 ×), buts 4,14 → 4,36 par match (0,3 ×). Sur 2 820 indicateurs : 8 hors bruit (0,3 %), tous à bruit nul (effectifs minuscules, par exemple ballons contrés « encore libres à 3 s » 0,12 → 0,19 sur une poignée de cas) ; A contre B : 91 (3,2 %). Les issues étant tirées comme avant, les écarts viennent de la suite du jeu (ballon remis au sol, trajectoires).

## Comments

- 26/11/2026 : **Points du propriétaire.** (1) Bande morte 2,22-2,44 m documentée, cas de barre renvoyés au `35c` (note ajoutée au `35c`). (2) Tir contré : le ballon repart du sol en ballon libre, freiné par le moteur 02a1, sans `line_z_m` (tests dédiés). (3) Le « tiers des tirs à 16 m » visés sous le sol était une estimation (Φ(−0,35) ≈ 36 %) ; mesuré : 28 % sur 4 matchs, 35,4 % sur 50. (4) Histogramme des hauteurs à la ligne : ci-dessus. (5) Réserve A2 du `28b` (ballon claqué sans hauteur) **non reprise** : renvoyée au `v2-realisme/03f` (le `03a` est livré).
- 26/11/2026 : **Point d'étape à 1 h 15** de travail effectif (analyse 30, code 25, tests 20), estimation révisée à 2 h 15-2 h 30 à cause des points ajoutés et de l'enquête sur le pic à 0, annoncée au propriétaire.
- 26/11/2026 : **Durée** : estimée 1 h 30 (90 min ; 15/35/25/15), réelle environ 2 h 50 (170 min ; 40/45/35/50, non chronométrée, horloge de la session hors attentes machine), écart + 89 %. Causes : cinq points ajoutés par le propriétaire (tests du contre, histogrammes, mesure de la part sous le sol) ; défaut de conception trouvé par la question A/B/C (visées sous le sol ramenées à `z = 0`), corrigé puis re-mesuré ; outil de tolérance du 02a1 perdu, réécrit. Temps machine hors total : une série de 50 matchs abandonnée après le correctif, une série de 50 matchs (environ 48 min), relevé des hauteurs (environ 30 min), déterminisme, suite complète.
- 26/11/2026 : **Suite donnée (décisions du propriétaire).** Cas C confirmé. Révision de la part visée sous le sol confiée au nouveau ticket `v2-collectif/35d`, qui bloque le `22c` (le `10a` et le `04a` passent après la calibration, ils ne peuvent pas la porter). Mesures laissées dans `.scratch/v2-hauteur-ballon/mesures/` (suivi par git, à côté des références du 02a1). Règle d'estimation ajoutée au registre : + 50 % par défaut pour les tickets ballon et tirs (`14a`, `14b`).
- 26/11/2026 : **Clôture.** Expert : `APPROVED` (empreinte be2d6b90…). QC (`valider-etape`) : `VALIDÉ`. Décision de clôture : `VALIDÉ`. Aucune anomalie bloquante. Améliorations facultatives : A1 contre et parade jugés à plat, ballon remis au sol d'un coup (`_blocked`, `_keeper_reaches`), à traiter au `03` ou au `02b` avant l'affichage de `z` ; A2 décollage très raide pour un tir à 1 m (ligne franchie dès le premier pas, sans effet visible) ; A3 plafond à exactement 2,22 m contre une inégalité stricte (probabilité négligeable) ; A4 une assertion toujours vraie dans le test des visées sous le sol.
