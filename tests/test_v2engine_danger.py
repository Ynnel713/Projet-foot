"""Carte du danger (ticket v2-collectif/33) : grille xT de Karun Singh, lissée, orientée par équipe."""

from v2engine.danger import danger, loss_cost
from v2engine.geometry import Vec2


def test_valeurs_de_reference_aux_centres_des_cases():
    assert abs(danger(Vec2(100.625, 29.75), "home") - 0.25745) < 1e-9  # case des 6 mètres, axe
    assert abs(danger(Vec2(4.375, 4.25), "home") - 0.00638) < 1e-9  # près de son poteau de corner


def test_orientation_et_cout_de_la_perte():
    penalty = Vec2(94.0, 34.0)
    assert danger(penalty, "home") > 0.1 > danger(penalty, "away")
    assert loss_cost(penalty, "away") == danger(penalty, "home")
    assert danger(Vec2(105.0 - 94.0, 34.0), "away") == danger(penalty, "home")


def test_lissage_sans_saut_et_croissant_vers_le_but():
    values = [danger(Vec2(x, 34.0), "home") for x in range(0, 106)]
    assert all(abs(b - a) < 0.03 for a, b in zip(values, values[1:]))
    assert values[-1] > values[52] > values[0]
