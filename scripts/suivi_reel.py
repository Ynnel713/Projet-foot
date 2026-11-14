"""Données de suivi réelles : téléchargement et lecture dans le repère du moteur V2 (ticket v2-realisme/27a).

Deux sources publiques, choisies par le propriétaire le 14/11/2026 :
- **SkillCorner open data** (licence MIT, citer SkillCorner) : 20 matchs du championnat d'Australie 2024/25, suivi
  tiré de la vidéo de diffusion à 10 images/s, avec le découpage du match en phases de jeu. Un joueur hors du champ
  de la caméra a une position estimée (`detected` faux) : c'est la source principale pour la forme des équipes et les
  phases.
- **Metrica Sports, échantillon** (pas de licence formelle : « usage responsable, citer la source ») : matchs 1 et 2,
  anonymes, terrain entier filmé à 25 images/s, tous les joueurs suivis ; contrôle des vitesses et des sprints. Le
  match 3 (format EPTS FIFA) n'est pas lu.

Repère de sortie : celui du moteur (`v2engine.geometry`, `v2engine.formation`), en mètres, origine dans un coin, x le
long du terrain, y en largeur et croissant vers le bas de l'écran : en attaquant vers les x croissants, la gauche d'une
équipe est en y petit. L'équipe à domicile attaque vers les x croissants pendant tout le match (le changement de côté
à la mi-temps est corrigé par une rotation de 180°, pas par un miroir). Le temps d'une image part de 0 au début de
chaque période, pour les deux sources. Les mètres restent réels : un terrain qui ne fait
pas 105 × 68 m garde ses dimensions (décision du propriétaire, 14/11/2026) et est signalé par `Match.standard`.

Les fichiers téléchargés vont dans `data/externe/` (ignoré par git, jamais versionné). Le téléchargement est
idempotent et vérifié : empreinte sha256 publiée par Git LFS pour SkillCorner, empreinte relevée au premier
téléchargement et figée ci-dessous pour Metrica (`METRICA_SHA256`), faute d'empreinte publiée.

Usage : `uv run python -m scripts.suivi_reel telecharger [--source skillcorner|metrica]` puis
`uv run python -m scripts.suivi_reel resume`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "externe"
SKILLCORNER_RAW = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data"
SKILLCORNER_MEDIA = "https://media.githubusercontent.com/media/SkillCorner/opendata/master/data"
METRICA_RAW = "https://raw.githubusercontent.com/metrica-sports/sample-data/master/data"
METRICA_LENGTH_M, METRICA_WIDTH_M, METRICA_FPS = 105.0, 68.0, 25.0  # README de Metrica : terrain 105 × 68 m
STANDARD_PITCH = (105.0, 68.0)
METRICA_GAMES = (1, 2)
# Empreintes relevées au premier téléchargement (14/11/2026) ; un fichier qui en diffère est refusé.
METRICA_SHA256: dict[str, str] = {
    "Sample_Game_1/Sample_Game_1_RawTrackingData_Home_Team.csv": "0a3d0eff7785950379c587d3597b86a2d91c2492281b4652e1abb97c99b6b364",
    "Sample_Game_1/Sample_Game_1_RawTrackingData_Away_Team.csv": "0a3df68a92af0290ede472e62de3b6489ddee29223da09bdf0cf76c8e0ab0618",
    "Sample_Game_2/Sample_Game_2_RawTrackingData_Home_Team.csv": "3f9990ac204b07133e4202441d6fcbb386897c7c7f81e1bc3ce4d35bc8644694",
    "Sample_Game_2/Sample_Game_2_RawTrackingData_Away_Team.csv": "aa639f40762eade46c389020fe4458266b5ba14027b1e96e22e75db62803718b",
}

HOME, AWAY = "home", "away"
_LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"


@dataclass(frozen=True)
class Player:
    id: str
    team: str  # HOME ou AWAY
    x: float
    y: float
    detected: bool  # faux : position estimée hors du champ de la caméra (SkillCorner)
    role: str | None = None  # poste fourni par la source (SkillCorner : GK, CB, RW…), None sinon


@dataclass(frozen=True)
class Frame:
    source: str
    match: str
    period: int
    time_s: float  # depuis le début de la période
    ball: tuple[float, float] | None
    players: tuple[Player, ...]
    possession: str | None  # HOME, AWAY ou None (ballon en l'air, mort ou disputé)
    phase: str | None  # phase de jeu de l'équipe en possession (SkillCorner : build_up, create, finish…)


@dataclass(frozen=True)
class Match:
    source: str
    id: str
    length_m: float
    width_m: float

    @property
    def standard(self) -> bool:
        return (self.length_m, self.width_m) == STANDARD_PITCH


# --- Repère ---------------------------------------------------------------------------------------------------


def to_engine(x: float, y: float, home_attacks_positive: bool, length_m: float, width_m: float) -> tuple[float, float]:
    """Point d'un repère centré (origine au rond central, x le long du terrain, y vers le haut : convention de
    SkillCorner) vers le repère du moteur (y vers le bas : la gauche d'une équipe qui attaque vers les x croissants est
    en y petit). Si l'équipe à domicile attaque vers les x négatifs pendant cette période, rotation de 180° (x et y
    changent de signe ensemble)."""
    sign = 1.0 if home_attacks_positive else -1.0
    return length_m / 2.0 + sign * x, width_m / 2.0 - sign * y


# --- Téléchargement -------------------------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def _download(url: str, target: Path, sha256: str | None) -> str:
    """Télécharge `url` vers `target` sauf si le fichier présent a déjà la bonne empreinte ; retourne l'empreinte."""
    if target.exists() and (sha256 is None or _sha256(target) == sha256):
        return _sha256(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as out:
        while block := response.read(1 << 20):
            out.write(block)
    found = _sha256(partial)
    if sha256 is not None and found != sha256:
        partial.unlink()
        raise ValueError(f"empreinte inattendue pour {url} : {found} au lieu de {sha256}")
    partial.replace(target)
    return found


def lfs_pointer(text: bytes) -> tuple[str, int]:
    """Empreinte sha256 et taille d'un pointeur Git LFS."""
    if not text.startswith(_LFS_HEADER):
        raise ValueError("pas un pointeur Git LFS")
    fields = dict(line.split(" ", 1) for line in text.decode("ascii").splitlines() if " " in line)
    return fields["oid"].removeprefix("sha256:"), int(fields["size"])


def skillcorner_ids(root: Path = DATA_DIR) -> list[str]:
    path = root / "skillcorner" / "matches.json"
    return [str(m["id"]) for m in json.loads(path.read_text(encoding="utf-8"))]


def download_skillcorner(root: Path = DATA_DIR) -> None:
    base = root / "skillcorner"
    base.mkdir(parents=True, exist_ok=True)
    (base / "matches.json").write_bytes(_get(f"{SKILLCORNER_RAW}/matches.json"))
    ids = skillcorner_ids(root)
    print(f"skillcorner : {len(ids)} matchs listés par matches.json", flush=True)  # la liste amont peut changer
    for match_id in ids:
        folder = base / match_id
        for name in (f"{match_id}_match.json", f"{match_id}_phases_of_play.csv"):
            raw = _get(f"{SKILLCORNER_RAW}/matches/{match_id}/{name}")
            if raw.startswith(_LFS_HEADER):
                sha, _ = lfs_pointer(raw)
                _download(f"{SKILLCORNER_MEDIA}/matches/{match_id}/{name}", folder / name, sha)
            else:
                folder.mkdir(parents=True, exist_ok=True)
                (folder / name).write_bytes(raw)
        name = f"{match_id}_tracking_extrapolated.jsonl"
        sha, _ = lfs_pointer(_get(f"{SKILLCORNER_RAW}/matches/{match_id}/{name}"))
        _download(f"{SKILLCORNER_MEDIA}/matches/{match_id}/{name}", folder / name, sha)
        print(f"skillcorner {match_id} : ok", flush=True)


def _metrica_names(game: int) -> list[str]:
    return [f"Sample_Game_{game}/Sample_Game_{game}_RawTrackingData_{side}_Team.csv" for side in ("Home", "Away")]


def download_metrica(root: Path = DATA_DIR) -> dict[str, str]:
    found = {}
    for game in METRICA_GAMES:
        for name in _metrica_names(game):
            found[name] = _download(f"{METRICA_RAW}/{name}", root / "metrica" / name, METRICA_SHA256.get(name))
            print(f"metrica {name} : {found[name]}", flush=True)
    return found


# --- Lecture SkillCorner --------------------------------------------------------------------------------------


def _skillcorner_phases(path: Path, home_id: int) -> list[tuple[int, int, str, str]]:
    """(image de début, image de fin, équipe en possession, phase), triées par début."""
    phases = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            team = HOME if int(row["team_in_possession_id"]) == home_id else AWAY
            phases.append((int(row["frame_start"]), int(row["frame_end"]), team, row["team_in_possession_phase_type"]))
    return sorted(phases)


def skillcorner_match(match_id: str, root: Path = DATA_DIR) -> Match:
    meta = json.loads((root / "skillcorner" / match_id / f"{match_id}_match.json").read_text(encoding="utf-8"))
    return Match("skillcorner", match_id, float(meta["pitch_length"]), float(meta["pitch_width"]))


def _timestamp_s(text: str) -> float:
    hours, minutes, seconds = text.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def read_skillcorner(match_id: str, root: Path = DATA_DIR) -> Iterator[Frame]:
    """Images en jeu (période connue) d'un match SkillCorner, dans le repère du moteur. La phase d'une image est celle
    du découpage SkillCorner qui la contient, None hors de toute phase."""
    folder = root / "skillcorner" / match_id
    meta = json.loads((folder / f"{match_id}_match.json").read_text(encoding="utf-8"))
    home_id = int(meta["home_team"]["id"])
    teams = {int(p["id"]): (HOME if int(p["team_id"]) == home_id else AWAY) for p in meta["players"]}
    roles = {int(p["id"]): (p.get("player_role") or {}).get("acronym") for p in meta["players"]}
    sides = meta["home_team_side"]  # par période : "left_to_right" = l'équipe à domicile attaque vers les x croissants
    length, width = float(meta["pitch_length"]), float(meta["pitch_width"])
    phases = _skillcorner_phases(folder / f"{match_id}_phases_of_play.csv", home_id)
    cursor = 0
    period_start: dict[int, float] = {}  # SkillCorner donne le temps de match (45:00 au début de la 2e période)
    with (folder / f"{match_id}_tracking_extrapolated.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            raw = json.loads(line)
            period = raw["period"]
            if period is None or raw["timestamp"] is None:
                continue
            positive = sides[period - 1] == "left_to_right"
            frame_no = int(raw["frame"])
            while cursor < len(phases) and phases[cursor][1] < frame_no:
                cursor += 1
            phase = phases[cursor][3] if cursor < len(phases) and phases[cursor][0] <= frame_no else None
            ball_raw = raw["ball_data"]
            ball = None
            if ball_raw and ball_raw.get("x") is not None:
                ball = to_engine(ball_raw["x"], ball_raw["y"], positive, length, width)
            players = []
            for p in raw["player_data"]:
                pid = int(p["player_id"])
                x, y = to_engine(p["x"], p["y"], positive, length, width)
                players.append(Player(str(pid), teams[pid], x, y, bool(p["is_detected"]), roles.get(pid)))
            group = (raw.get("possession") or {}).get("group")
            possession = HOME if group == "home team" else AWAY if group == "away team" else None
            stamp = _timestamp_s(raw["timestamp"])
            start = period_start.setdefault(int(period), stamp)
            yield Frame("skillcorner", match_id, int(period), stamp - start, ball, tuple(players), possession, phase)


# --- Lecture Metrica ------------------------------------------------------------------------------------------


def _metrica_rows(path: Path) -> Iterator[tuple[list[str], list[str]]]:
    """(identifiants des colonnes de position, valeurs) de chaque ligne d'un fichier Metrica (3 lignes d'en-tête)."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        next(reader)
        next(reader)
        header = next(reader)
        for row in reader:
            yield header, row


def _metrica_side(path: Path, team: str) -> Iterator[tuple[int, int, float, dict[str, tuple[float, float]], tuple | None]]:
    """(période, image, temps, joueurs {id: (x, y) centré, y vers le haut}, ballon centré) d'un fichier d'équipe.
    Metrica a son origine en haut à gauche, y vers le bas : y est inversé ici pour l'entrée commune de `to_engine`."""
    for header, row in _metrica_rows(path):
        players = {}
        ball = None
        for col in range(3, len(header) - 1, 2):
            name = header[col]
            if not name or not row[col] or not row[col + 1] or row[col] == "NaN" or row[col + 1] == "NaN":
                continue
            centred = (float(row[col]) * METRICA_LENGTH_M - METRICA_LENGTH_M / 2.0,
                       METRICA_WIDTH_M / 2.0 - float(row[col + 1]) * METRICA_WIDTH_M)
            if name == "Ball":
                ball = centred
            else:
                players[f"{team}-{name}"] = centred
        yield int(row[0]), int(row[1]), float(row[2]), players, ball


def read_metrica(game: int, root: Path = DATA_DIR) -> Iterator[Frame]:
    """Images d'un match Metrica, dans le repère du moteur. Le côté de l'équipe à domicile, inconnu dans les fichiers,
    se lit à la première image de chaque période : sa position moyenne est dans sa propre moitié au coup d'envoi."""
    home_path, away_path = (root / "metrica" / name for name in _metrica_names(game))
    positive: dict[int, bool] = {}
    period_start: dict[int, float] = {}
    for (period, _, time_s, home, ball), (_, _, _, away, _) in zip(_metrica_side(home_path, HOME),
                                                                    _metrica_side(away_path, AWAY)):
        if period not in positive:
            if not home:
                continue
            positive[period] = sum(x for x, _ in home.values()) / len(home) < 0.0
            period_start[period] = time_s
        sign = positive[period]
        players = tuple(Player(pid, team, *to_engine(x, y, sign, METRICA_LENGTH_M, METRICA_WIDTH_M), True)
                        for team, side in ((HOME, home), (AWAY, away)) for pid, (x, y) in side.items())
        engine_ball = to_engine(*ball, sign, METRICA_LENGTH_M, METRICA_WIDTH_M) if ball else None
        yield Frame("metrica", str(game), period, time_s - period_start[period], engine_ball, players, None, None)


# --- Résumé ---------------------------------------------------------------------------------------------------


def summary(frames: Iterator[Frame]) -> dict[str, float]:
    """Volume d'un match : images, part des images avec 22 joueurs (au moins 20 détectés), ballon connu, phase."""
    count = full = detected20 = with_ball = with_phase = 0
    for frame in frames:
        count += 1
        full += len(frame.players) >= 22
        detected20 += sum(p.detected for p in frame.players) >= 20
        with_ball += frame.ball is not None
        with_phase += frame.phase is not None
    share = (lambda n: round(n / count, 4)) if count else (lambda n: 0.0)
    return {"images": count, "part_22_joueurs": share(full), "part_20_detectes": share(detected20),
            "part_ballon": share(with_ball), "part_phase": share(with_phase)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)
    down = sub.add_parser("telecharger")
    down.add_argument("--source", choices=("skillcorner", "metrica"), default=None)
    sub.add_parser("resume")
    args = parser.parse_args(argv)
    if args.action == "telecharger":
        if args.source in (None, "metrica"):
            download_metrica()
        if args.source in (None, "skillcorner"):
            download_skillcorner()
        return 0
    rows = [(skillcorner_match(mid), lambda mid=mid: read_skillcorner(mid)) for mid in skillcorner_ids()]
    rows += [(Match("metrica", str(g), METRICA_LENGTH_M, METRICA_WIDTH_M), lambda g=g: read_metrica(g))
             for g in METRICA_GAMES]
    for match, reader in rows:
        start = time.perf_counter()
        result = summary(reader())
        flag = "" if match.standard else f" terrain {match.length_m:g} x {match.width_m:g} m"
        print(f"{match.source} {match.id}{flag} : {result}, lecture {time.perf_counter() - start:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
