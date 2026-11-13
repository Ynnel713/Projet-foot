# 08b: Mémoire de perception : positions vues, datées et vieillissantes

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** aucune mémoire : la perception est recalculée sur les positions réelles à chaque pas (`cerveau.perceive`).

**What to build:** Chaque joueur garde la dernière position et vitesse vues de chaque autre joueur, avec l'instant ; la position perçue est extrapolée et son erreur croît avec l'âge de l'observation. Anticipation règle seulement la qualité de l'extrapolation (déjà son rayon : lire l'action), sans nouvel effet.

**Attributs :** Anticipation (extrapolation, rayon existant)

**Blocked by:** 08a (Champ de vision : ce qui est dans le dos n'est pas vu).

**Bloque :** 08c, 08d, 08e, `v2-collectif/31`.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : erreur linéaire avec le temps : forme simple à valider.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** adversaire vu puis caché 2 s : position perçue extrapolée, erreur bornée

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (« ok constantes » ; chiffres réels : non trouvés, voir Comments)
- [x] Mémoire tracée pour le porteur et les receveurs (`DecisionRecord.memory_*`, `ReceptionEvent.memory_*`)
- [x] Aucun effet sur le jeu dans ce ticket (empreinte d'un match à graine fixée identique avant et après : `625f5ce17d50985c` ; `measure_v2 2` : 0 ligne du 08a modifiée)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (aucune lecture directe d'attribut : la part est `decision.anticipation_share`, même effet que le ticket 33 ; carte complétée)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`08b-det1`, `08b-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 833 passés, 0 ignoré, 14 désélectionnés = 2 823 + 10 ; `08b-suite.txt`)

## Comments

**13/11/2026, lancement.** « lance le 08b » ; 08a livré entre-temps. Estimation annoncée : 2 h, confiance moyenne.

**13/11/2026, constantes.** Proposées puis validées (« ok constantes ») : extrapolation = dernière position vue + part × dernière vitesse vue × âge, la part étant celle de l'Anticipation du ticket 33 (`decision.anticipation_share`, 99 → 100 %, 55 → 65 %, 11 → 30 %, aucune courbe nouvelle, R1) ; horizon de 2 s, puis position figée ; aucun bruit ajouté (l'erreur vient du jeu) ; initialisation à la position réelle de tous au coup d'envoi et à la 2e période ; mise à jour à chaque tick. Chiffres réels (durée de la mémoire visuelle d'un footballeur pour des positions mobiles) : non trouvés, choix de modèle.

**Correction d'un énoncé validé.** J'avais annoncé « erreur bornée (au plus l'horizon × la vitesse) ». C'est faux : c'est le déplacement extrapolé qui est borné ; l'erreur contre la position réelle continue de croître au-delà de 2 s tant que le joueur n'est pas revu (erreur maximale mesurée : 40 m côté porteur, 43 m côté receveur). Docstring de `perception_memory.py` et test corrigés (`test_extrapolation_stops_at_the_horizon`) ; comportement inchangé.

**13/11/2026, code.** `v2engine/perception_memory.py` : `PerceptionMemory` (mise à jour, `perceived_position`, `age_s`, `error_m`, `reading`) et `MemoryReading` ; `vision.seen_by` (même test que `sees`, une fois par observateur, chemin chaud) ; branchement dans `match.simulate_match` (mise à jour après les collisions, avant le ballon ; recréée à la mi-temps) et lecture seule dans `_step_ball` / `_step_loose_ball`. Trace : `DecisionRecord.memory_age_s`, `.memory_error_mean_m`, `.memory_error_max_m` (porteur, adversaires non vus) ; mêmes champs sur `ReceptionEvent` (receveur). Banc : `measure_v2` et `v2_indicators` (`on_receptions`, `peak`).

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/08b-*`).**
- Aucun effet sur le jeu : un match à graine fixée (20260923), empreinte sur événements, buts, tirs, décisions, réceptions et positions échantillonnées : identique sur le code du 08a et sur le code du 08b (`625f5ce17d50985c`, 2 444 décisions, 1 332 événements) ; `measure_v2 2` : les 2 429 lignes du 08a sont toutes inchangées (0 ligne modifiée ou retirée ; lignes en plus : 7 de mémoire et les découpages de `--detail`).
- Déterminisme : `08b-det1` et `08b-det2` identiques hors temps de calcul.
- Porteur à la décision (2 matchs, décisions avec un adversaire non vu) : âge moyen de la dernière vue 2,19 s ; erreur moyenne de position perçue 3,4 m ; maximale 39,9 m. Receveur à la réception : 61,5 % des réceptions avec au moins un adversaire non vu ; âge 3,25 s ; erreur moyenne 3,8 m ; maximale 42,7 m.
- Temps de calcul : coût propre de `update` 140 µs par tick, soit environ 7,6 s par match de 90 min (micro-banc, 22 joueurs) ; mesure de match entière non comparable (machine chargée : 84 s contre 75 s au 08a).
- Tests : 10 ajoutés (`tests/test_v2engine_perception_memory.py`). Suite : 2 833 passés, 0 ignoré, 14 désélectionnés ; `CLAUDE.md` mis à jour.

**À regarder au 08d / 08c.** Âge moyen de 2,2 s côté porteur et 3,3 s côté receveur : la mémoire est vieille, car le cône de 200° du corps laisse longtemps le dos non vu ; les scans (08c) devraient faire baisser ces chiffres.

**Durée.** Estimée 2 h. Réelle environ 1 h 45, non chronométrée (analyse 20 min, développement 40 min, tests 20 min, intégration et vérifications 25 min) : − 12 %. Temps machine hors total : suite complète (8 min 22 s, deux lancements dont un perdu au redémarrage du conteneur), 2 x 2 matchs, comparaison d'empreinte.

**13/11/2026, passage 1.** Expert : APPROVED (rapport `08b-expert-1.md`), aucune anomalie bloquante. Facultatifs : A1, l'énoncé « erreur bornée » corrigé (déjà fait, voir plus haut) ; A2, à surveiller au 08d et au 08c : la position figée après 2 s peut s'écarter de 40 m de la réalité et ne doit pas servir sans plafond de confiance, les âges de 2 à 3 s doivent baisser avec les scans, et aucune portée visuelle n'existe (un joueur à 80 m dans le cône est vu exactement, héritage du 08a) ; A3, documentation hors empreinte. QC : VALIDÉ (tests non exécutés par lui, preuves du ticket). Clôture : VALIDÉ (expert APPROVED, QC VALIDÉ).
