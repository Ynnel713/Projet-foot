"""Ajout de joueurs depuis une sauvegarde FM (scripts/add_fmsave_players.py, ticket
donnees-nouveaux-joueurs/07a). Hors ligne : CSV et classeur construits dans le test."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import add_fmsave_players as add
from import_fmsave_attributes import (
    FIELD_SET,
    GK_SET,
    GOALKEEPING,
    OUTFIELD_ONLY,
)
from scrape_fminside_attributes import ATTRIBUTES, NEW_COLUMNS, TABLE_NAME

ATTR_COLS = [
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
]
SAVE_HEADER = ["shortlisted", "name", "age", "natural_positions", "ability_current", "club_name",
               "transfer_value", "left_foot", "right_foot", *ATTR_COLS, "height_cm"]
BASE_HEADERS = ["ID", "Prénom", "Nom", "Moyenne FM", "Nationalité", "Âge", "Poste", "Club", "Championnat",
                "Valeur marchande", "Statut", "Catégorie", "Pieds", "Moyenne joueur", "Taille (cm)", *NEW_COLUMNS]


def srow(name, age, positions="MC", club="Club", value=12, left=8, right=20, height=181):
    row = {"shortlisted": "", "name": name, "age": age, "natural_positions": positions, "ability_current": 150,
           "club_name": club, "transfer_value": 1000000, "left_foot": left, "right_foot": right,
           "height_cm": height}
    row.update({c: value for c in ATTR_COLS})
    return row


def write_save(tmp_path, rows):
    path = tmp_path / "fmsave-list-hommes.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=SAVE_HEADER)
        w.writeheader()
        w.writerows(rows)
    return add.read_save(path), path


def bplayer(pid, first, last, age, club, champ="Ligue 1", poste="MC"):
    return {"ID": pid, "Prénom": first, "Nom": last, "Âge": age, "Club": club, "Championnat": champ,
            "Poste": poste, "Nationalité": "France", "Moyenne FM": 70, "Moyenne joueur": 70,
            **{a: 50 for a in FIELD_SET}}


def workbook(players):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = add.SHEET
    ws.append(BASE_HEADERS)
    for p in players:
        ws.append([p.get(h) for h in BASE_HEADERS])
    ref = f"A1:{openpyxl.utils.get_column_letter(len(BASE_HEADERS))}{ws.max_row}"
    table = Table(displayName=TABLE_NAME, ref=ref, autoFilter=AutoFilter(ref=ref))
    table._initialise_columns()
    ws.add_table(table)
    return wb, ws


def napoli_base(extra=()):
    return [bplayer(1, "Alex", "Meret", 29, "SSC Napoli", "Serie A"),
            bplayer(2, "Giovanni", "Di Lorenzo", 33, "SSC Napoli", "Serie A"),
            bplayer(3, "Frank", "Anguissa", 30, "SSC Napoli", "Serie A"),
            bplayer(4, "Alexsandro", None, 27, "LOSC Lille"),
            bplayer(5, "Ben", "White", 28, "Arsenal FC", "Premier League"),
            bplayer(6, "Lautaro", "Martínez", 29, "Inter Milan", "Serie A"),
            *extra]


# --- Conversions et correspondances -----------------------------------------------------------
def test_postes_au_format_du_classeur():
    sp = add.SavePlayer(0, "X", 20, ["STC", "AML"], "C", 180, 10, 20)
    assert add.save_postes(sp) == "BU / AG" and add.fm_natural(sp) == "ST, AML"


def test_correspondance_de_clubs_apprise(tmp_path):
    save, _ = write_save(tmp_path, [srow("Alex Meret", 29, "GK", "Parthenope"),
                                    srow("Giovanni Di Lorenzo", 33, "DR", "Parthenope"),
                                    srow("Nouveau Napolitain", 21, "MC", "Parthenope")])
    _, ws = workbook(napoli_base())
    h = {c.value: c.column for c in ws[1]}
    m = add.BaseMatcher(add.load_players(ws)[1], add.read_all_clubs(ws, h), save)
    assert m.alias["Parthenope"] == "SSC Napoli"
    assert m.club_for("Parthenope") == "SSC Napoli" and m.club_for("") == add.FREE_AGENTS


def test_deja_present_et_cas_douteux(tmp_path):
    save, _ = write_save(tmp_path, [
        srow("Alex Meret", 29, "GK", "Parthenope"), srow("Giovanni Di Lorenzo", 33, "DR", "Parthenope"),
        srow("Alexsandro Ribeiro", 27, "DC", "LOSC Lille"),            # nom d'usage seul du classeur
        srow("Benjamin White", 28, "DR", "Arsenal FC"),          # même nom de famille, même initiale
        srow("André-Franck Zambo Anguissa", 30, "MC", "Parthenope"),  # un seul mot commun : douteux
        srow("Josep Martínez", 28, "GK", "Inter Milan"),        # même nom de famille, autre prénom : douteux
        srow("Frank Anguissa", 30, "MC", "Ailleurs FC"),        # même nom ailleurs
        srow("Frank Anguissa", 25, "MC", "Ailleurs FC"),        # homonyme d'un autre âge : nouveau
    ])
    _, ws = workbook(napoli_base())
    h = {c.value: c.column for c in ws[1]}
    m = add.BaseMatcher(add.load_players(ws)[1], add.read_all_clubs(ws, h), save)
    status = [(m.known(sp) or ("NOUVEAU", ""))[0] for sp in save]
    assert status == ["DÉJÀ_PRÉSENT", "DÉJÀ_PRÉSENT", "DÉJÀ_PRÉSENT", "DÉJÀ_PRÉSENT", "À_VÉRIFIER",
                      "À_VÉRIFIER", "DÉJÀ_PRÉSENT", "NOUVEAU"]


def test_nom_d_usage_seul_ne_rapproche_pas_un_autre_joueur():
    """name_similarity donne 0,70 à tout nom d'usage seul différent (Natan / Ez Abde) : exclu."""
    assert add.SAME_CLUB_NAME > 0.70
    p = add.ExcelPlayer(row=2, id=1, first="Natan", last="", nat="", age=24, pos="DC", club="Betis", rating=None)
    assert not add.usage_name_in(p, "Ez Abde") and add.usage_name_in(p, "Natan Bernardo")
    assert add.same_surname("Benjamin White", "Ben White") and not add.same_surname("Josep Martínez",
                                                                                    "Lautaro Martínez")


