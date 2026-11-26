"""Hauteur du ballon (ticket v2-hauteur-ballon/02a1, révision de D-V03) : physique verticale pure, sans état global ni
hasard. La loi horizontale (freinage) est dans `freinage` (ticket v2-realisme/14a1) ; ce module ne calcule que la
hauteur et les rebonds.

Convention (décision du propriétaire du 26/11/2026) : `z` est la hauteur du **bas** du ballon, en mètres. Ballon au
repos : `z = 0` ; impact au sol : `z = 0`. Un ballon passe sous une barre de hauteur `h` si `z + 2 × rayon < h`.

Chute libre calculée exactement sur le pas (`z + vz·t − ½·g·t²`), impact coupé à l'instant exact : sur un pas de 0,1 s,
Euler semi-implicite sous-estimerait le sommet de 10 % pour `vz0 = 10 m/s`.

Constantes validées par le propriétaire le 26/11/2026, reprises de la V1 (`src/ligue1sim/animation/ball.py`, Phase 6,
bloc B2) : g, restitution au sol 0,70 (le rebond suivant monte à 0,49 × la hauteur du précédent), vitesse horizontale
× 0,85 par rebond, rebonds arrêtés quand le sommet suivant passerait sous 0,15 m (le ballon roule). Seuil « aérien »
de 0,5 m (hauteur du genou), **provisoire** jusqu'aux tranches de hauteur du ticket v2-hauteur-ballon/03."""

from __future__ import annotations

import math
from dataclasses import dataclass

GRAVITY_M_S2 = 9.81
GROUND_RESTITUTION = 0.70
GROUND_HORIZONTAL_KEEP = 0.85  # vitesse horizontale gardée à chaque rebond au sol
REBOUND_MIN_APEX_M = 0.15  # sous ce sommet, le rebond est supprimé : le ballon roule
AERIAL_THRESHOLD_M = 0.5  # bas du ballon au-dessus : mode « aérien » (provisoire, ticket 03)
# Durée de vol maximale (décision du propriétaire du 26/11/2026, valeur réelle à sourcer : temps de vol d'un long dégagement) :
# sommet au plus g·T²/8 ≈ 24,8 m. Avec le freinage exponentiel, un ballon de 56 m à 30 m/s mettrait 6,2 s (sommet 47 m) ;
# plafonné, il retombe un peu avant sa cible (vers 53 m) et rebondit vers elle. Provisoire jusqu'à `v2-realisme/14a`.
MAX_FLIGHT_S = 4.5

# Vitesse verticale de départ sous laquelle un rebond est supprimé (sommet `vz² / 2g` sous `REBOUND_MIN_APEX_M`).
_MIN_REBOUND_VZ = math.sqrt(2.0 * GRAVITY_M_S2 * REBOUND_MIN_APEX_M)


@dataclass(frozen=True)
class HeightStep:
    """Résultat d'un pas vertical : nouvelle hauteur `z` et vitesse verticale `vz`, facteur à appliquer à la vitesse
    horizontale (`horizontal_keep`, produit des rebonds du pas), nombre de rebonds dans le pas, et instant du premier
    contact avec le sol depuis le début du pas (`None` sans contact)."""
    z: float
    vz: float
    horizontal_keep: float
    bounces: int
    first_contact_s: float | None


def is_aerial(z: float) -> bool:
    """Mode « aérien » : bas du ballon au-dessus de `AERIAL_THRESHOLD_M`."""
    return z > AERIAL_THRESHOLD_M


def apex_m(z: float, vz: float) -> float:
    """Point le plus haut atteint depuis (`z`, `vz`) en chute libre (`z` si le ballon descend déjà)."""
    return z + vz * vz / (2.0 * GRAVITY_M_S2) if vz > 0.0 else z


def time_to_ground(z: float, vz: float) -> float:
    """Temps avant que le bas du ballon touche le sol (`z = 0`) en chute libre ; 0 pour un ballon déjà au sol qui ne
    monte pas."""
    if z <= 0.0 and vz <= 0.0:
        return 0.0
    return (vz + math.sqrt(vz * vz + 2.0 * GRAVITY_M_S2 * max(0.0, z))) / GRAVITY_M_S2


def height_at(z: float, vz: float, t: float) -> tuple[float, float]:
    """Hauteur et vitesse verticale après `t` secondes de chute libre, sans rebond (à n'utiliser qu'avant l'impact)."""
    return z + vz * t - 0.5 * GRAVITY_M_S2 * t * t, vz - GRAVITY_M_S2 * t


def launch_vz(flight_s: float | None) -> float:
    """Vitesse verticale de départ d'un ballon frappé au sol qui retombe au sol après `flight_s` secondes :
    `vz0 = g·T / 2`, durée plafonnée à `MAX_FLIGHT_S`. `None` (ballon qui n'arrive pas, `freinage.travel_time_s`) : vol plafonné,
    il retombe avant sa cible."""
    flight = MAX_FLIGHT_S if flight_s is None else min(MAX_FLIGHT_S, max(0.0, flight_s))
    return 0.5 * GRAVITY_M_S2 * flight


def step_height(z: float, vz: float, dt: float) -> HeightStep:
    """Avance la hauteur du ballon de `dt` secondes : chute libre exacte, impact coupé à l'instant exact, rebond
    (`vz ← −0,70·vz`, vitesse horizontale × 0,85), arrêt des rebonds sous `REBOUND_MIN_APEX_M` de sommet (le ballon roule :
    `z = 0`, `vz = 0`). Plusieurs rebonds dans un même pas sont traités dans l'ordre."""
    keep, bounces, first = 1.0, 0, None
    elapsed = 0.0
    while elapsed < dt:
        if z <= 0.0 and vz <= 0.0:
            return HeightStep(0.0, 0.0, keep, bounces, first)  # au sol : il roule
        left = dt - elapsed
        hit = time_to_ground(z, vz)
        if hit > left:
            z, vz = height_at(z, vz, left)
            return HeightStep(max(0.0, z), vz, keep, bounces, first)
        elapsed += hit
        first = elapsed if first is None else first
        impact_vz = vz - GRAVITY_M_S2 * hit  # négatif : le ballon descend
        rebound_vz = -GROUND_RESTITUTION * impact_vz
        z = 0.0
        if rebound_vz < _MIN_REBOUND_VZ:
            vz = 0.0  # rebond trop bas : supprimé, le ballon roule (pas de « rebond » ni de freinage horizontal)
            continue
        vz = rebound_vz
        keep *= GROUND_HORIZONTAL_KEEP
        bounces += 1
    return HeightStep(z, vz, keep, bounces, first)


def launch_vz_to(z_target_m: float, flight_s: float | None) -> float:
    """Vitesse verticale de départ d'un ballon frappé au sol pour que son bas soit à `z_target_m` après `flight_s`
    secondes de chute libre (ticket 02a2) : `vz0 = (z + ½·g·T²) / T`. Durée nulle ou inconnue : 0 (frappe à plat)."""
    if flight_s is None or flight_s <= 0.0:
        return 0.0
    return (max(0.0, z_target_m) + 0.5 * GRAVITY_M_S2 * flight_s * flight_s) / flight_s
