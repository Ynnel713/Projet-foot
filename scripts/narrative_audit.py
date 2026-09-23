"""Audit par lot du moteur narratif (brief "narrative engine foundations",
23/09/2026, Tâche 6) -- simule 1000 matchs via le pipeline existant
(`ligue1sim.simulation.simulate_match`), construit une `Timeline` pour
chacun (`engine.narrative.build_timeline`) et rapporte les distributions
clés + le taux de violation des invariants (attendu : 0 sur les timelines
effectivement construites).

Déterminisme (Tâche 6.3) : `simulation.py` ET `events.py` tirent depuis
l'état ALÉATOIRE GLOBAL, `numpy` (`np.random.uniform`/`.poisson`/`.choice`)
ET stdlib `random` (`random.randint`/`.random`/`.choice`/`.shuffle`/`.gauss`,
minutes de but comprises -- voir leur code, non modifié ici) -- ce script
seed donc CES DEUX états globaux une fois au démarrage, uniquement pour que
la SÉQUENCE de matchs simulés soit reproductible d'un run à l'autre.
`engine.narrative.build_timeline` reste, lui, seedé localement par match
(jamais l'état global), inchangé.

Usage :
    uv run python scripts/narrative_audit.py [--n N]
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import numpy as np  # noqa: E402

from ligue1sim.clubs import Club  # noqa: E402
from ligue1sim.lineup import pick_best_formation  # noqa: E402
from ligue1sim.players import Player  # noqa: E402
from ligue1sim.schedule import Match  # noqa: E402
from ligue1sim.simulation import LeagueContext, simulate_match  # noqa: E402

from narrative import (  # noqa: E402
    BUT,
    _MIN_MINUTE_GAP,
    AntiRepetitionUnsatisfiableError,
    MinuteCollisionError,
    _has_cyclic_pattern,
    build_timeline,
    match_result_from,
)

_AUDIT_SEED = 2026_09_23  # date du brief, arbitraire mais fixe -- voir docstring de module
_DEFAULT_N = 1000
_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "narrative_audit_report.md"


def _player(poste: str, note: float, name: str) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST")


def _squad(club_name: str, note: float) -> list[Player]:
    squad = [_player("GK", note, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("DC", note, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_player("LB", note, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("RB", note, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("MC", note, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_player("MOC", note, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("AG", note, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("AD", note, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("BU", note, f"{club_name}_cf{i}") for i in range(4)]
    return squad


def run(n: int) -> str:
    random.seed(_AUDIT_SEED)
    np.random.seed(_AUDIT_SEED)

    home = Club(name="Home FC", players=_squad("home", 72.0))
    away = Club(name="Away FC", players=_squad("away", 68.0))
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)

    timelines = []
    n_collisions = n_unsatisfiable = n_attempted = 0
    i = 0
    while len(timelines) < n:
        home_goals, away_goals, events = simulate_match(home, away, context)
        i += 1
        if events is None:
            continue
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        result = match_result_from(match, events, home_lineup, away_lineup, date=str(i))
        n_attempted += 1
        try:
            timelines.append(build_timeline(result))
        except MinuteCollisionError:
            n_collisions += 1
        except AntiRepetitionUnsatisfiableError:
            n_unsatisfiable += 1

    total_tried = n_attempted + n_collisions + n_unsatisfiable

    occasion_counts = [len(t.events) for t in timelines]
    gabarit_hist = Counter(e.gabarit for t in timelines for e in t.events)
    outcome_hist = Counter(e.outcome for t in timelines for e in t.events)
    bracket_hist = Counter((e.minute - 1) // 15 for t in timelines for e in t.events)

    score_violations = 0
    sort_violations = 0
    pair_repeat_violations = 0
    player_repeat_violations = 0
    gap_violations = 0
    cyclic_violations = 0
    for t in timelines:
        goal_events = [e for e in t.events if e.event_type == BUT]
        if len(goal_events) != t.home_goals + t.away_goals:
            score_violations += 1
        elif any(e.outcome != "but" for e in goal_events) or any(e.outcome == "but" for e in t.events if e.event_type != BUT):
            score_violations += 1

        minutes = [e.minute for e in t.events]
        if minutes != sorted(minutes) or len(minutes) != len(set(minutes)):
            sort_violations += 1

        couples = [(e.gabarit, e.declinaison) for e in t.events]
        if any(a == b for a, b in zip(couples, couples[1:])):
            pair_repeat_violations += 1
        players = [e.main_player for e in t.events]
        if any(a == b for a, b in zip(players, players[1:])):
            player_repeat_violations += 1
        events_sorted = sorted(t.events, key=lambda e: e.minute)
        if any(
            (b.minute - a.minute) < _MIN_MINUTE_GAP
            for a, b in zip(events_sorted, events_sorted[1:])
            if not (a.event_type == BUT and b.event_type == BUT)
        ):
            gap_violations += 1
        if _has_cyclic_pattern([e.gabarit for e in t.events]):
            cyclic_violations += 1

    lines = [
        "# Rapport d'audit du moteur narratif",
        "",
        f"Brief \"narrative engine foundations\" (23/09/2026), Tâche 6 -- `scripts/narrative_audit.py`, "
        f"seed numpy fixe `{_AUDIT_SEED}` (déterministe, voir docstring du script).",
        "",
        f"**{len(timelines)} timelines construites avec succès sur {total_tried} matchs simulés tentés.**",
        "",
        "## Matchs exclus (dette du moteur de résultats, voir docs/narrative_timeline_schema.md)",
        "",
        f"- Collisions de minute entre deux buts réels (`MinuteCollisionError`) : {n_collisions} ({n_collisions / total_tried:.2%})",
        f"- Règles anti-répétition structurellement insatisfiables (`AntiRepetitionUnsatisfiableError`) : {n_unsatisfiable} ({n_unsatisfiable / total_tried:.2%})",
        "",
        "## Distribution du nombre d'occasions par match",
        "",
        f"- Moyenne : {statistics.mean(occasion_counts):.2f}",
        f"- Écart-type : {statistics.pstdev(occasion_counts):.2f}",
        f"- Min : {min(occasion_counts)}",
        f"- Max : {max(occasion_counts)}",
        "",
        "## Distribution des gabarits utilisés",
        "",
    ]
    for name, count in gabarit_hist.most_common():
        lines.append(f"- `{name}` : {count} ({count / sum(gabarit_hist.values()):.2%})")
    lines += ["", "## Distribution des issues", ""]
    for name, count in outcome_hist.most_common():
        lines.append(f"- `{name}` : {count} ({count / sum(outcome_hist.values()):.2%})")
    lines += ["", "## Distribution temporelle (par tranche de 15 minutes)", ""]
    for bracket in sorted(bracket_hist):
        start, end = bracket * 15 + 1, bracket * 15 + 15
        lines.append(f"- {start}-{end}min : {bracket_hist[bracket]}")
    lines += [
        "",
        "## Vérification des propriétés anti-répétition (taux de violation, attendu 0)",
        "",
        f"- Répétition immédiate (gabarit, déclinaison) : {pair_repeat_violations}/{len(timelines)} ({pair_repeat_violations / len(timelines):.2%})",
        f"- Répétition immédiate du joueur principal : {player_repeat_violations}/{len(timelines)} ({player_repeat_violations / len(timelines):.2%})",
        f"- Écart minimum entre occasions non respecté : {gap_violations}/{len(timelines)} ({gap_violations / len(timelines):.2%})",
        f"- Pattern cyclique (periode <=5) sur les gabarits : {cyclic_violations}/{len(timelines)} ({cyclic_violations / len(timelines):.2%})",
        "",
        "## Vérification de l'invariant score (taux de violation, attendu 0)",
        "",
        f"- Score/buts incohérents avec les données d'entrée : {score_violations}/{len(timelines)} ({score_violations / len(timelines):.2%})",
        f"- Tri chronologique non strict : {sort_violations}/{len(timelines)} ({sort_violations / len(timelines):.2%})",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=_DEFAULT_N, help=f"nombre de timelines a construire (defaut {_DEFAULT_N})")
    args = parser.parse_args()

    report = run(args.n)
    _OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nRapport ecrit : {_OUTPUT_PATH}")
