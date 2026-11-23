"""Série du ticket v2-hauteur-ballon/03b (reprise de `02a2-serie.py`, ticket v2-hauteur-ballon/02a2 (hors dépôt, lecture seule du moteur) : mêmes matchs du banc
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
    # Atteinte (ticket 03b) : contreur et gardien retrouvés dans le journal (contres et arrêts, dans l'ordre des tirs),
    # atteinte recalculée depuis la base (taille, Jumping Reach brut ; gardien : mains, il arrête dans sa surface ou non)
    from ligue1sim.clubs import load_clubs
    from scripts.measure_v2 import CLUBS_PATH
    from v2engine.atteinte import HANDS_SHARE, JUMP_M, height_of
    base = {p.name: p for c in load_clubs(CLUBS_PATH, "Ligue 1") for p in c.players}

    def reach(name: str, hands: bool) -> float:
        p = base[name]
        jr = min(99, max(1, (p.attributes or {}).get("Jumping Reach", 60)))
        return (HANDS_SHARE if hands else 1.0) * height_of(p.taille_fm, p.poste) + JUMP_M[0] + (JUMP_M[1] - JUMP_M[0]) * (jr - 1) / 98

    blockers = [e.player for e in trace.events if e.kind == "contre"]
    savers = [e.player for e in trace.events if e.kind == "arrêt"]
    blocked = [s for s in shots if s["issue"] == "contré"]
    saved = [s for s in shots if s["issue"] in ("capté", "repoussé", "claqué") and s["origine"] != "penalty"]
    for s, name in zip(blocked, blockers):
        s["contre_atteinte"] = reach(name, False)
    for s, name in zip(saved, savers):
        s["gardien_atteinte"] = reach(name, True)
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "tirs": shots,
            "empreinte_2d": flat.hexdigest(), "empreinte": full.hexdigest(), "z_min": min_z,
            "mode_incohérent": bad_mode, "contres_journal": len(blockers), "arrêts_journal": len(savers)}


if __name__ == "__main__":
    n, procs, dest = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, range(n)))
    Path(dest).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)
