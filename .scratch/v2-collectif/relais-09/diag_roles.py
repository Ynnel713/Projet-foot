"""Diagnostic hors dépôt, réserve A2 du ticket 07 reprise au ticket 09 : part du temps de possession adverse (passes en
vol comprises) où l'équipe qui défend a au moins un rôle attribué, et distance médiane marqueur-attaquant, par niveau
de Marking (--profil : Marking forcé à 99 pour une équipe, 11 pour l'autre, rôles inversés d'un match à l'autre).

Usage (depuis la copie du moteur) : uv run --project <dépôt> python diag_roles.py [n_matchs] [--profil]"""

from __future__ import annotations

import random
import statistics
import sys

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

import v2engine.defense as defense
import v2engine.match as match
from v2engine.defense import MARQUAGE

AUDIT_SEED = 20260923


def run(n: int, profile: bool) -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    captured = {}
    real_update = defense.DefensiveRoles.update

    def update(self, *a, **k):
        captured["roles"] = self
        return real_update(self, *a, **k)
    defense.DefensiveRoles.update = update
    real_attr = defense.player_attribute
    forced = {}

    def player_attribute(player, name):
        if name == "Marking" and player.name in forced:
            return forced[player.name]
        return real_attr(player, name)
    defense.player_attribute = player_attribute

    ticks = covered = readers_only = mdc_ticks = mdc_comp = 0
    dist = {"haut": [], "bas": [], "tous": []}
    for i in range(n):
        k = i // 2 if profile else i
        random.seed(AUDIT_SEED + k)
        home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
        high = "home" if i % 2 == 0 else "away"
        forced.clear()
        if profile:
            for team, club in (("home", home), ("away", away)):
                for p in pick_best_formation(club).players:
                    forced[p.name] = 99 if team == high else 11
        level = {}
        last_team = [None]

        def observer(now_s, players, ball, scored):
            nonlocal ticks, covered, readers_only, mdc_ticks, mdc_comp
            holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
            receiver = next((p for p in players if p.name == ball.receiver), None) if ball.receiver else None
            owner = holder or receiver
            if owner is None:
                return
            ticks += 1
            roles = captured.get("roles")
            if roles is None:
                return
            team = "away" if owner.team == "home" else "home"
            mine = {p.name for p in players if p.team == team}
            if any(name in mine for name in roles.assignments):
                covered += 1
            elif any(name in mine for name in ball.readers):
                readers_only += 1
            for p in players:
                if p.team == team and p.poste == "MDC":
                    mdc_ticks += 1
                    a = roles.assignments.get(p.name)
                    mdc_comp += a is not None and a.role == "compensation"
            by_name = {p.name: p for p in players}
            for name, a in roles.assignments.items():
                if a.role == MARQUAGE and name in mine and a.mate in by_name:
                    d = by_name[name].position.distance_to(by_name[a.mate].position)
                    dist["tous"].append(d)
                    if profile:
                        dist["haut" if team == high else "bas"].append(d)

        match.simulate_match(home, away, observer=observer)
        print(f"match {i + 1}/{n}", file=sys.stderr)
    print(f"{n} matchs ; rôle attribué pendant la possession adverse (passes en vol comprises) : {covered / ticks:.1%}")
    print(f"sans rôle mais avec un lecteur de passe : {readers_only / ticks:.1%}")
    if mdc_ticks:
        print(f"milieu défensif en compensation : {mdc_comp / mdc_ticks:.1%} du temps de possession adverse")
    for key, values in dist.items():
        if values:
            print(f"distance marqueur-attaquant, {key} : médiane {statistics.median(values):.2f} m ({len(values)} ticks)")


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4, "--profil" in sys.argv)
