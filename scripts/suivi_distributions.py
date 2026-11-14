"""Distributions de référence tirées des données de suivi réelles (ticket v2-realisme/27b).

Sur les images lues par `scripts.suivi_reel` (repère du moteur), calcule des distributions (taille d'échantillon,
quartiles, médiane), avec les fonctions de mesure du moteur (`scripts.v2_indicators`) : aucune réécriture parallèle.

Indicateurs (définitions validées par le propriétaire le 14/11/2026, `docs/INDICATEURS_V2.md`, section 39) :
- forme de chaque équipe, joueurs de champ seulement (gardien exclu, 10 joueurs exigés) : longueur et largeur
  (`length_width`), écarts défense-milieu et milieu-attaque (`line_gaps`), hauteur de la ligne défensive
  (`block_height`), avec ou sans ballon et par phase de jeu SkillCorner ; deux variantes : « toutes positions »
  (positions estimées hors caméra comprises) et « équipe détectée » (les 10 joueurs de champ dans le champ de la caméra).
  L'équipe extérieure est mesurée après une rotation de 180° du terrain réel, comme si elle jouait à domicile : la
  hauteur reste exacte sur un terrain qui ne fait pas 105 m (`progress` suppose 105 m) ;
- autour du porteur (SkillCorner, porteur détecté) : soutien le plus proche (coéquipier, gardien compris), presseur
  (adversaire de champ le plus proche, comme `Collector._pressing`) et part des images où il est à moins de
  PRESS_RADIUS_M ;
- réception (SkillCorner) : le porteur change et le nouveau est de la même équipe que le précédent porteur connu, dans
  la même période ; distance du receveur (détecté) au plus proche adversaire, gardien compris, à sa première image ;
- vitesse : déplacement entre l'image SPEED_HALF_WINDOW_S avant et l'image SPEED_HALF_WINDOW_S après, le joueur détecté
  sur toute la fenêtre, valeurs au-dessus de SPEED_MAX_MPS écartées (bruit) ; par famille de postes (SkillCorner,
  remplaçants sans poste exclus) et pour tous les joueurs de champ (Metrica, gardien = joueur dont la position médiane
  est la plus proche de son but). Le moteur, lui, lit sa vitesse instantanée.

Usage : `uv run python -m scripts.suivi_distributions [--sortie fichier.json] [--matchs N]`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor

from scripts import suivi_reel as sr
from scripts.v2_indicators import (
    POSTE_FAMILY,
    PRESS_RADIUS_M,
    block_height,
    length_width,
    line_gaps,
    nearest_distance,
    quartiles,
    speed_shares,
)
from v2engine.geometry import Vec2

# Constantes de mesure (validées par le propriétaire le 14/11/2026), sans effet sur le jeu.
SPEED_HALF_WINDOW_S = 0.2
SPEED_MAX_MPS = 12.0
OUTFIELD = 10
# Rôles SkillCorner vers postes du moteur (LM et RM : milieux) ; un rôle absent (SUB) n'a pas de poste.
SKILLCORNER_POSTE = {"GK": "GK", "CB": "DC", "LCB": "DC", "RCB": "DC", "LB": "LB", "LWB": "LB", "RB": "RB", "RWB": "RB",
                     "DM": "MDC", "LDM": "MDC", "RDM": "MDC", "CM": "MC", "LCM": "MC", "RCM": "MC", "LM": "MC",
                     "RM": "MC", "AM": "MOC", "LW": "AG", "RW": "AD", "CF": "BU", "LF": "ATT", "RF": "ATT"}
FPS = {"skillcorner": 10.0, "metrica": sr.METRICA_FPS}


def own_view(team: str, points: Iterable[tuple[float, float]], length_m: float, width_m: float) -> list[Vec2]:
    """Points vus comme si `team` jouait à domicile (attaque vers les x croissants depuis x = 0) : rotation de 180° du
    terrain réel pour l'équipe extérieure."""
    if team == sr.HOME:
        return [Vec2(x, y) for x, y in points]
    return [Vec2(length_m - x, width_m - y) for x, y in points]


def shape(team: str, points: Sequence[tuple[float, float]], length_m: float, width_m: float) -> dict[str, float]:
    """Forme d'une équipe (joueurs de champ) avec les fonctions du moteur."""
    pts = own_view(team, points, length_m, width_m)
    length, width = length_width(pts)
    out = {"longueur (m)": length, "largeur (m)": width, "hauteur de la ligne défensive (m)": block_height("home", pts)}
    gaps = line_gaps("home", pts)
    if gaps:
        out["écart défense-milieu (m)"], out["écart milieu-attaque (m)"] = gaps
    return out


