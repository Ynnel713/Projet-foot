"""Pont entre la `Timeline` (occasions narratives, `engine.narrative`) et le
canvas (frames) -- brief "canvas player" (23/09/2026), Tâche 3.

Débloqué par l'extension explicite de `NarrativeEvent`/`Timeline` décidée
par Olivier le 23/09/2026 (voir `engine/narrative.py` : `NarrativeEvent.zone`
dérivée du gabarit, `Timeline.home_lineup`/`.away_lineup`) -- sans elle,
aucune `Sequence` n'aurait pu être construite ici : `Timeline` ne portait ni
`Lineup`, ni position de départ pour les occasions génériques (voir
`docs/next_step_canvas.md`, section déjà existante sur ce manque).

Consommateur PUR du pipeline existant : `templates.BUILDERS`/
`animation.motion.interpolate` restent INCHANGÉS, ce module ne fait
qu'assembler leurs entrées (`GoalEvent`-équivalent, `Lineup`,
`start_positions`) à partir d'une `Timeline` déjà construite, exactement
comme `animation.sequence_generator.generate_sequence` le fait pour un vrai
but -- sauf que le gabarit est ICI déjà décidé (`NarrativeEvent.gabarit`),
`pick_template` n'est JAMAIS rappelé.

Limite connue, non corrigée ici (voir retour de tâche) : `Timeline.home_lineup`/
`.away_lineup` ne portent que le ONZE DE DÉPART (décision explicite du
23/09/2026, pas `home_squad`/`away_squad`) -- un `NarrativeEvent.main_player`
qui serait un remplaçant entré en jeu (minute >= 46 uniquement, voir
`events.SUB_MIN_MINUTE`) ne s'y résout pas. `_build_clip_frames` retombe
alors sur `frames=[]` plutôt que de lever (voir `_resolve_start_positions`),
un cas qui reste à couvrir par un futur ajout de `home_squad`/`away_squad`
à la `Timeline` si la fréquence réelle le justifie."""

from __future__ import annotations

import json
from dataclasses import dataclass

from ligue1sim.animation.motion import FrameState, interpolate
from ligue1sim.animation.sequence_generator import enrich_with_background
from ligue1sim.animation.serialize import frame_sequence_to_json
from ligue1sim.animation.spatial import placed_player_to_normalized
from ligue1sim.animation.templates import BUILDERS, TEMPLATES, player_id_of
from ligue1sim.animation.types import PlayerId, RosterEntry
from ligue1sim.events import GoalEvent, PlayerMatchStat
from ligue1sim.kits import match_kit_colors
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PitchPoint, zone_of
from ligue1sim.pitch_layout import place_starting_xi

from narrative import BUT, NarrativeEvent, Timeline

_FPS = 30


@dataclass(frozen=True)
class Clip:
    """Un clip du lecteur -- une occasion (`NarrativeEvent`) mise en scène.

    `frames` n'est JAMAIS vide pour un `Clip` retourné par `build_clips` --
    un événement dont les frames ne peuvent pas être construites (voir
    `_build_clip_frames`) est OMIS du résultat, pas exposé avec `frames=[]`.

    `roster` : ajouté au-delà de la liste exacte de la Tâche 3.2 -- pas une
    dérive de périmètre, une nécessité déjà anticipée par la Tâche 4 (JSON
    canvas, voir `clips_to_json`) : `FrameState`/`PlayerMotionState` ne
    portent ni équipe, ni numéro, ni rôle actif/figurant (voir docstring de
    `animation.serialize`), ce couple `(frames, roster)` EST exactement le
    contrat de `Sequence` (`keyframes`+`roster`), minimal pour sérialiser un
    clip sans revenir chercher la `Sequence` d'origine.

    `interval_events` : liste vide pour l'instant -- `Timeline` ne porte pas
    les cartons/remplacements réels (`MatchEvents.cards`/`.substitutions`),
    hors du périmètre des DEUX extensions autorisées le 23/09/2026 (voir
    `engine/narrative.py`). Escaladé, pas inventé (voir retour de tâche) :
    un futur ajout de `Timeline.cards`/`.substitutions` serait nécessaire
    pour peupler ce champ."""

    minute: int
    gabarit: str
    declinaison: str
    equipe: str
    issue: str
    main_player: str
    score_before: tuple[int, int]
    score_after: tuple[int, int]
    interval_events: tuple[str, ...]
    frames: list[FrameState]
    roster: dict[PlayerId, RosterEntry]
    duration_s: float


