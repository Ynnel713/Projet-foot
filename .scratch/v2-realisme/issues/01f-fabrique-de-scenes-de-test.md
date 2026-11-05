# 01f: Fabrique de scènes de test partagée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les tickets suivants reposent sur des scènes contrôlées comparables). **Catégorie :** mesure.

**Constat vérifié :** chaque fichier `tests/test_v2engine_*.py` construit ses propres `PlayerState` ; aucune aide commune pour placer 22 joueurs, fixer des attributs ou faire varier un seul attribut.

**What to build:** Une aide de test unique : placer des joueurs par poste et coordonnées, régler un attribut sur tous ou sur un seul joueur, faire tourner N pas de la boucle de match à partir de cette scène, et comparer deux profils sur la même scène avec la même graine (scène A/B). Migrer deux tests existants comme exemples, sans changer leurs assertions.

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** 01a, 01g, 02a, 03a, 04a, 07a, 10e, 11a, 12a, 13a, 17d.

**Status:** à faire

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

- [ ] Aide disponible dans `tests/`, documentée en tête de fichier
- [ ] Deux tests migrés, assertions inchangées
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