class Accumulator:
    """Valeurs par libellé d'indicateur ; fusion dans un ordre fixe (déterminisme)."""

    def __init__(self) -> None:
        self.values: dict[str, list[float]] = defaultdict(list)
        self.counts: dict[str, int] = defaultdict(int)

    def add(self, label: str, value: float) -> None:
        self.values[label].append(value)

    def merge(self, other: Accumulator) -> None:
        for label, values in other.values.items():
            self.values[label].extend(values)
        for label, n in other.counts.items():
            self.counts[label] += n


def _shapes(acc: Accumulator, frame: sr.Frame, match: sr.Match, goalkeepers: set[str]) -> None:
    for team in (sr.HOME, sr.AWAY):
        field = [p for p in frame.players if p.team == team and p.id not in goalkeepers]
        if len(field) != OUTFIELD:
            continue
        if frame.possession is None:
            phases = ["possession inconnue"]
        else:
            side = "avec ballon" if frame.possession == team else "sans ballon"
            phases = [side] + ([f"{side}, phase {frame.phase}"] if frame.phase else [])
        variants = ["toutes positions"] + (["équipe détectée"] if all(p.detected for p in field) else [])
        for name, value in shape(team, [(p.x, p.y) for p in field], match.length_m, match.width_m).items():
            for variant in variants:
                for phase in phases:
                    acc.add(f"{match.source} | forme | {variant} | {phase} | {name}", value)


def _around_holder(acc: Accumulator, frame: sr.Frame, goalkeepers: set[str], last: dict) -> None:
    by_id = {p.id: p for p in frame.players}
    holder = by_id.get(frame.holder) if frame.holder else None
    if holder is None:
        return
    previous = last.get(frame.period)
    last[frame.period] = holder
    if not holder.detected:
        return
    here = Vec2(holder.x, holder.y)
    opponents = [p for p in frame.players if p.team != holder.team]
    phases = ["toutes"] + ([f"phase {frame.phase}"] if frame.phase else [])
    if previous is not None and previous.id != holder.id and previous.team == holder.team:
        gap = nearest_distance(here, [Vec2(p.x, p.y) for p in opponents])
        if gap is not None:
            acc.add("skillcorner | réception | distance au plus proche adversaire (m)", gap)
    support = nearest_distance(here, [Vec2(p.x, p.y) for p in frame.players if p.team == holder.team and p is not holder])
    presser = nearest_distance(here, [Vec2(p.x, p.y) for p in opponents if p.id not in goalkeepers])
    for phase in phases:
        if support is not None:
            acc.add(f"skillcorner | porteur | {phase} | soutien le plus proche (m)", support)
        if presser is not None:
            acc.add(f"skillcorner | porteur | {phase} | distance presseur-porteur (m)", presser)
            acc.add(f"skillcorner | porteur | {phase} | presseur à moins de {PRESS_RADIUS_M:g} m (part)",
                    1.0 if presser < PRESS_RADIUS_M else 0.0)


def track_speeds(track: Sequence[tuple[float, float, float, bool]], fps: float) -> list[float]:
    """Vitesses (m/s) d'un joueur sur une période : (temps, x, y, détecté) par image, dans l'ordre. Fenêtre centrée de
    ±SPEED_HALF_WINDOW_S, joueur détecté sur toute la fenêtre, images contiguës ; au-dessus de SPEED_MAX_MPS, écarté."""
    k = round(SPEED_HALF_WINDOW_S * fps)
    span = 2 * k / fps
    detected = [d for _, _, _, d in track]
    run = [0] * len(track)  # nombre d'images détectées consécutives finissant en i
    for i, d in enumerate(detected):
        run[i] = (run[i - 1] + 1 if i else 1) if d else 0
    out = []
    for i in range(k, len(track) - k):
        if run[i + k] < 2 * k + 1:
            continue
        (t0, x0, y0, _), (t1, x1, y1, _) = track[i - k], track[i + k]
        if abs((t1 - t0) - span) > 0.5 / fps:
            continue
        v = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / (t1 - t0)
        if v <= SPEED_MAX_MPS:
            out.append(v)
    return out


def _speeds(acc: Accumulator, tracks: dict, family: dict[str, str | None], source: str) -> None:
    for (pid, _period) in sorted(tracks):
        label = family.get(pid)
        if label is None or label == "gardien":
            continue
        for v in track_speeds(tracks[(pid, _period)], FPS[source]):
            acc.add(f"{source} | vitesse | {label} | vitesse (m/s)", v)


