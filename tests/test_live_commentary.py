"""api/live_commentary.py : fil « commentaire en direct » d'un match, a partir des evenements reels du moteur."""

from ligue1sim.events import CardEvent, GoalEvent, MatchEvents, PenaltyMissedEvent, SubstitutionEvent

from api.live_commentary import build_live_feed


def _events(**kw) -> MatchEvents:
    return MatchEvents(home_formation="4-4-2", away_formation="4-3-3", home_lineup=[], away_lineup=[], **kw)


def _texte(event) -> str:
    return "".join(t for t, _ in event.parts)


def _joueurs(event) -> list[str]:
    return [t for t, est_joueur in event.parts if est_joueur]


def test_fil_chronologique_avec_coup_d_envoi_et_fin():
    events = _events(
        goals=[GoalEvent(club_name="Nice", scorer="G. Laborde", assist="M. Sanson", minute=23)],
        cards=[CardEvent(club_name="Le Mans", player="M. Boissier", minute=47, card_type="yellow")],
        substitutions=[SubstitutionEvent(club_name="Nice", player_off="S. Diop", player_on="E. Guessand", minute=68)],
    )
    feed = build_live_feed(events, "Le Mans", "Nice")
    assert [(e.minute, e.kind) for e in feed] == [(0, "start"), (23, "goal"), (47, "yellow"), (68, "sub"), (90, "end")]
    assert [e.title for e in feed[1:4]] == ["BUT !", "CARTON JAUNE", "REMPLACEMENT"]
    assert [e.side for e in feed[1:4]] == ["away", "home", "away"]


def test_les_noms_de_joueurs_sont_marques_pas_les_clubs():
    events = _events(substitutions=[SubstitutionEvent(club_name="Nice", player_off="S. Diop", player_on="E. Guessand", minute=68)])
    sub = next(e for e in build_live_feed(events, "Le Mans", "Nice") if e.kind == "sub")
    assert set(_joueurs(sub)) == {"E. Guessand", "S. Diop"}
    assert "Nice" in _texte(sub) and "Nice" not in _joueurs(sub)


def test_texte_du_but_suit_le_score_ouverture_egalisation_avantage_ecart():
    goals = [
        GoalEvent(club_name="Nice", scorer="A", assist=None, minute=10),  # 0-0 -> 0-1 : ouverture
        GoalEvent(club_name="Le Mans", scorer="B", assist=None, minute=20),  # 0-1 -> 1-1 : egalisation
        GoalEvent(club_name="Nice", scorer="C", assist=None, minute=30),  # 1-1 -> 1-2 : avantage
        GoalEvent(club_name="Nice", scorer="D", assist=None, minute=40),  # 1-2 -> 1-3 : ecart creuse
        GoalEvent(club_name="Le Mans", scorer="E", assist=None, minute=50),  # 1-3 -> 2-3 : ecart reduit
    ]
    textes = [_texte(e) for e in build_live_feed(_events(goals=goals), "Le Mans", "Nice") if e.kind == "goal"]
    assert any(mot in textes[0] for mot in ("ouvre le score",))
    assert "égalis" in textes[1] or "hauteur" in textes[1]
    assert "avantage" in textes[2] or "devant" in textes[2]
    assert "creuse" in textes[3] or "double la mise" in textes[3]
    assert "réduit" in textes[4] or "relance" in textes[4]


def test_passeur_et_penalty():
    goals = [
        GoalEvent(club_name="Nice", scorer="G. Laborde", assist="M. Sanson", minute=23),
        GoalEvent(club_name="Le Mans", scorer="K. Ngom", assist=None, minute=60, penalty=True),
    ]
    buts = [e for e in build_live_feed(_events(goals=goals), "Le Mans", "Nice") if e.kind == "goal"]
    assert "M. Sanson" in _joueurs(buts[0]) and "Passe décisive" in _texte(buts[0])
    assert "penalty" in _texte(buts[1]) and "Passe" not in _texte(buts[1])


def test_elision_du_passeur():
    goals = [
        GoalEvent(club_name="Nice", scorer="A", assist="Axel Tuanzebe", minute=10),
        GoalEvent(club_name="Nice", scorer="B", assist="Romain Faivre", minute=20),
    ]
    buts = [_texte(e) for e in build_live_feed(_events(goals=goals), "Le Mans", "Nice") if e.kind == "goal"]
    assert "Passe décisive d'Axel Tuanzebe." in buts[0] and "Passe décisive de Romain Faivre." in buts[1]


def test_cartons_et_penalty_manque():
    events = _events(
        cards=[
            CardEvent(club_name="Nice", player="X", minute=50, card_type="second_yellow"),
            CardEvent(club_name="Nice", player="Y", minute=60, card_type="direct"),
        ],
        penalties_missed=[PenaltyMissedEvent(club_name="Le Mans", player="Z", minute=70)],
    )
    feed = {e.kind: e for e in build_live_feed(events, "Le Mans", "Nice")}
    assert feed["second_yellow"].title == "DEUXIÈME JAUNE" and "exclu" in _texte(feed["second_yellow"])
    assert feed["red"].title == "CARTON ROUGE" and "dix" in _texte(feed["red"])
    assert feed["penalty_missed"].title == "PENALTY MANQUÉ" and _joueurs(feed["penalty_missed"]) == ["Z"]


def test_ordre_a_minute_egale_et_determinisme():
    events = _events(
        goals=[GoalEvent(club_name="Nice", scorer="A", assist=None, minute=47)],
        cards=[CardEvent(club_name="Le Mans", player="B", minute=47, card_type="yellow")],
        substitutions=[SubstitutionEvent(club_name="Nice", player_off="C", player_on="D", minute=47)],
    )
    kinds = [e.kind for e in build_live_feed(events, "Le Mans", "Nice")]
    assert kinds == ["start", "goal", "yellow", "sub", "end"]
    assert build_live_feed(events, "Le Mans", "Nice") == build_live_feed(events, "Le Mans", "Nice")


def test_match_sans_evenement_garde_un_fil_non_vide():
    assert [e.kind for e in build_live_feed(_events(), "A", "B")] == ["start", "end"]
