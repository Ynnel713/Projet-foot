import pytest
from ligue1sim.animation.physics import apply_acceleration_constraint

_DT = 1.0 / 30.0


class TestAppliesNoCorrectionWhenAlreadySmooth:
    def test_uniform_motion_is_left_unchanged(self):
        # Vitesse constante (1 m/frame a dt=1/30 -> 30 m/s, largement
        # constant d'une frame a l'autre) -- rien a corriger.
        frames = [{"p": (float(i), 0.0)} for i in range(6)]
        corrected = apply_acceleration_constraint(frames, _DT, a_max=10.0)
        assert corrected == frames


class TestFirstTwoFramesAreNeverCorrected:
    def test_frame_0_and_1_pass_through_unchanged_even_with_a_huge_jump(self):
        # Un "saut" enorme entre la frame 0 et la frame 1 (equivalent au
        # saut documente sur un segment impossible de motion.py) : rien a
        # comparer avant la 1ere vitesse observee, donc ni la frame 0 ni la
        # frame 1 ne sont touchees (voir docstring de la fonction).
        frames = [{"p": (0.0, 0.0)}, {"p": (100.0, 0.0)}, {"p": (100.02, 0.0)}]
        corrected = apply_acceleration_constraint(frames, _DT, a_max=10.0)
        assert corrected[0] == frames[0]
        assert corrected[1] == frames[1]


class TestClampsAnAnomalousSpike:
    """Reproduit le motif mesure sur un vrai gabarit (brief "add
    velocity/acceleration to PlayerState", 24/09/2026) : mouvement uniforme
    puis saut brutal (frontiere de keyframe / arrivee anticipee), puis
    reprise -- le saut doit disparaitre, l'acceleration entre deux frames
    consecutives corrigees doit toujours rester <= a_max."""

    def _spiky_frames(self):
        # 0..4 : mouvement uniforme (1 m/frame). 5 : saut de +50 m (le
        # "keyframe boundary"). 6.. : reprise du mouvement uniforme a partir
        # de la nouvelle position brute (comme un nouveau segment).
        frames = [{"p": (float(i), 0.0)} for i in range(5)]
        frames.append({"p": (54.0, 0.0)})  # saut brutal (au lieu de 5.0)
        for i in range(6, 12):
            frames.append({"p": (54.0 + (i - 5), 0.0)})
        return frames

    def test_no_instantaneous_acceleration_exceeds_a_max_after_correction(self):
        a_max = 10.0
        frames = self._spiky_frames()
        corrected = apply_acceleration_constraint(frames, _DT, a_max=a_max)

        velocities = []
        for i in range(1, len(corrected)):
            dx = corrected[i]["p"][0] - corrected[i - 1]["p"][0]
            velocities.append(dx / _DT)
        for i in range(1, len(velocities)):
            accel = abs(velocities[i] - velocities[i - 1]) / _DT
            assert accel <= a_max + 1e-6, f"accel={accel:.3f} a l'intervalle {i}"

    def test_raw_spike_would_have_exceeded_a_max_by_far(self):
        # Preuve que le cas de test est bien pertinent (le saut brut viole
        # largement la contrainte avant correction).
        frames = self._spiky_frames()
        raw_velocities = [(frames[i]["p"][0] - frames[i - 1]["p"][0]) / _DT for i in range(1, len(frames))]
        spike_accel = abs(raw_velocities[4] - raw_velocities[3]) / _DT
        assert spike_accel > 1000.0

    def test_output_positions_differ_from_the_raw_ones_where_the_spike_was(self):
        # Preuve que le fix agit reellement (Tache 3.3 du brief) : la
        # position corrigee au moment du saut n'est plus la position brute.
        frames = self._spiky_frames()
        corrected = apply_acceleration_constraint(frames, _DT, a_max=10.0)
        assert corrected[5]["p"] != frames[5]["p"]


