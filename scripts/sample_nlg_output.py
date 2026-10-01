"""Echantillon de lecture de la chaine complete (validation produit, V2.1) : pour chaque paire de clubs,
simule un match, l'exporte en .jsonl (`scripts/export_match_to_nlg.py`) et le fait raconter par le NLG
(deuxieme processus, venv du NLG, base REELLE copiee), puis ecrit un rapport lisible : un match par section,
chaque phrase commentee numerotee, avec son scenario et un marqueur [SECOURS] si c'est une phrase de secours.

    uv run python scripts/sample_nlg_output.py [--out data/nlg_samples] [--seed 2026]

Sorties dans `--out` : `rapport.md` (lecture), `resultats.json` (une entree par evenement, pour compter),
`inbox/*.jsonl` (un par match), `work.db` (copie de la base du NLG, remise a VIDE d'historique : le
cooldown et la similarite jouent d'un match a l'autre, dans l'ordre des paires -- la base du NLG n'est
jamais modifiee). Le texte vient de `cli.narrer_flux` (la fonction qu'appelle `cli.py narrate`) ; avant
chaque match, `cli.py narrate` est lance sur le meme fichier (copie de la base, meme etat) et son texte doit etre identique
(sinon le script s'arrete) : c'est la commande officielle qui est verifiee.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

import export_match_to_nlg as export  # noqa: E402

NLG = ROOT / "simulafoot_nlg"
NLG_PYTHON = NLG / ".venv" / "Scripts" / "python.exe"
DEFAULT_OUT = ROOT / "data" / "nlg_samples"
DEFAULT_SEED = 2026_10_01

PAIRS: list[tuple[str, str]] = [
    ("Olympique Lyon", "Olympique Marseille"),
    ("Paris Saint-Germain", "AS Monaco"),
    ("LOSC Lille", "RC Lens"),
    ("OGC Nice", "Stade Rennais FC"),
    ("RC Strasbourg Alsace", "Stade Brestois 29"),
    ("Arsenal FC", "Liverpool FC"),
    ("Manchester City", "Manchester United"),
    ("Chelsea FC", "Tottenham Hotspur"),
    ("Real Madrid", "FC Barcelona"),
    ("Bayern Munich", "Borussia Dortmund"),
    ("Inter Milan", "Juventus FC"),
    ("AC Milan", "SSC Napoli"),
    ("Bayer 04 Leverkusen", "RB Leipzig"),
    ("Sevilla FC", "Valencia CF"),
]

# Execute DANS le venv du NLG : raconte un fichier .jsonl avec la fonction de cli.py narrate, base en
# ecriture (cooldown/similarite enregistres), et imprime un JSON {"events": [...], "noms": {id: nom}}.
_NARRER = """
import json, sys
import cli
from engine.db import get_sqlite
from engine.selectivity import Selectivite
db, fichier = sys.argv[1], sys.argv[2]
conn = get_sqlite(db)
evenements = [json.loads(l) for l in open(fichier, encoding="utf-8") if l.strip()]
resultats = list(cli.narrer_flux(conn, evenements, Selectivite.depuis_base(conn)))
noms = {}
for e in evenements:
    for cle in ("player_id", "passeur_id", "sortant_id", "entrant_id"):
        if cle in e and e[cle] not in noms:
            noms[e[cle]] = " ".join(conn.execute("SELECT first_name, last_name FROM players WHERE id=?", (e[cle],)).fetchone())
