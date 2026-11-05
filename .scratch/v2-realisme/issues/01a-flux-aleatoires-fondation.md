# 01a: Flux aléatoires par sous-système : fondation, perception et décision

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (sans flux séparés, un écart entre deux profils n'est pas attribuable). **Catégorie :** mesure.

**Constat vérifié :** 45 tirages passent par le module `random` global dans 13 fichiers de `v2engine/` ; `docs/INDICATEURS_V2.md` (paragraphe « Attribution des écarts ») constate qu'un tirage de perception ajouté décale tous les matchs suivants et rend les comparaisons non attribuables.

**What to build:** Créer un registre de générateurs nommés (un `random.Random` par sous-système), tous dérivés de la graine du match par une clé stable (sha256 du nom du sous-système, jamais `hash()`). Migrer d'abord les tirages de perception et de décision (`decision.py`, `anticipation.py`, `offside.py` pour la lecture de la ligne). Ajouter un tirage dans un sous-système ne doit plus changer les tirages des autres.

**Hors de ce ticket :** migration des autres sous-systèmes (01b) ; D-V06 reste valable (module `random`, déterminisme assoupli).

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 01b.

**Status:** livré (05/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : la graine du match est accessible à l'entrée de `simulate_match` ; les empreintes de tous les matchs changent une fois (attendu, à noter dans le rapport).
Temps machine, non compté : suite complète (environ 40 min) ; mesure de contrôle sur 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ajouter un tirage factice dans le flux « perception » ne change pas la suite des tirages du flux « duel » (comparaison de séquences)
- **Intégration :** deux exécutions à graine fixée donnent la même trace ; graine différente, trace différente
- **Statistiques (séries de matchs) :** 20 matchs avant / après : ordres de grandeur inchangés (tirs, buts, passes) à l'intervalle de confiance près

## Acceptance criteria

- [x] Registre de flux nommés, graine dérivée par sha256 d'une clé stable (`v2engine/flux.py`, `test_stream_seeds_come_from_sha256_of_a_stable_key`)
- [x] Tirages de perception et de décision migrés ; test d'indépendance des flux (`test_an_extra_perception_draw_does_not_shift_the_decision_stream`, `test_streams_and_the_random_module_do_not_shift_each_other`)
- [x] Écart sur les indicateurs principaux (20 matchs) dans l'intervalle de confiance de la version précédente : tirs, buts, passes dans l'IC à 20 matchs comme à 80 (détail au rapport)
- [x] Règle inscrite dans `docs/TRD_V2.md` (décision D-V à numéroter) sans contredire D-V06 : D-V13, marquée « proposé, à valider par le propriétaire » (D-V12 réservée au 28c)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`test_match_trace_is_reproducible_at_fixed_seed_and_changes_with_the_seed`, match de 1 min : même trace à graine égale, trace différente à graine différente)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 385 passés, 1 échec (`test_v2engine_mi_temps.py::test_half_time_resets_everyone_and_the_other_team_kicks_off`, corrigé puis relancé : 3 passés), 13 désélectionnés ; total 2 386 = 2 382 + 4 nouveaux tests

## Rapport (05/11/2026)

**Livré :** `v2engine/flux.py` (flux `PERCEPTION` et `DECISION`, `stream_seed`, `seed_streams`) ; `simulate_match` sème les flux au coup d'envoi avec un seul tirage du module `random` (`random.getrandbits(64)`). Migrés : perception (`decision.py` repérage de la passe clé et bruit de perception des options, `anticipation.py` lecture d'une passe, `offside.py` lecture de la ligne) ; décision (`decision.py` adoption du plan et choix contre-attaque ou conservation, `offside.py` respect de la ligne). Reste sur le module `random` jusqu'au 01b : `match.py:549` (le défenseur voit le drapeau), `cerveau.py` et tous les autres sous-systèmes.

**Choix :** le ticket supposait une graine du match accessible à l'entrée de `simulate_match` ; il n'y en a pas (les appelants sèment `random`). La base des flux est donc un tirage du module au coup d'envoi : `random.seed` reste la seule graine d'un match, sans changement d'API ni de banc (D-V06 intacte). Les objets de flux ne sont jamais remplacés (ressemés), pour que les imports et les `monkeypatch` restent valides.

