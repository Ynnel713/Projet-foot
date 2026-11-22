"""Tests du moteur V2, ticket v2-realisme/10g (marquage dans la surface : homme ou zone). Voir
.scratch/v2-realisme/issues/10g-marquage-dans-la-surface.md. Le comportement demandé existe déjà : le marqueur est
choisi à chaque pas parmi les libres, le plus proche de l'attaquant, avant les zones de la surface (10f) ; un défenseur
de zone prend donc l'attaquant qui entre dans sa zone et le rend au suivant quand il en sort. Ces tests le figent."""

from __future__ import annotations

from tests.scenes import player
from v2engine.ball_state import BallState
from v2engine.defense import MARQUAGE, ZONE_SURFACE, DefensiveRoles
from v2engine.geometry import Vec2

# « away » attaque vers x = 0 : le but défendu par « home » est en (0, 34). Ballon sur l'aile, à 15 m de la ligne :
# premier poteau (4 ; 37), point de penalty (11 ; 34), second poteau (5 ; 30), retrait (13 ; 40).
DEFENDERS = (("P", 17.0, 57.0), ("Z1", 4.0, 37.0), ("Z2", 11.0, 34.0), ("Z3", 5.0, 30.0), ("Z4", 13.0, 40.0))


def _update(defense: DefensiveRoles, attacker_at: tuple[float, float], now_s: float) -> dict[str, tuple[str, str]]:
    holder = player("H", "away", x=15.0, y=60.0)
    players = [holder, player("A", "away", x=attacker_at[0], y=attacker_at[1], poste="BU"),
               *(player(n, "home", x=x, y=y, poste="DC") for n, x, y in DEFENDERS),
               player("G", "home", x=1.0, y=34.0, poste="GK")]
    defense.update(players, BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H"), None, now_s)
    return {name: (a.role, a.mate) for name, a in defense.assignments.items()}


def test_the_zone_defender_takes_the_attacker_entering_his_zone_and_hands_him_on() -> None:
    defense = DefensiveRoles()
    at_first_post = _update(defense, (5.5, 37.5), 0.0)
    assert at_first_post["Z1"] == (MARQUAGE, "A")  # entré au premier poteau : le défenseur de cette zone le prend
    assert ZONE_SURFACE in {role for role, _ in at_first_post.values()}  # les autres libres tiennent les zones
    at_the_spot = _update(defense, (11.5, 33.0), 1.0)
    assert at_the_spot["Z2"] == (MARQUAGE, "A")  # passé au point de penalty : rendu au défenseur de cette zone
    assert at_the_spot["Z1"] == (ZONE_SURFACE, "premier poteau")  # le premier regagne sa zone


def test_an_attacker_outside_the_zones_is_marked_by_the_closest_free_defender() -> None:
    roles = _update(DefensiveRoles(), (20.0, 22.0), 0.0)
    markers = [name for name, (role, mate) in roles.items() if role == MARQUAGE and mate == "A"]
    assert markers == ["Z2"]  # 15 m de Z2, 17 m de Z3, 21 m de Z1 : le plus proche des libres
