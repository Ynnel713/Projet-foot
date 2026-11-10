"""Garde probabiliste (ticket v2-realisme/19c) : les notes modifient les probabilités, pas les possibilités. Un joueur
noté 11 peut réussir l'action la plus difficile, un joueur noté 99 peut rater la plus simple, et la meilleure note
fait mieux en moyenne.

Chaque résolution du moteur tire son issue par `flux.random() < p` : la garde lit donc `p`, la chance que le moteur
tire, dans la situation la plus facile et la plus difficile, aux notes 11 et 99. `p` dans [plancher, 1 - plancher]
équivaut à « réussite et échec ont chacun une fréquence au moins égale au plancher », sans bruit de tirage ; un test
par tirage vérifie l'équivalence sur un cas.

Plancher et exceptions : proposés le 10/11/2026, validés par délégation du propriétaire. Résolutions hors garde :
listées en bas, chacune renvoyée à son ticket ; ce ticket ne les corrige pas."""

from __future__ import annotations

import pytest

from tests.scenes import player, seed_scene
from v2engine import decision, duel, offside, possession, shooting
from v2engine.attributes import duel_probability
from v2engine.geometry import Vec2

FLOOR = 0.01  # réussite et échec : au moins 1 % chacun
GOAL = Vec2(105.0, 34.0)
NOTES = (11, 99)
_ALL = ("Passing", "First Touch", "Dribbling", "Tackling", "Strength", "Balance", "Finishing", "Long Shots",
        "Composure", "Aggression", "Off the Ball", "Anticipation", "Reflexes", "One on Ones", "Handling")


def _p(name: str, team: str, x: float, y: float, note: int = 60, poste: str = "MC"):
    return player(name, team, x, y, poste, **{a.replace(" ", "_"): note for a in _ALL})


def _keeper(note: int = 60):
    return _p("GK", "away", 104.5, 34.0, note, "GB")


# --- Situations -----------------------------------------------------------------------------------------------------
# facile : sans adversaire, à courte distance ; difficile : longue distance, pressé, ligne et receveur couverts.
def _pass(note: int, hard: bool) -> float:
    passer = _p("A", "home", 50, 34, note)
    if not hard:
        return possession.pass_success_probability(passer, _p("R", "home", 60, 34), [])
    opponents = [_p("D1", "away", 50.8, 34), _p("D2", "away", 65, 34), _p("D3", "away", 75, 34), _p("D4", "away", 90.8, 34)]
    return possession.pass_success_probability(passer, _p("R", "home", 90, 34), opponents)


def _control(note: int, hard: bool) -> float:
    player_ = _p("A", "home", 50, 34, note)
    ball, opponents = (Vec2(28, 0), [_p("D", "away", 50.5, 34)]) if hard else (Vec2(6, 0), [])
    # même chance que le tirage de `possession.attempt_control`
    return duel_probability(note, possession.control_difficulty(player_, ball, opponents), **possession._SUCCESS)


def _carry(note: int, hard: bool) -> float:
    return decision.keep_ball_probability(_p("A", "home", 50, 34, note), 1.0 if hard else 0.0)


def _tackle(note: int, hard: bool) -> float:
    return duel.tackle_success_probability(_p("A", "home", 50, 34, note), _p("H", "away", 50, 34, 99 if hard else 11))


def _shooter(note: int, hard: bool):
    shooter = _p("A", "home", 77, 14, note) if hard else _p("A", "home", 97, 34, note)
    return shooter, ([_p("D", "away", 77.8, 14)] if hard else [])


def _on_target(note: int, hard: bool) -> float:
    shooter, opponents = _shooter(note, hard)
    wide, under = shooting.on_target_axes(shooter, GOAL, opponents)
    return wide * under


def _goal(note: int, hard: bool) -> float:
    shooter, opponents = _shooter(note, hard)
    return shooting.physical_shot_chance(shooter, GOAL, _keeper(), opponents)


def _foul_free(note: int, hard: bool) -> float:  # réussite du tacle « propre » : Aggression haute = plus de fautes
    return 1.0 - duel.foul_probability(note)


def _keeps_onside(note: int, hard: bool) -> float:
    return offside.keep_onside_probability(note)


def _sees_flag(note: int, hard: bool) -> float:
    return offside.sees_the_flag_probability(note)


RESOLUTIONS = {
    "passe": _pass,
    "contrôle": _control,
    "conduite": _carry,
    "tacle": _tackle,
    "tir cadré": _on_target,
    "but": _goal,
    "tacle sans faute": _foul_free,
    "appel réglé sur la ligne": _keeps_onside,
    "drapeau du hors-jeu vu": _sees_flag,
}
# Note la meilleure = moins bonne issue pour ces résolutions (Aggression : plus de fautes, voulu).
INVERTED = {"tacle sans faute"}

