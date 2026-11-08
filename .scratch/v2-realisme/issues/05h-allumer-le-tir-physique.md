# 05h: Allumer le tir physique : l'issue du tir vient de sa trajectoire en match

**Chantier :** `v2-realisme` (découpé du 05b le 08/11/2026 : le 05b et les réserves A2 et A3 du 05a dépassaient 2 h). **Priorité :** P0. **Catégorie :** exécution.

**Constat vérifié :** depuis les tickets 05a et 05b, le tir en vol (trajectoire jusqu'à la ligne, arrêt par portée du gardien) existe derrière l'interrupteur `match.SHOT_FLIGHT_RESOLUTION`, coupé : en match, le but est toujours tiré au départ (`attempt_shot`), et le banc de mesure compte les tirs par cette fonction.

**What to build:**
1. Allumer l'interrupteur et retirer du jeu ouvert la branche `attempt_shot` / `shot_for` / `classify_unscored` (réserve A2 du 05a) ; test de garde sans monkeypatch.
2. Banc (`scripts/measure_v2.py`, `scripts/v2_indicators.py`) : compter les tirs et leur contexte depuis la trace (`MatchTrace.shots`), plus par `attempt_shot` (réserve A3 du 05a, partie banc).
3. Mesure sur 50 matchs (graine d'audit) : taux d'arrêt par tranche de distance et selon la vitesse à l'arrivée sur le gardien, conversion, tirs cadrés ; repères vérifiés au 01c (10-11 % de conversion, 30-35 % de cadrés). Si la conversion sort des repères, proposer un réglage des constantes du gardien (05b) au propriétaire avant de le coder.

**Hors de ce ticket :** contre physique (05c), hauteur (05f), notes du gardien (`v2-attributs-restants/03b`), évaluation du tir dans la décision (05e).

**Attributs :** aucun

**Blocked by:** 05b.

**Bloque :** 05e, 05g, 06a.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : les tests qui remplacent `attempt_shot` par monkeypatch sont adaptés à la nouvelle branche, sans être supprimés ; le réglage éventuel des constantes du gardien reste une proposition, codée après accord.
Temps machine, non compté : suite complète (environ 15 à 40 min) ; série de 50 matchs.

## Acceptance criteria

- [ ] Plus aucun tirage du but au départ en jeu ouvert (test de garde sans monkeypatch)
- [ ] Banc : tirs par équipe et contexte du tir lus dans la trace ; mêmes chiffres qu'avant sur une série interrupteur coupé
- [ ] 50 matchs : taux d'arrêt par distance et par vitesse, conversion et cadrés rapportés, comparés aux repères
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Reprises du 05b (réserves de l'expert, 08/11/2026), à traiter avant d'allumer l'interrupteur

- **A1** : pendant le vol, le gardien suit le ballon (état PLACEMENT, `cerveau._keeper`) puis plonge en plus : mouvement compté deux fois. Tracer son déplacement entre la frappe et le jugement ; au-delà d'environ 0,5 m en moyenne, le garder sur sa position de la frappe pendant le vol (correctif dans `_keeper`, plutôt que baisser `KEEPER_DIVE_REACH_M`).
- **A2** : à l'arrêt, le ballon saute du point de contact au corps du gardien (`_keeper_reaches` puis `_keeper_save`). Faire repartir le ballon repoussé ou claqué du point de contact ; capté : gardien amené au point ou plongeon animé au rendu. Test : après un arrêt, ballon à au plus `CONTROL_RADIUS_M` du point de contact.
- **A3** : un tir en vol sans issue (coup de sifflet pendant le vol, tir mort avant la ligne) garde « en vol » et laisse l'occasion ouverte (`ChanceTracker.flying`) ; une entrée peut aussi rester périmée après un second tir (point du QC). Fermer avec « tir : en vol » quand `ball.shot_flight` est vide et l'issue toujours « en vol », et vider `flying` à toute fermeture. Test : tir en vol interrompu par un coup de sifflet, occasion fermée au pas suivant.
- **À surveiller** : 77 % des tirs cadrés arrêtés sur 20 matchs (repère réel environ 70 %).
