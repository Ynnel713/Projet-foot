# 15a1: Point d'attaque aérien

**Chantier :** `v2-realisme`. **Ouvert le 27/11/2026**, découpage du ticket 15a (validé par le propriétaire le 27/11/2026). **Catégorie :** décision.

**Constat vérifié (27/11/2026)** : le receveur d'une passe lobée ou d'une remise aérienne vise `anticipation.meeting_point`, qui suit la trajectoire avec la loi de freinage **au sol** (`freinage.position_after`) ; en vol, le ballon ne subit que la traînée (`freinage.step_velocity(..., airborne)`, ticket 14a2b) et va plus loin : le receveur vise un point trop court. La même prédiction sert à la défense pour placer le receveur à son point de réception (`defense.py`, passe en vol).

**What to build:**
1. `anticipation.aerial_attack_point(player, position, velocity, z, vz)` : sur le premier vol du ballon (jusqu'au sol, chute libre de `hauteur`, distance horizontale par la traînée seule `freinage.distance_after(..., airborne=True)`), le premier point où le bas du ballon passe sous le plafond du joueur (`portee.player_ceiling_m`) et que le joueur peut atteindre à sa vitesse de pointe au plus tard quand le ballon y passe (marge 0 s, epsilon technique 1e-6 s). Aucun point : le point de chute. Échantillonnage tous les 0,1 s comme `meeting_point`, plus l'instant exact où le ballon repasse sous le plafond et l'instant de chute.
2. `anticipation.receiving_point(player, ball)` : ce point tant que le ballon est dans son premier vol (`not ball.landed` et ballon en l'air), sinon `meeting_point` inchangé. Lu par le receveur (`cerveau.decide`, rôle `RECEVEUR`) et par la défense (point de réception du receveur pendant une passe en vol), pour qu'ils voient le même point.
3. Aucune sélection ici (15a2), aucun nouvel attribut lu : Pace (vitesse de pointe, comme `meeting_point`), taille et Jumping Reach par le plafond du 03a (même rôle : qui peut atteindre le ballon).

**Constantes** : aucune nouvelle (validées au 15a).

**Décision du propriétaire du 27/11/2026 (option 2, après la première série de 50 matchs)** : le receveur que personne ne conteste vise le point d'attaque à hauteur de **poitrine** (`portee.player_body_ceiling_m` : sous l'épaule, 0,818 × taille, Winter, constante du 03a ; gardien dans sa surface : ses mains), pas sous la tête. Le point sous la tête (plafond par défaut de `aerial_attack_point`) est réservé au ballon disputé (`15a2`). Motif : la première version (point sous la tête) faisait passer les réceptions de la tête de 2,9 à 13,0 par match et les réceptions « centre » de 1,0 à 12,8, une tête comptant comme un contrôle (`attempt_control`, point A2 de l'expert au 03a) ; passes longues réussies 62,3 → 71,3 %.

**Option A du propriétaire (27/11/2026, après la deuxième série)** : viser la poitrine ne suffisait pas (têtes 13,7 par match) : la règle de contact du 03a fait toucher le ballon au premier instant sous la **tête** dès que le joueur est à portée (1,0 m pour le receveur), et le point poitrine n'est qu'à environ 1 m plus loin sur la descente. Règle ajoutée (`match._contact_ceiling`, lue par le contact et la tranche de `_step_loose_ball`) : sur le premier vol de la passe, le **receveur visé** joue le ballon sous sa poitrine (`portee.player_body_ceiling_m`) ; tous les autres joueurs, et le receveur après le premier contact au sol, gardent le plafond du 03a (tête, mains du gardien dans sa surface). Le 15a2 rend la tête au receveur contesté.

**Option 2 du propriétaire (28/11/2026, réserve A1 de l'expert au passage 1)** : l'option A s'appliquait aussi aux corners centrés dans la surface (l'attaquant ciblé ne pouvait plus attaquer le centre de la tête, le défenseur voisin si). Centre de coup de pied arrêté dans la surface (`BallState.set_piece_cross`, posé au lancement : corner lancé en l'air vers la surface adverse, ou coup franc lobé vers elle ; remis à faux par `_ground`) : le receveur visé garde sa tête (point d'attaque sous la tête, plafond de contact du 03a). Le coup franc lobé vers la surface n'existe pas encore en match (le coup franc passe par le porteur, lobé seulement en relance longue ; coup franc centré : ticket 16i).

**Blocked by:** `v2-hauteur-ballon/03a`, `03b` (livrés).

**Bloque :** 15a2.

**Status:** livré (28/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse (faite au 15a) | 5 min |
| Développement | 25 min |
| Tests | 20 min |
| Intégration et vérifications (série, empreintes, documentation, revues) | 30 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Temps machine hors total : série de 50 matchs avant et après (environ 45 min chacune), suite complète (environ 18 min).

**Réestimation du 27/11/2026 (annoncée au propriétaire)** : + 20 min (point à hauteur de poitrine, tests, seconde série « après ») : **1 h 40** ; puis + 25 min (option A : plafond de contact du receveur, tests, troisième série) : **2 h 05** ; puis + 20 min (option 2 : centres de coup de pied arrêté, annoncée avec l'option) : **2 h 25**.

## Acceptance criteria

- [x] Scène : passe lobée de 40 m, receveur hors d'atteinte pendant le vol (25 m sur le côté du point de chute) : le point d'attaque est à moins de 1 m du point de chute réel du moteur (simulation au pas), et `meeting_point` (loi au sol) est plus court ; écart chiffré dans le rapport (précisé à l'écriture du test le 27/11/2026 : un receveur placé au point visé va au-devant du ballon dès qu'il passe sous sa tête, ce qui est la scène suivante)
- [x] Scène : receveur à poitrine (décision du 27/11/2026) : point sous l'épaule, plus loin sur la descente que le point sous la tête, atteint à temps ; gardien dans sa surface : ses mains
- [x] Scène moteur (option A) : le receveur visé, au point poitrine, touche le ballon de la poitrine ou du pied ; un autre joueur au même endroit le prend de la tête ; contrôle : sans la règle, le receveur le prend de la tête
- [x] (option 2) Centre de coup de pied arrêté : le receveur visé touche le ballon de la tête ; corner vers la surface marqué « centre », relance longue (sortie de but) non
- [x] Scène : receveur sous la trajectoire, plus près que le point de chute : il vise le premier point où le ballon passe sous son plafond et qu'il atteint à temps (vérifié : hauteur sous le plafond, temps d'arrivée ≤ temps du ballon)
- [x] Scène : ballon au-dessus du plafond tout le vol jusqu'au voisinage du joueur : point de chute
- [x] Ballon au sol ou après le premier rebond : `receiving_point` identique à `meeting_point`
- [x] Défense et receveur lisent le même point (test)
- [x] 50 matchs (graines 0 à 49) avant/après : passes longues réussies, réceptions « centre », tranches touchées, buts, possession ; écarts hors bruit expliqués
- [x] Mêmes empreintes à graine fixée sur deux exécutions ; suite complète au compte attendu ; V1 inchangée
- [x] Durée réelle relevée et comparée

## Comments

**27-28/11/2026, implémentation.**

*Code* : `anticipation.aerial_attack_point(player, position, velocity, z, vz, ceiling=None)` (premier vol : chute libre de `hauteur`, horizontal par la traînée seule `freinage.distance_after(..., airborne=True)` ; échantillons tous les 0,1 s, plus l'instant exact où le ballon repasse sous le plafond, `portee.first_reachable_s`, et l'instant de chute ; premier point sous `ceiling` atteint à la vitesse de pointe au plus tard quand le ballon y passe, `ARRIVAL_EPSILON_S` = 1e-6 s ; sinon le point de chute ; plafond par défaut : tête, `player_ceiling_m`, pour le 15a2). `anticipation.receiving_point(player, ball)` : premier vol (`not ball.landed`, ballon en l'air) → point d'attaque à hauteur de poitrine ; sinon `meeting_point` inchangé ; lu par `cerveau.decide` (RECEVEUR) et `defense` (point de réception du receveur pendant une passe en vol), qui ne lisent plus `meeting_point`. `portee.player_body_ceiling_m` (0,818 × taille ; gardien dans sa surface : mains, même aiguillage). `match._contact_ceiling` (option A) : receveur visé sur le premier vol → plafond de poitrine pour le contact et la tranche ; sinon plafond du 03a.

*Tests* : `tests/test_v2_point_attaque_aerien.py`, 16 tests (13 au passage 1, + 3 pour l'option 2 : centre de coup de pied arrêté joué de la tête ; corner vers la surface marqué, sortie de but longue non) : point de chute à 0,5 m du point réel du moteur au pas (traînée continue contre traînée au pas), `meeting_point` 2,7 m plus court dans cette scène ; receveur sous la trajectoire (point sous son plafond, atteint à temps) ; ballon au-dessus de lui : il attend la redescente ; même point sur deux appels ; au sol et après le premier rebond : `meeting_point` (3 cas) ; premier vol : point poitrine ; receveur et défense lisent la même fonction (et `decide`) ; point poitrine plus loin que le point tête et atteint à temps ; gardien : mains dans sa surface, épaule hors ; scène moteur : receveur au point poitrine touché de la poitrine, autre joueur au même endroit de la tête (contrôle : sans la règle A, le receveur le prend de la tête) ; `_contact_ceiling` hors premier vol. Aucun test existant modifié.

*Ancienne cible* (scène, passe lobée de 40 m à 20 m/s, chute à 70 m) : `meeting_point` (loi au sol) visait 44 à 59 m selon la position du receveur ; le receveur placé sous le point de chute revenait 14 m vers le passeur, ballon encore à plus de 4 m au-dessus de lui. Point d'attaque : 67,9 m (tête) ; 68,9 m (poitrine).

*Séries de 50 matchs* (graines 0 à 49 ; avant = code de `90f51e4`, worktree ; bruit = séries A/B du 02a1, `.scratch/v2-realisme/mesures/15a1-tolerance.py`) : quatre séries « après », une par version (`15a1-apres-tete`, `15a1-apres-poitrine`, `15a1-apres-optionA`, `15a1-apres` = option A + centres de coup de pied arrêté, retenue).

| Indicateur (par match) | Avant | Tête | Poitrine (cible seule) | Option A | Option A + corners (retenue) |
|---|---|---|---|---|---|
| Réceptions contrôlées de la tête | 2,88 | 12,96 | 13,66 | 0,94 | **2,16** |
| Réceptions contrôlées de la poitrine | 1,04 | 0,28 | 0,52 | 12,90 | **11,76** |
| Réceptions « centre » | 1,02 | 12,80 | 13,58 | 12,82 | 13,06 |
| Passes longues réussies | 62,3 % | 71,3 % | 70,0 % | 69,0 % | 68,9 % (2,4× le bruit) |
| Passes réussies | 81,9 % | 82,6 % | 82,4 % | 82,4 % | 82,6 % (1,6×) |
| Buts | 3,98 | 4,34 | 4,64 | 4,48 | 4,58 (0,7×) |
| Tirs par équipe | 13,5 | 14,6 | 14,9 | 14,1 | 14,5 (0,8×) |
| Corners | 4,22 | 3,68 | 4,40 | 4,20 | 4,04 (0,2×) |

Version retenue : 5,3 % des 2 822 indicateurs hors bruit (option A seule : 5,4 %) (3,2 % entre A et B), dont beaucoup de cases à petit effectif (rendement par tranche de 15 min). Écarts expliqués :
- **réceptions « centre » 1,0 → 12,8** : le receveur arrive enfin sous le ballon avant la chute (l'ancienne cible le laissait 14 m trop court) et le cueille à sa première retombée (règle du 02c) ; amorties de la poitrine (option A) ; les corners, joués de la tête (option 2), font remonter les têtes de 0,94 à 2,16 par match. Aucun indicateur des tirs ou buts issus de corner dans la série (condition de la réserve A1 pour le 15a2).
- **passes longues réussies 62,3 → 69,0 %** : même cause ; aucun défenseur n'attaque encore la trajectoire (lecteurs vidés pour les passes lobées) : correction attendue au `15a2`. Repère réel : environ 50 % (de mémoire, non revérifié dans cette session) : à sourcer au 15a2.
- **engagement de l'équipe sans possession** (joueurs à moins de 10 m du ballon 0,82 → 0,70, distance au coéquipier le plus proche 12,8 → 13,2 m, 1,9 à 2,3× le bruit) : hypothèse non vérifiée : le receveur ne revient plus vers le passeur, donc vers ses adversaires ; il reçoit dans la zone de chute, où personne ne l'attaque encore (15a2).
- **touches 16,16 → 11,96 par match** (2,6× le bruit ; même baisse dans les quatre versions : 11,1 / 12,0 / 12,3 / 12,0), manquée au passage 1, relevée par l'expert au passage 2 (A4) : l'indicateur, déjà trop bas (repère réel ≈ 42, fourchette 30 à 55 du ticket 29, `docs/INDICATEURS_V2.md`), s'éloigne encore. Cause probable, non vérifiée : l'ancienne cible, trop courte, laissait filer les ballons longs en touche ; le receveur les cueille désormais. À suivre au 15a2 (indicateur de contrôle).
- « MC, au-dessus de 25 km/h, 75-90 / 0-15 » à 7,1× le bruit : artefact de moyenne de ratios (écart-type 12,4 ; ratio agrégé 0,98 → 1,02), pas un effet.
- Temps de calcul : 193 → 215 s par match, non comparable (série « après » en parallèle des empreintes et de la suite complète).

*Déterminisme* : empreintes complètes (`15a1-empreinte.py`, graines 0 et 1, positions de tous les joueurs et du ballon à chaque pas, score) identiques sur deux exécutions : `181ef2b67a8056b6`, `4b5a9fe9b6213ea5` (`15a1-empreintes-1.txt`, `-2.txt` ; option A seule : `d472923b469bc87e`, `4da6a6f1166911dc`). V1 : aucun fichier touché.

*Suite complète* : **3 668 passés, 0 ignoré, 14 désélectionnés** (3 652 + 16), 22 min ; 4 avertissements `DeprecationWarning` de `fork()` dans `test_bench_series`, sans lien.

*Durée* : estimée 1 h 20, réestimée 1 h 40 (poitrine) puis 2 h 05 (option A), annoncées ; réelle environ 2 h 40, non chronométrée (horloge de la session hors attentes machine), + 100 % sur l'initiale, + 10 % sur la dernière réestimation (2 h 25). Postes : analyse 30 min (5 ; analyse du 15a et découpage comptés ici), développement 50 min (25), tests 35 min (20), intégration 45 min (30). Cause : trois retours au propriétaire (tête-contrôle mesuré, cible poitrine sans effet à cause de la règle de contact du 03a, corners relevés par l'expert au passage 1), chacun avec une série de 50 matchs, une suite complète et des empreintes de plus. Temps machine hors total : cinq séries de 50 matchs (41 à 61 min), quatre suites complètes (17 à 22 min), quatre paires d'empreintes.

**Points à vérifier à l'écran** : une relance longue : le receveur va sous le point de chute (plus de course à contresens vers le passeur) et amortit de la poitrine ; un adversaire proche peut encore la prendre de la tête avant lui ; sur un corner, l'attaquant ciblé attaque le ballon de la tête.

**28/11/2026, clôture (passage 1)** : expert `APPROVED_WITH_RESERVATIONS` (A1 receveur visé privé de sa tête sur corner ; A2 passes longues réussies 69 % contre un repère réel non sourcé ; A3 baisse de l'engagement de l'équipe sans possession, cause non vérifiée ; facultatifs A4 point juste après la frappe, A5 coût de calcul) ; QC non lancé. Décision du propriétaire sur A1 : option 2 (« 2 ») : corners et coups francs centrés retirés de l'option A, nouvelle série, revue à refaire.

**28/11/2026, clôture (passage 2)** : expert `APPROVED_WITH_RESERVATIONS` sur l'option 2 (A1 levée ; réserves A2 passes longues réussies 68,9 % contre un repère non sourcé, A3 engagement de l'équipe sans possession, cause non vérifiée, A4 touches 16,2 → 12,0 par match contre ≈ 42 en réel ; facultatifs A5 artefact « MC 75-90 / 0-15 », A6 point juste après la frappe et coût de calcul). **Réserves acceptées par le propriétaire le 28/11/2026** : « J'accepte A2, A3 et A4 », reportées comme critères numérotés du `15a2` (A2 sourcer le repère ≈ 50 % avant le 15a2 ; A3 mesurer la distance receveur / défenseur aux réceptions aériennes ; A4 suivre les touches et expliquer l'écart au réel chiffres en main, sinon bloquant pour le 15a2), avec la checklist des ballons aériens (instant du contact, cas d'usage, touches, distance receveur / défenseur).
QC `VALIDÉ` (non bloquants : assertion de test valable par tailles égales, docstring large, tests qui importent `SHOULDER_SHARE` hors `__all__`) ; clôture journalisée `VALIDÉ` (réserves acceptées).
