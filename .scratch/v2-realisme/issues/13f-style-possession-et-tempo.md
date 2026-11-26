# 13f: Style Possession et tempo

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (passes sûres, tempo lent, récupération rapide). **Catégorie :** décision.

**Constat vérifié :** voir 13a ; le tempo (intervalle de décision `DECISION_INTERVAL_S`, temps de réception) est commun.

**What to build:** La consigne de possession pondère la perte plus fortement dans la valeur des options (même mécanisme que la transition, `decision._TRANSITION_WEIGHTS`), rallonge le temps avant de jouer quand le porteur n'est pas pressé (tempo) et réduit les ballons longs.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : Possession.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 13j (Arbitrage des styles par phase).

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

- **Comportementaux (profils comparés) :** avec et sans Possession : part de possession en hausse, passes courtes et passes par possession en hausse, passes longues sans cible en baisse, distance moyenne entre le porteur et ses deux soutiens les plus proches en baisse, changements d'aile en hausse, passes du gardien au pied en hausse, hauteur moyenne de circulation du ballon en hausse ; après récupération, part des passes de sécurisation en hausse

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu (200 matchs appariés)
- [ ] Leviers tracés : poids de la perte, tempo, réticence aux dégagements longs à l'aveugle, proximité des soutiens (distance de soutien des tickets `v2-collectif/06` et `v2-realisme/25c`), patience quand l'axe est fermé (changement d'aile, `v2-collectif/15d`), implication du gardien dans la relance (`v2-attributs-restants/03c`), sécurisation du ballon en transition offensive, contre-pressing réduit à la perte (13j)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Leviers ajoutés : **proximité des soutiens**, **changement d'aile** quand l'axe est fermé (s'appuie sur `v2-collectif/15d`), **gardien impliqué dans la relance** (s'appuie sur `v2-attributs-restants/03c`), et **sécurisation du ballon à la récupération** (transition offensive, en arbitrage avec Contre-attaque, 13j). « Récupère vite après la perte » (ticket chapeau) : contre-pressing de Possession à dose réduite, sur la seule durée du contre-pressing, sans toucher à la hauteur du bloc (dose fixée par 13j ; le contre-pressing complet reste au Pressing, 13b). Estimation portée de 1 h 40 à 2 h 05 : au-delà de 2 h, à examiner pour découpage avant le code (par exemple circulation et tempo d'un côté, soutiens et gardien de l'autre). Si 15d ou 03c ne sont pas livrés au moment du code, le levier correspondant est reporté et tracé comme tel.
