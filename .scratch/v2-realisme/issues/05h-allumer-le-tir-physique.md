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

**Status:** livré (09/11/2026), validé expert + QC

## Constantes (proposées le 09/11/2026, validées par délégation du propriétaire)

| Constante | Avant | Après | Source |
|---|---|---|---|
| `KEEPER_REACTION_S` | 0,25 s | 0,30 s | temps de réaction visuo-moteur, ordre de grandeur 0,2 à 0,3 s ; gardien sur tir : non trouvé |
| `KEEPER_DIVE_MPS` | 4,0 m/s | 3,0 m/s | non trouvé ; recalé hors ligne sur 1 103 tirs de 24 matchs (temps de vol et écart au gardien tracés) vers le repère d'environ 70 % d'arrêts des tirs cadrés |

Délégation : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026).

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 20 min | 30 min |
| Développement | 40 min | 50 min |
| Tests unitaires et comportementaux | 30 min | 40 min |
| Intégration et vérifications | 30 min | 45 min |
| **Total (travail effectif)** | **2 h** | **2 h 45** (+ 38 %, durée estimée, non chronométrée) |

Écart > 30 % : la conversion mesurée (6,7 %) sortait des repères, d'où le recalage du gardien (collecte de 24 matchs, calage hors ligne, adaptation de deux scènes) et une seconde série de 50 matchs ; tests existants de 8 fichiers adaptés au tir en vol (aucun supprimé).

Confiance : moyenne. Hypothèses : les tests qui remplacent `attempt_shot` par monkeypatch sont adaptés à la nouvelle branche, sans être supprimés ; le réglage éventuel des constantes du gardien reste une proposition, codée après accord.
Temps machine, non compté : suite complète (environ 15 à 40 min) ; série de 50 matchs.

## Acceptance criteria

- [x] Plus aucun tirage du but au départ en jeu ouvert (test de garde sans monkeypatch)
- [x] Banc : tirs par équipe et contexte du tir lus dans la trace ; mêmes chiffres qu'avant sur une série interrupteur coupé
- [x] 50 matchs : taux d'arrêt par distance et par vitesse, conversion et cadrés rapportés, comparés aux repères
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation

