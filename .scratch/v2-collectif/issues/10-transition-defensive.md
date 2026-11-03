# 10: Transition attaque-défense

**What to build:** À la perte du ballon, chaque joueur réagit selon sa position, son rôle, ses capacités et le contexte : les plus proches contre-pressent, d'autres protègent l'axe, d'autres sprintent vers leur zone. Pas un ordre universel de repli.

**Attributs :** Work Rate, Anticipation, Concentration, Teamwork ; Pace + Acceleration.

**Blocked by:** 03, 07, 09, 25 (socle cinématique et contact).

**Status:** livré (03/11/2026), validé expert + QC (réserves A1 à A3 acceptées par le propriétaire, renvoyées au ticket 22, voir Comments)

- [~] (indicateur, ticket 22) Temps de réaction moyen au repli dans une fourchette réelle : valeur réelle non trouvée (Bundesliga 2010/11 : ballon récupéré en environ 1 s par les meilleures équipes, temps de récupération et non de réaction) ; moteur : latence du repli 2,53 s
- [x] Le choix entre contre-presser et se replier dépend mesurablement de la distance au ballon et du rôle : 82 % à moins de 10 m, 81 % de 10 à 15 m, 0 % au-delà et pour les deux plus reculés ; BU 44 %, DC 2 %
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée (2294 passés, 13 désélectionnés, 0 échec)

**Reporté du ticket 05 (27/10/2026, décision du propriétaire) :** avec la ligne défensive à sa hauteur réelle, tirs et buts sortent des fourchettes (20 matchs : 18,1 tirs par équipe, 4,7 buts par match ; réel 8-15 et 2-3,5). Les tirs de contre-attaque après une récupération dans son camp doublent (4,8 → 9,5 par match) : les blocs se croisent plus haut et plus serrés, et personne ne se replace encore à la perte. Critère ajouté : ramener tirs de contre, tirs et buts vers les fourchettes réelles par le comportement de repli, sans baisser la ligne du ticket 05.

**Reporté du ticket 09 (réserve C3, acceptée par le propriétaire le 02/11/2026) :** depuis la passe en vol du ticket 09 (rôles défensifs gardés pendant une passe adverse), les tirs de contre après une récupération dans son camp passent de 3,35 à 4,55 par match (20 matchs), à nombre de récupérations égal (environ 400 par match) : ces contres aboutissent plus souvent à un tir (0,84 → 1,14 % des récupérations), cause non établie. À reprendre ici, avec la réaction de l'équipe qui perd le ballon. Frontière avec le ticket 09 : le 09 décide qui comble la place laissée vide ; ce ticket, ce que fait le joueur qui l'a quittée (repli, contre-pressing).

**Reporté du ticket 09, première case (réserve A1 de l'expert, passage 3, acceptée par le propriétaire le 02/11/2026 : « J'accepte ») :** « occasions de contre mesurablement moins nombreuses avec compensation » n'est pas démontré en match (tirs de contre après récupération dans son camp 3,45 → 4,05 par match après les corrections du passage 2). À démontrer et remesurer (C3) à la clôture de ce ticket, une fois le repli et le contre-pressing en place. À surveiller aussi : l'axe laissé vide quand le milieu défensif sort presser l'ailier servi.

## Réalisation (03/11/2026)

**Diagnostic avant le code** (20 matchs du ticket 14, 10 matchs) : le centre de l'équipe qui perd le ballon avance de 0,76 m/s au lieu de reculer, et ne commence à reculer qu'après 2,2 s. Rôles à 1,5 s de la perte : 64 % « replacement » (le bloc), 11 % presseur ; les défenseurs visent une cible 15 à 20 m plus haut que leur position.

