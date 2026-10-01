"""scripts/audit_conditions_larges.py : phrases conditionnees eligibles pour plus de 30 % des evenements de leur scenario."""

from __future__ import annotations

import pytest

from scripts.audit_conditions_larges import conditions_larges, tableau


def _carton(identifiant: int, joueur: int) -> dict:
    return dict(
        match_id="m1", match_sequence=1, event_id=identifiant, minute=10 + identifiant, player_id=joueur,
        player_team="Lyon", home_team="Lyon", away_team="Nice", is_home=True, competition=None, journee=None,
        score_context=None, event_type="carton", outcome="yellow",
    )


@pytest.fixture
def banque(sqlite_conn):
    # 4 acteurs : trois jeunes (age 20), un veteran (age 30)
    sqlite_conn.executemany(
        "INSERT INTO players (id, first_name, last_name, age) VALUES (?, 'J', ?, ?)",
        [(1, "a", 20), (2, "b", 20), (3, "c", 20), (4, "d", 30)],
    )
    scenario = sqlite_conn.execute("INSERT INTO scenarios (code, label) VALUES ('CARTON_JAUNE', 'c')").lastrowid
    variante = sqlite_conn.execute(
        "INSERT INTO variants (scenario_id, code, label, is_default) VALUES (?, 'DEFAUT', 'd', 1)", (scenario,)
    ).lastrowid
    for texte, conditions in [("large", [("age", "<=", "21")]), ("rare", [("age", ">=", "30")]), ("sans condition", [])]:
        phrase = sqlite_conn.execute("INSERT INTO phrases (variant_id, text) VALUES (?, ?)", (variante, texte)).lastrowid
        for attribut, operateur, valeur in conditions:
            sqlite_conn.execute(
                "INSERT INTO phrase_conditions (phrase_id, attribute, operator, value) VALUES (?, ?, ?, ?)",
                (phrase, attribut, operateur, valeur),
            )
    sqlite_conn.commit()
    return sqlite_conn


def test_une_phrase_eligible_pour_plus_de_30_pour_cent_des_evenements_est_signalee(banque):
    evenements = [_carton(i, joueur) for i, joueur in enumerate((1, 2, 3, 4))]
    [ligne] = conditions_larges(banque, evenements)
    assert (ligne["scenario"], ligne["texte"], ligne["conditions"]) == ("CARTON_JAUNE", "large", "age <= 21")
    assert (ligne["evenements"], ligne["total"], ligne["part"]) == (3, 4, 0.75)  # "rare" (25 %) et "sans condition" : non


def test_le_seuil_est_strict_et_parametrable(banque):
    evenements = [_carton(i, joueur) for i, joueur in enumerate((1, 2, 3, 4))]
    assert [g["texte"] for g in conditions_larges(banque, evenements, seuil=0.2)] == ["large", "rare"]
    assert conditions_larges(banque, evenements, seuil=0.75) == []  # 75 % n'est pas > 75 %


def test_les_evenements_sans_scenario_sont_ignores(banque):
    poteau = dict(_carton(0, 1), event_type="occasion", gabarit="corner", outcome="poteau")  # non commente en V2.1
    assert conditions_larges(banque, [poteau]) == []


def test_tableau(banque):
    larges = conditions_larges(banque, [_carton(i, joueur) for i, joueur in enumerate((1, 2, 3, 4))])
    assert "| CARTON_JAUNE |" in tableau(larges, 0.30) and "75%" in tableau(larges, 0.30)
