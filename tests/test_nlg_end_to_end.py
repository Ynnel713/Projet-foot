"""Bout en bout, DEUX PROCESSUS (decision B2 n°5) : un match simule -> Timeline -> dicts -> JSON Lines
(racine, ce venv) -> `cli.py narrate` du NLG (son propre venv, sans `ligue1sim`) -> commentaires.

Saute si le venv du NLG est absent. La base du NLG est construite dans le processus NLG (son schema, ses
modules) : un scenario trivial par code, chaque phrase portant le code et le joueur."""

import json
import random
from dataclasses import replace
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from nlg_ingestion import jsonl_path, timeline_to_events, write_jsonl
from narrative import build_timeline
from test_narrative import _clubs, _simulate_one

from ligue1sim.clubs import Club
from ligue1sim.lineup import pick_best_formation
from ligue1sim.simulation import LeagueContext

RACINE = Path(__file__).resolve().parent.parent
NLG = RACINE / "simulafoot_nlg"
NLG_PYTHON = NLG / ".venv" / "Scripts" / "python.exe"

pytestmark = pytest.mark.skipif(not NLG_PYTHON.exists(), reason="venv du NLG absent (simulafoot_nlg/.venv)")

SCENARIOS = ["BUT", "COUP_FRANC", "CONSTRUCTION", "CORNER", "ARRET_GARDIEN", "PENALTY_RATE", "TIR_NON_CADRE",
             "DEFENSE", "CARTON_JAUNE", "CARTON_ROUGE", "REMPLACEMENT"]

# Execute DANS le venv du NLG : base vide au schema du NLG + joueurs + une phrase par scenario.
_SETUP_NLG = r"""
import json, sqlite3, sys
from pathlib import Path
from scripts.init_db import init_db
db, joueurs, scenarios = Path(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
init_db(db_path=db)
conn = sqlite3.connect(db)
conn.executemany("INSERT INTO players (id, first_name, last_name, position) VALUES (?, ?, '', ?)", joueurs)
for code in scenarios:
    sid = conn.execute("INSERT INTO scenarios (code, label) VALUES (?, ?)", (code, code)).lastrowid
    vid = conn.execute("INSERT INTO variants (scenario_id, code, label, is_default) VALUES (?, 'D', 'd', 1)", (sid,)).lastrowid
    pid = conn.execute("INSERT INTO phrases (variant_id, text) VALUES (?, ?)", (vid, code + " {joueur}")).lastrowid
    conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (?, 0)", (pid,))
    conn.execute("INSERT INTO phrase_slots (phrase_id, slot_name, expression) VALUES (?, 'joueur', 'player.full_name')", (pid,))
    conn.execute("INSERT INTO phrases (variant_id, text, is_fallback) VALUES (?, ?, 1)", (vid, code + " secours"))
conn.commit()
"""


def _nlg(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(NLG_PYTHON), *args], cwd=NLG, capture_output=True, text=True, encoding="utf-8", timeout=300)


@pytest.fixture
def match_simule():
    random.seed(2026_10_01)
    np.random.seed(2026_10_01)
    # Ids distincts (Player est frozen : on recree les joueurs avec leur id).
    home, away = (Club(name=c.name, players=[replace(p, id=base + i) for i, p in enumerate(c.players)])
                  for base, c in ((1000, _clubs()[0]), (2000, _clubs()[1])))
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    i = 0
    while True:
        result = _simulate_one(home, away, context, home_lineup, away_lineup, date=f"2026-10-{i + 1:02d}")
        if result is not None and result.goals:
            return home, away, result
        i += 1


def test_un_match_simule_est_raconte_par_le_nlg(match_simule, tmp_path):
    home, away, result = match_simule
    timeline = build_timeline(result)
    skipped: list = []
    dicts = timeline_to_events(timeline, match_sequence=7, home_squad=home.players, away_squad=away.players,
                               competition="Test", journee=1, skipped=skipped)
    assert dicts and not skipped  # effectifs sans homonymes, avec gardiens : rien d'ecarte

    fichier = write_jsonl(dicts, jsonl_path(tmp_path, timeline.match_id, 7))
    assert fichier.name.startswith("000007_") and fichier.suffix == ".jsonl"
    assert [json.loads(ligne) for ligne in fichier.read_text(encoding="utf-8").splitlines()] == dicts

    db = tmp_path / "nlg.db"
    joueurs = [[p.id, p.name, p.poste] for p in home.players + away.players]
    setup = _nlg("-c", _SETUP_NLG, str(db), json.dumps(joueurs), json.dumps(SCENARIOS))
    assert setup.returncode == 0, setup.stderr

    narration = _nlg("cli.py", "--db", str(db), "narrate", "--events", str(fichier))
    assert narration.returncode == 0, narration.stderr  # le NLG a valide TOUS les dicts (contrat, coherence)

    commentes = [d for d in dicts if not (d["event_type"] == "occasion" and d["outcome"] in ("poteau", "barre"))]
    lignes = narration.stdout.splitlines()
    assert len(lignes) == len(commentes)
    for ligne, d in zip(lignes, commentes):
        assert ligne.startswith(f"{d['minute']}' ")
    # l'acteur vient bien de la resolution racine : le nom du joueur (id -> base du NLG) est dans la ligne
    noms = {p.id: p.name for p in home.players + away.players}
    for ligne, d in zip(lignes, commentes):
        assert noms[d["player_id"]] in ligne


