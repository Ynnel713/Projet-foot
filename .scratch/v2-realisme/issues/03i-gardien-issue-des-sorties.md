# 03i: Gardien : issue du ballon après une sortie

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans elle, la validation des sorties du gardien reste non prouvée). **Catégorie :** validation.

**Constat vérifié :** au 03g, la part de sorties « gagnées » (4,9 %) est mesurée par la relance du gardien ; elle ne dit ni qui a le ballon à la fin, ni si l'adversaire l'a pris. Les 35 sorties par match sont des épisodes d'état qui clignotent, pas des ballons (réserves A1 du 03d et A2 du 03g).

**What to build:** Indicateur par ballon (pas par épisode) : à chaque ballon libre pour lequel le gardien sort au moins une fois, qui a le ballon 3 s après (gardien, coéquipier, adversaire, ballon encore libre) et s'il y a eu tir adverse dans les 5 s. Hystérésis d'un tick ou regroupement des épisodes d'un même ballon pour les courses gagnantes masquées du 03g. Aucun réglage du filtre de portée.

**Attributs :** aucun

**Blocked by:** 03g (Validation du placement et des sorties du gardien).

**Bloque :** 18e.

**Status:** livré (07/11/2026), validé expert + QC

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

- [x] Constantes de mesure proposées avant le code : 3 s et 5 s sont celles du ticket, aucune constante du moteur
- [x] Issue par ballon mesurée sur 50 matchs ; courses gagnantes masquées recomptées par ballon (`docs/INDICATEURS_V2.md` section 13) : 35,0 ballons avec sortie par match, 71 % issus d'un tir adverse, 4,9 % au gardien à 3 s ; masquées par ballon 18,68 et 2,92, égales aux épisodes
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % : 2 h 05 estimées (non chronométrées) contre 1 h 30, soit + 39 % ; cause au registre `docs/agents/suivi-estimations.md`
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (2 matchs, `.scratch/v2-realisme/mesures/03i-det1.txt` et `03i-det2.txt`, hors ligne de durée de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 524 passés, 14 désélectionnés (attendu 2 520 + 4 tests ajoutés) ; `CLAUDE.md` mis à jour

## Comments

- **Périmètre élargi en cours de mesure.** La première série a donné 80 % de « jeu arrêté » à 3 s ; un match instrumenté a montré que ces ballons sont des tirs adverses (32 sur 44). Ajoutés : type de remise en jeu, ballon issu d'un tir adverse des 5 s précédentes, issue des ballons hors tir. Trois séries de 50 matchs (la dernière fait foi).
- **Hypothèse du ticket réfutée.** Les sorties ne clignotent pas : ballons et épisodes sont en rapport exactement 1 ; le clignotement existe pour le face-à-face (03e). Pas d'hystérésis nécessaire, regroupement par ballon retenu.
- **À trancher par le propriétaire (aucun réglage fait).** Le gardien « sort » surtout sur des tirs en vol (traités comme ballon libre par `gardien.race`) : voir `docs/INDICATEURS_V2.md` section 13.
- **Fichiers modifiés :** `scripts/v2_indicators.py`, `scripts/measure_v2.py`, `tests/test_v2_indicators.py`. Aucun fichier protégé.
- **Clôture (07/11/2026).** Expert `APPROVED_WITH_RESERVATIONS` (empreinte 86cd9c86), QC `VALIDÉ`, décision de clôture `VALIDÉ`. Réserves **A1** (le 71 % de « tirs » est une proximité temporelle, pas l'état du ballon ; trier par état du ballon avant tout réglage au 05b ou 18e ; les 45,5 % de corners hors tir restent inexpliqués) et **A2** (compteur « non résolus » collecté mais absent du rapport, à ajouter à un prochain ticket de bancs) acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026). A1 est consignée dans `docs/INDICATEURS_V2.md` section 13 ; A2 reste à faire.
