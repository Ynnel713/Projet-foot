"""Série du ticket v2-hauteur-ballon/02a2 (hors dépôt, lecture seule du moteur) : mêmes matchs du banc
(`scripts.v2_chain.play`). Par match : score ; tirs (minute, tireur, issue, origine) ; empreinte sha256 de la piste
du ballon EN 2D (positions, porteur, ballon mort : hauteur et mode exclus, pour comparer au code d'avant) ; empreinte
complète (hauteur et mode compris, pour le déterminisme). Avec la hauteur des tirs (code d'après) : hauteur réelle à la
ligne (`line_z_m`), au contre (`block_z_m`) et au passage du gardien (`keeper_z_m`) de chaque tir ; hauteur jamais
négative ; mode « aérien » si et seulement si la hauteur dépasse 2,5 m.

Utilisation : `PYTHONPATH=. PYTHONHASHSEED=0 <python> <script> 50 4 sortie.json`."""

from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def one(i: int) -> dict:
    from scripts.v2_chain import play
    trace = play(i)
    track = trace.ball_track
    flat, full = hashlib.sha256(), hashlib.sha256()
    min_z, bad_mode = 0.0, 0
    for b in track:
        line = f"{b.minute:.5f}|{b.position.x:.4f}|{b.position.y:.4f}|{b.holder}|{b.dead}"
        flat.update(line.encode())
        z = getattr(b, "z", 0.0)
        full.update(f"{line}|{z:.4f}|{b.mode}".encode())
        min_z = min(min_z, z)
        bad_mode += (b.mode == "aérien") != (z > 2.5)
    shots = [{"minute": round(s.minute, 5), "joueur": s.player, "issue": s.outcome, "origine": s.origin,
              "ligne_z": getattr(s, "line_z_m", None), "contre_z": getattr(s, "block_z_m", None),
              "gardien_z": getattr(s, "keeper_z_m", None)} for s in trace.shots]
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "tirs": shots,
            "empreinte_2d": flat.hexdigest(), "empreinte": full.hexdigest(), "z_min": min_z,
            "mode_incohérent": bad_mode}


if __name__ == "__main__":
    n, procs, dest = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, range(n)))
    Path(dest).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)
