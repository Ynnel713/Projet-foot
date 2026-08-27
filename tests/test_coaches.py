import pandas as pd
import pytest

from ligue1sim.clubs import Club
from ligue1sim.coaches import clear_cache, coach_name, coaches, preferred_formations
from ligue1sim.lineup import pick_best_formation, select_best_xi
from ligue1sim.players import Player


@pytest.fixture(autouse=True)
def _clear_cache():
    """Le chargement est mis en cache (appelé à chaque match simulé) : on
    vide le cache avant/après chaque test pour ne pas polluer les autres
    tests avec un fichier temporaire d'un test précédent."""
    clear_cache()
    yield
    clear_cache()


def _write_coaches_file(tmp_path, rows):
    path = tmp_path / "entraineurs.xlsx"
    pd.DataFrame(rows, columns=["Championnat", "Club", "Entraîneur", "Formation préférentielle", "Remarques"]).to_excel(
        path, index=False
    )
    return str(path)


def _player(poste: str, note: float, name: str) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST"
    )


def _full_squad() -> list[Player]:
    squad = [_player("GK", 70.0, f"gk{i}") for i in range(2)]
    squad += [_player("DC", 70.0, f"cb{i}") for i in range(4)]
    squad += [_player("LB", 70.0, "lb0")]
    squad += [_player("RB", 70.0, "rb0")]
    squad += [_player("MC", 70.0, f"cm{i}") for i in range(4)]
    squad += [_player("MOC", 70.0, "am0")]
    squad += [_player("AG", 70.0, "lw0")]
    squad += [_player("AD", 70.0, "rw0")]
    squad += [_player("BU", 70.0, f"cf{i}") for i in range(3)]
    return squad


def test_preferred_formations_reads_club_to_formation_mapping(tmp_path):
    path = _write_coaches_file(
        tmp_path,
        [
            ["Ligue 1", "LOSC Lille", "Bruno Genesio", "4-2-3-1", None],
            ["Ligue 1", "RC Lens", "Pierre Sage", "3-4-3", None],
        ],
    )

    result = preferred_formations((path,))

    assert result == {"LOSC Lille": "4-2-3-1", "RC Lens": "3-4-3"}


def test_preferred_formations_skips_rows_with_no_formation(tmp_path):
    path = _write_coaches_file(
        tmp_path,
        [
            ["Ligue 1", "AJ Auxerre", "Christophe Pélissier", None, "formation non renseignée"],
        ],
    )

    assert preferred_formations((path,)) == {}


def test_preferred_formations_ignores_missing_files(tmp_path):
    missing_path = str(tmp_path / "does_not_exist.xlsx")

    assert preferred_formations((missing_path,)) == {}


def test_coach_name_is_available_even_without_a_preferred_formation(tmp_path):
    path = _write_coaches_file(
        tmp_path,
        [["Ligue 1", "AJ Auxerre", "Christophe Pélissier", None, "formation non renseignée"]],
    )

    assert coach_name("AJ Auxerre", (path,)) == "Christophe Pélissier"
    assert preferred_formations((path,)) == {}


def test_coach_name_is_none_for_an_unknown_club(tmp_path):
    path = _write_coaches_file(tmp_path, [["Ligue 1", "AJ Auxerre", "Christophe Pélissier", "4-4-2", None]])

    assert coach_name("Unknown FC", (path,)) is None


def test_coaches_exposes_both_name_and_formation(tmp_path):
    path = _write_coaches_file(tmp_path, [["Ligue 1", "LOSC Lille", "Bruno Genesio", "4-2-3-1", None]])

    result = coaches((path,))

    assert result["LOSC Lille"].name == "Bruno Genesio"
    assert result["LOSC Lille"].preferred_formation == "4-2-3-1"


