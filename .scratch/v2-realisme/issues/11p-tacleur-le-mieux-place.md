# 11p: Le tacleur le mieux placé tente, pas seulement le plus proche

**Chantier :** `v2-realisme` (réserve A1 de l'expert à la clôture du 11h, acceptée par le propriétaire le 16/11/2026 : « Accepter + nouveau ticket »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11h, 50 matchs appariés) :** les tacles tombent de 37,3 à 22,1 par match, sous le repère réel de 30 à 40 (`docs/INDICATEURS_V2.md`, réserve du ticket 22). Une cause antérieure au 11h amplifie la baisse : un seul tirage de tentative par pas, pour l'adversaire **le plus proche** du porteur à portée (`match._nearest_opponent_in_range`, appelé dans `_step_ball`). Un défenseur placé dans le dos du porteur, devenu prudent (facteur 0,15 à Decisions 55), occupe ce tirage ; un coéquipier de face, à portée lui aussi, ne peut pas tenter.

**What to build:** parmi les défenseurs à portée de tacle, **seul le mieux placé tente** : celui qui a le meilleur angle d'approche face au porteur (`duel.tackle_approach_angle_deg`, 0° = de face). Quand deux angles sont à moins de **10°** l'un de l'autre, le plus proche du porteur l'emporte. Un seul tirage par pas : deux défenseurs ne taclent jamais en même temps (pas de collision entre tacleurs). Neutralisation `11p` ajoutée au banc (`scripts/bench_series.py`, `NEUTRALISATIONS`, ticket 11q) : retour à la règle du plus proche.

**Décisions du propriétaire (16/11/2026) :** option « seul le mieux placé tente (meilleur angle) », pour éviter que deux défenseurs se percutent en taclant ensemble ; tolérance d'égalité d'angle 10° (« 10° (Recommandé) »), chiffre réel non trouvé.

**Attributs :** aucun nouveau (Aggression : fréquence ; Decisions : discernement du 11h).

**Constantes (validées le 16/11/2026) :** tolérance d'égalité d'angle 10°. Chiffre réel : tacles par match 30 à 40 (repère du ticket 22).

**Lien avec l'existant :** complète le 11h ; volume de fautes suivi au `21c` (retour vers 21-26).

**Blocked by:** 11h (livré) ; 11q (option `--neutraliser` du banc, pour la série « avant »).

**Bloque :** rien.

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : changement local dans `_step_ball` ; quelques tests qui supposent un seul tacleur à adapter.
Temps machine, non compté : série appariée de 50 matchs ; suite complète.

## Tests

- **Unitaires (scène contrôlée) :** un défenseur dans le dos et un défenseur de face, tous deux à portée : celui de face peut tenter ; un seul tacle par pas.
- **Statistiques :** 50 matchs appariés (`--neutraliser 11p` pour la série « avant ») : tacles par match, part par angle, fautes, buts et tirs.

## Résultat (50 matchs appariés, 16/11/2026)

`docs/INDICATEURS_V2.md` section 50. Règle : `duel.best_placed_tackler` (constante `TACKLER_ANGLE_TIE_DEG` = 10°), appelée par `match._step_ball` à la place de l'ancien `_nearest_opponent_in_range` (supprimé) ; neutralisation `11p` du banc : tolérance infinie, donc le plus proche. Tacles par match 22,08 → 22,52 (+ 0,44 ± 0,46, non significatif ; repère réel 30-40, **non atteint**) ; tacles de face 52,4 → 55,4 % et par derrière 15,6 → 13,4 % des tentatives (significatifs) ; fautes 10,88 → 10,38 (− 0,5 ± 0,49) ; buts − 0,16 ± 0,41 et tirs par équipe − 0,05 ± 0,48 (non significatifs). L'hypothèse du constat (le tirage du plus proche amplifie la baisse) est réfutée. **Décision du propriétaire (16/11/2026)** : « Garder + ticket volume (Recommandé) » : règle gardée pour le gain de qualité, volume confié au ticket `11r`.

Tests : 6 tests dans `tests/test_v2engine_tacleur_mieux_place.py` (scène dos/face, tolérance de 10°, coéquipiers et hors portée ignorés, un seul tacle par pas dans `_step_ball`, neutralisation du banc). Suite complète : 3 207 passés, 14 désélectionnés (attendu 3 201 + 6). Déterminisme : deux exécutions à graine fixée (match de 10 min), même empreinte `8efbc7feb978e98c`.

## Acceptance criteria

- [x] Option et règle validées par le propriétaire avant le code
- [x] Scène : le défenseur de face à portée tente malgré un défenseur plus proche dans le dos
- [x] Tacles par match rapportés, comparés au repère réel 30 à 40 ; fautes, buts et tirs rapportés — 22,5, sous le repère ; volume confié au `11r` (décision du propriétaire)
- [x] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md`
- [x] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`) — 100 min pour 105 estimées (− 5 %)

**18/11/2026, statut corrigé.** Clôture journalisée `VALIDÉ` le 16/11/2026 (`.claude/qc/journal.jsonl`, sous-étape `v2-realisme/11p/cloture`), code commité en `6166acc` ; la ligne de statut était restée « implémenté » (mise à jour oubliée après la clôture, comme au 10a). Garde-fou : ticket `expert-dispositif/07`.
