# 14b2: Passes : lignes, lecture et coupe sur la trajectoire prédite

**Découpé du ticket 14b le 26/11/2026** (audit Magnus : `docs/AUDIT_MAGNUS_V2.md`, section 4 B). **Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié (26/11/2026) :** la difficulté, la lecture et la fermeture d'une passe sont calculées sur le **segment** passeur → receveur. Une passe brossée qui contourne un défenseur serait jugée coupée par lui.

**Sites (famille B de l'audit, côté passes ; recensement par recherche des projections sur un axe dans `v2engine/`, 26/11/2026) :**

| # | Site | Géométrie actuelle | Appelants (inchangés si la signature l'est) |
|---|---|---|---|
| 1 | `possession._cut_chance` (l. 112-125) | distance de l'adversaire au segment, `along` sur l'axe passeur → receveur | `pass_success_probability` (l. 179-180) |
| 2 | `possession.pass_success_probability` (l. 163) | boucle des coupes sur le segment | `decision` l. 258 (`lane_closed_during_turn`), 441, 456-457, 469 ; `match` l. 762 ; `occasion` l. 101 ; `off_ball` l. 146 ; `restart` l. 181 |
| 3 | `anticipation.pass_readers` (l. 48-70) | couloir autour du segment départ → cible (`along`, l. 62) | `match` l. 611 (remise en jeu), 895 (passe) |
| 4 | `decision.lane_closed_during_turn` (l. 253) | via le site 2 seulement | `match` l. 705 |
| 5 | `defense.press_point` (l. 290-310), appelé avec un receveur (l. 543, via `_lane` l. 433) | le presseur se place sur la direction porteur → receveur | — |

Exclus, avec raison : `possession.pass_difficulty` (distance seulement) ; `possession.deflect` et `match._ball_contacts` (géométrie d'un contact sur un pas de 0,1 s) ; `pass_aim` et `pass_velocity` (famille A, réécrits par 14a ; la visée inverse des passes avec effet est au 14b4) ; `press_point` vers le but (ligne de tir, 14b3).

**What to build:** Les sites 1, 3 et 5 lisent la trajectoire prédite (prédicteur partagé de 14a, avec l'effet du 14b1) au lieu du segment : distance d'un adversaire au **chemin** échantillonné, au même instant d'arrivée ; le site 5 prend la direction de départ du chemin. Le site 2 reçoit le chemin (ou l'effet prévu) en argument ; ses appelants passent un effet nul tant que 14b4 n'est pas livré. Sans effet, la trajectoire prédite est droite : résultats identiques au segment à la tolérance près.

**Séquencement avec 14b3 (vérifié dans le code le 26/11/2026) :** parallèle. La visée des tirs (`shooting.aim_angles`, `draw_shot_error`, `match.py` l. 852) n'appelle ni `meeting_point`, ni `pass_aim`, ni aucun site de ce ticket ; 14b3 résout sa visée inverse sur le prédicteur partagé du 14b1. Les deux tickets touchent des fonctions distinctes de `defense.press_point` (avec receveur ici, vers le but au 14b3) : à fusionner proprement si les deux sont en cours en même temps.

**Attributs :** aucun.

**Blocked by:** 14b1 (Spin du ballon et force de Magnus dans le solveur).

**Bloque :** 14b4.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : cinq sites, liste fermée ci-dessus ; le prédicteur de 14a rend des points échantillonnés (instant, position) ; coût de calcul acceptable (les lignes de passe sont évaluées pour chaque option à chaque décision : mesurer le temps de calcul d'un match avant / après). Un site de plus découvert en cours de route : estimation révisée et annoncée avant de continuer.
Temps machine, non compté : suite complète (environ 10 min) ; mesure du temps de calcul sur 4 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur sur le segment mais à 2 m de la courbe d'une passe avec effet : chance de coupe plus basse qu'en ligne droite ; défenseur dans la courbe : plus haute ; lecteur de passe de même ; sans effet : mêmes valeurs qu'avant (± 1e-9) pour les sites 1, 3 et 5
- **Non-régression :** empreintes identiques à graine fixée (aucune frappe n'a d'effet avant 14b4)

## Acceptance criteria

- [ ] Les sites 1 à 5 lisent la trajectoire prédite ; plus aucun calcul de ligne de passe sur un segment dans `v2engine/` (recherche des projections `along` jointe au rapport, comparée au tableau)
- [ ] Sans effet : valeurs identiques au segment (tests) et empreintes de trace identiques à graine fixée
- [ ] Temps de calcul d'un match : hausse ≤ 15 % (sinon proposer un échantillonnage plus grossier au propriétaire)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
