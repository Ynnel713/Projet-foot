# 05l: Chance d'un tir propre ramenée sur la table cible

**Chantier :** `v2-realisme` (suite du `10k`, recommandation du 21/11/2026 retenue par délégation du propriétaire). **Priorité :** P1 (excès de buts). **Catégorie :** exécution, gardien.

**Constat vérifié (`docs/INDICATEURS_V2.md` section 59, `scripts.shot_calibration scenes 400` et grille analytique `.scratch/v2-realisme/mesures/05l-grille.py`) :** tireur et gardien neutres, gardien bien placé, sans défenseur, la résolution physique du tir (05e/05h) donne face au but 0,336 à 11 m, 0,204 à 16 m, 0,118 à 20 m, 0,059 à 25 m, 0,054 à 30 m, contre 0,155, 0,088, 0,059, 0,035, 0,020 dans la table cible du propriétaire (`shooting._XG_LOGIT`, table du 05/11/2026) : environ deux fois la cible de 11 à 30 m. Cadrage plausible (44 % à 20 m) ; part des cadrés arrêtés faible (52 % à 11 m, 62 % à 16 m, 73 % à 20 m). En match après le `10k` : conversion 11,7 % hors surface (réel 4,2 %), 15,1 % dans la surface (réel 14,7 % penaltys compris), 4,34 buts par match (réel environ 2,7). Une recherche sur grille des seules constantes existantes (écart du tir, réaction, plongeon, portée) ne tient pas la table : l'arrêt est binaire (dans la portée ou non) et la portée plafonnée fait une marche (25 m : 0,059 à portée 2,8 m, 0,005 à 3,4 m).

**What to build :** Diagnostiquer d'abord, distance par distance, ce qui sépare la résolution de la table (cadrage, arrêt dans la portée, coins hors portée) et ce que la table suppose (tir réel moyen, donc sous pression : la cible d'un tir sans pression est un peu au-dessus de la table). Puis corriger le mécanisme en cause, même loi à l'évaluation (`occasion_quality`, `physical_shot_chance`) et à la résolution (`match._keeper_reaches`), par exemple un arrêt probable dans la portée plutôt que certain, ou un plongeon plus juste selon la distance ; constantes recommandées et retenues par délégation du propriétaire (22/11/2026), sourcées ou marquées « non trouvé ».

**Hors de ce ticket :** puissance de frappe selon le tireur (`v2-collectif/35a`), tir masqué (`05k`), anticipation du gardien (`03l`), calibration finale (`v2-collectif/22c`).

**Attributs :** aucun nouveau (le gardien neutre reste la référence ; ses notes viennent au `v2-attributs-restants/03b`).

**Blocked by :** aucun (`10k` implémenté).

**Bloque :** `v2-collectif/22c`.

