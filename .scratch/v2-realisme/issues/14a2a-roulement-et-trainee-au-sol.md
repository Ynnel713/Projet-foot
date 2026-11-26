# 14a2a: Freinage du ballon : roulement et traînée quadratique avec crise de traînée (même loi partout)

**Découpé du ticket 14a2 le 26/11/2026** (décision du propriétaire : « 14a2a introduit la vraie physique (traînée + roulement) : c'est le changement de gameplay majeur, on le mesure seul sur 50 matchs. Les prédicteurs (meeting_point, pass_aim) doivent être alignés sur cette nouvelle loi dans le même ticket, sinon l'IA va mal évaluer toutes ses passes. »). Constantes, sources et contexte : `14a2-roulement-et-trainee.md`. Le vol (loi sans roulement en l'air, `MAX_FLIGHT_S`, borne de la vitesse de frappe) est au `14a2b`.

**Chantier :** `v2-realisme`. **Catégorie :** physique (changement de jeu voulu).

**What to build:** dans `v2engine/freinage.py` seulement (interface du `14a1`), remplacer le freinage exponentiel par `dv/dt = −(a_roul + k(v)·v²)`, avec `k = ½·ρ·Cd·A / m`, `Cd` = 0,45 sous 15 m/s et 0,25 dès 15 m/s, la même loi au sol et en l'air (provisoire jusqu'au 14a2b). Solutions exactes par morceaux (`v(t) = w·tan(atan(v0/w) − c·t)`, `w = √(a/k)`, `c = √(a·k)` ; distance entre deux vitesses `ln((a + k·v0²)/(a + k·v1²)) / 2k`). Le ballon s'arrête en un temps fini.
- **Pas du moteur** : vitesse sur le pas par la solution exacte (pas d'Euler sur la vitesse), position toujours `x += v·dt` ; les lectures « au pas du moteur » (`distance_after`, `travel_time_s` avec `dt`) suivent cette boucle exactement (cumul des pas, interpolation linéaire dans le pas, comme `restart.exit_point`) ; `shot_travel_time_s` fusionné dans `travel_time_s` (recommandation de l'expert du 14a1).
- **Prédicteurs alignés** : `meeting_point` cherche jusqu'à l'arrêt réel du ballon (et non plus jusqu'à 4 s, horizon calé sur l'ancienne loi) ; `pass_aim`, `_launch_speed`, `max_pass_reach_m`, `occasion`, `gardien`, `shooting` passent déjà par l'interface.
- **Tests** : ceux qui recalculent la loi exponentielle à la main passent par l'interface (réserve facultative A1 du 14a1).

**Constantes** : celles du `14a2` (validées le 26/11/2026) : roulement 1,2 m/s², ρ 1,225 kg/m³, rayon 0,11 m, masse 0,43 kg, Cd 0,45 / 0,25, palier à 15 m/s. Aucune nouvelle.

**Blocked by:** 14a1 (livré). **Bloque :** 14a2b.

