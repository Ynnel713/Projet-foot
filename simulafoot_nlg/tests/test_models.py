from engine.models import MatchContext, Player


def _player(name: str) -> Player:
    return Player(id=1, first_name=name, last_name="")


class TestMatchContextOpponentTeam:
    def test_opponent_is_away_team_when_player_is_home(self):
        ctx = MatchContext(match_id="m1", home_team="PSG", away_team="OM", is_home=True)
        assert ctx.opponent_team == "OM"

    def test_opponent_is_home_team_when_player_is_away(self):
        ctx = MatchContext(match_id="m1", home_team="PSG", away_team="OM", is_home=False)
        assert ctx.opponent_team == "PSG"

    def test_none_when_is_home_unknown(self):
        ctx = MatchContext(match_id="m1", home_team="PSG", away_team="OM")
        assert ctx.opponent_team is None


class TestMatchContextTwoPlayerEvent:
    def test_passeur_and_receveur_default_to_none(self):
        ctx = MatchContext(match_id="m1")
        assert ctx.passeur is None
        assert ctx.receveur is None

    def test_passeur_and_receveur_can_be_set(self):
        passeur, receveur = _player("Vitinha"), _player("Dembélé")
        ctx = MatchContext(match_id="m1", passeur=passeur, receveur=receveur)
        assert ctx.passeur is passeur
        assert ctx.receveur is receveur
