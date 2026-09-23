import hashlib
import random

import pytest

from ligue1sim.animation.motion import (
    MAX_SPEED_MPS,
    _apply_avoidance,
    _ease_progress,
    _real_distance_m,
    _start_offset,
    interpolate,
    max_speed_normalized,
)
from ligue1sim.animation.templates import BUILDERS
from ligue1sim.animation.types import BackgroundTrack, BallState, Keyframe, RosterEntry, Sequence
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PitchPoint, Zone
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


def _start_positions(lineup: Lineup) -> dict[int, PitchPoint]:
    return {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


def _goal_event(*, assist: str | None = "mc0") -> GoalEvent:
    return GoalEvent(
        club_name="Test FC", scorer="bu", assist=assist, minute=34, penalty=False,
        zone=_SCORER_ZONE, assist_zone=_ASSIST_ZONE if assist else None,
    )


def _sequence(name: str, lineup: Lineup):
    return BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))


def _all_sequences(lineup: Lineup):
    return {name: _sequence(name, lineup) for name in BUILDERS}


class TestEaseProgress:
    def test_boundaries_are_exact(self):
        assert _ease_progress(0.0) == 0.0
        assert _ease_progress(1.0) == 1.0

    def test_is_monotonic_non_decreasing(self):
        values = [_ease_progress(s / 200) for s in range(201)]
        assert all(b >= a for a, b in zip(values, values[1:]))

    def test_out_of_range_inputs_are_clamped(self):
        assert _ease_progress(-1.0) == 0.0
        assert _ease_progress(2.0) == 1.0


class TestMaxSpeedNormalized:
    def test_every_documented_poste_has_a_positive_speed(self):
        for poste in MAX_SPEED_MPS:
            assert max_speed_normalized(poste) > 0

    def test_unknown_poste_falls_back_to_default(self):
        assert max_speed_normalized("XX") == max_speed_normalized(None)

    def test_goalkeeper_is_the_slowest(self):
        assert max_speed_normalized("GK") < max_speed_normalized("BU")


class TestStartOffset:
    def test_is_within_the_expected_range(self):
        duration = 10.0
        for player_id in range(50):
            offset = _start_offset(player_id, duration)
            assert 0.0 <= offset <= 0.3 * duration

    def test_is_deterministic(self):
        assert _start_offset(7, 8.0) == _start_offset(7, 8.0)

    def test_different_players_generally_get_different_offsets(self):
        offsets = {_start_offset(pid, 8.0) for pid in range(20)}
        assert len(offsets) > 1


class TestVelocityContinuity:
    """"|position(t+dt) - position(t)| <= v_max * dt * 1.1" pour tout t et
    tout joueur -- vérifié densément sur les 12 gabarits."""

    DT = 0.05
    TOLERANCE = 1.1

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_no_player_ever_exceeds_its_max_speed_by_more_than_ten_percent(self, name):
        lineup = _lineup()
        sequence = _sequence(name, lineup)

        t = sequence.keyframes[0].t
        end = sequence.keyframes[-1].t
        previous = interpolate(sequence, t)
        t += self.DT
        while t <= end + 1e-9:
            current = interpolate(sequence, t)
            for player_id, state in current.players.items():
                prev_state = previous.players[player_id]
                dist_m = _real_distance_m((prev_state.x, prev_state.y), (state.x, state.y))
                dist_normalized_equiv = dist_m / 105.0  # même échelle que max_speed_normalized
                poste = sequence.roster[player_id].poste
                v_max = max_speed_normalized(poste)
                bound = v_max * self.DT * self.TOLERANCE
                assert dist_normalized_equiv <= bound, (
                    f"{name}: joueur {player_id} a parcouru {dist_normalized_equiv:.5f} entre "
                    f"t={t - self.DT:.2f} et t={t:.2f}, borne={bound:.5f} (poste={poste})"
                )
            previous = current
            t += self.DT


class TestDeterminism:
    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_two_calls_with_the_same_arguments_produce_a_bit_identical_frame_state(self, name):
        lineup = _lineup()
        sequence = _sequence(name, lineup)

        t = sequence.duration * 0.37
        first = interpolate(sequence, t)
        second = interpolate(sequence, t)

        assert first == second


class TestNonCollision:
    """Sur les 12 gabarits x 100 tirages (instants aléatoires), jamais deux
    joueurs à moins de 0,5 m l'un de l'autre."""

    MIN_DISTANCE_M = 0.5
    NB_DRAWS = 100

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_players_never_end_up_closer_than_half_a_metre(self, name):
        lineup = _lineup()
        sequence = _sequence(name, lineup)
        # Seed stable (sha256, pas hash() qui varie d'un process Python à
        # l'autre) -- reproductible d'un run de la suite de tests à l'autre.
        seed = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "big")
        rng = random.Random(seed)

        for _ in range(self.NB_DRAWS):
            t = rng.uniform(sequence.keyframes[0].t, sequence.keyframes[-1].t)
            frame = interpolate(sequence, t)
            positions = [(state.x, state.y) for state in frame.players.values()]
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    dist_m = _real_distance_m(positions[i], positions[j])
                    assert dist_m >= self.MIN_DISTANCE_M, f"{name} à t={t:.2f} : {dist_m:.3f} m"


