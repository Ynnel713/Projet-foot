# 01f: Fabrique de scènes de test partagée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les tickets suivants reposent sur des scènes contrôlées comparables). **Catégorie :** mesure.

**Constat vérifié :** chaque fichier `tests/test_v2engine_*.py` construit ses propres `PlayerState` ; aucune aide commune pour placer 22 joueurs, fixer des attributs ou faire varier un seul attribut.

**What to build:** Une aide de test unique : placer des joueurs par poste et coordonnées, régler un attribut sur tous ou sur un seul joueur, faire tourner N pas de la boucle de match à partir de cette scène, et comparer deux profils sur la même scène avec la même graine (scène A/B). Migrer deux tests existants comme exemples, sans changer leurs assertions.

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** 01a, 01g, 02a, 03a, 04a, 07a, 10e, 11a, 12a, 13a, 17d.

**Status:** livré (05/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : aide de test seulement, aucun code moteur.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** la scène A/B rejoue exactement la même suite quand les deux profils sont identiques

## Acceptance criteria

- [x] Aide disponible dans `tests/`, documentée en tête de fichier (`tests/scenes.py`)
- [x] Deux tests migrés, assertions inchangées : `test_v2engine_pressing.py::test_coordinated_press_does_not_make_recoveries_automatic` (boucle par `Scene` et `run` : 7 récupérations sur 30 graines avant comme après) et `test_v2engine_duel.py::test_higher_tackling_strength_balance_favor_the_tackler` (`player`, `with_attribute`)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`test_full_scene_is_deterministic_at_fixed_seed`) ; profils identiques, même suite de 100 empreintes (`test_identical_profiles_replay_the_same_sequence`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 382 passés, 13 désélectionnés (05/11/2026, après les corrections du passage 1). L'attendu de `CLAUDE.md` (2 281, 02/11) est périmé ; l'arbre sans ce ticket collecte 2 374 tests, + 8 nouveaux = 2 382

## Rapport (05/11/2026)

**Livré :** `tests/scenes.py` (`player`, `with_attribute`, `Scene` et `Scene.full`, `run` avec arrêt `until`, `fingerprint`, `ab`) ; `tests/test_scenes.py` (8 tests, dont 3 ajoutés après le passage 1 de l'expert) ; deux tests migrés. Aucun fichier de `v2engine/`, de la V1 ni fichier protégé modifié.

**Choix :**
- `run` reprend l'ordre des mises à jour de `match.simulate_match` (situation, transition, bloc, défense, joueurs, collisions, ballon). Un composant à `None` n'est pas mis à jour, ce qui reproduit les scènes réduites des tests existants. Limite connue, signalée dans le code : copie de la boucle, sans période, temps additionnel ni trace, à aligner si l'ordre du match change.
- L'instant d'un pas vaut `départ + k × dt`, comme dans le match (pas de cumul d'arrondis) : condition de la migration exacte du test de pressing.
- `ab` règle le profil B **avant** de construire la scène, pour que bloc et délais de réaction lisent la note modifiée (Anticipation par exemple).
- Générateur aléatoire : module `random` (D-V06), semé par `ab` ; à basculer sur les flux par sous-système au ticket 01a.

**Tests :** réussis : 8 nouveaux, 31 dans les trois fichiers touchés, suite complète 2 382 (passage 1 : 5 nouveaux, 28, 2 379). Échoués : aucun. Non exécutés : marqueur `integration` (aucun fichier concerné). À l'écran : rien (aide de test).

**Corrections après le passage 1 de l'expert (REJECTED) :**
- A1 : Pace, Acceleration et Stamina sont lus par le moteur dans des champs dédiés de `PlayerState`, pas dans `attributes`. `player` et `with_attribute` règlent désormais aussi ces champs (`DEDICATED_FIELDS`). Tests : `test_player_sets_the_dedicated_fields`, `test_pace_changes_the_game_in_an_ab_scene` (Pace 99 contre 60 : le joueur arrive plus près du ballon en 2 s).
- A2 : `run` passe `transition.mode` à `_step_ball`, comme `simulate_match`. A3 : l'équipe qui vient de marquer est rendue au suivi de situation au pas suivant. Test d'alignement : `test_run_passes_the_match_arguments`.
- A4 : `with_attribute` copie le dictionnaire `attributes` (copies indépendantes, testé).
- Test de pressing migré toujours à 7 récupérations sur 30 (sans transition, mode None comme avant).

**Durée :** estimée 1 h 50 (110 min ; 20/50/30/10), réelle 1 h 10 (70 min ; 15/20/20/15, dont 20 min de corrections après le passage 1 de l'expert : 10 de développement, 10 de tests). Écart − 36 % : la boucle à reproduire existait déjà dans le test de pressing et le périmètre est resté une aide de test, sans scène de 22 joueurs imposée ; développement surestimé. Chiffres identiques à la ligne du registre `docs/agents/suivi-estimations.md`.

## Comments

- 05/11/2026, passage 1 : expert REJECTED (A1 Pace, Acceleration et Stamina réglés sans effet, lus dans des champs dédiés ; A2 `transition.mode` non transmis par `run` ; réserve A3 but non rendu au suivi de situation ; facultatif A4 copie superficielle). QC VALIDÉ. Clôture REFUSÉ. Les quatre points corrigés et testés.
- 05/11/2026, passage 2 : expert APPROVED (empreinte 2a9c7edd ; facultatif : décompte du ticket périmé, corrigé). QC REFUSÉ (décompte de tests périmé dans le ticket), puis REFUSÉ au passage 3 (durée du ticket incohérente avec le registre), corrigés ; QC VALIDÉ au passage 4 (réserve non bloquante : attendu de `CLAUDE.md` périmé, décision du propriétaire). **Clôture VALIDÉ.**
