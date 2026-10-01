"""Simule un match entre deux clubs et l'exporte pour le NLG : match -> `Timeline` -> dicts du contrat
(`engine/nlg_ingestion.py`) -> un fichier JSON Lines, a raconter ensuite avec le NLG (deux processus) :

    uv run python scripts/export_match_to_nlg.py --home "Olympique Lyon" --away "Olympique Marseille"
    cd simulafoot_nlg && .venv/Scripts/python cli.py narrate --events ../data/nlg_inbox/000001_<match>.jsonl

Sortie : `data/nlg_inbox/` par convention (`--out` pour changer), un fichier par match, nomme
`<match_sequence sur 6 chiffres>_<match_id>.jsonl`. `--match-sequence` (rang du match dans la sequence
jouee, unite du cooldown du NLG) vaut par defaut le rang suivant dans le dossier de sortie. Les
evenements ecartes (homonyme dans un club, joueur sans id, pas de gardien) sont listes sur stderr.
`--seed` fixe les etats aleatoires globaux du moteur (simulation.py/events.py) pour rejouer un match.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "engine"))

import numpy as np  # noqa: E402

from ligue1sim.clubs import Club, load_all_clubs  # noqa: E402
from ligue1sim.lineup import pick_best_formation  # noqa: E402
from ligue1sim.schedule import Match  # noqa: E402
from ligue1sim.simulation import LeagueContext, simulate_match  # noqa: E402

from narrative import build_timeline, match_result_from  # noqa: E402
from nlg_ingestion import jsonl_path, timeline_to_events, write_jsonl  # noqa: E402

DEFAULT_XLSX = ROOT / "data" / "joueurs.xlsx"
DEFAULT_OUT = ROOT / "data" / "nlg_inbox"
_RANG = re.compile(r"^(\d{6})_.*\.jsonl$")


def next_match_sequence(out: Path) -> int:
    """Rang suivant dans `out` : 1 + le plus grand prefixe `NNNNNN_` deja present (1 si le dossier est vide)."""
    rangs = [int(m.group(1)) for f in out.glob("*.jsonl") if (m := _RANG.match(f.name))] if out.exists() else []
    return max(rangs, default=0) + 1


def export_match(
    home: Club,
    away: Club,
    out: Path,
    *,
    match_sequence: int | None = None,
    match_date: str | None = None,
    competition: str | None = None,
    journee: int | None = None,
    skipped: list[tuple[int, str]] | None = None,
) -> Path:
    """Simule `home` - `away`, convertit et ecrit le `.jsonl` ; retourne son chemin. Un match sans
    evenements (compos synthetiques) est resimule ; `RuntimeError` si les clubs n'en produisent jamais."""
    match_date = match_date or date.today().isoformat()
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    for _ in range(50):
        home_goals, away_goals, events = simulate_match(home, away, context)
        if events is not None:
            break
    else:
        raise RuntimeError(f"{home.name} - {away.name} : aucun evenement de match (effectifs reels requis)")
    match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
    timeline = build_timeline(match_result_from(match, events, home_lineup, away_lineup, date=match_date,
                                                competition_type=None))
    if match_sequence is None:
        match_sequence = next_match_sequence(out)
    dicts = timeline_to_events(timeline, match_sequence=match_sequence, home_squad=home.players,
                               away_squad=away.players, competition=competition, journee=journee, skipped=skipped)
    return write_jsonl(dicts, jsonl_path(out, timeline.match_id, match_sequence))


def _club(nom: str, xlsx: Path) -> Club:
    options = [o for o in load_all_clubs(xlsx) if o.name == nom]
    if not options:
        raise SystemExit(f"Club introuvable dans {xlsx} : {nom!r}")
    if len(options) > 1:
        raise SystemExit(f"Club ambigu ({[o.championnat for o in options]}) : {nom!r}")
    return options[0].as_club()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--home", required=True, help="Club a domicile (nom exact dans le classeur)")
    parser.add_argument("--away", required=True, help="Club a l'exterieur")
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX, help="Classeur des joueurs (defaut : data/joueurs.xlsx)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Dossier de sortie (defaut : data/nlg_inbox)")
    parser.add_argument("--match-sequence", type=int, help="Rang du match (defaut : suivant dans --out)")
    parser.add_argument("--date", help="Date du match (AAAA-MM-JJ, defaut : aujourd'hui) -- entre dans le match_id")
    parser.add_argument("--competition", help="Libelle de competition transmis au NLG")
    parser.add_argument("--journee", type=int, help="Numero de journee transmis au NLG")
    parser.add_argument("--seed", type=int, help="Fixe random et numpy pour rejouer le match")
    args = parser.parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    skipped: list[tuple[int, str]] = []
    chemin = export_match(_club(args.home, args.xlsx), _club(args.away, args.xlsx), args.out,
                          match_sequence=args.match_sequence, match_date=args.date,
                          competition=args.competition, journee=args.journee, skipped=skipped)
    for event_id, raison in skipped:
        print(f"evenement {event_id} ecarte : {raison}", file=sys.stderr)
    print(chemin)


if __name__ == "__main__":
    main()
