"""Ticket 14a2b : série de 50 matchs (`scripts.bench_series`) avec relevé de chaque frappe en l'air (passe aérienne,
relance, tir) : vitesse horizontale, vitesse verticale rendue et vitesse verticale non bornée. L'enveloppe ne change
aucun résultat (mêmes valeurs rendues). Une ligne par frappe dans `14a2b-frappes/<pid>.txt`.
Usage : uv run python .scratch/v2-realisme/mesures/14a2b-frappes.py 50 --processus 4 --json apres.json"""
import math
import os
import sys

sys.path.insert(0, ".")
from v2engine import hauteur
from scripts import bench_series

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "14a2b-frappes")
os.makedirs(OUT, exist_ok=True)
_vz, _vz_to = hauteur.launch_vz, hauteur.launch_vz_to


def _log(kind, horizontal, vz, raw):
    with open(os.path.join(OUT, f"{os.getpid()}.txt"), "a", encoding="utf-8") as f:
        f.write(f"{kind} {horizontal!r} {vz!r} {raw!r}\n")


def launch_vz(flight_s, horizontal_mps):
    vz = _vz(flight_s, horizontal_mps)
    raw = math.inf if flight_s is None else 0.5 * hauteur.GRAVITY_M_S2 * max(0.0, flight_s)
    _log("passe", horizontal_mps, vz, raw)
    return vz


def launch_vz_to(z_target_m, flight_s):  # tirs : non bornés (décision du 27/11/2026) ; vh = 30 m/s
    horizontal_mps = 30.0
    vz = _vz_to(z_target_m, flight_s)
    raw = 0.0 if not flight_s else (max(0.0, z_target_m) + 0.5 * hauteur.GRAVITY_M_S2 * flight_s ** 2) / flight_s
    _log("tir", horizontal_mps, vz, raw)
    return vz


hauteur.launch_vz, hauteur.launch_vz_to = launch_vz, launch_vz_to
bench_series.main(sys.argv[1:])
