# 06b: Indicateurs : occasion, exécution, gardien, par attribut

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (permet de vérifier que chaque attribut agit au bon étage). **Catégorie :** mesure.

**Constat vérifié :** le banc rapporte une « qualité moyenne de l'occasion » qui inclut aujourd'hui Finishing et la note du gardien (`occasion_quality`) ; aucune décomposition.

**What to build:** Indicateurs : somme des xG neutres, gain d'exécution (xG après frappe moins xG neutre, tirs non contrés), gain du gardien (xG après frappe moins buts), par tranche de Finishing et de Long Shots, par Composure sous pression et par note du gardien. Définitions dans `docs/INDICATEURS_V2.md`.

**Attributs :** aucun

**Blocked by:** 06a (xG après frappe : la qualité d'exécution mesurée).

**Bloque :** 06c, 18a, 18e.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** données synthétiques : décomposition exacte
- **Statistiques (séries de matchs) :** 50 matchs : gain d'exécution croissant avec Finishing dans la surface et Long Shots dehors

## Acceptance criteria

- [ ] Indicateurs définis et ajoutés au banc
- [ ] Chaque attribut agit sur son étage seulement (Finishing et Long Shots sur l'exécution, gardien sur l'arrêt)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
