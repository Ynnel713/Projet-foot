"""Resolution d'un identifiant de joueur en `Player` NLG, par lookup dans la base (decision D14).

La racine fournit des `player_id` (= `players.id` = colonne ID du classeur = `Player.id` de la
simulation) ; le NLG fait le lookup. Le `Player` retourne porte ses attributs FM26 (table
`player_attributes`) : sans eux, toute condition FM d'une phrase serait fausse. Un joueur SANS
attributs importes (6,9 % de la base) donne `attributes == {}`, un etat normal (D16).
"""

from __future__ import annotations

from sqlite3 import Connection

from engine.models import Player
from engine.profile_engine import normalize_player


def resolve(player_id: int, conn: Connection) -> Player:
    """Le `Player` d'identifiant `player_id` (connexion injectee : l'appelant garde la main sur sa
    duree de vie et sa transaction). KeyError si l'identifiant est absent de `players` ; TypeError si
    `player_id` n'est pas un entier (un bool n'en est pas un)."""
    if isinstance(player_id, bool) or not isinstance(player_id, int):
        raise TypeError(f"player_id doit etre un int, recu {type(player_id).__name__}")
    curseur = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,))
    ligne = curseur.fetchone()
    if ligne is None:
        raise KeyError(f"Joueur {player_id} absent de la table players.")
    brut = dict(zip((colonne[0] for colonne in curseur.description), tuple(ligne), strict=True))
    brut["attributes"] = {
        nom: valeur
        for nom, valeur in conn.execute(
            "SELECT attribute, value FROM player_attributes WHERE player_id = ?", (player_id,)
        ).fetchall()
    }
    return normalize_player(brut)
