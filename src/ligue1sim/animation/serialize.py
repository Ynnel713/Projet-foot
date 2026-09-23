"""Sérialisation JSON d'une séquence de `FrameState` pour le rendu canvas
(brief "canvas vertical slice", 23/09/2026, Tâche 2) -- voir
`docs/canvas_json_schema.md` pour le format exact produit.

Nouveau module plutôt qu'un ajout à `motion.py`/`types.py` : la
sérialisation est un souci de RENDU (JS/canvas), pas du moteur d'animation
lui-même -- même logique de séparation que `animation.ball` vs
`animation.motion` (chacun un point d'entrée indépendant et testable seul).

`frame_sequence_to_json` ne reçoit jamais la `Sequence` d'origine, seulement
`list[FrameState]` -- `FrameState`/`PlayerMotionState` ne portent pas
`team_side`/`numero`/`role` (ces champs vivent sur `Sequence.roster`, statique
pour toute la séquence, voir `animation/types.py`). L'appelant doit donc
fournir cette jointure toute faite via `metadata["roster"]` : c'est un choix
délibéré pour garder ce module indépendant de `Sequence`, pas un oubli."""

from __future__ import annotations

import json

from ligue1sim.animation.motion import FrameState


def frame_sequence_to_json(frames: list[FrameState], metadata: dict) -> str:
    """Sérialise `frames` (voir `animation.motion.interpolate`, une entrée
    par instant échantillonné) en une chaîne JSON conforme à
    `docs/canvas_json_schema.md`.

    `metadata` attendu (clés consommées par cette fonction, aucune autre
    exigée) ::

        {
            "duration": float,       # -> racine.duration
            "fps_target": int,       # -> racine.fps_target
            "template": str,         # -> racine.metadata.template
            "teams": {               # -> racine.metadata.teams, transmis tel quel
                "scorer": {"name": str, "color_fill": str, "color_outline": str},
                "opponent": {"name": str, "color_fill": str, "color_outline": str},
            },
            "roster": {               # PAS copié dans la sortie -- consommé pour enrichir players[]
                "<player_id>": {"team": "scorer" | "opponent", "numero": int, "active": bool},
            },
        }

    `roster` doit porter une entrée pour CHAQUE `player_id` présent dans
    `frames[i].players` (clés converties en `str`, même convention que
    `Sequence.to_json()`) -- un joueur sans entrée est un bug de l'appelant
    (jointure `Sequence.roster` incomplète), jamais un repli silencieux :
    lève `ValueError`.

    Déterminisme : `json.dumps(..., sort_keys=True)` -- deux appels avec les
    mêmes `frames`/`metadata` produisent TOUJOURS la même chaîne (ordre des
    clés stable), voir `tests/test_serialize.py::test_determinism`."""
    roster = metadata["roster"]

    payload = {
        "duration": metadata["duration"],
        "fps_target": metadata["fps_target"],
        "metadata": {
            "template": metadata["template"],
            "teams": metadata["teams"],
        },
        "frames": [_frame_to_dict(frame, roster) for frame in frames],
    }
    return json.dumps(payload, sort_keys=True)


def _frame_to_dict(frame: FrameState, roster: dict) -> dict:
    if frame.ball is None:
        raise ValueError(f"FrameState.ball est None (t={frame.t}) -- attendu peuplé par animation.motion.interpolate")

    players = []
    for player_id, state in frame.players.items():
        key = str(player_id)
        if key not in roster:
            raise ValueError(f"metadata['roster'] ne porte aucune entrée pour le joueur {key!r} (t={frame.t})")
        entry = roster[key]
        players.append({
            "id": key,
            "x": state.x,
            "y": state.y,
            "team": entry["team"],
            "numero": entry["numero"],
            "active": entry["active"],
        })

    return {
        "t": frame.t,
        "players": players,
        "ball": {
            "x": frame.ball.x,
            "y": frame.ball.y,
            "z": frame.ball.z,
            "spin": frame.ball.spin,
        },
    }
