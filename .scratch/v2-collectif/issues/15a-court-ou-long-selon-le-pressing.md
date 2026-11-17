# 15a: Court ou long selon le pressing, depuis la zone de construction

**Découpé du ticket 15 le 17/11/2026** (décision du propriétaire : « Je valide le découpage »). Détail d'origine : `15-construction-face-au-pressing.md`. **Chantier :** `v2-collectif`. **Priorité :** P1 (la sortie de balle ne s'adapte pas au pressing). **Catégorie :** décision.

**Constat vérifié (17/11/2026, série de 50 matchs du ticket `v2-realisme/25b`, graines du banc) :**
- le gardien relance court (passe de moins de 25 m) dans **97,7 %** des cas ; 92,1 % des relances sont gardées ; pertes dans son propre tiers : 14,6 par match ;
- en jeu, aucune passe longue aérienne n'existe : le ballon aérien n'est utilisé qu'aux remises en jeu (`match.py`, `restart.is_aerial`, vol jusqu'au point de chute à `AERIAL_LANDING_M` près, `restart.LONG_RESTART_M` = 25 m). La passe lobée générale est le ticket `32b`, bloqué par `32a` et `v2-hauteur-ballon/03` ;
- le placement de construction (25b) crée maintenant les solutions courtes et mesure le pressing haut (`Bloc.build_up` : part de l'écartement gardée, 1 sans pressing, 0,5 sous pressing).

**What to build:** quand le porteur est dans sa zone de construction (gardien, ou défenseur dans ses 35 m : la phase du 25b), il compare la meilleure solution courte et une relance longue vers un coéquipier haut (attaquant ou milieu offensif), selon le risque de perte de chacune. Sous pressing haut, la passe courte devient plus risquée et le jeu long plus fréquent ; sans pressing, il joue court. La relance longue en jeu réutilise le vol aérien des remises (point de chute, pas d'interception en vol), sans attendre la passe lobée générale (32b, qui la généralisera).

**Hors de ce ticket :** attirer le pressing, troisième homme (15b) ; qualité du geste du gardien, Kicking et Throwing (`v2-attributs-restants/03c`) ; passe lobée dans tout le jeu (32b).

**Attributs :** Decisions (choisir l'option qui sert, courbe partagée existante), Composure (garder son choix sous pression) ; Passing reste l'exécution de la passe longue, déjà lue. Rayons à vérifier dans `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage avec la décision existante (`decision.py`).

**Blocked by:** `v2-realisme/25b` (livré), 08 (livré), 13 (livré).

**Bloque :** 15b, 15c.

**Status:** livré (17/11/2026), validé expert (réserves A2 et A3 acceptées) + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible. Hypothèses : le vol aérien des remises se réutilise en jeu sans changer `ball.py` ni le moteur de vol ; la valeur de la passe longue se calcule avec les fonctions existantes de `decision.py` (chance de réussite, valeur future du ticket 13). Au-dessus du seuil de 2 h de peu : découpage examiné, le choix et son exécution sont indivisibles (le choix sans passe longue n'a pas d'effet mesurable).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après.

## Tests

- **Scènes :** gardien porteur, sortie de but jouée : sans pressing, il joue court ; avec 4 adversaires dans ses 35 m et ses solutions courtes couvertes, il joue long plus souvent (part mesurée sur des tirages à graine fixée).
- **Statistiques (50 matchs) :** part de relances longues du gardien et des défenseurs, avec et sans pressing haut ; pertes dans son propre tiers ; relances gardées.

## Acceptance criteria

- [x] Constantes produit (seuils, valeur du jeu long) et chiffres réels (part de relances longues, pertes dans son propre tiers : sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Part de jeu long mesurablement plus forte face à un pressing haut qu'en son absence, à situation égale (scène et 50 matchs)
- [x] Pertes de balle dans son propre tiers rapportées avant et après, comparées à la fourchette réelle si elle est trouvée (indicateur de calibration, pas objectif : pas de réglage générique, ticket 22)
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Choix tracé (journal des décisions : court ou long, et pourquoi)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Constantes validées (17/11/2026)

Proposées après analyse, validées par le propriétaire (« je valide 0,8 et 0,5, vas-y ») :
- `possession.LONG_BALL_DIFFICULTY_PER_M = 0,8` : difficulté de la passe longue en l'air par mètre au-delà de 10 m (1,8 au sol). À 50 m : 47 / 69 / 87 % de passes précises à Passing 40 / 55 / 70 (au sol : 5 / 14 / 32 %).
- `decision.LONG_BALL_WON = 0,5` : part des retombées que le porteur pense voir gagnées par son coéquipier (le choix seulement ; le duel aérien est le ticket `v2-realisme/15b`). Alternative écartée : 0,88, la part réellement gardée à la retombée dans le moteur actuel (mesurée sur 8 matchs : 112 gardés, 15 perdus).
- Périmètre validé : zone de construction du 25b ; cibles aux postes BU, ATT, SA, AG, AD, MOC, à plus de 25 m (`possession.LONG_PASS_M`, désormais la source de `restart.LONG_RESTART_M`) et à portée de frappe (`possession.max_pass_reach_m`, environ 58 m, dérivé des constantes existantes) ; envisagées hors de la portée de Vision (schéma d'équipe connu).

Chiffres réels : part de passes longues (32 m et plus) des gardiens de Premier League 46,6 % en 2023-24, 79,3 % en 2014-15 (Opta Analyst, « The evolution of the ball-playing goalkeeper », 2023) ; ballons longs gardés à la retombée : non trouvé (Opta : une sortie de but longue finit le plus souvent en duel aérien) ; pertes dans son propre tiers : non trouvé.

Cause du 97,7 % court (analyse) : la Vision limite les coéquipiers envisagés à environ 30 m (Vision 55) ; une passe de 50 m au sol réussit à 14 % (Passing 55), coupée tout le long.

## Réalisation (17/11/2026)

- `v2engine/possession.py` : `LONG_BALL_DIFFICULTY_PER_M`, `LONG_PASS_M`, `max_pass_reach_m()` ; paramètre `lofted` dans `pass_difficulty`, `pass_accuracy_probability`, `pass_success_probability` (en l'air : ni coupe ni coupe imprévue, précision seule, `_MISS_NOT_LOST` si imprécise), `pass_aim`, `pass_velocity`.
- `v2engine/restart.py` : `LONG_RESTART_M = LONG_PASS_M` (même valeur, 25 m).
- `v2engine/bloc.py` : fonction publique `builds_up(holder)` (zone de construction du 25b), utilisée par `_update_build_up` et par le match.
- `v2engine/decision.py` : `LONG_BALL_WON`, `LONG_BALL_POSTES` ; `evaluate_options` et `choose_action` prennent `build_up` ; en zone, une option de passe en l'air par cible haute (même monnaie, `_pass_option(lofted=True)` : réussite x `LONG_BALL_WON`, gêne du receveur comme au sol, perte comptée au point de chute) ; jamais de première ; `Action.lofted` et `Action.short_long` (meilleures valeurs réelles court / long).
- `v2engine/match.py` : `builds_up(holder)` transmis à la décision (positionnel, comme `seen_opponents`) ; passe en l'air exécutée comme une remise longue (`AERIEN`, `aerial_left_m` = distance − 3 m, aucun lecteur de passe), hors-jeu jugé au départ ; pas de renoncement « ligne fermée » après rotation pour une passe en l'air ; journal : précision `relance longue` sur l'événement de passe.
- `v2engine/trace.py` : `DecisionRecord.lofted`, `best_short_value`, `best_long_value` (le « pourquoi » du choix, en zone seulement).
- `docs/CARTE_ATTRIBUTS_V2.md` : Vision (ne filtre pas la relance longue) et Passing (exécute la passe en l'air, difficulté 0,8/m). Decisions et Composure : aucun effet nouveau, ils jouent par la perception. Test de rayon inchangé (aucun attribut lu par un nouveau module).
- Tests : 10 ajoutés (`tests/test_v2engine_relance_longue.py`, dont la scène défenseur ajoutée en réponse à A1) : précision aux points validés ; pas de coupe en vol ; seuil partagé avec les remises et portée 57,8 m ; `builds_up` (gardien, défenseur à 34 / 36 m, milieu, miroir) ; périmètre (zone, postes, 25 m, portée, Vision 11, jamais de première) ; avant-centre marqué moins intéressant ; scène pressing (0 % long sans pressing, 100 % avec 4 adversaires sur les solutions courtes, critère : ≤ 5 % et ≥ 80 %) ; exécution aérienne et journal (passe et décision) ; choix court tracé avec ses valeurs, rien hors zone.

**Mesures :** séries de 50 matchs aux graines du banc (`AUDIT_SEED + k`, k = 0 à 49, mêmes affiches que `scripts.measure_v2`), avant (`0f164be`, arbre de travail séparé) et après, script hors dépôt `serie_15a.py`. Relance : passe d'un gardien ou d'un défenseur dans ses 35 m ; longue : plus de 25 m (au sol avant, au sol ou en l'air après). Pressing : adversaires de champ dans les 35 m du passeur (0-1 sans, 2-3 moyen, 4 et plus haut).

| Indicateur | Avant | Après |
|---|---|---|
| Gardien : part longue sans / moyen / haut pressing | 1,5 / 2,1 / 0,0 % | 5,8 / 11,4 / 20,1 % |
| Défenseurs : part longue sans / moyen / haut pressing | 6,4 / 6,8 / 4,6 % | 11,0 / 10,7 / 7,0 % |
| Relances longues en l'air (50 matchs) : gardien ; défenseurs | 0 ; 0 | 101 ; 152 |
| Relances courtes gardées ; longues gardées | 91,8 % ; 85,3 % | 91,3 % ; 79,7 % |
| Pertes de balle par match ; dans son propre tiers (35 m) | 222,3 ; 11,8 | 221,9 ; 10,6 (− 10 %) |
| Buts par match ; tirs par match | 4,98 ; 40,5 | 5,36 (+ 8 %) ; 41,2 (+ 2 %) |

Lecture : chez le gardien, la part de jeu long croît nettement avec le pressing (critère tenu, scène et 50 matchs). Chez les défenseurs, elle augmente partout mais reste plus faible sous pressing haut que sans pressing (7,0 contre 11,0 %) : critère non tenu en match pour les défenseurs (anomalie A1 de l'expert, passage 1), tranché par le propriétaire (voir ci-dessous).

**Réponse à A1 (17/11/2026) :**
- Scène défenseur à situation égale (ajoutée, `test_defender_plays_long_more_often_under_high_pressing`) : central à 25 m de son but, avant-centre à 46 m marqué ; parmi ses passes, 0,9 % de relances longues sans pressing, 45,5 % sous pressing (toutes décisions : 0,6 et 10,1 % ; sous pressing il conduit surtout, risque de conduite du ticket `v2-realisme/04a`).
- Série stratifiée de 50 matchs (décisions où une relance longue était envisagée, script hors dépôt `serie_15a_strat.py`), part longue parmi les passes, sans / moyen / haut pressing : gardien 2,0 / 10,7 / 19,6 % (n = 51 / 383 / 301) ; défenseurs 9,8 / 5,8 / 3,3 % (n = 468 / 1 154 / 1 179, erreurs types 1,4 / 0,7 / 0,5 point).
- Diagnostic par mode (30 matchs, `diag_match.py`), défenseurs, part longue parmi les passes : construction normale 9,6 / 7,1 / 8,3 % ; contre-attaque après récupération 12,5 / 5,4 / 3,1 % ; conservation après récupération 0 / 1,7 / 0 %. Sous pressing haut, 81 % des décisions d'un défenseur sont des transitions après récupération (contre-attaque 52 %, conservation 29 %) ; la rotation n'y est pour rien (0 s en moyenne). La baisse vient du mélange des situations, pas d'une décision qui irait contre le pressing à situation égale.
- **Décision du propriétaire (17/11/2026) : « option A et je valide A2 et A3 »** : le critère « part de jeu long plus forte face à un pressing haut, à situation égale » est jugé sur les deux scènes (gardien, défenseur) et sur la série du gardien ; le jeu long des défenseurs en match (après récupération, et pressing mesuré par les solutions couvertes) passe au ticket de suite `15c-jeu-long-des-defenseurs-en-match.md`.
- Réserves de l'expert acceptées par le propriétaire (mêmes mots) : A2 (retombée estimée à 50 %, gardée à 80 % par le moteur, à faire converger au ticket `v2-realisme/15b`) ; A3 (un tir après une relance longue est classé « centre » dans l'origine des tirs, défaut déjà présent pour les remises longues, laissé hors de ce ticket).
- A4 (facultatif) corrigé : `_pass_option` ne calcule plus la réussite au sol d'une passe en l'air. Pertes dans son propre tiers : 11,8 → 10,6 par match (fourchette réelle non trouvée ; indicateur de calibration, pas d'objectif). Les ballons longs restent gardés à 80 % à la retombée, faute de duel aérien (`v2-realisme/15b`).

Déterminisme : deux exécutions à graine fixée (20260923, 30 min de jeu) : mêmes empreintes (événements `513f31603a6020ed`, ticks `aef11379806ef391`, décisions `86ca81a11a7aedb2`).

Première suite complète : 60 échecs, une seule cause (les tests qui remplacent `choose_action` par une fonction à arguments positionnels refusaient `build_up=`) ; corrigé dans `match.py` en passant l'argument en position. Deuxième suite : 3 199 passés, 1 échec (`test_v2engine_perceived_decision.py::test_the_match_gives_the_holder_his_perceived_world`, qui lisait `seen_opponents` comme dernier argument positionnel) ; test adapté pour le lire à sa position (9e argument), même intention, 9 passés dans son fichier. Suite complète : 3 200 passés (3 191 + 9). Après la scène défenseur (réponse à A1) et la correction de A4 : **3 201 passés, 0 ignoré, 14 désélectionnés** (3 191 + 10) ; `CLAUDE.md` mis à jour.

**Durée :** estimée 2 h 15, réestimée à 4 h 30 après le refus de l'expert (annoncée au propriétaire) ; réelle environ 4 h 15 de travail effectif (analyse 45, développement 40, tests 35, intégration et vérifications 135), à l'horloge de la session, non chronométrée ; écart + 89 % sur l'estimation initiale, − 6 % sur la réestimation. Cause : le refus de l'expert au passage 1 (critère non tenu pour les défenseurs en match) a demandé une scène défenseur, une série stratifiée et un diagnostic par mode ; la première suite complète a montré 60 échecs d'une seule cause (fonctions de test à arguments positionnels) ; un passage 3 de l'expert a été nécessaire pour sortir le suivi documentaire de la liste des fichiers revus. Temps machine hors total : mesure de la retombée (8 matchs), trois séries de 50 matchs (avant, après, stratifiée), deux diagnostics (12 et 30 matchs), quatre suites complètes (14 à 15 min).

## Comments

- **17/11/2026, passage 1** — Expert : `REJECTED`. QC : non lancé (refus de l'expert d'abord traité). Clôture : non journalisée. Anomalie bloquante A1 : critère « plus de jeu long sous pressing haut » non tenu pour les défenseurs en match (11,0 → 7,0 %). Réserves : A2 (retombée 50 % estimée contre 80 % gardée), A3 (relance longue classée « centre » dans l'origine des tirs). Facultatif : A4 (calcul en double). Suite : scène défenseur, série stratifiée, diagnostic par mode ; décision du propriétaire « option A et je valide A2 et A3 » ; A4 corrigé ; ticket `15c` créé.
- **17/11/2026, passage 2** — Expert : `APPROVED_WITH_RESERVATIONS` (A1 levée par la scène défenseur et la décision du propriétaire ; réserves A2, A3 ; facultatif A5 : cases non cochées). Liste des fichiers revus incluant le suivi documentaire : refaite au passage 3.
- **17/11/2026, passage 3** — Expert : `APPROVED_WITH_RESERVATIONS` (code identique au passage 2 ; réserves A2 et A3). QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ` (expert APPROVED_WITH_RESERVATIONS, réserves acceptées par le propriétaire, QC VALIDÉ). Réserves acceptées, mots du propriétaire : « option A et je valide A2 et A3 ». Points à surveiller (expert) : A2 au ticket `v2-realisme/15b` ; part longue des défenseurs sous pressing mesuré par les solutions couvertes (15c) ; conduite du central sous pressing dans la scène (78 %, ticket `v2-realisme/04a`) ; buts par match (4,98 → 5,36, non significatif sur 50 matchs).
