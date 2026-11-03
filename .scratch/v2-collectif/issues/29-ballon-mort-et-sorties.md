# 29: Ballon mort : touches, sorties de but, corners, engagement

**What to build:** Aujourd'hui le ballon ne peut pas sortir : `geometry.clamp_to_pitch` le retient à la ligne (`match.py:266-268`), où il reste collé jusqu'à ce que la friction l'arrête. Après un tir non converti, le gardien reçoit le ballon sur place (`match.py:225-237`). Après un but, le ballon est posé au centre et le premier arrivé le prend (`match.py:222`). Ce ticket crée le **ballon mort** et ses remises en jeu simples, socle de tout ce qui suit (arrêts variés, corners, fautes, célébrations).

1. **Détection de la sortie** : un ballon libre ou passé qui franchit une ligne sort. Les joueurs restent bornés au terrain. Les points visés par `anticipation.loose_ball_target` et `meeting_point` tiennent compte des lignes.
2. **Qui remet en jeu** : touche (ligne latérale) pour l'adversaire du dernier toucheur ; ligne de but : **sortie de but** (relance du gardien depuis les 6 mètres) si le dernier toucheur est un attaquant, **corner** si c'est un défenseur. Le dernier toucheur est ajouté à l'état du ballon.
3. **Exécution simple** : touche jouée court ou longue, sortie de but jouée court ou longue, corner joué court ou centré simplement (les centres variés viennent au ticket `v2-attributs-restants/11`). Le choix dépend de la situation (pression, solutions de passe, score), jamais d'un tirage libre. Le hors-jeu ne s'applique pas à ces trois remises en jeu.
4. **Temps mort** : le ballon est mort pendant un temps proposé, les joueurs se replacent (placement du bloc pour chaque remise, preneur choisi par proximité et rôle) puis le jeu reprend. Ce temps alimente le temps additionnel (`v2-coach-et-gestion-de-match/03`) et fait baisser le temps de jeu effectif.
5. **Engagement après but** : coup d'envoi par l'équipe qui a encaissé, tous les joueurs replacés dans leur camp, au lieu du ballon posé au centre.
6. **Mode de ballon** : un champ de la trace (et de l'état du ballon), au ras du sol par défaut ; aérien et lobé sont posés par les tickets suivants. L'écran lui associe un rendu simple (taille ou ombre du ballon, trajectoire courbe). Le moteur reste à plat (D-V03) : le mode sert à l'affichage et à deux règles (un joueur au sol n'intercepte pas un ballon aérien sur son trajet, sauf à son point de chute ; un tir « au sol » reste contrable).
7. **Trace** : événement de sortie de balle (minute, type, équipe, position, dernier toucheur), engagement, mode de ballon par tick.

**Attributs :** aucun nouveau (Long Throws, Corners : ticket `v2-attributs-restants/02`). Decisions règle jeu court ou long, comme pour toute passe.

**Blocked by:** 16 (évite de modifier `cerveau.py` et `off_ball.py` en parallèle). Avant 28, 30 et 22.

**Status:** livré (03/11/2026), validé expert + QC (réserves A1 et A2 acceptées par le propriétaire, voir Comments)

**Origine (03/11/2026) :** constat du propriétaire (« le ballon ne sort jamais, ni en touche ni en 6 mètres ») et revue de réalisme (décisions Q3, Q6, Q7, Q14, Q17).

**Constantes à proposer avant le code :** durée du ballon mort par type de remise en jeu ; distance de replacement ; part de remises jouées court ou long selon la situation ; vitesse d'une touche longue.

**Chiffres réels :** touches, sorties de but et corners par match, durée d'un ballon mort, temps de jeu effectif (environ 55-60 minutes sur 90, ordre de grandeur de mémoire) : **non trouvés, à sourcer** avant d'en faire des critères.

## Chiffres réels sourcés (03/11/2026)

