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

Ce module ne connaît pas le gardien : la tranche « mains » (gardien dans sa surface) est au ticket 03b, isolée des
tranches de champ ; jusque-là le gardien suit les tranches de champ sur le ballon libre.
"""

from __future__ import annotations

import math

from v2engine.condition import effective_rating
from v2engine.hauteur import GRAVITY_M_S2, height_at

BALL_RADIUS_M = 0.11  # le même que `match.BALL_RADIUS_M` (test)

HIP_SHARE = 0.530  # hanche (grand trochanter) / taille, Winter
SHOULDER_SHARE = 0.818  # épaule / taille, Winter
JUMP_MIN_M = 0.35  # détente à Jumping Reach 1
JUMP_MAX_M = 0.75  # détente à Jumping Reach 99

PIED, CORPS, TETE = "pied", "corps", "tête"

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


def player_jump_m(player) -> float:
    """Détente du joueur, par sa note exprimée de Jumping Reach (façade `effective_rating`)."""
    return jump_m(effective_rating(player, "Jumping Reach"))


def player_height_m(player) -> float:
    """Taille du joueur : celle de sa fiche, sinon la médiane de son poste."""
    return player.height_m if player.height_m is not None else neutral_height_m(player.poste)


def player_ceiling_m(player) -> float:
    """Plafond de jeu d'un joueur de champ (`field_ceiling_m` à sa taille et à sa détente)."""
    return field_ceiling_m(player_height_m(player), player_jump_m(player))


def player_band(player, z: float) -> str | None:
    """`field_band` à la taille et à la détente du joueur."""
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


__all__ = ["CORPS", "PIED", "TETE", "field_band", "field_ceiling_m", "first_reachable_s", "jump_m", "neutral_height_m",
           "player_band", "player_ceiling_m", "player_height_m", "player_jump_m"]
