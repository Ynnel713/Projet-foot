# Inventaire des données pour le rendu canvas 2D

Brief "ball_owner=None debt" (23/09/2026), Tâche 4 -- constat seul, aucun
code ajouté. Pour chaque frame produite par `motion.interpolate(sequence, t)
-> FrameState`, ce qu'un rendu canvas 2D aura besoin de lire, et le champ
exact qui le porte.

`FrameState` (`animation/motion.py`) ne porte pas tout : certaines données
sont statiques pour toute la `Sequence` (numéro, équipe, rôle, nom, poste) et
vivent sur `Sequence.roster` (`animation/types.py`), pas sur `FrameState`
lui-même -- un rendu doit donc recevoir la `Sequence` (au moins son
`roster`) en plus du flux de `FrameState` par frame.

## Par joueur (`FrameState.players[player_id]`, `PlayerMotionState`)

- Position (x, y), normalisée [0,1] : `PlayerMotionState.x`, `PlayerMotionState.y`
- Vitesse (vx, vy), normalisée/seconde : `PlayerMotionState.vx`, `PlayerMotionState.vy`
- Porteur du ballon (bool) : `PlayerMotionState.is_ball_carrier`

## Par joueur (statique, `Sequence.roster[player_id]`, `RosterEntry`)

- Numéro (1-11) : `RosterEntry.numero`
- Équipe ("scorer" | "opponent") : `RosterEntry.team_side`
- Rôle actif/figurant : `RosterEntry.role` -- `None` = figurant (joueur
  "décor", suivi via `Sequence.background`, jamais mis en scène par le
  gabarit) ; une chaîne ("scorer", "assist", "support1"...) = actif (suivi
  via `Sequence.keyframes`, scripté par le gabarit). Équivalent structurel :
  `player_id in sequence.background` (figurant) vs `player_id in
  sequence.keyframes[0].players` (actif) -- invariant 3 de `Sequence`, les
  deux ensembles sont disjoints.
- Nom : `RosterEntry.nom`
- Poste : `RosterEntry.poste`

## Ballon (`FrameState.ball`, `BallState`)

- Position (x, y), normalisée [0,1] : `BallState.x`, `BallState.y`
- Hauteur z, en MÈTRES (pas normalisée, voir `BallState.z` docstring) : `BallState.z`
- Vitesse (vx, vy), normalisée/seconde, (vz) en m/s : `BallState.vx`, `BallState.vy`, `BallState.vz`
- Spin, rad/s (convention fixée le 23/09/2026, non consommée par le rendu actuel) : `BallState.spin`
- Porteur (`PlayerId` ou `None` si en l'air/disputé) : `BallState.owner_id`

## Autre

- Timestamp de la frame (secondes depuis le début de la séquence) : `FrameState.t`

## Manquant

- **Orientation/direction faciale du joueur** : aucun champ dédié sur
  `PlayerMotionState` ni `RosterEntry`. Approximable depuis `(vx, vy)`
  (`atan2(vy, vx)`) mais ce serait une dérivation côté rendu, pas une donnée
  du contrat -- non stubbé ici.
- **État d'animation du joueur** (course/tir/tacle/immobile...) : aucun
  champ, ni sur `FrameState` ni sur `Sequence`/`RosterEntry`.
- **Orientation du ballon** (axe de rotation) : `BallState.spin` est un
  scalaire (rad/s), pas un vecteur d'axe -- insuffisant pour animer la
  rotation visuelle du ballon lui-même (seulement sa vitesse de rotation
  autour d'un axe non spécifié).

## Vertical slice implémenté (brief "canvas vertical slice", 23/09/2026)

Voir `docs/canvas_json_schema.md` pour le format JSON exact. Un seul
gabarit câblé : `decalage_enroulee` (substitution de "frappe_enroulee",
demandé mais inexistant dans `animation.templates.BUILDERS` -- voir le
retour de tâche pour le détail).

- **Fichier canvas autonome** : `render/canvas.html` (placeholder
  `/*__SEQUENCE_JSON__*/null` remplacé par le JSON injecté).
- **Preview navigateur, sans Streamlit** :
  ```bash
  uv run python scripts/render_preview.py
  ```
  génère `render/canvas_preview.html`, ouvrable directement dans un
  navigateur (double-clic ou `file://...`).
- **Preview Streamlit** (fichier autonome, volontairement absent de
  `Lancer l'appli.bat` -- le propriétaire le lance manuellement) :
  ```bash
  uv run streamlit run apps/streamlit_preview.py --server.port 8600
  ```
  puis ouvrir `http://localhost:8600` dans un navigateur.
