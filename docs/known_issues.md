# Dette connue — Simulafoot

Tickets ouverts, documentés pour être traités plus tard. **Aucun n'est corrigé à ce jour.** Créé le 07/10/2026 (clôture de l'Étape B, `LineupSnapshot`) ; tickets 4 et 5 ajoutés le même jour (intégration PWA par iframe).

| # | Titre | Priorité (avant…) | Statut |
|---|---|---|---|
| 1 | Joueur statique poussé hors de la marge près d'un bord du terrain | Phase 5 (habillage visuel) | Ouvert |
| 2 | Un joueur expulsé peut être remplacé plus tard dans le même match | Phase 4 (branchement PWA effectif) | Ouvert |
| 3 | `SubstitutionEvent` identifie les joueurs par nom, pas par `player_id` | Phase 6 (produit / carrière) | Ouvert |
| 4 | Latence et poids du payload d'animation | Phase 6 (produit / carrière) | Ouvert |
| 5 | `build_clips` écarte silencieusement un événement dont le protagoniste n'est pas résolu (protagoniste hors onze de départ) | Phase 6 (produit / carrière) | Ouvert (non reproduit) |

---

## 1. Joueur statique poussé hors de la marge près d'un bord du terrain

**Description.** Dans les clips animés, un joueur immobile (`vx = vy = 0`, souvent hors porteur de balle) peut se retrouver légèrement au-delà de la marge de tolérance (0,1 en coordonnées normalisées) près d'un bord du terrain.

**Reproduction.** Test d'intégration `tests/test_narrative_player.py::TestNoOmissionAfterSubstitutesFix::test_substitute_placed_correctly` (marqueur `integration`, donc hors suite par défaut). Constaté le 07/10/2026 :
- échec dans le run complet des 12 tests d'intégration (`x = 1.1048`) ;
- échec **3 fois sur 3 en isolation** : `x = 1.1002`, `x = 1.1059`, `x = 1.1048`, ou `y = −0.105` (tolérance 0,1, soit des bornes −0,1 / 1,1) ;
- identique avec la création du `LineupSnapshot` désactivée (2 fois sur 2) : le problème préexiste à l'Étape B.

`_simulate_n(100)` n'a pas de graine aléatoire : les valeurs changent à chaque exécution, l'échec lui est systématique.

**Cause probable.** `animation.motion._apply_avoidance` (évitement de collisions entre joueurs), que le commentaire du test désigne lui-même comme pouvant pousser une position au-delà de 0/1 près du bord. **Non confirmée** : le mécanisme exact n'a pas été tracé.

**Impact produit.** Un joueur est légèrement hors du terrain près d'un bord, perceptible visuellement dans l'animation.

**Priorité.** Avant la Phase 5 (habillage visuel).

**Statut.** Ouvert.

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

## 5. `build_clips` écarte silencieusement un événement dont le protagoniste n'est pas résolu (protagoniste hors onze de départ)

**Description.** `engine/narrative_player.build_clips` ignore (`if not frames: continue`) tout événement pour lequel `_build_clip_frames` ne produit aucune frame, sans trace ni compteur ; l'événement disparaît des clips alors qu'il reste dans `Timeline.events` (et le score progressif est calculé sur tous les événements). La docstring de `build_clips` (datée du 23/09/2026) attribue ce cas aux protagonistes absents du onze de départ (« ~36 % des occasions » mesurées à l'époque), typiquement un buteur entré en cours de jeu.

**Constat du 07/10/2026 : non reproduit.** Depuis la correction « remplaçants » (`Lineup.substitutes` peuplé par `narrative.match_result_from`, classe de tests `TestNoOmissionAfterSubstitutesFix`), mesure sur 18 matchs de Ligue 1 simulés (graine 3, 2 journées) : 299 événements de timeline, **299 clips, 0 omission**, dont 46 buts. Sur la journée 1, 27 événements ont un remplaçant pour protagoniste (dont 2 buts) : les 27 sont rendus. La docstring de `build_clips` est donc **obsolète** ; le risque résiduel est l'omission silencieuse d'un événement dont le protagoniste ne serait résolu dans aucune liste (onze de départ ni remplaçants entrés).

**Reproduction (si le cas réapparaît).** Simuler des matchs avec buteur entré en cours de jeu, construire `build_timeline` puis `build_clips(timeline, None)` et comparer `len(timeline.events)` à `len(clips)` (clé `(minute, gabarit, main_player)`). Script de mesure : voir le constat ci-dessus (boucle sur `calendar[0].matches`, `persisted_lineups`).

**Cause probable.** Le `continue` silencieux ; non reproduit depuis la correction, donc cause de l'omission d'origine non confirmée dans l'état actuel du code.

**Impact produit.** Si le cas se produit : moins de temps forts que d'occasions, et un score affiché qui avance sans clip correspondant (un but manquant dans la timeline du lecteur). Aucun impact observé à ce jour.

**Priorité.** Avant la Phase 6 (produit / carrière). À réévaluer : mettre à jour la docstring, ou transformer le `continue` silencieux en avertissement.

**Statut.** Ouvert (non reproduit au 07/10/2026) ; rien n'est corrigé.