| Grandeur | Valeur | Source |
|---|---|---|
| Touches par match | ≈ 42 (16 154 sur 380 matchs, PL 2018-19) | Sheffield Hallam, shura.shu.ac.uk/27964 |
| Corners par match | ≈ 10 à 11 (PL 2023-24, source faible) ; ≈ 8,5 centrés directement (PL 2025-26) | theanalyst.com |
| Sorties de but par match | **non trouvé** (aucun chiffre publié lisible) | — |
| Durée d'arrêt : touche | 13 à 16 s (PL 2025-26 : 15,3 s ; CdM 2026 : 13,2 s) | theanalyst.com, premier-league-rules-throw-ins-goal-kicks-ball-in-play |
| Durée d'arrêt : sortie de but | 24 à 30 s (PL 2025-26 : 30,1 s ; CdM 2026 : 23,7 s) | idem |
| Durée d'arrêt : corner | 28 à 34 s (PL 2025-26 : 33,9 s) | idem ; fivethirtyeight.com (CdM 2018) |
| Temps de jeu effectif | 53 à 56 % (L1 55,9 %, PL 53,1 %, CIES/Impect 2026) | morning-foot.com, cies.ch |

Le temps effectif réel inclut fautes, remplacements, blessures et VAR, absents à ce stade (tickets 30, `v2-coach-et-gestion-de-match/05`, `v2-attributs-restants/09`) : la cible de ce ticket est donc plus haute que 55 %.

## Constantes retenues (03/11/2026, recommandation validée par délégation du propriétaire)

| Constante | Valeur | Justification |
|---|---|---|
| `DEAD_THROW_IN_S` | 15 s | médiane réelle 13-16 s |
| `DEAD_GOAL_KICK_S` | 25 s | réel 24-30 s |
| `DEAD_CORNER_S` | 30 s | réel 28-34 s |
| `DEAD_KICKOFF_S` | 45 s | célébration + replacement ; la vraie célébration vient de `v2-mise-en-scene/04` |
| `RESTART_DISTANCE_M` | 9,15 m (corner, sortie de but, engagement) ; 2 m (touche) | Lois du jeu |
| Engagement | chaque joueur dans son camp, adversaires hors du rond central | Lois du jeu |
| Point de la sortie de but | sur la ligne des 6 m (5,5 m de la ligne de but), du côté de la sortie | Lois du jeu (simplifié) |
| Choix court ou long | **pas de part fixe** : le preneur passe par la décision de passe existante (`choose_action`, Decisions), tir et conduite exclus ; la pression et les solutions décident | règle du ticket : jamais un tirage libre |
| Portée d'une touche | 25 m au plus, vitesse de lancer ≤ 14 m/s ; la touche longue de Long Throws vient de `v2-attributs-restants/02` | lancer à la main |
| Preneur | touche : joueur de champ le plus proche, latéral préféré à distance égale ; corner : joueur offensif (ni GK ni DC) le plus proche ; sortie de but : gardien | « proximité et rôle » |
| Mode aérien | corner centré, touche ou sortie de but de plus de 25 m ; un joueur ne touche un ballon aérien qu'à moins de `AERIAL_LANDING_M` = 3 m de son point de chute | D-V03, moteur à plat |

## Critères chiffrés (posés avant le code)

- Scènes contrôlées : 100 % des sorties donnent la bonne remise (touche, corner, sortie de but) au bon camp ; 0 hors-jeu sifflé sur ces remises ; 0 joueur hors du terrain sur tout un match.
- Après un but : l'équipe qui a encaissé engage ; au coup d'envoi, 22 joueurs sur 22 dans leur camp.
- En match (50 matchs, graine d'audit) : touches 30 à 55 par match, corners 6 à 14, sorties de but 8 à 25 (fourchette large faute de chiffre sourcé) ; temps de jeu effectif entre 65 et 80 % (plus haut que le réel tant que fautes et remplacements manquent).
- Cohérence du choix : part de remises jouées long plus haute sous pressing haut adverse qu'en bloc bas adverse (écart d'au moins 10 points).
- Un joueur au sol n'intercepte pas un ballon aérien sur son trajet (test unitaire).

