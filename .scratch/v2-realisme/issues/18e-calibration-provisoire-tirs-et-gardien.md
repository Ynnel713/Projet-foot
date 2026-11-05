# 18e: Calibration provisoire 2 : tirs, conversion et gardien après les fondations P0

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le volume et la conversion des tirs doivent être plausibles avant les développements tactiques). **Catégorie :** validation.

**Constat vérifié :** mesure 28b : 37,6 tirs par équipe, conversion 5,7 %, 54,7 % des buts dans la surface ; les P0 changent la trajectoire du tir, l'arrêt et la décision (05, 03, 04).

**What to build:** Régler provisoirement, sur 500 matchs, les constantes du tir (exécution 35b, portée et réaction du gardien 05b, contre 05c) et de la valeur du tir dans la décision (05e), une fois le gardien placé (03), pour approcher tirs par équipe, cadrés, conversion et part des buts dans la surface. Règles d'une calibration provisoire (décision du propriétaire du 05/11/2026) : seules les constantes des mécanismes concernés bougent, dans leurs fourchettes validées ; chaque valeur est marquée « provisoire » dans le code et dans `docs/INDICATEURS_V2.md` avec la date et la mesure ; aucun réglage ne masque une lacune de mécanisme (un écart dû à un mécanisme absent devient un ticket) ; la calibration finale (`v2-collectif/22a` à `22c`) repart de ces valeurs et peut toutes les revoir.

**Hors de ce ticket :** calibration finale (`v2-collectif/22c`).

**Attributs :** aucun

**Blocked by:** 18d (Calibration provisoire 1 : volumes de course et rythme après les fondations P0); 05g (Validation des tirs : trajectoire, cadrage, contres, arrêts); 03g (Validation du placement et des sorties du gardien); 06b (Indicateurs : occasion, exécution, gardien, par attribut).

**Bloque :** `v2-collectif/22c`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : la position du gardien est validée (03g) avant de régler l'arrêt.
Temps machine, non compté : suite complète (environ 40 min) ; séries de 500 matchs.

## Tests

- **Statistiques (séries de matchs) :** 500 matchs avant / après : tirs, cadrés, contrés, conversion, buts dans la surface, xG neutre cumulé contre buts

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Chaque constante modifiée marquée « provisoire », avec date et mesure
- [ ] Gardien jamais réglé avant que son placement soit validé (03g)
- [ ] Écarts restants attribués (mécanisme ou calibration finale)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
