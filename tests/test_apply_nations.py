"""Nationalités des nouveaux joueurs (scripts/apply_nations.py, ticket donnees-nouveaux-joueurs/09)."""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import apply_nations as an

BASE = ["ID", "Prénom", "Nom", "Nationalité", "Poste", "Club"]


def base_ws(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = an.SHEET
    ws.append(BASE)
    for r in rows:
        ws.append(r)
    return wb, ws


def nations_file(tmp_path, rows, header=an.HEADER):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    path = tmp_path / "nations.xlsx"
    wb.save(path)
    return path


def test_uniformisation_des_libelles():
    assert an.uniform("Bréso") == "Brésil" and an.uniform("Pays  Bas") == "Pays-Bas"
    assert an.uniform(" Tchéquie ") == "République tchèque" and an.uniform("Iles Feroé") == "Îles Féroé"
    assert an.uniform("Congo") == "Congo" and an.uniform("RD Congo") == "RD Congo"  # pays distincts
    assert an.uniform("Argentine") == "Argentine" and an.uniform(None) is None


def test_report_sur_les_seules_lignes_a_renseigner(tmp_path):
    _, ws = base_ws([[1, "Lionel", "Messi", "À renseigner", "AD / MOC / BU", "Inter Miami CF"],
                     [2, "Carlo", "Holse", "À renseigner", "MOC / MC", "St. Louis City SC"],
                     [3, "Julián", "Álvarez", "Argentine", "BU", "Atlético"],
                     [4, "Vitinha", None, "À renseigner", "MC", "PSG"]])
    path = nations_file(tmp_path, [["Messi", "Lionel", "AD / MOC / BU", "Inter Miami CF", "Argentine"],
                                   ["Holse", "Carlo", "MOC / MC", "St. Louis City SC", "Danemarl"],
                                   ["Álvarez", "Julián", "BU", "Atlético", "France"],  # déjà renseigné : intact
                                   ["Inconnu", "Joueur", "MC", "Nulle part", "Brésil"],
                                   ["", "Vitinha", "MC", "PSG", None]])  # nation vide : intact
    res = an.apply(ws, an.read_nations(path))
    assert [ws.cell(r, 4).value for r in range(2, 6)] == ["Argentine", "Danemark", "Argentine", "À renseigner"]
    assert [a[0] for a in res["appliqués"]] == [1, 2]
    assert len(res["déjà renseignés"]) == 1 and len(res["introuvables"]) == 1 and len(res["vides"]) == 1
    again = an.apply(ws, an.read_nations(path))  # idempotent
    assert again["appliqués"] == [] and again["inchangés"] == 2


def test_cle_ambigue_non_ecrite(tmp_path):
    _, ws = base_ws([[1, "Paulinho", None, "À renseigner", "BU", "Club"],
                     [2, "Paulinho", None, "À renseigner", "BU", "Club"]])
    path = nations_file(tmp_path, [["", "Paulinho", "BU", "Club", "Brésil"]])
    res = an.apply(ws, an.read_nations(path))
    assert res["ambigus"] and [ws.cell(r, 4).value for r in (2, 3)] == ["À renseigner"] * 2


def test_entete_inattendu(tmp_path):
    with pytest.raises(SystemExit):
        an.read_nations(nations_file(tmp_path, [], header=["Nom", "Prénom", "Club", "Pays", "X"]))


def test_fichier_uniformise(tmp_path):
    nations = an.read_nations(nations_file(tmp_path, [["Luiz", "David", "DC", "Pafos FC", "Bréso"]]))
    out = tmp_path / "out.xlsx"
    an.write_uniform(out, nations)
    ws = openpyxl.load_workbook(out).active
    assert [c.value for c in ws[1]] == an.HEADER and [c.value for c in ws[2]] == ["Luiz", "David", "DC", "Pafos FC",
                                                                               "Brésil"]
