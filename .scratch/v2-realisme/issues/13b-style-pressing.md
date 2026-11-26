# 13b: Style Pressing

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (presser haut est le style le plus visible). **Catégorie :** décision.

**Constat vérifié :** voir 13a ; déclencheurs et hauteur du pressing communs à toutes les équipes (tickets 05, 08, 10).

**What to build:** La consigne de pressing avance la hauteur du bloc, abaisse le seuil des déclencheurs et allonge le contre-pressing ; contrepartie : intensité plus élevée (réserve d'énergie 12e) et espace dans le dos.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Pressing.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 13j (Arbitrage des styles par phase); 12e (Réserve d'énergie qui dépend de l'effort).

**Bloque :** 13i, 13k, 13l, 20e (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : leviers existants seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** même équipe avec et sans Pressing contre le même adversaire : récupérations dans le tiers adverse plus nombreuses, PPDA plus bas, joueurs engagés dans le contre-pressing plus nombreux, occasions concédées dans le dos plus nombreuses, distance parcourue à haute intensité plus grande

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu, avec sa contrepartie (200 matchs appariés, intervalle de confiance)
- [ ] Les quatre leviers agissent et sont tracés : hauteur de ligne, distance de déclenchement du presseur, nombre de joueurs qui suivent le pressing (`FOLLOW_M`, défenseurs gardés en couverture `REST_DEFENDERS` / 09g), durée du contre-pressing (`TRIGGER_S`)
- [ ] Combiné à Défensif (13j) : pressing déclenché seulement dans la zone déclencheur validée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Leviers précisés : en plus de la hauteur, du seuil et de la durée du contre-pressing, le style règle le **nombre de joueurs autorisés à suivre** le pressing collectif (rayon `FOLLOW_M` et nombre de défenseurs gardés derrière, ticket `v2-collectif/10`). Phase : sans ballon et transition défensive seulement (13j). Indicateur PPDA ajouté par 13i. Estimation portée de 1 h 50 à 2 h (un levier de plus).
