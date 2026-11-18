# 10b: Le défenseur central ne quitte sa ligne que couvert

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un central qui sort sans couverture ouvre la profondeur). **Catégorie :** décision.

**Constat vérifié :** la couverture n'existe que si le porteur est dans la moitié défendue (`defense.py:332`) ; rien n'empêche un central marqueur ou presseur de quitter sa ligne sans couverture.

**What to build:** Un défenseur central ne sort de sa ligne (presser, suivre un décrochage) que si un partenaire couvre sa place (compensation existante ou couverture) ; sinon il garde sa ligne et cède le rôle au suivant.

**Attributs :** aucun

**Blocked by:** 10a (Choix du presseur selon la zone et la responsabilité).

**Bloque :** 10b2, 10c, 10j.

**Status:** livré (18/11/2026), validé expert + QC (réserve A2 acceptée par le propriétaire, traitée au `10b2`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : réutilise `_compensate`.

**Révisée le 18/11/2026, avant le code : 2 h 15** (+ 20 min pour tracer l'indicateur et mesurer l'état d'avant), annoncée au propriétaire avec les valeurs.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant qui décroche, aucun couvreur : le central reste ; couvreur présent : il suit

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Sorties non couvertes des centraux en baisse mesurée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (18/11/2026)

**Règle validée par le propriétaire le 18/11/2026** (« je valide », sans constante nouvelle ; chiffres réels non trouvés, les guides tactiques décrivent le principe « couverture et équilibre » sans le chiffrer) :
- sortie de ligne : un DC sort quand le point visé par son rôle (presser, marquer, suivre un receveur du pressing d'équipe) est à plus de `HOLE_AWAY_M` = 10 m de sa place de référence sans ballon, sans être plus près de son but qu'elle (`defense.line_exit`) ;
- couvert : un partenaire est déjà à `HOLE_FILLED_M` = 5 m ou moins de sa place ; ou un compensateur libre (ordre des compensations : MDC, autre DC, latéral) y arrive, délai de réaction compris, avant l'attaquant le plus proche (hors celui qu'il presse ou marque) et l'accepte (Teamwork, courbe des compensations, un tirage par partenaire visé, repris par la compensation qui suit : `_willing` lit `cover_draws`) ; ou aucun attaquant n'est à `HOLE_DANGER_M` = 20 m ou moins de sa place ;
- sinon il cède le rôle : presseur choisi parmi les autres (règle du 10a) ; seul joueur libre, il presse quand même ; marquage au défenseur libre le plus proche après lui, personne s'il était seul ;
- vérification quand le rôle devient une sortie ; sorti couvert, il garde son rôle pour le même partenaire (`exits`, `exits_before`).

Critères posés avant le code : sorties non couvertes des DC (presse et marquage) en baisse d'au moins 50 % ; buts, tirs, tacles, hors-jeu dans ± 10 % ; DC pressant hors de leur zone (acquis du 10a, 1,96 min par match) sans hausse de plus de 10 %.

**Code** : `v2engine/defense.py` (`line_exit`, `DefensiveRoles._leaves_uncovered`, `_covers`, `_remember_exits` ; `Assignment.reference` aussi pour la couverture et les marqueurs) ; trace `MatchTrace.line_exits` (`LineExitRecord` à chaque changement d'état d'un DC : rôle, sorti, place couverte, place menacée), écrite par `match._record_line_exits`, lecture seule. Sans bloc (scènes de test) : comportement d'avant. Tests : `tests/test_v2engine_central_couvert.py` (10 tests).

**Hors périmètre, tracé** : le rôle de couverture (6 m derrière le porteur) peut aussi sortir un central de sa ligne ; non restreint (périmètre validé : presser, marquer). Décision du propriétaire du 18/11/2026 : « Ticket séparé » → `10b2`.

**Mesure, 100 matchs appariés** (graines `AUDIT_SEED + k`, k = 0 à 99 ; `.scratch/v2-realisme/mesures/10b-central-couvert.py` et `10b-comparaison.py`, sortie `10b-comparaison.txt` ; « avant » = vérification neutralisée, scores identiques au 10a livré sur les 50 graines communes). Le premier bilan sur 50 matchs donnait buts − 12,8 % (IC ± 15,4 %) ; décision du propriétaire : « Doubler le banc ».

| Minutes par match (sauf compteurs) | avant | après | écart |
|---|---|---|---|
| Sorties non couvertes des DC (presse + marquage) | 6,78 | 1,92 | **− 71,6 %** |
| dont place menacée | 6,69 | 1,85 | − 72,3 % |
| presseur non couvert | 2,16 | 0,83 | − 61,5 % |
| marquage non couvert | 4,62 | 1,09 | − 76,4 % |
| couverture non couverte (hors périmètre, 10b2) | 3,62 | 3,29 | − 9,2 % |
| DC pressant hors de leur zone (10a) | 1,98 | 0,82 | − 58,8 % |

Chiffres après la correction A1 du passage 2 (100 matchs « après » relancés une deuxième fois ; passages précédents gardés en `10b-passe1-comparaison.txt` : − 71,6 %, buts − 4,2 %, hors-jeu − 12,7 % ; `10b-passe2-comparaison.txt` : − 71,7 %, buts + 0,2 %, hors-jeu − 7,3 %).

Écarts appariés (IC 95 %, approximation normale) : buts 5,03 → 5,22 (+ 3,8 %, [− 6,7 ; + 14,3]) ; tirs + 3,6 % ([0,0 ; + 7,1]) ; tacles + 0,1 % ([− 2,3 ; + 2,6]) ; fautes − 1,8 % ([− 6,0 ; + 2,4]) ; hors-jeu 4,11 → 3,80 (− 7,5 %, [− 22,1 ; + 7,0]), dans le critère de ± 10 %. Au passage 1, le hors-jeu à − 12,7 % avait été accepté par le propriétaire le 18/11/2026 (« Accepter l'écart ») ; l'écart n'est plus hors critère.

**Déterminisme** : deux exécutions à graine fixée, mêmes empreintes (score, trace des sorties, presseurs, ticks ; graines 20260923 et 20260924, 15 minutes) ; test `test_line_exits_are_traced_and_deterministic`. Après la correction A1 du passage 2 : deux processus séparés, matchs complets, mêmes empreintes (20260923 : 1-2, `568dd23c2d48` ; 20260924 : 3-7, `60bbf050bb94` ; au passage 2 : `fb610f4bc88e`, `fa237fad2dc6`).

**Suite complète** (18/11/2026, après la correction A1 du passage 2) : 3 415 passés, 0 ignoré, 14 désélectionnés (3 400 après le 10a + 15 tests nouveaux), 20 min 21 (passage 1 : 3 410, 18 min 39 ; passage 2 : 3 412, 18 min 53).

**Durée réelle** : environ 4 h 10 de travail effectif (analyse 35 min, développement 75 min, tests 55 min, intégration et vérifications 85 min) contre 2 h 15 estimées (révision avant le code), soit + 85 %. Causes : deux refus de l'expert (A1 au passage 1 puis au passage 2 : tirage Teamwork du couvreur, puis sa reprise par la compensation après un changement de porteur ; deux corrections, quatre tests, deux relances des 100 matchs « après », un test de compensation dépendant de l'ordre des tirages diagnostiqué et ressemé), banc doublé à 100 matchs (décision du propriétaire), rôle de couverture découvert dans les scènes puis tracé et sorti du périmètre (`10b2`). Non compté : correction des statuts de cinq tickets et création des tickets `10b2` et `expert-dispositif/07`. Temps machine hors total : 200 matchs du banc plus deux fois 100 relancés, trois suites complètes, une mesure de 2 000 scènes de compensation. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée.

## Comments

- **18/11/2026, passage 1 (/valider-ticket-simulafoot).** Expert `REJECTED` (empreinte `84578349`), contrôle qualité `VALIDÉ`, décision de clôture `REFUSÉ` (journal). **A1 [bloquant]** : le tirage Teamwork du couvreur était gardé par couple (central, couvreur) et remplacé dès que le partenaire visé changeait (porteur, attaquant marqué, receveur suivi, souvent dans le même tick) : un refus ne tenait qu'environ un tick, et la compensation pouvait reprendre un autre tirage que celui qui avait autorisé la sortie. Corrigé : un tirage par (central, couvreur, partenaire visé), gardé tant que le porteur ne change pas (comme la ligne de passe lue par le presseur), et la compensation reprend celui du partenaire pour lequel le central est sorti ; deux tests ajoutés avec des tirages non constants (`test_a_refusal_holds_while_the_holder_is_the_same`, `test_the_compensation_reuses_the_draw_that_let_him_out`) ; 100 matchs « après » relancés (sorties du passage 1 gardées en `10b-passe1-*`). **A2 [réserve]** : un couvreur compté pour la sortie du central peut recevoir ensuite un autre rôle dans le même tick (marquage, suivi) ; à traiter au `10b2` (réserver le couvreur) ou à consigner. **A3, A4 [facultatifs]** : exemption « sorti couvert » sans revérification (voulue, testée) ; durée de la suite dans `CLAUDE.md` (environ 10 min annoncées, 18 min 39 mesurées). Contrôle qualité, réserves non bloquantes : hors-jeu − 12,7 % (accepté par le propriétaire) ; durée réelle et ligne de `suivi-estimations.md` à faire avant le commit.
- **18/11/2026, passage 2 (/valider-ticket-simulafoot).** Expert `REJECTED` (empreinte `eb04ec4e`) ; contrôle qualité non relancé (le code devait changer) ; pas de décision de clôture journalisée pour ce passage. Critères chiffrés tenus (− 71,7 %, buts + 0,2 %, hors-jeu − 7,3 %, sorties gardées en `10b-passe2-*`). **A1 [bloquant]** : la compensation ne reprenait toujours pas le tirage qui avait autorisé la sortie quand le porteur changeait (décrochage servi : tirages des couvreurs effacés à la réception), ni quand un ancien tirage de trou (`willing`) était encore ouvert. Corrigé : le couvreur qui autorise la sortie est noté (`cover_found`, `exit_cover`) et son accord devient le tirage du trou (`willing`), réécrit à chaque tick tant que la sortie dure, quel que soit le porteur ; un trou encore ouvert impose son tirage à la couverture (`_covers`) ; deux tests ajoutés (`test_the_draw_that_let_him_out_survives_a_change_of_holder`, `test_an_open_hole_imposes_its_draw_on_the_cover`, ce dernier dans les deux sens). Effet de bord corrigé : `test_the_compensator_holds_the_place_after_the_winger_arrives` (`tests/test_v2engine_compensations.py`) tombait à 280/300 (seuil 285) parce que le flux `DEFENSE` n'y était pas ressemé à chaque graine (taux dépendant du nombre de tirages faits avant ; 15 échecs sur 300 au 10a, à la limite) ; même comportement avant et après (37 échecs sur 1 000 graines ressemées, 10a comme 10b) ; flux ressemés à chaque graine comme au coup d'envoi, seuil inchangé (5 échecs sur 300). A2 (réserver le couvreur) reste au `10b2` ; A3, A4 facultatifs, inchangés. 100 matchs « après » relancés.
- **18/11/2026, passage 3 (/valider-ticket-simulafoot).** Expert `APPROVED_WITH_RESERVATIONS` (empreinte `0199f71b`), contrôle qualité `VALIDÉ`, décision de clôture `VALIDÉ` (journal). A1 levé : l'accord qui laisse sortir le central devient le tirage du trou, repris par la compensation quel que soit le porteur ; test de compensation ressemé jugé légitime (comportement identique avant et après, seuil inchangé). **A2 [réserve]** : couvreur compté pour la sortie non réservé (peut recevoir un marquage ou un suivi au même tick) ; acceptée par le propriétaire le 18/11/2026 (« Accept A2 (Recommended) » : traitée au `10b2`). **A3, A4 [facultatifs]** : exemption « sorti couvert » sans revérification (voulue, testée) ; durée de la suite dans `CLAUDE.md` (environ 10 min annoncées, 20 min 21 mesurées), non modifiée sans accord du propriétaire. Contrôle qualité : réserves non bloquantes identiques (A2, A3, A4).
