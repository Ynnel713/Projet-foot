# 15c1: Choix du geste de la tête

**Chantier :** `v2-realisme` (découpe du `15c`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié :** un ballon joué de la tête est un contrôle (`possession.attempt_control`) posé au pied, puis une décision au sol ; Heading n'est lu nulle part (24/11/2026).

**What to build:** au contact de la tête (joueur de champ, ballon en l'air à hauteur de tête), le joueur choisit en une touche entre remise ou passe de la tête, tir de la tête, dégagement et amorti (contrôle, comme aujourd'hui), par l'évaluation tactique existante (`decision.choose_action`, valeurs dans la monnaie commune, erreur de perception de Decisions, options vues de Vision). Exécution provisoire neutre (sans attribut), remplacée par les `15c2` à `15c4`. Cas limites : coéquipier hors-jeu (filtre existant), ballon dégagé ou passé jamais hors du terrain par construction, pas de tête de joueur à la main.

**Attributs :** Decisions, Vision (rôles existants du choix), aucun rôle nouveau.

**Blocked by:** `15b1` (livré). **Bloque :** `15c2`, `15c3`, `15c4`, `15d`.

**Constantes** (proposées et validées par le propriétaire le 24/11/2026, « Je valide ») ; aucune source trouvée, ordres de grandeur :
- `HEADER_PASS_RANGE_M` = 20 m : passe de la tête possible jusqu'à 20 m ;
- `HEADER_SHOT_RANGE_M` = 16 m : tir de la tête possible jusqu'à 16 m du but (la surface) ;
- dégagement proposé seulement dans sa moitié de terrain, ballon envoyé à `CLEARANCE_DISTANCE_M` = 30 m droit devant, loin de son but (provisoire : vers l'extérieur au `15d`) ; valeur : `CLEARANCE_KEEP_SHARE` = 40 % de chances que son équipe récupère le ballon à l'arrivée ;
- chaque tête d'un joueur de champ passe par ce choix, sans tirage « pense-t-il à jouer de première » (en l'air, on ne peut pas attendre) ;
- exécution provisoire : passe et tir de la tête avec des notes neutres (50) et la trajectoire actuelle d'une passe ou d'un tir, jusqu'aux `15c2` à `15c4`.

**Status:** livré (24/11/2026), validé expert + QC

## Estimation

**Total (travail effectif) : 2 h 15** (analyse 30, développement 50, tests 30, intégration et vérifications 25). Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [x] Constantes validées par le propriétaire avant le code
- [x] Effet mesuré en scène et en série de 50 matchs, indicateurs globaux dans le bruit
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

**Critères chiffrés** (posés avant le code, 24/11/2026) : options filtrées exactement (tir ≤ 16 m du but, remise de première ≤ 20 m, dégagement seulement dans sa moitié, valeur du dégagement = `option_value` avec 40 % de récupération au point visé) ; scènes de 40 contacts : tir de la tête seul à 9 m du but dans 30 cas au moins, dégagement d'un défenseur pressé sur ballon dur dans sa surface dans 20 cas au moins, remise vers un coéquipier libre au moins une fois ; aucun geste pour un gardien ni sous la tête ; série de 50 matchs : gestes comptés et rapportés (non réglés), buts, tirs, fautes, passes réussies dans le bruit ; déterminisme à graine fixée ; suite complète à 3 663 passés + nouveaux cas, 0 ignoré, 14 désélectionnés.

## Résultats (24/11/2026)

- Code : `v2engine/decision.py` : constantes (ci-dessus), `header_twin` (notes du geste neutres, joueur sans fiche : notes par défaut), `clearance_point`, `in_own_half`, `header_options` (filtres de portée, dégagement dans la monnaie commune, amorti pondéré par la chance de contrôle), `header_cushion` (pondération de l'amorti, réelle et perçue), `header_gesture` ; `choose_action(header=True, ball_velocity=...)` (conduites perçues pondérées aussi, réserve A1) ; pas de talonnade de la tête (réserve A3). `v2engine/possession.py` : `control_probability` (même loi qu'`attempt_control`, qui l'appelle), `launch_speed_mps`. `v2engine/match.py` : au contact de la tête d'un joueur de champ (ballon en l'air), `_header_choice` puis `_head` (exécution par `_execute` avec le double neutre ; dégagement en l'air vers son point, journal `dégagement`, hors-jeu signalé au départ ; origine du ballon reçu posée pour l'origine d'un tir de la tête, réserve A2) ; sinon contrôle comme avant. Trace : `HeaderRecord`, `MatchTrace.headers`, événement `DEGAGEMENT` (perte « dégagement » si l'adversaire le prend). Banc : têtes par match et part de chaque geste.
- Choix de modélisation, sans constante nouvelle : l'amorti vaut le jeu au pied pondéré par la chance de réussir le contrôle, contrôle raté = perte sur place (sans lui, l'amorti était jugé comme un ballon déjà contrôlé).
- Tests (`tests/test_v2engine_geste_tete.py`, 13 cas) : constantes ; double neutre (et joueur sans fiche) ; point de dégagement et moitié ; filtres, dégagement, amorti pondéré ; scènes tir, dégagement, remise ; pas de geste pour le gardien ni sous la tête ; déterminisme ; hors-jeu signalé au départ d'un dégagement ; choix au niveau de `choose_action` sans bruit : dégagement préféré quand la conduite non pondérée l'aurait battu (A1) ; pas de talonnade de la tête (A3) ; origine « centre » d'un tir de la tête (A2).
- Série (50 matchs appariés, avant : série « après » du `15b2`, même code moteur que `ecf6b95` ; refaite après les corrections A1 à A3), `docs/INDICATEURS_V2.md` § 81 : 15,7 têtes par match ; amorti 76,6 %, remise 19,3 %, dégagement 3,1 %, tir 1,0 % ; buts 5,26 → 4,86, tirs par équipe 15,14 → 15,30, fautes 21,06 → 21,50 : dans le bruit ; « premier contrôle après un centre : tête » − 24,1 points, par définition (une tête jouée n'est plus un contrôle) ; 148 indicateurs significatifs sur 2 860 (143 attendus par hasard). Première série (avant A1) : dégagement 2,1 %, amorti 78,1 %.
- Constat : l'amorti domine parce que la loi du contrôle donne environ 97 % de réussite même à hauteur de tête (sonde d'un match) ; difficulté de l'amorti aérien : périmètre du `15c2`.
- Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes de la trace complète (`6dca7ea56b75684b`, `df0a18cd196748f7` ; 10 et 22 têtes), avant et après les corrections A1 à A3 (aucun choix changé sur ces deux matchs).
- Suite complète : 3 676 passés, 0 ignoré, 14 désélectionnés (3 663 + 13 cas). Première passe : 1 échec (`test_v2engine_hauteur_ballon`, joueur sans fiche d'attributs dans `header_twin`), corrigé ; deuxième passe : 3 673 passés ; troisième après les corrections de l'expert.
- Durée réelle : environ 3 h (analyse 40, développement 60, tests 45, intégration et vérifications 35), + 33 % sur 2 h 15 : la correction des réserves A1 à A3 du premier passage de l'expert (30 min) et la reprise des mesures. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : deux matchs d'essai, une sonde d'un match, deux séries de 50 matchs (46 et 44 min), deux rejeux de 2 matchs (environ 12 min chacun), trois suites complètes (23, 22 et 21 min).

## Comments
- 24/11/2026, passage 1 : expert REJECTED (empreinte `5ad978e1…`) : A1 [BLOQUANT] conduite perçue après amorti non pondérée par la chance de contrôle au moment du choix (`choose_action`, `seen_as`) ; A2 [RÉSERVE] origine d'un tir de la tête ; A3 [RÉSERVE] talonnade de la tête ; A4 [FACULTATIF] le dégagement roule au-delà du point visé (à surveiller au 15d). QC non lancé. Corrigés A1 à A3 dans le même passage, tests ajoutés, série, rejeu et suite refaits.
- 24/11/2026, passage 2 : expert APPROVED (empreinte `4e3b63a2…`, corrections A1 à A3 vérifiées dans le code et par les tests) ; QC VALIDÉ. Clôture VALIDÉ.
- Facultatif (expert, ex-A4) : le ballon dégagé peut rouler au-delà du point visé ; à reprendre au `15d` avec un test de non-sortie après rebond.
- Remarque QC : le test importe `match._step_ball` (fonction privée), comme les autres tests de scène V2.
- À surveiller (expert, QC) : amorti dominant (77 %), dégagements (3 %) et têtes au but (0,16 par match) rares tant que l'amorti aérien n'est pas plus difficile (`15c2`, la pondération `header_cushion` fera basculer le choix sans autre retouche).

