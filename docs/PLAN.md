# Plan : Réalisme du mouvement collectif des joueurs

> PRD source : `docs/PRD.md`

## Décisions architecturales

- **Chemin clips vs feuille de match** : `pitch_layout.py::place_starting_xi` n'est jamais modifié. Toute dispersion ou mouvement ajouté par ce chantier est appliqué en aval, dans `src/ligue1sim/animation/sequence_generator.py`, uniquement sur le chemin de production des clips d'action. La feuille de match avant-match reste strictement inchangée.
- **Style de jeu d'entraîneur** : réutilisation du concept déjà existant dans `src/ligue1sim/coaches.py` (`Coach.styles`, 5 valeurs : Pressing, Offensif, Défensif, Contre-attaque, Possession). Pas de nouveau champ sur `Club` : ce chantier relie un concept existant au rendu visuel, il ne l'invente pas.
- **Modèle de trajectoire des joueurs de décor** : `BackgroundTrack` (actuellement 2 points : départ + delta figé) est étendu vers une trajectoire à plusieurs points/segments. Mise à jour corrélée de `types.py`, `serialize.py` et `motion.py::_background_position_at`.
- **Courbe de mouvement** : réutilisation de la courbe Bézier ease-in-out déjà utilisée pour les acteurs scriptés (`motion.py::_ease_progress`) pour les joueurs de décor — pas de nouvelle courbe à inventer.
- **Déterminisme** : toute nouvelle variabilité introduite par une phase suit le pattern sha256 existant (clé stable `f"{player_id}|{event_ref}|{salt}"`), avec un `salt` dédié propre à la phase. Jamais `hash()`, `random`, horloge.
- **Mesure** : une métrique de dispersion/réalisme du mouvement de décor (absente aujourd'hui de `scripts/measure_geometry.py`, qui ne mesure que les acteurs scriptés) est ajoutée dès la Phase 1 et réutilisée/étendue par les phases suivantes.
- **Constantes produit** : chaque seuil, amplitude ou profil introduit par une phase est proposé au propriétaire avant d'être figé dans le code (US-10).
- **Échantillon de mesure** : graine d'audit `20260923`, pipeline réel via `scripts/measure_geometry.py`, comme pour le chantier 1.
- **Préalable** : ce chantier ne démarre qu'après la clôture complète du chantier 1 en cours (géométrie macro des gabarits).

---

## Phase 1 : Dispersion des lignes de départ

**User stories** : US-1, US-6, US-7, US-8, US-9, US-10

### Ce qu'on livre

Pour le chemin de production des clips uniquement, chaque joueur de décor reçoit, en aval de `place_starting_xi`, un écart déterministe par rapport à sa position de ligne tactique théorique, borné pour rester tactiquement crédible. La feuille de match avant-match n'est pas affectée.

### Critères d'acceptation

- [ ] Nouvelle métrique de dispersion (dans `scripts/measure_geometry.py`) strictement supérieure après, sur l'échantillon de référence (graine 20260923)
- [ ] Déterminisme bit-à-bit vérifié sur deux lectures d'un même clip
- [ ] Résultat sportif (score, buts, cartons, remplacements) identique sur l'échantillon de matchs
- [ ] Feuille de match avant-match visuellement inchangée
- [ ] Propriétaire valide visuellement que l'effet « file indienne » de départ a diminué sur l'échantillon
- [ ] Suite de tests complète passée, revue `simulafoot-reviewer` effectuée

## Bloquée par

- Aucune — démarrable après la clôture complète du chantier 1 existant.

---

## Phase 2 : Mouvement continu pendant l'action

**User stories** : US-2, US-6, US-7, US-8, US-9, US-10

### Ce qu'on livre

Le modèle de trajectoire des joueurs de décor passe d'un point de départ + delta figé (`BackgroundTrack` actuel) à une trajectoire à plusieurs points, interpolée par la même courbe Bézier ease-in-out que les acteurs scriptés, pour un mouvement fluide sur toute la durée du clip, sans à-coup.

### Critères d'acceptation

- [ ] Aucun segment ne présente plus de saut de position/arrêt net d'une image à l'autre qu'aujourd'hui (mesure `measure_geometry.py`)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif inchangé sur l'échantillon de matchs
- [ ] Feuille de match avant-match inchangée
- [ ] Propriétaire valide visuellement la fluidité du mouvement sur l'échantillon
- [ ] Suite de tests complète passée, revue `simulafoot-reviewer` effectuée

## Bloquée par

- Phase 1

---

## Phase 3 : Initiatives de soutien par poste

**User stories** : US-3, US-6, US-7, US-8, US-9, US-10

### Ce qu'on livre

Certains joueurs de décor, selon leur poste (ex. latéral, attaquant), peuvent initier un mouvement de soutien identifiable (dédoublement offensif, repli défensif) pendant le clip. L'amplitude n'est pas bridée à une zone figée mais reste dans un secteur tactiquement crédible pour le poste.

### Critères d'acceptation

- [ ] Mesure chiffrée de fréquence/amplitude des initiatives par poste, documentée avant/après
- [ ] Aucune initiative ne place un joueur hors de son secteur tactiquement crédible, vérifié sur l'échantillon
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif inchangé, feuille de match avant-match inchangée
- [ ] Propriétaire valide visuellement les initiatives de soutien sur l'échantillon
- [ ] Suite de tests complète passée, revue `simulafoot-reviewer` effectuée

## Bloquée par

- Phase 2

---

## Phase 4 : Modulation par qualités individuelles du joueur

**User stories** : US-4, US-6, US-7, US-8, US-9, US-10

### Ce qu'on livre

L'intensité et la fréquence des initiatives de soutien d'un joueur dépendent de ses attributs déjà connus du projet (endurance, sens défensif, etc.) quand ils sont disponibles. Comportement par défaut cohérent pour les joueurs sans attributs renseignés.

### Critères d'acceptation

- [ ] Mesure comparant deux profils de joueurs contrastés (ex. forte vs faible endurance) montrant une différence de comportement cohérente
- [ ] Comportement par défaut vérifié pour un joueur sans attributs renseignés
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif inchangé, feuille de match avant-match inchangée
- [ ] Propriétaire valide visuellement le contraste de comportement sur l'échantillon
- [ ] Suite de tests complète passée, revue `simulafoot-reviewer` effectuée

## Bloquée par

- Phase 3

---

## Phase 5 : Style de jeu d'entraîneur et comportement collectif

**User stories** : US-5, US-6, US-7, US-8, US-9, US-10

### Ce qu'on livre

Chaque club est relié, de façon stable, à son style de jeu d'entraîneur déjà existant dans le projet (`coaches.py`), qui module la hauteur du bloc et l'intensité collective des initiatives de soutien définies aux phases 3 et 4 (une équipe qui presse ne se comporte pas comme une équipe qui défend bas).

### Critères d'acceptation

- [x] Mesure chiffrée du contraste de comportement entre deux styles de jeu (ex. pressing vs défensif) sur l'échantillon
- [x] Un même club produit le même style d'un match à l'autre (stabilité vérifiée)
- [x] Déterminisme bit-à-bit vérifié (deux exécutions séparées du pipeline 100 matchs, style de coach actif : 1552/1552 images identiques, même hash moteur)
- [x] Résultat sportif inchangé, feuille de match avant-match inchangée (`simulation.py`, `pitch_layout.py` non modifiés — confirmé par `simulafoot-reviewer`)
- [x] Propriétaire valide visuellement le contraste collectif sur l'échantillon (démo Pressing vs Défensif, même séquence/tirage, seul le style du club scoreur change)
- [x] Suite de tests complète passée, revue `simulafoot-reviewer` effectuée (1780 passés, 13 désélectionnés, 0 échec ; revue : aucun défaut bloquant ni majeur)

## Bloquée par

- Phase 4
