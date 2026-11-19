# 10c: Couverture de la profondeur derrière la ligne

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'espace dans le dos est le premier danger d'une ligne haute). **Catégorie :** placement.

**Constat vérifié :** un seul couvreur, placé 6 m derrière le porteur sur l'axe porteur-but (`COVER_DEPTH_M`), seulement dans la moitié défendue.

**What to build:** Quand une passe en profondeur est possible (attaquant dans le dos possible, espace derrière la ligne), le défenseur le plus éloigné du ballon de la dernière ligne se place légèrement plus bas que la ligne (décalage validé) côté opposé au ballon, sans casser le piège du hors-jeu au moment des passes.

**Attributs :** aucun

**Blocked by:** 10b (Le défenseur central ne quitte sa ligne que couvert).

**Bloque :** 10j.

**Status:** livré (19/11/2026), validé expert + QC

## Constantes et critères (19/11/2026, proposés par Claude, validés par délégation du propriétaire : « Je valide automatiquement toutes tes recommandations et celles de l'expert »)

Chiffres réels non trouvés (les guides tactiques décrivent le latéral opposé « en couverture », un peu plus bas que la ligne, sans le chiffrer) ; ordres de grandeur, à recalibrer au 27b.

- **Passe en profondeur possible :** le porteur adverse n'est pas pressé (aucun défenseur à `PRESSED_M` = 3 m ou moins, constante existante du bloc) et la dernière ligne sans ballon est à `DEPTH_SPACE_M` = **25 m** au moins de son but (espace dans le dos).
- **Qui :** le défenseur de la dernière ligne de la forme de départ (même bande que le critère Pace du ticket 05 : 1 m de la ligne la plus basse) le plus éloigné du ballon dans la largeur.
- **Décalage :** sa place sans ballon recule de `DEPTH_DROP_M` = **3 m** vers son but (« légèrement plus bas »).
- **Piège du hors-jeu :** le décalage ne s'applique que si aucun attaquant n'est au-delà de la ligne (plus près du but que la hauteur de ligne) : il ne remet jamais en jeu, à cet instant, un attaquant hors jeu.
- **Critères (100 matchs appariés, banc du 10b2, « avant » = commit `1282f00`) :** passes en profondeur réussies de l'adversaire rapportées (baisse attendue) ; hors-jeu par match dans ± 10 % (pas de chute non expliquée) ; buts, tirs, tacles, fautes dans ± 10 % ; minutes de couverture de la profondeur par match tracées ; déterminisme à graine fixée.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : conflit possible avec le piège du hors-jeu (ticket 23) : mesure du hors-jeu obligatoire.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Réalisation (19/11/2026)

**Code :** `v2engine/bloc.py` : constantes `DEPTH_SPACE_M` = 25 m et `DEPTH_DROP_M` = 3 m ; `Bloc.update` désigne, par équipe, le défenseur qui couvre la profondeur (`Bloc.depth_cover`) quand le porteur adverse n'est pas pressé (`PRESSED_M`), que la dernière ligne sans ballon est à 25 m au moins de son but et qu'aucun attaquant n'est au-delà de la ligne (même lecture que la hauteur de ligne, mémoire de perception comprise) ; c'est le défenseur de la dernière ligne de la forme de départ le plus éloigné du ballon dans la largeur ; `Bloc.reference` recule sa place sans ballon de 3 m vers son but. Trace : `MatchTrace.depth_covers` (`DepthCoverRecord`, à chaque changement), écrite dans `match.simulate_match`, lecture seule. Tests : `tests/test_v2engine_profondeur.py`, 7 tests (recul du côté opposé, côté qui suit le ballon, pas de recul porteur pressé, attaquant au-delà, ligne sous 25 m, avec ballon ; trace déterministe) ; chaque condition retirée seule fait échouer son test.

**Mesure, 100 matchs appariés** (collecteur des indicateurs `scripts.measure_v2.run`, graines `AUDIT_SEED + k`, k = 0 à 99 ; `.scratch/v2-realisme/mesures/10c-profondeur.py` et `10c-comparaison.py`, sortie `10c-comparaison.txt` ; « avant » = commit `1282f00` lancé depuis un worktree) :

