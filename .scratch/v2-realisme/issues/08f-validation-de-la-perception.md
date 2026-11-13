# 08f: Validation de la perception

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle des erreurs de perception). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur de perception.

**What to build:** Indicateurs : part des adversaires proches non vus au moment d'une décision, pertes de balle sur adversaire non vu, scans par minute par poste. Rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 08d (Le porteur décide sur ce qu'il perçoit); 08e (Le défenseur ne voit pas toujours l'appel dans son dos); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** rien.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 1 h 20 |
| Tests unitaires et comportementaux | 55 min |
| Intégration et vérifications | 1 h 00 |
| **Total (travail effectif)** | **3 h 50**, réestimé le 13/11/2026 (1 h 30 au départ : indicateurs seuls ; reprises des réserves A1 du 08d et A1 du 08e ajoutées ; un seul ticket, décision du propriétaire) |

Confiance : moyenne. Hypothèses : lecture de la trace pour les pertes, les scans et les adversaires proches ; la hauteur de ligne se recalcule sur les vraies positions sans état partagé (elle ne lit que les formes de départ) ; aucune constante produit (seuils de mesure seulement).
Temps machine, non compté : suite complète (environ 10 min) ; deux séries de 50 matchs (avec et sans perception de la défense, 4 lots chacune) ; 8 matchs pour la courbe du meilleur choix.

## Tests

- **Unitaires (scène contrôlée) :** adversaire proche compté vu ou non ; perte au contact (tacle, conduite, rotation) sur un adversaire vu ou non, avec et sans scan, sans mémoire ; collecteur et rapport ; ligne perçue contre ligne sur vraies positions ; oscillation de la ligne ; marquage non vu ; le banc ne change pas le jeu (positions identiques avec et sans lui)
- **Statistiques (séries de matchs) :** 50 matchs : rapport publié ; 50 matchs sans perception de la défense (`--sans-perception-defense`), mêmes graines ; 8 matchs pour la courbe du meilleur choix (`scripts/measure_v2_meilleur_choix.py`)

## Acceptance criteria

- [x] Indicateurs définis et ajoutés : part des adversaires proches (5 m) non vus à la décision ; pertes de balle au contact sur adversaire non vu (tacle, conduite, rotation) ; scans par minute et par joueur, par poste (`scripts/measure_v2.py`, `tests/test_v2engine_perception_validation.py`)
- [x] Rapport publié (`docs/INDICATEURS_V2.md`, section 36) sur 50 matchs
- [x] Réserve A1 du 08d : écart du taux de meilleur choix à la courbe validée du ticket 33 relevé par tranche de Decisions ; sous environ 2 points par tranche, sinon la cause et la suite sont consignées (recalage : constante produit, proposée au propriétaire avant tout code) : **écart non tenu** (− 9,2 / − 8,9 / − 3,5 / − 4,6 / + 1,1 points), cause et suite consignées, recalage à proposer (section 36)
- [x] Réserve A1 du 08e : effet de la ligne et du marquage perçus mesuré (écart à la ligne sur vraies positions, marquage non vu, marqueur différent), variance de `bloc.lines` d'un tick à l'autre avec et sans perception (A4), niveau de hors-jeu relevé, et A/B de 50 matchs avec et sans perception de la défense
- [x] Le banc ne change pas le jeu : mêmes positions et même score avec et sans ses branchements (test)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : 1 h 40 contre 3 h 50, − 57 %, expliqué ci-dessous
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`08f-det1.json`, `08f-det2.json` : 877 indicateurs identiques ; série de 50 matchs identique à celle du 08e sur 852 indicateurs)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 883 passés, 0 ignoré, 14 désélectionnés = 2 861 + 22 ; `08f-suite.txt`)

## Comments

**13/11/2026, lancement.** « lance le ticket suivant dans un ordre logique » : 08f, seul ticket sans bloqueur (08d, 08e, 01d livrés ; 07g reste bloqué par 07b et 07d, à constantes à proposer). Estimation annoncée : 2 h 10 avec un découpage (reprise du 08e dans un 08g) ; le propriétaire a retenu **un seul ticket** (comme au 08e) : réestimé à 3 h 50, confiance moyenne.

