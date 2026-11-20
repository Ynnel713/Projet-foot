# 18o: Chance évaluée : passeurs faibles et receveur marqué de face

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (calibration).

**Constat vérifié (20/11/2026, clôture du `18n`) :** sur 48 matchs joués avec le moteur du `18n` (graines 2400 à 2447, 60 231 passes de jeu au sol, `.scratch/v2-realisme/mesures/18n-controle.txt`) :
- passeurs à Passing < 50 : chance évaluée surestimée de + 3,6 ± 1,9 point (1 830 passes ; + 2,0 ± 1,8 avant le `18n`). Rejoint la réserve A2 du `23a` (Passing pèse peu sur la passe courte) ;
- adversaire à moins de 1,5 m du receveur, entre le passeur et lui : chance sous-estimée de 12,5 ± 4,9 points (385 passes : évaluée 0,49, non perdue 0,61) ; sur la ligne (moins de 0,5 m) : − 12,7 ± 8,0 (149). À l'inverse, dans le cas statique du test `test_the_called_player_is_a_pass_option_only_when_he_is_not_covered` (adversaire immobile à 0,5 m devant le receveur, passe de 12 m), la chance remonte à 0,70, au seuil `OPEN_LANE_PROBABILITY`. La table du `18n` ignore la proximité du receveur.

**What to build :** diagnostic d'abord, sur des matchs joués avec le moteur courant : écart évaluée / observée par Passing croisé avec la longueur et la bande d'écart ; et pour les adversaires près du receveur, par distance au receveur et position (devant, à côté, derrière). Trouver le facteur en cause (poids de Passing dans l'erreur de passe, ou entrée « proximité du receveur » dans la table de coupe) et le corriger seul. Ajouter un test explicite du receveur marqué au contact. Toute constante nouvelle est proposée au propriétaire avant d'être codée. Facultatif, à la même remesure (réserve A3 du `18n`) : lissage monotone ou interpolation de la table dans le temps.

**Critères d'acceptation (proposés) :** Passing < 50 à moins de 2 points ; passes avec un adversaire à moins de 1,5 m du receveur à moins de 4 points (sur au moins 500 passes, série plus longue si besoin) ; critère du `18n` toujours tenu (au plus 4 points par tranche d'au moins 500 passes, moyenne à 0,5 point).

**Attributs :** Passing (aucun nouveau).

**Blocked by :** aucun.

**Status:** livré (20/11/2026), validé expert + QC

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

## Critères d'acceptation (posés avant le code, 20/11/2026, après la phase 1)

Périmètre réduit par le propriétaire (« oui valide les 3, lance la phase 2 », 20/11/2026) : Passing < 50 sort du ticket (cause non unique, ticket à ouvrir sur la vitesse des adversaires vers la ligne) ; le test du receveur marqué fige la valeur réelle du moteur (ticket de physique à ouvrir : le défenseur collé devant le receveur gagne trop peu le ballon).

