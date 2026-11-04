"""Carte du danger (ticket v2-collectif/33) : monnaie commune des options du porteur. Grille « expected threat » de
Karun Singh (2019), jeu ouvert, publiée en `karun.in/blog/data/open_xt_12x8_v1.json` (téléchargée le 03/11/2026,
constante validée par le propriétaire) : probabilité de marquer dans les actions qui suivent, ballon à cet endroit."""

from __future__ import annotations

from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2

# 8 lignes (largeur) x 12 colonnes (de son propre but vers le but adverse). Symétrique en largeur.
_XT = (
    (0.00638, 0.00780, 0.00845, 0.00978, 0.01126, 0.01248, 0.01474, 0.01745, 0.02122, 0.02756, 0.03485, 0.03793),
    (0.00750, 0.00879, 0.00942, 0.01059, 0.01215, 0.01385, 0.01612, 0.01870, 0.02402, 0.02953, 0.04067, 0.04648),
    (0.00888, 0.00978, 0.01001, 0.01110, 0.01269, 0.01429, 0.01686, 0.01935, 0.02412, 0.02855, 0.05491, 0.06443),
    (0.00941, 0.01083, 0.01017, 0.01132, 0.01263, 0.01485, 0.01690, 0.01997, 0.02385, 0.03511, 0.10805, 0.25745),
    (0.00941, 0.01083, 0.01017, 0.01132, 0.01263, 0.01485, 0.01690, 0.01997, 0.02385, 0.03511, 0.10805, 0.25745),
    (0.00888, 0.00978, 0.01001, 0.01110, 0.01269, 0.01429, 0.01686, 0.01935, 0.02412, 0.02855, 0.05491, 0.06443),
    (0.00750, 0.00879, 0.00942, 0.01059, 0.01215, 0.01385, 0.01612, 0.01870, 0.02402, 0.02953, 0.04067, 0.04648),
    (0.00638, 0.00780, 0.00845, 0.00978, 0.01126, 0.01248, 0.01474, 0.01745, 0.02122, 0.02756, 0.03485, 0.03793),
)
_COLS, _ROWS = len(_XT[0]), len(_XT)


def _axis(coord: float, length: float, cells: int) -> tuple[int, int, float]:
    """Deux cases voisines et le poids de la seconde, entre les centres des cases (bornées aux bords)."""
    t = min(max(coord / length * cells - 0.5, 0.0), cells - 1.0)
    low = min(int(t), cells - 2)
    return low, low + 1, t - low


def danger(point: Vec2, team: str) -> float:
    """Danger pour `team` d'avoir le ballon en `point`, lissé entre les centres des cases (interpolation bilinéaire) :
    sans lissage, un mètre de plus pourrait faire sauter la valeur d'une case à l'autre. `home` attaque vers x = 105."""
    x = point.x if team == "home" else PITCH_LENGTH_M - point.x
    c0, c1, tx = _axis(x, PITCH_LENGTH_M, _COLS)
    r0, r1, ty = _axis(point.y, PITCH_WIDTH_M, _ROWS)
    top = _XT[r0][c0] * (1 - tx) + _XT[r0][c1] * tx
    bottom = _XT[r1][c0] * (1 - tx) + _XT[r1][c1] * tx
    return top * (1 - ty) + bottom * ty


def loss_cost(point: Vec2, team: str) -> float:
    """Coût de perdre le ballon en `point` : le danger qu'y aurait l'adversaire (grille retournée)."""
    return danger(point, "away" if team == "home" else "home")
