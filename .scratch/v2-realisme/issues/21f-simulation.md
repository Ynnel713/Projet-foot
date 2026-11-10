# 21f: Simulation : tomber sans faute

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P2 (l'arbitre peut se tromper dans les deux sens). **Catégorie :** arbitrage.

**Constat vérifié :** aucune simulation dans `v2engine/` ni dans les tickets V2 (recherche du 10/11/2026).

**What to build:** Un attaquant au contact léger dans la surface peut tomber sans faute. L'arbitre (21a) décide : penalty à tort, jaune pour simulation ou rien. Attribut ou geste préféré à proposer (aucune colonne de la base ne porte la simulation : à vérifier dans les 58 gestes) ; sinon constante unique.

**Attributs :** à proposer (voir ci-dessus).

**Blocked by:** 21a, `v2-attributs-restants/09a`.

**Bloque :** 21g (cas du penalty à tort).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : faible. Hypothèses : événement rare, fréquence réelle probablement non publiée.
Temps machine, non compté : suite complète (environ 40 min) ; 200 matchs.

## Tests

- **Unitaires (scène contrôlée) :** contact léger dans la surface : chute possible, trois décisions possibles selon la vue de l'arbitre

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Simulation tracée (fait) et décision tracée
- [ ] Fréquence rapportée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
