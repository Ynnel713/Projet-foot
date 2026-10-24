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
- Coachs et compétitions existantes : hors périmètre de ce plan (D-V09/D-V10) — chantiers séparés, à planifier plus tard.

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

Quand un adversaire est à portée directe (1,5 m) du porteur du ballon, il peut tenter un tacle -- fréquence de la tentative pilotée par Aggression seule, issue du duel pilotée par Tackling (tacleur, avec un peu d'Aggression) contre la moyenne Strength/Balance du porteur. Un tacle raté a un risque de faute piloté par Aggression seule, indépendamment de Tackling (contrepartie attendue par le guide). Pas de lecture tactique de QUAND tacler (IA placeholder, D-V08) ni de conséquence de jeu pour une faute (pas de coup franc : Phase 5+). La table de pondération par poste (D-V07) reste vide : ces 4 attributs ne sont pas différenciés par poste dans ce modèle (un tacle est un tacle, quel que soit le poste de qui le tente) -- à revoir si un besoin concret apparaît.

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

**Principe d'ordre** : un attribut n'a d'effet que si l'action qu'il pilote existe dans le moteur. On construit l'action, puis on y branche les attributs.

| Phase | Ce qu'on ajoute au moteur | Attributs |
|---|---|---|
| 5. Cerveau des joueurs | Vraie décision du porteur et des non-porteurs (remplace l'IA placeholder D-V08) | Decisions, Vision, Off the Ball, Anticipation, Flair, Teamwork |
| 6. Défense organisée | Bloc, marquage, pressing | Positioning, Marking, Work Rate, Concentration |
| 7. Gestes offensifs | Dribble, centre, tête, frappe de loin | Dribbling, Crossing, Heading, Jumping Reach, Long Shots, Bravery, Agility |
| 8. Ballon hors du terrain | Touches, corners, coups francs, penalties | Corners, Free Kick Taking, Long Throws, Penalty Taking |
| 9. Gardien complet | Sorties, centres, relances | Aerial Reach, Command of Area, Communication, Kicking, Throwing, Rushing Out, Punching, Eccentricity |
| 10. Caractère et profil | Moral selon le score, pied fort, habitudes | Determination, Leadership, Weak foot, Pieds, Preferred moves |

Natural Fitness agit entre les matchs : hors de ces phases, avec le branchement aux compétitions (D-V10).

**Phase 5 découpée** : `.scratch/v2-cerveau-joueurs/issues/` (01 à 06). Phases 6 à 10 : à découper une fois la précédente livrée.

**Correctif préalable (24/10/2026)** : `movement.step` perdait les attributs des joueurs dès le 2ᵉ tick (retour à 60 par défaut) ; passes, contrôles, tacles et tirs des Phases 2 à 4 ignoraient donc les vraies notes en match. Corrigé, test de régression dans `tests/test_v2engine_movement.py`.

### Bloquée par

- Phase 4
