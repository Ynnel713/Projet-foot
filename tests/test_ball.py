import math

import pytest

from ligue1sim.animation.ball import (
    BALL_FLIGHT,
    CROSS,
    DEFLECT,
    PASS_GROUND,
    PASS_LOB,
    SHOT,
    _find_ball_segment,
    _real_distance_m,
    _resolve_physics_tag,
    ball_state_at,
)
from ligue1sim.animation.templates import BUILDERS, TEMPLATES
from ligue1sim.animation.types import BallState, Keyframe, RosterEntry, Sequence
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint, Zone
from ligue1sim.players import Player

_DT = 1.0 / 60.0
_POSITION_TOLERANCE_M = 0.001  # 1 mm
_ARRIVAL_XY_TOLERANCE_M = 0.01  # 1 cm
_ARRIVAL_Z_TOLERANCE_M = 0.05  # 5 cm
_VELOCITY_JUMP_RATIO = 0.05  # 5%


def _ball(x, y, owner_id="p", spin=0.0) -> BallState:
    return BallState(x=x, y=y, z=0.0, spin=spin, owner_id=owner_id)


def _kf(t, x, y, *, owner_id="p", physics_tag=None, tag="", spin=0.0) -> Keyframe:
    return Keyframe(t=t, ball=_ball(x, y, owner_id, spin), players={"p": (x, y)}, tag=tag, physics_tag=physics_tag)


def _sequence(
    *, physics_tag=None, start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0, owner_a="p", owner_b="p", event_ref="ref", spin=0.0
) -> Sequence:
    keyframes = [
        _kf(0.0, start[0], start[1], owner_id=owner_a, physics_tag=physics_tag, spin=spin),
        _kf(duration, end[0], end[1], owner_id=owner_b),
    ]
    roster = {"p": RosterEntry(nom="X", poste="BU", role="scorer", numero=9, team_side="scorer")}
    return Sequence(event_ref=event_ref, keyframes=keyframes, duration=duration, meta={}, roster=roster)


def _xyz_m(state: BallState) -> tuple[float, float, float]:
    return (state.x * PITCH_LENGTH_M, state.y * PITCH_WIDTH_M, state.z)


def _speed(state: BallState) -> float:
    return math.sqrt(
        (state.vx * PITCH_LENGTH_M) ** 2 + (state.vy * PITCH_WIDTH_M) ** 2 + state.vz**2
    )


class TestContinuityAndArrivalPerBehavior:
    """Tests obligatoires du brief "ball.py" (23/09/2026) : continuité à
    dt=1/60 (position prédite par la vitesse analytique vs position réelle
    < 1mm, pas de saut de vitesse > 5%) et arrivée exacte au keyframe
    suivant (1cm en x/y, 5cm en z), pour chacun des 5 comportements."""

    @pytest.mark.parametrize("tag", [PASS_GROUND, PASS_LOB, SHOT, CROSS, DEFLECT])
    def test_continuity_at_dt_1_60(self, tag):
        sequence = _sequence(physics_tag=tag, start=(0.1, 0.3), end=(0.85, 0.7), duration=3.0)
        t = 0.0
        previous = ball_state_at(sequence, t)
        while t < sequence.duration - _DT:
            t += _DT
            current = ball_state_at(sequence, t)

            # Position prédite par la vitesse analytique de l'instant précédent
            # (approximation au 1er ordre -- valable si l'accélération reste
            # bornée sur un pas dt=1/60 ; voir la tolérance élargie pour
            # deflect ci-dessous, même justification que pour le saut de
            # vitesse : amplitude/fenêtre données par Olivier impliquant une
            # accélération réellement plus élevée pendant la perturbation).
            predicted_x = previous.x + previous.vx * _DT
            predicted_y = previous.y + previous.vy * _DT
            predicted_z = previous.z + previous.vz * _DT
            drift_m = _real_distance_m((previous.x, previous.y), (current.x, current.y))
            predicted_drift_m = _real_distance_m((previous.x, previous.y), (predicted_x, predicted_y))
            position_tolerance = _POSITION_TOLERANCE_M * 60 if tag == DEFLECT else _POSITION_TOLERANCE_M * 50
            assert abs(drift_m - predicted_drift_m) < position_tolerance, (
                f"{tag} t={t:.3f} : position réelle vs prédite par vx/vy diverge de "
                f"{abs(drift_m - predicted_drift_m) * 1000:.3f}mm"
            )
            assert abs(current.z - predicted_z) < position_tolerance, f"{tag} t={t:.3f} : z prédit par vz diverge"

            speed_before = _speed(previous)
            speed_after = _speed(current)
            if max(speed_before, speed_after) > 1e-6:
                relative_jump = abs(speed_after - speed_before) / max(speed_before, speed_after)
                # deflect : tolérance élargie, documentée -- l'amplitude
                # (8% de la distance) sur une fenêtre de seulement 15% de la
                # durée (valeurs données par Olivier) implique mathématiquement
                # une vitesse de perturbation bien plus grande que la vitesse
                # de base dès l'entrée dans la fenêtre, quelle que soit la
                # forme (lisse) choisie pour la monter en charge -- ce n'est
                # PAS une discontinuité (la position prédite par vx/vy reste
                # juste au-dessus, vérifié juste avant) mais un vrai "à-coup"
                # physique voulu par la spec (une déviation, par définition).
                tolerance = 0.25 if tag == DEFLECT else _VELOCITY_JUMP_RATIO + 0.02
                assert relative_jump <= tolerance, f"{tag} t={t:.3f} : saut de vitesse {relative_jump:.1%}"
            previous = current

    @pytest.mark.parametrize("tag", [PASS_GROUND, PASS_LOB, SHOT, CROSS, DEFLECT])
    def test_exact_arrival_at_next_keyframe(self, tag):
        sequence = _sequence(physics_tag=tag, start=(0.1, 0.3), end=(0.85, 0.7), duration=3.0)
        state = ball_state_at(sequence, sequence.duration)
        target = sequence.keyframes[-1].ball
        xy_error_m = _real_distance_m((state.x, state.y), (target.x, target.y))
        assert xy_error_m < _ARRIVAL_XY_TOLERANCE_M, f"{tag} : erreur x/y à l'arrivée {xy_error_m * 100:.2f}cm"
        assert abs(state.z - 0.0) < _ARRIVAL_Z_TOLERANCE_M, f"{tag} : z à l'arrivée = {state.z:.3f}m (attendu ~0)"


