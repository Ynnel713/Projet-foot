# 20c: Récupération pendant les arrêts de jeu et à la mi-temps

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (un arrêt ou la pause rendent un peu d'énergie, sans effacer la fatigue accumulée). **Catégorie :** physique.

**Constat vérifié :** aucune récupération : la fatigue dépend de la minute ; la mi-temps remet les positions à zéro sans toucher à la fatigue (`v2-coach-et-gestion-de-match/07`, point 6, laissé au ticket 12) ; 12e prévoit une recharge « au repos » sans traiter les arrêts de jeu ni la pause.

**What to build:** Recharge de la réserve pendant le ballon mort, selon la durée réelle de l'arrêt (blessure, VAR, remplacement, célébration, remise en jeu), et pendant la mi-temps (part proposée, sourcée ou « non trouvé »). La recharge plafonne sous un niveau qui baisse avec l'effort cumulé : la fatigue accumulée ne s'efface pas.

**Attributs :** Stamina (recharge, rayon de 12e : pas de second effet).

**Blocked by:** 12e.

**Bloque :** 20d ; `v2-coach-et-gestion-de-match/05a` ; `v2-collectif/22a` (par 20d).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : deux paramètres : recharge par seconde de ballon mort, part récupérée à la pause.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** réserve à 50 % à la pause : plus haute après, mais sous le niveau du coup d'envoi ; arrêt de 60 s : remontée partielle
- **Statistiques (séries de matchs) :** 50 matchs : course intense de la 46e à la 60e comparée à la 31e-45e

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Récupération mesurée en scène, plafonnée par l'effort cumulé
- [ ] Reprise de la 2e période visible dans les indicateurs par tranche (19d)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
