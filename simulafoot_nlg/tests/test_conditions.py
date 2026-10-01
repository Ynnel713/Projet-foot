from pathlib import Path
from typing import Any

import pytest
import yaml

from engine.conditions import ConditionAtom, evaluate_condition, parse_condition_atoms
from engine.models import MatchContext, PhraseCondition, Player

SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "scenarios.yml"


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

    @pytest.mark.parametrize("litteral", ["true", "vrai", "True"])
    def test_is_home_reads_boolean_literals_from_match_context(self, litteral):
        # D1 (01/10/2026) : sans le cast booleen, True == "true" est False et
        # la condition ne matcherait JAMAIS (echec silencieux).
        domicile = PhraseCondition(id=1, phrase_id=1, attribute="is_home", operator="==", value=litteral)
        assert evaluate_condition(domicile, _player(), _context(is_home=True)) is True
        assert evaluate_condition(domicile, _player(), _context(is_home=False)) is False

    def test_is_home_false_literal_and_not_equal_operator(self):
        exterieur = PhraseCondition(id=1, phrase_id=1, attribute="is_home", operator="==", value="false")
        assert evaluate_condition(exterieur, _player(), _context(is_home=False)) is True
        assert evaluate_condition(exterieur, _player(), _context(is_home=True)) is False
        pas_domicile = PhraseCondition(id=1, phrase_id=1, attribute="is_home", operator="!=", value="true")
        assert evaluate_condition(pas_domicile, _player(), _context(is_home=False)) is True

    def test_unknown_is_home_never_matches_even_with_not_equal(self):
        for operateur in ("==", "!="):
            cond = PhraseCondition(id=1, phrase_id=1, attribute="is_home", operator=operateur, value="true")
            assert evaluate_condition(cond, _player(), _context(is_home=None)) is False

    def test_is_home_parses_as_condition_atom(self):
        assert parse_condition_atoms("is_home == true") == [ConditionAtom("is_home", "==", "true")]

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

    def test_fm_rating_is_readable_as_a_player_field(self):
        # Les pilotes V2 (REMPLACEMENT : "fm_rating >= 75", surnom joker
        # ">= 80") conditionnent sur fm_rating : sans PLAYER_FIELDS, _resolve
        # levait ValueError a l'execution.
        cond = PhraseCondition(id=1, phrase_id=1, attribute="fm_rating", operator=">=", value="75")
        assert evaluate_condition(cond, _player(fm_rating=80.0), _context()) is True
        assert evaluate_condition(cond, _player(fm_rating=60.0), _context()) is False

    def test_position_is_readable_with_equality_and_in_operator(self):
        # Decision A du 01/10/2026 (HORS-JEU : conditionner sur le poste).
        egal = PhraseCondition(id=1, phrase_id=1, attribute="position", operator="==", value='"BU"')
        assert evaluate_condition(egal, _player(position="BU"), _context()) is True
        assert evaluate_condition(egal, _player(position="DC"), _context()) is False
        dans = PhraseCondition(id=2, phrase_id=1, attribute="position", operator="in", value="BU, AG, AD")
        assert evaluate_condition(dans, _player(position="AG"), _context()) is True
        assert evaluate_condition(dans, _player(position="MC"), _context()) is False
        assert parse_condition_atoms("position in [BU, AG, AD]") == [
            ConditionAtom("position", "in", "BU, AG, AD")
        ]

    def test_foot_field_distinguishes_natural_foot(self):
        # Ajoute le 30/09/2026 (audit éditorial) : BUT/DEFAUT
        # "{joueur} envoie un missile du pied droit..." n'était conditionnée
        # que sur preferred_moves="Shoots With Power", sans rien sur le pied
        # naturel -- un gaucher pur pouvait déclencher une phrase qui
        # affirme un tir du pied droit (non-sens football). `foot` existe
        # bien comme champ Player (engine/models.py) mais manquait de
        # PLAYER_FIELDS : ce test verrouille sa résolution correcte,
        # au-delà du seul cas de cette phrase.
        cond = PhraseCondition(id=1, phrase_id=1, attribute="foot", operator="==", value='"Right"')
        assert evaluate_condition(cond, _player(foot="Right"), _context()) is True
        assert evaluate_condition(cond, _player(foot="Left"), _context()) is False

    def test_unknown_attribute_raises_instead_of_silently_never_matching(self):
        cond = PhraseCondition(id=1, phrase_id=1, attribute="nom_inconnu", operator=">=", value="1")
        with pytest.raises(ValueError, match="nom_inconnu"):
            evaluate_condition(cond, _player(), _context())


