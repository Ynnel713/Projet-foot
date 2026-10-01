"""engine/event_contract.py : TypedDicts par famille d'evenement et leur validation."""

from __future__ import annotations

from typing import Any, get_args, get_type_hints

import pytest

from engine.event_contract import (
    EVENT_TYPES,
    GABARITS,
    ButDict,
    CartonDict,
    OccasionDict,
    RemplacementDict,
    validate_event,
    validate_event_stream,
)
from engine.models import SCORE_CONTEXT_VALUES


def _base(**surcharges: Any) -> dict[str, Any]:
    base: dict[str, Any] = dict(
        match_id="m1",
        match_sequence=12,
        event_id=0,
        minute=67,
        player_id=7,
        player_team="Lyon",
        home_team="Lyon",
        away_team="Marseille",
        is_home=True,
        competition="L1",
        journee=5,
        score_context="egalisation",
    )
    base.update(surcharges)
    return base


def but(**s: Any) -> dict[str, Any]:
    return _base(**{"event_type": "but", "gabarit": "contre_attaque", **s})


def occasion(**s: Any) -> dict[str, Any]:
    return _base(**{"event_type": "occasion", "gabarit": "une_deux", "outcome": "arret", **s})


def carton(**s: Any) -> dict[str, Any]:
    return _base(**{"event_type": "carton", "outcome": "yellow", **s})


def remplacement(**s: Any) -> dict[str, Any]:
    return _base(**{"event_type": "remplacement", "sortant_id": 8, "entrant_id": 7, **s})


@pytest.mark.parametrize("fabrique", [but, occasion, carton, remplacement])
def test_un_evenement_complet_de_chaque_famille_est_valide(fabrique):
    validate_event(fabrique())


def test_champs_nullables_valent_none_mais_restent_requis():
    validate_event(but(journee=None, competition=None, score_context=None))
    evenement = but()
    del evenement["journee"]
    with pytest.raises(ValueError, match="cles manquantes.*journee"):
        validate_event(evenement)


def test_passeur_et_receveur_sont_optionnels_sur_un_but():
    validate_event(but())
    validate_event(but(passeur_id=8, receveur_id=9))


class TestStructure:
    def test_event_type_inconnu_ou_absent(self):
        with pytest.raises(ValueError, match="event_type inconnu.*'corner'"):
            validate_event(_base(event_type="corner"))  # corner est un GABARIT, pas un event_type
        evenement = but()
        del evenement["event_type"]
        with pytest.raises(ValueError, match="event_type inconnu"):
            validate_event(evenement)

    def test_les_champs_requis_viennent_de_required_keys(self):
        for nom, famille in EVENT_TYPES.items():
            evenement = {"but": but, "occasion": occasion, "carton": carton, "remplacement": remplacement}[nom]()
            for cle in famille.__required_keys__ - {"event_type"}:  # event_type absent : voir test precedent
                incomplet = {k: v for k, v in evenement.items() if k != cle}
                with pytest.raises(ValueError, match=f"{nom}.*cles manquantes.*{cle}"):
                    validate_event(incomplet)

    def test_une_cle_inconnue_est_rejetee_meme_une_faute_de_frappe(self):
        with pytest.raises(ValueError, match="cles inconnues.*journe"):
            validate_event(but(journe=3))

    def test_une_cle_d_une_autre_famille_est_rejetee(self):
        with pytest.raises(ValueError, match="cles inconnues.*sortant_id"):
            validate_event(but(sortant_id=8))
        with pytest.raises(ValueError, match="cles inconnues.*gabarit"):
            validate_event(carton(gabarit="corner"))

    def test_un_non_mapping_est_refuse(self):
        with pytest.raises(TypeError, match="mapping"):
            validate_event([("event_type", "but")])  # type: ignore[arg-type]

    def test_tous_les_problemes_sont_listes_d_un_coup(self):
        with pytest.raises(ValueError) as erreur:
            validate_event(but(minute="soixante", journe=1))
        message = str(erreur.value)
        assert "minute" in message and "cles inconnues" in message


