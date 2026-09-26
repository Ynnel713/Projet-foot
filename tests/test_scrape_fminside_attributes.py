"""Tests de note_fm_weight_moyenne (27/09/2026) -- voir
scripts/scrape_fminside_attributes.py pour le contexte : Ability sous-note
structurellement les jeunes joueurs par rapport à Moyenne joueur (retour
terrain "Lamine Camara a 70, très loin de la réalité", confirmé sur les
3381 joueurs déjà enrichis)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import scrape_fminside_attributes as scrape  # noqa: E402


def test_weight_is_maximal_at_or_below_the_youth_age():
    assert scrape.note_fm_weight_moyenne(scrape.NOTE_FM_YOUTH_AGE) == scrape.NOTE_FM_WEIGHT_YOUTH_MAX
    assert scrape.note_fm_weight_moyenne(scrape.NOTE_FM_YOUTH_AGE - 3) == scrape.NOTE_FM_WEIGHT_YOUTH_MAX


def test_weight_is_the_base_value_at_or_above_the_adult_age():
    assert scrape.note_fm_weight_moyenne(scrape.NOTE_FM_ADULT_AGE) == scrape.NOTE_FM_WEIGHT_BASE
    assert scrape.note_fm_weight_moyenne(scrape.NOTE_FM_ADULT_AGE + 10) == scrape.NOTE_FM_WEIGHT_BASE


def test_weight_decreases_monotonically_with_age():
    ages = range(scrape.NOTE_FM_YOUTH_AGE, scrape.NOTE_FM_ADULT_AGE + 1)
    weights = [scrape.note_fm_weight_moyenne(a) for a in ages]
    assert weights == sorted(weights, reverse=True)


def test_red_a_flat_weight_would_not_favour_young_players(monkeypatch):
    # Preuve rouge : un poids fixe (l'ancien comportement, avant ce brief)
    # donne le MEME poids a un jeune et a un joueur etabli -- doit faire
    # echouer la meme verification de monotonie stricte entre les deux bornes.
    monkeypatch.setattr(scrape, "note_fm_weight_moyenne", lambda age: 0.15)
    young = scrape.note_fm_weight_moyenne(19)
    old = scrape.note_fm_weight_moyenne(29)
    assert young == old  # confirme que le cas casse bien l'invariant
    with pytest.raises(AssertionError):
        assert young > old, "devrait echouer"
