# 14: Combinaisons collectives

**What to build:** Reconnaître des **séquences possibles** comme des opportunités, jamais comme des scripts : remise, troisième homme, une-deux, dédoublement, renversement, passe dans la course, changement de position. Évaluer la faisabilité de la séquence entière (joueurs accessibles, interception possible) et l'abandonner si le défenseur ferme la ligne.

**Attributs :** Vision, Decisions, Off the Ball, Teamwork, Anticipation.

**Blocked by:** 13.

**Status:** livré (03/11/2026), validé expert + QC (clôture groupée 10-14-16, réserves acceptées par délégation, voir Comments)

## Constantes et critères validés par le propriétaire (02/11/2026, « Oui, valide tout », après revue de `simulafoot-architect`)

**Mécanisme : le plan de passe.** Le porteur transmet au receveur la suite qu'il a comptée (ticket 13), quand elle bat la position atteinte. À sa première décision, le receveur l'adopte selon son Teamwork, la tient si la passe reste jouable et que sa Vision la voit (Decisions choisit ensuite, comme avant), sinon l'abandonne ; le coéquipier prévu relance son appel, une fois, à la passe, vers un espace où le receveur le trouve (Off the Ball, `choose_space`). Une-deux et troisième homme sont reconnus dans la mesure, pas scénarisés.

**Constantes**
- `PLAN_BONUS = 0,3` : valeur de la passe prévue majorée de 30 % quand le plan est tenu (mesuré à 0, 0,15 et 0,3 sur les mêmes graines).
- Adoption du plan (Teamwork) : 99 → 100 %, 55 → 85 %, 11 → 65 %, même courbe que tenir le bloc (`defense._STAYS`), un tirage.
- Ligne encore ouverte : réussite de la passe au moins `OPEN_LANE_PROBABILITY` (0,7, ticket 06).
- Validité : la première décision du receveur seulement. Pas de plan en contre-attaque.
- Mesure seulement : une-deux si le passeur a avancé d'au moins 5 m entre sa passe et le retour.

**Hors périmètre** : dédoublement et changement de position (tickets 16 et 17) ; renversement, seulement émergent (si la Vision le voit) ; passe dans la course déjà faite (`possession.pass_aim`). A2 du ticket 13 (progression au-delà de 20 m) laissée au ticket 22.

