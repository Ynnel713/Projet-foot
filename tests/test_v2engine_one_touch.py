"""Jeu à une touche (ticket v2-collectif/31a) : à la réception d'une passe au sol qui lui est destinée, le receveur
pense à jouer de première selon First Touch et Technique, plus souvent sous pression ; il décide alors tout de suite
(Decisions) et sa passe part sans contrôle si c'est une passe sans rotation, avec une précision du geste selon
Technique ; sinon il contrôle comme avant."""

from __future__ import annotations

import random
from dataclasses import replace

import pytest

from v2engine.ball_state import BallState
from v2engine.decision import (_ONE_TOUCH_IDEA_POINTS, ONE_TOUCH_PRESSURE_GAIN, evaluate_options,
                               one_touch_idea_probability)
from v2engine.flux import seed_streams
from v2engine.geometry import Vec2
from v2engine.match import _step_ball, simulate_match
from v2engine.possession import one_touch_precision, pass_accuracy_probability, pass_success_probability
from tests.scenes import player

GOAL = Vec2(105.0, 34.0)
EAST = Vec2(1.0, 0.0)


def _skilled(name: str, note: int, **kw):
    return replace(player(name, **kw, **{"First_Touch": note, "Technique": note}), facing=EAST)


def test_idea_follows_first_touch_and_technique_never_certain_nor_impossible() -> None:
    low, mid, high = (one_touch_idea_probability(_skilled("R", n), []) for n in (11, 55, 99))
    assert (low, mid, high) == pytest.approx(tuple(v for _, v in _ONE_TOUCH_IDEA_POINTS))
    assert 0.0 < low < mid < high < 1.0


def test_pressure_raises_the_idea() -> None:
    """Option A validée par le propriétaire (13/11/2026) : sous pression, il joue plus souvent de première (faute de
    temps pour contrôler) ; la précision, elle, baisse (test suivant)."""
    receiver = _skilled("R", 55, x=50.0, y=34.0)
    free = one_touch_idea_probability(receiver, [player("O", team="away", x=70.0, y=34.0)])
    contact = one_touch_idea_probability(receiver, [player("O", team="away", x=50.0, y=34.0)])
    assert contact == pytest.approx(free * (1.0 + ONE_TOUCH_PRESSURE_GAIN))


def test_one_touch_precision_follows_technique_and_pressure_still_hurts() -> None:
    assert one_touch_precision(_skilled("A", 11)) == pytest.approx(0.85)
    assert one_touch_precision(_skilled("A", 55)) == pytest.approx(0.93)
    assert one_touch_precision(_skilled("A", 99)) == pytest.approx(0.98)
    passer, mate = _skilled("P", 55, x=50.0, y=34.0), player("M", x=62.0, y=34.0)
    controlled = pass_accuracy_probability(passer, mate, [])
    first = pass_accuracy_probability(passer, mate, [], one_touch=True)
    assert first == pytest.approx(controlled * 0.93)
    pressed = pass_accuracy_probability(passer, mate, [player("O", team="away", x=50.5, y=34.0)], one_touch=True)
    assert pressed < first
    assert pass_success_probability(passer, mate, [], one_touch=True) < pass_success_probability(passer, mate, [])


def test_only_passes_without_rotation_are_judged_first_time() -> None:
    holder = replace(_skilled("P", 55, x=50.0, y=34.0), attributes={"First Touch": 55, "Technique": 55, "Flair": 1})
    ahead, behind = player("Devant", x=62.0, y=34.0), player("Derriere", x=35.0, y=34.0)
    passes = {o.target.name: o for o in evaluate_options(holder, [holder, ahead, behind], GOAL, None, one_touch=True)
              if o.kind == "pass"}
    assert passes["Devant"].one_touch and not passes["Derriere"].one_touch


def _reception(note: int, opponent_at: Vec2 | None, seed: int) -> str:
    """Passe au sol vers un receveur face au jeu, un partenaire libre devant lui ; rend « première », « contrôle » ou
    « raté » selon ce qu'il fait de la passe."""
    seed_streams(seed)
    passer = player("Passeur", x=30.0, y=34.0)
    receiver = _skilled("Receveur", note, x=45.0, y=34.0)
    mate = player("Libre", x=60.0, y=30.0)
    players = [passer, receiver, mate] + ([player("Adv", team="away", x=opponent_at.x, y=opponent_at.y)]
                                          if opponent_at is not None else [])
    ball = BallState(position=Vec2(44.4, 34.0), velocity=Vec2(6.0, 0.0), receiver="Receveur", released_by="Passeur")
    now = 0.0
    for _ in range(4):  # réception, puis décision au tick suivant
        _step_ball(ball, 0.1, players, now, None, None, None)
        now += 0.1
        if ball.holder is None and ball.receiver == "Libre":
            return "première"
    if ball.holder == "Receveur":
        return "contrôle"
    return "raté"


def _share(note: int, opponent_at: Vec2 | None, draws: int = 300) -> float:
    """Part des passes jouées de première parmi les réceptions réussies (contrôle raté exclu), sur `draws` graines."""
    outcomes = [_reception(note, opponent_at, k) for k in range(draws)]
    return outcomes.count("première") / max(1, sum(o != "raté" for o in outcomes))


def test_skilled_receiver_plays_first_time_more_often_never_always() -> None:
    """Scène contrôlée (critère du ticket) : passe suivante prête, pression faible. Mesuré le 13/11/2026 sur 300 graines :
    8,6 % (notes 11), 22,5 % (55), 40,6 % (99) ; fourchettes larges pour repérer une dérive de calibration (réserve A3
    de l'expert)."""
    low, mid, high = _share(11, None), _share(55, None), _share(99, None)
    assert 0.0 < low < mid < high < 1.0
    assert 0.03 <= low <= 0.16 and 0.15 <= mid <= 0.31 and 0.32 <= high <= 0.50


def test_pressure_raises_first_time_play() -> None:
    """Critère du ticket réécrit (option A, propriétaire, 13/11/2026) : la pression augmente les jeux de première.
    Mesuré sur 300 graines, note 55, adversaire à 2 m : 22,5 % -> 30,2 %."""
    free, pressed = _share(55, None), _share(55, Vec2(46.5, 35.5))
    assert pressed > free
    assert 0.22 <= pressed <= 0.38


def test_match_plays_some_first_time_passes_and_is_deterministic() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    runs = []
    for _ in range(2):
        random.seed(20260923)
        trace = simulate_match(clubs[0], clubs[1], duration_minutes=10.0)
        runs.append([(d.minute, d.player, d.action, d.one_touch) for d in trace.decisions])
    assert runs[0] == runs[1]
    passes = [d for d in runs[0] if d[2] == "pass"]
    first = [d for d in passes if d[3]]
    assert 0 < len(first) < len(passes)
