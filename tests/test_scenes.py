"""Tests de la fabrique de scènes partagée (`tests/scenes.py`, ticket v2-realisme/01f)."""

from __future__ import annotations

import random

from scenes import Scene, ab, fingerprint, player, run, with_attribute
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2


def _players() -> list:
    return [player("GKh", x=3, y=34, poste="GK"), player("DC", x=30, y=34, poste="DC", Decisions=70),
            player("MC", x=50, y=30, Decisions=70), player("BU", x=65, y=40, poste="BU", Decisions=70),
            player("GKa", "away", x=102, y=34, poste="GK"), player("DCa", "away", x=75, y=34, poste="DC"),
            player("MCa", "away", x=55, y=38), player("BUa", "away", x=40, y=30, poste="BU")]


def _scene(players: list) -> Scene:
    return Scene.full(players, holder="MC")


def test_identical_profiles_replay_the_same_sequence() -> None:
    a, b = ab(_players(), _scene, 10.0, 7, lambda s: s.log, "Decisions", 70)
    assert len(a) == 100
    assert a == b


def test_full_scene_is_deterministic_at_fixed_seed() -> None:
    prints = []
    for _ in range(2):
        scene = _scene(_players())
        random.seed(11)
        run(scene, 10.0)
        prints.append(fingerprint(scene))
    assert prints[0] == prints[1]


def test_profile_b_is_built_from_the_changed_players() -> None:
    a, b = ab(_players(), _scene, 0.1, 1, lambda s: (s.get("DCa").attributes or {}).get("Tackling"), "Tackling", 99,
              only="DCa")
    assert (a, b) == (None, 99)


def test_with_attribute_sets_one_or_all_and_leaves_the_originals() -> None:
    players = _players()
    one = with_attribute(players, "Pace", 90, only="MC")
    every = with_attribute(players, "Pace", 90)
    assert [p.name for p in one if (p.attributes or {}).get("Pace") == 90] == ["MC"]
    assert [p.name for p in one if p.pace == 90] == ["MC"]  # champ dédié lu par le moteur (movement.step)
    assert all(p.attributes["Pace"] == 90 and p.pace == 90 for p in every)
    assert all("Pace" not in (p.attributes or {}) and p.pace == 60 for p in players)
    one[1].attributes["Decisions"] = 1  # copies indépendantes : l'original ne bouge pas
    assert players[1].attributes["Decisions"] == 70


def test_player_sets_the_dedicated_fields() -> None:
    p = player("R", Pace=90, Acceleration=80, Stamina=70)
    assert (p.pace, p.acceleration, p.stamina) == (90, 80, 70)


def test_pace_changes_the_game_in_an_ab_scene() -> None:
    """Note lue dans un champ dédié : la comparaison A/B doit la voir (réserve A1 de l'expert, passage 1)."""
    def gap(s: Scene) -> float:
        return (s.get("R").position - s.ball.position).length()
    a, b = ab([player("R", x=40)], lambda ps: Scene(ps, BallState(position=Vec2(70.0, 34.0), velocity=Vec2(0.0, 0.0))),
              2.0, 1, gap, "Pace", 99)
    assert b < a - 1.0


def test_run_passes_the_match_arguments(monkeypatch) -> None:
    """Alignement sur `simulate_match` : mode de transition au ballon, but du pas précédent au suivi de situation
    (réserves A2 et A3 de l'expert, passage 1)."""
    scene = _scene(_players())
    modes, scored = [], []
    monkeypatch.setattr("scenes._step_ball", lambda ball, dt, players, now, d, o, m: modes.append(m) or "home")
    update = scene.situations.update
    monkeypatch.setattr(scene.situations, "update", lambda *args: scored.append(args[3]) or update(*args))
    random.seed(2)
    run(scene, 0.2)
    assert modes == [scene.transition.mode] * 2 and modes[0] is scene.transition.mode
    assert scored == [None, "home"]


def test_until_stops_the_loop() -> None:
    scene = _scene(_players())
    random.seed(3)
    assert run(scene, 10.0, until=lambda s: len(s.log) == 10)
    assert abs(scene.now_s - 1.0) < 1e-9
