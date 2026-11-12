"""Tests du moteur V2, ticket v2-socle/04 (difficulté et dosage des passes, contrôle). Voir
.scratch/v2-socle/issues/04-fonction-de-difficulte.md et docs/REVUE_ATTRIBUTS_V2.md."""

from __future__ import annotations

import math
import random

from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.possession import (
    BALL_FRICTION_PER_S,
    IDEAL_ARRIVAL_MPS,
    MAX_PASS_MPS,
    composure_factor,
    control_difficulty,
    dosage_quality,
    pass_difficulty,
    pass_aim,
    pass_success_probability,
    pass_velocity,
)


def _player(name: str = "P", team: str = "home", position: Vec2 = Vec2(30.0, 34.0),
            attributes: dict[str, int] | None = None, velocity: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste="MC", position=position, velocity=velocity,
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_difficulty_follows_validated_distance_scale() -> None:
    passer = _player()
    for distance, expected in [(8.0, 10.0), (25.0, 37.0), (35.0, 55.0), (45.0, 73.0)]:
        receiver = _player("R", position=Vec2(30.0 + distance, 34.0))
        assert math.isclose(pass_difficulty(passer, receiver, []), expected)


def test_lane_marking_and_pressure_add_validated_points() -> None:
    passer = _player()
    receiver = _player("R", position=Vec2(45.0, 34.0))  # 15 m : difficulté 19
    in_lane = _player("A", team="away", position=Vec2(37.0, 35.0))  # dans le couloir, à 7 m du passeur (pas de pression)
    assert math.isclose(pass_difficulty(passer, receiver, [in_lane]), 19.0 + 12.0)
    receiver = _player("R", position=Vec2(38.0, 34.0))
    marker = _player("M", team="away", position=Vec2(39.0, 34.5))  # marque le receveur, hors couloir
    assert math.isclose(pass_difficulty(passer, receiver, [marker]), 10.0 + 10.0)


def test_presser_blocks_the_lane_only_in_front_of_the_passer() -> None:
    """Ticket v2-realisme/18f : le presseur au contact compte déjà dans la pression du passeur ; il ne ferme en plus
    le couloir que pour une passe jouée vers lui (cône de 45° près du passeur), pas pour une passe à côté de lui."""
    passer = _player()
    receiver = _player("R", position=Vec2(45.0, 34.0))  # 15 m : difficulté 19
    beside = _player("B", team="away", position=Vec2(30.75, 35.3))  # à 1,5 m, à 60° de la passe
    in_front = _player("F", team="away", position=Vec2(31.3, 34.75))  # à 1,5 m, à 30° de la passe
    pressure_only = pass_difficulty(passer, receiver, [beside])
    assert pressure_only < 19.0 + 12.0  # pression seule, pas de couloir
    assert math.isclose(pass_difficulty(passer, receiver, [in_front]) - pressure_only, 12.0, abs_tol=0.1)


def test_composure_halves_pressure_at_99_and_keeps_it_at_11() -> None:
    assert math.isclose(composure_factor(_player(attributes={"Composure": 99})), 0.5)
    assert math.isclose(composure_factor(_player(attributes={"Composure": 55})), 0.75)
    assert math.isclose(composure_factor(_player(attributes={"Composure": 11})), 1.0)


def test_easy_pass_succeeds_for_everyone_and_hard_pass_separates_notes() -> None:
    receiver_near = _player("R", position=Vec2(38.0, 34.0))
    receiver_far = _player("R", position=Vec2(65.0, 34.0))  # 35 m : difficulté 55
    # Avec les constantes validées, « au moins 90 % » vaut à partir de 50 en Passing (40 points d'avance sur la
    # difficulté 10) ; en dessous, un joueur faible rate aussi des passes faciles (guide : « ballons ratés à 10 m »).
    for note in (50, 55, 90, 99):
        assert pass_success_probability(_player(attributes={"Passing": note}), receiver_near, []) >= 0.90
    assert math.isclose(pass_success_probability(_player(attributes={"Passing": 55}), receiver_far, []), 0.5)
    gap = (pass_success_probability(_player(attributes={"Passing": 90}), receiver_far, [])
           - pass_success_probability(_player(attributes={"Passing": 30}), receiver_far, []))
    assert gap >= 0.25


def test_dosage_lead_follows_passing() -> None:
    assert math.isclose(dosage_quality(_player(attributes={"Passing": 99})), 1.0)
    assert math.isclose(dosage_quality(_player(attributes={"Passing": 11})), 0.0)


def _arrival_speed(launch: float, distance: float) -> float:
    """Vitesse du ballon après `distance` m, freiné de BALL_FRICTION_PER_S par seconde (v = v0 + s.ln f)."""
    return launch + distance * math.log(BALL_FRICTION_PER_S)


def test_well_dosed_pass_arrives_at_ideal_speed_and_in_the_run(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PASSE.random", lambda: 0.0)  # passe réussie
    monkeypatch.setattr("v2engine.flux.PASSE.uniform", lambda a, b: 0.0)  # pas d'erreur de dosage
    passer = _player(attributes={"Passing": 99})
    runner = _player("R", position=Vec2(55.0, 34.0), velocity=Vec2(0.0, 5.0))
    aim = pass_aim(passer, runner)
    assert aim.y > 34.0  # visée devant le receveur, dans sa course
    v = pass_velocity(passer, runner)
    assert math.isclose(_arrival_speed(v.length(), passer.position.distance_to(aim)), IDEAL_ARRIVAL_MPS, abs_tol=1e-9)


def test_pass_speed_is_capped_at_30_mps(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PASSE.random", lambda: 0.0)
    passer = _player(attributes={"Passing": 99})
    far = _player("R", position=Vec2(95.0, 34.0))  # 65 m
    assert pass_velocity(passer, far).length() <= MAX_PASS_MPS + 1e-9


def test_poor_dosage_spreads_the_arrival_speed(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PASSE.random", lambda: 0.0)
    receiver = _player("R", position=Vec2(50.0, 34.0))
    for note, error in ((11, 0.30), (99, 0.05)):
        monkeypatch.setattr("v2engine.flux.PASSE.uniform", lambda a, b: b)  # erreur maximale
        launch = pass_velocity(_player(attributes={"Passing": note}), receiver).length()
        ideal = IDEAL_ARRIVAL_MPS - 20.0 * math.log(BALL_FRICTION_PER_S)
        assert math.isclose(launch, ideal * (1.0 + error))


def test_missed_pass_deviates_by_10_to_25_percent_of_its_length(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PASSE.random", lambda: 0.999)  # passe ratée
    passer = _player(attributes={"Passing": 60})
    receiver = _player("R", position=Vec2(70.0, 34.0))  # 40 m
    random.seed(3)
    deviations = []
    real_uniform = random.Random(5).uniform
    monkeypatch.setattr("v2engine.flux.PASSE.uniform", real_uniform)
    for _ in range(300):
        deviations.append(pass_aim(passer, receiver).distance_to(receiver.position) / 40.0)
    assert min(deviations) >= 0.10 - 1e-9 and max(deviations) <= 0.25 + 1e-9
    assert max(deviations) - min(deviations) > 0.1  # la déviation varie bien dans la fourchette


def test_easy_ball_is_easy_to_control_and_fast_ball_is_harder() -> None:
    player = _player()
    assert math.isclose(control_difficulty(player, Vec2(IDEAL_ARRIVAL_MPS, 0.0), []), 10.0)
    assert math.isclose(control_difficulty(player, Vec2(26.0, 0.0), []), 30.0)
