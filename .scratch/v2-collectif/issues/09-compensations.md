# 09: Compensations défensives en cascade

**What to build:** Quand un joueur quitte sa zone (latéral qui monte, milieu attiré), l'équipe identifie **qui peut compenser** : selon une hiérarchie (le milieu défensif coulisse, le défenseur central se décale, le latéral opposé resserre), le **temps qu'il lui faut pour arriver**, le danger réel et les profils. Compensations en cascade si le premier est lui-même attiré ailleurs. Pas de compensation systématique : un porteur bien protégé, ou une équipe qui choisit de prendre des risques, compense moins. Les erreurs de coordination (mauvaise décision, manque de concentration ou d'anticipation) créent des retards, de façon probabiliste. Scénario de référence : le latéral droit monte, le ballon est perdu, l'adversaire lance son ailier gauche. Précisé par le propriétaire le 02/11/2026 (« Oui, ça suffit ») : l'ailier **servi** dans le couloir est pressé et couvert (milieu défensif presseur, central voisin en couverture entre lui et le but), sans que la place du latéral soit comblée ; la compensation vaut pour l'attaquant qui court vers la place **sans ballon**.

**Attributs :** Positioning, Anticipation, Teamwork, Decisions, Concentration ; Pace + Acceleration pour le temps d'arrivée.

**Blocked by:** 07, 25 (socle cinématique et contact).

**Status:** livré (02/11/2026), validé expert + QC

## Constantes et critères validés par le propriétaire (01/11/2026, « Oui, valide tout », après revue de `simulafoot-architect`)

**Constantes** (ordres de grandeur ; valeurs réelles des compensations non trouvées)
- Trou : un défenseur (DC, LB, RB) à plus de 10 m de sa place dans le bloc sans ballon, personne d'autre à moins de 5 m de cette place, place dans sa moitié entre le ballon et son but, et un attaquant adverse non marqué à 20 m ou moins. Vaut en défense placée comme en transition défensive.
- Qui : milieu défensif, puis défenseur central voisin, puis latéral opposé (pour la place d'un central : l'un ou l'autre latéral), le plus proche de la place à rang égal ; le premier qui arrive avant l'attaquant (temps d'arrivée, Pace + Acceleration, capacité R5, plus son délai de réaction d'Anticipation) ; personne sinon.
- Titulaire gardé tant qu'il arrive au plus 0,3 s après l'attaquant (`HOLD_MARGIN_S`) ; il rend la place dès que le joueur absent revient à moins de 5 m de sa place.
- Cascade : deux niveaux au plus (on compense la place d'un défenseur parti compenser, pas au-delà).
- Teamwork : accepte de quitter sa place pour compenser, 99 → 95 %, 55 → 80 %, 11 → 55 % (courbe du ticket 08), un tirage par trou.
- Anticipation : délai de réaction existant (`anticipation.reaction_delay_s`) ajouté au temps d'arrivée. Positioning : erreur de placement existante appliquée au point de compensation (comme la couverture, ticket 07).
- Retirés : Decisions (règle R1 : un seul attribut pour « partir compenser », Teamwork) ; Concentration, renvoyée au ticket 21 (règle R3, sa condition est la fin de match et l'après-but) ; « équipe qui prend des risques », pas de mentalité d'équipe en V2.
- Frontière avec le ticket 10 : ici, qui comble la place vide ; au ticket 10, ce que fait le joueur qui l'a quittée (repli, contre-pressing).
- Réserve A2 : pendant une passe adverse en vol, rôles attribués comme si le receveur avait le ballon, à son point de réception ; le déclencheur du pressing suit toujours le vrai porteur ; les lecteurs de passe gardent leur priorité et sont retirés des joueurs libres.

**Critères** (avant : 4 matchs, graine d'audit, `81f3b3d` sans le ticket 13 en cours)
- C1 : scénario de référence, joueurs moyens, 1 000 tirages : place tenue avant l'arrivée de l'attaquant au moins 60 % (0 % avant).
- C2 : profils 99 contre 11 sur le même scénario : Teamwork et Anticipation, place tenue à temps plus souvent ; Positioning, compensateur à moins de 2 m de la place à l'arrivée de l'attaquant plus souvent.
- C3 : tirs de contre après récupération dans son camp, pas de hausse (3,5 par match ; 20 matchs).
- C4 : rôle attribué pendant plus de 90 % de la possession adverse, passes en vol comprises, lecteurs de passe comptés à part (57,5 %) ; distance médiane marqueur-attaquant à Marking 99 en baisse (8,20 m, marquages du pressing d'équipe compris).
- C5 : 15 à 17 passes par minute (15,8) ; tacles (51,75) et buts (3,0) sans dérive ; temps de calcul +25 % au plus (284 s) ; suite V2 verte ; V1 inchangée.
- C6 : le milieu défensif compense au plus 20 % du temps de possession adverse (ordre de grandeur, ajustable).
- Indicateur abandonné : « trou dans la ligne après une perte » (99,7 % des pertes, sans lien avec les tirs adverses : 3,7 % contre 5,1 %).

## Résultats (02/11/2026)

Code : `v2engine/defense.py` (`_compensate`, `_rank`, `_willing`, rôle `COMPENSATION`, passe en vol), `v2engine/cerveau.py` (rôle pendant la passe adverse en vol, action « compenser »). Tests : `tests/test_v2engine_compensations.py` (13 au passage 1, 17 au passage 3). Mesures sur une copie de `81f3b3d` plus ces deux fichiers, sans le ticket 13 en cours (`v2engine/decision.py` non commité), graine d'audit ; scripts de diagnostic hors dépôt.

| Critère | Avant | Après | Visé |
|---|---|---|---|
| C1 : place occupée (défenseur à moins de 5 m) quand l'ailier y arrive, déplacements réels, 1 000 tirages | 0 % | 96,2 % | ≥ 60 % |
| C2 : Teamwork 99 / 11 (même scénario) | — | 99,2 % / 91,3 % | 99 > 11 |
| C2 : Anticipation, compensateur placé pour 0,55 s de réaction | — | à temps à 99, pas à 11 | 99 > 11 |
| C2 : Positioning, compensateur visé à moins de 2 m de la place | — | > 90 % à 99, < 50 % à 11 | 99 > 11 |
| C3 : tirs de contre par match, récupération dans son camp (20 matchs) | 3,35 | **4,55** | pas de hausse : **non tenu** |
| C4 : rôle attribué pendant la possession adverse, passes en vol comprises (4 matchs) | 57,5 % | 98,8 % (lecteur sans rôle : 0 %) | > 90 % |
| C4 : distance médiane marqueur-attaquant, Marking 99 | 8,20 m | 7,36 m | en baisse |
| C5 : passes par minute (20 matchs) | 15,94 | 16,01 | 15-17 |
| C5 : buts par match / tirs par équipe (20 matchs) | 2,65 / 12,3 | 2,70 / 12,8 | sans dérive |
| C5 : tacles par match (20 matchs) | 47,3 | 50,0 | sans dérive (+6 %) |
| C5 : temps de calcul par match, mesuré seul | 273 s | 241 s | +25 % au plus |
| C6 : milieu défensif en compensation | — | 8,5 % | ≤ 20 % |

Suite complète : 2 262 passés, 13 désélectionnés (2 244 avant, plus 13 tests de ce ticket et 5 du ticket 13 en cours). Passage 2 (arbre isolé : `819e7e9` plus les seuls fichiers du ticket, la session des tickets 14 et 16 travaillant dans les mêmes fichiers) : 2 256 passés, 5 ignorés (NLG, environnement absent de la copie), 13 désélectionnés.

**Remesure après le commit du ticket 13 (`7a94d64`, 02/11/2026, 20 matchs, avant → après) :** tirs de contre après récupération dans son camp 3,45 → 4,5 (C3, réserve) ; passes 15,87 → 15,90 par minute ; tirs 12,5 → 12,25 par équipe ; buts 2,5 → 2,7 ; tacles 44,8 → 50,0 ; temps de calcul 182 → 207 s (+13,5 %, deux mesures en parallèle). Rôle attribué 56,6 → 98,8 % ; distance du marqueur à Marking 99 8,05 → 7,48 m ; milieu défensif en compensation 7,7 % (4 matchs). Suite complète sur `7a94d64` plus ce ticket : 2 262 passés, 13 désélectionnés. Déterminisme : même empreinte de trace sur deux exécutions (10 minutes, graine d'audit) : `e40b0564d4a4a897`.

**Remesure après les corrections A1 à A3 (passage 2, 02/11/2026, copie de `7a94d64` plus ce ticket, 20 matchs, machine seule) :** tirs de contre après récupération dans son camp 4,05 (3,45 avant ; réserve C3) ; passes 15,94 par minute ; tirs 12,3 par équipe ; buts 2,65 ; tacles 51,15 (44,75 avant, +14 % : à soumettre à l'expert) ; temps de calcul 117 s (non comparable aux 182 s de référence, mesurés sur une machine chargée). 4 matchs : rôle attribué 98,8 % ; milieu défensif en compensation 8,3 à 8,7 % ; distance du marqueur à Marking 99 7,46 m (8,05 avant). Déterminisme : même empreinte sur deux exécutions, `cb7b02eab890a147`.

**Réserve C3, acceptée par le propriétaire le 02/11/2026 et renvoyée au ticket 10.** Décomposition sur 20 matchs (mêmes graines) :

| Variante | Tirs de contre, récupération dans son camp | Récupérations dans son camp | Buts | Tacles |
|---|---|---|---|---|
| Avant | 3,35 | 400,7 | 2,65 | 47,3 |
| Passe en vol (A2) seule | 4,30 | 395,0 | 2,30 | 55,6 |
| A2 et compensations | 4,55 | 400,1 | 2,70 | 50,0 |

La hausse vient de A2, pas des compensations ; le nombre de récupérations dans son camp ne change pas, ce sont ces contres qui aboutissent plus souvent à un tir (0,84 → 1,14 % des récupérations). Cause non établie. La réaction de l'équipe qui perd le ballon (contre-pressing, repli) relève du ticket 10.

Revue `simulafoot-reviewer` (02/11/2026) : aucun bloquant ; corrigés : titulaire passé à un autre rôle, tirage Teamwork refait à chaque réouverture du trou (gardé désormais jusqu'au retour de l'absent), test C1 sans déplacement, titulaires périmés pendant une passe, niveaux de cascade non remis à zéro, attaquant hors-jeu compté comme menace, point de réception hors du terrain, commentaires, carte des attributs. Le porteur compte parmi les menaces (l'ailier servi du scénario de référence) : lecture de « attaquant non marqué » confirmée par l'expert au passage 2 (seul un rôle de marquage retire un attaquant des menaces).

- [ ] Test de compensation : pertes de balle après une montée de latéral, avec et sans couverture du milieu ; occasions de contre mesurablement moins nombreuses avec compensation — non démontré en match (contres 3,45 → 4,05, hausse venant de la passe en vol) ; en scène, place tenue 96,2 % avec compensateur, vide sans (C1). Renvoyé au ticket 10 (réserve A1 de l'expert, passage 2)
- [x] Une compensation n'est choisie que si le joueur peut arriver à temps (temps de déplacement calculé)
- [x] Les profils meilleurs en Positioning, Anticipation et Teamwork compensent mesurablement mieux
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18) — Teamwork : tirage sur la courbe du ticket 08 ; Anticipation : `reaction_delay_s` existant ; Positioning : `bloc.placement_error` existant ; Decisions et Concentration retirés (R1, R3) ; `tests/test_v2engine_rayon_attributs.py` vert, sans nouveau module autorisé
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22) — aucune constante réglée sur une mesure ; tacles (+14 %) renvoyés au ticket 22
- [x] Suite V2 verte ; V1 inchangée

**Reporté du ticket 07 (réserve A2 de l'expert, rattachée ici par le propriétaire le 30/10/2026)**

- Le problème : quand une passe est en l'air (36 % du temps de jeu, mesuré sur 4 matchs), `DefensiveRoles.update` ne donne aucun rôle (`v2engine/defense.py`). Les défenseurs reviennent alors à l'ancienne règle, « ballon libre à moins de 15 m, sinon bloc ».
- La conséquence : le marqueur lâche son attaquant au moment où la passe part vers lui. C'est probablement pour cela qu'un marqueur à Marking 99 reste à 3,66 m de son attaquant, en médiane, pour 1 m visé.
- La piste de l'expert : tant que `ball.receiver` est renseigné, attribuer les rôles comme si le receveur était déjà le porteur. Le presseur vise le point de réception (`meeting_point`) et les marqueurs restent en place. Les lecteurs de passe gardent leur priorité.
- [x] Un rôle défensif est attribué pendant plus de 90 % du temps de possession adverse, passes en vol comprises
- [x] La distance médiane entre le marqueur et son attaquant baisse à Marking 99 (`diag_marking.py`, à recréer hors dépôt)

## Comments
- 02/11/2026, passage 1 (base `7a94d64`, empreinte `45764bb1`) : expert REJECTED, QC BLOQUÉ, clôture REFUSÉ (journalisée).
  - A1 [bloquant] : le compensateur lâchait la place dès l'arrivée de l'ailier (33,7 % des tirages, temps de montée en vitesse compté à distance nulle), contraire à la règle « il rend la place quand l'absent revient à moins de 5 m ». Corrigé : arrivé (à 5 m de la place ou de son point visé), il la tient jusqu'au retour de l'absent.
  - A2 [bloquant] : le porteur, toujours « pris » par le presseur, n'était jamais une menace, contrairement au ticket. Corrigé : seuls les attaquants marqués (rôle de marquage) sont exclus.
  - A3 [réserve] : niveaux de cascade remis à zéro sur un tick de ballon libre. Corrigé.
  - A4 [réserve] : le test C1 s'arrêtait à l'arrivée de l'ailier. Tests V1 (tenue de la place 2 s après) et A2 ajoutés.
  - QC : C3 non tenu et acceptation non tracée hors du ticket (le propriétaire l'a acceptée dans la conversation du 02/11/2026 : « Ok avc ta recommandation ») ; première case (contres moins nombreux avec compensation) non démontrée ; lecture du porteur comme menace à confirmer.
  - Vérification V2 de l'expert, après correction : l'ailier servi est pressé et couvert dans 100 % des ticks, mais la place du latéral (bloc) recule avec le ballon et l'ailier porteur en est toujours à plus de 20 m : pas de compensation dans ce scénario synthétique (0 %).
- 02/11/2026, passage 2 (base `819e7e9`, arbre isolé, empreinte `d89f84e5`) : expert APPROVED_WITH_RESERVATIONS, QC REFUSÉ (journalisé, 1er refus) ; pas de décision de clôture (désaccord).
  - Expert : A1 et A2 du passage 1 corrigés (V1 96,2 %, test du porteur pressé) ; réserves A1 (C3 3,45 → 4,05 et première case, renvoi au ticket 10) et A2 (tacles 44,75 → 51,15, renvoi au ticket 22) ; facultatifs A3 (test avec une vraie hauteur de ligne), A4 (temps de vol restant), A5 (temps de calcul non comparable).
  - QC : bloquants : première case non démontrée ; scénario de référence non compensé en flux réel (V2) ; cases rayon/double comptage et calibration non fermées. Ouverts : tacles, fiche périmée.
  - Test A3 écrit après le passage 2 : avec `bloc.update`, l'ailier servi est à 12 à 19 m de la place (dans le rayon), mais la place n'est jamais comblée (0/200) : le milieu défensif le presse, le central voisin le couvre, les autres n'arrivent pas à temps. L'hypothèse de l'expert (0 % dû à la scène) est donc réfutée.
  - Décision du propriétaire (02/11/2026, « Oui, ça suffit ») : face à l'ailier servi, presser et couvrir suffit ; la compensation vaut pour l'attaquant sans ballon. Scénario de référence précisé en tête du ticket ; test `test_the_served_winger_is_pressed_and_covered_with_a_real_line_height` ajouté ; cases rayon et calibration fermées avec leurs preuves.
- 02/11/2026, passage 3 (base `819e7e9`, arbre isolé, empreinte `d3fb6dfb`) : expert APPROVED_WITH_RESERVATIONS ; QC REFUSÉ (journalisé, 2e refus) sur le seul motif de l'acceptation non tracée du report de la première case.
  - Expert : moteur identique au passage 2 ; test de l'ailier servi conforme à la décision du propriétaire ; hypothèse du passage 2 reconnue fausse. Réserves A1 (C3 et première case) et A2 (tacles) ; facultatifs A3 (temps de vol restant) et A4 (temps de calcul).
  - Réserve A1 acceptée par le propriétaire le 02/11/2026, dans la conversation : « J'accepte » (clôturer avec la première case ouverte, renvoyée au ticket 10, remesurée à sa clôture). Tracée dans `10-transition-defensive.md`.
  - Réserve A2 acceptée par le propriétaire le 02/11/2026, dans la conversation : « J'accepte » (tacles +14 % renvoyés à la calibration du ticket 22). Tracée dans `22-calibration-generale.md`.
- 02/11/2026, passage 4 : QC VALIDÉ (code identique au passage 3). Clôture VALIDÉ, journalisée par `cloture.py decision` (expert APPROVED_WITH_RESERVATIONS du passage 3, réserves A1 et A2 acceptées par le propriétaire, empreinte `d3fb6dfb`).
