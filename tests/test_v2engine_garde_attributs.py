"""Test de garde des attributs (ticket v2-realisme/17d) : un attribut que `docs/CARTE_ATTRIBUTS_V2.md` annonce comme
agissant sur le jeu est lu par le moteur (`v2engine/`) et change l'issue d'une scène jouée avec la fabrique du 01f.

Règle de lecture de la carte (colonne « État ») : un attribut est annoncé **avec effet** sauf si son état commence par
« à créer » ou « non branché » (« branché », « agit sur l'issue… », « lu hors de son rayon… » sont donc avec effet).

Effet : la même scène, à la même graine, est jouée avec l'attribut à 11 puis à 99 sur tous les joueurs ; elle doit
diverger (empreinte exacte des joueurs et du ballon, `scenes.fingerprint`). Les graines 1 à `max_seeds` sont essayées
dans l'ordre : beaucoup d'attributs agissent par un tirage (tacle, arrêt), et une seule graine pourrait ne pas le
toucher. Le sens et la taille de l'effet ne sont pas vérifiés ici : ils relèvent des tests de chaque ticket.
"""

from __future__ import annotations

import ast
import pathlib
import re
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH
from tests.scenes import Scene, player, run, seed_scene, with_attribute
from v2engine.formation import initial_positions
from v2engine.match import _build_players
from v2engine.movement import PlayerState

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARTE = ROOT / "docs" / "CARTE_ATTRIBUTS_V2.md"
ENGINE = ROOT / "v2engine"
# Lecture d'une note par le moteur (mêmes lecteurs que tests/test_v2engine_rayon_attributs.py)
READERS = {"player_attribute", "effective_rating", "intrinsic_rating"}
WITHOUT_EFFECT = ("à créer", "non branché")
LOW, HIGH = 11, 99


# --- carte -------------------------------------------------------------------------------------------------------

def carte_states(text: str) -> dict[str, str]:
    """Attribut -> état (dernière colonne) des lignes `| **Nom** ...` de la carte ; `\\|` n'est pas un séparateur."""
    states = {}
    for line in text.splitlines():
        if not line.startswith("| **"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]
        states[re.match(r"\*\*(.+?)\*\*", cells[0]).group(1)] = cells[-1]
    return states


def announced_with_effect(states: dict[str, str]) -> set[str]:
    return {name for name, state in states.items() if not state.lower().startswith(WITHOUT_EFFECT)}


def engine_reads(engine: pathlib.Path = ENGINE) -> set[str]:
    """Noms littéraux lus par `player_attribute`, `effective_rating` ou `intrinsic_rating` dans le moteur (ast)."""
    names = set()
    for path in sorted(engine.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) in READERS:
                arg = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "name"), None)
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    names.add(arg.value)
    return names


def unread(announced: set[str], reads: set[str]) -> set[str]:
    return announced - reads


def read_but_announced_without_effect(states: dict[str, str], reads: set[str]) -> set[str]:
    return {name for name in reads if name in states and name not in announced_with_effect(states)}


STATES = carte_states(CARTE.read_text(encoding="utf-8"))
ANNOUNCED = sorted(announced_with_effect(STATES))


def test_the_carte_is_read_with_its_announced_attributes() -> None:
    # 52 lignes d'attributs le 14/11/2026, dont 27 annoncées avec effet (23 « branché », Dribbling, Finishing,
    # Balance et Handling)
    assert len(STATES) >= 50
    assert {"Pace", "Dribbling", "Finishing", "Balance", "Handling"} <= set(ANNOUNCED)
    assert {"Natural Fitness", "Heading", "Jumping Reach"}.isdisjoint(ANNOUNCED)


def test_every_attribute_announced_with_effect_is_read_by_the_engine() -> None:
    missing = unread(set(ANNOUNCED), engine_reads())
    assert not missing, f"annoncé avec effet dans la carte, jamais lu dans v2engine/ : {sorted(missing)}"


def test_no_attribute_announced_without_effect_is_read_by_the_engine() -> None:
    stale = read_but_announced_without_effect(STATES, engine_reads())
    assert not stale, f"lu dans v2engine/ mais annoncé « à créer » ou « non branché » dans la carte : {sorted(stale)}"


def test_the_reading_guard_fails_on_a_fake_attribute() -> None:
    fake = carte_states("| **Bidon** | rayon | rien | nulle part | aucun | branché (`nulle_part.py`) |\n"
                        "| **Fantôme** | rayon | à créer (`x`) |")
    assert announced_with_effect(fake) == {"Bidon"}
    assert unread(announced_with_effect(fake), engine_reads()) == {"Bidon"}
    assert read_but_announced_without_effect({"Pace": "à créer"}, engine_reads()) == {"Pace"}


# --- scènes ------------------------------------------------------------------------------------------------------

