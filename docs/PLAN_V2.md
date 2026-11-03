# Plan : Simulafoot V2 — moteur physique piloté par les attributs

> PRD source : `docs/PRD_PRODUIT.md` (US-27 à 29) · TRD source : `docs/TRD_V2.md` (D-V01 à D-V11). Premier jalon uniquement : un seul match isolé, jouable de bout en bout (score inclus) avant branchement aux compétitions existantes.

## Décisions architecturales

- Module V2 entièrement séparé du code V1 ; aucun fichier protégé modifié (D-V01).
- Réutilisation en lecture seule de `clubs.py`/`players.py`/`lineup.py` pour charger joueurs, clubs et compos (D-V02).
- Calcul physique continu, à plat (x/y), côté serveur Python ; trace complète du match calculée une fois puis rejouée par le rendu à vitesse réglable (D-V03/D-V04).
- Deux modes sur le même moteur : « regarder » et « tout simuler sans regarder » (D-V05).
- Déterminisme assoupli, pas de garantie bit-à-bit pour la V2 (D-V06).
- Table de pondération attribut × poste construite une fois en Phase 1, consommée par toutes les phases suivantes (D-V07).
- Découpage en un ticket par attribut, ordre essentiels d'abord : un match doit devenir jouable dès la fin de la Phase 4 ; les attributs dispensables viennent après (D-V11).
- Compétitions existantes : hors périmètre de ce plan (D-V09), chantier séparé, à planifier plus tard. Coachs : D-V10 levée le 02/11/2026, chantier `.scratch/v2-coach-et-gestion-de-match/`.

---

## Phase 1 — Déplacement (le strict nécessaire pour qu'un match existe)

**Statut** : Livrée (24/10/2026). Code : `v2engine/` (`geometry.py`, `attributes.py`, `trace.py`, `movement.py`, `formation.py`, `match.py`). Tests : `tests/test_v2engine_movement.py` (7, tous verts). Suite de tests V1 complète vérifiée après ce ticket : 1881 passés, 0 échec, aucun fichier protégé modifié.

**User stories** : US-27, US-28

**Attributs couverts** : Pace, Acceleration, Stamina pilotent directement la vitesse, la montée en régime et la fatigue de chaque joueur. Positioning/Off the Ball sont réservés par la position de formation (bandes) mais pas encore pilotés individuellement par leur note — vraie IA de décision différée à la Phase 5+ (D-V08). Agility (changements de direction) n'est pas encore un paramètre séparé du modèle de pilotage actuel — à ajouter si le rendu montre des virages trop artificiels, pas inclus dans ce lot. Plus la table de pondération attribut × poste (D-V07, `attributes.py`, mécanisme construit mais vide — aucun attribut de cette phase n'en a besoin, voir le commentaire du module) et le format de trace de match (D-V04, `trace.py`), construits ici une fois pour toutes les phases suivantes.

### Ce qu'on livre

Les 22 joueurs (données réelles via `clubs.py`/`players.py`/`lineup.py`) se déplacent sur un terrain 2D plat, avec collision simple entre eux et avec le ballon. L'IA de déplacement est un placeholder volontairement simpliste (chaque joueur rejoint sa position de formation, ou le ballon s'il en est proche) — pas de vraie prise de décision à ce stade (D-V08). Pace/Acceleration/Stamina pilotent la vitesse, l'explosivité et la baisse de régime de chaque joueur selon ses notes réelles. Aucun tir, aucune passe, aucun duel encore : ce ticket prouve que le moteur fait exister 22 joueurs et un ballon sur un terrain, pas qu'un match se joue.

### Critères d'acceptation

- [x] Les 22 joueurs d'un match (données réelles) sont positionnés et se déplacent sur le terrain 2D
- [x] Un joueur avec un Pace/Acceleration élevé se déplace visiblement plus vite qu'un joueur avec une note basse, à distance égale
- [x] La Stamina d'un joueur fait baisser sa vitesse de déplacement à mesure que le temps simulé avance
- [x] Aucune collision aberrante (joueurs superposés durablement, traversée du ballon sans interaction)
- [x] Le mode batch (sans rendu) tourne sur le même moteur que le mode « regarder », seul le rendu diffère (une seule fonction `simulate_match`, aucun rendu construit à ce stade)
- [x] Un joueur avec des données manquantes (`Pieds`/`Weak foot` absents) se comporte normalement, sans erreur
- [x] La V1 reste 100 % inchangée (suite de tests V1 intégralement verte, aucun fichier protégé modifié)