**Critères**
- Scène contrôlée (Decisions 55, 2 000 tirages) : plan tenu, passe prévue choisie au moins 15 points plus souvent que sans plan ; ligne fermée, écart avec le choix sans plan de 2 points au plus ; Teamwork 99 contre 11, écart mesurable ; pas de plan en contre-attaque ; le coéquipier prévu choisit un espace où la passe depuis le receveur réussit au moins à 0,7.
- En match (10 matchs, mêmes graines, plan contre `--sans-plan`) : C2 au moins 39 % ; retour au passeur en 3 s au plus 8,6 %, donné aussi hors une-deux ; 15 à 17 passes par minute ; réussite des passes, recul de 2 points au plus ; temps de calcul +25 % au plus ; déterminisme ; part des plans abandonnés rapportée.
- Triangle : à une décision du porteur, deux coéquipiers à 30 m au plus, trois passes toutes au moins à 0,7, angle au porteur de 20 à 160 degrés ; part des décisions avec au moins un triangle, avec et sans plan.
- Indicateurs réels : fréquence des une-deux **non trouvée** ; troisième homme, une à deux attaques réussies par match pour les meilleures équipes, méthode partielle (seulement les séquences où le ballon revient au joueur qui lance l'action ; [Footballytics](https://www.footballytics.ch/post/tactics-and-data-outplay-opponents-with-pass-combinations)). Pistes non lues : Gyarmati, Kwak et Rodriguez (2014) ; Bekkers et Dabadghao (2019), motifs de passes.

**C2 renvoyé au ticket 22 (accord du propriétaire, 02/11/2026).** Mesure sur 10 matchs : C2 32,0 % sans plan, 30,7 % avec `PLAN_BONUS` 0,15, 30,0 % avec 0,3. Diagnostic sur 2 matchs : seules 26 % des passes sans gain portent un plan (72 % de ces plans visent une suite qui fait avancer, gain moyen 15 m), et 46 % des plans sont abandonnés : ligne fermée, cible hors de la Vision ou hors-jeu évident, sans distinction dans cette mesure (séparés après la revue). Pour atteindre 39 %, il faudrait qu'environ 61 % des passes avec plan soient suivies d'une passe qui fait avancer, contre environ 40 % mesurés : le plan ne peut pas, seul, porter C2 à 39 %. Critère retenu pour ce ticket : le plan ne fait pas baisser C2 au-delà du bruit de mesure. L'objectif de 39 % passe à la calibration générale (ticket 22). La passe prévue, jouée environ 2 fois sur 3 quand le plan est tenu, ne fait plus avancer qu'environ 4 fois sur 10 au moment où elle est jouée. Ce n'est pas dû à la relance de l'appel : sans relance (2 matchs, mêmes graines), on mesure 40,6 % de passes qui font avancer avec un plan tenu, contre 40,8 % avec relance, et 43,4 % contre 40,4 % sur l'ensemble des passes avec plan. Ces écarts restent dans le bruit de mesure. La relance est donc gardée.

- [x] Test de circulation : les joueurs créent mesurablement des triangles et des solutions de soutien (triangles mesurés : 35,8 % des décisions sans plan, 35,4 % avec ; le plan n'en crée pas davantage, voir Réalisation)
- [x] Une combinaison démarrée est abandonnée quand la ligne se ferme (test)
- [x] Fréquence des une-deux et du troisième homme dans une fourchette réelle (à sourcer) : une-deux non trouvée ; troisième homme, définition réelle plus étroite, non comparable (voir Réalisation)
- [ ] Repris du ticket 13 (réserve A1, acceptée le 02/11/2026) : en match, une passe sans gain suivie par le receveur d'une passe qui casse une ligne ou gagne 10 m augmente mesurablement (32,5 % sans la suite du ticket 13, 30,6 % avec, 10 matchs ; critère d'origine : au moins 39 %), le receveur jouant la passe que le porteur a préparée ; échelle de progression de la deuxième passe au-delà de 20 m à proposer (A2 de l'expert, facultatif) — **non atteint, renvoyé au ticket 22** avec l'accord du propriétaire (voir « C2 renvoyé au ticket 22 ») ; critère retenu ici : pas de baisse de C2 au-delà du bruit de mesure ; A2 laissée au ticket 22
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Réalisation (02/11/2026)

**Code.** `v2engine/ball_state.py` (champ `plan` : receveur, suite, instant de la passe) ; `v2engine/decision.py` (`PLAN_BONUS`, `_ADOPT_PLAN`, `adopt_plan_probability`, `Action.follow` et `Action.plan`, paramètre `planned` de `evaluate_options` et `choose_action`, `follow_up` rend aussi le nom de la suite ; sort du plan : tenu, abandonné, non vu, refusé, non compté en contre-attaque) ; `v2engine/match.py` (`_step_ball` : le receveur lit le plan à sa première décision, toute décision l'efface, une passe avec une suite le pose) ; `v2engine/cerveau.py` (branche APPEL : relance unique vers un espace où le receveur le trouve). Banc : `scripts/v2_indicators.py` (journal des passes, lignes cassées, triangles, enchaînements), `scripts/measure_v2.py` (option `--sans-plan`). Définitions : `docs/INDICATEURS_V2.md`, indicateurs 12 à 16. Rayon : Teamwork lu dans `decision` (carte et test de rayon).

**Tests.** `tests/test_v2engine_combinaisons.py` (10 tests : plan tenu +15 points au moins, ligne fermée sans effet, Teamwork 99 contre 11, pas de plan en contre-attaque, cible hors de vue, suite transmise, relance vers un espace jouable, relance unique, branchement dans `_step_ball`) ; `tests/test_v2_indicators.py` (+2). Suite complète : 2 281 passés, 13 désélectionnés (avant les corrections de revue) ; suite V2 après corrections : 402 passés.

**Mesures (10 matchs, graine d'audit, `.scratch/v2-collectif/mesures-14/`).**

| | Sans plan | Plan 0,15 | Plan 0,3 | Plan 0,3 final* |
|---|---|---|---|---|
| C2 | 32,0 % | 30,7 % | 30,0 % | 32,3 % |
| Retour au passeur en 3 s (hors une-deux) | 7,1 % (5,6 %) | 7,6 % (6,2 %) | 7,5 % (5,8 %) | 7,2 % (5,5 %) |
| Passes par minute | 16,2 | 16,1 | 16,1 | 16,0 |
| Réussite des passes | 63,2 % | 63,6 % | 63,5 % | 62,7 % |
| Temps de calcul par match | 640 s | 640 s | 640 s | 503 s** |
| Décisions avec un triangle | 35,8 % | 34,9 % | 35,4 % | 36,1 % |
| Une-deux / troisième homme (par équipe et par match) | 6,5 / 0 | 6,1 / 22,4 | 7,2 / 22,8 | 7,2 / 21,4 |
| Plans par match ; tenus / ligne fermée / non vus / refusés | — | 173 ; 40 / 46 (fusionnés) / — / 14 % | 172 ; 41 / 46 (fusionnés) / — / 14 % | 173 ; 39 / 39 / 10 / 12 % |

\* Après les corrections de revue (sort du plan séparé, contre-attaque exclue) ; l'arbre de travail contenait alors des changements moteur non commités d'autres tickets (`off_ball.py`, `cerveau.py`, mention « ticket 16 ») : colonne non comparable aux trois autres. \*\* Trois séries tournaient en parallèle pour les trois premières colonnes, une seule pour la dernière.

Déterminisme : empreinte de 10 minutes identique sur deux exécutions (`a78f82de78d4cc0a` avant les corrections de revue ; `ad43725e05d41b90` après, arbre contenant les changements d'autres tickets).

**Lecture.** Le plan agit à situation égale (scènes contrôlées), sans effet mesurable sur C2, les triangles ou le rythme en match ; il ne dégrade ni la réussite des passes, ni les retours au passeur, ni le temps de calcul. Le bonus n'est pas le levier (0,15 et 0,3 donnent le même résultat). Troisième homme : 21 à 23 par équipe et par match contre une à deux « attaques réussies » pour la source, dont la définition est bien plus étroite ; pas de comparaison possible. Une-deux : 6 à 7 par équipe et par match, fréquence réelle non trouvée.

**Revue `simulafoot-reviewer` (02/11/2026)** : aucun bloquant. Corrigés : branchement dans `_step_ball` sans test (majeur) ; libellés de mesure (abandons séparés, contre-attaque exclue) ; ligne mal formée dans `v2_indicators.py` ; définitions des mesures écrites dans `docs/INDICATEURS_V2.md`. Non corrigé : un plan peut survivre quand le receveur reprend le ballon à l'adversaire avant que celui-ci ait décidé (rare, impact faible). Suggestions laissées : `_ADOPT_PLAN` recopie `defense._STAYS` au lieu de le partager (ticket 19, pas d'import privé) ; `pass_success_probability` calculé deux fois pour la cible du plan.

## Interaction avec le ticket 16 (réserve A3 de l'expert, clôture groupée 10-14-16, 03/11/2026)

À la relance de son appel par le plan, le coéquipier prévu passe d'abord par l'appel dans le dos du ticket 16 (`cerveau.py`, `depth_run` avant `choose_space`). Si l'appel dans le dos est tiré, il part sur la ligne : la garantie « espace où la passe depuis le receveur réussit au moins à 0,7 » ne s'applique pas à ce cas, et un appel dans le dos tenu est retiré au sort au départ de la passe (le passeur pris en compte devient le receveur). Choix assumé : un troisième homme qui part dans le dos est plausible. Réserve acceptée par délégation du propriétaire. Suivi : rendre `test_the_planned_mate_relaunches_his_run_where_the_receiver_finds_him` indépendant de la graine (neutraliser `depth_run`), dans un ticket séparé après le commit. Fait le 03/11/2026 (suivi v2-collectif/14-suivi-A3, base `bce1f74`) : `depth_run` neutralisé dans les deux tests de relance (verts sous les graines 1 à 5), priorité de l'appel dans le dos fixée par `test_a_depth_run_takes_precedence_over_the_planned_space` ; expert APPROVED, QC VALIDÉ, clôture VALIDÉ. Suite complète : 2 303 passés, 1 échec hors changement (rayon des attributs, `v2engine/restart.py` d'une autre session, non suivi).

## Comments

- 03/11/2026, clôture groupée v2-collectif/10-14-16 (tickets imbriqués dans `cerveau.py`, `measure_v2.py`, `test_v2engine_rayon_attributs.py`), base `704cae3`, empreinte `40a69fa0` : expert INCONCLUSIVE au passage 1 (suite complète absente), APPROVED_WITH_RESERVATIONS au passage 2 ; QC VALIDÉ ; clôture VALIDÉ. Suite complète : 2 305 passés, 13 désélectionnés, 0 échec. Réserves acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes les reco d'experts ») : documents dans le même commit ; priorité de l'appel dans le dos sur la relance du plan du 14, avec test du plan à rendre indépendant de la graine (ticket de suivi). A13 jugée conforme à R1 (Vision et Passing du porteur = contexte perçu par le coureur), reformulée dans la carte.