**Point de vigilance :**
- Le tirage supplémentaire et le temps mort décalent la suite aléatoire et les possessions : toutes les mesures de référence sont à refaire (comme après les tickets 25 et 26).
- Les fichiers protégés du rendu V1 (`render/canvas.html`, `ball.py`, `serialize.py`, etc.) ne sont pas touchés : le rendu V2 est `ui/src/routes/V2Match.jsx`.
- Le tir non converti ne finit plus forcément dans les mains du gardien : cette issue appartient au ticket 28, qui s'appuie sur celui-ci. Ici, un tir à côté sort du terrain et reçoit la remise en jeu qui convient.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes contrôlées : un ballon qui franchit la ligne latérale donne une touche à l'adversaire du dernier toucheur ; la ligne de but donne un corner (dernier toucheur défenseur) ou une sortie de but (dernier toucheur attaquant) ; aucun hors-jeu sur ces trois remises en jeu
- [ ] Aucun joueur ne sort du terrain ; aucun point visé de ballon libre n'est hors du terrain sans que la sortie soit traitée
- [ ] Après un but, l'équipe qui a encaissé donne le coup d'envoi, tous les joueurs sont dans leur camp
- [ ] En match (50 matchs, graine d'audit) : touches, sorties de but et corners par match non nuls, tracés, comparés aux chiffres réels sourcés ; temps de jeu effectif mesuré
- [ ] Le mode de ballon est tracé et affiché ; un joueur au sol n'intercepte pas un ballon aérien sur son trajet (test)
- [ ] Le choix jeu court ou long dépend de la situation (test de cohérence : plus de jeu long sous forte pression adverse haute qu'en possession tranquille)
- [ ] Indicateurs ajoutés au banc (`scripts/v2_indicators.py`) et définis dans `docs/INDICATEURS_V2.md`
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Réalisation (03/11/2026)

**Code.** `v2engine/restart.py` (nouveau) : détection de la sortie (`exit_point`), remise à l'adversaire du dernier toucheur (`award`), preneur par proximité et rôle, placement pendant le ballon mort à distance réglementaire (`place`), choix du receveur (`restart_target` : réussite × liberté × progression, puis Decisions ; jamais un tirage libre), ballon aérien (`is_aerial`). `match.py` : ballon mort tenu au point de remise puis joué par une passe sans hors-jeu (`_play_restart`) ; coup d'envoi du match et engagement après un but par l'équipe qui a encaissé ; dernier toucheur suivi ; ballon aérien intouchable avant son point de chute ; **tir à côté** (`SHOT_WIDE_SHARE` = 0,64 des tirs non convertis, sourcé : 45,1 % des tirs non contrés cadrés en Premier League sur 20 saisons) qui file vers la ligne et peut être contré en route. `cerveau.think` : pendant le ballon mort, le preneur va au point, les autres se replacent au trot (`REPLACING_INTENSITY` = 0,5). `situation.py` : une remise en jeu n'est ni une perte ni une récupération. `anticipation` : points visés bornés au terrain. Trace : `RestartEvent`, mode et ballon mort par tick (`BallSnapshot.mode`, `.dead`). **Affichage reporté** : l'écran V2 (`api/routers/v2.py`, `ui/src/routes/V2Match.jsx`) est en cours de modification par une autre session (feuille de match, non commitée) ; le dessin du ballon aérien (plus gros, avec son ombre) écrit ici a été effacé par elle. Il sera repris dans un suivi dès son commit, pour ne pas mélanger les deux travaux dans un même commit. Banc : `on_restart`, option `--debut` (lots parallèles).

Constantes ajoutées pendant le code (validées par délégation) : `SHOT_WIDE_SHARE` 0,64 (sourcée), `SHOT_WIDE_M` 0,5 à 5 m au-delà du poteau (non trouvé, ordre de grandeur), `REPLACING_INTENSITY` 0,5. Écarts à la table : pas de vitesse propre à la touche (la loi de passe s'applique, moteur à plat) ; latéral préféré « à distance égale » lu comme « dans la même tranche de 5 m ».

**Tests.** `tests/test_v2engine_ballon_mort.py` (11 tests : lignes, touche, corner, sortie de but, ballon mort puis remise sans hors-jeu, engagement et camps, distance réglementaire, ballon aérien, points visés bornés, jeu long sous pressing, portée de la touche) ; `test_v2engine_shooting.py` adapté (engagement au lieu du centre ; tir cadré au gardien) et `test_wide_shot_leaves_the_pitch_for_a_goal_kick` ajouté ; `test_v2engine_rayon_attributs.py` : `restart` autorisé à lire Decisions ; faux ballon de `test_v2_indicators.py` complété (`restart=None`).

**Mesures (graine d'audit, banc `measure_v2`).** Avant = moteur `bce1f74`, 20 matchs ; après = 20 mêmes matchs, puis 50 matchs.

| Indicateur | Avant (20) | Après (20) | Après (50) | Critère | Verdict |
|---|---|---|---|---|---|
| Touches par match | 0 | 22,1 | 22,7 | 30-55 (réel ≈ 42) | **NON** |
| Sorties de but par match | 0 | 11,6 | 10,1 | 8-25 | OK |
| Corners par match | 0 | 0,80 | 0,84 | 6-14 (réel ≈ 10) | **NON** |
| Engagements par match | — | — | 3,4 | indicateur | |
| Temps de jeu effectif | 100 % | 85,8 % | 86,6 % | 65-80 % | **NON** |
| Sorties de but jouées long | — | — | 28,9 % | indicateur (réel ≈ 50 %) | |
| Corners centrés | — | — | 78 % | indicateur | |
| Buts par match | 3,30 | 2,75 | 2,38 | 2-3,5 | OK |
| Tirs par équipe | 12,2 | 12,2 | 10,9 | 8-15 | OK |
| Passes par minute de match | 15,8 | 13,7 | 13,9 | 15-17 | (16,0 par minute de jeu effectif) |
| Hors-jeu par match | 1,50 | 1,45 | 1,48 | 3,2-3,5 | inchangé |
| Tacles par match | 43,1 | 36,8 | 36,9 | 30-40 | OK |

Contrôles : 0 joueur hors du terrain (2 matchs complets, position bornée par `movement.step`) ; déterminisme à graine fixée vérifié (même empreinte de trace sur deux exécutions, 15 minutes). Le temps de calcul n'est pas comparable (8 processus en parallèle après, 4 avant).

**Lecture.** Les volumes baissent avec le temps de jeu effectif (−14 %), à rythme égal par minute de jeu. Les trois critères non atteints ont une même cause : le moteur ne produit presque pas de jeu qui sort. Passes longues 0,4 % des passes, ni centre, ni dégagement, ni contre, ni arrêt repoussé ; un corner suppose un défenseur qui touche le ballon en dernier derrière sa ligne. Ces actions sont l'objet des tickets 28 (contres, arrêts repoussés et claqués en corner, dégagements), 32 (passes lobées et longues), `v2-attributs-restants/11` (centres) et 30 (fautes, qui ajoutent du temps mort). Le temps effectif suivra mécaniquement les volumes. Recommandation : corners et touches deviennent des indicateurs suivis ici, avec critère repris aux tickets 28 et 22 ; temps de jeu effectif repris au 22 (après 28, 30 et 32). Pas de réglage artificiel ici (par exemple forcer des sorties) pour atteindre les fourchettes.

**À vérifier à l'écran.** Ballon aérien : après le suivi d'affichage ; replacement au trot pendant le ballon mort ; engagement depuis le rond central, chaque équipe dans son camp ; le preneur en retard est posé au point de remise (`ponytail`, à animer si la relecture le montre).

## Comments

**Passage 1 (03/11/2026), base 31458a2, empreinte bdd1fe75…**
- Expert : APPROVED_WITH_RESERVATIONS. A1 (réserve) : mode de ballon tracé mais pas affiché, ticket de suivi à créer. A2 (réserve) : touches 22,7, corners 0,84 et temps effectif 86,6 % hors fourchettes, transfert aux tickets 28 et 22 sans réglage artificiel. A3 à A6 facultatifs : ballon dévié entre les poteaux compté comme sortie ; placement au corner du bloc ; preneur posé au point sans remise à zéro de sa vitesse ; équipe par défaut dans `award`.
- QC : REFUSÉ. Mêmes trois fourchettes et affichage non livré ; requalification des critères non décidée par le propriétaire ; `docs/INDICATEURS_V2.md` hors du diff revu.
- Clôture : non validée, en attente de la décision du propriétaire sur A1 et A2.
- Décision du propriétaire (03/11/2026), sur la question « acceptes-tu A1 et A2 telles que l'expert les propose ? » : « Oui j'accepte ». A1 : l'affichage passe au ticket de suivi `.scratch/v2-correctifs-ecran/issues/02-affichage-mode-ballon.md`. A2 : les fourchettes des touches et des corners passent au ticket 28, celle du temps de jeu effectif au ticket 22 ; ici, ces trois valeurs restent des indicateurs mesurés, sans réglage artificiel. A3 à A6 : facultatifs, non traités.

**Passage 2 (03/11/2026), même code (empreinte bdd1fe75…), suivi documentaire ajouté au diff revu**
- QC : VALIDÉ (décision du propriétaire consignée, critères transférés aux tickets 28 et 22, ticket de suivi d'affichage créé, indicateurs définis dans `docs/INDICATEURS_V2.md`).
- Expert : rapport du passage 1 inchangé (APPROVED_WITH_RESERVATIONS), réserves A1 et A2 acceptées par le propriétaire (« Oui j'accepte »).
- Clôture : VALIDÉ.
