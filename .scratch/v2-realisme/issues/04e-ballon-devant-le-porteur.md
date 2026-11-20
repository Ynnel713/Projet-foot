# 04e: Le ballon n'est plus collé au porteur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans touche de balle, aucune conduite ne se dispute physiquement). **Catégorie :** physique.

**Constat vérifié :** `match.py:383` : `ball.position = holder.position` à chaque pas ; le ballon n'a ni avance ni touche.

**What to build:** Pendant une conduite, le ballon avance devant le porteur par touches : à chaque touche il part à une distance qui dépend de la vitesse et de Dribbling (touche plus courte pour un bon dribbleur), puis le porteur le rejoint. Le ballon a une position propre, visible à l'écran.

**Hors de ce ticket :** interception entre deux touches (04f).

**Attributs :** Dribbling (longueur de touche)

**Blocked by:** 04d (Vitesse de conduite selon Dribbling et la pression).

**Bloque :** 04f.

**Status:** livré (20/11/2026), validé expert + QC

## Constantes proposées (19/11/2026), validées par délégation du propriétaire

Délégation : « Je valide automatiquement toutes tes recommandations et avis d'expert » (propriétaire, 19/11/2026).

| Constante | Valeur | Raison |
|---|---|---|
| `TOUCH_PERIOD_S` | 0,6 s | une touche toutes les trois ou quatre foulées en conduite rapide (ordre de grandeur ; donnée chiffrée : non trouvée) |
| `TOUCH_LEAD_M` (avance maximale à vitesse de référence) | 2,0 m à Dribbling 11, 1,4 m à 55, 0,8 m à 99, linéaire | ballon à 1 à 2 m en conduite rapide ; touche plus courte pour un bon dribbleur (ticket) ; donnée réelle : non trouvée |
| `TOUCH_REFERENCE_MPS` | 7,0 m/s | avance proportionnelle à la vitesse jusqu'à une conduite rapide, plafonnée au-delà |
| Forme | demi-onde par touche, de `CONTROL_RADIUS_M` (au pied) à `CONTROL_RADIUS_M` + avance | ballon continu à l'écran (pas de saut), revient au pied à chaque touche ; aucun tirage |
| Porteur à l'arrêt ou en réception | ballon au pied, devant lui (cap `facing`) | posture de réception (07c) |

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible. Hypothèses : interactions nombreuses avec les contrôles, les tacles et le rendu (`api/routers/v2.py`) ; à redécouper si l'analyse le montre.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** conduite rectiligne à 6 m/s : ballon devant le porteur, à une distance bornée
- **Intégration :** rendu : le ballon apparaît devant le joueur

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code — section « Constantes proposées », délégation du 19/11/2026 ; chiffres réels : non trouvés.
- [x] Le ballon a une position propre pendant la conduite — `match.carried_ball_position` (demi-onde par touche, avance selon vitesse et Dribbling) ; `tests/test_v2engine_touche_de_balle.py` (conduite rectiligne à 6 m/s : ballon devant, avance bornée, dans l'axe ; bon dribbleur plus près ; à l'arrêt et en réception, au pied ; le moteur pose le ballon devant le porteur).
- [x] Aucune régression sur passes, contrôles et tacles (suite V2) — suite verte ; 50 matchs appariés : passes réussies, pertes en conduite, pertes sur tacle, buts, tirs sans écart significatif (`docs/INDICATEURS_V2.md` section 58). Le joueur frappe ou passe le ballon à son pied (il l'a rejoint) : sans cela, 9 tests du tir échouaient (tir parti du ballon devant lui, contre et cadrage jugés depuis lui).
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour — Dribbling règle la longueur de touche (effet nouveau, sans tirage, sans effet sur l'issue) ; `tests/test_v2engine_rayon_attributs.py` vert ; ligne Dribbling de la carte complétée.
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) — section « Durée réelle ».
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions — match de 10 min, piste du ballon `bb7be3f8eb53abe6` deux fois.
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` — 3 461 passés (3 455 + 6), 0 ignoré, 14 désélectionnés.
- [x] Reprise 04d A2 : vitesse moyenne balle au pied par tranche de Dribbling (Pace égal) ajoutée au banc (`v2_indicators.py` ou `--profil Dribbling`), relevée avant et après le ticket — `Collector._carry_speed` (part de la vitesse maximale, donc Pace neutralisé) : 0,326 / 0,329 / 0,336 (Dribbling 40-55 / 55-70 / 70+), avant 0,329 / 0,333 / 0,337.
- [x] Reprise 04d A1 : série de 50 matchs (tirs de près par équipe, distance au but des tirs, buts) comparée à la fourchette de `docs/INDICATEURS_V2.md` ; `CONTACT_SLOWDOWN` (0,15) proposé au propriétaire pour recalage (0,08 à 0,10) si les tirs de près en sortent — tirs de près 3,93 par équipe (3,89 avant), buts 4,34 (4,20) ; le 04e n'y change rien ; aucune fourchette de tirs de près dans la doc, volume de tirs déjà renvoyé au `v2-collectif/22a` : pas de recalage proposé.

## Reprises du 04d (réserves de l'expert acceptées le 08/11/2026)

- **A1** : le joueur moyen ralentit d'environ 10 % en pratique (80 % des intervalles de conduite ont une gêne ≥ 0,5, adversaire à moins de 2,5 m), alors que le 04d visait à ne pas le déplacer. Sur 20 matchs : tirs de près par équipe 4,98 → 4,30, buts 2,95 → 2,55 (dans le bruit). La touche de balle du 04e change la conduite : la mesure à 50 matchs se fait ici, avant tout calage de constante.
- **A2** : le critère « Dribbling 99 contre 11, même Pace : vitesse moyenne balle au pied plus élevée » du 04d n'est vérifié que par un test de scène ; aucun indicateur du banc ne le mesure en match.
- Facultatif (A3) : renforcer deux tests du 04d (`test_high_dribbling_covers_more_ground_than_low_at_the_same_pace` a une assertion tautologique ; `test_a_slower_carry_reaches_less_free_space` accepte `slow is None`).

## Comments

- 20/11/2026, implémentation : `BallState.carry_start_s` (première touche du porteur), `match.carried_ball_position`, `match.touch_lead_m` ; ballon ramené au pied à la frappe et à la passe. Test adapté : `tests/test_v2engine_central_couvert.py` (scène de 5 minutes au lieu de 3 : la graine ne donnait plus de sortie de ligne en 3 minutes). Reprise facultative A3 du 04d non faite. À vérifier à l'écran : le ballon devant le joueur en conduite, et le petit retour au pied au moment de la passe ou du tir (jusqu'à l'avance du moment, 0,7 m en moyenne).
- 20/11/2026, ticket traité avant le 23a (bloqué par la clôture, arbitrage du propriétaire attendu) : base `c3bc860` (29b).

- 20/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (empreinte 5f5a0562), QC VALIDÉ, clôture VALIDÉ. Réserves acceptées par délégation du propriétaire (« Je valide automatiquement toutes tes recommandations et avis d'expert », 19/11/2026) : A1 (le ballon recule vers le porteur dans la seconde moitié d'une touche quand Dribbling est sous environ 60, jusqu'à − 3,5 m/s à Dribbling 11 et 7 m/s) et A2 (retour du ballon au pied à la passe et au tir, recul à la touche trop longue). **Condition : A1 corrigée au plus tard au début du 04f** (profil de touche asymétrique, poussée brève puis décroissance, à proposer au propriétaire), A2 au 04f ou dans un ticket d'écran, avec tests de vitesse du ballon et de continuité de la piste. Facultatif : A3 (phase non remise à zéro après un coup franc de hors-jeu), A4 (pivot du ballon sur un virage serré). QC : test d'intégration du rendu absent (non exigé par les critères).

## Durée réelle

Environ 2 h 20 de travail effectif pour 2 h 15 estimées (+ 4 %) : analyse 25 min, développement 40 min, tests 35 min, intégration et vérifications 40 min (9 tests du tir réparés par la frappe au pied, banc relancé). Durée estimée à l'horloge de la session hors attentes machine, non chronométrée ; temps machine hors total : 50 matchs appariés du banc (deux fois pour l'arbre d'après), trois suites complètes (15 min chacune).

