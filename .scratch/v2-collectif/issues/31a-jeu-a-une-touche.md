# 31a: Jeu à une touche (remise, passe de première)

**Découpé du ticket 31 le 13/11/2026** (validé par le propriétaire : « Oui vas y »). Détail : `31-premiere-touche.md`, point 1.

**What to build:** Sur une passe qui arrive, le receveur peut jouer sans contrôler (remise, passe à une touche) quand une passe suivante est prête, que la pression est supportable et que sa technique le permet. Decisions choisit entre jouer de première et contrôler ; le plan de passe du ticket 14 donne la suite préparée. Aujourd'hui, toute réception passe par un contrôle puis 1,7 à 2,9 s d'attente (`possession.reception_delay_s`).

**Hors de ce ticket :** contrôle orienté (31b), durée de réception (31c), tir de première (`34a`), difficulté de la passe selon l'arrivée du ballon (`36a` : ballon fort, de côté, de dos).

**Attributs :** First Touch et Technique (réussite du geste), Anticipation (préparer le geste), Decisions (choisir). Rayons fixés dans `docs/CARTE_ATTRIBUTS_V2.md` avant le code, sans double comptage (`v2-collectif/18`).

**Blocked by:** 14 (livré) ; `v2-realisme/07a`, `07c`, `07e`, `08c` (livrés) : démarrable.

**Bloque :** 31b, `34a`, `36a`.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **2 h 45** |

Confiance : moyenne. Hypothèses : la décision existante (`decision.decide`) évalue les options au moment de la réception ; l'exécution réutilise la passe existante avec une pénalité de geste ; pas de nouvelle géométrie d'arrivée (36a).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs avant/après (environ 25 min).

## Acceptance criteria

- [x] Constantes et chiffres réels validés par le propriétaire avant le code : idée de jouer de première selon la moyenne de First Touch et Technique, proposée à 8 / 22 / 40 % (11 / 55 / 99), niveau calé sur 6 matchs pour viser 9 % (x 1,75 : 14 / 38,5 / 70 %) ; sous pression x 1,5 au contact (option A) ; précision du geste selon Technique 0,85 / 0,93 / 0,98 (non trouvée) ; part réelle : 7,4 à 9,3 % des passes au pied du jeu courant (calcul sur les données ouvertes StatsBomb, 45 matchs, voir Comments) ; validés le 13/11/2026 (« Ok avec ta recommandation »)
- [x] Scène contrôlée : passe suivante prête, pression faible : passes de première à 8,6 % (notes 11), 22,5 % (55), 40,6 % (99), jamais 0 ni 100 % (300 graines, `.scratch/v2-collectif/mesures/31a-scene.txt` ; fourchettes assertées par `tests/test_v2engine_one_touch.py::test_skilled_receiver_plays_first_time_more_often_never_always`)
- [x] Scène contrôlée, pression : **critère réécrit** sur décision du propriétaire (option A, 13/11/2026) : la pression **augmente** les jeux de première (22,5 → 30,2 % à 55, adversaire à 2 m, `31a-scene.txt` ; asserté par `test_pressure_raises_first_time_play`) et baisse leur précision (`pass_difficulty`, déjà)
- [x] En match (50 matchs, graines du banc) : part de passes à une touche, temps par possession de joueur, une-deux et troisième homme, passes par match et réussite, comparés avant et après (`31a-50-synthese.txt`)
- [x] Rayon des attributs conforme à la carte, sans double comptage : First Touch et Technique lus dans `decision` (idée, cumul A16), Technique dans `possession` (précision) ; `tests/test_v2engine_rayon_attributs.py` à jour
- [x] Indicateur ajouté au banc et défini dans `docs/INDICATEURS_V2.md` (section 2, n° 24)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée (`31a-det1`, `31a-det2` identiques hors temps de calcul) ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**13/11/2026, lancement.** Estimation annoncée : 2 h 45, confiance moyenne (découpage du 31 validé par le propriétaire).

