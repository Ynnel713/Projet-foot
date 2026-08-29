"""Sélections nationales : parse les 5 onglets continentaux (Europe/Afrique/
Amérique/Asie/Océanie) de data/joueurs.xlsx en objets `Club`-compatibles, un
par pays marqué COMPLET (23/23) -- conformément à la notice, seules les
sélections complètes sont proposées en jeu (les autres se complètent au fur
et à mesure que de nouveaux joueurs sont ajoutés/notés dans la feuille
principale).

Chaque bloc de pays y liste ses 23 joueurs avec seulement leur poste au sens
large (Gardien/Défenseur/Milieu/Attaquant), pas leur poste précis
(RB/LB/MOC/...) : on recroise donc par ID avec "Infos principales" (déjà
chargé via `clubs.load_all_clubs`) pour reconstruire des `Player` complets
et fidèles à ceux utilisés partout ailleurs dans le jeu (poste exact, poste
secondaire, style de jeu...), avec juste le club/championnat remplacés par
la sélection nationale.
"""

from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd

from ligue1sim.clubs import Club, load_all_clubs
from ligue1sim.players import Player

NATION_SHEETS = ["Europe", "Afrique", "Amérique", "Asie", "Océanie"]
CHAMPIONNAT_LABEL = "Sélection nationale"

# Confédération par onglet -- l'onglet "Amérique" mélange CONMEBOL et
# CONCACAF (un seul onglet historique), donc on affine par pays via
# _CONCACAF_NAMES juste en dessous. Un pays hors de ce set sur l'onglet
# "Amérique" est considéré CONMEBOL par défaut.
CONFEDERATION_BY_SHEET = {
    "Europe": "UEFA",
    "Afrique": "CAF",
    "Amérique": "CONMEBOL",
    "Asie": "AFC",
    "Océanie": "OFC",
}
# Fédérations d'Amérique du Nord/centrale/Caraïbes rattachées à la CONCACAF
# malgré l'onglet "Amérique" générique -- inclut Suriname, qui a rejoint la
# CONCACAF en 2016 bien que géographiquement en Amérique du Sud.
_CONCACAF_NAMES = {
    "Canada", "Costa Rica", "Curaçao", "États-Unis", "Guadeloupe", "Haïti",
    "Honduras", "Jamaïque", "Martinique", "Mexique", "Panama", "Porto Rico",
    "République dominicaine", "Suriname", "Trinité-et-Tobago",
}

_TITLE_ROW = re.compile(r"^(.+?) — (COMPLET|INCOMPLET)")
_HEADER_MARKER = "Poste"


def _players_by_id(path: str) -> dict[int, Player]:
    return {p.id: p for option in load_all_clubs(path) for p in option.players if p.id is not None}


def _country_blocks(sheet_df: pd.DataFrame) -> list[tuple[str, bool, pd.DataFrame]]:
    """[(nom du pays avec son drapeau, sélection complète (23/23) ?, lignes
    joueurs du bloc)], en parcourant l'onglet ligne par ligne : chaque pays y
    est un bloc "titre (drapeau + statut) / composition / [manquants] /
    en-tête Poste-ID-Prénom-Nom-Club-Moyenne / 23 lignes joueurs / séparateur
    vide" (voir le docstring du module)."""
    blocks: list[tuple[str, bool, pd.DataFrame]] = []
    n = len(sheet_df)
    i = 0
    while i < n:
        value = sheet_df.iat[i, 0]
        match = _TITLE_ROW.match(value) if isinstance(value, str) else None
        if match is None:
            i += 1
            continue

        country, status = match.group(1).strip(), match.group(2)
        header_row = i + 1
        while header_row < n and sheet_df.iat[header_row, 0] != _HEADER_MARKER:
            header_row += 1
        end_row = header_row + 1
        while end_row < n and pd.notna(sheet_df.iat[end_row, 0]):
            end_row += 1

        players_df = sheet_df.iloc[header_row + 1 : end_row].copy()
        players_df.columns = sheet_df.iloc[header_row]
        blocks.append((country, status == "COMPLET", players_df))
        i = end_row
    return blocks


def load_national_teams(path: str, *, complete_only: bool = True) -> list[Club]:
    """Une sélection par pays (nom = drapeau + pays, ex. "🇫🇷 France"),
    limité par défaut aux sélections COMPLET (23/23). Mis en cache (5 gros
    onglets à parser, voir clubs.py pour le même besoin côté clubs) : appeler
    `clear_cache()` si le classeur est modifié en cours de session."""
    teams, complete_names = _load_all_national_teams(path)
    if not complete_only:
        return list(teams)
    return [t for t in teams if t.name in complete_names]


@lru_cache(maxsize=None)
def _load_all_national_teams(path: str) -> tuple[tuple[Club, ...], frozenset[str]]:
    lookup = _players_by_id(path)
    teams: list[Club] = []
    complete_names: set[str] = set()
    for sheet in NATION_SHEETS:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        for country, complete, players_df in _country_blocks(df):
            players = [
                _as_national_player(base, country)
                for _, row in players_df.iterrows()
                if (base := lookup.get(_safe_int(row["ID"]))) is not None
            ]
            teams.append(Club(name=country, players=players))
            if complete:
                complete_names.add(country)
    return tuple(teams), frozenset(complete_names)


def clear_cache() -> None:
    _load_all_national_teams.cache_clear()
    _confederation_by_team.cache_clear()


@lru_cache(maxsize=None)
def _confederation_by_team(path: str) -> dict[str, str]:
    """{nom d'équipe tel que renvoyé par `load_national_teams` (drapeau +
    pays) : confédération}, en reparcourant les mêmes 5 onglets -- sert à
    grouper "Sélections nationales" par continent côté UI sans dupliquer le
    nom du pays."""
    result: dict[str, str] = {}
    for sheet in NATION_SHEETS:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        confederation = CONFEDERATION_BY_SHEET[sheet]
        for country, _, _ in _country_blocks(df):
            bare_name = country.split(" ", 1)[1] if " " in country else country
            if confederation == "CONMEBOL" and bare_name in _CONCACAF_NAMES:
                result[country] = "CONCACAF"
            else:
                result[country] = confederation
    return result


def confederation(path: str, team_name: str) -> str:
    """Confédération de l'équipe `team_name` (tel que renvoyé par
    `load_national_teams`, ex. "🇧🇷 Brésil"). "?" si inconnue (ne devrait pas
    arriver pour une équipe issue de `load_national_teams`)."""
    return _confederation_by_team(path).get(team_name, "?")


def _as_national_player(base: Player, country: str) -> Player:
    """Le joueur `base` (tel que chargé pour son club réel), transposé dans
    le contexte de la sélection `country` -- poste, notes, style de jeu
    inchangés, seuls club/championnat changent."""
    return Player(
        prenom=base.prenom,
        nom=base.nom,
        nationalite=base.nationalite,
        age=base.age,
        poste=base.poste,
        note=base.note,
        club=country,
        championnat=CHAMPIONNAT_LABEL,
        poste_secondaire=base.poste_secondaire,
        categorie=base.categorie,
        id=base.id,
    )


def _safe_int(value: object) -> int | None:
    return int(value) if pd.notna(value) else None
