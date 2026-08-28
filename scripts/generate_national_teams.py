"""Régénère les 5 onglets de sélections nationales (Europe/Afrique/Amérique/
Asie/Océanie de data/joueurs.xlsx) à partir de "Infos principales", par
nationalité.

Contexte (28/08/2026) : ces onglets pilotent Sélections nationales dans
l'app (voir nations.py) via un snapshot généré une fois par un algorithme
non documenté puis jamais recalculé -- un joueur ajouté à "Infos
principales" depuis (scraping Championship, sélections nationales, etc.)
n'y apparaissait donc jamais, même s'il aurait dû compléter une sélection.
Ce script les régénère intégralement à partir de l'état actuel de la base,
remplaçant ce snapshot figé par un pipeline reproductible (même esprit que
transfermarkt_scraper.py / merge_missing_players.py / calibrate_engine.py)
: à relancer après tout ajout de joueurs pour que Sélections nationales
reflète la base à jour.

Registre pays : (drapeau, onglet) extraits des 5 onglets EXISTANTS avant
régénération -- ce sont eux qui font autorité sur "quel pays va dans quel
onglet avec quel drapeau", pas une liste recopiée à la main. Une
nationalité de "Infos principales" sans correspondance dans ce registre
(aucun bloc préexistant pour ce pays, dans aucune langue) est ignorée avec
un avertissement en fin d'exécution, jamais une invention de
drapeau/continent.

Composition ciblée (TARGET_QUOTA) : 3 gardiens, 7 défenseurs, 6 milieux, 7
attaquants (23 au total) -- la répartition la plus fréquente parmi les
sélections déjà COMPLET avant régénération (8 pays sur 70 suivaient très
exactement ce schéma, ex. Autriche, Pologne, Turquie). Simplification
assumée par rapport à l'ancien onglet : chaque groupe de poste a son
propre quota FIXE, sans redistribution entre postes -- le comportement
précédent semblait redistribuer les quotas selon les postes disponibles
par pays (les décomptes "manquant(s)" observés ne correspondaient à aucune
règle de soustraction simple retrouvée), mais son fonctionnement exact n'a
pas pu être déterminé de façon fiable à partir des seules données
observées, donc pas reproduit tel quel.

Nationalité : la colonne "Nationalité" de "Infos principales" mélange
français et anglais selon la source du scraping d'origine (contamination
du même type que le bug de poste corrigé le même jour dans
transfermarkt_scraper.py, découverte en écrivant ce script) --
NATIONALITY_ALIASES traduit les formes anglaises rencontrées vers le nom
français du registre. Un double national ("Canada / England") est
éligible aux DEUX sélections listées, jamais une seule.

Usage :
    uv run python scripts/generate_national_teams.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.clubs import load_all_clubs  # noqa: E402
from ligue1sim.players import Player, position_group  # noqa: E402

GAME_PATH = "data/joueurs.xlsx"
NATION_SHEETS = ["Europe", "Afrique", "Amérique", "Asie", "Océanie"]

_TITLE_ROW = re.compile(r"^(.+?) — (COMPLET|INCOMPLET)")

GROUP_ORDER = ["GK", "DEF", "MID", "ATT"]
TARGET_QUOTA: dict[str, int] = {"GK": 3, "DEF": 7, "MID": 6, "ATT": 7}
SQUAD_SIZE = sum(TARGET_QUOTA.values())  # 23, comme "COMPLET (23/23)"

GROUP_LABEL = {"GK": "Gardien", "DEF": "Défenseur", "MID": "Milieu", "ATT": "Attaquant"}
GROUP_LABEL_LOWER = {"GK": "gardien", "DEF": "défenseur", "MID": "milieu", "ATT": "attaquant"}

# Anglais Transfermarkt (colonne "Nationalité" d'une partie de la base,
# voir docstring du module) -> nom français utilisé par le registre pays.
# Construit en comparant les nationalités présentes dans "Infos
# principales" au nom exact des blocs déjà existants (voir la conversation
# du 28/08/2026) -- pas une liste de pays générique, seulement les formes
# réellement rencontrées dans ce fichier.
NATIONALITY_ALIASES: dict[str, str] = {
    "Albania": "Albanie",
    "Algeria": "Algérie",
    "Argentina": "Argentine",
    "Armenia": "Arménie",
    "Australia": "Australie",
    "Austria": "Autriche",
    "Belgium": "Belgique",
    "Benin": "Bénin",
    "Bosnia-Herzegovina": "Bosnie-Herzégovine",
    "Brazil": "Brésil",
    "Cameroon": "Cameroun",
    "Cape Verde": "Cap-Vert",
    "Chile": "Chili",
    "Colombia": "Colombie",
    "Comoros": "Comores",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Croatia": "Croatie",
    "Curacao": "Curaçao",
    "Cyprus": "Chypre",
    "Czech Republic": "République tchèque",
    "DR Congo": "RD Congo",
    "Denmark": "Danemark",
    "Ecuador": "Équateur",
    "Egypt": "Égypte",
    "England": "Angleterre",
    "Estonia": "Estonie",
    "Finland": "Finlande",
    "Georgia": "Géorgie",
    "Germany": "Allemagne",
    "Greece": "Grèce",
    "Guinea": "Guinée",
    "Guinea-Bissau": "Guinée-Bissau",
    "Haiti": "Haïti",
    "Hungary": "Hongrie",
    "Iceland": "Islande",
    "Indonesia": "Indonésie",
    "Ireland": "Irlande",
    "Israel": "Israël",
    "Italy": "Italie",
    "Jamaica": "Jamaïque",
    "Japan": "Japon",
    "Jordan": "Jordanie",
    "Korea, South": "Corée du Sud",
    "Lithuania": "Lituanie",
    "Mexico": "Mexique",
    "Montenegro": "Monténégro",
    "Morocco": "Maroc",
    "Netherlands": "Pays-Bas",
    "New Zealand": "Nouvelle-Zélande",
    "Northern Ireland": "Irlande du Nord",
    "Norway": "Norvège",
    "Peru": "Pérou",
    "Poland": "Pologne",
    "Romania": "Roumanie",
    "Russia": "Russie",
    "Saudi Arabia": "Arabie saoudite",
    "Scotland": "Écosse",
    "Senegal": "Sénégal",
    "Serbia": "Serbie",
    "Slovakia": "Slovaquie",
    "Slovenia": "Slovénie",
    "South Africa": "Afrique du Sud",
    "Spain": "Espagne",
    "Sweden": "Suède",
    "Switzerland": "Suisse",
    "Tanzania": "Tanzanie",
    "The Gambia": "Gambie",
    "Trinidad and Tobago": "Trinité-et-Tobago",
    "Tunisia": "Tunisie",
    "Türkiye": "Turquie",
    "United States": "États-Unis",
    "Wales": "Pays de Galles",
}


def _harvest_country_registry(path: str) -> dict[str, tuple[str, str]]:
    """{nom de pays français : (drapeau, onglet)}, extrait des blocs des 5
    onglets existants -- voir docstring du module."""
    registry: dict[str, tuple[str, str]] = {}
    for sheet in NATION_SHEETS:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        for value in df.iloc[:, 0]:
            if not isinstance(value, str):
                continue
            match = _TITLE_ROW.match(value)
            if match is None:
                continue
            flag_and_name = match.group(1).strip()
            if " " not in flag_and_name:
                continue
            flag, name = flag_and_name.split(" ", 1)
            registry[name.strip()] = (flag, sheet)
    return registry


def _canonical_nationality(token: str, registry: dict[str, tuple[str, str]]) -> str | None:
    token = token.strip()
    if token in registry:
        return token
    aliased = NATIONALITY_ALIASES.get(token)
    if aliased in registry:
        return aliased
    return None


def _players_by_nationality(
    path: str, registry: dict[str, tuple[str, str]]
) -> tuple[dict[str, list[Player]], set[str]]:
    by_nat: dict[str, list[Player]] = {name: [] for name in registry}
    unmatched: set[str] = set()
    for option in load_all_clubs(path):
        for player in option.players:
            if not player.nationalite or player.id is None:
                continue
            for token in str(player.nationalite).split(" / "):
                token = token.strip()
                if not token:
                    continue
                canonical = _canonical_nationality(token, registry)
                if canonical is None:
                    unmatched.add(token)
                    continue
                by_nat[canonical].append(player)
    return by_nat, unmatched


def _select_squad(players: list[Player]) -> dict[str, list[Player]]:
    """{groupe (GK/DEF/MID/ATT) : joueurs retenus}, triés par note
    décroissante et plafonnés à TARGET_QUOTA[groupe]."""
    by_group: dict[str, list[Player]] = {g: [] for g in GROUP_ORDER}
    for p in players:
        by_group[position_group(p.poste)].append(p)
    return {g: sorted(by_group[g], key=lambda p: -p.note)[: TARGET_QUOTA[g]] for g in GROUP_ORDER}


def _build_block(country: str, flag: str, selected: dict[str, list[Player]]) -> list[list]:
    total = sum(len(v) for v in selected.values())
    status = "COMPLET" if total == SQUAD_SIZE else "INCOMPLET"

    rows: list[list] = [[f"{flag} {country} — {status} ({total}/{SQUAD_SIZE})", None, None, None, None, None]]

    composition = " - ".join(f"{len(selected[g])} {GROUP_LABEL_LOWER[g]}" for g in GROUP_ORDER)
    rows.append([f"Composition : {composition}", None, None, None, None, None])

    if status == "INCOMPLET":
        missing_parts = [
            f"{TARGET_QUOTA[g] - len(selected[g])} {GROUP_LABEL_LOWER[g]}(s) manquant(s)"
            for g in GROUP_ORDER
            if len(selected[g]) < TARGET_QUOTA[g]
        ]
        rows.append([", ".join(missing_parts), None, None, None, None, None])

    rows.append(["Poste", "ID", "Prénom", "Nom", "Club", "Moyenne joueur"])
    for g in GROUP_ORDER:
        for p in selected[g]:
            rows.append([GROUP_LABEL[g], p.id, p.prenom, p.nom, p.club, p.note])

    rows.append([None] * 6)
    rows.append([None] * 6)
    return rows


def generate(path: str, dry_run: bool = False) -> None:
    registry = _harvest_country_registry(path)
    by_nat, unmatched = _players_by_nationality(path, registry)

    sheets_content: dict[str, list[list]] = {sheet: [] for sheet in NATION_SHEETS}
    complete_count = 0
    for country in sorted(registry):
        flag, sheet = registry[country]
        selected = _select_squad(by_nat.get(country, []))
        if sum(len(v) for v in selected.values()) == SQUAD_SIZE:
            complete_count += 1
        sheets_content[sheet].extend(_build_block(country, flag, selected))

    print(f"{len(registry)} pays traités, {complete_count} COMPLET ({SQUAD_SIZE}/{SQUAD_SIZE})")
    for sheet in NATION_SHEETS:
        nb_countries = sum(1 for _, s in registry.values() if s == sheet)
        print(f"  {sheet:10s} {nb_countries} pays")

    if unmatched:
        print(f"\n{len(unmatched)} nationalités non reconnues (ignorées, aucun pays existant pour elles) :")
        for tok in sorted(unmatched):
            print(f"  {tok}")

    if dry_run:
        print("\n--dry-run : rien n'a été écrit.")
        return

    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        for sheet in NATION_SHEETS:
            pd.DataFrame(sheets_content[sheet]).to_excel(writer, sheet_name=sheet, index=False, header=False)
    print(f"\nOnglets régénérés : {', '.join(NATION_SHEETS)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Affiche le rapport sans rien écrire.")
    parser.add_argument("--path", default=GAME_PATH, help=f"Chemin du fichier joueurs (défaut : {GAME_PATH})")
    args = parser.parse_args()
    generate(args.path, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
