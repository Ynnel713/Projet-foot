# 18m: Chance évaluée de la passe, adversaires proches du receveur

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, clôture du `23a`, piste b) :** à écart latéral réel égal, les passes des passeurs faibles sont plus souvent perdues que celles des forts. Écart réalisé sous 1 m : 0,758 non perdues à Passing < 50 (207 passes), 0,847 de 50 à 70, 0,879 à 70 et plus (24 matchs, graines 300 à 323, moteur après le `04e`). L'écart reste à chaque tranche d'écart réalisé, de vitesse et de dosage : ce n'est pas l'exécution (loi d'écart du `23a`), c'est le contexte de la passe (à qui, où, sous quel marquage du receveur). Toutes ces pertes viennent d'un adversaire qui touche le ballon avant le receveur visé. La chance évaluée (`possession.pass_success_probability`) ne compte que les adversaires entre le passeur et le receveur (`_cut_chance`, avancée de 0 à la longueur de la passe) : ceux qui sont autour du receveur, à côté ou derrière lui, n'y entrent pas. Ce trou existe depuis le `18g`. Effet résiduel après le réajustement du `23a` : − 1,9 ± 1,9 points chez les passeurs faibles (48 matchs, 1 882 passes) ; écarts de 2,4 à 3,3 points dans les tranches 0,14 et 0,43 de la chance évaluée.

**What to build :** mesurer, méthode du `18g`, la chance qu'un adversaire proche du point d'arrivée (devant, à côté ou derrière le receveur, par tranche de distance au receveur et selon qu'il arrive avant lui) touche le ballon le premier, et l'ajouter à la chance évaluée si elle tient hors échantillon. La réserve A2 du `23a` reste : le receveur marqué n'élargit pas l'écart de la passe, il compte seulement dans la chance évaluée. Diagnostic d'abord : si l'effet sur la calibration reste sous 1 point par tranche, clore sans changement.

**Attributs :** aucun nouveau.

**Blocked by :** `23a`.

**Status:** livré (20/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (enregistrement, table, branchement) | 50 min |
| Tests | 30 min |
| Intégration et vérifications (ajustement, contrôle hors échantillon) | 40 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne. Hypothèses : le script d'enregistrement du `23a` (passe, adversaires, premier contact) est repris ; une table de plus, même forme que `_CUT_ON_PATH`. Au-delà du seuil de 2 h : découpage possible en diagnostic (1 h) puis branchement, à examiner avant le code. Temps machine, non compté : 24 matchs d'ajustement, 48 de contrôle, suite complète.

## Critères d'acceptation (posés avant le diagnostic, 20/11/2026)

1. Diagnostic sur 24 matchs neufs (graines 2200 à 2223) : si ajouter une table « adversaires hors coupe près du receveur » change la chance évaluée de moins de 1 point dans chaque tranche, clore sans changement moteur.
2. Sinon : la table tient hors échantillon (48 matchs, graines 2300 à 2347) au critère du propriétaire (au plus 4 points par tranche d'au moins 500 passes, moyenne à 0,5 point) et réduit l'écart des passeurs à Passing < 50.

## Clôture

Diagnostic seul, **aucun changement moteur** (critère 1 atteint). Scripts : `.scratch/v2-realisme/mesures/18m-diag-script.py` (enregistrement, lecture seule du moteur), `18m-analyse.py` ; sortie : `18m-rapport.txt`. Moteur du commit `a048268`. 72 matchs, 92 206 passes de jeu au sol (30 703 d'ajustement, 61 503 de contrôle).

- Trou réel mais rare : 1,7 % des passes ont un adversaire non compté par la coupe à moins de 2 m du receveur, presque toujours derrière lui (premier à toucher : 0,039 derrière, 0 devant ou à côté, adversaires à moins de 3 m). Sur ces passes, la chance est optimiste de + 6,6 ± 2,5 points (contrôle), + 10,1 ± 5,9 si l'adversaire atteint le point visé avant le receveur.
- Ces adversaires font 2 % des pertes (6 % chez Passing < 50) ; 89 % des pertes viennent d'adversaires déjà comptés par la coupe.
- Table ajustée (méthode du 18g, par distance au receveur et selon qu'il arrive avant) : le sous-groupe passe de + 6,6 à + 1,5 point, mais aucune tranche de chance ne bouge de plus de 0,5 point (pire tranche 4,3 → 4,4 en 10 tranches) ; Passing < 50 inchangé (+ 2,0 ± 1,8). L'hypothèse du ticket (écart des passeurs faibles dû au marquage du receveur) n'est pas confirmée : leurs pertes viennent plus souvent d'adversaires loin du receveur (12 % contre 6 %).
- Constaté en passant : passes de moins de 15 m surévaluées de + 2,0 ± 0,4 point (27 996 passes), de 15 à 30 m sous-évaluées de − 1,0 ± 0,4. Contrôle du 23a refait avec le moteur livré (réserve A4 du 23a), 7 tranches : pire écart + 4,2 points (0,14 à 0,29, 1 608 passes) et + 4,1 (0,43 à 0,57, 2 750), moyenne + 0,3 : critère du propriétaire légèrement dépassé. Ticket `18n` créé (décision du propriétaire, 20/11/2026).

Tests : aucun ajouté (aucun code du moteur ni des scripts versionnés modifié) ; suite complète passée : 3 464 passés, 0 ignoré, 14 désélectionnés (17 min 04), identique à l'état après le 23a. Déterminisme : sans objet (moteur inchangé ; série reproductible par graine).

Durée : estimée 2 h 20 (phase 1, diagnostic : 1 h), réelle 1 h 30 (analyse 20 min, scripts 30 min, analyse des résultats et documentation 40 min), − 36 % : arrêt à la phase 1 comme prévu par le critère 1 (branchement, tests et contrôle non faits). Temps machine hors total : 1 + 72 matchs (45 min), suite complète.

## Comments

- 20/11/2026, création à la clôture du `23a` (décision du propriétaire : critère de calibration relâché, trou de contexte traité à part).
- 20/11/2026, diagnostic : table « près du receveur » sans effet sur la calibration (moins de 0,5 point par tranche) ; clôture sans changement moteur et ticket `18n` (biais selon la longueur) décidés par le propriétaire : « vas-y, clôture le 18m et crée le ticket ».
- 20/11/2026, revue de clôture, passage 1 : expert APPROVED (empreinte 5308cb9b), QC VALIDÉ ; facultatifs : A1 tableau en 7 tranches produit hors script (corrigé : `18m-analyse.py`, `calib(..., parts=7)`, rapport régénéré), A2 table « près du receveur » (+ 6,6 → + 1,5 points sur 1,7 % des passes) à garder sous la main pour le 18n. Liste des fichiers revus corrigée (ticket et `docs/PLAN_V2.md` sortis de la revue pour recevoir le statut, contenu inchangé).
- 20/11/2026, revue de clôture, passage 2 : expert APPROVED (empreinte 06a1b4cc), QC VALIDÉ, clôture VALIDÉ. Facultatif reporté au 18n : commandes exactes de régénération des lots (`18m-diag-script.py 6 2200 > fit-2200.json`, etc.) et option `--ajuste` citée à tort dans le docstring de `18m-analyse.py`.
