"""Ingestion NLG cote racine : `Timeline` (engine/narrative.py) -> liste de dicts d'evenements, au
contrat de `simulafoot_nlg/engine/event_contract.py` (voir simulafoot_nlg/SPEC_NLG_INGESTION.md).

Deux projets, aucun import croise : le NLG ne lit jamais ce module ni les types de la racine ; il
recoit des dicts (puis du JSON Lines, voir `write_jsonl`). Les formes sont donc REPLIQUEES ici, pas
importees.

Un dict par evenement commentable : buts et occasions (`NarrativeEvent`), cartons (`CardEvent`),
remplacements (`SubstitutionEvent`). Tri par minute (a minute egale : buts/occasions, puis cartons,
puis remplacements, puis ordre d'origine) ; `event_id` = rang dans ce tri, calcule AVANT tout rejet :
un evenement ecarte ne decale jamais l'`event_id` (donc la graine de rendu) des suivants -- unique et
stable, avec d'eventuels trous.

`match_sequence` est fourni par l'appelant (seul a connaitre l'ordre des matchs) ; `match_id` est celui
de la `Timeline` sauf surcharge. Un evenement qu'on ne sait pas convertir (joueur introuvable...) est
ECARTE, jamais devine : il est signale dans `skipped` si l'appelant le demande.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from random import Random
from typing import Any

from ligue1sim.events import CardEvent, SubstitutionEvent
from ligue1sim.players import DEFENDER, GOALKEEPER, Player, position_group

from narrative import BUT, NarrativeEvent, Timeline

# Rang de tri a minute egale : ce qui se joue (but, occasion) avant la sanction, avant le changement.
_RANG_NARRATIF, _RANG_CARTON, _RANG_REMPLACEMENT = 0, 1, 2

# Decision B2 n°6 : un but SANS passeur sur ces gabarits n'a pas de scenario propre (les pools COUP_FRANC,
# CONSTRUCTION, CORNER decrivent une passe ou un centre) -> scenario BUT. Le dict ne porte pas de
# scenario_code (le NLG le deduit du gabarit, narrative_adapter.event_to_scenario) : la regle vit ICI, en
# remplacant le gabarit par un gabarit neutre qui mene a BUT. `percee_individuelle` (action seule) : aucune
# phrase de BUT ne conditionne ce gabarit (seul `penalty` active une variante). Le gabarit d'origine reste
# dans `Timeline` ; seul le dict est modifie.
_GABARITS_A_PASSEUR = frozenset({"corner", "coup_franc", "construction_placee"})
GABARIT_BUT_SANS_PASSEUR = "percee_individuelle"

_CARTON_OUTCOMES = {"yellow", "second_yellow", "direct"}


class EvenementEcarte(ValueError):
    """Un evenement du moteur ne peut pas devenir un dict du contrat ; le message dit pourquoi."""


class EffectifClub:
    """Index d'un effectif (`Club.players`) par nom, pour resoudre un nom du moteur en `Player.id`.

    Pas de lookup en base (decision B2) : l'id est lu directement sur `Player.id`. Les titulaires du
    `Lineup` et les remplacants (reconstruits sans id par `narrative._player_from_stat`) se resolvent
    pareil, par (nom, club) dans l'effectif du club -- le club est donne par le cote (domicile ou
    exterieur) de l'evenement. Deux joueurs de meme nom dans un club : ambigu, ValueError."""

    def __init__(self, club: str, players: Sequence[Player]) -> None:
        self.club = club
        self._par_nom: dict[str, list[Player]] = {}
        for player in players:
            self._par_nom.setdefault(player.name, []).append(player)

    def joueur(self, name: str) -> Player:
        candidats = self._par_nom.get(name, [])
        if not candidats:
            raise EvenementEcarte(f"joueur {name!r} introuvable dans l'effectif de {self.club}")
        if len(candidats) > 1:
            raise EvenementEcarte(f"homonymes dans l'effectif de {self.club} : {name!r} ({len(candidats)} joueurs)")
        return candidats[0]

    def player_id(self, name: str) -> int:
        player = self.joueur(name)
        if player.id is None:
            raise EvenementEcarte(f"joueur {name!r} ({self.club}) sans Player.id : refuse")
        return player.id


