# 07e: Se réorienter avant une passe, un tir ou une conduite

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** exécution.

**Constat vérifié :** une passe ou un tir part immédiatement dans n'importe quelle direction à la décision (`match._step_ball`, branches tir et passe).

**What to build:** Une passe, un tir ou une conduite dans une direction éloignée du cap demande une rotation préalable (07a) : l'action part après ce délai ; la valeur de l'option (décision) tient compte de ce délai pour la pression subie pendant la rotation.

**Périmètre revu le 13/11/2026 (propriétaire)** : la conduite passe au 07b (déplacement selon l'orientation) ; la **talonnade** entre dans ce ticket (« inclus-le dans ce ticket-là ») : passe dans le dos sans se retourner, à fréquence réaliste, surtout chez les joueurs techniques.

**Attributs :** Agility (délai, déjà lu au 07f) ; talonnade : Technique (précision), Flair (y penser)

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 07g, `v2-collectif/31`, 09i (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le délai s'ajoute au temps de décision existant, sans le remplacer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe dans le dos du porteur : partie après le délai de rotation ; dans l'axe du corps : immédiate
- **Statistiques (séries de matchs) :** 50 matchs : passes par minute et tirs avant / après

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (cônes 90° / 60° : « Ce que tu me dis est cohérent et je suis d'accord » ; chiffres réels non trouvés ; talonnade : borne StatsBomb, constantes par délégation, voir Comments)
- [x] Délai de rotation appliqué et tracé (`DecisionRecord.rotation_s`, journal : perte « rotation », passe « talonnade »)
- [x] Décision et exécution utilisent le même délai (test : `test_execution_draws_the_loss_with_the_decision_delay`, `test_decision_carries_the_delay_of_each_pass`)
- [x] Talonnade : seulement vers un coéquipier dans le dos à 10 m au plus, sans rotation, précision selon Technique, tentative selon Flair (tests de scène) ; fréquence dans la cible de 1 à 4 par match sur 50 matchs (2,66 au passage 2 ; 3,28 au passage 1) et réussite proche du repère StatsBomb (reçue 90,6 % au passage 2, 81,9 % au passage 1, contre 83,1 %)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : 5 h 05 contre 4 h 55 (estimation revue), + 3 % ; contre 2 h d'origine, + 154 %, expliqué par la talonnade ajoutée par le propriétaire et les corrections du passage 1 (voir Durée)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07e-det1`, `07e-det2`, identiques hors temps de calcul, passage 2)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 819 passés, 0 ignoré, 14 désélectionnés = 2 805 + 14 ; `07e-suite.txt`)

## Comments

**13/11/2026, lancement.** « Ok 07e ». Estimation annoncée : 2 h, confiance moyenne.

**13/11/2026, analyse et périmètre.** Une passe ou un tir partait au tick de la décision, quel que soit le cap. Proposition au propriétaire : délai = (angle au cap − cône libre) / vitesse de rotation (Agility, 07f) ; cône libre ± 90° pour la passe, ± 60° pour le tir ; risque de perte pendant la rotation par la loi de la conduite (`keep_ball_probability` rapportée à la durée, aucune constante nouvelle), appliqué à la valeur de l'option et tiré à l'exécution avec le même délai ; conduite rattachée au 07b ; chiffres réels non trouvés. Nouvelle estimation annoncée : 2 h 55. Réponse : « Ce que tu me dis est cohérent et je suis d'accord », puis demande d'intégrer la talonnade à fréquence réaliste, chez les joueurs techniques, dans ce ticket (« Ce n'est pas grave s'il dépasse les 2 heures »). Nouvelle estimation annoncée : 4 h 55.

**13/11/2026, talonnade : fréquence réelle.** Opta : aucun qualificatif « talonnade » publié trouvé. StatsBomb (données ouvertes, 80 matchs des cinq grands championnats 2015-16, 16 par championnat ; script `scratchpad`, résumé ici) : la mention « Backheel » n'existe que pour les tirs (7 tirs), pas pour les passes. Passes de jeu « Other » (ni pied, ni tête, ni main : talon, poitrine, genou), borne haute des talonnades : 5,2 par match (0,60 % des passes), réussite 83,1 %, longueur médiane 7,8 m, surtout des attaquants. Cible retenue : 1 à 4 talonnades par match, ordre de grandeur.

**13/11/2026, code.**
- `decision` : `turn_angle_deg`, `rotation_delay_s` (cône libre, Agility), `rotation_keep_probability`, `with_rotation` (valeur si le ballon est gardé pendant la rotation, sinon perte à sa place pondérée par la transition), `backheel_idea_probability` (Flair) ; options de passe (`_pass_option`) et de tir avec leur délai (`Action.rotation_s`) ; variante talonnade (`Action.backheel`, sans délai) vers un coéquipier hors du cône à `BACKHEEL_MAX_M` (10 m) au plus, si le porteur y pense (un tirage DECISION par décision).
- `possession` : `backheel` dans `pass_difficulty` (+ `BACKHEEL_DIFFICULTY` = 20), `pass_accuracy_probability` (Technique à la place de Passing), `pass_success_probability`, `pass_aim`, `pass_velocity` : même loi à l'évaluation et en vol (principe du 18g).
- `match` : geste en attente (`BallState.pending`) jusqu'à la fin de la rotation ; à l'échéance, perte tirée par `dribble_lost` avec le délai de la décision, issue de la conduite perdue (04b, journal « rotation ») ; passe vers la position actuelle du receveur ; oublié si un autre joueur a le ballon ; tireur de coup franc sans rotation. Exécution extraite dans `_execute`, ballon libre dans `_step_loose_ball` (découpage sans changement de comportement). Porteur en rotation : intention « se retourner » (`cerveau`), cap tourné vers son geste. Trace : `DecisionRecord.rotation_s`, `.backheel` ; passe « talonnade » au journal.
- **Défaut du 07a corrigé** (révélé par le premier essai) : le porteur « regardait le ballon », posé à sa position du tick précédent ; en course lente, son cap se tournait donc vers l'arrière (96,6 % des tirs demandaient une rotation sur 12 matchs). Il s'oriente désormais selon sa course et garde son cap à l'arrêt.
- Banc : `scripts/measure_v2.py`, `scripts/v2_indicators.py` (rotation, pertes en se retournant, talonnades ; la calibration de la passe évalue une talonnade comme telle).

**13/11/2026, réglage de la talonnade (délégation).** Premier essai (12 matchs, chance d'y penser 0,30 / 0,15 / 0,01 à Flair 99 / 55 / 11) : 7,9 talonnades par match, au-dessus de la borne StatsBomb ; ramenée à 0,12 / 0,06 / 0,005.

**13/11/2026, mesures du passage 1 (50 matchs, mêmes graines que le 18k ; fichiers déplacés dans `mesures/07e-passage1/`, script `07e-synthese.py`).**
- Rotation : 51,7 % des passes décidées en demandent une (0,115 s en moyenne) ; 17,0 % des tirs (0,050 s) ; 2,84 ballons perdus en se retournant par match.
- Talonnades : 3,28 par match (cible 1 à 4) ; non perdues 87,6 %, reçues par le receveur visé 81,9 % (StatsBomb « Other » : 83,1 %) ; chance évaluée 89,6 %.
- 18k → 07e : passes par match 1 007 → 992 (repère 890 à 940) ; passes réussies 85,0 → 84,2 % ; chez l'adversaire 12,7 → 13,5 % (15 à 20) ; passes par possession 4,54 → 4,33 ; possession d'équipe 26,1 → 25,3 s ; pertes en conduite 64,8 → 68,1 ; tirs par équipe 16,0 → 16,4 ; xG neutre 2,78 → 2,82 ; buts 2,58 → 2,90 (environ un écart-type de la différence ; l'essai de 12 matchs donnait 3,83, bruit). Temps de calcul 71 → 78 s par match (+ 10 %).
- Calibration de la passe : écarts du même ordre qu'au 18k sauf [0,6 ; 0,7[ (− 4,3 → − 5,5 points, 3 206 passes) ; [0,4 ; 0,5[ − 5,9 (− 6,3 avant). Table de passe à remesurer au 07g (critère ajouté par la revue du 12/11/2026). À regarder : la tranche [0,1 ; 0,2[ passe de 213 à 826 passes sur 50 matchs ; hypothèse, non vérifiée : passes décidées avant la rotation dont la ligne s'est fermée pendant celle-ci (le porteur ne réévalue pas).
- Déterminisme : `measure_v2 2` identique sur deux exécutions hors temps de calcul (`07e-det1`, `07e-det2`).
- Tests : 11 ajoutés (`tests/test_v2engine_reorientation.py`) ; `test_v2engine_rayon_attributs.py` (Agility dans `decision`, Technique dans `possession`, Flair dans `decision`). Suite : 2 816 passés, 0 ignoré, 14 désélectionnés (`07e-suite.txt`) ; `CLAUDE.md` mis à jour.

**Durée (passage 1).** Estimée 2 h, revue à 2 h 55 (analyse) puis 4 h 55 (talonnade ajoutée par le propriétaire). Réelle environ 4 h, non chronométrée (analyse 50 min dont les données StatsBomb, développement 1 h 15, tests 40 min, intégration et vérifications 1 h 15 dont le défaut du cap du porteur et le réglage de la talonnade) : − 19 % sur l'estimation revue. Temps machine hors total : 2 essais de 12 matchs (8 min chacun), série de 50 matchs (25 min), déterminisme, suite complète (9 min).

**13/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS (rapport `07e-expert-1.md`, empreinte `c8b0f2b3`). QC : non lancé (corrections décidées avant). Réserves :
- A1 [réserve] : la passe part après la rotation même si sa ligne s'est fermée (tranche [0,1 ; 0,2[ : 213 → 826 passes sur 50 matchs).
- A2 [réserve] : en course rapide, le cap ne se tourne pas vers le geste (desired_facing), rendu en retard sur le délai.
- A3 [réserve] : constantes de la talonnade (10 m, + 20, 0,12 / 0,06 / 0,005) à confirmer par le propriétaire.
- A4 [facultatif] : le porteur regarde la position figée du receveur ; test de talonnade dépendant du flux DECISION non semé.
Recommandation proposée au propriétaire : corriger A1, A2 et A4 maintenant, confirmer A3. Réponse : « OK » (lue comme : corrections maintenant, constantes de la talonnade validées ; interprétation annoncée dans la conversation).

**13/11/2026, corrections du passage 1.**
- A1 : à l'échéance de la rotation, `decision.lane_closed_during_turn` : renonce et redécide si la chance de réussite est passée sous `OPEN_LANE_PROBABILITY` (0,7) en perdant au moins `LANE_CLOSED_DROP` (0,3) depuis la décision ; chance à la décision gardée dans `BallState.pending`. Premier essai sans marge (toute baisse sous 0,7, correctif suggéré par l'expert) : 68,6 passes abandonnées par match sur 50 matchs (`mesures/07e-passage2a/`), baisse médiane des abandonnées 0,13 (diagnostic de 8 matchs) ; d'où la marge de 0,3, nouvelle constante recommandée et validée par délégation : 14,3 abandons par match.
- A2 : `movement.desired_facing(..., turning=True)` : pendant la rotation, la direction du geste prime sur le sens de course (`step(..., turning=...)`).
- A4 : le porteur regarde la position actuelle du receveur ; flux DECISION semé dans le test de la talonnade.
- Banc : passes abandonnées comptées (`measure_v2`).
- Tests : 3 ajoutés (ligne fermée pendant la rotation : la passe ne part pas ; passe déjà risquée à la décision : elle part ; porteur rapide : cap dans le cône au départ).

**13/11/2026, mesures du passage 2 (50 matchs, mêmes graines que le 18k ; `07e-50-lot*`, synthèse `07e-50-synthese.txt`).**
- 18k → 07e : passes par match 1 007 → 977 (repère 890 à 940) ; passes réussies 85,0 → 84,9 % ; chez l'adversaire 12,7 → 12,9 % (15 à 20) ; passes par possession 4,54 → 4,36 ; possession d'équipe 26,1 → 25,9 s ; pertes en conduite 64,8 → 70,1 ; tirs par équipe 16,0 → 17,0 ; xG neutre 2,78 → 2,97 ; buts 2,58 → 3,46 ; temps de calcul 71 → 80 s par match (+ 12 %).
- Rotation : 51,7 % des passes décidées (0,115 s), 18,7 % des tirs (0,053 s) ; 2,52 ballons perdus en se retournant et 14,3 passes abandonnées (ligne fermée) par match.
- Talonnades : 2,66 par match ; non perdues 94,6 %, reçues par le receveur visé 90,6 % (StatsBomb « Other » : 83,1 %).
- Calibration de la passe : tranche [0,1 ; 0,2[ revenue à 219 passes (213 au 18k) ; écarts hors 5 points : [0,3 ; 0,4[ − 13,3 (187 passes ; − 10,3 au 18k), [0,4 ; 0,5[ − 6,8 (− 6,3), [0,6 ; 0,7[ − 5,6 (− 4,3) ; table de passe à remesurer au 07g.
- **Buts : contrôle sur d'autres graines.** La hausse 2,58 → 3,46 (environ 2,7 écarts-types) a été vérifiée sur les graines 50 à 99 (`18e-zones.py`, `mesures/07e-zones-b/` contre `18k-zones-b/`) : 07e 2,64 buts par match contre 2,80 au 18k, xG neutre 2,77 contre 2,76, tirs par équipe 16,96 contre 15,97. Sur 100 matchs : 3,05 contre 2,69 (environ 1,5 écart-type) : pas d'effet établi sur les buts ; seuls les tirs augmentent dans les deux séries (+ 1 par équipe).- Déterminisme : `measure_v2 2` identique sur deux exécutions hors temps de calcul (`07e-det1`, `07e-det2`).
- Suite : 2 819 passés, 0 ignoré, 14 désélectionnés (2 816 + 3 ; `07e-suite.txt`) ; `CLAUDE.md` mis à jour.

**Durée (totale).** Estimée 2 h, revue à 4 h 55 (talonnade). Réelle environ 5 h 05, non chronométrée (analyse 50 min, développement 1 h 35, tests 50 min, intégration et vérifications 1 h 50, dont le réglage du seuil de ligne fermée et le contrôle des buts sur d'autres graines) : + 3 % sur l'estimation revue. Temps machine hors total : 2 essais de 12 matchs, 3 séries de 50 matchs, 50 matchs de contrôle (graines 50 à 99), diagnostic de 8 matchs, déterminisme (2 fois), suite complète (2 fois, 9 min).

**13/11/2026, passage 2.** Expert : APPROVED_WITH_RESERVATIONS (rapport `07e-expert-2.md`, empreinte `de00e343`). QC : VALIDÉ. Clôture : VALIDÉ. Réserves acceptées par le propriétaire (« j'accepte les deux réserves et je valide 0,3 ») :
- A1 [réserve] : constante `LANE_CLOSED_DROP` = 0,3 apparue au réglage, sans validation écrite ; validée par le propriétaire.
- A2 [réserve] : tirs par équipe + 1 (16,0 → 17,0 ; 15,97 → 16,96 sur les graines 50 à 99), au-dessus du repère 8 à 15 ; à surveiller au prochain ticket qui touche au volume de tirs ou à la décision de tirer.
- A3 [facultatif] : réussite de la talonnade 90,6 % contre 83,1 % (repère mêlant plusieurs gestes, loi calibrée à 91,4 %) ; à revoir si un repère propre est trouvé.
- A4 [facultatif] : cas limites (arrondi de la fenêtre d'exécution, drapeau `turning` d'un tick après un tacle, réévaluation sur positions réelles) ; commentaire de `LANE_CLOSED_DROP` à corriger (« environ 16 par match », mesuré 14,3) à la prochaine retouche de `decision.py`.
À surveiller (expert) : tirs et buts sur la prochaine série ; table de passe au 07g ([0,3 ; 0,4[ − 13,3, [0,6 ; 0,7[ − 5,6) ; temps de calcul + 12 %. À l'écran : un porteur lancé qui joue en retrait freine et pivote avant le départ du ballon ; une passe renoncée est suivie d'une nouvelle décision sans à-coup du cap.
