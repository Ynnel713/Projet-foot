# 04c: Validation : risque annoncé, probabilité calculée, résultat observé

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (garantit que la décision et la résolution restent alignées). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur ne compare la chance de garder le ballon évaluée par le porteur à ce qui arrive ensuite.

**What to build:** Indicateur de calibration : pour chaque conduite, risque évalué au moment du choix et issue sur l'intervalle ; courbe par tranche de pression et par tranche de Dribbling. Rapport sur 50 matchs ; à refaire après 04e, 07 et 11.

**Attributs :** aucun

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution); 04b (Conduite : où va le ballon perdu); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 18a.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : lecture de la trace des décisions.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** courbe de calibration exacte sur données synthétiques
- **Statistiques (séries de matchs) :** 50 matchs : écart par tranche inférieur à 3 points

## Acceptance criteria

- [ ] Indicateur défini et ajouté au banc
- [ ] Écart risque évalué / observé sous 3 points par tranche de pression (50 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
