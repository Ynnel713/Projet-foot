# 19c: Garde probabiliste : jamais infaillible, jamais incapable

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (exigence centrale : les notes modifient les probabilités, pas les possibilités ; vérifiée aujourd'hui ticket par ticket). **Catégorie :** validation.

**Constat vérifié :** la courbe partagée borne la réussite entre 5 et 95 % (`attributes._cubic_curve`), mais plusieurs résolutions sortent de ce cadre : la passe est réussie ou ratée en tout ou rien, et l'ampleur de l'erreur d'une passe ratée (point visé décalé de 10 à 25 % de la distance, `possession.pass_aim`, `_MISS_SHARE`) ne dépend pas de la note ; l'arrêt du gardien est déterministe à position donnée (`shooting.py`, constat du 06c) ; `dosage_quality` et `attempt_tackle_probability` vont de 0 à 1. Aucun test transversal ne vérifie qu'un joueur noté 11 peut réussir l'action la plus difficile et qu'un joueur noté 99 peut rater la plus simple.

**What to build:** Test de garde paramétré sur chaque fonction de résolution (passe, contrôle, conduite, tacle, tir cadré, but, arrêt, contre, faute, lecture du hors-jeu) : notes 11 et 99, situation la plus facile et la plus difficile, N tirages dans le flux nommé. Vérifie que la réussite et l'échec ont chacun une fréquence au moins égale à un plancher, que la hiérarchie des notes est respectée en moyenne, et que la queue des issues (exceptionnelle, complètement ratée) existe pour les deux notes. Les fonctions hors garde sont listées et renvoyées chacune à un ticket ; ce ticket ne les corrige pas. Liste des exceptions assumées (exemple : une passe de 2 m sans adversaire) validée par le propriétaire.

**Attributs :** aucun

**Blocked by:** 05e (livré) ; 01f (livré).

**Bloque :** 18a ; `v2-collectif/22a` ; 23a (ajouté le 10/11/2026).

**Status:** livré (10/11/2026), validé expert + QC

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

## Comments

- 10/11/2026, constantes (validées par délégation du propriétaire, « Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) : plancher 1 % de réussite et 1 % d'échec ; exceptions assumées : conduite sans adversaire à 5 m pour un 99 (perte 0,5 % sur 1,5 s, plancher 0,4 %) et but sur la frappe la plus difficile (35 m, angle fermé, sous pression) pour un 11 (0,56 %, plancher 0,5 %), chiffres réels non trouvés.
- 10/11/2026, implémentation : `tests/test_v2engine_garde_probabiliste.py` (52 tests). Méthode : chaque résolution tire `flux.random() < p` ; la garde lit `p` (exact, sans bruit de tirage) pour 9 résolutions (passe, contrôle, conduite, tacle, tir cadré, but, tacle sans faute, appel réglé sur la ligne, drapeau vu), notes 11 et 99, situation facile et difficile ; un test par tirage (5 000 tirages du flux `DECISION`, `offside.respects_the_line`) vérifie l'équivalence. Hiérarchie des notes vérifiée pour chaque résolution (Aggression inversée : plus de fautes) ; queue des issues : un 99 peut dévisser, un 11 peut marquer de 35 m. Aucun code du moteur modifié.
- Hors garde, renvoyés (tests d'écart connu, à retirer par le ticket correcteur) : arrêt sans note du gardien (`v2-attributs-restants/03b`) ; contre sans note du défenseur (`17b`) ; dosage de la passe de 0 à 1 et ampleur de la passe ratée indépendante de la note (`23a`). Non gardé : la tentative de tacle (`attempt_tackle_probability`, taux par seconde de 0,009 à 0,051), qui est une fréquence et non une issue. Constat : à First Touch 99, la difficulté du contrôle ne mord plus (0,97 au plus facile comme au plus difficile), renvoyé à `18d`.
- Mesures : suite complète 2 707 passés, 14 désélectionnés (2 655 + 52, `.scratch/v2-realisme/mesures/19c-suite.txt`) ; déterminisme : fichier passé deux fois, mêmes résultats (seul tirage semé, `seed_scene(19)`).
- Durée : estimée 90 min, réelle environ 75 min (analyse 20, développement 30, tests 15, intégration 10 ; estimée, non chronométrée), − 17 %. Temps machine hors total : 25 min de suite.
- 10/11/2026, clôture : expert APPROVED, QC VALIDÉ, clôture VALIDÉ. Facultatifs de l'expert : A1, rejouer `scripts/shot_calibration.py` avec la garde aux lots de calibration (22a), le tir étant gardé sur sa formule analytique ; A2, passe difficile de 40 m et non du pire cas (60 m), à revoir si 23a ou 18d touchent la difficulté de distance. Réserve de forme du QC : la conduite est gardée sur sa durée de référence (1,5 s), alors que le moteur tire par intervalle de 0,5 s (perte d'un 99 libre : 0,17 % par tirage) ; la docstring du test dit « la chance que le moteur tire », exact pour les autres résolutions.