class TestEdgeCases:
    def test_fewer_than_two_frames_returns_input_unchanged(self):
        assert apply_acceleration_constraint([], _DT) == []
        one = [{"p": (1.0, 2.0)}]
        assert apply_acceleration_constraint(one, _DT) == one

    def test_non_positive_dt_returns_input_unchanged(self):
        frames = [{"p": (0.0, 0.0)}, {"p": (1.0, 0.0)}, {"p": (2.0, 0.0)}]
        assert apply_acceleration_constraint(frames, 0.0) == frames
        assert apply_acceleration_constraint(frames, -0.01) == frames

    def test_never_mutates_the_input_list(self):
        frames = [{"p": (0.0, 0.0)}, {"p": (100.0, 0.0)}, {"p": (100.02, 0.0)}]
        snapshot = [dict(f) for f in frames]
        apply_acceleration_constraint(frames, _DT, a_max=10.0)
        assert frames == snapshot


class TestBoundsKeepThePlayerOnThePitch:
    """Ticket 1 (Phase 5, sous-etape 1) : face a un SAUT de la trajectoire brute, la contrainte
    d'acceleration poursuivait la cible sans freiner et pouvait deriver a des dizaines de metres
    (hors du terrain). Avec `bounds`, la vitesse visee est plafonnee pour qu'un arret a a_max reste
    possible avant le bord : le joueur reste dans les bornes SANS depasser a_max."""

    _BOUNDS = ((0.0, 105.0), (0.0, 68.0))

    @staticmethod
    def _max_acceleration(frames, pid="p"):
        velocities = [
            ((frames[i][pid][0] - frames[i - 1][pid][0]) / _DT, (frames[i][pid][1] - frames[i - 1][pid][1]) / _DT)
            for i in range(1, len(frames))
        ]
        return max(
            (((velocities[j][0] - velocities[j - 1][0]) ** 2 + (velocities[j][1] - velocities[j - 1][1]) ** 2) ** 0.5) / _DT
            for j in range(2, len(velocities))
        )

    def test_teleport_toward_the_touchline_does_not_leave_the_pitch(self):
        # Immobile en x=10, saut brut a x=100 (un segment impossible), immobile ensuite : sans bornes, le joueur
        # accelere vers 100, la depasse largement (> 105) et finit hors du terrain.
        frames = [{"p": (10.0, 20.0)}] * 3 + [{"p": (100.0, 20.0)}] * 400
        unbounded = apply_acceleration_constraint(frames, _DT, a_max=10.0)
        assert max(f["p"][0] for f in unbounded) > 105.0  # le defaut qui est corrige
        bounded = apply_acceleration_constraint(frames, _DT, a_max=10.0, bounds=self._BOUNDS)
        xs = [f["p"][0] for f in bounded]
        assert 0.0 <= min(xs) and max(xs) <= 105.0

    def test_bounds_never_break_the_acceleration_limit(self):
        frames = [{"p": (10.0, 20.0)}] * 3 + [{"p": (100.0, 20.0)}] * 400
        bounded = apply_acceleration_constraint(frames, _DT, a_max=10.0, bounds=self._BOUNDS)
        assert self._max_acceleration(bounded) <= 10.0 + 1e-6

    def test_player_running_along_the_touchline_is_not_slowed(self):
        # y = 0 (sur la touche) : seule la composante x est libre, aucun freinage parasite.
        frames = [{"p": (1.0 + 0.2 * i, 0.0)} for i in range(100)]
        assert apply_acceleration_constraint(frames, _DT, a_max=10.0, bounds=self._BOUNDS) == frames

    def test_without_bounds_behaviour_is_unchanged(self):
        frames = [{"p": (0.0, 0.0)}, {"p": (0.1, 0.0)}, {"p": (30.0, 0.0)}] + [{"p": (30.0, 0.0)}] * 50
        assert apply_acceleration_constraint(frames, _DT, a_max=10.0) == apply_acceleration_constraint(
            frames, _DT, a_max=10.0, bounds=None
        )
