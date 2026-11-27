# 03b: Mains du gardien, un seul modèle de portée

**Ouvert le 27/11/2026**, découpage du ticket 03.

**What to build:** la tranche « mains » du gardien, isolée du code des joueurs de champ, et commune aux deux chemins où le gardien joue le ballon :
1. `portee.keeper_hands_ceiling(...)` : plafond des mains, bras levés (z + r ≤ 1,258 H + détente ; épaule 0,818 + bras 0,186 + avant-bras 0,146 + main 0,108, Winter), dans sa propre surface. Hors de sa surface, le gardien suit les tranches de champ (Lois du jeu).
2. **Tir en vol** (`_keeper_reaches`, code des arrêts) : portée latérale du 05b inchangée ; le tir n'est atteint que s'il passe sous ce plafond au point de passage (le tir capté à 1,01 m du 02b2 le reste ; un lob au-dessus de ses mains passe).
3. **Ballon libre** (`_step_loose_ball`) : même plafond, par un seul aiguillage (`gardien dans sa surface → mains, sinon tranches de champ`).
4. Aerial Reach reste au `v2-attributs-restants/03a`.

**Constantes** : validées par le propriétaire le 27/11/2026 (voir 03a), aucune nouvelle.

**Blocked by:** 03a.

**Status:** livré (27/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 10 min |
| Développement | 25 min |
| Tests | 25 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Temps machine hors total : série de 50 matchs, suite complète.

## Acceptance criteria

- [x] Scène fixe : le gardien capte dans sa surface un ballon libre hors de portée d'un joueur de champ de 1,83 m (Jumping Reach 60)
- [x] Scène fixe : tir à 1,01 m capté par `_keeper_reaches` ; tir au-dessus du plafond des mains non atteint
- [x] Test d'isolation : la tranche « mains » n'est lue que par l'aiguillage ; hors de sa surface, le gardien suit les tranches de champ
- [x] 50 matchs avant/après : arrêts, buts, prises du gardien sur ballon libre, réceptions « centre » ; écarts expliqués
- [x] Mêmes empreintes à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [x] (ajouté en cours de route) Estimateur de tir aligné sur la résolution ; `scripts/shot_calibration.py scenes` calibré

## Comments

**27/11/2026, périmètre élargi avant le code (annoncé au propriétaire)** : l'estimateur de tir (`shooting.physical_shot_chance`, lu par la décision de tirer et l'xG) doit suivre la résolution (« toute modification de la résolution […] se reporte ici ») : un tir sous la barre qui passe au-dessus des mains du gardien n'est plus arrêté, l'estimateur doit le compter. Nouvelle estimation : **2 h 10** (+ 30 min : estimateur 20, tests 10), au-delà du seuil de 2 h ; pas de découpage (résolution et estimateur doivent changer ensemble).

**27/11/2026, implémentation.**

