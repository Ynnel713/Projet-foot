"""Contrat des dicts d'evenements que la racine (le moteur de simulation) fournit au NLG.

Le NLG ne lit JAMAIS les types de la racine (collision du paquet `engine`, dette D15 ; venv sans
`ligue1sim`, R12) : il recoit des dicts, avec des IDENTIFIANTS de joueur (`players.id`, resolus par
la racine -- les evenements du moteur ne portent que des noms, D14) et jamais des noms. Ce module est
la forme de ces dicts et leur validation ; la conversion racine -> dict est HORS V2.1
(proprio-conversion) : les tests du NLG utilisent des dicts ecrits a la main.

Familles (`event_type`, declare dans CHAQUE variante : mypy refuse une redefinition plus etroite dans
la base) :
    "but"          buteur = `player_id` ; `gabarit` ; `passeur_id` / `receveur_id` si le gabarit les porte.
    "occasion"     non-but : `outcome` (arret, hors_cadre, tacle, degagement, poteau, barre) et `gabarit`.
    "carton"       joueur sanctionne = `player_id` ; `outcome` = yellow | direct | second_yellow.
    "remplacement" `entrant_id` (== `player_id`) et `sortant_id`.
`corner`, `coup_franc`, `construction_placee`, `penalty`... sont des GABARITS (de buts comme
d'occasions), pas des `event_type`.

ACTEUR (`player_id`, et `player_team` = equipe de CET acteur) : but -> buteur ; occasion `arret` ->
GARDIEN qui arrete (pas le tireur, que le NarrativeEvent de la racine nomme) ; `tacle`/`degagement` ->
le defenseur ; `hors_cadre`/`poteau`/`barre` -> le tireur ; carton -> le sanctionne ; remplacement ->
l'entrant. Le choix du gardien ou du defenseur (absents du NarrativeEvent) revient a la racine.

Hors perimetre V2.1, documente : autobuts ; coup franc direct (un seul acteur, alors que le contrat
impose passeur et receveur) ; occasions `poteau` et `barre` (aucun pilote ne sait les commenter : pas
de scenario, voir narrative_adapter).
"""

# PAS de `from __future__ import annotations` ici : avec des annotations en chaines, TypedDict ne
# reconnait pas NotRequired et __required_keys__ serait faux (le contrat en depend).
import types
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Literal, NotRequired, TypedDict, Union, get_args, get_origin, get_type_hints

from engine.models import SCORE_CONTEXT_VALUES
from engine.profile_engine import validate_match_sequence

# Les 12 gabarits de narrative.py (_GABARIT_BASE_ZONE). Copie volontaire : le NLG n'importe pas la
# racine ; la liste fait partie du contrat.
Gabarit = Literal[
    "contre_attaque",
    "construction_placee",
    "debordement_centre_tete",
    "percee_individuelle",
    "une_deux",
    "coup_franc",
    "corner",
    "profondeur_1v1",
    "recuperation_haute",
    "decalage_enroulee",
    "penalty",
    "but_gag",
]
GABARITS: tuple[str, ...] = get_args(Gabarit)

OutcomeOccasion = Literal["arret", "hors_cadre", "tacle", "degagement", "poteau", "barre"]
OutcomeCarton = Literal["yellow", "direct", "second_yellow"]


class EventBaseDict(TypedDict):
    """Champs communs. Toutes les cles sont requises ; `journee`, `competition` et `score_context`
    sont requis mais PEUVENT valoir None (inconnus). `event_type` est declare par chaque variante."""

    match_id: str
    match_sequence: int  # rang du match, unite du cooldown (validate_match_sequence)
    event_id: int  # ordinal de l'evenement dans le match (graine du rng) : stable, unique par match_id
    minute: int
    player_id: int  # `players.id` de l'acteur (voir module)
    player_team: str  # club de l'acteur
    home_team: str
    away_team: str
    is_home: bool  # l'acteur joue-t-il a domicile ? doit etre coherent avec player_team
    competition: str | None
    journee: int | None
    score_context: str | None  # une valeur de SCORE_CONTEXT_VALUES, ou None


class ButDict(EventBaseDict):
    event_type: Literal["but"]
    gabarit: Gabarit
    passeur_id: NotRequired[int]
    receveur_id: NotRequired[int]


class OccasionDict(EventBaseDict):
    event_type: Literal["occasion"]
    outcome: OutcomeOccasion
    gabarit: Gabarit


class CartonDict(EventBaseDict):
    event_type: Literal["carton"]
    outcome: OutcomeCarton


class RemplacementDict(EventBaseDict):
    event_type: Literal["remplacement"]
    sortant_id: int
    entrant_id: int  # == player_id


EVENT_TYPES: dict[str, type] = {
    "but": ButDict,
    "occasion": OccasionDict,
    "carton": CartonDict,
    "remplacement": RemplacementDict,
}


def _accepte(valeur: object, annotation: Any) -> bool:
    """`valeur` respecte-t-elle `annotation` (Literal, int, str, bool, `X | None`) ? Un bool n'est
    jamais un int (isinstance(True, int) est vrai en Python)."""
    origine = get_origin(annotation)
    if origine is Literal:
        return valeur in get_args(annotation) and not isinstance(valeur, bool)
    if origine is Union or origine is types.UnionType:
        return any(_accepte(valeur, alternative) for alternative in get_args(annotation))
    if annotation is type(None):
        return valeur is None
    if annotation is bool:
        return isinstance(valeur, bool)
    if annotation is int:
        return isinstance(valeur, int) and not isinstance(valeur, bool)
    if annotation is str:
        return isinstance(valeur, str)
    raise TypeError(f"Annotation non geree par le validateur : {annotation!r}")  # pragma: no cover


