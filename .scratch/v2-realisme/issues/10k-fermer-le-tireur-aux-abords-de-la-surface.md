# 10k: Fermer le tireur aux abords de la surface

**Chantier :** `v2-realisme` (suite du `18m` et du `10f`, décision du propriétaire du 21/11/2026 : garder la baisse des buts pour un ticket dédié). **Priorité :** P1 (excès de buts). **Catégorie :** placement.

**Constat vérifié (`docs/INDICATEURS_V2.md` sections 57 et 58, 50 matchs appariés) :** après la sélection des frappes de loin (`18m`), 4,59 tirs hors surface par équipe (réel environ 4,1) mais convertis à 13,3 % (réel 4,2 %) ; 4,86 buts par match (réel environ 2,7) ; conversion dans la surface 16,1 % (réel 14,7 %). Les frappes gardées partent ligne de tir libre, tireur peu gêné entre 16 et 25 m dans l'axe. Les zones de la surface (`10f`) ne jouent que ballon sur l'aile (3 % du temps de possession) et ne changent pas les buts.

**What to build:** À diagnostiquer d'abord (situation des tirs à 16-25 m : distance du plus proche défenseur, ligne de tir couverte ou non, presseur présent, défenseurs entre le tireur et le but), puis proposer la correction au propriétaire : par exemple, porteur dans l'axe à 25 m ou moins, le défenseur libre le plus proche se place sur la ligne de tir (contre), ou le presseur ferme d'abord le tir. Aucune constante sans accord.

**Attributs :** à vérifier sur la carte (`docs/CARTE_ATTRIBUTS_V2.md`) avant tout effet nouveau (Positioning, Anticipation, Bravery pour le contre).

**Blocked by:** aucun (`10f` livré ; à coordonner avec `10g`, marquage dans la surface).

**Bloque :** `v2-collectif/22c` (calibration des tirs et des buts).

**Status:** livré (22/11/2026), validé expert + QC

## Diagnostic (21/11/2026, 20 matchs du banc, avant le code)

Script : `PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/10k-diag.py 20 4 10k-diag-20.json` (état exact du moteur à chaque tir, lu sur la pile d'appel, rien ne change au jeu), synthèse `10k-diag-synthese.py` → `10k-diag-20-synthese.txt`. 5,00 buts par match, 15,70 tirs de jeu par équipe.

- Tirs hors surface 16-25 m : 3,98 par équipe, 97 % dans l'axe, conversion 11,9 %, xG neutre moyen 0,128.
- Le tireur **n'est pas libre** : presseur à 5 m ou moins dans 90 % des cas (médiane 1,53 m), plus proche défenseur à 1,45 m (médiane). L'hypothèse « tireur peu gêné » est fausse.
- Mais **la ligne de tir reste ouverte** : couverte (défenseur à 1 m ou moins de la ligne tireur-centre du but) dans 21 % des cas, triangle tireur-poteaux vide dans 89 % ; tirs contrés 9 %. Cause lue dans le code : `defense.press_point` fait tourner le presseur vers la ligne de passe, jamais vers le but, même porteur à 20 m dans l'axe.
- Seconde cause, hors du placement : la résolution physique du tir (05e/05h) donne, tireur et gardien neutres, gardien bien placé, sans défenseur (`scripts.shot_calibration scenes 400`) : 0,204 à 16 m, 0,118 à 20 m, 0,059 à 25 m face au but, contre la table cible du propriétaire (commentaire de `_XG_LOGIT`) 0,08-0,11, 0,04-0,06, 0,025-0,04 ; aussi 0,336 à 11 m (cible 0,15-0,20). Environ deux fois la cible de 11 à 25 m.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et diagnostic (situations de tir) | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (cause à confirmer par le diagnostic). Temps machine, non compté : diagnostic de 10 matchs, série appariée de 50 matchs, suite complète. Au-delà de 2 h : à examiner pour découpage après le diagnostic (diagnostic seul, puis correction).

## Acceptance criteria

- [x] Diagnostic des tirs à 16-25 m chiffré, correction proposée et validée par le propriétaire avant le code (recommandation retenue le 21/11/2026, délégation du propriétaire)
- [x] Conversion hors surface et buts par match rapportés avant et après (50 matchs appariés, intervalles) : `docs/INDICATEURS_V2.md` section 59 ; cible retenue : baisse significative des buts et contrés dans le repère réel (20 à 28 %)
- [x] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 3 470 passés, 0 ignoré, 14 désélectionnés (3 467 au `10f` + 3 tests ajoutés)

## Correction retenue (recommandation du 21/11/2026, retenue par délégation du propriétaire)

Porteur à `defense.SHOT_LANE_RANGE_M` = 25 m ou moins du centre du but défendu : le presseur qui lit bien (Anticipation, courbe existante `_GOOD_LANE` de la ligne de passe, un tirage par presseur et porteur, `DefensiveRoles.shot_lanes`, oublié à chaque changement de porteur) tourne vers la ligne de tir (`press_point(..., aim=but)`), sur le même arc `SHADOW_M`, à sa distance d'arrêt (Aggression) ; sinon il garde sa lecture de passe. Constante nouvelle : 25 m seulement. Attributs vérifiés sur la carte : Anticipation (lire l'action, rayon existant, même courbe : pas de double comptage) ; Positioning (zone sans adversaire) et Bravery (contre, `17b` à créer) non utilisés.

## Résultat (22/11/2026, `docs/INDICATEURS_V2.md` section 59)

50 matchs appariés : buts 5,42 → 4,34 (− 1,08 [− 1,81 ; − 0,35]) ; tirs hors surface 4,28 → 3,32 par équipe ; contrés 14,0 → 24,2 % (repère 20 à 28 %) ; ligne de tir couverte, tirs à 16-25 m 20,9 → 30,6 %, dans la surface 42,5 → 63,4 % ; conversion hors surface 12,9 → 11,7 % (réel 4,2 %) : la conversion d'un tir propre reste environ deux fois la table cible, cause hors placement, ticket de suite `05l`. Matchs 0 et 1 rejoués : mêmes empreintes. 3 tests ajoutés (`tests/test_v2engine_pressing.py`).

Durée : estimée 2 h 15, réelle environ 2 h 10 (diagnostic 40 min, développement 30 min, tests 20 min, intégration et documentation 40 min), écart − 4 %. Durée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : diagnostic de 20 matchs, deux séries de 50 matchs, suite complète.

## Comments
- 22/11/2026, passage 1 : expert APPROVED (empreinte calculée à tort avec la doc et le ticket ; A1 facultatif : critère 4 à cocher, fait). Passage 2 (empreinte sur `v2engine/defense.py` et `tests/test_v2engine_pressing.py`, 13845c56) : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Réserves facultatives, non bloquantes : A1 bascule sans hystérésis à 25 m (saut de cible d'au plus 2,3 m, à regarder à l'écran) ; A2 contres hors surface encore bas (9,6 %), à recontrôler au `05l` et au `v2-collectif/22c`.
