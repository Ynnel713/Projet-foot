# 18b: Protocole de validation indépendante

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (éviter de valider sur les matchs qui ont servi à calibrer). **Catégorie :** validation.

**Constat vérifié :** calibration et contrôle utilisent la même graine d'audit (20260923) ; aucune série réservée.

**What to build:** Définir des graines réservées à la validation (jamais utilisées pour calibrer), la liste figée des critères et seuils avant la série, la taille (1 000 à 2 000 matchs) et la règle de décision (intervalle de confiance). Documenter dans `docs/INDICATEURS_V2.md`.

**Attributs :** aucun

**Blocked by:** 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance); 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 18c.

**Status:** livré (14/11/2026), validé expert + QC (commit `79c944e`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : documentation et petite option du banc.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** le banc refuse une graine réservée en mode calibration

## Acceptance criteria

- [x] Protocole documenté et validé par le propriétaire (« Je valide », 14/11/2026 ; `docs/INDICATEURS_V2.md` section 41)
- [x] Graines réservées protégées par le banc (`scripts/graines_validation.py`, appelée par `measure_v2.run` et `bench_series.run_series`, option `--validation` ; `tests/test_graines_validation.py`)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : 55 min pour 90 estimées (− 39 %), voir le registre
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (match réservé 100 000 joué deux fois en validation, test ; séries existantes inchangées : empreintes `b19f5278` (graines 0-1) et `30f57f1f` (50-51), 2 matchs de 5 min, identiques avant et après)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 996 passés, 0 ignoré, 14 désélectionnés (2 982 attendus + 14 tests ajoutés), 11 min 03 ; aucun fichier V1 ni protégé touché

## Comments

**14/11/2026, protocole proposé et validé par le propriétaire** (« Je valide ») : graines réservées à partir de l'indice 100 000 par blocs de 2 000 (un bloc par passage, jamais réutilisé ; réserve étendue à 50 blocs, 100 000 à 199 999, pour les passages après correction) ; 1 000 matchs, portés à 2 000 pour les indicateurs à cheval sur une borne ; critères R1 à R7 (section 6, définitions du 01d) plus les cibles de la calibration finale inscrites avant le lancement ; règle conforme / à confirmer / écart sur l'IC 95 % ; moteur figé sur un commit cité, série lancée une fois. Garde placée dans un module à part (`scripts/graines_validation.py`) pour limiter le conflit avec le ticket 24, mené en parallèle, qui modifie aussi `scripts/measure_v2.py` (option `--niveaux`).
