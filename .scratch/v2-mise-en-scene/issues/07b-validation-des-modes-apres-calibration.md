# 07b: Validation des modes de visionnage après la calibration (second passage)

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026, décision du propriétaire). **Catégorie :** validation.

**Constat :** les poids du score d'intérêt (`01b`), les fenêtres (`01c`) et les budgets (`02`, `03`) sont fixés sur le moteur d'avant la calibration générale. Après `v2-collectif/22a` à `22c`, le nombre de tirs, de grosses occasions et de buts par match change, donc les durées et la part du Tier 2.

**What to build:** relancer `scripts/measure_moments.py` (07a) sur 50 matchs, graine d'audit, sur le moteur calibré ; comparer chaque indicateur au premier passage. Si une durée sort de sa cible ou si la part du Tier 2 change de plus d'un tiers, proposer au propriétaire de nouveaux poids ou budgets (ticket de réglage ouvert, pas de réglage ici).

**Attributs :** aucun.

**Blocked by:** 07a ; `v2-collectif/22c`.

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 5 min |
| Développement | 5 min |
| Tests unitaires et comportementaux | 10 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **50 min** |

Confiance : élevée. Hypothèses : script du `07a` inchangé, relancé tel quel.
Temps machine, non compté : 50 matchs (environ 2 h 30).

## Acceptance criteria

- [ ] Rapport avant et après calibration, indicateur par indicateur
- [ ] Couverture du Tier 1 : 100 % ; doublons : 0
- [ ] Tout écart de durée ou de part du Tier 2 renvoyé à un ticket de réglage proposé au propriétaire
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
