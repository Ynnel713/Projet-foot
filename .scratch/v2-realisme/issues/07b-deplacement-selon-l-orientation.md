# 07b: Se déplacer de face, de côté ou à reculons

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un défenseur qui recule est plus lent qu'un attaquant qui court face au jeu). **Catégorie :** physique.

**Constat vérifié :** `movement.step` donne la même vitesse maximale quelle que soit la direction par rapport au corps (aucun corps, voir 07a).

**What to build:** La vitesse maximale dépend de l'angle entre la direction de course et le cap : pleine vitesse vers l'avant, réduite en pas chassés, plus réduite à reculons (parts validées). Le joueur choisit de se retourner ou de reculer selon la distance à parcourir.

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 07g.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : choix « se retourner ou reculer » : règle simple par distance.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur face au jeu qui doit reculer de 3 m : recule ; de 20 m : se retourne et court
- **Statistiques (séries de matchs) :** 20 matchs : km par poste avant / après

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : vitesse max 100 % jusqu'à 45° du cap, 80 % à 90° (pas chassés, chiffre réel non trouvé), 65 % à 180° (à reculons ; réel : 29 % plus lent que vers l'avant sur les 20 premiers mètres, 21 footballeurs universitaires, J Sports Sci 2021 ; vitesse de pointe non trouvée) ; se retourner à 8 m ou plus de la cible avec le ballon à plus de 45° de la course, revenir face au ballon sous 6 m ; bande de ± 0,3 m/s autour de 19,8 km/h (réserve A1 du 07a) ; validées par le propriétaire le 13/11/2026 (« ok »)
- [x] Vitesses par direction documentées : `movement._DIRECTION_SPEED_POINTS`, `direction_speed_factor` ; tests `tests/test_v2engine_direction_speed.py`
- [x] Choix tracé : `PlayerState.facing_run` (corps tourné vers sa course), cap déjà tracé et affiché (07a)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07b-det1`, `07b-det2`, identiques hors temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**12/11/2026, reprise du 07a (réserve facultative A1 de l'expert).** Le cap vise le sens de course au-dessus de `movement.FACING_RUN_SPEED_MPS` (19,8 km/h) et le ballon en dessous, sans hystérésis : quand ce ticket fera lire le cap au jeu, prévoir une bande de quelques dixièmes de m/s ou une pondération continue entre les deux directions (test : vitesse oscillant de ± 0,1 m/s autour du seuil, variation de cap bornée).

**13/11/2026, lancement et constantes.** Estimation annoncée : 2 h 20 (1 h 55 d'origine, plus la bande A1 et la conduite rattachée au 07b depuis le 07e), confiance moyenne. Constat à l'analyse : avec un plafond à reculons à 65 %, un joueur ne dépasse plus 19,8 km/h en reculant, donc la règle du 07a (corps vers la course au-dessus de ce seuil) ne le ferait jamais se retourner ; d'où le choix par la distance. Constantes proposées (tableau ci-dessus) et validées par le propriétaire. Ordre « de côté plus vite qu'à reculons » : choix de modèle, non sourcé (une course croisée de côté peut être rapide).

**13/11/2026, implémentation.** `movement.direction_speed_factor` (part de la vitesse max selon l'angle entre le cap du début du pas et la vitesse voulue, appliquée au plafond de `step`) ; `movement.faces_run` (course rapide avec bande ± 0,3 m/s, ou cible à 8 m ou plus avec le ballon hors du cône de 45° de la course ; sous 6 m il revient au ballon, selon le choix du pas précédent) ; `PlayerState.facing_run` ; `desired_facing(..., facing_run=)` ; direction de course = vitesse, ou la cible quand il est presque arrêté (sous 0,5 m/s). Conduite : même loi, rien de spécifique (le porteur regarde sa course ; un crochet coûte de la vitesse tant que le corps n'a pas tourné) ; lien avec le 12b noté dans ce ticket (double comptage à éviter). Tests : 9 ajoutés (`tests/test_v2engine_direction_speed.py` : parts par angle, recul de 3 m face au ballon, demi-tour et course pour 20 m, se retourner arrive plus tôt que reculer sur 20 m, ballon dans la course, hystérésis de distance, vitesse oscillant de ± 0,1 m/s autour de 19,8 km/h sans bascule, pas chassés à 80 %) ; `test_facing_does_not_change_the_movement` (07a) adapté : il affirmait que le cap n'a aucun effet sur le déplacement, faux par construction ici ; il vérifie maintenant l'égalité tant que le cap reste à 45° au plus de la course.

**13/11/2026, mesures (50 matchs, mêmes graines que le 08f, `07b-50-synthese.txt`).** km par joueur de champ 12,67 → 12,18 (− 3,9 % ; de − 2,6 % pour BU à − 4,9 % pour LB) ; distance au-dessus de 19,8 km/h quasi inchangée (part 0,095 → 0,096 ; par joueur − 6 % à + 2,5 % selon le poste) ; passes 1 062 → 1 046 ; tirs par équipe 17,4 → 17,7 ; buts 3,20 → 2,92 (sous un écart-type de la différence) ; xG neutre 3,27 → 3,21 ; **tirs en face-à-face 13,9 → 16,2 par match (+ 17 %, environ 3 écarts-types en Poisson)** : le défenseur qui recule face au jeu est plus lent, l'attaquant passe plus souvent ; sens attendu, mais le niveau était déjà sans repère réel (03e) : à surveiller à la calibration (18d, 18e) et au 07g ; vision : adversaires proches non vus 0,570 → 0,575. Temps de calcul 120 → 112 s par match (lots en parallèle, bruit de machine). Déterminisme : `measure_v2 2` identique sur deux exécutions hors temps de calcul.

**13/11/2026, suite.** Premier passage : 1 échec, `test_v2engine_agilite.py::test_agility_changes_the_facing_only_not_the_run` (07f), qui affirmait qu'Agility ne change que le cap, pas la course ; faux par construction depuis ce ticket. Adapté, pas retiré : `test_higher_agility_turns_sooner_and_so_runs_faster_from_a_turned_back` (parti dos à la cible, le plus agile va plus loin, son cap reste plus proche du ballon). `docs/CARTE_ATTRIBUTS_V2.md` (Agility) mis à jour : effet indirect sur le déplacement par la rotation, sans nouvelle lecture d'Agility. Suite complète : 2 898 passés, 0 ignoré, 14 désélectionnés (2 883 + 15 : 7 cas paramétrés et 8 tests ; `.scratch/v2-realisme/mesures/07b-suite.txt`) ; `CLAUDE.md` mis à jour. V1 inchangée (aucun fichier V1 touché).

**13/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. A1 (réserve) : la bascule « se retourner » ignore la vitesse de la cible ; le défenseur au marquage d'un appel dans son dos recule à 65 % jusqu'à 8 m d'écart, cause plausible des + 17 % de face-à-face. A2 (facultatif) : pas de bande sur le cône de 45° du ballon (cap qui peut trembler). A3 (facultatif) : `docs/` hors liste des fichiers, suivi documentaire admis par le verrou, rien à faire. QC non lancé avant la décision du propriétaire. Décision du propriétaire (« Ok avc les recommandations ») : corriger A1 et ajouter la bande A2. Nouvelle estimation annoncée : 3 h 05.

**13/11/2026, corrections A1 et A2.** A1 : `faces_run(..., target_velocity, backpedal_speed)` : il se retourne aussi quand sa cible s'éloigne dans le sens de sa course plus vite que sa vitesse à reculons (65 % de sa vitesse max du pas), sans constante nouvelle. Scène de l'expert (attaquant à 2 m qui part à 8 m/s dans le dos du défenseur) : pivot en 0,5 s au lieu de 1,6 s, écart à 2 s de 7,3 m au lieu de 10,0 m. A2 : `BALL_CONE_BAND_DEG` = 5° (validée par le propriétaire) : retourné, il ne revient face au ballon que sous 40°. Tests : 3 ajoutés (pivot sur l'appel dans le dos, cible lente gardée face au ballon, hystérésis du cône).

**13/11/2026, mesures après corrections (50 matchs, graines du 08f, `07b-50b-synthese.txt`).** km par joueur de champ 12,67 → 12,23 (− 3,5 %) ; distance au-dessus de 19,8 km/h inchangée (0,095 → 0,096) ; passes 1 062 → 1 054 ; tirs par équipe 17,4 → 17,3 ; buts 3,20 → 3,12 ; xG neutre 3,27 → 3,21 ; **face-à-face 13,9 → 15,7 par match** (16,2 avant la correction A1) : la correction en explique une partie, pas tout ; écart restant + 1,8 (environ 2,4 écarts-types en Poisson), cause non établie (pistes : pas chassés à 80 % des défenseurs qui coulissent, cibles de ligne et de couverture sans vitesse de cible). Indicateur sans repère réel (03e) : à reprendre au 07g et à la calibration (18d, 18e). Temps de calcul 120 → 111 s par match (bruit de machine). Déterminisme : `07b-det1` et `07b-det2` identiques hors temps de calcul.

**13/11/2026, suite après corrections.** 2 901 passés, 0 ignoré, 14 désélectionnés (2 883 + 18 : 7 cas paramétrés et 11 tests ; `.scratch/v2-realisme/mesures/07b-suite.txt`) ; `CLAUDE.md` mis à jour.

**13/11/2026, passage 2.** Expert : APPROVED_WITH_RESERVATIONS (corrections A1 et A2 du passage 1 jugées justes et testées). A1 (réserve) : hausse résiduelle des face-à-face (13,9 → 15,7 par match, + 13 %, cause non établie) ; acceptée par le propriétaire (« Ok avc la recommandation », 13/11/2026), reprise au 07g avec une mesure qui isole les deux pistes (pas chassés à 90 %, vitesse des cibles de ligne et de couverture) avant toute calibration des face-à-face. A2 (facultatif) : pas de bande sur le critère « la cible fuit » (cap qui pourrait trembler si l'attaquant court autour de la vitesse à reculons du défenseur) : non faite, sur recommandation (vitesse perçue lissée par la mémoire de perception), à vérifier à l'écran. QC : VALIDÉ (remarque : ligne du registre des estimations, ajoutée). Clôture : VALIDÉ.

**À vérifier à l'écran (propriétaire).** Un défenseur qui marque un appel en profondeur pivote tôt, sans reculer longuement dos au but ; le cap d'un marqueur qui suit un attaquant au trot ne tremble pas ; la ligne qui recule lentement reste face au jeu.

**Durée.** Estimée 1 h 55, revue à 2 h 20 au lancement puis à 3 h 05 avec les corrections A1 et A2. Réelle environ 1 h 55, non chronométrée (analyse 25 min, développement 35 min, tests 20 min, intégration et vérifications 35 min), relevée à l'horloge de la session (15:58 → 17:50) moins les attentes machine et les réponses du propriétaire : − 18 % sur 2 h 20, − 38 % sur 3 h 05. Cause de l'écart avec l'estimation revue : les 45 min prévues pour les corrections en ont pris environ 15 (correction A1 sans constante nouvelle, tests sur la scène de l'expert) ; le temps passé était surtout en attente machine, hors total. Temps machine hors total : deux séries de 50 matchs (25 min chacune), déterminisme 2 x 2 matchs (deux fois), trois suites complètes (10 min chacune).
