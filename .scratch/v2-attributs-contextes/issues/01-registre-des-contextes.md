# 01: Registre des contextes d'attributs, sans changement de jeu

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P1. **Catégorie :** architecture.

**What to build:** un module `v2engine/contextes.py` qui déclare les contextes (nom, temps du cerveau, attributs et poids sommant à 1) et une fonction `contextual_rating(player, contexte)` qui lit chaque note par `condition.effective_rating`. Y migrer, à poids identiques, les cumuls existants : porteur tête haute (`scan.head_up_share`, Dribbling 0,6 + Technique 0,4, ticket 08c), idée de jouer de première (`decision.one_touch_idea_probability`, moyenne First Touch / Technique, 31a). Les cumuls d'une autre forme restent hors du registre et sont listés dans la carte : ballon dur à orienter (First Touch x Technique, A17, un produit et non une moyenne), temps d'arrivée Pace + Acceleration (capacités en secondes, R5), note du gardien (A8, jusqu'au ticket `v2-attributs-restants/03b`). Section « Contextes » ajoutée à `docs/CARTE_ATTRIBUTS_V2.md` ; entrée « Contexte (d'attribut) » ajoutée à `GLOSSARY.md`.

**Hors de ce ticket :** transformation du test de rayon (02) ; tout nouveau branchement d'attribut (03 et suivants).

**Attributs :** aucun nouvel effet (Dribbling, Technique, First Touch : poids inchangés).

**Blocked by:** aucun.

**Status:** livré (17/11/2026), validé expert + QC

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

- [x] Registre et `contextual_rating` ; poids d'un contexte sommant à 1 (test)
- [x] Cumuls 08c et 31a lus par le registre, mêmes valeurs à 1e-12 près (test)
- [x] Aucun changement de jeu : mêmes empreintes à graine fixée qu'avant le ticket (événements, ticks, décisions)
- [x] Section « Contextes » de la carte et entrée du glossaire
- [x] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md`

## Réalisation (17/11/2026)

- **Code** : `v2engine/contextes.py` (classe `Contexte` : nom, temps du cerveau, (attribut, poids), ticket ; contrôle à la création : temps connu, au moins deux attributs distincts, poids positifs sommant à 1 ; `CONTEXTES` ; `contextual_rating(joueur, contexte ou nom)` par la façade `condition.effective_rating`). Deux contextes : « porteur tête haute » (perception, Dribbling 0,6 + Technique 0,4, `scan.head_up_share`) et « idée de jouer de première » (décision, First Touch 0,5 + Technique 0,5, `decision.one_touch_idea_probability`). Constantes `DRIBBLING_PART` et `TECHNIQUE_PART` retirées de `scan.py` (aucun poids hors du registre). Calcul identique au bit près : 0 + 0,6 D + 0,4 T dans le même ordre ; 0,5 FT + 0,5 T = 0,5 (FT + T) exactement (multiplication par une puissance de 2).
- **Test de rayon, adaptation minimale** (refonte au 02) : chaque attribut d'un contexte compte comme lu dans le module `contextes` ; `ALLOWED` : `scan` retiré de Dribbling et Technique, `decision` retiré de Technique et First Touch, `contextes` ajouté ; dérogations Dribbling + Technique et First Touch + Technique retirées de `TOLERATED_MIXES`.
- **Tests** : `tests/test_v2engine_contextes.py` (poids sommant à 1 et temps valide par contexte ; cinq contextes mal formés refusés ; lecture par la façade, espionnée ; identité avec les anciennes formules à 1e-12 près sur 100 couples de notes, note composée et fonctions `head_up_share`, `one_touch_idea_probability`) ; `tests/test_v2engine_scan.py` adapté (poids lus dans le registre).
- **Empreintes** (deux matchs de 90 min, `random.seed`, `PYTHONHASHSEED=0`, sha256 de la trace complète et par partie) : identiques avant et après.
  - 20260923, Ligue 1 clubs 0 contre 1, 1-0 : complet `6bcc1083e580476d` ; ticks `3f825073b78d2095`, événements `c2657f6399816f75`, décisions `607d375f5d33811c`, scans `a94b890701a55d4d`.
  - 20261107, clubs 4 contre 5, 6-0 : complet `b77172eb7208e8ed` ; ticks `efde83113252a56e`, événements `fc2d1b4221ae3951`, décisions `40847430e13003ca`, scans `e8c18dc7784406aa`.
- **Documentation** : section « Contextes » de `docs/CARTE_ATTRIBUTS_V2.md` (table des contextes, cumuls hors registre : A17, temps d'arrivée, A8) ; garde automatique, A15, A16 et cellules Dribbling, Technique, First Touch mises à jour ; entrée « Contexte (d'attribut) » de `GLOSSARY.md`.
- **Suite complète** (17/11/2026, session cloud) : 3 364 passés, 0 ignoré, 14 désélectionnés (15 min 11) ; attendu 3 255 + 109 tests ajoutés (`test_v2engine_contextes.py`) = 3 364.
- **Durée** : estimée 2 h 05, réelle environ 1 h 15 de travail effectif (− 40 %) : deux cumuls seulement, migration mécanique, adaptation du test de rayon sans surprise ; durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : quatre matchs de 90 min (empreintes, 4 min 40 par paire), tests ciblés (2 min 33), suite complète (15 min 11).

## Comments

- **17/11/2026, passage 1** : expert APPROVED (sans réserve) ; QC VALIDÉ ; clôture journalisée VALIDÉ (empreinte `6c1372f2bf8f…`). Aucune anomalie bloquante. Améliorations facultatives de l'expert, à reprendre au ticket 02 : A1, `CONTEXTES` est un dict mutable (proposer `types.MappingProxyType`) ; A2, la garde de rayon accepte toute lecture non littérale dans `contextes` : le 02 doit vérifier que ce module ne lit des notes que par `contextual_rating`. Point à surveiller : poids de la note du gardien (A8) encore dans `shooting.py`, reporté au `v2-attributs-restants/03b`.
