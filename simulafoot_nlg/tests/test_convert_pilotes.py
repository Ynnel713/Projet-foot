"""scripts/convert_pilotes_to_yaml.py : pilotes_v2/*.py -> data/seed/v2/*.yml."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import scripts.convert_pilotes_to_yaml as convertisseur
from scripts.convert_commentary_xlsx_to_yaml import (
    PILOTES_METADATA,
    SLOTS_AUTORISES,
    CommentaryConversionError,
)
from scripts.convert_pilotes_to_yaml import DEFAULT_OUT_DIR, convertir_pilote, convertir_pilotes
from scripts.import_seed import DEFAULT_SCENARIOS_PATH, DEFAULT_SLOTS_PATH, import_seed
from scripts.init_db import init_db
from tests.test_pilotes_v2_garde_fous import _pilotes


def _nom(module) -> str:
    return module.__name__.rsplit(".", 1)[-1]


def _lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def test_un_yaml_par_pilote_nomme_comme_son_module_avec_le_bon_nombre_de_phrases(tmp_path):
    nombres = convertir_pilotes(tmp_path)

    assert sorted(p.name for p in tmp_path.glob("*.yml")) == sorted(f"{_nom(m)}.yml" for m in _pilotes())
    for module in _pilotes():
        attendu = len(module.DEFAUT) + len(getattr(module, "SURNOM", []))
        assert nombres[_nom(module).upper()] == attendu
    assert sum(nombres.values()) == 213


def test_reconversion_diff_vide(tmp_path):
    premiere, seconde = tmp_path / "1", tmp_path / "2"
    convertir_pilotes(premiere)
    convertir_pilotes(seconde)
    for fichier in premiere.glob("*.yml"):
        assert _lire(fichier) == _lire(seconde / fichier.name)


def test_les_yaml_commites_sont_a_jour_avec_les_modules(tmp_path):
    """Echoue quand un module pilotes_v2/*.py change sans regeneration de
    data/seed/v2/ (`uv run python scripts/convert_pilotes_to_yaml.py`)."""
    convertir_pilotes(tmp_path)
    for fichier in tmp_path.glob("*.yml"):
        assert _lire(fichier) == _lire(DEFAULT_OUT_DIR / fichier.name), fichier.name
    assert sorted(p.name for p in DEFAULT_OUT_DIR.glob("*.yml")) == sorted(p.name for p in tmp_path.glob("*.yml"))


def test_ne_touche_ni_fallback_ni_les_autres_fichiers_du_dossier(tmp_path):
    fallback = tmp_path / "fallback"
    fallback.mkdir()
    (fallback / "fallback.yml").write_text("- {scenario: BUT, text: x}\n", encoding="utf-8")
    sortie = tmp_path / "v2"
    sortie.mkdir()
    (sortie / "note.md").write_text("a la main", encoding="utf-8")

    convertir_pilotes(sortie)

    assert _lire(fallback / "fallback.yml") == "- {scenario: BUT, text: x}\n"
    assert _lire(sortie / "note.md") == "a la main"


def test_forme_du_yaml_variantes_cooldown_et_slots():
    (defense,) = convertir_pilote("defense")
    assert (defense["code"], defense["label"]) == ("DEFENSE", "Défense")
    defaut, surnom = defense["variants"]
    assert (defaut["code"], defaut["is_default"], defaut["label"]) == ("DEFAUT", True, "Variante par défaut")
    assert (surnom["code"], surnom["is_default"], surnom["label"]) == ("SURNOM", False, "Surnom")
    phrase = defaut["phrases"][0]
    assert phrase["cooldown_matches"] == PILOTES_METADATA["DEFENSE"].cooldown_matches
    assert {s["slot_name"] for s in phrase["slots"]} <= {"joueur", "adversaire"}
    assert all(s["expression"] for s in phrase["slots"])

    (ambiance,) = convertir_pilote("ambiance")
    assert [v["code"] for v in ambiance["variants"]] == ["DEFAUT"]


def test_la_banque_v1_et_les_8_pilotes_s_importent_ensemble(tmp_path):
    convertir_pilotes(tmp_path / "v2")
    db_path = tmp_path / "test.db"
    init_db(db_path=db_path)

    fichiers = [DEFAULT_SCENARIOS_PATH, *sorted((tmp_path / "v2").glob("*.yml"))]
    stats = import_seed(db_path, fichiers, DEFAULT_SLOTS_PATH, fallback_path=[])

    assert (stats.scenarios, stats.phrases) == (9 + 8, 281 + 213)
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM phrase_cooldowns").fetchone()[0] == 494
    finally:
        conn.close()


def test_un_slot_non_autorise_nomme_le_module_et_le_rang(monkeypatch):
    monkeypatch.setitem(SLOTS_AUTORISES, "DEFENSE", frozenset({"joueur"}))
    with pytest.raises(CommentaryConversionError, match=r"pilotes_v2/defense\.py.*adversaire"):
        convertir_pilote("defense")


def test_un_move_hors_reservoir_est_refuse_comme_dans_le_chemin_classeur(monkeypatch):
    faux = SimpleNamespace(DEFAUT=[("{joueur} tacle", [("preferred_moves", "contient", "Faux Move")])])
    monkeypatch.setattr(convertisseur, "_module_pilote", lambda nom: faux)
    with pytest.raises(CommentaryConversionError, match=r"pilotes_v2/defense\.py.*Faux Move"):
        convertir_pilote("defense")


def test_un_module_sans_entree_dans_pilotes_metadata_est_refuse():
    with pytest.raises(CommentaryConversionError, match="PILOTES_METADATA"):
        convertir_pilote("inconnu")


def test_les_yaml_ecrits_se_relisent_en_une_liste_d_un_scenario(tmp_path):
    convertir_pilotes(tmp_path)
    for fichier in tmp_path.glob("*.yml"):
        donnees = yaml.safe_load(_lire(fichier))
        assert isinstance(donnees, list) and len(donnees) == 1
