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

**User stories** : US-27

**Attributs couverts** : First Touch, Passing, Technique

### Ce qu'on livre

Un joueur en possession du ballon peut le contrôler (qualité du contrôle pilotée par First Touch) et le passer à un coéquipier (précision/réussite pilotées par Passing, gamme de gestes par Technique). Le ballon suit une trajectoire physique simple entre les deux joueurs. Toujours pas de tir, de duel ni de gardien à ce stade.

### Critères d'acceptation

- [ ] Un joueur peut recevoir, contrôler et transmettre le ballon à un coéquipier
- [ ] Un First Touch bas produit visiblement plus de ballons mal contrôlés qu'un First Touch élevé, à situation égale
- [ ] Un Passing bas produit visiblement plus de passes imprécises/ratées qu'un Passing élevé
- [ ] Le mode batch reste cohérent avec le mode « regarder »
- [ ] La V1 reste 100 % inchangée

### Bloquée par

- Phase 1

---

## Phase 3 — Duels et tacles

**User stories** : US-27

**Attributs couverts** : Tackling, Strength, Balance, Aggression

### Ce qu'on livre

Quand un adversaire est à proximité du porteur du ballon, un duel peut se déclencher (tacle), résolu par un tirage pondéré par Tackling/Strength/Balance/Aggression des deux joueurs, modulé par leur poste (table de pondération de la Phase 1). Une Aggression haute augmente les tacles tentés et le risque de faute (contrepartie attendue par le guide), pas seulement le taux de réussite.

### Critères d'acceptation

- [ ] Un joueur proche du porteur adverse peut tenter un tacle, résolu par les attributs des deux joueurs
- [ ] Un écart de Tackling/Strength/Balance favorise mesurablement le joueur le mieux noté, sans jamais garantir l'issue à 100 %
- [ ] Une Aggression haute produit plus de fautes/tacles ratés qu'une Aggression basse, à Tackling égal
- [ ] Le mode batch reste cohérent avec le mode « regarder »
- [ ] La V1 reste 100 % inchangée

### Bloquée par

- Phase 2

---

## Phase 4 — Tirs et gardien (match complet jouable, score inclus)

**User stories** : US-27, US-29

**Attributs couverts** : Finishing, Composure (côté tireur) ; Reflexes, Handling, One on Ones (côté gardien, essentiels seulement — Communication/Kicking/Throwing/Aerial Reach/Command of Area/les tendances viennent en Phase 5+)

### Ce qu'on livre

Un joueur en position de tir peut tenter sa chance ; l'issue (cadré, arrêté, but) est résolue par Finishing/Composure côté tireur et Reflexes/Handling/One on Ones côté gardien, modulés par la distance/l'angle issus de la physique. À la fin de ce ticket, un match complet est jouable de bout en bout : l'issue (score) émerge entièrement du moteur, pour la première fois sans aucun score décidé à l'avance. C'est le jalon livrable de ce premier plan (US-29 : regardable sans connaître le score à l'avance, ou simulable d'un coup sans regarder).

### Critères d'acceptation

- [ ] Un tir est résolu par les attributs du tireur et du gardien, jamais par un tirage indépendant des données
- [ ] Un Finishing/Composure élevé augmente mesurablement le taux de conversion, sans jamais garantir un but
- [ ] Un gardien avec un Reflexes/One on Ones élevé arrête mesurablement plus de tirs qu'un gardien noté bas, à tir égal
- [ ] Un match complet (coup d'envoi à coup de sifflet final) se joue de bout en bout et produit un score, sans score pré-décidé
- [ ] Le match est regardable depuis la nouvelle tuile « Version 2 (bêta) » de l'accueil, sans connaître le score avant de lancer la lecture
- [ ] Le mode « tout simuler sans regarder » produit aussi un score exploitable, sur le même moteur
- [ ] La V1 reste 100 % inchangée

### Bloquée par

- Phase 3

---

## Phase 5+ — Attributs dispensables (après qu'un match complet existe)

**User stories** : US-27 (approfondissement)

**Statut** : non découpée en tickets précis à ce stade — à détailler une fois la Phase 4 livrée et validée par le propriétaire.

**Attributs restants à intégrer, par groupe, sans ordre de priorité encore fixé entre eux** :
- Prise de décision / lecture de jeu : Decisions, Vision, Anticipation, Concentration, Off the Ball (déjà en Phase 1 en placeholder — vraie IA ici), Teamwork, Flair, Work Rate
- Coups de pied arrêtés spécialisés : Corners, Free Kick Taking, Long Throws, Penalty Taking
- Jeu de tête et duels aériens : Jumping Reach, Heading, Crossing, Long Shots, Marking, Dribbling
- Gardien, le reste : Aerial Reach, Command of Area, Communication, Kicking, Throwing, Eccentricity, Punching (Tendency), Rushing Out (Tendency)
- Caractère et intangibles : Determination, Courage (Bravery), Leadership, Weak foot, Pieds, Preferred moves

### Bloquée par

- Phase 4
