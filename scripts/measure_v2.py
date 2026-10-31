"""Banc de mesure du moteur V2 (ticket v2-collectif/01) : simule N matchs entre clubs de Ligue 1, graines
fixes, et donne tous les indicateurs de `docs/INDICATEURS_V2.md` (classiques et tactiques), découpés par
zone du ballon, score et tranche de 15 minutes.

Usage : uv run python -m scripts.measure_v2 [nombre_de_matchs] [--profil "Work Rate"] [--detail] [--json chemin] [--pas 0.15]

`--profil <Attribut>` : test de profils. L'attribut est forcé à 99 pour une équipe et à 11 pour l'autre,
les rôles s'inversant d'un match à l'autre (neutralise l'avantage du terrain) ; le rapport compare les deux
niveaux. `--detail` : affiche les découpages. Lecture seule : le jeu n'est pas modifié (sauf l'attribut du
profil testé)."""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from collections.abc import Callable

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.cerveau as cerveau
import v2engine.match as match
from ligue1sim.lineup import pick_best_formation

from scripts.v2_indicators import Collector

AUDIT_SEED = 20260923
HIGH, LOW = 99, 11
TICK_S = match.TICK_SECONDS  # le pas du produit (ticket v2-collectif/25) : le banc mesure le match regardé


def _hook(collector: Collector, clock: dict[str, float]) -> Callable[[], None]:
    """Branche le collecteur sur les fonctions publiques du moteur ; retourne la fonction qui les restaure."""
    real = {name: getattr(match, name) for name in ("pass_velocity", "attempt_shot", "resolve_tackle", "choose_action")}

    def pass_velocity(passer, target, *args, **kwargs):
        collector.on_pass(passer, target)
        return real["pass_velocity"](passer, target, *args, **kwargs)

    def attempt_shot(shooter, *args, **kwargs):
        collector.on_shot(shooter, clock["now"] + clock["dt"])  # le tir a lieu pendant le tick en cours
        return real["attempt_shot"](shooter, *args, **kwargs)

    def resolve_tackle(*args, **kwargs):
        collector.on_tackle()
        return real["resolve_tackle"](*args, **kwargs)

    def choose_action(*args, **kwargs):
        action = real["choose_action"](*args, **kwargs)
        collector.on_choice(action.kind)
        return action

    real_stays = cerveau.stays_behind

    def stays_behind(player):
        stays = real_stays(player)
        collector.on_balance(player, stays)
        return stays

    match.pass_velocity, match.attempt_shot = pass_velocity, attempt_shot
    match.resolve_tackle, match.choose_action = resolve_tackle, choose_action
    cerveau.stays_behind = stays_behind
    return lambda: [setattr(match, name, fn) for name, fn in real.items()] + [setattr(cerveau, "stays_behind", real_stays)]


def _force_attribute(attribute: str, high_team: str, team_of: dict[str, str]) -> Callable[[], None]:
    """Force `attribute` à 99 pour `high_team` et à 11 pour l'autre, dans tous les modules du moteur. `team_of`
    (nom -> équipe) sert aux joueurs encore sans équipe : Pace, Acceleration et Stamina sont lus à la
    construction des joueurs, sur les fiches de la base."""
    patched = []
    for name, module in list(sys.modules.items()):
        if name.startswith("v2engine") and hasattr(module, "player_attribute"):
            real = module.player_attribute

            def forced(player, attr, _real=real):
                team = getattr(player, "team", None) or team_of.get(getattr(player, "name", None))
                if attr == attribute and team in ("home", "away"):
                    return HIGH if team == high_team else LOW
                return _real(player, attr)
            module.player_attribute = forced
            patched.append((module, real))
    return lambda: [setattr(m, "player_attribute", r) for m, r in patched]


def run(n_matches: int, profile: str | None = None, duration_minutes: float = 90.0, tick_s: float = TICK_S) -> Collector:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    collector = Collector()
    collector.minutes_per_match = duration_minutes
    clock = {"now": 0.0, "dt": tick_s}
    started = time.perf_counter()
    restore = _hook(collector, clock)
    try:
        for i in range(n_matches):
            # profils : chaque affiche est jouée deux fois, même graine, rôles haut/bas inversés
            k = i // 2 if profile else i
            random.seed(AUDIT_SEED + k)
            clock["now"] = 0.0
            home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
            high_team = "home" if i % 2 == 0 else "away"
            team_of = {p.name: "home" for p in pick_best_formation(home).players}
            team_of.update({p.name: "away" for p in pick_best_formation(away).players})
            unforce = _force_attribute(profile, high_team, team_of) if profile else (lambda: None)

            def observer(now_s, players, ball, scoring_team):
                clock["now"] = now_s
                if profile and not collector.levels:
                    collector.levels = {p.name: ("haut" if p.team == high_team else "bas") for p in players}
                collector.on_tick(now_s, players, ball, scoring_team, tick_s)
            try:
                trace = match.simulate_match(home, away, duration_minutes=duration_minutes, tick_seconds=tick_s,
                                             observer=observer)
                for event in trace.offsides:  # hors-jeu sifflés (ticket v2-collectif/23)
                    collector.on_offside(event)
            finally:
                unforce()
            collector.end_match()
    finally:
        restore()
    collector.seconds_per_match = (time.perf_counter() - started) / max(1, n_matches)
    return collector


