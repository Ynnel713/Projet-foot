# 23a: Erreur d'exécution continue de la passe

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`, recommandation « ticket dédié », acceptée par le propriétaire le 10/11/2026). **Priorité :** P1. **Catégorie :** moteur.

**Constat vérifié (10/11/2026) :** la passe est réussie ou ratée en tout ou rien (`possession.pass_aim`). Réussie, elle part vers la course du receveur avec le seul dosage (`dosage_quality`) ; ratée, le point visé est décalé de 10 à 25 % de sa longueur dans une direction tirée au hasard sur 360° (`_MISS_SHARE`), sans lien avec la note ni avec la difficulté. L'erreur de vitesse (`pass_velocity`, `_DOSAGE_ERROR`) est déjà continue, mais indépendante du tirage réussi / raté. Conséquence : pas de passe « un peu trop longue » ou « légèrement derrière le receveur », seulement des passes parfaites ou des passes perdues au hasard.

**What to build:** Remplacer le tout ou rien par une erreur d'exécution continue, sur le modèle du tir depuis le 35b : la direction et la vitesse de départ sont tirées autour de la passe idéale (écarts gaussiens), avec un écart d'autant plus large que Passing est bas et que le passeur est sous pression (pression et Composure) ; la longueur n'élargit l'écart angulaire que si une difficulté technique propre aux passes longues est justifiée, puisqu'un écart angulaire fixe fait déjà croître l'erreur latérale avec la distance. L'adversaire dans la ligne de passe et le receveur marqué **n'élargissent pas l'écart** : ils agissent par la physique (interception, receveur devancé), et la chance de décision les intègre par l'alignement (réserve A2 de l'expert, 10/11/2026). La passe réussit ou non par la physique : le ballon arrive, ou non, dans la portée du receveur avant un adversaire. L'anticipation de la course du receveur (`dosage_quality` dans `pass_aim`) reste la lecture du jeu : elle fixe la passe idéale et n'est pas une erreur d'exécution. La vitesse tirée est bornée (jamais négative, jamais au-delà de `MAX_PASS_MPS`). La note passe par la façade des notes (`19a`), pour que la fatigue s'y branche au `20a` sans reprendre ce code ; ce ticket n'ajoute aucun effet de fatigue.

La chance de passe (`pass_success_probability`) doit rester alignée sur la nouvelle résolution, comme le tir l'a été au `05e` : même loi d'écart, pas deux modèles. Elle est lue en six endroits, tous à aligner (réserve A1 de l'expert, 10/11/2026) : `decision.py` (trois appels : choix du receveur, plan « ligne ouverte »), `off_ball.py` (démarquage), `restart.py` (choix du receveur d'une remise), `occasion.py`. Les remises en jeu servies (touches, corners, six mètres, y compris aériennes, `match.py`) passent déjà par `pass_velocity` : elles changent aussi avec ce ticket. Tous les tirages restent dans le flux nommé `PASSE`.

**Attributs :** Passing, Composure (déjà lus ; aucun attribut nouveau).

**Blocked by:** 19a (façade des notes), 19c (garde probabiliste : chiffre l'écart actuel de la passe) ; 29b (interception par le défenseur non lecteur, ordre du propriétaire du 19/11/2026).

**Bloque :** 23b ; `v2-collectif/32a`. Le `20a` branchera la fatigue sur cette loi d'écart s'il est livré après ; sinon, ce ticket la lit par la façade (aucune dépendance bloquante).

**Status:** livré (20/11/2026), validé expert + QC

## Constantes proposées (19/11/2026), validées par délégation du propriétaire

Délégation : « Je valide automatiquement toutes tes recommandations et avis d'expert » (propriétaire, 19/11/2026, enchaînement 29b → 23a → 04e).

| Constante | Valeur | Raison |
|---|---|---|
| `PASS_SIGMA_DEG_POINTS` (écart-type de l'angle, sans pression) | 6° à Passing 11, 3° à 55, 1,5° à 99, linéaire | hypothèse du ticket (2° à 99, 8° à 11) resserrée pour garder la réussite des passes : à 20 m, 3° donne 1 m d'écart latéral ; donnée réelle : non trouvée |
| `PASS_PRESSURE_SIGMA_GAIN` | 1,0 | même forme que le tir (`SHOT_ERROR_PRESSURE_GAIN`) : écart x (1 + pression x part de Composure), x 1,75 au contact à Composure moyenne |
| `PASS_SPEED_SIGMA` | 0,30/√3 à Passing 11, 0,05/√3 à 99 (selon le dosage) | écart-type de l'erreur uniforme d'avant (hypothèse du ticket) |
| `BACKHEEL_SIGMA_FACTOR` | x 2 | remplace les 20 points de difficulté de la talonnade (07e) |
| Passe de première | écart / `one_touch_precision` | la précision du geste (31a) multipliait la chance précise ; elle divise maintenant l'écart |
| `ON_TARGET_M` (chance évaluée) | 1,0 m | portée du receveur (`RECEIVER_REACH_M`) ; ajustée sur 62 531 passes de 50 matchs (graines 12 à 61, grille 1 à 2,5 m) ; 1,5 m au premier ajustement sur 12 matchs, rejeté au contrôle hors échantillon |
| `LOFTED_ON_TARGET_M` | 2,5 m | passe longue en l'air : à 50 m, Passing 55 garde 66 % de passes précises (69 % au 15a) |
| `_LATERAL_NOT_LOST` (remplace `_MISS_NOT_LOST` 0,70 / 0,95 et `UNFORESEEN_CUT`, réserve A2 de la clôture) | 0,99 sous 1 m, 0,98 de 1 à 2 m, 0,98 de 2 à 4 m, 0,70 au-delà (écart latéral à l'arrivée, tiré de la même gaussienne) | réajusté à la reprise du 20/11/2026 sur le moteur après le 04e (24 matchs, graines 300 à 323) par moindres carrés sur les tranches ; plafond 0,99 imposé par la garde du 19c (1 % d'échec au moins sur une passe facile) |
| Table de coupe (`_CUT_NEAR_PASSER`, `_CUT_ON_PATH`) | 0,81 / 0,20 / 0,023 près du passeur ; 0,45 / 0,32 / 0,15 / 0,083 / 0,057 / 0,031 sur le trajet | remesurée par adversaire (méthode du 18g) sur les mêmes 24 matchs ; remplace l'exposant 1,2 du premier passage |
| Longueur, ligne de passe, receveur marqué | n'élargissent pas l'écart | ticket (réserve A2) ; `_MARKED_DIFFICULTY`, `_DIFFICULTY_PER_M`, `LONG_BALL_DIFFICULTY_PER_M`, `BACKHEEL_DIFFICULTY`, `pass_difficulty`, `_MISS_SHARE` et `_DOSAGE_ERROR` supprimés |

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 1 h 30 |
| Tests unitaires et comportementaux | 45 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **3 h 30** |

Confiance : moyenne. Hypothèses : `19a` livré (lecture par la façade) ; l'alignement de la chance de décision réutilise la méthode du `05e` (`scripts/shot_calibration.py` adapté) ; écarts proposés à valider : direction σ ≈ 2° à Passing 99 et ≈ 8° à 11 sans pression, vitesse σ = a/√3 de l'erreur uniforme actuelle `_DOSAGE_ERROR` (environ 17 % à Passing 11, 2,9 % à 99) ; chiffre réel cherché, « non trouvé » sinon.

**Estimation révisée (10/11/2026, avant le code)** : 2 h 30 au lieu de 2 h 00 (+ 30 min : six lecteurs de la chance de passe à aligner et remises en jeu à mesurer, réserve A1). Au-delà du seuil indicatif de 2 h, examiné pour découpage : non découpé, car aligner la décision dans un ticket séparé laisserait deux modèles de passe dans le moteur entre les deux livraisons.

**Estimation révisée (10/11/2026, réserve A1 de la revue `backlog-v2/erreur-execution-continue-reserves`)** : 3 h 30 au lieu de 2 h 30. Les tickets du tir les plus proches ont pris 170 min (35b, erreur continue) et 220 min (05e, alignement de la décision) ; le développement passe de 45 min à 1 h 30 (construire une chance de passe qui reproduit une réussite décidée par la physique). L'expert recommandait un découpage en 23a1 et 23a2 ; le propriétaire a choisi de garder un seul ticket (« Garde le seul », 10/11/2026), écart au seuil de 2 h assumé.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs avant / après.

## Tests

- **Unitaires (scène contrôlée, `tests/scenes.py`) :** passe de 10 m et de 35 m, Passing 11 / 55 / 99, avec et sans pression, 5 000 tirages : écart moyen au point idéal croissant quand la note baisse et quand la difficulté monte
- **Garde (`19c`) :** Passing 11 peut réussir une passe difficile, Passing 99 peut rater une passe facile (plancher validé au `19c`)
- **Ligne de passe (réserve A2) :** même passe en scène, avec et sans adversaire dans la ligne : écart au point idéal identique, seule la réussite baisse
- **Alignement :** par tranche de chance évaluée, passes réussies observées dans l'intervalle de confiance
- **Match (50 matchs) :** taux de passes réussies, pertes de balle, tirs et buts avant / après ; remises en jeu (touches, corners, six mètres) : part qui atteint un coéquipier, avant / après

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code — section « Constantes proposées », délégation du 19/11/2026 ; chiffres réels : non trouvés.
- [x] `_MISS_SHARE` et le décalage au hasard sur 360° supprimés ; une seule loi d'écart, lue par la décision et par la résolution — `pass_error_sigma_rad` et `pass_speed_sigma` tirés par `pass_velocity`, lus par `pass_accuracy_probability` ; test `test_the_imprecise_share_follows_the_accuracy_chance_lane_or_not` (part imprécise tirée = 1 − chance de précision à 2 points près).
- [x] Écart au point idéal croissant quand Passing baisse et quand la difficulté monte (scène, 5 000 tirages) — `test_lateral_error_grows_when_passing_drops_and_with_difficulty` (10 et 35 m, Passing 11 / 55 / 99, avec et sans pression).
- [x] Écart au point idéal identique avec et sans adversaire dans la ligne de passe (scène, 5 000 tirages) ; seule la réussite baisse — même test que ci-dessus (écarts identiques au tirage près, chance évaluée plus basse).
- [x] Les six lecteurs de `pass_success_probability` utilisent la loi alignée — tous lisent la même fonction, réécrite sur la loi d'écart (`decision.py` x 3, `off_ball.py`, `restart.py`, `occasion.py`).
- [x] Garde du `19c` tenue pour la passe — `tests/test_v2engine_garde_probabiliste.py` vert ; écart connu du 19c remplacé par `test_pass_error_is_continuous_and_narrows_with_the_rating`.
- [x] Chance évaluée calibrée sur 7 tranches (méthode du `05e`), **critère révisé par le propriétaire le 20/11/2026** (l'ancien, au plus une tranche hors de l'intervalle à 95 %, est hors d'atteinte avec ce modèle : à 60 000 passes l'intervalle des tranches pleines fait ± 0,2 à 2 points) : au plus 4 points d'écart dans chaque tranche d'au moins 500 passes, moyenne à 0,5 point près, hors échantillon — 48 matchs neufs (graines 400 à 447, 61 958 passes) : moyenne − 0,2 point, pire écart 3,3 points (tranche 0,43, 2 782 passes), 4 tranches sur 7 hors de l'intervalle ; `docs/INDICATEURS_V2.md` section 59.
- [x] Taux de passes réussies par match : écart au plus 3 points avec l'avant, sinon cause expliquée et soumise au propriétaire (aucun recalage compensatoire) — 81,41 % → 82,95 % (+ 1,54 ± 0,39), 50 matchs appariés contre l'état après le 04e (`137b9f4`).
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) — section « Durée réelle ».
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions — match complet, graine 3 : `a0a00fc70e436018` deux fois (reprise du 20/11/2026).
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` — 3 464 passés (3 461 après le 04e, + 3), 0 ignoré, 14 désélectionnés ; aucun fichier V1 touché.

