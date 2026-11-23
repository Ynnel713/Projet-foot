"""Série du ticket v2-hauteur-ballon/02a1 (hors dépôt, lecture seule du moteur) : mêmes matchs du banc
(`scripts.v2_chain.play`). Par match : score, tirs, empreinte sha256 de la piste du ballon (positions, hauteur, mode,
porteur) ; vols du ballon (du départ du sol à son premier retour au sol) : durée, sommet, distance au premier impact ;
contrôles : hauteur jamais négative, mode « aérien » si et seulement si la hauteur dépasse 2,5 m ; ballons longs (vol
de plus de 25 m) gardés par l'équipe du passeur. Sans hauteur (code d'avant), seuls score, tirs, empreinte et ballons
longs gardés (détectés par l'événement de passe) sont relevés.

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
    has_z = bool(track) and hasattr(track[0], "z")
    h = hashlib.sha256()
    for b in track:
        h.update(f"{b.minute:.5f}|{b.position.x:.4f}|{b.position.y:.4f}|{getattr(b, 'z', 0.0):.4f}|{b.mode}|{b.holder}|"
                 f"{b.dead}".encode())
    h.update(f"{trace.home_goals}-{trace.away_goals}".encode())
    teams = {}
    for tick in trace.ticks[::120]:
        for pl in tick.players:
            teams[pl.name] = pl.team
    out = {"match": i, "score": [trace.home_goals, trace.away_goals], "tirs": len(trace.shots),
           "empreinte": h.hexdigest(), "aériens_tracés": sum(b.mode == "aérien" for b in track)}
    if not has_z:
        return out
    flights, bad_mode, min_z = [], 0, 0.0
    for b in track:
        min_z = min(min_z, b.z)
        bad_mode += (b.mode == "aérien") != (b.z > 2.5)
    k = 1
    while k < len(track):
        if not (track[k].z > 0.0 and track[k - 1].z == 0.0):
            k += 1
            continue
        start = track[k - 1]  # dernier point au sol : départ du vol
        passer_team = teams.get(start.holder) if start.holder else None
        j, peak = k, 0.0
        # premier impact : la hauteur cesse de descendre (rebond) ou le vol s'arrête (contact, ballon mort, au sol)
        while j < len(track) and track[j].z > 0.0 and track[j].holder is None and not track[j].dead:
            peak = max(peak, track[j].z)
            if j > k and track[j].z > track[j - 1].z and track[j - 1].z < track[j - 2].z:
                break
            j += 1
        end = track[min(j, len(track) - 1)]
        caught = end.holder is not None
        n = j
        while n < len(track) and track[n].holder is None and not track[n].dead:
            n += 1
        after = track[n] if n < len(track) else None
        kept = None if after is None or after.dead or passer_team is None else teams.get(after.holder) == passer_team
        flights.append({"durée": (end.minute - start.minute) * 60.0, "sommet": peak,
                        "distance": start.position.distance_to(end.position), "gardé": kept, "pris_en_l_air": caught})
        while j < len(track) and track[j].z > 0.0:
            j += 1
        k = j + 1
    out.update({"z_min": min_z, "mode_incohérent": bad_mode, "vols": flights})
    return out


if __name__ == "__main__":
    n, procs, dest = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, range(n)))
    Path(dest).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)
