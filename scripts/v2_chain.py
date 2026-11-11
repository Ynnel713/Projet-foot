"""Lecture de la chaîne d'un but et origine des buts (ticket v2-realisme/19e). Lecture seule du journal
`MatchTrace.events` (ticket 19b) : rien ici ne modifie le jeu. Définitions : `docs/INDICATEURS_V2.md`, section 24.

Origine d'un but : en remontant la chaîne depuis le but, le premier événement qui donne le ballon à l'équipe qui marque
(début de sa possession). Les arrêts et contres adverses, et la faute adverse laissée en avantage, ne rendent pas le
ballon à l'adversaire : l'attaque continue (rebond, avantage).

Constantes du ticket (recommandations retenues par délégation du propriétaire, 10/11/2026) :
- coup de pied arrêté : corner, coup franc (dont celui d'un hors-jeu, qui n'a pas d'événement de remise), penalty ;
  la touche est comptée à part, pour pouvoir l'ajouter selon la définition du repère comparé ;
- limite de temps `SET_PIECE_WINDOW_S` : un but plus de 15 s après la remise n'en vient plus, il est « jeu placé après
  <remise> ».

Utilisation : `uv run python -m scripts.v2_chain 20` (origine des buts des matchs 0 à 19 du banc) ou
`uv run python -m scripts.v2_chain --match 3 --but 1` (chaîne du 2e but du match 3)."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import dataclass

from v2engine.restart import CORNER, FREE_KICK, GOAL_KICK, KICKOFF, PENALTY, THROW_IN
from v2engine.trace import (ARRET, BUT, CONTRE, CONTROLE_RATE, FAUTE, HORS_JEU, PERTE, REMISE, TOUCHE_LONGUE,
                            TraceEvent, chain)

SET_PIECE_WINDOW_S = 15.0
SET_PIECE_KINDS = (CORNER, FREE_KICK, PENALTY)

CPA, TOUCHE, JEU_PLACE, ERREUR, RECUPERATION, INCLASSABLE = (
    "coup de pied arrêté", "touche", "jeu placé", "erreur adverse", "récupération", "inclassable")
FAMILIES = (CPA, TOUCHE, JEU_PLACE, ERREUR, RECUPERATION, INCLASSABLE)


@dataclass(frozen=True)
class Origin:
    family: str  # une des `FAMILIES`
    detail: str  # corner, coup franc, coup franc (hors-jeu), penalty, touche, engagement, sortie de but, contrôle raté...
    event: TraceEvent | None  # événement qui donne le ballon (None : inclassable)
    delay_s: float | None  # temps entre cet événement et le but


def _gives_ball(e: TraceEvent, events: list[TraceEvent], team: str) -> tuple[str, str] | None:
    """(famille, détail) si `e` donne le ballon à `team`, sinon None."""
    if e.kind == REMISE and e.team == team:
        if e.detail in SET_PIECE_KINDS:
            return CPA, e.detail
        if e.detail == THROW_IN:
            return TOUCHE, THROW_IN
        return JEU_PLACE, e.detail or "remise"  # engagement, sortie de but
    if e.kind == HORS_JEU and e.team != team:
        return CPA, "coup franc (hors-jeu)"
    if e.kind == PERTE and e.team != team:
        if e.detail == "contrôle":
            return ERREUR, "contrôle raté"
        if e.detail == "conduite" and e.cause is not None and events[e.cause].kind == TOUCHE_LONGUE:
            return ERREUR, "touche trop longue"
        return RECUPERATION, {"passe interceptée": "interception"}.get(e.detail or "", e.detail or "perte")
    if e.kind in (ARRET, CONTRE) and e.team == team:  # tir adverse arrêté ou contré par l'équipe qui marquera
        return RECUPERATION, "arrêt" if e.kind == ARRET else "contre"
    return None


def _breaks(e: TraceEvent, team: str) -> bool:
    """Événement de l'adversaire en possession : la possession de `team` ne peut pas remonter au-delà."""
    if e.team is None or e.team == team:
        return False
    if e.kind in (ARRET, CONTRE, BUT):
        return False  # le ballon reste à disputer (rebond) ; un but adverse est précédé de son engagement
    if e.kind == FAUTE:
        return e.detail != "avantage"  # faute sifflée : la remise qui suit donne le ballon
    return e.kind != CONTROLE_RATE  # contrôle raté adverse : la perte qui suit le dira


