# 07g: Validation de l'orientation

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle avant la perception (08)). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur d'orientation.

**What to build:** Indicateurs : part des réceptions par type et par poste, délai moyen de rotation avant une action, vitesse à reculons des défenseurs. Scènes de référence et rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 07b (Se déplacer de face, de côté ou à reculons); 07c (Réception de face, de profil ou dos au jeu); 07d (Temps de contrôle et enchaînement selon l'orientation); 07e (Se réorienter avant une passe, un tir ou une conduite); 07f (Agility : vitesse de rotation du corps); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** rien.

**Status:** livré (14/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

**Réestimation (14/11/2026)** : 2 h 15 (analyse 30 min, développement 35 min, tests 25 min, intégration et enquête 45 min), confiance moyenne, après l'ajout des reprises (dérive des buts, face-à-face, contrôle à l'aveugle, cap qui tremble) et de l'enquête par séries appariées et ablations. Annoncée en cours de route, après le début de l'enquête (écart à la règle de `CLAUDE.md` : la réestimation aurait dû précéder la suite). Temps machine, non compté : quatre séries de 60 matchs (graines 50 à 109), déterminisme 2 x 2 matchs, deux suites complètes.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [x] Indicateurs définis et ajoutés (`docs/INDICATEURS_V2.md`, indicateur n° 28 ; `scripts/v2_indicators.py`, `scripts/measure_v2.py` ; `ReceptionEvent.facing_run`, mesure seule)
- [x] Rapport publié (`docs/INDICATEURS_V2.md`, section 37 ; séries de 60 matchs, graines 50 à 109, au lieu de 50 : une série à graines nouvelles, appariée, demandée par les reprises)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07g-det1`, `07g-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 933 = 2 927 + 6)

## Comments

