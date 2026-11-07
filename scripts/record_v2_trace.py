"""Enregistre une VRAIE trace de match V2 pour la rejouer à l'écran sans l'API (ticket v2-ecran-match/00).

Usage : uv run python -m scripts.record_v2_trace <nom> <domicile> <extérieur> [graine]

Le match est calculé par le moteur, graine fixée (`random.seed`, D-V06 : mêmes octets à graine égale), via la route
publique `create_match` de l'API (`api.routers.v2`), appelée en processus : le fichier contient donc la trace que l'écran
reçoit, marquée terminée (`done`), plus les deux feuilles de match (`club_lineup`). Écrit
`ui/src/dev/fixtures/<nom>.json` (ignoré par git). Rien n'est inventé ni modifié : lecture du moteur seulement."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from api.routers.v2 import SimulateV2Request, club_lineup, create_match

OUT = Path(__file__).resolve().parent.parent / "ui" / "src" / "dev" / "fixtures"


def record(home: str, away: str, seed: int) -> dict:
    random.seed(seed)
    trace = create_match(SimulateV2Request(home=home, away=away))  # calcul complet, comme la route POST /api/v2/matches
    return {
        **trace.model_dump(),
        # champs de la lecture par morceaux (`MatchProgressOut`) : tout est déjà calculé
        "done": True, "error": None, "first_tick": 0,
        "lineups": {"home": club_lineup(home).model_dump(), "away": club_lineup(away).model_dump()},
        "seed": seed,
    }


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    name, home, away = sys.argv[1:4]
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20261107
    data = record(home, away, seed)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{name}: {data['home']} {data['home_goals']}-{data['away_goals']} {data['away']} | "
          f"{len(data['ticks'])} images, temps additionnel {data['added_minutes']} | {path.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()
