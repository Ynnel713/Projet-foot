"""Mode découverte des nouveaux joueurs fminside (scripts/fminside_new_players.py).

Ticket .scratch/donnees-nouveaux-joueurs/issues/01. Hors ligne : un faux client remplace
fminside, le classeur est construit en mémoire.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl
import pytest
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fminside_new_players as fnp
from scrape_fminside_attributes import (
    ATTRIBUTES,
    NEW_COLUMNS,
    Candidate,
    ProfileUnreadable,
)

BASE_HEADERS = ["ID", "Prénom", "Nom", "Moyenne FM", "Nationalité", "Âge", "Poste", "Club",
                "Championnat", "Valeur marchande", "Statut", "Pieds", "Moyenne joueur"]
HEADERS = BASE_HEADERS + NEW_COLUMNS


def cand(name, club, ability, age=24, nat="France", pos=("MC",), url=None, full=""):
    slug = name.lower().replace(" ", "-")
    return Candidate(url=url or f"https://fminside.net/players/7-fm-26/{slug}", name=name, full_name=full,
                     nat=nat, age=age, club=club, positions=set(pos), ability=ability)


def workbook(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = fnp.SHEET
    ws.append(HEADERS)
    for r in rows:
        ws.append([r.get(h) for h in HEADERS])
    ref = f"A1:{openpyxl.utils.get_column_letter(len(HEADERS))}{ws.max_row}"
    table = Table(displayName=fnp.TABLE_NAME, ref=ref, autoFilter=AutoFilter(ref=ref))  # comme Tableau8
    table._initialise_columns()  # colonnes nommées, comme dans un classeur relu
    ws.add_table(table)
    return wb, ws


def player(pid, first, last, club, champ="Ligue 1", age=25, url=None):
    return {"ID": pid, "Prénom": first, "Nom": last, "Nationalité": "France", "Âge": age, "Poste": "MC",
            "Club": club, "Championnat": champ, "Moyenne joueur": 70, "Moyenne FM": 70, fnp.URL_COL: url}


class FakeAPI:
    def __init__(self, by_query, bad_profiles=()):
        self.by_query = by_query
        self.bad = set(bad_profiles)
        self.cache = {"search": {}}
        self.profiles = []

    def search(self, name="", nationality="", min_age=None, max_age=None, club=""):
        rows = list(self.by_query.get(club, []))
        key = json.dumps([name, nationality, min_age, max_age] + ([club] if club else []))
        self.cache["search"][key] = [c.to_json() for c in rows]  # comme FMInside.search
        return rows

    def attributes(self, url):
        if url in self.bad:
            raise ProfileUnreadable(f"Aucun attribut trouvé sur {url}")  # comme FMInside.profile
        self.profiles.append(url)
        return {a: 12 for a in ATTRIBUTES}

    def extras(self, url):
        return {"natural": ["AM (RL)", "ST (C)"], "height": 181, "weak_foot": 3.0, "locked": True, "moves": []}

    def save_cache(self):
        pass


# --- Conversions ------------------------------------------------------------------------------
def test_fm_poste_suit_l_ordre_de_la_fiche_et_le_format_du_classeur():
    assert fnp.fm_poste(["ST", "AML"]) == "BU / AG"
    assert fnp.fm_poste(["AM (RL)", "ST (C)"]) == "AD / AG / BU"
    assert fnp.fm_poste(["D (RLC)", "WB (R)"]) == "RB / LB / DC"
    assert fnp.fm_poste(["DM", "M (C)"]) == "MDC / MC"
    assert fnp.fm_poste([], {"ST", "GK"}) == "GK / BU"  # repli : ordre fixe, déterministe
    assert fnp.fm_poste([], set()) is None


def test_nationalite_et_nom():
    assert fnp.fr_nationality("Ivory Coast") == ("Côte d'Ivoire", True)
    assert fnp.fr_nationality("Korea Republic") == ("Corée du Sud", True)
    assert fnp.fr_nationality("Atlantis") == ("Atlantis", False)  # gardé tel quel, signalé
    assert fnp.split_name("Vitinha") == ("Vitinha", None)  # convention des noms d'usage
    assert fnp.split_name("Jean-Paul de la Cruz") == ("Jean-Paul", "de la Cruz")


# --- Joueurs déjà présents --------------------------------------------------------------------
def test_joueurs_deja_presents_ecartes():
    _, ws = workbook([player(1, "Jean", "Dupont", "Rennes", url="https://fminside.net/players/x"),
                      player(2, "Paul", "Martin", "Lyon", age=27)])
    headers = {c.value: c.column for c in ws[1]}
    index, clubs, next_id = fnp.read_base(ws, headers)
    assert next_id == 3 and set(clubs) == {"Lyon", "Rennes"}
    assert "URL" in index.known_reason("Rennes", cand("Autre", "Rennes", 60, url="https://fminside.net/players/x"))
    assert "club" in index.known_reason("Rennes", cand("J. Dupont", "Rennes", 60, full="Jean Dupont"))
    # même nom ailleurs, âge FM 26 -> 27 dans le classeur : même joueur, transféré
    assert "même nom" in index.known_reason("Rennes", cand("Paul Martin", "Rennes", 60, age=26))
    # homonyme d'un autre âge : bien un autre joueur
    assert index.known_reason("Rennes", cand("Paul Martin", "Rennes", 60, age=19)) is None


# --- Sélection --------------------------------------------------------------------------------
def test_selection_quotas_egaux_plafond_et_cible():
    pools = {k: [cand(f"{k} {i}", k, 90 - i) for i in range(20)] for k in ("A", "B", "C")}
    sizes = {"A": 38, "B": 30, "C": 25}
    chosen = fnp.select(pools, sizes, max_squad=40, target=17, accept=lambda *_: True)
    added = {k: sum(1 for c, _ in chosen if c == k) for k in pools}
    assert len(chosen) == 17
    assert added["A"] == 2  # plafond 40
    assert abs(added["B"] - added["C"]) <= 1  # quotas égaux entre clubs non plafonnés
    assert all(sizes[k] + added[k] <= 40 for k in pools)
    # meilleurs FM d'abord, dans chaque club
    assert [c.name for k, c in chosen if k == "B"] == [f"B {i}" for i in range(added["B"])]
    # déterministe
    again = fnp.select(pools, sizes, max_squad=40, target=17, accept=lambda *_: True)
    assert [(k, c.url) for k, c in again] == [(k, c.url) for k, c in chosen]


def test_selection_candidat_refuse_remplace_par_le_suivant_du_club():
    pools = {"A": [cand("A0", "A", 80), cand("A1", "A", 70)], "B": [cand("B0", "B", 75)]}
    chosen = fnp.select(pools, {"A": 1, "B": 1}, 40, 10, accept=lambda k, c: c.name != "A0")
    assert sorted(c.name for _, c in chosen) == ["A1", "B0"]


def test_pool_order_note_fm_puis_nom():
    order = fnp.pool_order([cand("Zed", "A", 70), cand("Abel", "A", 70), cand("Max", "A", 80),
                            cand("Nul", "A", None)])
    assert [c.name for c in order] == ["Max", "Abel", "Zed", "Nul"]


# --- Recherche par club -----------------------------------------------------------------------
def test_filtre_club_ignore_arrete_tout():
    rows = [cand(f"P{i}", f"Club {i}", 80) for i in range(10)]
    with pytest.raises(fnp.FilterIgnored):
        fnp.club_pool(FakeAPI({"Rennes": rows}), fnp.TargetClub("Rennes", "Ligue 1", 25))


def test_club_introuvable_ou_different():
    api = FakeAPI({"Rennes": [cand("P", "Rennes Women", 50)]})
    status, cands, _, detail = fnp.club_pool(api, fnp.TargetClub("Rennes", "Ligue 1", 25))
    assert status == "CLUB_DIFFÉRENT" and not cands and "fminside_clubs.csv" in detail
    assert fnp.club_pool(FakeAPI({}), fnp.TargetClub("Lyon", "Ligue 1", 25))[0] == "INTROUVABLE"


def test_nom_fminside_deduit_du_cache():
    cache = {"search": {"k": [{"url": "u1", "club": "Stade Rennais FC"}, {"url": "u2", "club": "Stade Rennais FC"},
                              {"url": "u3", "club": "Lyon"}]}}
    assert fnp.fm_names_from_cache(cache, {"u1": "Rennes", "u2": "Rennes", "u3": "OL"}) == {
        "Rennes": "Stade Rennais FC", "OL": "Lyon"}


# --- De bout en bout --------------------------------------------------------------------------
def _base():
    return workbook([player(1, "Jean", "Dupont", "Rennes"), player(2, "Paul", "Martin", "Lyon"),
                     player(3, "Ali", "Ba", "Club Exotique", champ="Autres clubs")])


def _api(bad=()):
    return FakeAPI({
        "Rennes": [cand("Jean Dupont", "Rennes", 75), cand("Luc Petit", "Rennes", 70, nat="Ivory Coast"),
                   cand("Bruno", "Rennes", 65), cand("Hugo Roy", "Rennes", 60)],
        "Lyon": [cand("Marc Noir", "Lyon", 72), cand("Theo Blanc", "Lyon", 68)],
        "Club Exotique": [cand("Ne Pas", "Club Exotique", 99)],
    }, bad)


def test_decouverte_ecrit_les_nouvelles_lignes_sans_rien_inventer():
    _, ws = _base()
    out = fnp.discover(ws, _api(bad={"https://fminside.net/players/7-fm-26/bruno"}), target=4, max_squad=40)
    h = {c.value: c.column for c in ws[1]}
    new = list(range(5, ws.max_row + 1))
    assert len(out.added) == 4 and len(new) == 4
    vals = [{k: ws.cell(r, c).value for k, c in h.items()} for r in new]
    names = sorted(v["Prénom"] for v in vals)
    # Jean Dupont déjà là, Bruno illisible (remplacé par Hugo), Autres clubs hors cible
    assert names == ["Hugo", "Luc", "Marc", "Theo"]
    assert sorted(v["ID"] for v in vals) == [4, 5, 6, 7]
    luc = next(v for v in vals if v["Prénom"] == "Luc")
    assert luc["Nom"] == "Petit" and luc["Nationalité"] == "Côte d'Ivoire" and luc["Âge"] == 25
    assert luc["Poste"] == "AD / AG / BU" and luc["Club"] == "Rennes" and luc["Championnat"] == "Ligue 1"
    assert all(luc[a] == 12 for a in ATTRIBUTES) and luc[fnp.URL_COL].endswith("luc-petit")
    assert luc["Taille FM (cm)"] == 181 and luc["Weak foot (/5)"] == 3
    for col in ("Moyenne joueur", "Moyenne FM", "Valeur marchande", "Statut", "Pieds", "Preferred moves"):
        assert luc[col] is None, col
    assert ws.tables[fnp.TABLE_NAME].ref.endswith(str(ws.max_row))
    statuts = {row[0] for row in out.players_report}
    assert {"AJOUTÉ", "DÉJÀ_PRÉSENT", "REFUSÉ"} <= statuts
    assert {r[0] for r in out.clubs_report} == {"Rennes", "Lyon"}


def test_dry_run_ne_telecharge_ni_n_ecrit():
    _, ws = _base()
    api = _api()
    before = ws.max_row
    out = fnp.discover(ws, api, target=10, max_squad=40, dry_run=True)
    assert ws.max_row == before and api.profiles == []
    assert len(out.added) == 5  # 3 nouveaux à Rennes (Jean Dupont exclu) + 2 à Lyon
    assert {row[0] for row in out.players_report} == {"PRÉVU", "DÉJÀ_PRÉSENT"}


def test_erreur_bloquante_garde_les_lignes_deja_ajoutees():
    _, ws = _base()
    api = _api()
    calls = {"n": 0}
    real = api.attributes

    def flaky(url):
        calls["n"] += 1
        if calls["n"] > 2:
            raise RuntimeError("Bloqué par Cloudflare")
        return real(url)

    api.attributes = flaky
    out = fnp.discover(ws, api, target=10, max_squad=40)
    assert len(out.added) == 2 and ws.max_row == 6 and "Cloudflare" in out.error


def test_relance_ne_reajoute_pas_les_memes():
    _, ws = _base()
    fnp.discover(ws, _api(), target=2, max_squad=40)
    first = {ws.cell(r, 1).value for r in range(2, ws.max_row + 1)}
    out = fnp.discover(ws, _api(), target=10, max_squad=40)
    urls = [ws.cell(r, {c.value: c.column for c in ws[1]}[fnp.URL_COL]).value for r in range(2, ws.max_row + 1)]
    urls = [u for u in urls if u]
    assert len(urls) == len(set(urls))
    assert len(out.added) == 3 and len(first) == 5


def test_filtre_ignore_purge_les_recherches_par_club_du_cache():
    """Réserve A1 (expert, passage 1) : une relance ne doit pas relire des réponses non filtrées."""
    _, ws = _base()
    api = _api()
    api.by_query["Rennes"] = [cand(f"P{i}", f"Club {i}", 80) for i in range(10)]  # filtre ignoré
    api.cache["search"][json.dumps(["Jean", "France", 20, 30])] = []  # recherche du script de base
    with pytest.raises(fnp.FilterIgnored):
        fnp.discover(ws, api, target=10, max_squad=40)
    assert list(api.cache["search"]) == [json.dumps(["Jean", "France", 20, 30])]
    assert ws.max_row == 4


def test_fiche_sans_attributs_ne_bloque_pas_la_collecte():
    """Réserve A2 : l'erreur réelle de FMInside.profile fait passer au suivant, sans arrêt."""
    _, ws = _base()
    out = fnp.discover(ws, _api(bad={"https://fminside.net/players/7-fm-26/luc-petit"}), target=10, max_squad=40)
    assert out.error == "" and len(out.added) == 4
    assert any(r[0] == "REFUSÉ" and "Aucun attribut" in r[-1] for r in out.players_report)


def test_meme_fiche_dans_deux_clubs_une_seule_ligne():
    """Réserve A3 : pas de doublon d'URL au sein d'une même exécution."""
    _, ws = _base()
    api = _api()
    api.by_query["Lyon"].append(cand("Hugo Roy", "Lyon", 99))  # même URL que le Hugo Roy de Rennes
    out = fnp.discover(ws, api, target=10, max_squad=40)
    urls = [c.url for _, _, c in out.added]
    assert len(urls) == len(set(urls)) and len(urls) == 5
    dry = fnp.discover(_base()[1], api, target=10, max_squad=40, dry_run=True)
    assert len({c.url for _, _, c in dry.added}) == len(dry.added) == 5
