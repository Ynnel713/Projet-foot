# 07: Mi-temps dans le moteur : arrêt, replacement, coup d'envoi

**What to build:** le moteur V2 joue 90 minutes d'un seul bloc (`v2engine/match.py`, `simulate_match`) : pas d'arrêt à la 45e, pas de coup d'envoi, ni au début ni en seconde période. Depuis le 03/11/2026, l'écran V2 retourne la scène d'un demi-tour à partir de la 45e pour que les équipes changent de camp, mais en plein jeu : l'image bascule au milieu d'une action. Ce ticket reprend le point 1 du ticket 03 (le temps additionnel y reste, toujours bloqué).

1. **Arrêt à la mi-temps.** À 45:00 de jeu, l'action en cours s'arrête : passe en vol, tir en route, hors-jeu signalé, pressing et transitions sont remis à zéro.
2. **Replacement.** Les 22 joueurs reprennent leur position de coup d'envoi (`formation.initial_positions`), sans téléportation visible à l'écran (voir point 5).
3. **Coup d'envoi.** Il y en a un au début du match et un en seconde période, par l'autre équipe. Aujourd'hui, le ballon est posé libre au centre et le premier arrivé le prend. Le ballon est confié au joueur de champ le plus avancé et le plus central de l'équipe qui engage, posé sur le point central ; il le joue comme n'importe quel porteur (voir les constantes ci-dessous). Les adversaires restent hors du rond central jusqu'au premier toucher. L'équipe qui engage la première période est tirée au sort (module `random`, graine du match, D-V06).
4. **Changement de camp.** Recommandation : garder dans le moteur la convention « domicile attaque vers x croissant » tout le match, et retourner l'image à l'écran (déjà fait).
   - Le terrain V2 n'a aucune asymétrie : pas de vent, pas de soleil, rien ne dépend du côté. Retourner l'image donne donc exactement le même match.
   - Inverser vraiment le sens dans le moteur toucherait environ 8 modules qui supposent cette convention : `bloc.py`, `cerveau.py`, `decision.py`, `defense.py`, `offside.py`, `situation.py`, `formation.py` et `match.py` (`_OPPONENT_GOAL`). Le risque de régression serait réel, sans rien changer au jeu.
   - Ce qui change dans le moteur : la trace dit quand commence la seconde période (`second_half_start_minute`), et l'écran retourne l'image sur ce signal plutôt que sur la constante `HALF_TIME_MIN = 45` codée en dur.
5. **Écran.** Bandeau « MI-TEMPS » (durée : voir les constantes), puis seconde période retournée. Les joueurs n'apparaissent à leur place qu'après le bandeau.
6. **Récupération d'énergie à la pause.** Hors ticket : la fatigue dépend aujourd'hui seulement de la minute (`movement.stamina_factor`). Il n'y a pas de réserve d'énergie à remplir. À faire avec `v2-collectif/12`.

**Attributs :** aucun.

**Blocked by:** v2-collectif/29 (ballon mort et engagement). Ce ticket, en cours dans une autre session le 03/11/2026, pose déjà `restart.kickoff` : engagement du début de match et après chaque but, joueurs dans leur camp, adversaires hors du rond. Le 07 se réduit alors à la mi-temps (arrêt à 45:00, engagement par l'autre équipe, signal dans la trace, bandeau à l'écran), construite sur ce `kickoff`. Coder le 07 en parallèle ferait écrire deux sessions dans `v2engine/match.py`.

**Status:** livré (04/11/2026), validé expert + QC (réserves A1 et A2 acceptées par délégation du propriétaire, voir Comments) ; reste le contrôle visuel du propriétaire (dernier critère)

**Constantes (proposées et validées le 03/11/2026, par délégation du propriétaire) :**

