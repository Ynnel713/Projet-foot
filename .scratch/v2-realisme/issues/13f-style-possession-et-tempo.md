# 13f: Style Possession et tempo

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (passes sûres, tempo lent, récupération rapide). **Catégorie :** décision.

**Constat vérifié :** voir 13a ; le tempo (intervalle de décision `DECISION_INTERVAL_S`, temps de réception) est commun.

**What to build:** La consigne de possession pondère la perte plus fortement dans la valeur des options (même mécanisme que la transition, `decision._TRANSITION_WEIGHTS`), rallonge le temps avant de jouer quand le porteur n'est pas pressé (tempo) et réduit les ballons longs.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Possession.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre).

**Bloque :** 13i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : leviers existants seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** avec et sans Possession : passes par possession en hausse, passes longues en baisse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu (200 matchs appariés)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
