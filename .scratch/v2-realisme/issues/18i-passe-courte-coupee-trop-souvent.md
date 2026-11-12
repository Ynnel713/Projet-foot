# 18i: Passe précise coupée trop souvent, même courte

**Chantier :** `v2-realisme`. **Priorité :** P0 (cohérence de la passe, avant la fin des fondations ; ordre revu le 12/11/2026, spec section 13). **Catégorie :** exécution, défense.

**Origine :** ticket 18h (12/11/2026, 12 matchs, moteur après 18g). Une passe PRÉCISE (tirage de `possession.pass_aim` réussi) n'est reçue par un coéquipier que dans environ 85 % des cas, quelle que soit sa longueur : courte 85,4 %, moyenne 85,3 %, longue 86,0 %. Les échecs viennent des coupes (adversaire qui touche le ballon le premier : table du 18g, plus environ 5 % de coupes imprévues). Réel indicatif (toutes passes, précises ou non) : courte 89,4 %, moyenne 87,1 %, longue 51,7 % (Premier League 2024-25, Total Football Analysis d'après FBref). Une passe courte précise est presque jamais coupée dans le réel.

**Cadrage (12/11/2026, décision du propriétaire) :** recherche d'une cause MÉCANIQUE ; aucune constante réglée pour atteindre un chiffre réel. Si le mécanisme est sain, refermer le ticket et laisser l'écart à `v2-collectif/22a`.

**What to build :** Trouver pourquoi une passe courte précise est coupée aussi souvent qu'une longue (placement et course des défenseurs pendant la passe, `anticipation.pass_readers`, contacts du ballon avec un joueur proche du passeur, choix de passes dans le trafic) et corriger le mécanisme. Remesurer ensuite la table de coupe du 18g et l'indicateur de calibration de la passe.

**Hors de ce ticket :** conséquence de la passe ratée (18h) ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Anticipation, Positioning, Passing (aucun rôle nouveau).

**Blocked by :** 18h.

**Bloque :** `v2-collectif/22a`.

**Status :** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 1 h |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible (cause à trouver). À examiner pour découpage après le diagnostic. Temps machine, hors total : diagnostics et séries de 50 matchs, suite complète.

## Acceptance criteria

- [x] Cause des coupes de passes courtes précises identifiée et chiffrée (diagnostic) : près de la moitié des coupes (71 sur 150, 4 matchs) ont lieu au-delà du point visé ; le receveur passe à moins de 1 m du ballon (0,6 m en moyenne) sans le toucher, sa portée de contact étant le corps seul (0,41 m), et un adversaire derrière le récupère (`.scratch/v2-realisme/mesures/18i-prototypes.txt`)
- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : règle B et `LEG_REACH_M` = 1,0 m (valeur réelle non trouvée, même portée que le contre du 05c) validées le 12/11/2026 (« ok pour B et 1,0 m ») ; tables remesurées validées le 12/11/2026 (« je valide »)
- [x] Réussite par longueur (courte, moyenne, longue) mesurée avant/après sur 50 matchs, comparée au réel : 86,1 / 79,5 / 68,3 % → 88,7 / 84,0 / 73,2 % (réel indicatif 89,4 / 87,1 / 51,7 %) (`18i-tables-50.txt`)
- [x] Table de coupe du 18g remesurée ; indicateur de calibration de la passe sous 5 points par tranche : toutes les tranches de − 1,5 à + 4,9 points, toutes passes − 1,0 (+ 2,2 avant) (`18i-bench-synthese.txt`)
- [x] Suite complète comparée à l'attendu de `CLAUDE.md` : 2 771 passés, 14 désélectionnés (2 759 au 18h + 9 au 07a + 3 ici), 7 min 22 (`18i-suite.txt`) ; déterminisme : deux exécutions de `measure_v2 2` identiques sur 820 indicateurs hors temps de calcul (`18i-determinisme.txt`)

## Comments

