"""Diagnostic du volume de tacles du moteur V2 (ticket v2-realisme/11r) : où se perd le volume, sur le moteur courant,
sans le modifier. Lecture seule : les fonctions publiques du moteur sont enveloppées le temps de la série (aucun
tirage aléatoire consommé), les graines sont celles du banc (`scripts/measure_v2.run`, indice `i` -> `AUDIT_SEED + i`).

Mesures, par match :
- exposition : temps où au moins un adversaire est à portée de tacle (`match.TACKLE_RADIUS_M`) du porteur, découpé par
  nombre de défenseurs à portée ; temps-défenseur à portée par statut (tirage, à portée mais non retenu par le 11p,
  déjà engagé, relève après un tacle raté, déséquilibré du 12c, hors jeu) ;
- tirages : pas où le défenseur retenu tire sa tentative ; taux effectif par seconde d'exposition, par contexte
  (urgence, surface, angle d'approche hors urgence) ; tacles attendus au taux de base (sans le facteur 11h) et avec ;
- confrontations : épisodes (défenseur, porteur) à portée sans interruption, durée et issue (tacle tenté, porteur
  qui joue ou perd le ballon, séparation au-delà de la portée, arrêt de jeu).

Usage : uv run python -m scripts.diagnostic_tacles 50 --processus 3 [--json chemin]
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match
from v2engine.duel import attempt_tackle_probability, tackle_approach_angle_deg

from scripts.graines_validation import check_series
from scripts.v2_indicators import APPROACH_BANDS, approach_band

AUDIT_SEED = 20260923
DURATION_BANDS = ((0.3, "moins de 0,3 s"), (1.0, "0,3 à 1 s"), (3.0, "1 à 3 s"), (math.inf, "3 s et plus"))
STATUSES = ("tirage", "à portée, non retenu (11p)", "déjà engagé", "relève après tacle raté", "déséquilibré (12c)",
            "hors jeu")
CONTEXTS = ("en urgence", "dans sa surface") + tuple(f"hors urgence, {band}" for band in APPROACH_BANDS)
EXITS = ("tacle tenté", "porteur joue ou perd le ballon", "séparation", "arrêt de jeu")


def duration_band(seconds: float) -> str:
    return next(label for limit, label in DURATION_BANDS if seconds < limit)


class TackleDiagnostic:
    """Compteurs d'un ou plusieurs matchs. `on_context` et `on_draw` sont branchés sur le moteur (`hooked`),
    `on_tick` sur l'observateur de `simulate_match` ; `end_match` clôt les confrontations ouvertes."""

    def __init__(self) -> None:
        self.count: Counter[str] = Counter()
        self.durations: list[float] = []
        self.matches = 0
        self.now = 0.0
        self.ctx: tuple | None = None
        self.open: dict[tuple[str, str], float] = {}  # (défenseur, porteur) -> début de la confrontation (s)
        self.tackled: set[tuple[str, str]] = set()  # confrontations closes par un tacle tenté pendant ce pas
        self.spent: set[tuple[str, str]] = set()  # confrontations closes par un tacle, défenseur encore à portée

    # --- moteur ---
    def on_context(self, tackler, holder, urgent: bool, in_own_box: bool, factor: float) -> None:
        if in_own_box:
            context = "dans sa surface"
        elif urgent:
            context = "en urgence"
        else:
            context = f"hors urgence, {approach_band(tackle_approach_angle_deg(tackler, holder))}"
        self.ctx = (tackler.name, holder.name, context, factor)

    def on_draw(self, aggression: float, dt: float, attempted: bool) -> None:
        """Tirage de la tentative (`dt` déjà multiplié par le facteur 11h) : contexte noté par `on_context`."""
        if self.ctx is None:
            return
        tackler, holder, context, factor = self.ctx
        self.ctx = None
        rate = attempt_tackle_probability(aggression)
        base_dt = dt / factor if factor > 0.0 else dt
        k = self.count
        k[f"tirages, {context} (s)"] += base_dt
        k[f"tirages, {context} : facteur x s"] += factor * base_dt
        k[f"tirages, {context} : taux de base x s"] += rate * base_dt
        k[f"tirages, {context} : tacles attendus au taux de base"] += 1.0 - math.exp(-rate * base_dt)
        k[f"tirages, {context} : tacles attendus"] += 1.0 - math.exp(-rate * dt)
        k[f"tirages, {context} : tacles tentés"] += attempted
        if attempted:
            self.tackled.add((tackler, holder))

    # --- observateur ---
    def on_tick(self, now_s: float, players, ball, dt: float) -> None:
        self.now = now_s
        k = self.count
        holder = next((p for p in players if p.name == ball.holder), None) if ball.holder is not None else None
        live = holder is not None and ball.restart is None
        current: set[tuple[str, str]] = set()
        if live:
            k["ballon tenu (s)"] += dt
            in_range = [p for p in players if p.team != holder.team
                        and holder.position.distance_to(p.position) < match.TACKLE_RADIUS_M]
            near = [p for p in players if p.team != holder.team
                    and holder.position.distance_to(p.position) < match.CONFRONTATION_END_M]
            k["pression à moins de 3 m (s)"] += dt * bool(near)
            if in_range:
                k["exposition (s)"] += dt
                k[f"exposition, {min(len(in_range), 3)}{'+' if len(in_range) >= 3 else ''} à portée (s)"] += dt
            for p in in_range:
                k[f"temps-défenseur à portée, {self._status(p, ball, now_s)} (s)"] += dt
                current.add((p.name, holder.name))
        for pair, start in list(self.open.items()):
            if pair in current and pair not in self.tackled:
                continue
            if pair in self.tackled:
                reason = "tacle tenté"
            elif not live:
                reason = "arrêt de jeu" if ball.restart is not None else "porteur joue ou perd le ballon"
            elif pair[1] != holder.name:
                reason = "porteur joue ou perd le ballon"
            else:
                reason = "séparation"
            self._close(pair, start, reason)
        # après un tacle, la confrontation est close tant que le défenseur reste à portée du même porteur
        self.spent = (self.spent | self.tackled) & current
        for pair in current - self.open.keys() - self.spent:
            self.open[pair] = now_s
        self.tackled.clear()

    def _status(self, p, ball, now_s: float) -> str:
        if ball.offside_out_until.get(p.name, 0.0) > now_s:
            return "hors jeu"
        if ball.unsettled_until_s.get(p.name, 0.0) > now_s:
            return "déséquilibré (12c)"
        if ball.tackle_ban_until_s.get(p.name, 0.0) > now_s:
            return "relève après tacle raté"
        if p.name in ball.engaged:
            return "déjà engagé"
        return "tirage" if self.last_drawn == p.name else "à portée, non retenu (11p)"

    last_drawn: str | None = None

    def _close(self, pair, start: float, reason: str) -> None:
        del self.open[pair]
        duration = self.now - start
        self.durations.append(duration)
        self.count[f"confrontations, issue : {reason}"] += 1
        self.count[f"confrontations, durée {duration_band(duration)}"] += 1
        self.count["confrontations"] += 1

    def end_match(self) -> None:
        for pair, start in list(self.open.items()):
            self._close(pair, start, "arrêt de jeu")
        self.tackled.clear()
        self.spent.clear()
        self.ctx = None
        self.matches += 1