**13/11/2026, code (mesure seulement, aucun effet sur le jeu).** `trace.DecisionRecord.near_opponents` (adversaires à 5 m au plus, vus ou non) ; `trace.TraceEvent.seen` (perte au contact : le porteur voyait-il l'adversaire qui l'a pris) ; `PerceptionMemory.is_seen` ; `match._seen_by` et `_execute(..., memory)` ; collecteur (`on_line`, `on_marking`, `on_marker_choice`, temps sur le terrain par poste) ; `measure_v2` : rapport, `_hook` (ligne recalculée à côté sur les vraies positions, marquage et choix du marqueur comptés) et interrupteur `--sans-perception-defense` (`run(..., defence_perception=False)`), seul changement de jeu du banc, hors série par défaut. Tests : `tests/test_v2engine_perception_validation.py` (14), `tests/test_v2engine_perceived_defence_measure.py` (8).

**13/11/2026, bogues trouvés en cours de route.** (1) `near.distance_to` au lieu de `near.position.distance_to` dans la trace des décisions (trouvé au premier match de test). (2) Le marquage et la ligne sont calculés avant la mise à jour de la mémoire du tick : « vu » y signifie vu au tick précédent ; avec le test à l'instant courant, 100 % des attaquants étaient « non vus » (corrigé, garde dans le test du rapport).

**13/11/2026, mesures** (section 36 de `docs/INDICATEURS_V2.md`). Adversaires proches non vus : 57,0 % (44,4 % au hasard). Pertes au contact sur adversaire non vu : 43,9 % : la perception n'a aucun effet sur le risque de perte (le code des duels ne la lit pas). Effet de la perception sur la ligne : 13 cm en moyenne, 2,2 % des ticks au-dessus d'un mètre ; oscillation + 2 à + 4 %. Marquage : 22 % des attaquants non vus, marqueur différent dans 2,7 % des choix. A/B de 50 matchs : hors-jeu 42 contre 39, passes en profondeur réussies 70/167 contre 91/184 (1,4 σ) : rien de démontrable. Hors-jeu 0,84 par match (0,78 sans perception) contre 3,2 à 3,5 en réel : écart antérieur, à traiter à la calibration. Courbe du meilleur choix : écart non tenu, recalage de `decision._ERROR_POINTS` à proposer au propriétaire (réduction d'environ 15 à 30 % de l'erreur propre entre Decisions 11 et 75, inchangée à 99, à mesurer par essais de 8 matchs).

**13/11/2026, passage 1 de la revue.** Expert : APPROVED_WITH_RESERVATIONS (rapport `08f-expert-1.md`) ; QC : VALIDÉ (trois réserves de documentation). Aucun défaut bloquant ; mesure passive prouvée (série de 50 matchs identique au 08e sur 852 indicateurs). Réserves et suites :
- **A1 (expert) : critère de la courbe du meilleur choix non tenu.** Accepté par le propriétaire (« Accepter A1, recalage à part », 13/11/2026). Suite : recalage de l'erreur propre de Decisions (`decision._ERROR_POINTS`, constante produit) à ouvrir en ticket séparé ; proposition chiffrée non codée : réduire d'environ 15 à 30 % entre Decisions 11 et 75, inchangé à 99, mesure par essais de 8 matchs ; tester aussi la corrélation avec les 57 % d'adversaires proches non vus.
- **A2 (expert) : lecture statistique des pertes au contact.** Corrigé : la section 36 dit que le pourcentage n'est pas comparable à la part des adversaires proches non vus et que la cause est le code des duels (qui ne lisent pas la mémoire).
- **A3 (expert) et R1 (QC) : scans par minute, total contre postes.** Corrigé : le total du 08c divise par 90 minutes nominales (18,0) ; indicateur ajouté sur le temps réellement sur le terrain (16,4, durée moyenne 98,9 min), même base que les postes.
- **R2 (QC) : effectifs des passes en profondeur.** Corrigé : reconstruits depuis les JSON en pleine précision par `08f-profondeur.py` (167 / 70 et 184 / 91, entiers exacts), sortie `08f-profondeur.txt` ; la moyenne des parts par lot (40,2 % et 48,0 %) est indiquée à côté.
- **A4 (facultatif) :** garde `0 <= now_s - before[0]` dans `Collector.on_line` ; le banc remet déjà l'état à zéro à chaque match (`_reset_match`), le cas ne se produisait pas dans les séries ; test ajouté.
- **A5 (facultatif) :** la section 36 précise que l'écart de ligne de 13 cm comprend le tick de retard d'extrapolation (la ligne précède la mise à jour de la mémoire).
Après correction : 22 tests ajoutés (14 + 8), suite relancée.

