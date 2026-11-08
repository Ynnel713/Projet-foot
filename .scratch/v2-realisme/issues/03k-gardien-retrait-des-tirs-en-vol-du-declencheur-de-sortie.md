# 03k: Gardien : retirer les tirs en vol du déclencheur de sortie

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans ce retrait, 2 sorties du gardien sur 3 sont une course vers un ballon qui s'en va ; la « sortie gagnée » ne mesure rien). **Catégorie :** décision.

**À lancer une fois le 03j commité.** Ticket posé le 08/11/2026 à partir de la piste du 03j (`docs/INDICATEURS_V2.md` section 14, « À décider par le propriétaire »).

**Constat vérifié :** le gardien traite un tir en vol comme un ballon libre. Dans `cerveau._keeper`, `reach` est vrai dès que le ballon n'a pas de porteur, n'est pas une passe de son équipe, et qu'il est à moins de `CHASE_RADIUS_M` ou le plus proche de son équipe ; `gardien.race` (03d) compare ensuite les temps d'arrivée, sans savoir que le ballon est un tir. Le tir qui entre (`shot_for`) n'est touché par personne et traverse la surface jusqu'à la ligne ; le tir « à côté » (`match.py`, branche `SHOT_WIDE_SHARE`) sort du cadre. Aucun des deux ne peut être pris, et le gardien court pourtant derrière. Mesure du 03j (50 matchs, graine d'audit 20260923) : 35,02 ballons avec sortie par match, dont **22,26 tirs à côté** (63,6 %, 89 % finissent en sortie de but, gardien en possession à 3 s dans 0,7 %) et **1,10 tir qui entre** (3,1 %).

**What to build:** un tir en vol (tir à côté ou tir qui entre, ballon encore sur sa trajectoire d'origine) ne déclenche plus la sortie du gardien : il reste dans son état de placement (bissectrice ballon-poteaux), avec une raison tracée du type « tir en vol : il garde sa place pour l'arrêt, le ballon ne peut pas être pris ». Le drapeau est **posé par le moteur au départ du tir** (pas déduit de la proximité d'un tir dans le temps, ce que le 03j a montré fragile) et **effacé dès que le ballon change d'état** (touché par un joueur, contré en route, sorti, ballon mort).

**Décision de périmètre proposée (à valider au lancement).**
- **Retirés :** tir à côté et tir qui entre, soit 23,4 ballons par match (66,7 % des sorties). Ce sont les seuls ballons dont la destination est décidée au départ du tir.
- **Gardés comme ballon libre :** tir contré (7,3 par match, le gardien a le ballon à 3 s dans 16,4 % des cas), tir repoussé (0,8, ballon encore libre à 3 s dans 77,5 %), tir claqué (1,8, 96,7 % finissent en corner). Ce sont des ballons déviés, donc de vrais seconds ballons ; les retirer enlèverait au gardien le réflexe de suivre un rebond. Le claqué est le cas limite (c'est le gardien lui-même qui l'envoie derrière la ligne, et `control_ban_until_s` l'empêche déjà de le rejouer) : à ne retirer que si la mesure d'après montre des courses perdues d'avance.
- **Hors de ce ticket :** les joueurs de champ qui courent aussi vers un tir à côté (rôle `BALLON_LIBRE`, `cerveau.interpret`) ; le ticket les mesure et le rapport le dit, sans les modifier. L'arrêt par portée reste au `05b`, la calibration au `18e`.

**Pourquoi ce choix.** Tout écarter (les 95 % de « tirs » du 03j) ferait tomber les sorties de 35 à environ 2 par match, mais priverait le gardien de ses seuls vrais ballons à disputer (les rebonds). Ne retirer que les tirs dont la trajectoire est fixée corrige le défaut (courir derrière un ballon perdu d'avance) sans toucher au reste. Effet attendu : sorties de 35,0 à environ 11,7 par match (le reste, dominé par les contrés), à vérifier par la mesure, pas un objectif.

**Attributs :** aucun

**Fichiers probables :** `v2engine/ball_state.py` (un drapeau), `v2engine/match.py` (pose au tir à côté ; effacement là où le ballon change d'état, voir les lignes qui remettent `released_by`, `receiver` et `readers` à zéro), `v2engine/cerveau.py` (`_keeper` : le tir en vol exclu de `reach`), `scripts/measure_v2.py` et `tests/`. Aucun fichier protégé.

**Blocked by:** 03j (Gardien : trier les sorties par état du ballon), commité.

**Bloque :** 18e (calibration provisoire tirs et gardien) ; à lire avant tout réglage de la sortie sur tir au 05b.

**Status:** livré (08/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (drapeau, pose, effacement, condition du gardien, trace) | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (mesure avant/après, rapport) | 30 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : le drapeau ne se pose qu'en un endroit nouveau (le tir à côté ; le tir qui entre a déjà `shot_for`) et s'efface aux endroits qui remettent déjà `receiver` et `readers` à zéro. Si l'effacement demande plus de trois sites ou touche une règle de contrôle du ballon, annoncer la nouvelle estimation et découper avant de continuer. Sous le seuil de 2 h : pas de découpage prévu.
Temps machine, non compté : suite complète (environ 15 à 40 min) ; série « après » de 50 matchs (environ 24 min). La série « avant » existe : `.scratch/v2-realisme/mesures/03j.json` (graine d'audit 20260923), valable tant que `v2engine/` n'a pas changé depuis `e76ddf5` (`git diff e76ddf5 -- v2engine` vide), sinon la refaire.

## Tests

- **Unitaires (scène contrôlée, `tests/scenes.py`) :**
  - tir à côté en route vers la ligne, gardien le plus proche : état `placement` (avant le ticket : `sortie`), raison « tir en vol » tracée ;
  - tir qui entre (`shot_for`) : `placement` ;
  - même ballon, drapeau effacé (ballon libre ordinaire) : `sortie` comme au 03d (non-régression) ;
  - ballon contré, repoussé ou claqué (`rebound`, sans drapeau) : `sortie` inchangée ;
  - miroir pour l'équipe visiteuse.
- **Moteur (`match.py`) :** le drapeau est posé au tir à côté et à lui seul ; il est effacé quand un joueur touche le ballon, quand le ballon sort, au ballon mort et à l'engagement.
- **Statistiques (séries de matchs) :** 50 matchs, graine d'audit : sorties par match, sorties par état du ballon (indicateur du 03j), part de sorties gagnées, buts, tirs, arrêts, corners, distance moyenne du gardien à son but.

## Acceptance criteria

- [x] Périmètre (tir à côté et tir qui entre) et nom du drapeau proposés au propriétaire avant le code ; aucune constante produit nouvelle (sinon, proposée avant le code) — périmètre du ticket, validé d'office par la consigne du 08/11/2026 ; drapeau `shot_wide` (`BallState.shot_in_flight` pour les deux) ; aucune constante
- [x] Un tir en vol ne déclenche plus la sortie : sorties sur « tir qui entre » 1,10 → 0 ; sorties sur « tir à côté » 22,26 → 0,74, tous des tirs touchés en route (sonde sur 4 matchs : drapeau effacé par la touche d'un défenseur, croisement « hors tir du 03i » = 0), donc plus des tirs en vol (section 15) ; vérifié par test de scène et par la mesure
- [x] Les autres états du 03j sont inchangés dans le comportement (scènes) : contré, repoussé, claqué, passe, autre restent des ballons libres (tests de scène) ; sorties par match 35,02 → 12,62 (projection 11,7 : +8 %, sous les 20 %)
- [x] Effets de jeu rapportés, sans réglage : buts +0,04, tirs par équipe −0,30, chance des tirs +0,00001, arrêts −0,46, corners −0,5, distance du gardien à son but +0,007 m, tous dans l'IC à 95 % ; les écarts significatifs sont ceux du gardien (32) et 8 petits écarts hors gardien (section 15)
- [x] La trace (raison de l'intention du gardien) dit « tir en vol » quand il garde sa place pour cette raison (test de scène)
- [x] Les joueurs de champ qui courent vers un tir à côté sont comptés au rapport, non modifiés : 177,6 épisodes par match (tir à côté), 18,2 (tir qui entre)
- [x] Aucun fichier protégé modifié ; V1 inchangée (`v2engine/ball_state.py`, `match.py`, `cerveau.py`, `scripts/` et `tests/` seulement)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % : 2 h 30 contre 1 h 55 (+ 30 %), voir `docs/agents/suivi-estimations.md`
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions de 2 matchs (`03k-det1.txt` et `03k-det2.txt`, seule la ligne de durée de calcul diffère)
- [x] Suite V2 verte : 2 536 passés, 14 désélectionnés (`03k-suite.txt`), soit 2 528 + 6 tests du moteur et du gardien + 2 tests d'indicateurs ; `CLAUDE.md` mis à jour
- [ ] À vérifier à l'écran (rejeu d'un match) : sur un tir à côté, le gardien reste sur sa ligne au lieu de courir derrière le ballon — non vérifié par moi, à regarder

## Comments

- **Clôture (08/11/2026).** Expert : `APPROVED_WITH_RESERVATIONS` (empreinte e461d136…). QC (`valider-etape`) : `VALIDÉ`. Réserves de l'expert : A1 (rejeu à l'écran non fait : le critère reste décoché, à regarder sur 3 à 5 tirs à côté) ; A2 (63,5 placements sur tir en vol par match non expliqués : note ajoutée à la section 15, compte d'épisodes de trace à lire avec prudence) ; A3 facultative (la raison « il garde sa place pour l'arrêt » est aussi produite pour le gardien du camp du tireur, trace seule) ; A4 facultative (pas de test de scène pour un penalty). Réserves acceptées d'office par la consigne du propriétaire du 08/11/2026 : « Considéré que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit si les conditions sont nécessaires ». Critère « sorties sur tir à côté = 0 » tenu pour un tir en vol et non à la lettre (0,74 par match, tirs touchés en route).

- **Origine (08/11/2026).** Piste du 03j : « écarter les tirs en vol du déclencheur de sortie ». Le propriétaire a demandé le ticket dans la session du 03j, à lancer une fois le 03j commité.
- **Réalisation (08/11/2026).** `shot_wide` posé au tir à côté (`match.py`), effacé aux cinq sites qui remettent `pass_from` et `rebound` à zéro ; `BallState.shot_in_flight` ; `reach` exclut le tir en vol dans `cerveau._keeper` ; raison tracée « tir en vol ». Indicateurs : état « placement, tir en vol » séparé de « ballon libre laissé » (la première série comptait le libellé « garde sa place » comme ballon libre laissé, +55 par match, corrigé et série refaite) ; joueurs de champ en course vers un tir en vol. Hypothèse du ticket tenue (un seul site de pose, cinq d'effacement, aucune règle de contrôle touchée). Durée réelle estimée, non chronométrée : 2 h 30 (analyse 20, développement 50, tests 35, intégration 45 : sonde des sorties restantes, second jeu d'indicateurs, deux séries de 50 matchs).
- **À la clôture, documenter** : `docs/INDICATEURS_V2.md` (nouvelle section 15, mesure avant/après), `docs/PLAN_V2.md` (statut du 03k et chaîne 03j → 03k → 05b/18e), `docs/agents/suivi-estimations.md`. Clôture par `/valider-ticket-simulafoot` (expert + QC), puis commit avec les seuls hunks du ticket.