def _metrica_goalkeepers(game: int, root) -> set[str]:
    """Gardien de chaque équipe : le joueur dont la position médiane est la plus proche de son propre but."""
    depth: dict[tuple[str, str], list[float]] = defaultdict(list)
    for i, frame in enumerate(sr.read_metrica(game, root)):
        if i % round(sr.METRICA_FPS):  # une image par seconde suffit
            continue
        for p in frame.players:
            depth[(p.team, p.id)].append(p.x if p.team == sr.HOME else sr.METRICA_LENGTH_M - p.x)
    keepers = set()
    for team in (sr.HOME, sr.AWAY):
        medians = {pid: statistics.median(v) for (t, pid), v in depth.items() if t == team}
        keepers.add(min(sorted(medians), key=lambda pid: medians[pid]))
    return keepers


def measure_match(source: str, match_id: str, root=sr.DATA_DIR) -> Accumulator:
    acc = Accumulator()
    tracks: dict[tuple[str, int], list] = defaultdict(list)
    if source == "skillcorner":
        match = sr.skillcorner_match(match_id, root)
        meta = json.loads((root / "skillcorner" / match_id / f"{match_id}_match.json").read_text(encoding="utf-8"))
        roles = {str(p["id"]): (p.get("player_role") or {}).get("acronym") for p in meta["players"]}
        goalkeepers = {pid for pid, role in roles.items() if role == "GK"}
        family = {pid: POSTE_FAMILY[SKILLCORNER_POSTE[role]] if role in SKILLCORNER_POSTE else None
                  for pid, role in roles.items()}
        frames = sr.read_skillcorner(match_id, root)
    else:
        match = sr.Match("metrica", match_id, sr.METRICA_LENGTH_M, sr.METRICA_WIDTH_M)
        goalkeepers = _metrica_goalkeepers(int(match_id), root)
        family = None
        frames = sr.read_metrica(int(match_id), root)
    last: dict[int, sr.Player] = {}
    for frame in frames:
        acc.counts[f"{source} | images"] += 1
        _shapes(acc, frame, match, goalkeepers)
        if source == "skillcorner":
            _around_holder(acc, frame, goalkeepers, last)
        for p in frame.players:
            tracks[(p.id, frame.period)].append((frame.time_s, p.x, p.y, p.detected))
    if family is None:
        family = {pid: ("gardien" if pid in goalkeepers else "joueurs de champ") for pid, _ in tracks}
    _speeds(acc, tracks, family, source)
    acc.counts[f"{source} | matchs"] += 1
    return acc


def _job(args: tuple[str, str]) -> Accumulator:
    return measure_match(*args)


def report(acc: Accumulator) -> dict:
    """Distributions publiées : quartiles de chaque indicateur ; pour les vitesses, parts au-dessus de 19,8 et 25 km/h."""
    out: dict = {"volumes": dict(sorted(acc.counts.items())), "distributions": {}}
    for label in sorted(acc.values):
        values = acc.values[label]
        row = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in quartiles(values).items()}
        if label.endswith("(part)"):
            row = {"n": len(values), "part": round(statistics.fmean(values), 4)}
        if "| vitesse |" in label:
            high, sprint = speed_shares(values)
            row["part > 19,8 km/h"], row["part > 25 km/h"] = round(high, 4), round(sprint, 4)
        out["distributions"][label] = row
    return out


def jobs(limit: int | None = None) -> list[tuple[str, str]]:
    ids = sr.skillcorner_ids()
    return [("skillcorner", mid) for mid in ids[:limit]] + [("metrica", str(g)) for g in sr.METRICA_GAMES]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sortie", default=None, help="fichier JSON de sortie (sinon : sortie standard)")
    parser.add_argument("--matchs", type=int, default=None, help="limiter aux N premiers matchs SkillCorner")
    parser.add_argument("--processus", type=int, default=4)
    args = parser.parse_args(argv)
    total = Accumulator()
    with ProcessPoolExecutor(max_workers=args.processus) as pool:
        for acc in pool.map(_job, jobs(args.matchs)):  # ordre des matchs fixe : fusion déterministe
            total.merge(acc)
    text = json.dumps(report(total), ensure_ascii=False, indent=1, sort_keys=True)
    if args.sortie:
        with open(args.sortie, "w", encoding="utf-8") as stream:
            stream.write(text + "\n")
        print(f"{args.sortie} : sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
