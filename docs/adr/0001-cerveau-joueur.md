# 0001 — Cerveau du joueur : perception, interprétation, décision, exécution

- **Statut** : accepté (26/10/2026, propriétaire)
- **Ticket** : `.scratch/v2-collectif/issues/02-intentions-perception-decision.md`

## Contexte

Dans le moteur V2, ce que fait un joueur sans ballon était décidé dans une seule fonction (`match._step_player`), par une suite de cas : porteur, appel, receveur visé, passe lue, ballon proche, place de formation. Les attributs y intervenaient à des endroits dispersés. Les tirages « voir », « choisir » et « réussir » existaient (Vision, Anticipation, Off the Ball ; Decisions ; Passing, First Touch, Finishing…), mais sans cadre commun, et rien ne permettait de relire après coup pourquoi un joueur avait fait ce qu'il a fait.

Le chantier « intelligence collective » (`docs/PLAN_V2.md`) va ajouter la reconnaissance de la situation de jeu, des rôles collectifs (presser, couvrir, compenser), des transitions et des tendances individuelles. Sans structure commune, chacun de ces ajouts viendrait allonger la suite de cas.

## Décision

1. **Quatre temps à chaque tick, pour chaque joueur** (module `v2engine/cerveau.py`) :
   - **Perception** : ce que le joueur détecte (porteur, ballon, trajectoire, passe qu'il a lue, place dans son équipe) ;
   - **Interprétation** : son **rôle** à cet instant ;
   - **Décision** : son action, sa cible et son intensité ;
   - **Exécution** : le mouvement (`movement.step`) et les gestes (passe, contrôle, tir, tacle), résolus par les modules existants.
2. **L'intention est l'unique sortie du cerveau** : rôle, action, cible (point et joueur), intensité, raison lisible. L'exécution du déplacement ne lit que l'intention. Exception assumée de ce premier passage : le choix du porteur (passer, tirer, conduire : Vision et Decisions) reste pris dans `match._step_ball` via `decision.choose_action`, et c'est le journal des décisions qui le trace ; l'intention du porteur décrit son déplacement (contrôle, conduite). L'intention enregistrée est celle du début du tick, avant que le ballon ne bouge.
3. **Chaque attribut est rattaché à un seul temps** (règle anti double comptage, ticket 18) :
   - perception : Vision, Anticipation, Concentration (à venir) ;
   - décision : Decisions, Off the Ball (choix de l'espace), Positioning (où est sa place dans le bloc, sans ballon) puis Teamwork (y retourner ou la tenir), en deux temps distincts (ticket v2-collectif/04), et plus tard les tendances (Flair) ;
   - exécution : techniques et physiques.

   Un même effet n'est jamais compté dans deux temps.
4. **Introduction sans changement de jeu** : le premier passage reprend les règles existantes telles quelles, dans le même ordre de tirages aléatoires. Critère : même graine, même trace, au tirage près.
5. **Relecture** : les intentions sont enregistrées dans la trace (une par joueur et par instant enregistré), avec un **journal des décisions du porteur** (instant, joueur, action, cible, nombre d'options envisagées, meilleure option prise ou non). Elles sont exposées par l'API V2 et affichées dans l'écran V2 pour le joueur sélectionné.

## Conséquences

- Les tickets suivants ajoutent des rôles, des règles d'interprétation et des raisons dans `cerveau.py`, sans toucher à la boucle de match.
- La trace et la réponse de l'API grossissent (une intention par joueur et par seconde enregistrée) ; leur poids est mesuré à chaque ticket.
- L'ordre des tirages aléatoires devient une contrainte explicite : tout changement de cet ordre change les matchs, et doit être volontaire.
