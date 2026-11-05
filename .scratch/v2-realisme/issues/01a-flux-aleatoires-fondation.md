# 01a: Flux aléatoires par sous-système : fondation, perception et décision

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (sans flux séparés, un écart entre deux profils n'est pas attribuable). **Catégorie :** mesure.

**Constat vérifié :** 45 tirages passent par le module `random` global dans 13 fichiers de `v2engine/` ; `docs/INDICATEURS_V2.md` (paragraphe « Attribution des écarts ») constate qu'un tirage de perception ajouté décale tous les matchs suivants et rend les comparaisons non attribuables.

**What to build:** Créer un registre de générateurs nommés (un `random.Random` par sous-système), tous dérivés de la graine du match par une clé stable (sha256 du nom du sous-système, jamais `hash()`). Migrer d'abord les tirages de perception et de décision (`decision.py`, `anticipation.py`, `offside.py` pour la lecture de la ligne). Ajouter un tirage dans un sous-système ne doit plus changer les tirages des autres.

**Hors de ce ticket :** migration des autres sous-systèmes (01b) ; D-V06 reste valable (module `random`, déterminisme assoupli).

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 01b.

**Status:** à faire

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

- [ ] Registre de flux nommés, graine dérivée par sha256 d'une clé stable
- [ ] Tirages de perception et de décision migrés ; test d'indépendance des flux
- [ ] Écart sur les indicateurs principaux (20 matchs) dans l'intervalle de confiance de la version précédente
- [ ] Règle inscrite dans `docs/TRD_V2.md` (décision D-V à numéroter) sans contredire D-V06
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
