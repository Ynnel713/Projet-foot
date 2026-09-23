"""Audit par lot du moteur narratif (brief "narrative engine foundations"
puis "constraint priority", 23/09/2026, Tâche 6 puis 3) -- simule des
matchs via le pipeline existant (`ligue1sim.simulation.simulate_match`),
construit une `Timeline` pour chacun (`engine.narrative.build_timeline`) et
rapporte les distributions clés + le taux de violation des invariants
(attendu : 0).

Sémantique brief "constraint priority" -- ÉCART attendu par rapport à
l'audit précédent : `build_timeline` ne rejette PLUS AUCUN match
(`MinuteCollisionError`/`AntiRepetitionUnsatisfiableError` retirées, voir
engine/narrative.py, PRIORITÉ DES CONTRAINTES) -- les règles anti-répétition
ne sont vérifiées ici QUE sur les `generated_events` (occasions inventées,
`event_type == "occasion"`), jamais sur les `existing_events` (buts réels,
hors périmètre de ces règles). Ce rapport traite donc TOUJOURS exactement
`n` matchs, contre ~92-96% de `n` dans la version précédente (matchs
exclus par collision de minute ou règle insatisfiable).

Déterminisme (Tâche 6.3 puis 3.1, inchangé) : `simulation.py` ET `events.py`
tirent depuis l'état ALÉATOIRE GLOBAL, `numpy` (`.uniform`/`.poisson`/
`.choice`) ET stdlib `random` (`.randint`/`.random`/`.choice`/`.shuffle`/
`.gauss`, minutes de but comprises -- voir leur code, non modifié ici) --
ce script seed donc CES DEUX états globaux une fois au démarrage.
`engine.narrative.build_timeline` reste, lui, seedé localement par match.

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

from narrative import BUT, OCCASION, _MIN_MINUTE_GAP, _has_cyclic_pattern, build_timeline, match_result_from  # noqa: E402

_AUDIT_SEED = 2026_09_23  # date du brief, arbitraire mais fixe -- voir docstring de module
_DEFAULT_N = 1000  # aucun rejet desormais (voir docstring) : 1000 matchs simules = 1000 timelines
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
    n_attempted = 0
    i = 0
    while len(timelines) < n:
        home_goals, away_goals, events = simulate_match(home, away, context)
        i += 1
        if events is None:
            continue
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        result = match_result_from(match, events, home_lineup, away_lineup, date=str(i))
        n_attempted += 1
        timelines.append(build_timeline(result))  # aucun rejet possible desormais, voir docstring de module

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
        if minutes != sorted(minutes):
            sort_violations += 1

        # Regles anti-repetition VERIFIEES UNIQUEMENT sur generated_events
        # (brief "constraint priority") -- existing_events (buts) hors perimetre.
        generated = [e for e in t.events if e.event_type == OCCASION]
        couples = [(e.gabarit, e.declinaison) for e in generated]
        if any(a == b for a, b in zip(couples, couples[1:])):
            pair_repeat_violations += 1
        players = [e.main_player for e in generated]
        if any(a == b for a, b in zip(players, players[1:])):
            player_repeat_violations += 1
        gen_minutes = sorted(e.minute for e in generated)
        if any((b - a) < _MIN_MINUTE_GAP for a, b in zip(gen_minutes, gen_minutes[1:])):
            gap_violations += 1
        if _has_cyclic_pattern([e.gabarit for e in generated]):
            cyclic_violations += 1

    lines = [
        "# Rapport d'audit du moteur narratif",
        "",
        "Brief \"constraint priority\" (23/09/2026), Tâche 3 -- `scripts/narrative_audit.py`, "
        f"seed fixe `{_AUDIT_SEED}` (déterministe, voir docstring du script).",
        "",
        "**Priorité des contraintes formalisée** (voir `engine/narrative.py`, PRIORITÉ DES CONTRAINTES) : "
        "les règles anti-répétition/écart minimum ne gouvernent QUE les occasions inventées "
        "(`generated_events`), jamais les buts réels (`existing_events`, hors périmètre). "
        "**Conséquence : aucun match n'est plus rejeté** -- `build_timeline` ne lève plus jamais "
        "d'exception. Écart avec l'audit précédent : ce rapport traite exactement "
        f"`n`={n} matchs (contre ~92-96% de `n` avant, le reste étant alors exclu par "
        "collision de minute ou règle anti-répétition structurellement insatisfiable).",
        "",
        f"**{len(timelines)} timelines construites sur {n_attempted} matchs simulés -- 0 rejeté.**",
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
        "## Vérification des propriétés anti-répétition sur `generated_events` uniquement (taux de violation, attendu 0)",
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
    parser.add_argument("--n", type=int, default=_DEFAULT_N, help=f"nombre de matchs a traiter (defaut {_DEFAULT_N})")
    args = parser.parse_args()

    report = run(args.n)
    _OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Rapport ecrit : {_OUTPUT_PATH}")