**13/11/2026, chiffre réel.** Les données ouvertes StatsBomb ne remplissent pas `pass.first_time` (aucune passe marquée sur 45 matchs). Méthode de StatsBomb (« Identifying Fast Passers Using Data ») : passe au pied du jeu courant partie au moment de la réception du même joueur (écart de 0,0 s, sans autre geste entre les deux). Ligue 1 2015-16 : 9,1 % ; Premier League 2015-16 : 9,3 % ; Bundesliga 2023-24 (saison de Leverkusen) : 7,4 % (15 matchs chacune, échantillon régulier par identifiant). Script et sortie : `.scratch/v2-collectif/mesures/31a-statsbomb-premiere.py` et `.txt` (données téléchargées hors dépôt, `statsbomb/open-data`) ; limites : échantillon, et définition (écart nul) qui ignore une remise en deux temps très rapide.

**13/11/2026, constantes (propriétaire).** Proposition : idée selon First Touch et Technique (8 / 22 / 40 %), niveau calé sur 6 matchs pour viser 9 % ; précision 0,85 / 0,93 / 0,98 selon Technique ; Anticipation hors de ce ticket. Désaccord exprimé sur le critère « la pression réduit les jeux de première » (réel : sous pression, on joue plus souvent en une touche, la précision baisse) ; option A recommandée (x 1,5 au contact). Réponse : « Ok avec ta recommandation ».

