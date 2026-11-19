# 10b2: Le défenseur central ne prend la couverture que si sa place reste tenue

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (après le 10b, première source de sorties non couvertes des centraux). **Catégorie :** décision.

**Origine :** mesure du ticket 10b (18/11/2026, 50 matchs appariés) ; décision du propriétaire du 18/11/2026 : « Ticket séparé ».

**Constat vérifié :** le rôle de couverture (`defense.py`, point à `COVER_DEPTH_M` = 6 m derrière le porteur, porteur dans la moitié défendue) revient au premier arrivé sur ce point, quel que soit son poste. Le 10b ne l'a pas restreint (périmètre validé : presser, marquer). Après le 10b, un central couvre à plus de 10 m de sa place sans partenaire à 5 m ou moins de celle-ci pendant 3,28 min par match (contre 1,08 pour le marquage et 0,84 pour le pressing ; 3,62 avant le 10b) ; place menacée (adversaire à 20 m ou moins) 3,21 min. Sortie : `.scratch/v2-realisme/mesures/10b-comparaison.txt`, trace `MatchTrace.line_exits` (rôle `couverture`).

**What to build:** Appliquer au rôle de couverture la règle du 10b (`DefensiveRoles._leaves_uncovered`) : un central dont le point de couverture est une sortie (`line_exit`) ne le prend que couvert ; sinon la couverture revient au premier arrivé parmi les autres. À décider avec le propriétaire : si personne d'autre n'est libre, le central couvre-t-il quand même (comme le presseur) ou personne ne couvre (comme le marquage) ?

