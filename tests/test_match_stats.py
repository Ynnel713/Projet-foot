import numpy as np
import pytest

from ligue1sim.match_stats import compute_match_stats


def test_possession_sums_to_one_hundred():
    stats = compute_match_stats(
        home_lambda=1.5, away_lambda=1.2, home_rating=75.0, away_rating=70.0, home_goals=2, away_goals=1
    )

    assert stats.home.possession + stats.away.possession == pytest.approx(100.0, abs=0.1)


def test_higher_rated_team_tends_to_have_more_possession():
    np.random.seed(0)
    possessions = [
        compute_match_stats(
            home_lambda=1.5, away_lambda=1.2, home_rating=85.0, away_rating=60.0, home_goals=2, away_goals=1
        ).home.possession
        for _ in range(20)
    ]

    assert sum(possessions) / len(possessions) > 50.0


def test_possession_style_shifts_the_split_towards_the_team_that_declares_it():
    np.random.seed(0)
    with_style = [
        compute_match_stats(
            home_lambda=1.2,
            away_lambda=1.2,
            home_rating=70.0,
            away_rating=70.0,
            home_goals=1,
            away_goals=1,
            home_styles=frozenset({"Possession"}),
        ).home.possession
        for _ in range(20)
    ]
    np.random.seed(0)
    without_style = [
        compute_match_stats(
            home_lambda=1.2, away_lambda=1.2, home_rating=70.0, away_rating=70.0, home_goals=1, away_goals=1
        ).home.possession
        for _ in range(20)
    ]

    assert sum(with_style) / len(with_style) > sum(without_style) / len(without_style)


def test_shots_on_target_never_below_goals_scored():
    for _ in range(30):
        stats = compute_match_stats(
            home_lambda=0.5, away_lambda=0.5, home_rating=70.0, away_rating=70.0, home_goals=4, away_goals=0
        )
        assert stats.home.shots_on_target >= 4


def test_shots_never_below_shots_on_target():
    for _ in range(30):
        stats = compute_match_stats(
            home_lambda=2.5, away_lambda=2.5, home_rating=70.0, away_rating=70.0, home_goals=3, away_goals=3
        )
        assert stats.home.shots >= stats.home.shots_on_target
        assert stats.away.shots >= stats.away.shots_on_target


def test_xg_is_centered_on_the_real_lambda_not_the_realised_goals():
    np.random.seed(0)
    xgs = [
        compute_match_stats(
            home_lambda=2.0, away_lambda=1.0, home_rating=70.0, away_rating=70.0, home_goals=0, away_goals=0
        ).home.xg
        for _ in range(40)
    ]

    # Malgré 0 but réel, le xG doit rester centré sur le lambda réel (2.0),
    # pas s'effondrer vers le score -- voir docstring du module
    # (cohérence avec le score, mais dérivé du LAMBDA, pas du résultat).
    assert 1.4 < sum(xgs) / len(xgs) < 2.6


def test_shots_and_stats_stay_within_sane_bounds():
    for _ in range(30):
        stats = compute_match_stats(
            home_lambda=3.0, away_lambda=0.2, home_rating=95.0, away_rating=40.0, home_goals=5, away_goals=0
        )
        assert 0 <= stats.home.shots <= 40
        assert 0 <= stats.away.shots <= 40
        assert stats.home.xg > 0
        assert stats.away.xg > 0