### Bloquée par

- Aucune — démarrable immédiatement.

---

## Phase 2 — Contact ballon et passes

**Statut** : Livrée (24/10/2026). Code : `v2engine/possession.py` (contrôle, choix du coéquipier, passe), `v2engine/ball_state.py` (possession), `v2engine/attributes.py` (`success_probability`, courbe non linéaire partagée, D-V07/guide §2). Tests : `tests/test_v2engine_possession.py` (6) + mise à jour de `tests/test_v2engine_movement.py` (1 test adapté à la nouvelle sémantique du ballon), tous verts.

**User stories** : US-27

**Attributs couverts** : First Touch, Passing, Technique

### Ce qu'on livre

Un joueur en possession du ballon peut le contrôler (qualité du contrôle pilotée par First Touch) et le passer à un coéquipier (précision/réussite pilotées par Passing, gamme de gestes par Technique). Le ballon suit une trajectoire physique simple entre les deux joueurs. Toujours pas de tir, de duel ni de gardien à ce stade. Introduit `success_probability` (`attributes.py`), le mécanisme partagé note → probabilité (courbe cubique, plate entre 45 et 55, amplifiée aux extrêmes, jamais 0 % ni 100 %) que toutes les actions probabilistes des phases suivantes réutiliseront.

### Critères d'acceptation

- [x] Un joueur peut recevoir, contrôler et transmettre le ballon à un coéquipier
- [x] Un First Touch bas produit visiblement plus de ballons mal contrôlés qu'un First Touch élevé, à situation égale
- [x] Un Passing bas produit visiblement plus de passes imprécises/ratées qu'un Passing élevé
- [x] Le mode batch reste cohérent avec le mode « regarder » (même fonction `_step_ball`, aucun rendu construit à ce stade)
- [x] La V1 reste 100 % inchangée

### Bloquée par

- Phase 1

---

## Phase 3 — Duels et tacles

**Statut** : Livrée (24/10/2026). Code : `v2engine/duel.py` (tentative de tacle, risque de faute, issue du duel), `v2engine/attributes.py` (`duel_probability`, même courbe que `success_probability` mais centrée sur un écart de notes). Tests : `tests/test_v2engine_duel.py` (7) + 1 test Phase 2 neutralisé explicitement vis-à-vis des tacles, tous verts.

**User stories** : US-27

**Attributs couverts** : Tackling, Strength, Balance, Aggression

### Ce qu'on livre

Quand un adversaire est à portée directe (1,5 m) du porteur du ballon, il peut tenter un tacle -- fréquence de la tentative pilotée par Aggression seule, issue du duel pilotée par Tackling (tacleur ; Aggression ne règle plus que la tentative et la faute depuis le ticket v2-collectif/18) contre la moyenne Strength/Balance du porteur. Un tacle raté a un risque de faute piloté par Aggression seule, indépendamment de Tackling (contrepartie attendue par le guide). Pas de lecture tactique de QUAND tacler (IA placeholder, D-V08) ni de conséquence de jeu pour une faute (pas de coup franc : Phase 5+). La table de pondération par poste (D-V07) reste vide : ces 4 attributs ne sont pas différenciés par poste dans ce modèle (un tacle est un tacle, quel que soit le poste de qui le tente) -- à revoir si un besoin concret apparaît.

### Critères d'acceptation

- [x] Un joueur proche du porteur adverse peut tenter un tacle, résolu par les attributs des deux joueurs
- [x] Un écart de Tackling/Strength/Balance favorise mesurablement le joueur le mieux noté, sans jamais garantir l'issue à 100 %
- [x] Une Aggression haute produit plus de fautes/tacles ratés qu'une Aggression basse, à Tackling égal
- [x] Le mode batch reste cohérent avec le mode « regarder » (même fonction `_step_ball`, aucun rendu construit à ce stade)
- [x] La V1 reste 100 % inchangée

