# 04a: Conduite : même risque de perte à l'évaluation et à la résolution

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le porteur décide sur un risque qui ne se produit jamais). **Catégorie :** exécution.

**Constat vérifié :** `decision.keep_ball_probability` (`decision.py:233`) donne la chance de garder le ballon en conduisant (Dribbling 55 : 83 % au contact) et sert seulement à évaluer l'option ; en match, la conduite ne perd le ballon que par un tacle, tenté au taux de base de 0,03 par seconde de contact (`duel.py:21`) contre Strength et Balance. Dribbling n'a aucun effet sur l'issue réelle. Mesure du 28b : 52 % des tirs viennent d'une conduite.

**What to build:** Une seule fonction de risque de perte en conduite, appelée par l'évaluation (`decision`) et par la résolution (`match`) : pendant une conduite au contact (pression), une perte est tirée à chaque intervalle de décision avec la probabilité qui a servi à évaluer l'option, rapportée à la durée de l'intervalle. Le tacle existant reste, mais son effet est retiré du risque de perte de conduite pour ne pas compter deux fois.

**Hors de ce ticket :** où part le ballon perdu (04b) ; gestes du duel (04g à 04j).

**Attributs :** Dribbling (garder le ballon en conduite serrée)

**Lien avec l'existant :** fondation commune du ticket `v2-attributs-restants/07a`, qui ajoutera les gestes sur cette fonction.

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 04b, 04c, 04d, 04g, 04i.

**Status:** livré (08/11/2026), validé expert + QC

**Point de vigilance :** Strength et Balance restent au tacle (`v2-attributs-restants/07a`, règle R1) : vérifier que la perte de conduite ne relit pas ces attributs.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne. Hypothèses : perte modélisée comme un événement par unité de temps au contact ; les volumes de tirs bougeront (à rapporter, pas à régler).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** conduite au contact pendant 2 s, 10 000 tirages : perte observée égale à la perte estimée à 1 point près
- **Comportementaux (profils comparés) :** Dribbling 99 contre 11 au contact : perte observée nettement plus faible
- **Statistiques (séries de matchs) :** 50 matchs : part des tirs après conduite, pertes en conduite par match

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Une seule fonction appelée par l'évaluation et la résolution (test de garde)
- [x] Écart perte estimée / observée sous 1 point en scène contrôlée
- [x] Dribbling agit sur l'issue réelle (scène A/B)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- **Constantes (08/11/2026).** `DRIBBLE_REFERENCE_S` = 1,5 s (durée d'une conduite évaluée : 10 m à environ 7 m/s) et retrait de `PRESSURE_KEEP_SHARE` de la conduite (il reste pour les passes) proposés puis acceptés d'office par la consigne du propriétaire du 08/11/2026 : « Considéré que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit si les conditions sont nécessaires ». Chiffre réel de la réussite des dribbles : non trouvé (aucune source chiffrée), ordre de grandeur d'environ 50 % chez les dribbleurs de volume, indication seulement.
- **Mesure (50 matchs, section 16 de `docs/INDICATEURS_V2.md`).** 87,6 pertes de conduite par match ; 0,64 % par intervalle sans adversaire proche, 4,30 % en conduite serrée ; perte observée = estimée à 1 point près en scène contrôlée (10 000 tirages). La conduite devient le choix de 74 % des décisions (45 % avant), passes 1 032 → 816, tirs par équipe 23,5 → 19,4, tacles 33 → 42, buts 3,12 → 2,78 (dans le bruit). Volumes rapportés, non réglés : examen aux tickets 04b et 04c, recalibrage du tacle à décider avec le propriétaire.
- **Clôture (08/11/2026).** Expert : `APPROVED_WITH_RESERVATIONS` (empreinte 4b4f2da6…). QC (`valider-etape`) : `VALIDÉ`. Suite complète sur l'état final : 2 544 passés, 14 désélectionnés (`04a-suite-finale.txt`). Réserves : A1 (volumes de conduite, tacle à 42 par match, tir à 1,52 % des décisions : à traiter aux tickets 04b et 04c, ne pas figer comme référence de réalisme ; 04c compare le risque évalué à durée égale, 1,5 s contre 0,5 s) ; A2 (deux tests adaptés ont perdu un peu de portée : bon finisseur à 99, choix de la passe imposé) ; A3 (phrase de la section 16 corrigée) ; A4 (la déviation du ballon perdu lit la vitesse de course du porteur et le flux PASSE : objet du 04b). Réserves acceptées d'office par la consigne du propriétaire du 08/11/2026 : « Considéré que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit si les conditions sont nécessaires ».
- **Durée.** Estimée 2 h 20, réelle environ 2 h 50 (+ 21 %), non chronométrée.
