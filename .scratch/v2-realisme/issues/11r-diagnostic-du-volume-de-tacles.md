# 11r: Diagnostic du volume de tacles (sous le repère réel 30 à 40)

**Chantier :** `v2-realisme` (suite du 11p, décision du propriétaire du 16/11/2026 : « Garder + ticket volume »). **Priorité :** P1. **Catégorie :** diagnostic.

**Constat vérifié (11p, 50 matchs appariés) :** 22,5 tacles par match, sous le repère réel de 30 à 40 (`docs/INDICATEURS_V2.md`, réserve du ticket 22). Avant le 11h : 37,3. Le 11h (facteur de tentative selon l'angle et Decisions hors urgence) explique la baisse ; la règle du tacleur le mieux placé (11p) n'a pas remonté le volume (+ 0,44, non significatif) : l'hypothèse d'un tirage bridé par le plus proche est réfutée.

**What to build:** diagnostic d'abord, sans changer le moteur (leçon du 11j : diagnostic sur le moteur courant avant de coder). Mesurer, sur le moteur courant : temps d'exposition des défenseurs à portée de tacle (par angle, urgence ou non), taux de tentative effectif par seconde d'exposition, part des expositions avec plusieurs défenseurs à portée, durée des confrontations (sortie par `CONFRONTATION_END_M`, interdiction après un tacle raté, déséquilibre du 12c). En déduire où se perd le volume (exposition trop courte, taux trop bas hors urgence, ou expositions trop rares), et proposer au propriétaire une ou plusieurs options chiffrées, avec leurs constantes, avant tout code.

**Attributs :** aucun nouveau a priori (Aggression : fréquence ; Decisions : discernement du 11h).

**Constantes :** aucune ; à proposer au propriétaire à l'issue du diagnostic. Chiffre réel : tacles par match 30 à 40 (repère du ticket 22).

**Lien avec l'existant :** 11h (facteur de tentative), 11p (choix du tacleur), 21c (volume de fautes, retour vers 21-26).

**Blocked by:** 11p (validé).

**Bloque :** rien.

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (instrumentation du banc) | 30 min |
| Tests | 15 min |
| Intégration et vérifications (analyse, options pour le propriétaire) | 30 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : instrumentation par le banc seul (`scripts/measure_v2.py`), comme au 11e.
Temps machine, non compté : série de 50 matchs ; suite complète.

## Résultat (50 matchs, graines du banc 0 à 49, 16/11/2026)

`docs/INDICATEURS_V2.md` section 51. Instrumentation en lecture seule : `scripts/diagnostic_tacles.py` (enveloppe `tackle_attempt_factor` et `should_attempt_tackle`, observateur par pas ; aucun tirage consommé), et non le banc `measure_v2` (hypothèse de l'estimation) : un script dédié, plus léger, sur les mêmes graines et affiches. Il retrouve 22,52 tacles par match, le chiffre du 11p : séries appariées. Sorties : `.scratch/v2-realisme/mesures/11r-diagnostic.txt|json`.

- **Exposition** : 1 234 s par match avec au moins un adversaire à portée (43 % du ballon tenu) ; à plusieurs défenseurs : 6 % ; temps-défenseur à portée bloqué par une règle (déjà engagé, relève après tacle raté, déséquilibré du 12c, hors jeu) : 3,4 %, non retenu par le 11p : 6 %. L'exposition n'est pas rare.
- **Confrontations** : 1 239 par match, durée médiane 0,8 s (moyenne 1,05 s) ; issue : tacle 1,7 %, porteur qui joue ou perd le ballon 50,6 %, séparation 47,6 %.
- **Taux** : 0,018 tacle par seconde d'exposition = taux de base des tireurs (0,031/s) × facteur 11h moyen (0,61).
- **Cause principale** : au taux de base, sans le facteur 11h, 38,6 tacles seraient attendus (dans le repère 30-40) : le taux de base de 0,03/s a été calibré sur 30-40 **avant** le 11h, qui en retire 16,1 par match (par derrière 8,6, voulu ; de côté 5,8 ; de face 1,2 ; surface 0,6).

**Décision du propriétaire (16/11/2026)** : option A, « recalibrer la base » : `_ATTEMPT_BASELINE` 0,03 → 0,047/s, `_ATTEMPT_AMPLITUDE` 0,021 → 0,033 (écart Aggression x2 gardé) ; environ 35 tacles attendus (premier ordre), proportions du 11h gardées, fautes sur tacle 10,4 → environ 16. Écartées : B (facteur de côté 0,6 → 0,9 et base 0,04 : revient sur le 11h), C (portée 2 m : l'exposition n'est pas le goulot), statu quo. Code : ticket `11s`.

Tests : 5 tests dans `tests/test_diagnostic_tacles.py` (match identique avec ou sans instrumentation et moteur rétabli, issues des confrontations, contexte des tirages, tranches de durée, déterminisme). Suite complète : 3 212 passés, 14 désélectionnés (3 207 après le 11p + 5). Déterminisme : deux exécutions (match de 10 min), même empreinte `d968749b1af109da`. Moteur non modifié.

**Durée réelle : 95 min** (analyse 20, développement 25, tests 15, intégration 35) pour 90 estimées (+ 6 %). Temps machine hors total : série de 50 matchs (24 min, 4 processus), suite complète 13 min.

## Acceptance criteria

- [x] Temps d'exposition, taux de tentative effectif et part des expositions multiples mesurés sur 50 matchs — 1 234 s, 0,018/s, 6 %
- [x] Cause principale du volume bas identifiée et chiffrée — base calibrée avant le 11h : 38,6 attendus sans facteur, − 16,1 par le 11h
- [x] Options chiffrées proposées au propriétaire avant tout code moteur — option A retenue, ticket `11s`
- [x] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`) — 95 min pour 90 (+ 6 %)

## Comments

- 16/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. A1 facultatif : séparation mesurée à 1,5 m (portée de tacle) et non à `CONFRONTATION_END_M` (3 m), sans effet sur la conclusion. A2 facultatif : décalage d'un demi-pas entre tirage et observateur (1 à 5 % sur les temps). QC, réserves mineures : `last_drawn` déclaré après usage ; statut « tirage » = dernier tireur du pas. Points à surveiller au 11s : volume à mesurer (pertes de balle accrues), fautes totales contre 21-26 (21c).
