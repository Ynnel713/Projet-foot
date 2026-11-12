# 18f: Calibration provisoire 1 bis : choix du porteur et rythme de décision

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0. **Catégorie :** validation.

**Origine :** découpé du 18d le 11/11/2026 (estimation du 18d au-delà de 2 h). Le 18d règle la course et les appels ; ce ticket reprend le volet « choix du porteur et rythme de décision » que le point d'étape 18a avait ajouté au 18d (`docs/INDICATEURS_V2.md` section 25).

**Constat vérifié (12e, 50 matchs) :** le porteur choisit la conduite dans 72 % des décisions (passe 27 %, tir 1,3 %) ; 2,55 passes par possession (cible 3 à 5) ; 21,4 tirs tracés par équipe (R1 : 8 à 15), dont la plupart dans les 15 s d'une récupération haute ; passes 911 par match (R7 : 890 à 940, déjà dans la fourchette), 12,5 par minute de jeu effectif (cible 15 à 17, l'écart tient surtout au temps de jeu effectif, 70 %, sans remplacements ni assez de fautes). Une part des décisions n'est pas comparable à une donnée réelle : le porteur réévalue toutes les 0,5 s (`decision.DECISION_INTERVAL_S`), chaque intervalle de conduite compte pour une décision.

**What to build:** D'abord diagnostiquer pourquoi la conduite l'emporte (valeur de la conduite contre celle de la passe dans la monnaie commune du ticket 33 : chance de garder le ballon, `FREE_TOUCH_SHARE`, `PRESSURE_KEEP_SHARE`, portée de l'espace libre ; rythme de décision), en séparant mécanisme et constante. Puis régler provisoirement, sur 50 matchs puis 500, les seules constantes en cause, dans leurs fourchettes validées, pour rapprocher passes par possession (3 à 5) et volume de tirs (R1), sans faire sortir les passes par match de 890 à 940. Mêmes règles de calibration provisoire que le 18d. Relire après réglage : tacles (47), fautes (15), possession d'équipe (17,6 s), passes visées vers les DC (environ 12 par match ; si l'écart reste, ticket de relance à créer).

**Hors de ce ticket :** volumes de course et appels (18d) ; tir et gardien (18e) ; passes longues et en profondeur (`v2-collectif/32a`, 32b).

**Attributs :** aucun

**Blocked by:** 18d (Calibration provisoire 1 : volumes de course et rythme).

**Bloque :** 18e, `v2-collectif/22a`.

**Status:** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : faible (la cause de la part des conduites n'est pas encore établie). Hypothèses : leviers existants seulement ; si la cause est un mécanisme, ticket neuf.
Temps machine, non compté : séries de 50 matchs (environ 70 min chacune), série de 500 matchs (environ 4 h), suite complète (environ 40 min).

## Tests

- **Statistiques (séries de matchs) :** 50 puis 500 matchs avant / après, intervalles de confiance ; profils A/B inchangés en sens (Dribbling, Decisions, Passing, Vision)

## Acceptance criteria

- [ ] Cause de la part des conduites établie (mécanisme ou constante) avant tout réglage
- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Passes par possession rapprochées de 3 à 5 ; passes par match toujours dans 890 à 940
  - **Dérogation du propriétaire (12/11/2026)** : 947,8 passes par match [940,8 ; 954,8] sur 500 matchs tolérées, écart attribué au temps de jeu effectif trop long (74 %, réel 53 à 56 %) ; à relire au 18g, au `v2-collectif/22a` et à la correction du temps de jeu effectif. Mots du propriétaire, en réponse à la question « Do you grant the exception for 948 passes per match? » : « Yes, exception granted ».
- [ ] Chaque constante modifiée marquée « provisoire », avec date et mesure
- [ ] Écarts restants attribués (mécanisme ou calibration finale)
- [ ] Aucun effet d'attribut inversé ni annulé (scènes A/B rejouées)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (11/11/2026)

Lancé par délégation du propriétaire (« Je valide toutes tes recommandations et tous les avis d'expert », 11/11/2026). Estimation annoncée : 1 h 50, inchangée (la correction tient en une ligne, sans constante).

- **Diagnostic** (état 18d, 12 matchs, 37 440 décisions, script de diagnostic hors dépôt : il enveloppe `decision.evaluate_options` et `match.choose_action`, puis relit le porteur à chaque pas) : la conduite est le meilleur choix réel dans 80 % des décisions ; 5,7 % seulement des conduites laissaient une passe meilleure (la perception n'est pas la cause) ; la garde de conduite évaluée suit l'observée (0,88 contre 0,89 à gêne 0,6). La meilleure passe d'un porteur pressé ne réussit qu'à 0,60 : le presseur au contact comptait deux fois, dans la pression et dans le couloir de toute passe jouée de son côté. **Cause : mécanisme** (double compte), pas une constante : `FREE_TOUCH_SHARE` ne joue que sans adversaire à 5 m (4 % des conduites), `PRESSURE_KEEP_SHARE` presque pas (receveur peu gêné : 0,08 en moyenne), le rythme de décision ne change pas la valeur réelle des options.
- **Code** : `v2engine/possession.py` (`_lane_opponents` : près du passeur, cône de 45° ou portée de jambe tendue `_LANE_REACH_M` = 1 m, même valeur validée que `shooting.BLOCK_WIDTH_M`). Le cône seul (essai `18f-cone50`) faisait échouer `test_coordinated_press_closes_more_options_than_an_individual_press` (le pressing coordonné ne fermait plus que 0,3 solution au lieu de 1,8) : une passe qui frôle la jambe d'un presseur à 1,2 m (0,93 m) n'était plus gênée ; avec la portée de jambe, 1,7 solution fermée, test vert sans retouche.
- **Tests** : `tests/test_v2engine_difficulte.py` (presseur à 1,5 m à 60° de la passe : pression seule ; à 30° : pression + couloir).
- **Mesure** (`docs/INDICATEURS_V2.md` section 29, 50 matchs) : conduite 70,8 → 68,3 % des décisions, passes par possession 2,71 → 2,82, pertes en conduite 89,6 → 83,5, passes par match 912 → 945 [923 ; 968], par minute de jeu effectif 12,5 → 12,9 ; tirs, tacles, fautes, course inchangés ; buts 2,96 [2,46 ; 3,46] (4,1 avec le cône seul : bruit de 50 matchs, à relire au 18e sur 500).
- **Série de 500 matchs** (demandée par l'expert au passage 1 ; `18f-500.*`, comparaison appariée `18f-comparaison.txt` contre `18d-500`) : passes par possession + 0,12 [+ 0,10 ; + 0,13] (2,81) ; passes par match 948 [941 ; 955], 0,8 au-dessus de 940 ; buts 3,47, écart − 0,07 [− 0,29 ; + 0,15] (bruit des 50 matchs écarté) ; conversion, buts dans la surface, tacles, fautes sans écart significatif.
- **Déterminisme** : `18f-det2.json` contre les 10 premiers matchs de `18f-det1.json`, 2 437 clés identiques.
- **Suite complète** : 2 754 passés, 14 désélectionnés (`18f-suite.txt`) ; un test de plus que l'attendu (2 753).
- **Constantes** : aucune constante existante modifiée ; une constante de règle nouvelle, `possession._LANE_REACH_M` = 1,0 m (portée de jambe tendue, même valeur que `shooting.BLOCK_WIDTH_M`, validée au 05c), et une pente de cône de 1 (45°) implicite dans `max(_LANE_REACH_M, along)`. Ce sont des valeurs de modèle, pas de calibration : non marquées « provisoire ». Proposées et retenues par délégation du propriétaire (« Je valide toutes tes recommandations et tous les avis d'expert », 11/11/2026, dans la conversation de ce ticket).
- **Scènes A/B** (`.scratch/v2-realisme/mesures/18f-ab.txt`, script `18f-ab-script.py`, 400 scènes de porteur pressé, notes 99 contre 11, règle d'avant contre règle d'après) : sens et ampleur gardés. Meilleure passe : Passing + 0,53 → + 0,51, Composure + 0,075 → + 0,072. Part des passes choisies : Passing + 0,62 → + 0,62, Vision + 0,10 → + 0,11, Dribbling − 0,13 → − 0,15 (un bon dribbleur garde le ballon), Decisions − 0,30 → − 0,26 (dans ces scènes, la conduite est le meilleur choix réel).
- **Écarts attribués** : passes par possession sous 3 (mécanisme : coupe en vol absente de l'évaluation, ticket neuf **18g** ; puis 22a) ; passes par match à la limite haute (945, intervalle [923 ; 968] qui recoupe 890 à 940 : temps de jeu effectif 74 %, calibration finale) ; tirs au 18e.
- **Durée** : estimée 1 h 50, réelle environ 2 h 50 (+ 55 %, au-delà du seuil de 30 %). Causes : diagnostic outillé (deux scripts : valeurs d'options et pertes observées), règle retouchée après l'échec du test de pressing (portée de jambe), puis reprise après le refus du QC et la demande de l'expert (scènes A/B, documentation des constantes, série de 500 matchs). Temps machine hors total : diagnostic de 12 matchs, séries de 12, 50, 50, 10 et 500 matchs (496 min), deux suites complètes (16 et 17 min).

## Comments

- 12/11/2026, passage 1 : expert DEMANDE DE VÉRIFICATIONS (série de 500 matchs appariée à 18d-500 : passes par match, buts) ; QC REFUSÉ (passes par match 945 hors 890 à 940, ligne absente du registre des estimations, série de 500 absente, scènes A/B absentes, constante `_LANE_REACH_M` non déclarée). Corrigé hors code : registre, scènes A/B (`18f-ab.txt`), constante déclarée, série de 500 matchs (`18f-500.*`).
- 12/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS (A1 : passes par match 947,8 [940,8 ; 954,8], 0,8 au-dessus de 940, attribué au temps de jeu effectif ; A2 : constante `_LANE_REACH_M` et pente de 45° déclarées ; A3 facultatif : assertion du test plus explicite) ; QC REFUSÉ (critère « passes par match toujours dans 890 à 940 » violé sur 500 matchs, aucune dérogation explicite du propriétaire). Désaccord expert / QC : clôture non validée, décision du propriétaire attendue (dérogation au critère ou correction).
- 12/11/2026, décision du propriétaire sur le désaccord du passage 2 : dérogation au critère des passes par match accordée (« Yes, exception granted ») ; réserves de l'expert acceptées : A1 par cette dérogation, A2 (constante `_LANE_REACH_M` et pente de 45° déclarées) par la délégation du 11/11/2026 (« Je valide toutes tes recommandations et tous les avis d'expert ») ; A3 facultatif, non traité.
- 12/11/2026, passage 3 : QC VALIDÉ (dérogation du propriétaire sur les passes par match, réserves A1 et A2 acceptées) ; clôture VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserves acceptées par le propriétaire).
