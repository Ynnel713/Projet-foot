"""Série appariée du ticket v2-realisme/10f (lecture seule) : mêmes matchs du banc (graines et affiches de
`scripts/measure_v2.py`), zones de la surface désactivées (avant : `BOX_ZONES` vide, moteur d'avant le ticket) ou
actives (après). Par match : tirs, buts et passes / pertes comme `18m-serie.py` ; aux instants où une équipe tient le
ballon dans un couloir extérieur du dernier tiers adverse (35 m, hors largeur de surface) : nombre d'instants,
défenseurs de champ adverses dans la surface, zones tenues (défenseur à 3 m ou moins du point de la zone ; poteaux
comptés seulement ballon à 20 m ou moins, comme la règle), profondeur de l'avant-dernier défenseur (ligne de hors-jeu,
gardien compris) ; tirs et buts dans les 10 s qui suivent un tel passage ; hors-jeu sifflés par match.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/10f-serie.py <matchs> <processus>
<avant|après> <sortie.json>"""
from __future__ import annotations

import importlib.util
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from v2engine import defense
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

_spec = importlib.util.spec_from_file_location("serie18m", Path(".scratch/v2-realisme/mesures/18m-serie.py"))
serie = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(serie)
MODE = "après"
Y = PITCH_WIDTH_M / 2.0
# mêmes zones que `defense.BOX_ZONES` (copiées : la série « avant » vide la constante du moteur)
ZONES = (("premier poteau", 4.0, 3.0), ("point de penalty", 11.0, 0.0), ("second poteau", 5.0, -4.0),
         ("retrait", 13.0, 6.0))
POSTS, POST_MAX_M = ("premier poteau", "second poteau"), 20.0


def one(i: int) -> dict:
    if MODE == "avant":
        defense.BOX_ZONES = ()
    from scripts.v2_chain import play
    serie.play = lambda j, _t={}: _t.setdefault(j, play(j))  # une seule simulation par match
    row = serie.one(i)
    trace = serie.play(i)
    wide, inbox, held = 0, 0, {name: 0 for name, _, _ in ZONES}
    asked = {name: 0 for name, _, _ in ZONES}
    line_depth = 0.0
    last = {"home": -99.0, "away": -99.0}
    for tk in trace.ticks:
        b = tk.ball
        if b.holder is None:
            continue
        team = next((p.team for p in tk.players if p.name == b.holder), None)
        if team is None:
            continue
        goal = defense.own_goal("away" if team == "home" else "home")
        spots = _spots(b.position, goal)
        if not spots:
            continue
        wide += 1
        last[team] = tk.minute
        defs = [p.position for p in tk.players if p.team != team and p.poste != "GK"]
        inbox += sum(1 for q in defs if abs(goal.x - q.x) <= 16.5 and abs(q.y - Y) <= 20.16)
        depths = sorted(abs(goal.x - p.position.x) for p in tk.players if p.team != team)
        line_depth += depths[1] if len(depths) > 1 else 0.0
        for name, spot in spots:
            if name in POSTS and abs(goal.x - b.position.x) > POST_MAX_M:
                continue
            asked[name] += 1
            held[name] += any(q.distance_to(spot) <= 3.0 for q in defs)
    after = [s for s in trace.shots if 0.0 <= s.minute - last[s.team] <= 10.0 / 60.0]
    row.update({"instants_aile": wide, "défenseurs_surface": inbox, "zones_tenues": held, "zones_demandées": asked,
                "profondeur_ligne": line_depth, "hors_jeu": len(trace.offsides),
                "tirs_après_aile": len(after), "buts_après_aile": sum(s.outcome == "but" for s in after)})
    return row


def _spots(ball, goal):
    aside = ball.y - goal.y
    if abs(ball.x - goal.x) > 35.0 or abs(aside) <= 20.16:
        return []
    inward = 1.0 if goal.x < PITCH_LENGTH_M / 2.0 else -1.0
    side = 1.0 if aside > 0.0 else -1.0
    return [(n, type(ball)(goal.x + inward * d, goal.y + side * o)) for n, d, o in ZONES]


def _init(mode: str) -> None:
    global MODE
    MODE = mode


if __name__ == "__main__":
    n, procs, mode, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    with ProcessPoolExecutor(max_workers=procs, initializer=_init, initargs=(mode,)) as pool:
        rows = list(pool.map(one, range(n)))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", mode, n)
