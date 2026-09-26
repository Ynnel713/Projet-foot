from ligue1sim import faces


def test_face_path_returns_none_when_player_id_is_none():
    assert faces.face_path(None) is None


def test_face_path_returns_none_when_file_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    assert faces.face_path(12345) is None


def test_face_path_returns_the_file_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "FACES_DIR", tmp_path)
    photo = tmp_path / "42.png"
    photo.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = faces.face_path(42)

    assert result == photo
    assert result.is_file()
