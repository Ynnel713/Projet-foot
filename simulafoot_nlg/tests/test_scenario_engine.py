"""Cas minimum du brief : scénario inexistant -> None, variantes multiples,
fallback is_default (au sens : chargées correctement, le choix du fallback
appartient à phrase_selector, pas à scenario_engine)."""

from __future__ import annotations

from engine.scenario_engine import (
    load_phrase_conditions,
    load_phrase_slots,
    load_phrases,
    load_scenario,
    load_variants,
)


def test_load_scenario_returns_none_when_code_unknown(sqlite_conn):
    assert load_scenario(sqlite_conn, "INEXISTANT") is None


def test_load_scenario_returns_the_matching_scenario(sqlite_conn, seeded_scenario):
    scenario = load_scenario(sqlite_conn, "BUT_TEST")

    assert scenario is not None
    assert scenario.code == "BUT_TEST"
    assert scenario.id == seeded_scenario["scenario_id"]


def test_load_variants_returns_multiple_variants_including_the_default_one(sqlite_conn, seeded_scenario):
    sqlite_conn.execute(
        "INSERT INTO variants (scenario_id, code, label, is_default) "
        "VALUES (?, 'SPECIFIQUE', 'Spécifique', 0)",
        (seeded_scenario["scenario_id"],),
    )
    sqlite_conn.commit()

    variants = load_variants(sqlite_conn, seeded_scenario["scenario_id"])

    assert len(variants) == 2
    defaults = [v for v in variants if v.is_default]
    assert len(defaults) == 1
    assert defaults[0].code == "DEFAUT"


def test_load_variants_for_unknown_scenario_returns_empty_list(sqlite_conn):
    assert load_variants(sqlite_conn, 999) == []


def test_load_phrases_attaches_conditions_and_slots(sqlite_conn, seeded_scenario):
    phrase_id = seeded_scenario["phrase_id"]
    sqlite_conn.execute(
        "INSERT INTO phrase_conditions (phrase_id, attribute, operator, value) "
        "VALUES (?, 'Determination', '>=', '70')",
        (phrase_id,),
    )
    sqlite_conn.execute(
        "INSERT INTO phrase_slots (phrase_id, slot_name, expression) "
        "VALUES (?, 'player_name', 'player.full_name')",
        (phrase_id,),
    )
    sqlite_conn.commit()

    phrases = load_phrases(sqlite_conn, seeded_scenario["variant_id"])

    assert len(phrases) == 1
    phrase = phrases[0]
    assert len(phrase.conditions) == 1
    assert phrase.conditions[0].attribute == "Determination"
    assert len(phrase.slots) == 1
    assert phrase.slots[0].slot_name == "player_name"


def test_load_phrase_conditions_for_phrase_without_conditions_is_empty(sqlite_conn, seeded_scenario):
    assert load_phrase_conditions(sqlite_conn, seeded_scenario["phrase_id"]) == []


def test_load_phrase_slots_for_phrase_without_slots_is_empty(sqlite_conn, seeded_scenario):
    assert load_phrase_slots(sqlite_conn, seeded_scenario["phrase_id"]) == []