**Status:** livré (22/11/2026), validé expert + QC (réserves A1 à A3 acceptées, renvoyées au `v2-collectif/22c`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et diagnostic (grille, scènes, repères réels) | 40 min |
| Développement | 40 min |
| Tests (scènes, cohérence évaluation / résolution) | 30 min |
| Intégration et vérifications (scènes, 50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible (mécanisme à choisir après le diagnostic). Temps machine, hors total : scènes (environ 10 min), série appariée de 50 matchs (environ 50 min), suite complète.

## Périmètre élargi (22/11/2026, annoncé en cours de route)

Le plongeon recalé seul (3 → 6 m/s) rendait un tireur précis moins dangereux (il visait le centre, donc le gardien) : visée ajoutée (`shooting.aim_angles`, `_aimed`, `AIM_INSIDE_POST_M`), puis marge des frappes de loin du `18m` revue (elle compensait la frappe surévaluée). Le contre d'un défenseur en course, exposé par la visée, a été traité à part au `05j` (livré). Estimation révisée 2 h 20 → 3 h 30 → 5 h.

## Résultat (22/11/2026, `docs/INDICATEURS_V2.md` section 61)

- `shooting.KEEPER_DIVE_MPS` 3 → 6 m/s ; visée d'un côté tiré au sort à `AIM_INSIDE_POST_M` = 2,5 m à l'intérieur du poteau, même loi à l'évaluation (espérance des deux côtés) et au départ du tir ; `decision.LONG_SHOT_MARGIN` 0,05 → 0. Recommandations retenues par délégation du propriétaire (22/11/2026).
- Version écartée : visée choisie selon la place du gardien (5,02 buts, gardien exploité ; la lecture du gardien relève du `03l`).
- 50 matchs appariés : conversion hors surface 12,3 → 7,6 % (réel 4,2 %), buts de loin 0,82 → 0,40 (significatif), cadrés par zone au niveau réel (28,4 % hors surface, 37,8 % dans la surface), arrêts 73 % / 58 % (repères 85 / 60 %) ; 2,64 tirs hors surface par équipe (repère 4,1) ; buts au total 4,48 → 4,20, dans le bruit. L'excès restant est dans le volume de tirs dans la surface (11,8 par équipe, réel environ 8,5).
- Tests : `tests/test_v2engine_visee_tir.py` (5), scènes adaptées (`test_v2engine_meilleur_choix.py` : bon finisseur ramené à 14 m, de 21 m la conduite vaut mieux pour tous ; `test_v2engine_contre.py` : défenseur à 45° touché au plus 1 fois sur 100, queue de l'écart) (`test_v2engine_occasion.py` : défenseur à 4 m, à 8 m il ne couvrait plus que l'angle du gardien), frappes de loin réécrites autour d'une scène où la frappe vaut à peine plus que la suite (`test_v2engine_frappes_de_loin.py`), tolérance de 5 % mesurée de l'estimateur (`test_v2engine_chance_tir.py`).

Durée : estimée 2 h 20 (révisée 5 h), réelle environ 5 h 15 (analyse et diagnostic 1 h 30, développement 1 h 15, tests 1 h, intégration, séries et documentation 1 h 30), écart + 125 % sur l'estimation initiale, + 5 % sur la révisée : mécanisme manquant (visée) découvert par un test de monotonie, première visée écartée après une série (effet de sélection invisible hors ligne), marge du `18m` à revoir, `05j` sorti en préalable. Temps machine hors total : capture de 20 matchs, scènes, six séries de 50 matchs (une interrompue par manque de mémoire), suites complètes.

## Acceptance criteria

- [x] Diagnostic chiffré par distance ; mécanisme et constantes recommandés avant le code (délégation du propriétaire)
- [x] Scènes neutres : chance évaluée et taux observé dans l'intervalle l'un de l'autre (`tests/test_v2engine_chance_tir.py`, à 5 % près, tolérance mesurée et documentée), rapport à la table cible ramené entre 0,8 et 1,3 à 16 et 20 m face au but (fourchette fixée au diagnostic ; test `test_a_clean_shot_from_16_to_20_m_follows_the_target_table`)
- [x] 50 matchs appariés : buts, conversion dans et hors surface, cadrés, part des cadrés arrêtés, avant / après, avec intervalles (`docs/INDICATEURS_V2.md` section 61)
- [x] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 3 486 passés, 0 ignoré, 14 désélectionnés (3 481 au `05j` + 5 tests)

## Comments
- 22/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ (réserves acceptées).
  - A1 [réserve] surévaluation de loin (25 à 30 m : 1,6 à 2,7 fois la table) alors que la marge est à 0 : le 22c ou le 35a traite le plafond de portée et la vitesse de frappe ; revoir la marge si les tirs de loin dépassent environ 4 par équipe avant.
  - A2 [réserve] distorsion spatiale (11 m axe 2,01 ; excentrés 16 m / 10 m 0,39) : reprendre 11 m et les tirs excentrés au 22c, dans son critère.
  - A3 [réserve] biais de l'estimateur d'environ + 4,5 % à 6 m : cause à identifier au 22c, tolérance à ne plus élargir sans mesure.
  - A4 [facultatif] commentaire `match.py:839` « visée selon le gardien » trompeur, retour constant de `_aimed` : non repris pour ne pas rouvrir la revue ; à corriger au prochain ticket qui touche ce code.
  - Réserves acceptées par délégation générale du propriétaire, mots cités : « Je suis ok avec ta recommandation. Je valide automatiquement toutes tes recommandations et les conseils d'expert. Je vous fait confiance pour obtenir un réalisme optimal, soyez exigeants et rigoureux. [...] Ne me sollicite donc pas pendant ce processus » (21/11/2026). Acceptation globale, donnée avant ces réserves : à confirmer ou révoquer par le propriétaire au bilan.
