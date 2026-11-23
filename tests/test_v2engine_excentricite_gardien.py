"""Sorties inattendues du gardien (ticket v2-attributs-restants/03b3b) : Eccentricity, tendance, lui fait tenter parfois
une sortie que la course (`gardien.race`) lui refuse, sur un ballon encore jouable ; un tirage par action, sans retour
en arrière. Référence : 40, médiane des gardiens notés de Ligue 1 de la base ; à la référence, en dessous et sans note,
aucun tirage : le comportement d'avant."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.scenes import player
from v2engine import cerveau, gardien
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.movement import max_speed_mps


def _keeper(note: int | None = None):
    keeper = player("G", "home", 5.0, 34.0, "GK")
    return keeper if note is None else replace(keeper, attributes={"Eccentricity": note})


def _scene(note: int | None, lead_s: float, at: float = 25.0):
    """Ballon libre arrêté à `at` m de son but, adversaire de même vitesse que le gardien avec `lead_s` s de retard sur lui
    (négatif : il arrive avant)."""
    keeper = _keeper(note)
    rival = player("A", "away", at + (at - 5.0) + lead_s * max_speed_mps(60), 34.0, "BU")
    return keeper, BallState(position=Vec2(at, 34.0), velocity=Vec2(0.0, 0.0)), [keeper, rival]


class _Draws:
    def __init__(self, value: float) -> None:
        self.value, self.count = value, 0

    def __call__(self) -> float:
        self.count += 1
        return self.value


def test_the_constants_and_the_reference() -> None:
    assert gardien.eccentricity(None) == gardien.ECCENTRICITY_REFERENCE_NOTE == 40.0
    assert gardien.eccentricity(_keeper()) == 40.0
    assert gardien.eccentricity(replace(_keeper(), attributes={"Decisions": 70})) == 40.0
    assert gardien.eccentricity(_keeper(80)) == 80.0
    assert gardien.whim_probability() == 0.0 and gardien.whim_probability(25) == 0.0
    assert gardien.whim_probability(50) == pytest.approx(0.08)
    assert gardien.whim_probability(80) == pytest.approx(0.32)
    assert gardien.whim_probability(200) == gardien.WHIM_MAX


@pytest.mark.parametrize("note", [None, 25, 40])
def test_no_draw_and_the_former_behaviour_at_or_below_the_reference(note, monkeypatch) -> None:
    draws = _Draws(0.0)
    monkeypatch.setattr("v2engine.flux.CAPRICE.random", draws)
    keeper, ball, players = _scene(note, 0.1)  # il arrive avant, mais sans la marge : il ne sort pas
    assert not gardien.race(keeper, ball, players).rush
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    assert draws.count == 0 and ball.keeper_whims == {}


def test_an_eccentric_keeper_sometimes_takes_a_disputed_ball_once_per_action(monkeypatch) -> None:
    draws = _Draws(0.1)  # sous 0,32 : il tente
    monkeypatch.setattr("v2engine.flux.CAPRICE.random", draws)
    keeper, ball, players = _scene(80, 0.1)
    first = cerveau.think(keeper, ball, players, 1.0, {})
    assert first.reason.startswith("sortie") and "sortie inattendue" in first.reason
    for _ in range(5):  # même action : même réponse, sans nouveau tirage
        assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie")
    assert draws.count == 1
    draws.value = 0.9  # nouvelle action (ballon tenu puis de nouveau libre) : nouveau tirage, cette fois il reste
    held = replace(ball, holder="A")
    held.keeper_whims = ball.keeper_whims
    cerveau.think(keeper, held, players, 1.0, {})
    assert ball.keeper_whims == {}
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    assert draws.count == 2


def test_a_refused_whim_does_not_flip_back(monkeypatch) -> None:
    draws = _Draws(0.9)
    monkeypatch.setattr("v2engine.flux.CAPRICE.random", draws)
    keeper, ball, players = _scene(80, 0.1)
    for _ in range(4):
        assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    draws.value = 0.0
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    assert draws.count == 1


@pytest.mark.parametrize("lead_s, at, playable", [(-0.05, 25.0, True), (-0.2, 25.0, False), (0.1, 40.0, True),
                                                  (0.1, 48.0, False)])
def test_the_window_of_a_playable_ball(lead_s, at, playable, monkeypatch) -> None:
    # arrivé 0,05 s après l'adversaire : un 50/50, encore jouable ; 0,2 s : perdu d'avance ; 40 m de son but (35 + 8 m) :
    # jouable, 48 m : trop loin
    draws = _Draws(0.0)
    monkeypatch.setattr("v2engine.flux.CAPRICE.random", draws)
    keeper, ball, players = _scene(80, lead_s, at)
    course = gardien.race(keeper, ball, players)
    assert not course.rush
    assert gardien.whim_window(keeper, course) is playable
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie") is playable
    assert draws.count == int(playable)


def test_a_ball_he_should_take_needs_no_draw(monkeypatch) -> None:
    draws = _Draws(0.99)
    monkeypatch.setattr("v2engine.flux.CAPRICE.random", draws)
    keeper, ball, players = _scene(80, 1.0)
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie")
    assert draws.count == 0


def test_the_frequency_follows_the_note() -> None:
    from v2engine import flux
    flux.CAPRICE.seed(20261122)
    taken = {}
    for note in (50, 80):
        count = 0
        for _ in range(2000):
            keeper, ball, players = _scene(note, 0.1)
            count += cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie")
        taken[note] = count / 2000
    assert taken[50] == pytest.approx(0.08, abs=0.02) and taken[80] == pytest.approx(0.32, abs=0.03)


def test_a_draw_without_effect_moves_no_other_stream() -> None:
    # flux à part (ticket 03b3b) : un tirage refusé ne décale pas le flux de décision, le match reste celui d'avant
    from v2engine import flux
    flux.seed_streams(11)
    expected = flux.DECISION.random()
    flux.seed_streams(11)
    keeper, ball, players = _scene(80, 0.1)
    cerveau.think(keeper, ball, players, 1.0, {})
    assert "G" in ball.keeper_whims
    assert flux.DECISION.random() == expected
