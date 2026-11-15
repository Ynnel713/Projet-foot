"""Duels et tacles (Phase 3, docs/PLAN_V2.md) : un adversaire à portée du porteur du ballon peut
tenter un tacle -- fréquence des tentatives et risque de faute pilotés par Aggression seule,
issue du duel pilotée par Tackling (tacleur) contre Strength/Balance (porteur, qui protège le
ballon). IA placeholder (D-V08) : dès qu'un adversaire est à portée, il peut tenter sa chance --
pas de lecture tactique de QUAND tacler, ça viendra en Phase 5+."""

from __future__ import annotations

import math
from dataclasses import dataclass

from v2engine.attributes import duel_probability, success_probability
from v2engine.condition import effective_rating
from v2engine.flux import ARBITRAGE, DUEL
from v2engine.movement import PlayerState

# Taux de BASE (tentatives par seconde de contact) auquel un adversaire à portée tente un tacle
# plutôt que d'éviter le contact (guide, Aggression : "NOTE HAUTE : tacles plus tôt... NOTE BASSE :
# évite le contact"). Taux par seconde, pas par tick (v2-socle/06, validé le 25/10/2026) : cible
# 30-40 tacles tentés par match, réel Premier League ~33 (premierleague.com) ; écart Aggression
# conservé (~x2 entre notes extrêmes, comme l'ancien 0,5 ± 0,35).
_ATTEMPT_BASELINE = 0.03
_ATTEMPT_AMPLITUDE = 0.021

# Probabilité de BASE qu'un tacle (gagné ou raté : un tacle qui touche le ballon peut aussi faucher) soit une faute,
# modulée par Aggression seule -- contrepartie du guide (plus de duels tentés, plus de fautes), indépendante de
# Tackling. Ticket v2-collectif/30, validé le 04/11/2026 : environ 30 % des tacles, soit une dizaine de fautes par
# match sur ~35 tacles ; le reste des 21-26 fautes réelles (CIES) vient des fautes de contact.
_FOUL_BASELINE = 0.30
_FOUL_AMPLITUDE = 0.25

# Gravité d'une faute (Lois du jeu, loi 12 : imprudente, inconsidérée, excès d'engagement), enregistrée pour les
# cartons (ticket v2-attributs-restants/09a). Parts fixes, indépendantes d'Aggression qui règle déjà la fréquence
# des fautes (pas de double comptage) ; validées le 04/11/2026, réel non trouvé (à sourcer au 09a).
CARELESS, RECKLESS, EXCESSIVE = "imprudente", "inconsidérée", "excès d'engagement"  # sans carton, jaune, rouge
_RECKLESS_SHARE = 0.12
_EXCESSIVE_SHARE = 0.005


def attempt_tackle_probability(aggression: float) -> float:
    """Taux (par seconde) auquel un adversaire à portée tente un tacle -- voir `_ATTEMPT_BASELINE`."""
    return success_probability(aggression, baseline=_ATTEMPT_BASELINE, amplitude=_ATTEMPT_AMPLITUDE,
                               min_prob=0.0, max_prob=1.0)


def foul_severity() -> str:
    """Gravité d'une faute (voir `_RECKLESS_SHARE`)."""
    r = ARBITRAGE.random()
    return EXCESSIVE if r < _EXCESSIVE_SHARE else RECKLESS if r < _EXCESSIVE_SHARE + _RECKLESS_SHARE else CARELESS


def foul_probability(aggression: float) -> float:
    """Probabilité qu'un tacle soit une faute -- voir `_FOUL_BASELINE`. Dépend
    uniquement d'Aggression, jamais de Tackling (le critère d'acceptation de cette phase compare
    les deux à Tackling égal, voir docs/PLAN_V2.md)."""
    return success_probability(aggression, baseline=_FOUL_BASELINE, amplitude=_FOUL_AMPLITUDE)


def tackle_success_probability(tackler: PlayerState, holder: PlayerState) -> float:
    """Probabilité que `tackler` gagne le ballon face à `holder` -- Tackling seul côté tacleur (qualité du geste ;
    Aggression règle déjà la fréquence des tentatives et le risque de faute : pas de double comptage, règle R1 de
    docs/CARTE_ATTRIBUTS_V2.md, ticket v2-collectif/18), Strength/Balance côté porteur (guide : Strength "gagne les
    duels, protège le ballon dos au but"). Strength seule côté porteur depuis le ticket v2-realisme/12c (décision du
    propriétaire du 14/11/2026, levée de la dérogation A3) : Balance joue APRÈS le contact (`after_contact_*`)."""
    tackler_rating = effective_rating(tackler, "Tackling")
    holder_resistance = effective_rating(holder, "Strength")
    return duel_probability(tackler_rating, holder_resistance)