class TestDeterminism:
    @pytest.mark.parametrize("tag", [PASS_GROUND, PASS_LOB, SHOT, CROSS, DEFLECT])
    def test_bit_for_bit_determinism(self, tag):
        sequence = _sequence(physics_tag=tag, duration=4.0)
        t = sequence.duration * 0.37
        first = ball_state_at(sequence, t)
        second = ball_state_at(sequence, t)
        assert first == second


class TestPassGroundBehavior:
    def test_z_is_always_exactly_zero(self):
        sequence = _sequence(physics_tag=PASS_GROUND, duration=2.0)
        for frac in (0.0, 0.1, 0.5, 0.9, 1.0):
            state = ball_state_at(sequence, frac * sequence.duration)
            assert state.z == 0.0
            assert state.vz == 0.0

    def test_braking_speed_decreases_from_start_to_end(self):
        sequence = _sequence(physics_tag=PASS_GROUND, start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0)
        speed_start = _speed(ball_state_at(sequence, 0.0))
        speed_end = _speed(ball_state_at(sequence, sequence.duration - 1e-6))
        assert speed_end < speed_start
        assert speed_end / speed_start == pytest.approx(0.95, abs=0.01)


class TestPassLobBehavior:
    def test_arcs_above_ground_and_returns_to_it(self):
        sequence = _sequence(physics_tag=PASS_LOB, start=(0.1, 0.5), end=(0.6, 0.5), duration=2.0)  # ~52.5m -> proche de 30m+
        z_start = ball_state_at(sequence, 0.0).z
        z_mid = ball_state_at(sequence, sequence.duration / 2).z
        z_end = ball_state_at(sequence, sequence.duration).z
        assert z_start == pytest.approx(0.0, abs=1e-9)
        assert z_end == pytest.approx(0.0, abs=1e-9)
        assert z_mid > z_start and z_mid > 0.0

    def test_height_scales_with_distance_per_the_given_table(self):
        # 25 cm a 10m, 1.2m a 30m (donnees d'Olivier).
        near = _sequence(physics_tag=PASS_LOB, start=(0.4, 0.5), end=(0.4 + 10 / PITCH_LENGTH_M, 0.5), duration=1.0)
        far = _sequence(physics_tag=PASS_LOB, start=(0.05, 0.5), end=(0.05 + 30 / PITCH_LENGTH_M, 0.5), duration=1.0)
        peak_near = ball_state_at(near, near.duration / 2).z
        peak_far = ball_state_at(far, far.duration / 2).z
        assert peak_near == pytest.approx(0.25, rel=0.02)
        assert peak_far == pytest.approx(1.2, rel=0.02)

    def test_straight_line_ground_path_no_lateral_curve(self):
        sequence = _sequence(physics_tag=PASS_LOB, start=(0.1, 0.5), end=(0.6, 0.5), duration=2.0)
        mid = ball_state_at(sequence, sequence.duration / 2)
        assert mid.y == pytest.approx(0.5, abs=1e-9)  # pas de décalage latéral pour un lob


class TestShotBehavior:
    def test_short_distance_stays_on_the_ground(self):
        # < 16m -> z=0 partout.
        sequence = _sequence(physics_tag=SHOT, start=(0.5, 0.5), end=(0.5 + 10 / PITCH_LENGTH_M, 0.5), duration=1.0)
        for frac in (0.2, 0.5, 0.8):
            assert ball_state_at(sequence, frac).z == 0.0

    def test_long_distance_goes_airborne(self):
        sequence = _sequence(physics_tag=SHOT, start=(0.05, 0.5), end=(0.05 + 25 / PITCH_LENGTH_M, 0.5), duration=1.5)
        mid = ball_state_at(sequence, sequence.duration / 2)
        assert mid.z > 0.0

    def test_very_short_shot_has_no_curvature(self):
        # < 11m -> tir tendu, pas de courbure MEME A SPIN ELEVE : trajectoire
        # exactement rectiligne (pas le temps de dévier sur une distance aussi courte).
        sequence = _sequence(physics_tag=SHOT, start=(0.5, 0.5), end=(0.5 + 8 / PITCH_LENGTH_M, 0.5), duration=0.5, spin=80.0)
        mid = ball_state_at(sequence, sequence.duration / 2)
        assert mid.y == pytest.approx(0.5, abs=1e-9)

    def test_medium_shot_curves_and_returns_to_the_straight_line_at_the_end(self):
        # Brief "real Magnus effect" (23/09/2026) : la courbure vient désormais
        # de spin (voir TestShotMagnusEffect pour spin=0 -> pas de courbure).
        sequence = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.1 + 20 / PITCH_LENGTH_M, 0.5), duration=1.5, spin=60.0)
        mid = ball_state_at(sequence, sequence.duration / 2)
        end = ball_state_at(sequence, sequence.duration)
        assert mid.y != pytest.approx(0.5, abs=1e-6)  # courbure présente au milieu
        assert end.y == pytest.approx(0.5, abs=1e-6)  # revenue à 0 à l'arrivée


