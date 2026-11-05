# 06a: xG après frappe : la qualité d'exécution mesurée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (sépare l'occasion, l'exécution et le gardien). **Catégorie :** mesure.

**Constat vérifié :** le ticket `v2-collectif/28c` (à faire) crée l'xG neutre (`occasion_xg`, étape 0) ; rien ne mesure la qualité de la frappe une fois partie (point d'arrivée, vitesse).

**What to build:** Pour chaque tir non contré, calculer un xG après frappe : chance qu'un gardien moyen, placé où est le vrai gardien, n'arrête pas un ballon arrivant à ce point à cette vitesse (même modèle que 05b, gardien neutre). Tracer xG neutre, xG après frappe et issue sur chaque tir.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/28c` (étape 0) sans le modifier.

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); `v2-collectif/28c`.

**Bloque :** 05e, 06b.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le modèle d'arrêt neutre de 05b est réutilisable sans tirage.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir en pleine lucarne : xG après frappe proche de 1 ; tir sur le gardien : proche de 0 ; tir non cadré : 0
- **Comportementaux (profils comparés) :** Finishing 99 contre 11, mêmes positions : xG neutre identique, xG après frappe plus élevé

## Acceptance criteria

- [ ] Trois valeurs tracées par tir
- [ ] xG neutre indépendant du tireur (test)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
