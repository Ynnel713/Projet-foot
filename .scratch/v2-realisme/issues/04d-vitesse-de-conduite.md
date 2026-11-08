# 04d: Vitesse de conduite selon Dribbling et la pression

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un bon dribbleur va plus vite balle au pied). **Catégorie :** physique.

**Constat vérifié :** `DRIBBLE_SPEED_FACTOR = 0.85` (`decision.py:28`) : même part de la vitesse maximale balle au pied pour tous, avec ou sans adversaire.

**What to build:** La part de vitesse maximale balle au pied dépend de Dribbling (conduite serrée) et baisse au contact d'un adversaire. La valeur de l'option de conduite (espace atteint) utilise la même vitesse.

**Attributs :** Dribbling (vitesse balle au pied ; Pace reste la vitesse maximale)

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution).

**Bloque :** 04e.

**Status:** livré (08/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : courbe partagée de `attributes`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** au contact : vitesse plus faible que sans adversaire
- **Comportementaux (profils comparés) :** Dribbling 99 contre 11, même Pace : vitesse moyenne balle au pied plus élevée

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées par Claude, validées par délégation, voir Comments ; chiffre réel non trouvé)
- [x] Même vitesse utilisée à l'évaluation et en mouvement (test : `test_evaluation_and_movement_use_the_same_speed`)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Dribbling reste lu dans `decision` seul ; carte et commentaire de `ALLOWED` mis à jour)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`measure_v2 2` deux fois, identique hors temps de calcul : `04d-det1.txt`, `04d-det2.txt`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 559 passés, 14 désélectionnés (08/11/2026, 15 min 14 s) ; attendu 2 554 + 5 nouveaux

## Comments

