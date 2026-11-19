"""Passes reçues en zone 14 (ticket v2-realisme/10d) : la trace donne la place du receveur à chaque contrôle, le
collecteur des indicateurs compte les passes reçues d'un coéquipier et celles reçues dans l'axe devant la surface
adverse (16,5 à 30 m du but, 11 m ou moins de l'axe). Mesure seule : l'écran du milieu prévu par le ticket a été retiré
après une mesure sans effet (voir le ticket)."""

from __future__ import annotations

import random

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from scripts.v2_indicators import Collector, in_zone_14
from v2engine.match import simulate_match
from v2engine.trace import ReceptionEvent


def _reception(team: str, x: float, y: float, origin: str = "passe au sol") -> ReceptionEvent:
    return ReceptionEvent(minute=1.0, team=team, player="R", poste="MC", kind="de face", facing_goal_deg=0.0,
                          ball_facing_deg=0.0, origin=origin, intended=True, first_time=True, x=x, y=y)


def test_zone_14() -> None:
    assert in_zone_14("home", 105.0 - 20.0, 34.0) and in_zone_14("away", 20.0, 34.0 + 11.0)
    assert not in_zone_14("home", 105.0 - 15.0, 34.0)  # dans la surface
    assert not in_zone_14("home", 105.0 - 31.0, 34.0)  # trop loin
    assert not in_zone_14("away", 20.0, 34.0 - 11.5)  # trop excentré
    assert not in_zone_14("away", 105.0 - 20.0, 34.0)  # face à son propre but


def test_the_collector_counts_passes_received_in_zone_14() -> None:
    c = Collector()
    c.on_receptions([_reception("home", 85.0, 34.0), _reception("away", 20.0, 40.0), _reception("home", 50.0, 34.0),
                     _reception("home", 85.0, 34.0, origin="récupération")])  # une récupération n'est pas une passe reçue
    assert c.count["passes reçues"] == 3
    assert c.count["passes reçues en zone 14"] == 2


def test_receptions_traced_with_their_place_deterministically() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    traces = []
    for _ in range(2):
        random.seed(20261119)
        traces.append(simulate_match(clubs[4], clubs[5], duration_minutes=3.0))
    received = [(r.minute, r.player, r.x, r.y) for r in traces[0].receptions]
    assert received and received == [(r.minute, r.player, r.x, r.y) for r in traces[1].receptions]
    assert all(0.0 <= x <= 105.0 and 0.0 <= y <= 68.0 for _, _, x, y in received)
    assert any(x != 0.0 or y != 0.0 for _, _, x, y in received)
