# 10h: Défendre le centre en retrait

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le retrait est la passe décisive la plus dangereuse). **Catégorie :** placement.

**Constat vérifié :** voir 10f ; aucune zone en retrait.

**What to build:** Quand le porteur adverse atteint la ligne de but dans la surface ou près d'elle, un milieu revenu ou le défenseur de la zone de retrait (10f) ferme le point de penalty et l'arc ; il ne recule pas sur la ligne avec les autres.

**Attributs :** aucun

**Blocked by:** 10f (Défense de la surface : premier poteau, second poteau, point de penalty, retrait).

**Bloque :** 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : déclencheur : porteur à moins d'une distance validée de la ligne de but.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur au bord du petit rectangle : un défenseur au point de penalty
- **Statistiques (séries de matchs) :** 50 matchs : buts sur passe en retrait

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Zone de retrait tenue (scène)
- [ ] Buts sur retrait rapportés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
