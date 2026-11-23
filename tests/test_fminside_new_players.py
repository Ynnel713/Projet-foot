"""Mode découverte des nouveaux joueurs fminside (scripts/fminside_new_players.py).

Ticket .scratch/donnees-nouveaux-joueurs/issues/01. Hors ligne : un faux client remplace
fminside, le classeur est construit en mémoire.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
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


# --- Mode « top N » (ticket 05) ---------------------------------------------------------------
class TopAPI(FakeAPI):
    """Faux client du mode top : liste du site dans l'ordre, postes naturels pris de la recherche."""

    def __init__(self, rows, bad_profiles=()):
        super().__init__({}, bad_profiles)
        self.rows = rows
        self.asked = None

    def top(self, n):
        self.asked = n
        return list(self.rows[:n])

    def extras(self, url):
        pos = next(min(c.positions) for c in self.rows if c.url == url)
        return {"natural": [pos], "height": 180, "weak_foot": 3.0, "locked": True, "moves": []}


def squad(club, n, prefix, pos):
    return [cand(f"{prefix} {i}", club, 70, pos=(pos,)) for i in range(n)]


def test_resolver_club_existant_variante_et_club_inconnu():
    clubs = {"Rennes": fnp.TargetClub("Rennes", "Ligue 1", 25),
             "Atalanta BC": fnp.TargetClub("Atalanta BC", "Serie A", 28),
             "Coventry City": fnp.TargetClub("Coventry City", "Autres clubs", 1)}
    r = fnp.ClubResolver(clubs, {"Rennes": "Stade Rennais FC"})
    assert r.resolve("Rennes FC") == "Rennes"  # FC ignoré : même nom normalisé
    assert r.resolve("Stade Rennais FC") == "Rennes"  # nom fminside appris du cache
    assert r.resolve("Coventry") == "Coventry City"  # mots génériques en plus
    assert r.resolve("Al Nassr") is None  # inconnu : nouveau club en Autres clubs


def test_resolver_prefere_le_club_du_championnat_a_la_ligne_isolee():
    clubs = fnp.read_all_clubs(*_sheet([player(1, "A", "B", "Atalanta BC", champ="Autres clubs"),
                                        player(2, "C", "D", "Atalanta BC", champ="Serie A"),
                                        player(3, "E", "F", "Atalanta BC", champ="Serie A")]))
    # club du championnat ; effectif compté sur toutes les lignes du nom (réserve A3 du 05)
    assert clubs["Atalanta BC"].championnat == "Serie A" and clubs["Atalanta BC"].size == 3


def _sheet(rows):
    _, ws = workbook(rows)
    return ws, {c.value: c.column for c in ws[1]}


def test_top_range_les_joueurs_plafonne_et_classe_les_autres_clubs():
    _, ws = _base()  # Rennes (Ligue 1), Lyon (Ligue 1), Club Exotique (Autres clubs), 1 joueur chacun
    complete = (squad("Al Nassr", 2, "G", "GK") + squad("Al Nassr", 5, "D", "DC")
                + squad("Al Nassr", 7, "M", "MC") + squad("Al Nassr", 4, "A", "ST"))  # 18, complet
    rows = ([cand("Jean Dupont", "Rennes", 80)]  # déjà dans la base
            + [cand(f"Rennais {i}", "Rennes FC", 75) for i in range(3)]  # plafond 3 : 2 places
            + complete
            + squad("Al Hilal", 3, "H", "ST")  # nouveau club, vedettes seules : incomplet
            + [cand("Libre Un", "", 60)])
    api = TopAPI(rows)
    out = fnp.discover_top(ws, api, n=4000, max_squad=3)
    assert api.asked == 4000
    h = {c.value: c.column for c in ws[1]}
    by_club = {}
    for r in range(5, ws.max_row + 1):
        by_club.setdefault(ws.cell(r, h["Club"]).value, []).append(ws.cell(r, h["Championnat"]).value)
    assert by_club["Rennes"] == ["Ligue 1", "Ligue 1"]  # 1 + 2 = plafond de 3
    assert set(by_club["Al Hilal"]) == {"Autres clubs"} and len(by_club["Al Hilal"]) == 3
    assert by_club["Sans club"] == ["Autres clubs"]
    statuts = {row[0] for row in out.players_report}
    assert {"DÉJÀ_PRÉSENT", "CLUB_PLEIN", "AJOUTÉ"} <= statuts


