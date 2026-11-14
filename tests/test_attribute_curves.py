"""Table des courbes d'attributs (ticket v2-realisme/24) : elle reproduit les fonctions du moteur, sans match."""

from scripts.attribute_curves import NOTES, duel_table, markdown, player, table
from v2engine.attributes import duel_probability, success_probability
from v2engine.decision import best_choice_probability
from v2engine.duel import tackle_success_probability


def _row(attribute: str, start: str) -> dict:
    return next(r for r in table() if r["attribut"] == attribute and r["mécanisme"].startswith(start))


def test_table_reproduces_the_engine_curves() -> None:
    decisions = _row("Decisions", "meilleur choix")
    assert all(decisions["valeurs"][n] == best_choice_probability(float(n)) for n in NOTES)
    tackle = _row("Tackling", "tacle gagné")
    for n in NOTES:
        assert tackle["valeurs"][n] == tackle_success_probability(player({"Tackling": n}), player())
        assert tackle["valeurs"][n] == duel_probability(float(n), 60.0)
    dosage = _row("Passing", "dosage")
    assert dosage["valeurs"][80] == success_probability(80.0, baseline=0.5, amplitude=0.5, min_prob=0.0, max_prob=1.0)


def test_shares_are_computed_on_the_50_to_99_range() -> None:
    row = _row("Decisions", "meilleur choix")
    v = row["valeurs"]
    assert abs(row["part 70-80"] - (v[80] - v[70]) / (v[99] - v[50])) < 1e-12
    assert abs(row["part 60-70"] - (v[70] - v[60]) / (v[99] - v[50])) < 1e-12


def test_duel_table_and_markdown() -> None:
    duels = duel_table()
    assert duels[0] == 0.5 and duels[10] == duel_probability(80.0, 70.0)
    text = markdown(table())
    assert "| Decisions | meilleur choix | courbe |" in text and "Chance du plus fort" in text


def test_neutral_player_reads_60_everywhere() -> None:
    p = player({"Passing": 80})
    assert p.attributes == {"Passing": 80} and p.pace == 60 and p.acceleration == 60 and p.stamina == 60
    assert player({"Pace": 90}).pace == 90
