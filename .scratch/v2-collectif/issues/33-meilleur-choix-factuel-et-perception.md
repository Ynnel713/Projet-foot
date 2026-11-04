# 33: Meilleur choix factuel et perception du porteur

**What to build:** Pour chaque prise de balle, il existe un **meilleur choix factuel**, que le joueur respecte ou non selon son intelligence de jeu. Le meilleur choix n'est pas le même pour tous : il dépend des capacités du porteur (un bon frappeur à l'entrée de la surface, peu exposé au contre, a intérêt à tirer ; un mauvais frappeur, dans la même situation, à chercher un décalage, une passe ou un retrait). C'est l'une des choses qui différencient les niveaux.

Constat de départ : un milieu avec le champ libre devant lui préfère une passe en retrait. La conduite a une valeur fixe (`DRIBBLE_WEIGHT * (1 - gene)`, `decision.py:156`) qui ignore l'espace libre ; les trois poids (tir 0,1, passe 0,25, conduite 0,04) sont des réglages de volume sans sens physique ; quand le porteur ne prend pas la meilleure option, il en prend une autre au hasard, absurde aussi souvent que voisine.

1. **Deux étages.**
   - **Valeur factuelle** : le moteur, en analyste omniscient, calcule la vraie valeur de chaque option dans la situation réelle, **avec les vraies capacités du porteur**. Le meilleur choix factuel est enregistré.
   - **Perception** : le porteur choisit l'option qu'il **croit** la meilleure ; sa perception des valeurs est déformée par ses attributs mentaux.
