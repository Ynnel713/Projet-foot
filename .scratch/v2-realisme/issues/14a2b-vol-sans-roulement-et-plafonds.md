# 14a2b: Freinage du ballon en l'air (traînée seule), suppression de MAX_FLIGHT_S, borne de la vitesse de frappe

**Découpé du ticket 14a2 le 26/11/2026** (décision du propriétaire : « 14a2b s'occupera du nettoyage de la dette (MAX_FLIGHT_S et plafond de vitesse), sur une base déjà stabilisée. »). Contexte et constantes : `14a2-roulement-et-trainee.md` ; constats du 02a1 : `14a-freinage-au-sol-calibre.md` (Comments).

**Chantier :** `v2-realisme`. **Catégorie :** physique.

**What to build:**
- en l'air (`z > 0`), `a = k·v²` sans roulement : l'interface `freinage` reçoit l'état en vol là où il compte (pas du moteur, durée de vol `match._launch_aerial`) ;
- supprimer `hauteur.MAX_FLIGHT_S` (durée de vol finie pour toute passe jouable avec la traînée seule) ;
- borner la vitesse totale de frappe √(vh² + vz²) à 35 m/s (repère réel 18 à 35 m/s, 02a1) ; **méthode à faire choisir au propriétaire à l'ouverture** (vz réduit et vol plus court, ou vh réduit).

**Blocked by:** 14a2a. **Bloque :** 14b, 14d ; `v2-collectif/22a`.

**Status:** livré (27/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs) | 35 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs, suite complète.

**Estimation révisée (26/11/2026, à l'ouverture) : 2 h 20** (+ 20 min de développement et de tests). Le moteur appliquant la traînée seule en vol, les tirs (tous lancés avec `vz > 0`) suivent cette loi : leurs prévisions (`match` : vitesse verticale du tir ; `shooting._flight_time_s`, `_flight_distance_m` : temps du gardien) passent en vol, sinon hauteur à la ligne et gardien décrochent du moteur.

**Estimation révisée (26/11/2026, après la première série de 50 matchs) : 2 h 50** (+ 30 min : borne d'angle de départ, décision du propriétaire, voir Comments), plus une seconde série de 50 matchs (temps machine).

## Acceptance criteria (posés avant le code, 26/11/2026)

- [x] Méthode de la borne de vitesse choisie par le propriétaire avant le code : **vz réduit** (26/11/2026) : vh gardé, `vz ≤ √(35² − vh²)`, vol plus court, le ballon retombe avant la cible puis rebondit ou roule vers elle
- [x] Loi en vol (tests, calcul analytique) : décélération 8,46 m/s² à 25 m/s et 2,44 m/s² à 10 m/s (± 0,01), aucun terme de roulement ; passe aérienne de 50 m (vh 23,4 m/s) : vol continu 3,19 ± 0,02 s ; de 30 m à 30 m/s jusqu'à 15 m/s en vol : 51,2 ± 0,1 m
- [x] Pas du moteur : en vol (`z > 0` ou `vz > 0` au début du pas) traînée seule, au sol loi du 14a2a inchangée ; lectures au pas en vol égales à la boucle de `match._step_ball` (écart < 1e-9 m, tolérance absolue)
- [x] `MAX_FLIGHT_S` supprimé ; durée de vol finie (non `None`) pour toute passe aérienne de 1 à 120 m (test)
- [x] Borne : passe de 70 m à 30 m/s : `vz` = 18,03 m/s, vitesse totale 35,0 m/s ; vitesse totale de frappe ≤ 35 m/s (+ 1e-9) sur toutes les passes et relances aériennes de 50 matchs, nombre de frappes bornées relevé (tirs exclus de la borne, décision du propriétaire du 27/11/2026, voir Comments)
- [x] Borne d'angle (ajoutée le 26/11/2026, décision du propriétaire) : `vz ≤ vh·tan 45°` ; passe de 48 m à 13,9 m/s : `vz` = 13,9 m/s, sommet < 10 m (test) ; sur 50 matchs, aucun sommet de passe aérienne au-dessus de 30 m, angle de départ ≤ 45° (+ 1e-9)
- [x] Tirs : hauteur à la ligne du moteur égale à la hauteur tirée (tests du 02a2 verts, plus un tir de 3 m tiré au-dessus de la barre qui reste au-dessus) ; prévision du gardien au pas en vol égale au moteur
- [x] 50 matchs avant/après (graines 0 à 49), écarts au-delà du bruit (séries A/B du 02a1) documentés et soumis au propriétaire ; temps de calcul par match ≤ + 15 %
- [x] Déterminisme à graine fixée (graines 0 et 1, deux exécutions) ; suite complète au compte attendu (3 585 + tests ajoutés), 0 échec ; V1 inchangée
- [x] Reprises du 14a2a : commentaires `match.py` (« 60 m de course ») et `hauteur.py` (« freinage exponentiel ») ; `test_stepped_quantities_follow_the_engine_step` en `abs=1e-9`
- [x] Durée réelle relevée

## Comments

### 26-27/11/2026 — implémentation

- **Code** : `v2engine/freinage.py` : paramètre `airborne` (`deceleration`, `speed_after`, `step_velocity`, `distance_after`, `stepped_travel_time_s`, `travel_time_s`) ; en vol `dv/dt = −k(v)·v²` (même crise de traînée à 15 m/s), solutions exactes `v0 / (1 + k·v0·t)`, `ln(1 + k·v0·t) / k` ; lectures au pas en vol par une boucle paresseuse sans cache (fin de table à 0,1 m/s, constante de calcul). `v2engine/hauteur.py` : `MAX_FLIGHT_S` supprimé ; `MAX_STRIKE_MPS = 35` et `MAX_LAUNCH_ANGLE_DEG = 45` (voir ci-dessous) appliqués par `max_launch_vz` dans `launch_vz` (passes et relances aériennes, vitesse horizontale en paramètre) ; `launch_vz_to` (tirs) non borné (voir clôture, passage 1). `v2engine/match.py` : le pas du ballon prend la loi en vol si `z > 0` ou `vz > 0` au début du pas ; `_launch_aerial` et la vitesse verticale des tirs lisent le temps de trajet en vol. `v2engine/shooting.py` : `_flight_time_s` et `_flight_distance_m` en vol (un tir part toujours vers le haut). Commentaires des reprises du 14a2a corrigés (`match` : 77 m de roulement à 30 m/s ; `hauteur` : bloc « freinage exponentiel » supprimé avec `MAX_FLIGHT_S`).
- **Limites (ponytail)** : seule la vitesse horizontale est freinée (traînée calculée sur vh, pas sur la vitesse totale) ; un tir parti trop bas qui retombe avant la ligne puis roule est prévu en vol par le gardien (écart faible) ; les tirs ne sont pas bornés : 36 tirs sur 1 346 dépassent 35 m/s en 50 matchs, dont des tirs tout près de la ligne à `vz` irréaliste (jusqu'à 1 462 m/s, préexistant au 02a2 : temps de trajet de quelques centièmes de seconde) ; la vitesse de départ des passes aériennes reste calculée par la loi au sol (`possession.pass_velocity`), donc plus rapide que nécessaire en l'air (au `v2-collectif/22a`) ; `meeting_point` et `occasion` prévoient encore les ballons aériens par la loi au sol.
- **Valeurs** (tests, calcul analytique) : décélération en vol 8,46 m/s² à 25 m/s, 2,44 à 10 m/s ; 30 → 15 m/s en 51,2 m ; passe aérienne de 50 m à 23,4 m/s : 3,19 s ; 70 m à 30 m/s : 4,05 s de vol, `vz` borné à 18,03 m/s ; passe de 48 m frappée à 13,9 m/s : `vz` 13,9 m/s (45°), sommet sous 10 m.
- **Tests** : 12 ajoutés (dont, après la clôture passage 1, `test_a_close_shot_over_the_bar_stays_over_without_strike_speed_cap`) (`test_v2engine_freinage.py` : loi en vol, valeurs, intégration fine, pas du moteur réel en vol et au sol ; `test_v2_hauteur_ballon.py` : borne de vitesse, borne d'angle, passes moyennes non bornées, durée de vol finie de 1 à 120 m) ; adaptés : `test_vol_plafonne` devient `test_vol_borne_par_la_vitesse_de_frappe`, temps de vol en vol dans `test_v2_hauteur_tirs`, `test_v2engine_ballon_mort`, `test_v2engine_relance_longue`, `test_shots_use_the_engine_step_travel_time` ; réserve A3 du 14a2a (`abs=1e-9`).
- **Suite complète** (code final) : 3 597 passés (3 585 + 12), 0 échec, 0 ignoré, 14 désélectionnés (19 min 29 s, machine chargée).
- **Série 1 (sans borne d'angle)**, 50 matchs (`14a2b-frappes.py`, enveloppe de `scripts.bench_series` qui relève chaque frappe, `14a2b-apres-sans-angle.*`, `14a2b-frappes-sans-angle/`) : vitesse totale ≤ 35,0 m/s ; mais 32 passes aériennes au-dessus de 25 m de sommet, jusqu'à 52,6 m (vh 13,9, vz 32,1 : passes mal dosées vers un coéquipier lointain ; avant, `MAX_FLIGHT_S` plafonnait le sommet à 24,8 m). **Décision du propriétaire (26/11/2026)** : borne d'angle de départ 45° (`vz ≤ vh·tan θ`).
- **Série 2**, 50 matchs, graines 0 à 49, tirs encore bornés (`14a2b-tirs-bornes/`) ; **série 3 (finale, tirs hors borne)** : `14a2b-apres.json`, `14a2b-frappes/` : tous les indicateurs identiques à la série 2 sauf « ticks au-dessus du plafond de vol (24,9 m) » (aucune issue de tir renversée par la borne sur ces 50 matchs). Valeurs ci-dessous ; avant = série après du 14a2a (code `9abb7c4`, identique à la base de ce ticket) ; bruit = séries A/B du 02a1 (`14a2b-tolerance.py`, `-tolerance.txt`, `14a2b-ecarts.txt`). Frappes en l'air : 913 passes, 1 346 tirs ; passes bornées : 157 ; passes : vitesse totale maximale 35,0 m/s, angle maximal 45,0°, sommet maximal 29,7 m (3 au-dessus de 25 m). Hors bruit : 72 indicateurs sur 971 sans tranches, quartiles ni effectifs (29 entre A et B). Principaux : réceptions « centre » 10,3 → 6,4 par match (4,8×), touches 13,2 → 16,5 (2,1×), gardien au tir, écart au point visé 1,84 → 2,24 m (1,8×), ballon libre repris par l'équipe qui l'avait 77,9 → 76,2 % (2,0×), tirs de contre 7,7 → 9,5 par match (1,6×), calibration xG des petites occasions [0 ; 0,03[ (5,8×, valeurs sous 0,03 but par match). Dans le bruit : buts 4,22 → 4,52, passes réussies 82,3 → 82,0 %, passes par match 1 343 → 1 319, possession 20,5 → 20,6 s, contrôles de ballon dur 6,7 → 6,5 % ; passes longues réussies 66,9 → 64,0 % (1,0×, limite). Temps de calcul : 156 → 163 s par match en série 2 (+ 4 %) ; 210 s en série 3 sur machine chargée (suite complète 19 min 29 s contre 15 min) ; mesure appariée simultanée, 2 matchs, base `9abb7c4` 285 s contre ticket 279 s par match (pas de ralentissement).
- **Diagnostic des centres** (8 matchs appariés, `14a2b-diag-centres.py`) : vol à la durée de la loi au sol (lobs plus hauts) 7,1 par match, code du ticket 7,3, pas du moteur avec roulement en vol 10,8 (avant 10,3). Cause : absence de roulement en vol et pendant les petits rebonds, l'effet voulu ; ces réceptions étaient surtout des fins de petits rebonds (constat du 02c).
- **Décision du propriétaire (27/11/2026)** sur ces écarts : « Accepter, clôturer » (calibration au `v2-collectif/22a`, classement des centres au `02c`).
- **Déterminisme** (code final) : graines 0 et 1, deux exécutions, mêmes empreintes (`b7d0ec9ca4c369e0`, `f5a1415dd2ea4bbb` ; `14a2b-empreintes-1.txt`, `-2.txt`). V1 : aucun fichier touché, tests V1 verts.
- **À vérifier à l'écran** (non fait) : longs ballons et dégagements moins hauts (sommet ≤ 30 m), passes molles qui retombent court, rebonds qui filent plus loin.
- **Durée réelle** (travail effectif, à l'horloge de la session hors attentes machine, non chronométrée) : analyse 20 min, développement 50 min, tests 35 min, intégration et vérifications 55 min, **total 2 h 40** avant la clôture (+ 20 min de correction après la clôture passage 1 : **3 h 00**) contre 2 h estimées à l'origine (+ 50 %) et 2 h 50 en dernière révision. Écart > 30 % : périmètre élargi en cours de route (prévisions des tirs en vol, borne d'angle décidée après la première série, diagnostic des centres, tirs sortis de la borne après la revue). Temps machine hors total : deux séries de 50 matchs (36 et 35 min), trois séries de 8 matchs, deux suites complètes (14 min 41 s, 15 min 00 s), empreintes.

### 27/11/2026 — clôture (`/valider-ticket-simulafoot`, passage 1)

- Expert : `DEMANDE DE VÉRIFICATIONS` (pas de verdict) : la borne de 35 m/s appliquée aux tirs (`vz` réduit) peut faire passer sous la barre un tir de près tiré au-dessus (V1 : relevé sur 50 matchs ; V2 : tir de 3 m tiré à 3,0 m). V2 exécuté (test jetable hors dépôt, empreinte du dépôt inchangée) : avec la borne, `vz` 18,03 m/s, ligne à 1,75 m, **but** ; sans, `vz` 30,5 m/s, ligne à 3,0 m, au-dessus. Défaut confirmé.
- **Décision du propriétaire (27/11/2026)** : « Tirs hors borne » (les bornes ne s'appliquent qu'aux passes et relances aériennes ; les `vz` irréalistes des tirs tout près de la ligne, préexistants, à traiter à part). Corrigé (`hauteur.launch_vz_to` sans borne, test permanent ajouté) ; V1 répondu par la série 3 (issues identiques à la série tirs bornés).

### 27/11/2026 — clôture (`/valider-ticket-simulafoot`, passage 2)

- Expert : `APPROVED_WITH_RESERVATIONS` (empreinte `be481e8b…`). QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ`.
- A1 [réserve] : `meeting_point`, `occasion` et `possession.pass_velocity` lisent encore la loi au sol pour les ballons aériens ; condition : le `v2-collectif/22a` les aligne sur la loi en vol (`airborne=True`) avant de recalibrer les passes longues (test : point de rencontre prévu d'un ballon aérien égal à la trajectoire du moteur, à un pas près). **Acceptée par le propriétaire (27/11/2026)** : « J'accepte A1 ».
- A2 [facultatif] : `vz` irréalistes des tirs tout près de la ligne (jusqu'à 1 462 m/s, préexistant au 02a2) : réduire vh plutôt que vz, à traiter à part.
- A3 [facultatif] : docstring de `launch_vz` trop longue (`hauteur.py:89`). QC, non bloquant : commentaire de `hauteur.py` « sommet maximal 28,6 m » (série 1 recalculée) contre 29,7 m mesuré en série finale.

### 26/11/2026 — reprises

**26/11/2026, reprises du 14a2a (expert, facultatif)** : corriger les commentaires `match.py:1026` (« 60 m de course à 30 m/s », environ 77 m désormais) et `hauteur.py:27` (« freinage exponentiel ») ; passer `test_stepped_quantities_follow_the_engine_step` en tolérance absolue `abs=1e-9` ; garder en tête l'écart d'environ ½·dt·v0 entre prévision continue et moteur (A1) si la précision des points de chute compte.
