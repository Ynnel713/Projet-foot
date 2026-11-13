# 08e: Le défenseur ne voit pas toujours l'appel dans son dos

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'appel dans le dos réussit quand le défenseur regarde le ballon). **Catégorie :** perception.

**Constat vérifié :** le marquage et la ligne défensive lisent les positions réelles des attaquants (`defense.update`, `bloc.update`).

**What to build:** Le marqueur et la ligne défensive utilisent les positions perçues des attaquants (08b) : un appel dans le dos d'un défenseur qui regarde le ballon est vu en retard. Positioning et Marking gardent leur rayon (placement, distance) ; aucun nouvel attribut.

**Attributs :** aucun

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes); 08c (Scan visuel avant la réception).

**Bloque :** 08f, 09i (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h**, réestimé à **3 h 50** le 13/11/2026 (coût du scan du 08c et mesures des réserves du 08d ajoutés ; un seul ticket, décision du propriétaire) |

Confiance : moyenne. Hypothèses : seuls marquage et ligne lisent la perception, pas l'attribution des rôles.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant qui part dans le dos d'un défenseur tourné vers le ballon : marquage réagit avec retard
- **Statistiques (séries de matchs) :** 50 matchs : hors-jeu et passes en profondeur réussies avant / après

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (aucune constante nouvelle ; choix de conception validés par « un seul ticket » le 13/11/2026)
- [x] Retard de réaction mesuré en scène (`tests/test_v2engine_perceived_defence.py` : marqueur dont l'attaquant a couru dans le dos, il vise plus de 8 m en retard, à la vitesse d'alors ; ligne qui reste haute de plus de 5 m)
- [x] Hors-jeu par match rapporté (repère 3,2-3,5 indicatif) : 0,86 → 0,84 par match sur 50 matchs ; très en dessous du repère, écart antérieur au ticket (voir Comments)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`08e-det1`, `08e-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 861 passés, 0 ignoré, 14 désélectionnés = 2 852 + 9 ; `08e-suite.txt`)

## Comments

**13/11/2026, lancement.** « lance le 08e ». Découpage proposé (cœur, puis coût du scan à part), refusé par le propriétaire : « un seul ticket ». Estimation annoncée : 3 h 50, confiance moyenne.

**13/11/2026, choix de conception (validés avec « un seul ticket »).** Marquage : chaque marqueur situe l'attaquant avec sa propre mémoire (08b) ; le marqueur choisi est le plus proche de la position qu'il perçoit, le point visé est le côté but de cette position perçue, à la vitesse d'alors ; le plan de l'équipe (qui est dangereux, qui est receveur proche pendant le pressing d'équipe) reste sur les vraies positions ; le ballon et son porteur restent connus de tous. Ligne : le défenseur le plus bas (celui qui la cale) perçoit l'attaquant le plus avancé et sa place ; une course dans son dos qu'il n'a pas vue ne fait pas redescendre la ligne. Coût du scan (réserve A1 du 08c, reportée ici depuis le 08d) : un joueur de l'équipe qui n'a pas le ballon, ballon tenu, garde son intention précédente le temps du scan (0,3 s) ; l'équipe qui a le ballon n'y perd rien ; ballon libre : pas de gel. Aucune constante nouvelle. Fréquence des scans non recalée, mémoire non plafonnée (décision du propriétaire sur la proposition) : mesurés et rapportés.

**13/11/2026, code.** `defense.DefensiveRoles.update(..., memory)` : `_closest_to` et `_seen_at` pour les marqueurs et les suiveurs du pressing d'équipe ; `bloc.Bloc.update(..., memory)` : le défenseur le plus bas observe ; `cerveau.think(..., scanning)` : intention précédente gardée pendant un scan en défense ; `PerceptionMemory.perceived_velocity` ; `match.simulate_match` : la mémoire est fournie au bloc et à la défense, les joueurs qui scannent sont transmis à leur tick ; `trace.ScanEvent.defending`. Sans mémoire, comportement inchangé (comme au 08d). Les appels de `defense.update` et `bloc.update` lisent la mémoire arrêtée à la fin du tick précédent (retard de 0,1 s, accepté).

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/08e-*`, 50 matchs, mêmes graines ; avant = lots `08d-50`).**
- Déterminisme : `08e-det1` et `08e-det2` identiques hors temps de calcul.
- Effet d'ensemble faible : passes réussies 79,9 % → 80,1 % ; passes chez l'adversaire 18,2 % → 18,0 % ; possession d'équipe 20,8 s → 20,6 s ; pertes de balle 274 → 276 par match ; buts 3,04 → 3,20 ; tirs cadrés 27,8 % → 29,5 % ; corners 6,6 → 5,8 par match.
- Hors-jeu : 0,86 → 0,84 par match, très en dessous du repère indicatif de 3,2 à 3,5 ; l'écart date d'avant le ticket (0,86 au 08d). Passes en profondeur réussies 44,8 % → 40,2 %. Le critère du ticket « hors-jeu rapporté » est tenu, le repère n'est pas atteint : à regarder au prochain recalage (calibration provisoire `18d`).
- Scans en défense : 23,6 % de tous les scans ; fréquence moyenne avant réception 2,68 scans en 10 s (2,65 au 08c), 18,0 scans par minute et par joueur.
- Réserve A2 du 08d : talonnades 4,74 → 4,26 par match, non perdues 75,5 % → 83,5 % (71,9 % au premier passage : le bruit d'une série de 50 matchs sur ce chiffre est de l'ordre de 10 points) ; fantômes 6,4 % → 6,6 % des décisions ; le 08e ne fait pas baisser le biais d'angle mort du porteur (le coût du scan et la perception des défenseurs ne portent pas sur lui). Plafond de confiance sur la mémoire très vieille : à décider avec les chiffres du ticket 08f.
- Attribution par mécanisme : variantes « sans gel du scan » et « sans perception du marquage et de la ligne » sur les 13 premiers matchs (`08e-sans-gel.*`, `08e-sans-perception.*`) : trop bruitées pour attribuer (buts par match de 2,3 à 3,4 selon la variante, sans lien net avec le mécanisme) ; les effets des deux mécanismes sont donc du même ordre que le bruit d'une série de 13 matchs.
- Calibration de la passe : écarts de la chance évaluée contre la réussite réelle de 4,6 points au plus ; tranche [0,1 ; 0,2[ : 2 476 passes sur 50 matchs.
- Temps de calcul : 97,0 s par match (91,9 au 08d, séries sous charge, non comparables).
- Tests : 9 ajoutés (`tests/test_v2engine_perceived_defence.py`). Suite : 2 861 passés, 0 ignoré, 14 désélectionnés ; `CLAUDE.md` mis à jour.

**À regarder.** L'effet est petit : le marquage ne vise que les attaquants à 25 m de son but et la ligne ne lit qu'un attaquant ; la plupart du temps l'attaquant est dans le cône du défenseur. Le hors-jeu est très bas (0,8 par match) pour une raison qui n'est pas ce ticket. Le gel du scan touche 23,6 % des scans, soit quelques pour cent du temps de chaque défenseur.

**Durée.** Estimée 3 h 50. Réelle environ 3 h 40, non chronométrée (analyse 35 min, développement 1 h 15, tests 45 min, intégration et vérifications 1 h 05) : − 4 %. Temps machine hors total : suite complète, série de 50 matchs (4 lots, 25 min), deux variantes de 13 matchs, déterminisme (2 x 2 matchs).

**13/11/2026, passage 1 de la revue (expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ) et correction.** L'expert a signalé : A1, effet non démontré en match ; A2, le gel du scan s'applique aussi au gardien (un gardien qui scanne en face-à-face garde son intention précédente 0,3 s) ; facultatifs, docstrings périmées (`scan.py`, `perception_memory.py`) et possible oscillation de la ligne. Réponse du propriétaire : « ok pour les corrections ». Corrigé : `cerveau.think` ne gèle plus le gardien (test `test_a_goalkeeper_who_scans_keeps_following_the_ball`), docstrings de `scan.py` et `perception_memory.py` mises à jour. Séries, déterminisme et suite refaits (les mesures ci-dessus sont celles du second passage ; premier passage conservé dans `mesures/08e-passage1/`). Écart entre les deux passages : sans effet lisible (hors-jeu 0,80 → 0,84 par match, buts 3,08 → 3,20, passes réussies 80,1 % → 80,1 %).

**13/11/2026, passage 2.** Expert : APPROVED_WITH_RESERVATIONS (rapport `08e-expert-2.md`), les corrections demandées au passage 1 (gel du gardien, docstrings) sont vérifiées et levées ; il reste une réserve, acceptée par le propriétaire (« j'accepte a1 ») : **A1**, effet du marquage et de la ligne perçus non démontré en match (hors-jeu 0,80 puis 0,84 sur deux passages du même code, pour 0,86 avant ; passes en profondeur réussies 44,8 % → 40,2 % sur environ 150 passes ; variantes de 13 matchs plus bruitées encore) ; à mesurer sur un échantillon plus grand ou ciblé (appels dans le dos, hors-jeu) au recalage `v2-realisme/18d`, ou dès que le 08f en dépend, et à reporter ici. Facultatif A4 : possible oscillation de la hauteur de ligne quand deux défenseurs sont à égalité de profondeur (aucune preuve ; à surveiller avec la variance de `bloc.lines` d'un tick à l'autre). QC : VALIDÉ (tests non exécutés par lui, preuves du ticket). Clôture : VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserve acceptée, QC VALIDÉ). Niveau de hors-jeu : 0,84 par match contre 3,2 à 3,5 en réel, écart antérieur au ticket, à traiter au recalage 18d.
