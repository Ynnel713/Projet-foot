# 13d: Style Offensif

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (plus de joueurs au-delà du ballon). **Catégorie :** décision.

**Constat vérifié :** voir 13a.

**What to build:** La consigne offensive augmente le nombre maximal d'appels simultanés (02g) et la projection des latéraux (02d), réduit la défense préventive au minimum validé ; contrepartie : exposition en transition.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Offensif.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 02g (Qui fait un appel, et quand); 09g (Défense préventive : un défenseur de plus que les attaquants restés haut).

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

Confiance : moyenne. Hypothèses : leviers existants seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** avec et sans Offensif : joueurs dans la surface adverse en hausse, tirs de contre concédés en hausse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu, avec sa contrepartie (200 matchs appariés)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