### Bloquée par

- Phase 2

---

## Phase 4 — Tirs et gardien (match complet jouable, score inclus)

**Statut** : Livrée, moteur ET rendu (24/10/2026). Moteur : `v2engine/shooting.py` (`shot_probability`, modulée par distance/angle), score et buts horodatés dans `trace.MatchTrace` (`home_goals`/`away_goals`/`goals`). API : `api/routers/v2.py` (`POST /api/v2/matches`, trace sérialisée). UI : `ui/src/routes/V2Match.jsx` (choix des deux clubs, terrain SVG simple rejouant la trace à vitesse réglable x1/x2/x4, score révélé au fil des buts horodatés, jamais avant) + tuile « Version 2 (bêta) » sur l'accueil (`Home.jsx`). Vérifié dans le navigateur : match PSG-OM lancé, calculé (~26 s), lu avec score progressif et pause/vitesse fonctionnels. Tests moteur : `tests/test_v2engine_shooting.py` (6), tous verts.

**User stories** : US-27, US-29

**Attributs couverts** : Finishing, Composure (côté tireur) ; Reflexes, Handling, One on Ones (côté gardien, essentiels seulement — Communication/Kicking/Throwing/Aerial Reach/Command of Area/les tendances viennent en Phase 5+)

### Ce qu'on livre

Un porteur du ballon à moins de 20 m du but adverse tente sa chance plutôt que de chercher une passe (IA de décision placeholder, D-V08) ; l'issue (but ou non) est résolue par Finishing/Composure côté tireur et Reflexes/One on Ones/Handling côté gardien, modulée par la distance et l'angle de tir (facteurs géométriques calculés depuis les positions réelles, jamais 0 ni 1 — un tir à la limite de la zone ou sous un angle fermé reste possible, juste moins probable). Un but remet le ballon au centre ; un tir non converti donne le ballon au gardien adverse (repli simple, pas de sortie de but/corner modélisée). Le score (`home_goals`/`away_goals`) émerge entièrement du moteur, pour la première fois sans aucun résultat pré-décidé.

### Critères d'acceptation