**13/11/2026, repris du 07b (réserve A1 du passage 2, acceptée par le propriétaire).** Tirs en face-à-face 13,9 → 15,7 par match après le 07b (+ 13 %, environ 2,4 écarts-types ; 16,2 avant la correction du pivot sur l'appel dans le dos), cause non établie. À isoler ici, sur les graines du 08f (`.scratch/v2-realisme/mesures/08f-50-lot*`), avant toute calibration des face-à-face : pas chassés à 90 % au lieu de 80 % ; vitesse de cible (`target_velocity`) des cibles de ligne et de couverture. Aucune constante changée sans validation du propriétaire. Aussi (facultatif A2 du passage 2) : vérifier qu'un marqueur dont l'attaquant court autour de sa vitesse à reculons ne fait pas trembler son cap.

**13/11/2026, repris du 07d (réserve A2 de l'expert).** Buts par match aux mêmes graines : 07b 3,12 ; 31a 3,02 ; 31b 3,10 ; 31c 3,48 ; 07d 3,62 (3,86 avant la correction du contrôle à l'aveugle), au-dessus du repère 2 à 3,5 ; chaque pas est sous une erreur type (environ 0,4 sur 50 matchs), la dérive cumulée non. À isoler ici sur une série plus longue (graines différentes, 01e) avant toute calibration (18d, 18e, 22c) : contrôle orienté et vitesse de réception (31b, 31c), face-à-face (07b, déjà à suivre ici).

**13/11/2026, repris du 07d (facultatif A1 de l'expert, passage 2).** Contrôle à l'aveugle : « lancé » = vitesse au moins 19,8 km/h (`match`, au contact), sans `PlayerState.facing_run` (07b) ; un appel en profondeur à 4 ou 5 m/s, corps vers sa course, peut compter à l'aveugle s'il ne contrôle pas orienté. Mesurer la part des contrôles à l'aveugle avec `facing_run` vrai ; si elle est notable, proposer au propriétaire `running = facing_run ou vitesse au-dessus du seuil`.

**14/11/2026, implémentation et rapport.** Indicateurs n° 28 (`docs/INDICATEURS_V2.md`) dans `scripts/v2_indicators.py` et `scripts/measure_v2.py` : type de réception par poste, délai moyen de rotation avant la passe ou le tir (rotations nulles comprises), course à reculons des défenseurs (DC, LB, RB : part du temps, vitesse moyenne et maximale, distance par 90 min ; seuils de mesure 135° et 1 m/s), contrôles à l'aveugle corps vers la course (`ReceptionEvent.facing_run`, champ de trace ajouté, sans effet sur le jeu), changements du choix course / ballon du cap et part défaite en moins de 0,5 s. `scripts/bench_series.py` : fusion des maxima (défaut préexistant, agrégé à 0). 6 tests (`tests/test_v2engine_orientation_validation.py`). Rapport : `docs/INDICATEURS_V2.md`, section 37.

**Reprises.** (1) Dérive des buts (A2 du 07d) : sur 60 matchs à graines nouvelles (50 à 109), appariés, 07b → 07d : buts + 0,20 (IC − 0,51 ; + 0,91), non établie ; xG neutre **+ 0,53 (+ 0,17 ; + 0,88)**, tirs + 1,4 par équipe, tirs de près + 0,63, temps par possession − 0,16 s. Ablation : sans le temps de contrôle bimodal du 31b, xG − 0,50 (− 0,83 ; − 0,16) : cause principale isolée (contrôle orienté rapide près du but). Part du 07d non mesurée (ablation perdue au redémarrage du conteneur). Aucune constante changée ; recommandation : garder le 31b, traiter le volume de tirs à la calibration finale (22c) et regarder la fermeture de la surface (10f, 10g). (2) Face-à-face (A1 du 07b) : pas de hausse significative du 07b au 07d (+ 0,65, IC − 0,88 ; + 2,18) ; la hausse propre au 07b n'est pas remesurée, pistes ouvertes. (3) Contrôle à l'aveugle corps vers la course (A1 du 07d) : 11,9 % des contrôles à l'aveugle, faible : pas de proposition. (4) Cap qui tremble (A2 du 07b) : 8,7 à 14,4 changements par joueur et par minute, dont 11 à 16 % défaits en moins de 0,5 s : à vérifier à l'écran.

**14/11/2026, suite et déterminisme.** Suite complète : 2 933 passés, 0 ignoré, 14 désélectionnés (2 927 + 6 ; `.scratch/v2-realisme/mesures/07g-suite.txt`) ; `CLAUDE.md` mis à jour. `07g-det1` et `07g-det2` (2 matchs, graine fixée) identiques hors temps de calcul. V1 inchangée (aucun fichier V1 touché).

**14/11/2026, durée.** Estimation 1 h 30, réestimée 2 h 15 en cours de route ; durée réelle environ 2 h 20 (analyse 35, développement 35, tests 20, intégration et enquête 50), + 56 % sur l'estimation d'origine : périmètre élargi par les quatre reprises (enquête par séries appariées et ablation), dont la réestimation a été annoncée tard ; + 4 % sur la réestimation. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : quatre séries de 60 matchs (environ 60, 63, 35 et 30 min, une perdue par manque de mémoire puis relancée, une perdue au redémarrage), déterminisme 2 x 2 matchs, deux suites complètes.

**14/11/2026, clôture (passage 1).** Expert : APPROVED (empreinte 20de9ec4). QC : VALIDÉ. Clôture journalisée : VALIDÉ. Aucune anomalie bloquante. Facultatifs de l'expert : A1, libellé du maximum à reculons (c'est la moyenne des maxima par match, 6,0 m/s ; libellé précisé dans la section 37) ; A2, compter le recul après une durée minimale (0,3 s au-delà de 135°) si l'indicateur sert un jour à calibrer. À surveiller : volume de tirs et effet du 31b sur l'xG (22c, 10f, 10g) ; hausse des face-à-face propre au 07b non remesurée ; ablation de la part du 07d à refaire. Aucune réserve à accepter.

