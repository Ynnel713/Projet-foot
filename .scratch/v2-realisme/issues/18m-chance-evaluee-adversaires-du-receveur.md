# 18m: Chance évaluée de la passe, adversaires proches du receveur

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, clôture du `23a`, piste b) :** à écart latéral réel égal, les passes des passeurs faibles sont plus souvent perdues que celles des forts. Écart réalisé sous 1 m : 0,758 non perdues à Passing < 50 (207 passes), 0,847 de 50 à 70, 0,879 à 70 et plus (24 matchs, graines 300 à 323, moteur après le `04e`). L'écart reste à chaque tranche d'écart réalisé, de vitesse et de dosage : ce n'est pas l'exécution (loi d'écart du `23a`), c'est le contexte de la passe (à qui, où, sous quel marquage du receveur). Toutes ces pertes viennent d'un adversaire qui touche le ballon avant le receveur visé. La chance évaluée (`possession.pass_success_probability`) ne compte que les adversaires entre le passeur et le receveur (`_cut_chance`, avancée de 0 à la longueur de la passe) : ceux qui sont autour du receveur, à côté ou derrière lui, n'y entrent pas. Ce trou existe depuis le `18g`. Effet résiduel après le réajustement du `23a` : − 1,9 ± 1,9 points chez les passeurs faibles (48 matchs, 1 882 passes) ; écarts de 2,4 à 3,3 points dans les tranches 0,14 et 0,43 de la chance évaluée.

**What to build :** mesurer, méthode du `18g`, la chance qu'un adversaire proche du point d'arrivée (devant, à côté ou derrière le receveur, par tranche de distance au receveur et selon qu'il arrive avant lui) touche le ballon le premier, et l'ajouter à la chance évaluée si elle tient hors échantillon. La réserve A2 du `23a` reste : le receveur marqué n'élargit pas l'écart de la passe, il compte seulement dans la chance évaluée. Diagnostic d'abord : si l'effet sur la calibration reste sous 1 point par tranche, clore sans changement.

**Attributs :** aucun nouveau.

**Blocked by :** `23a`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (enregistrement, table, branchement) | 50 min |
| Tests | 30 min |
| Intégration et vérifications (ajustement, contrôle hors échantillon) | 40 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne. Hypothèses : le script d'enregistrement du `23a` (passe, adversaires, premier contact) est repris ; une table de plus, même forme que `_CUT_ON_PATH`. Au-delà du seuil de 2 h : découpage possible en diagnostic (1 h) puis branchement, à examiner avant le code. Temps machine, non compté : 24 matchs d'ajustement, 48 de contrôle, suite complète.

## Comments

- 20/11/2026, création à la clôture du `23a` (décision du propriétaire : critère de calibration relâché, trou de contexte traité à part).
