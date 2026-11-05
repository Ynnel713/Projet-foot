# 13b: Style Pressing

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (presser haut est le style le plus visible). **Catégorie :** décision.

**Constat vérifié :** voir 13a ; déclencheurs et hauteur du pressing communs à toutes les équipes (tickets 05, 08, 10).

**What to build:** La consigne de pressing avance la hauteur du bloc, abaisse le seuil des déclencheurs et allonge le contre-pressing ; contrepartie : intensité plus élevée (réserve d'énergie 12e) et espace dans le dos.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Pressing.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 12e (Réserve d'énergie qui dépend de l'effort).

**Bloque :** 13i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : leviers existants seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** même équipe avec et sans Pressing contre le même adversaire : récupérations dans le tiers adverse plus nombreuses, occasions concédées dans le dos plus nombreuses

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu, avec sa contrepartie (200 matchs appariés, intervalle de confiance)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
