# Schéma JSON -- rendu canvas (vertical slice)

Brief "canvas vertical slice" (23/09/2026), Tâche 1 -- document seul, aucun
code. Format produit par `frame_sequence_to_json` (Tâche 2, voir
`src/ligue1sim/animation/serialize.py`) et consommé par `render/canvas.html`
(Tâche 3). Sérialisé UNE FOIS en Python, embarqué tel quel dans le HTML --
le JS n'interroge jamais Python après coup (pas de streaming frame par
frame).

## Convention d'unités (une seule, explicite)

- `x`, `y` (joueurs ET ballon) : coordonnées **normalisées [0, 1]**, référentiel
  unique de `ligue1sim.pitch_geometry` -- origine bas-gauche, `x=0` ligne de
  but de l'équipe qui attaque (`team="scorer"`), `x=1` ligne de but adverse,
  `y=0`/`y=1` les deux touches. TOUTES les positions (joueurs des deux
  équipes, ballon) partagent ce MÊME référentiel -- aucun retournement par
  équipe, aucune conversion pixel côté Python (le JS projette lui-même vers
  le canvas, voir Tâche 3).
- `z` (ballon uniquement) : **MÈTRES**, pas normalisé -- seule exception à la
  convention [0,1] ci-dessus (voir `BallState.z`, `ligue1sim/animation/types.py`).
  `z=0.0` = au sol.
- `spin` (ballon) : rad/s.
- `t` (par frame), `duration`, temps en général : **secondes**, depuis le
  début de la séquence.

## Objet racine

```json
{
  "duration": 6.0,
  "fps_target": 30,
  "metadata": {
    "template": "decalage_enroulee",
    "teams": {
      "scorer":   {"name": "Paris Saint-Germain", "color_fill": "#004170", "color_outline": "#DA020E"},
      "opponent": {"name": "AS Monaco",            "color_fill": "#CC0000", "color_outline": "#FFFFFF"}
    }
  },
  "frames": [ /* voir "Par frame" ci-dessous */ ]
}
```

| Champ | Type | Champ source exact |
|---|---|---|
| `duration` | float, secondes | fourni par l'appelant via `metadata["duration"]` (Tâche 2) -- typiquement `Sequence.duration` |
| `fps_target` | int | fourni par l'appelant via `metadata["fps_target"]` -- le fps utilisé pour GÉNÉRER `frames` (pas une contrainte de lecture : le JS interpole en continu entre les timestamps réels, voir Tâche 3) |
| `metadata.template` | str | `metadata["template"]` -- typiquement `Sequence.meta["template"]` |
| `metadata.teams.<scorer\|opponent>.name` | str | `Lineup.club_name` de l'équipe correspondante |
| `metadata.teams.<scorer\|opponent>.color_fill` / `.color_outline` | str, hex `#RRGGBB` | `ligue1sim.kits.match_kit_colors(...)` |

## Par frame (`frames[i]`)

```json
{
  "t": 1.4,
  "players": [
    {"id": "11", "x": 0.62, "y": 0.48, "team": "scorer", "numero": 9, "active": true},
    {"id": "104", "x": 0.35, "y": 0.30, "team": "opponent", "numero": 4, "active": false}
  ],
  "ball": {"x": 0.65, "y": 0.50, "z": 0.0, "spin": 0.0}
}
```

| Champ | Type | Champ source exact |
|---|---|---|
| `t` | float, secondes | `FrameState.t` |
| `players[j].id` | str (converti, même convention que `Sequence.to_json()`) | clé de `FrameState.players` (`PlayerId = int \| str`) |
| `players[j].x` / `.y` | float, [0,1] | `PlayerMotionState.x` / `PlayerMotionState.y` |
| `players[j].team` | `"scorer"` \| `"opponent"` | `RosterEntry.team_side` -- **absent de `FrameState`**, transmis par l'appelant via `metadata["roster"][id]["team"]` (Tâche 2) |
| `players[j].numero` | int, 1-11 | `RosterEntry.numero` -- idem, via `metadata["roster"][id]["numero"]` |
| `players[j].active` | bool | `RosterEntry.role is not None` -- idem, via `metadata["roster"][id]["active"]` (`true` = actif/scripté par le gabarit, `false` = figurant/décor, voir `sequence_generator.enrich_with_background`) |
| `ball.x` / `.y` | float, [0,1] | `BallState.x` / `BallState.y` (`FrameState.ball`) |
| `ball.z` | float, **mètres** | `BallState.z` |
| `ball.spin` | float, rad/s | `BallState.spin` -- **désormais consommé côté moteur** (brief "real Magnus effect", 23/09/2026, Tâche 2) : `animation.ball._behavior_shot` le lit pour calculer la courbure d'un segment `shot` (effet Magnus, `a = k · spin · v`) ; ce champ du JSON reste la même valeur, purement informative pour le rendu (`render/canvas.html` ne l'utilise toujours pas -- inchangé) |

`PlayerMotionState.team`/`.numero`/`.role` n'existent pas : ces trois champs
vivent sur `Sequence.roster` (statique pour toute la séquence), pas sur
`FrameState` (qui varie par frame). `frame_sequence_to_json` ne reçoit pas la
`Sequence` -- l'appelant doit donc lui fournir cette jointure toute faite via
`metadata["roster"]` (voir la docstring de la fonction, Tâche 2). Ce n'est
PAS un champ du JSON produit (il n'apparaît que dans l'entrée Python) : le
JSON produit répète `team`/`numero`/`active` sur CHAQUE frame plutôt que de
les déduplique dans une section roster séparée -- volontairement, pour que
chaque frame soit autonome côté JS (pas de jointure à faire dans `canvas.html`).

## Non inclus dans ce slice

- **Orientation du joueur** (direction faciale) -- pas de champ, ni source ni
  sérialisé (voir `docs/next_step_canvas.md`, section Manquant).
- **État d'animation** (course/tir/tacle/idle...) -- idem, absent du moteur.
- **Caméra** -- vue top-down fixe uniquement, aucun paramètre de caméra.
- **Commentaire** (texte narratif de l'action) -- hors slice.
- **Vitesses** (`PlayerMotionState.vx`/`.vy`, `BallState.vx`/`.vy`/`.vz`) --
  non sérialisées : le JS interpole linéairement en position entre deux
  frames (Tâche 3), pas besoin d'une vitesse Python précalculée.
- **Porteur du ballon explicite** (`PlayerMotionState.is_ball_carrier`) --
  non sérialisé : la position du ballon (`ball.x`/`.y`) suffit au rendu, pas
  besoin de savoir QUI le porte pour ce premier jet.
- **11 des 12 gabarits** -- seul `decalage_enroulee` est câblé dans
  `scripts/render_preview.py`/`apps/streamlit_preview.py` (voir le retour de
  tâche pour la substitution de nom).
- **Streaming frame par frame** -- toute la séquence est sérialisée UNE FOIS
  en Python et embarquée dans le HTML ; le JS n'appelle jamais Python après
  coup.
