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

**Status:** livré (20/11/2026), validé expert + QC

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

## Critères de clôture (décision du propriétaire, 20/11/2026, fin de la phase 1)

Phase 1 sans cause unique corrigible ; le propriétaire choisit l'option A (« Ok pour le A ») : clôture en diagnostic seul, sans changement moteur (comme le `18m`). Les critères d'acceptation proposés plus haut ne sont pas visés ; critères de cette clôture :
1. Chaque hypothèse testée sur des matchs joués avec le moteur actuel (commit `4c9e470`), avec sa mesure et sa conclusion, scripts et sorties dans `.scratch/v2-realisme/mesures/18p-*`.
2. Aucun changement du moteur ni des tests ; suite complète verte.
3. Biais restants (Passing < 50, A1, A2 du `18o`) documentés et rattachés à la remesure du `29c`.

## Clôture

- Données : 52 matchs du contrôle du `18o` (graines 2600 à 2651, moteur `4c9e470`, 64 887 passes), et les mêmes graines 2600 à 2647 réenregistrées avec le côté signé de chaque adversaire (`18p-diag-script.py`, 59 976 passes, matchs identiques).
- Hypothèses écartées (`18p-diagnostic.txt` à `18p-dosage.txt`) :
  - A2, correctif de l'expert (facteur du reste du trajet seulement si l'adversaire est plus près du receveur que du passeur) : moins de 8 m + 1,7 -> + 1,6 ; sans effet, le presseur n'est pas la cause ;
  - vitesse des adversaires vers la ligne : effet réel par adversaire (coupe observée / prévue 0,56 en s'éloignant à plus de 3 m/s, 1,66 en fonçant à plus de 5 m/s), mais en facteur simple Passing < 50 reste à + 3,7 et la pire tranche monte à 7,9 (la table devrait être réajustée avec cette entrée, sans garantie sur Passing < 50) ;
  - attributs des adversaires : coupe observée / prévue de 0,86 (Anticipation < 45) à 1,06 (75 et plus) ; adversaires des passeurs faibles à peine meilleurs lecteurs (Anticipation 72,3 contre 69 à 70) : au plus 0,2 point ;
  - ligne jouée (angle réellement tiré) au lieu de la ligne idéale, table réestimée sur 24 matchs et contrôlée sur 24 : Passing < 50 + 5,0 -> + 4,8 ;
  - dosage (receveur qui court) : à écart de dosage égal, pertes hors coupe sans ordre selon Passing (2 à 4 m : 6,7 % / 1,3 % / 4,0 % observées pour 3,9 / 3,4 / 3,2 prévues).
- Constat : chez les passeurs faibles, le surplus de pertes est diffus (coupe + 2 points, hors coupe + 1,4) ; passe jouée droit (écart latéral réalisé sous 1 m) perdue hors coupe à 5,4 % contre 1,0 à 1,3 % pour les autres, sans explication géométrique. Probable effet de contexte non mesuré (poste, zone, moment).
- Biais laissés en l'état (moteur `4c9e470`, graines 2600 à 2651) : Passing < 50 + 3,8 ± 1,8 (3 % des passes) ; moins de 8 m + 1,6 ± 0,7 ; 15 à 30 m − 1,1 ± 0,4. Calibration globale : pire tranche 1,5, moyenne − 0,1. À remesurer au `29c`, qui changera la physique et imposera de réestimer la table.
- Critère 1 : tenu. Critère 2 : tenu (aucun fichier du moteur ni des tests modifié ; suite complète : voir Comments). Critère 3 : tenu (`29c` complété).
- Mesures : `docs/INDICATEURS_V2.md` section 63.
- Durée réelle : 1 h 55 (analyse et diagnostic 85 min, documentation et clôture 30 min) pour 3 h 45 estimées (− 49 %) : arrêt à la phase 1 sur décision du propriétaire. Temps machine hors total : 48 matchs d'enregistrement (35 min), suite complète.

## Comments

- 20/11/2026, création pendant le `18o` (décision du propriétaire : Passing < 50 sort du `18o`, « oui valide les 3 »).
- 20/11/2026, réserves A1 et A2 du `18o` renvoyées ici (décision du propriétaire à la clôture du `18o`).
- 20/11/2026, phase 1 : aucune cause unique corrigible (vitesse des adversaires, attributs, ligne jouée, dosage, correctif A2 testés) ; options présentées (A : clore en diagnostic seul ; B : vitesse des adversaires dans la table ; C : poursuivre le diagnostic) ; le propriétaire choisit A (« Ok pour le A »). Implémenté, en attente de clôture.
- 20/11/2026, suite complète (moteur et tests inchangés depuis `4c9e470`) : 3 467 passés, 14 désélectionnés.
- 20/11/2026, clôture, passage 1 : expert APPROVED (A1 à A4 facultatives : écart maximal de recalcul dû aux gardiens écartés par l'enregistrement, masses de bandes non homogènes dans `18p-bandes.py`, chiffres de dosage sur passes « angle juste », source du constat « coupe + 2, hors coupe + 1,4 » au `18o-diagnostic-2.txt`) ; QC VALIDÉ (réserves mineures : « pire tranche 1,5 » et « coupe + 2, hors coupe + 1,4 » tirés du 18o ; + 3,8 contre + 3,9 en colonne moteur) ; clôture VALIDÉ.
