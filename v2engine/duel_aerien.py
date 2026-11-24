"""Duel aérien loyal et retombée (ticket v2-realisme/15b1) : quand le ballon arrive à la tête d'un joueur et qu'un
adversaire tout proche peut aussi l'atteindre, les deux se disputent le ballon. Chacun a une hauteur effective : sa
taille plus sa détente (Jumping Reach, `atteinte.jump_m`, entière avec élan, réduite sans), plus ou moins son placement
au contact (Strength, part du contact du ticket 11b, `duel.contact_share`). Le gagnant est tiré sur une courbe en S de
l'écart des hauteurs effectives, jamais sûr. Fautes du duel : ticket 15b2 (plus bas) ; jeu dangereux : ticket 15b3.

Constantes validées par le propriétaire le 24/11/2026 (« oui je valide ») :
- `DUEL_RADIUS_M` : un adversaire à moins de 1,0 m (centre à centre) du joueur que le ballon atteint ;
- `RUN_UP_MPS`, `STANDING_JUMP_SHARE` : détente entière avec élan (3 m/s ou plus), 85 % sans (non trouvé : ordre de
  grandeur) ;
- `PLACEMENT_M` : placement au contact, de - 6 cm (part du contact 0,25) à + 6 cm (0,75), linéaire ;
- `DUEL_SCALE_M`, `DUEL_MIN`, `DUEL_MAX` : courbe en S d'échelle 0,18 m, bornée de 10 à 90 % ; repères : 1,95 m
  contre 1,70 m, autres notes égales, 80 % ; 10 cm d'écart, 64 % ; 1,70 m (Jumping Reach 99) contre 1,95 m (50), 36 % ;
- `LANDING_S` : un joueur qui a sauté (ballon au-dessus de sa taille) ne peut pas agir pendant 0,2 s (non trouvé).
Chiffres réels : StatsBomb (HOPS) : la taille explique 22 % de la variation de la capacité aérienne ; avantage chiffré
en pourcentage de duels gagnés : non trouvé.

Pas de double comptage (`docs/CARTE_ATTRIBUTS_V2.md`) : la hauteur atteinte est celle de l'atteinte (ticket
v2-hauteur-ballon/03a), sans bonus ; Strength n'entre que par la part du contact du 11b ; Balance joue après le contact
(12c, dans `match`)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from v2engine.atteinte import jump_m, reach_m, uses_hands
from v2engine.condition import effective_rating
from v2engine.duel import box_prudence, contact_share, foul_probability, tackle_approach_angle_deg
from v2engine.flux import DUEL
from v2engine.geometry import in_penalty_area
from v2engine.movement import PlayerState

DUEL_RADIUS_M = 1.0
RUN_UP_MPS = 3.0
STANDING_JUMP_SHARE = 0.85
PLACEMENT_M = 0.06
DUEL_SCALE_M = 0.18
DUEL_MIN, DUEL_MAX = 0.10, 0.90
LANDING_S = 0.2

_SHARE_SPAN = 0.25  # part du contact de 0,25 à 0,75 (`duel._CONTACT_SHARE_AMPLITUDE`)


def has_run_up(player: PlayerState) -> bool:
    """Il saute avec élan : il court à `RUN_UP_MPS` ou plus."""
    return math.hypot(player.velocity.x, player.velocity.y) >= RUN_UP_MPS


def effective_height_m(player: PlayerState, share: float) -> float:
    """Hauteur effective dans le duel : taille + détente (réduite sans élan) + placement au contact, `share` étant la
    part du contact que `player` gagne (0,25 à 0,75)."""
    jump = jump_m(player) * (1.0 if has_run_up(player) else STANDING_JUMP_SHARE)
    placement = PLACEMENT_M * max(-1.0, min(1.0, (share - 0.5) / _SHARE_SPAN))
    return player.height_m + jump + placement


def win_probability(a: PlayerState, b: PlayerState) -> float:
    """Chance que `a` gagne le duel aérien face à `b` : courbe en S de l'écart des hauteurs effectives, bornée à
    [`DUEL_MIN`, `DUEL_MAX`]. Symétrique : `win_probability(b, a) = 1 - win_probability(a, b)`."""
    share = contact_share(a, b)
    gap = effective_height_m(a, share) - effective_height_m(b, 1.0 - share)
    return min(DUEL_MAX, max(DUEL_MIN, 1.0 / (1.0 + math.exp(-gap / DUEL_SCALE_M))))


def rival(player: PlayerState, players: list[PlayerState], z: float, excluded) -> PlayerState | None:
    """Adversaire qui dispute à `player` le ballon à `z` mètres : joueur de champ adverse à moins de `DUEL_RADIUS_M`,
    qui atteint lui aussi cette hauteur (`atteinte.reach_m`) et que `excluded(p)` n'écarte pas (déséquilibré, écarté
    de l'action, hors-jeu à la passe) ; le plus proche, puis par nom. Aucun duel pour un gardien dans sa surface
    (ballon à la main) : sa sortie aérienne est le ticket v2-attributs-restants/03a."""
    if uses_hands(player):
        return None
    candidates = [p for p in players
                  if p.team != player.team and p.poste != "GK"
                  and p.position.distance_to(player.position) <= DUEL_RADIUS_M
                  and reach_m(p) >= z and not excluded(p)]
    if not candidates:
        return None
    return min(candidates, key=lambda p: (p.position.distance_to(player.position), p.name))


@dataclass(frozen=True)
class AerialDuelResult:
    winner: PlayerState
    loser: PlayerState
    probability: float  # chance qu'avait le gagnant
    contact_loser: tuple[PlayerState, ...]  # perdant(s) du contact (Strength ; égalité : les deux), pour le 12c


def resolve(a: PlayerState, b: PlayerState) -> AerialDuelResult:
    """Tire le gagnant (flux DUEL) ; rend aussi le ou les perdants du contact au sens du 12c (part au plus 0,5)."""
    p_a = win_probability(a, b)
    a_wins = DUEL.random() < p_a
    share = contact_share(a, b)
    contact_loser = tuple(p for p, s in ((a, share), (b, 1.0 - share)) if s <= 0.5)
    return (AerialDuelResult(a, b, p_a, contact_loser) if a_wins
            else AerialDuelResult(b, a, 1.0 - p_a, contact_loser))


def jumped(player: PlayerState, z: float) -> bool:
    """Il a sauté pour jouer un ballon à `z` mètres : ballon au-dessus de sa taille."""
    return z > player.height_m


# Fautes du duel aérien (ticket v2-realisme/15b2, constantes validées par le propriétaire le 24/11/2026 ; seuil
# « par derrière » et fautif de côté choisis par lui le 24/11/2026). Le fautif possible dépend de la situation, sa
# probabilité de faute = facteur x celle d'un tacle (Aggression seule, `duel.foul_probability`), x sa prudence de
# surface dans la surface qu'il défend (Decisions, ticket 21c1) :
# - `SIDE` : les deux sautent, épaule contre épaule (de côté ou de face) : 0,10 (3 % à Aggression moyenne) ; fautif
#   possible : le gagnant du contact (Strength, part du contact du 11b, comme la charge du 11c ; égalité : tiré) ;
# - `BEHIND` : l'un saute dans le dos de l'autre (à plus de `BEHIND_ANGLE_DEG` du cap de celui-ci : à moins de 60° de
#   son dos, le seuil « de côté » du 11c) et s'appuie sur lui : 0,50 (15 %) ; fautif possible : celui de derrière ;
# - `BASCULE` : un adversaire collé au sauteur ne peut pas atteindre le ballon et reste sous lui (ou le charge sans
#   jouer le ballon) : 0,80 (24 %) ; sans faute, le sauteur gagne (il joue le ballon).
# Gravité propre : 20 % d'inconsidérées (jaune), 1 % d'excès d'engagement (coude, rouge). Coup franc sifflé tout de
# suite, ballon libre : pas d'avantage (comme le 11c). Chiffres réels : part des fautes nées des duels aériens non
# trouvée ; Stats Perform : 19,9 % des duels sont des fautes, tous duels confondus.
SIDE, BEHIND, BASCULE = "épaule contre épaule", "par derrière", "bascule"
FOUL_FACTOR = {SIDE: 0.10, BEHIND: 0.50, BASCULE: 0.80}
BEHIND_ANGLE_DEG = 120.0
RECKLESS_SHARE = 0.20
EXCESSIVE_SHARE = 0.01


def from_behind(player: PlayerState, victim: PlayerState) -> bool:
    """`player` est dans le dos de `victim` : à plus de `BEHIND_ANGLE_DEG` du cap de `victim` (cap nul : non)."""
    return tackle_approach_angle_deg(player, victim) > BEHIND_ANGLE_DEG


@dataclass(frozen=True)
class AerialChallenge:
    situation: str  # `SIDE`, `BEHIND` ou `BASCULE`
    fouler: PlayerState  # fautif possible
    victim: PlayerState


def challenge(a: PlayerState, b: PlayerState) -> AerialChallenge:
    """Situation d'un duel aérien loyal entre `a` et `b` (les deux sautent) et son fautif possible : celui qui est
    dans le dos de l'autre ; sinon (ou dos à dos) le gagnant du contact, tiré à égalité (flux DUEL)."""
    a_behind, b_behind = from_behind(a, b), from_behind(b, a)
    if a_behind != b_behind:
        return AerialChallenge(BEHIND, a, b) if a_behind else AerialChallenge(BEHIND, b, a)
    share = contact_share(a, b)
    a_pushes = share > 0.5 or (share == 0.5 and DUEL.random() < 0.5)
    situation = BEHIND if a_behind else SIDE
    return AerialChallenge(situation, a, b) if a_pushes else AerialChallenge(situation, b, a)


