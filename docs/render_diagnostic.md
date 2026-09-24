# Diagnostic de rendu — clip 1 (preview `apps/streamlit_preview.py`, mode "match")

Diagnostic du 24/09/2026. Aucune correction implémentée, aucun test ajouté, aucun fichier source modifié. Reproduction : `apps/streamlit_preview.py`, mode "match", seed=7 (PSG–Monaco), match_max_occasions=4 — mêmes données que ce que le propriétaire a vu à l'écran.

**Script d'extraction** : `scripts/diagnose_render_clip1.py`, écrit pour ce diagnostic, **supprimé après usage** (Tâche 1.3 — non réutilisable tel quel : hardcodé sur ce seed/ces squads/ces 5 analyses précises). La sortie brute complète (22 joueurs × 24 frames échantillonnées du clip 1) est conservée dans [docs/previews/canvas/clip1_raw_frames.json](previews/canvas/clip1_raw_frames.json).

**Clips construits sur ce match** (pour contexte) :
```
clip[0] minute=2  gabarit=debordement_centre_tete equipe=PSG    issue=hors_cadre main_player=home_cb0 duration_s=8.500 n_frames=256
clip[1] minute=6  gabarit=contre_attaque           equipe=PSG    issue=arret      main_player=home_cm2 duration_s=8.733 n_frames=263
clip[2] minute=11 gabarit=recuperation_haute       equipe=Monaco issue=arret      main_player=away_cb1 duration_s=5.333 n_frames=161
clip[3] minute=21 gabarit=debordement_centre_tete  equipe=PSG    issue=tacle      main_player=home_cb3 duration_s=6.000 n_frames=181
```
Le diagnostic porte sur **clip[0]** (le premier affiché à l'ouverture de la preview — celui vu par le propriétaire), gabarit `debordement_centre_tete`, formation déclarée PSG = "4-3-3", Monaco = "4-2-3-1".

---

## Problème 1 — Positionnement PSG sans structure tactique

**(a) Chiffres bruts** — positions de la frame 0 (départ), équipe PSG (`team_side="scorer"`), 11 titulaires :

| # | Poste | x (m, depuis sa ligne) | y (m, latéral) |
|---|---|---|---|
| 1 | GK | 3.0 | 34.0 |
| 2 | DC | 21.7 | 17.0 |
| 3 | DC | 21.7 | 34.0 |
| 4 | DC | 21.7 | 51.0 |
| 5 | LB | 21.7 | 8.2 |
| 6 | RB | 21.7 | 59.8 |
| 7 | MC | 32.9 | 21.8 |
| 8 | MC | 32.9 | 46.2 |
| 9 | BU | 44.1 | 34.0 |
| 10 | AG | 44.1 | 8.2 |
| 11 | AD | 44.1 | 59.8 |

Constat brut : **5 joueurs de champ (3×DC + LB + RB) partagent exactement la même profondeur x=21.7m**, et **3 joueurs (BU, AG, AD) partagent exactement la même profondeur x=44.1m** — pour un dispositif déclaré "4-3-3" (attendu : 4 défenseurs sur une ligne, pas 5 ; attaquants habituellement pas tous strictement alignés). Distances inter-joueurs (les 11 titulaires) : moyenne=28.89 m, min=4.03 m, max=56.33 m.

**(b) Cause probable — CONFIRMÉE, pas ambiguë.**

`engine/narrative_player.py::_lineup_start_positions` (lignes 140-143) reconstruit un `PlayerMatchStat` par joueur pour appeler `pitch_layout.place_starting_xi` :
```python
stats = [
    PlayerMatchStat(player_name=p.name, club_name=lineup.club_name, poste=p.poste, started=True)
    for p in lineup.players
]
```
**`band` n'est jamais renseigné** (reste à sa valeur par défaut `None`, voir `src/ligue1sim/events.py:211`). Or `pitch_layout._group_into_lines` (`src/ligue1sim/pitch_layout.py:178-204`) documente explicitement sa priorité : *"Priorité à `stat.band` ... Si un joueur n'a pas de bande connue ... retombe sur l'ancien regroupement par grande famille de poste (GK/DEF/MID/ATT)"*. Sans `band`, TOUS les DC/LB/RB tombent dans le même groupe `DEFENDER` et TOUS les AG/AD/BU dans le même groupe `ATTACKER` (`src/ligue1sim/players.py:22-35`, `POSITION_GROUP`) — chaque groupe est ensuite placé sur **une seule ligne, une seule profondeur** par `place_starting_xi` (`pitch_layout.py:122-129`, `_line_y` donne une valeur unique par ligne).

**Preuve que le "vrai" chemin existe et fonctionne ailleurs** : `src/ligue1sim/events.py:592-609` (`generate_match_events`, le vrai pipeline de simulation) construit ses `PlayerMatchStat` avec `band=entry.band` correctement renseigné — c'est le patron correct, déjà en place pour l'écran "stade" de l'app (`api/routers/competitions.py::get_pitch_view`). Le bug est localisé : **deux endroits précis oublient de le reproduire** :
- `engine/narrative_player.py:140-143` (`_lineup_start_positions`, équipe qui marque).
- `src/ligue1sim/animation/sequence_generator.py:340-342` (`_opponent_positions`, équipe adverse — même oubli, donc Monaco est ÉGALEMENT concerné par cet aplatissement en lignes, pas seulement PSG).

**Fait distinct, non tranché ici** : le XI réellement sélectionné compte 5 postes "défenseur" (3 DC + LB + RB) et seulement 2 "MC" pour un dispositif étiqueté "4-3-3" — même avec `band` correctement transmis, la ligne défensive resterait à 5 joueurs, pas 4. Est-ce normal pour ce pool synthétique (voir `apps/streamlit_preview.py::_match_squad`, 4 DC/2 LB/2 RB disponibles) ou un signe que `lineup.select_best_xi` s'écarte du dispositif visé plus que prévu ? **Non instrumenté ici** — hors périmètre de ce diagnostic (concerne `lineup.py`, pas le rendu).

**(c) Sévérité** : **majeur**. Ne casse rien mécaniquement (score/minute/buteur restent exacts, voir `tests/test_canvas_e2e.py`), mais compromet directement l'objectif affiché du chantier ("façon Football Manager", terrain crédible) sur **tous les clips**, pas seulement celui-ci.

**(d) Fichiers à modifier (identifiés, non touchés)** :
- `engine/narrative_player.py` (fonction `_lineup_start_positions`).
- `src/ligue1sim/animation/sequence_generator.py` (fonction `_opponent_positions`).

---

## Problème 2 — Joueurs Monaco quasi immobiles

**(a) Chiffres bruts** — déplacement total (distance euclidienne en mètres, position frame 0 → frame finale) de chaque joueur Monaco sur les 8,5 s du clip :

| # | Poste | Distance totale | Statut |
|---|---|---|---|
| 8 | MC | 3.607 m | mobile |
| 1 | GK | 2.397 m | mobile |
| 4 | LB | 0.007 m | **quasi figé** |
| 5 | RB | 0.034 m | **quasi figé** |
| 6 | MOC | 2.488 m | mobile |
| 2 | DC | 0.628 m | mobile |
| 9 | BU | 3.894 m | mobile |
| 3 | DC | 0.628 m | mobile |
| 11 | AD | 3.467 m | mobile |
| 10 | AG | 3.772 m | mobile |
| 7 | MC | 2.575 m | mobile |

**9 joueurs sur 11 se déplacent** (0.6 à 3.9 m sur 8,5 s), **2 sont quasi figés** (LB #4 = 0.007 m, RB #5 = 0.034 m).

**(b) Cause probable — confirmée pour les 2 joueurs figés, amplitude générale documentée comme limite connue pour les 9 autres.**

Les 2 latéraux figés : `sequence_generator._tactical_drift` (`src/ligue1sim/animation/sequence_generator.py:249-261`) — un latéral d'une équipe en phase défensive (`team_side="opponent"`, le cas de Monaco ici puisque PSG attaque) **du côté du ballon** est volontairement quasi statique : *"Latéral côté ballon, équipe qui défend : reste, couvre sur place"* (commentaire ligne 260-261), amplitude plafonnée à `_DEFENDER_Y_MAX = 0.02` (1,36 m) **multipliée par un facteur déterministe par joueur** (`_deterministic_unit`, hash SHA-256) qui, pour ce seed précis, est tombé proche de 0 pour ces deux joueurs — comportement voulu, pas une valeur figée en dur.

Les 9 autres joueurs bougent réellement, mais avec une **amplitude volontairement faible** (quelques mètres sur 8,5 s, ~0,3-0,5 m/s) : c'est le comportement documenté de `_tactical_drift`/`enrich_with_background`, dont les propres commentaires précisent *"Ces règles ne visent PAS le réalisme parfait ... seulement une cohérence tactique de base"* (`sequence_generator.py:149-151`). C'est une **limite déjà identifiée et planifiée** avant ce diagnostic (chantier "figurants actifs (amplitude micro-mouvements)" listé dans la feuille de route, après les briefs gardien actif) — pas une découverte nouvelle.

**(c) Sévérité** : **mineur**. Les 2 cas à 0 m sont un comportement voulu (défenseur qui "couvre sur place"), pas un bug. L'amplitude générale faible est une limite déjà connue et déjà planifiée, pas une régression à corriger en urgence.

**(d) Fichiers à modifier (si le chantier "figurants actifs" est priorisé)** : `src/ligue1sim/animation/sequence_generator.py` (constantes `_DEFENDER_Y_MAX`, `_MID_Y_MAX`, etc. et logique `_tactical_drift`) — **hors scope de ce diagnostic**, décision déjà différée à un chantier dédié.

---

## Problème 3 — Le porteur du ballon dépasse le ballon

**(a) Chiffres bruts** — distance porteur signalé (`is_ball_carrier=True`) ↔ ballon, échantillonné sur le clip :

| frame | t (s) | porteur signalé | joueur le + proche du ballon | distance porteur↔ballon (m) |
|---|---|---|---|---|
| 0 | 0.00 | #14 | #14 | 0.000 |
| 12 | 0.40 | #14 | #14 | 0.503 |
| 24 | 0.80 | #14 | #14 | 0.986 |
| 48 | 1.60 | #14 | #14 | 1.889 |
| 72 | 2.40 | #14 | #14 | 2.709 |
| 96 | 3.20 | #14 | #14 | 3.447 |
| 108 | 3.60 | #14 | #14 | 3.786 |
| 132 | 4.40 | #14 | **#4** | 3.727 |
| 156 | 5.20 | #14 | **#4** | 7.453 |
| 180 | 6.00 | #14 | #14 | 8.500 |
| 192 | 6.40 | #2 | #2 | 8.811 |
| 216 | 7.20 | #2 | #1 | 26.432 |
| 240 | 8.00 | #2 | #5 | 44.054 |
| 255 (fin) | 8.50 | #2 | #5 | **55.067** |

Distance moyenne porteur↔ballon sur l'échantillon : **12,85 m**. Maximum : **55,07 m** (à la toute dernière frame). La distance croît de façon quasi continue de 0 m (t=0) à 8,5 m (t=6.0s), point où le joueur porteur change (#14 → #2) — et continue ensuite de croître jusqu'à 55 m à la fin du clip. #2 est `home_cb0`, le buteur déclaré de cette occasion (`main_player`) : le "tireur" est censé être **à côté du ballon** au moment du tir, pas à 55 m.

**(b) Cause probable — confirmée, cause mécanique claire.**

Deux systèmes **indépendants** calculent chacun sa propre trajectoire, sans contrainte croisée entre eux :
- La position du joueur vient de `animation.motion._player_position_at` (`src/ligue1sim/animation/motion.py:224-231`), qui interpole entre les **keyframes scriptés du gabarit** (positions cibles définies par `templates.py`, indépendantes du ballon).
- La position du ballon vient de `animation.ball.ball_state_at` (`src/ligue1sim/animation/ball.py:481`), un modèle physique de trajectoire (passe/tir/centre) **indépendant** de la position du joueur.
- Le flag `is_ball_carrier` (`animation.motion.interpolate`, `src/ligue1sim/animation/motion.py:356-366`) vient de `_ball_carrier_at` (`motion.py:279-284`), qui lit `sequence.keyframes[idx].ball.owner_id` — un fait **narratif discret** (qui a le ballon à ce keyframe), **jamais recalculé ni contraint** par rapport à la position continue interpolée de ce joueur.

Rien dans ce pipeline n'impose "tant que `owner_id` == ce joueur, sa position doit rester à quelques dizaines de centimètres du ballon". Les deux trajectoires ne coïncident qu'AUX keyframes (par construction du gabarit), jamais entre deux keyframes, et rien ne garantit qu'elles restent proches après une transition de possession.

**(c) Sévérité** : **bloquant** pour l'objectif affiché du chantier (résumé "où le spectateur découvre le score en regardant") — le score/la minute/le buteur restent mécaniquement exacts (invariant respecté), mais la scène est visuellement incohérente au point de ne pas ressembler à une action de football.

**(d) Fichiers à modifier (identifiés, non touchés)** : `src/ligue1sim/animation/motion.py` (`_ball_carrier_at`, `_player_position_at`, `interpolate`) et/ou `src/ligue1sim/animation/ball.py` (`ball_state_at`) — c'est là que la coordination entre position joueur et position ballon devrait être imposée. Potentiellement aussi `src/ligue1sim/animation/templates.py` (calage des keyframes du porteur pendant une conduite de balle).

---

## Problème 4 — Clip tronqué avant le tir

**(a) Chiffres bruts** — 5 dernières frames du clip :
```
frame[251] t=8.367 ball=(0.9740, 0.9387, z=3.196) owner_id=home_cb0
frame[252] t=8.400 ball=(0.9754, 0.9493, z=3.241) owner_id=home_cb0
frame[253] t=8.433 ball=(0.9768, 0.9599, z=3.286) owner_id=home_cb0
frame[254] t=8.467 ball=(0.9782, 0.9705, z=3.331) owner_id=home_cb0
frame[255] t=8.500 ball=(0.9796, 0.9810, z=3.376) owner_id=home_cb0
```
`duration_s = 8.500` == `frames[-1].t = 8.500` (vérifié égal). `issue` déclarée pour ce clip : `'hors_cadre'`.

**(b) Cause probable — problème NON reproduit sur le clip 1, tel que demandé par les règles d'escalade.**

Les données ne montrent PAS de troncature : la dernière frame va bien jusqu'à `sequence.duration` (le correctif documenté du 24/09/2026 dans `narrative_player.py:293-301`, à propos de `duration_s = frames[-1].t`, semble tenir ici). Le ballon termine en `x≈0.98` (juste devant la ligne de but adverse), `y≈0.98` (très près de la touche haute, loin du centre du but `y=0.5`), `z≈3.38` (haut) — une trajectoire **cohérente avec `issue="hors_cadre"`** (tir cadré nulle part, au-dessus et large). L'action va donc bien jusqu'à une conclusion plausible sur ce clip précis.

**Hypothèse non confirmée** (à vérifier si le problème persiste sur d'autres clips) : ce que le propriétaire perçoit comme "l'action s'arrête avant le tir" pourrait être un **effet visuel du Problème 3** ci-dessus — le ballon final part dans une direction qui semble incohérente parce que le joueur censé le frapper (`#2`/`home_cb0`) en est à 55 m au moment du tir (voir Problème 3) : la scène finale peut donner l'impression d'un tir "fantôme", sans lien visible avec un joueur, ce qui peut se lire comme "l'action ne va pas à son terme" même si techniquement toutes les frames jusqu'à la fin déclarée sont bien jouées.

**(c) Sévérité** : **non confirmé sur ce clip** — pas de troncature mesurée. Ne pas traiter comme un problème séparé tant que l'hypothèse ci-dessus (symptôme du Problème 3) n'est pas testée sur un autre clip après correction du Problème 3.

**(d) Fichiers à modifier** : aucun identifié spécifiquement — voir Problème 3 si l'hypothèse se confirme.

---

## Ordre de correction suggéré (recommandation, non imposée)

1. **Problème 1 (band non transmis)** en premier — cause confirmée, fix localisé et de portée limitée (2 endroits précis identifiés : `narrative_player.py:140-143` et `sequence_generator.py:340-342`), aucune dépendance sur les autres problèmes, risque de régression faible (n'affecte que le placement de départ, pas les trajectoires actives ni l'invariant de score).
2. **Problème 3 (porteur/ballon désynchronisés)** ensuite — cause confirmée mais correction structurellement plus lourde (touche `motion.py`/`ball.py`, deux systèmes indépendants à faire coopérer) ; c'est le problème qui compromet le plus la crédibilité visuelle du résumé. Le corriger **avant** de rouvrir le Problème 4 : si l'hypothèse "Problème 4 = symptôme du Problème 3" est juste, une partie du travail de diagnostic du Problème 4 est déjà faite une fois le 3 traité.
3. **Problème 4** — revérifier après correction du Problème 3, sur plusieurs clips (pas seulement celui-ci), avant de décider s'il reste un problème distinct.
4. **Problème 2 (amplitude des figurants)** en dernier — déjà classé "mineur", déjà planifié dans un chantier dédié ("figurants actifs"), aucune urgence ni dépendance avec les 3 autres.