def en_jeu_a(timeline: Timeline, club: str, minute: int) -> list[str]:
    """Noms des joueurs de `club` sur le terrain a `minute` : titulaires du `Lineup`, moins les sortants
    et les expulses (`direct`, `second_yellow`), plus les entrants, pour les evenements STRICTEMENT
    anterieurs a `minute` (a minute egale, l'occasion se joue avant le changement). Ordre :
    titulaires d'abord, puis entrants dans l'ordre des changements."""
    lineup = timeline.home_lineup if club == timeline.home_team else timeline.away_lineup
    sur_le_terrain = [p.name for p in lineup.players]
    changements = [(e.minute, 0, e) for e in timeline.substitutions if e.club_name == club and e.minute < minute]
    expulsions = [(e.minute, 1, e) for e in timeline.cards
                  if e.club_name == club and e.minute < minute and e.card_type in {"direct", "second_yellow"}]
    for _minute, _rang, e in sorted(changements + expulsions, key=lambda t: t[:2]):
        if isinstance(e, SubstitutionEvent):
            if e.player_off in sur_le_terrain:
                sur_le_terrain.remove(e.player_off)
            sur_le_terrain.append(e.player_on)
        elif e.player in sur_le_terrain:
            sur_le_terrain.remove(e.player)
    return sur_le_terrain