# --- receveur_id : un but de corner / coup franc / construction est raconte comme une passe decisive suivie d'un but ---

# Base NLG minimale : pour chacun des 3 scenarios, UNE phrase de but (slots passeur ET receveur, comme 20/20 COUP_FRANC,
# 18/20 CONSTRUCTION, 18/30 CORNER de la vraie banque) + une phrase de secours. Sans receveur_id, la phrase est
# inrendable et le NLG retombe sur le secours (les 2 buts de coup franc du match 7 de l'echantillon).
_SETUP_NLG_RECEVEUR = r"""
import json, sqlite3, sys
from pathlib import Path
from scripts.init_db import init_db
db, joueurs = Path(sys.argv[1]), json.loads(sys.argv[2])
init_db(db_path=db)
conn = sqlite3.connect(db)
conn.executemany("INSERT INTO players (id, first_name, last_name, position) VALUES (?, ?, '', ?)", joueurs)
for code in ("CORNER", "COUP_FRANC", "CONSTRUCTION"):
    sid = conn.execute("INSERT INTO scenarios (code, label) VALUES (?, ?)", (code, code)).lastrowid
    vid = conn.execute("INSERT INTO variants (scenario_id, code, label, is_default) VALUES (?, 'D', 'd', 1)", (sid,)).lastrowid
    pid = conn.execute("INSERT INTO phrases (variant_id, text) VALUES (?, ?)", (vid, "BUT " + code + " : {passeur} sert {receveur}")).lastrowid
    conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (?, 0)", (pid,))
    for nom, expr in (("passeur", "context.passeur.full_name"), ("receveur", "context.receveur.full_name")):
        conn.execute("INSERT INTO phrase_slots (phrase_id, slot_name, expression) VALUES (?, ?, ?)", (pid, nom, expr))
    conn.execute("INSERT INTO phrases (variant_id, text, is_fallback) VALUES (?, ?, 1)", (vid, code + " secours"))
conn.commit()
"""


@pytest.mark.skipif(not NLG_PYTHON.exists(), reason="venv du NLG absent (simulafoot_nlg/.venv)")
@pytest.mark.parametrize("gabarit,scenario", [("corner", "CORNER"), ("coup_franc", "COUP_FRANC"),
                                              ("construction_placee", "CONSTRUCTION")])
def test_un_but_sur_gabarit_a_passeur_est_raconte_avec_passeur_et_receveur(gabarit, scenario, tmp_path):
    from test_nlg_ingestion import _match
    from ligue1sim.events import GoalEvent

    goals = [GoalEvent(club_name="Home FC", scorer="h_17", assist="h_14", minute=12)]
    match_result, home, away = _match(goals)
    timeline = build_timeline(match_result)
    but = next(e for e in timeline.events if e.event_type == "but")
    timeline = replace(timeline, events=[replace(e, gabarit=gabarit) if e is but else e for e in timeline.events])
    dicts = [d for d in timeline_to_events(timeline, match_sequence=1, home_squad=home.players, away_squad=away.players)
             if d["event_type"] == "but"]
    assert len(dicts) == 1 and dicts[0]["receveur_id"] == 1017

    fichier = write_jsonl(dicts, tmp_path / "but.jsonl")
    db = tmp_path / "nlg.db"
    joueurs = [[p.id, p.name, p.poste] for p in home.players + away.players]
    assert _nlg("-c", _SETUP_NLG_RECEVEUR, str(db), json.dumps(joueurs)).returncode == 0
    resultat = _nlg("cli.py", "--db", str(db), "narrate", "--events", str(fichier))
    assert resultat.returncode == 0, resultat.stderr
    assert resultat.stdout.strip() == f"12' BUT {scenario} : h_14 sert h_17"  # pas "secours" : receveur = buteur

    # et SANS receveur_id (comportement d'avant la correction) : phrase inrendable -> secours
    sans = [{k: v for k, v in d.items() if k != "receveur_id"} for d in dicts]
    fichier2 = write_jsonl(sans, tmp_path / "sans.jsonl")
    avant = _nlg("cli.py", "--db", str(db), "narrate", "--events", str(fichier2), "--dry-run")
    assert avant.stdout.strip() == f"12' {scenario} secours"
