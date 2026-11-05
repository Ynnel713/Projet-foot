# 04b: Conduite : où va le ballon perdu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une perte de conduite n'est pas toujours une dépossession propre). **Catégorie :** exécution.

**Constat vérifié :** aujourd'hui une perte en conduite n'existe que par tacle gagné : le ballon passe directement au tacleur (`match.py`, branche `result.won`).

**What to build:** Une perte de conduite du 04a donne, selon la situation : dépossession par l'adversaire au contact, ou ballon libre devant le porteur (touche trop longue) à une distance et un angle tirés dans des bornes validées. Le ballon libre est disputé normalement (`BALLON_LIBRE`).

**Attributs :** aucun

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution).

**Bloque :** 04c.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : partage dépossession / touche trop longue selon la pression : valeur proposée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** perte sans adversaire au contact : jamais une dépossession ; au contact : les deux issues possibles

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Deux issues tracées
- [ ] Part de chaque issue rapportée sur 20 matchs
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