def validate_event(event: Mapping[str, Any]) -> None:
    """Leve ValueError (listant TOUS les problemes) si `event` ne respecte pas le contrat :
    `event_type` inconnu ; cles requises manquantes (derivees de `__required_keys__`) ; cles inconnues ;
    type ou valeur invalide (les Literal, dont `outcome` et `gabarit`, sont verifies a l'execution via
    get_type_hints + get_args) ; incoherences metier -- `is_home` contre `player_team`,
    `player_team` hors des deux clubs, `score_context` hors de SCORE_CONTEXT_VALUES, `match_sequence`
    invalide, `passeur_id == receveur_id`, remplacement dont `player_id != entrant_id` ou
    `sortant_id == entrant_id`. TypeError si `event` n'est pas un mapping."""
    if not isinstance(event, Mapping):
        raise TypeError(f"validate_event : un mapping est attendu, recu {type(event).__name__}")
    type_evenement = event.get("event_type")
    famille = EVENT_TYPES.get(type_evenement) if isinstance(type_evenement, str) else None
    if famille is None:
        raise ValueError(f"event_type inconnu : {type_evenement!r} (attendu : {sorted(EVENT_TYPES)}).")

    problemes: list[str] = []
    requises = famille.__required_keys__  # type: ignore[attr-defined]
    autorisees = requises | famille.__optional_keys__  # type: ignore[attr-defined]
    manquantes = sorted(requises - event.keys())
    if manquantes:
        problemes.append(f"cles manquantes : {manquantes}")
    inconnues = sorted(set(event) - autorisees)
    if inconnues:
        problemes.append(f"cles inconnues : {inconnues}")

    annotations = get_type_hints(famille)
    for cle, annotation in annotations.items():
        if cle in event and not _accepte(event[cle], annotation):
            problemes.append(f"{cle}={event[cle]!r} invalide (attendu : {annotation})")

    if not problemes:  # les controles metier supposent des types corrects
        problemes.extend(_incoherences(event))
    if problemes:
        raise ValueError(f"Evenement {type_evenement!r} invalide : " + " ; ".join(problemes))


def _incoherences(event: Mapping[str, Any]) -> list[str]:
    problemes: list[str] = []
    try:
        validate_match_sequence(event["match_sequence"])
    except ValueError as exc:
        problemes.append(str(exc))
    if event["event_id"] < 0:
        problemes.append(f"event_id doit etre >= 0, recu {event['event_id']}")
    if event["minute"] < 0:
        problemes.append(f"minute doit etre >= 0, recu {event['minute']}")
    if event["player_team"] not in (event["home_team"], event["away_team"]):
        problemes.append(f"player_team={event['player_team']!r} n'est ni home_team ni away_team")
    elif event["is_home"] != (event["player_team"] == event["home_team"]):
        problemes.append("is_home incoherent avec player_team (is_home <=> player_team == home_team)")
    if event["score_context"] is not None and event["score_context"] not in SCORE_CONTEXT_VALUES:
        problemes.append(f"score_context={event['score_context']!r} hors de {SCORE_CONTEXT_VALUES}")
    if "passeur_id" in event and "receveur_id" in event and event["passeur_id"] == event["receveur_id"]:
        problemes.append("passeur_id == receveur_id (un joueur ne se passe pas le ballon)")
    if event["event_type"] == "remplacement":
        if event["player_id"] != event["entrant_id"]:
            problemes.append("player_id doit etre l'entrant (player_id == entrant_id)")
        if event["sortant_id"] == event["entrant_id"]:
            problemes.append("sortant_id == entrant_id")
    return problemes


def validate_event_stream(events: Iterable[Mapping[str, Any]]) -> Iterator[Mapping[str, Any]]:
    """Valide un flux d'evenements au fil de l'eau et le re-emet tel quel. Fonction pure (aucun etat
    hors de l'appel). Au-dela de validate_event, refuse : un meme (`match_id`, `event_id`) deux fois
    (l'`event_id` est la graine du rng : deux evenements ne peuvent pas la partager) et un meme
    `match_id` avec deux `match_sequence` differents. L'erreur donne la position de l'evenement fautif."""
    vus: set[tuple[str, int]] = set()
    rang_par_match: dict[str, int] = {}
    for position, event in enumerate(events):
        try:
            validate_event(event)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Evenement n°{position} : {exc}") from exc
        cle = (event["match_id"], event["event_id"])
        if cle in vus:
            raise ValueError(f"Evenement n°{position} : event_id {cle[1]} deja vu pour le match {cle[0]!r}.")
        vus.add(cle)
        precedent = rang_par_match.setdefault(event["match_id"], event["match_sequence"])
        if precedent != event["match_sequence"]:
            raise ValueError(
                f"Evenement n°{position} : le match {event['match_id']!r} a deux match_sequence "
                f"({precedent} puis {event['match_sequence']})."
            )
        yield event
