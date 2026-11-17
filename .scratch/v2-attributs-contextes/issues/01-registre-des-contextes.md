# 01: Registre des contextes d'attributs, sans changement de jeu

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P1. **Catégorie :** architecture.

**What to build:** un module `v2engine/contextes.py` qui déclare les contextes (nom, temps du cerveau, attributs et poids sommant à 1) et une fonction `contextual_rating(player, contexte)` qui lit chaque note par `condition.effective_rating`. Y migrer, à poids identiques, les cumuls existants : porteur tête haute (`scan.head_up_share`, Dribbling 0,6 + Technique 0,4, ticket 08c), idée de jouer de première (`decision.one_touch_idea_probability`, moyenne First Touch / Technique, 31a). Les cumuls d'une autre forme restent hors du registre et sont listés dans la carte : ballon dur à orienter (First Touch x Technique, A17, un produit et non une moyenne), temps d'arrivée Pace + Acceleration (capacités en secondes, R5), note du gardien (A8, jusqu'au ticket `v2-attributs-restants/03b`). Section « Contextes » ajoutée à `docs/CARTE_ATTRIBUTS_V2.md` ; entrée « Contexte (d'attribut) » ajoutée à `GLOSSARY.md`.

**Hors de ce ticket :** transformation du test de rayon (02) ; tout nouveau branchement d'attribut (03 et suivants).

**Attributs :** aucun nouvel effet (Dribbling, Technique, First Touch : poids inchangés).

**Blocked by:** aucun.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : deux cumuls seulement à migrer ; le test de rayon actuel accepte un module qui lit plusieurs attributs s'il est ajouté à `ALLOWED` (adaptation minimale, sa refonte est au 02). Au seuil de 2 h : indivisible (le registre sans migration n'a pas d'usage testable).
Temps machine, non compté : suite complète ; deux empreintes à graine fixée.

## Acceptance criteria

- [ ] Registre et `contextual_rating` ; poids d'un contexte sommant à 1 (test)
- [ ] Cumuls 08c et 31a lus par le registre, mêmes valeurs à 1e-12 près (test)
- [ ] Aucun changement de jeu : mêmes empreintes à graine fixée qu'avant le ticket (événements, ticks, décisions)
- [ ] Section « Contextes » de la carte et entrée du glossaire
- [ ] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
