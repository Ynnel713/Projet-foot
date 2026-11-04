# 02a: Penalty

**Découpé du ticket 02 le 04/11/2026** (audit de granularité). Répond au « point à trancher » du ticket `v2-collectif/30` : la faute dans la surface y est sifflée, le penalty est tiré ici. Détail : `02-coups-de-pied-arretes.md`.

**What to build:** une faute sifflée dans la surface (ticket `v2-collectif/30`) donne un penalty : ballon au point de penalty, joueurs hors de la surface, tireur choisi par l'attribut (Penalty Taking, geste « Demands to Take Penalties »), tir résolu par le calcul de tir (qualité du 28a, issue du 28b) avec la pression propre au penalty, puis jeu repris sur le ballon repoussé éventuel. Gardien neutre jusqu'au ticket 03.

**Attributs :** Penalty Taking, Composure (pression du penalty).

**Blocked by:** `v2-collectif/29` (livré), `v2-collectif/30` (fautes sifflées) ; `v2-collectif/28a` et `28b` (calcul et issue du tir).

**Bloque :** 09a ; 03 (a, b, c) ; `v2-coach-et-gestion-de-match/05a` ; `v2-collectif/22a`. Alimente le temps additionnel (`v2-coach-et-gestion-de-match/03`) sans le bloquer (décision Q14 du 03/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Nombre de penalties par match et taux de réussite dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Penalty Taking élevé : plus de penalties marqués, à gardien égal
- [ ] Le tireur désigné est le meilleur Penalty Taking présent, sauf geste « Demands to Take Penalties » d'un coéquipier (test)
- [ ] Penalty tracé et rejoué à l'écran
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
