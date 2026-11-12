# 18g: Passe : même risque à l'évaluation et en vol

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (cohérence entre décision et résolution, comme 04a pour la conduite). **Catégorie :** exécution.

**Origine :** diagnostic du ticket 18f (11/11/2026, 12 matchs, script de diagnostic décrit dans le ticket 18f).

**Constat vérifié :** pour les passes choisies, la chance évaluée par le porteur (`possession.pass_success_probability`) vaut 0,82 en moyenne, mais le receveur visé n'a le ballon que dans 72 % des cas (premier porteur de son équipe : 74 %). L'écart vient de ce que la résolution ajoute à l'évaluation : les adversaires qui lisent la passe et courent la couper en vol (`anticipation.pass_readers`) et le contrôle raté du receveur (`possession.attempt_control`). Le couloir de passe compte déjà dans la difficulté (`_LANE_DIFFICULTY`), puis l'adversaire qui s'y trouve peut aussi couper la passe en vol : l'adversaire du couloir pèse deux fois à la résolution, une seule fois à l'évaluation. Par tranche de gêne du receveur : 0,82 évaluée pour 0,73 atteinte sans gêne ; 0,77 pour 0,58 à 0,4.

**What to build:** Faire porter à l'évaluation et à la résolution le même risque de passe, comme le 04a l'a fait pour la conduite : soit la chance évaluée inclut la coupe en vol et le contrôle, soit le couloir ne compte plus que d'une seule façon (difficulté ou coupe physique). Mesurer, par tranche de chance évaluée, la part des passes reçues par le receveur visé (calibration comme au 04c).

**Hors de ce ticket :** réglage de la réussite des passes (calibration finale `v2-collectif/22a`) ; hauteur du ballon (`v2-hauteur-ballon/03`).

**Attributs :** Passing, First Touch, Anticipation (aucun rôle nouveau ; règle anti double comptage de `docs/CARTE_ATTRIBUTS_V2.md`)

**Blocked by:** 18f (Calibration provisoire 1 bis : choix du porteur et rythme de décision).

**Bloque :** `v2-collectif/22a`.

**Status:** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : même démarche que 04a et 04c ; aucune nouvelle constante si le couloir ne compte plus qu'une fois.
Temps machine, non compté : série de 50 matchs, suite complète (environ 40 min).

## Tests