| Constante | Valeur | Pourquoi |
|---|---|---|
| Bandeau de mi-temps | 3 s réelles, quelle que soit la vitesse de lecture | Assez pour être lu, sans casser le rythme ; masque le replacement des joueurs. À x8, une durée en temps de match serait illisible. |
| Équipe qui engage la 1re période | tirage 50/50 (module `random`, graine du match) | Loi 8 : tirage au sort. L'autre équipe engage la 2e période. |
| Joueur qui engage | joueur de champ le plus avancé, puis le plus proche de l'axe (à égalité : ordre de la compo) | C'est l'avant-centre ou le n°10 dans la quasi-totalité des matchs. Pas de second joueur requis (Loi 8 depuis 2016). |
| Première passe | aucune direction imposée : décision normale du porteur (`decision.choose_action`), après son délai de réception habituel (`possession.reception_delay_s`) | Depuis 2016, la Loi 8 autorise de jouer le ballon vers l'avant. Ce sont les attributs qui choisissent, et aucune constante nouvelle n'est créée. |
| Rond central | rayon `CENTER_CIRCLE_RADIUS_M` déjà défini (9,15 m, `ligue1sim.pitch_geometry`) ; adversaires dehors jusqu'au premier toucher | Loi 8 ; c'est une cote du terrain, pas une constante produit. |

**Décision du propriétaire (03/11/2026) :** le même coup d'envoi s'applique après chaque but, par l'équipe qui a encaissé (Loi 8). C'est le même code. Jusqu'ici, après un but, le ballon était posé libre au centre. Comme à la mi-temps, les 22 joueurs reprennent leur position de coup d'envoi : la Loi 8 impose que chacun soit dans sa moitié. Dans un vrai match, cela prend environ une minute de célébration. À l'écran, ce replacement est caché par le ralenti du but.

**Point de vigilance :** le jeu après la 45e change (tout le monde repart de sa position), donc les mesures V2 de référence qui couvrent un match entier se décalent. Il faut les refaire avant/après (`scripts/measure_v2.py`, `scripts/v2_indicators.py`), à graine fixée. Le ticket 03 (temps additionnel) partira de ce découpage en deux périodes.

## Acceptance criteria

- [x] À 45:00, plus aucun ballon en vol, tir en route ni hors-jeu en attente ; les 22 joueurs repartent de `initial_positions`
- [x] Coup d'envoi au début et en seconde période, par deux équipes différentes ; le ballon est tenu par un joueur de l'équipe qui engage, au rond central
- [x] Après chaque but, coup d'envoi par l'équipe qui a encaissé : ballon tenu au point central, adversaires hors du rond jusqu'au premier toucher
- [x] La trace expose le début de la seconde période ; l'écran retourne l'image sur ce signal et affiche « MI-TEMPS »
- [x] Test moteur : à graine fixée, état juste après la 45e (positions, porteur, ballon) ; deux exécutions donnent la même empreinte de trace
- [x] Mesures avant/après sur 20 matchs (buts, possession, indicateurs V2), écarts expliqués
- [x] Suite complète verte, compte comparé à l'attendu ; V1 inchangée
- [ ] Vu à l'écran par le propriétaire : mi-temps, changement de camp sans bascule en plein jeu

## Réalisation (04/11/2026)

Code écrit par la session « Ticket 7 », vérifié et clôturé par une autre session (délégation du propriétaire, « je te laisse finaliser les 2 tickets »).

