"""Ligue des Champions au vrai format : phase de ligue a 36 (8 matchs par club), barrages 9e-24e, 8es avec les 8 premiers, finale seche."""

import collections

import numpy as np
import pytest

from ligue1sim.champions_league import (
    DIRECT_SPOTS,
    LEAGUE_PHASE_MATCHDAYS,
    _championnats,
    _read_pots,
    draw_league_phase,
    load_champions_league_clubs,
    start_champions_league,
)
from ligue1sim.custom_competition import CompetitionFormat

DATA_PATH = "data/joueurs.xlsx"


@pytest.fixture(scope="module")
def phase():
    np.random.seed(7)
    return draw_league_phase(DATA_PATH)


def test_load_champions_league_clubs_returns_the_36_qualified_clubs():
    clubs = load_champions_league_clubs(DATA_PATH)

    assert len(clubs) == 36
    assert len({c.name for c in clubs}) == 36
    assert all(len(c.players) >= 11 for c in clubs)


class TestTirageDeLaPhaseDeLigue:
    def test_un_seul_classement_de_36_clubs_8_journees_de_18_matchs(self, phase):
        assert phase.name == "Phase de ligue" and len(phase.clubs) == 36
        assert [len(j.matches) for j in phase.calendar] == [18] * LEAGUE_PHASE_MATCHDAYS

    def test_chaque_club_joue_une_fois_par_journee(self, phase):
        for journee in phase.calendar:
            noms = [n for m in journee.matches for n in (m.home, m.away)]
            assert len(noms) == len(set(noms)) == 36

    def test_huit_adversaires_distincts_4_a_domicile_4_a_l_exterieur(self, phase):
        adversaires, domicile = collections.defaultdict(list), collections.Counter()
        for journee in phase.calendar:
            for m in journee.matches:
                adversaires[m.home].append(m.away)
                adversaires[m.away].append(m.home)
                domicile[m.home] += 1
        assert all(len(set(v)) == len(v) == 8 for v in adversaires.values())
        assert set(domicile.values()) == {4}

    def test_deux_adversaires_de_chaque_chapeau_le_sien_compris(self, phase):
        chapeau = {nom: pot for pot, noms in _read_pots(DATA_PATH).items() for nom in noms}
        adversaires = collections.defaultdict(list)
        for journee in phase.calendar:
            for m in journee.matches:
                adversaires[m.home].append(chapeau[m.away])
                adversaires[m.away].append(chapeau[m.home])
        assert all(collections.Counter(v) == {1: 2, 2: 2, 3: 2, 4: 2} for v in adversaires.values())

    def test_aucune_rencontre_entre_clubs_du_meme_championnat(self, phase):
        pays = _championnats(DATA_PATH)
        conflits = [
            (m.home, m.away) for j in phase.calendar for m in j.matches
            if pays[m.home] == pays[m.away] and pays[m.home] != "Autres clubs"
        ]
        assert conflits == []


def test_start_champions_league_est_une_competition_hybride_a_phase_de_ligue():
    competition = start_champions_league(DATA_PATH)

    assert competition.format == CompetitionFormat.HYBRID and competition.league_phase
    assert len(competition.clubs) == 36 and len(competition.groups) == 1
    assert (competition.knockout_legs, competition.final_legs) == (2, 1)
    assert not competition.groups_complete
    competition.simulate_groups_matchday()
    assert competition.groups_matchday == 1


def test_de_la_phase_de_ligue_au_champion_dans_le_vrai_format():
    np.random.seed(11)
    competition = start_champions_league(DATA_PATH)
    while not competition.groups_complete:
        competition.simulate_groups_matchday()
    assert competition.groups_matchday == LEAGUE_PHASE_MATCHDAYS
    classement = competition.groups[0].standings()["Club"].tolist()

    competition.start_knockout_from_groups()
    barrages = competition.bracket.current_round
    assert barrages.label == "Barrages" and len(barrages.ties) == 8
    # les barragistes sont exactement les 9e-24e ; le mieux classe (tete de serie) est `away` : il recoit le match retour
    assert {t for tie in barrages.ties for t in (tie.home, tie.away)} == set(classement[8:24])
    assert all(classement.index(t.away) < classement.index(t.home) for t in barrages.ties)
    assert {tuple(sorted((classement.index(t.home) + 1, classement.index(t.away) + 1)))[0] for t in barrages.ties} == {9, 10, 11, 12, 13, 14, 15, 16}

    tours = []
    while not competition.is_over:
        tour = competition.bracket.current_round
        competition.simulate_bracket_round()
        tours.append((tour.label, len(tour.ties), {len(t.legs) for t in tour.ties}))
        if competition.is_over:
            break
        competition.advance_bracket_round()
        if tour.number == 1:  # 8es : les 8 premiers + les 8 vainqueurs des barrages
            huitiemes = competition.bracket.current_round
            assert huitiemes.label == "8es de finale" and len(huitiemes.ties) == 8
            assert {t.away for t in huitiemes.ties} == set(classement[:DIRECT_SPOTS])
            assert {t.home for t in huitiemes.ties} == {t.winner for t in barrages.ties}

    assert tours == [
        ("Barrages", 8, {2}), ("8es de finale", 8, {2}), (None, 4, {2}), (None, 2, {2}), (None, 1, {1}),  # quarts, demies, finale seche
    ]
    assert competition.champion in classement[:24]
