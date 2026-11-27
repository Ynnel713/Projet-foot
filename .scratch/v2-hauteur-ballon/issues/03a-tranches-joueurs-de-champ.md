# 03a: Tranches de hauteur des joueurs de champ

**Ouvert le 27/11/2026**, découpage du ticket 03 (estimé 4 h 20, au-delà du seuil de 2 h ; découpage validé par le propriétaire le 27/11/2026).

**What to build:** un joueur de champ ne touche le ballon libre que s'il passe à une hauteur accessible à son corps, selon sa taille et sa détente. Remplace le seuil unique de 0,5 m (`hauteur.AERIAL_THRESHOLD_M`, provisoire depuis le 02a1) pour les contacts ; ce seuil ne sert plus qu'au `mode` transmis à l'API.

1. **Module `v2engine/portee.py`** (partie champ) : `field_band(height_m, jump_m, z)` rend la tranche touchée (`pied`, `corps`, `tete`) ou `None` (le ballon passe au-dessus). La fonction ne connaît pas le gardien (aucune lecture de `poste`).
2. **Taille** : `PlayerState.height_m`, depuis `Player.taille_fm` ; repli : médiane du poste dans `data/joueurs.xlsx`. Pas de repli `Taille (cm)` (décision du propriétaire : 16 joueurs sur 335 sans taille FM, et un champ de plus dans un fichier V1).
3. **Détente** : selon Jumping Reach (note exprimée, `effective_rating`).
4. **Contact sur le trajet** (`_step_loose_ball`) : premier instant, entre l'entrée et la sortie de portée du joueur, où le bas du ballon est sous son plafond ; le `return` anticipé « au-dessus de 0,5 m pendant tout le pas » disparaît. Le classement des réceptions du 02c est repris tel quel (`ball.landed`, `first_contact_s`, `caught_first_drop`), avec l'instant du contact à la place de l'instant d'entrée.
5. **Contres de tir** (`_blocked`) : le défenseur ne contre que si le tir passe sous son plafond (décision du propriétaire du 27/11/2026).
6. **Occasions** (`occasion.reach_probability`) : ballon jouable aux instants où il passe sous le plafond de la tête d'un joueur neutre, au lieu de 0,5 m. (Révisé à l'implémentation si un plafond par joueur est plus simple : voir Comments.)
7. Gardien : jusqu'au 03b, il suit les tranches de champ sur le ballon libre ; le chemin des tirs (`_keeper_reaches`) est inchangé ici.
8. La tranche touchée est tracée dans `ReceptionEvent.band`.

**Constantes (validées par le propriétaire le 27/11/2026)** — proportions du corps de Drillis et Contini (1966), reprises par Winter, *Biomechanics and Motor Control of Human Movement* ; `z` = bas du ballon, H = taille :
| Tranche | Plafond | Source |
|---|---|---|
| pied | z ≤ 0,530 H (hanche, grand trochanter) | Winter |
| corps | z ≤ 0,818 H (épaule) | Winter |
| tête | z + r ≤ H + détente (centre du ballon au sommet du crâne en saut ; r = rayon du ballon) | géométrie |
| détente | linéaire de 0,35 m (Jumping Reach 1) à 0,75 m (99) | non trouvé en mesure directe ; repères : saut sans élan des pros 0,35 à 0,45 m (Haugen et al. 2013), 0,71 m cité pour Ronaldo (presse, 2019) |
| taille absente | médiane du poste, `data/joueurs.xlsx` : GK 1,90, DC 1,88, BU 1,85, MDC 1,83, MC/LB/RB 1,80, AD/AG/MOC 1,78, SA 1,77 m ; autres : 1,83 (médiane de la base) | données |

