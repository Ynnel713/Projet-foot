"""SQUELETTE -- anti-repetition : penalites de recence/similarite, mise a
jour du cooldown. Aucune implementation dans cette session.

Algorithme prevu :
    recency_penalty : lit phrase_history pour (phrase_id, player_id),
        cherche le dernier usage (`used_at` le plus recent) puis le nombre de
        matchs ecoules depuis (a definir : soit un compteur de matchs
        explicite fourni par l'appelant, soit derive de match_id via une
        table de matchs a venir). Retourne une penalite dans [0, 1] : 0 = pas
        de penalite (cooldown largement ecoule), 1 = phrase totalement
        interdite (cooldown pas ecoule). Distinct du refus pur "cooldown non
        defini" gere par phrase_selector -- ici c'est une PENALITE continue,
        pas un refus binaire.
    similarity_penalty : calcule une signature MinHash (ou equivalent, k-shingles
        sur le texte rendu) du candidat, la compare aux `similarity_signatures`
        recentes du meme joueur (similarite de Jaccard approx). Retourne une
        penalite [0, 1] croissante avec la similarite au texte le plus proche
        deja vu.
    update_cooldown : APRES qu'une phrase a ete choisie et rendue (voir
        template_filler.render + post_process.apply), enregistre l'usage :
        insere dans phrase_history (ou delegue a logger.log_usage -- a
        trancher a l'implementation pour eviter la double ecriture), calcule
        et insere la signature de similarite dans similarity_signatures.
"""

from __future__ import annotations

from sqlite3 import Connection

from engine.models import Phrase, Player
from engine.profile_engine import validate_match_sequence


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
        raise ValueError(f"recency_penalty : phrase {phrase.id} sans cooldown (phrase_cooldowns) -- refusee.")
    dernier = conn.execute(
        """SELECT MAX(match_sequence) FROM phrase_history
           WHERE phrase_id = ? AND player_id = ? AND match_sequence IS NOT NULL""",
        (phrase.id, player.id),
    ).fetchone()[0]
    if dernier is None:
        return 0.0
    return 0.0 if rang - dernier >= cooldown[0] else 1.0


def similarity_penalty(conn: Connection, candidate_text: str, player: Player) -> float:
    """Penalite [0, 1] liee a la similarite de `candidate_text` avec les
    phrases recemment generees pour `player` (voir algorithme prevu en tete
    de module). Leve NotImplementedError tant que la banque de phrases n'est
    pas livree."""
    raise NotImplementedError(
        "anti_repeat.similarity_penalty : squelette non implémenté -- voir la docstring "
        "de engine/anti_repeat.py pour l'algorithme prévu."
    )


def update_cooldown(
    conn: Connection, phrase: Phrase, player: Player, match_id: str, rendered_text: str
) -> None:
    """Enregistre l'usage de `phrase` (texte final `rendered_text`) pour
    `player` sur `match_id` -- voir algorithme prevu en tete de module. Leve
    NotImplementedError tant que la banque de phrases n'est pas livree."""
    raise NotImplementedError(
        "anti_repeat.update_cooldown : squelette non implémenté -- voir la docstring "
        "de engine/anti_repeat.py pour l'algorithme prévu."
    )
