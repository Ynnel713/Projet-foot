"""cli.py narrate : bout en bout, avec des dicts d'evenements ECRITS A LA MAIN (la conversion racine ->
dicts, proprio-conversion, est hors V2.1) : validate_event_stream -> narrative_adapter -> player_resolver /
context_builder -> select -> update_cooldown."""

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

import cli
from engine.event_adapters import card_to_event, substitution_to_event
from scripts.init_db import init_db


def _scenario(conn: sqlite3.Connection, code: str, texte: str, slots: dict[str, str], secours: str) -> None:
    scenario_id = conn.execute("INSERT INTO scenarios (code, label) VALUES (?, ?)", (code, code)).lastrowid
    variante_id = conn.execute(
        "INSERT INTO variants (scenario_id, code, label, is_default) VALUES (?, 'DEFAUT', 'd', 1)", (scenario_id,)
    ).lastrowid
    phrase_id = conn.execute("INSERT INTO phrases (variant_id, text) VALUES (?, ?)", (variante_id, texte)).lastrowid
    conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (?, 3)", (phrase_id,))
    for nom, expression in slots.items():
        conn.execute(
            "INSERT INTO phrase_slots (phrase_id, slot_name, expression) VALUES (?, ?, ?)", (phrase_id, nom, expression)
        )
    conn.execute("INSERT INTO phrases (variant_id, text, is_fallback) VALUES (?, ?, 1)", (variante_id, secours))


def _construire_base(chemin: Path, *, sans: tuple[str, ...] = ()) -> Path:
    init_db(db_path=chemin)
    conn = sqlite3.connect(chemin)
    conn.executemany(
        "INSERT INTO players (id, first_name, last_name, position) VALUES (?, ?, ?, ?)",
        [(7, "Kylian", "Mbappé", "BU"), (10, "Ousmane", "Dembélé", "AD"), (11, "Rayan", "Cherki", "MOC"), (12, "Mike", "Maignan", "GK")],
    )
    scenarios = {
        "BUT": ("{joueur} marque pour {club}, face à {adversaire} !", {"joueur": "player.full_name", "club": "context.player_team", "adversaire": "context.opponent_team"}, "Le ballon termine au fond des filets."),
        "CARTON_JAUNE": ("{joueur} prend un carton jaune à la {minute}e minute.", {"joueur": "player.full_name", "minute": "context.minute"}, "L'arbitre sort le carton jaune."),
        "REMPLACEMENT": ("Changement chez {club} : {entrant} remplace {sortant}.", {"club": "context.player_team", "entrant": "context.entrant.full_name", "sortant": "context.sortant.full_name"}, "Un changement a lieu."),
        "ARRET_GARDIEN": ("{joueur} repousse la frappe de {adversaire} !", {"joueur": "player.full_name", "adversaire": "context.opponent_team"}, "Le gardien écarte le danger."),
    }
    for code, (texte, slots, secours) in scenarios.items():
        if code not in sans:
            _scenario(conn, code, texte, slots, secours)
    conn.commit()
    conn.close()
    return chemin


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return _construire_base(tmp_path / "narrate.db")


def _base_evenement(**s: Any) -> dict[str, Any]:
    base: dict[str, Any] = dict(
        match_id="m1", match_sequence=12, minute=67, player_team="Lyon", home_team="Lyon",
        away_team="Marseille", is_home=True, competition="L1", journee=5, score_context=None,
    )
    base.update(s)
    return base


def _jsonl(chemin: Path, evenements: list[dict[str, Any]]) -> Path:
    chemin.write_text("\n".join(json.dumps(e) for e in evenements) + "\n", encoding="utf-8")
    return chemin


def _evenements() -> list[dict[str, Any]]:
    commun = dict(match_id="m1", match_sequence=12, home_team="Lyon", away_team="Marseille", club_name="Lyon", competition="L1", journee=5)
    return [
        {**_base_evenement(event_id=0, minute=12, player_id=7, event_type="but", gabarit="contre_attaque")},
        dict(card_to_event({**commun, "event_id": 1, "minute": 34, "player_id": 10, "card_type": "yellow"})),
        dict(substitution_to_event({**commun, "event_id": 2, "minute": 60, "player_on_id": 11, "player_off_id": 10})),
        {**_base_evenement(event_id=3, minute=70, player_id=7, event_type="occasion", gabarit="une_deux", outcome="poteau")},
        {**_base_evenement(event_id=4, minute=81, player_id=12, event_type="occasion", gabarit="une_deux", outcome="arret", player_team="Marseille", is_home=False)},
    ]


def _compte(chemin: Path, table: str) -> int:
    conn = sqlite3.connect(chemin)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def _narrer(base: Path, evenements: Path, *options: str) -> None:
    cli.main(["--db", str(base), "narrate", "--events", str(evenements), *options])


def test_un_flux_ecrit_a_la_main_est_raconte_de_bout_en_bout(base, tmp_path, capsys):
    _narrer(base, _jsonl(tmp_path / "e.jsonl", _evenements()))

    sortie = capsys.readouterr()
    assert sortie.out.splitlines() == [
        "12' Kylian Mbappé marque pour Lyon, face à Marseille !",
        "34' Ousmane Dembélé prend un carton jaune à la 34e minute.",
        "60' Changement chez Lyon : Rayan Cherki remplace Ousmane Dembélé.",
        "81' Mike Maignan repousse la frappe de Lyon !",  # le gardien (Marseille) : adversaire = le club du tireur
    ]
    assert "1 evenement(s) non commente(s)" in sortie.err  # le poteau
    assert _compte(base, "phrase_history") == 4  # un usage enregistre par evenement commente
    assert _compte(base, "similarity_signatures") == 4


