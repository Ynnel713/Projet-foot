# 08d: Le porteur décide sur ce qu'il perçoit

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un adversaire non vu doit pouvoir surprendre). **Catégorie :** décision.

**Constat vérifié :** `decision.evaluate_options` utilise les positions réelles des adversaires ; voir 08a.

**What to build:** L'évaluation des options (passes, conduites, tir) utilise les positions perçues (08b) ; la valeur RÉELLE, pour le journal du meilleur choix (ticket 33), reste calculée sur les positions réelles. Un adversaire non vu peut donc couper une passe jugée sûre.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/33` (livré, non modifié) : même deux étages, perception enrichie.

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes).

**Bloque :** 08f.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** l'erreur de Decisions (ticket 33) a été réglée pour la perception actuelle : remesurer le taux de meilleur choix et signaler l'écart, sans régler ici.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : coût de calcul limité aux options envisagées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur dans le dos du porteur, non vu, sur la ligne de passe : passe choisie puis interceptée ; vu : passe évitée
- **Statistiques (séries de matchs) :** 50 matchs : interceptions et taux de meilleur choix avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Décision sur le monde perçu, valeur réelle conservée au journal
- [ ] Taux de meilleur choix remesuré et rapporté
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