class TestAvoidance:
    def test_two_coincident_players_are_pushed_apart(self):
        positions = {"a": (0.5, 0.5), "b": (0.5, 0.5)}
        adjusted = _apply_avoidance(positions)
        assert _real_distance_m(adjusted["a"], adjusted["b"]) > 0.0

    def test_players_already_far_apart_are_left_untouched(self):
        positions = {"a": (0.1, 0.1), "b": (0.9, 0.9)}
        adjusted = _apply_avoidance(positions)
        assert adjusted == positions

    def test_avoidance_is_deterministic(self):
        positions = {"a": (0.5, 0.5), "b": (0.5, 0.5), "c": (0.5, 0.51)}
        assert _apply_avoidance(positions) == _apply_avoidance(positions)


class TestFrameStateShape:
    def test_ball_field_is_always_none_in_this_phase(self):
        lineup = _lineup()
        sequence = _sequence("contre_attaque", lineup)
        frame = interpolate(sequence, sequence.duration / 2)
        assert frame.ball is None

    def test_covers_every_player_of_the_sequence(self):
        lineup = _lineup()
        sequence = _sequence("contre_attaque", lineup)
        frame = interpolate(sequence, 0.0)
        assert set(frame.players) == set(sequence.keyframes[0].players)

    def test_scorer_is_the_ball_carrier_at_the_final_instant(self):
        lineup = _lineup()
        sequence = _sequence("contre_attaque", lineup)
        scorer_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "scorer")

        frame = interpolate(sequence, sequence.duration)
        assert frame.players[scorer_id].is_ball_carrier

    def test_primary_roles_have_no_reaction_delay(self):
        # "scorer" (rôle primaire, voir _is_primary_role) doit être déjà en
        # mouvement à un instant où "support1" (comportement 4, "runner")
        # n'a pas encore commencé à réagir -- gabarit "corner", le seul où
        # support1 bouge réellement (ANCHOR_SCORER, pas ANCHOR_STATIC comme
        # dans les autres gabarits, voir templates.py).
        lineup = _lineup()
        sequence = _sequence("corner", lineup)
        scorer_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "scorer")
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")

        offset = _start_offset(support_id, sequence.duration)
        assert offset > 0
        t = offset / 2

        frame = interpolate(sequence, t)
        scorer_start = sequence.keyframes[0].players[scorer_id]
        support_start = sequence.keyframes[0].players[support_id]

        # support1 n'a pas encore atteint son propre décalage : encore
        # exactement à sa position de keyframe initiale. Le buteur, sans
        # décalage, a déjà bougé.
        assert (frame.players[support_id].x, frame.players[support_id].y) == support_start
        assert (frame.players[scorer_id].x, frame.players[scorer_id].y) != scorer_start


def _background_sequence(*, active_pos=(0.1, 0.1), background_start=(0.9, 0.9), drift=(0.03, -0.02), duration=4.0):
    """Sequence minimale à 1 joueur actif (keyframes) + 1 joueur "décor"
    (background) -- ils démarrent volontairement loin l'un de l'autre pour
    ne jamais déclencher `_apply_avoidance` (voir `_AVOIDANCE_TRIGGER_M`),
    afin d'isoler le comportement du drift lui-même."""
    ball = BallState(x=active_pos[0], y=active_pos[1], z=0.0, spin=0.0, owner_id="active")
    keyframes = [
        Keyframe(t=0.0, ball=ball, players={"active": active_pos}, tag=""),
        Keyframe(t=duration, ball=ball, players={"active": active_pos}, tag=""),
    ]
    roster = {
        "active": RosterEntry(nom="Actif", poste="BU", role="scorer", numero=9, team_side="scorer"),
        "decor": RosterEntry(nom="Decor", poste="DC", role=None, numero=4, team_side="opponent"),
    }
    background = {"decor": BackgroundTrack(start=background_start, drift=drift)}
    return Sequence(
        event_ref="ref", keyframes=keyframes, duration=duration, meta={}, roster=roster, background=background
    )