def test_le_cooldown_agit_dans_le_flux_et_le_fallback_n_est_jamais_enregistre(base, tmp_path, capsys):
    deux_buts = [
        _base_evenement(event_id=0, minute=12, player_id=7, event_type="but", gabarit="contre_attaque"),
        _base_evenement(event_id=1, minute=40, player_id=7, event_type="but", gabarit="contre_attaque"),
    ]
    _narrer(base, _jsonl(tmp_path / "e.jsonl", deux_buts))
    lignes = capsys.readouterr().out.splitlines()
    assert lignes == [
        "12' Kylian Mbappé marque pour Lyon, face à Marseille !",
        "40' Le ballon termine au fond des filets.",  # l'unique phrase est en cooldown : phrase de secours
    ]
    assert _compte(base, "phrase_history") == 1  # le secours n'est pas inscrit


def test_dry_run_n_enregistre_rien(base, tmp_path, capsys):
    _narrer(base, _jsonl(tmp_path / "e.jsonl", _evenements()), "--dry-run")
    assert len(capsys.readouterr().out.splitlines()) == 4
    assert _compte(base, "phrase_history") == 0


def test_le_flux_est_deterministe_sur_deux_bases_fraiches(tmp_path, capsys):
    sorties = []
    for nom in ("a.db", "b.db"):
        base = _construire_base(tmp_path / nom)
        _narrer(base, _jsonl(tmp_path / f"{nom}.jsonl", _evenements()))
        sorties.append(capsys.readouterr().out)
    assert sorties[0] == sorties[1] != ""


def test_stdin_est_accepte(base, tmp_path, capsys, monkeypatch):
    contenu = "\n\n".join(json.dumps(e) for e in _evenements()[:1])
    monkeypatch.setattr("sys.stdin", io.StringIO(contenu))
    cli.main(["--db", str(base), "narrate", "--events", "-"])
    assert capsys.readouterr().out.startswith("12' Kylian Mbappé marque")


def test_un_evenement_invalide_arrete_le_flux_avec_sa_position(base, tmp_path, capsys):
    evenements = _evenements()[:2]
    evenements[1]["journe"] = 3  # faute de frappe : cle inconnue
    with pytest.raises(SystemExit) as sortie:
        _narrer(base, _jsonl(tmp_path / "e.jsonl", evenements))
    assert sortie.value.code == 1
    capture = capsys.readouterr()
    assert capture.out.splitlines() == ["12' Kylian Mbappé marque pour Lyon, face à Marseille !"]  # le 1er est deja raconte
    assert "Evenement n°1" in capture.err and "journe" in capture.err


def test_un_event_id_en_double_est_refuse(base, tmp_path, capsys):
    evenements = _evenements()[:1] * 2
    with pytest.raises(SystemExit) as sortie:
        _narrer(base, _jsonl(tmp_path / "e.jsonl", evenements))
    assert sortie.value.code == 1
    assert "deja vu" in capsys.readouterr().err


def test_un_scenario_absent_de_la_base_est_refuse(tmp_path, capsys):
    base = _construire_base(tmp_path / "sans_carton.db", sans=("CARTON_JAUNE",))
    with pytest.raises(SystemExit) as sortie:
        _narrer(base, _jsonl(tmp_path / "e.jsonl", _evenements()[1:2]))
    assert sortie.value.code == 1
    assert "CARTON_JAUNE" in capsys.readouterr().err


def test_un_joueur_inconnu_est_refuse(base, tmp_path, capsys):
    evenement = _base_evenement(event_id=0, player_id=999, event_type="but", gabarit="contre_attaque")
    with pytest.raises(SystemExit) as sortie:
        _narrer(base, _jsonl(tmp_path / "e.jsonl", [evenement]))
    assert sortie.value.code == 1
    assert "999" in capsys.readouterr().err


def test_json_invalide_et_fichier_absent(base, tmp_path, capsys):
    chemin = tmp_path / "e.jsonl"
    chemin.write_text(json.dumps(_evenements()[0]) + "\n{pas du json\n", encoding="utf-8")
    with pytest.raises(SystemExit) as sortie:
        _narrer(base, chemin)
    assert sortie.value.code == 1
    assert "Ligne 2" in capsys.readouterr().err

    with pytest.raises(SystemExit) as absent:
        _narrer(base, tmp_path / "absent.jsonl")
    assert absent.value.code == 1


def test_un_scenario_a_sec_sans_secours_sort_avec_le_code_2(tmp_path, capsys):
    base = _construire_base(tmp_path / "a_sec.db")
    conn = sqlite3.connect(base)
    conn.execute("DELETE FROM phrases WHERE is_fallback = 1 AND variant_id IN (SELECT id FROM variants WHERE scenario_id = 1)")
    conn.execute("UPDATE phrases SET is_active = 0 WHERE variant_id IN (SELECT id FROM variants WHERE scenario_id = 1)")
    conn.commit()
    conn.close()
    with pytest.raises(SystemExit) as sortie:
        _narrer(base, _jsonl(tmp_path / "e.jsonl", _evenements()[:1]))
    assert sortie.value.code == 2
    assert "BUT" in capsys.readouterr().err
