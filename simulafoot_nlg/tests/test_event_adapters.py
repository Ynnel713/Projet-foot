"""engine/event_adapters.py : cartons et remplacements bruts -> dicts du contrat."""

from __future__ import annotations

from typing import Any

import pytest

from engine.event_adapters import card_to_event, substitution_to_event
from engine.event_contract import validate_event
from engine.narrative_adapter import event_to_scenario


def _commun(**surcharges: Any) -> dict[str, Any]:
    base = dict(
        match_id="m1", match_sequence=12, event_id=4, home_team="Lyon", away_team="Marseille",
        minute=67, club_name="Lyon",
    )
    base.update(surcharges)
    return base


def _carton(**s: Any) -> dict[str, Any]:
    return _commun(**{"player_id": 7, "card_type": "yellow", **s})


def _remplacement(**s: Any) -> dict[str, Any]:
    return _commun(**{"player_on_id": 11, "player_off_id": 10, **s})


class TestCard:
    def test_yellow_donne_event_type_carton_et_outcome_yellow(self):
        evenement = card_to_event(_carton())
        assert (evenement["event_type"], evenement["outcome"]) == ("carton", "yellow")
        assert evenement["player_id"] == 7

    @pytest.mark.parametrize("card_type", ["yellow", "second_yellow", "direct"])
    def test_les_trois_types_de_carton_sont_conserves_en_outcome(self, card_type):
        assert card_to_event(_carton(card_type=card_type))["outcome"] == card_type

    def test_le_dict_produit_respecte_le_contrat(self):
        validate_event(card_to_event(_carton()))
        validate_event(card_to_event(_carton(card_type="direct", club_name="Marseille", competition="L1", journee=3, score_context="egalisation")))

    def test_is_home_se_deduit_du_club(self):
        assert card_to_event(_carton(club_name="Lyon"))["is_home"] is True
        evenement = card_to_event(_carton(club_name="Marseille"))
        assert (evenement["is_home"], evenement["player_team"]) == (False, "Marseille")

    def test_les_champs_facultatifs_valent_none(self):
        evenement = card_to_event(_carton())
        assert (evenement["competition"], evenement["journee"], evenement["score_context"]) == (None, None, None)

    def test_card_type_absent_ou_inconnu_est_refuse(self):
        brut = _carton()
        del brut["card_type"]
        with pytest.raises(ValueError, match="cles manquantes.*card_type"):
            card_to_event(brut)
        with pytest.raises(ValueError, match="card_type='rouge' inconnu"):
            card_to_event(_carton(card_type="rouge"))

    def test_une_cle_commune_manquante_est_refusee(self):
        brut = _carton()
        del brut["minute"]
        with pytest.raises(ValueError, match="cles manquantes.*minute"):
            card_to_event(brut)

    def test_un_club_etranger_au_match_est_refuse(self):
        with pytest.raises(ValueError, match="club_name='Nice'"):
            card_to_event(_carton(club_name="Nice"))

    def test_aucune_decision_de_scenario_le_scenario_vient_de_narrative_adapter(self):
        evenement = card_to_event(_carton())
        assert "scenario_code" not in evenement and "scenario" not in evenement
        assert event_to_scenario(evenement) == "CARTON_JAUNE"
        assert event_to_scenario(card_to_event(_carton(card_type="second_yellow"))) == "CARTON_ROUGE"


class TestSubstitution:
    def test_traduit_les_joueurs_et_fait_de_l_entrant_l_acteur(self):
        evenement = substitution_to_event(_remplacement())
        assert evenement["event_type"] == "remplacement"
        assert (evenement["entrant_id"], evenement["sortant_id"], evenement["player_id"]) == (11, 10, 11)

    def test_le_dict_produit_respecte_le_contrat(self):
        validate_event(substitution_to_event(_remplacement()))
        validate_event(substitution_to_event(_remplacement(club_name="Marseille")))

    def test_is_home_et_player_team_viennent_du_club(self):
        evenement = substitution_to_event(_remplacement(club_name="Marseille"))
        assert (evenement["is_home"], evenement["player_team"]) == (False, "Marseille")

    @pytest.mark.parametrize("cle", ["player_on_id", "player_off_id", "club_name"])
    def test_cle_manquante_refusee(self, cle):
        brut = _remplacement()
        del brut[cle]
        with pytest.raises(ValueError, match=f"cles manquantes.*{cle}"):
            substitution_to_event(brut)

    def test_un_club_etranger_au_match_est_refuse(self):
        with pytest.raises(ValueError, match="club_name='Nice'"):
            substitution_to_event(_remplacement(club_name="Nice"))

    def test_le_scenario_vient_de_narrative_adapter(self):
        assert event_to_scenario(substitution_to_event(_remplacement())) == "REMPLACEMENT"

    def test_un_sortant_egal_a_l_entrant_est_attrape_par_le_contrat_pas_par_l_adaptateur(self):
        evenement = substitution_to_event(_remplacement(player_off_id=11))  # traduction pure
        with pytest.raises(ValueError, match="sortant_id == entrant_id"):
            validate_event(evenement)
