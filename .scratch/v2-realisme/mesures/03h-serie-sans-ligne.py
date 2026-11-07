"""Série du ticket v2-realisme/03h : le moteur actuel avec `gardien.LINE_RATIO = 0` (placement du 03b, sans la ligne
défensive du 03c). Même matchs et mêmes graines que `scripts.bench_series` ; seul le réglage change, y compris dans les
processus de la série (initialiseur du pool).

Usage (depuis la racine du dépôt) :
  PYTHONPATH=. uv run python .scratch/v2-realisme/mesures/03h-serie-sans-ligne.py 50 --processus 7 --json sortie.json
(mêmes arguments que `python -m scripts.bench_series`)."""

from concurrent.futures import ProcessPoolExecutor

import scripts.bench_series as bench_series
import v2engine.gardien as gardien


def _sans_ligne() -> None:
    gardien.LINE_RATIO = 0.0


def _pool(max_workers):
    return ProcessPoolExecutor(max_workers=max_workers, initializer=_sans_ligne)


if __name__ == "__main__":
    import sys

    _sans_ligne()  # le processus principal aussi (cas d'un seul processus)
    bench_series.ProcessPoolExecutor = _pool
    bench_series.main(sys.argv[1:])