| Par match | avant | après | écart (IC 95 %) | critère |
|---|---|---|---|---|
| Buts | 4,97 | 5,04 | + 1,4 % [− 10,6 ; + 13,4] | ± 10 % : tenu |
| Tirs | 41,94 | 41,01 | − 2,2 % [− 5,6 ; + 1,2] | tenu |
| Tacles | 39,81 | 40,06 | + 0,6 % | tenu |
| Fautes | 19,15 | 19,64 | + 2,6 % | tenu |
| Hors-jeu | 3,76 | 3,70 | − 1,6 % [− 15,6 ; + 12,4] | ± 10 % : tenu en estimation ponctuelle, pas de chute (l'IC, environ ± 14 % sur 100 matchs, ne permet pas de le démontrer) |
| Passes en profondeur | 16,73 | 16,83 | + 0,6 % | rapporté |
| Passes en profondeur réussies | 9,93 | 9,84 | − 0,9 % [− 10,5 ; + 8,6] | rapporté : baisse non démontrée |
| Appels dans le dos | 154,7 | 151,4 | − 2,2 % | |
| Couverture de la profondeur (min, deux équipes) | 0 | 4,52 | | tracée |

**Pourquoi l'effet est faible (diagnostic sur 4 matchs, script hors dépôt `diag10c.py`)** : sur les ticks où l'adversaire porte le ballon, le porteur est pressé dans 72 % des cas et un attaquant est au-delà de la ligne dans 72 % (le piège du ticket 23 tient la ligne jusqu'à 5 m au-dessus de l'attaquant le plus avancé) ; les trois conditions ne sont réunies que 9,6 % du temps (environ 4,6 min par match), ce que la trace confirme. La condition « personne au-delà de la ligne » est celle qui protège le piège (validée) ; l'assouplir (reculer jusqu'au niveau de l'attaquant le plus avancé seulement) doublerait environ le temps de couverture, à décider dans un ticket suivant.

**Déterminisme** : deux processus séparés, matchs complets, mêmes empreintes (20260923 : 1-1, `a8c8f2857974` ; 20260924 : 0-0, `76e01fcbf8e2`) ; test `test_depth_covers_are_traced_and_deterministic`.

**Suite complète** (19/11/2026) : 3 437 passés, 0 ignoré, 14 désélectionnés (3 430 après le 10b2 + 7 tests nouveaux), 13 min 05.

**Durée réelle** : environ 1 h 45 de travail effectif (analyse 30 min, développement 30 min, tests 25 min, intégration et vérifications 20 min) contre 2 h estimées, soit − 13 %. Temps machine hors total : 200 matchs (environ 2 h 30), suite complète, diagnostic de 4 matchs, une paire d'empreintes. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée.


- **Unitaires (scène contrôlée) :** ligne haute, ballon à droite : le défenseur gauche est en retrait de la valeur validée
- **Statistiques (séries de matchs) :** 50 matchs : passes en profondeur réussies et hors-jeu

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (par délégation, 19/11/2026)
- [x] Couverture tracée (`MatchTrace.depth_covers`, 4,52 min par match)
- [x] Hors-jeu par match rapporté (pas de chute non expliquée) : 3,76 → 3,70 (− 1,6 %)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (3 437 passés)

## Comments

- **19/11/2026, passage 1 :** expert APPROVED_WITH_RESERVATIONS. Réserves : A1 couverture perdue pendant le vol du ballon ; A2 aucune stabilité temporelle de la désignation ; A3 effet sur le jeu non démontré → ticket de suivi `10c2`. A4 (facultatif) : chiffres de la fiche (72 %, IC des hors-jeu) → corrigés. Réserves A1 à A3 acceptées par le propriétaire : « Je valide automatiquement toutes tes recommandations et celles de l'expert » (19/11/2026). QC VALIDÉ. Clôture journalisée : VALIDÉ.
