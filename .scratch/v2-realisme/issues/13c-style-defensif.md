# 13c: Style Défensif

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (bloc bas et compact). **Catégorie :** décision.

**Constat vérifié :** voir 13a.

**What to build:** La consigne défensive abaisse la hauteur du bloc, réduit les joueurs projetés (02g) et renforce la défense préventive (09g) ; contrepartie : moins de tirs.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Défensif.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 13j (Arbitrage des styles par phase); 02g (Qui fait un appel, et quand); 09g (Défense préventive : un défenseur de plus que les attaquants restés haut).

**Bloque :** 13i, 13k, 13l.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : leviers existants seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** avec et sans Défensif : hauteur moyenne du bloc plus basse, distance entre lignes plus faible, largeur du bloc sans ballon plus faible, tirs concédés depuis l'axe en baisse, montées simultanées des deux latéraux plus rares, dégagements sous pression plus fréquents dans son tiers, latence du repli à la perte plus courte ; tirs tirés en baisse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu, avec sa contrepartie (200 matchs appariés)
- [ ] Leviers tracés : hauteur du bloc, densité axiale (écart horizontal toléré du bloc), prudence des latéraux (pas de montée simultanée des deux), préférence pour le dégagement sous pression dans son tiers (valeur de la passe longue sûre contre la relance courte risquée), repli immédiat à la perte (transition défensive, ticket `v2-collectif/10`)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Leviers ajoutés : **densité axiale** (bloc resserré horizontalement sans ballon, distinct de la largeur avec ballon de 13g), **prudence des latéraux**, **dégagement préféré à la relance courte risquée sous pression**, et, en transition défensive, **repli immédiat vers le bloc** plutôt que contre-pressing (13j). Estimation portée de 1 h 35 à 2 h 05 : au-delà de 2 h, à examiner pour découpage avant le code (par exemple bloc et axe d'un côté, latéraux et dégagement de l'autre).