**13/11/2026, implémentation.** `decision.one_touch_idea_probability`, `thinks_one_touch` (flux décision) ; `possession.one_touch_precision`, paramètre `one_touch` de `pass_accuracy_probability`, `pass_success_probability`, `pass_aim`, `pass_velocity` (même calcul à la décision et à l'exécution) ; `evaluate_options(..., one_touch=)` juge de première les seules passes sans rotation (talonnade comprise) ; `Action.one_touch`. `match` : à la réception réussie d'une passe au sol qui lui est destinée (joueur de champ), s'il y pense, `BallState.one_touch` (nom, instant limite) et décision au tick suivant ; passe sans rotation choisie : elle part de première ; sinon il contrôle comme avant (attente `reception_delay_s` depuis cet instant, plan de passe conservé). Journal des décisions extrait dans `match._record_decision` (sans changement), `DecisionRecord.one_touch`. Banc : `passes de première` (part, par match, non perdues, chance évaluée) ; calibration des passes (18g) avec la précision de première. Gardien exclu (rare, hors de ce ticket).

**13/11/2026, calibration (6 matchs, graines 0 à 5).** Premier essai (8 / 22 / 40 %) : 5,2 % des passes décidées ; x 1,75 (14 / 38,5 / 70 %) : 9,1 %. Passes de première non perdues 88,9 % pour 89,7 % évalués.

**13/11/2026, mesures (50 matchs, graines du 08f, avant = 07b, `31a-50-synthese.txt`).** Passes de première 0 → 9,4 % des passes décidées (102 par match), non perdues 89,7 % pour 89,8 % évalués ; temps par possession de joueur 2,60 → 2,42 s ; troisième homme 29,5 → 37,5 par équipe et par match (+ 27 %) ; une-deux 1,59 → 1,58 ; passes par match 1 054 → 1 115 (repère 890 à 940, déjà dépassé avant ; à la calibration 22a) ; passes par minute de jeu effectif 14,1 → 14,9 (15 à 17 visés au ticket 31) ; réussite 79,8 → 80,3 % ; pertes de balle 279 → 285 ; tirs par équipe 17,3 → 17,7 ; buts 3,12 → 3,02 ; xG neutre 3,21 → 3,38 ; temps de calcul 111 → 118 s par match. Déterminisme : `31a-det1` et `31a-det2` identiques hors temps de calcul.

**13/11/2026, tests.** 7 ajoutés (`tests/test_v2engine_one_touch.py`) ; adaptés : `test_v2engine_rayon_attributs.py` (rayon et cumul A16), `test_v2engine_transition.py` (substitut de `choose_action` qui accepte les mots-clés), `test_v2engine_scan.py` (match de 3 → 10 minutes : sur 3 minutes l'écart d'âge de la mémoire avec et sans scans tenait au hasard, 1,288 contre 1,287 s après ce ticket ; sur 10 minutes 1,42 contre 1,51 s, propriété nette).

**13/11/2026, suite.** 2 908 passés, 0 ignoré, 14 désélectionnés (2 901 + 7 ; `.scratch/v2-collectif/mesures/31a-suite.txt`) ; `CLAUDE.md` mis à jour. V1 inchangée (aucun fichier V1 touché).

**13/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. A1 (réserve) : passes par match 1 054 → 1 115, au-delà du repère 890 à 940 (102 passes de première par match contre 64 à 73 au réel : la part est juste, le volume de passes déjà trop haut) ; renvoi à la calibration 22a. A2 (réserve) : une-deux inchangés (1,59 → 1,58) malgré plus de retours au passeur (2,4 → 3,4 %) : le passeur ne repart pas en course après sa passe ; à suivre au ticket qui la traitera. Facultatifs : A3, fourchettes de niveau dans le test de la scène ; A4, idée à 100 % au contact au-delà d'environ 93 de moyenne (borne à 0,95 possible) ; A5, dénominateur de l'indicateur avec les coups francs (environ 1 %). QC : BLOQUÉ : critères chiffrés de la scène (9 / 23 / 41 %, 23 → 30 %) cochés sans pièce ni assertion. Correction : sortie de la scène enregistrée (`31a-scene.txt`, 300 graines) et fourchettes assertées dans les deux tests de la scène (A3 de l'expert) ; critères réécrits aux valeurs mesurées (8,6 / 22,5 / 40,6 %, 22,5 → 30,2 %). Aucune ligne du moteur modifiée ; nombre de tests inchangé (7).

**13/11/2026, passage 2.** Expert : APPROVED_WITH_RESERVATIONS (A3 du passage 1 corrigée, moteur inchangé depuis le passage 1). Réserves A1 (volume de passes, à la 22a) et A2 (une-deux inchangés, le passeur ne repart pas en course après sa passe) acceptées par le propriétaire (« ok avec les reco expert », 13/11/2026) ; facultatifs non faits sur recommandation : borne de l'idée à 0,95 au contact, coups francs exclus du dénominateur de l'indicateur (environ 1 %), classement de la remise au passeur dans la scène de test. QC : VALIDÉ (blocage du premier examen levé). Clôture : VALIDÉ. Suivi : A1 et A2 notés au ticket 22a ; aucun ticket ne traite encore la course du passeur après sa passe (à créer si le propriétaire le souhaite).

**À vérifier à l'écran (propriétaire).** Remise de première : arrêt d'un tick (0,1 s) puis départ du pied du receveur, sans ballon « téléporté » ; les remises vont surtout dans l'axe du corps.

**Durée.** Estimée 2 h 45 (165 min). Réelle environ 1 h 25, non chronométrée (analyse 25 min dont le calcul StatsBomb, développement 30 min, tests 15 min, intégration et vérifications 15 min, plus la correction du blocage QC), relevée à l'horloge de la session (environ 17:50 → 19:10) moins les attentes machine (calibration, série, suite) et les réponses du propriétaire : − 48 %. Cause : le motif de la talonnade (07e), déjà passé par la décision, la précision et l'exécution, a servi de gabarit au paramètre `one_touch` ; la documentation et les tests ont été écrits pendant les séries. Temps machine hors total : 2 x 6 matchs de calibration, 50 matchs (environ 30 min), déterminisme 2 x 2 matchs, suite complète (10 min).
