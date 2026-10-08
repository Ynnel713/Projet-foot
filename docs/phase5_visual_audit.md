# Phase 5 — Audit visuel du rendu animé, cartographie du pipeline, proposition de découpage

Reconnaissance du **07/10/2026**, sur `HEAD` = `4ce6c0c`. **Aucun fichier de code n'a été modifié** : ce document est la référence de la Phase 5 (habillage visuel). Il remplace, pour le périmètre « rendu canvas », l'état des lieux de `docs/canvas_integration_state.md` (24/09/2026, antérieur à l'intégration PWA).

## 0. Méthode et limites

- **Sources** : lecture intégrale de `render/canvas.html` (575 lignes) ; lecture des modules du pipeline (§3) ; retour du 24/09/2026 = les **11 points de `docs/visual_backlog.md`** (statut « à faire » pour les 11) ; observations du 07/10/2026 dans la PWA (modale « Voir l'animation », Auxerre–Rennes, Ligue 1 journée 1).
- **Mesures** : toutes les dimensions en mètres sont **calculées** à partir des constantes du code et de l'échelle du terrain dessiné (§2.1) ; elles n'ont pas été relevées sur une capture. Les « px » sont des **pixels canvas** (canvas 1200 × 780) sauf mention contraire.
- **Échelle d'affichage** : le canvas est réduit par CSS (`max-width: 100%`, et en mode embarqué `max-height: calc(100vh - 150px)`). Dans la PWA, l'iframe occupe la largeur de la modale (`max-w-5xl`, ~1 000 px) sur une hauteur `min(80vh, 780px)` : l'échelle d'affichage est donc **au plus ~0,83**, et plus faible sur petite fenêtre (≈ 0,34 estimée sur une capture 800 × 450 du 07/10). Toute taille « en px » ci-dessous doit se lire à travers ce facteur.
- **Hors périmètre** : le terrain SVG de l'écran match (`ui/src/components/pitch/PitchField.jsx`) n'est pas le rendu animé ; il est cité seulement comme référence de cotes.
- **Capture de référence** : `docs/previews/canvas/player_clip1.png` est **périmée** (antérieure à plusieurs corrections, ex. « [object Object] » dans les événements intermédiaires) ; elle ne doit pas servir de baseline. Une baseline neuve est à produire au début de la sous-étape 5.1 (§4).

## 1. Baseline sur `git archive HEAD` propre (07/10/2026)

| Contrôle | Résultat obtenu | Attendu | Écart |
|---|---|---|---|
| `pytest tests --ignore=simulafoot_nlg` | `1044 passed, 5 skipped, 12 deselected in 127.17s` | 1044 verts | aucun |
| Suite NLG, depuis `simulafoot_nlg/` | `874 passed, 23 skipped in 84.37s` ; `TOTAL 881 2 99%` ; `Required test coverage of 85% reached. Total coverage: 99.77%` | 874 verts, 99,77 % | aucun |
| `npm run build` | `✓ 2279 modules transformed.` `✓ built in 799ms` ; PWA `precache 10 entries (503.53 KiB)` | OK | aucun |
| `npm run lint` | code de sortie 0 ; **0 erreur, 5 avertissements** `react(set-state-in-effect)` (`TeamRoster.jsx:35`, `PlayerPage.jsx:21`, `Simulation.jsx:55`, `CustomCompetition.jsx:348`, `PitchView.jsx:93`) | 0 erreur, 5 avertissements | aucun |

## 2. Audit visuel de `render/canvas.html`

Format de chaque entrée : **état actuel** — **réf. 24/09** (numéro du point de `visual_backlog.md`) — **écart constaté**.

### 2.1 Repère et géométrie du terrain

**Constat structurant (hors backlog du 24/09).** Le canvas fait 1200 × 780 px. Le terrain dessiné est un rectangle de **1160 × 740 px** (marge `MARGIN = 20`), soit un ratio 1,568 (FIFA 105/68 = 1,544) et une échelle de **11,05 px/m en x** et **10,88 px/m en y** (anisotropie de 1,5 %). Mais la projection des positions (`toPx(x, y) = [x·W, (1−y)·H]`, `canvas.html:151`) applique le repère normalisé [0, 1] à **tout le canvas**, pas au rectangle du terrain : `x = 0` (ligne de but) est tracé au pixel 0, alors que la ligne de but dessinée est au pixel 20. Le repère du moteur et le dessin sont donc **décalés de ~1,8 m** (x) et ~1,8 m (y) : un joueur sur sa ligne de but est dessiné 20 px **hors** du terrain, et le terrain dessiné ne correspond qu'à `x ∈ [0,0167 ; 0,9833]`, `y ∈ [0,0256 ; 0,9744]`. Ce décalage est une cause directe de l'aspect « hors limites » du ticket 1 et fausse toutes les comparaisons aux cotes réelles.

| Élément | Constantes dans `canvas.html` | Valeur dessinée | Cote FIFA | Écart | Réf. 24/09 |
|---|---|---|---|---|---|
| Terrain | `W × H` 1200 × 780, `MARGIN` 20 | 1160 × 740 px (ratio 1,568) | 105 × 68 m (1,544) | ratio +1,5 % ; échelle x/y inégale | 5 |
| Lignes (touche, but, médiane) | `lineWidth = 2`, blanc `#ffffff` | 2 px ≈ 18 cm (à l'échelle 1) | 12 cm | épaisseur proche ; **0,7 px** une fois réduit à 0,34 | 5 |
| Surface de réparation | `boxW = W×0,10`, `boxH = H×0,42` | **10,86 × 30,10 m** (10,3 % × 44,3 % du terrain) | 16,5 × 40,32 m (15,7 % × 59,3 %) | **−34 % en profondeur, −25 % en largeur** | 1 |
| Arc de cercle de la surface | **absent** | — | rayon 9,15 m, depuis le point de penalty, portion hors surface | **manquant** | 2 |
| Rond central | `arc(W/2, H/2, 70)` + point de 3 px | rayon 70 px = **6,34 m** (x) / 6,43 m (y) | 9,15 m | **−31 %** | 3 |
| Surface de but | `sixW = W×0,045`, `sixH = H×0,20` | **4,89 × 14,34 m** | 5,5 × 18,32 m | −11 % en profondeur, −22 % en largeur | 4 |
| Point de penalty | `spotDist = W×0,085`, disque de 3 px | **9,23 m** de la ligne | 11 m | −16 % | 5 |
| But (cage) | `goalW = H×0,12`, trait de 4 px sur la ligne de but | **8,60 m** de large, aucune profondeur ni poteaux | 7,32 m (2,44 m de haut, hors vue) | **+18 %** ; cage réduite à un trait | 5, 11 |
| Arcs de coin | **absents** | — | rayon 1 m | manquants | 5 |
| Ligne médiane | trait vertical pleine hauteur | conforme | — | aucun | — |

Les proportions dessinées sont des **fractions du canvas** (0,10 ; 0,42 ; 0,045 ; 0,20 ; 0,085 ; 0,12), jamais des mètres : aucune cote FIFA n'apparaît dans le fichier. Le terrain SVG de la PWA (`PitchField.jsx`) définit déjà ces cotes en mètres (`PEN_DEPTH = 16.5`, `PEN_WIDTH = 40.32`, `SIX_DEPTH = 5.5`, `SIX_WIDTH = 18.32`, `SPOT_DIST = 11`, `CIRCLE_R = 9.15`, `GOAL_WIDTH = 7.32`, `CORNER_R = 1`, arc de surface calculé) : c'est la **seule implémentation aux cotes FIFA relevée** dans le rendu du match, et une source de vérité candidate (voir §5, point 6).

### 2.2 Représentation des joueurs

| Aspect | État actuel (`drawFrame`, `canvas.html:227-255`) | Réf. 24/09 | Écart |
|---|---|---|---|
| Diamètre | rayon **9 px** (joueur) / **13 px** (« actif », rôle mis en scène) → 18 / 26 px, soit **1,6 m / 2,4 m** à l'échelle 1 ; ×0,34 à ×0,83 à l'écran | 6 | La référence FM est « ~12–14 px » : en pixels canvas c'est dépassé, **à l'affichage** (≈ 6 à 15 px) c'est comparable ou inférieur selon la fenêtre. Le critère « 12–14 px » est ambigu (canvas ou écran) : **à trancher** |
| Remplissage | `team.color_fill` (couleur primaire du club ; secondaire si les deux primaires sont trop proches, `kits._CLASH_THRESHOLD = 90`), aplat sans dégradé ni ombre | — | fidèle à l'identité du club ; pas de distinction de poste |
| Contour | `team.color_outline` (1 px) ; **joueur actif : `#ffd700`, 3 px** | — | l'actif est marqué par un anneau doré, pas par un autre signe |
| Numéro | `10px sans-serif` blanc, **sous** le rond (`y + rayon + 11`), sans contour ni fond ; numéro 1–11 **dérivé** de la compo (`templates.numeros_by_player_id`, pas un vrai numéro de maillot) | — | ~3 à 8 px à l'écran : **illisible à faible échelle** ; blanc sans liseré sur vert clair |
| Nom du porteur | **absent** (le payload ne transporte ni nom ni prénom : `serialize._frame_to_dict` n'émet que `id`, `x`, `y`, `team`, `numero`, `active`) | 7 | **manquant** ; nécessite le nom dans le payload ou le `main_player` du clip |
| Orientation faciale | **absente** (disque symétrique). `vx`/`vy` existent dans `motion.PlayerMotionState` mais ne sont pas sérialisés ; `state.PlayerState.direction_body` existe mais n'est pas utilisé par le chemin PWA | — | manquante ; déductible côté JS de deux frames successives |
| Ombre, halo | aucun | — | — |

### 2.3 Ballon

Disque blanc `#ffffff`, contour noir 1 px, rayon `5 + min(9, z × 3)` px où `z` est la hauteur en **mètres** (`BallState.z`) : 5 px au sol (**0,9 m de diamètre**, soit ~4 fois le ballon réel), jusqu'à 14 px (2,5 m) à 3 m de haut. Pas d'ombre au sol, pas de rotation visible (`spin` calculé, **jamais consommé** par le rendu), pas de traînée. Visibilité : bonne sur le vert (blanc/noir) mais, à l'échelle réduite, le ballon au sol (≈ 2 à 4 px) se confond avec le numéro d'un joueur proche. Aucun point du backlog du 24/09 ne porte sur le ballon.

### 2.4 Pelouse

Aplat uni `#1e824c` (CSS du `<canvas>` et `fillRect` de `drawPitch`), **sans rayures de tonte, sans texture, sans dégradé**, sans zone hors-jeu distincte (le fond autour du terrain est la même couleur sur 20 px). **Réf. 24/09 : point 8** (« vert plus profond et plus saturé + rayures tondeuse »). **Écart : intégral.** À titre de comparaison, `PitchField.jsx` utilise 18 bandes alternées `#2d8a4e` / `#26793f` sur fond `#1c5a30` : les deux terrains du produit n'ont ni la même teinte ni les mêmes bandes.

### 2.5 Bloc score

`<div id="scoreboard">` en HTML, positionné en absolu (`top: 10px`, centré), visible **uniquement en mode « player »** (donc dans la PWA). Contenu : `« <domicile> d – e <extérieur> | m' »`, texte seul (16 px, graisse 600, blanc), fond `rgba(0,0,0,0.45)`, `padding 4px 14px`, coins 4 px, `pointer-events: none`. Pas d'écussons, pas de couleurs d'équipe, pas de chronomètre qui défile : la minute affichée est **celle du clip courant**, figée pendant le clip (`updateScoreboard` à chaque `tick` mais sans changer de valeur). Il **chevauche le haut du terrain** (touche supérieure et ses joueurs). **Réf. 24/09 : point 9** (« bloc score / horloge compact en haut, style FM, position stable, à décliner canvas / Streamlit / PWA »). **Écart** : position stable, mais ni compact au sens FM, ni horloge, ni décliné ailleurs (`LivePanel` et `MatchHeader` de la PWA ont leur propre affichage, sans lien avec celui-ci).

### 2.6 Boutons de lecture

Mode « player » (PWA) : quatre boutons sous le canvas, `◀ ⏸/⏵ ↻ ▶` (précédent, lecture/pause, rejouer le clip, suivant), 15 px, fond `#1c1c1c`, bordure `#3a3a3a`, coins 4 px, survol `#2a2a2a` ; **pas** de contrôle de vitesse, pas de raccourci clavier, pas d'étiquette visible (info-bulles `title` seulement). Mode standalone « gabarit isolé » : deux boutons texte « Pause / Lecture » et « Recommencer » (14 px). **Réf. 24/09 : point 10** (« bandeau bas type lecteur vidéo : play/pause, précédent, suivant, progression »). **Écart** : les fonctions existent et sont regroupées sous le terrain, mais l'habillage n'est pas un bandeau intégré (boutons isolés sur fond noir de la page) et la barre de progression est séparée (§2.9).

### 2.7 Filets de but

**Absents.** Aucun dessin de filet, aucune animation au contact du ballon ; la cage est un trait de 4 px (§2.1). **Réf. 24/09 : point 11** (« filets animés au contact du ballon, grille + contraintes, chantier à part entière ; dépendance : moteur de rendu stabilisé »). **Écart : intégral**, et prérequis non levé (la géométrie des cages dépend de la sous-étape 5.1).

### 2.8 Éléments de match (cartons, remplacements, autres)

- **« Carton » intermédiaire** (`#carton`, overlay `rgba(0,0,0,0.72)` plein canvas, **2 s** — `CARTON_DURATION_S = 2.0`) : il s'agit d'une **carte de titre** entre deux temps forts, pas d'un carton d'arbitre. Contenu : minute (14 px), libellé (`BUT <équipe>` / `Penalty rate` / `Occasion <équipe>`, 20 px gras), score (28 px, 800), puis les événements intermédiaires de l'intervalle (jaunes, rouges, remplacements) en **lignes de texte** 13 px (`intervalEventLine`). Aucun pictogramme de carton jaune/rouge, aucune animation de remplacement, aucune célébration de but, aucun hors-jeu. Constaté dans la PWA le 07/10/2026 : « Occasion Stade Rennais FC / AJ Auxerre 0 – 0 Stade Rennais FC ».
- Pas de point du backlog du 24/09 sur ces éléments.

### 2.9 Timeline / barre de progression

`#progressBar` (mode « player » uniquement) : piste de 2 px (`#3a3a3a`), un marqueur circulaire de 10 px par clip (`#888`, survol `#aaa`), clip courant `#ffd700` de 13 px, position proportionnelle à la minute sur une échelle fixe 0–90 (`min(90, max(1, minute)) / 90`), clic = saut au clip. Pas d'étiquette de minute, pas de distinction but / occasion (couleur ou forme identiques), info-bulle `title` seulement. **Réf. 24/09 : point 10** (progression). **Écart** : présente et fonctionnelle, non habillée ; marqueurs rapprochés illisibles quand plusieurs occasions tombent à quelques minutes d'écart (observé : 20 marqueurs sur un match).

### 2.10 Écarts observés hors du retour du 24/09

1. **Repère décalé de la marge** (§2.1) : bloque la fiabilité de toute mesure de géométrie et explique en partie le ticket 1.
2. **Pas de borne des positions — diagnostic corrigé le 07/10/2026 (sous-étape 1).** La reconnaissance désignait `motion._apply_avoidance` ; la mesure (60 matchs, 5,67 M de positions) montre que **ni les positions brutes ni la sortie de `_apply_avoidance` ne sortent de [0, 1]** (0 cas). Les dépassements (jusqu'à ~60 m, 115 cas sur 16 349 joueurs × clips) naissaient dans `physics.apply_acceleration_constraint` : face à un saut de la trajectoire brute (3 à 8 m en une image, ~4 % des joueurs d'un clip), la contrainte poursuivait la cible sans freiner et la dépassait. Corrigé à la source : `physics.apply_acceleration_constraint` reçoit les bornes du terrain (`bounds`, passées par `narrative_player`) et plafonne la vitesse visée par axe pour qu'un arrêt à `a_max` reste possible avant le bord (freinage anticipé) ; le plafond d'accélération est conservé et le comportement loin des bords est inchangé. Les sauts de trajectoire brute eux-mêmes (changements de segment des gabarits) restent une dette amont, non traitée.
3. **Sens d'attaque** : chaque clip est exprimé dans le repère de l'équipe qui attaque (x vers le but adverse) : l'équipe à la manœuvre attaque **toujours vers la droite**, donc les deux équipes changent de côté d'un clip à l'autre. Le score, lui, est toujours affiché domicile–extérieur. Choix de lecture à arbitrer (§5), non couvert par le backlog.
4. **Lisibilité à l'échelle réduite** : lignes (2 px), numéros (10 px), ballon (5 px) sont dimensionnés pour l'échelle 1 ; en dessous de ~0,5 ils deviennent peu lisibles (§2.1, §2.2).
5. **Terrain dupliqué** : le canvas, `PitchField.jsx` (PWA), plusieurs scripts de prévisualisation Python (`scripts/preview_*.py`, tracé PIL) et `pitch_layout.py` (terrain vertical) définissent chacun leur propre terrain.

## 3. Cartographie du pipeline visuel

### 3.1 Flux de bout en bout (chemin réellement utilisé par la PWA)

```
Match joué + LineupSnapshot persisté
        │  api/animation.build_match_animation  (GET /api/competitions/{id}/animation)
        ▼
engine/narrative.match_result_from → build_timeline          # NarrativeEvent : minute, gabarit, zone, assist_zone, issue, outcome
        ▼
engine/narrative_player.build_clips                           # un Clip par événement retenu
   └─ _build_clip_frames :
        NarrativeEvent ──► GoalEvent (club, buteur, passeur, minute, zone, assist_zone)
        _lineup_start_positions(compo)  ──►  positions de départ (PitchPoint, repère normalisé)
        animation.templates.BUILDERS[gabarit](GoalEvent, compo, départ, outcome)
              ──► Sequence (keyframes : Keyframe{t, ball: BallState, players{id→(x,y)}, tag, physics_tag}, roster, meta)
        animation.sequence_generator.enrich_with_background   # 2e équipe + dérives tactiques des joueurs « de fond »
        boucle t = 0 … durée, pas 1/30 s :  animation.motion.interpolate(Sequence, t)
              ──► FrameState{t, players{id→PlayerMotionState(x,y,vx,vy,is_ball_carrier)}, ball}   (animation.ball.ball_state_at pour le ballon)
        _apply_acceleration_constraint_to_frames (animation.physics, a_max = 10 m/s²)
        ▼
engine/narrative_player.clips_to_json                         # + animation.serialize.frame_sequence_to_json + kits.match_kit_colors
        ──►  JSON : [ { duration, fps_target, metadata{template, teams{scorer,opponent}, minute, issue, score_*, interval_events, home_team, away_team},
                         frames[{t, players[{id,x,y,team,numero,active}], ball{x,y,z,spin}}] } ]
        ▼
api/animation → réponse {version:1, available:true, match, clips}
        ▼
ui/src/utils/matchAnimation.js (buildAnimationPayload) → ui/src/components/pitch/MatchAnimation.jsx
        ──► <iframe src="/render/canvas.html?embed=1&parent_origin=…"> + postMessage « init » (protocole v1)
        ▼
render/canvas.html :  startPlayer(clips, bridge) → tick() → drawFrame(clip, t) → drawPitch() + joueurs + ballon   [Canvas 2D, requestAnimationFrame]
                      + HTML : #scoreboard, #carton, #playerControls, #progressBar
```

Écarts avec le schéma attendu `GoalEvent → sequence_generator → Sequence/Keyframe → canvas.html` : **`sequence_generator.generate_sequence` n'est pas appelé** par ce chemin (il ne subsiste que des références en docstring ; il sert à l'ancien chemin « but isolé »). Le chemin PWA passe par `templates.BUILDERS` et n'utilise de `sequence_generator` que `enrich_with_background` (équipe adverse et dérives). `animation/state.py` (`PlayerState`, `direction_body`) n'est importé par aucun module hors tests.

### 3.2 Où est calculé chaque élément

| Élément | Où | Remarque |
|---|---|---|
| Positions des joueurs (repère normalisé [0,1]) | départ : `narrative_player._lineup_start_positions` (via `pitch_layout`), équipe adverse : `sequence_generator._opponent_positions` ; trajectoires : `templates.*` + `motion.interpolate` ; évitement : `motion._apply_avoidance` (1,5 m) ; accélération : `physics` | pas de borne à [0, 1] (§2.10) |
| Position du ballon (x, y, z m) | `animation.ball.ball_state_at` (tags `pass_ground`, `pass_lob`, `shot`, `cross`, `deflect`, `ball_flight`) | `spin` non consommé |
| Cage / buts | `templates` (`_GOAL_Y_CENTER = 0,5`, `_GOAL_HALF_WIDTH_Y = 3,66/68`) ; dessin : `canvas.html:196-205` | cage de 7,32 m côté moteur, 8,6 m côté dessin |
| Lignes du terrain | **`canvas.html:159-206` (`drawPitch`) uniquement** | constantes en fractions du canvas |
| Conversion repère → pixels | **`canvas.html:151` (`toPx`)** (JS) ; côté Python `pitch_geometry.to_canvas_px` (même convention, utilisée par les scripts de prévisualisation) | pas de prise en compte de `MARGIN` |
| Couleurs d'équipe | `kits.CLUB_KIT`, `kits.match_kit_colors` → `metadata.teams` | une seule paire fond/contour par équipe et par clip |
| Numéros | `templates.numeros_by_player_id` → `roster[].numero` | dérivés, 1–11 |
| Tailles, polices, couleurs (rayons 9/13, `#ffd700`, `10px sans-serif`, ballon, scoreboard, boutons, carton) | **`canvas.html`** (CSS lignes 6-69 et JS 227-276) | littéraux en dur, aucune constante nommée sauf `MARGIN`, `CARTON_DURATION_S` |
| Cadence, durée des clips | `narrative_player._FPS = 30` ; durée issue du gabarit | |
| Taille d'affichage | `canvas.html` (CSS `max-width`, `body.embed canvas`) ; PWA : `MatchAnimation.jsx` (`height: min(80vh, 780px)`), `PitchView.jsx` (`max-w-5xl`) | |

### 3.3 Variables de configuration actuelles

- **`canvas.html`** : `canvas width/height` 1200 × 780 (attributs), `MARGIN = 20`, `CARTON_DURATION_S = 2.0`, `DEBUG` (`?debug=1`), `EMBED` (`?embed=1`), fractions de la géométrie (0,10 ; 0,42 ; 0,045 ; 0,20 ; 0,085 ; 0,12), rayon du rond central (70 px), rayons joueurs (9/13), formule du rayon du ballon, couleurs en littéraux.
- **Python** : `pitch_geometry` (`PITCH_LENGTH_M = 105`, `PITCH_WIDTH_M = 68`, `CANVAS_WIDTH_PX = 1200`, `CANVAS_HEIGHT_PX = 780`, grille 12 × 8), `motion` (`MAX_SPEED_MPS`, `_AVOIDANCE_TRIGGER_M`, `_AVOIDANCE_PASSES`), `physics` (a_max 10 m/s²), `ball` (hauteurs et courbures), `sequence_generator` (dérives tactiques), `kits` (`CLUB_KIT`, `_CLASH_THRESHOLD = 90`).
- **`canvas.html` contient tout le tracé** (terrain, joueurs, ballon, scoreboard, boutons, barre, carton) ; il ne reçoit du Python que des **positions normalisées**, les couleurs d'équipe, les numéros et les métadonnées narratives (`docs/canvas_json_schema.md`). `engine/`, `render/`, `src/ligue1sim/animation/` fournissent les **données** ; aucun dessin n'y est fait (hors scripts de prévisualisation PIL).
- **Garde-fous existants** à respecter par tout changement de `canvas.html` : `tests/test_canvas_html.py` fige par **chaînes de texte** le contrat d'injection du mode standalone (`const SEQUENCE_DATA = /*__SEQUENCE_JSON__*/null;`, le bloc `if (!EMBED) { … startPlayer(SEQUENCE_DATA, null);`), le protocole fermé (4 messages sortants, `init` entrant), l'absence de `'*'`, et la seule règle CSS propre au mode embarqué (`body.embed canvas`). `tests/test_canvas_e2e.py` couvre la chaîne JSON mais pas le rendu navigateur (aucun test de rendu visuel n'existe).

## 4. Proposition de découpage de la Phase 5 (non exécutée)

Cinq sous-étapes, chacune commitable et testable seule, dans l'ordre des dépendances. Les noms de fichiers sont des **fichiers probables**, à confirmer à l'exécution.

### Sous-étape 5.1 — Géométrie du terrain, repère de projection et ticket 1

- **Périmètre** : (a) rendre `toPx` conforme au rectangle du terrain (repère [0,1] → terrain dessiné, marge hors terrain) ; (b) redessiner `drawPitch` en **mètres** aux cotes FIFA (surface 16,5 × 40,32 ; surface de but 5,5 × 18,32 ; penalty 11 m ; rond central 9,15 m ; arc de surface ; arcs de coin 1 m ; cage 7,32 m) avec une échelle unique x/y ; (c) traiter le **ticket 1** : borner les positions (écrêtage à [0, 1] ou à la marge voulue) à l'endroit retenu (§5), plus un test déterministe.
- **Fichiers probables** : `render/canvas.html` (`drawPitch`, `toPx`) ; selon l'arbitrage du ticket 1, `src/ligue1sim/animation/motion.py` ou `engine/narrative_player.py` (écrêtage) ; `tests/test_canvas_html.py` (constantes de géométrie en chaînes), nouveau test de bornes ; `docs/canvas_json_schema.md` (si le repère change).
- **Critères d'acceptation** : sur le terrain dessiné, surface de réparation = 15,7 % × 59,3 % du terrain ; surface de but = 5,2 % × 26,9 % ; rond central = 8,7 % de la longueur ; point de penalty à 10,5 % ; arc de surface présent (rayon 9,15 m) ; cage = 10,8 % de la largeur ; un joueur ou le ballon à `x = 0` ou `x = 1` tombe **sur** la ligne de but dessinée ; **aucun joueur hors de la marge** sur le jeu de matchs de `test_substitute_placed_correctly` (ticket 1 fermé) ; contrat standalone et protocole de `test_canvas_html.py` inchangés.
- **Vérification** : baseline neuve **avant** (capture du même clip, mêmes données, dans `docs/previews/phase5/`) puis après ; relevé numérique des constantes par `javascript_tool` sur une page de preview (positions des lignes en px converties en %) ; test statique des constantes ; `pytest` (1044) + build + lint inchangés ; rejouer le test d'intégration `test_substitute_placed_correctly` (12 tests `integration`) et rapporter le résultat.

### Sous-étape 5.2 — Joueurs et ballon

- **Périmètre** : ronds (taille et rapport à l'échelle d'affichage), contour et lisibilité du numéro (liseré, taille ajustée au facteur d'échelle), **nom du porteur** sous son rond, **orientation faciale**, ballon (taille réaliste, ombre au sol, éventuel traitement de la hauteur).
- **Fichiers probables** : `render/canvas.html` (`drawFrame`) ; pour le nom : `src/ligue1sim/animation/serialize.py` et `engine/narrative_player.py` (`roster_meta`) + `docs/canvas_json_schema.md` si le nom passe dans le payload (alternative sans changement de données : utiliser `metadata.main_player` du clip) ; l'orientation se déduit côté JS de deux frames successives (aucun changement de données) ; `tests/test_canvas_html.py`, `tests/test_serialize.py`.
- **Critères d'acceptation** : à l'échelle d'affichage nominale de la PWA, diamètre d'un joueur dans la plage retenue (FM : ~12–14 px, à arbitrer §5) ; numéro lisible à 0,5 d'échelle ; nom du porteur affiché sous son rond et lisible ; orientation visible sur un joueur en mouvement et stable à l'arrêt ; poids du payload non dégradé (mesure avant/après, voir ticket 4).
- **Vérification** : captures avant/après du même clip à deux échelles (0,83 et 0,5) ; mesure du diamètre en px d'écran sur capture ; comparaison du poids du payload d'un match (`curl`, taille) ; tests statiques ; `pytest` + build + lint.

### Sous-étape 5.3 — Environnement du match : pelouse, bloc score, bandeau de lecture

- **Périmètre** : pelouse (vert plus profond et plus saturé, bandes de tonte perpendiculaires à la longueur), bloc score compact en haut (noms, score, minute, position stable), bandeau de lecture bas regroupant boutons et barre de progression.
- **Fichiers probables** : `render/canvas.html` (CSS et `drawPitch` pour les bandes, `#scoreboard`, `#playerControls`, `#progressBar`) ; `tests/test_canvas_html.py` ; `ui/src/components/pitch/PitchField.jsx` seulement si l'on veut harmoniser les verts (lecture seule d'abord).
- **Critères d'acceptation** : bandes alternées visibles sans bruit sur les lignes ; contraste ligne/pelouse et joueurs/pelouse mesuré (ratio de contraste) ; bloc score ne recouvre plus la touche supérieure ni les joueurs ; bandeau aligné sur la largeur du terrain ; fonctions de lecture inchangées (précédent, pause, rejouer, suivant, saut par marqueur) ; mode standalone « gabarit isolé » inchangé fonctionnellement.
- **Vérification** : captures avant/après ; mesure des couleurs par `getImageData` (teintes des deux bandes) ; essai manuel des 4 boutons et du clic sur marqueur dans le navigateur intégré ; `pytest` + build + lint.

### Sous-étape 5.4 — Effets animés : filets de but (et autres effets)

- **Périmètre** : filets (grille et contraintes, animation à l'impact du ballon), éventuellement un effet de but (célébration) et un habillage des cartes d'événements si retenu. **Dépend de 5.1** (géométrie de la cage) et d'un moteur de rendu stable.
- **Fichiers probables** : `render/canvas.html` (nouvelle fonction de dessin et d'animation des filets) ; éventuellement `src/ligue1sim/animation/ball.py` si l'instant d'impact doit être exposé (à éviter : l'instant se déduit des frames) ; tests statiques.
- **Critères d'acceptation** : filet visible derrière la ligne de but ; déformation visible à l'impact d'un tir cadré, retour au repos en moins de ~1 s ; aucun effet sur les occasions sans but ; 30 images/s tenues (mesure).
- **Vérification** : enregistrement de clips avant/après (GIF via le navigateur) ; mesure du temps de dessin par frame (`performance.now`) sur un clip chargé ; `pytest` + build + lint.

### Sous-étape 5.5 — Cohérence multi-surfaces et sens d'attaque (conditionnelle)

- **Périmètre** : décliner le bloc score et les couleurs sur les autres surfaces (écran match PWA, Streamlit si maintenu), unifier les constantes de terrain entre `canvas.html` et `PitchField.jsx`, et, **si le propriétaire le décide**, afficher chaque équipe toujours du même côté (miroir du repère pour les clips de l'équipe extérieure).
- **Fichiers probables** : `render/canvas.html`, `ui/src/components/pitch/PitchField.jsx`, `ui/src/routes/PitchView.jsx` (composant interne `MatchHeader`), `apps/streamlit_preview.py` selon l'arbitrage ; tests statiques.
- **Critères d'acceptation** : mêmes proportions de terrain et mêmes verts sur toutes les surfaces ; si le miroir est retenu, une équipe attaque toujours dans le même sens sur l'ensemble d'un match et le score reste lisible ; aucune régression du protocole.
- **Vérification** : captures comparées des deux surfaces ; test statique égalisant les constantes ; `pytest` + build + lint.

## 5. Points à arbitrer avant d'exécuter

1. **Mode standalone et modification de `canvas.html`.** `drawPitch`, `toPx` et `drawFrame` sont **partagés** par le mode standalone et le mode embarqué : toute correction de géométrie ou d'habillage change aussi le rendu du standalone, même si son contrat d'injection (figé par `test_canvas_html.py`) reste intact. Faut-il (a) appliquer les changements aux deux modes (recommandé : un seul rendu, sans branchement), ou (b) les réserver au mode embarqué par un test sur `EMBED` ? La consigne « standalone intact » vaut pour cette reconnaissance ; la porter à la Phase 5 demande une décision.
2. **Lieu de l'écrêtage du ticket 1** : moteur (`motion.py` ou `narrative_player.py`, comportement des frames) ou rendu (`canvas.html`, simple borne à l'affichage). Le premier corrige à la source mais touche le moteur de rendu ; le second est local mais masque l'écart dans les données.
3. **Critère « ronds de 12–14 px »** : pixels canvas ou pixels d'écran à l'échelle nominale ?
4. **Nom du porteur** : changement de payload (`serialize.py`, `docs/canvas_json_schema.md`) ou réutilisation de `metadata.main_player` (aucun changement de données, mais un seul nom par clip) ?
5. **Sens d'attaque** (§2.10, point 3) : conserver « l'équipe à la manœuvre attaque vers la droite » ou imposer un côté fixe par équipe (sous-étape 5.5).
6. **Source de vérité des cotes** : reprendre les constantes de `PitchField.jsx` (copie dans `canvas.html`, qui doit rester autonome, avec test d'égalité) ou ajouter les cotes FIFA à `pitch_geometry.py` et les injecter.
7. **Baseline visuelle** : la capture `docs/previews/canvas/player_clip1.png` est périmée ; valider la création de `docs/previews/phase5/` (images ajoutées au dépôt) comme référence avant/après.

## 6. État des tickets liés

Ticket 1 (joueur hors de la marge) : traité par la sous-étape 5.1, **non corrigé** à ce jour. Tickets 2, 3, 4, 6, 9, 10 et 11 : sans lien direct avec le rendu ; le ticket 4 (latence et poids du payload) est à surveiller pour toute sous-étape qui enrichit le payload (5.2).

## 7. Écart entre `narrative_player` et `sequence_generator` (documenté le 07/10/2026, **non corrigé**)

**Constat.** Deux orchestrations coexistent pour passer d'un événement à une `Sequence` :

| | `engine/narrative_player._build_clip_frames` (chemin de la PWA) | `animation/sequence_generator.generate_sequence` |
|---|---|---|
| Entrée | `NarrativeEvent` (gabarit **déjà choisi** par `engine/narrative.py`) converti en `GoalEvent` | `GoalEvent` + `PitchLayoutState` + `MatchState` + `rng` |
| Positions de départ | `_lineup_start_positions` (+ `_substitute_start_position`) | `_start_positions` (via `pitch_layout`) |
| Choix du gabarit | aucun (hérité de la timeline) | `templates.pick_template(context, rng)` |
| Exécution | `BUILDERS[gabarit](...)` puis `enrich_with_background` (adversaire et dérives) | `BUILDERS[nom](...)` ; ajoute `match_id`/`event_index` à `meta` |
| Appelé par | `build_clips` → `api/animation` (**production**) | **uniquement des tests** (`tests/test_sequence_generator.py`, `tests/test_lineup_snapshot.py`) ; aucune référence hors docstrings dans `src/`, `engine/`, `api/`, `apps/`, `scripts/` |

**Impact.** *Maintenance* : la logique de départ des joueurs et d'exécution des gabarits existe deux fois ; un correctif sur l'une n'atteint pas l'autre (le diagnostic du 24/09, `docs/render_diagnostic.md`, a déjà dû corriger le même oubli de `band` à deux endroits). *Cohérence* : la suite de tests de `generate_sequence` (11 appels) ne couvre pas le chemin réellement utilisé par la PWA ; une régression de production peut passer au vert. *Lisibilité* : la docstring de `animation/__init__.py` présente `generate_sequence` comme point d'entrée, ce qui est faux pour le produit.

**Pistes (non appliquées, à arbitrer).** (1) Déclarer officiellement `narrative_player._build_clip_frames` comme chemin de production, marquer `generate_sequence` obsolète (docstring) puis le retirer avec ses tests si aucun usage n'est confirmé. (2) Ou extraire l'orchestration commune (positions de départ, exécution du gabarit, `enrich_with_background`) dans une fonction unique appelée par les deux. (3) Dans les deux cas, ajouter un test de non-divergence sur un événement donné. Aucun code modifié par cette note.

## 8. Avancement

- **Sous-étape 1 (géométrie FIFA, repère, ticket 1)** : réalisée le 07/10/2026 ; baseline avant/après dans `docs/previews/phase5/sous_etape_1/`. Décisions d'architecte appliquées : correctifs communs aux deux modes de `canvas.html`, cotes dans `pitch_geometry.py` (source unique), ticket 1 corrigé à la source (cause réelle : `physics.py`, voir §2.10). Mesures : 0 position hors [0, 1] sur 100 matchs après correctif (contre jusqu'à ~60 m de dépassement avant) ; clip de preview (seed 26) : 112 positions hors terrain avant, 0 après, 5 joueurs × clips modifiés. Fichiers hors liste initiale, nécessaires : `engine/narrative_player.py` (1 appel : passage de `bounds`), `ui/src/utils/pitchGeometry.json` (JSON dérivé de `pitch_geometry.py`), `tests/test_physics.py`.
- **Sous-étape 2 (joueurs et ballon)** : réalisée le 07/10/2026 ; baseline dans `docs/previews/phase5/sous_etape_2/`. Ronds à 14 px **écran** (conversion canvas par la largeur affichée, indépendante du device pixel ratio ; le joueur « actif » garde son rapport 13/9, soit ~20 px), numéro centré (58 % du diamètre, couleur contrastée), nom du porteur sous son rond (tant que le ballon est à terre et à moins de 3 m ; source `metadata.player_names`, gate `metadata.main_player`), cap en triangle déduit de deux images consécutives, ballon de 6 px écran avec ombre au sol et élévation en vol. Payload enrichi à la source (`engine/narrative_player.py`) : `ball.owner` par image et `metadata.player_names` (+0,74 % de poids sur 4 clips). Points §2.2 (diamètre, numéro, nom, orientation) et §2.3 (ballon) traités ; points 6 et 7 du backlog du 24/09 clos pour le canvas. Nouveau ticket 12 (sauts de trajectoire amont).
- **Sous-étape 3 (pelouse, bloc score, bandeau de lecture)** : réalisée le 08/10/2026 ; baseline dans `docs/previews/phase5/sous_etape_3/`. Pelouse à 9 bandes horizontales (68 / 9 = 7,6 m) en deux verts (`#1e824c` / `#1e8650`, écart de luminance 6,8 %) ; bloc score fixe 26 px de haut (abréviations à 3 lettres, score, minute ; 0 chevauchement de joueur mesuré sur 1 329 images aux échelles 0,56 et 0,83) ; bandeau de lecture de 52 px sous le terrain (lecture/pause, précédent, suivant, rejouer, barre de progression, compteur « Clip N / M »), buts = cercles blancs, occasions = losanges gris. Points 8, 9 et 10 du backlog du 24/09 traités pour le canvas. Limite connue (préexistante) : l'axe de la barre est fixé à 0–90 min, des clips rapprochés dans le temps ont des marqueurs qui se touchent ; les buts sont affichés au-dessus des occasions.
