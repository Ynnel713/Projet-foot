# 05l: Chance d'un tir propre ramenée sur la table cible

**Chantier :** `v2-realisme` (suite du `10k`, recommandation du 21/11/2026 retenue par délégation du propriétaire). **Priorité :** P1 (excès de buts). **Catégorie :** exécution, gardien.

**Constat vérifié (`docs/INDICATEURS_V2.md` section 59, `scripts.shot_calibration scenes 400` et grille analytique `.scratch/v2-realisme/mesures/05l-grille.py`) :** tireur et gardien neutres, gardien bien placé, sans défenseur, la résolution physique du tir (05e/05h) donne face au but 0,336 à 11 m, 0,204 à 16 m, 0,118 à 20 m, 0,059 à 25 m, 0,054 à 30 m, contre 0,155, 0,088, 0,059, 0,035, 0,020 dans la table cible du propriétaire (`shooting._XG_LOGIT`, table du 05/11/2026) : environ deux fois la cible de 11 à 30 m. Cadrage plausible (44 % à 20 m) ; part des cadrés arrêtés faible (52 % à 11 m, 62 % à 16 m, 73 % à 20 m). En match après le `10k` : conversion 11,7 % hors surface (réel 4,2 %), 15,1 % dans la surface (réel 14,7 % penaltys compris), 4,34 buts par match (réel environ 2,7). Une recherche sur grille des seules constantes existantes (écart du tir, réaction, plongeon, portée) ne tient pas la table : l'arrêt est binaire (dans la portée ou non) et la portée plafonnée fait une marche (25 m : 0,059 à portée 2,8 m, 0,005 à 3,4 m).

**What to build :** Diagnostiquer d'abord, distance par distance, ce qui sépare la résolution de la table (cadrage, arrêt dans la portée, coins hors portée) et ce que la table suppose (tir réel moyen, donc sous pression : la cible d'un tir sans pression est un peu au-dessus de la table). Puis corriger le mécanisme en cause, même loi à l'évaluation (`occasion_quality`, `physical_shot_chance`) et à la résolution (`match._keeper_reaches`), par exemple un arrêt probable dans la portée plutôt que certain, ou un plongeon plus juste selon la distance ; constantes recommandées et retenues par délégation du propriétaire (22/11/2026), sourcées ou marquées « non trouvé ».

**Hors de ce ticket :** puissance de frappe selon le tireur (`v2-collectif/35a`), tir masqué (`05k`), anticipation du gardien (`03l`), calibration finale (`v2-collectif/22c`).

**Attributs :** aucun nouveau (le gardien neutre reste la référence ; ses notes viennent au `v2-attributs-restants/03b`).

**Blocked by :** aucun (`10k` implémenté).

**Bloque :** `v2-collectif/22c`.

**Status:** à faire (diagnostic, puis constantes recommandées avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et diagnostic (grille, scènes, repères réels) | 40 min |
| Développement | 40 min |
| Tests (scènes, cohérence évaluation / résolution) | 30 min |
| Intégration et vérifications (scènes, 50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible (mécanisme à choisir après le diagnostic). Temps machine, hors total : scènes (environ 10 min), série appariée de 50 matchs (environ 50 min), suite complète.

## Acceptance criteria

- [ ] Diagnostic chiffré par distance ; mécanisme et constantes recommandés avant le code (délégation du propriétaire)
- [ ] Scènes neutres : chance évaluée et taux observé dans l'intervalle l'un de l'autre (`scripts.shot_calibration scenes`), et rapport à la table cible ramené dans une fourchette fixée au diagnostic
- [ ] 50 matchs appariés : buts, conversion dans et hors surface, cadrés, part des cadrés arrêtés, avant / après, avec intervalles
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
