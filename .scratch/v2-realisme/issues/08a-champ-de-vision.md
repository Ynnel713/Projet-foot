# 08a: Champ de vision : ce qui est dans le dos n'est pas vu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** le porteur évalue ses options avec les positions réelles de tous les adversaires (`decision.evaluate_options`) ; seule l'élan des adversaires est déformé par l'Anticipation (`decision.anticipation_share`).

**What to build:** Chaque joueur voit les joueurs situés dans un cône autour de son cap (angle sourcé ou « non trouvé ») ; les autres ne sont pas vus à cet instant. Ce ticket calcule la visibilité et la trace ; il ne change pas encore les décisions.

**Hors de ce ticket :** mémoire (08b), décisions sur le monde perçu (08d).

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 08b, `v2-collectif/31`.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : calcul en O(n²) par pas acceptable (à mesurer).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs (temps de calcul).

## Tests

- **Unitaires (scène contrôlée) :** adversaire à 2 m dans le dos : non vu ; devant : vu
- **Intégration :** temps de calcul rapporté

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (± 100°, « Ok 100° » ; réel 200 à 214°, voir Comments)
- [x] Visibilité calculée et tracée (`vision.sees`, `vision.unseen` ; `DecisionRecord.unseen_opponents`, `.unseen_near`)
- [x] Aucun effet sur le jeu dans ce ticket (`measure_v2 2` identique au 07e à graine fixée, hors temps de calcul et nouvelles lignes)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : 1 h 35 contre 1 h 50, − 14 %
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`08a-det1`, `08a-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 823 passés, 0 ignoré, 14 désélectionnés = 2 819 + 4 ; `08a-suite.txt`)

## Comments

**13/11/2026, lancement.** « Ok 08a ». Estimation annoncée : 1 h 50, confiance élevée.

**13/11/2026, constante.** Proposée : cône de ± 100° autour du cap (200° au total). Réel : champ visuel horizontal humain d'environ 200° (sources courantes ; vision binoculaire environ 120°) à 214° (± 107° : Strasburger, Rentschler et Jüttner 2011, « Peripheral vision and pattern recognition: A review », Journal of Vision, erratum 2024) ; l'extrême périphérie détecte mal un joueur, d'où 100°. Le cap est celui du corps : les rotations de tête (scan) élargiront ce champ au 08c. Réponse du propriétaire : « Ok 100° ».

**13/11/2026, code.** `v2engine/vision.py` : `FIELD_OF_VIEW_HALF_DEG`, `sees` (point dans le cône), `unseen` (joueurs hors du cône, éventuellement à une distance maximale) ; lecture pure, aucun tirage. Trace : à chaque décision du porteur, `DecisionRecord.unseen_opponents` (adversaires non vus) et `.unseen_near` (non vus à `possession.PRESSURE_RADIUS_M`, 5 m, au plus). Banc : moyennes et part des décisions avec un adversaire non vu à 5 m (`measure_v2`, `v2_indicators`). Visibilité calculée pour le porteur à sa décision seulement : la mémoire de chaque joueur (08b) la calculera pour tous.

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/08a-*`).**
- Aucun effet sur le jeu : `measure_v2 2` identique au 07e (`07e-det1.txt`) sur ses 2 426 lignes, hors temps de calcul ; 3 lignes nouvelles.
- Déterminisme : deux exécutions identiques hors temps de calcul (`08a-det1`, `08a-det2`).
- Porteur à la décision (2 matchs) : 4,14 adversaires non vus en moyenne ; 1,03 à 5 m au plus ; 73,9 % des décisions avec au moins un adversaire non vu à 5 m (le porteur fait face à sa course, le presseur arrive souvent de l'arrière ou du côté) : à relire au 08d, quand la décision se fera sur le monde perçu.
- Temps de calcul : 75,3 s par match, contre 81,2 au 07e mesuré pendant une suite complète (charge) : non comparable ; coût propre négligeable par construction (22 produits scalaires par décision, environ deux décisions par seconde).- Tests : 4 ajoutés (`tests/test_v2engine_vision.py` : cône de ± 100°, adversaire à 2 m dans le dos non vu et devant vu, trace à la décision, lecture pure sans tirage). Suite : 2 823 passés, 0 ignoré, 14 désélectionnés ; `CLAUDE.md` mis à jour.

**13/11/2026, décisions du propriétaire prises pendant le 08a (hors de son code).**
- Le champ de vision utile dépend de la possession, de la vitesse, de la gêne, de la technique et de la prise d'information (« QI foot ») : inscrit au **08c** (porteur tête basse selon Dribbling + Technique cumulés ; scans selon Vision, la vitesse et la gêne ; à réestimer et découper avant le code). Le 08a garde le cône géométrique, sans effet sur le jeu.
- **Règle R2 révisée** (`docs/CARTE_ATTRIBUTS_V2.md`) : « Un geste ou un mouvement peut résulter du cumul de plusieurs attributs sans aucun problème, c'est même ce qui fait la richesse du sport (et du projet). » Cumul permis s'il est justifié et documenté ; R1 (pas de double comptage d'un même effet) inchangée ; le test de garde devient l'inventaire des cumuls.
- **Ticket 05k créé** (tir masqué : le gardien voit partir le ballon en retard), sur l'idée du propriétaire.
- Réponse : « ok pour tout ».

**Durée.** Estimée 1 h 50. Réelle environ 1 h 35, non chronométrée (analyse 20 min dont la source du champ visuel, développement 25 min, tests 20 min, intégration et vérifications 30 min) : − 14 %. Temps machine hors total : 2 x 2 matchs, suite complète (9 min). Discussion des extensions de la perception hors durée du ticket (rédaction du 08c et du 05k comptée dans l'intégration).

**13/11/2026, passage 1.** Expert : APPROVED (rapport `08a-expert-1.md`). Facultatifs : A1, une passe abandonnée en cours de rotation (07e) produit une deuxième décision tracée, les moyennes de vision sont pondérées par décision ; A2, `unseen` parcourt deux fois les adversaires par décision. À surveiller au 08d : 73,9 % des décisions avec un adversaire non vu à 5 m (pertes par pressing venu de l'arrière) ; le 08c devrait faire baisser ce chiffre. QC : VALIDÉ. Clôture : VALIDÉ (expert APPROVED, QC VALIDÉ).
