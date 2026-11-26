# 13d: Style Offensif

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (plus de joueurs au-delà du ballon). **Catégorie :** décision.

**Constat vérifié :** voir 13a.

**What to build:** La consigne offensive augmente le nombre maximal d'appels simultanés (02g) et la projection des latéraux (02d), réduit la défense préventive au minimum validé ; contrepartie : exposition en transition.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Offensif.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 13j (Arbitrage des styles par phase); 02g (Qui fait un appel, et quand); 09g (Défense préventive : un défenseur de plus que les attaquants restés haut).

**Bloque :** 13i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : leviers existants seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** avec et sans Offensif : joueurs dans les 30 derniers mètres et dans la surface adverse (sur centre et en attaque placée) en hausse, passes clés, dribbles tentés et tirs dans le dernier tiers en hausse, tirs de contre concédés en hausse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu, avec sa contrepartie (200 matchs appariés)
- [ ] Leviers tracés : joueurs projetés (appels simultanés, latéraux), occupation de la surface sur les centres, prise de risque dans le dernier tiers (seuil de la passe clé, du dribble et du tir), liberté des créateurs (écart toléré à la place du bloc pour les rôles créatifs)
- [ ] Anti double comptage : le style décale un seuil d'équipe ; Flair et Decisions gardent leur rayon individuel (`docs/CARTE_ATTRIBUTS_V2.md`)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Leviers ajoutés : **occupation de la surface sur les centres**, **prise de risque dans le dernier tiers** (passes clés, dribbles, frappes) et **liberté des créateurs**. Phase : avec ballon seulement (13j). Estimation portée de 1 h 35 à 2 h.
