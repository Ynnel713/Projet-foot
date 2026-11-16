# 11s: Recalibrer le taux de base de tentative de tacle après le 11h

**Chantier :** `v2-realisme` (suite du 11r, décision du propriétaire du 16/11/2026 : option A). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11r, 50 matchs) :** 22,5 tacles par match, sous le repère réel 30 à 40. Au taux de base (0,03/s, `duel._ATTEMPT_BASELINE`, calibré sur 30-40 avant le 11h), 38,6 tacles seraient attendus ; le facteur 11h (moyenne 0,61) en retire 16,1. Exposition (1 234 s par match) et règles de blocage (3 %) ne sont pas en cause.

**What to build:** `_ATTEMPT_BASELINE` 0,03 → 0,047/s et `_ATTEMPT_AMPLITUDE` 0,021 → 0,033 (écart Aggression x2 gardé), commentaire de `duel.py` mis à jour (calibrage après le 11h). Aucun autre changement.

**Attributs :** Aggression seule (fréquence), inchangé (R1).

**Constantes (validées le 16/11/2026) :** base 0,047/s, amplitude 0,033. Chiffre réel : tacles par match 30 à 40 (premierleague.com, repère du ticket 22).

**Lien avec l'existant :** 11h (facteur gardé), 11p, 21c (fautes : environ 10,4 → 16 sur tacle, vers 21-26 au total).

**Blocked by:** 11r.

**Bloque :** rien.

**Status:** implémenté (16/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 10 min |
| Tests (adapter les tests qui lisent la base) | 20 min |
| Intégration et vérifications (série appariée, rapport) | 40 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : quelques tests figent 0,03 ; la série « avant » est celle du 11r/11p (mêmes graines).
Temps machine, non compté : série de 50 matchs ; suite complète.

## Résultat (50 matchs appariés, 16/11/2026)

`docs/INDICATEURS_V2.md` section 52. `duel._ATTEMPT_BASELINE` 0,047, `_ATTEMPT_AMPLITUDE` 0,033 ; série « avant » : `11p-apres-serie.json` (moteur inchangé depuis, mêmes matchs). Tacles par match 22,52 → 34,32 (+ 11,8 ± 1,3, dans le repère 30-40) ; part des tacles par derrière hors urgence 12,5 → 13,3 % (+ 0,7 ± 2,4 points, non significatif) ; de face 55,9 → 51,2 % et de côté 30,9 → 34,7 % des tentatives (significatifs) ; fautes 10,38 → 16,68 (+ 6,3 ± 0,9), coups francs + 4,8 ± 0,9, penaltys + 0,06 ± 0,10 ; buts − 0,04 ± 0,78 et tirs par équipe − 0,02 ± 0,98 (non significatifs). Aggression : rapport des taux 99 / 11 de 5,67 à 5,71 (calcul sur la courbe, pas de série de profil : les deux constantes sont multipliées par le même facteur).

Tests : 1 test ajouté dans `tests/test_v2engine_duel.py` (taux 0,047 à la note médiane, bornes de l'amplitude) ; aucun test existant ne figeait 0,03. Suite complète : 3 213 passés, 14 désélectionnés (3 212 + 1). Déterminisme : deux exécutions à graine fixée (match de 10 min), même empreinte `f4d4bb80ab482f36`.

**Durée réelle : 65 min** (analyse 10, développement 10, tests 10, intégration 35) pour 80 estimées (− 19 %). Temps machine hors total : série de 50 matchs (38 min, 3 processus), suite complète 14 min.

## Acceptance criteria

- [x] Tacles par match dans 30 à 40 sur 50 matchs appariés — 34,3
- [x] Part des tacles par derrière hors urgence sans hausse significative (proportions du 11h gardées) — + 0,7 ± 2,4 points
- [x] Fautes, buts, tirs rapportés (écart apparié) ; profil Aggression 99/11 : écart de fréquence gardé — fautes + 6,3, buts et tirs non significatifs ; rapport 5,67 → 5,71 (calcul)
- [x] Déterminisme à graine fixée ; suite complète comparée à l'attendu — 3 213 passés
- [x] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`) — 65 min pour 80 (− 19 %)