def test_top_rapport_complet_ou_incomplet():
    _, ws = _base()
    complete = (squad("Al Nassr", 2, "G", "GK") + squad("Al Nassr", 5, "D", "DC")
                + squad("Al Nassr", 7, "M", "MC") + squad("Al Nassr", 4, "A", "ST"))
    out = fnp.discover_top(ws, TopAPI(complete + squad("Al Hilal", 20, "H", "ST")), n=100, max_squad=40)
    report = {row[0]: row for row in out.clubs_report}
    assert report["Al Nassr"][3] == "complet" and report["Al Nassr"][5:9] == [2, 5, 7, 4]
    assert report["Al Hilal"][3] == "incomplet" and report["Al Hilal"][4] == "nouveau club"
    assert "Rennes" not in report  # seuls les clubs Autres clubs sont classés


def test_top_dry_run_ni_fiche_ni_ecriture_mais_composition_prevue():
    _, ws = _base()
    complete = (squad("Al Nassr", 2, "G", "GK") + squad("Al Nassr", 5, "D", "DC")
                + squad("Al Nassr", 7, "M", "MC") + squad("Al Nassr", 4, "A", "ST"))
    api = TopAPI(complete)
    before = ws.max_row
    out = fnp.discover_top(ws, api, n=100, max_squad=40, dry_run=True)
    assert ws.max_row == before and api.profiles == [] and len(out.added) == 18
    assert {row[0]: row[3] for row in out.clubs_report}["Al Nassr"] == "complet"


def test_top_deux_clubs_inconnus_aux_noms_voisins_restent_distincts():
    """Un club créé pendant l'exécution n'est retrouvé que sous son nom FM exact."""
    _, ws = _base()
    rows = squad("Al Ahli", 2, "X", "ST") + squad("Al Ahly", 2, "Y", "ST") + squad("Al Ahli", 1, "Z", "GK")
    out = fnp.discover_top(ws, TopAPI(rows), n=100, max_squad=40)
    added = Counter(club for _, club, _ in out.added)
    assert added == {"Al Ahli": 3, "Al Ahly": 2}


# --- Extraction seule (--top N --extract-only) -------------------------------------------------
def _top_rows():
    return [cand("Kylian Mbappe", "Real Madrid", 91, nat="France", pos=("ST",)),
            cand("Luc Petit", "Rennes", 70, nat="Ivory Coast", pos=("AMR",)),
            cand("Bruno", "Rennes", 65, pos=("GK",))]


def test_extraction_garde_l_ordre_du_site_et_toutes_les_colonnes():
    api = TopAPI(_top_rows(), bad_profiles={"https://fminside.net/players/7-fm-26/bruno"})
    rows, error, listed = fnp.extract_top(api, 4000)
    assert error == "" and api.asked == 4000 and listed == 3
    assert [r[0] for r in rows] == [1, 2, 3] and [r[3] for r in rows] == ["Kylian Mbappe", "Luc Petit", "Bruno"]
    head = fnp.EXTRACT_COLUMNS
    luc = dict(zip(head, rows[1]))
    assert len(rows[1]) == len(head) == 16 + len(ATTRIBUTES)
    assert luc["statut_fiche"] == "ok" and luc["nationalite_fr"] == "Côte d'Ivoire" and luc["age_fm"] == 24
    assert luc["poste_classeur"] == "AD" and luc["taille_cm"] == 180 and luc["preferred_moves"] == ""
    assert all(luc[a] == 12 for a in ATTRIBUTES)
    bruno = dict(zip(head, rows[2]))
    assert bruno["statut_fiche"].startswith("fiche illisible") and all(bruno[a] is None for a in ATTRIBUTES)


def test_extraction_erreur_bloquante_rend_les_lignes_deja_lues():
    api = TopAPI(_top_rows())
    real, calls = api.attributes, {"n": 0}

    def flaky(url):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("Bloqué par Cloudflare")
        return real(url)

    api.attributes = flaky
    rows, error, _ = fnp.extract_top(api, 10)
    assert len(rows) == 1 and "Cloudflare" in error


