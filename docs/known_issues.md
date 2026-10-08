# Dette connue — Simulafoot

Tickets ouverts, documentés pour être traités plus tard. **Aucun des tickets ouverts (3, 4, 6, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 et 26) n'est corrigé à ce jour** (le ticket 2 est fermé le 08/10/2026). Créé le 07/10/2026 (clôture de l'Étape B, `LineupSnapshot`) ; tickets 4 et 5 ajoutés le même jour (intégration PWA par iframe) ; ticket 5 fermé et tickets 6 à 8 ouverts le même jour (gouvernance, avant Phase 5) ; tickets 9 (`duckdb`) et 10 (couverture NLG) ajoutés le même jour (environnement de test). tickets 7 (résolu en `7309172`) et 11 (`ConnectionResetError`) traités le même jour. **État : ouverts 2, 3, 4, 6, 9, 10, 11, 12, 13, 15 ; fermés 1 (résolu en `61773ab`, Phase 5 sous-étape 1), 14 (décision produit, bandes de tonte horizontales conservées), 5 (non reproduit), 7 (résolu en `7309172`) et 8 (résolu en `2d71e55`, vérifié sur archive propre).**

| # | Titre | Priorité (avant…) | Statut |
|---|---|---|---|
| 1 | Joueur statique poussé hors de la marge près d'un bord du terrain | Phase 5 (habillage visuel) | **Résolu** — commit `61773ab`, tolérance recalibrée à 0,5 % |
| 2 | Un joueur expulsé peut être remplacé plus tard dans le même match | Phase 4 (branchement PWA effectif) | **Fermé — Résolu** (commit « fix(events): cohérence entre cartons et remplacements (ticket 2) ») |
| 3 | `SubstitutionEvent` identifie les joueurs par nom, pas par `player_id` | Phase 6 (produit / carrière) | Ouvert |
| 4 | Latence et poids du payload d'animation | Phase 6 (produit / carrière) | Partiellement résolu (transfert, poids, cache HTTP et `interpolate` optimisés), voir `docs/ticket4_latency_audit.md` §8 et §9 |
| 5 | `build_clips` écarte les événements dont le protagoniste n'est pas dans le onze de départ | — | **Fermé** (non reproduit) |
| 6 | `build_clips` : `continue` silencieux quand `frames` est vide (et docstring obsolète) | Phase 7 (qualité) | Ouvert (priorité basse) |
| 7 | `PitchView.jsx` : la version commitée diverge de celle de l'arbre de travail | Phase 5 (habillage visuel) | **Fermé — Résolu** (`7309172`) |
| 8 | `pytest` seul échoue sur un checkout propre de `HEAD` (`ModuleNotFoundError: api`) | Immédiate (avant tout partage / push) | **Fermé — Résolu** (`2d71e55`) |
| 9 | `pytest` nu échoue à la collecte à cause de `duckdb` absent du venv principal | Phase 7 (qualité / packaging) | Ouvert |
| 10 | Le seuil de couverture à 85 % sur `engine/` échoue depuis le venv NLG | Phase 7 (qualité / packaging) | Ouvert |
| 11 | `ConnectionResetError` Windows 10054 dans le journal de l'API | Phase 7 (qualité / packaging) — priorité basse | Ouvert |
| 12 | Sauts de trajectoire en amont liés aux changements de segment de gabarit | Phase 7 (qualité / packaging) — priorité basse | Ouvert |
| 13 | Axe de la barre de progression fixe à 0–90 min, marqueurs qui se chevauchent pour les clips rapprochés | Phase 7 (qualité / packaging) — priorité basse | Ouvert |
| 14 | Orientation des bandes de tonte : horizontal (implémenté) vs perpendiculaire (backlog 24/09) | — (priorité basse) | **Résolu — décision produit**, horizontal conservé |
| 15 | `PitchField.jsx` : bandes de tonte perpendiculaires à la longueur, incohérentes avec `canvas.html` | Phase 6 (produit / carrière) — priorité basse | Ouvert |
| 16 | Point d'entrée seed manquant : `random.seed` ne suffit pas, il faut aussi `np.random.seed` | Avant la Phase 7 (priorité basse) | Ouvert — cause diagnostiquée, non corrigée |
| 17 | Pas de remplacement d'urgence modélisé (gardien expulsé sans remplaçant) | Avant la Phase 7 (priorité basse) | Ouvert |
| 18 | Poteau / barre toujours attribués à l'attaquant | Avant la Phase 7 (priorité basse) | Ouvert |
| 19 | Imports privés entre modules : `ball_events.py` importe `_simulate_rebound` et `_deterministic_unit` depuis `ball.py` | Avant la Phase 7 (priorité basse) | Ouvert |
| 20 | Clips poteau prolongés jusqu'à la touche, coupés à 1,0 s | Avant la Phase 7 (priorité basse) | Ouvert |
| 21 | Spin binaire (0 ou 50 rad/s) dans `templates.py`, pas de valeurs intermédiaires | B5 (priorité moyenne) | Ouvert |
| 22 | Courbure non perceptible à l'échelle 6 px | Avant la Phase 7 (priorité basse) | Ouvert |
| 23 | NLG ne reçoit pas le type de frappe, texte générique incohérent avec le rendu | Après B5 (priorité moyenne) | Ouvert |
| 24 | Commentaire faux sur la zone d'un penalty dans `engine/narrative.py` | Priorité basse | Ouvert |
| 25 | Clips de but dont la dernière image est avant la ligne | Avant la Phase 7 (priorité basse) | Ouvert |
| 26 | Divergence moteur / narration sur les penaltys ratés : l'animation montre des ratés qui n'ont pas eu lieu et omet ceux du moteur | Basse à moyenne (à trancher), à coupler au Bloc C | Ouvert |

---

## 1. Joueur statique poussé hors de la marge près d'un bord du terrain

**Description.** Dans les clips animés, un joueur immobile (`vx = vy = 0`, souvent hors porteur de balle) peut se retrouver légèrement au-delà de la marge de tolérance (0,1 en coordonnées normalisées) près d'un bord du terrain.

**Reproduction.** Test d'intégration `tests/test_narrative_player.py::TestNoOmissionAfterSubstitutesFix::test_substitute_placed_correctly` (marqueur `integration`, donc hors suite par défaut). Constaté le 07/10/2026 :
- échec dans le run complet des 12 tests d'intégration (`x = 1.1048`) ;
- échec **3 fois sur 3 en isolation** : `x = 1.1002`, `x = 1.1059`, `x = 1.1048`, ou `y = −0.105` (tolérance 0,1, soit des bornes −0,1 / 1,1) ;
- identique avec la création du `LineupSnapshot` désactivée (2 fois sur 2) : le problème préexiste à l'Étape B.

`_simulate_n(100)` n'a pas de graine aléatoire : les valeurs changent à chaque exécution, l'échec lui est systématique.

