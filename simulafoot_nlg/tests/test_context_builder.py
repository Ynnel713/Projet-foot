"""engine/context_builder.py : dict d'evenement -> MatchContext (protagonistes resolus en base)."""

from __future__ import annotations

import pytest

from engine.context_builder import dict_to_context
from engine.event_contract import validate_event
from engine.models import MatchContext, Player


@pytest.fixture
def base_joueurs(sqlite_conn):
    sqlite_conn.executemany(
        "INSERT INTO players (id, first_name, last_name, position) VALUES (?, ?, ?, ?)",
        [
            (7, "Kylian", "Mbappé", "BU"),
            (8, "Alexandre", "Lacazette", "BU"),
            (9, "Moussa", "Dembélé", "AG"),
            (10, "Ousmane", "Dembélé", "AD"),
            (11, "Rayan", "Cherki", "MOC"),
        ],
    )
    sqlite_conn.executemany(
        "INSERT INTO player_attributes (player_id, attribute, category, value) VALUES (?, ?, ?, ?)",
        [(8, "Technique", "technique", 84), (11, "Pace", "physique", 80)],
    )
    sqlite_conn.commit()
    return sqlite_conn


def _base(**surcharges):
    base = dict(
        match_id="m1", match_sequence=12, event_id=3, minute=67, player_id=7, player_team="Lyon",
        home_team="Lyon", away_team="Marseille", is_home=True, competition="L1", journee=5,
        score_context="egalisation",
    )
    base.update(surcharges)
    return base


def test_un_but_sur_corner_resout_passeur_et_receveur_et_recopie_le_reste(base_joueurs):
    evenement = _base(event_type="but", gabarit="corner", passeur_id=8, receveur_id=9)
    validate_event(evenement)

    contexte = dict_to_context(evenement, base_joueurs)

    assert isinstance(contexte, MatchContext)
    assert (contexte.match_id, contexte.match_sequence, contexte.minute) == ("m1", 12, 67)
    assert (contexte.home_team, contexte.away_team, contexte.player_team, contexte.is_home) == ("Lyon", "Marseille", "Lyon", True)
    assert (contexte.competition, contexte.journee, contexte.score_context, contexte.gabarit) == ("L1", 5, "egalisation", "corner")
    assert isinstance(contexte.passeur, Player) and contexte.passeur.full_name == "Alexandre Lacazette"
    assert contexte.receveur is not None and contexte.receveur.id == 9
    assert contexte.passeur.attributes == {"Technique": 84}  # les attributs FM26 suivent le Player
    assert contexte.opponent_team == "Marseille"  # property derivee : jamais stockee
    assert (contexte.sortant, contexte.entrant) == (None, None)


def test_un_remplacement_resout_sortant_et_entrant(base_joueurs):
    evenement = _base(event_type="remplacement", player_id=11, entrant_id=11, sortant_id=10)
    validate_event(evenement)

    contexte = dict_to_context(evenement, base_joueurs)

    assert contexte.sortant is not None and contexte.sortant.full_name == "Ousmane Dembélé"
    assert contexte.entrant is not None and contexte.entrant.attributes == {"Pace": 80}
    assert (contexte.passeur, contexte.receveur, contexte.gabarit) == (None, None, None)


def test_un_carton_n_a_aucun_protagoniste_resolu(base_joueurs):
    contexte = dict_to_context(_base(event_type="carton", outcome="yellow"), base_joueurs)
    assert (contexte.passeur, contexte.receveur, contexte.sortant, contexte.entrant) == (None, None, None, None)
    assert contexte.player_team == "Lyon" and contexte.minute == 67


def test_un_but_sans_passeur_ni_receveur_les_laisse_a_none(base_joueurs):
    contexte = dict_to_context(_base(event_type="but", gabarit="percee_individuelle"), base_joueurs)
    assert (contexte.passeur, contexte.receveur) == (None, None)


def test_les_champs_nullables_restent_none(base_joueurs):
    contexte = dict_to_context(
        _base(event_type="occasion", gabarit="une_deux", outcome="arret", competition=None, journee=None, score_context=None),
        base_joueurs,
    )
    assert (contexte.competition, contexte.journee, contexte.score_context) == (None, None, None)
    assert contexte.gabarit == "une_deux"


def test_le_scenario_n_est_pas_decide_ici(base_joueurs):
    assert dict_to_context(_base(event_type="but", gabarit="corner"), base_joueurs).scenario_code is None


def test_un_visiteur_a_pour_adversaire_le_club_a_domicile(base_joueurs):
    contexte = dict_to_context(
        _base(event_type="carton", outcome="direct", player_team="Marseille", is_home=False), base_joueurs
    )
    assert contexte.opponent_team == "Lyon"


def test_un_protagoniste_inconnu_leve_key_error(base_joueurs):
    with pytest.raises(KeyError, match="999"):
        dict_to_context(_base(event_type="but", gabarit="corner", passeur_id=999), base_joueurs)


def test_match_sequence_invalide_est_refuse_par_la_normalisation(base_joueurs):
    with pytest.raises(ValueError, match="match_sequence"):
        dict_to_context(_base(event_type="carton", outcome="yellow", match_sequence=-1), base_joueurs)