def _lineup_start_positions(lineup: Lineup) -> dict[PlayerId, PitchPoint]:
    """`Lineup.players` (`Player`) -> positions de formation normalisées,
    même principe que `animation.sequence_generator._start_positions`/
    `_opponent_positions` (fonctions privées à ce module-là, donc non
    réutilisables directement) -- la logique de FOND (placement ligne par
    ligne, conversion de référentiel) reste entièrement dans
    `pitch_layout.place_starting_xi`/`animation.spatial.placed_player_to_normalized`,
    réutilisées telles quelles ici, pas dupliquées."""
    stats = [
        PlayerMatchStat(player_name=p.name, club_name=lineup.club_name, poste=p.poste, started=True)
        for p in lineup.players
    ]
    placed = place_starting_xi(stats, attacking_up=True)
    players_by_name = {p.name: p for p in lineup.players}
    positions: dict[PlayerId, PitchPoint] = {}
    for placed_player in placed:
        player = players_by_name.get(placed_player.stat.player_name)
        if player is None:
            continue  # meme repli que sequence_generator : compo desynchronisee, ignore
        positions[player_id_of(player)] = placed_player_to_normalized(placed_player, attacking_up=True)
    return positions


def _assist_name(event: NarrativeEvent) -> str | None:
    """Second nom réel de `involved_players`, résolu vers le rôle "assist"
    UNIQUEMENT si ce gabarit en a un (voir `_resolve_roles` dans
    `templates.py`) -- pour un gabarit sans rôle "assist" (ex.
    `recuperation_haute`), ce second nom n'est de toute façon jamais
    consommé par `build_from_template` (comportement déjà documenté,
    `docs/narrative_timeline_schema.md`, "Mapping vers canvas")."""
    role_names = {role.name for role in TEMPLATES[event.gabarit].roles}
    if "assist" not in role_names or len(event.involved_players) < 2:
        return None
    return event.involved_players[1]


def _build_clip_frames(
    timeline: Timeline, event: NarrativeEvent
) -> tuple[list[FrameState], dict[PlayerId, RosterEntry]]:
    scorer_lineup = timeline.home_lineup if event.team == timeline.home_team else timeline.away_lineup
    opponent_lineup = timeline.away_lineup if event.team == timeline.home_team else timeline.home_lineup

    scorer_names = {p.name for p in scorer_lineup.players}
    assist = _assist_name(event)
    if event.main_player not in scorer_names or (assist is not None and assist not in scorer_names):
        # Voir docstring de module -- remplacant (scorer OU assist) non
        # resolu par le onze de depart, cas connu, non invente.
        return [], {}

    goal_event = GoalEvent(
        club_name=event.team,
        scorer=event.main_player,
        assist=assist,
        minute=event.minute,
        penalty=(event.gabarit == "penalty"),
        zone=zone_of(*event.zone),
        assist_zone=None,  # voir _assist_name -- fallback sur event.zone dans build_from_template (ANCHOR_ASSIST)
    )
    start_positions = _lineup_start_positions(scorer_lineup)
    sequence = BUILDERS[event.gabarit](goal_event, scorer_lineup, start_positions)
    sequence = enrich_with_background(sequence, opponent_lineup)

    step = 1.0 / _FPS
    frames: list[FrameState] = []
    t = 0.0
    while t <= sequence.duration + 1e-9:
        frames.append(interpolate(sequence, t))
        t += step
    return frames, sequence.roster


