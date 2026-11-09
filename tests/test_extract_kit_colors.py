"""Extraction des couleurs de maillot (chantier kits-maillots, ticket KM-01) : maillots synthétiques, aucun fichier
téléchargé n'est lu ici."""

from __future__ import annotations

import io
import zlib

from PIL import Image

from scripts.extract_kit_colors import CLUB_BY_STEM, _de, _without_text, clubs_of, contact_sheet, kit_colors, read_packs


def _png(draw) -> bytes:
    im = Image.new("RGBA", (120, 120), (0, 0, 0, 0))  # fond transparent, comme les images des packs
    for x in range(10, 110):
        for y in range(10, 110):
            im.putpixel((x, y), draw(x, y))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def test_plain_shirt_has_no_secondary() -> None:
    primary, secondary = kit_colors(_png(lambda x, y: (20, 60, 200, 255)))
    assert _de(_rgb(primary), (20, 60, 200)) < 3 and secondary == primary


def test_striped_shirt_gives_both_colors() -> None:
    primary, secondary = kit_colors(_png(lambda x, y: (220, 20, 30, 255) if (x // 10) % 2 else (245, 245, 245, 255)))
    assert {_de(_rgb(primary), (220, 20, 30)) < 5, _de(_rgb(secondary), (245, 245, 245)) < 5} == {True} or \
        {_de(_rgb(secondary), (220, 20, 30)) < 5, _de(_rgb(primary), (245, 245, 245)) < 5} == {True}


def test_shaded_red_with_pink_highlight_stays_plain_red() -> None:
    # rouge ombré (deux tons) + reflet rose : le rose n'est pas une seconde couleur
    def draw(x, y):
        if y > 90:
            return (235, 150, 155, 255)  # reflet rose (20 % du maillot)
        return (200, 20, 30, 255) if x < 60 else (170, 15, 25, 255)

    primary, secondary = kit_colors(_png(draw))
    assert _de(_rgb(primary), (200, 20, 30)) < 15 and secondary == primary


def test_text_chunks_are_dropped_but_pixels_kept() -> None:
    png = _png(lambda x, y: (10, 120, 60, 255))
    data = b"Software\x00\x00" + zlib.compress(b"x" * 10_000_000)  # métadonnée énorme, refusée par Pillow
    chunk = len(data).to_bytes(4, "big") + b"zTXt" + data + zlib.crc32(b"zTXt" + data).to_bytes(4, "big")
    bloated = png[:33] + chunk + png[33:]  # juste après IHDR
    assert kit_colors(bloated) == kit_colors(png)
    assert len(_without_text(bloated)) == len(png)


def test_mapping_targets_existing_clubs_without_duplicate() -> None:
    from ligue1sim.clubs import load_all_clubs
    from ligue1sim.nations import load_national_teams
    from ligue1sim.season import CLUBS_PATH

    names = {o.name for o in load_all_clubs(CLUBS_PATH)}
    names |= {t.name for t in load_national_teams(CLUBS_PATH, complete_only=False)}
    targets = [club for key in CLUB_BY_STEM for club in clubs_of(key)]
    assert len(targets) == len(set(targets)) == 314  # 185 clubs + 129 sélections
    assert set(targets) <= names


def test_contact_sheet_is_drawn_from_a_pack(tmp_path) -> None:
    # Planche de contrôle (critère KM-01) : archive synthétique au format des packs, planche PNG produite
    import zipfile

    pack = tmp_path / "packs" / "Test_-_Pack.zip"
    pack.parent.mkdir()
    with zipfile.ZipFile(pack, "w") as z:
        z.writestr("Test - Pack/club_1.png", _png(lambda x, y: (220, 20, 30, 255)))
        z.writestr("Test - Pack/club_2.png", _png(lambda x, y: (245, 245, 245, 255)))
    packs = read_packs(pack.parent)
    assert set(packs["Test_-_Pack"]["club"]) == {"home", "away"}
    target = tmp_path / "planche.png"
    contact_sheet(pack.parent, packs, target)
    assert Image.open(target).size == (6 * 220, 96)
