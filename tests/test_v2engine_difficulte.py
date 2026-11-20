"""Tests du moteur V2, ticket v2-socle/04 (difficulté et dosage des passes, contrôle) ; erreur d'exécution continue de la
passe, ticket v2-realisme/23a. Voir .scratch/v2-socle/issues/04-fonction-de-difficulte.md et docs/REVUE_ATTRIBUTS_V2.md."""

from __future__ import annotations

import math
import random

from v2engine import possession
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.possession import (
    BALL_FRICTION_PER_S,
    IDEAL_ARRIVAL_MPS,
    MAX_PASS_MPS,
    ON_TARGET_M,
    composure_factor,
    control_difficulty,
    dosage_gap,
    dosage_quality,
    pass_accuracy_probability,
    pass_aim,
    pass_error_sigma_rad,
    pass_speed_sigma,
    pass_success_probability,
    pass_velocity,
)


def _player(name: str = "P", team: str = "home", position: Vec2 = Vec2(30.0, 34.0),
            attributes: dict[str, int] | None = None, velocity: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste="MC", position=position, velocity=velocity,
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_pass_error_follows_the_validated_points_and_pressure() -> None:
    """Ticket v2-realisme/23a : écart-type de l'angle 6° à Passing 11, 3° à 55, 1,5° à 99, sans pression ; adversaire au
    contact, Composure moyenne (0,75) : x 1,75. La longueur n'y entre pas."""
    for note, degrees in ((11, 6.0), (55, 3.0), (99, 1.5)):
        assert math.isclose(math.degrees(pass_error_sigma_rad(_player(attributes={"Passing": note}), [])), degrees)
    passer = _player(attributes={"Passing": 55, "Composure": 62})
    contact = _player("O", team="away", position=Vec2(30.0, 34.0))
    assert math.isclose(pass_error_sigma_rad(passer, [contact]), pass_error_sigma_rad(passer, []) * 1.75)


def test_lane_opponent_and_marker_cut_physically_without_widening_the_error() -> None:
    """Tickets v2-realisme/18g et 23a (réserve A2) : l'adversaire du couloir et le marqueur du receveur n'élargissent pas
    l'écart de la passe ; l'adversaire du couloir compte dans la chance évaluée par sa chance de couper la passe (table
    mesurée : sur le trajet, de 1 à 2 m de la trajectoire, 0,25 au ticket 18j, 0,32 au 23a ; depuis le 18n, selon le temps
    du ballon jusqu'à lui : 0,59 s ici, colonne 0,45 à 0,7 s, 0,44 ; 0,47 depuis le 18o)."""
    passer = _player()
    receiver = _player("R", position=Vec2(45.0, 34.0))  # 15 m
    in_lane = _player("A", team="away", position=Vec2(37.0, 35.5))  # sur le trajet, à 1,5 m de la ligne, sans pression
    assert math.isclose(pass_accuracy_probability(passer, receiver, [in_lane]), pass_accuracy_probability(passer, receiver, []))
    assert math.isclose(pass_success_probability(passer, receiver, [in_lane]),
                        pass_success_probability(passer, receiver, []) * (1.0 - 0.47))
    receiver = _player("R", position=Vec2(38.0, 34.0))
    marker = _player("M", team="away", position=Vec2(39.0, 34.5))  # marque le receveur, hors couloir
    assert math.isclose(pass_accuracy_probability(passer, receiver, [marker]), pass_accuracy_probability(passer, receiver, []))


def test_presser_cuts_the_pass_only_when_he_stands_on_its_line() -> None:
    """Ticket v2-realisme/18g (table mesurée, près du passeur) : le presseur gêne l'exécution par la pression, où qu'il
    soit ; il ne coupe la passe que s'il est sur sa ligne (table du 18o, ballon à son niveau en 0,1 à 0,15 s : 0,87 à
    moins de 0,5 m, 0,60 de 0,5 à 1 m, 0,08 de 1 à 2 m)."""
    passer = _player()
    receiver = _player("R", position=Vec2(45.0, 34.0))  # 15 m
    beside = _player("B", team="away", position=Vec2(30.75, 35.3))  # à 1,5 m du passeur, à 1,3 m de la ligne
    in_front = _player("F", team="away", position=Vec2(31.3, 34.75))  # à 1,5 m du passeur, à 0,75 m de la ligne
    on_line = _player("L", team="away", position=Vec2(31.5, 34.2))  # à 1,5 m du passeur, à 0,2 m de la ligne
    for presser in (beside, in_front, on_line):  # même pression : même écart d'exécution
        assert math.isclose(pass_error_sigma_rad(passer, [presser]), pass_error_sigma_rad(passer, [on_line]), rel_tol=0.05)
        assert pass_error_sigma_rad(passer, [presser]) > pass_error_sigma_rad(passer, [])
    chances = {name: pass_success_probability(passer, receiver, [p]) for name, p in
               (("beside", beside), ("in_front", in_front), ("on_line", on_line))}
    assert chances["beside"] > chances["in_front"] > chances["on_line"]
    assert chances["on_line"] < 0.3 * chances["beside"]


def test_composure_halves_pressure_at_99_and_keeps_it_at_11() -> None:
    assert math.isclose(composure_factor(_player(attributes={"Composure": 99})), 0.5)
    # note médiane (62) -> valeur de base, 55 avant le ticket v2-realisme/24
    assert math.isclose(composure_factor(_player(attributes={"Composure": 62})), 0.75)
    assert math.isclose(composure_factor(_player(attributes={"Composure": 11})), 1.0)


def test_easy_pass_succeeds_for_everyone_and_hard_pass_separates_notes() -> None:
    receiver_near = _player("R", position=Vec2(38.0, 34.0))
    receiver_far = _player("R", position=Vec2(65.0, 34.0))  # 35 m : difficulté 55
    # Précision de l'exécution (ticket v2-realisme/23a : écart latéral sous 1 m à l'arrivée, loi d'écart gaussienne ; la
    # chance évaluée y ajoute coupe et passe rattrapée) : au moins 90 % à 8 m à partir de 50 en Passing ; un joueur
    # faible rate aussi des passes faciles (guide : « ballons ratés à 10 m »).
    for note in (50, 55, 90, 99):
        assert pass_accuracy_probability(_player(attributes={"Passing": note}), receiver_near, []) >= 0.90
    assert pass_accuracy_probability(_player(attributes={"Passing": 11}), receiver_near, []) < 0.80
    assert math.isclose(pass_accuracy_probability(_player(attributes={"Passing": 55}), receiver_far, []), 0.415, abs_tol=0.01)
    gap = (pass_accuracy_probability(_player(attributes={"Passing": 90}), receiver_far, [])
           - pass_accuracy_probability(_player(attributes={"Passing": 30}), receiver_far, []))
    assert gap >= 0.25
    # la chance évaluée garde le même ordre entre les notes
    assert (pass_success_probability(_player(attributes={"Passing": 90}), receiver_far, [])
            > pass_success_probability(_player(attributes={"Passing": 30}), receiver_far, []))


def test_dosage_lead_follows_passing() -> None:
    assert math.isclose(dosage_quality(_player(attributes={"Passing": 99})), 1.0)
    assert math.isclose(dosage_quality(_player(attributes={"Passing": 11})), 0.0)


def _arrival_speed(launch: float, distance: float) -> float:
    """Vitesse du ballon après `distance` m, freiné de BALL_FRICTION_PER_S par seconde (v = v0 + s.ln f)."""
    return launch + distance * math.log(BALL_FRICTION_PER_S)


def test_well_dosed_pass_arrives_at_ideal_speed_and_in_the_run(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PASSE.gauss", lambda mu, sigma: 0.0)  # ni écart d'angle, ni erreur de vitesse
    passer = _player(attributes={"Passing": 99})
    runner = _player("R", position=Vec2(55.0, 34.0), velocity=Vec2(0.0, 5.0))
    aim = pass_aim(passer, runner)
    assert aim.y > 34.0  # visée devant le receveur, dans sa course
    v = pass_velocity(passer, runner)
    assert math.isclose(_arrival_speed(v.length(), passer.position.distance_to(aim)), IDEAL_ARRIVAL_MPS, abs_tol=1e-9)


def test_pass_speed_is_capped_at_30_mps_and_never_negative(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PASSE.gauss", lambda mu, sigma: 10.0)  # erreur de vitesse extrême
    passer = _player(attributes={"Passing": 99})
    far = _player("R", position=Vec2(95.0, 34.0))  # 65 m
    assert pass_velocity(passer, far).length() <= MAX_PASS_MPS + 1e-9
    monkeypatch.setattr("v2engine.flux.PASSE.gauss", lambda mu, sigma: -10.0)
    assert pass_velocity(_player(attributes={"Passing": 11}), far).length() >= 0.0


def test_poor_dosage_spreads_the_arrival_speed(monkeypatch) -> None:
    """Ticket v2-realisme/23a : écart-type de la vitesse de départ = erreur uniforme d'avant (+/- 30 % à 11, +/- 5 % à 99)
    divisée par racine de 3."""
    receiver = _player("R", position=Vec2(50.0, 34.0))
    for note, error in ((11, 0.30 / math.sqrt(3.0)), (99, 0.05 / math.sqrt(3.0))):
        assert math.isclose(pass_speed_sigma(_player(attributes={"Passing": note})), error)
        draws = iter([0.0, 1.0])  # angle nul, puis un écart-type de vitesse
        monkeypatch.setattr("v2engine.flux.PASSE.gauss", lambda mu, sigma: next(draws) * sigma)
        launch = pass_velocity(_player(attributes={"Passing": note}), receiver).length()
        ideal = IDEAL_ARRIVAL_MPS - 20.0 * math.log(BALL_FRICTION_PER_S)
        assert math.isclose(launch, ideal * (1.0 + error))


def _lateral_errors(passer, receiver, opponents=(), draws: int = 5000) -> list[float]:
    """Écart latéral (m) du ballon à la distance du receveur, par rapport à la passe idéale, sur `draws` tirages."""
    random.seed(20260923)
    from v2engine.flux import PASSE
    PASSE.seed(20260923)
    ideal = pass_aim(passer, receiver) - passer.position
    length = passer.position.distance_to(receiver.position)
    errors = []
    for _ in range(draws):
        v = pass_velocity(passer, receiver, list(opponents))
        angle = math.atan2(ideal.x * v.y - ideal.y * v.x, ideal.x * v.x + ideal.y * v.y)
        errors.append(length * abs(math.tan(angle)))
    return errors


def test_lateral_error_grows_when_passing_drops_and_with_difficulty() -> None:
    """Ticket v2-realisme/23a (scène, 5 000 tirages) : passe de 10 et de 35 m, Passing 11 / 55 / 99, avec et sans
    pression : écart moyen au point idéal croissant quand la note baisse, avec la longueur et sous la pression ; continu
    (pas deux valeurs)."""
    passer_at = Vec2(30.0, 34.0)
    presser = _player("O", team="away", position=Vec2(30.8, 34.0))
    for length in (10.0, 35.0):
        receiver = _player("R", position=Vec2(30.0 + length, 34.0))
        means = []
        for note in (11, 55, 99):
            passer = _player(position=passer_at, attributes={"Passing": note})
            errors = _lateral_errors(passer, receiver)
            pressed = _lateral_errors(passer, receiver, [presser])
            assert sum(pressed) > sum(errors)
            assert len({round(e, 6) for e in errors}) > 4000  # continu
            means.append(sum(errors) / len(errors))
        assert means[0] > means[1] > means[2]
        if length == 35.0:
            assert means[1] > 2.5 * short_mean_55
        else:
            short_mean_55 = means[1]


def test_the_imprecise_share_follows_the_accuracy_chance_lane_or_not() -> None:
    """Tickets v2-realisme/18g et 23a : la part de passes dont l'écart latéral à l'arrivée dépasse `ON_TARGET_M` suit la
    chance de précision (même loi qu'à l'évaluation) ; avec ou sans adversaire dans la ligne, l'écart est le même
    (réserve A2), seule la réussite évaluée baisse."""
    passer = _player(attributes={"Passing": 40})
    receiver = _player("R", position=Vec2(60.0, 34.0))  # 30 m
    in_lane = [_player("A", team="away", position=Vec2(45.0, 35.0))]
    shares = []
    for opponents in ([], in_lane):
        errors = _lateral_errors(passer, receiver, opponents)
        share = sum(e > ON_TARGET_M for e in errors) / len(errors)
        assert abs(share - (1.0 - pass_accuracy_probability(passer, receiver, opponents))) < 0.02
        shares.append((share, sum(errors) / len(errors)))
    assert shares[0] == shares[1]
    assert pass_success_probability(passer, receiver, in_lane) < pass_success_probability(passer, receiver, [])


def test_static_receiver_has_no_dosage_gap_and_keeps_the_angle_law() -> None:
    """Ticket v2-realisme/23a (piste b de la clôture) : receveur arrêté, aucun écart de dosage ; la chance de précision est
    celle de la seule loi d'angle (écart latéral sous `ON_TARGET_M` à la distance du receveur)."""
    passer = _player(attributes={"Passing": 40})
    receiver = _player("R", position=Vec2(55.0, 34.0))  # 25 m
    assert dosage_gap(passer, receiver) == (0.0, 0.0)
    sigma = pass_error_sigma_rad(passer, [])
    assert math.isclose(pass_accuracy_probability(passer, receiver, []),
                        math.erf(math.atan(ON_TARGET_M / 25.0) / (sigma * math.sqrt(2.0))))


def test_the_part_of_the_run_left_out_by_the_dosage_lowers_a_poor_passer_s_chance_only() -> None:
    """Ticket v2-realisme/23a (piste b) : un passeur faible joue dans les pieds d'un receveur lancé ; la part de la course
    que le dosage ne joue pas éloigne le ballon du receveur et compte dans la chance évaluée. Passing 99 (dosage parfait) :
    aucun écart, chance à peine changée (la passe dans la course est un peu plus longue) ; Passing 30 : la chance baisse
    nettement."""
    still = _player("R", position=Vec2(55.0, 34.0))
    running = _player("R", position=Vec2(55.0, 34.0), velocity=Vec2(0.0, 5.0))  # 5 m/s en travers, à 25 m
    strong, poor = _player(attributes={"Passing": 99}), _player(attributes={"Passing": 30})
    assert dosage_gap(strong, running) == (0.0, 0.0)
    assert math.isclose(pass_success_probability(strong, running, []), pass_success_probability(strong, still, []),
                        abs_tol=0.01)
    along, across = dosage_gap(poor, running)
    assert across > 8.0 and abs(along) < 1.0  # environ 10 m en travers : presque toute la course manquée
    assert pass_success_probability(poor, running, []) < pass_success_probability(poor, still, []) - 0.15
    assert pass_accuracy_probability(poor, running, []) < pass_accuracy_probability(poor, still, [])


def test_arrival_distance_to_the_running_receiver_follows_the_accuracy_chance() -> None:
    """Ticket v2-realisme/23a (piste b, une seule loi) : on tire la passe (5 000 tirages) et on mesure où passe le ballon par
    rapport à la position future du receveur (sa position plus sa course pendant le vol) ; la part sous `ON_TARGET_M`
    suit la chance de précision évaluée, à 2 points près, pour un receveur qui court en travers ou vers le passeur."""
    from v2engine.flux import PASSE
    for note, velocity in ((55, Vec2(0.0, 0.4)), (70, Vec2(0.0, 1.0)), (80, Vec2(-1.0, 0.0))):
        passer = _player(attributes={"Passing": note})
        receiver = _player("R", position=Vec2(50.0, 34.0), velocity=velocity)  # 20 m
        aim = pass_aim(passer, receiver)
        lead = (aim - receiver.position) * (1.0 / dosage_quality(passer))  # course entière pendant le vol
        future = receiver.position + lead
        reach = passer.position.distance_to(aim)  # le ballon arrive à hauteur du point visé, le long du cap tiré
        PASSE.seed(20260923)
        close = 0
        for _ in range(5000):
            arrival = passer.position + pass_velocity(passer, receiver).normalized() * reach
            close += future.distance_to(arrival) < ON_TARGET_M
        assert abs(close / 5000 - pass_accuracy_probability(passer, receiver, [])) < 0.02


def test_easy_ball_is_easy_to_control_and_fast_ball_is_harder() -> None:
    player = _player()
    assert math.isclose(control_difficulty(player, Vec2(IDEAL_ARRIVAL_MPS, 0.0), []), 10.0)
    assert math.isclose(control_difficulty(player, Vec2(26.0, 0.0), []), 30.0)


def test_evaluated_chance_combines_the_measured_cut_table_and_the_missed_pass() -> None:
    """Ticket v2-realisme/18g : chance que la passe ne soit pas perdue = produit des (1 - coupe) de chaque adversaire x
    part non perdue par bande d'écart latéral à l'arrivée, tirée de la loi d'écart (ticket 23a ; réajustée au ticket 18n :
    0,99 sous 2 m, 0,98 de 2 à 4 m, 0,80 au-delà). Coupe : table du 18n (réestimée au 18o), selon la distance à la
    trajectoire et le temps du ballon jusqu'à l'adversaire. Ne coupent pas : un adversaire derrière le passeur, au-delà du receveur, ou à 6 m ou plus
    de la ligne."""
    passer = _player()
    receiver = _player("R", position=Vec2(45.0, 34.0))  # 15 m, à l'arrêt : aucun écart de dosage

    def bands(opponents):
        scale = pass_error_sigma_rad(passer, opponents) * math.sqrt(2.0)
        w2, w4 = (math.erf(math.atan(limit / 15.0) / scale) for limit in (2.0, 4.0))
        return w2 * 0.99 + (w4 - w2) * 0.98 + (1.0 - w4) * 0.80

    alone = pass_success_probability(passer, receiver, [])
    assert math.isclose(alone, bands([]))
    near = _player("N", team="away", position=Vec2(31.5, 34.2))  # à 0,2 m de la ligne, ballon à 0,11 s : 0,87
    path = _player("W", team="away", position=Vec2(38.0, 35.5))  # à 1,5 m de la ligne, ballon à 0,70 s : 0,47
    for silent in (Vec2(24.0, 34.0), Vec2(48.0, 34.0), Vec2(38.0, 40.5)):  # derrière, au-delà, à 6,5 m (hors pression)
        assert math.isclose(pass_success_probability(passer, receiver, [_player("S", team="away", position=silent)]),
                            alone)
    both = pass_success_probability(passer, receiver, [near, path])  # la pression de N élargit l'écart du passeur
    assert math.isclose(both, (1 - 0.87) * (1 - 0.47) * bands([near, path]))


def test_cut_chance_follows_the_ball_travel_time_not_the_pass_length() -> None:
    """Ticket v2-realisme/18n : à la même place par rapport au passeur (1,5 m devant lui, 0,75 m de la ligne), l'adversaire
    coupe plus souvent une passe courte, qui part lentement (ballon à son niveau en 0,17 s pour 5 m : 0,62 depuis le 18o),
    qu'une passe longue (0,07 s pour 30 m : 0,26). À temps du ballon égal, la longueur n'y est pour rien."""
    passer = _player()
    presser = _player("O", team="away", position=Vec2(31.5, 34.75))
    short = _player("R", position=Vec2(35.0, 34.0))
    long_ = _player("R", position=Vec2(60.0, 34.0))
    assert math.isclose(possession._cut_chance(passer.position, short.position, presser), 0.62)
    assert math.isclose(possession._cut_chance(passer.position, long_.position, presser), 0.26)
    log_f = math.log(possession.BALL_FRICTION_PER_S)
    for length in (8.0, 20.0, 40.0):  # même temps du ballon (0,25 s) jusqu'à l'adversaire : même chance (0,66)
        speed = possession._launch_speed(length)
        along = speed * (math.exp(0.25 * log_f) - 1.0) / log_f
        rival = _player("O", team="away", position=Vec2(30.0 + along, 34.75))
        assert math.isclose(possession._cut_chance(passer.position, Vec2(30.0 + length, 34.0), rival), 0.66)


def test_receiver_contests_the_ball_near_the_end_of_the_pass() -> None:
    """Ticket v2-realisme/18o : à moins de 2 m du bout du trajet, le receveur dispute le ballon ; la coupe de la table est
    multipliée par un facteur selon le reste du trajet et l'écart à la ligne (moins de 1 m : 0,50 / 0,66 / 0,81 / 0,90 ;
    1 m et plus : 0,26 / 0,36 / 0,46 / 0,65, par tranche de 0,5 m). Passe de 12 m, ballon à plus de 1 s au bout : sur la
    ligne 0,41, à 1,5 m de la ligne 0,34."""
    passer = _player()
    end = Vec2(42.0, 34.0)

    def cut(x: float, y: float = 34.0) -> float:
        return possession._cut_chance(passer.position, end, _player("O", team="away", position=Vec2(x, y)))

    assert math.isclose(cut(41.8), 0.41 * 0.50)  # sur la ligne, 0,2 m avant le receveur
    assert math.isclose(cut(41.3), 0.41 * 0.66)  # 0,7 m avant
    assert math.isclose(cut(40.8), 0.41 * 0.81)  # 1,2 m avant
    assert math.isclose(cut(40.3), 0.41 * 0.90)  # 1,7 m avant
    assert math.isclose(cut(39.5), 0.41)  # 2,5 m avant : la table entière
    assert math.isclose(cut(41.8, 35.5), 0.34 * 0.26)  # à 1,5 m de la ligne, 0,2 m avant
    assert math.isclose(cut(40.3, 35.5), 0.34 * 0.65)  # à 1,5 m de la ligne, 1,7 m avant
    assert math.isclose(cut(39.5, 35.5), 0.34)  # 2,5 m avant : la table entière (ballon encore à plus de 1 s)


def test_marked_receiver_at_contact_keeps_the_measured_engine_chance() -> None:
    """Ticket v2-realisme/18o (réserve A2 du 18n) : receveur marqué de face au contact, adversaire immobile 0,5 m devant
    lui sur la ligne, passe de 12 m. La chance évaluée suit le moteur : en match, ces passes sont gardées deux fois sur
    trois (96 matchs, adversaire à moins de 1,5 m du receveur entre le passeur et lui : environ 0,61 non perdues), d'où 0,72
    ici (coupe 0,41 x 0,66). Physiquement, un défenseur collé devant le receveur devrait gagner presque toujours : écart du
    moteur, ticket de physique à part (décision du propriétaire, 20/11/2026) ; ce test fige la valeur actuelle."""
    passer = _player()
    receiver = _player("R", position=Vec2(42.0, 34.0))
    marker = _player("M", team="away", position=Vec2(41.5, 34.0))
    chance = pass_success_probability(passer, receiver, [marker])
    assert math.isclose(chance, pass_success_probability(passer, receiver, []) * (1.0 - 0.41 * 0.66))
    assert 0.6 < chance < 0.8
    assert chance < pass_success_probability(passer, receiver, [])
