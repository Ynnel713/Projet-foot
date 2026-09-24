import math

import pytest

from ligue1sim.animation.motion import MAX_SPEED_MPS, interpolate
from ligue1sim.animation.sequence_generator import enrich_with_background
from ligue1sim.animation.state import DynamicBallState, PlayerState, player_states_and_ball_at
from ligue1sim.animation.templates import BUILDERS
from ligue1sim.animation.types import BallState as EngineBallState
from ligue1sim.animation.types import Keyframe, RosterEntry, Sequence
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Zone
from ligue1sim.players import Player

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)


def _player(poste: str, note: float, name: str, player_id: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note,
        club="Test FC", championnat="TEST", id=player_id,
    )


def _lineup() -> Lineup:
    players = [
        _player("GK", 70.0, "gk", 1),
        _player("DC", 70.0, "cb0", 2),
        _player("DC", 70.0, "cb1", 3),
        _player("LB", 70.0, "lb", 4),
        _player("RB", 70.0, "rb", 5),
        _player("MDC", 70.0, "mdc", 6),
        _player("MC", 70.0, "mc0", 7),
        _player("MC", 70.0, "mc1", 8),
        _player("AG", 70.0, "ag", 9),
        _player("AD", 70.0, "ad", 10),
        _player("BU", 70.0, "bu", 11),
    ]
    return Lineup(club_name="Test FC", formation="4-3-3", players=players, rating=70.0)


def _opponent_lineup() -> Lineup:
    players = [
        _player("GK", 65.0, "opp-gk", 101),
        _player("DC", 65.0, "opp-cb0", 102),
        _player("DC", 65.0, "opp-cb1", 103),
        _player("LB", 65.0, "opp-lb", 104),
        _player("RB", 65.0, "opp-rb", 105),
        _player("MDC", 65.0, "opp-mdc", 106),
        _player("MC", 65.0, "opp-mc0", 107),
        _player("MC", 65.0, "opp-mc1", 108),
        _player("AG", 65.0, "opp-ag", 109),
        _player("AD", 65.0, "opp-ad", 110),
        _player("BU", 65.0, "opp-bu", 111),
    ]
    return Lineup(club_name="Opponent FC", formation="4-3-3", players=players, rating=65.0)


