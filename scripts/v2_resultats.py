"""Distribution des résultats du moteur V2 selon l'écart de niveau (ticket v2-realisme/27d) : mesure seulement, aucun
réglage (les écarts vont à la calibration, ticket v2-collectif/22c).

Plan d'expérience validé par le propriétaire le 22/11/2026 :
- note d'équipe : moyenne de la note du joueur (« Moyenne FM », issue des attributs FM pondérés par poste) sur le onze
  choisi par `pick_best_formation` ;
- trois niveaux d'écart entre clubs de Ligue 1 : équipes égales (écart < 1,5), écart moyen (4 à 7), gros écart (10 et
  plus) ; toutes les affiches du niveau, jouées tour à tour ;
- le match d'indice k d'un niveau joue l'affiche k // 2, camps inversés quand k est impair (le moteur V2 ne modélise
  pas d'avantage du terrain : « home » ne fixe que le camp défendu, le coup d'envoi est tiré au sort), graine
  `AUDIT_SEED + premier indice du niveau + k`, comme le banc (`scripts/measure_v2.run`) ;
- rapporté du point de vue du favori (note la plus haute) : victoires, nuls, défaites (intervalle de Wilson à 95 %),
  distribution des scores, part des nuls attendue par un tirage de Poisson au nombre de buts mesuré, et part des
  matchs où l'équipe menée d'un but à la 70e minute de jeu ne perd pas.

Usage :
  uv run python -m scripts.v2_resultats 100 --processus 4 --json resultats.json [--niveaux egal,moyen,gros]
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import statistics
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match
from scripts.graines_validation import check_series

AUDIT_SEED = 20260923
Z_95 = 1.96
SEVENTY_MINUTES = 70.0
REGULAR_HALF_MIN = 45.0

# Niveaux d'écart de note du onze (bornes validées par le propriétaire, 22/11/2026) : [bas, haut[
LEVELS: dict[str, tuple[float, float]] = {"egal": (0.0, 1.5), "moyen": (4.0, 7.0), "gros": (10.0, math.inf)}
# Premier indice de graine de chaque niveau : hors des séries déjà jouées (0 à environ 2 120) et de la réserve de
# validation (100 000 à 199 999, ticket v2-realisme/18b).
LEVEL_START: dict[str, int] = {"egal": 30_000, "moyen": 31_000, "gros": 32_000}

# Repères réels (indicateurs, pas objectifs ; validés par le propriétaire le 22/11/2026)
REAL_REFERENCES = {
    "nuls, équipes égales, terrain neutre": "27,1 % (36,5 / 27,1 / 36,5) : modèle Glicko calé sur la Premier League, "
                                            "arXiv 2611.15378, table 10",
    "nuls, tous matchs": "25 à 27 % : 10 saisons, 10 ligues, avec et sans public (Wunderlich, Scientific American)",
    "victoire du favori, tous écarts": "environ 6 sur 10 : Premier League, favori des cotes (Goal), source faible",
    "victoire du favori, gros écart": "non trouvé",
    "menée d'un but à la 70e qui ne perd pas": "non trouvé (le plus proche : 17 % des équipes ayant mené d'un but, à "
                                               "n'importe quel moment, perdent ; Premier League, Sky Sports)",
}


@dataclass(frozen=True)
class Affiche:
    favourite: str
    outsider: str
    favourite_note: float
    outsider_note: float

    @property
    def gap(self) -> float:
        return self.favourite_note - self.outsider_note


def team_note(club) -> float:
    """Note d'équipe : moyenne de la note du joueur sur le onze de `pick_best_formation`."""
    return statistics.fmean(p.note for p in pick_best_formation(club).players)


def affiches(clubs, level: str) -> list[Affiche]:
    """Affiches du niveau, ordre stable (écart puis noms) ; le favori est l'équipe à la note la plus haute."""
    low, high = LEVELS[level]
    notes = {c.name: team_note(c) for c in clubs}
    out = []
    for a, b in itertools.combinations(sorted(notes), 2):
        fav, out_ = (a, b) if notes[a] >= notes[b] else (b, a)
        affiche = Affiche(fav, out_, notes[fav], notes[out_])
        if low <= affiche.gap < high:
            out.append(affiche)
    return sorted(out, key=lambda x: (round(x.gap, 9), x.favourite, x.outsider))


