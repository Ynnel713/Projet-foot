import pandas as pd
import pytest

from ligue1sim.clubs import (
    ClubDataError,
    list_championnats,
    load_all_clubs,
    load_clubs,
)

DATA_PATH = "data/joueurs.xlsx"


def test_list_championnats_excludes_autres_clubs_and_returns_the_nine_leagues():
    assert list_championnats(DATA_PATH) == [
        "Bundesliga",
        "Championship",
        "Eredivisie",
        "Jupiler Pro League",
        "LaLiga",
        "Liga Portugal",
        "Ligue 1",
        "Premier League",
        "Serie A",
    ]


@pytest.mark.parametrize(
    "championnat,expected_club_count",
    [
        ("Premier League", 20),
        ("LaLiga", 20),
        ("Bundesliga", 18),
        ("Serie A", 20),
        ("Ligue 1", 18),
        ("Eredivisie", 18),
        ("Jupiler Pro League", 18),
        ("Liga Portugal", 18),
    ],
)
def test_load_clubs_returns_expected_club_count(championnat, expected_club_count):
    clubs = load_clubs(DATA_PATH, championnat)

    assert len(clubs) == expected_club_count
    assert len({c.name for c in clubs}) == expected_club_count


def test_load_clubs_populates_players_with_valid_notes_and_full_squads():
    clubs = load_clubs(DATA_PATH, "Ligue 1")

    for club in clubs:
        assert len(club.players) >= 11
        assert all(0 <= p.note <= 100 for p in club.players)
        assert all(p.club == club.name for p in club.players)
        assert all(p.championnat == "Ligue 1" for p in club.players)


