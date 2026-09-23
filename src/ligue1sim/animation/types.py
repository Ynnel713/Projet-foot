"""L'objet PIVOT entre le moteur (positions/mouvements calculés côté
Python) et le rendu (JS/canvas embarqué dans Streamlit, voir
animation.render.component) -- une `Sequence` EST le contrat stable que les
deux côtés doivent respecter : un empilement de `Keyframe` (un instant
complet du jeu -- ballon + position de chaque joueur), sérialisable tel
quel en JSON via `Sequence.to_json()`.

Délibérément indépendant du reste du pipeline (spatial.py/templates.py/
events.py) : ce module ne connaît rien du moteur ni du rendu, seulement la
forme du contrat qui les relie -- testable à 100% en Python pur, sans
Streamlit ni fichier Excel (voir tests/test_types.py). La construction
réelle d'une Sequence se fait dans `templates.py` (chaque gabarit construit
directement une `Sequence`, voir `templates.build_from_template`) puis
`sequence_generator.py` (choix du gabarit + calage sur le résultat connu).

Module renommé le 22/09/2026 (`sequences.py` -> `types.py`, à la demande
d'Olivier, pour que le nom du fichier ne laisse plus penser qu'il construit
des séquences -- il ne fait que définir leur FORME).

Voir docs/simulation_physique_archi.md pour la place de ce contrat dans le
pipeline complet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Identifiant d'un joueur : Player.id (int) si connu, sinon son nom (même
# repli que events._player_seed_id côté moteur) -- jamais None, contrairement
# à BallState.owner_id qui peut légitimement n'appartenir à personne.
PlayerId = int | str


@dataclass(frozen=True)
class BallState:
    """État du ballon à un instant donné, référentiel normalisé (voir
    ligue1sim.pitch_geometry -- x, y ∈ [0, 1]).

    `vx`/`vy` : vitesse normalisée par seconde, même convention que
    `motion.PlayerMotionState.vx`/`vy`. `vz` : vitesse verticale en m/s --
    `z` est en MÈTRES (voir plus bas), pas normalisé comme x/y, donc `vz`
    ne l'est pas non plus : un `BallState` mélange délibérément deux
    échelles (position latérale normalisée, hauteur réelle), au lieu de
    forcer une fausse cohérence entre deux grandeurs qui n'ont pas la même
    nature. `vx`/`vy`/`vz` par défaut à 0.0 (élargi le 23/09/2026, phase 3.2
    -- ancien contrat `(x, y, z, spin, owner_id)` préservé, tout code qui
    construisait un `BallState` sans ces 3 champs continue de fonctionner
    à l'identique, vitesse nulle)."""

    x: float
    y: float
    z: float  # hauteur au-dessus du sol en MÈTRES, 0.0 = au sol -- voir animation.ball pour le calcul (Keyframe.ball.z, lui, reste sur l'échelle héritée non calibrée de Template.ball_height, voir sa docstring)
    spin: float  # rotation du ballon, radians/seconde (convention fixée le 23/09/2026 -- toujours non consommée par le rendu actuel, mais l'ambiguïté d'unité est levée)
    owner_id: PlayerId | None  # joueur qui a le ballon à cet instant, None si en l'air/disputé
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0


@dataclass(frozen=True)
class Keyframe:
    """Un instant complet et autonome du jeu : le ballon ET tous les
    joueurs suivis, au même instant `t`. Un rendu peut interpoler entre
    deux Keyframe consécutifs sans avoir besoin d'aucune autre donnée.

    `tag` et `physics_tag` sont DEUX champs distincts, jamais l'un pour
    l'autre (23/09/2026, phase 3.2) : `tag` est narratif (ex.
    "recuperation", "tir", "centre"...), pour le débogage/l'UI, jamais
    interprété par le rendu -- 24 valeurs différentes sur les 12 gabarits
    actuels, aucun rapport avec la physique du ballon. `physics_tag` est LU
    par `animation.ball.ball_state_at` pour choisir le comportement du
    segment qui DÉMARRE à ce Keyframe (`"pass_ground"`/`"pass_lob"`/
    `"shot"`/`"cross"`/`"deflect"`, ou `None` -- dans ce cas `ball_state_at`
    infère un comportement par défaut, voir sa docstring)."""

    t: float  # secondes depuis le début de la Sequence
    ball: BallState
    players: dict[PlayerId, tuple[float, float]]  # position (x, y) normalisée de chaque joueur suivi à cet instant
    tag: str  # étiquette NARRATIVE libre (ex. "recuperation", "tir"...) -- pour le débogage/l'UI, jamais interprétée par le rendu ; voir physics_tag pour ce qui pilote réellement le ballon
    physics_tag: str | None = None  # comportement de trajectoire du segment qui démarre ici, voir animation.ball -- None = inféré


@dataclass(frozen=True)
class RosterEntry:
    """Identité et rôle d'un joueur suivi par une `Sequence` (voir
    `Sequence.roster`) -- ce qu'un consommateur (interpolate, à terme le
    rendu JS/canvas) lit pour connaître le poste et le rôle d'un joueur
    SANS avoir besoin de la `Lineup` d'origine : la `Sequence` doit être
    auto-descriptive, c'est le seul contrat que ses consommateurs
    connaissent (voir docstring de `Sequence`)."""

    nom: str
    poste: str
    role: str | None  # nom du rôle du gabarit ("scorer", "assist", "support1"...) ; None si le joueur est suivi mais n'a pas de rôle mis en scène par le gabarit
    numero: int  # 1-11, DÉRIVÉ de la compo (poste + nom, voir templates.numeros_by_player_id) -- Player n'a pas de vrai numéro de maillot, voir docstring de ce champ dans la fonction qui le calcule
    team_side: str  # "scorer" (l'équipe qui marque, seule suivie avant le Point 1 du bilan du 23/09/2026) ou "opponent" (voir sequence_generator.enrich_with_background) -- jamais "home"/"away", inconnu à ce niveau du pipeline


@dataclass(frozen=True)
class BackgroundTrack:
    """Trajectoire continue (PAS des keyframes) d'un joueur "décor" -- suivi
    par la `Sequence` (voir `Sequence.background`) mais jamais mis en scène
    par un gabarit : pas de Bézier/keyframes, juste un micro-mouvement
    déterministe de `start` vers `start + drift`, parcouru avec la même
    courbe ease-in-out que les joueurs actifs (voir `motion._ease_progress`)
    -- aucune vitesse à plafonner par poste, l'amplitude de `drift` est déjà
    bornée à la construction (voir `sequence_generator.enrich_with_background`,
    Point 1 du bilan simulation physique du 23/09/2026)."""

    start: tuple[float, float]  # position de formation, référentiel normalisé
    drift: tuple[float, float]  # déplacement (dx, dy) atteint à t=duration, ajouté à start


@dataclass(frozen=True)
class Sequence:
    """LE contrat stable entre le moteur et le rendu (voir docstring de
    module). `event_ref` référence l'événement source (voir ligue1sim.events)
    par une chaîne stable plutôt que l'objet event lui-même -- garde ce
    module indépendant des dataclasses du moteur, et rend `to_json()`
    trivialement sérialisable sans transformation ad hoc.

    `roster` porte, pour chaque `PlayerId` suivi (keyframes OU background),
    son nom/poste/rôle/numéro/équipe (voir `RosterEntry`) -- rempli par
    `templates.build_from_template` pour l'équipe qui marque, complété par
    `sequence_generator.enrich_with_background` pour l'adversaire. Une
    `Sequence` est ainsi auto-descriptive : un consommateur
    (`motion.interpolate`, à terme le rendu) n'a jamais besoin de recevoir
    une `Lineup` en plus de la `Sequence` elle-même.

    `background` porte, pour chaque joueur "décor" (jamais mis en scène par
    un gabarit -- le reste de l'équipe qui marque + les 11 adverses), sa
    `BackgroundTrack` -- voir `enrich_with_background`. Vide par défaut :
    une `Sequence` fraîchement sortie d'un gabarit n'a que ses 2-4 joueurs
    actifs en keyframes, `background` n'est rempli qu'après enrichissement.

    Invariants vérifiés À LA CONSTRUCTION (voir `__post_init__`), pas
    seulement documentés -- une Sequence mal formée ne peut pas exister :
    1. `keyframes` est trié par `t` croissant ou constant (jamais
       décroissant) -- un rendu qui interpole entre deux keyframes
       consécutifs dépend de cet ordre.
    2. Tous les `Keyframe.players` de la séquence suivent EXACTEMENT le
       même ensemble de joueurs -- un joueur ne doit jamais apparaître ou
       disparaître sans explication au milieu d'une séquence de quelques
       secondes (contrairement à un match entier, où un remplacement change
       légitimement l'effectif suivi).
    3. Un joueur suivi par les keyframes ne peut PAS aussi être dans
       `background`, et inversement -- un seul mode de suivi par joueur,
       jamais les deux (ambiguïté sinon sur la position "vraie").
    4. `roster` porte une entrée pour CHAQUE joueur suivi, keyframes ET
       background confondus -- un joueur référencé sans poste/rôle/numéro
       connu est un bug de génération (compo mal transmise), pas un cas à
       tolérer avec un repli silencieux sur un joueur générique."""

    event_ref: str
    keyframes: list[Keyframe]
    duration: float
    meta: dict[str, Any]
    roster: dict[PlayerId, RosterEntry]
    background: dict[PlayerId, BackgroundTrack] = field(default_factory=dict)

    def __post_init__(self) -> None:
        timestamps = [kf.t for kf in self.keyframes]
        if timestamps != sorted(timestamps):
            raise ValueError(f"Sequence.keyframes doit être trié par t croissant ou constant, reçu {timestamps!r}")

        reference_ids: set[PlayerId] = set(self.keyframes[0].players) if self.keyframes else set()
        for kf in self.keyframes:
            if set(kf.players) != reference_ids:
                raise ValueError(
                    "Tous les Keyframe d'une Sequence doivent suivre le même ensemble de joueurs "
                    f"(attendu {sorted(map(str, reference_ids))}, trouvé {sorted(map(str, kf.players))} à t={kf.t})"
                )

        background_ids = set(self.background)
        overlap = reference_ids & background_ids
        if overlap:
            raise ValueError(
                "Un joueur ne peut pas être suivi à la fois par des keyframes et par background "
                f"-- présent dans les deux : {sorted(map(str, overlap))}"
            )

        missing_from_roster = (reference_ids | background_ids) - set(self.roster)
        if missing_from_roster:
            raise ValueError(
                "Sequence.roster doit porter une entrée (nom/poste/rôle/numéro/équipe) pour chaque joueur "
                f"suivi (keyframes ou background) -- entrée manquante pour {sorted(map(str, missing_from_roster))}"
            )

    def to_json(self) -> dict[str, Any]:
        """Représentation JSON-safe et STABLE de la séquence -- le seul
        contrat que le rendu (JS/canvas) doit consommer, jamais les
        dataclasses Python elles-mêmes (voir invariant 5,
        docs/simulation_physique_archi.md). Uniquement des types natifs
        JSON (str/int/float/bool/None/list/dict), aucun tuple ni objet
        Python brut -- vérifié par un aller-retour json.dumps/json.loads
        dans les tests (voir tests/test_types.py).

        Les identifiants de joueur (`PlayerId` = int | str côté Python)
        sont toujours convertis en chaîne : une clé d'objet JSON est
        nécessairement une chaîne, la conversion est rendue explicite ici
        plutôt que laissée à la coercition implicite (et déroutante) d'un
        encodeur JSON standard sur des clés entières.

        Structure produite (stable, ne change pas d'un appel à l'autre pour
        une même Sequence)::

            {
                "event_ref": str,
                "duration": float,
                "meta": {...},
                "roster": {
                    "<player_id>": {
                        "nom": str, "poste": str, "role": str | None, "numero": int, "team_side": str,
                    },
                    ...
                },
                "background": {"<player_id>": {"start": [x, y], "drift": [dx, dy]}, ...},
                "keyframes": [
                    {
                        "t": float,
                        "tag": str,
                        "physics_tag": str | None,
                        "ball": {
                            "x": float, "y": float, "z": float,
                            "vx": float, "vy": float, "vz": float,
                            "spin": float, "owner_id": str | None,
                        },
                        "players": {"<player_id>": [x, y], ...},
                    },
                    ...
                ],
            }
        """
        return {
            "event_ref": self.event_ref,
            "duration": self.duration,
            "meta": self.meta,
            "roster": {
                str(player_id): {
                    "nom": entry.nom,
                    "poste": entry.poste,
                    "role": entry.role,
                    "numero": entry.numero,
                    "team_side": entry.team_side,
                }
                for player_id, entry in self.roster.items()
            },
            "background": {
                str(player_id): {"start": list(track.start), "drift": list(track.drift)}
                for player_id, track in self.background.items()
            },
            "keyframes": [
                {
                    "t": kf.t,
                    "tag": kf.tag,
                    "physics_tag": kf.physics_tag,
                    "ball": {
                        "x": kf.ball.x,
                        "y": kf.ball.y,
                        "z": kf.ball.z,
                        "vx": kf.ball.vx,
                        "vy": kf.ball.vy,
                        "vz": kf.ball.vz,
                        "spin": kf.ball.spin,
                        "owner_id": None if kf.ball.owner_id is None else str(kf.ball.owner_id),
                    },
                    "players": {str(player_id): [x, y] for player_id, (x, y) in kf.players.items()},
                }
                for kf in self.keyframes
            ],
        }
