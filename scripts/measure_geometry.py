"""Mesure de la géométrie des clips rendus (chantier 1, `docs/known_issues.md` tickets 46 et 47 ; chantier "mouvement collectif",
Phases 1 à 3) -- harnais versionné.

`run` simule N matchs de l'audit (`narrative_audit.py`, graine 20260923), construit les clips avec `build_clips` et enregistre, par clip :
l'empreinte des images, et pour chaque acteur scripté la vitesse (rapportée à la vitesse max de son poste), l'accélération et le saut en
une image, AVANT et APRÈS la contrainte d'accélération, plus l'écart entre sa position rendue et sa position scriptée au dernier
keyframe. Chaque passe (changement de porteur entre deux keyframes) donne sa durée, sa corde 3D et son chemin 3D (somme des images).
Chaque joueur de décor (hors gardien) donne l'amplitude (m) de l'écart latéral de départ qui lui est appliqué (`dispersion_m`,
chantier "mouvement collectif", Phase 1). `compare` rapproche deux mesures clip à clip (images identiques, clips en
dépassement, passes > 30 m/s, dispersion moyenne...).

Rien n'est modifié dans le code du produit : les fonctions de `narrative_player` et de `templates` sont enveloppées en mémoire, le
temps du script. Compos de l'audit : synthétiques (4-2-3-1, notes égales, sans entraîneur) -- biais connu, voir le ticket 46.

Usage :
    uv run python scripts/measure_geometry.py run [--n 100] [--root DOSSIER] --out mesure.json
    uv run python scripts/measure_geometry.py compare a.json b.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

_DEFAULT_N = 100
_OVERSHOOT = 1.05  # x vmax du poste
_ACCEL_MAX = 10.0  # m/s²
_ACCEL_TOLERANCE = 1e-3  # la contrainte plafonne à 10 m/s² à l'arrondi flottant près
_JUMP_MAX_M = 1.0  # en une image
_PASS_MAX_M_S = 30.0


def _setup(root: Path):
    for sub in ("scripts", "engine", "src"):
        sys.path.insert(0, str(root / sub))
    logging.disable(logging.CRITICAL)


def _kinematics(track: list[tuple[float, float]], dt: float, v_max: float) -> dict:
    speeds = [math.hypot(b[0] - a[0], b[1] - a[1]) / dt for a, b in zip(track, track[1:])]
    vels = [((b[0] - a[0]) / dt, (b[1] - a[1]) / dt) for a, b in zip(track, track[1:])]
    accels = [math.hypot(b[0] - a[0], b[1] - a[1]) / dt for a, b in zip(vels, vels[1:])]
    return {"ratio": max(speeds, default=0.0) / v_max, "accel": max(accels, default=0.0), "jump": max(speeds, default=0.0) * dt}


def run(n: int, root: Path) -> dict:
    _setup(root)
    import numpy as np

    import narrative_audit as audit
    import narrative_player as np_
    import ligue1sim.animation.templates as templates
    from ligue1sim.animation.motion import MAX_SPEED_MPS
    from ligue1sim.clubs import Club
    from ligue1sim.lineup import pick_best_formation
    from ligue1sim.pitch_geometry import PITCH_LENGTH_M as L, PITCH_WIDTH_M as W

    try:  # chantier "mouvement collectif", Phase 1 (16/10/2026) : absent avant cette phase, mesure dégradée proprement (liste vide)
        from ligue1sim.animation.sequence_generator import _start_dispersion
    except ImportError:
        _start_dispersion = None
    try:  # chantier "mouvement collectif", Phase 3 (16/10/2026) : absent avant cette phase, mesure dégradée proprement (liste vide)
        from ligue1sim.animation.sequence_generator import (
            _SUPPORT_INITIATIVE_MAX_M,
            _SUPPORT_LANE_M,
            _support_initiative,
            _support_initiative_eligible,
            _support_initiative_probability,
            _support_initiative_selected,
        )
    except ImportError:
        _support_initiative = None
    from ligue1sim.schedule import Match
    from ligue1sim.simulation import LeagueContext, simulate_match
    from narrative import build_timeline, match_result_from

    last: dict = {}
    rows: list[dict] = []
    build, accel = templates.build_from_template, np_._apply_acceleration_constraint_to_frames
    clip_of = np_._build_clip

    def spy_build(*args, **kwargs):
        last["seq"] = build(*args, **kwargs)
        return last["seq"]

    def spy_accel(frames, dt):
        last["pre"] = frames
        return accel(frames, dt)

    def spy_clip(timeline, event):
        frames, roster, ball_events = clip_of(timeline, event)
        if not frames:
            return frames, roster, ball_events
        seq, pre, dt = last["seq"], last["pre"], 1.0 / np_._FPS
        track = lambda fs, pid: [(f.players[pid].x * L, f.players[pid].y * W) for f in fs]  # noqa: E731
        actors = {}
        for pid, entry in roster.items():
            if entry.role is None or entry.team_side != "scorer":
                continue
            v_max, rendered = MAX_SPEED_MPS.get(entry.poste, 8.0), track(frames, pid)
            kfs = [k for k in seq.keyframes if pid in k.players]
            arrival = math.hypot(rendered[min(len(rendered) - 1, round(kfs[-1].t * np_._FPS))][0] - kfs[-1].players[pid][0] * L,
                                 rendered[min(len(rendered) - 1, round(kfs[-1].t * np_._FPS))][1] - kfs[-1].players[pid][1] * W)
            segments = [math.hypot((b.players[pid][0] - a.players[pid][0]) * L, (b.players[pid][1] - a.players[pid][1]) * W) / (b.t - a.t) / v_max
                        for a, b in zip(kfs, kfs[1:]) if b.t > a.t]
            actors[entry.role] = {"poste": entry.poste, "segment_ratio": max(segments, default=0.0), "arrival_gap_m": arrival,
                                  "post": _kinematics(rendered, dt, v_max), "pre": _kinematics(track(pre, pid), dt, v_max)}
        # Chantier "mouvement collectif", Phase 1 (16/10/2026) : amplitude (m) de l'écart latéral appliqué par
        # `sequence_generator._start_dispersion` à chaque joueur de décor (hors gardien, hors mur de coup franc, hors
        # remplaçant en_jeu -- déjà exclus par `_start_dispersion`/ses appelants). Mesure DIRECTE de ce que la Phase 1 ajoute,
        # pas une mesure indirecte sur les positions rendues : la largeur d'une ligne tactique (ex. latéral à latéral) est
        # volontaire et bien plus grande que l'amplitude de dispersion, toute mesure sur les positions absolues la noierait.
        # Absente avant la Phase 1 (`_start_dispersion` n'existe pas encore) : liste vide, mesure dégradée proprement. Gardien
        # exclu (jamais dispersé, voir ses appelants dans `sequence_generator.py`) ; mur de coup franc et remplaçant en_jeu
        # non filtrés ici (rares, mesure diagnostique -- pas une garantie chiffrée exacte sur ces deux cas limites).
        dispersion_m = (
            [abs(_start_dispersion(pid, seq.event_ref)[1]) * W for pid, entry in roster.items() if entry.role is None and entry.poste != "GK"]
            if _start_dispersion is not None else []
        )
        # Chantier "mouvement collectif", Phase 2 (16/10/2026) : saut de position (m) d'une image à l'autre pour chaque
        # joueur de décor, RENDU (après `interpolate`, trajectoire à plusieurs points le cas échéant) -- même définition
        # que `_JUMP_MAX_M` déjà utilisée pour les acteurs scriptés. Critère d'acceptation de la Phase 2 : "aucun segment
        # ne présente plus de saut... qu'aujourd'hui", donc mesuré pour TOUS les gabarits (aucune garde try/except : cette
        # mesure ne dépend d'aucune fonction absente avant Phase 2, seulement de `frames` déjà disponible).
        decor_jump_m = []
        for pid, entry in roster.items():
            if entry.role is not None:
                continue
            decor_track = track(frames, pid)
            decor_jump_m.append(max((math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(decor_track, decor_track[1:])), default=0.0))
        # Chantier "mouvement collectif", Phase 3 (16/10/2026) : mesure DIRECTE (même principe que `dispersion_m`) de la
        # fréquence/amplitude des initiatives de soutien par poste, et compteur de violations de secteur (doit rester à 0
        # par construction -- `_support_initiative` clampe toujours au couloir/plafond, mais le critère d'acceptation
        # exige une mesure chiffrée, pas seulement "garanti par le code"). `players_by_name` : effectif COMPLET des deux
        # équipes (titulaires + remplaçants), pour résoudre l'attribut pertinent (Work Rate/Positioning) d'un MC/MDC --
        # suffisant pour une mesure diagnostique, pas la vue filtrée par minute que `_build_clip` utilise en production.
        support_rows: list[dict] = []
        if _support_initiative is not None:
            scorer_lineup_full = timeline.home_lineup if event.team == timeline.home_team else timeline.away_lineup
            opponent_lineup_full = timeline.away_lineup if event.team == timeline.home_team else timeline.home_lineup
            players_by_name = {
                p.name: p for lu in (scorer_lineup_full, opponent_lineup_full) for p in list(lu.players) + list(lu.substitutes)
            }
            for pid, entry in roster.items():
                if entry.role is not None or not _support_initiative_eligible(entry.poste, entry.team_side):
                    continue
                probability = _support_initiative_probability(entry.poste, entry.team_side, players_by_name.get(entry.nom))
                selected = _support_initiative_selected(pid, seq.event_ref, probability)
                row = {"poste": entry.poste, "team_side": entry.team_side, "selected": selected}
                if selected:
                    dx, dy = _support_initiative(entry.poste, pid, entry.team_side, seq.event_ref)
                    row["amplitude_m"] = math.hypot(dx * L, dy * W)
                    row["lateral_m"] = abs(dy) * W
                    row["sector_violation"] = (
                        row["amplitude_m"] > _SUPPORT_INITIATIVE_MAX_M + 1e-6 or row["lateral_m"] > _SUPPORT_LANE_M[entry.poste] + 1e-6
                    )
                support_rows.append(row)
        passes = []
        for a, b in zip(seq.keyframes, seq.keyframes[1:]):
            if a.ball.owner_id is None or b.ball.owner_id is None or a.ball.owner_id == b.ball.owner_id or b.t <= a.t:
                continue
            ball = [(f.ball.x * L, f.ball.y * W, f.ball.z) for f in frames if f.ball is not None and a.t - 1e-9 <= f.t <= b.t + 1e-9]
            passes.append({"dt": b.t - a.t,
                           "chord": math.dist((a.ball.x * L, a.ball.y * W, a.ball.z), (b.ball.x * L, b.ball.y * W, b.ball.z)),
                           "path": sum(math.dist(p, q) for p, q in zip(ball, ball[1:]))})
        digest = hashlib.sha1(repr([(round(f.t, 6), sorted((k, round(s.x, 6), round(s.y, 6)) for k, s in f.players.items())) for f in frames]).encode())
        rows.append({"key": [event.minute, event.main_player, event.team, len(rows)], "gabarit": event.gabarit, "duration": seq.duration,
                     "frames": digest.hexdigest()[:16], "actors": actors, "passes": passes, "dispersion_m": dispersion_m,
                     "decor_jump_m": decor_jump_m, "support_rows": support_rows})
        return frames, roster, ball_events

    templates.build_from_template, np_._apply_acceleration_constraint_to_frames, np_._build_clip = spy_build, spy_accel, spy_clip
    random.seed(audit._AUDIT_SEED)
    np.random.seed(audit._AUDIT_SEED)
    home, away = Club(name="Home FC", players=audit._squad("home", 72.0)), Club(name="Away FC", players=audit._squad("away", 68.0))
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    engine, done, i = hashlib.sha256(), 0, 0
    while done < n:
        home_goals, away_goals, events = simulate_match(home, away, context)
        i += 1
        if events is None:
            continue
        done += 1
        engine.update(repr((home_goals, away_goals, events)).encode())
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        np_.build_clips(build_timeline(match_result_from(match, events, home_lineup, away_lineup, date=str(i))))
    return {"matches": n, "engine": engine.hexdigest()[:16], "rows": rows}


def _over(rows: list[dict], when: str, key: str, limit: float) -> int:
    """Clips où un acteur scripté dépasse `limit` (`when` : "post" = rendu, "pre" = avant contrainte ; `key` : ratio, accel, jump)."""
    return sum(any(a[when][key] > limit for a in r["actors"].values()) for r in rows)


def _summary(rows: list[dict]) -> str:
    passes = [p for r in rows for p in r["passes"]]
    gaps = [r["actors"]["scorer"]["arrival_gap_m"] for r in rows if "scorer" in r["actors"]]
    segs = [a["segment_ratio"] for r in rows for a in r["actors"].values()]
    dispersions = [d for r in rows for d in r.get("dispersion_m", [])]  # .get : compatible avec une mesure antérieure à la Phase 1
    decor_jumps = [j for r in rows for j in r.get("decor_jump_m", [])]  # .get : compatible avec une mesure antérieure à la Phase 2
    over = lambda key, limit: f"rendu {_over(rows, 'post', key, limit)}, brut {_over(rows, 'pre', key, limit)}"  # noqa: E731
    dispersion_str = f" | dispersion de départ : moyenne {statistics.mean(dispersions):.2f} m (n={len(dispersions)})" if dispersions else ""
    decor_jump_str = (
        f" | saut décor > {_JUMP_MAX_M:.0f} m : {sum(j > _JUMP_MAX_M for j in decor_jumps)} (n={len(decor_jumps)})" if decor_jumps else ""
    )
    support = [s for r in rows for s in r.get("support_rows", [])]  # .get : compatible avec une mesure antérieure à la Phase 3
    support_str = ""
    if support:
        by_poste: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        amplitudes, violations = [], 0
        for s in support:
            by_poste[s["poste"]][1] += 1
            if s["selected"]:
                by_poste[s["poste"]][0] += 1
                amplitudes.append(s["amplitude_m"])
                violations += s["sector_violation"]
        freq = ", ".join(f"{poste} {sel}/{tot} ({sel / tot:.0%})" for poste, (sel, tot) in sorted(by_poste.items()))
        amplitude_str = f"moyenne {statistics.mean(amplitudes):.2f} m (n={len(amplitudes)})" if amplitudes else "n=0"
        support_str = f" | initiatives de soutien : {freq} | amplitude {amplitude_str} | violations de secteur : {violations}"
    return (f"{len(rows)} clips | acteurs > 0,55 (keyframes) {sum(s > 0.5501 for s in segs)} | > {_OVERSHOOT} x vmax : {over('ratio', _OVERSHOOT)} "
            f"| > {_ACCEL_MAX:.0f} m/s2 : {over('accel', _ACCEL_MAX + _ACCEL_TOLERANCE)} | saut > {_JUMP_MAX_M:.0f} m : {over('jump', _JUMP_MAX_M)} | passes > {_PASS_MAX_M_S:.0f} m/s "
            f"(chemin / corde) {sum(p['path'] / p['dt'] > _PASS_MAX_M_S for p in passes)} / {sum(p['chord'] / p['dt'] > _PASS_MAX_M_S for p in passes)} sur {len(passes)} "
            f"| arrivée du scorer : médiane {statistics.median(gaps):.2f} m{dispersion_str}{decor_jump_str}{support_str}")


def compare(a: dict, b: dict) -> str:
    lines = [f"moteur identique : {a['engine'] == b['engine']} ({a['engine']} / {b['engine']})", f"A : {_summary(a['rows'])}", f"B : {_summary(b['rows'])}"]
    by_a = {tuple(r["key"]): r for r in a["rows"]}
    by_b = {tuple(r["key"]): r for r in b["rows"]}
    common = by_a.keys() & by_b.keys()
    same = defaultdict(lambda: [0, 0])
    for key in common:
        same[by_a[key]["gabarit"]][0] += by_a[key]["frames"] == by_b[key]["frames"]
        same[by_a[key]["gabarit"]][1] += 1
    lines.append(f"clips communs {len(common)} / {len(by_a)} / {len(by_b)} ; images identiques : " + ", ".join(f"{g} {s}/{t}" for g, (s, t) in sorted(same.items())))
    lines.append(f"TOTAL images identiques : {sum(s for s, _ in same.values())}/{sum(t for _, t in same.values())}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--n", type=int, default=_DEFAULT_N)
    p_run.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="racine du code à mesurer (défaut : ce dépôt)")
    p_run.add_argument("--out", type=Path, required=True)
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("a", type=Path)
    p_cmp.add_argument("b", type=Path)
    args = parser.parse_args()
    if args.cmd == "run":
        result = run(args.n, args.root.resolve())
        args.out.write_text(json.dumps(result), encoding="utf-8")
        print(f"{len(result['rows'])} clips, moteur {result['engine']}\n{_summary(result['rows'])}")
    else:
        print(compare(json.loads(args.a.read_text(encoding="utf-8")), json.loads(args.b.read_text(encoding="utf-8"))))


if __name__ == "__main__":
    main()
