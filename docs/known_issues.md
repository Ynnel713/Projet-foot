# Dette connue — Simulafoot

Tickets ouverts, documentés pour être traités plus tard. **Aucun n'est corrigé à ce jour.** Créé le 07/10/2026 (clôture de l'Étape B, `LineupSnapshot`).

| # | Titre | Priorité (avant…) | Statut |
|---|---|---|---|
| 1 | Joueur statique poussé hors de la marge près d'un bord du terrain | Phase 5 (habillage visuel) | Ouvert |
| 2 | Un joueur expulsé peut être remplacé plus tard dans le même match | Phase 4 (branchement PWA effectif) | Ouvert |
| 3 | `SubstitutionEvent` identifie les joueurs par nom, pas par `player_id` | Phase 6 (produit / carrière) | Ouvert |

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