def report(c: Collector, detail: bool = False) -> dict:
    n = max(1, c.matches)
    k = c.count
    passes = max(1, k["passes"])
    minutes = getattr(c, "minutes_per_match", 90.0) * n
    out: dict[str, object] = {
        "matchs": c.matches,
        "passes par minute": k["passes"] / minutes,
        "passes réussies (part)": k["passes réussies"] / passes,
        "passes chez l'adversaire (part)": k["passes chez l'adversaire"] / passes,
        "receveur visé (part)": k["receveur visé"] / passes,
        "passes longues (part)": k["passes longues"] / passes,
        "passes longues réussies (part)": k["passes longues réussies"] / max(1, k["passes longues"]),
        "passes en profondeur (part)": k["passes en profondeur"] / passes,
        "passes en profondeur réussies (part)": k["passes en profondeur réussies"] / max(1, k["passes en profondeur"]),
        "tirs par équipe": k["tirs"] / (2 * n),
        "tirs de près (16 m) par équipe": k["tirs de près"] / (2 * n),
        "part des tirs de près (16 m)": k["tirs de près"] / max(1, k["tirs"]),
        "buts par match": k["buts"] / n,
        "hors-jeu par match": k["hors-jeu"] / n,
        "hors-jeu par équipe": k["hors-jeu"] / (2 * n),
        "tacles par match": k["tacles"] / n,
        "pertes de balle par match": k["pertes de balle"] / n,
        "pertes en transition par match": None,
        "tirs de contre par match (récupération dans son camp)": k["tirs de contre, récupération propre camp"] / n,
        "tirs de contre par match (récupération dans le camp adverse)": k["tirs de contre, récupération camp adverse"] / n,
        "appels par match": k["appels"] / n,
        "pressings par match": k["pressings"] / n,
        "pressings suivis d'une récupération en 5 s (part)": k["pressings suivis d'une récupération en 5 s"] / max(1, k["pressings"]),
        "profil haut : temps de pressing par match (s)": k["profil haut : temps de pressing (s)"] / n,
        "profil bas : temps de pressing par match (s)": k["profil bas : temps de pressing (s)"] / n,
        "temps de calcul par match (s)": getattr(c, "seconds_per_match", None),
    }
    choices = sum(v for key, v in k.items() if key.startswith("choix "))
    for key, v in sorted(k.items()):
        if key.startswith("choix "):
            out[f"{key} (part)"] = v / max(1, choices)
    in_situation = sum(v for key, v in k.items() if key.startswith("temps en "))
    for key, v in sorted(k.items()):
        if key.startswith("temps en "):
            out[f"part du {key} (deux équipes)"] = v / max(1e-9, in_situation)
    recoveries = max(1, k["récupérations"])
    for key, v in sorted(k.items()):
        if key.startswith("récupération "):
            out[f"{key} (part)"] = v / recoveries
    relost = c.stats.get("pertes en transition (part des récupérations)")
    out["pertes en transition par match"] = sum(relost.values) / n if relost else 0.0
    out["km par joueur de champ, par poste"] = {p: round(statistics.fmean(v), 2) for p, v in sorted(c.km.items())}
    for name, stat in sorted(c.stats.items()):
        out[name] = statistics.fmean(stat.values) if stat.values else None
        if detail and stat.by:
            out[name + " — découpage"] = {f"{a}={b}": round(statistics.fmean(v), 2) for (a, b), v in sorted(stat.by.items())}
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=20, help="avec --profil : nombre pair (affiche jouée deux fois)")
    parser.add_argument("--profil", default=None)
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--json", default=None)
    parser.add_argument("--pas", type=float, default=TICK_S, help="pas de calcul (s), par défaut celui du produit")
    args = parser.parse_args(argv)
    result = report(run(args.matches, args.profil, tick_s=args.pas), args.detail)
    for key, value in result.items():
        if isinstance(value, dict):
            print(f"{key} :")
            for sub, v in value.items():
                print(f"    {sub} : {v}")
        else:
            print(f"{key} : {round(value, 3) if isinstance(value, float) else value}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