def goal_origin(events: list[TraceEvent], goal: TraceEvent) -> Origin:
    """Origine du but `goal` (événement `but` du journal)."""
    steps = chain(events, goal.id)
    for e in reversed(steps[:-1]):
        found = _gives_ball(e, events, goal.team)
        if found is not None:
            family, detail = found
            delay = (goal.minute - e.minute) * 60.0
            if family in (CPA, TOUCHE) and delay > SET_PIECE_WINDOW_S and detail != PENALTY:
                return Origin(JEU_PLACE, f"après {detail}", e, delay)
            return Origin(family, detail, e, delay)
        if _breaks(e, goal.team):
            return Origin(INCLASSABLE, f"possession adverse ({e.kind}) sans événement qui rend le ballon", None, None)
    return Origin(INCLASSABLE, "chaîne sans début", None, None)


def goals(events: list[TraceEvent]) -> list[TraceEvent]:
    return [e for e in events if e.kind == BUT]


def format_chain(events: list[TraceEvent], goal: TraceEvent) -> str:
    """Chaîne d'un but, de son engagement au but, une ligne par événement, et son origine."""
    origin = goal_origin(events, goal)
    lines = []
    for e in chain(events, goal.id):
        mark = "  <- origine" if origin.event is not None and e.id == origin.event.id else ""
        extra = " ".join(x for x in (e.detail, f"-> {e.other}" if e.other else None) if x)
        lines.append(f"{e.minute:6.2f}'  #{e.id:<5} {e.kind:<14} {e.team or '-':<5} {e.player or '-'} {extra}{mark}")
    delay = "" if origin.delay_s is None else f", {origin.delay_s:.0f} s avant le but"
    lines.append(f"origine : {origin.family} ({origin.detail}{delay})")
    return "\n".join(lines)


def origin_shares(origins: list[Origin]) -> dict:
    """Part des buts par famille et par détail."""
    n = len(origins)
    families, details = Counter(o.family for o in origins), Counter(f"{o.family} : {o.detail}" for o in origins)
    return {"buts": n,
            "par famille": {f: families[f] / n if n else None for f in FAMILIES},
            "par détail": {k: v / n for k, v in sorted(details.items())},
            "inclassables": [o.detail for o in origins if o.family == INCLASSABLE]}


def play(i: int):
    """Match `i` du banc (`scripts/measure_v2.py` : même graine, même affiche), sans collecteur."""
    from ligue1sim.clubs import load_clubs
    from scripts.measure_v2 import AUDIT_SEED, CLUBS_PATH, TICK_S
    from v2engine import match

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + i)
    home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
    return match.simulate_match(home, away, duration_minutes=90.0, tick_seconds=TICK_S)


def _one(i: int) -> list[dict]:
    trace = play(i)
    out = []
    for g in goals(trace.events):
        o = goal_origin(trace.events, g)
        out.append({"match": i, "minute": g.minute, "équipe": g.team, "buteur": g.player, "famille": o.family,
                    "détail": o.detail, "délai (s)": o.delay_s})
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=20)
    parser.add_argument("--match", type=int, default=None)
    parser.add_argument("--but", type=int, default=0)
    parser.add_argument("--processus", type=int, default=1)
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)
    if args.match is not None:
        trace = play(args.match)
        print(format_chain(trace.events, goals(trace.events)[args.but]))
        return
    if args.processus > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.processus) as pool:
            rows = [r for match_rows in pool.map(_one, range(args.matches)) for r in match_rows]
    else:
        rows = [r for i in range(args.matches) for r in _one(i)]
    shares = origin_shares([Origin(r["famille"], r["détail"], None, r["délai (s)"]) for r in rows])
    print(json.dumps(shares, ensure_ascii=False, indent=1))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"buts": rows, "parts": shares}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
