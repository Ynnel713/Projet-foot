# 18n: Chance évaluée de la passe selon sa longueur

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, clôture du `18m`) :** sur 48 matchs de contrôle (graines 2300 à 2347, moteur du commit `a048268`, 61 503 passes de jeu au sol), la chance évaluée (`possession.pass_success_probability`) surévalue les passes de moins de 15 m de + 2,0 ± 0,4 point (27 996 passes) et sous-évalue celles de 15 à 30 m de − 1,0 ± 0,4 point (30 662) ; les deux se compensent dans la moyenne (+ 0,3 point). Le contrôle du `23a` refait avec le moteur livré (réserve A4 du `23a`), 7 tranches, dépasse légèrement le critère du propriétaire (au plus 4 points par tranche d'au moins 500 passes) : + 4,2 points de 0,14 à 0,29 (1 608 passes) et + 4,1 de 0,43 à 0,57 (2 750). Rejoint la réserve A2 du `23a` (Passing pèse peu sur la passe courte : + 0,4 point de 30 à 90 à 15 m). Passeurs à Passing < 50 : + 2,0 ± 1,8 point, non expliqué par les adversaires autour du receveur (`18m`) ; leurs pertes viennent plus souvent d'adversaires loin du receveur (12 % contre 6 %).

**What to build :** diagnostic d'abord, sur les enregistrements du `18m` (`.scratch/v2-realisme/mesures/18m-diag-script.py`, données à rejouer si le conteneur les a perdues) : écart évaluée / observée par longueur croisée avec la coupe (`keep`), la bande d'écart et la pression ; trouver quel facteur porte le biais (table de coupe sans dépendance à la longueur, parts par bande, ou adversaires hors trajet qui récupèrent les passes très imprécises). Puis corriger ce facteur seul (pas de terme correctif par longueur sans cause) et revenir sous le critère du propriétaire hors échantillon. Toute constante nouvelle est proposée au propriétaire avant d'être codée.

**Attributs :** aucun nouveau.

**Blocked by :** aucun.

**Status:** à faire

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

## Comments

- 20/11/2026, création à la clôture du `18m` (décision du propriétaire).
