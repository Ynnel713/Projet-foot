import pytest

from ligue1sim.clubs import Club
from ligue1sim.knockout import advance_round, generate_bracket, simulate_round, simulate_round_leg, simulate_tie, simulate_tie_leg
from ligue1sim.lineup import club_strength
from ligue1sim.players import Player
from ligue1sim.simulation import LeagueContext


def _player(note: float, name: str) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25,
        poste="MC", note=note, club=name, championnat="TEST",
    )


def _make_clubs(n: int) -> list[Club]:
    return [Club(name=f"Club {i}", players=[_player(50 + i, f"Club {i}")]) for i in range(n)]


def test_generate_bracket_size_and_byes_for_non_power_of_two():
    clubs = _make_clubs(6)  # bracket de 8 -> 2 exemptions pour les 2 meilleures notes
    bracket = generate_bracket(clubs)

    round1 = bracket.rounds[0]
    assert len(round1.ties) == 4
    byes = [t for t in round1.ties if t.is_bye]
    assert len(byes) == 2
    assert all(t.played for t in byes)

    top2_names = {c.name for c in sorted(clubs, key=lambda c: -club_strength(c))[:2]}
    assert {t.home for t in byes} == top2_names


def test_generate_bracket_power_of_two_has_no_byes():
    bracket = generate_bracket(_make_clubs(8))

    assert len(bracket.rounds[0].ties) == 4
    assert not any(t.is_bye for t in bracket.rounds[0].ties)


def test_generate_bracket_rejects_less_than_two_clubs():
    with pytest.raises(ValueError):
        generate_bracket(_make_clubs(1))


@pytest.mark.parametrize("legs", [1, 2, 4])
def test_simulate_tie_produces_correct_number_of_legs_and_a_winner(legs):
    clubs = _make_clubs(2)
    by_name = {c.name: c for c in clubs}
    context = LeagueContext.from_clubs(clubs)
    tie = generate_bracket(clubs).rounds[0].ties[0]

    simulate_tie(tie, legs, by_name, context)

    assert len(tie.legs) == legs
    assert tie.winner in {tie.home, tie.away}


def test_full_tournament_reaches_a_champion_with_byes():
    clubs = _make_clubs(6)
    by_name = {c.name: c for c in clubs}
    context = LeagueContext.from_clubs(clubs)
    bracket = generate_bracket(clubs)

    while not bracket.is_complete:
        simulate_round(bracket.current_round, 1, by_name, context)
        advance_round(bracket)

    assert bracket.champion in by_name
    assert len(bracket.rounds) == 3  # 6 clubs -> tableau de 8 -> 3 tours


class TestPenaltyShootoutScore:
    """Scoreline de tirs au but affichée quand une confrontation est
    départagée (voir Tie.penalty_score/_penalty_shootout_score, retour
    terrain du 29/09/2026 : 'TAB : 4-5' plutôt qu'un simple 'X qualifié')."""

    def test_decided_by_penalties_always_has_a_winner_ahead_penalty_score(self, monkeypatch):
        import ligue1sim.knockout as knockout_module

        # Force un match nul à chaque manche pour garantir le passage par
        # les tirs au but, quel que soit le tirage réel du moteur.
        monkeypatch.setattr(knockout_module, "simulate_match", lambda *a, **k: (0, 0, None))

        clubs = _make_clubs(2)
        by_name = {c.name: c for c in clubs}
        context = LeagueContext.from_clubs(clubs)
        tie = generate_bracket(clubs).rounds[0].ties[0]

        simulate_tie(tie, 1, by_name, context)

        assert tie.decided_by_penalties
        assert tie.penalty_score is not None
        home_pens, away_pens = tie.penalty_score
        winner_pens = home_pens if tie.winner == tie.home else away_pens
        loser_pens = away_pens if tie.winner == tie.home else home_pens
        assert winner_pens > loser_pens

    def test_no_penalty_score_when_not_decided_by_penalties(self):
        clubs = _make_clubs(2)
        by_name = {c.name: c for c in clubs}
        context = LeagueContext.from_clubs(clubs)
        tie = generate_bracket(clubs).rounds[0].ties[0]

        simulate_tie(tie, 1, by_name, context)

        if not tie.decided_by_penalties:
            assert tie.penalty_score is None