# --- Ajout ------------------------------------------------------------------------------------
def test_ajout_ordre_plafond_clubs_crees_et_valeurs(tmp_path):
    save, _ = write_save(tmp_path, [
        srow("Alex Meret", 29, "GK", "Parthenope"), srow("Giovanni Di Lorenzo", 33, "DR", "Parthenope"),
        srow("Lionel Messi", 39, "AMR AMC STC", "Inter Miami CF", value=20, left=20, right=8, height=170),
        srow("Jeune Napoli", 20, "DC", "Parthenope", value=11),
        srow("Gardien Neuf", 30, "GK", "Inter Miami CF", value=13, height=190),
        srow("Plein Un", 25, "MC", "Petit Club"),
        srow("Refus Club", 25, "MC", "Petit Club"),  # Petit Club plein (3 + 1 = plafond de 4)
        srow("Libre Un", 31, "MC", ""),
        srow("Trop Tard", 25, "MC", "Inter Miami CF"),  # au-delà des 5 ajouts demandés
    ])
    base = napoli_base([bplayer(10 + i, c, c, 25, "Petit Club", "Autres clubs") for i, c in enumerate("ABC")])
    _, ws = workbook(base)
    rows_before = ws.max_row
    added, report, _, _ = add.add_players(ws, save, count=5, max_squad=4, write=True)
    h = {c.value: c.column for c in ws[1]}
    assert ws.max_row == rows_before + 5
    names = [ws.cell(r, h["Prénom"]).value + " " + (ws.cell(r, h["Nom"]).value or "") for r in range(rows_before + 1,
                                                                                                    ws.max_row + 1)]
    assert names == ["Lionel Messi", "Jeune Napoli", "Gardien Neuf", "Plein Un", "Libre Un"]
    clubs_of = {n: ws.cell(rows_before + 1 + i, h["Club"]).value for i, n in enumerate(names)}
    assert clubs_of["Jeune Napoli"] == "SSC Napoli" and clubs_of["Libre Un"] == add.FREE_AGENTS
    assert clubs_of["Gardien Neuf"] == "Inter Miami CF"  # club créé, retrouvé par son nom exact
    assert "Refus Club" not in " ".join(names) and "Trop Tard" not in " ".join(names)
    r = rows_before + 1  # Messi
    v = {k: ws.cell(r, c).value for k, c in h.items()}
    assert v["Nationalité"] == "À renseigner" and v["Âge"] == 39 and v["Poste"] == "AD / MOC / BU"
    assert v["Championnat"] == "Autres clubs" and v["Taille FM (cm)"] == 170 and v["Postes FM naturels"] == "AMR, AMC, ST"
    assert v["Pieds"] == "G" and v["Weak foot (/5)"] == 2
    assert all(v[a] == 99 for a in FIELD_SET) and all(v[a] is None for a in GOALKEEPING)
    for col in ("Valeur marchande", "Moyenne joueur", "Moyenne FM", "Statut", "Catégorie", "Taille (cm)"):
        assert v[col] is None, col
    gk = {k: ws.cell(rows_before + 3, c).value for k, c in h.items()}
    assert all(gk[a] == 65 for a in GK_SET) and all(gk[a] is None for a in OUTFIELD_ONLY)
    assert [a.pid for a in added] == [13, 14, 15, 16, 17]
    assert ws.tables[TABLE_NAME].ref.endswith(str(ws.max_row))
    statuts = [x[1] for x in report]
    assert "CLUB_PLEIN" in statuts and statuts.count("AJOUTÉ") == 5