class TestMissilePiedDroitNonSensFootballRegression:
    """Non-regression sur la banque REELLE (data/seed/scenarios.yml), pas un
    cas synthetique : verrouille le fix de l'audit editorial du 30/09/2026
    (BUT/DEFAUT "...un missile du pied droit...") directement contre le YAML
    livre, pas contre une copie recopiee a la main qui pourrait diverger."""

    def _phrase_missile(self) -> dict[str, Any]:
        with SCENARIOS_PATH.open(encoding="utf-8") as f:
            scenarios = yaml.safe_load(f)
        but = next(s for s in scenarios if s["code"] == "BUT")
        for variant in but["variants"]:
            for phrase in variant["phrases"]:
                if "missile du pied droit" in phrase["text"]:
                    return phrase
        raise AssertionError("Phrase 'missile du pied droit' introuvable dans scenarios.yml")

    def test_phrase_now_has_a_foot_condition(self):
        phrase = self._phrase_missile()
        attributs = {c["attribute"] for c in phrase["conditions"]}
        assert "foot" in attributs, (
            "La phrase 'missile du pied droit' doit conditionner sur `foot` -- "
            "voir AUDIT_EDITORIAL_2026-09-30.md, Audit 5."
        )

    def test_pure_lefty_fails_at_least_one_mandatory_condition(self):
        # C'est cette assertion qui, une fois phrase_selector implémenté,
        # garantit que la phrase est ÉCARTÉE (pas seulement dépriorisée) pour
        # un gaucher pur -- voir engine/phrase_selector.py, étape 4 de son
        # algorithme prévu ("filtrer les phrases dont une condition
        # mandatory=True échoue").
        phrase = self._phrase_missile()
        lefty = _player(foot="Left", preferred_moves=("Shoots With Power",))
        ctx = _context()

        conditions = [
            PhraseCondition(
                id=i,
                phrase_id=1,
                attribute=c["attribute"],
                operator=c["operator"],
                value=str(c["value"]),
                mandatory=c.get("mandatory", True),
            )
            for i, c in enumerate(phrase["conditions"])
        ]
        resultats = {c.attribute: evaluate_condition(c, lefty, ctx) for c in conditions}
        assert resultats["foot"] is False
        assert not all(resultats.values())

    def test_pure_righty_satisfies_all_conditions(self):
        # Non-regression symetrique : le fix ne doit pas, par erreur, exclure
        # aussi les droitiers pour lesquels la phrase reste parfaitement
        # valide.
        phrase = self._phrase_missile()
        righty = _player(foot="Right", preferred_moves=("Shoots With Power",))
        ctx = _context()

        conditions = [
            PhraseCondition(
                id=i,
                phrase_id=1,
                attribute=c["attribute"],
                operator=c["operator"],
                value=str(c["value"]),
                mandatory=c.get("mandatory", True),
            )
            for i, c in enumerate(phrase["conditions"])
        ]
        assert all(evaluate_condition(c, righty, ctx) for c in conditions)


class TestChampsJoueursDuContexte:
    """sortant/entrant (D3) : conditionnables au sens ou `_resolve` les
    reconnait. Sans leur ajout a MATCH_CONTEXT_FIELDS, `_resolve` leve
    ValueError ("inconnu")."""

    @staticmethod
    def _condition(attribute: str, operator: str, value: str) -> PhraseCondition:
        return PhraseCondition(id=1, phrase_id=1, attribute=attribute, operator=operator, value=value)

    @pytest.mark.parametrize("champ", ["sortant", "entrant"])
    def test_champ_absent_du_contexte_ne_matche_jamais_et_ne_leve_pas(self, champ):
        condition = self._condition(champ, "==", "x")
        assert evaluate_condition(condition, _player(), _context()) is False

    @pytest.mark.parametrize("champ", ["sortant", "entrant"])
    def test_champ_renseigne_est_resolu_sans_valueerror(self, champ):
        joueur = _player(id=9, first_name="Ousmane", last_name="Dembélé")
        condition = self._condition(champ, "!=", "x")
        assert evaluate_condition(condition, _player(), _context(**{champ: joueur})) is True


class TestNamespaceCollision:
    def test_no_collision_between_player_fields_and_fm26_attributes(self):
        from engine.conditions import PLAYER_FIELDS
        from engine.fm26 import FM26_ATTRIBUTES_KNOWN

        assert PLAYER_FIELDS & FM26_ATTRIBUTES_KNOWN == set()