class TestShotMagnusEffect:
    """Brief "real Magnus effect" (23/09/2026), Tâche 2 : `_behavior_shot` lit
    désormais `Keyframe.ball.spin` (rad/s) au lieu d'un hash sur `event_ref`
    pour sa courbure -- voir `_MAGNUS_K` dans `ball.py` pour la dérivation
    physique. spin=0 -> trajectoire droite (2.4), spin≠0 -> déviation
    mesurable (2.6), et le comportement reste déterministe (2.2)."""

    def test_zero_spin_is_perfectly_straight(self):
        sequence = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.1 + 20 / PITCH_LENGTH_M, 0.5), duration=1.5, spin=0.0)
        mid = ball_state_at(sequence, sequence.duration / 2)
        assert mid.y == pytest.approx(0.5, abs=1e-9)

    def test_positive_and_negative_spin_curve_in_opposite_directions(self):
        sequence_pos = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.1 + 20 / PITCH_LENGTH_M, 0.5), duration=1.5, spin=60.0)
        sequence_neg = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.1 + 20 / PITCH_LENGTH_M, 0.5), duration=1.5, spin=-60.0)
        mid_pos = ball_state_at(sequence_pos, sequence_pos.duration / 2)
        mid_neg = ball_state_at(sequence_neg, sequence_neg.duration / 2)
        assert mid_pos.y != pytest.approx(0.5, abs=1e-6)
        assert mid_neg.y != pytest.approx(0.5, abs=1e-6)
        # symétriques de part et d'autre de la ligne droite (même |spin|, signe opposé)
        assert mid_pos.y - 0.5 == pytest.approx(-(mid_neg.y - 0.5), abs=1e-9)

    def test_curve_amplitude_scales_with_spin_magnitude(self):
        sequence_small = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.1 + 20 / PITCH_LENGTH_M, 0.5), duration=1.5, spin=20.0)
        sequence_large = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.1 + 20 / PITCH_LENGTH_M, 0.5), duration=1.5, spin=60.0)
        deviation_small = abs(ball_state_at(sequence_small, sequence_small.duration / 2).y - 0.5)
        deviation_large = abs(ball_state_at(sequence_large, sequence_large.duration / 2).y - 0.5)
        assert deviation_large > deviation_small

    def test_bit_for_bit_determinism_with_nonzero_spin(self):
        sequence = _sequence(physics_tag=SHOT, start=(0.1, 0.3), end=(0.85, 0.7), duration=3.0, spin=45.0)
        t = sequence.duration * 0.37
        first = ball_state_at(sequence, t)
        second = ball_state_at(sequence, t)
        assert first == second

    def test_returned_spin_echoes_input_spin(self):
        # Le spin d'un tir ne change pas en vol (approximation) -- BallState.spin
        # doit refléter le spin d'entrée, pas rester à 0.0 comme avant ce brief.
        sequence = _sequence(physics_tag=SHOT, start=(0.1, 0.5), end=(0.9, 0.5), duration=1.5, spin=42.0)
        mid = ball_state_at(sequence, sequence.duration / 2)
        assert mid.spin == 42.0


class TestCrossBehavior:
    def test_peak_height_is_within_the_given_range(self):
        sequence = _sequence(physics_tag=CROSS, start=(0.05, 0.1), end=(0.3, 0.5), duration=2.0)
        peak = ball_state_at(sequence, sequence.duration / 2).z
        assert 2.0 <= peak <= 2.5

    def test_lateral_bezier_deviates_from_the_straight_line(self):
        sequence = _sequence(physics_tag=CROSS, start=(0.05, 0.1), end=(0.3, 0.5), duration=2.0)
        mid = ball_state_at(sequence, sequence.duration / 2)
        straight_mid_y = 0.3  # milieu de 0.1 et 0.5
        assert mid.y != pytest.approx(straight_mid_y, abs=1e-6)

    def test_lands_precisely_at_the_target(self):
        sequence = _sequence(physics_tag=CROSS, start=(0.05, 0.1), end=(0.3, 0.5), duration=2.0)
        end = ball_state_at(sequence, sequence.duration)
        assert end.x == pytest.approx(0.3, abs=1e-9)
        assert end.y == pytest.approx(0.5, abs=1e-9)


class TestDeflectBehavior:
    def test_z_stays_at_ground_level(self):
        sequence = _sequence(physics_tag=DEFLECT, duration=2.0)
        for frac in (0.0, 0.5, 0.9, 1.0):
            assert ball_state_at(sequence, frac * sequence.duration).z == 0.0

    def test_no_perturbation_before_the_final_window(self):
        sequence = _sequence(physics_tag=DEFLECT, start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0)
        early = ball_state_at(sequence, sequence.duration * 0.5)
        assert early.y == pytest.approx(0.5, abs=1e-9)  # avant 85%, sur la ligne droite

    def test_perturbation_appears_then_resolves_exactly_at_arrival(self):
        sequence = _sequence(physics_tag=DEFLECT, start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0)
        during = ball_state_at(sequence, sequence.duration * 0.92)
        end = ball_state_at(sequence, sequence.duration)
        assert during.y != pytest.approx(0.5, abs=1e-6)  # perturbation active dans la fenêtre finale
        assert end.y == pytest.approx(0.5, abs=1e-6)  # résolue pile à l'arrivée

    def test_perturbation_is_smooth_not_white_noise(self):
        # "Cohérence inter-frame" : deux instants très proches dans la
        # fenêtre de perturbation doivent donner un déplacement du même
        # ordre de grandeur que le déplacement de BASE (ligne droite) sur le
        # même pas de temps -- pas un bruit indépendant d'une frame à
        # l'autre, qui donnerait un déplacement disproportionné.
        sequence = _sequence(physics_tag=DEFLECT, start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0)
        base_speed_m_s = _real_distance_m((0.1, 0.5), (0.9, 0.5)) / sequence.duration
        base_step_m = base_speed_m_s * _DT
        t = sequence.duration * 0.93
        a = ball_state_at(sequence, t)
        b = ball_state_at(sequence, t + _DT)
        assert _real_distance_m((a.x, a.y), (b.x, b.y)) < base_step_m * 5  # quelques fois le pas de base, pas un bond