def test_sans_club_sans_plafond(tmp_path):
    save, _ = write_save(tmp_path, [srow(n, 30, "MC", "") for n in ("Alpha Un", "Bravo Deux", "Charlie Trois")])
    _, ws = workbook([bplayer(i, "X", str(i), 30, "Sans club", "Autres clubs") for i in range(1, 4)])
    added, _, _, _ = add.add_players(ws, save, count=10, max_squad=2, write=False)
    assert len(added) == 3


def test_essai_a_blanc_et_commande(tmp_path, monkeypatch):
    _, src = write_save(tmp_path, [srow("Alex Meret", 29, "GK", "Parthenope"),
                                   srow("Giovanni Di Lorenzo", 33, "DR", "Parthenope"),
                                   srow("Lionel Messi", 39, "AMR AMC STC", "Inter Miami CF")])
    wb, _ = workbook(napoli_base())
    xlsx = tmp_path / "joueurs.xlsx"
    wb.save(xlsx)
    before = xlsx.read_bytes()
    monkeypatch.setattr(sys, "argv", ["x", "--source", str(src), "--excel", str(xlsx)])
    add.main()
    assert xlsx.read_bytes() == before and not (tmp_path / "nouveaux_joueurs_nations.xlsx").exists()
    assert "PRÉVU" in (tmp_path / "fmsave_add_report.csv").read_text(encoding="utf-8-sig")
    monkeypatch.setattr(sys, "argv", ["x", "--source", str(src), "--excel", str(xlsx), "--write"])
    add.main()
    ws = openpyxl.load_workbook(xlsx)[add.SHEET]
    assert ws.max_row == 8
    nations = openpyxl.load_workbook(tmp_path / "nouveaux_joueurs_nations.xlsx").active
    assert [c.value for c in nations[1]] == ["Nom", "Prénom", "Poste", "Club", "Nation"]
    assert [c.value for c in nations[2]] == ["Messi", "Lionel", "AD / MOC / BU", "Inter Miami CF", None]
    assert nations.max_row == 2


