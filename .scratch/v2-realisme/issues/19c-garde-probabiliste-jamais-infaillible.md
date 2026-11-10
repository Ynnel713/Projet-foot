# 19c: Garde probabiliste : jamais infaillible, jamais incapable

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (exigence centrale : les notes modifient les probabilités, pas les possibilités ; vérifiée aujourd'hui ticket par ticket). **Catégorie :** validation.

**Constat vérifié :** la courbe partagée borne la réussite entre 5 et 95 % (`attributes._cubic_curve`), mais plusieurs résolutions sortent de ce cadre : la passe est réussie ou ratée en tout ou rien, et l'ampleur de l'erreur d'une passe ratée (point visé décalé de 10 à 25 % de la distance, `possession.pass_aim`, `_MISS_SHARE`) ne dépend pas de la note ; l'arrêt du gardien est déterministe à position donnée (`shooting.py`, constat du 06c) ; `dosage_quality` et `attempt_tackle_probability` vont de 0 à 1. Aucun test transversal ne vérifie qu'un joueur noté 11 peut réussir l'action la plus difficile et qu'un joueur noté 99 peut rater la plus simple.

**What to build:** Test de garde paramétré sur chaque fonction de résolution (passe, contrôle, conduite, tacle, tir cadré, but, arrêt, contre, faute, lecture du hors-jeu) : notes 11 et 99, situation la plus facile et la plus difficile, N tirages dans le flux nommé. Vérifie que la réussite et l'échec ont chacun une fréquence au moins égale à un plancher, que la hiérarchie des notes est respectée en moyenne, et que la queue des issues (exceptionnelle, complètement ratée) existe pour les deux notes. Les fonctions hors garde sont listées et renvoyées chacune à un ticket ; ce ticket ne les corrige pas. Liste des exceptions assumées (exemple : une passe de 2 m sans adversaire) validée par le propriétaire.

**Attributs :** aucun

**Blocked by:** 05e (en cours) ; 01f.

**Bloque :** 18a ; `v2-collectif/22a` ; 23a (ajouté le 10/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : test seulement ; plancher proposé : 1 % de réussite et 1 % d'échec, à valider.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** grille notes 11 / 99 × situation facile / difficile pour chaque résolution, 5 000 tirages

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Plancher et exceptions validés par le propriétaire
- [ ] Chaque résolution testée ; fonctions hors garde listées avec leur ticket de correction
- [ ] Hiérarchie des notes vérifiée en moyenne pour chaque résolution
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
