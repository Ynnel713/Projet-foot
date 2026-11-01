# 08: Pressing intelligent et coordonné

**What to build:** Le presseur ne court pas seulement vers le porteur : il **oriente sa course** pour fermer une ligne de passe et pousser vers une zone choisie. Le pressing se **déclenche collectivement** (passe en retrait, mauvais contrôle, joueur dos au jeu), et ses partenaires suivent pour ne pas laisser un adversaire libre derrière lui. Effort par à-coups : s'il échoue, il relâche, et un autre prend le relais.

**Attributs :** Work Rate, Aggression (engagement au contact), Anticipation, Teamwork.

**Blocked by:** 07, 25 (socle cinématique et contact).

**Status:** livré (01/11/2026), validé expert + QC (remis sur main ; réserves R1 à R3 acceptées par le propriétaire, renvoyées aux tickets 27 et 22, voir Comments)

**Point de vigilance :** le pressing par à-coups (5 s d'effort, puis 5 à 20 s pour souffler selon Work Rate) a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre ici.

- [~] (réserve, ticket 27) Test de pressing : le pressing coordonné ferme mesurablement plus de solutions qu'un pressing individuel, sans rendre les récupérations automatiques
- [~] (indicateur, ticket 22) Récupérations dans les 5 à 6 s après un pressing dans une fourchette réelle : 39 % dans le moteur, 23 % au réel (CMU 2025, MLS 2023, SkillCorner, 252 464 pressings sur 502 matchs). Définitions différentes : le moteur compte un défenseur à moins de 3 m du porteur, CMU une zone ovale de 3 à 9 m (Andrienko 2017)
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Base de référence après le ticket 25 (30/10/2026)

Depuis le ticket 25, le presseur rattrape vraiment le porteur en conduite, puisque la loi d'arrivée tient compte de la vitesse de la cible. Mesure de référence sur 20 matchs à 0,1 s : 87 tacles, 755 pertes de balle et 4,85 buts par match, et 9 % du temps en défense placée (contre 60 tacles, 581 pertes, 2,75 buts et 17 % avant). Deux défauts antérieurs, désormais visibles, sont à traiter ici. Tout adversaire à moins de 15 m du ballon devient presseur, ce qui forme un essaim. Un défenseur battu qui reste à moins de 3 m du porteur ne peut plus retenter de tacle (`CONFRONTATION_END_M`, revue expert du ticket 25, A4).

## Clôture (31/10/2026) : livré avec réserves, validées par le propriétaire

- Test unitaire du pressing coordonné vert, mais pas d'effet en match : solutions de passe faciles (≥ 80 %) 1,42 → 1,57, solutions ouvertes (≥ 0,5) 5,21 → 5,31. Suite au ticket 27.
- Récupération dans les 5 s après un pressing : 37 % avant, 39 % après. Tacles 68 → 53, pertes 545 → 578, buts 2,1 → 2,0 par match.
- Profils : Aggression 99 / 11, distance presseur-porteur 1,24 / 1,49 m. Work Rate presque sans effet (temps de pressing 1282 / 1261 s). Teamwork en sens inverse sur les solutions laissées (1,69 / 1,53).
- Rayon « marqué » testé à 3 m sans effet, puis annulé. La cause est la courbe de passe, plate autour d'un écart nul : marquage et pression ne font pas passer une passe courte sous 0,5. D'où le nouvel indicateur « solutions de passe faciles ».

## Comments

- 31/10/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC BLOQUÉ (validation du propriétaire non tracée, V1 non démontrée).
  - Clôture avec réserves validée par le propriétaire, ses mots : « Yes, close it ».
  - Réserves de l'expert acceptées, ses mots : « Accept A1–A5 ».
  - A1 : critère 1 non atteint en match, reporté au ticket 27.
  - A2 : le déclencheur « passe en retrait » n'a pas de seuil. Mesurer la fréquence des déclenchements au début du ticket 27.
  - A3 : la distance d'arrêt à Aggression 11 (1,6 m) dépasse le rayon de tacle (1,5 m). À surveiller au ticket 22.
  - A4 : l'effort peut dépasser 5 s si le presseur revient (facultatif).
  - A5 : Work Rate presque neutre en match, à voir au ticket 12 (facultatif).
  - Constantes validées avant le code (31/10/2026), mots du propriétaire : « Ok avec tes recommandations ». Seuil « solutions faciles » de 0,8 : « Ok avc ta recommandation ».
  - QC passage 2 : VALIDÉ.
  - V1 inchangée : aucun fichier V1 dans le diff (`git diff --stat 8043889`, voir le dossier de revue).

- 01/11/2026, remise sur main, passage 1 : expert REJECTED.
  - A1 [bloquant] : l'effort d'un presseur n'était jamais oublié au changement de porteur ; retrouvant plus tard ce porteur, il était mis au repos après un effort quasi nul. Corrigé : effort oublié quand le porteur change ; test `test_presser_back_on_the_holder_after_another_possession_starts_a_new_effort` (échoue sans la correction).
  - A2 [réserve] : la ligne de passe lue restait figée pour tout le match par paire presseur-porteur. Corrigé : relue à chaque détention ; test `test_presser_reads_the_lane_again_at_each_possession`.
  - A3 [réserve] : pressing d'équipe actif environ 60 % du temps sans ballon (réception en reculant). Ticket 27.
  - A4 [facultatif] : mémoires sans limite. Corrigé : contrôles ratés échus oubliés, effort et ligne purgés (A1, A2).
  - A5 [facultatif] : le test importe des fonctions privées de `match`. Non traité : déjà le cas des tests existants, la règle du ticket 19 vise les modules.
  - Recommandations acceptées d'avance par le propriétaire, ses mots : « Considère que j'accepte toutes les recommandations de l'expert ».
- 01/11/2026, remise sur main, passage 2 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ.
  - A1 et A2 du passage 1 corrigés et testés (vérifié par l'expert).
  - R1 [réserve] : critère 1 non atteint en match (solutions faciles 1,59 → 1,68). Ticket 27, avec l'indicateur à 0,8.
  - R2 [réserve] : pressing d'équipe actif environ 60 % du temps sans ballon, surtout par la réception en reculant. Ticket 27 (pistes : dos au but et seuil de vitesse vers 1,5 m/s, ou pas de relance pendant une fenêtre active).
  - R3 [réserve] : passes réussies 64,5 → 60,8 %. Ticket 22.
  - Facultatifs non traités : effort du relayeur remis à zéro ; détection des contrôles ratés sûre jusqu'à un pas de 0,25 s.
  - Réserves R1 à R3 acceptées par le propriétaire après lecture du rapport, ses mots : « Ok ».

## Remise sur main et recommandations de l'expert (01/11/2026)

**Pourquoi.** Le ticket avait été validé le 31/10/2026 dans la branche `claude/v2-08-pressing-d198df` (commit `a2f18d1`, base `8043889`), jamais fusionnée. Ses mesures datent d'avant le ticket 26 (une passe sur deux revenait au passeur) : elles sont faussées.

**Ce qui a été fait** (le propriétaire accepte toutes les recommandations de l'expert, 01/11/2026, ses mots : « Considère que j'accepte toutes les recommandations de l'expert ») :
- branche remise sur main (`e8114a0`) ; ticket de suite renuméroté 27 (le 26 est pris) ;
- **A2** : une passe ne déclenche le pressing d'équipe que si le receveur est au moins `BACKWARD_PASS_M` = 3 m plus près de son but que le passeur (haut de la fourchette de 2 à 3 m proposée par l'expert) ; les déclenchements sont comptés par le banc (`pressings d'équipe déclenchés par match`) ; test `test_only_a_real_back_pass_triggers_the_team_press` ;
- **A4** : un presseur relayé puis revenu sur le même porteur garde le début de son effort ; après son repos, il repart pour un effort neuf ; test `test_presser_back_on_the_same_holder_keeps_his_effort` ;
- **A1, A5** : ticket 27 (critères déjà écrits) ; **A3** : noté au ticket 22 ;
- test `test_coordinated_press_closes_more_options_than_an_individual_press` : seuil fixé à 0,5, celui de son écriture. Depuis le ticket 06, l'indicateur compte à 0,7 et les passes de la scène n'y arrivent presque jamais, pressing ou non (0,3 contre 0,1 solution) ; à 0,5 : 3,0 contre 1,4.

**Déclenchements (A2, 2 matchs, diagnostic).** Seuil 0 → 3 m : 765 → 654 par match. Avec 3 m : environ 200 passes en retrait, 340 réceptions en reculant (`BACKWARD_MPS`), 114 contrôles ratés. Le seuil ne retire qu'environ 15 % des déclenchements : la cause principale est la réception en reculant. Pressing d'équipe actif une grande partie du temps sans ballon : à traiter au ticket 27, qui commence par cette mesure.

**Mesures, 20 matchs, mêmes graines, pas de 0,1 s : avant (`e8114a0`) → après le passage 1 → après le passage 2 (corrections A1, A2, A4 de l'expert, voir Comments)**

| Indicateur | Avant | Passage 1 | Passage 2 | Réel |
|---|---|---|---|---|
| Buts par match | 2,1 | 1,65 | 2,65 | 2-3,5 |
| Tirs par équipe | 9,0 | 8,6 | 10,3 | 8-15 |
| Tacles par match | 55,8 | 45,1 | 48,6 | 30-40 |
| Pertes de balle par match | 555 | 595 | 613 | — |
| Passes par minute | 16,2 | 16,3 | 16,3 | 15-17 |
| Passes réussies | 64,5 % | 61,6 % | 60,8 % | 70-90 % |
| Hors-jeu par match | 0,85 | 1,2 | 0,5 | 3,2-3,5 |
| Pressings par match (défenseur à moins de 3 m) | 1 060 | 1 068 | 1 079 | environ 500 (CMU, autre définition) |
| Récupérés dans les 5 s | 35,9 % | 38,8 % | 39,5 % | 23 % (CMU) |
| Pressings d'équipe déclenchés par match | — | 692 | 685 | non trouvé |
| Solutions de passe ouvertes (≥ 0,7) | 2,06 | 2,18 | 2,16 | — |
| Solutions de passe faciles (≥ 0,8) | 1,59 | 1,71 | 1,68 | — |
| Couverture du presseur | 55,2 % | 54,3 % | 53,2 % | — |
| Temps de calcul par match | 276 s | 341 s | 220 s | — |

Temps de calcul mesuré sur machine chargée (plusieurs processus en parallèle) : comparaison relative seulement. Buts, tirs et hors-jeu : sur 20 matchs, l'écart-type des buts est d'environ 0,4 par match ; une petite correction change toute la suite du match à graine égale, l'écart du passage 2 n'est donc pas attribuable au seul ticket.

**Profils, 99 contre 11, 4 matchs par attribut (2 affiches jouées dans les deux sens) : passage 1 → passage 2**

| Attribut | Indicateur | 99 | 11 | Sens |
|---|---|---|---|---|
| Aggression | distance presseur-porteur | 1,32 → 1,31 m | 1,57 → 1,56 m | attendu |
| Anticipation | solutions faciles laissées au porteur | 1,39 → 1,43 | 1,43 → 1,43 | faible → nul en match |
| Work Rate | temps de pressing par match | 1 206 → 1 184 s | 1 089 → 1 150 s | attendu, +11 % → +3 % |
| Work Rate | solutions faciles laissées au porteur | 1,51 → 1,55 | 1,65 → 1,57 | attendu, faible |
| Teamwork | solutions faciles laissées au porteur | 1,58 → 1,63 | 1,47 → 1,59 | **inverse** (déjà au 31/10, ticket 27) |

Work Rate : l'écart du passage 1 était en partie dû au défaut A1 (repos déclenché après un effort quasi nul, plus long pour les Work Rate faibles). Anticipation et Work Rate restent bien visibles dans les scènes de test, faibles en match : ticket 27 (critère 1) et ticket 12.

Sources réelles : CMU 2025, *Forced Turnover* (https://www.stat.cmu.edu/cmsac/sure/2025/showcase/soccer_tracking/report.html) ; StatsBomb, 47 % des possessions pressées dans les 5 s (https://blogarchive.statsbomb.com/articles/soccer/how-statsbomb-data-helps-measure-counter-pressing/).

**Suite complète** (01/11/2026, après les corrections du passage 2) : 2 225 passés, 5 ignorés, 13 désélectionnés, 0 échec. V1 : aucun fichier V1 dans le diff.
