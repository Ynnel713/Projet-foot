# 03h: Gardien : expliquer la hausse des tirs du 03c et le saut de cible

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une hausse de buts non expliquée fausse le point d'étape 18a). **Catégorie :** validation.

**Constat vérifié :** au 03c, la chance moyenne des tirs est passée de 0,061 à 0,081 et les buts de 2,75 à 3,60 par match, alors que sur une scène statique un gardien avancé la fait baisser (tir de 20 m axial : 0,055 → 0,049). La cause n'est pas établie (réserve A1 du 03c). Le gardien saute aussi de 5 à 11 m environ entre la ligne de but et la profondeur visée quand le ballon passe de 12 à 40 m (réserve A3 du 03c, reprise du A1 du 03b).

**What to build:** Décomposer la hausse sur 50 à 100 matchs : chance des tirs avec la position réelle du gardien, puis recalculée avec le gardien posé sur la bissectrice, puis mélange de tirs (distances, angles) à position égale. Mesurer le saut de cible (distance à sa ligne en fonction de la distance du ballon, 12 à 40 m) et dire s'il est trop brutal pour le rendu. Aucune constante recalée dans ce ticket : le rapport propose, le propriétaire tranche.

**Attributs :** aucun

**Blocked by:** 03g (Validation du placement et des sorties du gardien).

**Bloque :** 18a, 18e.

**Status:** à faire (créé le 07/11/2026, découpé du 03g)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (observateurs de décomposition) | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications (rapport) | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : séries appariées sur la graine d'audit, outils de `bench_series.py` (comparaison appariée).
Temps machine, non compté : suite complète (environ 40 min) ; séries de 50 à 100 matchs.

## Tests

- **Unitaires (scène contrôlée) :** décomposition sur des tirs synthétiques à résultat connu
- **Statistiques (séries de matchs) :** 50 à 100 matchs, rapport dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Constantes de mesure proposées avant le code
- [ ] La hausse de 0,061 à 0,081 est répartie entre position du gardien, mélange de tirs et reste, avec intervalles de confiance
- [ ] Le saut de cible est chiffré et une correction est proposée si nécessaire (pas appliquée ici)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
