"""Verifie la fluidite de l'interpolation du ballon dans render/canvas.html
a l'echelle de la frame (brief "canvas vertical slice", Tache 2, 23/09/2026).

ESCALADE DOCUMENTEE (2.2 non realisable tel quel) : le brief demande un
script qui OUVRE render/canvas_preview.html?debug=1 via un navigateur
headless PYTHON. Aucun package headless (playwright/selenium/pyppeteer/...)
n'est installe dans ce projet (`pip list` verifie -- seuls
numpy/openpyxl/pandas/streamlit/fastapi/uvicorn/pytest) et en ajouter un
violerait la regle "aucune nouvelle dependance". Ce script implemente donc
l'alternative acceptee (2.3), RENFORCEE : plutot qu'une extraction manuelle
de 10 frames depuis les devtools, les frames sont capturees par le
navigateur INTEGRE de Claude (un vrai navigateur, pas un headless Python)
lors de la session de travail, sauvegardees telles quelles dans
`docs/previews/canvas/frame_deltas_raw.json` (methode documentee dans le
retour de tache), et VERIFIEES ici par du code Python pur (aucune
dependance navigateur dans CE script) -- reexecutable sur n'importe quelle
capture au meme format.

Format d'entree attendu (une liste d'objets, un par frame RENDUE, produits
par le mode debug de render/canvas.html) ::

    [{"frame_idx": int, "t": float, "ballon_x": float, "ballon_y": float}, ...]

Usage :
    uv run python scripts/verify_canvas_smoothness.py [chemin_vers_le_json_capture]
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M  # noqa: E402

_DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "docs" / "previews" / "canvas" / "frame_deltas_raw.json"
_DEFAULT_OUTPUT_CSV = Path(__file__).resolve().parent.parent / "docs" / "previews" / "canvas" / "frame_deltas.csv"

_MAX_JUMP_RATIO = 3.0  # aucun delta > 3x le delta median
_TARGET_FRAMES_PER_2S = 120  # 60 fps
_FRAME_COUNT_TOLERANCE = 0.30  # +/-30%


def _distance_m(a: dict, b: dict) -> float:
    dx_m = (b["ballon_x"] - a["ballon_x"]) * PITCH_LENGTH_M
    dy_m = (b["ballon_y"] - a["ballon_y"]) * PITCH_WIDTH_M
    return math.hypot(dx_m, dy_m)


def verify(frames: list[dict]) -> dict:
    """Calcule les deltas et les deux criteres du brief. Ne leve jamais --
    renvoie un dict avec les resultats et un booleen `ok` par critere, pour
    que l'appelant decide (script CLI ici, mais reutilisable tel quel)."""
    if len(frames) < 2:
        raise ValueError(f"au moins 2 frames requises, recu {len(frames)}")

    deltas_m = [_distance_m(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    median_delta = statistics.median(deltas_m)
    max_delta = max(deltas_m)
    max_ratio = max_delta / median_delta if median_delta > 0 else float("inf")

    duration_s = frames[-1]["t"] - frames[0]["t"]
    frame_count = len(frames)
    # Nombre de frames attendu sur la DUREE REELLEMENT couverte par la
    # capture (pas force a 2s pile) -- extrapolation lineaire depuis la
    # cible 120 frames / 2s du brief.
    expected_count = _TARGET_FRAMES_PER_2S * (duration_s / 2.0) if duration_s > 0 else _TARGET_FRAMES_PER_2S
    low = expected_count * (1 - _FRAME_COUNT_TOLERANCE)
    high = expected_count * (1 + _FRAME_COUNT_TOLERANCE)

    return {
        "frame_count": frame_count,
        "duration_s": duration_s,
        "median_delta_m": median_delta,
        "max_delta_m": max_delta,
        "max_ratio": max_ratio,
        "no_jump_ok": max_ratio <= _MAX_JUMP_RATIO,
        "expected_frame_count": expected_count,
        "frame_count_range": (low, high),
        "frame_count_ok": low <= frame_count <= high,
        "deltas_m": deltas_m,
    }


def write_csv(frames: list[dict], deltas_m: list[float], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_idx", "t", "ballon_x", "ballon_y", "delta_m_depuis_frame_precedente"])
        writer.writerow([frames[0]["frame_idx"], frames[0]["t"], frames[0]["ballon_x"], frames[0]["ballon_y"], ""])
        for frame, delta_m in zip(frames[1:], deltas_m):
            writer.writerow([frame["frame_idx"], frame["t"], frame["ballon_x"], frame["ballon_y"], delta_m])


if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_INPUT
    frames = json.loads(input_path.read_text(encoding="utf-8"))

    result = verify(frames)
    write_csv(frames, result["deltas_m"], _DEFAULT_OUTPUT_CSV)

    print(f"Frames : {result['frame_count']} sur {result['duration_s']:.3f}s")
    print(f"Delta median : {result['median_delta_m'] * 100:.3f}cm, delta max : {result['max_delta_m'] * 100:.3f}cm, ratio : {result['max_ratio']:.2f}")
    print(f"  -> aucun saut (ratio <= {_MAX_JUMP_RATIO}) : {'OK' if result['no_jump_ok'] else 'ECHEC'}")
    low, high = result["frame_count_range"]
    print(f"Frames attendues ~{result['expected_frame_count']:.0f} (tolerance +/-{_FRAME_COUNT_TOLERANCE:.0%} -> [{low:.0f}, {high:.0f}])")
    print(f"  -> nombre de frames dans la tolerance : {'OK' if result['frame_count_ok'] else 'ECHEC'}")
    print(f"CSV ecrit : {_DEFAULT_OUTPUT_CSV}")

    if not (result["no_jump_ok"] and result["frame_count_ok"]):
        sys.exit(1)
