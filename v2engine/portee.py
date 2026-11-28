"""Portée verticale des joueurs (ticket v2-hauteur-ballon/03a) : un joueur ne joue le ballon que s'il passe à une hauteur
accessible à son corps. Remplace, pour les contacts, le seuil unique de 0,5 m du ticket 02a1 (`hauteur.AERIAL_THRESHOLD_M`,
qui ne règle plus que le `mode` transmis à l'API).

`z` est la hauteur du **bas** du ballon (convention de `hauteur`), `height_m` la taille du joueur, `jump_m` sa détente.
Tranches des joueurs de champ (constantes validées par le propriétaire le 27/11/2026), proportions du corps de Drillis et
Contini (1966), reprises par D. A. Winter, *Biomechanics and Motor Control of Human Movement* :
- pied : bas du ballon sous la hanche (grand trochanter, 0,530 H) : ballon joué du pied, reprise de volée comprise ;
- corps : sous l'épaule (0,818 H) : contrôle de la poitrine ou de la cuisse ;
- tête : centre du ballon au plus au sommet du crâne en saut (`z + r ≤ H + détente`, r rayon du ballon).
Au-dessus, le ballon passe.

Détente selon Jumping Reach : linéaire de 0,35 m (note 1) à 0,75 m (note 99). Mesure directe non trouvée ; repères : saut
sans élan des footballeurs professionnels 0,35 à 0,45 m (Haugen et al. 2013), 0,71 m cité pour Ronaldo (presse, 2019).
Jumping Reach ne sert qu'ici, à la hauteur atteinte : le duel aérien (`v2-attributs-restants/01`) ne départage que les
joueurs éligibles, sans le relire (`docs/CARTE_ATTRIBUTS_V2.md`, règle anti double comptage).

Mains du gardien (ticket v2-hauteur-ballon/03b) : dans sa surface, le gardien joue le ballon bras levés, jusqu'à
`z + r ≤ 1,258 H + détente` (épaule 0,818 + bras 0,186 + avant-bras 0,146 + main 0,108, Winter) ; hors de sa surface, il
suit les tranches de champ (Lois du jeu, loi 12). Les tranches de champ (`field_band`, `field_ceiling_m`) ne lisent pas
le poste ; la tranche « mains » (`keeper_hands_ceiling`) n'est lue que par l'aiguillage `player_ceiling_m` /
`player_band`, le seul endroit où le poste et la surface comptent. Un seul modèle de portée pour les deux chemins où le
gardien joue le ballon : tir en vol (`match._keeper_reaches`) et ballon libre (`match._step_loose_ball`).
"""

from __future__ import annotations

import math

from v2engine.condition import effective_rating
from v2engine.geometry import in_penalty_area
from v2engine.hauteur import GRAVITY_M_S2, height_at

BALL_RADIUS_M = 0.11  # le même que `match.BALL_RADIUS_M` (test)

HIP_SHARE = 0.530  # hanche (grand trochanter) / taille, Winter
SHOULDER_SHARE = 0.818  # épaule / taille, Winter
# bras levé : épaule 0,818 + bras 0,186 + avant-bras 0,146 + main 0,108 (Winter), validé le 27/11/2026 (03a, 03b)
HANDS_SHARE = SHOULDER_SHARE + 0.186 + 0.146 + 0.108
JUMP_MIN_M = 0.35  # détente à Jumping Reach 1
JUMP_MAX_M = 0.75  # détente à Jumping Reach 99

PIED, CORPS, TETE, MAINS = "pied", "corps", "tête", "mains"

# Taille absente de la fiche (`Player.taille_fm`, 335 joueurs sur 7 473) : médiane du poste dans `data/joueurs.xlsx`
# (premier poste de la colonne « Poste », 27/11/2026) ; autre poste : médiane de la base (1,83 m).
NEUTRAL_HEIGHT_M = {"GK": 1.90, "DC": 1.88, "BU": 1.85, "MDC": 1.83, "MC": 1.80, "LB": 1.80, "RB": 1.80,
                    "AD": 1.78, "AG": 1.78, "MOC": 1.78, "SA": 1.77}
BASE_MEDIAN_HEIGHT_M = 1.83


def neutral_height_m(poste: str) -> float:
    """Taille de repli d'un joueur sans taille connue : médiane de son poste, sinon de la base."""
    return NEUTRAL_HEIGHT_M.get(poste, BASE_MEDIAN_HEIGHT_M)


def jump_m(jumping_reach: float) -> float:
    """Détente (m) pour une note de Jumping Reach (1 à 99, bornée)."""
    share = (min(99.0, max(1.0, jumping_reach)) - 1.0) / 98.0
    return JUMP_MIN_M + share * (JUMP_MAX_M - JUMP_MIN_M)


def field_ceiling_m(height_m: float, jump: float) -> float:
    """Plus haut bas de ballon qu'un joueur de champ touche : la tête en saut (`z + r ≤ H + détente`)."""
    return height_m + jump - BALL_RADIUS_M