**Cause (corrigée le 07/10/2026).** L'hypothèse initiale (`animation.motion._apply_avoidance`) était **inexacte** : mesure sur 60 matchs (5,67 M de positions), aucune position brute ni sortie de `_apply_avoidance` n'est hors de [0, 1]. Les dépassements (jusqu'à ~0,58 normalisé, ~60 m ; 115 cas sur 16 349 joueurs × clips) venaient de `animation.physics.apply_acceleration_constraint`, qui suit la position brute sans rappel ni freinage anticipé : à un saut de la trajectoire brute (3 à 8 m en une image), la vitesse monte, dépasse la cible et le joueur dérive hors du terrain.

**Impact produit.** Un joueur est légèrement hors du terrain près d'un bord, perceptible visuellement dans l'animation.

**Priorité.** Avant la Phase 5 (habillage visuel).

**Statut.** **Résolu — commit `61773ab`, tolérance recalibrée à 0,5 % de la longueur du terrain (0,525 m, contre 0,1 soit ~10 m).** Correctif à la source dans `physics.apply_acceleration_constraint` : paramètre `bounds` (bornes du terrain, passées par `narrative_player`) et freinage anticipé par axe près des bords, plafond d'accélération conservé. Les sauts de trajectoire brute en amont (changements de segment des gabarits) ne sont pas traités.

---

## 2. Un joueur expulsé peut être remplacé plus tard dans le même match

**Description.** Le moteur tire les remplacements et les cartons indépendamment (`events._play_match_squad` vs `_build_stats`). Un joueur déjà expulsé (carton `direct` ou `second_yellow`) peut donc figurer comme `player_off` d'un `SubstitutionEvent` postérieur, et son remplaçant entre en jeu.

**Reproduction.** Graine 11 (`random.seed(11)` et `np.random.seed(11)`, deux clubs synthétiques de `tests/test_lineup_snapshot.py`) : `Away FC_DC1` reçoit un second jaune à la 17e minute, puis est remplacé par `Away FC_RB0` à la 64e. Figé par `test_engine_substitutes_an_already_sent_off_player_and_the_helper_does_not_hide_it`.

**Cause probable.** Absence de lien entre les tirages de cartons et de remplacements : le choix du sortant ne tient pas compte des expulsions.

**Impact produit.** Rupture de réalisme visible si l'animation affiche l'expulsé remplacé : l'équipe reste à 10, puis un entrant arrive alors qu'aucun joueur n'est sorti. `lineup_snapshot.players_on_pitch` suit les événements persistés à la lettre (l'entrant joue dès sa minute) et ne masque pas l'anomalie.

**Priorité.** Avant le branchement PWA effectif (Phase 4).

**Statut.** **Fermé — Résolu** (commit « fix(events): cohérence entre cartons et remplacements (ticket 2) », 08/10/2026). Correction de la cohérence entre cartons et remplacements dans `events._play_match_squad` : tous les cartons sont désormais tirés **avant** les remplacements et les buts ; la minute d'expulsion borne la fenêtre de présence du joueur (`_SquadEntry.minute_expelled`), un expulsé est exclu des sortants (blessure forcée et tactique), et aucun but, passe, blessure ou penalty manqué ne peut suivre son expulsion. Un titulaire blessé puis expulsé voit sa minute de blessure ramenée à son expulsion.

**Mesure** (graines 1 à N, `random.seed` et `np.random.seed`, Ligue 1 réelle) : sur 100 matchs, **0 incohérence** contre 12 expulsés remplacés et 2 événements postérieurs à une expulsion ; sur 3 000 matchs, **0 contre 375** expulsés remplacés (360 matchs, 12 %) et **0 contre 141** événements postérieurs à une expulsion (121 matchs). Distribution sportive préservée : **buts identiques graine par graine** (le score est tiré avant les événements), jaunes 4,740 → 4,818 (z = +1,52), rouges 0,485 → 0,472 (z = −0,74), remplacements 7,986 → 8,032 (z = +1,55), tous dans le bruit (|z| < 2). Le flux de `random` est décalé (les tirages sont réordonnés, pas modifiés en nombre) : tous les résultats seedés du moteur changent, à loi identique.

**Trois tests existants adaptés** (décision d'architecte, option A) : `tests/test_lineup_snapshot.py` (l'ancien test figeait le défaut, réécrit en `test_engine_never_substitutes_a_sent_off_player`), `tests/test_events_zone.py` (snapshot `tests/fixtures/event_regression_snapshot.json` régénéré, format vérifié octet pour octet avec l'ancien code), `tests/test_narrative.py` (borne de `test_penalty_missed_ratio_calibrated` élargie de [0,74 ; 0,78] à [0,70 ; 0,85]). Détail au §8.19 de `docs/repo_state.md`.

**Limites connues.** Un gardien expulsé n'est pas remplacé (le moteur ne modélise pas de remplaçant d'urgence) ; `engine/narrative.py` tire encore ses occasions parmi tout l'effectif ayant joué, sans tenir compte des minutes de présence, donc une occasion non marquée peut encore être attribuée à un joueur après son expulsion (limite pré-existante, hors périmètre) ; la branche « sortant déjà absent » de `lineup_snapshot.players_on_pitch` ne sert plus que pour des documents antérieurs à cette correction.

---

## 3. `SubstitutionEvent` identifie les joueurs par nom, pas par `player_id`

**Description.** `SubstitutionEvent.player_off` / `player_on` (et `CardEvent.player`, `PlayerMatchStat.player_name`) sont des noms. Le `Player` correspondant se retrouve par nom dans `LineupSnapshot` ; le nom est la clé d'effectif de tout le moteur.

**Reproduction.** Non applicable en l'état : le risque apparaît si deux joueurs d'un même effectif partagent le même nom complet.