def _graine(match_id: str, minute: int, role: str) -> int:
    digest = hashlib.sha256(f"nlg_ingestion|{match_id}|{minute}|{role}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def choisir_acteur_defensif(timeline: Timeline, match_id: str, club: str, minute: int, groupe: str, squad: "EffectifClub") -> int:
    """`player_id` du gardien (`GOALKEEPER`) ou d'un defenseur (`DEFENDER`) de `club` a `minute`.

    Deterministe : candidats tries par nom, tirage par un `Random` seede par (match_id, minute, role) --
    jamais l'etat global, jamais l'horloge. Un seul gardien est normalement en jeu (titulaire, ou son
    remplacant apres un changement) ; aucun candidat -> evenement ecarte."""
    candidats = sorted(n for n in en_jeu_a(timeline, club, minute) if position_group(squad.joueur(n).poste) == groupe)
    if not candidats:
        raise EvenementEcarte(f"aucun {groupe} en jeu pour {club} a la minute {minute}")
    nom = Random(_graine(match_id, minute, groupe)).choice(candidats)
    return squad.player_id(nom)


def compute_score_context(home_score_before: int, away_score_before: int, scorer_is_home: bool) -> str:
    """Effet d'un but sur le score, d'apres le score juste AVANT lui. REPLIQUE de
    `simulafoot_nlg/engine/profile_engine.compute_score_context` (deux projets, pas d'import croise) ;
    un test verrouille les 5 valeurs de `SCORE_CONTEXT_VALUES` du contrat."""
    scorer_before = home_score_before if scorer_is_home else away_score_before
    opponent_before = away_score_before if scorer_is_home else home_score_before
    if home_score_before == 0 and away_score_before == 0:
        return "ouverture_score"
    if scorer_before + 1 == opponent_before:
        return "egalisation"
    if scorer_before > opponent_before:
        return "creuse_ecart"
    if scorer_before == opponent_before:
        return "prise_avantage"
    return "reduit_ecart"


def _commun(timeline: Timeline, match_id: str, match_sequence: int, event_id: int, minute: int, club: str,
            competition: str | None, journee: int | None) -> dict[str, Any]:
    return {
        "match_id": match_id,
        "match_sequence": match_sequence,
        "event_id": event_id,
        "minute": minute,
        "player_team": club,
        "home_team": timeline.home_team,
        "away_team": timeline.away_team,
        "is_home": club == timeline.home_team,
        "competition": competition,
        "journee": journee,
        "score_context": None,
    }


def _narratif_to_dict(event: NarrativeEvent, commun: dict[str, Any], squad: EffectifClub,
                      timeline: Timeline, adverse: EffectifClub) -> dict[str, Any]:
    if event.event_type == BUT:
        dico = {**commun, "event_type": "but", "gabarit": event.gabarit, "player_id": squad.player_id(event.main_player)}
        if len(event.involved_players) > 1:
            dico["passeur_id"] = squad.player_id(event.involved_players[1])
        elif event.gabarit in _GABARITS_A_PASSEUR:
            dico["gabarit"] = GABARIT_BUT_SANS_PASSEUR  # -> scenario BUT, voir plus haut
        return dico
    if event.outcome in {"hors_cadre", "poteau", "barre"}:  # le tireur est l'acteur
        return {**commun, "event_type": "occasion", "gabarit": event.gabarit, "outcome": event.outcome,
                "player_id": squad.player_id(event.main_player)}
    # arret -> gardien adverse ; tacle / degagement -> defenseur adverse (le NarrativeEvent ne nomme que le tireur).
    groupe = GOALKEEPER if event.outcome == "arret" else DEFENDER
    acteur = choisir_acteur_defensif(timeline, commun["match_id"], adverse.club, event.minute, groupe, adverse)
    return {**{**commun, "player_team": adverse.club, "is_home": adverse.club == commun["home_team"]},
            "event_type": "occasion", "gabarit": event.gabarit, "outcome": event.outcome, "player_id": acteur}


def _carton_to_dict(event: CardEvent, commun: dict[str, Any], squad: EffectifClub, timeline: Timeline, adverse: EffectifClub) -> dict[str, Any]:
    if event.card_type not in _CARTON_OUTCOMES:
        raise EvenementEcarte(f"type de carton inconnu : {event.card_type!r}")
    return {**commun, "event_type": "carton", "outcome": event.card_type, "player_id": squad.player_id(event.player)}


def _remplacement_to_dict(event: SubstitutionEvent, commun: dict[str, Any], squad: EffectifClub, timeline: Timeline, adverse: EffectifClub) -> dict[str, Any]:
    entrant = squad.player_id(event.player_on)
    return {**commun, "event_type": "remplacement", "player_id": entrant, "entrant_id": entrant,
            "sortant_id": squad.player_id(event.player_off)}


def timeline_to_events(
    timeline: Timeline,
    *,
    match_sequence: int,
    home_squad: Sequence[Player],
    away_squad: Sequence[Player],
    competition: str | None = None,
    journee: int | None = None,
    match_id: str | None = None,
    skipped: list[tuple[int, str]] | None = None,
) -> list[dict[str, Any]]:
    """Dicts du contrat NLG pour un match, tries par minute, `event_id` = rang.

    `home_squad`/`away_squad` : effectifs complets (`Club.players`) -- les ids viennent de `Player.id`.
    `skipped` (optionnel) recoit `(event_id, raison)` pour chaque evenement ecarte."""
    match_id = match_id or timeline.match_id
    squads = {timeline.home_team: EffectifClub(timeline.home_team, home_squad),
              timeline.away_team: EffectifClub(timeline.away_team, away_squad)}

    # (minute, rang, ordre d'origine, club, evenement du moteur, convertisseur)
    candidats: list[tuple[int, int, int, str, Any, Any]] = []
    for i, event in enumerate(timeline.events):
        candidats.append((event.minute, _RANG_NARRATIF, i, event.team, event, _narratif_to_dict))
    for i, event in enumerate(timeline.cards):
        candidats.append((event.minute, _RANG_CARTON, i, event.club_name, event, _carton_to_dict))
    for i, event in enumerate(timeline.substitutions):
        candidats.append((event.minute, _RANG_REMPLACEMENT, i, event.club_name, event, _remplacement_to_dict))
    candidats.sort(key=lambda c: c[:3])

    dicts: list[dict[str, Any]] = []
    score = {timeline.home_team: 0, timeline.away_team: 0}  # score avant l'evenement courant, dans l'ordre du tri
    for event_id, (minute, _rang, _ordre, club, event, convertir) in enumerate(candidats):
        commun = _commun(timeline, match_id, match_sequence, event_id, minute, club, competition, journee)
        if isinstance(event, NarrativeEvent) and (event.event_type == BUT or event.outcome == "arret"):
            # but : effet du but ; occasion `arret` : score HYPOTHETIQUE du point de vue du tireur (contrat).
            commun["score_context"] = compute_score_context(
                score[timeline.home_team], score[timeline.away_team], event.team == timeline.home_team
            )
        if isinstance(event, NarrativeEvent) and event.event_type == BUT:
            score[event.team] += 1  # apres le calcul : le contexte d'un but voit le score AVANT lui
        try:
            adverse = squads[timeline.away_team if club == timeline.home_team else timeline.home_team]
            dicts.append(convertir(event, commun, squads[club], timeline, adverse))
        except EvenementEcarte as exc:
            if skipped is not None:
                skipped.append((event_id, str(exc)))
    return dicts