def score_at(goals, minute: float) -> tuple[int, int]:
    """Score (domicile, extérieur) avant `minute` (horloge du moteur)."""
    home = sum(1 for g in goals if g.minute < minute and g.team == "home")
    away = sum(1 for g in goals if g.minute < minute and g.team == "away")
    return home, away


def seventy_minute(second_half_start: float | None) -> float:
    """Horloge du moteur à la 70e minute de jeu : 25 min après le coup d'envoi de la 2e période."""
    if second_half_start is None:
        return SEVENTY_MINUTES
    return second_half_start + SEVENTY_MINUTES - REGULAR_HALF_MIN


def match_record(trace, favourite_side: str) -> dict:
    """Résumé d'un match du point de vue du favori."""
    fav_goals = trace.home_goals if favourite_side == "home" else trace.away_goals
    out_goals = trace.away_goals if favourite_side == "home" else trace.home_goals
    h70, a70 = score_at(trace.goals, seventy_minute(trace.second_half_start_minute))
    fav70, out70 = (h70, a70) if favourite_side == "home" else (a70, h70)
    trailing = None  # équipe menée d'un but à la 70e (« favori », « outsider » ou None)
    if fav70 - out70 == 1:
        trailing = "outsider"
    elif out70 - fav70 == 1:
        trailing = "favori"
    if trailing is None:
        comeback = None
    elif trailing == "favori":
        comeback = fav_goals >= out_goals
    else:
        comeback = out_goals >= fav_goals
    return {"favori": fav_goals, "outsider": out_goals, "70e": [fav70, out70], "menée à la 70e": trailing,
            "menée ne perd pas": comeback}


def _one_match(job: tuple[str, int, Affiche, float]) -> dict:
    level, k, affiche, duration = job
    clubs = {c.name: c for c in load_clubs(CLUBS_PATH, "Ligue 1")}
    favourite_side = "home" if k % 2 == 0 else "away"
    home, away = ((affiche.favourite, affiche.outsider) if favourite_side == "home"
                  else (affiche.outsider, affiche.favourite))
    index = LEVEL_START[level] + k
    random.seed(AUDIT_SEED + index)
    started = time.perf_counter()
    trace = match.simulate_match(clubs[home], clubs[away], duration_minutes=duration)
    record = match_record(trace, favourite_side)
    record.update({"niveau": level, "k": k, "graine": index, "domicile": home, "extérieur": away,
                   "favori nom": affiche.favourite, "outsider nom": affiche.outsider, "écart": round(affiche.gap, 3),
                   "secondes": time.perf_counter() - started})
    return record


def wilson(successes: int, n: int) -> tuple[float, float]:
    """Intervalle de Wilson à 95 % d'une proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + Z_95 ** 2 / n
    centre = (p + Z_95 ** 2 / (2 * n)) / denom
    half = Z_95 * math.sqrt(p * (1 - p) / n + Z_95 ** 2 / (4 * n * n)) / denom
    return (centre - half, centre + half)


def poisson_draw(lam_a: float, lam_b: float, k_max: int = 40) -> float:
    """Probabilité d'un nul pour deux nombres de buts de Poisson indépendants."""
    pa = [math.exp(-lam_a) * lam_a ** k / math.factorial(k) for k in range(k_max)]
    pb = [math.exp(-lam_b) * lam_b ** k / math.factorial(k) for k in range(k_max)]
    return sum(x * y for x, y in zip(pa, pb))