## Comments

- 10/11/2026, création (ticket documentaire `backlog-v2/erreur-execution-continue`, commit `3ca8cbc`) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ. Réserves reportées ici, validées par délégation du propriétaire (« Oui reporte le », 10/11/2026) : A1 (six lecteurs de la chance de passe et remises en jeu), A2 (la ligne de passe et le marquage agissent par la physique, pas par l'écart), A5 (σ de vitesse, bornes, anticipation, nombre de tranches). Estimation portée à 2 h 30.
- 10/11/2026, renvoi de la garde probabiliste (`19c`) : dosage de 0 à 1 et ampleur de la passe ratée indépendante de la note, test d'écart connu `test_known_gap_pass_dosage_and_miss_size_are_all_or_nothing` (`tests/test_v2engine_garde_probabiliste.py`) ; à retirer par ce ticket, et la passe gardée sur la nouvelle loi.
- 20/11/2026, implémentation : la loi d'écart remplace la passe ratée au tirage (`possession.pass_velocity`) ; `pass_difficulty` et ses constantes supprimées. Tests adaptés : difficulté (réécrits sur la loi), garde du 19c, relance longue (15a : 52 / 66 / 75 % de passes en l'air précises à 50 m au lieu de 47 / 69 / 87 % ; sous pressing, le central joue long dans 6 % de ses passes au lieu de 44 %), passe de première, valeur de passe (A 36 % / B 13 %, rapport 2,75 au lieu de 3), troisième homme (B rapproché de 2 m, gain de lecture 0,077 à 99), tranches (B en retrait : A ne conduit plus 2 s face à une passe longue). Script de diagnostic : passe imprécise lue sur la vitesse du ballon (écart latéral au-delà de 1 m).
- 20/11/2026, critère de calibration non tenu (3 tranches sur 7) : soumis à la clôture, sans recalage de plus ; trois redémarrages du conteneur pendant les mesures (lots relancés).

