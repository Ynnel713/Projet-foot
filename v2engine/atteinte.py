"""Atteinte d'un joueur selon la hauteur du ballon (ticket v2-hauteur-ballon/03a) : un joueur ne joue le ballon que s'il
l'atteint dans une tranche de hauteur accessible à son corps, calculée depuis sa taille et sa détente (Jumping Reach).
Remplace la règle du ticket v2-collectif/29 (personne au-dessus de `vol.AERIAL_HEIGHT_M`, tout le monde en dessous).

Constantes validées par le propriétaire le 23/11/2026 :
- tranches en part de la taille H, proportions segmentaires de Drillis et Contini (1966, reprises par D. A. Winter,
  *Biomechanics and Motor Control of Human Movement*) : hanche 0,530 H, épaule 0,818 H ; pied jusqu'à la hanche
  (`FOOT_SHARE`), corps de la hanche à l'épaule (`BODY_SHARE`), tête de l'épaule à H + détente ;
- détente : de 0,35 m (Jumping Reach 1) à 0,65 m (99), linéaire (`JUMP_M`) ; repère : saut vertical d'environ 56 cm
  chez des footballeurs d'élite (Wisløff et al., 2004, Br J Sports Med, cité de mémoire, à confirmer) ; lien entre la
  note et les centimètres non trouvé (ordre de grandeur) ;
- mains du gardien dans sa surface : jusqu'à 1,30 H + détente (`HANDS_SHARE`, portée debout bras tendus, source non
  trouvée) ;
- taille manquante : médiane du poste dans la base (Ligue 1, 477 tailles sur 485 joueurs).

Une seule hauteur atteinte (taille + Jumping Reach) : le duel aérien (`v2-realisme/15b`) la réutilisera pour désigner
le gagnant, sans y ajouter de bonus (pas de double comptage, `docs/CARTE_ATTRIBUTS_V2.md`)."""

from __future__ import annotations

from v2engine.condition import effective_rating
from v2engine.geometry import in_penalty_area

FOOT_SHARE = 0.53
BODY_SHARE = 0.82
HANDS_SHARE = 1.30
JUMP_M = (0.35, 0.65)  # détente à Jumping Reach 1 et 99
# Taille médiane par poste dans la base (Ligue 1, 23/11/2026), pour un joueur sans taille
NEUTRAL_HEIGHT_M = {"GK": 1.89, "DC": 1.87, "BU": 1.84, "MC": 1.81, "MDC": 1.80, "MOC": 1.80, "AD": 1.775,
                    "AG": 1.78, "RB": 1.78, "LB": 1.78}
DEFAULT_HEIGHT_M = 1.82  # médiane de la base, poste inconnu

PIED, CORPS, TETE, MAINS = "pied", "corps", "tête", "mains"


def height_of(taille_cm: int | float | None, poste: str) -> float:
    """Taille (m) d'un joueur : sa fiche, sinon la médiane de son poste."""
    if taille_cm:
        return float(taille_cm) / 100.0
    return NEUTRAL_HEIGHT_M.get(poste, DEFAULT_HEIGHT_M)


def jump_m(player) -> float:
    """Détente (m) selon Jumping Reach, de `JUMP_M[0]` (1) à `JUMP_M[1]` (99)."""
    note = min(99.0, max(1.0, float(effective_rating(player, "Jumping Reach"))))
    return JUMP_M[0] + (JUMP_M[1] - JUMP_M[0]) * (note - 1.0) / 98.0


def uses_hands(player) -> bool:
    """Gardien dans sa propre surface : il peut prendre le ballon à la main."""
    return player.poste == "GK" and in_penalty_area("away" if player.team == "home" else "home", player.position)


def reach_m(player) -> float:
    """Hauteur la plus haute où `player` touche le ballon : tête en saut, ou mains du gardien dans sa surface."""
    share = HANDS_SHARE if uses_hands(player) else 1.0
    return share * player.height_m + jump_m(player)


def body_part(player, z: float) -> str | None:
    """Partie du corps qui joue un ballon à `z` mètres : pied, corps, tête, mains (gardien dans sa surface, ballon
    au-dessus du corps) ; `None` s'il passe au-dessus."""
    if z > reach_m(player):
        return None
    if z <= FOOT_SHARE * player.height_m:
        return PIED
    if z <= BODY_SHARE * player.height_m:
        return CORPS
    return MAINS if uses_hands(player) else TETE
