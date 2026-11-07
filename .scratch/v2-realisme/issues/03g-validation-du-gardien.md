# 03g: Validation du placement et des sorties du gardien

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (la position doit être juste avant de calibrer les arrêts). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur sur la position du gardien (le banc ne mesure que les issues des arrêts, ticket 28b).

**What to build:** Indicateurs : écart à la bissectrice au moment des tirs, distance à sa ligne par zone du ballon, sorties par match et leur issue, distance maximale à son but. Scènes de référence rejouées et rapport sur 50 matchs ; aucune calibration du taux d'arrêt.

**Réserves reportées ici par les clôtures du 03d et du 03e** (périmètre du 07/11/2026) : sorties disputées et filtre de portée (03d A1), profondeur de face-à-face derrière une ligne haute (03e A1, seul changement de code du ticket), profondeur cible atteinte au tir (03e A2, facultative). Les réserves 03c A1 (hausse des tirs) et A3 (saut de cible) passent au ticket **03h**.

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux); 03c (Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur)); 03d (Gardien : sortie sur un ballon dans la profondeur); 03e (Gardien : fermer l'angle dans un face-à-face); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 18a, 18e, 03h.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

Révisée le 07/11/2026 (réserves des 03c, 03d et 03e). Estimation d'origine : 1 h 35 ; le périmètre complet faisait environ 3 h 45, donc découpage (seuil de 2 h de `CLAUDE.md`) : 03g à 2 h 15, le reste au 03h.

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement (indicateurs, correctif 03e A1) | 55 min |
| Tests unitaires et scènes de référence | 35 min |
| Intégration et vérifications (rapport, documentation) | 20 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : les indicateurs lisent la trace et les observateurs du banc sans toucher au moteur, sauf le correctif 03e A1 (une ligne de profondeur transmise).
Temps machine, non compté : suite complète (environ 40 min) ; deux séries de 50 matchs (avant / après le correctif), environ 25 min chacune.

## Tests

- **Unitaires (scène contrôlée) :** indicateurs calculés sur trajectoires synthétiques
- **Scènes de référence :** une table de scènes rejouées dans `tests/test_v2engine_gardien.py` (état attendu et profondeur visée), dont « ballon à 18 m du gardien, défenseur à 15 m du ballon, attaquant à 30 m » (03d A1) et « ligne à 40 m, porteur seul à 22 m » (03e A1)
- **Statistiques (séries de matchs) :** 50 matchs, rapport dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

Constantes de mesure proposées avant le code (voir Comments), critères chiffrés :

- [x] Indicateurs définis par écrit (`docs/INDICATEURS_V2.md`, section 11) et ajoutés au banc (`scripts/v2_indicators.py`, `scripts/measure_v2.py`) : (1) distance du gardien à sa ligne par zone du ballon (moins de 12 m, 12 à 25 m, 25 à 40 m, 40 m et plus de son but) ; (2) sorties disputées (un adversaire arrive au point visé au plus 2,0 s après le gardien) et leur issue ; (3) courses gagnantes masquées par le filtre de portée, avec et sans coéquipier qui l'emporte ; (4) écart à la profondeur cible de face-à-face au tir
- [x] Chaque indicateur testé sur une trajectoire synthétique à résultat connu (`tests/test_v2_indicators.py`, 4 tests nouveaux)
- [x] 03e A1 (`tests/test_v2engine_gardien.py`, 3 tests nouveaux) : derrière une ligne à 40 m, un porteur seul à 22 m laisse le gardien au moins aussi avancé que son placement avec cette ligne ; 03d A1 : scène 18 m / 15 m / 30 m rejouée (état attendu documenté)
- [x] Rapport 50 matchs publié (section 11 ; `.scratch/v2-realisme/mesures/03g-avant.*` et `03g-apres.*`) (avant / après le correctif 03e A1), avec la limite du 03c A2 écrite (le plafond de 16 m laisse une profondeur découverte derrière une ligne haute)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : environ 175 min contre 135 estimées (+ 30 %, durée estimée, non chronométrée)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`d183e42f14c5ba1b`, 2 matchs, rapport sans la ligne du temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 517 passés, 14 désélectionnés (07/11/2026, état final) ; 2 510 à la clôture du 03e + 7 tests nouveaux (4 du banc, 3 de scènes) ; `CLAUDE.md` indique encore 2 500 (non mis à jour depuis le 03d, verrou de commit : à faire avec un autre fichier)

## Comments

- 07/11/2026 (15 h 55) : **Constantes de mesure proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne permanente ; aucun repère réel trouvé, ordres de grandeur du banc). **Zones du ballon** : distance du ballon à son but, bornes 12 m et 40 m (celles de `BALL_DISTANCE_M`) et 25 m (`FACE_RANGE_M`). **Sortie disputée** : au début de l'épisode, `defense.arrival_time_s` de l'adversaire de champ le plus rapide au point visé moins celui du gardien est de **2,0 s ou moins** ; issue gagnée = le gardien a le ballon (relance). **Course gagnante masquée** : ballon libre qui ne vient pas de son équipe, le gardien gagnerait la course (`gardien.race`) mais le filtre de portée (moins de 15 m, ou plus proche de son équipe) le laisse en placement ; comptée « le coéquipier l'emporte » si le coéquipier le plus proche arrive avant l'adversaire le plus rapide, « coéquipier battu » sinon (course réellement perdue). Mesure seule, aucun réglage du filtre.
- 07/11/2026 : **Mesure (50 matchs, graine d'audit, avant / après le correctif 03e A1)** : zones du ballon, distance à sa ligne 5,16 (moins de 12 m), 4,70 (12 à 25 m), 7,29 (25 à 40 m), 11,96 m (40 m et plus) ; écart à la bissectrice au tir 0,30 m (98,2 % sous 2 m) ; sorties 35,0 par match dont 33,3 disputées (2,0 s ou moins) et 9,1 très disputées (1,0 s ou moins), avance moyenne 1,34 s, part gagnée (relance) 4,9 % ; courses gagnantes masquées 18,7 par match avec coéquipier plus rapide, **2,9 par match avec coéquipier battu** (13,5 %) ; face-à-face 13,2 tirs par match, arrêté 92,1 %, écart à la profondeur visée 1,32 m. **Le correctif 03e A1 n'a aucun effet en match** (séries identiques ; en face-à-face la ligne vaut 5 à 26 m sur 300 instants, l'écart commence pour une ligne plus haute que 28 m (porteur à 25 m), 31,8 m (22 m) ou 38,8 m (18 m), calcul de l'expert) : démontré par scène seulement.
- 07/11/2026 : **Limites et points à surveiller.** (1) La zone « moins de 12 m » (5,2 m) est plus avancée que « 12 à 25 m » (4,7 m) : elle mélange le gardien qui a le ballon, les corners et les sorties ; ce n'est pas un défaut de placement mais l'indicateur n'isole pas l'état « placement ». (2) La fenêtre de sortie disputée (2,0 s) couvre 95 % des sorties : peu sélective, d'où l'indicateur « très disputée » (1,0 s). (3) La part de sorties gagnées reste mesurée par la relance (4,9 %) : elle ne prouve ni le gain ni la perte de la course (réserve A1 du 03d, preuve en match du cas « passe en profondeur coupée » non établie) ; un indicateur d'issue du ballon est au ticket 03i. (4) Le filtre de portée laisse perdre environ 2,9 courses gagnables par match : mesure seule, décision au propriétaire. (5) Le 03c A2 reste vrai : 35,3 m découverts derrière une ligne à 35 m ou plus. (6) Réserves 03c A1 (hausse des tirs) et A3 (saut de cible) : renvoyées au ticket 03h.
- 07/11/2026 : **Clôture (/valider-ticket-simulafoot)** : expert `APPROVED_WITH_RESERVATIONS` (empreinte `0af59094…`), contrôle qualité `VALIDÉ` (un seul passage), décision de clôture `VALIDÉ` (journal). **Réserves A1 et A2** (courses masquées et sorties comptées en épisodes qui clignotent, donc majorants ; issue du ballon rattachée à un ticket nommé) : acceptées par délégation permanente du propriétaire (« je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026, non reprise mot à mot dans cette conversation, qui contient seulement « Oui clôture et commit »), **et leur condition est remplie** : formulations corrigées dans `docs/INDICATEURS_V2.md` section 11, ticket `03i` créé (issue du ballon par ballon, courses masquées recomptées par ballon). Facultatifs : A3 seuil du correctif 03e A1 corrigé (ligne plus haute que 28 m pour un porteur à 25 m, 31,8 m à 22 m, 38,8 m à 18 m) ; A4 l'écart à la bissectrice au tir ignore la ligne défensive (biais estimé à 0,9 m à 18 m avec une ligne à 30 m), non corrigé, à reprendre avec le 03h ; A5 `CLAUDE.md` indique encore 2 500 tests (2 517), à mettre à jour avec un autre fichier. QC, non bloquant : `data/joueurs.xlsx` modifié hors périmètre, exclu du commit.

