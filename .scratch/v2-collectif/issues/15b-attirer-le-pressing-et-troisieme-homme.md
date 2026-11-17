# 15b: Attirer le pressing et trouver le troisième homme

**Découpé du ticket 15 le 17/11/2026** (décision du propriétaire : « Je valide le découpage »). Détail d'origine : `15-construction-face-au-pressing.md`. **Chantier :** `v2-collectif`. **Priorité :** P1. **Catégorie :** décision.

**What to build:** en construction (phase du 25b), le porteur peut garder le ballon un temps pour fixer un presseur (attirer le pressing) avant de jouer dans l'espace qu'il libère ; et jouer vers un coéquipier qui remet en une touche vers un troisième, démarqué derrière la première ligne de pressing (troisième homme). Une bonne équipe choisit entre ces options, la passe courte directe et le jeu long (15a) selon ce que l'adversaire lui permet.

**Constat à vérifier avant le code :** le plan de passe du ticket 14 (combinaisons collectives) et le jeu à une touche du `31a` existent ; vérifier s'ils produisent déjà des troisièmes hommes en construction, et en quelle part.

**Hors de ce ticket :** court ou long (15a) ; qualité du geste du gardien (`v2-attributs-restants/03c`).

**Attributs :** Decisions, Vision, Composure (attirer sans perdre le ballon) ; Passing pour l'exécution, déjà lue. Rayons à vérifier dans `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage avec les tickets 13, 14 et 31a.

**Blocked by:** 15a.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 40** |

Confiance : faible. Hypothèses : le plan de passe (14) et le jeu à une touche (31a) portent le troisième homme sans nouveau mécanisme de passe ; « attirer » est un délai de décision du porteur, pas une conduite nouvelle. Au-dessus du seuil de 2 h : **à réexaminer pour découpage avant le code** (attirer le pressing d'un côté, troisième homme de l'autre), une fois le constat fait.
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène : un presseur fixé libère une solution que le porteur joue ; un troisième homme démarqué derrière la première ligne reçoit en deux passes
- [ ] Statistiques (50 matchs) : part des sorties de balle par troisième homme, pertes dans son propre tiers, avant et après
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs (ticket 22)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
