# 05e: La valeur du tir dans la décision suit la résolution physique

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (évite de recréer l'écart corrigé au 04a, côté tir). **Catégorie :** décision.

**Constat vérifié :** la décision évalue le tir avec `occasion_quality` (`shooting.py:177`, formule analytique) ; après 05a à 05c, l'issue réelle vient de la trajectoire : les deux peuvent diverger.

**What to build:** Mesurer, sur scènes et en match, le taux de buts réel en fonction des mêmes variables que la formule (distance, angle, gardien, contreurs, pression, exécution), et ajuster la formule d'évaluation pour qu'elle reste un estimateur juste de la résolution (table de correction ou recalage des coefficients).

**Attributs :** aucun

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); 05c (Contre : le défenseur touche réellement le tir); 06a (xG après frappe : la qualité d'exécution mesurée); 05h (Allumer le tir physique, découpé du 05b le 08/11/2026).

**Bloque :** 05g, 06c.

**Status:** livré (10/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible. Hypothèses : besoin possible de 500 matchs (01e) pour une table fiable.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 500 matchs.

**Estimation révisée (10/11/2026, avant le code)** : 2 h 10 maintenue, confiance moyenne. Temps machine, hors total : deux relevés de 120 matchs (avant, après : environ 1 h 30 chacun sur 7 processus), grille de scènes (environ 1 min), suite complète (environ 40 min).

## Constantes et méthode (10/11/2026)

- **Aucune constante nouvelle.** La grille de scènes (05e, avant le code) montre que la formule analytique `shot_probability` ne suit pas la physique, ni en niveau ni en ordre : 15 % évalué contre 33 % observé à 11 m face au but, 37 % contre 22 % à 6 m. Une table de correction sur la chance évaluée (recalage logistique) ne peut pas corriger un ordre inversé. Recommandation retenue (validée d'office par le propriétaire, 10/11/2026, « je valide toutes tes recommandations ») : la chance hors contre est calculée avec les lois de la résolution (`shooting.physical_shot_chance`) : écart gaussien du ballon (note, pression, Composure), dévissé, cadre, portée du gardien au temps de vol, disque de portée coupé par la ligne de but. Elle reprend les constantes déjà validées (05a, 05b, 05h, 35b).
- Chance de contre : d'abord laissée au cône (`block_probability`), puis calculée elle aussi avec les lois du contre physique (voir « Périmètre élargi en cours », section Mesures) ; le cône reste la règle du gardien. La formule analytique reste celle de l'issue d'un arrêt (`save_shares`, difficulté), hors de ce ticket.
- **Méthode pour les tickets suivants** (`scripts/shot_calibration.py`, docstring) : toute modification de la résolution du tir se reporte dans `physical_shot_chance`, puis grille de scènes et relevé de matchs.

## Critères chiffrés (posés le 10/11/2026, avant les mesures en match)

- **Scènes** : 20 positions (6, 11, 16, 20, 25 m de la ligne ; 0, 5, 10, 15 m de l'axe), 2 000 tirs chacune, tireur et gardien neutres : chance évaluée dans l'intervalle à 95 % (Wilson) du taux de buts observé, pour chaque position.
- **Matchs** : 120 matchs après le changement (graines 2200 à 2319, indépendantes du relevé avant, 2000 à 2119), par tranche de chance évaluée (bornes du 06c) : tranche calibrée si l'intervalle de Wilson du taux de buts contient la chance moyenne, tolérée si l'écart est sous 0,02 ; taux de buts global à ± 10 % de la chance moyenne. Avant/après publiés.
- **Jeu** : temps de calcul par match publié (surcoût par appel mesuré : 410 µs contre 346 µs).

## Tests

- **Unitaires (scène contrôlée) :** grille de 20 positions de tir, 2 000 tirs chacune : écart chance évaluée / taux observé
- **Statistiques (séries de matchs) :** 500 matchs : courbe de calibration de la chance évaluée

## Mesures (10/11/2026, `.scratch/v2-realisme/mesures/05e-*`, détail : `docs/INDICATEURS_V2.md`, §21)

- **Constat avant** (120 matchs, 2000 à 2119) : aucune tranche de chance évaluée calibrée, ordre faux près du but (sous 8 m : 0,40 évalué, 0,20 observé ; 8 à 12 m : 0,12 contre 0,28) ; contres prévus par le cône : 0,2 % contre 9,9 % observés au bas, 60 % contre 40 % au haut.
- **Périmètre élargi en cours (annoncé, nouvelle estimation 3 h 30)** : la chance de contre faussait aussi la valeur du tir. Même principe, sans constante nouvelle : portée de chaque défenseur à sa place à l'arrivée du ballon, au temps de vol (corps puis jambe, y compris au pas suivant de la boucle), écart du ballon gaussien, un ballon contré n'atteint pas les suivants ; but et contre jugés ensemble, écart par écart (un défenseur dans l'axe contre surtout des tirs qui allaient au but). Le cône `block_probability` reste la règle du gardien (`gardien.py`, test de garde). Portée du gardien coupée par la ligne de but (le moteur juge l'écart sur la ligne si le ballon la franchit avant de passer au plus près), temps de vol au pas de la boucle (0,1 s). Repli neutre sans gardien identifiable : gardien bien placé (comme avant). Banc du 06c : chance neutre hors contre lue directement (`neutral_open_chance`), plus xG / (1 − contre).
- **Scènes** : 20 positions sur 20 sans défenseur dans l'intervalle à 95 % (écart maximal 1,2 point ; sortie de la grille : `05e-scenes.txt`, réserve A2 de l'expert) ; contres 7 scènes sur 7 ; but avec défenseurs 6 sur 7 (défenseur à 2 m du tireur : 11,2 % contre 13,1 %).
- **Matchs** (120, 2200 à 2319, `05e-apres.*` ; un premier relevé intermédiaire `05e-apres-v1.*`, cône encore en place) : **7 tranches de chance évaluée sur 7 calibrées** ; global 0,090 évalué, 0,093 observé (3 %). Écarts restants, listés sans réglage : 12 à 16 m (0,191 contre 0,146), angle 15 à 25° (0,062 contre 0,071), contres sous 0,05 prévus (1,5 % contre 4,1 %).
- **Jeu** : 48,4 tirs et 4,52 buts par match (avant 47,3 et 4,26), 20,2 % de tirs contrés (18,5 %). Le tir est valorisé à la physique du moteur, plus généreuse que le réel, face aux passes valorisées en xT réel : volume et conversion au 22c. Temps de calcul inchangé (86,7 min contre 88,1 pour 120 matchs).
- **Tests** : `tests/test_v2engine_chance_tir.py` (17 tests : scènes de but, de contre, but et contre ensemble, pas de la boucle, note, pression, gardien, repli, garde du cône du gardien) ; adaptés : `test_v2engine_decision.py` (scène à 9 m face à un gardien : à 6 m sans gardien, la chance physique écrasait les autres options), `test_v2engine_meilleur_choix.py` (deux scènes reculées à 21 m : un tir de 15 m vaut désormais 0,18 à 0,24), `test_v2_indicators.py` (chance neutre hors contre).
- **Déterminisme** : 3 matchs (2200 à 2202) joués deux fois, mêmes 136 tirs, empreinte `72d464c777a8`, identiques à la série.
- **Suite complète** (`05e-suite.txt`) : 2 643 passés, 14 désélectionnés = 2 626 (attendu réel avant le ticket : 2 611 de `CLAUDE.md` + 15 tests des maillots, commit `9eb0869`, attendu non mis à jour) + 17 tests du 05e.
- **Non fait** : courbe du 06c sur 500 matchs non relancée (environ 7 h de machine) ; le contrôle sur 120 matchs porte sur la même chance.
- **Durée** : estimée 2 h 10, révisée 3 h 30 en cours de route ; réelle environ 3 h 40 (+ 5 % sur la révisée, + 69 % sur l'initiale : périmètre élargi au contre et à la géométrie exacte de l'arrêt), non chronométrée.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Écart chance évaluée / taux observé sous le seuil validé par tranche
- [x] Méthode de recalage documentée pour les tickets suivants
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 10/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte 2b4c7a43) ; QC VALIDÉ. Réserves : A1, biais résiduel à 12-16 m (0,191 évalué contre 0,146 observé), reporté au 05g (écart au gardien selon la distance avant tout réglage) ; A2, grille des 20 scènes non archivée, corrigée (`05e-scenes.txt`, 20 sur 20 calibrées) ; A3, phrase du ticket contredite par l'implémentation (contre), corrigée ; A4 (facultatif), docstring de `occasion_quality` et champ « hors contre » du script, corrigés. Réserves acceptées par le propriétaire : « Je valide toutes tes recommandations et les avis d'expert » (10/11/2026).
- 10/11/2026, passage 2, clôture : expert APPROVED_WITH_RESERVATIONS (empreinte 896c5cec) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05e/cloture`), commit `839ad1f`. A2, A3 et A4 du passage 1 levées. Réserve A1 (biais 12-16 m) reconduite, acceptée par le propriétaire (« Je valide toutes tes recommandations et les avis d'expert », 10/11/2026), reportée au 05g ; facultatif A2 du passage 2 : reports inscrits dans le ticket 05g. Statut passé à « livré » dans le commit du 05g (le ticket faisait partie des fichiers revus du 05e).
