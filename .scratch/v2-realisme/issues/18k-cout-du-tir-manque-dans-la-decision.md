# 18k: Le tir manqué coûte le ballon dans la décision

**Chantier :** `v2-realisme`. **Priorité :** P0 (le volume et le mélange des tirs en dépendent ; à faire avant `v2-collectif/22c`). **Catégorie :** décision.

**Origine :** ticket 18e (12/11/2026, diagnostic de 50 matchs, `.scratch/v2-realisme/mesures/18e-zones-avant.txt`), et réserve A2 du ticket `v2-collectif/28a` (05/11/2026), reprise jusqu'ici au `v2-collectif/22a`. Par zone, la conversion est réaliste (surface 17,7 %, hors surface 4,4 % ; réel 14,7 et 4,2 %, Opta Premier League 2024-25). Le mélange ne l'est pas : 14,1 tirs hors surface par équipe et par match contre environ 4,2 dans le réel, dont 6,9 de 25 à 30 m à 0,021 d'xG ; 21,4 % des tirs dans la surface contre 68,3 %. Résultat : 18 tirs par équipe (repère 8 à 15), conversion 7,2 % (10 à 12), buts dans la surface 52 % (88 à 89).

**Constat vérifié :** `decision.evaluate_options` donne au tir la valeur `shooting.occasion_quality` (chance de but) sans contrepartie : la passe et la conduite paient la perte du ballon (`option_value`, `loss_cost`), le tir manqué ne paie rien (sortie de but, corner, ballon contré ou repoussé chez l'adversaire). Un tir à 2 % bat donc toute option de conservation dont la valeur nette est sous 0,02.

**What to build :** Donner au tir, dans la décision, la même monnaie que les autres options : chance de but, plus la valeur de ce qui suit un tir non marqué (ballon rendu à l'adversaire : sortie de but, arrêt capté ; ballon disputé : contré, repoussé ; corner), pondérée par les issues du tir (`shooting._flight_shares`). Pas de constante de pénalité arbitraire : les issues et leur valeur viennent du moteur (issues mesurées, `danger` et `loss_cost` existants).

**Hors de ce ticket :** calibration finale des tirs (`v2-collectif/22c`) ; penaltys (fautes dans la surface, `21b`, `21c`).

**Attributs :** aucun nouveau (Finishing, Long Shots, Decisions déjà en jeu).

**Blocked by :** 18e.

**Bloque :** `v2-collectif/22c`.

**Status :** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 40 min |
| Tests | 30 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne (mécanisme local ; la valeur d'un ballon rendu est déjà calculée pour la passe). À examiner pour découpage avant le code (au-delà de 2 h). Temps machine, hors total : diagnostic des zones (`18e-zones.py`, 50 matchs), série de 50 matchs, suite complète.

## Acceptance criteria

- [x] Valeur du tir dans la décision : chance de but et suite d'un tir non marqué, avec les issues du moteur ; constantes éventuelles proposées et validées avant le code : aucune constante nouvelle (grille de danger et parts de contre existantes) ; règle validée par le propriétaire (« Ok pour le 18k », 13/11/2026, après la recommandation du 18e)
- [x] Scène : tir à 28 m à 0,02 d'xG contre conservation sûre : la conservation l'emporte ; tir à 8 m face au but : le tir l'emporte (`tests/test_v2engine_valeur_tir.py` : à 28 m, chance de but 0,056 sans défenseur dans l'axe, seule elle battait la conduite ; valeur du tir 0,047 contre 0,050)
- [x] Tirs par zone avant/après sur 50 matchs (`18e-zones.py`) : tirs hors surface par équipe 14,1 → 11,6 ; part des tirs dans la surface 21,4 → 27,4 % (réel 68,3 %) ; conversion par zone à 2 points près sur 100 matchs (surface 17,7 → 16,1 %, dehors 4,4 → 5,3 %)
- [x] Tirs par équipe, conversion, buts dans la surface comparés aux repères R1 et R2 : tirs tracés 18,0 → 16,0 par équipe (8 à 15) ; conversion 7,3 → 8,1 % (10 à 12) ; buts dans la surface 51,8 → 48,7 % (88 à 89) ; conversion dans la surface sous surveillance (voir Comments)
- [x] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**13/11/2026, lancement.** Validation du propriétaire : « Ok pour le 18k ». Estimation annoncée : 2 h 20, confiance moyenne ; découpage examiné et écarté (le mécanisme et sa scène vont ensemble, la mesure seule n'a pas de sens).

**13/11/2026, analyse.** À 25-28 m dans l'axe, danger de garder le ballon (grille xT) environ 0,025 à 0,03, tir environ 0,02, passe sûre environ 0,024 : le tir est dans la marge de l'erreur de perception ; un tir manqué coûtait 0 alors que perdre le ballon à son but vaut environ 0,0095 à l'adversaire dans la même grille.

**13/11/2026, règle (recommandée, aucune constante nouvelle).** `decision.shot_value` : chance de but − poids de perte de la transition × [part contrée × `loss_cost` à la place du tireur + part non marquée et non contrée × `loss_cost` au but adverse (sortie de but, gardien)]. Parts de la résolution physique en un seul calcul (`shooting.shot_outcome_shares`, mêmes lois qu'`occasion_quality` et `physical_block_probability`). Approximation : le tir claqué en corner (environ 3 % des tirs) compte comme une perte ; à reprendre au `v2-collectif/22c`.

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/18k-*`).**
- Par zone (50 matchs, mêmes graines que le 18e ; `18k-zones-apres.txt` contre `18e-zones-avant.txt`) : tirs par équipe 18,0 → 16,0 ; hors surface 14,1 → 11,6 ; de 25 à 30 m 6,9 → 3,7 (− 47 %) ; surface 3,85 → 4,39 ; part dans la surface 21,4 → 27,4 % ; xG moyen hors surface 0,041 → 0,054.
- Conversion dans la surface : 17,7 → 13,7 % sur les 50 premiers matchs (60 buts pour 76,3 d'xG, − 2,3 σ) ; 50 matchs de plus (graines 50 à 99, `18k-zones-b-apres.txt`) : 18,4 % (85 buts pour 79,0 d'xG, + 0,8 σ). Sur 100 matchs : 16,1 % dans la surface, 5,3 % dehors (`18k-buts-xg.txt`). La résolution du tir n'est pas touchée : écart dû au hasard.
- Indicateurs généraux (50 matchs, `18k-50-lot*`, synthèse `18k-50-synthese.txt`) : tirs tracés 18,0 → 16,0 par équipe ; cadrés 26,8 → 27,9 % ; contrés 17,6 → 17,3 % ; conversion 7,3 → 8,1 % ; buts dans la surface 51,8 → 48,7 % ; buts 2,62 → 2,58 ; xG neutre 2,61 → 2,78 par match ; distance de tir 22,4 → 21,2 m ; passes 998 → 1 007 ; possession d'équipe 26,9 → 26,1 s ; pertes en conduite 61,5 → 64,8 ; face-à-face 10,3 → 11,9 par match.
- Écart restant : la part des tirs dans la surface (27 % contre 68 %) relève de la pénétration (occupation `09`, passes en profondeur `v2-collectif/32a`, surcharges `v2-collectif/17`), plus du choix de tirer ; conversion globale sous R2 en conséquence.
- Tests : 5 ajoutés (`tests/test_v2engine_valeur_tir.py`) ; `tests/test_v2engine_meilleur_choix.py` adapté (le défenseur dans l'axe multiplie la chance de but par 1 − `BLOCK_CHANCE` ; la valeur du tir, qui paie maintenant le contre, baisse davantage). Suite : 2 802 passés, 0 ignoré, 14 désélectionnés (2 797 + 5 ; `18k-suite.txt`).
- Déterminisme : deux exécutions de `measure_v2 2` identiques hors temps de calcul (`18k-det1`, `18k-det2`). Temps de calcul 70,5 s par match, non comparable aux 63 s du 07c (session sur une autre machine depuis le 13/11/2026) ; le 18k remplace `occasion_quality` par `shot_outcome_shares`, même calcul (`_flight_shares` une fois).

**13/11/2026, passage 1.** Expert : APPROVED. Facultatifs : A1, commentaire de `decision._TRANSITION_WEIGHTS` (« le tir n'en dépend pas ») devenu faux ; A2, docstring de `scripts/shot_calibration.py` (« la décision juge un tir avec `occasion_quality` ») obsolète ; A3, corners, repoussés et contrés comptés comme perte entière (effet environ 0,002 sur la valeur du tir), au `v2-collectif/22c`. A1 et A2 non corrigés ici (toute retouche d'un fichier revu rouvre la revue) : à faire à la prochaine retouche de ces fichiers.
QC : VALIDÉ. Clôture : VALIDÉ (expert APPROVED, QC VALIDÉ).

**Durée.** Estimée 2 h 20. Réelle environ 1 h 45, non chronométrée (analyse 25 min, développement 20 min, tests 25 min, intégration et vérifications 35 min, dont 50 matchs de contrôle supplémentaires sur la conversion en surface) : − 25 %. Temps machine hors total : zones sur 50 + 50 matchs (12 min chacun), série de 50 matchs (25 min), déterminisme, suite complète (11 min).
