"""Table des courbes d'attributs du moteur V2 (ticket v2-realisme/24) : pour chaque fonction du moteur qui lit un
attribut, sa valeur à 50, 60, 70, 80, 90 (et 99), sans match. Sert d'avant / après au changement de forme de la courbe
partagée (`attributes._s_curve`, ancienne `_cubic_curve`).

Usage : uv run python -m scripts.attribute_curves [--json chemin]

Chaque ligne appelle la vraie fonction du moteur sur une scène fixe (joueur seul, autres notes à 60) : la table suit le
moteur tel qu'il est, sans recopier ses constantes. Colonnes d'écart : part de l'écart 50 -> 99 prise entre 60 et 70, et
entre 70 et 80 (objectif du ticket 24, validé le 14/11/2026 : au moins 1/4 et 1/3)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable

import v2engine.anticipation as anticipation
import v2engine.bloc as bloc
import v2engine.decision as decision
import v2engine.defense as defense
import v2engine.duel as duel
import v2engine.off_ball as off_ball
import v2engine.offside as offside
import v2engine.possession as possession
import v2engine.shooting as shooting
from v2engine.attributes import duel_probability
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.movement import PlayerState, max_speed_mps

NOTES = (50, 60, 70, 80, 90, 99)
NEUTRAL = 60
_PHYSICAL = {"Pace": "pace", "Acceleration": "acceleration", "Stamina": "stamina"}
_GOAL_HOME = Vec2(PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)  # domicile attaque vers x = longueur (D-V03)


def player(attrs: dict[str, float] | None = None, x: float = 50.0, y: float = PITCH_WIDTH_M / 2.0, team: str = "home",
           poste: str = "MC") -> PlayerState:
    """Joueur seul, toutes notes à 60 sauf `attrs`."""
    attrs = dict(attrs or {})
    physical = {field: attrs.pop(name, NEUTRAL) for name, field in _PHYSICAL.items()}
    return PlayerState(name="J", team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0),
                       home_target=Vec2(x, y), attributes=attrs, **physical)


def _pass_accuracy(length_m: float) -> Callable[[float], float]:
    """Passe de `length_m` sans adversaire (difficulté : 20 m -> 28, 35 m -> 55, 45 m -> 73)."""
    def f(note: float) -> float:
        return possession.pass_accuracy_probability(player({"Passing": note}), player(x=50.0 + length_m), [])
    return f


def _control(ball_speed_mps: float) -> Callable[[float], float]:
    """Contrôle d'un ballon arrivant à `ball_speed_mps`, sans adversaire (6 m/s -> difficulté 10, 30 m/s -> 34)."""
    def f(note: float) -> float:
        p = player({"First Touch": note})
        difficulty = possession.control_difficulty(p, Vec2(ball_speed_mps, 0.0), [])
        # mêmes réglages que `possession.attempt_control` (tirage aléatoire autour de cette probabilité)
        return duel_probability(note, difficulty, **possession._SUCCESS)
    return f


def _shot_factor(attr: str, x: float) -> Callable[[float], float]:
    """Chance de but rapportée à celle d'un tireur à 60 (sans gardien, sans pression) : facteur d'exécution."""
    def f(note: float) -> float:
        ref = shooting.shot_probability(player(x=x), _GOAL_HOME, None, [])
        return shooting.shot_probability(player({attr: note}, x=x), _GOAL_HOME, None, []) / ref
    return f


def _keeper_factor(note: float) -> float:
    """Chance de but face à un gardien noté `note` (Reflexes, One on Ones, Handling) rapportée à un gardien à 60."""
    def keeper(n: float) -> PlayerState:
        return player({"Reflexes": n, "One on Ones": n, "Handling": n}, x=PITCH_LENGTH_M - 1.0, team="away",
                      poste="GB")
    shooter = player(x=PITCH_LENGTH_M - 14.0)
    return (shooting.shot_probability(shooter, _GOAL_HOME, keeper(note), [])
            / shooting.shot_probability(shooter, _GOAL_HOME, keeper(NEUTRAL), []))


