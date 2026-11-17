# 02: Test de rayon transformé : vérifier le registre au lieu de refuser les mélanges

**Chantier :** `v2-attributs-contextes` (ADR 0002, point 6). **Priorité :** P1. **Catégorie :** architecture, tests.

**What to build:** `tests/test_v2engine_rayon_attributs.py` cesse de refuser par défaut les calculs qui combinent plusieurs attributs (`TOLERATED_MIXES`) et de tenir une liste blanche de modules (`ALLOWED`). Il vérifie à la place : chaque contexte du registre est documenté dans la section « Contextes » de la carte ; ses poids somment à 1 ; aucune lecture d'attribut dans le moteur hors du registre, de la façade et des exceptions listées (cumuls d'une autre forme, A17, R5, A8) ; pas deux contextes déclarés pour un même effet (identifiant d'effet unique) ; chaque attribut non spécialiste figure dans au moins deux contextes, sauf liste de transition datée (attributs encore cloisonnés, avec leur ticket de branchement). La couverture des colonnes de la base (`COVERAGE_EXCEPTIONS`) et la garde de la façade (R6) restent.

**Hors de ce ticket :** les branchements eux-mêmes (03 et suivants) ; la liste de transition se vide au fil de ces tickets.

**Attributs :** aucun nouvel effet.

**Blocked by:** 01.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : les lectures directes restantes (un attribut, un calcul) passent par un contexte à un seul attribut, ou restent permises au titre de la liste de transition, sans réécrire tous les modules dans ce ticket.
Temps machine, non compté : suite complète.

## Acceptance criteria

- [ ] Les cinq vérifications ci-dessus, chacune avec un cas négatif synthétique (comme l'actuel test du mélange Tackling + Aggression)
- [ ] Liste de transition datée, chaque entrée liée à son ticket de branchement
- [ ] Carte : paragraphe « Garde automatique » réécrit
- [ ] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
