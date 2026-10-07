"""Fil de commentaire « live » d'un match déjà joué : les événements RÉELS du moteur (buts, cartons, remplacements, penaltys
manqués) mis en texte français, dans l'ordre chronologique.

Pas de simulation ici : tout vient de `MatchEvents`, donc le fil est cohérent avec les remplaçants et les stats déjà affichés
sur l'écran du match (le remplacement de la 68e du fil EST celui de la liste des remplaçants). Le texte est déterministe (la
variante de phrase dépend du match et de la minute, jamais de l'horloge ni d'un tirage global).

Chaque événement porte son texte en morceaux (`parts`) : les noms de joueurs sont marqués (`player=True`) pour que l'UI les mette
en valeur sans analyser la phrase."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from ligue1sim.events import CardEvent, GoalEvent, MatchEvents, PenaltyMissedEvent, SubstitutionEvent

# Ordre à minute égale : coup d'envoi, puis ce qui se joue (but, penalty manqué), la sanction, le changement, le coup de sifflet final.
_ORDER = {"start": 0, "goal": 1, "penalty_missed": 2, "yellow": 3, "second_yellow": 3, "red": 3, "sub": 4, "end": 5}

_TITLES = {
    "start": "COUP D'ENVOI",
    "goal": "BUT !",
    "penalty_missed": "PENALTY MANQUÉ",
    "yellow": "CARTON JAUNE",
    "second_yellow": "DEUXIÈME JAUNE",
    "red": "CARTON ROUGE",
    "sub": "REMPLACEMENT",
    "end": "FIN DU MATCH",
}

_FIN_DU_MATCH = 90


@dataclass(frozen=True)
class LiveEvent:
    minute: int
    kind: str  # clé de _TITLES
    title: str
    side: str | None  # "home" | "away" | None (coup d'envoi, fin du match)
    club: str | None
    parts: tuple[tuple[str, bool], ...]  # (texte, est_un_nom_de_joueur)


_TOKEN = re.compile(r"(\{[a-z_]+\})")


def _variant(options: list[str], *key: object) -> str:
    """Variante déterministe : sha256 de la clé (match, minute, type), jamais hash() ni l'état aléatoire global."""
    digest = hashlib.sha256("|".join(map(str, key)).encode("utf-8")).digest()
    return options[int.from_bytes(digest[:4], "big") % len(options)]


def _goal_text(scored: GoalEvent, home_score: int, away_score: int, scorer_is_home: bool, key: tuple) -> str:
    """Modèle du but selon son effet sur le score (score AVANT le but), avec le passeur s'il existe."""
    own, opp = (home_score, away_score) if scorer_is_home else (away_score, home_score)
    after = own + 1
    if scored.penalty:
        options = ["{buteur} transforme le penalty pour {club} !", "{buteur} ne tremble pas sur le penalty : {club} marque !"]
    elif own == 0 and opp == 0:
        options = ["{buteur} ouvre le score pour {club} !", "{club} ouvre le score : {buteur} fait mouche !"]
    elif after == opp:
        options = ["{buteur} égalise pour {club} !", "{club} revient à hauteur : {buteur} égalise !"]
    elif own == opp:
        options = ["{buteur} donne l'avantage à {club} !", "{buteur} remet {club} devant !"]
    elif own > opp:
        options = ["{buteur} creuse l'écart pour {club}.", "{club} double la mise : {buteur} marque encore !"]
    else:
        options = ["{buteur} réduit l'écart pour {club}.", "{buteur} relance {club} en réduisant le score !"]
    texte = _variant(options, *key)
    if scored.assist and not scored.penalty:
        # élision : « d'Axel », « de Romain » (le h aspiré/muet n'est pas distingué : « de Hugo »)
        texte += " Passe décisive d'{passeur}." if scored.assist[0].lower() in "aeiouyàâäéèêëîïôöûüœ" else " Passe décisive de {passeur}."
    return texte


def _sort_key(event: LiveEvent) -> tuple[int, int]:
    return (event.minute, _ORDER[event.kind])


def build_live_feed(events: MatchEvents, home: str, away: str) -> list[LiveEvent]:
    """Fil chronologique du match. Le score courant est recalculé en parcourant les buts dans l'ordre (minute, puis ordre du
    moteur) : il sert au texte des buts (ouverture du score, égalisation...) et reste cohérent avec le score final."""
    items: list[tuple[LiveEvent, object]] = [
        (LiveEvent(0, "start", _TITLES["start"], None, None, (("Le coup d'envoi est donné.", False),)), None),
        (LiveEvent(_FIN_DU_MATCH, "end", _TITLES["end"], None, None, (("Le coup de sifflet final retentit.", False),)), None),
    ]

    for goal in events.goals:
        items.append((LiveEvent(goal.minute, "goal", _TITLES["goal"], None, goal.club_name, ()), goal))
    for miss in events.penalties_missed:
        items.append((LiveEvent(miss.minute, "penalty_missed", _TITLES["penalty_missed"], None, miss.club_name, ()), miss))
    for card in events.cards:
        kind = {"yellow": "yellow", "second_yellow": "second_yellow", "direct": "red"}[card.card_type]
        items.append((LiveEvent(card.minute, kind, _TITLES[kind], None, card.club_name, ()), card))
    for sub in events.substitutions:
        items.append((LiveEvent(sub.minute, "sub", _TITLES["sub"], None, sub.club_name, ()), sub))

    items.sort(key=lambda it: _sort_key(it[0]))  # tri stable : à minute et type égaux, ordre du moteur

    feed: list[LiveEvent] = []
    score = {home: 0, away: 0}
    for event, source in items:
        if source is None:
            feed.append(event)
            continue
        club = event.club
        side = "home" if club == home else "away"
        key = (home, away, event.minute, event.kind, club)
        if isinstance(source, GoalEvent):
            template = _goal_text(source, score[home], score[away], club == home, key)
            names = {"buteur": source.scorer, "club": club, "passeur": source.assist or ""}
            score[club] += 1
        elif isinstance(source, PenaltyMissedEvent):
            template = _variant(["{joueur} manque son penalty pour {club} !", "{club} rate le penalty : {joueur} échoue !"], *key)
            names = {"joueur": source.player, "club": club}
        elif isinstance(source, CardEvent):
            template = {
                "yellow": _variant(["{joueur} ({club}) est averti.", "Carton jaune pour {joueur}, côté {club}."], *key),
                "second_yellow": "Deuxième jaune pour {joueur} : il est exclu, {club} termine à dix.",
                "red": "Carton rouge direct pour {joueur} ! {club} jouera à dix.",
            }[event.kind]
            names = {"joueur": source.player, "club": club}
        else:  # SubstitutionEvent
            assert isinstance(source, SubstitutionEvent)
            template = _variant(["{club} : {entrant} remplace {sortant}.", "Changement pour {club} : {entrant} entre, {sortant} sort."], *key)
            names = {"entrant": source.player_on, "sortant": source.player_off, "club": club}
        feed.append(
            LiveEvent(event.minute, event.kind, event.title, side, club, _parts(template, names))
        )
    return feed


def _parts(template: str, names: dict[str, str]) -> tuple[tuple[str, bool], ...]:
    """Découpe `template` : `{joueur}`-like -> (nom, True) ; `{club}` et le reste -> (texte, False)."""
    morceaux: list[tuple[str, bool]] = []
    for piece in _TOKEN.split(template):
        if not piece:
            continue
        if _TOKEN.fullmatch(piece):
            nom = piece[1:-1]
            morceaux.append((names[nom], nom != "club"))
        else:
            morceaux.append((piece, False))
    return tuple(morceaux)
