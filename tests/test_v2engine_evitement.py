"""Évitement entre coéquipiers (ticket v2-realisme/11f) : le joueur infléchit sa course (35° au plus) ou ralentit pour ne
pas percuter un coéquipier ; il n'évite pas les adversaires ; le porteur n'évite personne ; le côté choisi est tenu
0,2 s ; sans coéquipier dans le couloir, rien ne change."""

from __future__ import annotations

import math
import random
from dataclasses import replace

import pytest

from v2engine.evitement import (AVOID_MAX_BRAKE, AVOID_MAX_DEFLECTION_DEG, AVOID_SIDE_HOLD_S, LEFT, RIGHT,
                                avoid_teammates)
from v2engine.geometry import Vec2
from v2engine.match import _resolve_player_collisions
from v2engine.movement import step
from tests.scenes import player


def _runner(name: str, team: str, x: float, y: float, vx: float, vy: float = 0.0):
    p = replace(player(name, team, x, y, "MC", Pace=80, Acceleration=80, Agility=70), velocity=Vec2(vx, vy))
    return replace(p, facing=p.velocity.normalized() if p.velocity.length() > 0 else Vec2(1.0, 0.0))


def _angle_deg(u: Vec2, v: Vec2) -> float:
    cos = (u.x * v.x + u.y * v.y) / (u.length() * v.length())
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def test_free_run_is_unchanged() -> None:
    a = _runner("A", "home", 50.0, 34.0, 6.0)
    far = _runner("B", "home", 50.0, 44.0, 0.0)
    target = Vec2(70.0, 34.0)
    out = avoid_teammates(a, target, 0.9, [a, far], None, 10.0)
    assert out.target is target and out.intensity == 0.9 and out.side == 0


def test_opponent_in_the_corridor_is_not_avoided() -> None:
    a = _runner("A", "home", 50.0, 34.0, 6.0)
    rival = _runner("R", "away", 53.0, 34.0, 0.0)
    out = avoid_teammates(a, Vec2(70.0, 34.0), 1.0, [a, rival], None, 0.0)
    assert out.target == Vec2(70.0, 34.0) and out.intensity == 1.0


def test_teammate_ahead_is_bypassed_on_the_free_side_within_35_degrees() -> None:
    a = _runner("A", "home", 50.0, 34.0, 6.0)
    mate = _runner("B", "home", 53.0, 34.2, 0.0)  # un peu à gauche de la course
    target = Vec2(70.0, 34.0)
    out = avoid_teammates(a, target, 1.0, [a, mate], None, 0.0)
    deflected = out.target - a.position
    assert 0.0 < _angle_deg(deflected, target - a.position) <= AVOID_MAX_DEFLECTION_DEG + 1e-9
    assert deflected.y < 0.0 and out.side == RIGHT  # il passe à droite, loin du coéquipier
    assert out.side_until_s == pytest.approx(AVOID_SIDE_HOLD_S)
    assert deflected.length() == pytest.approx((target - a.position).length())


def test_head_on_both_turn_right_so_they_split() -> None:
    """Pile en face : chacun prend sa droite, donc des côtés opposés du terrain (pas d'effet miroir)."""
    a = _runner("A", "home", 50.0, 34.0, 6.0)
    b = _runner("B", "home", 54.0, 34.0, -6.0)
    out_a = avoid_teammates(a, Vec2(70.0, 34.0), 1.0, [a, b], None, 0.0)
    out_b = avoid_teammates(b, Vec2(30.0, 34.0), 1.0, [a, b], None, 0.0)
    assert out_a.side == RIGHT and out_b.side == RIGHT
    assert (out_a.target - a.position).y < 0.0 < (out_b.target - b.position).y


def test_holder_avoids_nobody_and_is_avoided() -> None:
    holder = _runner("H", "home", 50.0, 34.0, 5.0)
    mate = _runner("M", "home", 53.0, 34.0, -5.0)
    out_holder = avoid_teammates(holder, Vec2(70.0, 34.0), 1.0, [holder, mate], "H", 0.0)
    assert out_holder.target == Vec2(70.0, 34.0) and out_holder.side == 0
    out_mate = avoid_teammates(mate, Vec2(30.0, 34.0), 1.0, [holder, mate], "H", 0.0)
    assert out_mate.side != 0


def test_closed_corridor_brakes_at_most_half() -> None:
    a = _runner("A", "home", 50.0, 34.0, 6.0)
    wall = [_runner(f"W{i}", "home", 52.5, 34.0 + dy, 0.0) for i, dy in enumerate((-3.2, -2.4, -1.6, -0.8, 0.0,
                                                                                  0.8, 1.6, 2.4, 3.2))]
    out = avoid_teammates(a, Vec2(70.0, 34.0), 0.8, [a, *wall], None, 0.0)
    assert out.target == Vec2(70.0, 34.0)
    assert out.intensity == pytest.approx(0.8 * (1.0 - AVOID_MAX_BRAKE))  # coéquipiers arrêtés : freinage maximal