def hooked(diag: TackleDiagnostic):
    """Enveloppe `tackle_attempt_factor` et `should_attempt_tackle` du moteur ; retourne la restauration."""
    real_factor, real_draw = match.tackle_attempt_factor, match.should_attempt_tackle

    def tackle_attempt_factor(tackler, holder, urgent, in_own_box=False):
        factor = real_factor(tackler, holder, urgent, in_own_box)
        diag.on_context(tackler, holder, urgent, in_own_box, factor)
        diag.last_drawn = tackler.name
        return factor

    def should_attempt_tackle(aggression, dt):
        attempted = real_draw(aggression, dt)
        diag.on_draw(aggression, dt, attempted)
        return attempted

    match.tackle_attempt_factor, match.should_attempt_tackle = tackle_attempt_factor, should_attempt_tackle

    def restore() -> None:
        match.tackle_attempt_factor, match.should_attempt_tackle = real_factor, real_draw
    return restore


def run(n_matches: int, start: int = 0, duration_minutes: float = 90.0) -> TackleDiagnostic:
    """Joue les matchs `start` à `start + n_matches - 1` avec les graines et affiches du banc."""
    check_series(start, n_matches)
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    diag = TackleDiagnostic()
    tick = match.TICK_SECONDS
    restore = hooked(diag)
    try:
        for i in range(start, start + n_matches):
            random.seed(AUDIT_SEED + i)
            home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]

            def observer(now_s, players, ball, scoring_team):
                diag.on_tick(now_s, players, ball, tick)
                diag.last_drawn = None
            match.simulate_match(home, away, duration_minutes=duration_minutes, tick_seconds=tick, observer=observer)
            diag.end_match()
    finally:
        restore()
    return diag