- **Moteur** (`v2engine/match.py`) : l'équipe qui engage la 1re période est tirée au sort (`random.random() < 0.5`, graine du match). Au pas `n_ticks // 2` (45:00 pour 90 minutes) : chacun reprend `home_target` (sa place de départ) à vitesse nulle, ballon neuf au centre (passe, tir, hors-jeu et remise en attente abandonnés), engagement par l'autre équipe (`restart.kickoff`, ticket 29 : engageur, camps, rond central), suivis de situation, bloc, défense, transition, appels et intentions remis à zéro ; situation de jeu réenregistrée à cet instant. Le sens de jeu ne change pas (point 4).
- **Après un but** : déjà fait par le ticket `v2-collectif/29` (`kickoff` par l'équipe qui a encaissé), rien à ajouter.
- **Trace et API** : `MatchTrace.second_half_start_minute`, exposé par `MatchTraceOut` et `MatchProgressOut` (`api/routers/v2.py`).
- **Écran** (`V2Match.jsx`) : demi-tour de la scène sur `second_half_start_minute` (repli 45 tant que le moteur ne l'a pas donné) ; bandeau « MI-TEMPS » 3 s réelles, match en attente pendant le bandeau ; pas de glissade entre la dernière image de la 1re période et la première de la 2e.
- **Tests** : `tests/test_v2engine_mi_temps.py` (replacement et engagement par l'autre équipe à graine fixée, empreinte identique sur deux exécutions, tirage au sort du premier engagement sur 10 graines).

**Vérifications.** Arbre isolé = `9aa4ff9` + seuls fichiers du ticket. Suite complète : 2 334 passés, 5 ignorés, 13 désélectionnés, 0 échec (+3 tests). À l'écran (API et Vite de l'arbre isolé, x8 ; panneau du navigateur masqué, animation entraînée par un minuteur dans la page) : à 45:00, bandeau « MI-TEMPS » 3,0 s, match arrêté à 45' pendant le bandeau, puis 2e période retournée (gardien domicile x 5 → 100).

**Mesures (banc `measure_v2`, graine d'audit, 20 matchs en 2 lots de 10).** Avant = `9aa4ff9`, après = ticket.

| Indicateur | Avant | Après | Lecture |
|---|---|---|---|
| Buts par match | 2,95 | 2,95 | inchangé |
| Tirs par équipe | 30,4 | 30,6 | inchangé |
| Engagements par match | 3,95 | 4,85 | +1 attendu (engagement de la 2e période) ; 4,85 contre 4,95 attendus : 2 buts sur 20 matchs marqués dans les 45 s avant la pause ou la fin, dont l'engagement n'est jamais joué (revue expert) |
| Hors-jeu par match | 1,45 | 0,80 | 29 contre 16 sur 20 matchs, ≈ 2 écarts-types : bruit du tirage (le tirage au sort décale tout l'aléa du match) ; la mi-temps n'annule au plus qu'un hors-jeu en attente par match |
| Tacles par match | 33,2 | 33,7 | inchangé |
| Touches / sorties de but / corners | 26,1 / 29,7 / 8,1 | 25,7 / 29,4 / 7,8 | inchangés |
| Temps de jeu effectif | 72,1 % | 72,6 % | inchangé |
| Possession d'équipe (s), passes par possession | 14,3 / 2,65 | 14,3 / 2,65 | inchangés |
| Baisse de la course intense en fin de match | 23,5 % | 15,3 % | à suivre : fatigue fonction de la minute seulement (`stamina_factor`), écart attribué au replacement et au bruit sur 20 matchs |

**Engagement réellement joué (réserve A2).** Le 07 se construit sur `restart.kickoff` du ticket `v2-collectif/29` : l'engageur est le joueur de champ le plus proche du centre (`restart.py`), posé au point central, et passe aussitôt vers `restart_target`, sans délai de réception. Le tableau des constantes ci-dessus (engageur « le plus avancé puis le plus proche de l'axe », première passe après délai de réception) décrit l'intention initiale, pas le code ; il prévaut ce qui est codé au ticket 29, identique au coup d'envoi du match.

Hors ticket, inchangé : récupération d'énergie à la pause (`v2-collectif/12`).

## Comments

- 04/11/2026, clôture (passage 1) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ. Réserves acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes les reco d'experts », 03/11/2026 ; « je te laisse finaliser les 2 tickets », 04/11/2026).
  - A1 [réserve] hors-jeu 1,45 → 0,80 par match (29 contre 16, ≈ 1,9 σ, dans les deux lots) sans mécanisme démontré : à remesurer sur au moins 40 matchs avant/après dans `v2-collectif/22`.
  - A2 [réserve] le tableau des constantes ne décrivait pas l'engagement codé (ticket 29) : note ajoutée dans la Réalisation.
  - A3 [facultatif] but dans les 2 dernières secondes de la 1re période : bandeau puis ralenti en 1re période.
  - A4 [facultatif] sous le bandeau (voile à 60 %), la 2e période est déjà placée et retournée ; voile opaque ou image gelée possibles.
  - Lint `ui/` : 0 erreur, 5 avertissements (inchangé) ; build OK.
  - À surveiller (`v2-collectif/22`) : hors-jeu par match ; baisse de la course intense en fin de match (15 %, bas de la fourchette 10-30 %).