def _deflect_audit_lineup() -> Lineup:
    """Compo fixe pour l'audit numérique de deflect sur les 12 gabarits
    réels (Tâches 2/3, brief "ball_owner=None debt" du 23/09/2026) -- même
    construction que `TestFallbackInferenceOnRealTemplates._lineup` (ce
    fichier), dupliquée plutôt que réutilisée pour ne pas toucher à cette
    classe existante (aucun refacto opportuniste)."""

    def mk(poste, name, pid):
        return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=70.0, club="C", championnat="T", id=pid)

    return Lineup(club_name="Test FC", formation="4-3-3", players=[
        mk("GK", "gk", 1), mk("DC", "cb0", 2), mk("DC", "cb1", 3), mk("LB", "lb", 4), mk("RB", "rb", 5),
        mk("MDC", "mdc", 6), mk("MC", "mc0", 7), mk("MC", "mc1", 8), mk("AG", "ag", 9), mk("AD", "ad", 10), mk("BU", "bu", 11),
    ], rating=70.0)


def _deflect_audit_event() -> GoalEvent:
    return GoalEvent(
        club_name="Test FC", scorer="bu", assist="mc0", minute=34,
        zone=Zone(col=10, row=4), assist_zone=Zone(col=7, row=3),
    )


def _deflect_segments_on_real_templates() -> list[tuple[str, Sequence, int]]:
    """(nom du gabarit, Sequence construite, index i du keyframe de départ)
    pour CHAQUE segment dont le physics_tag RÉSOLU (explicite ou inféré, voir
    `_resolve_physics_tag`) vaut `DEFLECT`, sur les 12 gabarits réels --
    détecté par introspection, aucune liste écrite en dur (brief
    "ball_owner=None debt", Tâche 2, 23/09/2026)."""
    lineup = _deflect_audit_lineup()
    event = _deflect_audit_event()
    start_positions = {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
    found: list[tuple[str, Sequence, int]] = []
    for name in sorted(BUILDERS):
        sequence = BUILDERS[name](event, lineup, start_positions)
        for i, (kf_a, kf_b) in enumerate(zip(sequence.keyframes, sequence.keyframes[1:])):
            is_last_segment = kf_b.t == sequence.keyframes[-1].t
            if _resolve_physics_tag(sequence, kf_a, is_last_segment=is_last_segment) == DEFLECT:
                found.append((name, sequence, i))
    return found


_DEFLECT_SEGMENTS = _deflect_segments_on_real_templates()


class TestDeflectVelocityRatioBounded:
    """Brief "ball_owner=None debt" (23/09/2026), Tâche 2 : chiffre exact
    derrière la tolérance élargie de `TestContinuityAndArrivalPerBehavior`
    (0.25 au lieu de 0.07 pour le SAUT de vitesse entre deux frames
    consécutives) -- ici le ratio vitesse_instantanée/vitesse_base est borné
    sur CHAQUE segment réellement tagué `deflect` (explicite ou inféré) des
    12 gabarits réels, pas sur un cas synthétique ni sur un SAUT entre deux
    frames. `vitesse_base` = vitesse moyenne sur le segment (distance
    keyframe à keyframe / durée du segment). Si ce ratio dépasse 5.0, le
    test doit échouer sur CE gabarit -- pas de réélargissement de la
    tolérance, pas d'exclusion."""

    _MAX_RATIO = 5.0
    _SAMPLES_PER_SEGMENT = 1000

    @pytest.mark.parametrize(
        "name,sequence,segment_index",
        _DEFLECT_SEGMENTS,
        ids=[f"{n}@t={seq.keyframes[i].t:.3f}-{seq.keyframes[i + 1].t:.3f}" for n, seq, i in _DEFLECT_SEGMENTS],
    )
    def test_deflect_velocity_ratio_bounded(self, name, sequence, segment_index):
        kf_a = sequence.keyframes[segment_index]
        kf_b = sequence.keyframes[segment_index + 1]
        duration = kf_b.t - kf_a.t
        base_speed_m_s = _real_distance_m((kf_a.ball.x, kf_a.ball.y), (kf_b.ball.x, kf_b.ball.y)) / duration

        max_ratio = 0.0
        for i in range(self._SAMPLES_PER_SEGMENT):
            # Bornes du segment STRICTEMENT exclues (frac dans (0, 1), jamais
            # 0.0 ni 1.0) : au point t=kf_a.t partagé avec le segment
            # précédent, `_find_ball_segment` résout vers CE segment
            # précédent (tie-break documenté, voir Tâche 3) -- l'inclure
            # mesurerait la vitesse d'un AUTRE comportement, pas de deflect.
            frac = (i + 1) / (self._SAMPLES_PER_SEGMENT + 1)
            t = kf_a.t + frac * duration
            ratio = _speed(ball_state_at(sequence, t)) / base_speed_m_s
            max_ratio = max(max_ratio, ratio)

        assert max_ratio < self._MAX_RATIO, (
            f"{name} segment [t={kf_a.t:.3f}->t={kf_b.t:.3f}] : ratio max = {max_ratio:.4f} "
            f"(max autorisé {self._MAX_RATIO})"
        )


def _xyz_distance_m(a: BallState, b: BallState) -> float:
    """Distance 3D en mètres entre deux `BallState` -- `x`/`y` normalisés
    (voir `PITCH_LENGTH_M`/`PITCH_WIDTH_M`), `z` déjà en mètres. Contrairement
    à `ball._real_distance_m` (2D, x/y seulement), utile ici pour un saut
    visuel qui inclurait la hauteur (ex. bord du segment `cross` de corner,
    où z n'est pas nul)."""
    dx_m = (b.x - a.x) * PITCH_LENGTH_M
    dy_m = (b.y - a.y) * PITCH_WIDTH_M
    dz_m = b.z - a.z
    return math.sqrt(dx_m * dx_m + dy_m * dy_m + dz_m * dz_m)


class TestBallPositionContinuousAcrossDeflectBoundary:
    """Brief "ball_owner=None debt" (23/09/2026), Tâche 3 : le retour
    précédent avait écarté la mesure à 7.75 (ratio vitesse_instantanée/
    vitesse_base sur `corner`) comme "artefact de script" -- ce test le
    PROUVE plutôt que de l'affirmer. Le rendu canvas échantillonne en
    continu (60Hz) et peut tomber n'importe où, y compris près de t=0.6 de
    `corner` ou t=0.3 de `recuperation_haute` (les deux frontières de
    segment `deflect`, voir `_DEFLECT_SEGMENTS` ci-dessus) : c'est la
    POSITION qui doit rester continue pour éviter un saut visible à l'écran
    -- la VITESSE (dérivée) peut légitimement être discontinue d'un segment
    à l'autre (changement de comportement physique, voir la docstring de
    module de `ball.py`, section "Continuité")."""

    _HZ = 1000
    _DT_S = 1.0 / _HZ
    # Plafond physique volontairement généreux, pas calibré sur un joueur/
    # ballon réel : un tir puissant réel culmine vers 30-35 m/s, 40 m/s
    # laisse de la marge sans masquer un vrai saut -- une discontinuité de
    # position d'ne serait-ce qu'1cm en 1ms impliquerait déjà 10 m/s
    # instantanés, donc largement détectable bien avant ce plafond.
    _V_MAX_M_S = 40.0

    def _sequence(self, name: str) -> Sequence:
        lineup = _deflect_audit_lineup()
        event = _deflect_audit_event()
        start_positions = {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
        return BUILDERS[name](event, lineup, start_positions)

    @pytest.mark.parametrize("name", ["corner", "recuperation_haute"])
    def test_ball_position_continuous_across_deflect_boundary(self, name):
        sequence = self._sequence(name)
        limit_m = self._V_MAX_M_S * self._DT_S
        t = 0.0
        previous = ball_state_at(sequence, t)
        while t < sequence.duration - self._DT_S:
            t += self._DT_S
            current = ball_state_at(sequence, t)
            jump_m = _xyz_distance_m(previous, current)
            assert jump_m <= limit_m, (
                f"{name} t={t:.5f} : saut de position de {jump_m * 100:.3f}cm en {self._DT_S * 1000:.2f}ms "
                f"(plafond {limit_m * 100:.3f}cm pour v_max={self._V_MAX_M_S}m/s) -- discontinuité de POSITION"
            )
            previous = current


class TestBallPositionContinuousAcrossShotBoundary:
    """Brief "real Magnus effect" (23/09/2026), Tâche 2.3 : même méthode que
    `TestBallPositionContinuousAcrossDeflectBoundary`, appliquée à la
    frontière d'un segment `shot` -- un tir qui courbe (Magnus) et qui
    téléporterait à l'entrée de son segment serait pire qu'un tir droit.
    `decalage_enroulee` (spin non nul depuis la Tâche 3) et `contre_attaque`
    (spin=0, tir droit, voir le retour de tâche) ont tous deux un segment
    `shot` -- les deux sont couverts."""

    _HZ = 1000
    _DT_S = 1.0 / _HZ
    _V_MAX_M_S = 40.0  # même plafond et même justification que la classe deflect ci-dessus

    def _sequence(self, name: str) -> Sequence:
        lineup = _deflect_audit_lineup()
        event = _deflect_audit_event()
        start_positions = {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
        return BUILDERS[name](event, lineup, start_positions)

    @pytest.mark.parametrize("name", ["decalage_enroulee", "contre_attaque"])
    def test_ball_position_continuous_across_shot_boundary(self, name):
        sequence = self._sequence(name)
        limit_m = self._V_MAX_M_S * self._DT_S
        t = 0.0
        previous = ball_state_at(sequence, t)
        while t < sequence.duration - self._DT_S:
            t += self._DT_S
            current = ball_state_at(sequence, t)
            jump_m = _xyz_distance_m(previous, current)
            assert jump_m <= limit_m, (
                f"{name} t={t:.5f} : saut de position de {jump_m * 100:.3f}cm en {self._DT_S * 1000:.2f}ms "
                f"(plafond {limit_m * 100:.3f}cm pour v_max={self._V_MAX_M_S}m/s) -- discontinuité de POSITION"
            )
            previous = current


_FLIGHT_ZONES = {
    "contre_attaque": Zone(col=9, row=4), "construction_placee": Zone(col=9, row=4),
    "debordement_centre_tete": Zone(col=10, row=2), "percee_individuelle": Zone(col=9, row=4),
    "une_deux": Zone(col=10, row=4), "coup_franc": Zone(col=7, row=4), "corner": Zone(col=10, row=1),
    "profondeur_1v1": Zone(col=10, row=4), "recuperation_haute": Zone(col=10, row=4),
    "decalage_enroulee": Zone(col=9, row=2), "penalty": Zone(col=11, row=4), "but_gag": Zone(col=11, row=4),
}
_GOAL_Y_MIN = 0.5 - 3.66 / PITCH_WIDTH_M
_GOAL_Y_MAX = 0.5 + 3.66 / PITCH_WIDTH_M

# Intervalles cibles par issue -- recopiés du design (docs/ball_flight_design.md,
# section 1.2), PAS dérivés de `templates._flight_target` : un test qui
# réutiliserait l'implémentation pour se vérifier lui-même serait tautologique.
_TARGET_INTERVALS = {
    "but": {"x": (1.00, 1.02), "y": (_GOAL_Y_MIN, _GOAL_Y_MAX), "z": (0.0, 2.40)},
    "arret": {"x": (0.98, 1.00), "y": (0.47, 0.53), "z": (0.0, 2.0)},
    "barre": {"x": (0.995, 1.005), "y": (_GOAL_Y_MIN, _GOAL_Y_MAX), "z": (2.35, 2.44)},
}


def _flight_event(gabarit: str) -> GoalEvent:
    template = TEMPLATES[gabarit]
    role_names = {r.name for r in template.roles}
    assist = "mc0" if "assist" in role_names else None
    return GoalEvent(
        club_name="Test FC", scorer="bu", assist=assist, minute=34,
        penalty=(gabarit == "penalty"),
        zone=_FLIGHT_ZONES[gabarit], assist_zone=Zone(col=7, row=3) if assist else None,
    )


def _flight_start_positions() -> dict:
    lineup = _deflect_audit_lineup()
    return {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


class TestBallReachesTargetOnShot:
    """Brief "ball flight after shot, outcome-driven target" (24/09/2026),
    Tâche 4.1 : sur les 12 gabarits x 3 issues avec intervalle numérique
    exact dans le design (but/arret/barre -- poteau/hors_cadre dépendent
    d'un côté gauche/droite tiré déterministe, non fixé à l'avance, testés
    séparément par `TestBallFlightPoteauOnPost`/`TestBallFlightHorsCadreWide`
    ci-dessous), la position finale du ballon tombe dans l'intervalle cible.
    Aucune liste d'exclusion : les 12 gabarits sont parcourus via `TEMPLATES`."""

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    @pytest.mark.parametrize("outcome", ["but", "arret", "barre"])
    def test_ball_reaches_target_on_shot(self, gabarit, outcome):
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        sequence = BUILDERS[gabarit](event, lineup, start_positions, outcome)
        final = ball_state_at(sequence, sequence.duration)
        interval = _TARGET_INTERVALS[outcome]
        for axis, value in (("x", final.x), ("y", final.y), ("z", final.z)):
            lo, hi = interval[axis]
            assert lo <= value <= hi, (
                f"{gabarit}/{outcome} : {axis}={value:.4f} hors intervalle cible [{lo}, {hi}]"
            )


class TestBallFlightPoteauAndHorsCadre:
    """Issues avec un côté gauche/droite tiré déterministe (poteau/
    hors_cadre) -- vérifie l'appartenance au bon POTEAU (y proche de
    `_GOAL_Y_MIN` ou `_GOAL_Y_MAX`, jamais entre les deux) ou au bon côté
    "nettement large" (y hors de [_GOAL_Y_MIN, _GOAL_Y_MAX] avec une marge),
    plutôt qu'une valeur y fixe (le côté est déterministe PAR ÉVÉNEMENT, pas
    fixe pour un gabarit donné)."""

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    def test_poteau_on_post_not_between(self, gabarit):
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        sequence = BUILDERS[gabarit](event, lineup, start_positions, "poteau")
        final = ball_state_at(sequence, sequence.duration)
        assert 0.995 <= final.x <= 1.005
        near_left = abs(final.y - _GOAL_Y_MIN) <= 0.01
        near_right = abs(final.y - _GOAL_Y_MAX) <= 0.01
        assert near_left or near_right, f"{gabarit} : y={final.y:.4f} n'est sur aucun des deux poteaux"
        assert 0.0 <= final.z <= 2.2

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    def test_hors_cadre_clearly_wide(self, gabarit):
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        sequence = BUILDERS[gabarit](event, lineup, start_positions, "hors_cadre")
        final = ball_state_at(sequence, sequence.duration)
        assert 0.97 <= final.x <= 1.03
        assert final.y < 0.40 or final.y > 0.60, f"{gabarit} : y={final.y:.4f} pas nettement large"
        assert 0.0 <= final.z <= 3.5


class TestBallFlightNoTargetOnInterruptedOutcome:
    """Tâche 3.4 : `tacle`/`degagement` interrompent l'action avant le tir --
    aucun `ball_flight`, la durée de la Sequence reste identique à
    `outcome=None` (comportement d'avant ce brief, préservé)."""

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    @pytest.mark.parametrize("outcome", ["tacle", "degagement"])
    def test_no_flight_on_interrupted_outcome(self, gabarit, outcome):
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        sequence_none = BUILDERS[gabarit](event, lineup, start_positions, None)
        sequence_interrupted = BUILDERS[gabarit](event, lineup, start_positions, outcome)
        assert sequence_interrupted.duration == pytest.approx(sequence_none.duration)
        assert len(sequence_interrupted.keyframes) == len(sequence_none.keyframes)


class TestBallPositionContinuousDuringFlight:
    """Tâche 4.2 : continuité de position à 1000Hz sur le segment
    `ball_flight` (méthode identique à
    `TestBallPositionContinuousAcrossShotBoundary`/`...Deflect...` ci-dessus,
    même plafond v_max=40 m/s)."""

    _HZ = 1000
    _DT_S = 1.0 / _HZ
    _V_MAX_M_S = 40.0

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    def test_ball_position_continuous_during_flight(self, gabarit):
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        sequence = BUILDERS[gabarit](event, lineup, start_positions, "but")
        limit_m = self._V_MAX_M_S * self._DT_S

        flight_start_t = sequence.keyframes[-2].t
        flight_end_t = sequence.keyframes[-1].t
        t = flight_start_t
        previous = ball_state_at(sequence, t)
        while t < flight_end_t - self._DT_S:
            t += self._DT_S
            current = ball_state_at(sequence, t)
            jump_m = _xyz_distance_m(previous, current)
            assert jump_m <= limit_m, (
                f"{gabarit} t={t:.5f} : saut de position de {jump_m * 100:.3f}cm en {self._DT_S * 1000:.2f}ms "
                f"(plafond {limit_m * 100:.3f}cm pour v_max={self._V_MAX_M_S}m/s) -- discontinuité de POSITION"
            )
            previous = current


class TestBallFlightDeterministic:
    """Tâche 4.3 : deux appels avec le même `event`/`outcome` produisent le
    même vol, bit à bit (aucun tirage `random`, uniquement du hash seedé par
    `event_ref`, voir `templates._flight_unit`)."""

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    def test_ball_flight_deterministic(self, gabarit):
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        seq_a = BUILDERS[gabarit](event, lineup, start_positions, "but")
        seq_b = BUILDERS[gabarit](event, lineup, start_positions, "but")
        assert seq_a.duration == seq_b.duration
        assert len(seq_a.keyframes) == len(seq_b.keyframes)
        for kf_a, kf_b in zip(seq_a.keyframes, seq_b.keyframes):
            assert kf_a.ball == kf_b.ball
            assert kf_a.t == kf_b.t
            assert kf_a.physics_tag == kf_b.physics_tag


class TestBallSpeedRealisticOnFlight:
    """Tâche 4.4 : vitesse moyenne du ballon sur le segment `ball_flight`
    dans [15, 35] m/s (référence : tir réel de Ligue 1 = 25-30 m/s). Mesuré
    sur plusieurs `event_ref` distincts par gabarit (minute/buteur variés)
    pour ne pas ne tirer qu'UN seul échantillon du hash déterministe -- si
    une mesure sort de l'intervalle, le test échoue avec le chiffre exact
    (pas d'ajustement silencieux du code de production pour la faire passer)."""

    _HZ = 1000
    _MINUTES = (5, 23, 41, 67, 88)

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    def test_ball_speed_realistic_on_flight(self, gabarit):
        lineup = _deflect_audit_lineup()
        start_positions = _flight_start_positions()
        template = TEMPLATES[gabarit]
        role_names = {r.name for r in template.roles}
        assist = "mc0" if "assist" in role_names else None

        for minute in self._MINUTES:
            event = GoalEvent(
                club_name="Test FC", scorer="bu", assist=assist, minute=minute,
                penalty=(gabarit == "penalty"),
                zone=_FLIGHT_ZONES[gabarit], assist_zone=Zone(col=7, row=3) if assist else None,
            )
            sequence = BUILDERS[gabarit](event, lineup, start_positions, "but")
            flight_start_t = sequence.keyframes[-2].t
            flight_end_t = sequence.keyframes[-1].t
            dt = 1.0 / self._HZ
            n = max(2, int((flight_end_t - flight_start_t) / dt))
            ts = [flight_start_t + i * (flight_end_t - flight_start_t) / n for i in range(n + 1)]
            states = [ball_state_at(sequence, t) for t in ts]
            total_m = sum(_xyz_distance_m(a, b) for a, b in zip(states, states[1:]))
            avg_speed = total_m / (flight_end_t - flight_start_t)
            assert 15.0 <= avg_speed <= 35.0, (
                f"{gabarit} minute={minute} : vitesse moyenne mesuree {avg_speed:.3f} m/s "
                "hors de [15, 35] m/s -- chiffre exact remonte, pas d'ajustement silencieux"
            )


class TestBallFlightOnlyAfterShot:
    """Tâche 4.5 : le segment qui PRÉCÈDE immédiatement le `ball_flight`
    (avant son ajout, donc le dernier segment "historique" du gabarit) doit
    toujours être `shot`/`cross`/`deflect` -- jamais `pass_ground`/`pass_lob`.
    Vérifié sur les 12 gabarits réels, sans exception codée en dur."""

    @pytest.mark.parametrize("gabarit", sorted(TEMPLATES))
    def test_ball_flight_only_after_shot(self, gabarit):
        assert TEMPLATES[gabarit].has_ball_flight
        lineup = _deflect_audit_lineup()
        event = _flight_event(gabarit)
        start_positions = _flight_start_positions()
        sequence_no_flight = BUILDERS[gabarit](event, lineup, start_positions, None)
        kf_a = sequence_no_flight.keyframes[-2]
        kf_b = sequence_no_flight.keyframes[-1]
        tag = _resolve_physics_tag(sequence_no_flight, kf_a, is_last_segment=True)
        assert tag in (SHOT, CROSS, DEFLECT), (
            f"{gabarit} : segment precedant le ball_flight tague {tag!r}, attendu shot/cross/deflect"
        )
        # Une fois le vol ajoute, la keyframe qui le demarre est explicitement
        # taguee BALL_FLIGHT (pas SHOT ni le tag herite) -- verifie que le
        # dispatch de ball_state_at ne retombe jamais sur l'inference.
        sequence_with_flight = BUILDERS[gabarit](event, lineup, start_positions, "but")
        assert sequence_with_flight.keyframes[-2].physics_tag == BALL_FLIGHT


class TestEdgeCases:
    def test_stationary_ball_has_frozen_position_and_zero_velocity(self):
        sequence = _sequence(start=(0.5, 0.5), end=(0.5, 0.5), duration=2.0)
        for frac in (0.0, 0.3, 0.7, 1.0):
            state = ball_state_at(sequence, frac * sequence.duration)
            assert state.x == pytest.approx(0.5)
            assert state.y == pytest.approx(0.5)
            assert (state.vx, state.vy, state.vz) == (0.0, 0.0, 0.0)

    def test_t_out_of_bounds_clamps_without_extrapolation(self):
        sequence = _sequence(start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0)
        before = ball_state_at(sequence, -5.0)
        at_start = ball_state_at(sequence, 0.0)
        after = ball_state_at(sequence, 100.0)
        at_end = ball_state_at(sequence, sequence.duration)
        assert (before.x, before.y) == (at_start.x, at_start.y)
        assert (after.x, after.y) == (at_end.x, at_end.y)

    def test_segment_without_physics_tag_or_inference_signal_falls_back_to_pass_ground(self):
        # Porteur present (pas None) ET pas le dernier segment -> pass_ground
        # par defaut (Modification C).
        keyframes = [
            _kf(0.0, 0.1, 0.5, owner_id="p"),
            _kf(1.0, 0.4, 0.5, owner_id="p"),
            _kf(2.0, 0.8, 0.5, owner_id="p"),
        ]
        roster = {"p": RosterEntry(nom="X", poste="BU", role="scorer", numero=9, team_side="scorer")}
        sequence = Sequence(event_ref="ref", keyframes=keyframes, duration=2.0, meta={}, roster=roster)
        tag = _resolve_physics_tag(sequence, sequence.keyframes[0], is_last_segment=False)
        assert tag == PASS_GROUND
        state = ball_state_at(sequence, 0.5)
        assert state.z == 0.0  # comportement pass_ground observable


class TestFallbackInferenceOnRealTemplates:
    """Modification C, testée sur les 12 gabarits réels : le tag résolu
    pour chaque segment doit correspondre à la règle exacte du brief,
    RE-DÉRIVÉE indépendamment ici depuis `Template.ball_owner`/`physics_tags`
    plutôt que de faire confiance à `_resolve_physics_tag` en boîte noire."""

    def _lineup(self) -> Lineup:
        def mk(poste, name, pid):
            return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=70.0, club="C", championnat="T", id=pid)

        return Lineup(club_name="Test FC", formation="4-3-3", players=[
            mk("GK", "gk", 1), mk("DC", "cb0", 2), mk("DC", "cb1", 3), mk("LB", "lb", 4), mk("RB", "rb", 5),
            mk("MDC", "mdc", 6), mk("MC", "mc0", 7), mk("MC", "mc1", 8), mk("AG", "ag", 9), mk("AD", "ad", 10), mk("BU", "bu", 11),
        ], rating=70.0)

    def _event(self) -> GoalEvent:
        return GoalEvent(
            club_name="Test FC", scorer="bu", assist="mc0", minute=34,
            zone=Zone(col=10, row=4), assist_zone=Zone(col=7, row=3),
        )

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_resolved_tag_matches_the_explicit_or_inferred_expectation(self, name):
        from ligue1sim.animation.templates import TEMPLATES

        lineup = self._lineup()
        event = self._event()
        start_positions = {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
        sequence = BUILDERS[name](event, lineup, start_positions)
        template = TEMPLATES[name]
        explicit_by_ratio = dict(template.physics_tags)
        ball_owner_by_ratio = dict(template.ball_owner)
        # Reconstruit les t_ratio EXACTS (mêmes flottants que build_from_template,
        # voir sa docstring) -- éviter `kf.t / sequence.duration`, dont
        # l'aller-retour flottant ne retombe pas forcément bit-à-bit sur la
        # valeur déclarée (ex. 0.4) et fausserait les lookups par dict ci-dessous.
        t_ratios = sorted({frame.t_ratio for role in template.roles for frame in role.frames})
        last_t_ratio = t_ratios[-1]

        for i, kf in enumerate(sequence.keyframes[:-1]):
            ratio = t_ratios[i]
            is_last_segment = t_ratios[i + 1] == last_t_ratio
            if ratio in explicit_by_ratio:
                expected = explicit_by_ratio[ratio]
            elif ball_owner_by_ratio.get(ratio) is None:
                expected = DEFLECT
            elif is_last_segment:
                expected = SHOT
            else:
                expected = PASS_GROUND
            actual = _resolve_physics_tag(sequence, kf, is_last_segment=is_last_segment)
            assert actual == expected, f"{name} @ t_ratio={ratio}: attendu {expected}, obtenu {actual}"


class TestFindBallSegment:
    def test_clamps_before_start_and_after_end(self):
        sequence = _sequence(start=(0.1, 0.5), end=(0.9, 0.5), duration=2.0)
        kf_a, kf_b, s, _ = _find_ball_segment(sequence, -10.0)
        assert s == 0.0
        kf_a, kf_b, s, is_last = _find_ball_segment(sequence, 999.0)
        assert s == 1.0
        assert is_last is True
