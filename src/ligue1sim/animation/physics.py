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

BORNES DU TERRAIN (Phase 5, sous-étape 1, ticket 1 de docs/known_issues.md,
07/10/2026) : la correction est un suivi limité en accélération de la position
brute, SANS freinage anticipé : face à un SAUT de la trajectoire brute (3 à 8 m
en une image, ~4 % des joueurs d'un clip -- changement de segment des
gabarits), la vitesse monte, dépasse la cible, et un joueur peut dériver de
plusieurs dizaines de mètres, hors du terrain (mesuré sur 60 matchs : jusqu'à
~60 m, 115 cas sur 16 349 joueurs x clips ; aucune position brute ni sortie de
`motion._apply_avoidance` n'est hors [0, 1] -- l'hypothèse initiale du ticket
était inexacte). Paramètre optionnel `bounds` ((x_min, x_max), (y_min, y_max),
même unité que les positions) : par axe, la vitesse visée est plafonnée pour
qu'un arrêt à `a_max` reste possible avant le bord (vitesse max = sqrt((a_max
dt)^2 + 2 a_max d) - a_max dt, d = distance au bord). Le plafond d'accélération
est conservé ; loin des bords le comportement est inchangé. Secours : si la
contrainte vectorielle (norme de dv <= a_max dt) empêche de freiner sur deux axes
à la fois (coin), la position est ramenée dans les bornes et la composante
bloquée annulée -- cas rare qui peut dépasser a_max ponctuellement. `bounds=None`
(défaut) : aucun changement.

DETTE DE DUPLICATION (24/09/2026) : la même contrainte doit être appliquée
dans 3 autres scripts QA (`scripts/render_preview.py`,
`scripts/preview_motion.py`, `scripts/preview_background.py`) et les 5
boucles qui construisent une séquence de frames devraient être factorisées
en un seul point d'entrée. Pas fait ici (périmètre resserré aux 2 boucles
réellement utilisées par le propriétaire, `apps/streamlit_preview.py` mode
"gabarit" et `narrative_player._build_clip_frames`) -- à traiter dans un
brief dédié."""

from __future__ import annotations

import math

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


def _viable_component(velocity: float, position: float, low: float, high: float, a_max: float, dt: float) -> float:
    """Plafonne UNE composante de vitesse pour qu'un arrêt à `a_max` reste
    possible avant `low`/`high` (voir BORNES DU TERRAIN en tête de module)."""
    step = a_max * dt
    up = math.sqrt(step * step + 2.0 * a_max * max(high - position, 0.0)) - step
    down = math.sqrt(step * step + 2.0 * a_max * max(position - low, 0.0)) - step
    return min(max(velocity, -down), up)


def apply_acceleration_constraint(
    frames: list[dict],
    dt: float,
    a_max: float = _DEFAULT_A_MAX_M_S2,
    bounds: tuple[tuple[float, float], tuple[float, float]] | None = None,
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
    contraindre sans au moins un intervalle de temps.

    `bounds` (optionnel) : bornes du terrain, voir BORNES DU TERRAIN en tête
    de module."""
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
            if bounds is not None:
                raw_velocity = (
                    _viable_component(raw_velocity[0], prev_pos[0], bounds[0][0], bounds[0][1], a_max, dt),
                    _viable_component(raw_velocity[1], prev_pos[1], bounds[1][0], bounds[1][1], a_max, dt),
                )
            velocity = _clamp_velocity_change(prev_velocity, raw_velocity, max_delta_v)
            x = prev_pos[0] + velocity[0] * dt
            y = prev_pos[1] + velocity[1] * dt
            if bounds is not None:  # secours (coin) : voir BORNES DU TERRAIN
                if not bounds[0][0] <= x <= bounds[0][1]:
                    x, velocity = min(max(x, bounds[0][0]), bounds[0][1]), (0.0, velocity[1])
                if not bounds[1][0] <= y <= bounds[1][1]:
                    y, velocity = min(max(y, bounds[1][0]), bounds[1][1]), (velocity[0], 0.0)
            new_frame[player_id] = (x, y)
            new_velocity[player_id] = velocity
        corrected.append(new_frame)
        previous_velocity = new_velocity

    return corrected
