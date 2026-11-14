# 17d: Test de garde : attribut annoncé branché = attribut lu avec effet

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (empêche de confondre un attribut lu et un attribut qui change le jeu). **Catégorie :** validation.

**Constat vérifié :** `tests/test_v2engine_rayon_attributs.py` vérifie les rayons ; aucun test ne vérifie qu'un attribut « branché » dans la carte est lu par le moteur et change l'issue d'une scène.

**What to build:** Test qui lit la carte, liste les attributs marqués branchés, vérifie qu'ils sont lus dans `v2engine/` et, pour chacun, joue une scène A/B (note 99 contre 11, fabrique du 01f) dont un indicateur doit différer.

**Attributs :** aucun

**Blocked by:** 17a (Carte des attributs : état réel de branchement); 01f (Fabrique de scènes de test partagée).

**Bloque :** rien.

**Status:** livré (14/11/2026), validé expert + QC (commit `d465fd1`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : une scène type par attribut, à écrire au fur et à mesure.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** attribut factice marqué branché mais jamais lu : le test échoue

## Acceptance criteria

- [x] Test en place pour tous les attributs branchés (`tests/test_v2engine_garde_attributs.py` : 27 attributs annoncés avec effet, lus dans `v2engine/` et qui font diverger une scène 11 contre 99 ; règle de lecture de la carte dans la docstring)
- [x] Échec démontré sur un cas factice (attribut « Bidon » : non lu, aucune divergence ; « Pace » annoncé « à créer » : signalé ; hors dépôt, Marking lu mais valeur ignorée dans `defense.py` : aucune divergence, le test échouerait)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : environ 40 min pour 180 réestimées (− 78 %), voir le registre
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (chaque profil rejoué jusqu'au pas de divergence, dans le test ; deux exécutions du fichier : 32 passés, mêmes graines et pas)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 3 028 passés, 0 ignoré, 14 désélectionnés (2 996 + 32 tests ajoutés), 12 min 06 (+ 1 min 03 : le nouveau fichier) ; aucun fichier du moteur, V1 ni protégé touché

## Comments

**14/11/2026, implémentation (un seul ticket, décision du propriétaire « fais un seul ticket », réestimé à 3 h au lieu de 1 h 55 : 23 attributs « branché » plus Dribbling, Finishing, Balance et Handling, une scène par attribut).**

- **Règle de lecture de la carte** : un attribut est annoncé avec effet sauf si son état commence par « à créer » ou « non branché » : 27 attributs le 14/11/2026. Contrôle inverse ajouté : un attribut annoncé « à créer » ou « non branché » ne doit pas être lu par le moteur (aucun aujourd'hui).
- **Effet** : même scène, même graine, attribut à 11 puis à 99 sur tous les joueurs ; divergence de l'empreinte exacte (`scenes.fingerprint`). Trois scènes : mini-match (deux onze réels, 60 s, 3 graines), duel au contact (3 s, jusqu'à 300 graines : environ 0,05 tentative de tacle par seconde) et tir dans la surface face au gardien (3 s, jusqu'à 300 graines). Le sens et la taille de l'effet ne sont pas vérifiés : ils relèvent des tests de chaque ticket. Première divergence (graine, pas de 0,1 s) : 19 attributs à la graine 1 dans le mini-match, Flair et Stamina à la graine 2 (pas 288 et 286) ; Tackling (44, 6), Strength et Balance (140, 11), Finishing (1, 5), Reflexes (21, 11), One on Ones et Handling (82, 5). Durée du fichier : environ 48 s.
- **Constat pour le propriétaire (aucun changement ici)** : depuis l'arrêt par portée (05b, 05h), la note du gardien (0,5 Reflexes + 0,3 One on Ones + 0,2 Handling) ne décide plus si le tir est arrêté (`match._keeper_reaches` ne lit que `keeper_reach_m`, sans attribut) ; elle ne règle que la part captée / repoussée de l'arrêt (`flight.chance` → `save_outcome`). D'où leur effet rare en scène (graines 21 et 82). La carte (« note d'arrêt unique… pour tous les tirs ») surestime donc leur rôle : à reprendre au `v2-attributs-restants/03b` (sorties et arrêts) ou au 24.

**14/11/2026, fusion avec main (ticket v2-realisme/24, courbe en S).** La garde a joué son rôle : sur le mini-match de 60 s (3 graines), Long Shots ne divergeait plus, faute de tir hors de la surface avec la nouvelle courbe (fragilité signalée par l'expert, A2). Scène dédiée ajoutée (`tir_de_loin` : tireur à 27 m, défenseur au contact, jusqu'à 300 graines) : divergence à la graine 1, pas 5. Aucun test supprimé ni affaibli.