class TestTypesEtLiterals:
    @pytest.mark.parametrize("champ", ["player_id", "minute", "event_id", "match_sequence", "journee"])
    def test_un_bool_n_est_jamais_un_int(self, champ):
        with pytest.raises(ValueError, match=champ):
            validate_event(but(**{champ: True}))

    @pytest.mark.parametrize("champ", ["match_id", "player_team", "home_team", "away_team"])
    def test_un_champ_texte_refuse_un_non_texte(self, champ):
        with pytest.raises(ValueError, match=champ):
            validate_event(but(**{champ: 12}))

    def test_is_home_doit_etre_un_bool(self):
        with pytest.raises(ValueError, match="is_home"):
            validate_event(but(is_home=1))

    @pytest.mark.parametrize("outcome", ["arret", "hors_cadre", "tacle", "degagement", "poteau", "barre"])
    def test_outcome_d_occasion_verifie_a_l_execution(self, outcome):
        validate_event(occasion(outcome=outcome))

    @pytest.mark.parametrize("outcome", ["but", "corner", "penalty_rate", "ARRET", None, 3])
    def test_outcome_d_occasion_inconnu_est_refuse(self, outcome):
        with pytest.raises(ValueError, match="outcome"):
            validate_event(occasion(outcome=outcome))

    @pytest.mark.parametrize("outcome", ["yellow", "direct", "second_yellow"])
    def test_outcome_de_carton(self, outcome):
        validate_event(carton(outcome=outcome))

    def test_outcome_de_carton_est_distinct_de_celui_d_occasion(self):
        with pytest.raises(ValueError, match="outcome"):
            validate_event(carton(outcome="arret"))
        with pytest.raises(ValueError, match="outcome"):
            validate_event(occasion(outcome="yellow"))

    @pytest.mark.parametrize("gabarit", GABARITS)
    def test_les_12_gabarits_sont_acceptes(self, gabarit):
        validate_event(but(gabarit=gabarit))
        validate_event(occasion(gabarit=gabarit))

    def test_il_y_a_12_gabarits_et_un_gabarit_inconnu_est_refuse(self):
        assert len(GABARITS) == 12
        with pytest.raises(ValueError, match="gabarit"):
            validate_event(occasion(gabarit="tir_lointain"))

    def test_chaque_variante_declare_son_event_type_et_les_literals_sont_coherents(self):
        for nom, famille in EVENT_TYPES.items():
            assert get_args(get_type_hints(famille)["event_type"]) == (nom,)
        assert "event_type" not in get_type_hints(ButDict.__mro__[1])  # la base ne le declare pas


class TestIncoherences:
    def test_is_home_doit_suivre_player_team(self):
        with pytest.raises(ValueError, match="is_home incoherent"):
            validate_event(but(is_home=False))  # player_team == home_team
        validate_event(but(player_team="Marseille", is_home=False))

    def test_player_team_doit_etre_l_un_des_deux_clubs(self):
        with pytest.raises(ValueError, match="ni home_team ni away_team"):
            validate_event(but(player_team="Nice"))

    @pytest.mark.parametrize("valeur", SCORE_CONTEXT_VALUES)
    def test_score_context_connu(self, valeur):
        validate_event(but(score_context=valeur))

    def test_score_context_inconnu_est_refuse(self):
        with pytest.raises(ValueError, match="score_context"):
            validate_event(but(score_context="remontada"))

    @pytest.mark.parametrize(("champ", "valeur", "attendu"), [
        ("match_sequence", -1, ">= 0"),
        ("event_id", -1, "event_id"),
        ("minute", -3, "minute"),
    ])
    def test_valeurs_negatives_refusees(self, champ, valeur, attendu):
        with pytest.raises(ValueError, match=attendu):
            validate_event(but(**{champ: valeur}))

    def test_passeur_et_receveur_distincts(self):
        with pytest.raises(ValueError, match="passeur_id == receveur_id"):
            validate_event(but(passeur_id=8, receveur_id=8))

    def test_remplacement_player_id_est_l_entrant(self):
        with pytest.raises(ValueError, match="entrant"):
            validate_event(remplacement(player_id=99))
        with pytest.raises(ValueError, match="sortant_id == entrant_id"):
            validate_event(remplacement(sortant_id=7))


class TestFlux:
    def test_un_flux_valide_est_re_emis_tel_quel(self):
        flux = [but(event_id=0), occasion(event_id=1), carton(event_id=2), but(match_id="m2", match_sequence=13, event_id=0)]
        assert list(validate_event_stream(flux)) == flux

    def test_le_flux_est_valide_au_fil_de_l_eau(self):
        generateur = validate_event_stream(iter([but(event_id=0), but(event_id=1, minute="x")]))
        assert next(generateur)["event_id"] == 0
        with pytest.raises(ValueError, match="Evenement n°1.*minute"):
            next(generateur)

    def test_un_event_id_en_double_dans_un_match_est_refuse(self):
        with pytest.raises(ValueError, match="n°1.*event_id 0 deja vu.*'m1'"):
            list(validate_event_stream([but(event_id=0), occasion(event_id=0)]))

    def test_le_meme_event_id_dans_deux_matchs_est_normal(self):
        list(validate_event_stream([but(event_id=0), but(match_id="m2", event_id=0)]))

    def test_un_match_ne_change_pas_de_match_sequence(self):
        with pytest.raises(ValueError, match="deux match_sequence"):
            list(validate_event_stream([but(event_id=0), but(event_id=1, match_sequence=99)]))

    def test_l_erreur_d_un_evenement_invalide_donne_sa_position(self):
        with pytest.raises(ValueError, match="Evenement n°2"):
            list(validate_event_stream([but(event_id=0), but(event_id=1), _base(event_type="nope", event_id=2)]))

    def test_la_fonction_est_pure_deux_appels_sont_independants(self):
        flux = [but(event_id=0)]
        list(validate_event_stream(flux))
        list(validate_event_stream(flux))  # pas d'etat partage : le meme event_id n'est pas "deja vu"


def test_les_quatre_familles_sont_des_typeddict_distincts():
    assert {ButDict, OccasionDict, CartonDict, RemplacementDict} == set(EVENT_TYPES.values())