- 20/11/2026, revue de clôture, passage 1 : expert REJECTED (empreinte ae274663), QC REFUSÉ ; clôture non validée. Bloquants : A1 critère de calibration non tenu (3 tranches sur 7 hors IC) ; A2 part non perdue des passes imprécises constante (0,95 au-delà de 10 m) : Passing et la pression ne pèsent plus que 1 à 3 points dans la chance d'une passe au sol (35 m : 1,1 point entre Passing 30 et 90, environ 22 avant) ; A3 régression du 15a (central sous pressing : 6 % de passes longues au lieu de 45 %, seuil de test abaissé). Non vérifié : A4 remises en jeu (mesurées depuis : réussite 81,1 % → 76,5 %, − 4,7 ± 2,8 points ; au sol − 3,4). Réserve A5 : pertes au contrôle + 4,5. La loi d'exécution (`pass_error_sigma_rad`, `pass_velocity`) est jugée saine et à garder.
- 20/11/2026, correctif A2 essayé (non revu) : part non perdue par bande d'écart latéral tirée de la même gaussienne (`_LATERAL_NOT_LOST`, bandes < 1 / 1-2 / 2-4 / > 4 m) et table de coupe remesurée selon la méthode du 18g, sur 50 matchs (graines 112 à 161, 69 000 passes ; table 0,825 / 0,201 / 0,021 près du passeur, 0,453 / 0,313 / 0,168 / 0,096 / 0,055 / 0,032 sur le trajet ; parts 0,971 / 0,962 / 0,933 / 0,792). Calibration **sur l'échantillon d'ajustement même** : 4 tranches sur 7 hors IC (écarts de 0,5 à 4 points), moyenne exacte ; passeurs à Passing < 50 surestimés de 6,7 points (0,810 évaluée, 0,743 observée), 50-70 et ≥ 70 à moins de 1,3 point ; pression bien suivie. La physique ne punit l'écart latéral que faiblement (part non perdue 0,97 sous 2 m, 0,93 de 2 à 4 m, 0,79 au-delà).
- **Décision attendue du propriétaire** (le critère « au plus une tranche hors IC sur 7 » n'est pas atteignable avec ce modèle à 60 000 passes, où l'IC des tranches pleines fait ± 0,2 à 1 point) : (a) relâcher le critère en écart maximal par tranche (par exemple 3 points, tranche la plus basse exceptée) et garder le modèle par bandes ; (b) chercher pourquoi un passeur faible perd plus que son écart ne l'explique (piste : dosage et vitesse d'arrivée, contrôle du receveur) avant de reclôturer ; (c) revenir à la passe ratée au tirage. Recommandation : (b) puis (a). Le travail (loi d'exécution, modèle par bandes, tests) est conservé hors commit (le verrou interdit de commiter sans clôture validée) : `git stash` « 23a » et le correctif en scratch.

- 20/11/2026, décision du propriétaire : piste (b) puis (a) (« ok avec ta reco »). Reprise estimée à 2 h 05 (diagnostic 1 h 20, reclôture 45 min) ; réestimée en cours de route à 2 h 35 (réajustement sur le moteur après le 04e, non prévu).
- 20/11/2026, piste (b), diagnostic (24 matchs neufs, graines 300 à 323, moteur après le 04e, 29 723 passes) : (1) la chance évaluée était pessimiste de 2,4 points en moyenne (5 tranches sur 10 hors IC) : les parts par bande avaient été ajustées avant le 04e, qui a réduit les pertes ; (2) passeurs à Passing < 50 (3 % des passes) : à écart latéral réel égal, leurs passes sont plus souvent perdues (sous 1 m : 0,758 non perdues contre 0,879 à 70 et plus), à chaque tranche de vitesse et de dosage ; ce n'est pas la loi d'exécution mais le contexte (adversaires autour du receveur, que la chance ne voit pas depuis le 18g) : ticket `18m` créé ; (3) erreur de vitesse : passes lentes des faibles 7 points sous la chance, environ 1 point au total, laissée hors chance ; (4) passes en l'air de jeu : 0,63 observées contre 0,87 évaluées sur 123 passes (retombée disputée hors de la chance, voulu au 15a ; renvoyé au 15b).
- 20/11/2026, réajustement : table de coupe et parts par bande remesurées sur les 24 matchs, parts plafonnées à 0,99 (garde du 19c) ; contrôle hors échantillon sur 48 matchs (graines 400 à 447) : moyenne − 0,2 point, pire écart 3,3 points. Décision du propriétaire (option 1) : critère « 4 points par tranche d'au moins 500 passes, moyenne à 0,5 point » ; trou de contexte au `18m`.
- 20/11/2026, réserve A3 (régression du 15a) : défenseur central sous pressing 5,7 % de passes longues (45,5 % au 15a). Décision du propriétaire (option 1) : nouvelle référence, test réécrit sur la valeur mesurée (au moins 4 % sous pressing et 10 fois le jeu libre), valeur de la passe longue sous pressing renvoyée au `15b`.
- 20/11/2026, réserve A2 remesurée : chance d'une passe au sol de 35 m, Passing 30 → 90 : + 5,0 points sans pression, + 10,4 au contact (+ 1,1 au premier passage, environ 22 avant le 23a) ; 15 m : + 0,4 et + 1,7. A4 (remises, 50 matchs appariés contre le 04e) : réussite 81,5 % → 76,1 % (− 5,4 ± 2,4), au sol inchangée (91,5 %), en l'air 67,2 % → 59,0 % (− 8,2 ± 4,7 ; cause non établie : les remises n'utilisent pas le modèle en l'air, piste d'un effet de sélection vers des cibles lointaines, à mesurer au 15b ; explication corrigée après la réserve A1 de l'expert au second passage). A5 : pertes au contrôle 19,4 → 21,5 (+ 2,1 ± 1,8).

- 20/11/2026, revue de clôture, passage 2 : expert APPROVED_WITH_RESERVATIONS (empreinte e13d99ba). Réserves : A1 remises en l'air − 8,2 ± 4,7 points, cause documentée fausse (les remises n'utilisent pas le modèle en l'air) : explication corrigée, cause non établie, mesure au 15b ; A2 Passing pèse peu sur la passe au sol courte (+ 0,4 point à 15 m, + 5,0 à 35 m), à suivre au 18m et au 36a ; A3 pertes au contrôle + 2,1 ± 1,8, à suivre au 36a ; A4 contrôle hors échantillon joué avec les parts non plafonnées, à refaire avec le moteur livré au 23b ou au 18m. Facultatifs : A5 commentaires périmés dans les tests (corrigés) ; A6 seuils abaissés au premier passage sous la délégation du 19/11 (troisième homme 0,08 → 0,05, valeur de passe 3 → 2,5). Réserves A1 à A4 acceptées par le propriétaire : « Oui j'accepte » (20/11/2026). Corrections A1 et A5 soumises à un passage 3.
- 20/11/2026, revue de clôture, passage 3 (corrections A1 et A5, documentation et commentaires seulement) : expert APPROVED_WITH_RESERVATIONS (empreinte 066788f7, mêmes réserves A1 à A4, déjà acceptées), QC VALIDÉ ; clôture VALIDÉ.

## Durée réelle

Premier passage : environ 4 h 30 de travail effectif pour 3 h 30 estimées (+ 29 %) : analyse 30 min, développement 1 h, tests 1 h, intégration et vérifications 2 h (deux ajustements de la chance évaluée, le premier rejeté hors échantillon ; deux tests de comportement réparés après la suite ; mesures relancées après trois redémarrages).

Reprise du 20/11/2026 (pistes b puis a) : environ 2 h 40 pour 2 h 05 estimées (+ 28 %), dont diagnostic 1 h 05, réajustement et contrôle 45 min, tests 20 min, documentation 30 min ; réestimée à 2 h 35 en cours de route (réajustement non prévu, annoncé avant). Total du ticket : environ 7 h 10 pour 3 h 30 estimés au départ (+ 105 %) ; cause : la chance évaluée devait reproduire une réussite décidée par la physique, sur un moteur qui a changé pendant le ticket (29b, puis 04e), soit trois ajustements au lieu d'un, et deux arbitrages du propriétaire.

Durées estimées à l'horloge de la session hors attentes machine, non chronométrées. Temps machine hors total : premier passage 12 + 50 + 50 matchs de calibration, 50 matchs appariés, deux suites complètes ; reprise 1 + 24 + 48 matchs, 2 x 50 matchs appariés, une suite complète (17 min 55).