def test_pick_best_formation_uses_the_forced_formation_when_known(tmp_path, monkeypatch):
    path = _write_coaches_file(tmp_path, [["Ligue 1", "Test FC", "Coach Test", "3-4-3", None]])
    import ligue1sim.lineup as lineup_module

    monkeypatch.setattr(lineup_module, "preferred_formations", lambda: preferred_formations((path,)))

    club = Club(name="Test FC", players=_full_squad())
    lineup = pick_best_formation(club)

    assert lineup.formation == "3-4-3"


def test_pick_best_formation_falls_back_to_adaptive_choice_when_club_unknown(tmp_path, monkeypatch):
    path = _write_coaches_file(tmp_path, [["Ligue 1", "Some Other Club", "Coach Test", "3-4-3", None]])
    import ligue1sim.lineup as lineup_module

    monkeypatch.setattr(lineup_module, "preferred_formations", lambda: preferred_formations((path,)))

    club = Club(name="Test FC", players=_full_squad())
    lineup = pick_best_formation(club)

    assert lineup.formation in {"4-4-2", "4-3-3", "4-2-3-1"}


def test_pick_best_formation_switches_away_from_a_badly_hurt_forced_formation(tmp_path, monkeypatch):
    # Le coach impose "4-4-2" (2 places de BU, aucune place de MOC). Le seul
    # avant-centre reconnu de l'effectif ("bu_hurt") est blessé pour ce match
    # : sans lui, "4-4-2" doit combler SES DEUX places de BU avec les deux
    # seuls corps encore tactiquement proches (deux ailiers de réserve,
    # "spare_ag"/"spare_ad", moins bien notés que les titulaires). "4-2-3-1"
    # (une seule place de BU, une place de MOC pourvue par un vrai milieu
    # offensif "moc0") n'a besoin de piocher qu'UN seul des deux ailiers de
    # réserve et laisse l'autre sur le banc -- nettement mieux noté au global.
    # Doit basculer plutôt que de s'entêter sur "4-4-2".
    path = _write_coaches_file(tmp_path, [["Ligue 1", "Test FC", "Coach Test", "4-4-2", None]])
    import ligue1sim.lineup as lineup_module

    monkeypatch.setattr(lineup_module, "preferred_formations", lambda: preferred_formations((path,)))

    players = [_player("GK", 75.0, "gk0")]
    players += [_player("LB", 75.0, "lb0")]
    players += [_player("DC", 75.0, f"cb{i}") for i in range(2)]
    players += [_player("RB", 75.0, "rb0")]
    players += [_player("MDC", 75.0, "mdc0")]
    players += [_player("MC", 75.0, "mc0")]
    players += [_player("AD", 75.0, "ad0")]
    players += [_player("AG", 75.0, "ag0")]
    players += [_player("MOC", 75.0, "moc0")]
    players += [_player("AG", 60.0, "spare_ag")]
    players += [_player("AD", 50.0, "spare_ad")]
    players += [_player("BU", 90.0, "bu_hurt")]
    club = Club(name="Test FC", players=players)

    unavailable = frozenset({"bu_hurt"})
    degraded = pick_best_formation(club, unavailable=unavailable)
    forced_hurt = select_best_xi(club, "4-4-2", unavailable=unavailable)

    assert degraded.formation != "4-4-2"
    assert degraded.rating > forced_hurt.rating


def test_pick_best_formation_keeps_the_forced_formation_when_the_gap_is_small(tmp_path, monkeypatch):
    # Une indisponibilité qui ne touche qu'un joueur de banc jamais titularisé
    # ne doit rien changer : le dispositif du coach reste appliqué (pas de
    # bascule pour un écart nul/négligeable, voir _FORMATION_LOYALTY_FACTOR).
    path = _write_coaches_file(tmp_path, [["Ligue 1", "Test FC", "Coach Test", "3-4-3", None]])
    import ligue1sim.lineup as lineup_module

    monkeypatch.setattr(lineup_module, "preferred_formations", lambda: preferred_formations((path,)))

    club = Club(name="Test FC", players=_full_squad())
    lineup = pick_best_formation(club, unavailable=frozenset({"gk1"}))

    assert lineup.formation == "3-4-3"
