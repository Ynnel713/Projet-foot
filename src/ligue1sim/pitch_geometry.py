"""Référentiel spatial normalisé, partagé par le moteur (ligue1sim.events)
ET la couche d'habillage visuel (ligue1sim.animation) -- volontairement un
module à part, sans dépendance vers ni l'un ni l'autre, pour que ni
`events.py` ne dépende de `animation/` (l'habillage doit rester supprimable
sans rien casser), ni l'inverse.

--- Référentiel de coordonnées -----------------------------------------

x, y ∈ [0, 1], origine au coin BAS-GAUCHE, axe x orienté vers le BUT
ADVERSE -- donc relatif au sens d'attaque de l'équipe qui a le ballon, pas à
un côté fixe de l'écran (même principe que `pitch_layout.attacking_up`, qui
gère déjà ce retournement pour l'affichage statique). x=0 : ligne de but de
l'équipe qui attaque ; x=1 : ligne de but adverse. y=0 : touche "basse" ;
y=1 : touche "haute".

Ce référentiel est INDÉPENDANT de celui de `pitch_layout.py` (terrain
vertical, x=latéral/y=profondeur en 0-100) -- toute conversion entre les
deux doit être explicite, jamais une réutilisation directe des valeurs
brutes.

Voir docs/simulation_physique_archi.md pour la place de ce référentiel dans
le pipeline d'animation complet et les invariants à respecter.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

# Dimensions réglementaires FIFA -- documentent l'échelle réelle que
# représente le référentiel normalisé (utile pour calibrer une vitesse de
# déplacement plausible en m/s, voir animation/motion.py, ou une distance
# réelle comme le point de penalty, voir events.PENALTY_SPOT_ZONE). Non
# utilisées directement par to_canvas_px (qui projette [0, 1] -> pixels
# sans repasser par les mètres).
PITCH_LENGTH_M = 105.0  # axe x
PITCH_WIDTH_M = 68.0  # axe y

# --- Cotes du terrain (SOURCE UNIQUE, mètres) -----------------------------
#
# Phase 5, sous-étape 1 (07/10/2026) : toutes les cotes de TRACÉ vivent ici.
# `render/canvas.html` (bloc PITCH, vérifié par tests/test_canvas_html.py) et
# `ui/src/components/pitch/PitchField.jsx` (via ui/src/utils/pitchGeometry.json,
# vérifié par tests/test_pitch_geometry.py) en dérivent : ne jamais les modifier
# ailleurs. Régénérer le JSON : `python -m ligue1sim.pitch_geometry`.
# Origine des mètres : coin bas-gauche du terrain (même origine que le
# référentiel normalisé ci-dessus), x vers le but adverse, y vers la touche haute.
PENALTY_AREA_DEPTH_M = 16.5  # surface de réparation, profondeur (depuis la ligne de but)
PENALTY_AREA_WIDTH_M = 40.32  # surface de réparation, largeur (centrée sur le but)
GOAL_AREA_DEPTH_M = 5.5  # surface de but, profondeur
GOAL_AREA_WIDTH_M = 18.32  # surface de but, largeur
PENALTY_SPOT_DISTANCE_M = 11.0  # point de penalty, distance à la ligne de but
CENTER_CIRCLE_RADIUS_M = 9.15  # rond central
PENALTY_ARC_RADIUS_M = 9.15  # arc de cercle de la surface, centré sur le point de penalty
CORNER_ARC_RADIUS_M = 1.0  # arc de coin, centré sur le poteau de corner (= coin du terrain)
GOAL_WIDTH_M = 7.32  # largeur du but (entre poteaux)
GOAL_HEIGHT_M = 2.44  # hauteur du but (information : invisible en vue de dessus)
GOAL_NET_DEPTH_M = 2.0  # profondeur de filet REPRÉSENTÉE derrière la ligne de but (choix de tracé, non réglementaire)

# Clés exportées vers les consommateurs de tracé (canvas.html, PitchField.jsx) :
# uniquement ce qui sert à dessiner, en mètres.
_EXPORTED_DIMENSIONS: tuple[str, ...] = (
    "pitch_length_m",
    "pitch_width_m",
    "penalty_area_depth_m",
    "penalty_area_width_m",
    "goal_area_depth_m",
    "goal_area_width_m",
    "penalty_spot_distance_m",
    "center_circle_radius_m",
    "penalty_arc_radius_m",
    "corner_arc_radius_m",
    "goal_width_m",
    "goal_net_depth_m",
)


def pitch_dimensions() -> dict[str, float]:
    """Cotes de tracé du terrain en mètres (clés = `_EXPORTED_DIMENSIONS`),
    même contenu que `ui/src/utils/pitchGeometry.json` et que le bloc `PITCH`
    de `render/canvas.html`."""
    return {
        "pitch_length_m": PITCH_LENGTH_M,
        "pitch_width_m": PITCH_WIDTH_M,
        "penalty_area_depth_m": PENALTY_AREA_DEPTH_M,
        "penalty_area_width_m": PENALTY_AREA_WIDTH_M,
        "goal_area_depth_m": GOAL_AREA_DEPTH_M,
        "goal_area_width_m": GOAL_AREA_WIDTH_M,
        "penalty_spot_distance_m": PENALTY_SPOT_DISTANCE_M,
        "center_circle_radius_m": CENTER_CIRCLE_RADIUS_M,
        "penalty_arc_radius_m": PENALTY_ARC_RADIUS_M,
        "corner_arc_radius_m": CORNER_ARC_RADIUS_M,
        "goal_width_m": GOAL_WIDTH_M,
        "goal_net_depth_m": GOAL_NET_DEPTH_M,
    }


def pitch_dimensions_json() -> str:
    """`pitch_dimensions()` sérialisé en JSON compact, clés triées -- format
    commun du fichier JSON de l'UI et du bloc `PITCH` de canvas.html."""
    return json.dumps(pitch_dimensions(), sort_keys=True, separators=(",", ":"))


