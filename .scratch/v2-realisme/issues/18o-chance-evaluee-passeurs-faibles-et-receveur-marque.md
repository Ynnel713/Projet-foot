# 18o: Chance évaluée : passeurs faibles et receveur marqué de face

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, clôture du `18n`) :** sur 48 matchs joués avec le moteur du `18n` (graines 2400 à 2447, 60 231 passes de jeu au sol, `.scratch/v2-realisme/mesures/18n-controle.txt`) :
- passeurs à Passing < 50 : chance évaluée surestimée de + 3,6 ± 1,9 point (1 830 passes ; + 2,0 ± 1,8 avant le `18n`). Rejoint la réserve A2 du `23a` (Passing pèse peu sur la passe courte) ;
- adversaire à moins de 1,5 m du receveur, entre le passeur et lui : chance sous-estimée de 12,5 ± 4,9 points (385 passes : évaluée 0,49, non perdue 0,61) ; sur la ligne (moins de 0,5 m) : − 12,7 ± 8,0 (149). À l'inverse, dans le cas statique du test `test_the_called_player_is_a_pass_option_only_when_he_is_not_covered` (adversaire immobile à 0,5 m devant le receveur, passe de 12 m), la chance remonte à 0,70, au seuil `OPEN_LANE_PROBABILITY`. La table du `18n` ignore la proximité du receveur.

**What to build :** diagnostic d'abord, sur des matchs joués avec le moteur courant : écart évaluée / observée par Passing croisé avec la longueur et la bande d'écart ; et pour les adversaires près du receveur, par distance au receveur et position (devant, à côté, derrière). Trouver le facteur en cause (poids de Passing dans l'erreur de passe, ou entrée « proximité du receveur » dans la table de coupe) et le corriger seul. Ajouter un test explicite du receveur marqué au contact. Toute constante nouvelle est proposée au propriétaire avant d'être codée. Facultatif, à la même remesure (réserve A3 du `18n`) : lissage monotone ou interpolation de la table dans le temps.

**Critères d'acceptation (proposés) :** Passing < 50 à moins de 2 points ; passes avec un adversaire à moins de 1,5 m du receveur à moins de 4 points (sur au moins 500 passes, série plus longue si besoin) ; critère du `18n` toujours tenu (au plus 4 points par tranche d'au moins 500 passes, moyenne à 0,5 point).

**Attributs :** Passing (aucun nouveau).

**Blocked by :** aucun.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Diagnostic (deux croisements) | 50 min |
| Développement (correction d'un facteur) | 35 min |
| Tests | 30 min |
| Intégration et vérifications (contrôle sur matchs joués, matchs appariés) | 60 min |
| **Total (travail effectif)** | **3 h 10** |

Confiance : faible (deux constats, cause non établie, peut-être deux facteurs). Hypothèses : le script d'enregistrement du `18m` suffit ; un facteur par constat. Au-delà du seuil de 2 h : découpage proposé en diagnostic (1 h 05) puis correction, à confirmer avant le code ; si les deux constats ont des causes distinctes, scinder en deux tickets. Temps machine, non compté : 48 matchs de contrôle, 50 matchs appariés, suite complète.

## Comments

- 20/11/2026, création à la clôture du `18n` (réserves A1 et A2 de l'expert ; décision du propriétaire : « j'accepte A1 et A2, un seul ticket 18o »).