- 08/11/2026 : **Constantes proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne permanente ; chiffre réel de la vitesse balle au pied en part de la vitesse max : non trouvé, une recherche sans résultat, ordres de grandeur). **Sans adversaire à 5 m** : 0,85 de la vitesse max à Dribbling 55 (valeur d'avant le ticket, pour ne pas déplacer le joueur moyen), amplitude ±0,05 sur la courbe commune des attributs : 0,90 à Dribbling 99, 0,80 à 11. **Au contact** : `CONTACT_SLOWDOWN` = 0,15, la part de vitesse perdue au prorata de la gêne (0 sans adversaire à 5 m, 1 au contact) : un joueur moyen passe de 0,85 à environ 0,72 au contact. **Une seule fonction**, `decision.dribble_speed_factor(porteur, gêne)`, lue par `free_point` (espace atteint, via `dribble_options`) et par `cerveau.decide` (intensité du porteur) ; `DRIBBLE_SPEED_FACTOR` disparaît. Pace reste la vitesse maximale (le facteur multiplie `max_speed_mps`). **Critères chiffrés** : (1) 0,85 exactement à Dribbling 55 sans adversaire ; (2) 0,90 / 0,80 à 99 / 11 ; (3) au contact, 0,85 x facteur libre ; (4) évaluation et déplacement : même valeur sur une scène ; (5) 20 matchs avant / après, perte de conduite par intervalle et écarts de calibration du 04c dans leurs bornes.
- 08/11/2026 : **Réalisé.** `v2engine/decision.py` (`_CARRY_SPEED`, `CONTACT_SLOWDOWN`, `dribble_speed_factor`, paramètre `speed_factor` de `free_point`), `v2engine/cerveau.py` (intensité du porteur calculée avec la gêne réelle), `v2engine/movement.py` (docstring), `docs/CARTE_ATTRIBUTS_V2.md` (ligne Dribbling), `tests/test_v2engine_rayon_attributs.py` (commentaire). Aucun test existant adapté. 5 tests ajoutés (`tests/test_v2engine_vitesse_conduite.py`) : 0,85 à 55 et 0,90 / 0,80 aux extrêmes, ralentissement au contact proportionnel à la gêne, même vitesse à l'évaluation et au déplacement, un facteur plus faible atteint moins d'espace libre, Dribbling 99 couvre plus de terrain que 11 à Pace égal.
- 08/11/2026 : **Mesure (20 matchs, graine d'audit, 3 lots ; avant = même code avec facteur 0,85 pour tous et aucun ralentissement, fichiers `04d-avant.json` et `04d-apres.json`).** Conduite : intervalles par match 2 246 → 2 219, pertes par match 86,6 → 92,3, perte par intervalle 3,9 → 4,2 % (sans adversaire proche 0,5 → 0,7 %, serrée 4,4 → 4,6 %) ; écarts d'étalonnage du 04c (risque évalué contre perte tirée) toujours sous 0,6 point par tranche de Dribbling (critère du 04c : 3 points). Jeu : passes 848 → 838, tirs par équipe 18,3 → 18,8, tirs de près (16 m) par équipe 4,98 → 4,30, part des tirs de près 27,2 → 22,9 %, distance moyenne au but des tirs 20,5 → 21,1 m, chance du tir 0,082 → 0,067, buts 2,95 → 2,55 par match, conversion 6,5 → 5,5 %, distance au-dessus de 19,8 km/h par joueur −1 à −4 % selon le poste. **Lecture** : le sens est celui attendu (conduite plus lente sous pression, donc moins de pénétrations jusqu'aux abords du but) ; à 20 matchs, buts et conversion restent dans le bruit (les lots d'avant vont de 2,1 à 4,5 buts par match) ; la part de buts dans la surface (86 → 66 %) est la plus forte variation et repose sur une soixantaine de buts. À reprendre sur 50 matchs avant tout calage de constante.
- 08/11/2026 : **Limites.** (1) Aucun indicateur du banc ne mesure encore la vitesse moyenne balle au pied par niveau de Dribbling : le critère « Dribbling 99 contre 11, même Pace » n'est vérifié que par le test de scène (distance parcourue en 5 s), pas par une série de matchs (`--profil Dribbling` non lancé). (2) La vitesse ne dépend que de Dribbling et de la gêne : ni Agility ni Balance (carte des attributs, règle anti double comptage) ; le ralentissement dans les virages relève de 07f et 12b. (3) Les valeurs 0,80 à 0,90 et 15 % sont des ordres de grandeur sans source.
- 08/11/2026 : **Durée** : estimée 1 h 30 (90 min ; 15/35/25/15), réelle environ 1 h 25 (85 min ; 15/20/25/25, non chronométrée), écart environ − 6 % ; l'intégration pèse plus que prévu (mesure avant / après avec un lot de 6 processus, déterminisme). Temps machine, hors total : mesure 20 matchs avant et après (6 lots, environ 65 min), déterminisme (2 matchs, environ 6 min), suite complète 15 min 14 s.
- 08/11/2026 : **Clôture.** Expert : `APPROVED_WITH_RESERVATIONS` (empreinte 6d4e73c0…). QC (`valider-etape`) : `VALIDÉ`. Décision de clôture : `VALIDÉ`. Suite complète relancée sur l'état final : 2 559 passés, 14 désélectionnés (19 min 52 s). Réserves : **A1** (le joueur moyen ralentit d'environ 10 % en pratique : 80 % des intervalles de conduite ont une gêne ≥ 0,5, contrairement à « ne pas déplacer le joueur moyen » ; mesure à 50 matchs avant tout calage, `CONTACT_SLOWDOWN` à recaler vers 0,08 à 0,10 si les tirs de près sortent de la fourchette de `INDICATEURS_V2.md`) ; **A2** (le critère « Dribbling 99 contre 11 » n'est vérifié que par un test de scène : ajouter une vitesse moyenne balle au pied par tranche de Dribbling au banc, au 04e) ; facultatif **A3** (assertion tautologique et `slow is None` toléré dans deux tests, à renforcer). QC, réserve mineure : aucun test ne prouve que `dribble_options` transmet `dribble_speed_factor` à `free_point` (relu dans le diff, correct). Réserves A1 et A2 acceptées d'office par la consigne permanente du propriétaire du 08/11/2026 (« je valide automatiquement toutes tes recommandations, les avis d'expert… »). Durée : voir le commentaire précédent (réelle 1 h 25 contre 1 h 30 estimée).
