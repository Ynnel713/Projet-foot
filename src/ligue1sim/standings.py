"""Calcul du classement à partir des matchs joués du calendrier."""

from __future__ import annotations

import pandas as pd

from ligue1sim.clubs import Club
from ligue1sim.schedule import Journee, Match

STANDINGS_COLUMNS = ["Club", "J", "G", "N", "P", "BP", "BC", "Diff", "Pts"]


def compute_standings(clubs: list[Club], calendar: list[Journee]) -> pd.DataFrame:
    """Calcule le classement (points 3/1/0) à partir de tous les matchs joués.

    Tri : points desc, puis différence de buts desc, puis buts pour desc
    (version simplifiée, sans confrontations directes).
    """
    stats = {c.name: dict(J=0, G=0, N=0, P=0, BP=0, BC=0) for c in clubs}

    for journee in calendar:
        for match in journee.matches:
            if match.played:
                _apply_match(stats, match)

    rows = []
    for name, s in stats.items():
        rows.append({"Club": name, **s, "Diff": s["BP"] - s["BC"], "Pts": s["G"] * 3 + s["N"]})

    df = pd.DataFrame(rows, columns=STANDINGS_COLUMNS)
    df = df.sort_values(by=["Pts", "Diff", "BP"], ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rang"
    return df


def _apply_match(stats: dict[str, dict[str, int]], match: Match) -> None:
    home, away = stats[match.home], stats[match.away]
    home["J"] += 1
    away["J"] += 1
    home["BP"] += match.home_goals
    home["BC"] += match.away_goals
    away["BP"] += match.away_goals
    away["BC"] += match.home_goals

    if match.home_goals > match.away_goals:
        home["G"] += 1
        away["P"] += 1
    elif match.home_goals < match.away_goals:
        away["G"] += 1
        home["P"] += 1
    else:
        home["N"] += 1
        away["N"] += 1
