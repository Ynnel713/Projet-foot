# 18j: Portée du défenseur qui lit la passe

**Chantier :** `v2-realisme`. **Catégorie :** défense, exécution.

**Origine :** réserve A3 de l'expert sur le ticket 18i (12/11/2026), acceptée par le propriétaire (« ok A1 A2 A3, crée le 18j »). Depuis le 18i, le receveur visé d'une passe touche le ballon à 1,0 m (`match.RECEIVER_REACH_M`, jambe tendue) ; tout autre joueur à 0,41 m (`match.CONTROL_RADIUS_M`), y compris le défenseur qui a lu la passe (`anticipation.pass_readers`, `ball.readers`) et court la couper. Sur 50 matchs après le 18i : passes chez l'adversaire 11,6 % (repère 15 à 20 %). Le défenseur qui anticipe se jette lui aussi sur le ballon.

**What to build :** Donner une portée propre au seul défenseur qui a lu la passe, entre 0,41 m et 1,0 m, éventuellement après un délai de réaction comme le contre d'un tir (`shooting.BLOCK_REACTION_S`). Un défenseur qui n'a pas lu la passe garde 0,41 m. Remesurer la table de coupe du 18g et l'indicateur de calibration de la passe, puisque la coupe change en jeu.

**Hors de ce ticket :** défenseurs sans rôle qui traitent une passe adverse en vol comme un ballon libre (`cerveau.interpret`, `BALLON_LIBRE`) ; presseur qui vise le point de rencontre du receveur ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Anticipation (déjà : qui lit la passe), aucun rôle nouveau (règle anti double comptage de `docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by :** 18i.

**Bloque :** `v2-collectif/22a`.

**Status :** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications (table du 18g remesurée) | 45 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne (mécanisme local, comme le 18i ; la remesure de la table peut demander un tour de plus). Hypothèses : `_ball_contacts` du 18i étendu aux lecteurs ; diagnostic du 18i réutilisable (`.scratch/v2-realisme/mesures/18i-diag-script.py`). Temps machine, hors total : séries de 50 matchs (environ 25 min chacune), suite complète (8 min).

## Acceptance criteria

- [x] Portée du lecteur (et délai éventuel) proposée avec chiffres réels sourcés ou « non trouvé », validée par le propriétaire avant le code : 1,0 m (`match.READER_REACH_M` = `RECEIVER_REACH_M`), sans délai ; réel non trouvé ; validée par délégation (« Je valide automatiquement toutes tes recommandations », 12/11/2026)
- [x] Scène : un lecteur à 0,8 m de la trajectoire touche le ballon, un non-lecteur à 0,8 m ne le touche pas ; le receveur garde 1,0 m (`tests/test_v2engine_portee_lecteur.py`, 7 tests)
- [x] Passes chez l'adversaire et réussie par longueur mesurées avant/après sur 50 matchs : chez l'adversaire 11,6 → 12,5 % (repère 15 à 20 %, encore en dessous) ; réussie courte / moyenne / longue 92,0 / 85,3 / 76,6 → 90,6 / 84,6 / 75,0 % (réel 89,4 / 87,1 / 51,7)
- [~] Table de coupe du 18g remesurée ; indicateur de calibration de la passe sous 5 points par tranche d'au moins 100 passes : tenu partout sauf [0,3 ; 0,4[ (150 passes sur 50 matchs, 0,3 % des passes) à − 7,0 points ; **dérogation du propriétaire par délégation** (« Je valide automatiquement toutes tes recommandations et les conseils d'experts », 12/11/2026) : écart accepté sur recommandation de l'expert (réserve A1, passage 1), à reprendre au `v2-collectif/22a`
- [x] Suite complète comparée à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**12/11/2026, lancement.** Estimation annoncée : 2 h 15, confiance moyenne. Le propriétaire délègue la validation des constantes, des recommandations de l'expert et des commits (« enchaine les les uns après les autres. Je valide automatiquement toutes tes recommandations et les conseils d'experts ainsi que les commits si les conditions le permettent donc ne me sollicite pas »).

**12/11/2026, essai hors moteur (12 matchs, graines d'audit 20260923 + 0 à 11, moteur du 18i ; enveloppe `.scratch/v2-realisme/mesures/18j-variante.py`, sorties `18j-var-*`).**

| Portée du lecteur | Passes/match | Chez l'adversaire | Receveur visé | Possession d'équipe | Buts |
|---|---|---|---|---|---|
| 0,41 m (18i) | 1 032 | 11,7 % | 84,2 % | 28,2 s | 1,83 |
| 0,7 m | 1 061 | 13,3 % | 82,6 % | 25,6 s | 2,33 |
| 1,0 m | 1 086 | 14,9 % | 81,1 % | 23,8 s | 1,92 |

Recommandation retenue (validée par délégation) : **1,0 m**, même portée que le receveur (jambe tendue, `shooting.BLOCK_WIDTH_M`), **sans délai** : la lecture (`anticipation.pass_readers`) exige déjà que le défenseur atteigne la trajectoire avant le ballon, son temps de réaction y est inclus. Donnée réelle : non trouvée. Codé : `match.READER_REACH_M`, `match._ball_contacts` (les lecteurs de `ball.readers` touchent à cette portée ; le receveur garde la sienne ; les autres 0,41 m).

**12/11/2026, table remesurée (diagnostic `18i-diag-script.py`, 50 matchs, sortie `18j-diag/` ; ajustement `18j-ajustement.py`, sortie `18j-ajustement.txt`, ajustement lots 0 et 2, contrôle lots 1 et 3).** Avec la portée seule, la table du 18i surévalue la chance de 2,4 à 12 points selon la tranche (+ 3,2 au total). Ajustée : près du passeur 0,75 / 0,14 / 0,01 → **0,82 / 0,21 / 0,02** ; trajet 0,31 / 0,16 / 0,07 / 0,04 / 0,02 / 0,01 → **0,43 / 0,25 / 0,12 / 0,07 / 0,03 / 0,02** ; coupe imprévue mesurée 0,014, **0,01 gardée** ; passe imprécise non perdue **0,85 / 0,69** (0,68 avant). Contrôle hors ligne : + 0,1 point au total, sous 4 points sur les tranches d'au moins 300 passes. Valeurs validées par délégation. Test mis à jour : `tests/test_v2engine_difficulte.py` (3 assertions et docstrings, nouvelles valeurs).

**12/11/2026, mesures après (section 33 de `docs/INDICATEURS_V2.md` ; `.scratch/v2-realisme/mesures/18j-*`).**
- 50 matchs, mêmes graines que le 18i (`18j-50-lot*`, synthèse `18j-50-synthese.txt`, `18j-synthese.py`) : passes par match 1 043 → 998 (repère 890 à 940) ; passes réussies 86,2 → 85,2 % ; chez l'adversaire 11,6 → 12,5 % (15 à 20) ; passes par possession 5,11 → 4,63 (3 à 5) ; possession d'équipe 28,3 → 26,9 s (11 à 16) ; buts 2,64 → 2,62 ; pertes en conduite 54,6 → 61,5 ; face-à-face 9,0 → 10,3 par match.
- Calibration de la passe : − 0,3 à − 4,6 points sur les tranches de 0,4 à 1 (avant : − 1,1 à − 6,9) ; [0,3 ; 0,4[ − 7,0 (3 passes par match) ; [0 ; 0,1[ − 7,5 (1,8 par match, sous le seuil de 100 passes).
- Réussite par longueur (diagnostic de 50 matchs sur le moteur final, `18j-diag-final/`, `18j-longueurs.txt`) : 90,6 / 84,6 / 75,0 % ; précises 92,0 / 92,1 / 90,0 %.
- Scènes A/B (`18j-ab.txt`) : aucun effet inversé ni annulé (Passing + 0,134 meilleure passe, + 0,215 part de passes choisies ; Composure + 0,020 ; Dribbling − 0,197 ; Vision + 0,182 ; Decisions − 0,190).
- Déterminisme : deux exécutions de `measure_v2 2` identiques hors temps de calcul (`18j-det1`, `18j-det2`).
- Écart restant : passes chez l'adversaire sous le repère après le choix plus prudent du passeur (la table remesurée lui fait éviter les passes que le lecteur coupe désormais) ; possession d'équipe et passes par match toujours au-dessus : `v2-collectif/22a`. Passe longue toujours trop réussie (75,0 contre 51,7 %) : `22a`.
- Tests : 7 ajoutés (`tests/test_v2engine_portee_lecteur.py`) ; `tests/test_v2engine_difficulte.py` mis à jour (nouvelles valeurs de la table) ; une scène déplacée dont la prémisse ne tenait plus (`tests/test_v2engine_combinaisons.py`, relance de l'appel : Coupe et Coupe2 abaissés de 0,5 m, ils fermaient aussi l'espace relancé avec la table remesurée ; la ligne R -> P reste fermée). Suite : 2 775 passés, 0 ignoré, 14 désélectionnés (2 768 + 7 ; `.scratch/v2-realisme/mesures/18j-suite.txt`) ; `CLAUDE.md` mis à jour.

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : REFUSÉ (critère 4 non tenu sur [0,3 ; 0,4[ sans dérogation écrite). Réserves de l'expert :
- A1 [réserve] : tranche [0,3 ; 0,4[ à − 7,0 points (150 passes), confirmée − 7,1 hors ligne (248 passes), écart systématique ; 0,3 % des passes, − 20,5 au 18i. Correctif suggéré au 22a : une case « deux adversaires ou plus près de la ligne » dans la table.
- A2 [réserve] : évaluation légèrement pessimiste en jeu (biais pondéré environ − 1,4 point), passeur un peu trop prudent (pertes en conduite + 13 %, solutions ouvertes 4,71 → 3,96) ; remesurer la table au 22a une fois le choix du passeur stabilisé, par itération jusqu'au point fixe.
- A3 [facultatif] : le lecteur garde 1,0 m pendant tout le vol (portée liée au nom, pas à la position) ; effet négligeable.

**12/11/2026, décision par délégation du propriétaire** (« enchaine les les uns après les autres. Je valide automatiquement toutes tes recommandations et les conseils d'experts ainsi que les commits si les conditions le permettent donc ne me sollicite pas ») : A1 et A2 acceptées, inscrites au `v2-collectif/22a` ; dérogation au critère 4 écrite ci-dessus. A3 non retenu (facultatif, effet négligeable).

**12/11/2026, passage 2 (QC seul, code inchangé).** QC : VALIDÉ (dérogation au critère 4 écrite). Clôture : VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserves A1 et A2 acceptées par délégation du propriétaire, QC VALIDÉ). Dossiers bruts du diagnostic (`18j-diag/`, `18j-diag-final/`, environ 240 Mo) non versionnés, comme au 18i ; synthèses gardées.

**Durée.** Estimée 2 h 15. Réelle environ 2 h, non chronométrée (analyse 25 min, développement 20 min, tests 25 min, intégration et vérifications 50 min, dont un refus du QC levé par la dérogation) : − 11 %. Temps machine hors total : essai de 3 portées sur 12 matchs (13 min), 2 diagnostics de 50 matchs (12 min chacun), série de 50 matchs (25 min, relancée une fois faute de `PYTHONPATH`), scènes A/B, déterminisme, 2 suites complètes (7 min).
