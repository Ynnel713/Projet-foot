"""Contrainte d'accélération maximale sur une trajectoire déjà interpolée
(brief "acceleration constraint on rendered frames", 24/09/2026, option D).

Option D (clarification architecturale de cette session) : `motion.
interpolate` est une fonction PURE, appelée ponctuellement, sans mémoire des
appels précédents (voir sa propre docstring, `tests/test_motion.py::
TestDeterminism`) -- la contrainte d'accélération est par nature
SÉQUENTIELLE (corriger la frame N exige de connaître la frame N-1 déjà
corrigée), elle ne peut donc pas vivre dans `interpolate` sans lui faire
perdre cette pureté. Elle vit ici, appliquée par les boucles qui PRODUISENT
une séquence ORDONNÉE de frames pour le rendu -- `motion.py`/`interpolate`
restent strictement intouchés.

Fonction PURE et autonome : positions en entrée, positions en sortie,
AUCUNE dépendance à `interpolate`/`templates`/aucun autre module interne de
ce projet (pas même `ligue1sim.pitch_geometry`). Unité GÉNÉRIQUE : `dt` et
`a_max` doivent être exprimés dans la même unité de distance que les
positions passées -- convertir en mètres avant l'appel (et reconvertir
après) reste la responsabilité de l'appelant, voir `narrative_player.
_build_clip_frames` et `apps/streamlit_preview.py::build_sequence_json`.

DETTE DE DUPLICATION (24/09/2026) : la même contrainte doit être appliquée
dans 3 autres scripts QA (`scripts/render_preview.py`,
`scripts/preview_motion.py`, `scripts/preview_background.py`) et les 5
boucles qui construisent une séquence de frames devraient être factorisées
en un seul point d'entrée. Pas fait ici (périmètre resserré aux 2 boucles
réellement utilisées par le propriétaire, `apps/streamlit_preview.py` mode
"gabarit" et `narrative_player._build_clip_frames`) -- à traiter dans un
brief dédié."""

from __future__ import annotations

_DEFAULT_A_MAX_M_S2 = 10.0  # acceleration humaine plausible pour un footballeur en pleine course

Frame = dict  # {player_id: (x, y)} -- alias documentaire, pas un vrai type generique (voir docstring : cle/unite au choix de l'appelant)


def _clamp_velocity_change(
    previous_velocity: tuple[float, float], raw_velocity: tuple[float, float], max_delta_v: float
) -> tuple[float, float]:
    """Ramène `raw_velocity` à au plus `max_delta_v` d'écart avec
    `previous_velocity` (norme du vecteur différence), en la déplaçant le
    long du segment qui les relie -- inchangée si déjà dans la limite."""
    dvx = raw_velocity[0] - previous_velocity[0]
    dvy = raw_velocity[1] - previous_velocity[1]
    magnitude = (dvx * dvx + dvy * dvy) ** 0.5
    if magnitude <= max_delta_v:
        return raw_velocity
    scale = max_delta_v / magnitude
    return (previous_velocity[0] + dvx * scale, previous_velocity[1] + dvy * scale)


def apply_acceleration_constraint(
    frames: list[dict], dt: float, a_max: float = _DEFAULT_A_MAX_M_S2
) -> list[dict]:
    """Parcourt `frames` (liste ORDONNÉE de `{player_id: (x, y)}`, un dict
    par instant, même pas de temps `dt` entre deux frames consécutives) et
    contraint, pour chaque joueur et chaque paire de frames consécutives à
    partir de la 3e, le changement de vitesse à au plus `a_max * dt` -- si
    la vitesse brute entre N-1 (DÉJÀ CORRIGÉE) et N impliquerait un
    changement plus grand que celle entre N-2 et N-1, la position de la
    frame N est ramenée à celle que cette vitesse plafonnée aurait produite.

    Les frames 0 ET 1 ne sont JAMAIS corrigées -- il faut au moins DEUX
    vitesses consécutives pour détecter un changement anormal (une seule
    vitesse, la toute première, n'a rien à quoi se comparer : la contraindre
    contre une vitesse initiale supposée nulle introduirait un démarrage en
    douceur ARTIFICIEL au tout début de chaque séquence, jamais demandé par
    le brief -- seules les DISCONTINUITÉS doivent être corrigées, pas le
    profil de vitesse normal d'un début de clip).

    Retourne une NOUVELLE liste (ne modifie jamais `frames` en place) ;
    `len(frames) < 2` ou `dt <= 0` : retournée telle quelle, rien à
    contraindre sans au moins un intervalle de temps."""
    if len(frames) < 2 or dt <= 0.0:
        return frames

    max_delta_v = a_max * dt
    corrected: list[dict] = [dict(frames[0]), dict(frames[1])]
    previous_velocity: dict = {
        player_id: ((frames[1][player_id][0] - pos0[0]) / dt, (frames[1][player_id][1] - pos0[1]) / dt)
        for player_id, pos0 in frames[0].items()
        if player_id in frames[1]
    }

    for i in range(2, len(frames)):
        raw_frame = frames[i]
        prev_frame = corrected[i - 1]
        new_frame: dict = {}
        new_velocity: dict = {}
        for player_id, raw_pos in raw_frame.items():
            prev_pos = prev_frame.get(player_id, raw_pos)
            raw_velocity = ((raw_pos[0] - prev_pos[0]) / dt, (raw_pos[1] - prev_pos[1]) / dt)
            prev_velocity = previous_velocity.get(player_id, raw_velocity)
            velocity = _clamp_velocity_change(prev_velocity, raw_velocity, max_delta_v)
            new_frame[player_id] = (prev_pos[0] + velocity[0] * dt, prev_pos[1] + velocity[1] * dt)
            new_velocity[player_id] = velocity
        corrected.append(new_frame)
        previous_velocity = new_velocity

    return corrected
