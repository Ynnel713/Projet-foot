# 02: Test de rayon transformé : vérifier le registre au lieu de refuser les mélanges

**Chantier :** `v2-attributs-contextes` (ADR 0002, point 6). **Priorité :** P1. **Catégorie :** architecture, tests.

**What to build:** `tests/test_v2engine_rayon_attributs.py` cesse de refuser par défaut les calculs qui combinent plusieurs attributs (`TOLERATED_MIXES`) et de tenir une liste blanche de modules (`ALLOWED`). Il vérifie à la place : chaque contexte du registre est documenté dans la section « Contextes » de la carte ; ses poids somment à 1 ; aucune lecture d'attribut dans le moteur hors du registre, de la façade et des exceptions listées (cumuls d'une autre forme, A17, R5, A8) ; pas deux contextes déclarés pour un même effet (identifiant d'effet unique) ; chaque attribut non spécialiste figure dans au moins deux contextes, sauf liste de transition datée (attributs encore cloisonnés, avec leur ticket de branchement). La couverture des colonnes de la base (`COVERAGE_EXCEPTIONS`) et la garde de la façade (R6) restent.

**Hors de ce ticket :** les branchements eux-mêmes (03 et suivants) ; la liste de transition se vide au fil de ces tickets.

**Attributs :** aucun nouvel effet.

**Blocked by:** 01.

**Status:** livré (17/11/2026), validé expert + QC

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

- [x] Les cinq vérifications ci-dessus, chacune avec un cas négatif synthétique (comme l'actuel test du mélange Tackling + Aggression)
- [x] Liste de transition datée, chaque entrée liée à son ticket de branchement
- [x] Carte : paragraphe « Garde automatique » réécrit
- [x] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md`

## Réalisation (17/11/2026)

- **Choix du propriétaire** (question posée avant le code, réponse « Registre seul (Recommandé) ») : pour la règle « au moins deux contextes », seuls les contextes du registre comptent ; les attributs sans ticket de branchement sont rattachés à un nouveau ticket, `08` (solde de la liste de transition). Réestimation annoncée avant le code : 1 h 55 (+ 15 min pour rédiger le 08).
- **Registre** (`v2engine/contextes.py`) : champ `effet` (identifiant `module.fonction` de la fonction qui porte l'effet) ; `CONTEXTES` en lecture seule (`MappingProxyType`, réserve facultative A1 de l'expert au 01). Aucun calcul changé.
- **Garde** (`tests/test_v2engine_rayon_attributs.py`) : `ALLOWED` et `TOLERATED_MIXES` supprimés ; cinq vérifications, chacune avec un cas négatif synthétique : (1) contexte documenté dans la carte (nom, effet, « Attribut poids ») ; (2) poids sommant à 1 ; (3) aucune lecture hors registre et façade (`player_attribute` réservé à `attributes` et `condition`, `intrinsic_rating` au chargement, nom non littéral seulement dans `contextes.contextual_rating` : réserve A2 de l'expert au 01) et aucun mélange d'attributs hors registre, sauf `CUMULS_HORS_REGISTRE` (A8, R5, A17) dans leur fonction, avec garde de péremption ; (4) un effet, un contexte, et chaque contexte lu par la seule fonction de son effet ; (5) chaque attribut non spécialiste lu par le moteur dans au moins deux contextes, sauf `TRANSITION` (24 attributs datés du 17/11/2026, chacun avec son ticket ; entrée devenue inutile = échec). Gardes conservées : dictionnaire brut, champs physiques, couverture des 52 caractéristiques, gestes préférés.
- **Tests** : `test_v2engine_rayon_attributs.py` passe de 14 à 21 fonctions de test ; `test_v2engine_contextes.py` : effet = fonction réelle, registre en lecture seule.
- **Documentation** : paragraphe « Garde automatique » de la carte réécrit, colonne « Effet » de la table des contextes précisée, points 1 et 2 de la grille de relecture mis à jour ; ticket `08` créé ; spec et `docs/PLAN_V2.md` ; compte attendu de `CLAUDE.md` passé à 3 372.
- **Jeu inchangé** : mêmes empreintes à graine fixée qu'avant le ticket 01 (20260923 : `6bcc1083e580476d` ; 20261107 : `b77172eb7208e8ed`, et chaque partie).
- **Suite complète** (17/11/2026) : 3 372 passés, 0 ignoré, 14 désélectionnés (15 min 25) ; 3 364 après le ticket 01 + 8.
- **Durée** : estimée 1 h 40, réestimée 1 h 55 ; réelle environ 1 h 20 de travail effectif (− 31 % sur la réestimation) : la garde se réécrit d'un seul tenant, le décompte des attributs à mettre en transition a été mesuré par un script avant la question au propriétaire ; durée estimée à l'horloge de la session hors attentes machine et réponse du propriétaire, non chronométrée. Temps machine hors total : suite complète (15 min 25), deux matchs de 90 min (empreintes, 4 min 40).

## Comments

- **17/11/2026, passage 1** : expert APPROVED (sans réserve) ; QC VALIDÉ ; clôture journalisée VALIDÉ (empreinte `35b18e1e0c88…`). Aucune anomalie bloquante. Améliorations facultatives de l'expert : A1, sans `ALLOWED` une lecture directe d'un attribut n'est plus restreinte par module (conforme à l'ADR ; piste : inventaire informatif des modules lecteurs) ; A2, `_context_uses` ne voit pas `contextual_rating(p, contexte=X)` en argument nommé (examiner `node.keywords` ou le refuser) ; A3, comparaison des poids par `f"{w:g}"` fragile pour un poids comme 1/3 (aucun poids actuel concerné). QC : réserve non bloquante, chiffres de suite et d'empreintes vérifiables seulement par le fichier de résultats.