def test_statut_des_clubs_autres_clubs(tmp_path):
    rows = ([srow(f"G {i}", 25, "GK", "Nouveau FC") for i in range(2)]
            + [srow(f"D {i}", 25, "DC", "Nouveau FC") for i in range(5)]
            + [srow(f"M {i}", 25, "MC", "Nouveau FC") for i in range(7)]
            + [srow(f"A {i}", 25, "STC", "Nouveau FC") for i in range(4)]
            + [srow("Seul", 25, "STC", "Petit FC")])
    save, _ = write_save(tmp_path, rows)
    _, ws = workbook([bplayer(1, "X", "Y", 30, "Lyon")])
    added, _, _, clubs = add.add_players(ws, save, count=50, write=False)
    status = {s[0]: s[1] for s in add.other_clubs_status(ws, added, clubs, write=False)}
    assert status == {"Nouveau FC": "complet", "Petit FC": "incomplet"}
    assert len(ATTRIBUTES) == 47


# --- Rattachement aux clubs existants (revue expert du 07a, A1 et A2) -------------------------
def _matcher(tmp_path, save_rows, base, manual=None, manual_known=None):
    save, _ = write_save(tmp_path, save_rows)
    _, ws = workbook(base)
    h = {c.value: c.column for c in ws[1]}
    return add.BaseMatcher(add.load_players(ws)[1], add.read_all_clubs(ws, h), save, manual, manual_known)


def test_sigles_a_points_et_futbol_neutralises(tmp_path):
    m = _matcher(tmp_path, [srow("Nouveau Un", 25)], [bplayer(1, "A", "B", 30, "Palermo FC", "Autres clubs"),
                                                       bplayer(2, "C", "D", 30, "CF Monterrey", "Autres clubs")])
    assert add.clean_club_name("Palermo F.C.") == "Palermo FC"
    assert m.club_for("Palermo F.C.") == "Palermo FC"
    assert m.club_for("Club de Fútbol Monterrey") == "CF Monterrey"


def test_un_seul_joueur_commun_et_sans_club(tmp_path):
    """Revue expert du 07a, passage 2 : un vote isolé entre noms sans rapport est un transfert."""
    rows = [srow("Agustin Canobbio", 27, "AMR", "FLU"),  # 1 vote, noms sans rapport : écarté
            srow("Tim Lemperle", 24, "STC", "1. FC Nürnberg"),  # 1 vote, noms apparentés : retenu
            srow("Joueur Libre", 30, "MC", "Mystere FC"), srow("Autre Libre", 31, "MC", "Mystere FC")]
    base = [bplayer(1, "Agustin", "Canobbio", 27, "Fluminense Football Club", "Autres clubs"),
            bplayer(4, "Tim", "Lemperle", 24, "1.FC Nuremberg", "Autres clubs"),
            bplayer(2, "Joueur", "Libre", 30, "Sans club", "Autres clubs"),
            bplayer(3, "Autre", "Libre", 31, "Sans club", "Autres clubs")]
    m = _matcher(tmp_path, rows, base)
    assert m.club_for("FLU") is None and "seul joueur" in m.alias_rejected["FLU"][2]
    assert m.club_for("1. FC Nürnberg") == "1.FC Nuremberg"
    assert "Mystere FC" not in m.alias and m.club_for("Mystere FC") is None  # « Sans club » ne vote pas


def test_transfert_isole_ne_rattache_pas_un_effectif(tmp_path):
    """« Oviedo » (1 joueur commun, transféré à la Real Sociedad) ne devient pas la Real Sociedad,
    dont le vrai nom figure aussi dans la sauvegarde avec plus de joueurs communs."""
    rows = [srow("Ancien Oviedo", 25, "MC", "Oviedo"), srow("Nouveau Oviedo", 22, "MC", "Oviedo"),
            srow("Joueur Txuri", 26, "DC", "Real Sociedad"), srow("Autre Txuri", 27, "DC", "Real Sociedad")]
    base = [bplayer(1, "Ancien", "Oviedo", 25, "Real Sociedad", "LaLiga"),
            bplayer(2, "Joueur", "Txuri", 26, "Real Sociedad", "LaLiga"),
            bplayer(3, "Autre", "Txuri", 27, "Real Sociedad", "LaLiga")]
    m = _matcher(tmp_path, rows, base)
    assert m.club_for("Oviedo") is None and m.club_for("Real Sociedad") == "Real Sociedad"
    rows2 = rows[:2] + [srow("Deux Transfert", 24, "MC", "Oviedo")]
    base2 = base + [bplayer(4, "Deux", "Transfert", 24, "Real Sociedad", "LaLiga")]
    m2 = _matcher(tmp_path, rows2 + rows[2:], base2)  # 2 votes Oviedo, mais 2 aussi pour le vrai club
    assert m2.club_for("Oviedo") is None  # égalité 2-2 : Oviedo écarté
    assert m2.club_for("Real Sociedad") == "Real Sociedad"  # écarté aussi, mais retrouvé par son nom


