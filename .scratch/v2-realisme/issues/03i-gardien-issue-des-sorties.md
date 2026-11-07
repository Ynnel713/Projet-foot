# 03i: Gardien : issue du ballon après une sortie

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans elle, la validation des sorties du gardien reste non prouvée). **Catégorie :** validation.

**Constat vérifié :** au 03g, la part de sorties « gagnées » (4,9 %) est mesurée par la relance du gardien ; elle ne dit ni qui a le ballon à la fin, ni si l'adversaire l'a pris. Les 35 sorties par match sont des épisodes d'état qui clignotent, pas des ballons (réserves A1 du 03d et A2 du 03g).

**What to build:** Indicateur par ballon (pas par épisode) : à chaque ballon libre pour lequel le gardien sort au moins une fois, qui a le ballon 3 s après (gardien, coéquipier, adversaire, ballon encore libre) et s'il y a eu tir adverse dans les 5 s. Hystérésis d'un tick ou regroupement des épisodes d'un même ballon pour les courses gagnantes masquées du 03g. Aucun réglage du filtre de portée.

**Attributs :** aucun

**Blocked by:** 03g (Validation du placement et des sorties du gardien).

**Bloque :** 18e.

**Status:** à faire (créé le 07/11/2026, réserves A1 et A2 de l'expert du 03g)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : lecture seule de la trace et du ballon.
Temps machine, non compté : suite complète (environ 40 min) ; série de 50 matchs.

## Acceptance criteria

- [ ] Constantes de mesure proposées avant le code
- [ ] Issue par ballon mesurée sur 50 matchs ; courses gagnantes masquées recomptées par ballon
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