def _with(attr: str, fn: Callable[[PlayerState], float]) -> Callable[[float], float]:
    return lambda note: fn(player({attr: note}))


# (attribut, mécanisme, forme, fonction de la note) ; forme : « courbe » si la valeur passe par
# `success_probability` / `duel_probability`, « linéaire » sinon (référence, hors objectif du ticket).
MECHANISMS: list[tuple[str, str, str, Callable[[float], float]]] = [
    ("Passing", "passe précise, 20 m sans pression (difficulté 28)", "courbe", _pass_accuracy(20.0)),
    ("Passing", "passe précise, 35 m sans pression (difficulté 55)", "courbe", _pass_accuracy(35.0)),
    ("Passing", "passe précise, 45 m sans pression (difficulté 73)", "courbe", _pass_accuracy(45.0)),
    ("Passing", "dosage de la passe", "courbe", _with("Passing", possession.dosage_quality)),
    ("First Touch", "contrôle réussi, ballon idéal à 6 m/s (difficulté 10)", "courbe", _control(6.0)),
    ("First Touch", "contrôle réussi, ballon à 30 m/s (difficulté 34)", "courbe", _control(30.0)),
    ("First Touch", "contrôle orienté", "linéaire", _with("First Touch", possession.oriented_control_probability)),
    ("Tackling", "tacle gagné, porteur à 60", "courbe",
     lambda n: duel.tackle_success_probability(player({"Tackling": n}), player())),
    ("Strength", "tacle subi gagné par le porteur, tacleur à 60 (Balance 60)", "courbe",
     lambda n: 1.0 - duel.tackle_success_probability(player(), player({"Strength": n}))),
    ("Balance", "tacle subi gagné par le porteur, tacleur à 60 (Strength 60)", "courbe",
     lambda n: 1.0 - duel.tackle_success_probability(player(), player({"Balance": n}))),
    ("Dribbling", "garder le ballon au contact", "courbe", _with("Dribbling", lambda p: decision.keep_ball_probability(p, 1.0))),
    ("Dribbling", "vitesse de conduite, sans gêne (facteur)", "courbe",
     _with("Dribbling", lambda p: decision.dribble_speed_factor(p, 0.0))),
    ("Finishing", "exécution du tir dans la surface (facteur, gardien neutre)", "courbe",
     _shot_factor("Finishing", PITCH_LENGTH_M - 14.0)),
    ("Long Shots", "exécution du tir hors surface (facteur, gardien neutre)", "courbe",
     _shot_factor("Long Shots", PITCH_LENGTH_M - 25.0)),
    ("Gardien", "chance de but encaissée (facteur, Reflexes, One on Ones, Handling)", "courbe", _keeper_factor),
    ("Decisions", "meilleur choix", "courbe", decision.best_choice_probability),
    ("Vision", "portée de vision (m)", "courbe", decision.vision_range_m),
    ("Vision", "repère la passe clé", "courbe", decision.key_pass_spot_probability),
    ("Composure", "part de la pression gardée (passe, contrôle)", "courbe", _with("Composure", possession.composure_factor)),
    ("Composure", "part de la pression gardée (tir)", "courbe", _with("Composure", shooting.shot_composure_factor)),
    ("Anticipation", "délai de réaction (s)", "courbe", _with("Anticipation", anticipation.reaction_delay_s)),
    ("Anticipation", "lit la passe adverse", "courbe", anticipation.read_pass_probability),
    ("Anticipation", "avance sur le ballon libre", "courbe", anticipation.loose_ball_lead),
    ("Anticipation", "bonne ligne de course (défense)", "courbe", _with("Anticipation", defense.good_lane_probability)),
    ("Anticipation", "voit le drapeau (hors-jeu)", "courbe", offside.sees_the_flag_probability),
    ("Anticipation", "part d'anticipation du porteur", "courbe", _with("Anticipation", decision.anticipation_share)),
    ("Positioning", "erreur de placement (m)", "courbe", _with("Positioning", bloc.positioning_error_m)),
    ("Marking", "distance de marquage (m)", "courbe", _with("Marking", defense.marking_distance_m)),
    ("Teamwork", "adopte le plan de passe", "courbe", _with("Teamwork", decision.adopt_plan_probability)),
    ("Teamwork", "retard de la ligne (s)", "courbe", _with("Teamwork", bloc.line_lag_s)),
    ("Teamwork", "tolérance de ligne (m)", "courbe", _with("Teamwork", bloc.teamwork_tolerance_m)),
    ("Teamwork", "lâche son marquage", "courbe", _with("Teamwork", defense.leave_probability)),
    ("Teamwork", "suit son vis-à-vis", "courbe", _with("Teamwork", defense.follow_probability)),
    ("Off the Ball", "reste en jeu", "courbe", offside.keep_onside_probability),
    ("Off the Ball", "rayon de recherche d'espace (m)", "courbe", off_ball.search_radius_m),
    ("Off the Ball", "délai d'appel (s)", "courbe", off_ball.call_delay_s),
    ("Off the Ball", "trouve le meilleur espace", "courbe", off_ball.best_space_probability),
    ("Off the Ball", "intensité de l'appel (hors profondeur)", "courbe",
     _with("Off the Ball", lambda p: off_ball.run_intensity(p, False))),
    ("Flair", "idée de talonnade", "courbe", _with("Flair", decision.backheel_idea_probability)),
    ("Aggression", "tente le tacle (par s)", "courbe", duel.attempt_tackle_probability),
    ("Aggression", "faute sur tacle", "courbe", duel.foul_probability),
    ("Aggression", "distance d'arrêt au pressing (m)", "courbe", _with("Aggression", defense.stop_distance_m)),
    ("Work Rate", "intensité du pressing", "courbe", _with("Work Rate", defense.press_intensity)),
    ("Work Rate", "repos entre deux pressings (s)", "courbe", _with("Work Rate", defense.press_rest_s)),
    ("Work Rate", "intensité du replacement", "courbe", _with("Work Rate", lambda p: defense.replacement_intensity(p, False))),
    ("Pace", "vitesse de pointe (km/h)", "linéaire", lambda n: max_speed_mps(n) * 3.6),
]