**13/11/2026, passage 2 de la revue.** Expert : APPROVED_WITH_RESERVATIONS (rapport `08f-expert-2.md`) : les corrections A2 à A5 et les effectifs des passes en profondeur sont vérifiés dans le code et par calcul indépendant ; il ne reste que A1, acceptée par le propriétaire (« Accepter A1, recalage à part », 13/11/2026) ; facultatif : ouvrir le ticket de recalage de `decision._ERROR_POINTS`. QC : VALIDÉ, quatre remarques non bloquantes : trois de texte corrigées dans la section 36 (phrase contradictoire sur les pertes, gardien dans les scans par poste, cause de l'écart à la courbe formulée comme hypothèse) ; une sur les tests (le test du banc ne vérifie pas la restauration de `_closest_to` ni de `DefensiveRoles.update`) : non faite, elle rouvrirait la revue d'un fichier revu, à reprendre à la prochaine modification du banc.

**Durée.** Estimée 3 h 50. Réelle 1 h 40, relevée à l'horloge de la session (14:19 → 15:55, attentes machine comprises ; pas chronométrée poste par poste : analyse 20 min, développement 35 min, tests 20 min, intégration et vérifications 25 min) : − 57 %. Cause : l'estimation reprenait la cadence du 08e (3 h 40 pour un changement de comportement avec itérations) ; ici le travail est de la mesure en lecture seule qui réutilise le banc, les lots et le collecteur existants, sans boucle de correction de comportement, et les séries (26 min chacune) et la rédaction se sont faites en parallèle. Un ticket de validation qui reprend des réserves de mesure se chiffre plutôt autour de 2 h. Temps machine hors total : deux séries de 50 matchs (4 lots, 26 min chacune), 8 matchs de courbe (12 min), deux exécutions de déterminisme (2 matchs), deux suites complètes (12 min chacune).

**À regarder.** Le porteur ne voit pas 57 % des adversaires proches, plus que le hasard : à comprendre avant de recaler Decisions (une part de l'écart à la courbe vient peut-être de là). La perte de balle ignore la perception : écart au réel, hors périmètre.

**Repris du 08d (réserve A1, acceptée le 13/11/2026).** Le taux de meilleur choix est passé sous la courbe validée du ticket 33 avec la décision sur le monde perçu (8 matchs : 49,8 % pour 67,5 %, 61,4 % pour 69,9 %, 66,4 % pour 70,1 %, 67,2 % pour 70,9 %, 74,6 % pour 73,9 %) ; le recalage de l'erreur propre de Decisions est prévu avec la calibration provisoire `v2-realisme/18d` : vérifier ici qu'il est fait (écart à la courbe sous environ 2 points par tranche, `scripts/measure_v2_meilleur_choix.py`).

**Repris du 08e (réserve A1, acceptée le 13/11/2026).** L'effet du marquage et de la ligne perçus n'est pas démontré sur 50 matchs (bruit : hors-jeu 0,80 puis 0,84 sur deux passages du même code, 0,86 avant ; passes en profondeur réussies 44,8 % → 40,2 % sur environ 150 passes) : le mesurer ici sur un échantillon plus grand ou ciblé (appels dans le dos, hors-jeu) ; relever aussi le niveau de hors-jeu (0,84 par match contre 3,2 à 3,5 en réel, écart antérieur au 08e) et la variance de `bloc.lines` d'un tick à l'autre (oscillation possible de la ligne, A4).