def field_band(height_m: float, jump: float, z: float) -> str | None:
    """Tranche d'un joueur de champ qui touche un ballon dont le bas est à `z` : pied, corps, tête, ou `None` (il passe
    au-dessus)."""
    if z <= HIP_SHARE * height_m:
        return PIED
    if z <= SHOULDER_SHARE * height_m:
        return CORPS
    if z <= field_ceiling_m(height_m, jump):
        return TETE
    return None


def keeper_hands_ceiling(height_m: float, jump: float) -> float:
    """Plus haut bas de ballon que le gardien capte dans sa surface, bras levés en saut (`z + r ≤ 1,258 H + détente`)."""
    return HANDS_SHARE * height_m + jump - BALL_RADIUS_M


def keeper_band(height_m: float, jump: float, z: float) -> str | None:
    """Tranche du gardien dans sa surface : pied sous la hanche (comme un joueur de champ), mains au-dessus jusqu'à
    `keeper_hands_ceiling`, sinon `None` (le ballon passe au-dessus de ses mains)."""
    if z <= HIP_SHARE * height_m:
        return PIED
    if z <= keeper_hands_ceiling(height_m, jump):
        return MAINS
    return None


NEUTRAL_JUMPING_REACH = 60  # note par défaut de `attributes.player_attribute` (égalité gardée par un test)


def neutral_keeper_ceiling_m() -> float:
    """Plafond des mains d'un gardien neutre dans sa surface (taille médiane du poste, Jumping Reach neutre) : repli de
    l'estimateur de tir sans gardien identifiable (`shooting._goal_angles`, gardien placé dans sa surface)."""
    return keeper_hands_ceiling(neutral_height_m("GK"), jump_m(NEUTRAL_JUMPING_REACH))


def uses_hands(player) -> bool:
    """Aiguillage du ticket 03b : gardien dans sa propre surface (celle que l'adversaire attaque)."""
    return player.poste == "GK" and in_penalty_area("away" if player.team == "home" else "home", player.position)


def player_jump_m(player) -> float:
    """Détente du joueur, par sa note exprimée de Jumping Reach (façade `effective_rating`)."""
    return jump_m(effective_rating(player, "Jumping Reach"))


def player_height_m(player) -> float:
    """Taille du joueur : celle de sa fiche, sinon la médiane de son poste."""
    return player.height_m if player.height_m is not None else neutral_height_m(player.poste)


def player_ceiling_m(player) -> float:
    """Plafond de jeu du joueur à sa taille et à sa détente : mains du gardien dans sa surface (`keeper_hands_ceiling`),
    sinon tête en saut (`field_ceiling_m`). Seul aiguillage entre les deux (03b)."""
    if uses_hands(player):
        return keeper_hands_ceiling(player_height_m(player), player_jump_m(player))
    return field_ceiling_m(player_height_m(player), player_jump_m(player))


def player_body_ceiling_m(player) -> float:
    """Plus haut bas de ballon que le joueur contrôle du corps (poitrine, sous l'épaule : 0,818 × taille), ticket
    v2-realisme/15a1 : là où le receveur que personne ne conteste va chercher un ballon aérien (décision du propriétaire du
    27/11/2026). Gardien dans sa surface : ses mains (`player_ceiling_m`, même aiguillage)."""
    if uses_hands(player):
        return player_ceiling_m(player)
    return SHOULDER_SHARE * player_height_m(player)


def player_band(player, z: float) -> str | None:
    """Tranche touchée par le joueur, même aiguillage que `player_ceiling_m` (`keeper_band` ou `field_band`)."""
    if uses_hands(player):
        return keeper_band(player_height_m(player), player_jump_m(player), z)
    return field_band(player_height_m(player), player_jump_m(player), z)


def first_reachable_s(z0: float, vz0: float, ceiling: float, t_in: float, t_out: float) -> float | None:
    """Premier instant de [`t_in`, `t_out`] (depuis le début du pas, ballon en `z0`, `vz0`, chute libre) où le bas du
    ballon est sous `ceiling`, ou `None`. Une parabole est concave : elle est au-dessus du plafond entre ses deux
    racines `t1 < t2` et dessous ailleurs ; au-dessus en `t_in`, elle repasse dessous en `t2`. Un ballon qui touche le
    sol pendant le pas est passé sous le plafond avant (plafond positif) : la chute libre suffit jusqu'à `t2`."""
    if height_at(z0, vz0, t_in)[0] <= ceiling:
        return t_in
    disc = vz0 * vz0 - 2.0 * GRAVITY_M_S2 * (ceiling - z0)
    if disc < 0.0:
        return None
    t_down = (vz0 + math.sqrt(disc)) / GRAVITY_M_S2
    return t_down if t_in <= t_down <= t_out else None


__all__ = ["CORPS", "MAINS", "PIED", "TETE", "field_band", "field_ceiling_m", "first_reachable_s", "jump_m",
           "keeper_band", "keeper_hands_ceiling", "neutral_height_m", "neutral_keeper_ceiling_m", "player_band", "player_body_ceiling_m", "player_ceiling_m", "player_height_m",
           "player_jump_m", "uses_hands"]
