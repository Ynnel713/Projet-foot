# 17d: Test de garde : attribut annoncé branché = attribut lu avec effet

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (empêche de confondre un attribut lu et un attribut qui change le jeu). **Catégorie :** validation.

**Constat vérifié :** `tests/test_v2engine_rayon_attributs.py` vérifie les rayons ; aucun test ne vérifie qu'un attribut « branché » dans la carte est lu par le moteur et change l'issue d'une scène.

**What to build:** Test qui lit la carte, liste les attributs marqués branchés, vérifie qu'ils sont lus dans `v2engine/` et, pour chacun, joue une scène A/B (note 99 contre 11, fabrique du 01f) dont un indicateur doit différer.

**Attributs :** aucun

**Blocked by:** 17a (Carte des attributs : état réel de branchement); 01f (Fabrique de scènes de test partagée).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : une scène type par attribut, à écrire au fur et à mesure.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** attribut factice marqué branché mais jamais lu : le test échoue

## Acceptance criteria

- [ ] Test en place pour tous les attributs branchés
- [ ] Échec démontré sur un cas factice
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
