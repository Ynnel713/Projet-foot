"""Echantillon de 14 matchs simules racontes par le NLG (base reelle copiee) : invariants d'anti-repetition et de
variete mesures de bout en bout. Lourd (~1 min : simulation + deux processus NLG), donc `integration` -- a lancer
avec `pytest -m integration tests/test_nlg_echantillon.py`. Saute si le venv du NLG ou le classeur de joueurs manque.

Les seuils viennent du ticket « repetitions » du 02/10/2026 (voir simulafoot_nlg/SPEC_ANTI_REPEAT.md, derniere section)."""

import json
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sample_nlg_output as sample  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not sample.NLG_PYTHON.exists(), reason="venv du NLG absent (simulafoot_nlg/.venv)"),
    pytest.mark.skipif(not sample.export.DEFAULT_XLSX.exists(), reason="data/joueurs.xlsx absent"),
    pytest.mark.skipif(not (sample.NLG / "data" / "simulafoot.db").exists(), reason="base du NLG absente (cli.py init-db, import-players, import-seed)"),
]

# Execute dans le venv du NLG : rejoue les 14 fichiers sur une copie VIERGE de la base du NLG, avec les memes graines
# que l'echantillon (memes choix), en comptant les tirages ou une variante SURNOM ET la variante DEFAUT ont chacune un
# candidat (les seuls ou SURNOM peut sortir) et ceux ou SURNOM est sorti.
_COMPTER_SURNOM = """
import json, sys, glob, shutil
import cli
import engine.phrase_selector as module
from engine.db import get_sqlite
from engine.selectivity import Selectivite
db, inbox = sys.argv[1], sys.argv[2]
compte = {"eligibles": 0, "surnom": 0}
tirer = module._tirer
def espion(groupes, rng):
    resultat = tirer(groupes, rng)
    if {v.code for v, _ in groupes} >= {"SURNOM", "DEFAUT"}:
        compte["eligibles"] += 1
        compte["surnom"] += any(r.phrase.id == resultat.phrase.id for v, rs in groupes if v.code == "SURNOM" for r in rs)
    return resultat
module._tirer = espion
conn = get_sqlite(db)
conn.execute("DELETE FROM phrase_history"); conn.execute("DELETE FROM similarity_signatures"); conn.commit()
selectivite = Selectivite.depuis_base(conn)
for fichier in sorted(glob.glob(inbox + "/*.jsonl")):
    list(cli.narrer_flux(conn, [json.loads(l) for l in open(fichier, encoding="utf-8") if l.strip()], selectivite))
print(json.dumps(compte))
"""


# Execute dans le venv du NLG : phrases conditionnees eligibles pour plus de 30 % des evenements de leur scenario.
_CONDITIONS_LARGES = """
import json, sys
from pathlib import Path
from engine.db import get_sqlite
from scripts.audit_conditions_larges import _lire, conditions_larges
conn = get_sqlite(sys.argv[1])
print(json.dumps([[g["scenario"], g["phrase_id"], g["conditions"], round(g["part"], 3)] for g in conditions_larges(conn, _lire(Path(sys.argv[2])))]))
"""

# Conditions larges tolerees : celles de contexte (`score_context == "ouverture_score"` : le premier but arrive a 0-0, donc
# pour beaucoup d'evenements) et « Changement precoce » (minute <= 55), dont le resserrement reporte ses tirages sur les
# modeles sans condition et fait depasser le plafond de 12 usages.
SEUIL_CONDITIONS_LARGES = 3