**12/11/2026, reprise du 18h.** Corriger aussi la docstring de `possession.pass_aim` (« déviée de 10 à 25 % » : 25 à 50 % depuis le 18h, réserve facultative A2 de l'expert).

**12/11/2026, diagnostic (`.scratch/v2-realisme/mesures/18i-diagnostic-cause.py`, 4 matchs, moteur après 07a).** Passes courtes précises : reçues par le visé 80,9 %, coupées 12,0 % (presseur 3,6 %, lecteur 1,8 %, autres 6,6 %). 71 des 150 coupes ont lieu au-delà du point visé : le receveur était à moins de 1 m du ballon dans 70 cas (0,6 m en moyenne au relevé de 0,1 s), mais ne le touche qu'avec le corps (`CONTROL_RADIUS_M` = 0,41 m), alors que le contre d'un tir se fait jambe tendue à 1 m (05c). Cause : portée du contact, pas le placement des défenseurs. Prototypes hors moteur (portée 1 m) : receveur seul 81 → 89 % ; receveur et lecteurs 81 → 85 % ; tous 81 → 55 % (le presseur coupe un tiers des passes dès le départ, écarté).

**12/11/2026, décisions du propriétaire.** Règle B : le receveur visé et les lecteurs de la passe (joueurs qui attendent le ballon) l'atteignent à `LEG_REACH_M` = 1,0 m, les autres avec le corps (« ok pour B et 1,0 m »). Estimation révisée et annoncée : 3 h 15 (second relevé de 50 matchs et seconde validation). Tables remesurées sur 50 matchs (50 778 passes, ajustement sur les matchs pairs, contrôle sur les impairs, `18i-tables.py` et `18i-ajustement.py`) et validées (« je valide ») : près du passeur 0,76 / 0,21 / 0,02 (0,75 / 0,14 / 0,01) ; sur le trajet 0,37 / 0,22 / 0,13 / 0,08 / 0,05 / 0,04 (0,31 / 0,16 / 0,07 / 0,04 / 0,02 / 0,01) ; coupe imprévue 0,015 (0,05) ; imprécise non perdue 0,84 / 0,76 (0,78 / 0,64). La méthode retrouve les tables du moteur sur le relevé d'avant (0,72 / 0,14 / 0,02 ; 0,29 / 0,15 / 0,09 / 0,06 / 0,05 / 0,05 ; 0,055 ; 0,77 / 0,60).

**12/11/2026, implémentation et mesures après.**
- `match.LEG_REACH_M` (1,0 m) ; `match._contacts(..., expecting=...)` : rayon `LEG_REACH_M` pour les joueurs attendus (receveur visé, `ball.readers`), `radius` pour les autres ; tables de `possession.py` remplacées ; docstring de `pass_aim` corrigée (25 à 50 %, réserve A2 du 18h).
- Réussite par longueur, 50 matchs (toutes passes, réussie = premier contact par un coéquipier, remises en jeu exclues) : courte 86,1 → 88,7 %, moyenne 79,5 → 84,0 %, longue 68,3 → 73,2 % (réel indicatif 89,4 / 87,1 / 51,7 %) ; passe courte précise reçue par le visé 85,6 → 88,4 %.
- Calibration de la passe, 50 matchs (`scripts.bench_series`) : écart évaluée / non perdue de − 1,5 à + 4,9 points sur toutes les tranches (critère 5), − 1,0 point sur toutes les passes (+ 2,2 avant).
- Effets (50 matchs appariés, `18i-bench-synthese.txt`) : passes par match 933 → 1 006 (repère 890 à 940, désormais dépassé) ; réussies 79,7 → 84,8 % ; chez l'adversaire 16,6 → 12,8 % (repère 15 à 20 %, désormais en dessous) ; passes par possession 3,8 → 4,7 ; possession d'équipe 23,8 → 27,1 s (repère 11 à 16, plus loin) ; buts 2,08 → 2,48 ; tirs par équipe 16,5 → 17,4 ; corners 6,5 → 8,5. Volume de passes et durée des possessions renvoyés au `v2-collectif/22a` (cadrage du propriétaire : aucune constante réglée pour un chiffre).
- Tests : 3 ajoutés (`tests/test_v2engine_portee.py` : portée du joueur attendu, corps pour tous, scène de passe rapide qui frôle le receveur, discriminante : elle échoue avec `LEG_REACH_M` ramené à 0,41 m) ; 2 tests de constantes mis à jour (`test_v2engine_difficulte.py`) ; scène de fatigue (`test_v2_tranches.py`) : B écarté de 20 à 24 m (la passe mieux évaluée était jouée avant les 2 s de conduite mesurées).

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS (`18i-expert-1.md`, hors dépôt ; un premier lancement interrompu par une limite d'usage de l'API, sans rapport, relancé). QC : VALIDÉ. Clôture : VALIDÉ. Réserves acceptées par le propriétaire (« oui ok ») :
- A1 [réserve] : indicateurs collectifs dégradés (passes par match 1 006, chez l'adversaire 12,8 %, possession d'équipe 27,1 s, passe longue 73,2 % contre 51,7 % réel) ; reportés au ticket `v2-collectif/22a` (section « Repris de la réserve A1 du ticket v2-realisme/18i »).
- A2 [réserve] : le contrôle jambe tendue réussit aussi souvent qu'un contrôle du corps ; reporté au `22a` (levier à proposer).
- A3 [facultatif] : commentaire de position périmé dans `tests/test_v2_tranches.py` (« à (45 ; 20) »), antérieur au ticket ; non corrigé (la correction rouvrirait la revue).
- À surveiller : tranche [0,4 ; 0,5[ de la calibration à 4,9 points ; part des coupes par les lecteurs après tout réglage de l'Anticipation.

**Durée.** Estimée 2 h 30, révisée et annoncée à 3 h 15. Réelle environ 3 h 30, non chronométrée (analyse et diagnostic 1 h 30, développement 30 min, tests 45 min, intégration et vérifications 45 min) : + 40 % sur l'estimation d'origine, + 8 % sur la révision. Causes : trois prototypes de portée mesurés avant la proposition ; second relevé de 50 matchs pour les tables et leur validation ; test de scène rendu discriminant (première version non discriminante). Temps machine hors total : diagnostics de 4 matchs (4 séries), relevé de 50 matchs avant et après, banc de 50 matchs avant et après, déterminisme, suite complète (7 min 22).