**Tests ajoutés ou adaptés :** nouveaux : `tests/test_v2engine_flux.py` (4 tests). Adaptés : 9 remplacements de tirage par `monkeypatch` redirigés vers le flux visé (anticipation, cerveau, décision, combinaisons, valeur de passe ; assertions inchangées) ; fixture `tests/conftest.py` qui ressème les flux avant chaque test (indépendance de l'ordre) ; `tests/scenes.seed_scene` sème module et flux (utilisé par `ab` et le test de déterminisme de la fabrique) ; `test_v2engine_mi_temps.py` : graine 20260925 → 20260927, la première donnant désormais un corner à 0,72 qui prolonge la période (règle du ticket coach/03), assertions inchangées.

**Mesure avant/après (banc `scripts/measure_v2.py`, une ligne par match, moyenne et IC 95 %) :** avant = `d5a361f`, après = arbre du ticket. Toutes les traces changent une fois (attendu).

| Indicateur | Avant (80 matchs) | Après (80 matchs) | Écart [IC 95 %] |
|---|---|---|---|
| Tirs par équipe | 31,23 | 31,13 | −0,10 [−1,37 ; +1,17] |
| Buts par match | 4,39 | 4,21 | −0,18 [−0,85 ; +0,50] |
| Passes par minute | 11,02 | 10,94 | −0,08 [−0,30 ; +0,14] |
| Passes réussies | 67,0 % | 67,2 % | +0,2 pt [−0,4 ; +0,9] |
| Tacles par match | 33,43 | 32,35 | −1,08 [−3,03 ; +0,88] |
| Hors-jeu par match | 1,18 | 0,89 | −0,29 [−0,62 ; +0,04] |
| Tirs cadrés | 33,2 % | 33,0 % | −0,2 pt [−2,0 ; +1,6] |
| Fautes par match | 10,03 | 10,60 | +0,58 [−0,38 ; +1,53] |
| Temps de jeu effectif | 62,4 % | 62,3 % | −0,1 pt [−1,2 ; +0,9] |

Lecture : à 20 matchs, hors-jeu (1,40 → 0,60) et fautes (8,70 → 10,75) sortaient de l'IC. Contrôle A/A sur l'ancien code (graines 0-39 contre 40-79, mêmes 9 affiches) : fautes +2,15 et tacles +2,65 sans aucun changement de code, donc la variabilité entre jeux de graines dépasse ce que suppose le test. À 80 contre 80, aucun écart n'est significatif ; l'écart des hors-jeu décroît avec l'échantillon (−0,80, −0,43, −0,29) et aucun mécanisme ne peut le produire (mêmes lois de tirage, `uniform` et `random`, mêmes appels). Indicateurs principaux (tirs, buts, passes) dans l'IC à 20 comme à 80 matchs.

**Tests :** réussis 2 386 (suite complète 2 385 + test de mi-temps relancé) ; échoués : aucun après correction ; non exécutés : marqueur `integration` (aucun fichier V1 ni protégé touché). À l'écran : rien de spécifique (le rejeu d'un match à graine donnée change une fois).

**Durée :** estimée 2 h 15 (135 min ; 30/45/30/30), réelle environ 2 h 20 (140 min ; 30/30/30/50). Écart + 4 %. Intégration plus longue que prévu (contrôle A/A et 60 matchs de mesure supplémentaires pour trancher deux écarts du premier lot), développement plus court. Temps machine, non compté : 200 matchs de mesure et deux suites complètes.

## Comments

- 05/11/2026, passage 1 : expert APPROVED (empreinte bdb8a2a1). Facultatifs : A1 flux globaux partagés entre threads de l'API (pas de régression, à réexaminer au 01b si la reproductibilité de matchs simultanés est voulue) ; A2 test de mi-temps dépendant de sa graine ; A3 `restart.py:184` et `off_ball.py:124` à ranger dans le flux DECISION au 01b. QC VALIDÉ (non bloquant : hors-jeu à relire au 01b). **Clôture VALIDÉ.**
