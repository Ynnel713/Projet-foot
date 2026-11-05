# 01b: Flux aléatoires : duels, passes, tirs, placement, arbitrage

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (termine l'isolation des tirages). **Catégorie :** mesure.

**Constat vérifié :** voir 01a : `duel.py`, `possession.py`, `shooting.py`, `bloc.py`, `defense.py`, `cerveau.py`, `match.py`, `restart.py`, `added_time.py`, `off_ball.py` tirent dans le flux global.

**What to build:** Migrer tous les tirages restants vers les flux nommés du 01a (duel, passe, tir, placement, rôles défensifs, arbitrage, remises en jeu). Ajouter un test qui interdit `random.random`, `random.uniform`, `random.gauss` et `random.choice` directs dans `v2engine/` (recherche dans le source).

**Attributs :** aucun

**Blocked by:** 01a (Flux aléatoires par sous-système : fondation, perception et décision).

**Bloque :** 01e.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : migration mécanique ; aucun changement de loi de probabilité.
Temps machine, non compté : suite complète (environ 40 min) ; mesure de contrôle sur 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** test de garde : aucun appel direct au module `random` dans `v2engine/`
- **Comportementaux (profils comparés) :** profil Aggression 99 contre 11 : le nombre de tirages consommés par le flux « tir » est indépendant du profil d'Aggression
- **Intégration :** déterminisme à graine fixée sur 2 matchs complets

## Acceptance criteria

- [x] Plus aucun tirage direct dans le flux global (test de garde `test_the_engine_never_draws_from_the_global_random_module` : seuls restent `random.Random` et la base du match, `match.py`)
- [x] Indicateurs principaux sur 20 matchs dans l'intervalle de confiance de la version 01a (9 indicateurs sur 9, tableau ci-dessous)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`test_two_full_matches_are_reproducible_at_fixed_seed`, marqueur `integration`, 2 matchs complets, réussi en 10 min 26)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 389 passés, 14 désélectionnés, contre 2 386 et 13 : 3 tests ajoutés, 1 test `integration`)

## Rapport d'implémentation (05/11/2026)

**Livré :** flux `DUEL`, `PASSE`, `TIR`, `PLACEMENT`, `DEFENSE`, `ARBITRAGE` dans `v2engine/flux.py`, semés comme ceux du 01a. Répartition des 37 appels de tirage migrés (9 fichiers, lois de tirage et arguments inchangés) :

| Flux | Tirages |
|---|---|
| duel | `duel.py` : tentative de tacle, issue, faute |
| passe | `possession.py` : contrôle, angle de la première touche, précision et dosage de la passe |
| tir | `shooting.py` (déclenchement, contre, arrêt, déviation et vitesse des arrêts) ; `match.py` : penalty, déviation, tir non cadré |
| placement | `bloc.py` : erreur de Positioning ; `off_ball.py` : appel en profondeur |
| défense | `defense.py` : suivi du contre-pressing, ligne de passe coupée, compensation, sortie du bloc ; `cerveau.py` : défenseur d'équilibre |
| arbitrage | `duel.py` : gravité de la faute ; `match.py` : tirage au sort du coup d'envoi |
| décision (01a) | `off_ball.py` : choix de l'espace ; `restart.py` : partenaire d'une remise en jeu (réserve A3 de l'expert au 01a) |
| perception (01a) | `match.py` : le défenseur voit le drapeau du hors-jeu (lecture, Anticipation) |

**Choix :** pas de flux « remises en jeu » : son seul tirage est un choix (Decisions), rangé dans le flux décision selon la réserve A3 du 01a. `added_time.py` garde son générateur local, semé par sha256 (ce n'est pas un tirage du module). La réserve A1 du 01a (flux globaux partagés entre threads de l'API) est inchangée : le module `random` l'était déjà avant le 01a ; à traiter si l'API doit rejouer des matchs simultanés de façon reproductible.

**Tests ajoutés ou adaptés :** nouveaux, dans `tests/test_v2engine_flux.py` : test de garde (recherche dans le source de `v2engine/`, imports renommés de `random` compris), profil Aggression 99 contre 11 (le flux « tir » et le module `random` ne bougent pas, le flux « duel » si), déterminisme sur 2 matchs complets (`integration`). Adaptés : 16 remplacements de tirage par `monkeypatch` redirigés vers le flux visé (cerveau, difficulté, possession, hors-ballon ; assertions inchangées). `test_v2engine_transition_defensive.py` : `random.seed(1)` remplacé par `seed_scene(1)` (les flux suivent la graine du test). `test_v2engine_compensations.py::test_cascade_stops_after_two_levels` : tirage de Teamwork forcé à « accepte », le test contrôle la structure de la cascade et échouait selon la graine (2 sur 4).

**Mesure avant/après (`scripts/measure_v2.py 20`, graine d'audit 20260923) :** avant = `b06b704`, après = arbre du ticket. Le banc ne publie pas les valeurs par match (01e) : l'IC 95 % de l'écart à 20 contre 20 est déduit de l'écart-type par match de la série de 80 matchs du 01a.

| Indicateur | Avant | Après | Écart [IC 95 %] |
|---|---|---|---|
| Tirs par équipe | 30,98 | 30,68 | −0,30 [−2,84 ; +2,24] |
| Buts par match | 3,85 | 4,05 | +0,20 [−1,15 ; +1,55] |
| Passes par minute | 10,77 | 10,96 | +0,19 [−0,25 ; +0,63] |
| Passes réussies | 67,1 % | 66,8 % | −0,3 pt [−1,6 ; +1,0] |
| Tacles par match | 33,40 | 31,70 | −1,70 [−5,61 ; +2,21] |
| Hors-jeu par match | 0,60 | 1,05 | +0,45 [−0,21 ; +1,11] |
| Tirs cadrés | 32,8 % | 31,3 % | −1,5 pt [−5,1 ; +2,1] |
| Fautes par match | 10,75 | 9,25 | −1,50 [−3,41 ; +0,41] |
| Temps de jeu effectif | 62,0 % | 62,8 % | +0,8 pt [−1,3 ; +3,0] |

Mesure refaite sur l'arbre corrigé après le passage 1 (première mesure, choix de l'espace encore dans PLACEMENT : 9 indicateurs sur 9 dans l'IC également, passes par minute +0,40 [−0,04 ; +0,84]). Toutes les traces changent une fois (attendu, D-V06). Aucun écart ne peut venir d'un mécanisme (mêmes lois, mêmes arguments) ; passes par minute et pertes de balle à revoir au 01e avec les valeurs par match (recommandation de l'expert).

**Tests :** réussis 2 389 (suite complète, relancée sur l'arbre corrigé : 2 389 passés, 14 désélectionnés) + 1 `integration` (relancé : réussi) ; échoués : aucun après correction des 2 tests dépendants de la graine ; non exécutés : autres tests `integration` (aucun fichier V1 ni protégé touché). À l'écran : rien de spécifique (le rejeu d'un match à graine donnée change une fois).

**Durée :** estimée 2 h 10 (130 min ; 20/50/30/30), réelle environ 2 h 10 (130 min ; 15/35/30/50). Écart 0 %. Migration mécanique par script ; intégration plus longue (2 tests dépendants de la graine, mesure sans valeurs par match, correction après le passage 1).

## Comments

- 05/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte 29f19fa3). Réserve A1 : le choix de l'espace (`off_ball.py:124,126`) était resté dans PLACEMENT (substitution par numéro de ligne décalée par l'import ajouté), alors que la docstring, ce rapport et la réserve A3 du 01a annoncent DECISION ; le test qui force « meilleur espace » ne forçait plus rien. Facultatifs : A2 compte des tirages (46 annoncés, 37 dans le diff), A3 test de garde aveugle aux imports renommés, A4 `docs/PLAN_V2.md` hors liste (suivi documentaire). QC REFUSÉ (mêmes constats : test sans effet, import mort, documentation en désaccord). Corrections : A1 (choix de l'espace dans DECISION, comme annoncé), A2 et A3 appliqués (recommandations de l'expert acceptées d'office par le propriétaire : « Tes recommandations et les conseils d'expert sont automatiquement validé »). Suite complète, test `integration` et mesure 20 matchs relancés sur l'arbre corrigé.
- 06/11/2026, passage 2 : expert APPROVED (empreinte ca8886f1), A1 du passage 1 corrigée. Facultatifs : `random.seed(...)` devenus décoratifs dans des tests V2 qui tirent dans les flux (`test_v2engine_compensations.py`, `test_v2engine_pressing.py`), à remplacer par `seed_scene` au fil des tickets ; `docs/PLAN_V2.md` suivi documentaire. À surveiller au 01e (valeurs par match) : passes par minute, pertes de balle, buts dans la surface, réussite des passes en profondeur. Toujours ouvert : réserve A1 du 01a (flux partagés entre threads de l'API). QC VALIDÉ. **Clôture VALIDÉ.**
