import pytest

from engine.conditions import ConditionAtom, evaluate_condition, parse_condition_atoms
from engine.models import MatchContext, PhraseCondition, Player


def _player(**overrides) -> Player:
    defaults = dict(
        id=1,
        first_name="Kylian",
        last_name="Mbappé",
        age=25,
        height_cm=178,
        weak_foot=4,
        preferred_moves=("Runs With Ball Often", "Shoots From Distance"),
        attributes={"Aggression": 60, "Pace": 95},
    )
    defaults.update(overrides)
    return Player(**defaults)


def _context(**overrides) -> MatchContext:
    defaults = dict(
        match_id="m1", minute=10, home_team="PSG", away_team="OM", is_home=True, player_team="PSG"
    )
    defaults.update(overrides)
    return MatchContext(**defaults)


class TestParseConditionAtoms:
    def test_empty_condition_returns_no_atoms(self):
        assert parse_condition_atoms("") == []
        assert parse_condition_atoms("   ") == []

    def test_single_comparison_atom(self):
        assert parse_condition_atoms("Aggression >= 85") == [ConditionAtom("Aggression", ">=", "85")]

    def test_conjunction_splits_into_two_atoms(self):
        atoms = parse_condition_atoms('Aggression >= 85 et preferred_moves contient "Dives Into Tackles"')
        assert atoms == [
            ConditionAtom("Aggression", ">=", "85"),
            ConditionAtom("preferred_moves", "contient", "Dives Into Tackles"),
        ]

    def test_score_context_equality(self):
        assert parse_condition_atoms('score_context == "reduit_ecart"') == [
            ConditionAtom("score_context", "==", '"reduit_ecart"')
        ]

    def test_unrecognized_atom_raises_with_the_offending_fragment(self):
        with pytest.raises(ValueError, match="aggression ~~ 15"):
            parse_condition_atoms("aggression ~~ 15")

    def test_french_contient_not_english_contains(self):
        # Bug du brief initial : le regex attendait "contains" (anglais),
        # les 48 conditions réelles du classeur écrivent "contient"
        # (français) -- non-régression.
        with pytest.raises(ValueError):
            parse_condition_atoms('preferred_moves contains "Dives Into Tackles"')
        parse_condition_atoms('preferred_moves contient "Dives Into Tackles"')  # ne lève pas


class TestEvaluateCondition:
    def test_fm26_attribute_comparison(self):
        cond = PhraseCondition(id=1, phrase_id=1, attribute="Pace", operator=">=", value="90")
        assert evaluate_condition(cond, _player(), _context()) is True

    def test_player_field_takes_precedence_and_is_read_correctly(self):
        cond = PhraseCondition(id=1, phrase_id=1, attribute="age", operator="<=", value="25")
        assert evaluate_condition(cond, _player(age=25), _context()) is True
        assert evaluate_condition(cond, _player(age=30), _context()) is False

    def test_minute_reads_from_match_context(self):
        cond = PhraseCondition(id=1, phrase_id=1, attribute="minute", operator=">=", value="80")
        assert evaluate_condition(cond, _player(), _context(minute=85)) is True
        assert evaluate_condition(cond, _player(), _context(minute=10)) is False

    def test_preferred_moves_contient(self):
        cond = PhraseCondition(
            id=1, phrase_id=1, attribute="preferred_moves", operator="contient", value="Shoots From Distance"
        )
        assert evaluate_condition(cond, _player(), _context()) is True

    def test_quoted_string_literal_is_unquoted_before_comparison(self):
        # Bug du brief initial : "reduit_ecart" gardait ses guillemets,
        # ne matchait donc jamais score_context == "reduit_ecart" -- échec
        # silencieux. Non-régression explicitement demandée.
        cond = PhraseCondition(
            id=1, phrase_id=1, attribute="score_context", operator="==", value='"reduit_ecart"'
        )
        assert evaluate_condition(cond, _player(), _context(score_context="reduit_ecart")) is True

    def test_in_operator_checks_membership(self):
        # Non utilisé par les 281 phrases réelles du classeur (voir
        # l'analyse du 29/09/2026), mais fait partie de la grammaire D6 --
        # couvert pour ne pas livrer une branche jamais exécutée.
        cond = PhraseCondition(id=1, phrase_id=1, attribute="weak_foot", operator="in", value="4, 5")
        assert evaluate_condition(cond, _player(weak_foot=4), _context()) is True
        assert evaluate_condition(cond, _player(weak_foot=2), _context()) is False

    def test_unknown_attribute_raises_instead_of_silently_never_matching(self):
        cond = PhraseCondition(id=1, phrase_id=1, attribute="nom_inconnu", operator=">=", value="1")
        with pytest.raises(ValueError, match="nom_inconnu"):
            evaluate_condition(cond, _player(), _context())


class TestNamespaceCollision:
    def test_no_collision_between_player_fields_and_fm26_attributes(self):
        # "data.import.import_players" n'est pas importable statiquement
        # ("import" est un mot-clé Python) -- même contournement que cli.py
        # (importlib.import_module, voir sa docstring).
        import importlib

        from engine.conditions import PLAYER_FIELDS

        import_players_module = importlib.import_module("data.import.import_players")
        flat_fm26 = {name for names in import_players_module.FM26_ATTRIBUTES.values() for name in names}
        assert PLAYER_FIELDS & flat_fm26 == set()
