# 18p: Chance évaluée : vitesse des adversaires vers la ligne de passe (passeurs faibles)

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, diagnostic du `18o`, `.scratch/v2-realisme/mesures/18o-diagnostic-*.py`) :** passeurs à Passing < 50 : chance évaluée surestimée de + 3,6 ± 1,9 point (48 matchs, graines 2400 à 2447, 1 830 passes), + 3,7 après le `18o` (graines 2600 à 2647 : voir la clôture du `18o`). Causes écartées : erreur de vitesse de la passe (+ 3,4 avec la vitesse réalisée), écart latéral réalisé (surplus de coupe même passe droite), pression sur le passeur, dosage (receveur arrêté compris), poste (gardiens bien calibrés ; DC et MDC faibles portent l'écart). Piste : la table de coupe est statique. Pour tous les passeurs, un adversaire qui va vers la ligne à plus de 3 m/s coupe 1,3 à 2 fois la chance prévue, celui qui s'en éloigne 0,6 fois (compensé en moyenne) ; chez les passeurs faibles, ces adversaires lancés coupent 0,40 contre 0,20 prévu.

**Réserves renvoyées du `18o` (acceptées par le propriétaire le 20/11/2026) :**
- A1 : passes de 15 à 30 m à − 1,1 ± 0,4 point (critère du `18n` : moins de 1 point ; − 0,9 au `18n`), à reprendre à la remesure de la table ;
- A2 : passes de moins de 8 m de + 0,4 à + 1,6 ± 0,7 point : le facteur du `18o` (`_CUT_REST_FACTOR`) s'applique aussi au presseur d'une passe très courte, à moins de 2 m du bout ; correctif proposé par l'expert, sans constante nouvelle : n'appliquer le facteur que si l'adversaire est plus près du receveur que du passeur (`rest < along`). Test : ligne « longueur 0 à 8 m » de `18o-controle.py` sous 1 point.

**What to build :** diagnostic d'abord : pourquoi les adversaires lancés coupent davantage les passes des passeurs faibles (choix des passes, lecture, temps de décision du passeur) ; puis, si la cause est la vitesse des adversaires, une entrée « vitesse vers la ligne » dans la coupe évaluée (sans terme correctif par Passing). Toute constante nouvelle est proposée au propriétaire avant d'être codée.

**Critères d'acceptation (proposés) :** Passing < 50 à moins de 2 points (au moins 1 500 passes) ; critère du `18n` tenu, passes de 15 à 30 m comprises (A1) ; passes de moins de 8 m à moins de 1 point (A2) ; adversaire près du receveur (`18o`) toujours à moins de 4 points.

**Attributs :** Passing (aucun nouveau).

**Blocked by :** aucun.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Diagnostic | 60 min |
| Développement (dont correctif A2 du `18o`) | 55 min |
| Tests | 30 min |
| Intégration et vérifications (contrôle sur matchs joués, matchs appariés, réserves A1 et A2 du `18o`) | 65 min |
| **Total (travail effectif)** | **3 h 45** |

Confiance : faible (cause non établie). Hypothèses : l'enregistrement du `18o` (`18o-diag-script.py`, vitesse des adversaires vers la ligne) suffit. Au-delà du seuil de 2 h : découpage en diagnostic (1 h 15) puis correction, à confirmer avant le code. Temps machine, non compté : 48 matchs d'enregistrement, 48 de contrôle, 50 appariés, suite complète.

## Comments

- 20/11/2026, création pendant le `18o` (décision du propriétaire : Passing < 50 sort du `18o`, « oui valide les 3 »).
- 20/11/2026, réserves A1 et A2 du `18o` renvoyées ici (décision du propriétaire à la clôture du `18o`).