**Status:** livré (26/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications (50 matchs, tolérance) | 40 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : les sites passent tous par l'interface (14a1) ; les lectures au pas du moteur deviennent des boucles (cache pour la vitesse fixe des tirs) sans coût notable. Temps machine, non compté : séries de 50 matchs avant et après (environ 50 min chacune), suite complète.

## Acceptance criteria (posés avant le code, 26/11/2026)

- [x] Loi changée dans `freinage.py` seulement ; tests de cohérence du 14a1 verts sans modification de leurs assertions (seul le test de la loi exponentielle est remplacé)
- [x] Valeurs de la loi (tests, calcul analytique) : décélération 9,66 m/s² à 25 m/s (9,64 d'abord posé avec `k` arrondi à 0,0135 ; valeur exacte `k` = 0,013537, corrigée avant le code des tests) et 3,64 m/s² à 10 m/s (± 0,01) ; passe au sol partie à 15 m/s : arrêt à 35,1 ± 0,2 m ; portée d'une passe frappée à 30 m/s jusqu'à 0,5 m/s : 77,6 ± 0,3 m (57,8 aujourd'hui) ; passe de 20 m arrivant à 6 m/s : départ à 13,3 ± 0,1 m/s (16,2 aujourd'hui)
- [x] Encadrement par la source du roulement : passe de 20 m, temps de trajet et vitesse d'arrivée entre ceux d'un roulement à 1,0 et à 1,5 m/s² (bande FIFA du 14a2)
- [x] Lectures au pas du moteur égales à la boucle de `match._step_ball` (écart < 1e-9 m) ; aucune vitesse négative ; ballon arrêté en temps fini
- [x] `meeting_point` trouve un point sur toute la trajectoire jusqu'à l'arrêt (test : receveur atteignable seulement après 4 s)
- [x] 50 matchs avant/après (graines 0 à 49, `scripts.bench_series`) : passes, interceptions, contrôles ratés, tirs, buts ; écarts au-delà du bruit (séries de référence A/B du 02a1) documentés et soumis au propriétaire ; temps de calcul par match ≤ + 15 %
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite complète au compte attendu (3 573 + tests ajoutés), 0 échec ; V1 inchangée
- [x] Durée réelle relevée (rapport et `docs/agents/suivi-estimations.md`)

## Comments

### 26/11/2026 — implémentation

- **Code** : `v2engine/freinage.py` réécrit (même interface que le 14a1, plus `deceleration`) : loi `dv/dt = −(a + k(v)·v²)` par morceaux exacts (morceau sur-critique jusqu'à 15 m/s, puis sous-critique), arrêt en temps fini ; pas du moteur par la vitesse exacte en fin de pas ; lectures au pas par la boucle du moteur (`_stepped_path`, en cache : les tirs partent tous à 30 m/s), interpolation linéaire dans le pas ; `shot_travel_time_s` supprimé, `shooting._flight_time_s` lit `travel_time_s` au pas. `anticipation.meeting_point` cherche jusqu'à l'arrêt réel (`time_to_slow(v, 0)`) au lieu de 4 s. Commentaires calés sur l'ancienne loi corrigés (`possession` : portée 77,5 m, plafond de vitesse dès ~66 m ; `match` : commentaire orphelin de la loi exponentielle retiré).
- **Valeurs** (calcul analytique, tests) : décélération 9,66 m/s² à 25 m/s, 3,64 à 10 m/s ; arrêt d'une passe à 15 m/s : 35,2 m (29 m avant) ; portée à 30 m/s jusqu'à 0,5 m/s : 77,5 m (57,8 avant) ; passe de 20 m arrivant à 6 m/s : départ à 13,3 m/s (16,2 avant) ; passe de 20 m partie à 14 m/s : 2,06 s, arrivée à 6,58 m/s, entre les valeurs à 1,0 et 1,5 m/s² de roulement ; ballon à 30 m/s arrêté en 8,6 s.
- **Tests** : `test_v2engine_freinage.py` (36 : le test de la loi exponentielle est remplacé par 6 tests de la nouvelle loi, dont une comparaison à une intégration fine au pas de 0,1 ms ; le test des inverses ne prend plus que les instants avant l'arrêt, assertions inchangées) ; `test_v2engine_receveur.py` (+1 : point de rencontre trouvé après 4 s) ; réserve A1 du 14a1 traitée : 5 fichiers de tests ne recalculent plus la loi à la main (`speed_after`, `distance_after`, `distance_to_slow`, `arrival_speed`, `launch_speed`, `step_velocity`) ; `test_vol_plafonne` passe de 56,3 à 70 m (à 56,3 m le vol ne dépasse plus `MAX_FLIGHT_S`) ; portée attendue 57,8 → 77,5 m (`test_v2engine_relance_longue`).
- **Suite complète** : 3 585 passés (3 573 + 12), 0 échec, 0 ignoré, 14 désélectionnés (15 min 27 s).
- **Série de 50 matchs** (graines 0 à 49, `scripts.bench_series 50`) : avant = `c9b5c19` rejoué dans un arbre séparé (`.scratch/v2-realisme/mesures/14a2a-avant.json`), après = code du ticket (`14a2a-apres.json`) ; bruit = séries de référence A/B du 02a1 (`14a2a-tolerance.py`, `14a2a-tolerance.txt`, `14a2a-ecarts.txt`). Sur les 2 817 indicateurs comparables : 11,5 % hors bruit (3,2 % entre les deux séries de référence). Sur les 927 sans tranches, quartiles ni effectifs : 156 hors bruit. Effet de passes plus lentes à distance égale : contrôles « ballon dur > 12 m/s » 10,7 % → 6,7 % (6,9×), passes réussies 84,1 % → 82,3 % (4,0×), passes chez l'adversaire 14,8 % → 16,7 % (4,5×), pertes de balle par match 259 → 278 (2,7×), pertes en transition 39,5 → 48,1 par match, possession d'équipe 22,0 → 20,5 s (2,6×), passes par possession 5,08 → 4,74, joueurs à moins de 10 m du ballon 4,51 → 4,73 (4,4×), épisodes de ballon libre disputés 535 → 491 par match, passes longues réussies 70,4 % → 66,9 % (1,2×). Dans le bruit : buts 4,36 → 4,22 par match, tirs 13,95 → 13,26 par équipe, passes par match 1 344 → 1 343, tacles, corners, hors-jeu. Temps de calcul : 158 → 156 s par match (critère ≤ + 15 % tenu).
- **Décision du propriétaire (26/11/2026)** sur ces écarts : « Accepter, clôturer » (effet attendu ; 82 % de passes réussies reste dans la fourchette des grands championnats ; calibration au `v2-collectif/22a`).
- **Déterminisme** : matchs complets, graines 0 et 1, deux exécutions : mêmes empreintes (`46d984aa35607499`, `7b4336c27a88b4e7` ; `14a2a-empreintes-1.txt`, `-2.txt`).
- **À vérifier à l'écran** (non fait) : passes visiblement plus lentes et ballon qui s'arrête net en fin de roulement (arrêt en temps fini, plus de lente glissade).
- **Durée réelle** (travail effectif, à l'horloge de la session hors attentes machine, non chronométrée) : analyse 20 min, développement 45 min, tests 45 min, intégration et vérifications 50 min, **total 2 h 40** contre 2 h 15 estimées (+ 19 %). Temps machine hors total : deux séries de 50 matchs (45 et 47 min), suite complète (15 min 27 s), empreintes.

### 26/11/2026 — clôture (`/valider-ticket-simulafoot`, passage 1)

- Expert : `APPROVED` (empreinte `083af5b0…`). QC : `VALIDÉ` (réserve non bloquante : durée réelle à reporter, faite ci-dessus). Clôture journalisée : `VALIDÉ`.
- A1 [facultatif] : le moteur avance de `v·dt` avec la vitesse de début de pas : sa course dépasse la prévision continue d'environ ½·dt·v0 (1,5 m depuis 30 m/s) ; `stop_position`, `meeting_point`, `max_pass_reach_m`. Préexistant (même écart avec l'ancienne loi).
- A2 [facultatif] : commentaires sur l'ancienne loi, `match.py:1026` (« 60 m de course à 30 m/s ») et `hauteur.py:27` (« freinage exponentiel ») : au 14a2b.
- A3 [facultatif] : `test_stepped_quantities_follow_the_engine_step` compare en relatif (`rel=1e-9`) et non en absolu (`abs=1e-9` m) comme le critère ; écart réel nul (mêmes opérations).