2. **Monnaie commune : le danger attendu.** Valeur d'une option = réussite × danger de l'endroit atteint − (risque de perte × danger qu'aurait l'adversaire à cet endroit). Carte du danger : grille publiée et sourcée de type « expected threat » (Karun Singh, 2019, 12 × 8 zones), vérifiée et proposée au propriétaire avant le code ; la même carte, retournée, donne le coût de la perte.
3. **Les options.**
   - **Conduite** : quelques directions (devant, diagonales, côtés). Pour chacune, une course contre les défenseurs les plus proches (`defense.arrival_time_s`) mesure l'espace réellement libre, à la vitesse balle au pied du porteur. Valeur = danger atteint × chance de garder le ballon (Dribbling, pression) − coût de la perte. La direction choisie devient la cible de conduite jusqu'à la décision suivante (toutes les 0,5 s, inchangé).
   - **Passe** : réussite actuelle (Passing, Technique, `possession.pass_success_probability`) dans la nouvelle monnaie.
   - **Tir** : chance de but actuelle (`shooting.shot_probability`, Finishing). Le ticket 28 la remplace ensuite (défenseurs dans l'axe, gardien, contre) sans toucher au cadre.
   - **Mécanismes livrés réécrits sans changer leur sens** : transition (ticket 11 : en contre-attaque le gain de danger pèse plus et la perte moins, en conservation l'inverse), valeur future de la passe (ticket 13 : danger après la meilleure action suivante du receveur), plan de passe (ticket 14 : bonus conservé). Les poids `SHOT_WEIGHT`, `PASS_WEIGHT`, `DRIBBLE_WEIGHT` disparaissent.
4. **Perception (attributs mentaux).** L'erreur porte sur la **valeur perçue**, puis le porteur prend ce qu'il croit le mieux : un bon choix évident est vu par presque tous, deux options proches font hésiter même un très bon joueur, un joueur faible fait surtout des erreurs voisines, rarement des absurdités.
   - **Decisions** : ampleur de l'erreur. La courbe validée (99 → 95 %, 55 → 70 %, 11 → 45 %) devient la **cible moyenne sur un match** du taux de meilleur choix suivi ; les constantes d'erreur sont proposées après mesure.
   - **Composure** : multiplie l'erreur seulement sous pression (adversaire à moins de 5 m), d'autant plus que la note est basse (ordre d'idée ×1,2 à 99, ×2 à 11, à proposer).
   - **Anticipation** : part du mouvement des défenseurs prolongée pendant la course du porteur (ordre d'idée 100 % à 99, 30 % à 11, à proposer) ; une faible Anticipation croit libre un espace qui se referme.
   - **Vision** : inchangée, elle filtre les options vues.
5. **Séparation des attributs (sans double comptage).** Exécution (Finishing, Long Shots, Passing, Technique, Dribbling, Pace, Acceleration, First Touch) dans la valeur factuelle seulement ; mental (Decisions, Composure, Anticipation, Vision) dans la perception seulement. Hors de ce ticket : Flair (`v2-cerveau-joueurs/05`), Teamwork (plan, ticket 14), ce que le joueur croit de ses propres capacités (ticket 20).
6. **Visible.** Journal des décisions : meilleur choix factuel, choix fait, écart de valeur. Panneau du joueur à l'écran : « Meilleur choix : conduite. Choisi : passe en retrait (erreur légère) ».

**Attributs :** Decisions, Composure, Anticipation, Vision (perception) ; Finishing, Passing, Technique, Dribbling, Pace, Acceleration, First Touch (valeur factuelle).

**Blocked by:** 14 et 16 (fichiers partagés, `decision.py`). À livrer avant 28, `v2-attributs-restants/07`, 32, et donc avant 22.

**Status:** livré (04/11/2026), validé expert + QC

**Origine (03/11/2026) :** constat du propriétaire (un milieu au champ libre joue en retrait), puis séance de questions (/grill-me) : deux étages, monnaie du danger attendu, erreur plausible sur la valeur perçue, meilleur choix calculé avec les vraies capacités du joueur, ticket dédié avant 28, 07 et 32 ; découpage des attributs, carte publiée, course contre les défenseurs, coût de la perte, tir actuel en attendant 28 ; courbe Decisions comme cible moyenne, Composure sous pression seulement, Anticipation par projection des défenseurs, direction de conduite tenue jusqu'à la décision suivante, meilleur choix visible ; mécanismes 11, 13 et 14 réécrits, volumes rapportés sans réglage.

**Point de vigilance :**
- Les volumes (passes, tirs, buts) et les critères chiffrés des tickets 13 et 14 (dont C2) vont bouger : mesurés avant et après, rapportés, pas réglés ici (ticket 22). Un mécanisme livré qui perd son effet mesurable, ou un volume absurde, est un défaut à corriger dans ce ticket.
- Chaque nouveau tirage décale la suite aléatoire : mesures de référence à refaire.
- Coût de calcul : plusieurs directions évaluées par décision du porteur, deux fois par seconde ; à mesurer (le rejeu en direct supporte un calcul jusqu'à environ 3 fois plus lent qu'aujourd'hui à x8).

## Acceptance criteria

- [x] Constantes produit proposées et validées avant le code : carte du danger (source, valeurs), directions de conduite, force de l'erreur selon Decisions, facteur Composure, part de projection Anticipation
- [x] Scène fixe : milieu au champ libre devant lui → la conduite est le meilleur choix factuel ; il la choisit plus souvent que le retrait, nettement plus à Decisions élevée
- [x] Scène fixe : à l'entrée de la surface, à situation identique, le meilleur choix factuel est le tir pour un bon frappeur et la passe (décalage ou retrait) pour un mauvais
- [x] Scène fixe : sous pression près de son propre but, le retrait devient le meilleur choix factuel
- [x] Scène fixe : à faible Anticipation, le porteur choisit plus souvent une conduite vers un espace qui se referme ; Composure ne change rien sans pression
- [x] En match (graine d'audit) : taux de meilleur choix suivi par tranche de Decisions, comparé à la courbe validée ; les erreurs sont surtout voisines (écart de valeur rapporté)
- [x] Mécanismes des tickets 11, 13, 14 encore mesurables (effet de la contre-attaque, valeur future, plan tenu)
- [x] Indicateurs rapportés avant et après : passes en arrière (≈ 18 % aujourd'hui ; réel 24-42 %, à sourcer), conduites et distance balle au pied, passes par minute, tirs, buts, durée de calcul par match
- [x] Meilleur choix, choix fait et écart dans la trace et dans le panneau du joueur
- [x] Carte des attributs (`docs/CARTE_ATTRIBUTS_V2.md`) et test de rayon des attributs à jour ; déterminisme à graine fixée

## Constantes proposées (03/11/2026) — validées par délégation du propriétaire (recommandations acceptées d'office)

**Carte du danger.** Grille « expected threat » de Karun Singh (2019), jeu ouvert, 12 colonnes (de son but au but adverse) × 8 lignes, fichier publié `karun.in/blog/data/open_xt_12x8_v1.json`, téléchargé le 03/11/2026. Valeur d'une case = probabilité de marquer dans les actions qui suivent quand on a le ballon à cet endroit. Repères : 0,006 près de son propre poteau de corner, 0,02 au milieu du terrain, 0,035 aux 25 m dans l'axe, 0,108 au point de penalty, 0,257 dans les 6 mètres. Lecture **lissée** entre les centres de cases (interpolation bilinéaire) : sans lissage, avancer d'un mètre pourrait faire sauter la valeur d'une case à l'autre et fausser le choix de direction. Le coût d'une perte au point P = valeur de la grille pour l'adversaire au même point (grille retournée).

**Monnaie commune.** Tir : chance de but (`shot_probability`), déjà dans la même unité que la grille ; un tir manqué ne coûte rien (sortie de but ou corner). Passe : réussite × danger au point du receveur − (1 − réussite) × danger adverse au milieu de la trajectoire (lieu probable de l'interception). Conduite : chance de garder × danger au point atteint − (1 − chance de garder) × danger adverse au point de départ.

**Conduite.**
- 5 directions : droit vers le but adverse, deux diagonales à 45°, deux côtés à 90°. Pas de direction vers l'arrière : le retrait passe par la passe.
- Espace libre : points tous les 2 m jusqu'à 10 m (portée d'environ 1,5 s de conduite). Un point est libre si le porteur, à sa vitesse balle au pied (`DRIBBLE_SPEED_FACTOR`), y arrive au moins 0,3 s avant tout défenseur (`defense.arrival_time_s`). Point atteint = dernier point libre ; aucun point libre = la conduite reste sur place, en duel.
- Chance de garder le ballon : courbe Dribbling 99 → 95 %, 55 → 85 %, 11 → 70 %, multipliée par (1 − 0,5 × gêne).

**Mécanismes livrés, même sens dans la nouvelle monnaie.**
- Contre-attaque (ticket 11) : gain ×1,3, coût de la perte ×0,7 ; conservation : gain ×0,7, coût ×1,3.
- Valeur future (ticket 13) : part de la suite 0,4, inchangée.
- Plan tenu (ticket 14) : valeur ×1,3, inchangé (`PLAN_BONUS`).

**Perception.**
- Decisions : erreur aléatoire ajoutée à chaque valeur perçue, d'écart-type égal à une part de la meilleure valeur réelle : 99 → 15 %, 55 → 45 %, 11 → 90 % (valeurs de départ). Ces trois parts sont **ajustées après mesure** pour que le taux de meilleur choix suivi, en moyenne sur un match, tombe sur la courbe validée (95 / 70 / 45 %, tolérance ± 5 points).
- Composure : l'écart-type est multiplié par 1 + gêne × k, avec k 99 → 0,2, 55 → 0,6, 11 → 1,0 (soit ×1,2 à ×2 au contact, rien sans adversaire à moins de 5 m).
- Anticipation : part du déplacement des défenseurs prolongée pendant la course du porteur : 99 → 100 %, 55 → 65 %, 11 → 30 %.
- Vision : inchangée.

**Chiffres réels.** Part des passes en arrière (24-42 %, de mémoire) : non sourcée, rapportée sans en faire un critère.

## Mise à jour après mesure (04/11/2026) — validée par délégation du propriétaire

Remplace, là où elles diffèrent, les constantes proposées le 03/11/2026.

- **Chance de garder le ballon en conduisant** : courbe Dribbling 99 → 95 %, 55 → 83 %, 11 → 71 % au contact ; sans adversaire à moins de 5 m, seul un dixième de ce risque (mauvaise touche, `FREE_TOUCH_SHARE`) : sans lui, une conduite dans le vide perdait le ballon 17 fois sur 100.
- **Course des adversaires** (corrigée après la revue de l'expert, anomalie A1) : l'adversaire garde son élan pendant un temps de réaction de 0,3 s (`REACTION_S`), puis court droit au point à sa vitesse max, sans montée en vitesse ; jamais plus vite que sa vitesse max depuis t = 0 (test d'invariant). La faible Anticipation ne prolonge qu'une part de cet élan. Marge de 0,3 s conservée (le porteur doit arriver 0,3 s avant).
- **Meilleur choix suivi** : un choix qui perd moins de 10 % de la valeur du meilleur compte comme le meilleur choix (« erreur légère » du panneau). En match, 60 % des décisions ont une deuxième option à moins de 10 % de la meilleure.
- **Choix en deux temps** (après la revue de l'expert, A4) : 1) la direction de conduite, avec une erreur par direction tirée une fois et gardée pendant la possession (tirée toutes les 0,5 s, elle faisait zigzaguer : 45 % des conduites consécutives changeaient de cap de 90° ou plus ; après : 3,2 %, 2,1 % de quasi demi-tours, 3 matchs de 15 min) ; 2) cette conduite, chaque passe et le tir, une erreur fraîche par option. La conduite compte pour une option et non cinq (cinq chances de paraître la meilleure : 62 % de conduites).
- **Erreur de Decisions** (écart-type, en part de la meilleure valeur, linéaire entre les repères) : 11 → 110 %, 40 → 42 %, 55 → 36 %, 75 → 26 %, 99 → 8 %. Mesuré (6 matchs de 15 min, graine d'audit ; décisions, taux, courbe, écart médian des erreurs) : 0-40 : 22, 50,0 %, 67,7 %, 0,95 ; 40-55 : 130, 69,2 %, 69,9 %, 0,41 ; 55-65 : 423, 67,8 %, 70,1 %, 0,27 ; 65-75 : 737, 68,2 %, 70,9 %, 0,30 ; 75-100 : 210, 75,7 %, 74,0 %, 0,35. La tranche 0-40 est trop peu peuplée en Ligue 1 pour conclure.
- **Arbitrage du propriétaire (04/11/2026)** : la courbe validée, en moyenne sur un match, prime sur « un bon choix évident est vu par presque tous ». Les deux se contredisent quand la plupart des décisions de match sont serrées. Un choix nettement meilleur (tir à 6 m, deux fois la meilleure conduite) est vu par presque tous les bons décideurs et souvent manqué à Decisions 20 (test : au moins 95 % à 95, 40 points de plus qu'à 20). Les effets des tickets 13 et 14 se lisent à Decisions 99 dans les tests (plan tenu +56 points, Teamwork +23 points, passe qui ouvre la suite 25 % contre 6 %), et sont estompés à 55 (+10, +4 ; 16 % contre 13 %).
- **Tir contré (version minimale, avant le ticket 28)** : un défenseur de champ entre le tireur et le but, à moins de 1 m de la ligne de tir, contre avec la chance 60 % pile dans la ligne, de moins en moins vers le bord ; même règle pour la valeur du tir et sa résolution ; le ballon rebondit sur lui (déviation jusqu'à 60°, moitié de la vitesse), libre.
- **Chance de but selon la distance** : divisée par deux tous les 5 m au-delà de 6 m (avant : baisse linéaire jusqu'à 10 % à 30 m, soit 14 % de but à 25 m), plancher 1 % (avant 3 %). Ordres de grandeur « expected goals » de mémoire, à sourcer au ticket 28. Sans ce changement, le tir à 25-30 m était le meilleur choix factuel avec une marge énorme (0,049 contre 0,009) et le match comptait 7,7 buts.

## Mesure avant / après (6 matchs de 90 min, graine d'audit ; après la correction de la revue)

| Indicateur | Avant (cd441d8) | Après |
|---|---|---|
| Passes par minute | 14,2 | 10,6 |
| Choix : passe / conduite / tir | 70 % / 28 % / 1,3 % | 56 % / 39 % / 4,7 % |
| Tirs par équipe | 11,3 | 33,0 |
| Tirs de près (16 m) par équipe | 1,2 | 5,8 |
| Buts par match | 2,83 | 3,83 |
| Corners par match | 1,3 | 7,7 |
| Sorties de but par match | 9,2 | 32,7 |
| Temps de jeu effectif | 89 % | 71 % |
| Part du temps en dernier tiers | 8,5 % | 9,5 % |
| C2 (passe sans gain suivie d'une passe qui fait avancer) | 0,31 | 0,36 |
| Une-deux / troisième homme par équipe | 6,7 / 14,4 | 4,4 / 14,5 |
| Plans tenus | 36 % | 34 % |
| Km par joueur de champ | 20,3 | 16,7 |
| Calcul par match | 260 s | 118 s |

Déterminisme : même empreinte sur deux exécutions à graine fixée (`33980f7dcffe730d`, 5 min, clubs 2 et 3).

**Réserve (acceptée par le propriétaire le 04/11/2026) : volume de tirs.** 33 tirs par équipe après correction (36,5 avant ; réel environ 12), avec ce qu'il entraîne : sorties de but (32,7 par match) et temps de jeu effectif (71 %). Même à perception parfaite (erreur nulle), 42 : le tir est le vrai meilleur choix factuel parce que les équipes arrivent trop souvent à portée de tir (conduites qui passent presque toujours, 42 tirs par match après une récupération dans le camp adverse). Repris par le ticket 28 (qualité de l'occasion, défenseurs dans le cône, pression sur le tireur) puis par la calibration (ticket 22).

## Comments

- 04/11/2026, passage 1 : expert REJECTED, QC VALIDÉ, clôture REFUSÉ. Bloquant A1 : la course des défenseurs comptait deux fois le temps d'élan (vitesse implicite jusqu'à 2 fois la vitesse max) ; l'effet d'Anticipation reposait sur ce défaut. Mesure demandée A4 : 45 % des conduites consécutives changeaient de cap de 90° ou plus. Facultatifs : panneau non aligné sur le ticket (A5), commentaire périmé (A6), critère 2 trop lâche (A8). Corrigés : temps de réaction `REACTION_S` 0,3 s avec test d'invariant ; choix en deux temps (erreur gardée par direction, conduite comptée pour une option) ; panneau ; commentaire ; critère 2 resserré ; erreur de Decisions recalée.
- 04/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ. Réserves acceptées par le propriétaire (« Considère que je valide automatiquement toutes les recommandations des experts », 04/11/2026) :
  - R1 : 33 tirs par équipe (réel environ 12), sorties de but et temps de jeu effectif en conséquence ; tickets 28 (tirs ramenés à 8-15) et 22 (buts remesurés sur plus de matchs).
  - R2 : Dribbling dans la valeur de la conduite, pas dans la résolution des duels ; à aligner au ticket `v2-attributs-restants/07` avec un test d'égalité statistique.
  - R3 : suite complète à relancer sur l'arbre recombiné après remise en place du travail non commité d'une autre session (feuille de match), tous les tests attendus au vert.
  - R4 : écart médian des erreurs en match de 0,27 à 0,41 ; à suivre au ticket 22 (part des erreurs au-delà de 50 %, écart en valeur absolue).
  - Facultatifs non traités : seuil 0,4 « nette » / « lourde » du panneau (F1), déviation du contre centrée sur le but (F2, chantier `but-contre-son-camp`), erreur gardée si le même joueur reprend le ballon (F3).