def report(diag: TackleDiagnostic) -> dict[str, float]:
    n = max(1, diag.matches)
    k = diag.count
    out: dict[str, float] = {"matchs": diag.matches}
    tackles = sum(k[f"tirages, {c} : tacles tentés"] for c in CONTEXTS)
    out["tacles tentés par match"] = tackles / n
    out["tacles attendus au taux de base (sans 11h), par match"] = sum(
        k[f"tirages, {c} : tacles attendus au taux de base"] for c in CONTEXTS) / n
    out["ballon tenu par match (s)"] = k["ballon tenu (s)"] / n
    out["pression à moins de 3 m par match (s)"] = k["pression à moins de 3 m (s)"] / n
    out["exposition par match (s)"] = k["exposition (s)"] / n
    out["exposition (part du ballon tenu)"] = k["exposition (s)"] / max(1e-9, k["ballon tenu (s)"])
    for label in ("1", "2", "3+"):
        out[f"exposition, {label} à portée (part)"] = k[f"exposition, {label} à portée (s)"] / max(1e-9, k["exposition (s)"])
    out["exposition multiple (part)"] = 1.0 - out["exposition, 1 à portée (part)"]
    defender_time = sum(k[f"temps-défenseur à portée, {s} (s)"] for s in STATUSES)
    for s in STATUSES:
        out[f"temps-défenseur à portée, {s}, par match (s)"] = k[f"temps-défenseur à portée, {s} (s)"] / n
        out[f"temps-défenseur à portée, {s} (part)"] = k[f"temps-défenseur à portée, {s} (s)"] / max(1e-9, defender_time)
    draw_s = sum(k[f"tirages, {c} (s)"] for c in CONTEXTS)
    out["tirages par match (s)"] = draw_s / n
    out["taux effectif par seconde d'exposition"] = tackles / max(1e-9, k["exposition (s)"])
    out["taux effectif par seconde de tirage"] = tackles / max(1e-9, draw_s)
    out["taux de base moyen des tireurs (par s)"] = sum(
        k[f"tirages, {c} : taux de base x s"] for c in CONTEXTS) / max(1e-9, draw_s)
    out["facteur 11h moyen (pondéré par le temps de tirage)"] = sum(
        k[f"tirages, {c} : facteur x s"] for c in CONTEXTS) / max(1e-9, draw_s)
    for c in CONTEXTS:
        s = k[f"tirages, {c} (s)"]
        out[f"tirages, {c} (part du temps de tirage)"] = s / max(1e-9, draw_s)
        out[f"tirages, {c} : facteur 11h moyen"] = k[f"tirages, {c} : facteur x s"] / max(1e-9, s)
        out[f"tirages, {c} : tacles tentés par match"] = k[f"tirages, {c} : tacles tentés"] / n
        out[f"tirages, {c} : tacles attendus au taux de base, par match"] = (
            k[f"tirages, {c} : tacles attendus au taux de base"] / n)
    confrontations = max(1, k["confrontations"])
    out["confrontations par match"] = k["confrontations"] / n
    out["confrontations : durée moyenne (s)"] = statistics.fmean(diag.durations) if diag.durations else 0.0
    out["confrontations : durée médiane (s)"] = statistics.median(diag.durations) if diag.durations else 0.0
    for _, label in DURATION_BANDS:
        out[f"confrontations, durée {label} (part)"] = k[f"confrontations, durée {label}"] / confrontations
    for reason in EXITS:
        out[f"confrontations, issue : {reason} (part)"] = k[f"confrontations, issue : {reason}"] / confrontations
    return out


def _one(args: tuple[int, float]) -> dict:
    i, duration = args
    diag = run(1, i, duration)
    return {"count": dict(diag.count), "durations": diag.durations}


def run_series(n_matches: int, processes: int = 1, start: int = 0, duration: float = 90.0) -> TackleDiagnostic:
    """Série répartie sur plusieurs processus, fusionnée dans l'ordre des matchs (résultat indépendant du découpage)."""
    jobs = [(i, duration) for i in range(start, start + n_matches)]
    merged = TackleDiagnostic()
    pool = ProcessPoolExecutor(max_workers=processes) if processes > 1 else None
    try:
        for r in (pool.map(_one, jobs) if pool else map(_one, jobs)):
            merged.count.update(r["count"])
            merged.durations.extend(r["durations"])
            merged.matches += 1
    finally:
        if pool:
            pool.shutdown()
    return merged


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=50)
    parser.add_argument("--processus", type=int, default=1)
    parser.add_argument("--debut", type=int, default=0)
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    result = report(run_series(args.matches, args.processus, args.debut))
    for key, value in result.items():
        print(f"{key} : {round(value, 4) if isinstance(value, float) else value}")
    print(f"durée machine : {(time.perf_counter() - started) / 60:.1f} min")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
