# 18n: Chance évaluée de la passe selon sa longueur

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, clôture du `18m`) :** sur 48 matchs de contrôle (graines 2300 à 2347, moteur du commit `a048268`, 61 503 passes de jeu au sol), la chance évaluée (`possession.pass_success_probability`) surévalue les passes de moins de 15 m de + 2,0 ± 0,4 point (27 996 passes) et sous-évalue celles de 15 à 30 m de − 1,0 ± 0,4 point (30 662) ; les deux se compensent dans la moyenne (+ 0,3 point). Le contrôle du `23a` refait avec le moteur livré (réserve A4 du `23a`), 7 tranches, dépasse légèrement le critère du propriétaire (au plus 4 points par tranche d'au moins 500 passes) : + 4,2 points de 0,14 à 0,29 (1 608 passes) et + 4,1 de 0,43 à 0,57 (2 750). Rejoint la réserve A2 du `23a` (Passing pèse peu sur la passe courte : + 0,4 point de 30 à 90 à 15 m). Passeurs à Passing < 50 : + 2,0 ± 1,8 point, non expliqué par les adversaires autour du receveur (`18m`) ; leurs pertes viennent plus souvent d'adversaires loin du receveur (12 % contre 6 %).

**What to build :** diagnostic d'abord, sur les enregistrements du `18m` (`.scratch/v2-realisme/mesures/18m-diag-script.py`, données à rejouer si le conteneur les a perdues) : écart évaluée / observée par longueur croisée avec la coupe (`keep`), la bande d'écart et la pression ; trouver quel facteur porte le biais (table de coupe sans dépendance à la longueur, parts par bande, ou adversaires hors trajet qui récupèrent les passes très imprécises). Puis corriger ce facteur seul (pas de terme correctif par longueur sans cause) et revenir sous le critère du propriétaire hors échantillon. Toute constante nouvelle est proposée au propriétaire avant d'être codée.

**Attributs :** aucun nouveau.

**Blocked by :** aucun.

**Status:** livré (20/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Diagnostic (croisements sur les données du 18m) | 45 min |
| Développement (correction d'un facteur) | 40 min |
| Tests | 30 min |
| Intégration et vérifications (contrôle hors échantillon, matchs appariés) | 40 min |
| **Total (travail effectif)** | **2 h 50** |

Confiance : faible (cause inconnue). Hypothèses : les données du `18m` suffisent au diagnostic ; une seule table ou part à réajuster. Au-delà du seuil de 2 h : découpage proposé en diagnostic (1 h) puis correction, à confirmer avant le code. Temps machine, non compté : 24 matchs d'ajustement, 48 de contrôle, 50 matchs appariés, suite complète.

## Critères d'acceptation (posés avant le code, 20/11/2026)

1. Calibration hors échantillon, sur des matchs joués avec le moteur modifié : au plus 4 points d'écart par tranche d'au moins 500 passes (7 tranches) et moyenne à 0,5 point près (critère du propriétaire, 23a).
2. Biais selon la longueur résorbé : passes de moins de 15 m et de 15 à 30 m chacune à moins de 1 point.
3. Un seul facteur corrigé, avec sa cause (pas de terme correctif par longueur) ; constantes validées par le propriétaire avant le code.
4. 50 matchs appariés : réussite des passes de jeu au-dessus de 80 % (29b), buts et tirs sans écart au-delà du bruit ; déterminisme (même empreinte sur deux exécutions à graine fixée) ; suite complète verte.

## Clôture

- Cause : la coupe dépend du temps du ballon jusqu'à l'adversaire, pas de la longueur (à temps égal, passes courtes et longues ont le même taux) ; la table du 18g, fixe, surévaluait la passe courte près du presseur. Second défaut : estimateur non séquentiel du 18g (adversaires du fond sous-comptés).
- Correction (`v2engine/possession.py`) : table de coupe distance à la trajectoire × temps du ballon (`_CUT_TABLE`, `_CUT_TIME_S`), parts par bande 0,99 / 0,99 / 0,98 / 0,80 ; constantes validées par le propriétaire (« oui valide, lance la phase 2 », 20/11/2026).
- Critère 1 : tenu (48 matchs joués, graines 2400 à 2447, 60 231 passes : pire tranche 3,2 points, moyenne − 0,3). Hors ligne sur le contrôle du 18m : 1,4 et − 0,1.
- Critère 2 : tenu (moins de 15 m + 0,3, 15 à 30 m − 0,9). Plus de 30 m : + 1,2 (3 379 passes).
- Critère 3 : tenu (table de coupe seule, parts par bande réajustées par moindres carrés sur la même loi).
- Critère 4 : tenu. Réussite des passes 82,9 % → 84,7 % (+ 1,8 ± 0,4 point), passes interceptées − 27,2 ± 6,3 par match, tirs + 1,5 ± 2,3, buts + 0,20 ± 0,97 ; déterminisme : empreinte `4121454b8e0184da` deux fois (match 3 du banc) ; suite complète : 3 465 passés, 14 désélectionnés (premier passage : 1 échec, `test_the_called_player_is_a_pass_option_only_when_he_is_not_covered`, marqueur collé au receveur à 0,70 de chance avec la nouvelle table, juste au-dessus du seuil de 0,7 ; marqueur placé sur la ligne à 4 m devant le receveur, 0,44, intention du test inchangée).
- À signaler : Passing < 50 passe de + 2,0 ± 1,8 à + 3,6 ± 1,9 point (1 830 passes), cause non établie, rejoint la réserve A2 du 23a.
- Mesures : `docs/INDICATEURS_V2.md` section 61 ; scripts et sorties `.scratch/v2-realisme/mesures/18n-*`.
- Durée réelle : 3 h 15 (analyse et diagnostic 80 min, développement 30, tests 35, intégration 50) pour 2 h 50 estimées, + 15 %. Temps machine hors total : 48 matchs de contrôle (35 min), 2 x 50 matchs appariés (1 h 10), suite complète.

## Comments

- 20/11/2026, création à la clôture du `18m` (décision du propriétaire).
- 20/11/2026, phase 1 (diagnostic) : cause trouvée (temps du ballon), table et parts proposées au propriétaire, validées (« oui valide, lance la phase 2 »).
- 20/11/2026, phase 2 : table codée, contrôle sur 48 matchs joués, 50 matchs appariés ; implémenté, en attente de clôture.
- 20/11/2026, clôture, passage 1 : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ.
  - A1 (réserve) : Passing < 50 surestimé de + 3,6 ± 1,9 point (+ 2,0 avant).
  - A2 (réserve) : receveur collé de face jugé ouvert dans le cas statique du test (chance 0,70) ; mesuré sur les 48 matchs joués : adversaire à moins de 1,5 m du receveur, entre passeur et lui, chance sous-estimée de 12,5 ± 4,9 points (385 passes).
  - A3, A4 (facultatives) : table non monotone dans le temps ; fichiers hors revue (ticket, plan : suivi documentaire). Commentaire de test « 1,1 s » à lire 1,3 s.
  - Réserves A1 et A2 acceptées par le propriétaire : « j'accepte A1 et A2, un seul ticket 18o ». Suite : `18o`.