def level_report(records: list[dict]) -> dict:
    n = len(records)
    wins = sum(r["favori"] > r["outsider"] for r in records)
    draws = sum(r["favori"] == r["outsider"] for r in records)
    losses = n - wins - draws
    lam_f = statistics.fmean(r["favori"] for r in records)
    lam_o = statistics.fmean(r["outsider"] for r in records)
    trailing = [r for r in records if r["menée à la 70e"] is not None]
    held = sum(bool(r["menée ne perd pas"]) for r in trailing)
    scores = Counter(f"{r['favori']}-{r['outsider']}" for r in records)
    margins = Counter(r["favori"] - r["outsider"] for r in records)

    def share(count: int) -> dict:
        lo, hi = wilson(count, n)
        return {"n": count, "part": count / n, "ic95": [lo, hi]}

    lo, hi = wilson(held, len(trailing))
    return {
        "matchs": n,
        "affiches distinctes": len({(r["favori nom"], r["outsider nom"]) for r in records}),
        "écart moyen de note": statistics.fmean(r["écart"] for r in records),
        "victoires du favori": share(wins),
        "nuls": share(draws),
        "victoires de l'outsider": share(losses),
        "buts par match": lam_f + lam_o,
        "buts du favori par match": lam_f,
        "buts de l'outsider par match": lam_o,
        "nuls attendus (Poisson au nombre de buts mesuré)": poisson_draw(lam_f, lam_o),
        "menée d'un but à la 70e": {"matchs": len(trailing), "ne perd pas": held,
                                    "part": held / len(trailing) if trailing else float("nan"), "ic95": [lo, hi],
                                    "dont favori mené": sum(r["menée à la 70e"] == "favori" for r in trailing)},
        "écart de buts (favori - outsider)": dict(sorted(margins.items())),
        "scores (favori-outsider), les plus fréquents": dict(scores.most_common(12)),
    }


