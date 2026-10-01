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
from dataclasses import replace

from nlg_ingestion import EffectifClub, choisir_acteur_defensif, en_jeu_a, timeline_to_events

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


class TestResolutionPlayerId:
    """Pas de lookup en base : `Player.id` lu dans l'effectif, remplacants par (nom, club)."""

    def test_titulaire_par_id_direct(self):
        effectif = EffectifClub("Home FC", _effectif("h", 1000))
        assert effectif.player_id("h_17") == 1017

    def test_remplacant_par_nom_et_club(self, match_synthetique):
        # a_19 entre : le Lineup le reconstruit SANS id (narrative._player_from_stat), l'effectif le porte.
        match_result, home, away = match_synthetique
        entrant = [p for p in match_result.away_lineup.substitutes if p.name == "a_19"]
        assert not entrant or entrant[0].id is None
        _, dicts, _ = _convertir(match_result, home, away)
        [remp] = [d for d in dicts if d["event_type"] == "remplacement"]
        assert remp["entrant_id"] == 2019

    def test_homonymes_intra_club_valueerror(self):
        joueurs = _effectif("h", 1000) + [_joueur("DC", "h_3", 9999)]  # second h_3
        effectif = EffectifClub("Home FC", joueurs)
        with pytest.raises(ValueError, match="homonymes"):
            effectif.player_id("h_3")

    def test_homonyme_evenement_ecarte_pas_les_autres(self):
        goals = [GoalEvent(club_name="Home FC", scorer="h_17", assist=None, minute=12)]
        cards = [CardEvent(club_name="Home FC", player="h_3", minute=30, card_type="yellow")]
        match_result, home, away = _match(goals, cards)
        home.players.append(_joueur("DC", "h_3", 9999))
        _, dicts, skipped = _convertir(match_result, home, away)
        assert [d["event_type"] for d in dicts if d["event_type"] in ("but", "carton")] == ["but"]
        assert any("homonymes" in raison for _, raison in skipped)

    def test_player_id_none_refuse(self):
        effectif = EffectifClub("Home FC", [_joueur("BU", "h_sans_id", None)])
        with pytest.raises(ValueError, match="sans Player.id"):
            effectif.player_id("h_sans_id")

    def test_joueur_inconnu_refuse(self):
        with pytest.raises(ValueError, match="introuvable"):
            EffectifClub("Home FC", []).player_id("fantome")


class TestActeurDefensifSeede:
    """Gardien (arret) / defenseur (tacle, degagement) : le NarrativeEvent ne nomme que le tireur."""

    @staticmethod
    def _timeline(substitutions=(), cards=()):
        match_result, home, away = _match([GoalEvent(club_name="Home FC", scorer="h_17", assist=None, minute=12)],
                                          cards, substitutions)
        return build_timeline(match_result), EffectifClub("Away FC", away.players)

    @staticmethod
    def _gardien_titulaire(timeline):
        [gk] = [p for p in timeline.away_lineup.players if p.poste == "GK"]
        return gk

    def test_gardien_titulaire(self):
        timeline, away = self._timeline()
        gk = self._gardien_titulaire(timeline)
        assert choisir_acteur_defensif(timeline, "M", "Away FC", 40, "GK", away) == gk.id
        assert choisir_acteur_defensif(timeline, "M", "Away FC", 89, "GK", away) == gk.id

    def test_gardien_remplace(self):
        timeline0, _ = self._timeline()
        titulaire = self._gardien_titulaire(timeline0)
        remplacant = next(p for p in _effectif("a", 2000) if p.poste == "GK" and p.name != titulaire.name)
        sub = SubstitutionEvent(club_name="Away FC", player_off=titulaire.name, player_on=remplacant.name, minute=60)
        timeline, away = self._timeline([sub])
        assert choisir_acteur_defensif(timeline, "M", "Away FC", 59, "GK", away) == titulaire.id
        assert choisir_acteur_defensif(timeline, "M", "Away FC", 60, "GK", away) == titulaire.id  # le changement suit l'occasion
        assert choisir_acteur_defensif(timeline, "M", "Away FC", 61, "GK", away) == remplacant.id
        assert remplacant.name in en_jeu_a(timeline, "Away FC", 90)

    def test_gardien_expulse_sans_remplacant_aucun_gardien(self):
        timeline0, _ = self._timeline()
        titulaire = self._gardien_titulaire(timeline0)
        carton = CardEvent(club_name="Away FC", player=titulaire.name, minute=50, card_type="direct")
        timeline, away = self._timeline(cards=[carton])
        with pytest.raises(ValueError, match="aucun GK"):
            choisir_acteur_defensif(timeline, "M", "Away FC", 70, "GK", away)

    def test_aucun_gardien(self):
        timeline, away = self._timeline()
        sans_gk = replace(timeline.away_lineup, players=[p for p in timeline.away_lineup.players if p.poste != "GK"])
        timeline = replace(timeline, away_lineup=sans_gk)
        with pytest.raises(ValueError, match="aucun GK"):
            choisir_acteur_defensif(timeline, "M", "Away FC", 40, "GK", away)

    def test_defenseur_deterministe_et_en_jeu(self):
        timeline, away = self._timeline()
        defenseurs = {p.id for p in timeline.away_lineup.players if p.poste in ("DC", "LB", "RB")}
        choix = {choisir_acteur_defensif(timeline, "M", "Away FC", m, "DEF", away) for m in range(1, 90)}
        assert choix <= defenseurs and len(choix) > 1  # varie selon la minute
        assert choisir_acteur_defensif(timeline, "M", "Away FC", 33, "DEF", away) == choisir_acteur_defensif(timeline, "M", "Away FC", 33, "DEF", away)
        # la graine depend du match
        assert any(choisir_acteur_defensif(timeline, "M1", "Away FC", m, "DEF", away) != choisir_acteur_defensif(timeline, "M2", "Away FC", m, "DEF", away) for m in range(1, 90))

    def test_occasions_defensives_converties_cote_adverse(self):
        match_result, home, away = _match([GoalEvent(club_name="Home FC", scorer="h_17", assist=None, minute=12)])
        for seed_date in range(40):  # des fillers avec arret/tacle/degagement apparaissent vite
            match_result = replace(match_result, date=str(seed_date))
            timeline = build_timeline(match_result)
            dicts = timeline_to_events(timeline, match_sequence=1, home_squad=home.players, away_squad=away.players)
            for d in dicts:
                if d["event_type"] == "occasion" and d["outcome"] in ("arret", "tacle", "degagement"):
                    tireur_home = next(e.team == "Home FC" for e in timeline.events if e.minute == d["minute"] and e.event_type == "occasion")
                    assert d["is_home"] != tireur_home  # l'acteur est dans le camp oppose au tireur
                    assert d["player_team"] == ("Away FC" if tireur_home else "Home FC")
                    return
        pytest.fail("aucune occasion defensive generee")
