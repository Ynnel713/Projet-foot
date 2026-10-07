# Dette connue — Simulafoot

Tickets ouverts, documentés pour être traités plus tard. **Aucun des tickets ouverts (2, 3, 4, 6, 9, 10, 11 et 12) n'est corrigé à ce jour.** Créé le 07/10/2026 (clôture de l'Étape B, `LineupSnapshot`) ; tickets 4 et 5 ajoutés le même jour (intégration PWA par iframe) ; ticket 5 fermé et tickets 6 à 8 ouverts le même jour (gouvernance, avant Phase 5) ; tickets 9 (`duckdb`) et 10 (couverture NLG) ajoutés le même jour (environnement de test). tickets 7 (résolu en `7309172`) et 11 (`ConnectionResetError`) traités le même jour. **État : ouverts 2, 3, 4, 6, 9, 10, 11, 12 ; fermés 1 (résolu en `61773ab`, Phase 5 sous-étape 1), 5 (non reproduit), 7 (résolu en `7309172`) et 8 (résolu en `2d71e55`, vérifié sur archive propre).**

| # | Titre | Priorité (avant…) | Statut |
|---|---|---|---|
| 1 | Joueur statique poussé hors de la marge près d'un bord du terrain | Phase 5 (habillage visuel) | **Résolu** — commit `61773ab`, tolérance recalibrée à 0,5 % |
| 2 | Un joueur expulsé peut être remplacé plus tard dans le même match | Phase 4 (branchement PWA effectif) | Ouvert |
| 3 | `SubstitutionEvent` identifie les joueurs par nom, pas par `player_id` | Phase 6 (produit / carrière) | Ouvert |
| 4 | Latence et poids du payload d'animation | Phase 6 (produit / carrière) | Ouvert |
| 5 | `build_clips` écarte les événements dont le protagoniste n'est pas dans le onze de départ | — | **Fermé** (non reproduit) |
| 6 | `build_clips` : `continue` silencieux quand `frames` est vide (et docstring obsolète) | Phase 7 (qualité) | Ouvert (priorité basse) |
| 7 | `PitchView.jsx` : la version commitée diverge de celle de l'arbre de travail | Phase 5 (habillage visuel) | **Fermé — Résolu** (`7309172`) |
| 8 | `pytest` seul échoue sur un checkout propre de `HEAD` (`ModuleNotFoundError: api`) | Immédiate (avant tout partage / push) | **Fermé — Résolu** (`2d71e55`) |
| 9 | `pytest` nu échoue à la collecte à cause de `duckdb` absent du venv principal | Phase 7 (qualité / packaging) | Ouvert |
| 10 | Le seuil de couverture à 85 % sur `engine/` échoue depuis le venv NLG | Phase 7 (qualité / packaging) | Ouvert |
| 11 | `ConnectionResetError` Windows 10054 dans le journal de l'API | Phase 7 (qualité / packaging) — priorité basse | Ouvert |
| 12 | Sauts de trajectoire en amont liés aux changements de segment de gabarit | Phase 7 (qualité / packaging) — priorité basse | Ouvert |

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

**Statut.** Ouvert. Toute correction touche le moteur d'événements, donc le comportement sportif : à arbitrer avant.

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

**Statut.** Ouvert.

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