# Collision asymétrique (ticket v2-realisme/11b, valeur recommandée et validée par délégation du propriétaire,
# 14/11/2026) : part du contact gagnée par chacun, Strength contre Strength sur la courbe de duel partagée. À égalité
# 50/50 ; 10 points d'écart 58/42 ; 20 points 65/35 ; 40 points ou plus 75/25 (le plus fort trois fois moins déplacé).
# Chiffre réel : non trouvé (masses de 65 à 95 kg en Ligue 1, rapport ~1,5 ; l'appui, porté par Strength, au-delà).
_CONTACT_SHARE_AMPLITUDE = 0.25
_CONTACT_SHARE_MIN = 0.5 - _CONTACT_SHARE_AMPLITUDE
_CONTACT_SHARE_MAX = 0.5 + _CONTACT_SHARE_AMPLITUDE


def contact_share(a: PlayerState, b: PlayerState) -> float:
    """Part du contact que `a` gagne face à `b` (0,25 à 0,75), Strength seule (duel de contact, docs/CARTE_ATTRIBUTS_V2.md ;
    Balance joue après le contact, ticket 12c). Le joueur qui gagne la part `s` subit `1 - s` de la correction de
    position et de vitesse : c'est un rapport de masses `s / (1 - s)`. Symétrique : `contact_share(b, a) = 1 - s`."""
    return duel_probability(effective_rating(a, "Strength"), effective_rating(b, "Strength"),
                            amplitude=_CONTACT_SHARE_AMPLITUDE, min_prob=_CONTACT_SHARE_MIN,
                            max_prob=_CONTACT_SHARE_MAX)


# Après un contact perdu (ticket v2-realisme/12c, valeurs recommandées et validées par le propriétaire le 14/11/2026) :
# perte de vitesse et délai avant d'agir, réduits par Balance (rester debout et continuer). Contact perdu : collision
# dont on reçoit la plus petite part (`contact_share`, égalité : les deux) à plus de `CONTACT_MIN_CLOSING_MPS` de
# vitesse de rapprochement, ou tacle subi sans perdre le ballon. Repères (note médiane 62 de la courbe partagée) :
# vitesse perdue 99 -> 5 %, 62 -> 20 %, 11 -> 40 % ; délai 99 -> 0,1 s, 62 -> 0,3 s, 11 -> 0,6 s. Chiffre réel :
# non trouvé (un joueur bousculé met quelques dixièmes de seconde à se rééquilibrer : ordre de grandeur).
CONTACT_MIN_CLOSING_MPS = 2.0
_SPEED_LOSS_POINTS = (0.40, 0.20, 0.05)  # note 11, 62, 99
_DELAY_POINTS_S = (0.6, 0.3, 0.1)


def _balance_curve(player: PlayerState, points: tuple[float, float, float]) -> float:
    """Valeur pour la Balance de `player` : forme en S partagée (`success_probability`, -1 à 1 autour de la médiane),
    étirée vers `points[0]` en dessous de la médiane et vers `points[2]` au-dessus (repères asymétriques)."""
    shaped = success_probability(effective_rating(player, "Balance"), baseline=0.0, amplitude=1.0,
                                 min_prob=-1.0, max_prob=1.0)
    low, mid, high = points
    return mid + shaped * ((high - mid) if shaped >= 0.0 else (mid - low))


def after_contact_speed_loss(player: PlayerState) -> float:
    """Part de sa vitesse que `player` perd après un contact perdu (0,05 à 0,40), Balance seule."""
    return _balance_curve(player, _SPEED_LOSS_POINTS)


def after_contact_delay_s(player: PlayerState) -> float:
    """Délai (s) avant que `player` puisse agir après un contact perdu (0,1 à 0,6 s), Balance seule."""
    return _balance_curve(player, _DELAY_POINTS_S)


def should_attempt_tackle(aggression: float, dt: float) -> bool:
    """Tirage sur un tick de `dt` secondes : indépendant du pas de simulation (taux par seconde)."""
    return DUEL.random() < 1.0 - math.exp(-attempt_tackle_probability(aggression) * dt)


@dataclass(frozen=True)
class TackleResult:
    won: bool  # le tacleur gagne le ballon
    foul: bool  # faute commise (ticket v2-collectif/30) : le ballon reste à l'équipe du porteur


def resolve_tackle(tackler: PlayerState, holder: PlayerState) -> TackleResult:
    """Résout un tacle déjà tenté (voir `should_attempt_tackle`) : jamais une issue garantie,
    même à écart d'attributs extrême (règle "jamais binaire" du guide, voir `duel_probability`). Une faute annule le
    gain du ballon."""
    won = DUEL.random() < tackle_success_probability(tackler, holder)
    foul = DUEL.random() < foul_probability(effective_rating(tackler, "Aggression"))
    return TackleResult(won=won and not foul, foul=foul)