def test_load_clubs_rejects_odd_number_of_clubs(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 33,
            "Club": ["A"] * 11 + ["B"] * 11 + ["C"] * 11,
            "Prénom": [f"P{i}" for i in range(33)],
            "Nom": [f"N{i}" for i in range(33)],
            "Nationalité": ["France"] * 33,
            "Âge": [25] * 33,
            "Poste": ["MC"] * 33,
            "Moyenne joueur": [70] * 33,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_clubs_rejects_understaffed_club(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22 + ["TEST"] * 3,
            "Club": ["A"] * 11 + ["B"] * 11 + ["C"] * 3,
            "Prénom": [f"P{i}" for i in range(25)],
            "Nom": [f"N{i}" for i in range(25)],
            "Nationalité": ["France"] * 25,
            "Âge": [25] * 25,
            "Poste": ["MC"] * 25,
            "Moyenne joueur": [70] * 25,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_all_clubs_includes_autres_clubs_and_covers_the_whole_file():
    options = load_all_clubs(DATA_PATH)

    championnats = {o.championnat for o in options}
    assert "Autres clubs" in championnats
    assert {
        "Premier League",
        "LaLiga",
        "Bundesliga",
        "Serie A",
        "Ligue 1",
    } <= championnats

    ligue1_clubs = [o for o in options if o.championnat == "Ligue 1"]
    assert len(ligue1_clubs) == 18
    assert all(len(o.players) >= 11 for o in ligue1_clubs)


def test_club_option_as_club_carries_players_through():
    options = load_all_clubs(DATA_PATH)
    option = next(o for o in options if o.championnat == "Ligue 1")

    club = option.as_club()

    assert club.name == option.name
    assert club.players == option.players


def test_load_all_clubs_is_cached_across_calls():
    """Régression perf (29/08/2026) : `load_all_clubs` recalculait tout le
    regroupement/parsing (866 groupes club/championnat) à chaque appel, sans
    cache propre -- contrairement à toutes les autres fonctions de parsing du
    classeur entier (`_read`, `_load_all_national_teams`...). Chaque
    interaction du sélecteur de clubs de la Compétition Perso (qui appelle
    `load_all_clubs` à chaque rerun Streamlit) refaisait ce travail, d'où la
    lenteur ressentie."""
    assert load_all_clubs(DATA_PATH) is load_all_clubs(DATA_PATH)


def test_at_least_18_players_cleanly_separates_real_clubs_from_stray_rows():
    """Régression (29/08/2026) : "Autres clubs" contient des centaines de
    lignes isolées (1 seul joueur rattaché à son club réel dans le classeur),
    jamais un effectif complet -- voir `app._perso_club_pool`, qui filtre le
    vivier de la Compétition Perso à `_MIN_PERSO_SQUAD_SIZE=18` pour les
    exclure. Certaines de ces lignes isolées partagent leur nom avec un vrai
    club d'un championnat officiel (ex. Atalanta BC en Serie A) -- sans ce
    filtre, sélectionner le club par son nom (voir `_render_club_picker_step`)
    l'incluait deux fois dans la compétition, d'où le calendrier généré avec
    un nombre de journées incohérent selon le club. Ce test verrouille
    l'hypothèse dont ce filtre dépend : aucun club réel (>=18 joueurs) ne
    partage son nom avec un autre club réel d'un championnat différent."""
    options = load_all_clubs(DATA_PATH)
    real_clubs = [o for o in options if len(o.players) >= 18]

    names = [o.name for o in real_clubs]
    assert len(names) == len(set(names)), "un nom de club réel est partagé par deux championnats"


def test_load_clubs_rejects_out_of_range_note(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": [f"P{i}" for i in range(22)],
            "Nom": [f"N{i}" for i in range(22)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["MC"] * 22,
            "Moyenne joueur": [70] * 21 + [150],
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_clubs_defaults_to_no_secondary_poste_when_column_absent(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": [f"P{i}" for i in range(22)],
            "Nom": [f"N{i}" for i in range(22)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["MC"] * 22,
            "Moyenne joueur": [70] * 22,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    clubs = load_clubs(path, "TEST")
    assert all(p.poste_secondaire == () for c in clubs for p in c.players)


def test_load_clubs_parses_secondary_postes_when_present(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": ["Star"] + [f"P{i}" for i in range(21)],
            "Nom": ["Player"] + [f"N{i}" for i in range(21)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["RB"] + ["MC"] * 21,
            "Moyenne joueur": [70] * 22,
            "Poste secondaire": ["MC / MDC"] + [None] * 21,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    clubs = load_clubs(path, "TEST")
    star = next(p for c in clubs for p in c.players if p.prenom == "Star")
    others = [p for c in clubs for p in c.players if p.prenom != "Star"]

    assert star.poste_secondaire == ("MC", "MDC")
    assert all(p.poste_secondaire == () for p in others)


def test_load_clubs_splits_a_compound_poste_into_primary_and_secondary(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": ["Versatile"] + [f"P{i}" for i in range(21)],
            "Nom": ["Player"] + [f"N{i}" for i in range(21)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["AD / AG / BU"] + ["MC"] * 21,
            "Moyenne joueur": [70] * 22,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    clubs = load_clubs(path, "TEST")
    player = next(p for c in clubs for p in c.players if p.prenom == "Versatile")

    # Le premier poste cité est le plus spécialisé : poste principal.
    assert player.poste == "AD"
    assert player.poste_secondaire == ("AG", "BU")


def test_load_clubs_combines_compound_poste_with_declared_secondary_column(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": ["Versatile"] + [f"P{i}" for i in range(21)],
            "Nom": ["Player"] + [f"N{i}" for i in range(21)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["AD / AG"] + ["MC"] * 21,
            "Moyenne joueur": [70] * 22,
            "Poste secondaire": ["MOC"] + [None] * 21,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    clubs = load_clubs(path, "TEST")
    player = next(p for c in clubs for p in c.players if p.prenom == "Versatile")

    # Les postes tirés de la colonne "Poste" (plus spécialisés) passent avant
    # ceux de la colonne "Poste secondaire" (repli).
    assert player.poste == "AD"
    assert player.poste_secondaire == ("AG", "MOC")


def test_load_clubs_allows_missing_nom_for_mononym_players(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": ["Vitinha"] + [f"P{i}" for i in range(21)],
            "Nom": [None] + [f"N{i}" for i in range(21)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["MC"] * 22,
            "Moyenne joueur": [70] * 22,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    clubs = load_clubs(path, "TEST")
    vitinha = next(p for c in clubs for p in c.players if p.prenom == "Vitinha")
    assert vitinha.nom == ""
    assert vitinha.name == "Vitinha"
