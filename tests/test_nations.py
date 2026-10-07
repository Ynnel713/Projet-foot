from ligue1sim.lineup import pick_best_formation
from ligue1sim.nations import _as_national_player, load_national_teams
from ligue1sim.players import Player

DATA_PATH = "data/joueurs.xlsx"


def test_load_national_teams_returns_only_complete_squads_of_18():
    # TARGET_QUOTA de scripts/generate_national_teams.py a été abaissé de
    # 23 à 18 le 29/08/2026 (2 gardiens, 6 défenseurs, 5 milieux, 5
    # attaquants) : les données scrapées pour 20 sélections manquantes ne
    # fournissaient pas toujours assez de joueurs bien notés par groupe de
    # poste pour boucler un 23/23 -- voir la docstring du script.
    #
    # Le Brésil fait exception à 17 (retour utilisateur du 28/09/2026) :
    # "Lucas Paquetá" y était listé deux fois (deux lignes distinctes de
    # "Infos principales", même nom/club/note -- doublon de saisie), corrigé
    # en supprimant la ligne en trop plutôt qu'en réduisant le quota général.
    teams = load_national_teams(DATA_PATH)

    assert len(teams) > 0
    counts = {t.name: len(t.players) for t in teams}
    assert all(count == 17 if "Brésil" in name else count == 18 for name, count in counts.items())
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


def test_as_national_player_keeps_the_enriched_fm26_fields():
    # Régression du 28/09/2026 : ces champs (attributs recalés côté club par
    # players.weighted_attributes, postes FM, taille, pied fort, preferred
    # moves, valeur marchande, pied) disparaissaient entièrement à la
    # transposition en sélection nationale -- tout joueur vu via sa
    # sélection (Coupe du Monde) retombait sur "Caractéristiques FM26 pas
    # encore récupérées", même déjà pleinement enrichi côté club.
    base = Player(
        prenom="Test", nom="Player", nationalite="France", age=25, poste="AG",
        note=80.0, club="Real Club", championnat="Ligue 1", id=1,
        attributes={"Pace": 88}, postes_fm="AMR", taille_fm=180,
        weak_foot=3.0, preferred_moves="Cuts Inside",
        valeur_marchande=20.0, pied="D",
    )

    national = _as_national_player(base, "France")

    assert national.attributes == {"Pace": 88}
    assert national.postes_fm == "AMR"
    assert national.taille_fm == 180
    assert national.weak_foot == 3.0
    assert national.preferred_moves == "Cuts Inside"
    assert national.valeur_marchande == 20.0
    assert national.pied == "D"
    # Le reste continue à changer comme avant (club/championnat).
    assert national.club == "France"
    assert national.championnat != base.championnat