class TestLegByLeg:
    """Simulation manche par manche (ticket refonte-ui/05) : pas de vainqueur avant la dernière manche."""

    def _setup(self, n=2):
        clubs = _make_clubs(n)
        return clubs, {c.name: c for c in clubs}, LeagueContext.from_clubs(clubs)

    def test_two_legs_no_winner_after_first_leg(self):
        clubs, by_name, context = self._setup()
        tie = generate_bracket(clubs).rounds[0].ties[0]

        simulate_tie_leg(tie, 2, by_name, context)
        assert len(tie.legs) == 1
        assert tie.winner is None and not tie.played
        assert tie.legs[0].home == tie.home

        simulate_tie_leg(tie, 2, by_name, context)
        assert len(tie.legs) == 2
        assert tie.winner in {tie.home, tie.away}
        assert tie.legs[1].home == tie.away  # le retour inverse les rôles

        simulate_tie_leg(tie, 2, by_name, context)  # sans effet une fois jouée
        assert len(tie.legs) == 2

    def test_single_leg_decides_immediately(self):
        clubs, by_name, context = self._setup()
        tie = generate_bracket(clubs).rounds[0].ties[0]
        simulate_tie_leg(tie, 1, by_name, context)
        assert len(tie.legs) == 1 and tie.winner in {tie.home, tie.away}

    def test_round_leg_skips_byes_and_round_finishes_after_last_leg(self):
        clubs, by_name, context = self._setup(6)  # 2 exemptions
        round_ = generate_bracket(clubs).rounds[0]

        simulate_round_leg(round_, 2, by_name, context)
        assert not round_.played
        assert all(t.legs == [] for t in round_.ties if t.is_bye)
        assert all(len(t.legs) == 1 for t in round_.ties if not t.is_bye)

        simulate_round_leg(round_, 2, by_name, context)
        assert round_.played
        assert all(len(t.legs) == 2 for t in round_.ties if not t.is_bye)

    def test_round_after_first_leg_plays_remaining_legs(self):
        clubs, by_name, context = self._setup()
        round_ = generate_bracket(clubs).rounds[0]
        simulate_round_leg(round_, 2, by_name, context)
        simulate_round(round_, 2, by_name, context)
        assert round_.played and len(round_.ties[0].legs) == 2

    def test_penalties_only_after_last_leg(self, monkeypatch):
        import ligue1sim.knockout as knockout_module

        clubs, by_name, context = self._setup()
        tie = generate_bracket(clubs).rounds[0].ties[0]
        monkeypatch.setattr(knockout_module, "simulate_match", lambda *a, **k: (1, 1, None))

        simulate_tie_leg(tie, 2, by_name, context)
        assert tie.winner is None and not tie.decided_by_penalties
        simulate_tie_leg(tie, 2, by_name, context)
        assert tie.decided_by_penalties and tie.winner in {tie.home, tie.away}

    def test_ban_from_first_leg_applies_to_second_leg(self, monkeypatch):
        import ligue1sim.knockout as knockout_module
        from ligue1sim.events import AvailabilityTracker

        clubs, by_name, context = self._setup()
        tie = generate_bracket(clubs).rounds[0].ties[0]
        seen = []

        def fake_match(host, guest, ctx, unavailable_host, unavailable_guest, *a, **k):
            seen.append((host.name, unavailable_host, unavailable_guest))
            return 1, 0, object()

        calls = iter([([(tie.home, "Absent", 2)], []), ([], [])])
        monkeypatch.setattr(knockout_module, "simulate_match", fake_match)
        monkeypatch.setattr(knockout_module, "collect_new_bans", lambda events: next(calls))
        suspensions, injuries = AvailabilityTracker(), AvailabilityTracker()

        simulate_tie_leg(tie, 2, by_name, context, suspensions, injuries)
        simulate_tie_leg(tie, 2, by_name, context, suspensions, injuries)

        assert seen[0][1] == frozenset() and seen[0][2] == frozenset()
        host2, unavailable_host2, unavailable_guest2 = seen[1]
        assert host2 == tie.away  # retour : rôles inversés
        assert unavailable_guest2 == frozenset({"Absent"})  # le suspendu de l'aller (club `tie.home`, invité au retour) manque le retour
