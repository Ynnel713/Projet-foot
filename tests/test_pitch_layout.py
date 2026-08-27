from collections import defaultdict

from ligue1sim.events import PlayerMatchStat
from ligue1sim.pitch_layout import actual_formation_label, place_starting_xi


def _stat(poste: str, name: str) -> PlayerMatchStat:
    return PlayerMatchStat(player_name=name, club_name="Test FC", poste=poste, started=True)


def _x_of(placed, name: str) -> float:
    return next(p.x for p in placed if p.stat.player_name == name)


def _y_of(placed, name: str) -> float:
    return next(p.y for p in placed if p.stat.player_name == name)


def _assert_lines_are_mirror_symmetric(placed) -> None:
    """Pour chaque ligne (même y), l'ensemble des x doit être un miroir
    parfait par rapport à l'axe du terrain (x=50) : pour tout x du multi-
    ensemble, 100-x doit aussi en faire partie (à la tolérance flottante
    près)."""
    by_y: dict[float, list[float]] = defaultdict(list)
    for p in placed:
        by_y[p.y].append(round(p.x, 6))

    for y, xs in by_y.items():
        mirrored = sorted(round(100.0 - x, 6) for x in xs)
        assert sorted(xs) == mirrored, f"ligne y={y} non symétrique : {sorted(xs)} vs miroir {mirrored}"