def corner_posts_m() -> tuple[tuple[float, float], ...]:
    """Les 4 poteaux de corner (= coins du terrain), en mètres : bas-gauche,
    haut-gauche, haut-droit, bas-droit."""
    return ((0.0, 0.0), (0.0, PITCH_WIDTH_M), (PITCH_LENGTH_M, PITCH_WIDTH_M), (PITCH_LENGTH_M, 0.0))


def penalty_arc_half_angle_rad() -> float:
    """Demi-ouverture (radians) de la portion visible de l'arc de la surface,
    vue depuis le point de penalty : l'arc de rayon `PENALTY_ARC_RADIUS_M`
    est tracé là où il sort de la surface, soit à `PENALTY_AREA_DEPTH_M -
    PENALTY_SPOT_DISTANCE_M` (5,5 m) de ce point -> acos(5,5 / 9,15) ≈ 53,1°."""
    return math.acos((PENALTY_AREA_DEPTH_M - PENALTY_SPOT_DISTANCE_M) / PENALTY_ARC_RADIUS_M)

# Grille tactique : découpe le référentiel normalisé en cases discrètes.
# 12x8 = 96 zones, choisi pour que l'axe x (12) se divise exactement en 3
# tiers égaux (voir zones_in_third).
GRID_COLUMNS = 12  # découpage de l'axe x (progression vers le but adverse)
GRID_ROWS = 8  # découpage de l'axe y (latéral)

THIRD_DEFENSIVE = "defensive"
THIRD_MIDDLE = "middle"
THIRD_ATTACKING = "attacking"

# Projection par défaut vers un canvas HTML (voir animation.render) -- un
# terrain 105x68 m a un rapport largeur/longueur de 68/105 ≈ 0.648 ; 780/1200
# = 0.65, donc un canvas 1200x780 conserve à peu près les proportions
# réelles du terrain sans étirement visible.
CANVAS_WIDTH_PX = 1200
CANVAS_HEIGHT_PX = 780


@dataclass(frozen=True)
class PitchPoint:
    """Coordonnée normalisée sur le terrain -- voir le référentiel canonique
    en tête de module (x, y ∈ [0, 1], origine bas-gauche, x vers le but
    adverse)."""

    x: float  # 0.0-1.0, progression vers le but adverse
    y: float  # 0.0-1.0, latéral (0 = touche basse, 1 = touche haute)


@dataclass(frozen=True)
class Zone:
    """Une case de la grille tactique (voir zone_of/center_of/
    zones_in_third). col=0 : zone la plus proche du but défendu ;
    col=GRID_COLUMNS-1 : zone la plus proche du but adverse. row=0 : touche
    basse ; row=GRID_ROWS-1 : touche haute."""

    col: int
    row: int


def _check_unit_range(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} doit être dans [0, 1], reçu {value!r}")


def zone_of(x: float, y: float, *, columns: int = GRID_COLUMNS, rows: int = GRID_ROWS) -> Zone:
    """Zone de la grille `columns`x`rows` contenant le point normalisé
    (x, y). x=1.0/y=1.0 (bord du terrain) retombent sur la dernière
    colonne/ligne plutôt que de déborder de la grille (une case a une
    largeur de 1/columns, donc x=1.0 appartiendrait mathématiquement à une
    colonne `columns` inexistante sans ce clamp)."""
    _check_unit_range(x, "x")
    _check_unit_range(y, "y")
    col = min(int(x * columns), columns - 1)
    row = min(int(y * rows), rows - 1)
    return Zone(col=col, row=row)


