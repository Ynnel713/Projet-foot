"""scripts/export_match_to_nlg.py : deux clubs -> un .jsonl dans le dossier de sortie, lisible par
`cli.py narrate` du NLG (deuxieme processus, venv du NLG)."""

import json
import random
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import export_match_to_nlg as export  # noqa: E402
from ligue1sim.clubs import Club  # noqa: E402
from test_narrative import _clubs  # noqa: E402
from test_nlg_end_to_end import _SETUP_NLG, NLG_PYTHON, SCENARIOS, _nlg  # noqa: E402


@pytest.fixture
def clubs():
    random.seed(2026_10_01)
    np.random.seed(2026_10_01)
    home, away = _clubs()
    return tuple(Club(name=c.name, players=[replace(p, id=base + i) for i, p in enumerate(c.players)])
                 for base, c in ((1000, home), (2000, away)))


def test_next_match_sequence(tmp_path):
    assert export.next_match_sequence(tmp_path / "absent") == 1
    (tmp_path / "000004_x.jsonl").write_text("")
    (tmp_path / "000002_y.jsonl").write_text("")
    (tmp_path / "notes.txt").write_text("")
    assert export.next_match_sequence(tmp_path) == 5


def test_un_match_un_jsonl_rang_suivant(clubs, tmp_path):
    out = tmp_path / "nlg_inbox"  # le dossier est cree
    premier = export.export_match(*clubs, out, match_date="2026-10-01")
    assert premier.parent == out and premier.name.startswith("000001_")
    second = export.export_match(*clubs, out, match_date="2026-10-02")
    assert second.name.startswith("000002_")
    evenements = [json.loads(ligne) for ligne in premier.read_text(encoding="utf-8").splitlines()]
    assert evenements and {e["match_sequence"] for e in evenements} == {1}
    assert [e["minute"] for e in evenements] == sorted(e["minute"] for e in evenements)


def test_main_ecrit_dans_out_et_parametre_sequence(clubs, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(export, "_club", lambda nom, xlsx: clubs[0] if nom == "H" else clubs[1])
    export.main(["--home", "H", "--away", "A", "--out", str(tmp_path), "--match-sequence", "9",
                 "--date", "2026-10-01", "--competition", "L1", "--journee", "3", "--seed", "5"])
    [fichier] = tmp_path.glob("*.jsonl")
    assert fichier.name.startswith("000009_") and str(fichier) in capsys.readouterr().out
    premier = json.loads(fichier.read_text(encoding="utf-8").splitlines()[0])
    assert (premier["competition"], premier["journee"]) == ("L1", 3)


@pytest.mark.skipif(not NLG_PYTHON.exists(), reason="venv du NLG absent (simulafoot_nlg/.venv)")
def test_le_jsonl_produit_est_lisible_par_cli_narrate(clubs, tmp_path):
    fichier = export.export_match(*clubs, tmp_path / "nlg_inbox", match_date="2026-10-01")
    joueurs = [[p.id, p.name, p.poste] for c in clubs for p in c.players]
    db = tmp_path / "nlg.db"
    assert _nlg("-c", _SETUP_NLG, str(db), json.dumps(joueurs), json.dumps(SCENARIOS)).returncode == 0
    resultat = _nlg("cli.py", "--db", str(db), "narrate", "--events", str(fichier))
    assert resultat.returncode == 0, resultat.stderr
    evenements = [json.loads(ligne) for ligne in fichier.read_text(encoding="utf-8").splitlines()]
    commentes = [e for e in evenements if e.get("outcome") not in ("poteau", "barre")]
    assert len(resultat.stdout.splitlines()) == len(commentes) > 0
