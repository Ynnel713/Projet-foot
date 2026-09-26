"""Résolution des photos de joueurs (pack Sortitoutsi, 26/09/2026).

Une image par joueur déjà enrichi FM26, dans `assets/faces/`, nommée par
l'ID Excel du joueur (`Player.id`) -- pas par l'ID Sortitoutsi d'origine, pour
que ce module (et l'UI qui l'appelle) n'ait jamais besoin de connaître le
format d'URL fminide : c'est `scripts/extract_faces.py` qui fait la
conversion une seule fois, à l'extraction depuis le megapack.

`assets/faces/` n'est pas versionné (voir .gitignore) -- régénérable à tout
moment via `scripts/extract_faces.py`, à partir du megapack (~16 Go,
téléchargé séparément) et de `data/joueurs.xlsx`.
"""

from __future__ import annotations

from pathlib import Path

FACES_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "faces"


def face_path(player_id: int | None) -> Path | None:
    """Chemin de la photo d'un joueur, ou None si absente (joueur pas encore
    enrichi FM26, ou introuvable dans le megapack -- voir le rapport de
    scripts/extract_faces.py)."""
    if player_id is None:
        return None
    path = FACES_DIR / f"{player_id}.png"
    return path if path.is_file() else None
