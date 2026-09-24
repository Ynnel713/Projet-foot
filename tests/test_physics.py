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