conn.close()
sys.stdout.buffer.write(json.dumps({"events": resultats, "noms": noms}, ensure_ascii=False).encode("utf-8"))
"""


def _nlg(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(NLG_PYTHON), *args], cwd=NLG, capture_output=True, timeout=600,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def _score(evenements: list[dict]) -> tuple[int, int]:
    home = sum(1 for e in evenements if e["event_type"] == "but" and e["is_home"])
    away = sum(1 for e in evenements if e["event_type"] == "but" and not e["is_home"])
    return home, away


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--xlsx", type=Path, default=export.DEFAULT_XLSX)
    parser.add_argument("--db", type=Path, default=NLG / "data" / "simulafoot.db", help="Base du NLG (copiee, jamais modifiee)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--pairs-file", type=Path, help="JSON : liste de paires [club domicile, club exterieur]")
    args = parser.parse_args(argv)

    pairs = [tuple(p) for p in json.loads(args.pairs_file.read_text(encoding="utf-8"))] if args.pairs_file else PAIRS
    if len(pairs) < 10:
        raise SystemExit("Au moins 10 paires sont attendues pour un echantillon de lecture.")
    if not NLG_PYTHON.exists():
        raise SystemExit(f"venv du NLG introuvable : {NLG_PYTHON}")

    args.out.mkdir(parents=True, exist_ok=True)
    inbox = args.out / "inbox"
    shutil.rmtree(inbox, ignore_errors=True)
    work_db = args.out / "work.db"
    shutil.copyfile(args.db, work_db)
    conn = sqlite3.connect(work_db)
    conn.execute("DELETE FROM phrase_history")
    conn.execute("DELETE FROM similarity_signatures")
    conn.commit()
    conn.close()

    random.seed(args.seed)
    np.random.seed(args.seed)
    sections: list[str] = []
    resultats: list[dict] = []
    for rang, (home_name, away_name) in enumerate(pairs, 1):
        skipped: list[tuple[int, str]] = []
        fichier = export.export_match(
            export._club(home_name, args.xlsx), export._club(away_name, args.xlsx), inbox,
            match_sequence=rang, match_date=f"2026-10-{rang:02d}", competition="Echantillon", journee=rang, skipped=skipped,
        )
        evenements = [json.loads(ligne) for ligne in fichier.read_text(encoding="utf-8").splitlines()]

        copie = args.out / "work_verif.db"  # cli.py narrate (enregistrant) sur une COPIE : meme etat de depart
        shutil.copyfile(work_db, copie)
        officiel = _nlg("cli.py", "--db", str(copie), "narrate", "--events", str(fichier))
        if officiel.returncode != 0:
            raise SystemExit(f"cli.py narrate a echoue sur {fichier.name} :\n{officiel.stderr.decode('utf-8', 'replace')}")
        narre = _nlg("-c", _NARRER, str(work_db), str(fichier))
        if narre.returncode != 0:
            raise SystemExit(f"narrer_flux a echoue sur {fichier.name} :\n{narre.stderr.decode('utf-8', 'replace')}")
        donnees = json.loads(narre.stdout.decode("utf-8"))
        lignes = [f"{r['minute']}' {r['texte']}" for r in donnees["events"] if r["texte"] is not None]
        if lignes != officiel.stdout.decode("utf-8").splitlines():
            raise SystemExit(f"{fichier.name} : cli.py narrate et narrer_flux divergent -- echantillon invalide.")

        noms = {int(k): v for k, v in donnees["noms"].items()}
        par_id = {e["event_id"]: e for e in evenements}
        h, a = _score(evenements)
        sections.append(f"## Match {rang} -- {home_name} {h}-{a} {away_name}\n")
        n = 0
        for r in donnees["events"]:
            e = par_id[r["event_id"]]
            acteur = f"{noms[e['player_id']]} ({e['player_team']})"
            if r["texte"] is None:
                sections.append(f"- _non commente_ : {r['minute']}' {e['event_type']}/{e.get('outcome')} -- {acteur}")
            else:
                n += 1
                marque = " **[SECOURS]**" if r["secours"] else ""
                sections.append(f"{n}. {r['minute']}' `{r['scenario']}`{marque} -- {r['texte']}  \n   _acteur : {acteur}_")
            resultats.append({"match": rang, "home": home_name, "away": away_name, **r,
                              "gabarit": e.get("gabarit"), "outcome": e.get("outcome"), "event_type": e["event_type"],
                              "acteur": noms[e["player_id"]], "club": e["player_team"],
                              "score_context": e["score_context"]})
        for event_id, raison in skipped:
            sections.append(f"- _evenement {event_id} ecarte a l'export_ : {raison}")
        sections.append("")
        print(f"[{rang}/{len(pairs)}] {home_name} {h}-{a} {away_name} : {n} phrases", file=sys.stderr)

    entete = (f"# Echantillon NLG -- {len(pairs)} matchs simules (graine {args.seed})\n\n"
              "Genere par `scripts/sample_nlg_output.py`. Base du NLG reelle, historique vide au depart ; "
              "cooldown et similarite jouent d'un match a l'autre.\n")
    (args.out / "rapport.md").write_text(entete + "\n" + "\n".join(sections), encoding="utf-8")
    (args.out / "resultats.json").write_text(json.dumps(resultats, ensure_ascii=False, indent=1), encoding="utf-8")
    (args.out / "work_verif.db").unlink(missing_ok=True)
    print(args.out / "rapport.md")


if __name__ == "__main__":
    main()