def mini_match() -> tuple[list[PlayerState], str]:
    """Deux onze réels de Ligue 1 à leurs places de coup d'envoi, ballon à un milieu de l'équipe à domicile."""
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    home, away = pick_best_formation(clubs[0]), pick_best_formation(clubs[1])
    players = (_build_players(home, "home", initial_positions(home, attacking_right=True))
               + _build_players(away, "away", initial_positions(away, attacking_right=False)))
    return players, next(p.name for p in players if p.team == "home" and p.poste in ("MC", "MDC", "MOC"))


def duel() -> tuple[list[PlayerState], str]:
    """Porteur au contact d'un défenseur prêt à tacler (Aggression 99 : tentatives fréquentes)."""
    return [player("Porteur", "home", 60, 34, "MC", Aggression=99), player("Def", "away", 61.0, 34, "DC", Aggression=99),
            player("Gardien", "away", 104, 34, "GK")], "Porteur"


def tir() -> tuple[list[PlayerState], str]:
    """Tireur dans la surface face au gardien, un défenseur au contact (pression)."""
    return [player("Tireur", "home", 92, 34, "BU"), player("Gardien", "away", 104, 34, "GK"),
            player("Def", "away", 93.2, 35, "DC")], "Tireur"


def tir_de_loin() -> tuple[list[PlayerState], str]:
    """Tireur à 27 m du but, hors de la surface, un défenseur au contact : Long Shots."""
    return [player("Tireur", "home", 78, 34, "MOC"), player("Gardien", "away", 104, 34, "GK"),
            player("Def", "away", 79.2, 35, "DC")], "Tireur"


@dataclass(frozen=True)
class Plan:
    build: Callable[[], tuple[list[PlayerState], str]] = mini_match
    seconds: float = 60.0
    max_seeds: int = 3


# Attribut -> scène où il agit. Par défaut le mini-match de 60 s. Les attributs de duel n'agissent qu'au tacle (environ
# 0,05 tentative par seconde et par défenseur au contact) et ceux du gardien qu'à l'arrêt : scènes courtes, graines
# nombreuses ; Finishing ne joue que sur un tir dans la surface, rare en 60 s de mini-match.
PLANS = {
    "Strength": Plan(duel, 3.0, 300), "Balance": Plan(duel, 3.0, 300), "Tackling": Plan(duel, 3.0, 300),
    "Reflexes": Plan(tir, 3.0, 300), "One on Ones": Plan(tir, 3.0, 300), "Handling": Plan(tir, 3.0, 300),
    "Finishing": Plan(tir, 3.0, 300),  # dans la surface seulement
    # hors de la surface : rare dans le mini-match depuis la courbe en S du ticket v2-realisme/24 (fusion du 14/11/2026)
    "Long Shots": Plan(tir_de_loin, 3.0, 300),
}


def _play(players: list[PlayerState], holder: str, seconds: float, seed: int,
          reference: list[str] | None = None) -> list[str]:
    """Empreintes de chaque pas ; avec `reference`, s'arrête au premier pas qui en diffère."""
    scene = Scene.full(players, holder=holder)
    seed_scene(seed)
    until = None if reference is None else (lambda s: s.log[-1] != reference[len(s.log) - 1])
    run(scene, seconds, until=until)
    return scene.log


def first_divergence(attribute: str, plan: Plan) -> tuple[int, int] | None:
    """(graine, pas) de la première divergence entre l'attribut à 11 et à 99, ou None sur toutes les graines."""
    players, holder = plan.build()
    low, high = with_attribute(players, attribute, LOW), with_attribute(players, attribute, HIGH)
    for seed in range(1, plan.max_seeds + 1):
        reference = _play(low, holder, plan.seconds, seed)
        other = _play(high, holder, plan.seconds, seed, reference)
        step = next((i for i, (a, b) in enumerate(zip(reference, other)) if a != b), None)
        if step is not None:
            return seed, step
    return None


@pytest.mark.parametrize("attribute", ANNOUNCED)
def test_every_attribute_announced_with_effect_changes_a_scene(attribute: str) -> None:
    plan = PLANS.get(attribute, Plan())
    hit = first_divergence(attribute, plan)
    assert hit is not None, (f"{attribute} : aucune divergence entre {LOW} et {HIGH} sur {plan.max_seeds} graines "
                             f"({plan.seconds} s, scène {plan.build.__name__}) : lu sans effet sur le jeu ?")
    seed, step = hit
    # déterminisme : jusqu'au pas de la divergence, chaque profil rejoué à la même graine redonne les mêmes empreintes
    players, holder = plan.build()
    seconds = (step + 1) * Scene.dt
    for value in (LOW, HIGH):
        profile = with_attribute(players, attribute, value)
        assert _play(profile, holder, seconds, seed) == _play(profile, holder, seconds, seed)


def test_the_effect_guard_fails_on_a_fake_attribute() -> None:
    assert first_divergence("Bidon", Plan(seconds=5.0, max_seeds=2)) is None
    assert first_divergence("Bidon", Plan(duel, 3.0, 2)) is None