- `match._step_ball` : interrupteur `SHOT_FLIGHT_RESOLUTION` retiré, le tir en vol est le seul chemin du tir en jeu (contre tiré au départ jusqu'au 05c) ; branche `attempt_shot` / `classify_unscored` retirée de `match` (les fonctions restent dans `shooting`, lues par leurs tests). Le penalty garde sa conversion provisoire (`shot_for`). Un tir hors du cadre garde le drapeau `shot_wide` (ticket 03k).
- **A1** : mesuré, le gardien se déplaçait de 0,55 à 1,03 m en moyenne entre la frappe et le jugement (3 lots de 2 matchs) : `cerveau._keeper` le garde sur sa position de la frappe (`ShotFlight.keeper_from`) pendant le vol ; après correctif, 0,09 m (2 matchs).
- **A2** : `match._keeper_save` part du point de contact : capté, gardien amené au point ; repoussé ou claqué, ballon relancé de ce point.
- **A3** : `occasion.ChanceTracker` ferme l'occasion « tir : en vol » dès que le tir n'est plus en vol sans issue, et vide `flying` à toute fermeture.
- Banc (`scripts/measure_v2.py`) : tirs et contexte lus dans la trace (`MatchTrace.shots`, via `on_start`), mêmes tirs que l'ancien comptage (ni contrés, ni penaltys) ; taux d'arrêt des tirs cadrés par distance et par vitesse au gardien (`scripts/v2_indicators.py`).
- Gardien recalé (constantes ci-dessus).
- Tests : tests de 8 fichiers adaptés (écart du tir imposé par `draw_shot_error` au lieu du tirage du but), garde sans monkeypatch (`test_v2engine_tir_en_vol` : plus d'interrupteur ni de tirage dans `match` ; `test_v2engine_issues_tir` : en match, tout tir cadré a été jugé par le gardien), 2 tests ajoutés (A2, A3). Suite complète : voir Comments.
- Hors périmètre, constaté : `scripts/measure_v2_decisions.py` était déjà cassé (signature de `_step_ball`), et lit encore `attempt_shot`.

## Mesures (09/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/05h-*`)

- **Banc recâblé** : moteur du commit `b3a2a28`, ancien banc (`05h-banc-ancien.json`) contre nouveau banc (`05h-banc-nouveau.json`), 2 matchs : tous les indicateurs identiques.
- **Déterminisme** : lot 0 joué deux fois (`05h2-on0.json`, `05h2-det2.json`) : identiques.
- **50 matchs, gardien du 05b** (`05h-on*.json`) : conversion 6,7 %, cadrés 30,1 %, environ 78 % des tirs cadrés arrêtés.
- **50 matchs, gardien recalé** (`05h2-on*.json`, moyenne des 10 lots) : buts 4,04 par match, tirs tracés 22,4 par équipe, **conversion 9,0 %** (repère 10-11 %), **cadrés 29,8 %** (repère 30-35 %), 70 % des tirs cadrés arrêtés (repère environ 70 %), contrés 18,7 %, à côté 34,3 %, au-dessus 14,4 %, dévissés 2,3 % ; arrêts captés 58 %, repoussés 24 %, claqués 18 %. Taux d'arrêt par distance : moins de 11 m 61 %, 11-18 m 50 %, 18-25 m 74 %, 25 m et plus 94 % ; par vitesse au gardien : 18-24 m/s 84 %, 24 m/s et plus 54 %.
- **À surveiller** : 4,0 buts par match, porté par le volume de tirs (22 par équipe, réel environ 12), à traiter à la calibration `v2-collectif/22c` ; la conversion remontera avec la puissance de frappe (`35a`).

## Reprises du 05b (réserves de l'expert, 08/11/2026), à traiter avant d'allumer l'interrupteur

- **A1** : pendant le vol, le gardien suit le ballon (état PLACEMENT, `cerveau._keeper`) puis plonge en plus : mouvement compté deux fois. Tracer son déplacement entre la frappe et le jugement ; au-delà d'environ 0,5 m en moyenne, le garder sur sa position de la frappe pendant le vol (correctif dans `_keeper`, plutôt que baisser `KEEPER_DIVE_REACH_M`).
- **A2** : à l'arrêt, le ballon saute du point de contact au corps du gardien (`_keeper_reaches` puis `_keeper_save`). Faire repartir le ballon repoussé ou claqué du point de contact ; capté : gardien amené au point ou plongeon animé au rendu. Test : après un arrêt, ballon à au plus `CONTROL_RADIUS_M` du point de contact.
- **A3** : un tir en vol sans issue (coup de sifflet pendant le vol, tir mort avant la ligne) garde « en vol » et laisse l'occasion ouverte (`ChanceTracker.flying`) ; une entrée peut aussi rester périmée après un second tir (point du QC). Fermer avec « tir : en vol » quand `ball.shot_flight` est vide et l'issue toujours « en vol », et vider `flying` à toute fermeture. Test : tir en vol interrompu par un coup de sifflet, occasion fermée au pas suivant.
- **À surveiller** : 77 % des tirs cadrés arrêtés sur 20 matchs (repère réel environ 70 %).

## Comments

- 09/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (un passage, empreinte b8fc2171) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05h/cloture`). Suite complète : 2 591 passés, 14 désélectionnés.
- Réserve A1 (conversion 9,0 % sous le repère, 4,0 buts par match portés par le volume de tirs) : acceptée ; volume de tirs au `v2-collectif/22c`, gardien à reprendre avec `35a`, sans le retoucher d'ici là pour les buts par match.
- Réserve A2 (courbe d'arrêt selon la distance peu réaliste ; banc sans effectifs par tranche, vitesse confondue avec la distance) : acceptée ; effectifs par tranche à ajouter au banc, forme de la courbe aux tickets 05e, 35a et 03b.
- Réserve A3 (gardien amené d'un coup au point de contact quand il capte) : acceptée ; à regarder à l'écran.
- Facultatifs A4 (vitesse au gardien à tracer dans `ShotEvent`) et A5 (`shot_wide` à remettre à faux pour un tir mort avant la ligne) : repris au 05c.
- QC : non bloquant, `scripts/measure_v2_decisions.py` lit encore `attempt_shot` (déjà cassé, hors périmètre).
- Réserves acceptées par le propriétaire : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026, lancement de la série 05h, 05c, 05d, 06a).