À traiter aussi (réserve A2 de l'expert au 10b, 18/11/2026) : un couvreur compté pour autoriser la sortie d'un central (`_leaves_uncovered`, lu dans `free`) peut recevoir ensuite un autre rôle dans le même tick (marquage d'un attaquant suivant, suivi d'un receveur) et ne plus être libre pour la compensation ; le réserver une fois retenu.

**Attributs :** aucun

**Lien avec l'existant :** prolonge le 10b (livré avec lui), sans nouvelle constante ; distinct du 10c (placement du défenseur le plus éloigné, sous la ligne, quand une passe en profondeur est possible), qui ne change pas l'attribution du rôle de couverture.

**Blocked by:** 10b (Le défenseur central ne quitte sa ligne que couvert).

**Bloque :** 10j.

**Status:** livré (19/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 10** |

Confiance : moyenne. Hypothèses : la vérification du 10b se réutilise telle quelle ; la mesure du 10b (`10b-central-couvert.py`) sert de banc.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs avant/après (environ 1 h 20).

**Révisée le 18/11/2026, avant le code : 1 h 40** (analyse 10 min, développement 30 min, tests 25 min, intégration et vérifications 35 min) : réserve A2 ajoutée au périmètre, intégration sous-estimée d'environ 1,5 d'après le registre ; validée par le propriétaire (« Je valide tout »).
Temps machine, non compté : 100 matchs appariés (environ 40 min) ; suite complète (environ 20 min).

**Révisée le 18/11/2026, en cours de route : 2 h 15** (+ 35 min : développement 10, test 10, intégration et vérifications 15) : critère principal manqué à la première mesure (− 42,8 %), revérification de la couverture à chaque tick décidée par le propriétaire (« Re-check the cover »). Temps machine, non compté : 100 matchs « après » relancés (environ 1 h), suite complète.

**Révisées le 19/11/2026, en cours de route : 3 h 15** (+ 1 h après le refus de l'expert : marge du titulaire et réserve A2) **puis 4 h 00** (+ 45 min : hystérésis du seuil de sortie, diagnostic de l'oscillation).

## Décisions du propriétaire (18/11/2026, « Je valide tout »)

- **Règle :** un central dont le point de couverture est une sortie (`line_exit`) ne prend la couverture que couvert (règle du 10b : partenaire à 5 m de sa place, compensateur qui y arrive avant l'attaquant et accepte, ou aucun attaquant à 20 m) ; sinon elle revient au premier arrivé parmi les autres. **Personne d'autre de libre : personne ne couvre** (comme le marquage).
- **Réserve A2 :** le couvreur compté pour autoriser la sortie d'un central est réservé pour le reste du tick (ni couverture, ni marquage, ni suivi) ; il reste libre pour la compensation.
- **Critères (100 matchs appariés, banc du 10b) :** couverture non couverte des centraux − 50 % au moins ; buts, tirs, tacles, fautes, hors-jeu dans ± 10 % ; sorties non couvertes presse + marquage pas plus de + 10 % ; tracé en plus : temps où un attaquant dangereux n'est pas marqué.

- **Revérification de la couverture (18/11/2026, décision du propriétaire : « Re-check the cover (Recommended) »)** : première mesure à − 42,8 % ; le diagnostic montre que les décisions de couvrir sans couverture ont presque disparu (1,60 → 0,03 min par match sur 4 matchs), mais que l'exemption « sorti couvert » s'applique désormais à la couverture (0,52 min par match) ; le central qui couvre est revérifié à chaque tick, sans cette exemption, gardée pour le pressing et le marquage.

## Réalisation (18-19/11/2026)

**Code** (`v2engine/defense.py`) :
- couverture : les candidats sont les libres non réservés pour qui `_leaves_uncovered` est faux, avec `recheck=True` (pas d'exemption « sorti couvert », vérification à chaque tick) ; personne : personne ne couvre ;
- hystérésis (réserve A1 de l'expert, passage 1) : le central titulaire de la couverture (même porteur, tick précédent) garde la marge `HOLD_MARGIN_S` sur l'arrivée de son couvreur, comme le titulaire d'une compensation, et perd le rôle aux seuils de `line_exit` ; un autre central ne prend sans couverture un point de couverture qu'à moins de `HOLE_AWAY_M` moins la distance qu'il parcourt à pleine vitesse en `HOLD_MARGIN_S` (2,6 m à Pace 60), ou à plus de cette distance en deçà de sa place vers son but ;
- réserve A2 (10b) : `DefensiveRoles.reserved`, vidé à chaque mise à jour ; `_reserve_coverer` y met le couvreur qui autorise une sortie (`cover_found`, ou `exit_cover` pour une sortie gardée) après chaque presseur, couverture, marquage et suivi ; le couvreur d'une sortie en cours est réservé avant le choix de la couverture (réserve A2 de l'expert, passage 1) ; les réservés ne reçoivent ni couverture, ni marquage, ni suivi, mais restent libres pour la compensation ;
- `_remember_exits` retient aussi les sorties de couverture (tirage du couvreur repris par la compensation).

Aucune constante nouvelle. Tests : `tests/test_v2engine_central_couvert.py`, 15 cas nouveaux, 11 fonctions dont 3 paramétrées (couverture cédée, personne ne couvre, central couvert quand sa place est tenue, couvreur réservé, revérification à chaque tick, marge du titulaire, couvreur d'une sortie en cours, perte au seuil, prise dans la bande, central qui a perdu le rôle, bande en deçà de la place) ; chacun des correctifs est vérifié par un test qui échoue sans lui.

**Mesure, 100 matchs appariés** (banc du 10b, graines `AUDIT_SEED + k`, k = 0 à 99 ; `.scratch/v2-realisme/mesures/10b2-couverture.py` et `10b2-comparaison.py`, sortie `10b2-comparaison.txt` ; « avant » = moteur du 10b livré, commit `4e4a56d`, lancé depuis un worktree ; scores « avant » identiques au 10b livré sur 100/100).

| Minutes par match (sauf compteurs) | avant | après | écart | critère |
|---|---|---|---|---|
| Couverture non couverte des DC | 3,29 | 1,23 | **− 62,5 %** | − 50 % au moins : tenu |
| dont place menacée | 3,23 | 1,17 | − 63,8 % | |
| Sorties non couvertes presse + marquage | 1,92 | 1,99 | + 3,3 % | + 10 % au plus : tenu |
| Attaquant dangereux non marqué | 0,00 | 0,00 | 0 | tracé |
| DC pressant hors de leur zone (10a) | 0,82 | 0,77 | − 5,5 % | |

Écarts appariés (IC 95 %) : buts 5,22 → 4,97 (− 4,8 %, [− 16,2 ; + 6,6]) ; tirs + 0,8 % ([− 2,8 ; + 4,4]) ; tacles − 0,4 % ([− 3,0 ; + 2,1]) ; fautes + 0,4 % ([− 3,5 ; + 4,3]) ; hors-jeu − 1,1 % ([− 14,4 ; + 12,3]) : tous dans ± 10 %.

**Stabilité de la décision** (vérification V1 de l'expert, 20 matchs, script hors dépôt `verif10b2.py` ; porteur inchangé) :

| Par match | 10b | 10b2 sans hystérésis | 10b2 livré | attendu (expert) |
|---|---|---|---|---|
| Allers-retours A → B → A en 1 s ou moins | 5,25 | 28,15 | 13,8 | ≤ 1,5 × avant |
| part des changements de couvreur | 2,0 % | 7,9 % | 4,2 % | ≤ 5 % |
| Épisodes DC de 0,5 s ou moins | 16,9 % | 25,2 % | 22,4 % | ≤ 15 % |
| Reprises par le même DC en 1 s ou moins | 2,5 | 22,75 | 8,1 | ≤ 2 × avant |
| Couvreur d'une sortie qui couvre (V2) | 19,6 % | 5,1 % | 0 % | ≤ 2 % |

Reprises restantes (diagnostic sur 4 matchs, `flip10b2.py`) : 19 sur 23 après une perte à la sortie se font avec un point revenu sous la bande (en moyenne 4 m en moins d'1 s : la place de référence suit le ballon), donc un vrai changement de situation, non un battement au seuil.

Étapes intermédiaires (gardées hors dépôt) : sans revérification − 42,8 % (exemption « sorti couvert » étendue à la couverture, 0,52 min par match) ; revérification seule − 53,6 % mais oscillation (rapport expert passage 1, REJECTED) ; marge d'arrivée seule : oscillation inchangée (cause : le point de couverture traverse le seuil de 10 m) ; bande du côté du titulaire (12,6 m) : oscillation 10,85 mais − 39,3 % et buts − 11,3 % ; bande du côté de l'entrée : retenue.

**Déterminisme** : deux processus séparés, matchs complets, mêmes empreintes (20260923 : 1-2, `c4887dede899` ; 20260924 : 3-2, `1635ffa83a4d`).

**Suite complète** (19/11/2026) : 3 430 passés, 0 ignoré, 14 désélectionnés (3 415 après le 10b + 15 cas nouveaux), 12 min 53.

**Durée réelle** : environ 4 h 30 de travail effectif (analyse 15 min, développement 65 min, tests 60 min, intégration et vérifications 130 min) contre 4 h 00 estimées (dernière révision), soit + 13 % ; + 170 % sur la révision d'avant le code (1 h 40). Causes : critère principal manqué à la première mesure (revérification décidée par le propriétaire), refus de l'expert au passage 1 (oscillation), trois essais d'hystérésis mesurés chacun sur 100 matchs et 20 matchs de stabilité, diagnostics des pertes de couverture ; deux interruptions de mesure (limite de temps d'une tâche de fond, redémarrage du conteneur), matchs manquants relancés un à un. Temps machine hors total : 700 matchs du banc, 140 matchs de stabilité, six diagnostics de 4 matchs, trois suites complètes (20 min 04, 17 min 16, 12 min 53), trois paires d'empreintes. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée.

## Comments

- **19/11/2026, passage 1 :** expert REJECTED (A1 bloquant : oscillation de la décision de couverture, allers-retours × 5,4 ; A2 réserve : couvreur d'une sortie de marquage en cours encore pris pour la couverture, 5,1 % ; A3 non vérifié : marge du critère ; A4 facultatif : point vérifié sans l'erreur de placement). Décision du propriétaire : « HOLD_MARGIN_S margin (Recommended) », « Yes, same pass (Recommended) » pour A2, puis « Je valide automatiquement toutes tes recommandations et celles de l'expert » (19/11/2026). QC non lancé (revue experte refusée).
- **19/11/2026, passage 2 :** expert APPROVED_WITH_RESERVATIONS (A3 du passage 1 levé : pire cas − 58,5 %). Réserves : A1 instabilité résiduelle de la décision de couverture (allers-retours 13,8 par match contre 5,25 au 10b, reprises 8,1 contre 2,5), attribuée surtout aux sauts de la place de référence, hors périmètre → ticket de suivi `10b3` créé, mesure de stabilité à refaire au 10j ; A2 fiche incohérente (− 53,6 % et 3 420 cités, ordre des révisions) → corrigée. Facultatifs non traités : A3 (réservation anticipée seulement porteur dans la moitié défendue, 0,2 % des ticks), A4 (point vérifié sans l'erreur de placement). Réserves A1 et A2 acceptées par le propriétaire : « Je valide automatiquement toutes tes recommandations et celles de l'expert » (19/11/2026). QC VALIDÉ. Clôture journalisée : VALIDÉ.

## Tests

- **Unitaires (scène contrôlée) :** porteur dans la moitié défendue, à 20 m devant la place du central, seul le central arrive le premier sur le point de couverture, place non couverte et menacée : un autre couvre ; milieu défensif sur sa place : le central couvre
- **Statistiques (séries de matchs) :** 50 matchs : minutes de couverture non couverte des centraux

## Acceptance criteria

- [x] Règle (repli si personne d'autre n'est libre) et critères chiffrés validés par le propriétaire avant le code
- [x] Couvertures non couvertes des centraux en baisse mesurée (− 62,5 %, 100 matchs appariés)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (3 430 passés)