# Duel d'épaule à la course (ticket v2-realisme/11c, constantes validées par le propriétaire le 15/11/2026) : deux
# adversaires au contact, côte à côte, courant vers le même ballon libre. Strength décide le gagnant (courbe partagée) ;
# le perdant est décalé de sa course puis subit le contact perdu du 12c (Balance : vitesse et délai), sans double
# comptage. Faute de charge possible, selon l'Aggression du gagnant. Fréquence réelle des duels d'épaule : non trouvée.
SHOULDER_MIN_SPEED_MPS = 3.0  # les deux courent
SHOULDER_CONTACT_MARGIN_M = 0.3  # distance au plus égale à la somme des rayons + cette marge
SHOULDER_MAX_HEADING_GAP_DEG = 45.0  # courses dans le même sens
SHOULDER_MIN_SIDE_ANGLE_DEG = 60.0  # contact par le côté : axe des deux joueurs à au moins 60° de la course
SHOULDER_BALL_MAX_M = 20.0  # ballon libre à moins de 20 m devant les deux
SHOULDER_BALL_MAX_ANGLE_DEG = 30.0  # « devant » : au plus 30° de la course de chacun
SHOULDER_COOLDOWN_S = 1.0  # au plus un duel par paire toutes les 1,0 s
SHOULDER_PUSH_M = 0.5  # décalage latéral du perdant, à l'opposé du gagnant
SHOULDER_PUSH_STEPS = 3  # réparti sur 3 pas (0,3 s au pas du produit), pas en un saut (réserve A2 de l'expert, propriétaire)
SHOULDER_FOUL_FACTOR = 0.15  # part de la probabilité de faute d'un tacle (même Aggression)


def _angle_deg(u, v) -> float:
    lu, lv = math.hypot(u.x, u.y), math.hypot(v.x, v.y)
    if lu < 1e-9 or lv < 1e-9:
        return 180.0
    cos = max(-1.0, min(1.0, (u.x * v.x + u.y * v.y) / (lu * lv)))
    return math.degrees(math.acos(cos))


def shoulder_contact(a: PlayerState, b: PlayerState, ball_position) -> bool:
    """Vrai si `a` et `b` (adversaires) sont au contact, côte à côte, et courent tous deux vers `ball_position`."""
    if a.team == b.team:
        return False
    if math.hypot(a.velocity.x, a.velocity.y) < SHOULDER_MIN_SPEED_MPS or \
            math.hypot(b.velocity.x, b.velocity.y) < SHOULDER_MIN_SPEED_MPS:
        return False
    axis = b.position - a.position
    if math.hypot(axis.x, axis.y) > a.radius_m + b.radius_m + SHOULDER_CONTACT_MARGIN_M:
        return False
    if _angle_deg(a.velocity, b.velocity) > SHOULDER_MAX_HEADING_GAP_DEG:
        return False
    run = a.velocity + b.velocity
    side = _angle_deg(axis, run)
    if min(side, 180.0 - side) < SHOULDER_MIN_SIDE_ANGLE_DEG:
        return False
    for p in (a, b):
        to_ball = ball_position - p.position
        if math.hypot(to_ball.x, to_ball.y) > SHOULDER_BALL_MAX_M or _angle_deg(to_ball, p.velocity) > SHOULDER_BALL_MAX_ANGLE_DEG:
            return False
    return True


def shoulder_win_probability(a: PlayerState, b: PlayerState) -> float:
    """Chance que `a` gagne le duel d'épaule face à `b` : Strength seule, courbe partagée (`duel_probability`)."""
    return duel_probability(effective_rating(a, "Strength"), effective_rating(b, "Strength"))


def shoulder_foul_probability(charger: PlayerState) -> float:
    """Chance que la charge du gagnant soit une faute : `SHOULDER_FOUL_FACTOR` x celle d'un tacle (Aggression)."""
    return SHOULDER_FOUL_FACTOR * foul_probability(effective_rating(charger, "Aggression"))


@dataclass(frozen=True)
class ShoulderResult:
    winner: PlayerState
    loser: PlayerState
    foul: bool
    issue: str  # « plus fort », « plus faible » ou « égalité » : Strength du gagnant face au perdant (mesure du banc)


def resolve_shoulder_duel(a: PlayerState, b: PlayerState) -> ShoulderResult:
    """Tire le gagnant (flux DUEL) puis la faute de charge du gagnant."""
    a_wins = DUEL.random() < shoulder_win_probability(a, b)
    winner, loser = (a, b) if a_wins else (b, a)
    gap = effective_rating(winner, "Strength") - effective_rating(loser, "Strength")
    issue = "plus fort" if gap > 0 else "plus faible" if gap < 0 else "égalité"
    return ShoulderResult(winner, loser, DUEL.random() < shoulder_foul_probability(winner), issue)