class TestBackgroundInterpolation:
    """Point 1 du bilan simulation physique (23/09/2026) : les joueurs
    "décor" (`sequence.background`) doivent apparaître dans `interpolate`
    au même titre que les joueurs actifs, avec un mouvement dérivé du
    drift (pas de keyframes/Bézier pour eux)."""

    def test_covers_both_active_and_background_players(self):
        sequence = _background_sequence()
        frame = interpolate(sequence, sequence.duration / 2)
        assert set(frame.players) == {"active", "decor"}

    def test_background_player_starts_exactly_at_its_track_start(self):
        sequence = _background_sequence()
        frame = interpolate(sequence, 0.0)
        assert (frame.players["decor"].x, frame.players["decor"].y) == sequence.background["decor"].start

    def test_background_player_reaches_start_plus_drift_at_the_end(self):
        sequence = _background_sequence(background_start=(0.9, 0.9), drift=(0.03, -0.02))
        frame = interpolate(sequence, sequence.duration)
        assert frame.players["decor"].x == pytest.approx(0.93)
        assert frame.players["decor"].y == pytest.approx(0.88)

    def test_background_player_is_never_the_ball_carrier(self):
        sequence = _background_sequence()
        for t in (0.0, sequence.duration / 2, sequence.duration):
            assert not interpolate(sequence, t).players["decor"].is_ball_carrier

    def test_background_player_never_strays_beyond_its_drift_bound(self):
        # Pas de vitesse plafonnée pour le décor (voir _background_position_at)
        # -- mais l'amplitude, elle, ne doit jamais dépasser start+drift.
        sequence = _background_sequence(background_start=(0.9, 0.9), drift=(0.03, -0.02))
        max_reach = _real_distance_m((0.9, 0.9), (0.93, 0.88))
        for i in range(21):
            t = sequence.duration * i / 20
            frame = interpolate(sequence, t)
            dist = _real_distance_m((0.9, 0.9), (frame.players["decor"].x, frame.players["decor"].y))
            assert dist <= max_reach + 1e-9


def _impossible_sequence(*, duration: float = 0.1) -> Sequence:
    """Un keyframe artificiellement impossible : traverser tout le terrain
    (x: 0.0 -> 1.0) en 0.1 s, très au-delà de `v_max` (voir docstring de
    module, "Limite connue et non corrigée"). Sert à caractériser (et
    figer par un test) ce qui se passe quand le repli linéaire lui-même ne
    peut pas couvrir la distance à temps -- aucun des 12 gabarits réels
    n'atteint ce régime (voir docs/simulation_physique_archi.md, "Point B"),
    ce cas est purement synthétique."""
    ball0 = BallState(x=0.0, y=0.5, z=0.0, spin=0.0, owner_id="p")
    ball1 = BallState(x=1.0, y=0.5, z=0.0, spin=0.0, owner_id="p")
    return Sequence(
        event_ref="ref",
        keyframes=[
            Keyframe(t=0.0, ball=ball0, players={"p": (0.0, 0.5)}, tag=""),
            Keyframe(t=duration, ball=ball1, players={"p": (1.0, 0.5)}, tag=""),
        ],
        duration=duration,
        meta={},
        roster={"p": RosterEntry(nom="X", poste="BU", role="scorer", numero=9, team_side="scorer")},
    )


class TestImpossibleSegment:
    """Documenté en tête de motion.py : un segment qui exige plus que
    `v_max` même en ligne droite ne peut pas être "corrigé" par le repli
    linéaire (comportement 2) -- celui-ci garantit seulement qu'aucun
    INSTANT du segment ne dépasse `v_max`, pas que la distance soit
    couverte à temps. Ces tests figent le comportement réel (position en
    retard puis saut à la transition), pour qu'il soit visible et testé
    plutôt que découvert en silence par une future session (`ball.py`)."""

    def test_the_player_falls_short_of_the_target_just_before_the_deadline(self):
        sequence = _impossible_sequence()
        frame = interpolate(sequence, sequence.duration - 1e-4)
        # v_max("BU") * duration < 1.0 (la distance totale) -- ne peut pas
        # être arrivé à ce stade, même en ligne droite à pleine vitesse.
        assert frame.players["p"].x < 0.99

    def test_the_player_snaps_to_the_keyframe_target_exactly_at_the_deadline(self):
        sequence = _impossible_sequence()
        frame = interpolate(sequence, sequence.duration)
        assert frame.players["p"].x == pytest.approx(1.0)

    def test_the_snap_produces_an_anomalous_velocity_spike(self):
        # Conséquence directe du saut de position : la différence finie
        # (vx) explose au moment de la transition -- documenté, pas corrigé
        # (voir docstring de module).
        sequence = _impossible_sequence()
        v_max = max_speed_normalized("BU")
        frame = interpolate(sequence, sequence.duration)
        assert abs(frame.players["p"].vx) > v_max * 100

    def test_well_before_the_deadline_the_player_still_respects_v_max(self):
        # Comportement 2 tient bon TANT QU'on reste loin de la transition --
        # seul l'instant du saut est anormal, pas tout le segment.
        sequence = _impossible_sequence()
        v_max = max_speed_normalized("BU")
        frame = interpolate(sequence, sequence.duration * 0.5)
        assert abs(frame.players["p"].vx) <= v_max * 1.1