def test_side_is_held_for_0_2_s_then_free_again() -> None:
    a = _runner("A", "home", 50.0, 34.0, 6.0)
    mate = _runner("B", "home", 53.0, 33.8, 0.0)  # à droite : il passerait à gauche
    held = avoid_teammates(a, Vec2(70.0, 34.0), 1.0, [a, mate], None, 1.0, side=RIGHT, side_until_s=1.15)
    assert held.side == RIGHT and held.side_until_s == pytest.approx(1.0 + AVOID_SIDE_HOLD_S)
    free = avoid_teammates(a, Vec2(70.0, 34.0), 1.0, [a, mate], None, 1.3, side=RIGHT, side_until_s=1.15)
    assert free.side == LEFT


def _frank_contact(before: list, after: list, radii: float = 0.6) -> bool:
    """Contact franc pendant le pas : distance minimale du mouvement relatif (rectiligne sur le pas) sous la somme des
    rayons, à plus de 2 m/s de rapprochement. Attrape aussi deux joueurs qui se traversent entre deux pas."""
    d0 = before[1].position - before[0].position
    d1 = after[1].position - after[0].position
    move = d1 - d0
    mm = move.x * move.x + move.y * move.y
    s = 0.0 if mm < 1e-12 else max(0.0, min(1.0, -(d0.x * move.x + d0.y * move.y) / mm))
    closest = d0 + move * s
    if closest.length() >= radii:
        return False
    rel = after[0].velocity - after[1].velocity
    axis = closest if closest.length() > 1e-9 else d0
    return (rel.x * axis.x + rel.y * axis.y) / max(axis.length(), 1e-9) > 2.0


def _turn(out_target: Vec2, target: Vec2, position: Vec2) -> float:
    wanted, chosen = target - position, out_target - position
    return 0.0 if wanted.length() < 1e-9 or chosen.length() < 1e-9 else _angle_deg(chosen, wanted)


def _cross(seed: int):
    """Deux coéquipiers lancés l'un vers l'autre (angle et décalage tirés), cibles fixes, 4 s au pas de 0,1 s :
    évitement, `step`, collisions. Rend les contacts francs, l'inflexion max et le plus court maintien d'un côté."""
    rng = random.Random(seed)
    angle = math.radians(rng.uniform(-60.0, 60.0))
    a = _runner("A", "home", 40.0, 34.0, 6.0)
    start_b = Vec2(60.0, 34.0 + rng.uniform(-1.0, 1.0))
    heading_b = Vec2(-math.cos(angle), math.sin(angle))
    speed_b = rng.choice((0.0, 2.0, 4.0, 6.0))  # coéquipier arrêté, lent ou lancé
    b = _runner("B", "home", start_b.x, start_b.y, heading_b.x * speed_b, heading_b.y * speed_b)
    targets = {"A": Vec2(80.0, 34.0), "B": start_b + heading_b * (40.0 if speed_b > 0.0 else 0.0)}
    players, frank, max_turn, sides = [a, b], 0, 0.0, {"A": [], "B": []}
    for k in range(40):
        now, moved = k * 0.1, []
        for p in players:
            out = avoid_teammates(p, targets[p.name], 1.0, players, None, now, p.avoid_side, p.avoid_side_until_s)
            max_turn = max(max_turn, _turn(out.target, targets[p.name], p.position))
            sides[p.name].append((now, p.avoid_side, p.avoid_side_until_s, out.side))
            moved.append(replace(step(p, 0.1, out.target, now / 60.0, out.intensity), avoid_side=out.side,
                                 avoid_side_until_s=out.side_until_s))
        frank += _frank_contact(players, moved)
        players = moved
        _resolve_player_collisions(players)
    return frank, max_turn, sides


@pytest.mark.parametrize("seed", range(20))
def test_crossing_teammates_never_collide_frankly(seed: int) -> None:
    frank, max_turn, sides = _cross(seed)
    assert frank == 0
    assert max_turn <= AVOID_MAX_DEFLECTION_DEG + 1e-6
    for history in sides.values():  # un côté retenu n'est jamais inversé tant qu'il est tenu (0,2 s après son choix)
        for now, before, until, after in history:
            if before != 0 and now < until:
                assert after == before


