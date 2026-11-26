# 14b3: Tirs : contres, gardien, issue et visée sur la trajectoire courbe

**Découpé du ticket 14b le 26/11/2026** (audit Magnus : `docs/AUDIT_MAGNUS_V2.md`, section 4 B). **Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** physique.

**Constat vérifié (26/11/2026) :** tout le tir suppose « angle au départ = angle sur la ligne de but ». La décision lit la même chance que la résolution (05e) : les deux doivent changer ensemble.

**Sites (famille B de l'audit, côté tirs) :**

| # | Site | Géométrie actuelle |
|---|---|---|
| 1 | `shooting._goal_angle` (l. 106), `_covered_share` (l. 115-125) | rayons droits depuis le tireur, `along` sur l'axe tireur → but |
| 2 | `shooting._blockers` (l. 217), `block_probability` (l. 229), `_block_covers` (l. 434-470), `physical_block_probability` (l. 532) | contres : angle masqué par un corps, `along` l. 455 |
| 3 | `shooting._keeper_cover` (l. 362-395), `_goal_angles` (l. 472) | portée du gardien coupée par des rayons droits, `along` l. 368 |
| 4 | `shooting._flight_shares` (l. 486), `physical_shot_chance` (l. 520), `on_target_axes` (l. 289) | parts cadré / à côté / au-dessus par angles de départ |
| 5 | `shooting.aim_angles` (l. 411), `draw_shot_error` (l. 580) | visée = angle de départ vers le côté visé |
| 6 | `match.py` l. 852-869 | `heading × SHOT_SPEED_MPS` ; `on_target` et `keeper_at_m` (`along` l. 868) calculés sur la droite |
| 7 | `match.py` l. 921 (`shot_for`), l. 948 (hauteur = `origin.distance × slope`) | tir cadré avancé en ligne droite jusqu'au but ; hauteur selon la distance à vol d'oiseau |
| 8 | `match._keeper_reaches` (l. 443), `_blocked` (l. 479-510, `along` l. 498) | distance parcourue = distance à l'origine ; passage au plus près sur le segment du pas |
| 9 | `defense.press_point` vers le but (l. 541, ligne de tir du 10k) | presseur sur la direction porteur → but |

**What to build:**
1. **Résolution en vol** (sites 6 à 8) : le tir suit la trajectoire du solveur (plus de ligne droite forcée pour `shot_for`) ; hauteur, gardien et contres jugés sur la trajectoire réelle (distance parcourue le long du chemin).
2. **Visée inverse** (site 5) : problème inverse sans formule fermée dès qu'il y a de l'effet. Un tir avec effet part dans la direction qui ramène la trajectoire sur le point visé : résolution numérique sur le prédicteur partagé (méthode de la sécante sur l'angle de départ, départ = visée droite). Fonction unique, réutilisée par 14b4 pour les passes. L'erreur d'exécution (35b, 05l) s'applique à la direction de départ trouvée, lois inchangées. **Repli documenté** : si la résolution ne converge pas dans la limite d'itérations, la frappe part sans effet (ω = 0), visée droite, et l'événement est compté dans la trace.
3. **Chance de décision** (sites 1 à 4) : parts cadrées, portée du gardien et contres évaluées sur les trajectoires prédites des angles de départ, pour garder décision = résolution (05e).
4. Site 9 : direction de départ du chemin prédit.
5. Sans effet : résultats identiques à avant.

**Séquencement avec 14b2 (vérifié dans le code le 26/11/2026) :** parallèle. Aucune fonction de ce ticket n'appelle `meeting_point`, `pass_aim` ni un site du 14b2 ; la visée inverse repose sur le prédicteur du 14b1 seulement.

**Attributs :** aucun (le choix de l'effet est au 14b4).

**Blocked by:** 14b1 (Spin du ballon et force de Magnus dans le solveur).

**Bloque :** 14b4 ; 16e (coup franc direct : tir enroulé au-dessus ou à côté du mur).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 45 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 40** |

Confiance : faible. Hypothèses : neuf sites, liste fermée ci-dessus ; les calculs analytiques des parts (`_flight_shares`) acceptent un échantillonnage d'angles sans coût prohibitif ; la sécante converge en moins de 6 itérations jusqu'à 35 m. Au-dessus du seuil de 2 h, examiné : un découpage résolution / décision casserait l'alignement 05e entre deux livraisons ; découpage non retenu. **Garde-fou contre le débordement** : point d'étape à 1 h 20 de travail ; si la visée inverse ou l'alignement 05e n'est pas acquis, réestimation annoncée au propriétaire avant de continuer.
Temps machine, non compté : suite complète (environ 10 min) ; deux empreintes ; temps de calcul sur 4 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir enroulé visé au second poteau depuis 20 m : départ hors du cadre, arrivée sur la ligne à moins de 5 cm du point visé (hors erreur d'exécution) ; gardien placé sur l'axe de départ : portée jugée sur le point de passage réel ; défenseur dans l'angle de départ mais hors de la courbe : pas de contre
- **Visée inverse, grille de scènes :** distances de 11 à 35 m, angles de 0 à 60°, effet de 0 au spin maximal du 14b1 (au moins 200 cas) : précision, nombre d'itérations, replis
- **Cohérence 05e :** sur une grille de scènes avec effet, chance de décision et fréquence de résolution (1 000 tirages) à ± 2 points
- **Non-régression :** sans effet, empreintes identiques à graine fixée

## Acceptance criteria

- [ ] Constantes produit (tolérance, nombre maximal d'itérations, repli) validées par le propriétaire avant le code
- [ ] **Visée inverse, précision** : sur la grille de scènes, arrivée à moins de 5 cm du point visé dans 100 % des cas convergés (hors erreur d'exécution, tirée après)
- [ ] **Visée inverse, convergence** : au plus 6 appels du prédicteur par frappe ; repli (sans effet, visée droite) dans 0 % des cas de la grille, et compté dans la trace pour le suivi en match (14b4 : ≤ 1 % des frappes avec effet)
- [ ] **Visée inverse, coût** : temps de calcul d'un match ≤ + 15 % avec la visée inverse et les parts de décision échantillonnées (mesure 4 matchs, effet forcé sur tous les tirs en scène de banc)
- [ ] Plus aucun tir avancé en ligne droite forcée ; hauteur, gardien et contres lus sur la trajectoire (sites 1 à 9 traités, recherche des projections `along` jointe au rapport)
- [ ] Décision et résolution alignées (± 2 points) avec effet
- [ ] Sans effet : empreintes identiques à graine fixée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