def test_doublons_valides_par_le_proprietaire(tmp_path):
    rows = [srow("Pote", 28, "AML AMC", "ACF Fiorentina")]
    base = [bplayer(1803, "Pedro", "Gonçalves", 28, "ACF Fiorentina", "Serie A")]
    assert _matcher(tmp_path, rows, base).known(add.read_save(write_save(tmp_path, rows)[1])[0]) is None
    m = _matcher(tmp_path, rows, base, manual_known={("Pote", "ACF Fiorentina"): 1803, ("X", "Y"): 99})
    sp = add.read_save(write_save(tmp_path, rows)[1])[0]
    assert m.known(sp)[0] == "DÉJÀ_PRÉSENT" and ("X", "Y") not in m.manual_known
    path = tmp_path / "known.csv"
    path.write_text("nom_sauvegarde;club_sauvegarde;id_classeur\nPote;ACF Fiorentina;1803\n", encoding="utf-8")
    assert add.read_manual_known(path) == {("Pote", "ACF Fiorentina"): 1803}


def test_correspondance_manuelle_prioritaire(tmp_path, monkeypatch):
    base = [bplayer(1, "Arthur", "Chaves", 24, "TSG Hoffenheim", "Bundesliga"),
            bplayer(2, "Nahuel", "Ferraresi", 27, "Botafogo de Futebol e Regatas", "Autres clubs")]
    rows = [srow("Arthur Chaves", 24, "DC", "BOT"), srow("Nahuel Ferraresi", 27, "DC", "BOT")]
    assert _matcher(tmp_path, rows, base).club_for("BOT") is None  # 1 vote contre 1 : inconnu
    m = _matcher(tmp_path, rows, base, {"BOT": "Botafogo de Futebol e Regatas", "XYZ": "Club absent"})
    assert m.club_for("BOT") == "Botafogo de Futebol e Regatas" and "XYZ" not in m.manual_alias
    path = tmp_path / "aliases.csv"
    path.write_text("club_sauvegarde;club_classeur\nBOT;Botafogo de Futebol e Regatas\n", encoding="utf-8")
    assert add.read_manual_alias(path) == {"BOT": "Botafogo de Futebol e Regatas"}
    assert add.read_manual_alias(tmp_path / "absent.csv") == {}


def test_creation_forcee_contre_un_rapprochement_de_nom_faux(tmp_path):
    """Revue expert du 07a, passage 3 : « AS Aris Thessalonikis » n'est pas Iraklis."""
    rows = [srow("Rafa Mir", 29, "STC", "AS Aris Thessalonikis"), srow("Christian Kouame", 28, "STC",
                                                                       "AS Aris Thessalonikis")]
    base = [bplayer(1, "Nanu", None, 31, "Iraklis Thessaloniki", "Autres clubs")]
    m = _matcher(tmp_path, rows, base)
    assert m.club_for("AS Aris Thessalonikis") == "Iraklis Thessaloniki"  # sans correction
    assert m.approx == {"AS Aris Thessalonikis": "Iraklis Thessaloniki"}  # listé pour relecture
    save, _ = write_save(tmp_path, rows)
    _, ws = workbook(base)
    added, _, _, _ = add.add_players(ws, save, count=5, write=False,
                                     manual_alias={"AS Aris Thessalonikis": add.CREATE})
    assert [a.values["Club"] for a in added] == ["AS Aris Thessalonikis"] * 2
    assert all(a.created_club for a in added)