def test_without_avoidance_the_same_crossing_collides() -> None:
    """Témoin : sans évitement, les mêmes courses se percutent franchement (la scène teste bien quelque chose)."""
    a, b = _runner("A", "home", 40.0, 34.0, 6.0), _runner("B", "home", 60.0, 34.0, 0.0)  # coéquipier arrêté
    players, frank = [a, b], 0
    for k in range(40):
        moved = [step(players[0], 0.1, Vec2(80.0, 34.0), 0.0), step(players[1], 0.1, Vec2(60.0, 34.0), 0.0)]
        frank += _frank_contact(players, moved)
        players = moved
        _resolve_player_collisions(players)
    assert frank >= 1


def test_priority_player_avoids_nobody_and_is_avoided() -> None:
    """Réserve A1 de l'expert : receveur visé, gardien qui sort, désigné sur ballon libre n'évitent pas (`priority`)."""
    runner = _runner("R", "home", 50.0, 34.0, 5.0)
    mate = _runner("M", "home", 53.0, 34.0, -5.0)
    out = avoid_teammates(runner, Vec2(70.0, 34.0), 1.0, [runner, mate], None, 0.0, priority=True)
    assert out.target == Vec2(70.0, 34.0) and out.intensity == 1.0 and out.side == 0
    assert avoid_teammates(mate, Vec2(30.0, 34.0), 1.0, [runner, mate], None, 0.0).side != 0


@pytest.mark.parametrize("role, action, poste, nearest, expected", [
    ("receveur visé", "venir au ballon", "MC", False, True),
    ("ballon libre", "aller au ballon", "MC", True, True),
    ("ballon libre", "aller au ballon", "MC", False, False),
    ("soutien", "soutenir", "MC", True, False),
    ("gardien", "aller au ballon", "GK", False, True),  # sortie (rôle toujours « gardien », `cerveau._keeper`)
    ("gardien", "venir au ballon", "GK", False, True),  # passe pour lui
    ("gardien", "se replacer", "GK", True, False)])
def test_match_gives_priority_to_the_player_going_to_the_ball(monkeypatch, role, action, poste, nearest,
                                                              expected) -> None:
    """`match._step_player` passe `priority` au receveur, au désigné sur ballon libre et au gardien qui va au ballon."""
    from types import SimpleNamespace

    import v2engine.match as match
    from v2engine.ball_state import BallState

    seen: list[bool] = []
    real = match.avoid_teammates

    def spy(*args, **kwargs):
        seen.append(kwargs["priority"] if "priority" in kwargs else args[9])
        return real(*args, **kwargs)

    monkeypatch.setattr(match, "think", lambda p, *a, **k: SimpleNamespace(
        role=role, action=action, target=Vec2(70.0, 34.0), intensity=1.0, target_velocity=Vec2(0.0, 0.0)))
    monkeypatch.setattr(match, "nearest_field_player", lambda *a: nearest)
    monkeypatch.setattr(match, "avoid_teammates", spy)
    p = replace(_runner("P", "home", 50.0, 34.0, 5.0), poste=poste)
    ball = BallState(position=Vec2(60.0, 34.0), velocity=Vec2(0.0, 0.0), holder=None)
    match._step_player(p, ball, 0.1, 0.0, [p])
    assert seen == [expected]


def test_keeper_coming_out_has_priority_with_the_real_brain(monkeypatch) -> None:
    """Sans simulation du cerveau : gardien qui sort sur un ballon libre, défenseur dans son couloir. Le gardien a la
    priorité (vrai `think`, action « aller au ballon ») ; le défenseur s'écarte."""
    import v2engine.match as match
    from tests.scenes import Scene

    seen: dict[str, tuple[bool, object]] = {}
    real = match.avoid_teammates

    def spy(*args, **kwargs):
        out = real(*args, **kwargs)
        seen[args[0].name] = (kwargs["priority"] if "priority" in kwargs else args[9], out)
        return out

    monkeypatch.setattr(match, "avoid_teammates", spy)
    keeper = player("G", "home", 3.0, 34.0, "GK")
    defender = replace(player("D", "home", 9.0, 34.5, "DC"), velocity=Vec2(-3.0, 0.0))
    scene = Scene.full([keeper, defender, player("A", "away", 40.0, 34.0, "BU")], ball_at=Vec2(12.0, 34.0))
    scene.ball.velocity = Vec2(-4.0, 0.0)
    keeper_now = replace(scene.players[0], velocity=Vec2(3.0, 0.0))
    scene.players[0] = keeper_now
    for p in scene.players:
        match._step_player(p, scene.ball, 0.1, 0.0, scene.players, scene.runs, scene.intentions, scene.situations,
                           scene.bloc, scene.defense, scene.transition)
    assert scene.intentions["G"].role == "gardien" and scene.intentions["G"].action == "aller au ballon"
    assert seen["G"][0] is True and seen["G"][1].side == 0  # il va droit au ballon
    assert seen["D"][0] is False