def build_clips(timeline: Timeline, max_occasions: int | None = None) -> list[Clip]:
    """Construit les clips du lecteur, dans l'ordre chronologique de
    `timeline.events`, jusqu'à en retenir `max_occasions` (`None` = tous les
    événements construisibles).

    Un événement dont le protagoniste (`main_player`/assist) n'est pas dans
    le onze de départ (voir `_build_clip_frames` -- remplaçant, limite
    connue du 23/09/2026) est OMIS du résultat plutôt que d'y figurer avec
    `frames=[]` : mesuré empiriquement sur 200 matchs simulés (script de
    calibration ponctuel, non conservé), ~36% des occasions retombent sur un
    protagoniste hors onze de départ (la sélection du protagoniste d'une
    occasion, `narrative._pick_main_player`, pioche dans TOUT l'effectif qui
    a joué, sans tenir compte de la minute d'entrée réelle d'un remplaçant --
    limite pré-existante de `engine/narrative.py`, hors du périmètre
    autorisé ici, voir retour de tâche). Omettre plutôt qu'exposer des
    frames vides garantit qu'un clip retenu est TOUJOURS jouable, au prix de
    puiser plus loin dans `timeline.events` que les seuls `max_occasions`
    premiers pour en trouver `max_occasions` construisibles -- le score
    progressif (`score_before`/`score_after`) reste néanmoins calculé sur
    TOUS les événements traversés, omis ou non, pour rester cohérent avec ce
    qui précède chaque clip retenu."""
    home_score = away_score = 0
    clips: list[Clip] = []
    for event in timeline.events:
        score_before = (home_score, away_score)
        if event.event_type == BUT:
            if event.team == timeline.home_team:
                home_score += 1
            else:
                away_score += 1
        score_after = (home_score, away_score)

        frames, roster = _build_clip_frames(timeline, event)
        if not frames:
            continue

        clips.append(Clip(
            minute=event.minute,
            gabarit=event.gabarit,
            declinaison=event.declinaison,
            equipe=event.team,
            issue=event.outcome,
            main_player=event.main_player,
            score_before=score_before,
            score_after=score_after,
            interval_events=(),  # voir docstring de Clip
            frames=frames,
            roster=roster,
            duration_s=TEMPLATES[event.gabarit].duration,
        ))
        if max_occasions is not None and len(clips) >= max_occasions:
            break

    return clips


def clips_to_json(clips: list[Clip], timeline: Timeline) -> str:
    """Sérialise `clips` en JSON ARRAY pour `render/canvas.html` (Tâche 4) --
    un objet par clip, chacun de la MÊME forme qu'un JSON de gabarit isolé
    (`duration`/`fps_target`/`metadata`/`frames`, voir
    `docs/canvas_json_schema.md`), avec les champs narratifs du clip
    (`minute`, `declinaison`, `equipe`, `issue`, `main_player`,
    `score_before`, `score_after`, `interval_events`) ajoutés sous
    `metadata`. Réutilise `animation.serialize.frame_sequence_to_json` pour
    toute la partie frames/roster/couleurs -- pas de duplication de cette
    logique ; `json.loads` puis ré-`json.dumps` pour l'emboîter dans le
    tableau final, coût négligeable à cette échelle (quelques clips)."""
    payload = []
    for clip in clips:
        opponent_team = timeline.away_team if clip.equipe == timeline.home_team else timeline.home_team
        (scorer_fill, scorer_outline), (opp_fill, opp_outline) = match_kit_colors(clip.equipe, opponent_team)
        roster_meta = {
            str(player_id): {"team": entry.team_side, "numero": entry.numero, "active": entry.role is not None}
            for player_id, entry in clip.roster.items()
        }
        sequence_json = frame_sequence_to_json(
            clip.frames,
            {
                "duration": clip.duration_s,
                "fps_target": _FPS,
                "template": clip.gabarit,
                "teams": {
                    "scorer": {"name": clip.equipe, "color_fill": scorer_fill, "color_outline": scorer_outline},
                    "opponent": {"name": opponent_team, "color_fill": opp_fill, "color_outline": opp_outline},
                },
                "roster": roster_meta,
            },
        )
        clip_payload = json.loads(sequence_json)
        clip_payload["metadata"].update({
            "minute": clip.minute,
            "declinaison": clip.declinaison,
            "equipe": clip.equipe,
            "issue": clip.issue,
            "main_player": clip.main_player,
            "score_before": list(clip.score_before),
            "score_after": list(clip.score_after),
            "interval_events": list(clip.interval_events),
            # home_team/away_team (redondants sur chaque clip, pas juste sur
            # "scorer"/"opponent" qui changent d'un clip a l'autre selon
            # quelle equipe est a la manoeuvre) -- necessaires au JS pour
            # l'affichage du score en Tache 4 ("Marseille 1 - 0 PSG"),
            # toujours dans le MEME ordre domicile/exterieur quel que soit
            # le clip courant.
            "home_team": timeline.home_team,
            "away_team": timeline.away_team,
        })
        payload.append(clip_payload)
    return json.dumps(payload, sort_keys=True)