def center_of(zone: Zone, *, columns: int = GRID_COLUMNS, rows: int = GRID_ROWS) -> PitchPoint:
    """Point normalisé au centre de `zone`, dans la grille `columns`x`rows`."""
    if not (0 <= zone.col < columns):
        raise ValueError(f"zone.col={zone.col} hors de la grille (0..{columns - 1})")
    if not (0 <= zone.row < rows):
        raise ValueError(f"zone.row={zone.row} hors de la grille (0..{rows - 1})")
    return PitchPoint(x=(zone.col + 0.5) / columns, y=(zone.row + 0.5) / rows)


def zones_in_third(third: str, *, columns: int = GRID_COLUMNS, rows: int = GRID_ROWS) -> tuple[Zone, ...]:
    """Toutes les zones du tiers de terrain `third` (THIRD_DEFENSIVE/
    THIRD_MIDDLE/THIRD_ATTACKING), tiers découpés à parts égales sur l'axe x
    (le tiers défensif est le plus proche du but défendu, le tiers
    "attacking" le plus proche du but adverse). `columns` doit être un
    multiple de 3 pour un découpage exact (12 par défaut -> 4 par tiers)."""
    if columns % 3 != 0:
        raise ValueError(f"columns={columns} doit être un multiple de 3 pour un découpage en tiers exact")
    third_size = columns // 3
    third_columns = {
        THIRD_DEFENSIVE: range(0, third_size),
        THIRD_MIDDLE: range(third_size, 2 * third_size),
        THIRD_ATTACKING: range(2 * third_size, columns),
    }
    if third not in third_columns:
        raise ValueError(f"third doit être un de {tuple(third_columns)}, reçu {third!r}")
    return tuple(Zone(col=col, row=row) for col in third_columns[third] for row in range(rows))


def to_canvas_px(
    point: PitchPoint, *, canvas_width: int = CANVAS_WIDTH_PX, canvas_height: int = CANVAS_HEIGHT_PX
) -> tuple[float, float]:
    """Projette un point normalisé sur un canvas `canvas_width`x`canvas_height`
    px (1200x780 par défaut). Convention canvas standard : l'axe Y écran
    pointe vers le BAS, donc y=0 (touche basse du terrain) est projeté sur
    le BAS du canvas (px_y = canvas_height) et y=1 sur le HAUT (px_y = 0) --
    inversion nécessaire, sans quoi le terrain s'afficherait retourné
    verticalement à l'écran."""
    px_x = point.x * canvas_width
    px_y = (1.0 - point.y) * canvas_height
    return px_x, px_y


# Marge (px) autour du terrain dans le canvas 1200x780 de render/canvas.html.
CANVAS_MARGIN_PX = 20


def pitch_rect_px(
    *, canvas_width: int = CANVAS_WIDTH_PX, canvas_height: int = CANVAS_HEIGHT_PX, margin_px: int = CANVAS_MARGIN_PX
) -> tuple[float, float, float]:
    """(échelle px/m, origine x px, origine y px) du terrain 105x68 m inscrit
    dans un canvas, avec `margin_px` au moins de chaque côté. Échelle UNIQUE
    pour les deux axes (cercles réellement ronds), terrain centré. Même
    formule que `render/canvas.html` (SCALE/OX/OY) : 1200x780, marge 20 ->
    10,882 px/m, origine (28,7 ; 20) px -- le terrain occupe 1142,6 x 740 px."""
    scale = min((canvas_width - 2 * margin_px) / PITCH_LENGTH_M, (canvas_height - 2 * margin_px) / PITCH_WIDTH_M)
    return scale, (canvas_width - PITCH_LENGTH_M * scale) / 2, (canvas_height - PITCH_WIDTH_M * scale) / 2


def to_pitch_px(
    point: PitchPoint,
    *,
    canvas_width: int = CANVAS_WIDTH_PX,
    canvas_height: int = CANVAS_HEIGHT_PX,
    margin_px: int = CANVAS_MARGIN_PX,
) -> tuple[float, float]:
    """Projette un point normalisé sur le TERRAIN dessiné (x=0/x=1 = lignes de
    but, y=0/y=1 = touches), et non sur tout le canvas comme `to_canvas_px`
    (conservé tel quel pour les scripts de prévisualisation). Axe y inversé
    comme `to_canvas_px`. C'est la projection de `render/canvas.html`."""
    scale, origin_x, origin_y = pitch_rect_px(canvas_width=canvas_width, canvas_height=canvas_height, margin_px=margin_px)
    return origin_x + point.x * PITCH_LENGTH_M * scale, origin_y + (1.0 - point.y) * PITCH_WIDTH_M * scale


if __name__ == "__main__":
    # Régénère ui/src/utils/pitchGeometry.json : python -m ligue1sim.pitch_geometry > ui/src/utils/pitchGeometry.json
    print(pitch_dimensions_json())
