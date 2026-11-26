# 13e: Style Contre-attaque

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (récupérer bas puis jouer vite vers l'avant). **Catégorie :** décision.

**Constat vérifié :** voir 13a ; le choix contre-attaque / conservation est le même pour toutes les équipes (`decision.choose_transition`).

**What to build:** La consigne de contre-attaque biaise le choix de transition vers la contre-attaque, garde un attaquant haut (09f) et un bloc médian.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Contre attaque.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 13j (Arbitrage des styles par phase); 09f (Un attaquant reste haut quand l'équipe défend).

**Bloque :** 13i, 13k, 13l.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : biais du choix, pas obligation (Decisions garde son rôle).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** avec et sans Contre-attaque : part des passes vers l'avant après récupération en hausse, vitesse de progression verticale dans les 10 s après récupération (m/s) en hausse, délai avant le premier appel en profondeur en baisse, part des tirs issus d'une transition rapide en hausse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu (200 matchs appariés)
- [ ] Leviers tracés : biais du choix de transition, vitesse de projection des attaquants et ailiers dès la récupération (intensité des appels en transition, sans toucher au plafond de vitesse de l'attribut), poids des passes dans le dos de la défense face aux passes latérales ou en retrait, prise de risque à la transition
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Leviers ajoutés : **vitesse de projection** des attaquants et ailiers dès la récupération (intensité de course des appels, ticket 12d, pas la vitesse maximale qui reste à Pace et à la réserve), **poids des passes longues et verticales dans le dos** contre les passes latérales ou en retrait, **prise de risque** à la transition. Phase : transition offensive et, à moindre dose, avec ballon (13j). Estimation portée de 1 h 35 à 2 h.
