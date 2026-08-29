from ligue1sim.lineup import pick_best_formation
from ligue1sim.nations import load_national_teams

DATA_PATH = "data/joueurs.xlsx"


def test_load_national_teams_returns_only_complete_squads_of_18():
    # TARGET_QUOTA de scripts/generate_national_teams.py a été abaissé de
    # 23 à 18 le 29/08/2026 (2 gardiens, 6 défenseurs, 5 milieux, 5
    # attaquants) : les données scrapées pour 20 sélections manquantes ne
    # fournissaient pas toujours assez de joueurs bien notés par groupe de
    # poste pour boucler un 23/23 -- voir la docstring du script.
    teams = load_national_teams(DATA_PATH)

    assert len(teams) > 0
    assert all(len(t.players) == 18 for t in teams)
    assert len({t.name for t in teams}) == len(teams)  # pas de doublon de pays


def test_load_national_teams_includes_incomplete_squads_when_asked():
    complete_only = load_national_teams(DATA_PATH, complete_only=True)
    everyone = load_national_teams(DATA_PATH, complete_only=False)

    assert len(everyone) > len(complete_only)
    assert {t.name for t in complete_only} <= {t.name for t in everyone}


def test_national_players_keep_their_precise_poste_from_infos_principales():
    # L'onglet continental ne donne que "Gardien/Défenseur/Milieu/Attaquant" :
    # les joueurs reconstruits doivent avoir un poste précis (RB/DC/MOC/...),
    # jamais un de ces 4 libellés larges.
    teams = load_national_teams(DATA_PATH)
    postes = {p.poste for team in teams for p in team.players}

    assert postes.isdisjoint({"Gardien", "Défenseur", "Milieu", "Attaquant"})
    assert "GK" in postes


def test_national_team_squad_can_field_a_full_lineup():
    teams = load_national_teams(DATA_PATH)
    team = teams[0]

    lineup = pick_best_formation(team)

    assert len(lineup.players) == 11
