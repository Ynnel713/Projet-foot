"""Couleurs de maillot réelles fusionnées dans `kits.CLUB_KIT` (chantier kits-maillots, ticket KM-02)."""

from __future__ import annotations

from pathlib import Path

from ligue1sim.kit_colors_data import EXTRACTED_KITS
from ligue1sim.kits import CLUB_KIT, Kit, kit_for
from scripts.extract_kit_colors import write_module


def test_covered_clubs_take_extracted_home_and_away_colors() -> None:
    assert len(EXTRACTED_KITS) == 314  # 185 clubs + 129 sélections (KM-03)
    for club, (home, home2, away, away2) in EXTRACTED_KITS.items():
        kit = kit_for(club)
        assert (kit.primary, kit.secondary, kit.away_primary, kit.away_secondary) == (home, home2, away, away2)


def test_drawn_pattern_is_kept_and_new_clubs_get_trim() -> None:
    assert kit_for("Paris Saint-Germain").pattern == "center_stripe"
    assert kit_for("RC Lens").pattern == "horizontal_stripes"
    assert kit_for("Derby County").pattern == "trim"  # club sans kit avant le chantier


def test_clubs_outside_the_packs_keep_their_kit() -> None:
    assert kit_for("AEK Athens") == Kit("#ffe100", "#000000", "halves")
    assert kit_for("Club inexistant") == Kit("#6b7280", "#d1d5db", "trim")
    assert len(CLUB_KIT) == 341  # 160 kits d'avant + 52 clubs nouveaux + 129 sélections


def test_generated_module_is_reproduced_exactly(tmp_path: Path) -> None:
    clubs = {club: {"home": [h, h2], "away": [a, a2]} for club, (h, h2, a, a2) in EXTRACTED_KITS.items()}
    target = tmp_path / "kit_colors_data.py"
    write_module(clubs, target)
    source = Path(__file__).resolve().parents[1] / "src" / "ligue1sim" / "kit_colors_data.py"
    # fins de ligne normalisées : un checkout en CRLF ne doit pas faire échouer le test (réserve A3 de l'expert)
    assert target.read_bytes() == source.read_bytes().replace(b"\r\n", b"\n")


def test_every_national_team_has_its_real_colors() -> None:
    # Sélections nationales (ticket KM-03) : les 129 du jeu, plus aucune en gris par défaut
    from ligue1sim.nations import load_national_teams
    from ligue1sim.season import CLUBS_PATH

    teams = [t.name for t in load_national_teams(CLUBS_PATH, complete_only=False)]
    assert len(teams) == 129 and all(name in EXTRACTED_KITS for name in teams)
    france = kit_for("🇫🇷 France")
    assert (france.primary, france.away_primary) == EXTRACTED_KITS["🇫🇷 France"][::2]
    assert france.pattern == "trim"


def _distance(a: str, b: str) -> float:
    return sum((int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) ** 2 for i in (1, 3, 5)) ** 0.5


def test_clash_falls_back_on_the_real_away_kit() -> None:
    # Réserve A1 de l'expert (revue de clôture du 09/11/2026) : maillot uni (secondaire = principale), l'extérieur
    # sort son vrai maillot extérieur au lieu de rester de la même couleur que le domicile.
    from ligue1sim.kits import match_kit_colors

    for home, away in [("Arsenal FC", "Manchester United"), ("🇨🇭 Suisse", "🇩🇰 Danemark")]:
        (home_fill, _), (away_fill, away_border) = match_kit_colors(home, away)
        assert _distance(home_fill, away_fill) >= 90
        assert away_border == kit_for(away).primary


def test_clash_rule_picks_a_contrasted_candidate_whenever_one_exists() -> None:
    from ligue1sim.kits import match_kit_colors

    for home in CLUB_KIT:
        for away in CLUB_KIT:
            if home == away:
                continue
            h, a = CLUB_KIT[home], CLUB_KIT[away]
            if _distance(h.primary, a.primary) >= 90:
                continue
            candidates = [c for c in (a.secondary, a.away_primary, a.away_secondary) if c]
            (_, _), (fill, _) = match_kit_colors(home, away)
            if any(_distance(h.primary, c) >= 90 for c in candidates):
                assert _distance(h.primary, fill) >= 90, (home, away)