1. Passes avec un adversaire à moins de 1,5 m du receveur, entre le passeur et lui : écart évaluée / non perdue à moins de 4 points, sur des matchs joués avec le moteur modifié (graines 2500 à 2547 ; série plus longue si moins de 500 passes, l'intervalle est alors rapporté).
2. Critère du 18n toujours tenu sur les mêmes matchs : au plus 4 points par tranche d'au moins 500 passes (7 tranches), moyenne à 0,5 point ; passes de moins de 15 m et de 15 à 30 m à moins de 1 point.
3. Un seul facteur corrigé (reste du trajet après l'adversaire), constantes validées par le propriétaire avant le code.
4. Test explicite du receveur marqué au contact (valeur du moteur : chance au-dessus de 0,6) ; 50 matchs appariés : réussite des passes de jeu au-dessus de 80 %, buts et tirs sans écart au-delà du bruit ; déterminisme (même empreinte sur deux exécutions à graine fixée) ; suite complète verte.

## Clôture

- Cause (receveur marqué) : la table de coupe ignorait que le receveur dispute le ballon ; un adversaire à moins de 2 m du bout du trajet coupe bien moins que prévu, et ces cas, mêlés à l'ajustement du 18n, faisaient sous-estimer ceux de 3 à 5 m du bout.
- Correction (`v2engine/possession.py`) : table réestimée sur les adversaires à au moins 2 m du bout (`CUT_REST_FULL_M`), facteur `_CUT_REST_FACTOR` sous 2 m selon le reste du trajet et l'écart à la ligne (`CUT_REST_GAP_M`) : 0,50 / 0,66 / 0,81 / 0,90 sur la ligne, 0,26 / 0,36 / 0,46 / 0,65 à côté. Premier jeu (ajusté sur 48 matchs) : surcorrection hors échantillon (+ 5,0 ± 4,3 points) ; réajusté sur 96 matchs (« oui pars sur A », puis « oui valide, code et lance le contrôle », 20/11/2026).
- Critère 1 : tenu. Contrôle sur 52 matchs joués (graines 2600 à 2651, 64 887 passes) : adversaire à moins de 1,5 m du receveur − 0,6 ± 4,2 point (528 passes ; − 12,5 avant), sur la ligne + 0,5 ± 7,5 (169).
- Critère 2 : tenu sauf les passes de 15 à 30 m. Pire tranche 1,5, moyenne − 0,1, moins de 15 m + 0,9 ; 15 à 30 m − 1,1 (réserve annoncée au propriétaire : − 1,3 sans le facteur sur l'échantillon d'ajustement, biais antérieur au ticket).
- Critère 3 : tenu (un facteur, reste du trajet ; constantes validées avant le code).
- Critère 4 : tenu. Test `test_marked_receiver_at_contact_keeps_the_measured_engine_chance` (0,72) et `test_receiver_contests_the_ball_near_the_end_of_the_pass` ; 50 matchs appariés : réussite des passes 84,7 % → 85,2 % (+ 0,5 ± 0,4), passes interceptées − 6,0 ± 5,8, tirs + 0,7 ± 1,9, buts − 0,26 ± 0,86 ; déterminisme : empreinte `2c5c9208a1790fa2` deux fois (match 3 du banc) ; suite complète : 3 467 passés, 14 désélectionnés (3 465 au 18n, + 2 tests).
- Hors ticket : Passing < 50 + 3,8 ± 1,8 (ticket `18p`) ; receveur marqué de face au contact jugé ouvert, fidèle au moteur (ticket `29c`).
- Mesures : `docs/INDICATEURS_V2.md` section 62 ; scripts `.scratch/v2-realisme/mesures/18o-*`.
- Durée réelle : 3 h 45 (analyse et diagnostic 90 min, développement 35, tests 30, intégration 70) pour 3 h 10 estimées au départ (+ 18 %), 4 h 15 après la révision de l'option A. Temps machine hors total : 4 x 48 matchs d'enregistrement et de contrôle (environ 2 h 20), 50 matchs appariés (35 min), suite complète (17 min).

## Comments

- 20/11/2026, création à la clôture du `18n` (réserves A1 et A2 de l'expert ; décision du propriétaire : « j'accepte A1 et A2, un seul ticket 18o »).
- 20/11/2026, phase 1 (diagnostic, `.scratch/v2-realisme/mesures/18o-*`, enregistrement enrichi des 48 matchs du contrôle du 18n, graines 2400 à 2447, mêmes 60 231 passes) :
  - receveur marqué : cause trouvée. La table de coupe ignore que le receveur dispute le ballon : un adversaire à moins de 2 m du bout du trajet coupe bien moins que prévu (reste sous 0,5 m : 6 % observé contre 18 % prévu) ; en contrepartie, ceux à 3 à 5 m du bout sont un peu sous-estimés (rapport 1,13). Correction : table réestimée sur les adversaires à au moins 2 m du bout, facteur par reste du trajet sous 2 m et classe d'écart (moins de 1 m / 1 m et plus) : 0,32 / 0,64 / 0,73 / 1,0 et 0,35 / 0,39 / 0,53 / 0,58. En échantillon : adversaire à moins de 1,5 m du receveur − 12,6 -> + 0,9 point, pire tranche 1,4 ;
  - Passing < 50 : pas de cause unique. Écartés : erreur de vitesse (+ 3,4 avec la vitesse réalisée), écart latéral réalisé, pression, dosage, poste (gardiens calibrés). Piste : la table ignore la vitesse des adversaires vers la ligne (plus de 3 m/s : coupe 1,3 à 2 fois la prévue pour tous ; 0,40 contre 0,20 chez les passeurs faibles) ;
  - cas statique (marqueur immobile 0,5 m devant le receveur) : chance d'environ 0,73 après correction, fidèle au moteur (ces passes sont gardées deux fois sur trois en match), sans doute irréaliste physiquement ;
  - décisions du propriétaire : « oui valide les 3, lance la phase 2 » (constantes, Passing < 50 hors ticket, test figeant la valeur du moteur et ticket de physique).
  - Estimation revue : diagnostic 1 h 30 (1 h 05 prévue, enregistrement enrichi à relancer), phase 2 2 h ; total 3 h 30.
- 20/11/2026, phase 2 : premier jeu de facteurs (48 matchs) surcorrige hors échantillon (+ 5,0 ± 4,3, graines 2500 à 2547) ; option A choisie par le propriétaire (réajustement sur 96 matchs, contrôle sur les graines 2600 à 2651) ; estimation portée à 4 h 15. Implémenté, en attente de clôture.
- 20/11/2026, clôture, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC REFUSÉ (passes de 15 à 30 m à − 1,1 point, critère 2, sans acceptation tracée du propriétaire) ; pas de décision de clôture (fichier ticket et plan inclus à tort dans les fichiers revus : revue refaite sur la liste corrigée).
  - A1 (réserve) : passes de 15 à 30 m à − 1,1 ± 0,4 point (critère 2 : moins de 1 point) ; biais antérieur (− 0,9 au 18n, − 1,3 sans le facteur).
  - A2 (réserve) : passes de moins de 8 m de + 0,4 à + 1,6 ± 0,7 point (moins de 15 m + 0,9) ; facteur appliqué aussi au presseur d'une passe très courte, à moins de 2 m du bout ; correctif proposé : facteur seulement si l'adversaire est plus près du receveur que du passeur.
  - A3 (facultative) : saut de la coupe à 2 m du bout (rejoint la réserve A3 du 18n, lissage).
  - Réserves A1 et A2 acceptées par le propriétaire : « Je recommande d'accepter A1 et A2 en réserves et de les renvoyer toutes les deux au 18p pour clôturer le 18o dès maintenant ». Suite : `18p`.
- 20/11/2026, clôture, passage 2 (fichiers revus corrigés, code inchangé) : expert APPROVED_WITH_RESERVATIONS (A1, A2 confirmées, renvoyées au `18p` ; A3 facultative) ; QC VALIDÉ ; clôture VALIDÉ (réserves A1 et A2 acceptées par le propriétaire, mots cités au passage 1).
