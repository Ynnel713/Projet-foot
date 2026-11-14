# 01e: Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (nécessaire aux calibrations provisoires (500 matchs), à la calibration finale et à la validation indépendante). **Catégorie :** mesure.

**Constat vérifié :** le banc publie des moyennes sans intervalle de confiance ; les comparaisons de 20 matchs sont souvent dans le bruit (écart-type des buts d'environ 0,4 noté dans `docs/INDICATEURS_V2.md`).

**What to build:** Exécuter une série en plusieurs processus (une graine par match, résultats agrégés), afficher pour chaque indicateur moyenne, écart-type et intervalle de confiance à 95 %, et comparer deux séries appariées (même graine, deux versions ou deux profils). Estimer et afficher la durée machine avant le lancement.

**Attributs :** aucun

**Blocked by:** 01b (Flux aléatoires : duels, passes, tirs, placement, arbitrage).

**Bloque :** 06c, 13i, 18b, 18d, 27d (ajouté le 14/11/2026).

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 1 h |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : les matchs sont indépendants (aucun état partagé entre processus) ; machine Windows, `multiprocessing` en mode spawn.
Temps machine, non compté : suite complète (environ 40 min) ; essai de 100 matchs.

## Tests

- **Unitaires (scène contrôlée) :** agrégation sur données connues : moyenne et intervalle exacts
- **Intégration :** même graine, 1 processus contre 4 : résultats identiques

## Acceptance criteria

- [x] Intervalles de confiance affichés pour chaque indicateur (moyenne par match, écart-type, IC 95 % ; km par poste compris ; 179 indicateurs sur 179 sur une série de contrôle de 6 matchs courts)
- [x] Résultats identiques quel que soit le nombre de processus (`test_results_do_not_depend_on_the_number_of_processes` : 1 contre 4 processus, comme prévu au ticket, sur 4 matchs d'1 min ; agrégé et valeurs par match identiques)
- [x] Durée machine estimée avant lancement (première ligne affichée ; modèle recalé sur l'essai, voir rapport)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (même test : deux séries des mêmes matchs, sorties identiques ; et agrégé égal à `measure_v2` aux arrondis près)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 399 passés, 14 désélectionnés, contre 2 394 et 14 : 5 tests ajoutés ; attendu mis à jour)

## Rapport d'implémentation (06/11/2026)

**Livré :** `scripts/bench_series.py` (nouveau) : `run_series` (un match par tâche, `ProcessPoolExecutor`, rendu dans l'ordre des matchs, compteurs bruts fusionnés dans un collecteur unique puis `measure_v2.report` : la valeur agrégée est celle de `measure_v2`) ; `summary` (moyenne, écart-type d'échantillon, IC 95 % par approximation normale) ; `confidence` (par indicateur, sur les valeurs par match) ; `compare` (écart apparié après − avant, match par match, mêmes matchs exigés) ; `estimate_seconds` (durée machine affichée avant le lancement) ; ligne de commande (`--processus`, `--json`, `--comparer`, options de `measure_v2`). `docs/INDICATEURS_V2.md`, section 8 (usage, modèle de durée, essai). Aucun fichier du moteur touché ; `measure_v2.py` inchangé.

**Choix :** fusion des compteurs bruts plutôt que moyenne des rapports par lot : la valeur agrégée reste exactement la mesure de `measure_v2` (parts et taux calculés sur les sommes), et les valeurs par match servent aux intervalles. Le découpage par zone, score et minute (`--detail`) n'est pas repris dans les séries. Approximation normale pour l'intervalle (pas de quantile de Student dans la bibliothèque standard) : valable pour 500 matchs et plus, indicative sous une trentaine.

**Durée machine estimée, recalée :** première version : 75 s par match divisées par le nombre de processus ; essai de 100 matchs sur 7 processus : 18 min annoncées, 48,5 min réelles (accélération réelle 2,6, 8 fils logiques, 4 cœurs physiques supposés). Modèle recalé : 0,65 par cœur physique occupé (`PARALLEL_EFFICIENCY`), testé sur le cas mesuré ; à recaler si l'estimation s'écarte de plus de 30 % (commentaire `ponytail:` dans le code). Ordres de grandeur : 500 matchs en 4 h environ, 2 000 en 16 h environ.

**Essai de 100 matchs (7 processus, `6b8d1b8`) :** passes par minute de match 10,97 [10,87 ; 11,07] ; buts par match 4,13 [3,72 ; 4,54] ; tirs tracés par équipe 37,6 [36,8 ; 38,4] ; conversion 5,5 % [4,9 ; 6,0] ; temps de jeu effectif 66,3 % [65,8 ; 66,7]. Cohérent avec la référence de 50 matchs du 01d.

**À surveiller (recommandation de l'expert au 01b) :** passes par minute, pertes de balle, buts dans la surface et réussite des passes en profondeur entre 01a et 01b : comparaison appariée désormais possible (`--comparer`), non lancée ici (elle demande deux séries sur deux versions du moteur, hors du périmètre du ticket).

**Tests ajoutés :** `tests/test_bench_series.py` (5 tests, dont `test_every_indicator_of_any_match_gets_per_match_values`) : moyenne, écart-type et IC sur données connues ; comparaison appariée (match sans valeur écarté, séries non appariées refusées) ; estimation de la durée machine (cas mesuré, plafond de cœurs) ; 1 contre 4 processus sur 4 matchs courts (1 min) : résultats identiques, égaux à `measure_v2` aux arrondis près, km par poste présents ; indicateur absent du premier match : valeurs par match sur tous les matchs (0 pour une part tirée d'un compteur, écarté pour un poste absent).

**Durée :** estimée 2 h 10 (130 min ; 20/60/30/20), réelle environ 1 h 55 (115 min ; 10/45/25/35). Écart − 12 %. Analyse plus courte (matchs déjà indépendants et indexés, `run(start=…)`) ; corrections après le passage 1 (valeurs par match sur tous les matchs, km par poste, fusion au fil de l'eau, paramètres enregistrés) ; estimation de durée recalée après l'essai.

## Comments

- 06/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte a52589de). A1 : pour une part, l'intervalle porte sur la moyenne par match, qui peut différer de la valeur agrégée ; A2 : indicateurs par match pris sur les clés du premier match seulement, parts absentes traitées comme manquantes ; A3 : mémoire des séries de 2 000 matchs (8 à 12 Go estimés) ; A4 facultatif : modèle de durée calé sur 7 processus, paramètres non enregistrés. QC REFUSÉ (indicateurs sans IC, km par poste sans IC, test 1 contre 2 au lieu de 1 contre 4). Corrections (conseils de l'expert acceptés d'office par le propriétaire) : union des clés, 0 pour une part tirée d'un compteur, km par poste dépliés (QC et A2) ; valeur agrégée hors de l'IC signalée dans la sortie (A1, correctif minimal ; intervalle de la valeur agrégée non construit) ; fusion au fil de l'eau sans double rétention, pic mémoire à mesurer avant la première série de 2 000 (A3) ; paramètres enregistrés et comparés (A4) ; test 1 contre 4 processus.
- 06/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS (empreinte b87d2cfb), corrections du passage 1 vérifiées. Réserves acceptées par le propriétaire, une à une, par sa consigne de la session du 06/11/2026 (« Tes recommandations et les conseils d'expert sont automatiquement validé ») : **A1** construire l'intervalle de la valeur agrégée d'une part (jackknife par match ou méthode delta) avant toute décision de calibration sur une part rare ; **A3** mesurer le pic mémoire sur 100 matchs avant la première série de 2 000 (18b ou 18d). Facultatif : A5 modèle de durée linéaire en cœurs (sous-estime 2 ou 3 processus). QC VALIDÉ. **Clôture VALIDÉ.**