Anti double comptage : Jumping Reach fixe ici la hauteur atteinte ; le ticket `v2-attributs-restants/01` ne départage que les joueurs éligibles, sans repondérer par Jumping Reach (`docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by:** 02c (livré le 27/11/2026).

**Bloque :** 03b ; et, avec le 03b, les tickets bloqués par le 03.

**Status:** livré (27/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse (faite en partie au 03) | 20 min |
| Développement | 40 min |
| Tests | 35 min |
| Intégration et vérifications (série, écarts, empreintes, documentation, revues) | 65 min |
| **Total (travail effectif)** | **2 h 40** |

Confiance : moyenne. Hypothèses : contact et classement réutilisent le 02c sans le réécrire ; un test du 02c (ballon qui remonte au-dessus de 0,5 m) est à adapter (plafond de la tête). Temps machine hors total : séries de 50 matchs avant et après (environ 50 min chacune), suite complète (environ 17 min).

## Acceptance criteria

- [x] Constantes proposées, sourcées ou notées « non trouvé », validées avant le code (27/11/2026)
- [x] Scène fixe : ballon à z = 2,5 m au-dessus d'un défenseur de 1,70 m (Jumping Reach 60) : il passe ; repris par un joueur de 1,90 m à Jumping Reach 99
- [x] Scène fixe : un ballon à 0,5 m est jouable du pied par tous (dès 1,60 m)
- [x] Test : `field_band` ne lit pas le poste (même résultat pour un gardien et un joueur de champ de même taille et détente)
- [x] Test : un ballon qui entre au-dessus du plafond et redescend dessous avant la sortie de portée est touché ; classement du 02c (centre à la première retombée, passe ordinaire après rebond) inchangé
- [x] Test : un tir au-dessus du plafond d'un défenseur n'est pas contré
- [x] 50 matchs (graines 0 à 49) avant/après : interceptions, possession, passes réussies, buts, contres, réceptions « centre », tranches touchées ; chaque écart hors bruit expliqué
- [x] Mêmes empreintes à graine fixée sur deux exécutions ; suite complète au compte attendu ; V1 inchangée
- [x] Durée réelle relevée et comparée

## Comments

**27/11/2026, périmètre élargi en cours de route (annoncé au propriétaire)** : la suite complète a relevé que l'estimateur de la chance de contre (`shooting._block_covers`, lu par la décision de tirer et l'xG) doit suivre la règle du contre réel (« toute modification de la résolution […] se reporte ici », `physical_shot_chance`) : chaque défenseur contre avec `BLOCK_CHANCE` × part des tirs qui passent sous son plafond, à son temps de vol (écart en hauteur gaussien comme `draw_shot_error`, hauteur par la loi du moteur : `line_height_m`, `ground_strike_m`, `launch_vz_to`). Aussi : garde des attributs (Jumping Reach et Taille annoncés avec effet ; Taille lue par le champ `height_m`), test du ballon mort (règle du 02a1 réécrite au plafond). Nouvelle estimation : **3 h 25** (+ 45 min : estimateur 20, tests 10, garde 15).

**27/11/2026, implémentation.**

*Code* : `v2engine/portee.py` (nouveau : tranches pied 0,530 H, corps 0,818 H, tête `z + r ≤ H + détente` ; détente 0,35 à 0,75 m selon Jumping Reach ; taille de repli par la médiane du poste ; `first_reachable_s`). `movement.PlayerState.height_m` (depuis `Player.taille_fm`, `match._build_players`), conservée par `movement.step`. `match._step_loose_ball` : le `return` anticipé « au-dessus de 0,5 m pendant tout le pas » est supprimé ; chaque joueur touche le ballon au premier instant de son passage à portée (`_exit_share`, `_reach_radius`) où le ballon est sous son plafond (`_reach_instant`), sinon il passe au-dessus ; contacts triés sur cet instant (au sol : ordre inchangé, tri stable). Classement du 02c repris tel quel (`ball.landed`, `first_contact_s`, `caught_first_drop`) avec l'instant du contact à la place de l'instant d'entrée. `ReceptionEvent.band` (pied, corps, tête). `match._blocked` : contre seulement sous le plafond du défenseur (instant d'entrée seul). `shooting._block_covers` / `_flight_shares` : chance de contre évaluée = `BLOCK_CHANCE` × part des tirs sous le plafond du défenseur, conditionnée à « sous la barre » pour la part qui marque (`_under_error`, dichotomie sur l'écart en hauteur, loi de hauteur du moteur). `occasion.reach_probability` : ballon jouable sous le plafond du joueur. `hauteur.AERIAL_THRESHOLD_M` ne règle plus que le `mode` de l'API. Gardien : tranches de champ sur le ballon libre ; chemin des tirs inchangé (03b).

*Bug trouvé en route* : `movement.step` reconstruit le joueur champ par champ et perdait `height_m` (tout le monde retombait sur la médiane du poste dès le premier pas) ; trouvé par la garde des attributs (Taille sans effet en 240 s), corrigé, test ajouté.

*Tests* : `tests/test_v2_portee.py`, 25 tests (constantes, détente, tranches, 0,5 m jouable du pied de 1,60 à 2,00 m, repli de taille, isolation du poste, scènes 2,5 m au-dessus d'un 1,70 m et repris par un 1,90 m à Jumping Reach 99, ballon qui redescend sous le plafond pendant le passage classé « centre », premier atteint sous son plafond, `first_reachable_s`, `_exit_share`, tranche tracée, tranche au plafond exact, tir au-dessus du défenseur non contré, taille conservée par `movement.step`). Adaptés, pas supprimés : `test_v2_reception_centre` (filtre au plafond de la tête ; ballon à 0,6 m touché de la poitrine), `test_v2engine_ballon_mort` (deux cas : passe haute au-dessus du joueur, passe à hauteur de poitrine touchée), `test_v2engine_garde_attributs` (Jumping Reach et Taille annoncés avec effet ; Taille lue par le champ `height_m` ; scène de 120 s, première divergence graine 2, pas 881), `test_v2engine_rayon_attributs` (exceptions de couverture retirées ; Jumping Reach en liste de transition jusqu'au `v2-realisme/15b`). Suite complète : **3 638 passés, 0 ignoré, 14 désélectionnés** (3 610 + 28), 19 min.

*Série de 50 matchs* (graines 0 à 49, `scripts.bench_series 50`) : avant = `03a-avant.json` (code de `145a292`), après = `03a-apres.json` ; bruit = séries A/B du 02a1 (`03a-tolerance.py`, `03a-tolerance.txt`). 2 823 indicateurs : 4,1 % hors bruit (3,2 % entre A et B), presque tous des cases à très petit effectif (rendement par tranche de 15 min, quartiles, calibration xG par tranche) ; au-delà de 1,3 × le bruit hors ces cases, 6 indicateurs, tous à effectif minuscule (calibration xG tranche [0 ; 0,03[, appels du banc porteur 0,0001 → 0,0005).
- **Dans le bruit** : buts 4,32 → 4,28 par match (0,0×), tirs par équipe 13,64 → 13,81, passes réussies 82,18 → 82,15 %, possession d'équipe 20,75 → 20,59 s, tirs contrés 24,2 → 22,4 % (0,5×), arrêts 5,86 → 6,64 par match (0,8×), touches 16,1 → 15,7, corners 4,28 → 4,38.
- **Réceptions « centre »** 0,20 → 0,92 par match (0,9× le bruit) : le centre cueilli de la tête ou de la poitrine redevient possible (le 02c l'avait presque effacé, faute de tranches).
- **Tranches touchées (contrôles réussis)** : pied 1 321,2, corps 1,0, tête 2,9 par match. Ballon en l'air : 1,63 → 1,44 % des ticks (les ballons aériens sont joués plus tôt).
- **Interceptions des passes** : pas d'indicateur direct ; passes longues réussies 64,5 → 63,2 %, pertes de balle 273,2 → 276,3 par match, dans le bruit. Effet global faible : peu de ballons passent entre 0,5 m et la tête des joueurs (relances longues et dégagements : environ 18 passes aériennes par match).
- Temps de calcul 263 → 237 s par match : les deux séries partageaient les processeurs avec la suite complète et d'autres mesures, pas comparable ; coût propre du 03a : une dichotomie de 16 pas par défenseur dans l'estimateur de contre.

*Déterminisme* : empreintes complètes (`14a1-empreinte.py`, graines 0 et 1) identiques sur deux exécutions : `51e9d7f42d0aadde`, `b62ead65e55e9311` (`03a-empreintes-1.txt`, `-2.txt`). V1 : aucun fichier touché.

*Durée* : estimée 2 h 40, réestimée 3 h 25 en cours de route (estimateur de contre, garde des attributs) ; réelle environ 3 h 50, non chronométrée (horloge de la session hors attentes machine), + 44 % sur l'estimation initiale, + 12 % sur la révisée. Postes : analyse 20 min (20), développement 1 h 15 (40), tests 50 min (35), intégration 1 h 25 (65). Cause : trois découvertes de la suite complète (estimateur de contre à aligner, puis à conditionner « sous la barre » ; garde des attributs ; taille perdue par `movement.step`), chacune avec une relance de la suite et de la série. Temps machine hors total : deux séries de 50 matchs (environ 60 min chacune), quatre suites complètes (18 à 19 min), trois paires d'empreintes.

**27/11/2026, clôture (passage 1)** : expert `APPROVED` ; QC `VALIDÉ` ; clôture journalisée `VALIDÉ`. Aucune anomalie bloquante, aucune réserve. Facultatifs (expert) : A1 retards adverses de `occasion.reach_probability` calculés sur le chemin filtré par le plafond du joueur évalué ; A3 coût de l'estimateur de contre (dichotomie) non mesuré à charge égale. Point à surveiller (expert, A2) : une tête passe par `attempt_control` comme un contrôle (2,9 par match), à reprendre aux `v2-realisme/15b`, `15c` et `v2-attributs-restants/01` ; à l'écran, têtes et poitrines sur dégagements longs et ballons montants près du passeur. Non bloquants (QC) : `docs/PLAN_V2.md` mis à jour ; compte attendu de `CLAUDE.md` (3 638) hors fichiers revus, reporté au prochain commit validé ; pas d'indicateur direct d'interceptions des passes.
