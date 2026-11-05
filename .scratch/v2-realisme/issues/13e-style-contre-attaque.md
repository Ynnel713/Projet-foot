# 13e: Style Contre-attaque

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (récupérer bas puis jouer vite vers l'avant). **Catégorie :** décision.

**Constat vérifié :** voir 13a ; le choix contre-attaque / conservation est le même pour toutes les équipes (`decision.choose_transition`).

**What to build:** La consigne de contre-attaque biaise le choix de transition vers la contre-attaque, garde un attaquant haut (09f) et un bloc médian.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Contre attaque.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 09f (Un attaquant reste haut quand l'équipe défend).

**Bloque :** 13i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : biais du choix, pas obligation (Decisions garde son rôle).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** avec et sans Contre-attaque : part des passes vers l'avant après récupération en hausse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu (200 matchs appariés)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
