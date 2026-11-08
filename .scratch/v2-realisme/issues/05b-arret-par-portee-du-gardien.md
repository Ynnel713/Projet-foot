# 05b: Arrêt : le gardien atteint ou non le ballon

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (un arrêt doit dépendre de la position, du temps de réaction et de la portée). **Catégorie :** exécution.

**Constat vérifié :** aujourd'hui un tir non converti et cadré est toujours remis au gardien (`match.py`, `save_outcome`), sans que le gardien ait à atteindre le ballon ; sa position compte seulement comme une part d'angle (`keeper_position_factor`).

**What to build:** Sur le trajet du tir, le gardien intercepte le ballon s'il peut atteindre le point de passage à temps : temps de réaction, puis déplacement latéral et plongeon jusqu'à une portée maximale (valeurs neutres, validées). Atteint : arrêt, avec l'issue du ticket 28b (capté, repoussé, claqué). Non atteint : le ballon continue.

**Hors de ce ticket :** notes du gardien (Reflexes, One on Ones, Handling) : `v2-attributs-restants/03b`.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/28b` (issues de l'arrêt, implémenté) sans le modifier.

**Blocked by:** 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ); 03b (Gardien : placement sur la bissectrice ballon-poteaux).

**Bloque :** 03f, 05e, 05f, 05g, 06a, 16e.

**Status:** livré (08/11/2026), validé expert + QC

**Découpage (08/11/2026)** : le ticket et les réserves A2 et A3 du 05a dépassaient 2 h. L'allumage de l'interrupteur (A2), le recâblage du banc (A3, partie banc) et la série de 50 matchs (taux d'arrêt par distance) passent au nouveau ticket `05h` ; ici : la mécanique de l'arrêt, derrière l'interrupteur, et la trace des grosses occasions (A3, partie occasions).

## Constantes (proposées le 08/11/2026, validées par délégation du propriétaire)

| Constante | Valeur | Source |
|---|---|---|
| `KEEPER_REACTION_S` | 0,25 s | ordre de grandeur (temps de réaction visuo-moteur simple, environ 0,2 s) ; temps de réaction d'un gardien sur tir : non trouvé |
| `KEEPER_STANDING_REACH_M` | 1,0 m | corps et bras, sans plonger ; non trouvé |
| `KEEPER_DIVE_REACH_M` | 2,8 m | plongeon complet ; non trouvé (repère : demi-largeur du but 3,66 m) |
| `KEEPER_DIVE_MPS` | 4,0 m/s | vitesse à laquelle le plongeon gagne de la portée ; non trouvé |

Réglage sur la mesure au `05h`.

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 30 min | 30 min |
| Développement | 50 min | 45 min |
| Tests unitaires et comportementaux | 35 min | 15 min |
| Intégration et vérifications | 25 min | 35 min |
| **Total (travail effectif)** | **2 h 20** | **2 h 05** (− 11 %, durée estimée, non chronométrée) |

Confiance : moyenne. Hypothèses : trajectoire à plat ; la hauteur viendra au 05f.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir à 20 m au centre : arrêté ; tir à 8 m en pleine lucarne latérale : non atteint ; gardien mal placé (03b désactivé) : plus de buts
- **Statistiques (séries de matchs) :** 50 matchs : taux d'arrêt par distance, rapporté sans réglage (déplacé au `05h`, qui recâble le banc)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Arrêt décidé par l'atteinte du ballon, tracé avec le temps disponible
- [x] Taux d'arrêt décroissant avec la proximité et la vitesse du tir (scènes)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Reprises du 05a (réserves de l'expert, 08/11/2026)

- **A2** : allumer `SHOT_FLIGHT_RESOLUTION` et retirer du jeu ouvert la branche `attempt_shot` / `shot_for` / `classify_unscored` ; test de garde sans monkeypatch de l'interrupteur.
- **A3** : `OccasionTracker.update` ferme l'occasion sur l'issue provisoire « en vol » : la fermer quand l'issue se décide sur la ligne (ou relire l'issue définitive) ; `measure_v2` doit compter les tirs depuis la trace, plus par `attempt_shot`. Test : un tir en vol qui marque donne une occasion d'issue « tir : but ».
- **À surveiller** : le tir est freiné comme une passe (environ 15 m/s à l'arrivée d'un tir de 30 m), ce qui donne au gardien plus de temps qu'en réalité tant que le 35a n'est pas livré.

## Réalisation

- `shooting.keeper_reach_m` : portée du gardien selon le temps de vol (constantes ci-dessus).
- `BallState.shot_flight` devient `ball_state.ShotFlight` : au départ, chance de but (pour l'issue de l'arrêt du 28b), tir cadré ou non, et distance de vol au point où le ballon passe au plus près du gardien (il ne va que sur un tir cadré).
- `match._keeper_reaches` : quand le ballon passe ce point, le gardien l'atteint si son écart au ballon tient dans sa portée ; atteint : issue du 28b (capté, repoussé, claqué ; jamais capté hors de sa surface, 03d), sinon le ballon continue. Temps de vol et écart tracés (`ShotEvent.keeper_time_s`, `keeper_gap_m`). Suite d'un arrêt regroupée dans `match._keeper_save`, partagée avec l'ancienne branche.
- `occasion.ChanceTracker` : un tir « en vol » laisse l'occasion ouverte jusqu'à son issue (réserve A3 du 05a, partie occasions).
- Tests : `tests/test_v2engine_arret_portee.py` (7 ; suite complète : 2 589 passés, 14 désélectionnés) : portée, tir à 20 m dans l'axe arrêté (temps et écart tracés), tir à 8 m en pleine lucarne non atteint, moins d'arrêts plus le tir est proche, tir plus rapide qui passe, gardien mal placé qui encaisse, occasion fermée sur l'issue finale du tir en vol.

## Mesures (08/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/05b-*`)

- **Interrupteur coupé** : 2 matchs, moteur du commit `b351c13` (`05b-avant.json`) contre moteur du ticket (`05b-det1.json`, `05b-det2.json`) : tous les indicateurs identiques, seul le temps de calcul diffère.
- **Interrupteur allumé** (20 matchs, 4 lots de 5, `05b-on*.json`) : 3,9 buts par match (2,2 à 5,4 selon le lot ; 12 à 14 au 05a sans gardien), conversion 8,5 % (repère 10-11 %), arrêts 28,3 % des tirs, à côté 35,1 %, au-dessus 14,5 %, contrés 18,1 %. Taux d'arrêt par distance : au `05h` (banc à recâbler).

## Comments

- 08/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (un passage, empreinte 95358d77) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05b/cloture`).
- Réserve A1 (gardien qui suit le ballon pendant le vol puis plonge : mouvement compté deux fois) : acceptée ; mesure et correctif reportés au `05h`, avant d'allumer l'interrupteur.
- Réserve A2 (ballon replacé du point de contact au corps du gardien à l'arrêt) : acceptée ; reportée au `05h`.
- Réserve A3 (occasion ouverte si un tir en vol n'a jamais d'issue ; entrée `flying` périmée possible, point aussi relevé par le QC) : acceptée ; reportée au `05h`.
- Facultatif A4 (longueur des lignes d'import) : non traité.
- Ligne du registre des estimations ajoutée (QC, point de suivi 1).
- Réserves acceptées par le propriétaire : délégation permanente du 05/11/2026 (« Considère que je valide automatiquement toutes tes recommandations et celles des expert ») et lancement de la clôture du 08/11/2026 (« Oui »).
