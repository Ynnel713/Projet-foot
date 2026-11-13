# 08d: Le porteur décide sur ce qu'il perçoit

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un adversaire non vu doit pouvoir surprendre). **Catégorie :** décision.

**Constat vérifié :** `decision.evaluate_options` utilise les positions réelles des adversaires ; voir 08a.

**What to build:** L'évaluation des options (passes, conduites, tir) utilise les positions perçues (08b) ; la valeur RÉELLE, pour le journal du meilleur choix (ticket 33), reste calculée sur les positions réelles. Un adversaire non vu peut donc couper une passe jugée sûre.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/33` (livré, non modifié) : même deux étages, perception enrichie.

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes).

**Bloque :** 08f.

**Status:** livré (13/11/2026), validé expert + QC

**Point de vigilance :** l'erreur de Decisions (ticket 33) a été réglée pour la perception actuelle : remesurer le taux de meilleur choix et signaler l'écart, sans régler ici.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05**, réestimé à **2 h 40** le 13/11/2026 (évaluation à deux étages dans `evaluate_options`) |

Confiance : moyenne. Hypothèses : coût de calcul limité aux options envisagées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur dans le dos du porteur, non vu, sur la ligne de passe : passe choisie puis interceptée ; vu : passe évitée
- **Statistiques (séries de matchs) :** 50 matchs : interceptions et taux de meilleur choix avant / après

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (aucune constante nouvelle ; choix de conception validés par « Ok » le 13/11/2026)
- [x] Décision sur le monde perçu, valeur réelle conservée au journal (`Action.seen_value` pour tirs et passes, conduites perçues dans `choose_action` ; `value`, `best` et `gap` restent sur les vraies positions ; exécution inchangée)
- [x] Taux de meilleur choix remesuré et rapporté (8 matchs, avant puis après, `08d-choix-avant.txt` et `08d-choix-apres.txt` : baisse de 4 à 7 points selon la tranche de Decisions ; voir Comments ; aucun réglage)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`08d-det1`, `08d-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 852 passés, 0 ignoré, 14 désélectionnés = 2 843 + 9 ; `08d-suite.txt`)

## Comments

**13/11/2026, lancement.** « lance le 08d ». Estimation annoncée : 2 h 40, confiance moyenne.

**13/11/2026, choix de conception (validés par « Ok »).** Adversaires de champ perçus par la mémoire du 08b ; gardien et coéquipiers réels (le gardien est devant le tireur, les coéquipiers déjà filtrés par la portée de Vision) ; gêne du porteur réelle (au contact, il la sent) ; pas de plafond de confiance sur une position figée, mesuré à la place ; aucune constante produit nouvelle. **Réserve A1 du 08c** (coût du scan : un joueur qui scanne ne suit pas le ballon pendant 0,3 s) **reportée au 08e** (le porteur n'a pas de suivi du ballon à interrompre ; le coût a un sens pour le défenseur qui regarde ailleurs) : déplacement accepté avec le « Ok » du propriétaire, noté dans le 08e. **Réserve A2 du 08c** (fréquence des scans à recaler) : reste à traiter au 08e, sur l'effet observé dans le jeu.

**13/11/2026, code.** `decision.evaluate_options` : paramètre `seen_opponents` ; un seul passage calcule la valeur réelle et la valeur perçue (`Action.seen_value`) des tirs et des passes, sans tirage de plus (un test le vérifie sur les flux) ; `decision.choose_action` : les conduites perçues se calculent sur les adversaires perçus avec la part d'Anticipation du ticket 33 (même courbe), le tirage de la perception ne change pas de nombre de tirages, la valeur perdue (`gap`) reste la valeur réelle ; `PerceptionMemory.perceived_opponents` (vus : exacts ; non vus : position extrapolée et dernière vitesse vue ; gardien gardé réel) ; `match._step_ball` fournit ce monde perçu au porteur (sans mémoire : il perçoit les vraies positions, les appels existants ne changent pas). Trace : `DecisionRecord.memory_stale` (adversaires perçus avec plus de 4 s de retard et 10 m d'erreur, seuils de mesure seulement, pas de plafond). Banc : fantômes par décision et part des décisions avec un fantôme. Test du 08c corrigé : « mêmes décisions avec et sans scans » n'est plus vrai (la mémoire nourrit la décision) ; il affirme maintenant que sans scan la mémoire du porteur vieillit davantage.

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/08d-*`, 50 matchs, mêmes graines que le 07e ; avant = lots `07e-50`, le jeu n'a pas changé depuis, les ticket 08a à 08c étant sans effet : empreinte d'un match identique).**
- Déterminisme : `08d-det1` et `08d-det2` identiques hors temps de calcul.
- Passes : réussies 84,9 % → 79,9 % ; chez l'adversaire 12,9 % → 18,2 % ; receveur visé 83,2 % → 77,9 % ; par match 977 → 1 044 ; par possession 4,36 → 3,75 ; possession d'équipe 25,9 s → 20,8 s ; pertes de balle 219 → 274 par match.
- Choix : conduite 62,8 % → 56,5 %, passe 35,9 % → 42,1 % (une passe dans le dos paraît sûre : le défenseur qui arrive de derrière n'est pas vu) ; pertes en conduite 70,1 → 60,3 par match ; talonnades 2,66 → 4,74 par match, non perdues 94,6 % → 75,5 % (même cause : la ligne arrière est dans l'angle mort).
- Résultat : buts 3,46 → 3,04 par match ; tirs cadrés 29,8 % → 27,8 % ; conversion 10,1 % → 8,8 % ; xG neutre 2,97 → 3,16 par match.
- Calibration de la passe (après) : écarts de la chance évaluée contre la réussite réelle de 6,5 points au plus ; la tranche [0,1 ; 0,2[ passe de 219 à 2 355 passes sur 50 matchs (passes jugées plus sûres qu'elles ne sont ; réussies à 14,8 % pour 15,2 % évalué).
- Mémoire du porteur à la décision : 4,19 adversaires non vus en moyenne, âge moyen de leur dernière vue 1,43 s, erreur moyenne 2,5 m, maximale 43 m ; **fantômes** (plus de 4 s de retard et 10 m d'erreur) : 0,125 par décision, présents dans 6,4 % des décisions.
- Taux de meilleur choix (8 matchs, avant → après, courbe validée du ticket 33) : Decisions 0-40 : 56,2 % → 49,8 % (67,5 %) ; 40-55 : 65,9 % → 61,4 % (69,9 %) ; 55-65 : 72,8 % → 66,4 % (70,1 %) ; 65-75 : 73,5 % → 67,2 % (70,9 %) ; 75-100 : 79,2 % → 74,6 % (73,9 %). L'erreur de Decisions du ticket 33 a été réglée pour la perception de l'époque : l'écart est signalé, sans réglage ici (consigne du ticket).
- Temps de calcul : 79,8 s → 92,0 s par match (séries sous charge, non comparables) ; coût propre faible (deux évaluations pour les seuls tirs et passes, environ 2 décisions par seconde).
- Tests : 9 ajoutés (`tests/test_v2engine_perceived_decision.py`). Suite : 2 852 passés, 0 ignoré, 14 désélectionnés ; `CLAUDE.md` mis à jour.

**À regarder.** Le jeu a changé : passes moins réussies (79,9 %, repère Ligue 1 d'environ 80 à 83 %), possessions plus courtes, plus de pertes. Le taux de meilleur choix passe sous la courbe validée dans quatre tranches sur cinq : recalage à envisager avec la calibration provisoire (`v2-realisme/18d`). Les talonnades non perdues à 75,5 % sont à surveiller (angle mort du porteur). Aucun plafond sur les fantômes (6,4 % des décisions) : mesuré, pas réglé.

**Durée.** Estimée 2 h 40. Réelle environ 2 h 30, non chronométrée (analyse 30 min, développement 55 min, tests 30 min, intégration et vérifications 35 min) : − 6 %. Temps machine hors total : suite complète, série de 50 matchs (4 lots, 25 min), meilleur choix avant et après (8 matchs chacun), déterminisme (2 x 2 matchs), un premier lot de 50 matchs interrompu pour ajouter l'indicateur de fantômes.

**13/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS (rapport `08d-expert-1.md`), aucune anomalie bloquante. QC : VALIDÉ (tests non exécutés par lui, preuves du ticket). Réserves, acceptées par le propriétaire (« j'accepte les réserves ») :
- **A1** : le taux de meilleur choix passe sous la courbe validée du ticket 33 dans quatre tranches de Decisions sur cinq (49,8 % pour 67,5 %, 61,4 % pour 69,9 %, 66,4 % pour 70,1 %, 67,2 % pour 70,9 % ; 74,6 % pour 73,9 % dans la dernière) ; recalage de l'erreur propre de Decisions (`decision._ERROR_POINTS`) avec la calibration provisoire `v2-realisme/18d`, avant que la courbe ne serve de base à un autre ticket ; critère de non-régression : écart à la courbe sous environ 2 points par tranche au banc `scripts/measure_v2_meilleur_choix.py`. Le 08f en hérite.
- **A2** : biais d'angle mort (talonnades 2,66 → 4,74 par match, non perdues 94,6 % → 75,5 % ; passes à moins de 30 % de réussite réelle environ 0,7 % → 5,9 % ; fantômes dans 6,4 % des décisions) ; au 08e, mesurer la fréquence des scans et vérifier si ces passes baissent, sinon envisager un plafond de confiance sur la mémoire très vieille.
Facultatifs : A3, le commentaire de `match.py` (autour de `PerceptionMemory`, ligne 1058) disant « sans effet sur le jeu » est périmé, à corriger au prochain ticket qui touche ce fichier ; A4, aucun test ne joue la scène « défenseur non vu, passe interceptée » de bout en bout (couverte par les tests unitaires et la série de 50 matchs). Observation du QC : les seuils 4 s et 10 m des fantômes sont des constantes numériques nouvelles, annoncées dans la proposition et validées par « Ok » ; seuils de mesure, sans effet sur le jeu. Clôture : VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserves acceptées, QC VALIDÉ).