**Cause probable.** Choix historique du moteur (le nom précède l'usage de `Player.id`, qui est `None` pour une partie des joueurs ; voir le repli `templates.player_id_of`).

**Impact produit.** Risque de confusion (mauvais joueur sorti ou entré, buteur mal attribué) à mesure que les effectifs grossissent ou que des homonymes apparaissent.

**Priorité.** Avant la Phase 6 (produit / carrière).

**Statut.** Ouvert.

---

## 4. Latence et poids du payload d'animation

**Description.** `GET /api/competitions/{id}/animation` (`api/animation.py`) calcule à la demande tous les clips d'un match (`match_result_from` → `build_timeline` → `build_clips` → `clips_to_json`) et renvoie un JSON non compressé, sans cache. Mesures du 07/10/2026 :
- **13,6 s et 9,5 Mo** pour un match de **22 clips** (appel direct, une seule requête) ;
- **7,3 s** pour un match de **10 clips** (build servi par l'API, même origine) ;
- 15 clips, `npm run dev` : **19,8 s** entre le clic et le premier frame du lecteur (dont 19,3 s d'appel API) ; en développement React `StrictMode` double l'appel, les deux calculs se concurrencent côté serveur.

**Reproduction.** Simuler une journée de Ligue 1, ouvrir la fiche d'un match à fort volume d'occasions (15 clips ou plus), cliquer sur « Voir l'animation » ; chronométrer jusqu'à l'apparition du lecteur. Équivalent en ligne de commande : `curl` sur l'endpoint `/animation` du même match (durée et `size_download`).

**Cause probable.** Génération des frames (`_build_clip_frames`, contrainte d'accélération, enrichissement des 22 joueurs) refaite à chaque ouverture, pour tous les clips du match, et sérialisée en JSON verbeux (une position par joueur et par frame). Non profilé précisément.

**Impact produit.** Attente de plusieurs secondes à plus de dix secondes à chaque ouverture (un indicateur de chargement avec compteur est affiché depuis le 07/10/2026, il masque l'attente sans la réduire) ; transfert réseau de plusieurs Mo par clic, pénalisant hors réseau local (accès par tunnel, téléphone) ; mémoire côté navigateur (le payload entier est conservé puis copié vers l'iframe par `postMessage`) et côté serveur (aucune mise en cache, recalcul identique à chaque clic).

**Pistes identifiées (non implémentées).**
- cache mémoire par match (clé : identité du match + libellé ; le résultat est déterministe, vérifié par `test_animation_uses_only_the_persisted_lineup_even_if_squads_change`) ;
- compression gzip de la réponse API (`GZipMiddleware`) : le JSON de frames est très redondant ;
- plafond de `max_occasions` dans `build_clips` (au prix de temps forts en moins) ;
- à plus long terme : génération progressive (premiers clips d'abord) ou JSON plus compact.

**Priorité.** Avant la Phase 6 (produit / carrière).

**Statut.** **Partiellement résolu** — transfert, poids et cache HTTP optimisés (gzip, arrondi à 4 décimales, cache LRU) ; `interpolate` optimisé via mémoïsation et sortie anticipée (premier appel à froid divisé par environ 2 : 16-18 s → 9-11 s sur la machine de mesure, résultat bit-à-bit identique). Reste à évaluer : plafond `max_occasions`, optimisation d'`_apply_avoidance` (levier 3 : vectorisation), vitesse analytique (levier 4, Phase 6). **15 images/s et remplaçants non animés ont été refusés par le propriétaire.** Détail et mesures : `docs/ticket4_latency_audit.md` §8 et §9.

---

## 5. `build_clips` écarte les événements dont le protagoniste n'est pas dans le onze de départ (fermé)

**Description.** `engine/narrative_player.build_clips` ignore (`if not frames: continue`) tout événement pour lequel `_build_clip_frames` ne produit aucune frame, sans trace ni compteur ; l'événement disparaît des clips alors qu'il reste dans `Timeline.events` (et le score progressif est calculé sur tous les événements). La docstring de `build_clips` (datée du 23/09/2026) attribue ce cas aux protagonistes absents du onze de départ (« ~36 % des occasions » mesurées à l'époque), typiquement un buteur entré en cours de jeu.

**Constat du 07/10/2026 : non reproduit.** Depuis la correction « remplaçants » (`Lineup.substitutes` peuplé par `narrative.match_result_from`, classe de tests `TestNoOmissionAfterSubstitutesFix`), mesure sur 18 matchs de Ligue 1 simulés (graine 3, 2 journées) : 299 événements de timeline, **299 clips, 0 omission**, dont 46 buts. Sur la journée 1, 27 événements ont un remplaçant pour protagoniste (dont 2 buts) : les 27 sont rendus. La docstring de `build_clips` est donc **obsolète** ; le risque résiduel est l'omission silencieuse d'un événement dont le protagoniste ne serait résolu dans aucune liste (onze de départ ni remplaçants entrés).

**Reproduction (si le cas réapparaît).** Simuler des matchs avec buteur entré en cours de jeu, construire `build_timeline` puis `build_clips(timeline, None)` et comparer `len(timeline.events)` à `len(clips)` (clé `(minute, gabarit, main_player)`). Script de mesure : voir le constat ci-dessus (boucle sur `calendar[0].matches`, `persisted_lineups`).

**Cause probable.** Le `continue` silencieux ; non reproduit depuis la correction, donc cause de l'omission d'origine non confirmée dans l'état actuel du code.

**Impact produit.** Si le cas se produit : moins de temps forts que d'occasions, et un score affiché qui avance sans clip correspondant (un but manquant dans la timeline du lecteur). Aucun impact observé à ce jour.

**Priorité.** Sans objet (fermé). Le `continue` silencieux et la docstring obsolète sont suivis dans le ticket 6.

**Statut.** **Fermé — non reproduit le 07/10/2026 : plus aucune omission mesurée sur 18 matchs / 299 événements** (299 clips, dont 46 buts ; 27 événements à protagoniste remplaçant, tous rendus). *Note de précision :* la docstring de `build_clips`, obsolète, n'est **pas** corrigée à ce jour — `engine/` n'a pas été modifié, par contrainte de cette étape — ; ce point est repris dans le ticket 6.

---

## 6. `build_clips` : `continue` silencieux quand `frames` est vide, et docstring obsolète

**Description.** Dans `engine/narrative_player.build_clips`, la boucle fait `frames, roster = _build_clip_frames(timeline, event)` puis `if not frames: continue` : un événement dont les frames sont vides est écarté **sans trace** (ni log, ni compteur, ni avertissement) ; il reste dans `Timeline.events` et son effet sur le score progressif est conservé, mais aucun clip ne lui correspond. La docstring de la fonction (datée du 23/09/2026) décrit encore l'ancienne cause, « protagoniste hors onze de départ (~36 % des occasions) », qui n'est plus reproduite (ticket 5, fermé) : elle est **obsolète et non corrigée**.

**Constat.** Au 07/10/2026 le `continue` n'est jamais atteint sur 18 matchs / 299 événements (0 omission). Aucun défaut visible aujourd'hui.

**Impact potentiel.** Si un futur gabarit (ou une évolution de `_build_clip_frames`) produit des frames vides, un clip disparaît silencieusement : moins de temps forts que d'occasions, un score qui avance sans clip correspondant, sans aucun signal pour le diagnostiquer. La docstring obsolète peut en outre induire en erreur (elle a servi de source à une affirmation inexacte dans un rapport du 07/10/2026).

**Reproduction.** Aucune à ce jour. Pour détecter le cas : comparer `len(timeline.events)` à `len(build_clips(timeline, None))`, ou ajouter un test d'invariant « un événement de la timeline = un clip » sur un lot de matchs simulés.

**Pistes (non implémentées).** Journaliser un avertissement (ou lever en mode test) quand `frames` est vide ; corriger la docstring ; test d'invariant sur 100 matchs.

**Priorité.** Basse — avant la Phase 7 (qualité).

**Statut.** Ouvert. Rien n'est corrigé (`engine/` non modifié).

---

## 7. `PitchView.jsx` : la version commitée diverge de celle de l'arbre de travail

**Description.** Le commit `f70b37d` contient `ui/src/routes/PitchView.jsx` dans sa version **adaptée au contexte de `HEAD`** (ancienne vue de 116 lignes) : bouton « Voir l'animation » placé **à côté du libellé de contexte**, état `showAnimation`, import de `MatchAnimation`, composant `AnimationDialog` en fin de fichier. L'arbre de travail contient une **refonte préexistante non commitée** de ce fichier (~400 lignes modifiées : `LivePanel`, `MatchHeader`, `MatchStatsPanel`, `PitchField`, replay en direct, alertes de buts) où le même bouton est placé **à côté de « Retour »**. Les deux versions ne partagent pas le même contexte textuel : le dépôt a, pour ce fichier, une version que personne n'utilise en pratique (celle du poste de travail est la refonte).

**Reproduction.** `git diff HEAD -- ui/src/routes/PitchView.jsx` : la refonte apparaît comme un grand diff qui **inclut** (ré-écrit dans son propre contexte) les 4 ajouts de l'animation ; un commit tel quel de la refonte remplacerait la version commitée sans conflit mais sans relecture des hunks d'animation.

**Impact.** Réconciliation obligatoire au prochain commit de la refonte préexistante ; risque de perdre ou de dupliquer un hunk d'animation (import, état, bouton, `AnimationDialog`) si le fichier est commité en bloc ou écrasé par un `git checkout`.

**Action attendue.** Lorsque le travail préexistant sera commité : partir de la **refonte**, y réintégrer explicitement les 4 hunks (import `MatchAnimation`, état `showAnimation`, bouton « Voir l'animation » à côté de « Retour », composant `AnimationDialog`), puis re-tester le build (`vite build`), le lint (`oxlint`) et le lancement en dev (modale d'animation fonctionnelle sur un match animable et sur un match sans snapshot). **Ne pas modifier la version commitée d'ici là.**

**Priorité.** Avant la Phase 5 (habillage visuel).

**Statut.** **Fermé — Résolu (07/10/2026).** Commit `7309172` a aligné la version commitée de `PitchView.jsx` sur l'arbre de travail. Les 4 hunks d'animation étaient déjà dans HEAD depuis `f70b37d`. Plus de divergence.

---

## 8. `pytest` seul échoue sur un checkout propre de `HEAD` (`ModuleNotFoundError: api`)

**Description.** `tests/test_api_animation.py` (commit `f70b37d`) importe `api.*`. Le `pyproject.toml` de `HEAD` fixe `pythonpath = ["engine"]` ; l'ajout de `"."` (nécessaire pour importer le paquet `api` à la racine) n'existe que dans une **modification préexistante non commitée** de `pyproject.toml`. Résultat : sur un checkout propre de `HEAD`, la commande `pytest tests` s'arrête à la collecte (`1 error during collection`) ; seule `python -m pytest` passe (elle ajoute le dossier courant au chemin).

**Reproduction (constatée le 07/10/2026).** `git archive HEAD` dans un dossier vierge, puis `pytest tests/test_api_animation.py` → `ModuleNotFoundError: No module named 'api'`. Avec `python -m pytest tests/test_canvas_html.py` : 5 passed.

**Cause.** Dépendance non commitée : le test commité (`f70b37d`) suppose le `pythonpath = ["engine", "."]` que le travail préexistant ajoute à `pyproject.toml` (3 lignes, commentaire compris).

**Impact.** Sur un clone propre, la suite de tests ne se lance pas avec la commande standard ; masqué sur le poste de travail où `pyproject.toml` est modifié.

**Correction proposée (non appliquée ici, hors périmètre de ce commit).** Commiter le hunk `pythonpath = ["engine", "."]` de `pyproject.toml` (voir `docs/repo_state.md`, plan, étape 0).

**Priorité.** Immédiate : avant tout push ou partage du dépôt.

**Statut.** **Fermé — Résolu (07/10/2026).** Correction commitée en `2d71e55` (`pythonpath = ["engine", "."]` dans `pyproject.toml`), vérifiée sur archive propre. Plus reproductible.


---

## 9. `pytest` nu échoue à la collecte à cause de `duckdb` absent du venv principal

**Description.** `simulafoot_nlg/tests/conftest.py` importe `duckdb` (ligne 11), qui n'est pas installé dans le venv principal (`.venv`). La collecte de `pytest` lancé sans précaution s'interrompt donc sur ce dossier avant d'exécuter le moindre test.

**Reproduction.** Depuis la racine du dépôt, `pytest tests` (ou `pytest` nu) avec le venv principal, sans ignorer NLG → `ModuleNotFoundError: No module named 'duckdb'`, **1 erreur de collecte**, 0 test exécuté. Constaté le 07/10/2026 (identique sur `git archive HEAD`).

**Contournement actuel.** `pytest tests --ignore=simulafoot_nlg` : 1018 passés, 5 ignorés, 12 désélectionnés sur HEAD `8ee3e7d`. La suite NLG se lance à part, depuis `simulafoot_nlg/` avec `simulafoot_nlg/.venv` (874 passés, 23 ignorés).

**Impact produit.** Impossible de lancer la suite complète en une seule commande ; la suite doit être scindée en deux exécutions avec deux environnements.

**Priorité.** Avant la Phase 7 (qualité / packaging).

**Statut.** Ouvert.

---

## 10. Le seuil de couverture à 85 % sur `engine/` échoue depuis le venv NLG

**Description.** `simulafoot_nlg/pyproject.toml:71` impose `addopts = "--cov=engine --cov-report=term-missing --cov-fail-under=85"`. Lancée depuis la racine du dépôt avec `simulafoot_nlg/.venv` (`python -m pytest simulafoot_nlg/tests`), la mesure échoue : **« FAIL Required test coverage of 85% not reached. Total coverage: 0.00% »**, alors que les tests passent (874 passés, 23 ignorés).

**Reproduction.** Depuis la racine du dépôt (ou d'une archive de `HEAD`) : `simulafoot_nlg/.venv/Scripts/python.exe -m pytest simulafoot_nlg/tests`. Le rapport liste `engine\narrative.py`, `engine\narrative_player.py`, `engine\nlg_ingestion.py` (le `engine/` **de la racine**) à 0 %. À l'inverse, lancée **depuis `simulafoot_nlg/`** (`cd simulafoot_nlg && .venv/Scripts/python.exe -m pytest tests`), la même suite atteint **99,77 %** (881 instructions, 2 non couvertes) et le seuil est tenu (constaté le 07/10/2026).

**Cause probable (précision).** Le défaut vient du **répertoire de lancement** et non du venv : `--cov=engine` désigne le paquet `engine` résolu depuis le répertoire courant, c'est-à-dire le `engine/` de la racine (moteur graphique, non couvert par ces tests) et non `simulafoot_nlg/engine/`. Non confirmée au-delà de ces deux lancements.

**Impact produit.** Faux échec (code de sortie non nul) d'une CI qui lancerait les tests NLG depuis la racine, malgré une suite verte.

**Pistes (non appliquées).** Lancer les tests NLG depuis `simulafoot_nlg/` ; ou redéfinir le périmètre (`--cov=simulafoot_nlg/engine`) ; ou ajuster le seuil. Décision de packaging à prendre.

**Priorité.** Avant la Phase 7 (qualité / packaging).

**Statut.** Ouvert.

---

## 11. `ConnectionResetError` Windows 10054 dans le journal de l'API

**Description.** Pendant le test §8.4 (07/10/2026), le journal d'`uvicorn` (`api.main:app`, port 8000) a affiché un `ConnectionResetError: [WinError 10054]` (« Une connexion existante a dû être fermée par l'hôte distant »), sans effet visible côté client : les pages se sont chargées, la simulation et l'animation ont fonctionné.

**Reproduction.** Non systématique. Apparue une fois au chargement de la liste de matchs depuis la PWA ; le mécanisme exact n'a pas été tracé. Une cause plausible, **non confirmée**, est une connexion fermée par le navigateur en cours de requête (rechargement, annulation, double appel de `StrictMode`) ; l'arrêt d'un serveur en cours de requête produit le même type d'erreur.

**Impact.** Bruit dans le journal ; aucune conséquence fonctionnelle connue.

**Priorité.** Basse, avant la Phase 7 (qualité / packaging).

**Statut.** Ouvert.

---

## 12. Sauts de trajectoire en amont liés aux changements de segment de gabarit

**Description.** Les joueurs effectuent des sauts brusques de position au changement de segment d'un gabarit : la trajectoire brute produite par `animation.motion.interpolate` présente des discontinuités (3 à 8 m en une image, soit 100 à 250 m/s). Distinct du ticket 1 (position hors du terrain, résolu en `61773ab` : la contrainte d'accélération est désormais bornée au terrain) ; la contrainte lisse ces sauts sans les supprimer.

**Reproduction.** Observer les clips de contre-attaque où le porteur change. Mesure du 07/10/2026 sur 40 matchs : 682 joueurs × clips sur ~16 300 (≈ 4 %) ont au moins un saut brut de plus de 40 m/s entre deux images, principalement entre 20 % et 60 % de la durée du clip (équipes `scorer` et `opponent`, tous postes). Cause non tracée plus finement (changement de segment, délai de réaction, évitement).

**Impact.** Rendu visuellement moins fluide (glissement ou téléportation d'un joueur sur quelques images) ; aucune position impossible depuis la correction du ticket 1.

**Priorité.** Basse, avant la Phase 7 (qualité / packaging).

**Statut.** Ouvert.

---

## 13. Axe de la barre de progression fixe à 0–90 min, marqueurs qui se chevauchent pour les clips rapprochés

**Description.** `render/canvas.html` positionne chaque marqueur de la barre de progression à `minute / 90` de sa largeur (échelle fixe 0–90, `Math.min(90, Math.max(1, minute))`). Quand plusieurs clips tombent à quelques minutes d'écart (cas fréquent : les temps forts sont concentrés), les marqueurs (9 à 12 px) se touchent ou se superposent. Depuis la sous-étape 3 de la Phase 5, un but est dessiné au-dessus d'une occasion voisine (`z-index`), ce qui évite qu'il soit masqué mais ne règle pas la superposition.

**Reproduction.** Match de référence de la Phase 5 (seed 26) : clips à 5', 7', 12' et 13' sur une barre d'environ 380 px (~4 px par minute) : les marqueurs de 5' et 7' sont à 8 px l'un de l'autre, ceux de 12' et 13' se recouvrent presque (4 px). Ouvrir l'animation d'un match avec plusieurs occasions dans le même quart d'heure.

**Impact.** Lisibilité : on distingue mal les marqueurs voisins et leur type (but / occasion) ; le clic peut tomber sur le mauvais marqueur. Aucune conséquence fonctionnelle sur la lecture.

**Pistes (non appliquées).** Axe ajusté à l'étendue réelle des minutes des clips (premier et dernier, avec marge) ; axe non linéaire (logarithmique ou compressé) ; zoom intelligent (écarter localement les marqueurs trop proches, infobulle de regroupement) ; ou marqueurs régulièrement espacés avec la minute en étiquette.

**Priorité.** Basse, avant la Phase 7 (qualité / packaging).

**Statut.** Ouvert.

---

## 14. Orientation des bandes de tonte : horizontal (implémenté) vs perpendiculaire (backlog 24/09)

**Description.** Le point 8 de `docs/visual_backlog.md` (retour du 24/09/2026) demandait des bandes de tonte « perpendiculaires à la longueur » du terrain (découpage de la longueur de 105 m). La sous-étape 3 de la Phase 5 a implémenté, sur instruction de l'architecte, des bandes **horizontales, parallèles aux lignes de touche** (9 bandes de 7,6 m sur la largeur de 68 m). Le terrain SVG de l'écran match de la PWA (`PitchField.jsx`) garde 18 bandes perpendiculaires à la longueur : les deux surfaces n'ont donc pas la même orientation de bandes.

**Décision actuelle.** Horizontal conservé (décision produit). Entrée créée pour la traçabilité de l'écart avec le backlog ; aucune correction prévue.

**Priorité.** Basse.

**Statut.** **Résolu — décision produit, horizontal conservé.**

---

## 15. `PitchField.jsx` : bandes de tonte perpendiculaires à la longueur, incohérentes avec `canvas.html`

**Description.** `render/canvas.html` (animation des temps forts) dessine des bandes de tonte **parallèles aux lignes de touche** (9 bandes horizontales de 7,6 m, Phase 5 sous-étape 3, voir ticket 14). `ui/src/components/pitch/PitchField.jsx` (terrain SVG de la fiche de match) dessine 18 bandes **perpendiculaires à la longueur** du terrain, avec d'autres verts (`#2d8a4e` / `#26793f`, fond `#1c5a30`). Les deux vues d'un même match n'ont donc ni la même orientation de bandes ni la même teinte.

**Reproduction.** Ouvrir la fiche d'un match joué (`PitchField.jsx`), puis cliquer sur « Voir l'animation » (`canvas.html`) et comparer les deux pelouses.

**Impact.** Incohérence visuelle entre les deux vues d'un même match ; aucune conséquence fonctionnelle.

**Piste.** Aligner `PitchField.jsx` sur `canvas.html` (bandes parallèles aux touches, mêmes verts), sauf décision produit contraire. Les cotes du terrain sont déjà partagées (`pitch_geometry.py` → `pitchGeometry.json`) ; les couleurs et le nombre de bandes ne le sont pas.

**Priorité.** Basse, avant la Phase 6 (produit / carrière).

**Statut.** Ouvert.

---

## 16. Point d'entrée seed manquant : `random.seed` ne suffit pas, il faut aussi `np.random.seed`

**Description.** Observation faite pendant le diagnostic du ticket 4 (08/10/2026) : deux processus lancés avec `random.seed(11)` (le `PYTHONHASHSEED=0` posé dans l'environnement n'était en fait pas appliqué : les scripts de mesure utilisaient `python -I`, qui l'ignore) simulent des saisons différentes (le même match « FC Toulouse – Paris FC » a donné 12, 16 puis 22 clips selon le processus). Cela contredit la propriété supposée « même graine = même match ». **Reformulation (08/10/2026) : le moteur est reproductible, c'est le point d'entrée de graine qui manque** (voir ci-dessous).

**Reproduction.** Lancer deux fois, dans deux processus distincts, `random.seed(11)` puis `simulate_current` sur une Ligue 1 (`CustomCompetition(format="LEAGUE", legs=2, ...)`), et comparer les scores de la journée 1, les buteurs et les compositions. Les scores diffèrent (mesure du 08/10/2026 : `5-0,1-0,2-1,…` contre `1-2,1-0,5-0,…`).

**Diagnostic (08/10/2026, aucun code modifié).** Le moteur n'est pas intrinsèquement non reproductible : **la graine ne fixait qu'un des deux générateurs globaux qu'il utilise.**
- `random.seed(…)` fixe le module Python `random`, utilisé par `src/ligue1sim/events.py` (`randint`, `choice`, `shuffle`, `random`, `gauss` : lignes 401, 413, 466, 502, 559, 563, 701, 714-715, 722-724, 757).
- Le **résultat sportif** (nombre de buts) vient de **`np.random`** (état global NumPy), jamais seedé par `random.seed` : `src/ligue1sim/simulation.py:643` (bruit sur lambda, `np.random.uniform`) et `:753` (tirage `np.random.poisson`) ; aussi `events.py:614` (choix pondéré du buteur), `match_stats.py:69-84`, `knockout.py:210` et `:226`, `champions_league.py:149-201`, `world_cup.py:68-181`.
- Nature : **(a) une graine manquante** (un seul des deux générateurs est seedé). Ni (b) un seed écrasé, ni (c) un ordre de `set` ou de dictionnaire, ni (d) l'horloge ou un identifiant système : `api/store.py:20` utilise `uuid.uuid4()` pour l'identifiant de compétition, mais il n'entre pas dans les tirages.
- Les générateurs locaux (`events._deterministic_rng`, `narrative.py`, `nlg_ingestion.py`) sont seedés par SHA-256, donc stables d'un processus à l'autre.
- **Vérification sur archive jetable de `HEAD`** (une saison de Ligue 1, empreinte SHA-256 des scores de toute la saison et des `MatchEvents` des journées 1 à 3, 2 processus par cas) : `random.seed` seul → empreintes **différentes** ; `random.seed` **et** `np.random.seed` → empreintes **identiques**, avec `PYTHONHASHSEED` libre (les scores et les événements ne dépendent donc pas du hachage ; seul l'ordre des joueurs dans une image du payload en dépend, voir ci-dessous). Aucune autre source d'aléa n'a été mise en évidence sur ce chemin.
- Les tests qui veulent de la reproductibilité seedent déjà les deux (`tests/test_canvas_e2e.py:64-65`, `tests/test_canvas_html.py:270-271`). Rien dans l'application ne seede quoi que ce soit : le comportement normal est aléatoire, ce qui est voulu.

**Impact.** Impossible de reproduire un bug à partir d'une graine unique (il faut connaître et fixer les deux générateurs) ; la comparaison de deux versions du moteur sur le même match demande cette précaution. Les deux générateurs étant **globaux**, deux requêtes API concurrentes (ou toute autre consommation de tirages) décalent le flux : même avec les deux graines, la reproductibilité n'est garantie qu'en exécution mono-fil et sans autre appel intercalé. Dette de fond.

**Précisions de mesure.** Dans `np.random` : lambdas et buts de Poisson (`simulation.py:643`, `:753`), choix du buteur (`events.py:614`), statistiques de match, tirs au but, tirages de Ligue des Champions et de Coupe du Monde. Dans `random` (module Python) : cartons, blessures, remplacements, notes (`events.py:701-757`). Autre constat (08/10/2026) : l'ordre des joueurs à l'intérieur d'une image du payload d'animation dépend de `PYTHONHASHSEED` (`interpolate` itère sur un `set`, `motion.py`) ; seul l'ordre change, pas les valeurs, et le client indexe par identifiant. Avec `PYTHONHASHSEED=0` deux processus donnent un payload identique octet pour octet.

**Proposition (non implémentée).** Un helper `seed_all(seed)`, par exemple dans `src/ligue1sim/seeding.py` :
```python
def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
```
appelé par les scripts, les tests et un éventuel paramètre de graine de l'API, avec une règle « toute comparaison de moteur passe par `seed_all` ». À plus long terme, des générateurs locaux passés explicitement. Ne change pas le résultat sportif tant qu'il n'est pas appelé.

**Règle de test (précisée le 08/10/2026).** Toute comparaison de moteur ou de payload doit fixer `random.seed`, `np.random.seed` **et** `PYTHONHASHSEED=0` (sans `python -I`, qui ignore cette variable) : sans le troisième, l'ordre des joueurs dans une image du payload varie d'un processus à l'autre.

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Cause diagnostiquée, **non corrigée**.

---

## 17. Pas de remplacement d'urgence modélisé (gardien expulsé sans remplaçant)

**Description.** Le moteur ne modélise aucun mécanisme d'urgence pour un gardien expulsé. Depuis la correction du ticket 2 (08/10/2026), un expulsé n'est jamais remplacé (règle volontaire), et le générateur n'a rien prévu pour le gardien : ni entrée du gardien remplaçant, ni passage d'un joueur de champ dans les buts. Le gardien expulsé reste sur la feuille de match, sans gardien actif pour la suite du match, **même quand un gardien remplaçant est sur le banc** (les remplacements tactiques excluent le poste de gardien, `events._play_match_squad`, et un expulsé est exclu des sortants).

**Reproduction.** Déterministe dès qu'un gardien titulaire reçoit un rouge direct ou un second jaune. Fréquence mesurée sur 3 000 matchs (graines 1 à 3 000, `random.seed` et `np.random.seed`, Ligue 1 réelle) : **93 gardiens titulaires expulsés sur 6 000 équipes-matchs, soit 1,55 % des équipes-matchs et 3,10 % des matchs**. Pour le voir : forcer le rouge du gardien (monkeypatch de `events._draw_card`, comme dans `tests/test_events.py::test_expelled_players_appear_in_no_later_event_even_when_forced`) et lire `events.substitutions`, qui ne contient aucune entrée du gardien remplaçant.

**Impact.** Un match peut se terminer sans gardien actif : `lineup_snapshot.players_on_pitch` retire l'expulsé à sa minute et personne ne le remplace ; l'animation compose chaque clip depuis la composition de départ, sans tenir compte des minutes de présence (limite préexistante de `engine/narrative.py`), et montre donc encore le gardien expulsé dans ses buts ; les buts encaissés continuent d'être comptés normalement (le résultat sportif n'est pas modifié). Impact visuel et de réalisme ; aucun effet sur les scores.

**Piste (non implémentée).** Lors d'une expulsion de gardien : soit faire entrer le gardien remplaçant s'il y en a un (en sacrifiant un joueur de champ non expulsé, selon la règle usuelle), soit désigner un joueur de champ comme gardien de fortune. À arbitrer car cela fait consommer des tirages et modifie la distribution des remplacements.

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Non corrigé.

---

## 18. Poteau / barre toujours attribués à l'attaquant

**Description.** `engine/ball_events.py` attribue le dernier toucher d'un poteau ou d'une barre à l'**attaquant**, quel que soit le cas. Un défenseur qui dégage le ballon sur son propre poteau devrait lui aussi pouvoir produire un corner ; aujourd'hui, un ballon qui ressort par la ligne de but après un poteau ne peut donner qu'une `sortie_but`.

**Reproduction.** Rare : seul un rebond de montant qui franchirait la ligne de but hors des poteaux est concerné. Avec les règles actuelles (le ballon repart toujours vers le terrain après un poteau ou une barre, jamais derrière la ligne), le cas ne se produit pratiquement pas dans les clips actuels ; il apparaîtra si une issue « dégagement sur le poteau » est ajoutée à la narration.

**Impact.** Incohérence logique avec la règle du corner (dernier toucheur défenseur), sans effet visible aujourd'hui ni sur le score.

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Non corrigé.

---

## 19. Imports privés entre modules : `ball_events.py` importe `_simulate_rebound` et `_deterministic_unit` depuis `ball.py`

**Description.** `engine/ball_events.py` importe deux fonctions préfixées par `_` de `src/ligue1sim/animation/ball.py` : `_simulate_rebound` (simulation des rebonds au sol) et `_deterministic_unit` (fraction déterministe par hachage). Le code est fonctionnel, mais ces noms sont privés et peuvent changer sans prévenir.

**Reproduction.** Renommer ou changer la signature de l'une de ces deux fonctions dans `ball.py` : `engine/ball_events.py` ne s'importe plus (échec immédiat des tests de `tests/test_ball_events.py`).

**Impact.** Fragilité : une refactorisation de `ball.py` casse `ball_events.py`. Aucun effet fonctionnel aujourd'hui.

**Piste (non implémentée).** Exposer ces deux fonctions dans l'interface publique de `ball.py` (sans préfixe), ou déplacer la simulation de trajectoire dans un module partagé.

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Non corrigé.

---

## 20. Clips poteau prolongés jusqu'à la touche, coupés à 1,0 s

**Description.** Un tir sur le poteau dont le ballon ressort par la ligne de touche produit un événement `touche`, et le clip est coupé 1,0 s après. Mesure du 08/10/2026 (avant le biais gardien) : 54 poteaux sur 131 sont concernés. `canvas.html` ignore l'événement `touche` : le ballon quitte le terrain sans aucune animation, puis le clip s'arrête.

**Reproduction.** Simuler 100 matchs (graines 1 à 100) et lire les événements `touche` qui suivent un événement `poteau` dans `metadata.events_ball`.

**Impact.** Cas fréquent parmi les poteaux (41 %) mais sans conséquence sur le score ; la sortie n'est pas soulignée à l'écran.

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Non corrigé.

---

## 21. Spin binaire (0 ou 50 rad/s) dans `templates.py`, pas de valeurs intermédiaires

**Description.** Le spin est posé par `templates.py` (`build_decalage_enroulee`, constante `_DECALAGE_ENROULEE_SHOT_SPIN_RAD_S = 50.0`) et prend **deux valeurs seulement** : 0 ou 50 rad/s. Mesure du 08/10/2026 (graines 1 à 100, 1 586 clips, 373 456 images échantillonnées à 30 Hz) : aucune image avec un spin strictement compris entre 0 et 5 rad/s ; seul `decalage_enroulee` (163 clips, 10,3 %) porte un spin non nul. La traînée de rotation de `canvas.html` (B3) ne peut donc distinguer que deux cas : enroulé ou pas. Le spin est en outre posé sur la **conduite** de ce gabarit (82,5 % des images à spin non nul, 17 767 sur 21 546) et pas seulement sur la frappe.

**Reproduction.** Construire les séquences des 12 gabarits de `templates.py` et échantillonner `ball_state_at(...).spin` : valeurs 0,0 et 50,0 uniquement.

**Impact.** Aucune variété de frappes : un tir enroulé est toujours le même, un tir tendu n'a jamais d'effet. La traînée de B3 apparaît sur 10,3 % des clips, toujours sur le même gabarit.

**Piste (non implémentée).** Pour varier les frappes (B5), introduire une distribution continue de spin selon le type de frappe, et le poser sur le vol (`ball_flight`) plutôt que sur la conduite.

**Priorité.** Moyenne, à traiter en B5.

**Statut.** Ouvert. Non corrigé.

---

## 22. Courbure non perceptible à l'échelle 6 px

**Description.** Avec un ballon de 6 px (décision Phase 5) et la traînée de B3 (0,37 s), la courbure d'un tir enroulé n'est pas perceptible à l'œil nu. Mesures du 08/10/2026 (graines 1 à 5, canvas 1 200 × 780, 10,88 px par mètre) :
- **courbure réelle** (écart maximal à la corde, séquences `decalage_enroulee`, spin 50 rad/s) : 0,36 à 1,32 m sur le vol `ball_flight` (4 à 14 px) ; 0 à 3,46 m sur la conduite `shot` (jusqu'à 38 px) ;
- **courbure visible dans la traînée** (flèche de la traînée de 0,37 s, 4 à 12 m de long) : **0,06 à 0,82 px** en vol, 2,47 px au plus en conduite. Ces chiffres sont ceux de la traînée, pas de la trajectoire entière : la traînée suit les positions réelles du ballon mais, sur une durée aussi courte, elle se lit comme une ligne droite.

**Reproduction.** Rejouer un clip `decalage_enroulee` (graine 2, clip 0, t = 6,4 s) : le sillage est droit à l'œil ; l'écart à la corde de la trajectoire complète n'apparaît qu'en regardant l'ensemble du tracé après coup.

**Impact.** Impossible de distinguer visuellement une frappe courbée d'une frappe droite à l'échelle actuelle ; la traînée ne signale que la présence d'un spin (B3, ticket 21).

**Pistes.** (a) agrandir le ballon à 8 px (modifie la décision Phase 5, refusée) ; (b) exagérer l'effet Magnus (`_MAGNUS_K`, `ball.py`, refusé) ; (c) un tracé long (2 à 3 s) de la trajectoire, à évaluer ; (d) accepter la limitation.

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Non corrigé.

---

## 23. NLG ne reçoit pas le type de frappe, texte générique incohérent avec le rendu

**Description.** Le NLG choisit son commentaire sur (type d'événement, gabarit, issue) et pioche dans des banques génériques ; il ne reçoit ni le type de frappe de B5 (`shot_tendu`, `shot_enroule_*`, `reprise_vollee`, `tete`…) ni le spin. Une phrase du type « enroule sa frappe » peut donc accompagner un `shot_tendu` sans traînée, et un `decalage_enroulee` (toujours `shot_enroule_fort`) être commenté sans le mot « enroule » (1 texte sur 149, mesure du 08/10/2026, 100 matchs). Contradictions texte / animation mesurées : 83 avant B5, 61 après (volée 41, enroulée 13, tête 7).

**Fichiers concernés.** `engine/narrative.py` (le `NarrativeEvent` ne porte pas le type), `engine/narrative_player.py` (le type n'existe que dans `templates.py`, au moment de construire l'animation), `engine/nlg_ingestion.py` (dictionnaire transmis au NLG : gabarit et issue seulement).

**Piste (non implémentée).** Calculer le type de frappe en amont de l'animation (même hachage de `event_ref`) et le transmettre au NLG (champ du contrat), ou conditionner les phrases « volée », « enroulée », « tête » sur ce champ.

**Priorité.** Moyenne ; résolution prévue après B5.

**Statut.** Ouvert. Non corrigé.

---

## 24. Commentaire faux sur la zone d'un penalty dans `engine/narrative.py`

**Description.** Le commentaire qui précède `_GABARIT_BASE_ZONE` (`engine/narrative.py`, lignes 380 à 387 environ) affirme qu'un penalty part « exactement au point réglementaire, aucune divergence » avec `events.PENALTY_SPOT_ZONE`. C'est inexact : `_narrative_event_zone` applique à **tous** les gabarits, penalty compris, un décalage déterministe (`_ZONE_JITTER_COLS = 1`, `_ZONE_JITTER_ROWS = 2`), et `PENALTY_SPOT_ZONE` (`src/ligue1sim/events.py`) est le centre d'une case de la grille (13,12 m de la ligne de but, 4,25 m de l'axe), pas le point de penalty réel (11 m, axe). Mesure du 08/10/2026 (graines 1 à 100, 34 clips de penalty) : le ballon part de 4,4 à 21,9 m de la ligne de but.

**Correction attendue.** Corriger le texte du commentaire seulement, **sans modifier le comportement** ; le point de départ des penaltys sera traité dans `src/ligue1sim/animation/templates.py` (B6) et non dans ce fichier.

**Priorité.** Basse.

**Statut.** Ouvert. Non corrigé.

---

## 25. Clips de but dont la dernière image est avant la ligne

**Description.** Certains clips de but n'ont aucune image où le ballon dépasse la ligne entre les poteaux : l'image la plus tardive (échantillonnage à 30 images/s, `_FPS` dans `engine/narrative_player.py`) tombe quelques centimètres avant la ligne (écart maximal mesuré 1,5 m). Le canvas gère le cas par un repli (`goalEvents` dans `render/canvas.html` : l'événement but part à la dernière image), donc rien ne casse à l'écran. Mesure sur 295 clips de but (graines 1 à 100) : **45 (15,3 %) avant B5**, 54 (18,3 %) juste après B5, **50 (16,9 %) après le recalibrage du pool pied** (`6bb8e5e` puis `dbe65a9`), les vols étant plus rapides (`src/ligue1sim/animation/templates.py`).

**Impact et trace.** Le test `test_goal_clips_of_a_real_payload_cross_the_line_between_the_posts` (`tests/test_canvas_html.py`) tolère maintenant une dernière image à moins de 1,5 m de la ligne. Défaut préexistant, légèrement aggravé par B5 (+5 clips sur 295 par rapport à avant B5).

**Résolution.** À décider par le propriétaire (par exemple une image finale ajoutée à l'instant exact de la fin du vol, ou une durée de séquence alignée sur le pas d'image).

**Priorité.** Basse, avant la Phase 7.

**Statut.** Ouvert. Non corrigé.

---

## 26. Divergence moteur / narration sur les penaltys ratés : l'animation montre des ratés qui n'ont pas eu lieu et omet ceux du moteur

**Description.** Il existe deux générateurs indépendants de penaltys ratés. Le moteur (`src/ligue1sim/events.py`, `_generate_missed_penalties`, champ `penalties_missed`) en produit environ 9 par 100 matchs ; ils apparaissent dans le fil de commentaire live (`api/live_commentary.py`, « PENALTY MANQUÉ ») et dans la liste des événements du match (`app.py`), mais **ne produisent aucun clip**. La narration (`engine/narrative.py`, `_missed_penalty_count`, moyenne de Poisson `_MISSED_PENALTY_POISSON_MEAN` ≈ 0,078 par match) en invente de son côté environ 8 par 100 matchs, qui sont animés (gabarit `penalty`) mais **absents** du moteur. Mesure du 08/10/2026 (graines 1 à 100) : 9 ratés côté moteur, 8 côté narration, **0 en commun** (même minute, joueur et club). Les buts de penalty, eux, sont les mêmes des deux côtés (26 sur 26, identiques dans les 100 matchs).

**Impact.** Divergence entre le moteur et la narration, pas seulement un trou d'affichage : l'animation montre des penaltys ratés **qui n'ont jamais eu lieu** (ceux de la narration, absents des événements du moteur) et **ne montre pas** ceux qui ont eu lieu (ceux du moteur, listés dans le fil live et la liste des événements). Le fil du NLG (`api/nlg_live.py`, qui lit la narration) et le fil du moteur (`api/live_commentary.py`) ne racontent donc pas les mêmes penaltys ratés. Le résultat sportif n'est pas touché (un penalty raté ne change pas le score) ; la cohérence du produit l'est.

**Fichiers concernés.** `src/ligue1sim/events.py` (`_generate_missed_penalties`, `penalties_missed`), `engine/narrative.py` (`_missed_penalty_count`, `_MISSED_PENALTY_POISSON_MEAN`, `_generated_events`), `api/live_commentary.py`, `api/nlg_live.py`, `app.py` (liste des événements du match).

**Résolution.** À décider par le propriétaire (par exemple animer les ratés du moteur et supprimer ceux de la narration). Hors périmètre de B6 ; elle pourrait être couplée au **Bloc C (cohérence du rendu)** plutôt qu'à B6.

**Priorité.** Basse à moyenne, à trancher par le propriétaire.

**Statut.** Ouvert. Non corrigé.

---

# Décisions du propriétaire (entrées documentaires — ce ne sont pas des tickets)

## Décision propriétaire — dispositifs clubs conservés (D3)

**Description factuelle.** Le commit 3b (`3070543`) remplace `data/entraineurs.xlsx` par `data/Coachs-Simulafoot.xlsx`. En Ligue 1, ce nouveau classeur change le **dispositif préférentiel de 6 clubs sur 18** par rapport à `HEAD` d'avant 3b : Le Havre (4-2-3-1 → 4-3-3 Attacking), Paris FC (3-4-2-1 → 4-2-3-1), Lens (4-2-3-1 → 3-4-2-1), Angers (4-3-1-2 → 4-2-3-1), Troyes et Paris Saint-Germain (4-3-3 → 4-3-3 Attacking). Les notes de secteur de composition (utilisées par le modèle de Poisson) changent pour 4 d'entre eux ; elles sont inchangées pour Troyes et le PSG. Effet **sur le résultat sportif** : les lambdas de ces clubs, et marginalement ceux des autres (via les moyennes de la ligue qui les normalisent). Aucun modulateur coach/styles n'est en jeu (lot 3c non commité).

**Mesure** (simulations sur archives jetables, Ligue 1 réelle, `HEAD` avant 3b contre `HEAD` + 3b ; détail au §8.10 de `docs/repo_state.md`) :
- **1 000 matchs, flux continu** : écart de moyenne de buts totale **+0,017** (graine 1) et **−0,017** (graine 2), du même ordre que le bruit de référence ; aucun test significatif.
- **30 612 matchs, flux continu** : Δ buts/match total **−0,0131 ± 0,0267** (IC 95 %), non significatif.
- **30 612 matchs, mode apparié** (même graine à chaque match) : Δ buts/match total **−0,0042** (IC 95 % apparié [−0,0067 ; −0,0018]).
- **Part des matchs dont le score diffère, en apparié** : **2,73 %** des matchs de la Ligue 1 (837 / 30 612) ; **4,25 %** des matchs impliquant au moins l'un des 6 clubs (739 / 17 404) ; **0,74 %** des matchs n'en impliquant aucun (98 / 13 208).
- **Effet par club** (points par match, 30 612 matchs, flux continu) : de l'ordre du bruit (Le Havre +0,025, Lens +0,028, Paris FC −0,003 ; bruit des 12 clubs non modifiés : de −0,029 à +0,035).

**Précision sur les chiffres de la consigne du propriétaire (écart consigné, non recopié).** La consigne du 07/10/2026 citait « +0,062 but par match (+2,3 %) » et « 7 % des matchs des clubs concernés ». Les mesures ci-dessus donnent autre chose : **+0,062 est l'écart de moyenne entre deux graines différentes du `HEAD` seul** (A graine 1 2,764 − A graine 2 2,702), c'est-à-dire du **bruit**, pas l'effet des données de coachs ; la part de scores différents pour les matchs des 6 clubs est de **4,25 %** (5,67 % pour les 4 clubs à notes de secteur modifiées), et **0,74 %** concerne les matchs **sans** aucun de ces clubs, non la Ligue 1 entière (2,73 %).

**Décision.** Le propriétaire a tranché : **les dispositifs issus de `data/Coachs-Simulafoot.xlsx` sont conservés tels quels, aucune neutralisation** ; l'effet est une **caractéristique produit assumée**. La décision est enregistrée telle qu'elle a été communiquée ; les chiffres mesurés ci-dessus sont fournis pour information.

**Référence.** `docs/repo_state.md` §8.10 (vérification `np.random` et effet « données ») et §8.11 (baseline de la mesure D2).

**Statut.** **Résolu — décision propriétaire, 07/10/2026.** Ne crée aucun ticket ouvert ; les tickets 1 à 8 ne sont pas modifiés.