- **Unitaires :** une passe à travers un couloir occupé a la même chance à l'évaluation et à la résolution (scène fixe, tirages répétés)
- **Statistiques (séries de matchs) :** 50 matchs, calibration par tranche de chance évaluée (évaluée contre reçue par le receveur visé)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (12/11/2026)
- [x] Écart entre chance évaluée et passe non perdue sous 5 points par tranche de chance évaluée (50 matchs ; 3 points et « reçue par le receveur visé » à l'origine, portés à 5 points et « non perdue » par le propriétaire le 12/11/2026) : tenu sur les tranches qui portent 99 % des passes (au plus 3,2 points de 0,5 à 1) ; hors critère [0,1 ; 0,2[ (+ 5,5 sur 125 passes, erreur type 2,8) et [0,3 ; 0,4[ (10 passes)
- [x] Aucun effet d'attribut inversé ni annulé (scènes A/B rejouées) : aucun inversé ni annulé ; effet de Passing très réduit (réserve, ticket 18h)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : estimée 2 h, réelle environ 7 h (+ 250 %), voir Comments
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`measure_v2 2` deux fois : aucune clé différente hors temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 758 passés, 14 désélectionnés (2 754 + 4 ajoutés ; `.scratch/v2-realisme/mesures/18g-suite.txt`)

## Comments

**12/11/2026, diagnostic (12 matchs, graine d'audit, 10 604 passes de jeu ; script hors dépôt qui enveloppe `pass_aim`, `pass_velocity`, `pass_readers` et `attempt_control`).** Évaluée 0,831, reçue par le receveur visé 0,705 (écart 12,6 points ; 0,965 contre 0,802 sur la tranche [0,9 ; 1]). Issues : reçue 70,5 % ; premier contact d'un adversaire non lecteur 15,8 %, lecteur 6,7 % ; contrôle raté du receveur 3,4 % ; morte, sortie ou sifflée 2,1 % ; autre coéquipier 1,4 %. Avec au moins un adversaire dans le couloir : évaluée 0,718, reçue 0,462 (0,962 contre 0,559 sur [0,9 ; 1]) ; sans : 0,894 contre 0,841. Contacts adverses non lecteurs sur passe précise : 50 % à 3 m ou moins du passeur, 47 % sur le trajet, 3 % près du receveur. Passes imprécises (17,5 %) : 46 % reçues quand même par le receveur visé. **Cause : mécanisme.** Le couloir est sous-compté (+ 12 de difficulté contre une coupe physique d'environ une passe sur deux), et une passe imprécise n'est pas perdue alors que l'évaluation la compte comme telle.

**12/11/2026, décisions du propriétaire.** Un seul ticket (« Tu peux tout faire en 1 ticket je suis ok ») : la chance évaluée prédit la coupe en vol avec les règles du jeu (accès à la trajectoire avant le ballon, lecture par Anticipation, contrôle), et la passe imprécise rattrapée ; suppression de `_LANE_DIFFICULTY`, `_LANE_WIDTH_M` et `_LANE_REACH_M` acceptée (même message). Estimation révisée : 3 h 45 (analyse 1 h, développement 1 h 15, tests 45 min, intégration 45 min), confiance moyenne.

**12/11/2026, essai de règles sans constante (6 matchs, 4 150 passes précises, test hors ligne).** Cinq règles déterministes tirées des règles existantes (contact sur la ligne au rayon `CONTROL_RADIUS_M`, critère actuel des lecteurs, temps d'arrivée de `defense.arrival_time_s` contre ballon freiné, course actuelle vers la ligne) : écarts de 10 à 50 points par tranche ; la meilleure est juste en moyenne (+ 2,5 points) mais ses passes « coupées à coup sûr » ne le sont que 64 fois sur 100 et 6,4 % des coupes restent imprévues. La coupe dépend de joueurs qui bougent selon leur rôle pendant le vol : une photo au départ ne la prédit pas. Mesurable en revanche : chance de coupe d'un adversaire selon sa distance à la trajectoire (près du passeur : 0,75 sous 0,5 m, 0,12 de 0,5 à 1 m ; sur le trajet : 0,37, 0,22, 0,20, 0,11, 0,10, 0,06 par demi-mètre…) ; passe imprécise reçue quand même : 0,45 environ, quelle que soit la longueur.

**12/11/2026, décision du propriétaire (« Je suis ok avec ta recommandation »).** Voie 1 : physique inchangée ; l'évaluation estime la coupe adversaire par adversaire avec une table mesurée sur le moteur (chance selon la distance à la trajectoire, près du passeur ou sur le trajet) et la récupération d'une passe imprécise ; indicateur de calibration comme au 04c. Critère d'écart porté à moins de 5 points par tranche (au lieu de 3). Valeurs de la table soumises au propriétaire après la mesure de 50 matchs, avant le code. Écartée : coupe tirée au départ façon 04a (la coupe n'émergerait plus du jeu).

**12/11/2026, constantes validées par le propriétaire (« Ok »).** Mesurées sur 26 matchs (23 187 passes), vérifiées sur 24 autres (21 121 passes) ; chiffres réels : non trouvés (la table décrit le moteur, voie 1). Zone près du passeur : avancée le long de la passe jusqu'à 3 m. Coupe par adversaire selon sa distance à la trajectoire : près du passeur 0,75 (moins de 0,5 m), 0,14 (0,5 à 1 m), 0,01 (1 à 6 m) ; sur le trajet 0,31 (0 à 1 m), 0,16, 0,07, 0,04, 0,02, 0,01 (par mètre jusqu'à 6 m), 0 au-delà. Coupe imprévue par passe 0,10. Passe imprécise rattrapée (hors coupe) 0,65. Chance évaluée = produit des (1 - coupe) x [précise x (1 - coupe imprévue) x contrôle du receveur + imprécise x 0,65] ; précise : Passing contre la difficulté sans terme de couloir ; contrôle : règle First Touch existante au ballon idéal. Test hors échantillon : pire écart 4,3 points par tranche (au moins 100 passes).

**12/11/2026, passe imprécise rattrapée selon la longueur (validé par le propriétaire : « Ok pour tout »).** La valeur unique 0,65 donnait un plancher à la chance évaluée : une passe de 40 m très imprécise valait encore environ 0,7 et le gardien jouait long sans pressing (68 % des tirages, test `test_long_restarts_more_often_under_high_press`). Mesure par longueur (50 matchs, 7 453 passes imprécises, hors coupe) : 0,77 sous 10 m (1 191), 0,64 de 10 à 35 m (6 236), 0,35 au-delà (26 ; le moteur ne joue presque jamais long : 303 passes de plus de 30 m sur 44 308). Table retenue : 0,77 / 0,64 / 0,35. Avec elle : jeu long 70,5 % sous pressing, 13,5 % sans. Même message : estimation révisée à 6 h (au-delà de 3 h 45 : 11 tests V2 à reprendre, dont 8 scènes de décision) ; ticket 18h créé (passe ratée trop bénigne).

**12/11/2026, estimation révisée à 7 h 15 (« ok continue »).** 8 scènes de décision recalées en gardant le principe testé (justification par scène ci-dessous) ; `OPEN_LANE_PROBABILITY` inchangé (défini comme la passe moyenne du moteur, 69,8 % ; nouvelle évaluation : moyenne 0,707 ; part des passes jouées au-dessus de 0,7 : 75 % avant, 73 % après).

**12/11/2026, définition « passe non perdue » (validé par le propriétaire : « ok pour tout, continue »).** La décision traite tout échec de passe comme une perte de balle (`decision.option_value`) ; « reçue par le receveur visé » y comptait aussi les passes touchées par un coéquipier, mortes, ou mal contrôlées sans pression (environ 11 % même pour une passe sûre), d'où des passes surpénalisées face à la conduite (risque de vraie perte depuis le 04a). Chance évaluée = chance qu'aucun adversaire ne touche le ballon le premier. Valeurs (50 matchs, un match sur deux pour l'ajustement, l'autre pour le test) : coupe imprévue d'une passe précise 0,05 (au lieu de 0,10) ; passe imprécise non perdue 0,83 sous 10 m, 0,77 de 10 à 35 m, 0,62 au-delà (au lieu de 0,77 / 0,64 / 0,35 rattrapée) ; contrôle du receveur retiré de l'évaluation ; table de coupe inchangée. Test : pire écart 5,1 points (tranches d'au moins 100 passes), moyenne + 0,1. Critère d'écart mesuré sur « non perdue » ; « reçue par le receveur visé » publiée pour information. Effet : 7 des 8 scènes de décision repassent sans modification.

**12/11/2026, mesures après (section 30 de `docs/INDICATEURS_V2.md`, fichiers `.scratch/v2-realisme/mesures/18g-*`).**
- Calibration (50 matchs, 46 525 passes de jeu, indicateur ajouté au banc) : évaluée 0,854, non perdue 0,869 ; par tranche, au plus 3,2 points de 0,5 à 1 (98 % des passes).
- Effets (18f livré, `18f-det1`, mêmes graines) : passes réussies 74,9 → 81,9 % ; chez l'adversaire 23,1 → 14,9 % ; passes par possession 2,81 → 4,35 ; buts 2,96 → 2,50 ; pertes en conduite 83,5 → 46,3 ; possession d'équipe 17,2 → 25,6 s (repère 11 à 16, dépassé) ; passes par match 945 → 985 (repère 890 à 940, dépassé davantage : réserve du 18f) ; fautes 14,7 → 12,2.
- Scènes A/B (400 scènes du 18f, avant reproduit à l'identique) : aucun effet inversé ni annulé ; Passing + 0,514 → + 0,086 (meilleure passe) et + 0,620 → + 0,143 (part de passes choisies), Composure + 0,072 → + 0,012 ; cause : passe ratée trop bénigne dans le moteur (ticket 18h).
- Déterminisme : deux exécutions de `measure_v2 2` identiques hors temps de calcul (`18g-det1`, `18g-det2`).
- Tests : 3 tests de règle réécrits (`test_v2engine_difficulte.py`), 4 ajoutés (2 au moteur, 2 à l'indicateur) ; 5 scènes recalées en gardant leur principe, justification dans chaque test : marqueur à 0,8 m au lieu de 0,3 m (physiquement impossible, sur la ligne de toute passe) ; indicateur de pressing au seuil de l'indicateur 0,7 au lieu de 0,5 (le pressing coordonné y ferme les lignes : 1,7 contre 0 solution) ; appui latéral au lieu d'un coéquipier libre devant (scène de fatigue, A ne conduisait plus) ; espace coupé par un adversaire au lieu de « trop loin » ; avant-centre marqué sur la sortie de but (jeu long 72 % sous pressing, 16,5 % sans).

**Durée.** Estimée 2 h (ticket), révisée et annoncée trois fois : 3 h 45, 6 h, 7 h 15. Réelle environ 7 h, non chronométrée (analyse 2 h 30, développement 1 h, tests 2 h, intégration 1 h 30) : + 250 % sur l'estimation d'origine, − 3 % sur la dernière révision. Causes : hypothèse du ticket fausse (le couloir était sous-compté, pas compté deux fois) ; la coupe ne se prédit pas avec les règles existantes (cinq règles essayées), d'où une table mesurée sur 50 matchs ; plancher de la passe imprécise découvert aux tests (table par longueur) ; définition de la mesure revue (reçue par le visé → non perdue) après l'échec de 8 scènes de décision ; 5 scènes recalées. Temps machine hors total : diagnostics de 1, 12, 6, 6 et 50 matchs, série de 50 matchs après, scènes A/B, déterminisme, suite complète (11 min).

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : VALIDÉ. Clôture : VALIDÉ. Réserves acceptées par le propriétaire (« Ok », en réponse à la liste A1 à A3 et aux deux tranches exclues) :
- A1 [réserve] : possession d'équipe 25,6 s et passes par match 985, au-dessus des repères ; une-deux divisés par deux. Condition : traiter 18h avant `v2-collectif/22a`, puis remesurer.
- A2 [réserve] : effet de Passing très réduit (scènes A/B + 0,620 → + 0,143). Condition : 18h rend un coût réaliste à la passe ratée ; remesurer `_MISS_NOT_LOST` et `UNFORESEEN_CUT`, rejouer les scènes A/B.
- A3 [réserve] : « non perdue » plus étroit que « possession gardée » (sortie, sifflée, contrôle raté : environ 5 %) ; publier ces parts à part dans l'indicateur au 18h ou au 22a.
- Tranches [0,1 ; 0,2[ (+ 5,5 sur 125 passes) et [0,3 ; 0,4[ (10 passes) exclues du critère des 5 points.
- A4 [facultatif] : le banc accroche la fonction privée `match._play_restart` (détecter la remise par le journal du ballon). A5 [facultatif] : table à remesurer quand le mouvement défensif, `pass_readers` ou la vitesse des passes changent.
