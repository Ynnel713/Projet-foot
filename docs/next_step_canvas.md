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
  puis ouvrir `http://localhost:8600` dans un navigateur. Un `st.selectbox`
  permet de choisir entre `decalage_enroulee`, `corner` et `contre_attaque`
  (brief "vertical slice validation", Tâche 4, 23/09/2026).

### Notes d'itération -- extension à 3 gabarits (Tâche 4)

Les 3 gabarits (`decalage_enroulee`, `corner`, `contre_attaque`) se sont
générés et affichés SANS modification du moteur ni de `render/canvas.html`
-- `FrameState`/`Sequence.roster` portaient déjà tout ce dont
`animation.serialize.frame_sequence_to_json` avait besoin pour les trois.
`scripts/render_preview.py` et `apps/streamlit_preview.py` ont juste reçu un
paramètre `template_name` (avant : constante figée à
`decalage_enroulee`) -- seul changement de code, hors moteur.

Ce qui a coincé (pas dans le rendu lui-même, dans l'outillage de capture de
screenshot pendant cette session) : le navigateur intégré de Claude ne
compose réellement le `<canvas>` (et donc `canvas.toDataURL()` ne renvoie
pas une image vide) que lorsque sa fenêtre est effectivement affichée à
l'écran -- `requestAnimationFrame` semble suspendu tant que le panneau
navigateur reste masqué derrière un autre panneau (diff, artifact...). Deux
captures faites sans amener le panneau au premier plan juste avant ont
donné des PNG entièrement noirs (canvas jamais dessiné). Correction :
toujours prendre un `screenshot` (qui force l'affichage réel) juste avant
d'extraire l'image via `toDataURL()`. Aucun rapport avec le code du projet
-- pas un bug à corriger ici, juste une note pour la prochaine session qui
génère des captures.

### Effet Magnus sur `decalage_enroulee` (brief "real Magnus effect", 23/09/2026)

Le tir de `decalage_enroulee` courbe désormais réellement (voir
`animation.ball._behavior_shot`/`_MAGNUS_K` et
`animation.templates._DECALAGE_ENROULEE_SHOT_SPIN_RAD_S = 50.0`) -- avant ce
brief, la "courbure" était un artefact géométrique sans lien avec le spin
(toujours 0.0, jamais lu), voir l'audit de la Tâche 3 du brief précédent.

**Où la voir à l'écran** : le segment `shot` de `decalage_enroulee` couvre
`t ∈ [2.4s, 6.0s]` (t_ratio 0.4 -> 1.0 sur une durée totale de 6.0s). La
courbure suit une parabole (fonction `_hat`, voir `ball.py`) : nulle au
départ (t=2.4s, sur la ligne droite passeur -> tireur), MAXIMALE à mi-tir
(**t=4.2s**, écart latéral ≈ 0.98 m sur la géométrie du fixture standard),
puis revient exactement à 0 à l'arrivée (t=6.0s, le ballon retombe pile sur
la position visée). Schéma textuel (vue de dessus, axe du tir horizontal) :

```
depart (t=2.4s)                                          arrivee (t=6.0s)
   o------.                                                        .------o
          `.                                                    ,'
            `.                                                ,'
              `-.                                          ,-'
                 `-.                                    ,-'
                    `--.  <- pic de courbure ~0.98m  ,--'
                        `--..              ..--'
                            `--..........--'   (t=4.2s, s=0.5)
```

Un seul screenshot statique (`decalage_enroulee.png`, capturé à t≈4.2s) ne
montre PAS la courbe elle-même (`render/canvas.html` ne dessine pas de
traînée) -- seule la position du ballon à cet instant précis, décalée de la
ligne droite passeur→tireur. Voir `docs/canvas_json_schema.md` pour la
source du champ `spin`.

### État des segments `shot` sur `corner`/`contre_attaque` (Tâche 3.3)

- **`corner`** : AUCUN segment tagué `shot` (son dernier segment est
  `deflect` depuis le brief "corner tags decision", 23/09/2026, voir
  `templates.py:669`) -- rien à laisser à `spin=0`, la question ne se pose
  pas pour ce gabarit.
- **`contre_attaque`** : A un segment `shot` (`templates.py:557`,
  `physics_tags=((0.4, "shot"),)`) -- laissé à `spin=0.0` (défaut de
  `build_from_template`, non touché) : tir parfaitement droit. À varier
  dans un brief séparé si un tir droit systématique sur ce gabarit devient
  visuellement monotone.

## Preuve visuelle Magnus

Brief "trajectory stroboscopic proof" (23/09/2026) -- `render/canvas.html`
ne dessine pas de traînée (choix de design assumé, non modifié), donc un
script séparé (`scripts/render_trajectory.py`, ne touche ni `ball.py`, ni
`templates.py`, ni `canvas.html`) trace la trajectoire réelle du ballon
échantillonnée à 10 instants sur `t ∈ [2.4s, 4.2s]` (première moitié du
segment `shot` de `decalage_enroulee`, telle que demandée par le brief).

- **Avec le spin réel** (50.0 rad/s) : [docs/previews/canvas/trajectory_decalage_enroulee.png](previews/canvas/trajectory_decalage_enroulee.png)
- **Avec spin forcé à 0** (comparaison) : [docs/previews/canvas/trajectory_straight_comparison.png](previews/canvas/trajectory_straight_comparison.png)

**Déviation max mesurée** (distance des points échantillonnés à la corde
reliant le premier et le dernier point) :
- spin=50.0 rad/s : **0.23 m**
- spin=0.0 (comparaison) : **0.00 m** (les points tombent exactement sur la
  corde, par construction)

La courbe est visiblement bombée par rapport à la ligne droite de référence
sur `trajectory_decalage_enroulee.png` (écart net, pas une nuance de
quelques pixels) ; `trajectory_straight_comparison.png` montre les 10
points parfaitement alignés. Les deux images confirment visuellement que le
Magnus agit.

Nuance à noter (transparence, pas un problème) : ce 0.23 m est mesuré sur
la fenêtre `t=2.4-4.2s` demandée par CE brief (corde plus courte que le
segment complet), différent du pic de ~0.98 m documenté plus haut (mesuré
par rapport à la corde du segment COMPLET `t=2.4-6.0s`, à son point milieu
t=4.2s) -- deux mesures légitimes, deux référentiels différents, aucune
contradiction : la fenêtre demandée ici ne couvre que la phase montante de
la courbe, avant son pic.