def under(jumper: PlayerState, players: list[PlayerState], z: float, excluded) -> PlayerState | None:
    """Adversaire qui reste sous `jumper` (bascule) : joueur de champ adverse à moins de `DUEL_RADIUS_M`, qui
    n'atteint pas le ballon à `z` mètres et que `excluded(p)` n'écarte pas ; seulement si `jumper` a sauté et ne joue
    pas à la main ; le plus proche, puis par nom."""
    if uses_hands(jumper) or not jumped(jumper, z):
        return None
    candidates = [p for p in players
                  if p.team != jumper.team and p.poste != "GK"
                  and p.position.distance_to(jumper.position) <= DUEL_RADIUS_M
                  and reach_m(p) < z and not excluded(p)]
    if not candidates:
        return None
    return min(candidates, key=lambda p: (p.position.distance_to(jumper.position), p.name))


def foul_chance(c: AerialChallenge) -> float:
    """Chance que le fautif possible commette la faute : facteur de la situation x faute d'un tacle (Aggression), x
    prudence de surface (Decisions) si la faute tombe dans la surface qu'il défend (lieu : la victime, comme
    `restart.foul_restart`)."""
    probability = FOUL_FACTOR[c.situation] * foul_probability(effective_rating(c.fouler, "Aggression"))
    if in_penalty_area(c.victim.team, c.victim.position):
        probability *= box_prudence(c.fouler)
    return probability

