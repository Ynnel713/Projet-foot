"""Génère un JSON de clips (`engine.narrative_player.clips_to_json`) et
l'injecte dans une copie de `render/canvas.html` (mode "player", Tâche 4) --
produit `render/canvas_player_preview.html`, ouvrable via le serveur statique
`canvas-static` (`.claude/launch.json`, voir docs/next_step_canvas.md pour la
commande exacte).

Match choisi déterministe (seed fixe) mais RETIRÉ jusqu'à obtenir un profil
utile pour la démonstration/les captures (Tâche 4.7, puis Tâche 6 de la
consolidation du 23/09/2026) : le 1er clip retenu une occasion (score 0-0
tout du long), au moins 2 buts parmi les 3 suivants (pour que le score
change deux fois sur les 4 premiers clips), ET au moins un clip avec un
`interval_events` non vide (carton/remplacement réel, Tâche 1 de la
consolidation -- pour la capture `player_interval_events.png`). Ce n'est pas
un tirage caché -- la seed retenue est imprimée par le script.

Usage :
    uv run python scripts/render_player_preview.py [--seed N] [--max-occasions N]
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import numpy as np  # noqa: E402

from ligue1sim.clubs import Club  # noqa: E402
from ligue1sim.lineup import pick_best_formation  # noqa: E402
from ligue1sim.players import Player  # noqa: E402
from ligue1sim.schedule import Match  # noqa: E402
from ligue1sim.simulation import LeagueContext, simulate_match  # noqa: E402

from narrative import BUT, build_timeline, match_result_from  # noqa: E402
from narrative_player import build_clips, clips_to_json  # noqa: E402

_HOME_CLUB = "Paris Saint-Germain"
_AWAY_CLUB = "AS Monaco"
_DEFAULT_SEED = 1
_MAX_SEED_ATTEMPTS = 500
_DEFAULT_MAX_OCCASIONS = 4

_CANVAS_HTML = Path(__file__).resolve().parent.parent / "render" / "canvas.html"
_OUTPUT_HTML = Path(__file__).resolve().parent.parent / "render" / "canvas_player_preview.html"
_PLACEHOLDER = "/*__SEQUENCE_JSON__*/null"


def _player(poste: str, note: float, name: str) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST")


def _squad(club_name: str, note: float) -> list[Player]:
    squad = [_player("GK", note, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("DC", note, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_player("LB", note, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("RB", note, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("MC", note, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_player("MOC", note, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("AG", note, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("AD", note, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("BU", note, f"{club_name}_cf{i}") for i in range(4)]
    return squad


def _useful_profile(clips, max_occasions: int) -> bool:
    if len(clips) < min(3, max_occasions):
        return False
    if clips[0].issue == "but":
        return False
    n_goals_early = sum(1 for c in clips[: min(3, len(clips))] if c.issue == "but")
    if n_goals_early < 2:
        return False
    return any(c.interval_events for c in clips)


def find_timeline(seed: int, max_occasions: int):
    for attempt in range(_MAX_SEED_ATTEMPTS):
        random.seed(seed + attempt)
        np.random.seed(seed + attempt)

        home = Club(name=_HOME_CLUB, players=_squad("home", 80.0))
        away = Club(name=_AWAY_CLUB, players=_squad("away", 70.0))
        context = LeagueContext.from_clubs([home, away])
        home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)

        home_goals, away_goals, events = simulate_match(home, away, context)
        if events is None:
            continue
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        result = match_result_from(match, events, home_lineup, away_lineup, date=str(seed + attempt))
        timeline = build_timeline(result)
        clips = build_clips(timeline, max_occasions=max_occasions)
        if _useful_profile(clips, max_occasions):
            print(f"seed retenue : {seed + attempt} (essai {attempt + 1}/{_MAX_SEED_ATTEMPTS})")
            return timeline, clips
    raise SystemExit(f"aucune seed utile trouvee en {_MAX_SEED_ATTEMPTS} essais a partir de {seed}")


def run(*, seed: int, max_occasions: int) -> Path:
    timeline, clips = find_timeline(seed, max_occasions)
    for i, c in enumerate(clips):
        print(f"  [{i}] {c.minute}' {c.gabarit} ({c.equipe}) -- {c.issue} -- score_after={c.score_after}")
        for item in c.interval_events:
            print(f"        interval_event: {item}")

    payload = clips_to_json(clips, timeline)
    html = _CANVAS_HTML.read_text(encoding="utf-8")
    if _PLACEHOLDER not in html:
        raise ValueError(f"placeholder {_PLACEHOLDER!r} introuvable dans {_CANVAS_HTML} -- injection impossible")
    html = html.replace(_PLACEHOLDER, payload)
    _OUTPUT_HTML.write_text(html, encoding="utf-8")
    return _OUTPUT_HTML


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=_DEFAULT_SEED)
    parser.add_argument("--max-occasions", type=int, default=_DEFAULT_MAX_OCCASIONS)
    args = parser.parse_args()

    output_path = run(seed=args.seed, max_occasions=args.max_occasions)
    print(f"HTML autonome genere (mode player) : {output_path}")
