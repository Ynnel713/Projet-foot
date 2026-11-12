# 18h: Passe ratée trop bénigne

**Chantier :** `v2-realisme`. **Catégorie :** exécution.

**Origine :** ticket 18g (12/11/2026, 50 matchs, graine d'audit). Une passe imprécise (tirage raté de `possession.pass_aim`) ne dévie que de 10 à 25 % de sa longueur (`_MISS_SHARE`) : le receveur visé la rattrape quand même dans 64 % des cas de 10 à 35 m (77 % sous 10 m), hors coupe. La note de Passing pèse donc peu sur l'issue réelle d'une passe ; depuis le 18g, la chance évaluée le reflète fidèlement (table `_MISS_RECOVERED`), ce qui rend jouables des passes très imprécises.

**What to build :** Revoir la conséquence d'une passe ratée (ampleur et direction de la déviation, dosage) pour que Passing compte dans l'issue comme dans le football réel ; chiffres réels à chercher (part des passes ratées récupérées par le receveur visé). Remesurer ensuite la table `_MISS_RECOVERED` du 18g.

**Hors de ce ticket :** coupe en vol (18g) ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Passing (aucun rôle nouveau).

**Blocked by :** 18g.

**Status :** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (chiffres réels à trouver). Temps machine, hors total : séries de 50 matchs, suite complète.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (déviation 25-50 % et table `_MISS_NOT_LOST` 0,78 / 0,64 validées le 12/11/2026 ; chiffres réels de réussite par longueur sourcés, indicatifs)
- [x] Part des passes imprécises reçues par le receveur visé, avant/après, sur 50 matchs ; table `_MISS_RECOVERED` remesurée : 61,7 % (avant, 12 matchs) → 50,2 % (50 matchs) ; table `_MISS_NOT_LOST` remesurée (0,78 / 0,64), calibration de la passe sous 5 points sur les tranches d'au moins 100 passes sauf [0,3 ; 0,4[ (40 passes, + 5,3)
- [x] Effet de Passing sur l'issue réelle d'une passe mesuré (scènes A/B) : meilleure passe + 0,086 → + 0,142, part de passes choisies + 0,143 → + 0,230 ; aucun effet inversé ni annulé ; issue réelle : réussie 76,9 % (Passing sous 55) contre 84,9 % (70 et plus) avant, 67,5 contre 80,8 % avec la déviation 25-50 % (6 matchs)
- [x] Suite complète comparée à l'attendu de `CLAUDE.md` : 2 759 passés, 14 désélectionnés (2 758 + 1 ajouté ; `.scratch/v2-realisme/mesures/18h-suite.txt`)

## Comments

**12/11/2026, diagnostic (12 matchs, moteur après 18g, 11 085 passes de jeu ; script hors dépôt ; réussie = reçue par un coéquipier au premier contact).** Moteur contre réel (indicatif : Premier League 2024-25, Total Football Analysis d'après les catégories FBref ; Opta, passes de plus de 35 yards : 47,3 %) : courte (moins de 13,7 m) 84,9 % contre 89,4 % ; moyenne (13,7 à 27,4 m) 79,5 % contre 87,1 % ; longue (plus de 27,4 m) 75,8 % contre 51,7 %. Passe imprécise réussie quand même : 79 % (courte), 63 % (moyenne et longue). Passe précise : environ 85 % quelle que soit la longueur (l'échec vient des coupes). Passing : imprécises 44 % sous 55, 14 % à 70 et plus ; réussie 78,0 % contre 84,5 %.

**Essais de déviation (6 matchs chacun, mêmes graines).** 10-25 % (actuel) : 85,0 / 78,8 / 77,0 %, toutes 80,5 %, Passing sous 55 contre 70 et plus 76,9 / 84,9 %. 25-50 % : 81,4 / 74,2 / 68,3 %, toutes 75,9 %, 67,5 / 80,8 %. 35-70 % : 80,5 / 73,5 / 66,3 %, toutes 75,0 %, 69,3 / 80,4 %. La déviation redonne du poids à Passing et rend la passe longue moins gratuite, mais ne retrouve pas le profil réel : les passes courtes et moyennes sont déjà trop basses, parce qu'une passe précise est coupée environ 15 % du temps quelle que soit sa longueur (ticket 18i).

**12/11/2026, décision du propriétaire (« ok option 1 »).** Déviation de la passe ratée portée à 25-50 % de sa longueur (au lieu de 10-25 %) ; table `_MISS_NOT_LOST` du 18g remesurée ensuite et soumise avant d'être codée ; ticket 18i créé (passe courte coupée trop souvent), à traiter avant `v2-collectif/22a`. Réussite globale attendue en baisse d'environ 4,5 points d'ici le 18i. Estimation révisée : 2 h 15.

**12/11/2026, définition et table remesurées (validé par le propriétaire : « ok »).** Avec la déviation 25-50 %, la passe imprécise mesurée « non perdue » au sens du 18g montait à 0,81 (10 à 35 m) : une passe très déviée finit plus souvent en touche ou morte sans contact, comptée non perdue (réserve A3 du 18g). Issues d'une passe imprécise (50 matchs, 44 692 passes de jeu) : reçue 50,2 %, adversaire en premier 29,4 %, sortie ou sifflée avec remise adverse 14,1 %, contrôle raté 3,5 %, autre coéquipier 2,8 %. Définition retenue : perdue si un adversaire touche le ballon le premier OU si le ballon sort ou est sifflé avec remise pour l'adversaire. Valeurs (ajustement lots 0 et 2, contrôle lots 1 et 3) : coupe imprévue 0,05 (0,052 / 0,045) ; passe imprécise non perdue hors coupe 0,78 sous 10 m (0,780 / 0,789), 0,64 au-delà (0,642 / 0,637 de 10 à 35 m ; au-delà de 35 m, 20 passes seulement, même valeur faute de preuve d'un écart). Estimation révisée : 3 h 45 (annoncée).

**12/11/2026, mesures après (section 31 de `docs/INDICATEURS_V2.md`, fichiers `.scratch/v2-realisme/mesures/18h-*`).**
- Calibration de la passe (50 matchs, définition du 18h) : évaluée 0,834, non perdue 0,813 (+ 2,2 points) ; de + 1,1 à + 3,4 points sur les tranches de 0,6 à 1 (88 % des passes).
- Effets (18g → 18h, mêmes graines) : passes par match 985 → 933 (repère 890 à 940 retrouvé ; réserve du 18f) ; passes réussies 81,9 → 79,7 % ; chez l'adversaire 14,9 → 16,6 % ; passes par possession 4,35 → 3,84 ; possession d'équipe 25,6 → 23,8 s (repère 11 à 16, toujours dépassé) ; buts 2,50 → 2,08 ; pertes en conduite 46 → 56 ; une-deux 0,97 → 1,47.
- Réussite par longueur (réussie = reçue par un coéquipier au premier contact) : 84,9 / 79,5 / 75,8 % → 82,9 / 76,3 / 71,2 % (réel indicatif 89,4 / 87,1 / 51,7 %).
- Scènes A/B : Passing + 0,086 → + 0,142 (meilleure passe), + 0,143 → + 0,230 (part de passes choisies) ; aucun effet inversé ni annulé.
- Déterminisme : deux exécutions de `measure_v2 2` identiques hors temps de calcul (`18h-det1`, `18h-det2`).
- Tests : 2 tests de la constante mis à jour (`test_v2engine_difficulte.py`, `test_v2engine_garde_probabiliste.py`), 1 test de la formule (valeur 0,64), 1 test ajouté (sortie avec remise adverse comptée perdue, `test_v2_indicators.py`).
- **Correctif annexe, hors périmètre mais nécessaire** : `test_in_a_match_every_framed_shot_was_judged_by_the_keeper` échouait avec la nouvelle déviation (déroulé des matchs différent). Cause préexistante : un tir tiré depuis la ligne de but même (rebond, `to_line = 0`) n'était pas « cadré » (`to_line > 0`), donc jamais jugé par le gardien, mais entrait quand même. Correction : `to_line >= 0` (`v2engine/match.py`) ; le gardien le juge à l'instant 0.

**Durée.** Estimée 2 h, révisée et annoncée deux fois (2 h 15, 3 h 45). Réelle environ 3 h 15, non chronométrée (analyse 1 h 15, développement 30 min, tests 45 min, intégration 45 min) : + 63 % sur l'estimation d'origine, − 13 % sur la dernière révision. Causes : la déviation seule ne retrouvait pas le profil réel (essais de deux variantes, ticket 18i) ; la définition « non perdue » du 18g comptait la sortie de balle comme non perdue (deuxième relevé de 50 matchs pour la séparer) ; un bug préexistant de tir depuis la ligne de but révélé par un test. Temps machine hors total : diagnostics de 12, 2 x 6 et 2 x 50 matchs, série de 50 matchs avec l'indicateur, scènes A/B, déterminisme, suite complète (9 min).

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : VALIDÉ. Clôture : VALIDÉ. Réserve acceptée par le propriétaire (« ok ») :
- A1 [réserve] : réussite des passes courtes et moyennes encore plus loin du réel (82,9 / 76,3 % contre 89,4 / 87,1 %). Condition : traiter le 18i avant `v2-collectif/22a`, puis remesurer `_MISS_NOT_LOST` et `UNFORESEEN_CUT`.
- A2 [facultatif] : docstring de `pass_aim` (« déviée de 10 à 25 % ») périmée ; à corriger au 18i.
- À surveiller : buts par match 2,08 (près de la borne basse) ; passe longue encore trop réussie (71 % contre 52 %) ; optimisme de la chance évaluée de + 1 à + 3 points.
