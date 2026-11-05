# 18b: Protocole de validation indépendante

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (éviter de valider sur les matchs qui ont servi à calibrer). **Catégorie :** validation.

**Constat vérifié :** calibration et contrôle utilisent la même graine d'audit (20260923) ; aucune série réservée.

**What to build:** Définir des graines réservées à la validation (jamais utilisées pour calibrer), la liste figée des critères et seuils avant la série, la taille (1 000 à 2 000 matchs) et la règle de décision (intervalle de confiance). Documenter dans `docs/INDICATEURS_V2.md`.

**Attributs :** aucun

**Blocked by:** 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance); 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 18c.

**Status:** à faire

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

- [ ] Protocole documenté et validé par le propriétaire
- [ ] Graines réservées protégées par le banc
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