def test_back_four_spreads_full_backs_wide_and_centre_backs_central():
    starters = [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("RB", "rb"),
        _stat("MC", "cm1"),
        _stat("MC", "cm2"),
        _stat("MC", "cm3"),
        _stat("AG", "lw"),
        _stat("BU", "cf"),
        _stat("AD", "rw"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    assert _x_of(placed, "lb") < 30
    assert _x_of(placed, "rb") > 70
    assert 32 <= _x_of(placed, "cb1") <= 68
    assert 32 <= _x_of(placed, "cb2") <= 68


def test_lanes_mirror_for_the_team_attacking_downward():
    # Gauche/droite se définissent du point de vue de l'équipe qui attaque
    # (comme au vrai foot), pas du spectateur : une équipe qui attaque vers
    # le BAS de l'écran (gardien tourné vers le haut, dos au sens du jeu) a
    # sa gauche/droite inversée à l'écran par rapport à une équipe qui
    # attaque vers le haut -- son latéral droit apparaît à GAUCHE de l'écran
    # (bug réel observé : un vrai latéral droit affiché à droite de l'écran
    # pour l'équipe du haut, alors qu'il doit apparaître à gauche).
    starters = [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("RB", "rb"),
    ]

    placed = place_starting_xi(starters, attacking_up=False)

    assert _x_of(placed, "rb") < 30
    assert _x_of(placed, "lb") > 70
    assert 32 <= _x_of(placed, "cb1") <= 68
    assert 32 <= _x_of(placed, "cb2") <= 68


def test_central_midfielders_never_pushed_to_the_touchline_when_alone_in_their_line():
    # Doublette de milieux axiaux (double pivot) sans latéraux dans la même
    # ligne : ne doivent jamais se retrouver écartés vers les couloirs.
    starters = [
        _stat("GK", "gk"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("DC", "cb3"),
        _stat("DC", "cb4"),
        _stat("MDC", "dm1"),
        _stat("MDC", "dm2"),
        _stat("MOC", "am"),
        _stat("AG", "lw"),
        _stat("BU", "cf"),
        _stat("AD", "rw"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    for name in ("dm1", "dm2"):
        x = _x_of(placed, name)
        assert 32 <= x <= 68, f"{name} at x={x} should stay central, not be pushed wide"


def test_433_forms_a_triangle_with_one_holding_midfielder_deeper_than_the_two_ahead():
    starters = [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("RB", "rb"),
        _stat("MDC", "dm"),
        _stat("MC", "cm1"),
        _stat("MC", "cm2"),
        _stat("AG", "lw"),
        _stat("BU", "cf"),
        _stat("AD", "rw"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    dm_y = _y_of(placed, "dm")
    cm1_y = _y_of(placed, "cm1")
    cm2_y = _y_of(placed, "cm2")
    assert dm_y != cm1_y == cm2_y  # le sentinelle forme sa propre ligne, à part des 2 relayeurs
    # attacking_up=True : l'équipe attaque vers le haut (y décroissant), donc
    # le sentinelle (plus proche de la défense) a un y plus grand.
    assert dm_y > cm1_y

    for name in ("dm", "cm1", "cm2"):
        x = _x_of(placed, name)
        assert 32 <= x <= 68, f"{name} at x={x} should stay central"


def test_4231_splits_into_a_deep_pivot_and_a_high_trio_all_central_players_grouped_centrally():
    starters = [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("RB", "rb"),
        _stat("MDC", "dm1"),
        _stat("MDC", "dm2"),
        _stat("AG", "lw"),
        _stat("MOC", "am"),
        _stat("AD", "rw"),
        _stat("BU", "cf"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    assert _y_of(placed, "dm1") == _y_of(placed, "dm2")
    assert _y_of(placed, "dm1") != _y_of(placed, "am")
    for name in ("dm1", "dm2", "am"):
        x = _x_of(placed, name)
        assert 32 <= x <= 68, f"{name} at x={x} should stay central"
    assert _x_of(placed, "lw") < 30
    assert _x_of(placed, "rw") > 70


def test_flat_four_man_midfield_stays_a_single_line_without_a_holding_midfielder():
    # AG/AD sont désormais des postes offensifs (voir players.POSITION_GROUP) :
    # un "milieu large" au sens de l'ancienne nomenclature Transfermarkt n'a
    # plus d'équivalent MIDFIELDER dans le nouveau tagging -- ce scénario se
    # limite donc à des milieux d'axe (MC), sans paire large confirmée.
    starters = [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("RB", "rb"),
        _stat("MC", "cm1"),
        _stat("MC", "cm2"),
        _stat("MC", "cm3"),
        _stat("MC", "cm4"),
        _stat("BU", "cf1"),
        _stat("BU", "cf2"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    assert _y_of(placed, "cm1") == _y_of(placed, "cm2") == _y_of(placed, "cm3") == _y_of(placed, "cm4")


def test_lopsided_lane_composition_never_overlaps():
    # La meilleure compo choisit les 4 meilleurs défenseurs par note, sans
    # garantir un exact 1 latéral gauche / 1 latéral droit -- un effectif
    # peut être plus riche à droite (ex. 3 RB + 1 LB). Les 4
    # doivent rester à des positions distinctes, jamais deux ronds superposés
    # (bug réel observé : AS Monaco, 2 joueurs affichés au même endroit).
    starters = [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("RB", "rb1"),
        _stat("RB", "rb2"),
        _stat("RB", "rb3"),
        _stat("MC", "cm1"),
        _stat("MC", "cm2"),
        _stat("MC", "cm3"),
        _stat("AG", "lw"),
        _stat("BU", "cf"),
        _stat("AD", "rw"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    def_line = [p for p in placed if p.stat.poste in ("LB", "RB")]
    xs = sorted(p.x for p in def_line)
    assert len(def_line) == 4
    assert len(set(xs)) == 4  # 4 positions strictement distinctes
    min_gap = min(b - a for a, b in zip(xs, xs[1:]))
    assert min_gap >= 15.0  # écart suffisant pour ne jamais superposer les ronds (92px de large)
    _assert_lines_are_mirror_symmetric(placed)


def test_lane_without_any_left_side_candidate_stays_symmetric_not_pinned_to_one_edge():
    # Effectif réel observé (AS Monaco) : 2 DC + 2 RB, AUCUN
    # LB du tout. Sans logique de paire confirmée, un tri naïf par
    # couloir pousserait un vrai DC tout seul sur la touche gauche
    # -- ce n'est pas symétrique. Faute de paire gauche/droite, les 4 doivent
    # former un bloc central symétrique, aucun n'allant jusqu'au bord (12/88)
    # réservé aux vraies paires larges.
    starters = [
        _stat("GK", "gk"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("RB", "rb1"),
        _stat("RB", "rb2"),
        _stat("MC", "cm1"),
        _stat("MC", "cm2"),
        _stat("MC", "cm3"),
        _stat("AG", "lw"),
        _stat("BU", "cf"),
        _stat("AD", "rw"),
    ]

    placed = place_starting_xi(starters, attacking_up=True)

    def_line = [p for p in placed if p.stat.poste in ("DC", "RB")]
    xs = sorted(p.x for p in def_line)
    assert len(set(xs)) == 4
    assert xs[0] > 12.0  # personne poussé jusqu'au bord réservé aux vraies paires larges
    assert xs[-1] < 88.0
    _assert_lines_are_mirror_symmetric(placed)


def test_every_line_is_mirror_symmetric_across_a_range_of_formations():
    scenarios = {
        "4-4-2 equilibre": [
            _stat("GK", "gk"),
            _stat("LB", "lb"),
            _stat("DC", "cb1"),
            _stat("DC", "cb2"),
            _stat("RB", "rb"),
            _stat("AG", "lm"),
            _stat("MC", "cm1"),
            _stat("MC", "cm2"),
            _stat("AD", "rm"),
            _stat("BU", "cf1"),
            _stat("BU", "cf2"),
        ],
        "4-2-3-1": [
            _stat("GK", "gk"),
            _stat("LB", "lb"),
            _stat("DC", "cb1"),
            _stat("DC", "cb2"),
            _stat("RB", "rb"),
            _stat("MDC", "dm1"),
            _stat("MDC", "dm2"),
            _stat("AG", "lw"),
            _stat("MOC", "am"),
            _stat("AD", "rw"),
            _stat("BU", "cf"),
        ],
        "defense 100% RB": [
            _stat("GK", "gk"),
            _stat("RB", "rb1"),
            _stat("RB", "rb2"),
            _stat("RB", "rb3"),
            _stat("RB", "rb4"),
            _stat("MC", "cm1"),
            _stat("MC", "cm2"),
            _stat("MC", "cm3"),
            _stat("AG", "lw"),
            _stat("BU", "cf"),
            _stat("AD", "rw"),
        ],
    }

    for label, starters in scenarios.items():
        placed = place_starting_xi(starters, attacking_up=True)
        _assert_lines_are_mirror_symmetric(placed)


def test_actual_formation_label_counts_by_true_group():
    starters = [
        _stat("GK", "gk"),
        _stat("DC", "cb1"),
        _stat("DC", "cb2"),
        _stat("MDC", "dm"),
        _stat("MC", "cm"),
        _stat("BU", "cf"),
    ]

    assert actual_formation_label(starters) == "2-2-1"
