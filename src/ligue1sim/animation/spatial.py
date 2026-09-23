"""Passerelle entre le référentiel de `pitch_layout.py` (terrain vertical,
x=latéral/y=profondeur en 0-100) et le référentiel normalisé partagé
`ligue1sim.pitch_geometry` (x=progression vers le but adverse, y=latéral,
0-1) -- c'est le seul besoin résiduel réel de ce module (voir "NOTE ARCHI"
plus bas pour l'historique).

Les conversions normalisé <-> pixels et la grille de zones (`zone_of`,
`center_of`, `zones_in_third`) sont RÉ-EXPORTÉES depuis
`ligue1sim.pitch_geometry` pour rester accessibles depuis ce module (import
`ligue1sim.animation.spatial.zone_of` fonctionne), mais leur implémentation
réelle vit dans `pitch_geometry.py` -- un module PARTAGÉ avec `events.py`,
qui ne doit jamais dépendre d'`animation/` (voir invariant 1,
docs/simulation_physique_archi.md). Ne pas dupliquer cette logique ici.

NOTE ARCHI (22/09/2026) : ce module portait auparavant `SpatialEvent`/
`build_spatial_event`, pensés pour associer une zone d'origine/de
conclusion à un événement. Supprimés -- leur rôle est entièrement absorbé
par `templates.py`, qui utilise directement `event.zone`/`event.assist_zone`
(déjà calculés par `events.py`) comme ancrages de rôle, sans jamais avoir eu
besoin de `SpatialEvent`. Voir docs/simulation_physique_archi.md pour
l'historique complet de cette décision.
"""

from __future__ import annotations

from dataclasses import dataclass

# ATTENTION avant de chercher zone_of/center_of/... ailleurs : leur CODE vit
# dans pitch_geometry.py, pas ici. Ce bloc ne fait que les RÉ-EXPORTER pour
# qu'ils restent importables via `animation.spatial` -- si tu modifies leur
# comportement, c'est dans pitch_geometry.py qu'il faut le faire.
from ligue1sim.pitch_geometry import (  # noqa: F401 -- ré-export volontaire, voir docstring de module
    CANVAS_HEIGHT_PX,
    CANVAS_WIDTH_PX,
    GRID_COLUMNS,
    GRID_ROWS,
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    THIRD_ATTACKING,
    THIRD_DEFENSIVE,
    THIRD_MIDDLE,
    PitchPoint,
    Zone,
    center_of,
    to_canvas_px,
    zone_of,
    zones_in_third,
)
from ligue1sim.pitch_layout import PlacedPlayer


@dataclass(frozen=True)
class PitchLayoutState:
    """Un XI déjà placé par `pitch_layout.place_starting_xi`, avec le sens
    d'attaque qui a servi à ce placement -- le bundle minimal nécessaire
    pour convertir vers le référentiel normalisé (voir
    `placed_player_to_normalized`). `attacking_up` doit être la même valeur
    que celle passée à `place_starting_xi` pour produire `placed_players`."""

    placed_players: tuple[PlacedPlayer, ...]
    attacking_up: bool


def placed_player_to_normalized(placed: PlacedPlayer, *, attacking_up: bool) -> PitchPoint:
    """Convertit la position d'UN `PlacedPlayer` (référentiel `pitch_layout`,
    x=latéral/y=profondeur en 0-100) vers le référentiel normalisé
    (x=progression vers le but adverse, y=latéral, 0-1).

    `pitch_layout.y` code déjà la profondeur (0=haut de l'écran, 100=bas) ;
    le sens de progression dépend du côté attaqué par cette équipe
    (`attacking_up`, même paramètre que celui passé à `place_starting_xi`) :
    une équipe qui attaque vers le HAUT (`attacking_up=True`) progresse
    quand `y` DIMINUE (son but est en bas, y≈90-100) ; une équipe qui
    attaque vers le BAS progresse quand `y` AUGMENTE (son but est en haut,
    y≈0-10). `pitch_layout.x` (latéral, indépendant du sens d'attaque) se
    reporte tel quel sur l'axe y normalisé (latéral lui aussi) -- une simple
    mise à l'échelle, sans inversion.

    Transformation purement linéaire, donc exactement inversible -- voir
    `normalized_to_placed_player_xy` et `tests/test_spatial.py` pour la
    vérification de bijectivité."""
    progression = (1.0 - placed.y / 100.0) if attacking_up else (placed.y / 100.0)
    lateral = placed.x / 100.0
    return PitchPoint(x=progression, y=lateral)


def normalized_to_placed_player_xy(point: PitchPoint, *, attacking_up: bool) -> tuple[float, float]:
    """Inverse exacte de `placed_player_to_normalized` -- reconstruit les
    `(x, y)` `pitch_layout` (0-100) à partir d'un point normalisé. Existe
    surtout pour prouver et tester la bijectivité de la conversion ;
    utilisable aussi pour réafficher une position calculée dans le
    référentiel normalisé sur la vue "stade" existante (`pitch_layout`/
    `app.py`), si un jour nécessaire."""
    y = (1.0 - point.x) * 100.0 if attacking_up else point.x * 100.0
    x = point.y * 100.0
    return x, y