- [x] Un tir est résolu par les attributs du tireur et du gardien, jamais par un tirage indépendant des données
- [x] Un Finishing/Composure élevé augmente mesurablement le taux de conversion, sans jamais garantir un but
- [x] Un gardien avec un Reflexes/One on Ones élevé arrête mesurablement plus de tirs qu'un gardien noté bas, à tir égal
- [x] Un match complet (coup d'envoi à coup de sifflet final) se joue de bout en bout et produit un score, sans score pré-décidé (`simulate_match` expose `home_goals`/`away_goals`)
- [x] Le match est regardable depuis la nouvelle tuile « Version 2 (bêta) » de l'accueil, sans connaître le score avant de lancer la lecture
- [x] Le mode « tout simuler sans regarder » produit aussi un score exploitable, sur le même moteur
- [x] La V1 reste 100 % inchangée

### Bloquée par

- Phase 3

---

## Phases 5 à 10 — Attributs restants (ordre validé par le propriétaire le 24/10/2026)

**User stories** : US-27 (approfondissement). Exigence : toutes les notes influencent réellement le comportement, façon Football Manager (référence : `Guide_attributs_joueurs.pdf`). La V1 est gelée, sans moteur graphique : tout l'effort porte sur la V2.

**Référence** : le rayon propre de chacun des 47 attributs (ce qu'il pilote, et que lui seul pilote) est fixé dans `docs/CARTE_ATTRIBUTS_V2.md` ; la revue des attributs déjà branchés, avec données réelles, dans `docs/REVUE_ATTRIBUTS_V2.md`. Tout ticket d'attribut s'y conforme.

**Principe d'ordre** : un attribut n'a d'effet que si l'action qu'il pilote existe dans le moteur. On construit l'action, puis on y branche les attributs.

| Phase | Ce qu'on ajoute au moteur | Attributs |
|---|---|---|
| 5. Cerveau des joueurs | Vraie décision du porteur et des non-porteurs (remplace l'IA placeholder D-V08) | Decisions, Vision, Off the Ball, Anticipation, Flair, Teamwork |
| 6. Défense organisée | Remplacée par le chantier « intelligence collective » (ci-dessous) | Positioning, Marking, Work Rate, Concentration, Teamwork, Flair — et le critère en match reporté du ticket cerveau 03 |
| 7. Gestes offensifs | Dribble, centre, tête, frappe de loin | Dribbling, Crossing, Heading, Jumping Reach, Long Shots, Bravery, Agility |
| 8. Ballon hors du terrain | Touches, corners, coups francs, penalties | Corners, Free Kick Taking, Long Throws, Penalty Taking |
| 9. Gardien complet | Sorties, centres, relances | Aerial Reach, Command of Area, Communication, Kicking, Throwing, Rushing Out, Punching, Eccentricity |
| 10. Caractère et profil | Moral selon le score, pied fort, habitudes | Determination, Leadership, Weak foot, Pieds, Preferred moves |

Natural Fitness agit entre les matchs : hors de ces phases, avec le branchement aux compétitions (D-V09).

**Phase 5 découpée** : `.scratch/v2-cerveau-joueurs/issues/` (01 à 04 livrés ; 05 et 06 absorbés par le chantier « intelligence collective » ci-dessous). Socle (`.scratch/v2-socle/issues/`) : 01, 03, 04 et 06 livrés ; 02 et 05 absorbés par ce même chantier.

### Chantier « intelligence collective » (décidé le 26/10/2026, remplace la phase 6)

**Pourquoi.** Les réglages génériques faits pour coller aux chiffres réels ont fini par produire des comportements incohérents : avec un seul presseur et un bloc qui coulisse, personne ne couvrait plus, et la mesure du 26/10 donnait 59 tirs par équipe et 17,8 buts par match. Décision du propriétaire : implémenter d'abord les **principes** du football (structure collective, compensations, transitions, puis circulation et comportements individuels), et ne recalibrer qu'ensuite.

**Principes de travail.**
- Les données réelles restent la boussole, mais ce sont des **indicateurs de calibration**, pas des objectifs à atteindre par un réglage générique. Une seule calibration, à la fin (ticket 22).
- Chaque joueur suit quatre temps : **perception, interprétation, décision, exécution**. Voir, choisir et réussir sont trois choses distinctes.
- Les attributs changent les **comportements** (options envisagées, espaces repérés), pas seulement la réussite des actions. Chaque effet n'est compté qu'une fois (règle anti double comptage).
- Pas de scripts : les situations et les combinaisons orientent les choix, sans les imposer. Les attributs donnent des **tendances**, jamais des seuils qui interdisent une action.
- La validation passe aussi par des **tests tactiques ciblés** (compensation, pressing, circulation, profils, fatigue, diversité, cohérence) et par la **relecture** des intentions enregistrées dans la trace.

**Tickets** : `.scratch/v2-collectif/issues/` (01 à 23, puis 25 à 27 ; le 24 est réservé à la passe dans l'espace proposée au ticket 23 ; 28 à 32 ajoutés le 03/11/2026, voir « Revue de réalisme » plus bas), dans cet ordre d'exécution :

| Étape | Tickets | Contenu |
|---|---|---|
| A. Fondations | 01, 02, 18, 03 | Banc de mesure et tests tactiques ; perception, décision, exécution et intentions tracées ; règle des interactions entre attributs ; reconnaissance de la situation de jeu |
| B. Structure collective | 04, 05, 23, 25, 06, 26 | Bloc de référence dynamique ; hauteur du bloc ; hors-jeu (ajouté le 27/10/2026) ; socle cinématique et contact du ballon (ajouté le 29/10/2026 après l'audit global : arrivée et freinage, contact sur le trajet du ballon, un seul pas de temps) ; soutien du porteur et lignes de passe ; le passeur ne reprend plus sa propre passe (ajouté le 31/10/2026, correctif du 25) |
| C. Défense organisée | 07, 08, 09 | Rôles défensifs (presser, couvrir, marquer, fermer l'axe) ; pressing coordonné ; compensations en cascade |
| D. Transitions | 10, 11 | Attaque-défense ; défense-attaque |
| E. Effort | 12 | Intensité selon le rôle et réserve d'énergie (reprise du socle 02 et de son code non commité) |
| F. Circulation | 13, 14, 33, 31, 32, 15 | Valeur future d'une passe ; combinaisons collectives ; meilleur choix factuel et perception du porteur ; première touche (passe à une touche, contrôle orienté) ; types de passes (lobée, en retrait, en profondeur) ; construction face au pressing |
| G. Attaque | 16, 29, 30, 28, 17 | Appels complémentaires ; ballon mort (touches, sorties de but, corners, engagement, mode de ballon) ; fautes, avantage et coups francs simples ; danger, occasion, issue du tir et arrêts variés ; surcharges et déséquilibres |
| H. Individus | 19, 20, 21 | Profils et tendances (Flair, Teamwork, Preferred Moves) ; conscience de ses limites ; adaptation au score, au temps et à la fatigue |
| I. Calibration | 22 | Calibration générale (reprise du socle 05), sur au moins 50 matchs |

**Avancement (31/10/2026)** : livrés 01 (`a20a6af`), 02 (`832b53c`), 18 en partie (`4205ab9`), 03 (`926f96d`), 04 (`c505f65`), 05 (`48c11cb`), 23 (`e64780b`, `b4a7264`), 25 (`4d71418`), 07 (`8043889`), 06 (`b8461d9`, validé expert avec réserves A1-A2 acceptées + QC) ; 26 (passeur qui reprenait sa passe, validé expert + QC) ; 11 (transition défense-attaque, validé expert avec réserve A1 acceptée + QC : sanction d'une contre-attaque en infériorité à remesurer aux tickets 10 et 22) ; 13 (valeur future d'une passe, validé expert avec réserve A1 acceptée + QC : agit à situation égale, sans effet mesurable en match ; critère repris au ticket 14) ; 10 (transition attaque-défense : contre-pressing, réaction retardée par Anticipation, repli à l'intensité de Work Rate ; validé expert avec réserves A1-A3 acceptées + QC : tirs de contre, hors-jeu et recul du bloc à remesurer au ticket 22 sur au moins 40 matchs) ; 14 (combinaisons collectives : plan de passe, une-deux et troisième homme selon Teamwork) et 16 (appels dans le dos selon Off the Ball, lus par le coureur sur Vision et Passing du porteur ; appel tenu ; attaquant à 2 m ou moins de la ligne à la passe 11 % → 17 %), validés expert avec réserves acceptées + QC en clôture groupée avec le 10 (03/11/2026) : C2 du 14, C3 et médiane de C4 du 16 renvoyés au ticket 22 ; 08 en cours sur sa branche. Le 26 change la base de mesure (passes, tirs, buts, hors-jeu : voir `INDICATEURS_V2.md`) ; toute mesure faite depuis `4d71418` est à refaire. Points reportés au ticket 22 par le 06 : buts (2,75 par match), regroupement hors porteur, effet d'Off the Ball sur les solutions de passe, appels des DC et latéraux.

**Hors chantier, dans les phases suivantes** : centres et jeu aérien du dernier tiers (phase 7) ; types de finition, dont lob et dribble du gardien (phase 7, `v2-attributs-restants/10`, après le ticket 22) ; coups de pied arrêtés, avec placement, blocs, marquage et seconds ballons (phase 8) ; relance du gardien (phase 9, en lien avec le ticket 15) ; Leadership individuel et moral (phase 10, en lien avec le ticket 21).

**Revue de réalisme (03/11/2026).** Le propriétaire constate que le ballon ne sort jamais du terrain, que les arrêts, les centres, les tirs et les buts se ressemblent. Après une revue point par point avec l'expert et l'audit du code, décisions :

- **Règle de diversité.** Toute variété (arrêts, centres, tirs, passes, duels, relances, célébrations) naît de la **situation** et des **notes** des joueurs, jamais d'un tirage dans une liste. Chaque geste ajouté est livré avec un **test de cohérence** (scènes fixes : le geste change avec la situation dans le bon sens) ; sans lui, le ticket est refusé. Chaque type de geste apparaît au moins une fois sur 50 matchs et aucun ne domine quand aucun chiffre réel n'existe.
- **Visible à l'écran.** Chaque type d'action ajouté se voit à l'animation, même simplement (trajectoire, étiquette, mode de ballon).
- **Mode de ballon.** D-V03 est conservée (pas de physique 3D) ; la trace porte un mode de ballon (au ras du sol, aérien, lobé), posé au ticket 29, pour l'affichage et deux règles d'interception.
- **Réalisme vérifié par des chiffres et par la relecture de matchs** (`docs/GRILLE_RELECTURE_V2.md`) : la relecture alimente le ticket suivant, elle ne conditionne pas la clôture, qui reste l'expert plus le contrôle qualité.
- **Tickets ajoutés** : `v2-collectif/29` (ballon mort), `30` (fautes, avantage, coups francs simples), `28` (danger, occasion, issue du tir, arrêts variés), `31` (première touche), `32` (types de passes) ; `v2-attributs-restants/10` (types de finition), `11` (centres variés) ; chantier `.scratch/v2-mise-en-scene/` (buts et lecteur, moments clés, résumé, célébrations). Le `07` (duels) devient le vrai duel un contre un avec tacle glissé ; le `09` reçoit les échauffourées ; `v2-coach-et-gestion-de-match/03` dépend du 29 et non plus du 02.
- **Laissés de côté** : vent et état de la pelouse (peu de variété pour du bruit dans la calibration).
- **Ordre.** Tout ce qui change le nombre ou la forme des actions passe avant la calibration (22), qui ne se fait qu'une fois sur le moteur complet : 16 (puis commit du 14) → 29 → 30 → **33** → 28 → 31 → 17 → 19, 20, 21 → `v2-attributs-restants/07` → 32 et 15 → `v2-attributs-restants/01` puis `11` → `v2-attributs-restants/02` puis `03` → **22** → `v2-attributs-restants/10`, `05`, `04`, `09`. Le chantier mise en scène suit son propre ordre (`01` en parallèle ; `02` après 28 ; `03` après 28 à 31 ; `04` après 29).

**Décision du porteur (03/11/2026, ticket `v2-collectif/33`)** : constat du propriétaire (un milieu au champ libre joue en retrait) puis séance de questions. Pour chaque prise de balle, le moteur calcule le **meilleur choix factuel** avec les vraies capacités du porteur (un bon frappeur à l'entrée de la surface tire, un mauvais cherche le décalage), dans une monnaie commune, le danger attendu (carte publiée de type « expected threat », coût de la perte inclus) ; le joueur choisit sur sa **perception**, déformée par Decisions (cible moyenne : la courbe validée), Composure sous pression et Anticipation. Erreurs plausibles, pas de tirage au hasard parmi les autres options. Livré avant 28, `v2-attributs-restants/07` et 32.

**Correctifs écran (03/11/2026, `.scratch/v2-correctifs-ecran/issues/01`)** : rejeu en direct (le match se calcule pendant qu'on le regarde, démarrage en quelques secondes), préchauffage des chargements au démarrage de l'API, moteur 1,6 fois plus rapide à comportement identique ; un tir gagnant va jusqu'à la ligne avant de compter ; nom du porteur sous son rond. Livré, validé expert (réserves A1-A2 acceptées) + QC.

**Correctifs écran (03/11/2026, `.scratch/v2-correctifs-ecran/issues/01`)** : rejeu en direct (le match se calcule pendant qu'on le regarde, démarrage en quelques secondes), préchauffage des chargements au démarrage de l'API, moteur 1,6 fois plus rapide à comportement identique ; un tir gagnant va jusqu'à la ligne avant de compter ; nom du porteur sous son rond. Livré, validé expert (réserves A1-A2 acceptées) + QC.

**Correctif préalable (24/10/2026)** : `movement.step` perdait les attributs des joueurs dès le 2ᵉ tick (retour à 60 par défaut) ; passes, contrôles, tacles et tirs des Phases 2 à 4 ignoraient donc les vraies notes en match. Corrigé, test de régression dans `tests/test_v2engine_movement.py`.

### Bloquée par

- Phase 4