def test_commande_extract_only_ecrit_un_excel_separe_sans_toucher_joueurs(tmp_path, monkeypatch):
    wb, _ = _base()
    joueurs = tmp_path / "joueurs.xlsx"
    wb.save(joueurs)
    before = joueurs.read_bytes()
    monkeypatch.setattr(fnp, "FMInside", lambda *a, **k: TopAPI(_top_rows()))
    monkeypatch.setattr(sys, "argv", ["x", "--excel", str(joueurs), "--top", "4000", "--extract-only"])
    fnp.main()
    assert joueurs.read_bytes() == before  # joueurs.xlsx intact
    ws = openpyxl.load_workbook(tmp_path / "fminside_top4000.xlsx")[fnp.EXTRACT_SHEET]
    assert [c.value for c in ws[1]] == fnp.EXTRACT_COLUMNS and ws.max_row == 4
    assert ws.cell(2, 4).value == "Kylian Mbappe"


def test_extract_only_exige_top(tmp_path, monkeypatch):
    monkeypatch.setattr(fnp, "FMInside", lambda *a, **k: TopAPI([]))
    monkeypatch.setattr(sys, "argv", ["x", "--excel", str(tmp_path / "joueurs.xlsx"), "--extract-only"])
    with pytest.raises(SystemExit):
        fnp.main()


def test_extraction_fiche_en_erreur_inattendue_ne_fait_rien_perdre():
    """Réserve A1 (expert, ticket 05) : une HTTPError (fiche en 404...) donne une ligne sans
    attributs, comme le mode par club, au lieu d'interrompre l'extraction sans Excel."""
    api = TopAPI(_top_rows())
    real = api.attributes

    def http_404(url):
        if url.endswith("luc-petit"):
            raise ValueError("404 Client Error")
        return real(url)

    api.attributes = http_404
    rows, error, _ = fnp.extract_top(api, 10)
    assert error == "" and len(rows) == 3
    assert rows[1][1].startswith("fiche illisible") and all(v is None for v in rows[1][16:])


def test_liste_du_site_tronquee_signalee_et_non_mise_en_cache(tmp_path, monkeypatch, capsys):
    """Réserve A2 : liste plus courte que demandé = message dédié, pas « relance »."""
    wb, _ = _base()
    joueurs = tmp_path / "joueurs.xlsx"
    wb.save(joueurs)
    monkeypatch.setattr(fnp, "FMInside", lambda *a, **k: TopAPI(_top_rows()))
    monkeypatch.setattr(sys, "argv", ["x", "--excel", str(joueurs), "--top", "4000", "--extract-only"])
    fnp.main()
    out = capsys.readouterr().out
    assert "s'arrête à 3 joueurs" in out and "relance la même commande" not in out


def test_fminside_top_ne_met_pas_en_cache_une_liste_tronquee(tmp_path):
    """Réserve A2, côté client : FMInside.top garde la liste seulement si elle est complète."""
    from scrape_fminside_attributes import FMInside

    api = FMInside(0, tmp_path / "cache.json", use_cache=False)
    page = ('<ul class="player database-table-row"><span class="name">'
            '<a href="/players/7-fm-26/p1">P1</a></span></ul>')

    class R:
        status_code, text = 200, page

    api._req = lambda *a, **k: R()
    api.warmup = lambda: None
    assert len(api.top(10)) == 1 and api.cache["search"] == {}  # tronquée : pas en cache
    assert len(api.top(1)) == 1 and list(api.cache["search"]) == ['["__top__", 1]']


def test_extraction_caracteres_interdits_par_excel_retires(tmp_path):
    """Réserve A4 : un caractère de contrôle dans un nom n'empêche pas d'écrire le fichier."""
    row = fnp.extract_row(1, cand("Nom\x07Bizarre", "Club", 60), None, None, "ok")
    path = tmp_path / "x.xlsx"
    fnp.write_extract(path, [row])
    assert openpyxl.load_workbook(path)[fnp.EXTRACT_SHEET].cell(2, 4).value == "NomBizarre"
