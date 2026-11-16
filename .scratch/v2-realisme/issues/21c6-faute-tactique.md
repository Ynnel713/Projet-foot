# 21c6: Faute tactique pour casser une transition

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** aucun joueur ne choisit de faire faute ; toutes les fautes sont des accidents de duel.

**What to build:** Sur une transition adverse dangereuse (danger du 28c), le joueur le plus proche du porteur peut choisir la faute (Decisions) ; jaune selon la gravité du 21b. Presque jamais dans sa surface (prudence du 21c1). Fréquence par Aggression inchangée.

**Attributs :** Decisions (choisir la faute ; prudence de surface, 21c1) ; Aggression inchangée.

**Blocked by:** 21c1, 21b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : le danger du 28c et la gravité du 21b sont disponibles.
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** contre-attaque à 3 contre 2 : faute tactique plus fréquente qu'en possession lente ; Decisions haute : plus de fautes tactiques choisies à bon escient
- **Statistiques :** 50 matchs : fautes tactiques et jaunes qui en découlent, par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Source tracée (« faute tactique »), jaune par le 21b
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md` ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
