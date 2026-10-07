"""Tests des ajouts à api/serializers.py pour l'écran équipe de la PWA
(player_out/roster_out, 26/09/2026) -- le reste du fichier (match_out,
standings, pitch_view...) n'a pas de couverture existante, pas dans le
périmètre de cette tâche (voir le rapport de tâche)."""

from ligue1sim import faces
from ligue1sim.clubs import Club
from ligue1sim.players import Player

from api.serializers import player_out, roster_out


def _player(**overrides) -> Player:
    defaults = dict(
        prenom="Joueur",
        nom="Test",
        nationalite="France",
        age=25,
        poste="MC",
        note=70.0,
        club="Club Test",
        championnat="Ligue 1",
    )
    defaults.update(overrides)
    return Player(**defaults)


def test_player_out_photo_url_none_when_no_face(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    player = _player(id=1)

    out = player_out(player)

    assert out.photo_url is None
    assert out.name == "Joueur Test"


def test_player_out_exposes_poste_secondaire_as_a_list(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    player = _player(id=1, poste_secondaire=("MDC", "MC"))

    out = player_out(player)

    assert out.poste_secondaire == ["MDC", "MC"]


def test_player_out_photo_url_points_at_media_faces_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    (tmp_path / "7.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    player = _player(id=7)

    out = player_out(player)

    assert out.photo_url == "/media/faces/7.png"


def test_roster_out_aggregates_note_age_and_valeur(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    club = Club(
        name="Club Test",
        players=[
            _player(id=1, note=80.0, age=20, valeur_marchande=10.0),
            _player(id=2, note=60.0, age=30, valeur_marchande=None),
        ],
    )

    out = roster_out(club)

    assert out.club == "Club Test"
    assert out.championnat == "Ligue 1"
    assert out.note == 70.0  # (80 + 60) / 2
    assert out.age_moyen == 25.0  # (20 + 30) / 2
    assert out.valeur_totale == 10.0  # seul le joueur avec une valeur connue compte
    assert len(out.players) == 2
    assert out.color  # une couleur (hex) est toujours renvoyée, même pour un club inconnu de kits.CLUB_KIT


def test_roster_out_valeur_totale_none_when_no_player_has_a_value(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    club = Club(name="Club Test", players=[_player(id=1, valeur_marchande=None)])

    out = roster_out(club)

    assert out.valeur_totale is None


def test_roster_out_empty_club_does_not_crash():
    club = Club(name="Club Vide", players=[])

    out = roster_out(club)

    assert out.note == 0.0
    assert out.age_moyen == 0.0
    assert out.valeur_totale is None
    assert out.championnat == ""
    assert out.players == []
