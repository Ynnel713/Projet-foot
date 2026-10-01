"""Tests de engine/nlg_ingestion.py : Timeline -> dicts du contrat NLG (simulafoot_nlg/SPEC_NLG_INGESTION.md).

Le NLG n'est jamais importe (collision du paquet `engine`) : la forme des dicts est verifiee ici avec
les cles du contrat, recopiees. Le test bout-en-bout contre le vrai validateur du NLG est dans
tests/test_nlg_end_to_end.py."""

import pytest

from ligue1sim.clubs import Club
from ligue1sim.events import CardEvent, GoalEvent, MatchEvents, PlayerMatchStat, SubstitutionEvent
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Match

from narrative import build_timeline, match_result_from
from nlg_ingestion import timeline_to_events

CLES_COMMUNES = {
    "match_id", "match_sequence", "event_id", "minute", "player_id", "player_team", "home_team", "away_team",
    "is_home", "competition", "journee", "score_context", "event_type",
}
CLES_PAR_TYPE = {
    "but": CLES_COMMUNES | {"gabarit", "passeur_id"},
    "occasion": CLES_COMMUNES | {"gabarit", "outcome"},
    "carton": CLES_COMMUNES | {"outcome"},
    "remplacement": CLES_COMMUNES | {"entrant_id", "sortant_id"},
}
CLES_OPTIONNELLES = {"passeur_id", "receveur_id"}


def _joueur(poste: str, nom: str, id_: int | None, club: str = "Test FC") -> Player:
    return Player(prenom=nom, nom="", nationalite="France", age=25, poste=poste, note=70.0, club=club, championnat="TEST", id=id_)


def _effectif(prefixe: str, base_id: int) -> list[Player]:
    postes = ["GK", "GK"] + ["DC"] * 4 + ["LB"] * 2 + ["RB"] * 2 + ["MC"] * 4 + ["MOC"] * 2 + ["AG"] * 2 + ["AD"] * 2 + ["BU"] * 4
    return [_joueur(poste, f"{prefixe}_{i}", base_id + i) for i, poste in enumerate(postes)]


def _match(goals, cards=(), substitutions=(), *, home_goals=None, away_goals=None):
    home, away = Club(name="Home FC", players=_effectif("h", 1000)), Club(name="Away FC", players=_effectif("a", 2000))
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    stat = lambda club, p, started=True: PlayerMatchStat(player_name=p.name, club_name=club.name, poste=p.poste, started=started)
    home_squad = [stat(home, p) for p in home.players]
    away_squad = [stat(away, p) for p in away.players]
    events = MatchEvents(
        home_formation=home_lineup.formation, away_formation=away_lineup.formation,
        home_lineup=home_squad, away_lineup=away_squad, goals=list(goals),
        cards=list(cards), substitutions=list(substitutions),
    )
    nh = home_goals if home_goals is not None else sum(g.club_name == home.name for g in goals)
    na = away_goals if away_goals is not None else sum(g.club_name == away.name for g in goals)
    match = Match(home=home.name, away=away.name, home_goals=nh, away_goals=na, events=events)
    return match_result_from(match, events, home_lineup, away_lineup, date="2026-10-01"), home, away


@pytest.fixture
def match_synthetique():
    # Les noms viennent de l'effectif : h_x / a_x
    goals = [
        GoalEvent(club_name="Home FC", scorer="h_17", assist="h_14", minute=12),
        GoalEvent(club_name="Away FC", scorer="a_18", assist=None, minute=55),
    ]
    cards = [CardEvent(club_name="Home FC", player="h_3", minute=30, card_type="yellow")]
    subs = [SubstitutionEvent(club_name="Away FC", player_off="a_18", player_on="a_19", minute=70)]
    return _match(goals, cards, subs)


def _convertir(match_result, home, away, **kw):
    timeline = build_timeline(match_result)
    skipped: list = []
    dicts = timeline_to_events(timeline, match_sequence=3, home_squad=home.players, away_squad=away.players,
                               skipped=skipped, **kw)
    return timeline, dicts, skipped


class TestTimelineToEvents:
    def test_dicts_valides_au_contrat(self, match_synthetique):
        match_result, home, away = match_synthetique
        _, dicts, _ = _convertir(match_result, home, away)
        assert dicts
        for d in dicts:
            attendues = CLES_PAR_TYPE[d["event_type"]]
            assert set(d) <= attendues
            assert set(d) >= attendues - CLES_OPTIONNELLES
            assert d["is_home"] == (d["player_team"] == d["home_team"])
            assert d["match_sequence"] == 3
            assert all(isinstance(d[k], int) and not isinstance(d[k], bool) for k in d if k.endswith("_id") and k != "match_id")

    def test_but_carton_remplacement_convertis(self, match_synthetique):
        match_result, home, away = match_synthetique
        _, dicts, _ = _convertir(match_result, home, away, competition="L1", journee=4)
        buts = [d for d in dicts if d["event_type"] == "but"]
        assert [(b["minute"], b["player_id"], b.get("passeur_id")) for b in buts] == [(12, 1017, 1014), (55, 2018, None)]
        assert buts[0]["is_home"] is True and buts[1]["is_home"] is False
        [carton] = [d for d in dicts if d["event_type"] == "carton"]
        assert (carton["minute"], carton["player_id"], carton["outcome"], carton["player_team"]) == (30, 1003, "yellow", "Home FC")
        [remp] = [d for d in dicts if d["event_type"] == "remplacement"]
        assert (remp["player_id"], remp["entrant_id"], remp["sortant_id"]) == (2019, 2019, 2018)
        assert {d["competition"] for d in dicts} == {"L1"} and {d["journee"] for d in dicts} == {4}

    def test_tri_par_minute_et_event_id_rang(self, match_synthetique):
        match_result, home, away = match_synthetique
        timeline, dicts, skipped = _convertir(match_result, home, away)
        minutes = [d["minute"] for d in dicts]
        assert minutes == sorted(minutes)
        ids = [d["event_id"] for d in dicts]
        assert ids == sorted(set(ids))  # unique, croissant
        # sans ecarts : event_id = rang contigu ; sinon les ecarts laissent des trous
        total = len(timeline.events) + len(timeline.cards) + len(timeline.substitutions)
        assert len(dicts) + len(skipped) == total
        assert set(ids) | {i for i, _ in skipped} == set(range(total))

    def test_match_id_de_la_timeline_ou_surcharge(self, match_synthetique):
        match_result, home, away = match_synthetique
        timeline, dicts, _ = _convertir(match_result, home, away)
        assert {d["match_id"] for d in dicts} == {timeline.match_id}
        _, dicts2, _ = _convertir(match_result, home, away, match_id="M-42")
        assert {d["match_id"] for d in dicts2} == {"M-42"}

    def test_deterministe(self, match_synthetique):
        match_result, home, away = match_synthetique
        assert _convertir(match_result, home, away)[1] == _convertir(match_result, home, away)[1]
