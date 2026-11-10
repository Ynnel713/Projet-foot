# 23a: Erreur d'exécution continue de la passe

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`, recommandation « ticket dédié », acceptée par le propriétaire le 10/11/2026). **Priorité :** P1. **Catégorie :** moteur.

**Constat vérifié (10/11/2026) :** la passe est réussie ou ratée en tout ou rien (`possession.pass_aim`). Réussie, elle part vers la course du receveur avec le seul dosage (`dosage_quality`) ; ratée, le point visé est décalé de 10 à 25 % de sa longueur dans une direction tirée au hasard sur 360° (`_MISS_SHARE`), sans lien avec la note ni avec la difficulté. L'erreur de vitesse (`pass_velocity`, `_DOSAGE_ERROR`) est déjà continue, mais indépendante du tirage réussi / raté. Conséquence : pas de passe « un peu trop longue » ou « légèrement derrière le receveur », seulement des passes parfaites ou des passes perdues au hasard.

**What to build:** Remplacer le tout ou rien par une erreur d'exécution continue, sur le modèle du tir depuis le 35b : la direction et la vitesse de départ sont tirées autour de la passe idéale (écarts gaussiens), avec un écart d'autant plus large que Passing est bas et que le passeur est sous pression (pression et Composure) ; la longueur n'élargit l'écart angulaire que si une difficulté technique propre aux passes longues est justifiée, puisqu'un écart angulaire fixe fait déjà croître l'erreur latérale avec la distance. L'adversaire dans la ligne de passe et le receveur marqué **n'élargissent pas l'écart** : ils agissent par la physique (interception, receveur devancé), et la chance de décision les intègre par l'alignement (réserve A2 de l'expert, 10/11/2026). La passe réussit ou non par la physique : le ballon arrive, ou non, dans la portée du receveur avant un adversaire. L'anticipation de la course du receveur (`dosage_quality` dans `pass_aim`) reste la lecture du jeu : elle fixe la passe idéale et n'est pas une erreur d'exécution. La vitesse tirée est bornée (jamais négative, jamais au-delà de `MAX_PASS_MPS`). La note passe par la façade des notes (`19a`), pour que la fatigue s'y branche au `20a` sans reprendre ce code ; ce ticket n'ajoute aucun effet de fatigue.

La chance de passe (`pass_success_probability`) doit rester alignée sur la nouvelle résolution, comme le tir l'a été au `05e` : même loi d'écart, pas deux modèles. Elle est lue en six endroits, tous à aligner (réserve A1 de l'expert, 10/11/2026) : `decision.py` (trois appels : choix du receveur, plan « ligne ouverte »), `off_ball.py` (démarquage), `restart.py` (choix du receveur d'une remise), `occasion.py`. Les remises en jeu servies (touches, corners, six mètres, y compris aériennes, `match.py`) passent déjà par `pass_velocity` : elles changent aussi avec ce ticket. Tous les tirages restent dans le flux nommé `PASSE`.

**Attributs :** Passing, Composure (déjà lus ; aucun attribut nouveau).

**Blocked by:** 19a (façade des notes), 19c (garde probabiliste : chiffre l'écart actuel de la passe).

**Bloque :** 23b ; `v2-collectif/32a`. Le `20a` branchera la fatigue sur cette loi d'écart s'il est livré après ; sinon, ce ticket la lit par la façade (aucune dépendance bloquante).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 35 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : moyenne. Hypothèses : `19a` livré (lecture par la façade) ; l'alignement de la chance de décision réutilise la méthode du `05e` (`scripts/shot_calibration.py` adapté) ; écarts proposés à valider : direction σ ≈ 2° à Passing 99 et ≈ 8° à 11 sans pression, vitesse σ = a/√3 de l'erreur uniforme actuelle `_DOSAGE_ERROR` (environ 17 % à Passing 11, 2,9 % à 99) ; chiffre réel cherché, « non trouvé » sinon.

**Estimation révisée (10/11/2026, avant le code)** : 2 h 30 au lieu de 2 h 00 (+ 30 min : six lecteurs de la chance de passe à aligner et remises en jeu à mesurer, réserve A1). Au-delà du seuil indicatif de 2 h, examiné pour découpage : non découpé, car aligner la décision dans un ticket séparé laisserait deux modèles de passe dans le moteur entre les deux livraisons.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs avant / après.

## Tests

- **Unitaires (scène contrôlée, `tests/scenes.py`) :** passe de 10 m et de 35 m, Passing 11 / 55 / 99, avec et sans pression, 5 000 tirages : écart moyen au point idéal croissant quand la note baisse et quand la difficulté monte
- **Garde (`19c`) :** Passing 11 peut réussir une passe difficile, Passing 99 peut rater une passe facile (plancher validé au `19c`)
- **Ligne de passe (réserve A2) :** même passe en scène, avec et sans adversaire dans la ligne : écart au point idéal identique, seule la réussite baisse
- **Alignement :** par tranche de chance évaluée, passes réussies observées dans l'intervalle de confiance
- **Match (50 matchs) :** taux de passes réussies, pertes de balle, tirs et buts avant / après ; remises en jeu (touches, corners, six mètres) : part qui atteint un coéquipier, avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] `_MISS_SHARE` et le décalage au hasard sur 360° supprimés ; une seule loi d'écart, lue par la décision et par la résolution
- [ ] Écart au point idéal croissant quand Passing baisse et quand la difficulté monte (scène, 5 000 tirages)
- [ ] Écart au point idéal identique avec et sans adversaire dans la ligne de passe (scène, 5 000 tirages) ; seule la réussite baisse
- [ ] Les six lecteurs de `pass_success_probability` utilisent la loi alignée
- [ ] Garde du `19c` tenue pour la passe
- [ ] Chance évaluée calibrée sur 7 tranches (méthode du `05e`) : au plus une tranche hors de l'intervalle de confiance à 95 % (50 matchs)
- [ ] Taux de passes réussies par match : écart au plus 3 points avec l'avant, sinon cause expliquée et soumise au propriétaire (aucun recalage compensatoire)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 10/11/2026, création (ticket documentaire `backlog-v2/erreur-execution-continue`, commit `3ca8cbc`) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ. Réserves reportées ici, validées par délégation du propriétaire (« Oui reporte le », 10/11/2026) : A1 (six lecteurs de la chance de passe et remises en jeu), A2 (la ligne de passe et le marquage agissent par la physique, pas par l'écart), A5 (σ de vitesse, bornes, anticipation, nombre de tranches). Estimation portée à 2 h 30.
