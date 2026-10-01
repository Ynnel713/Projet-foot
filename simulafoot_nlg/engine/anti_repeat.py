"""Anti-repetition : penalites de recence et de similarite, enregistrement d'un usage.

Tout se mesure en MATCHS (`match_sequence`, rang du match fourni par l'appelant), jamais en
heures (decision sim-window) ; `match_sequence` est obligatoire et par mot-cle partout, None est
refuse sans repli (voir profile_engine.validate_match_sequence).

    recency_penalty    : 1.0 tant que le cooldown de la phrase n'est pas ecoule pour ce joueur, 0.0 apres.
    similarity_penalty : similarite (MinHash, engine/minhash.py) avec les textes recents du joueur.
    update_cooldown    : APRES le choix et le rendu (template_filler.render + post_process.apply),
        enregistre l'usage : phrase_history (via logger.log_usage, ecrivain unique, D17) puis
        similarity_signatures, dans UNE transaction.
"""

from __future__ import annotations

from sqlite3 import Connection

from engine import minhash
from engine.db import sqlite_transaction
from engine.logger import log_usage
from engine.models import Phrase, Player
from engine.profile_engine import validate_match_sequence


class CooldownManquantError(ValueError):
    """Une phrase normale n'a aucune ligne `phrase_cooldowns` (regle "cooldown obligatoire") :
    phrase_selector la refuse au lieu de planter."""


def recency_penalty(conn: Connection, phrase: Phrase, player: Player, *, match_sequence: int) -> float:
    """Penalite de recence : 1.0 si `phrase` a ete utilisee pour `player` il y a MOINS de
    `cooldown_matches` matchs, 0.0 sinon (jamais utilisee, ou cooldown ecoule).

    Le calcul est en MATCHS (decision sim-window), jamais en heures : `ecoules = match_sequence -
    dernier match_sequence d'usage` ; la phrase redevient disponible quand `ecoules >=
    cooldown_matches` (cooldown 3, usage au match 10 : bloquee aux matchs 10, 11, 12, libre au 13).
    Le meme match (ecoules = 0) est donc toujours bloque. Un usage "dans le futur" (rejeu d'un
    match anterieur) compte comme non ecoule. Les lignes d'historique sans `match_sequence`
    (anterieures a la colonne) sont ignorees.

    `match_sequence` est obligatoire, par mot-cle : None -> ValueError (aucun repli), voir
    profile_engine.validate_match_sequence. Une phrase de secours (`is_fallback`) n'est jamais
    soumise au cooldown : 0.0. Une phrase normale SANS ligne `phrase_cooldowns` leve ValueError (regle
    "cooldown obligatoire")."""
    rang = validate_match_sequence(match_sequence)
    if phrase.is_fallback:
        return 0.0
    cooldown = conn.execute(
        "SELECT cooldown_matches FROM phrase_cooldowns WHERE phrase_id = ?", (phrase.id,)
    ).fetchone()
    if cooldown is None:
        raise CooldownManquantError(
            f"recency_penalty : phrase {phrase.id} sans cooldown (phrase_cooldowns) -- refusee."
        )
    dernier = conn.execute(
        """SELECT MAX(match_sequence) FROM phrase_history
           WHERE phrase_id = ? AND player_id = ? AND match_sequence IS NOT NULL""",
        (phrase.id, player.id),
    ).fetchone()[0]
    if dernier is None:
        return 0.0
    return 0.0 if rang - dernier >= cooldown[0] else 1.0


# Fenetre de comparaison, en MATCHS (decision sim-window : jamais en heures) : le match
# courant et les FENETRE_SIMILARITE_MATCHS precedents. PLACE-HOLDER assume, comme les cooldowns
# (aucune donnee d'usage reel pour le calibrer) : a affiner une fois l'anti-repetition mesurable.
FENETRE_SIMILARITE_MATCHS = 3


def similarity_penalty(
    conn: Connection,
    candidate_text: str,
    player: Player,
    *,
    match_sequence: int,
    fenetre_matchs: int = FENETRE_SIMILARITE_MATCHS,
) -> float:
    """Penalite [0, 1] : similarite (MinHash, estimation de Jaccard) de `candidate_text` avec le
    texte le plus proche parmi ceux deja rendus pour `player` dans la fenetre -- 0.0 si aucun,
    1.0 pour un texte identique (a la casse, la ponctuation et l'accentuation composee pres).

    Fenetre EN MATCHS : usages dont `match_sequence` est dans [match_sequence - fenetre_matchs,
    match_sequence] (match courant inclus : deux phrases voisines du meme match comptent ; un
    usage futur ou sans rang est ignore). Par joueur, comme le cooldown.

    `match_sequence` est obligatoire, par mot-cle (None -> ValueError, aucun repli) ;
    `fenetre_matchs` doit etre un entier >= 0."""
    rang = validate_match_sequence(match_sequence)
    if isinstance(fenetre_matchs, bool) or not isinstance(fenetre_matchs, int) or fenetre_matchs < 0:
        raise ValueError(f"fenetre_matchs doit etre un entier >= 0, recu {fenetre_matchs!r}")
    lignes = conn.execute(
        """SELECT s.signature FROM similarity_signatures s
           JOIN phrase_history h ON h.id = s.history_id
           WHERE h.player_id = ? AND h.match_sequence IS NOT NULL
             AND h.match_sequence BETWEEN ? AND ?""",
        (player.id, rang - fenetre_matchs, rang),
    ).fetchall()
    candidate = minhash.signature(candidate_text)
    return max((minhash.similarite(candidate, minhash.deserialiser(ligne[0])) for ligne in lignes), default=0.0)


def update_cooldown(
    conn: Connection,
    phrase: Phrase,
    player: Player,
    match_id: str,
    rendered_text: str,
    *,
    match_sequence: int,
) -> int:
    """Enregistre l'usage de `phrase` (texte final `rendered_text`) pour `player` sur `match_id`
    (rang `match_sequence`) et retourne l'id de la ligne `phrase_history`.

    UNE transaction couvre l'historique puis la signature de similarite : `logger.log_usage` insere
    la ligne, son id (`history_id`) sert a inserer la signature ; si n'importe quelle etape echoue,
    TOUT est annule (jamais un historique sans signature, qui fausserait similarity_penalty). Les
    validations (match_sequence, phrase de secours : ValueError) precedent toute ecriture.

    La transaction est commitee ici : si la connexion en a deja une d'ouverte (ecritures de
    l'appelant non commitees), RuntimeError -- on ne commite ni n'annule les ecritures d'autrui."""
    if conn.in_transaction:
        raise RuntimeError(
            "update_cooldown : une transaction est deja ouverte sur la connexion -- commitez ou "
            "annulez-la d'abord (cette fonction commite sa propre transaction)."
        )
    with sqlite_transaction(conn):
        history_id = log_usage(conn, phrase.id, player.id, match_id, rendered_text, match_sequence=match_sequence)
        conn.execute(
            "INSERT INTO similarity_signatures (history_id, signature) VALUES (?, ?)",
            (history_id, minhash.serialiser(minhash.signature(rendered_text))),
        )
    return history_id