def _start_positions(lineup: Lineup):
    from ligue1sim.pitch_geometry import PitchPoint
    return {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


def _goal_event(*, assist: str | None = "mc0") -> GoalEvent:
    return GoalEvent(
        club_name="Test FC", scorer="bu", assist=assist, minute=34, penalty=False,
        zone=_SCORER_ZONE, assist_zone=_ASSIST_ZONE if assist else None,
    )


def _enriched_sequence(name: str):
    lineup = _lineup()
    opponent = _opponent_lineup()
    sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
    return enrich_with_background(sequence, opponent)


class TestPositionsAreIdenticalToTheOldSystem:
    """Tâche 3.1, brief "introduce PlayerState and BallState" (24/09/2026) --
    `player_states_and_ball_at` ne recalcule jamais une position : c'est un
    pur pont de reformatage au-dessus d'`interpolate` (INCHANGÉ), converti
    de normalisé (0-1) en mètres par une simple mise à l'échelle. Egalité à
    `1e-9` près (pas une égalité bit-à-bit stricte) : justifiée par
    l'arrondi flottant introduit par la MULTIPLICATION `* PITCH_LENGTH_M`/
    `* PITCH_WIDTH_M` elle-même (pas par un nouveau calcul indépendant --
    diviser le résultat par la même constante ne redonne pas TOUJOURS
    bit-à-bit la valeur d'origine en IEEE 754, écart de l'ordre de 1e-13 à
    1e-16 mesuré, très en-deçà de toute tolérance de rendu)."""

    SAMPLE_FRACTIONS = (0.0, 0.13, 0.37, 0.5, 0.71, 0.9, 1.0)

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_player_positions_match_the_old_interpolate_output(self, name):
        sequence = _enriched_sequence(name)
        for frac in self.SAMPLE_FRACTIONS:
            t = sequence.duration * frac
            old_frame = interpolate(sequence, t)
            new_players, _new_ball = player_states_and_ball_at(sequence, t)
            new_by_id = {p.player_id: p for p in new_players}

            assert len(new_by_id) == len(old_frame.players)
            for player_id, old_state in old_frame.players.items():
                new_state = new_by_id[str(player_id)]
                assert new_state.position[0] / PITCH_LENGTH_M == pytest.approx(old_state.x, abs=1e-9)
                assert new_state.position[1] / PITCH_WIDTH_M == pytest.approx(old_state.y, abs=1e-9)

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_ball_position_matches_the_old_ball_state_at_output(self, name):
        sequence = _enriched_sequence(name)
        for frac in self.SAMPLE_FRACTIONS:
            t = sequence.duration * frac
            old_frame = interpolate(sequence, t)
            _new_players, new_ball = player_states_and_ball_at(sequence, t)

            assert new_ball.position[0] / PITCH_LENGTH_M == pytest.approx(old_frame.ball.x, abs=1e-9)
            assert new_ball.position[1] / PITCH_WIDTH_M == pytest.approx(old_frame.ball.y, abs=1e-9)
            assert new_ball.position[2] == pytest.approx(old_frame.ball.z, abs=1e-9)  # z deja en metres, aucune conversion


class TestPlayerStatesShape:
    """Tâche 3.2 -- 22 `PlayerState` par frame (11 + 11, voir
    `enrich_with_background`), types et champs non vides."""

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_exactly_22_player_states_with_valid_fields(self, name):
        sequence = _enriched_sequence(name)
        players, _ball = player_states_and_ball_at(sequence, sequence.duration * 0.4)

        assert len(players) == 22
        seen_ids = set()
        for p in players:
            assert isinstance(p, PlayerState)
            assert isinstance(p.player_id, str) and p.player_id
            seen_ids.add(p.player_id)
            assert p.team in ("scorer", "opponent")
            assert isinstance(p.position, tuple) and len(p.position) == 2
            assert all(isinstance(v, float) for v in p.position)
            assert isinstance(p.direction_body, float)
            assert p.current_action in ("idle", "sprint")
            assert p.target is None or (isinstance(p.target, tuple) and len(p.target) == 2)
            assert isinstance(p.velocity, tuple) and len(p.velocity) == 2
            assert all(isinstance(v, float) for v in p.velocity)
            assert isinstance(p.acceleration, tuple) and len(p.acceleration) == 2
            assert all(isinstance(v, float) for v in p.acceleration)
        assert len(seen_ids) == 22  # jamais deux joueurs avec le meme player_id


class TestBallStateShape:
    """Tâche 3.3 -- `DynamicBallState` par frame (distinct de
    `ligue1sim.animation.types.BallState`, voir docstring de `state.py`)."""

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_ball_state_has_valid_fields(self, name):
        sequence = _enriched_sequence(name)
        _players, ball = player_states_and_ball_at(sequence, sequence.duration * 0.4)

        assert isinstance(ball, DynamicBallState)
        assert not isinstance(ball, EngineBallState)  # jamais confondus, voir docstring de state.py
        assert isinstance(ball.position, tuple) and len(ball.position) == 3
        assert all(isinstance(v, float) for v in ball.position)
        assert isinstance(ball.velocity, tuple) and len(ball.velocity) == 3
        assert all(isinstance(v, float) for v in ball.velocity)
        assert ball.possession is None or isinstance(ball.possession, str)


def _uniform_motion_sequence(*, v_max_m_s: float, duration_s: float) -> Sequence:
    """Séquence synthétique à 1 joueur actif, construite pour forcer le
    repli linéaire à vitesse constante d'`animation.motion._interpolate_segment`
    (comportement 2, voir sa docstring) : distance très supérieure à ce que
    `v_max` permet de couvrir dans `duration_s`, donc vitesse CONSTAMENT
    égale à `v_max` (pas d'accélération/décélération ease-in-out) sur tout
    le segment -- une vérité de référence connue pour la Tâche 4.2."""
    start = (0.05, 0.5)
    end = (0.95, 0.5)  # ~94.5 m en x, très au-dela de v_max*duration_s
    ball = EngineBallState(x=start[0], y=start[1], z=0.0, spin=0.0, owner_id="runner")
    keyframes = [
        Keyframe(t=0.0, ball=ball, players={"runner": start}, tag="test", physics_tag=None),
        Keyframe(t=duration_s, ball=ball, players={"runner": end}, tag="test", physics_tag=None),
    ]
    roster = {"runner": RosterEntry(nom="runner", poste="BU", role="scorer", numero=9, team_side="scorer")}
    return Sequence(event_ref="test:uniform", keyframes=keyframes, duration=duration_s, meta={}, roster=roster)


class TestVelocityAndAccelerationAreConsistent:
    """Tâche 4.2 -- sur un déplacement à vitesse constante connue (`v_max`
    du poste "BU", voir `MAX_SPEED_MPS`), `velocity` doit être proche de
    cette vitesse théorique et `acceleration` proche de 0."""

    def test_uniform_motion_matches_the_known_speed(self):
        v_max = MAX_SPEED_MPS["BU"]
        sequence = _uniform_motion_sequence(v_max_m_s=v_max, duration_s=2.0)
        t = sequence.duration / 2.0  # loin des deux bords (>> _DERIVATIVE_DT_S)

        players, _ball = player_states_and_ball_at(sequence, t)
        runner = next(p for p in players if p.player_id == "runner")

        speed = math.hypot(*runner.velocity)
        assert speed == pytest.approx(v_max, rel=0.01), f"vitesse mesuree {speed:.4f} m/s, attendue ~{v_max} m/s"
        assert runner.velocity[1] == pytest.approx(0.0, abs=1e-6)  # deplacement purement horizontal
        assert math.hypot(*runner.acceleration) == pytest.approx(0.0, abs=1e-3)


class TestVelocityAndAccelerationAreFiniteAtBoundaries:
    """Tâche 4.3 -- à `t=0` et `t=durée` (différences avant/arrière, voir
    `_velocities_m_s_at`), aucune valeur `NaN`/infinie."""

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    @pytest.mark.parametrize("frac", (0.0, 1.0))
    def test_boundary_values_are_finite(self, name, frac):
        sequence = _enriched_sequence(name)
        players, ball = player_states_and_ball_at(sequence, sequence.duration * frac)

        for p in players:
            assert all(math.isfinite(v) for v in p.velocity), f"{name}@{frac} : velocity non finie pour {p.player_id}"
            assert all(math.isfinite(v) for v in p.acceleration), f"{name}@{frac} : acceleration non finie pour {p.player_id}"
        assert all(math.isfinite(v) for v in ball.velocity)