# Exceptions assumées : (résolution, note, difficile) -> plancher propre.
EXCEPTIONS = {
    # sans adversaire à 5 m, seule une touche trop longue fait perdre : 0,5 % sur 1,5 s pour un 99, réaliste
    ("conduite", 99, False): 0.004,
    # frappe de 35 m, angle fermé, sous pression, par un 11 : 0,56 % ; chiffre réel non trouvé
    ("but", 11, True): 0.005,
}

CASES = [(name, note, hard) for name in RESOLUTIONS for note in NOTES for hard in (False, True)]


@pytest.mark.parametrize("name,note,hard", CASES, ids=[f"{n}-{note}-{'difficile' if h else 'facile'}" for n, note, h in CASES])
def test_success_and_failure_both_remain_possible(name: str, note: int, hard: bool) -> None:
    p = RESOLUTIONS[name](note, hard)
    floor = EXCEPTIONS.get((name, note, hard), FLOOR)
    assert floor <= p <= 1.0 - floor, f"{name}, note {note}, {'difficile' if hard else 'facile'} : p = {p:.4f}"


@pytest.mark.parametrize("name", RESOLUTIONS)
def test_the_better_rating_does_better_on_average(name: str) -> None:
    for hard in (False, True):
        low, high = RESOLUTIONS[name](11, hard), RESOLUTIONS[name](99, hard)
        assert (low > high) if name in INVERTED else (high > low), f"{name}, {'difficile' if hard else 'facile'}"


def test_the_harder_situation_is_harder() -> None:
    for name in ("passe", "contrôle", "conduite", "tacle", "tir cadré", "but"):
        for note in NOTES:
            if (name, note) == ("contrôle", 99):
                continue  # constat du 19c, voir le test suivant
            assert RESOLUTIONS[name](note, True) < RESOLUTIONS[name](note, False), (name, note)


def test_finding_the_hardest_control_does_not_bite_on_a_99() -> None:
    # Constat du 19c : à First Touch 99, le contrôle le plus difficile (ballon à 28 m/s, adversaire à 0,5 m) touche le
    # plafond de la courbe (0,97) comme le plus facile. La garde tient (3 % d'échec) ; l'effet de la difficulté sur un
    # très bon joueur est à revoir à la calibration (18d). Ce test échouera si la difficulté se remet à mordre.
    assert _control(99, True) == _control(99, False) == pytest.approx(0.97)


def test_the_tail_of_outcomes_exists_for_both_ratings() -> None:
    # tir : un 99 peut dévisser la frappe la plus facile, un 11 peut marquer la plus difficile
    shooter, opponents = _shooter(99, False)
    assert shooting._shank_share(shooter, GOAL, opponents) > 0.0
    assert _goal(11, True) > 0.0


def test_the_engine_draw_matches_the_guarded_probability() -> None:
    # `offside.respects_the_line` tire `DECISION.random() < keep_onside_probability(note)` : 5 000 tirages
    seed_scene(19)
    for note in NOTES:
        runner = _p("A", "home", 80, 34, note)
        share = sum(offside.respects_the_line(runner) for _ in range(5000)) / 5000
        assert abs(share - offside.keep_onside_probability(note)) < 0.02


# --- Hors garde : écarts connus, renvoyés à leur ticket (ce ticket ne les corrige pas) ---------------------------------
def test_known_gap_keeper_ratings_do_not_change_the_save() -> None:
    # L'arrêt est physique (portée du gardien, `shooting.keeper_reach_m`) et ne lit aucune note du gardien : 11 et 99
    # arrêtent pareil. Renvoyé à `v2-attributs-restants/03b`. Ce test échouera quand les notes compteront : le retirer
    # et ajouter l'arrêt à RESOLUTIONS.
    shooter, opponents = _shooter(60, False)
    low = shooting.physical_shot_chance(shooter, GOAL, _keeper(11), opponents)
    high = shooting.physical_shot_chance(shooter, GOAL, _keeper(99), opponents)
    assert low == high


def test_known_gap_the_block_reads_no_defender_rating() -> None:
    # Le contre dépend de la place du défenseur et de la précision du tireur, d'aucune note du défenseur
    # (`shooting.BLOCK_CHANCE`). Renvoyé à `v2-realisme/17b` (Bravery).
    shooter = _p("A", "home", 90, 34)
    blocks = {shooting.physical_block_probability(shooter, GOAL, [_p("D", "away", 95, 34, note)]) for note in NOTES}
    assert len(blocks) == 1


def test_known_gap_pass_dosage_and_miss_size_are_all_or_nothing() -> None:
    # Dosage de 0 (dans les pieds) à 1 (dans la course) ; ampleur d'une passe ratée indépendante de la note
    # (`possession._MISS_SHARE`). Renvoyé à `v2-realisme/23a` (erreur d'exécution continue).
    assert possession.dosage_quality(_p("A", "home", 50, 34, 11)) == 0.0
    assert possession.dosage_quality(_p("A", "home", 50, 34, 99)) == 1.0
    assert possession._MISS_SHARE == (0.10, 0.25)
