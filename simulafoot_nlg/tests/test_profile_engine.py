"""Cas minimum du brief : joueur complet, joueur sans attributs, postes
secondaires multiples, weak foot manquant."""

from __future__ import annotations

import pytest

from engine.profile_engine import compute_score_context, normalize_match_context, normalize_player


def test_normalizes_a_complete_player_row():
    row = {
        "id": 1,
        "first_name": "Kylian",
        "last_name": "Mbappé",
        "nationality": "France",
        "age": 26,
        "position": "BU",
        "secondary_positions": "AG / AD",
        "club": "Real Madrid",
        "league": "LaLiga",
        "market_value": 180.0,
        "average_rating": 90.0,
        "height_cm": 178,
        "status": "star",
        "role_category": "ST_Poacher",
        "foot": "D",
        "fm_rating": 91.0,
        "weak_foot": 4.0,
        "preferred_moves": "Cuts Inside ; Runs With Ball Often",
        "attributes": {"Pace": 95, "Finishing": 90},
    }
    player = normalize_player(row)

    assert player.full_name == "Kylian Mbappé"
    assert player.secondary_positions == ("AG", "AD")
    assert player.preferred_moves == ("Cuts Inside", "Runs With Ball Often")
    assert player.attributes == {"Pace": 95, "Finishing": 90}


def test_player_without_attributes_gets_an_empty_dict_not_an_error():
    row = {"id": 2, "first_name": "Joueur", "last_name": "Sans Attributs"}
    player = normalize_player(row)

    assert player.attributes == {}
    assert player.age is None
    assert player.fm_rating is None


def test_multiple_secondary_positions_are_split_and_trimmed():
    row = {"id": 3, "first_name": "A", "last_name": "B", "secondary_positions": "RB / DC / MDC"}
    player = normalize_player(row)

    assert player.secondary_positions == ("RB", "DC", "MDC")


def test_no_secondary_positions_gives_empty_tuple():
    row = {"id": 4, "first_name": "A", "last_name": "B"}
    player = normalize_player(row)

    assert player.secondary_positions == ()


def test_missing_weak_foot_is_none_not_a_default_value():
    row = {"id": 5, "first_name": "A", "last_name": "B"}
    player = normalize_player(row)

    assert player.weak_foot is None


def test_normalize_player_requires_an_id():
    with pytest.raises(KeyError):
        normalize_player({"first_name": "A", "last_name": "B"})


def test_normalizes_a_match_context():
    row = {
        "match_id": "m1",
        "minute": 67,
        "home_team": "PSG",
        "away_team": "OM",
        "home_score": 2,
        "away_score": 1,
        "player_team": "PSG",
        "is_home": True,
        "scenario_code": "BUT_PIED_DROIT",
    }
    context = normalize_match_context(row)

    assert context.match_id == "m1"
    assert context.minute == 67
    assert context.is_home is True


def test_normalize_match_context_requires_a_match_id():
    with pytest.raises(KeyError):
        normalize_match_context({"minute": 10})


def test_normalize_match_context_passes_through_score_context():
    context = normalize_match_context({"match_id": "m1", "score_context": "egalisation"})
    assert context.score_context == "egalisation"


def test_normalize_match_context_score_context_defaults_to_none():
    context = normalize_match_context({"match_id": "m1"})
    assert context.score_context is None


# --- compute_score_context : un cas par valeur de SCORE_CONTEXT_VALUES -----

def test_compute_score_context_first_goal_of_the_match():
    # Retour utilisateur du 29/09/2026 : "{joueur} remet les deux équipes à
    # égalité..." a besoin de savoir que ce but égalise, pas seulement sa
    # minute ou les caractéristiques du joueur.
    assert compute_score_context(0, 0, scorer_is_home=True) == "ouverture_score"
    assert compute_score_context(0, 0, scorer_is_home=False) == "ouverture_score"


def test_compute_score_context_equalizer_for_home_and_away():
    # Menés 1-2, le but à domicile égalise à 2-2.
    assert compute_score_context(1, 2, scorer_is_home=True) == "egalisation"
    # Menés 2-1, le but à l'extérieur égalise à 2-2.
    assert compute_score_context(2, 1, scorer_is_home=False) == "egalisation"


def test_compute_score_context_takes_the_lead_from_a_tie():
    assert compute_score_context(1, 1, scorer_is_home=True) == "prise_avantage"
    assert compute_score_context(1, 1, scorer_is_home=False) == "prise_avantage"


def test_compute_score_context_extends_an_existing_lead():
    assert compute_score_context(2, 0, scorer_is_home=True) == "creuse_ecart"
    assert compute_score_context(0, 2, scorer_is_home=False) == "creuse_ecart"


def test_compute_score_context_still_behind_after_scoring():
    assert compute_score_context(0, 3, scorer_is_home=True) == "reduit_ecart"
    assert compute_score_context(3, 0, scorer_is_home=False) == "reduit_ecart"
