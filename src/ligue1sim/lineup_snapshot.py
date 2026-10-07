"""Compo réellement alignée à la simulation, figée dans le `Match`.

Problème résolu : `Match` ne gardait que des `PlayerMatchStat` (nom, poste,
titulaire) -- insuffisant pour rejouer un match en animation sans rappeler
`pick_best_formation`, ce qui diverge dès que l'effectif du club change. Le
`LineupSnapshot` ci-dessous est pris dans `events.generate_match_events`, au
moment même où la compo est consommée, et voyage avec `MatchEvents`.

SOURCE DE VÉRITÉ UNIQUE : `lineup` est le `Lineup` exact utilisé par la
simulation (mêmes `Player` complets, mêmes `bands`, mêmes notes de secteur).
Les consommateurs (animation, narration) le lisent via `persisted_lineups` /
`require_persisted_lineups` et ne rappellent JAMAIS `pick_best_formation`.

Ce que le modèle de données n'a PAS (rien n'est inventé ici) : il n'existe ni
"rôle tactique" ni "consigne individuelle" distincts dans le moteur. Les
équivalents portés tels quels par `Player` sont `categorie` (rôle/style, ex.
"buteur_axial") et `preferred_moves` ; `Lineup.bands` donne la ligne du
dispositif de chaque joueur.

Dégradation contrôlée (matchs sans snapshot, ex. documents antérieurs) :
`persisted_lineups` renvoie `None`, `require_persisted_lineups` lève
`LineupNotPersistedError`. Aucun recalcul silencieux.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from ligue1sim.lineup import Lineup
from ligue1sim.players import Player

if TYPE_CHECKING:  # pragma: no cover
    from ligue1sim.schedule import Match

SCHEMA_VERSION = 1


class LineupNotPersistedError(LookupError):
    """Le match n'a pas de compo persistée (document antérieur au snapshot,
    ou match sans `MatchEvents`). Le moteur graphique doit dégrader (pas
    d'animation de compo) plutôt que recalculer une compo."""


@dataclass(frozen=True)
class StarterSlot:
    """Place d'un titulaire dans le onze de départ, au coup d'envoi.

    `x`/`y` : position (0-100, % du terrain) calculée par
    `pitch_layout.place_starting_xi(attacking_up=True)` À LA SIMULATION --
    trace d'audit de la zone assignée. `enrich_with_background` recalcule
    ses positions depuis `lineup` (poste + bande), il ne lit pas ces champs.
    """

    player_id: int | str  # `templates.player_id_of` : Player.id, sinon le nom
    name: str
    poste: str
    band: int | None
    x: float
    y: float


@dataclass(frozen=True)
class LineupSnapshot:
    schema_version: int
    lineup: Lineup  # le Lineup EXACT de la simulation (substitutes vide, comme à la simulation)
    starters: list[StarterSlot]  # onze de départ, ordre de `lineup.players`
    # Remplaçants ayant réellement joué (profil `Player` complet, pas la
    # version réduite reconstruite depuis PlayerMatchStat). Statut "remplaçant".
    entered_substitutes: list[Player] = field(default_factory=list)


def snapshot_lineup(lineup: Lineup, entered_substitutes: list[Player]) -> LineupSnapshot:
    """Fige `lineup` (copie défensive : les listes/dict mutables du `Lineup`
    ne sont pas partagés avec la simulation). Aucun aléa, aucun effet de
    bord : n'altère pas les tirages du moteur."""
    # Imports locaux : pitch_layout importe events, qui importe ce module.
    from ligue1sim.events import PlayerMatchStat
    from ligue1sim.pitch_layout import place_starting_xi

    frozen = replace(lineup, players=list(lineup.players), bands=dict(lineup.bands), substitutes=list(lineup.substitutes))
    stats = [
        PlayerMatchStat(
            player_name=p.name, club_name=lineup.club_name, poste=p.poste, started=True, band=lineup.bands.get(p.name)
        )
        for p in lineup.players
    ]
    placed = {pl.stat.player_name: pl for pl in place_starting_xi(stats, attacking_up=True)}
    starters = []
    for p in lineup.players:
        pl = placed[p.name]
        starters.append(
            StarterSlot(
                player_id=p.id if p.id is not None else p.name,
                name=p.name,
                poste=p.poste,
                band=lineup.bands.get(p.name),
                x=pl.x,
                y=pl.y,
            )
        )
    return LineupSnapshot(
        schema_version=SCHEMA_VERSION,
        lineup=frozen,
        starters=starters,
        entered_substitutes=list(entered_substitutes),
    )


def persisted_lineups(match: Match) -> tuple[Lineup, Lineup] | None:
    """(compo domicile, compo extérieur) persistées, ou `None` si le match
    n'en a pas (dégradation contrôlée, voir le docstring du module)."""
    events = match.events
    if events is None or events.home_lineup_snapshot is None or events.away_lineup_snapshot is None:
        return None
    return events.home_lineup_snapshot.lineup, events.away_lineup_snapshot.lineup


def require_persisted_lineups(match: Match) -> tuple[Lineup, Lineup]:
    lineups = persisted_lineups(match)
    if lineups is None:
        raise LineupNotPersistedError(
            f"{match.home} vs {match.away} : pas de compo persistée (match antérieur au snapshot ou sans MatchEvents) ; "
            "aucun recalcul via pick_best_formation n'est tenté"
        )
    return lineups


_SENDING_OFF = ("direct", "second_yellow")


def players_on_pitch(match: Match, club_name: str, minute: int) -> list[Player]:
    """Joueurs de `club_name` sur le terrain à `minute`, depuis le seul Match
    persisté (aucun recalcul de compo). Onze de départ du snapshot, puis :
    un remplacement (`SubstitutionEvent`, noms joueur_off/joueur_on) à la
    minute m retire le sortant et fait entrer l'entrant à partir de m (même
    convention que `events._SquadEntry.minute_range` : présent de minute_on à
    minute_off) ; un carton rouge (`CardEvent` "direct"/"second_yellow") retire
    le joueur à sa minute, sans remplaçant (un remplacement ultérieur d'un
    joueur déjà expulsé -- tiré indépendamment par le moteur -- fait quand
    même entrer l'entrant : événement persisté suivi à la lettre). Un titulaire blessé SANS
    remplaçant disponible reste sur le terrain, comme dans le moteur
    (`_play_match_squad`). Les joueurs sont identifiés par nom, clé unique
    d'un effectif dans tout le moteur (`PlayerMatchStat.player_name`)."""
    home, away = require_persisted_lineups(match)
    snapshots = (match.events.home_lineup_snapshot, match.events.away_lineup_snapshot)
    snapshot = next((s for s in snapshots if s.lineup.club_name == club_name), None)
    if snapshot is None:
        raise ValueError(f"{club_name!r} ne joue pas ce match ({home.club_name} vs {away.club_name})")

    by_name = {p.name: p for p in snapshot.lineup.players}
    by_name.update({p.name: p for p in snapshot.entered_substitutes})
    on_pitch = [p.name for p in snapshot.lineup.players]

    timeline = [(s.minute, 0, s) for s in match.events.substitutions if s.club_name == club_name]
    timeline += [(c.minute, 1, c) for c in match.events.cards if c.club_name == club_name and c.card_type in _SENDING_OFF]
    for when, _, event in sorted(timeline, key=lambda t: (t[0], t[1])):
        if when > minute:
            break
        if hasattr(event, "player_off"):
            if event.player_off in on_pitch:
                on_pitch[on_pitch.index(event.player_off)] = event.player_on
            else:
                # Incohérence connue du moteur : le sortant est déjà absent (expulsé plus tôt,
                # voir docs/canvas_integration_state.md §2.8). L'entrant a pourtant joué
                # (PlayerMatchStat, minute_on) : on suit l'événement persisté, on ne le masque pas.
                on_pitch.append(event.player_on)
        elif event.player in on_pitch:
            on_pitch.remove(event.player)
    return [by_name[name] for name in on_pitch]