*Code* : `v2engine/portee.py` : `HANDS_SHARE` (0,818 + 0,186 + 0,146 + 0,108 = 1,258), `keeper_hands_ceiling(H, détente)` (`z ≤ 1,258 H + détente − r`), `keeper_band` (pied sous la hanche, mains au-dessus, `None` au-dessus des mains), aiguillage unique `uses_hands` (gardien dans sa propre surface) lu par `player_ceiling_m` et `player_band` ; `neutral_keeper_ceiling_m` (repli de l'estimateur sans gardien). `match._keeper_reaches` : tir non atteint si le bas du ballon passe au-dessus de `player_ceiling_m(gardien)` au point de passage (portée latérale du 05b inchangée) ; xG après frappe 1 dans ce cas (tir cadré qu'il ne peut pas toucher, règle du tir sans gardien). `match._step_loose_ball` : inchangé hors la tranche tracée (ramenée au plafond en cas d'arrondi : tête ou mains) ; le gardien y passe par le même aiguillage. `shooting._goal_angles` / `_flight_shares` : dans l'angle couvert par le gardien, marquent les tirs sous la barre qui passent au-dessus de son plafond au temps de vol jusqu'à lui (`_under_error`, loi de hauteur du moteur ; ponytail : indépendance avec la hauteur des contres). `ReceptionEvent.band` : `mains`. Indicateur ajouté : `réceptions contrôlées du gardien, tranche : …` (scripts `v2_indicators`, `measure_v2`, `bench_series`). Aerial Reach reste au `v2-attributs-restants/03a`.

*Tests* : `tests/test_v2_mains_gardien.py`, 14 tests (constantes, tranches, aiguillage dans et hors de la surface et dans la surface adverse, isolation par l'AST : `keeper_hands_ceiling` et `keeper_band` appelés seulement par l'aiguillage dans `portee`, note neutre de Jumping Reach, ballon libre à 2,55 m capté par le gardien dans sa surface et pas par un 1,83 m ni par le gardien hors de sa surface, `_keeper_reaches` à 1,01 m et au-dessus des mains, hors surface aux tranches de champ, en match : tir ras de 20 m arrêté, tir de 35 m sur un gardien à 10 m de sa ligne qui passe au-dessus de ses mains (but, arrêté avant le 03b), estimateur : part au-dessus des mains positive pour le gardien sorti, nulle sur sa ligne, chance de but qui monte quand le plafond baisse, plafond de champ hors de la surface). Aucun test existant modifié. Suite complète : **3 652 passés, 0 ignoré, 14 désélectionnés** (3 638 + 14), 18 min ; `CLAUDE.md` mis à jour (3 652, décision du propriétaire du 27/11/2026, au lieu du 3 638 demandé d'abord).

*Calibration de l'estimateur* (`scripts.shot_calibration scenes 500`) : 20 positions sur 20 « calibrées » (chance évaluée dans l'intervalle de Wilson du taux de buts de la vraie trajectoire).

*Série de 50 matchs* (graines 0 à 49) : avant = `03b-avant.json` (code de `c6f3869`, worktree, scripts d'indicateurs du 03b reportés), après = `03b-apres.json` ; bruit = séries A/B du 02a1 (`03b-tolerance.py`, `03b-tolerance.txt`). 2 821 indicateurs : **1,0 % hors bruit** (3,2 % entre A et B), tous en cases à effectif minuscule ou à bruit nul (rendement par tranche de 15 min, quartiles, parts du gardien sur 12 cas).
- Buts 4,28 → 3,98 par match (0,3× le bruit), arrêts 6,64 → 6,46 (0,2×), tirs par équipe 13,81 → 13,5, réceptions « centre » 0,92 → 1,02.
- Prises du gardien sur ballon libre : mains 0 → 0,02 par match (une en 50 matchs), pied 10,3 → 10,0, tête (hors surface) 0,08 → 0,06. Effet faible attendu : peu de ballons libres passent dans la surface entre la tête des joueurs de champ et les mains du gardien ; les centres restent au `v2-attributs-restants/01` et `03a` (sorties aériennes).
- Lobs au-dessus des mains : seulement sur un gardien loin de sa ligne (scène : 10 m sur un tir de 35 m) ; gardien à moins de 6 m, tout tir cadré passe sous ses mains (scènes de 18 à 30 m).
- Temps de calcul : série 189 → 345 s par match, non comparable (série « après » en parallèle d'autres calculs, « avant » seule ; première série « avant » tuée par manque de mémoire, relancée seule) ; mesure appariée seule, temps processeur : graine 2 142,6 → 153,2 s (+ 7 %), graine 3 148,8 → 149,1 s (+ 0,2 %) ; coût propre : une dichotomie de 16 pas par évaluation de tir quand le gardien couvre une part du but.

*Déterminisme* : empreintes (`14a1-empreinte.py`, graines 0 et 1) identiques sur deux exécutions : `3465b8269d5b8016`, `2a695a3fd33e2cd0` (`03b-empreintes-1.txt`, `-2.txt`) ; différentes du 03a (jeu changé). Graine 0 : 0-2 → 3-2, divergence chaotique (aucun des 5 buts n'est passé au-dessus des mains). V1 : aucun fichier touché.

*Durée* : estimée 1 h 40, réestimée 2 h 10 avant le code (estimateur) ; réelle environ 2 h 25, non chronométrée (horloge de la session hors attentes machine), + 45 % sur l'initiale, + 12 % sur la révisée. Postes : analyse 20 min (10), développement 40 min (25), tests 30 min (25), intégration 55 min (40). Cause : l'estimateur de tir (ajout annoncé), la série « avant » à relancer (manque de mémoire), la mesure de temps appariée. Temps machine hors total : deux séries de 50 matchs (environ 45 min chacune, plus une interrompue), une suite complète (18 min), une calibration, deux paires d'empreintes.

**Points à vérifier à l'écran** : un ballon libre capté aux mains dans la surface ; un lob qui passe au-dessus d'un gardien sorti.

**27/11/2026, clôture (passage 1)** : expert `APPROVED_WITH_RESERVATIONS` ; QC `VALIDÉ` ; clôture journalisée `VALIDÉ` (réserve acceptée).
- Réserve A1 (expert) : terme « tir au-dessus des mains d'un gardien sorti » de l'estimateur vérifié seulement en sens. Vérification faite hors dépôt (`mesures/03b-gardien-sorti.py`, `.txt`, scène de `shot_calibration` avec le gardien à 6, 8 et 10 m, tirs de 25 à 35 m, 500 tirs par case ; empreinte du dépôt identique avant et après) : 17 cases calibrées sur 18, seule hors intervalle gardien à 6 m, tir de 35 m dans l'axe (3,5 % évalué contre 5,8 % observé [4,1 ; 8,2]). **Acceptée par le propriétaire le 27/11/2026** (« J'accepte A1 »). Reste à faire : scène « gardien sorti » dans `scripts/shot_calibration.py`, avant tout ticket qui s'appuie sur le tir de loin ou le lob.
- Facultatif A2 (expert) : sous la hanche, le gardien dans sa surface est tracé « pied » alors qu'il ramasse souvent à la main ; l'indicateur « réceptions contrôlées du gardien, tranche : pied » mélange les deux (trace seulement, sans effet sur le jeu).
- À surveiller (expert) : fréquence des lobs réussis et des prises aux mains quand arriveront les centres et les sorties aériennes (`v2-attributs-restants/01`, `03a`).
- Non bloquants (QC) : longueur de la ligne `__all__` de `portee.py` ; temps par match de la série non comparable (mesure appariée + 7 % / + 0,2 %).
