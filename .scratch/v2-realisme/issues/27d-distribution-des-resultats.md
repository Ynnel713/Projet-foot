# 27d: Distribution des résultats : nuls, surprises et écarts de niveau

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « incertitude » : deux matchs ne se ressemblent jamais, sans scénario). **Priorité :** P1 (avant `v2-collectif/22c`). **Catégorie :** validation.

**Constat vérifié (14/11/2026) :** le moteur est stochastique (D-V06, D-V13) et rien n'est scripté, mais aucun indicateur ne vérifie la **quantité** d'incertitude : part des matchs nuls, fréquence des victoires de l'équipe la plus faible, distribution des scores, matchs retournés. Les repères du banc portent sur les volumes (tirs, buts, passes), pas sur l'issue.

**What to build:** une série du banc qui joue des affiches à écarts de niveau choisis (équipes égales, écart moyen, gros écart, mesuré par la note moyenne du onze) et rapporte : victoires, nuls, défaites, distribution des scores, part des matchs où l'équipe menée d'un but à la 70e ne perd pas. Repères réels à sourcer (part des nuls dans les grands championnats, victoire du favori selon l'écart de cote ou de classement), ou « non trouvé ». Le plan d'expérience précise si le moteur V2 modélise l'avantage du terrain ; sinon le repère réel choisi l'exclut (matchs à huis clos, ou écart domicile-extérieur neutralisé). Trop peu d'incertitude (le favori gagne presque toujours) ou trop (les écarts de niveau ne comptent pas) sont deux défauts. Aucun réglage ici : les écarts vont à la calibration (22c).

**Attributs :** aucun.

**Blocked by:** 01e (séries longues et intervalles).

**Bloque :** `v2-collectif/22c`.

**Status:** à faire (repères et plan d'expérience à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : le banc (`scripts/measure_v2.py`) joue aujourd'hui des affiches fixées par ses propres règles, pas une affiche choisie : une option à ajouter ; l'écart de niveau se mesure par une note d'équipe dont la méthode est à proposer (par exemple la moyenne du onze sur les attributs clés de chaque poste).
Temps machine, non compté : au moins 100 matchs par niveau d'écart (environ 1 h 30 en session cloud, à confirmer).

## Tests

- **Statistiques (séries de matchs) :** trois niveaux d'écart, 100 matchs chacun : résultats et intervalles publiés dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Repères réels (sourcés ou « non trouvé ») et plan d'expérience validés par le propriétaire avant le code
- [ ] Intervalles de confiance publiés (01e) ; un écart n'est signalé que s'il dépasse l'intervalle
- [ ] Aucun réglage du moteur dans ce ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
