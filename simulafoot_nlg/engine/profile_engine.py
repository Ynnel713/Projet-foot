"""Normalise des lignes brutes (dict issu d'une requete SQLite, typiquement
`dict(row)` sur un sqlite3.Row) en objets types du domaine (Player,
MatchContext) -- aucun acces base ici, uniquement de la conversion/validation
pure. Jamais d'invention de valeur : un champ absent du dict reste None (ou
tuple vide pour les listes), jamais une valeur de repli arbitraire (ex. age
manquant -> None, jamais 0 ou une moyenne)."""

from __future__ import annotations

from typing import Any

from engine.models import MatchContext, Player


def _split_joined(value: Any, separator: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in str(value).split(separator) if part.strip())


def normalize_player(row: dict[str, Any]) -> Player:
    """Construit un Player depuis une ligne `players` (+ une cle optionnelle
    "attributes": dict[str, int], typiquement assemblee par l'appelant via
    une jointure/aggregation sur player_attributes -- voir
    scenario_engine pour le pattern de chargement equivalent cote scenarios).

    Cas geres explicitement :
    - `secondary_positions`/`preferred_moves` stockes en base comme chaines
      jointes (" / ", " ; ") -- redecoupes ici en tuple.
    - "attributes" absent du dict -> Player.attributes = {} (jamais une
      erreur : un joueur sans attributs importes est un etat normal, voir
      data/import/import_players.py).
    - champs manquants -> None, jamais de valeur inventee.
    """
    if "id" not in row:
        raise KeyError('normalize_player: la ligne ne contient pas de clé "id"')

    return Player(
        id=int(row["id"]),
        first_name=str(row.get("first_name") or ""),
        last_name=str(row.get("last_name") or ""),
        nationality=row.get("nationality"),
        age=row.get("age"),
        position=row.get("position"),
        secondary_positions=_split_joined(row.get("secondary_positions"), " / "),
        club=row.get("club"),
        league=row.get("league"),
        market_value=row.get("market_value"),
        average_rating=row.get("average_rating"),
        height_cm=row.get("height_cm"),
        status=row.get("status"),
        role_category=row.get("role_category"),
        foot=row.get("foot"),
        fm_rating=row.get("fm_rating"),
        weak_foot=row.get("weak_foot"),
        preferred_moves=_split_joined(row.get("preferred_moves"), " ; "),
        attributes=dict(row.get("attributes") or {}),
    )


def _player_or_none(row: dict[str, Any], key: str) -> Player | None:
    """Pass-through d'un `Player` deja resolu par l'appelant (decision D14 :
    resolution par ID hors de ce module, aucun acces base ici). Cle absente
    ou None -> None ; tout autre type (dict brut, nom, ID...) -> TypeError :
    convertir silencieusement un dict en Player inventerait des champs."""
    value = row.get(key)
    if value is None or isinstance(value, Player):
        return value
    raise TypeError(
        f"normalize_match_context: {key!r} doit etre un Player ou None, recu {type(value).__name__}"
    )


def _match_sequence_or_none(row: dict[str, Any]) -> int | None:
    """`match_sequence` : None/absent -> None ; un entier >= 0 sinon. Un bool
    est refuse explicitement (isinstance(True, int) est vrai en Python :
    `match_sequence=True` passerait pour 1 et fausserait les cooldowns sans
    bruit) ; tout autre type -> TypeError ; un rang negatif -> ValueError."""
    value = row.get("match_sequence")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"normalize_match_context: 'match_sequence' doit etre un int, recu {type(value).__name__}")
    if value < 0:
        raise ValueError(f"normalize_match_context: 'match_sequence' doit etre >= 0, recu {value}")
    return value


def normalize_match_context(row: dict[str, Any]) -> MatchContext:
    """Construit un MatchContext depuis un dict brut (ex. un evenement issu
    du moteur de simulation ligue1sim, pas d'une table dediee -- voir
    engine.models.MatchContext). `match_id` est la seule cle obligatoire.
    `sortant`/`entrant` sont des `Player` deja resolus (voir _player_or_none)."""
    if "match_id" not in row:
        raise KeyError('normalize_match_context: la ligne ne contient pas de clé "match_id"')

    return MatchContext(
        match_id=str(row["match_id"]),
        minute=row.get("minute"),
        home_team=row.get("home_team"),
        away_team=row.get("away_team"),
        home_score=row.get("home_score"),
        away_score=row.get("away_score"),
        player_team=row.get("player_team"),
        is_home=row.get("is_home"),
        competition=row.get("competition"),
        journee=row.get("journee"),
        scenario_code=row.get("scenario_code"),
        score_context=row.get("score_context"),
        gabarit=row.get("gabarit"),
        sortant=_player_or_none(row, "sortant"),
        entrant=_player_or_none(row, "entrant"),
        match_sequence=_match_sequence_or_none(row),
    )


def compute_score_context(home_score_before: int, away_score_before: int, scorer_is_home: bool) -> str:
    """Deduit l'effet d'un but sur le score (voir engine.models.SCORE_CONTEXT_VALUES)
    a partir du score juste AVANT ce but et de l'equipe qui vient de marquer
    -- pure derivation arithmetique, pas une supposition : le resultat est
    entierement determine par les 3 arguments. A appeler par le moteur de
    simulation au moment ou il construit le MatchContext d'un but, puis a
    passer tel quel a normalize_match_context (cle "score_context").

    Retourne toujours une valeur de SCORE_CONTEXT_VALUES :
    - "ouverture_score" : 0-0 avant le but (premier but du match).
    - "egalisation" : l'equipe qui marque etait menee d'exactement 1 but,
      revient a egalite.
    - "prise_avantage" : score deja a egalite (mais pas 0-0) avant le but,
      l'equipe qui marque passe devant.
    - "creuse_ecart" : l'equipe qui marque menait deja avant le but.
    - "reduit_ecart" : l'equipe qui marque reste derriere apres son but."""
    scorer_before = home_score_before if scorer_is_home else away_score_before
    opponent_before = away_score_before if scorer_is_home else home_score_before
    scorer_after = scorer_before + 1

    if home_score_before == 0 and away_score_before == 0:
        return "ouverture_score"
    if scorer_after == opponent_before:
        return "egalisation"
    if scorer_before > opponent_before:
        return "creuse_ecart"
    if scorer_before == opponent_before:
        return "prise_avantage"
    return "reduit_ecart"
