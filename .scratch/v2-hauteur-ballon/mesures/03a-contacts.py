"""Relevé des contacts du ticket v2-hauteur-ballon/03a (hors dépôt, lecture seule du moteur) : mêmes matchs du banc
(`scripts.v2_chain.play`). Par contrôle réussi (`trace.receptions`) : hauteur du ballon, partie du corps ; atteinte du
joueur recalculée depuis la base (taille, Jumping Reach ; mains si gardien et partie « mains ») pour vérifier qu'aucun
contact n'est au-dessus. Empreinte complète de la piste du ballon (déterminisme).

Utilisation : `PYTHONPATH=.:src PYTHONHASHSEED=0 <python> <script> 20 4 sortie.json`."""

from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def one(i: int) -> dict:
    from ligue1sim.clubs import load_clubs
    from scripts.measure_v2 import CLUBS_PATH
    from scripts.v2_chain import play
    from v2engine.atteinte import HANDS_SHARE, JUMP_M, height_of
    players = {p.name: p for c in load_clubs(CLUBS_PATH, "Ligue 1") for p in c.players}
    trace = play(i)
    h = hashlib.sha256()
    for b in trace.ball_track:
        h.update(f"{b.minute:.5f}|{b.position.x:.4f}|{b.position.y:.4f}|{b.z:.4f}|{b.mode}|{b.holder}|{b.dead}".encode())
    rows, above = [], 0
    for r in trace.receptions:
        p = players.get(r.player)
        if p is not None:
            jr = (p.attributes or {}).get("Jumping Reach", 60)
            jump = JUMP_M[0] + (JUMP_M[1] - JUMP_M[0]) * (min(99, max(1, jr)) - 1) / 98
            share = HANDS_SHARE if r.body_part == "mains" else 1.0
            reach = share * height_of(p.taille_fm, p.poste) + jump
            above += r.ball_z_m > reach + 1e-9
        rows.append([r.body_part, round(r.ball_z_m, 3), r.poste])
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "empreinte": h.hexdigest(),
            "contacts": rows, "au_dessus": above}


if __name__ == "__main__":
    n, procs, dest = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        out = list(pool.map(one, range(n)))
    Path(dest).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    parts = Counter(c[0] for r in out for c in r["contacts"])
    print("ok", n, "contacts", sum(parts.values()), dict(parts), "au-dessus de l'atteinte", sum(r["au_dessus"] for r in out))
    for part in parts:
        zs = sorted(c[1] for r in out for c in r["contacts"] if c[0] == part)
        print(part, "z médiane", zs[len(zs) // 2], "max", zs[-1])