@pytest.fixture(scope="module")
def echantillon(tmp_path_factory):
    sortie = tmp_path_factory.mktemp("nlg_samples")
    sample.main(["--out", str(sortie)])
    rapport = json.loads((sortie / "resultats.json").read_text(encoding="utf-8"))
    base = sqlite3.connect(sortie / "work.db")
    historique = base.execute(
        """SELECT h.match_sequence, h.phrase_id, h.player_id, h.rendered_text, v.code, s.code, p.text
           FROM phrase_history h JOIN phrases p ON p.id = h.phrase_id JOIN variants v ON v.id = p.variant_id
           JOIN scenarios s ON s.id = v.scenario_id ORDER BY h.id"""
    ).fetchall()
    conditions_joker = base.execute(
        "SELECT c.value FROM phrase_conditions c JOIN phrases p ON p.id = c.phrase_id WHERE p.text LIKE 'Le joker sort%'"
    ).fetchall()
    base.close()
    copie = sortie / "compte.db"
    copie.write_bytes((sample.NLG / "data" / "simulafoot.db").read_bytes())
    mesure = subprocess.run(
        [str(sample.NLG_PYTHON), "-c", _COMPTER_SURNOM, str(copie), str(sortie / "inbox")],
        cwd=sample.NLG, capture_output=True, timeout=900,
    )
    assert mesure.returncode == 0, mesure.stderr.decode("utf-8", "replace")
    larges = subprocess.run(
        [str(sample.NLG_PYTHON), "-c", _CONDITIONS_LARGES, str(sample.NLG / "data" / "simulafoot.db"), str(sortie / "inbox")],
        cwd=sample.NLG, capture_output=True, timeout=900,
    )
    assert larges.returncode == 0, larges.stderr.decode("utf-8", "replace")
    return {"rapport": rapport, "historique": historique, "joker": conditions_joker, "surnom": json.loads(mesure.stdout),
            "larges": json.loads(larges.stdout)}


def test_taux_surnom(echantillon):
    """SURNOM (poids 0.35) : 20 a 30 % des tirages ou il est eligible face a DEFAUT, et 5 a 10 % de toutes les lignes
    (plafond ~13 % : eligible dans ~26 % des tirages, 5 a 8 modeles par scenario, memoire inter-joueurs)."""
    compte = echantillon["surnom"]
    assert compte["eligibles"] >= 50  # l'echantillon est assez grand pour mesurer
    assert 0.20 <= compte["surnom"] / compte["eligibles"] <= 0.30
    lignes = echantillon["historique"]
    assert 0.05 <= sum(ligne[4] == "SURNOM" for ligne in lignes) / len(lignes) <= 0.10


def test_joker_seuil(echantillon):
    """Avec `fm_rating >= 82`, « Le joker… » ne prend plus que quelques changements (31 sur 114 avec `>= 80`)."""
    assert echantillon["joker"] == [("82",)]
    changements = [ligne for ligne in echantillon["historique"] if ligne[5] == "REMPLACEMENT"]
    jokers = [ligne for ligne in changements if ligne[6].startswith("Le joker sort")]
    assert len(changements) > 100
    assert len(jokers) / len(changements) <= 0.20


def test_aucune_domination_d_un_modele(echantillon):
    usages = Counter(ligne[1] for ligne in echantillon["historique"])
    assert max(usages.values()) <= 12  # 31 avant (« Le joker… »)


def test_invariants_de_repetition(echantillon):
    historique = echantillon["historique"]
    assert not [r for r in echantillon["rapport"] if r.get("secours")]
    # (a) meme phrase pour le meme joueur : jamais ; (b) meme texte pour des joueurs differents : jamais
    assert max(Counter((ligne[1], ligne[2]) for ligne in historique).values()) == 1
    assert max(Counter(ligne[3] for ligne in historique).values()) == 1
    # REMPLACEMENT : un meme modele ne sort jamais deux fois dans un meme match
    par_match = Counter((ligne[0], ligne[1]) for ligne in historique if ligne[5] == "REMPLACEMENT")
    assert max(par_match.values()) == 1


def test_conditions_larges_non_dominantes(echantillon):
    """Au plus 3 phrases conditionnees eligibles pour plus de 30 % des evenements de leur scenario (16 avant le ticket
    banque du 02/10/2026) ; la liste est dans le message d'echec."""
    larges = echantillon["larges"]
    assert len(larges) <= SEUIL_CONDITIONS_LARGES, larges
