"""Import des attributs d'une sauvegarde FM (scripts/import_fmsave_attributes.py, ticket
donnees-nouveaux-joueurs/06a). Hors ligne : CSV et classeur construits dans le test."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import import_fmsave_attributes as imp
from scrape_fminside_attributes import ATTRIBUTES

SAVE_ATTR_COLS = [
    "attributes_corners", "attributes_crossing", "attributes_dribbling", "attributes_finishing",
    "attributes_first_touch", "attributes_free_kick_taking", "attributes_heading", "attributes_long_shots",
    "attributes_long_throws", "attributes_marking", "attributes_passing", "attributes_penalty_taking",
    "attributes_tackling", "attributes_technique", "attributes_aggression", "attributes_anticipation",
    "attributes_bravery", "attributes_composure", "attributes_concentration", "attributes_decisions",
    "attributes_determination", "attributes_flair", "attributes_leadership", "attributes_off_the_ball",
    "attributes_positioning", "attributes_teamwork", "attributes_vision", "attributes_work_rate",
    "attributes_acceleration", "attributes_agility", "attributes_balance", "attributes_jumping_reach",
    "attributes_natural_fitness", "attributes_pace", "attributes_stamina", "attributes_strength",
    "attributes_aerial_reach", "attributes_command_of_area", "attributes_communication",
    "attributes_eccentricity", "attributes_handling", "attributes_kicking", "attributes_one_on_ones",
    "attributes_punching", "attributes_reflexes", "attributes_rushing_out", "attributes_throwing",
]  # les 47 colonnes d'attributs de l'export fmsave-list
HEADER = ["shortlisted", "name", "age", "natural_positions", "club_name", "transfer_value", "height_cm", "left_foot", "right_foot",
          *SAVE_ATTR_COLS]
BASE_HEADERS = ["ID", "Prénom", "Nom", "Moyenne FM", "Nationalité", "Âge", "Poste", "Club", "Championnat",
                "Pieds", "Moyenne joueur", *ATTRIBUTES, "FMInside URL", "Postes FM naturels", "Taille FM (cm)",
                "Weak foot (/5)"]


def save_row(name, age, positions, club="Club", value=12, left=8, right=20, height=180, **over):
    row = {"shortlisted": "", "name": name, "age": age, "natural_positions": positions, "club_name": club,
           "height_cm": height, "left_foot": left, "right_foot": right}
    row.update({c: value for c in SAVE_ATTR_COLS})
    row.update(over)
    return row


def write_save(tmp_path, rows):
    path = tmp_path / "fmsave-list.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    return path


def base_player(pid, first, last, age, poste, attrs=True, **cols):
    gk = poste.split("/")[0].strip() == "GK"
    values = {"ID": pid, "Prénom": first, "Nom": last, "Âge": age, "Poste": poste, "Club": "Club",
              "Championnat": "Ligue 1", "Moyenne FM": 70, "Moyenne joueur": 70, "Nationalité": "France"}
    if attrs:
        values.update({a: 50 for a in (imp.GK_SET if gk else imp.FIELD_SET)})
        values.update({"Weak foot (/5)": 2, "Taille FM (cm)": 175})
    values.update(cols)
    return values


def workbook(players):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = imp.SHEET
    ws.append(BASE_HEADERS)
    for p in players:
        ws.append([p.get(h) for h in BASE_HEADERS])
    return wb, ws


def cells(ws):
    return [[c.value for c in row] for row in ws.iter_rows()]


# --- Conversions ------------------------------------------------------------------------------
def test_colonnes_de_la_sauvegarde_couvrent_les_47_attributs(tmp_path):
    assert len(set(SAVE_ATTR_COLS)) == 47
    save = imp.read_save(write_save(tmp_path, [save_row("A B", 25, "MC")]))
    assert set(save[0].attrs) == set(ATTRIBUTES)


def test_colonne_inconnue_arrete(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("name,age,attributes_bogus\nA,20,3\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        imp.read_save(path)


def test_echelle_pieds_et_weak_foot():
    assert [imp.to_base_scale(v) for v in (1, 12, 19, 20)] == [5, 60, 95, 99]
    assert [imp.weak_foot(v, 20) for v in (1, 4, 5, 8, 9, 12, 13, 20)] == [1, 1, 2, 2, 3, 3, 4, 4]
    assert imp.strong_foot(8, 20) == "D" and imp.strong_foot(20, 8) == "G" and imp.strong_foot(15, 15) is None


def test_jeux_de_36_attributs():
    assert len(imp.FIELD_SET) == len(imp.GK_SET) == 36
    assert "Handling" not in imp.FIELD_SET and "Finishing" not in imp.GK_SET and "Passing" in imp.GK_SET


# --- Correspondance ---------------------------------------------------------------------------
def test_correspondance_nom_age_poste_et_conflits(tmp_path):
    save = imp.read_save(write_save(tmp_path, [
        save_row("Kylian Mbappé", 27, "STC AML"),
        save_row("Jean Dupont", 30, "MC"), save_row("Jean Dupont", 31, "DC"),  # homonymes, âges proches
        save_row("Paul Gardien", 25, "GK"),
        save_row("Max Avant", 22, "DC"),  # attaquant dans la base : 3 crans, écarté
        save_row("Luc Lateral", 23, "DM MC"),  # latéral devenu milieu défensif : 2 crans, accepté
        save_row("Rodri", 29, "DM"),
        save_row("Vieux Joueur", 40, "MC"),  # âge trop différent
    ]))
    _, ws = workbook([
        base_player(1, "Kylian", "Mbappe", 27, "BU / AG"),
        base_player(2, "Jean", "Dupont", 30, "MC"),
        base_player(3, "Paul", "Gardien", 25, "DC"),  # gardien d'un seul côté
        base_player(4, "Max", "Avant", 22, "BU"),
        base_player(5, "Luc", "Lateral", 23, "LB"),
        base_player(6, "Rodri", None, 30, "MDC"),
        base_player(7, "Rodri", None, 29, "MDC"),  # deux joueurs de la base pour une ligne
        base_player(8, "Vieux", "Joueur", 37, "MC"),
    ])
    h = {c.value: c.column for c in ws[1]}
    status = {m.pid: m.status for m in imp.match_players(ws, h, save)}
    assert status == {1: "RETROUVÉ", 2: "HOMONYMES", 3: "POSTE_INCOMPATIBLE", 4: "POSTE_INCOMPATIBLE",
                      5: "RETROUVÉ", 6: "CONFLIT", 7: "CONFLIT", 8: "ABSENT"}


# --- Modifications ----------------------------------------------------------------------------
def test_remplacement_dans_le_jeu_du_metier_et_pieds(tmp_path):
    save = imp.read_save(write_save(tmp_path, [
        save_row("Joueur Champ", 25, "MC", value=14, left=20, right=9, height=190),
        save_row("Paul Gardien", 25, "GK", value=13, left=7, right=15),
        save_row("Sans Attributs", 21, "DC", value=10, left=6, right=18, height=185),
        save_row("Deux Pieds", 24, "MC", value=12, left=16, right=16),
    ]))
    _, ws = workbook([
        base_player(1, "Joueur", "Champ", 25, "MC", Pieds="D"),
        base_player(2, "Paul", "Gardien", 25, "GK"),
        base_player(3, "Sans", "Attributs", 21, "DC", attrs=False),
        base_player(4, "Deux", "Pieds", 24, "MC", Pieds="G"),
    ])
    rows_before = ws.max_row
    _, plans = imp.run(ws, save, write=True)
    h = {c.value: c.column for c in ws[1]}

    def val(r, col):
        return ws.cell(r, h[col]).value

    assert ws.max_row == rows_before  # aucune ligne ajoutée
    # joueur de champ : 36 attributs à 70 (14 × 5), aucun attribut de gardien écrit
    assert all(val(2, a) == 70 for a in imp.FIELD_SET) and all(val(2, a) is None for a in imp.GOALKEEPING)
    assert val(2, "Pieds") == "G" and val(2, "Weak foot (/5)") == 3  # gauche 20, droit 9
    assert val(2, "Taille FM (cm)") == 175  # déjà remplie : gardée
    # gardien : jeu de gardien, aucun attribut propre au jeu de champ
    assert all(val(3, a) == 65 for a in imp.GK_SET) and all(val(3, a) is None for a in imp.OUTFIELD_ONLY)
    # sans attributs : reçoit le jeu de son métier, taille remplie
    assert all(val(4, a) == 50 for a in imp.FIELD_SET) and all(val(4, a) is None for a in imp.GOALKEEPING)
    assert val(4, "Taille FM (cm)") == 185 and val(4, "Pieds") == "D" and val(4, "Weak foot (/5)") == 2
    # deux pieds égaux : pied fort actuel gardé, rien d'inventé
    assert val(5, "Pieds") == "G" and val(5, "Weak foot (/5)") == 4
    assert "Pieds" not in plans[5]


def test_essai_a_blanc_ne_touche_pas_le_classeur(tmp_path):
    save = imp.read_save(write_save(tmp_path, [save_row("Joueur Champ", 25, "MC", value=14)]))
    _, ws = workbook([base_player(1, "Joueur", "Champ", 25, "MC")])
    before = cells(ws)
    matches, plans = imp.run(ws, save, write=False)
    assert cells(ws) == before and plans[2]["Passing"] == (50, 70)
    assert any("Joueurs modifiés : 1" in line for line in imp.summary(matches, plans))


def test_commande_par_defaut_laisse_le_fichier_intact(tmp_path, monkeypatch):
    src = write_save(tmp_path, [save_row("Joueur Champ", 25, "MC", value=14)])
    wb, _ = workbook([base_player(1, "Joueur", "Champ", 25, "MC")])
    xlsx = tmp_path / "joueurs.xlsx"
    wb.save(xlsx)
    before = xlsx.read_bytes()
    monkeypatch.setattr(sys, "argv", ["x", "--source", str(src), "--excel", str(xlsx)])
    imp.main()
    assert xlsx.read_bytes() == before
    report = (tmp_path / "fmsave_import_report.csv").read_text(encoding="utf-8-sig")
    assert "RETROUVÉ" in report and "Joueur Champ" in report
    monkeypatch.setattr(sys, "argv", ["x", "--source", str(src), "--excel", str(xlsx), "--write"])
    imp.main()
    ws = openpyxl.load_workbook(xlsx)[imp.SHEET]
    h = {c.value: c.column for c in ws[1]}
    assert ws.cell(2, h["Passing"]).value == 70


# --- Départage des incertitudes (club, puis valeur marchande) ---------------------------------
def test_meme_club_malgre_deux_ecritures():
    assert imp.same_club("US Lecce", "Unione Sportiva Lecce")
    assert imp.same_club("FC Porto", "Futebol Clube do Porto")
    assert imp.same_club("Paris Saint-Germain", "Paris Saint-Germain")
    assert not imp.same_club("São Paulo FC", "Futebol Clube do Porto")
    assert not imp.same_club("Real Madrid", "Real Betis")
    assert not imp.same_club("SE Palmeiras", "SEP") and not imp.same_club("", "Lorient")


def test_valeur_marchande_du_classeur():
    assert imp.parse_value("€9.00m") == 9e6 and imp.parse_value("€600k") == 6e5 and imp.parse_value("-") is None
    assert imp.close_value(9e6, 12.3e6) and not imp.close_value(3e5, 12.3e6) and not imp.close_value(None, 1e6)


def test_homonymes_et_conflits_departages_par_le_club_puis_la_valeur(tmp_path):
    save = imp.read_save(write_save(tmp_path, [
        save_row("Mohamed Bamba", 24, "STC", club="FC Lorient"), save_row("Mohamed Bamba", 23, "MC DM", club=""),
        save_row("Vitinha", 26, "DM MC", club="Paris Saint-Germain"),
        save_row("Paulinho", 26, "STC AML", club="SEP", transfer_value=12343626),
        save_row("Jean Doublon", 25, "MC", club="Club C", transfer_value=1e6),
    ]))
    BASE = [*BASE_HEADERS, "Valeur marchande"]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(BASE)
    players = [
        base_player(1, "Mohamed", "Bamba", 24, "BU", Club="FC Lorient"),
        base_player(2, "Vitinha", None, 26, "MDC", Club="Paris Saint-Germain"),
        base_player(3, "Vitinha", None, 26, "BU", Club="Genoa CFC"),
        base_player(4, "Paulinho", None, 26, "SA", Club="SE Palmeiras", **{"Valeur marchande": "€9.00m"}),
        base_player(5, "Paulinho", None, 26, "BU", Club="Académico de Viseu", **{"Valeur marchande": "€300k"}),
        base_player(6, "Jean", "Doublon", 25, "MC", Club="Club A", **{"Valeur marchande": "€1.00m"}),
        base_player(7, "Jean", "Doublon", 25, "MC", Club="Club B", **{"Valeur marchande": "€1.50m"}),
    ]
    for p in players:
        ws.append([p.get(h) for h in BASE])
    h = {c.value: c.column for c in ws[1]}
    res = {m.pid: (m.status, m.save.club if m.save else None) for m in imp.match_players(ws, h, save)}
    assert res[1] == ("RETROUVÉ", "FC Lorient")  # homonyme de la sauvegarde départagé par le club
    assert res[2] == ("RETROUVÉ", "Paris Saint-Germain") and res[3][0] == "CONFLIT"  # conflit : club
    assert res[4] == ("RETROUVÉ", "SEP") and res[5][0] == "CONFLIT"  # conflit : valeur marchande
    assert res[6][0] == res[7][0] == "CONFLIT"  # ni club ni valeur ne départagent : rien d'écrit