**Constantes validées par le propriétaire (02/11/2026, « Oui, ta reco »)** ; aucune courbe nouvelle :
- réaction : tant qu'il n'a pas perçu la perte (délai d'Anticipation, 0,4 à 1,0 s, ticket 03), le joueur poursuit son intention offensive ;
- contre-pressing : toute perte dans le jeu déclenche le pressing d'équipe du ticket 08 pendant `TRIGGER_S` = 5 s ; suivent les joueurs à `FOLLOW_M` = 15 m ou moins du ballon (Teamwork, 95 / 80 / 55 %), sauf les `REST_DEFENDERS` = 2 plus reculés (axe protégé) ; exclus : ballon pris par le gardien, coup franc de hors-jeu, engagement ;
- repli : le joueur sans rôle devant le ballon rejoint sa place du bloc sans l'écart toléré de Teamwork, à l'intensité de Work Rate (99 → 100 %, 55 → 80 %, 11 → 55 %, courbe du presseur) ;
- Concentration non branchée (règle R3, ticket 21). Valeur réelle : non trouvée ; indicateur : Vogelbein, Nopp et Hökelmann 2014, Bundesliga 2010/11, les meilleures équipes récupèrent le ballon environ 1 s plus vite (temps de récupération, pas de réaction).

**Code** : `v2engine/defense.py` (`_counter_press`, `REST_DEFENDERS`, `situations` dans `update`), `v2engine/cerveau.py` (`REPLI`, réaction à la perte, `previous` dans `think`), `v2engine/match.py` (branchement) ; banc : `scripts/v2_indicators.py` (vitesse de repli à 1,5 s), `scripts/measure_v2.py`. Tests : `tests/test_v2engine_transition_defensive.py` (5), `tests/test_v2_indicators.py` (1).

**Règle « pas de montée » essayée puis retirée (propriétaire, 03/11/2026, « La retirer »).** Un joueur sans rôle derrière le ballon ne remontait pas en transition défensive. Elle faisait reculer l'équipe (+0,22 m/s au lieu de −0,79) mais faisait chuter le hors-jeu (2,0 → 0,69 par match, la ligne du ticket 05/23 ne montait plus) et montait les tirs de contre (4,8 → 6,2) et les buts (3,9). Retirée ; piste pour le ticket 22.

**Mesures, 16 matchs, mêmes graines, état avant (même arbre de travail sans les changements du ticket) → après**

| Indicateur | Avant | Après | Réel |
|---|---|---|---|
| Tirs par équipe | 11,25 | 11,9 | 8-15 |
| Buts par match | 3,56 | 2,94 | 2-3,5 |
| Tirs de contre, récupération dans son camp | 4,8 | 4,75 | — |
| Tirs de contre, récupération dans le camp adverse | 14,0 | 15,4 | — |
| Pertes en transition par match | 142 | 117 | — |
| Hors-jeu par match | 2,0 | 1,6 | 3,2-3,5 |
| Passes réussies | 63,2 % | 65,1 % | — |
| Latence du repli / vitesse de recul du centre / bloc reformé | 2,27 s / −0,79 m/s / 3,65 s | 2,53 s / −0,76 m/s / 3,83 s | — |

Le bruit entre deux séries de 16 matchs est grand (buts du même état avant : 2,94 ou 3,56 selon la série).

**Choix à la perte (après)** : suivent le contre-pressing 82 % des joueurs à moins de 10 m, 81 % entre 10 et 15 m, 0 % au-delà et 0 % des deux plus reculés ; par poste, BU 44 %, MOC 39 %, AG/AD 27 %, MC 13 %, MDC 11 %, LB/RB 4 %, DC 2 %. Work Rate 99 / 11 : vitesse de repli à 1,5 s, 1,14 / 0,92 m/s.

**Réserve 11 A1 (contre-attaque non jouable mieux sanctionnée ?)** : reperdue en moins de 5 s, avant → après : 20-40 m, jouable 22,6 → 21,0 %, non jouable 27,8 → 21,6 % ; 40-60 m, jouable 27,4 → 21,9 %, non jouable 29,2 → 27,0 %. Les contre-attaques sont moins reperdues, mais la sanction de la non jouable ne se précise pas : non démontré, renvoyé au ticket 22.

**Réserves 09 (C3 et première case)** : tirs de contre après récupération dans son camp 4,81 → 4,75 par match : pas de hausse, pas de baisse. « Occasions de contre moins nombreuses avec compensation » n'est pas démontré non plus ; les sauts du banc sont dans le bruit. Renvoyé au ticket 22.

**Critères** : réaction et repli par rôle, distance et attributs : atteints. Temps de réaction moyen au repli (latence) 2,5 s : pas de valeur réelle trouvée, non atteint comme objectif de réalisme. Baisse des tirs de contre / tirs / buts « vers les fourchettes » : tirs et buts dans les fourchettes (11,9 ; 2,94), tirs de contre inchangés. Le repli ne fait pas reculer le centre de l'équipe (−0,76 m/s) : cause identifiée, la montée du bloc vers sa place, dont la correction coûte le hors-jeu ; à traiter au ticket 22.

**Déterminisme** : même empreinte sur deux exécutions (10 minutes, graine d'audit), `1c5693a06768f14e`.

**Suite complète (03/11/2026)** : `PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider` : **2294 passés, 13 désélectionnés, 0 échec** (attendu de `CLAUDE.md` : 2281 ; l'écart inclut les 6 tests de ce ticket et les tests des autres tickets non commités de l'arbre de travail, non décomposé). Fichiers V1 et fichiers protégés : non touchés. Dernier tour de mise en forme (lignes continuées) sans changement de logique : 31 tests ciblés verts, même empreinte de trace.

## Comments

- 03/11/2026, clôture groupée v2-collectif/10-14-16 (tickets imbriqués dans `cerveau.py`, `measure_v2.py`, `test_v2engine_rayon_attributs.py`), base `704cae3`, empreinte `40a69fa0` : expert INCONCLUSIVE au passage 1 (suite complète absente), APPROVED_WITH_RESERVATIONS au passage 2 ; QC VALIDÉ ; clôture VALIDÉ. Suite complète : 2 305 passés, 13 désélectionnés, 0 échec. Réserves acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes les reco d'experts ») : documents dans le même commit ; priorité de l'appel dans le dos sur la relance du plan du 14, avec test du plan à rendre indépendant de la graine (ticket de suivi). A13 jugée conforme à R1 (Vision et Passing du porteur = contexte perçu par le coureur), reformulée dans la carte.
- 03/11/2026, passage 1 (base `a0a5de9`, arbre d'avant le ticket 10 : le ticket 14, non commité, est dans la base ; empreinte `1ab7fddf`) : expert APPROVED_WITH_RESERVATIONS ; QC BLOQUÉ (résultat de la suite complète absent du ticket ; critères non atteints à faire accepter).
  - A1 [réserve] : latence du repli (2,53 s) sans valeur réelle de référence. Ticket 22.
  - A2 [réserve] : tirs de contre inchangés (4,8 → 4,75) ; réserves 09 C3, 09 A1 et 11 A1 non démontrées. Ticket 22, série d'au moins 40 matchs avec dispersion.
  - A3 [réserve] : hors-jeu 1,6 par match (réel 3,2-3,5) et centre d'équipe qui ne recule pas (−0,76 m/s). Ticket 22 ; rouvrir si le hors-jeu reste sous 2 par match sur une série plus longue.
  - A4 [facultatif] : l'intention `previous` renvoyée peut avoir une cible périmée de moins de 1 s. Non traité.
  - QC, non bloquants : clause du coup franc de hors-jeu sans test dédié ; tri des deux plus reculés écrit deux fois (`cerveau.py`, `defense.py`).
  - Réserves acceptées par le propriétaire, ses mots : « J'accepte A1, A2, A3 ».
- 03/11/2026, passage 2 (même code, empreinte `1ab7fddf`) : QC VALIDÉ après ajout du résultat de la suite au ticket. Clôture VALIDÉ journalisée.
- Règle « pas de montée » essayée puis retirée sur décision du propriétaire (« La retirer »), voir Réalisation.