def table() -> list[dict]:
    rows = []
    for attribute, label, shape, fn in MECHANISMS:
        values = {n: fn(float(n)) for n in NOTES}
        full = values[99] - values[50]
        rows.append({
            "attribut": attribute, "mécanisme": label, "forme": shape, "valeurs": values,
            "part 60-70": (values[70] - values[60]) / full if abs(full) > 1e-12 else 0.0,
            "part 70-80": (values[80] - values[70]) / full if abs(full) > 1e-12 else 0.0,
        })
    return rows


def duel_table(gaps: tuple[int, ...] = (0, 5, 10, 20, 30)) -> dict[int, float]:
    """Duel par défaut (`duel_probability`, réglages du tacle) selon l'écart de note entre les deux joueurs."""
    return {g: duel_probability(70.0 + g, 70.0) for g in gaps}


def markdown(rows: list[dict]) -> str:
    head = "| Attribut | Mécanisme | Forme | " + " | ".join(str(n) for n in NOTES) + " | 60→70 / 50→99 | 70→80 / 50→99 |"
    lines = [head, "|" + "---|" * (len(NOTES) + 5)]
    for r in rows:
        cells = " | ".join(f"{r['valeurs'][n]:.3f}" for n in NOTES)
        lines.append(f"| {r['attribut']} | {r['mécanisme']} | {r['forme']} | {cells} | "
                     f"{r['part 60-70']:.0%} | {r['part 70-80']:.0%} |")
    duels = duel_table()
    lines += ["", "| Écart de note (duel) | " + " | ".join(f"+{g}" for g in duels) + " |",
              "|---|" + "---|" * len(duels),
              "| Chance du plus fort | " + " | ".join(f"{v:.1%}" for v in duels.values()) + " |"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)
    rows = table()
    print(markdown(rows))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"mécanismes": rows, "duel": duel_table()}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