def fingerprint(records: list[dict]) -> str:
    """Empreinte sha256 des résultats (sans les durées), pour vérifier le déterminisme à graine fixée."""
    stable = [{k: v for k, v in r.items() if k != "secondes"} for r in records]
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def run_series(n_per_level: int, levels: list[str], processes: int = 1, duration: float = 90.0,
               progress_path: str | None = None) -> dict:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    jobs = []
    for level in levels:
        check_series(LEVEL_START[level], n_per_level)  # jamais dans la réserve de validation (18b)
        pairs = affiches(clubs, level)
        jobs += [(level, k, pairs[(k // 2) % len(pairs)], duration) for k in range(n_per_level)]
    # Un processus neuf par match : le cache sans borne de `v2engine.movement._lerp` grossit d'environ 200 Mo par match
    # dans un même processus (mesuré le 22/11/2026) ; 25 matchs par processus ont saturé la mémoire.
    pool = ProcessPoolExecutor(max_workers=processes, max_tasks_per_child=1) if processes > 1 else None
    records = []
    try:
        for record in (pool.map(_one_match, jobs) if pool else map(_one_match, jobs)):
            records.append(record)
            if progress_path:  # au fil de l'eau : une série interrompue garde ses matchs joués
                with open(progress_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        if pool:
            pool.shutdown()
    return {
        "paramètres": {"matchs par niveau": n_per_level, "niveaux": {lv: list(LEVELS[lv]) for lv in levels},
                       "durée (min)": duration, "graine d'audit": AUDIT_SEED},
        "repères réels": REAL_REFERENCES,
        "niveaux": {lv: level_report([r for r in records if r["niveau"] == lv]) for lv in levels},
        "empreinte": fingerprint(records),
        "secondes par match": statistics.fmean(r["secondes"] for r in records),
        "matchs": records,
    }


# Repères des bookmakers (ajout du 22/11/2026, accord du propriétaire : les notes du onze reflètent la valeur réelle des
# équipes). Cotes de clôture moyennes du marché (colonnes AvgCH, AvgCD, AvgCA), Ligue 1 2026/27, football-data.co.uk,
# copie dans `.scratch/v2-realisme/mesures/27d-cotes-F1-2627.csv`.
ODDS_NAMES = {
    "Paris SG": "Paris Saint-Germain", "Nice": "OGC Nice", "Lille": "LOSC Lille", "Lens": "RC Lens",
    "Marseille": "Olympique Marseille", "Lyon": "Olympique Lyon", "Paris FC": "Paris FC", "Monaco": "AS Monaco",
    "Rennes": "Stade Rennais FC", "Brest": "Stade Brestois 29", "Strasbourg": "RC Strasbourg Alsace",
    "Angers": "Angers SCO", "Auxerre": "AJ Auxerre", "Lorient": "FC Lorient", "Toulouse": "FC Toulouse",
    "Le Havre": "Le Havre AC", "Troyes": "ESTAC Troyes", "Le Mans": "Le Mans FC",
}


def implied(home_odds: float, draw_odds: float, away_odds: float) -> tuple[float, float, float]:
    """Probabilités implicites, marge du bookmaker retirée par normalisation."""
    raw = (1 / home_odds, 1 / draw_odds, 1 / away_odds)
    total = sum(raw)
    return tuple(r / total for r in raw)


def market_references(rows: list[dict], notes: dict[str, float]) -> dict:
    """Par niveau d'écart : probabilités moyennes du marché vues du favori (note la plus haute), calculées à part quand
    le favori reçoit et quand il se déplace, puis moyennées à poids égaux (avantage du terrain neutralisé, le V2 n'en
    modélise pas). Aussi : résultats réels de ces matchs (indicatifs, échantillon court)."""
    by_level: dict[str, dict[str, list]] = {lv: {"home": [], "away": [], "réel": []} for lv in LEVELS}
    for row in rows:
        home, away = ODDS_NAMES[row["HomeTeam"]], ODDS_NAMES[row["AwayTeam"]]
        gap = abs(notes[home] - notes[away])
        level = next((lv for lv, (lo, hi) in LEVELS.items() if lo <= gap < hi), None)
        if level is None:
            continue
        p_home, p_draw, p_away = implied(float(row["AvgCH"]), float(row["AvgCD"]), float(row["AvgCA"]))
        fav_home = notes[home] >= notes[away]
        side = "home" if fav_home else "away"
        by_level[level][side].append((p_home, p_draw, p_away) if fav_home else (p_away, p_draw, p_home))
        result = {"H": "home", "D": "draw", "A": "away"}[row["FTR"]]
        by_level[level]["réel"].append("nul" if result == "draw" else ("favori" if (result == "home") == fav_home else "outsider"))
    out = {}
    for level, data in by_level.items():
        sides = [data[s] for s in ("home", "away") if data[s]]
        if not sides:
            out[level] = {"matchs": 0}
            continue
        mean = [statistics.fmean(statistics.fmean(p[i] for p in s) for s in sides) for i in range(3)]
        real = Counter(data["réel"])
        out[level] = {"matchs": len(data["réel"]), "favori à domicile": len(data["home"]),
                      "favori à l'extérieur": len(data["away"]),
                      "victoire du favori": mean[0], "nul": mean[1], "victoire de l'outsider": mean[2],
                      "résultats réels (favori, nul, outsider)": [real["favori"], real["nul"], real["outsider"]]}
    return out


def market_from_csv(path: str) -> dict:
    import csv
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    notes = {c.name: team_note(c) for c in clubs}
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return market_references(rows, notes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=100, help="matchs par niveau (pair : affiche jouée deux fois)")
    parser.add_argument("--niveaux", default="egal,moyen,gros")
    parser.add_argument("--processus", type=int, default=1)
    parser.add_argument("--duree", type=float, default=90.0, help="durée d'un match (min), pour les essais")
    parser.add_argument("--json", default=None)
    parser.add_argument("--cotes", default=None, help="CSV football-data.co.uk : repères du marché par niveau, sans simuler")
    args = parser.parse_args(argv)
    if args.cotes:
        print(json.dumps(market_from_csv(args.cotes), ensure_ascii=False, indent=2))
        return
    levels = [lv.strip() for lv in args.niveaux.split(",") if lv.strip()]
    unknown = [lv for lv in levels if lv not in LEVELS]
    if unknown:
        parser.error(f"niveau inconnu : {', '.join(unknown)} (connus : {', '.join(LEVELS)})")
    result = run_series(args.matches, levels, args.processus, args.duree,
                        progress_path=f"{args.json}.partiel.jsonl" if args.json else None)
    print(json.dumps({k: v for k, v in result.items() if k != "matchs"}, ensure_ascii=False, indent=2))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
