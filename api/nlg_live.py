"""Fil « commentaire en direct » produit par le NLG (simulafoot_nlg) pour un match déjà joué.

Chaîne (la même que scripts/export_match_to_nlg.py) : match simulé -> `Timeline` (engine/narrative.py : buts, cartons, remplacements
RÉELS + occasions intercalées) -> dicts du contrat NLG (engine/nlg_ingestion.py) -> `cli.narrer_flux` dans le venv du NLG (deuxième
processus) -> un texte par événement commenté (BUT, CARTON_JAUNE, REMPLACEMENT, TIR_NON_CADRE, ARRET_GARDIEN, DEFENSE...).

Base de travail : une COPIE de la base du NLG (historique vide), créée une fois par processus API dans le dossier temporaire. Les usages
de phrases y sont enregistrés match après match : l'anti-répétition (cooldown, mémoire inter-joueurs) joue d'un match à l'autre, comme
dans scripts/sample_nlg_output.py, et la vraie base du NLG n'est jamais modifiée. Le fil de chaque match est généré UNE fois (cache).

Si le NLG est indisponible (venv, base ou joueurs sans id), `generate_nlg_feed` lève `NlgUnavailable` : l'appelant retombe sur le fil
à gabarits simples (api.live_commentary.build_live_feed)."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import replace
from pathlib import Path

from ligue1sim.clubs import Club
from ligue1sim.lineup import pick_best_formation
from ligue1sim.schedule import Match

from api.live_commentary import _FIN_DU_MATCH, _TITLES, LiveEvent

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
NLG_DIR = ROOT / "simulafoot_nlg"
NLG_DB = NLG_DIR / "data" / "simulafoot.db"
_ENGINE_DIR = ROOT / "engine"
_TIMEOUT_S = 180

# Scénario NLG -> type d'événement de l'UI (titre et couleur : voir _TITLES et le frontend).
_KIND_BY_SCENARIO = {
    "BUT": "goal",
    "CARTON_JAUNE": "yellow",
    "CARTON_ROUGE": "red",
    "REMPLACEMENT": "sub",
    "TIR_NON_CADRE": "shot_off",
    "ARRET_GARDIEN": "save",
    "DEFENSE": "defense",
    "PENALTY_RATE": "penalty_missed",
}
_TITLES = {
    **_TITLES,
    "shot_off": "TIR NON CADRÉ",
    "save": "ARRÊT GARDIEN",
    "defense": "DÉFENSE",
}
_ORDER = {"start": 0, "goal": 1, "penalty_missed": 2, "shot_off": 2, "save": 2, "defense": 2, "yellow": 3, "second_yellow": 3, "red": 3,
          "sub": 4, "end": 5}

_lock = threading.Lock()
_work_db: Path | None = None
_sequence = 0
_cache: dict[tuple, list[LiveEvent]] = {}

# Exécuté DANS le venv du NLG : raconte le fichier d'événements avec la fonction de `cli.py narrate` (usage enregistré dans la base de
# travail) et imprime en UTF-8 un JSON [{event_id, minute, scenario, texte}].
_NARRER = """
import json, sys
import cli
from engine.db import get_sqlite
from engine.selectivity import Selectivite
db, fichier = sys.argv[1], sys.argv[2]
conn = get_sqlite(db)
evenements = [json.loads(l) for l in open(fichier, encoding="utf-8") if l.strip()]
resultats = list(cli.narrer_flux(conn, evenements, Selectivite.depuis_base(conn)))
conn.close()
sys.stdout.buffer.write(json.dumps(resultats, ensure_ascii=False).encode("utf-8"))
"""


class NlgUnavailable(RuntimeError):
    """Le NLG ne peut pas raconter ce match (venv ou base absents, joueurs sans id, échec du processus)."""


def _nlg_python() -> Path:
    for relatif in ("Scripts/python.exe", "bin/python"):
        chemin = NLG_DIR / ".venv" / relatif
        if chemin.exists():
            return chemin
    raise NlgUnavailable(f"venv du NLG introuvable ({NLG_DIR / '.venv'})")


def _ensure_work_db() -> Path:
    """Copie de la base du NLG, historique d'usage vide, créée une fois par processus."""
    global _work_db
    if _work_db is None:
        if not NLG_DB.exists():
            raise NlgUnavailable(f"base du NLG introuvable ({NLG_DB})")
        chemin = Path(tempfile.gettempdir()) / f"simulafoot_nlg_live_{os.getpid()}.db"
        shutil.copyfile(NLG_DB, chemin)
        import sqlite3

        conn = sqlite3.connect(chemin)
        conn.execute("DELETE FROM phrase_history")
        conn.execute("DELETE FROM similarity_signatures")
        conn.commit()
        conn.close()
        _work_db = chemin
    return _work_db


def _marquer_joueurs(texte: str, noms: set[str]) -> tuple[tuple[str, bool], ...]:
    """Découpe `texte` en morceaux ; les noms de joueurs de l'événement (plus longs d'abord) sont marqués (texte, True)."""
    noms = {n for n in noms if n}
    if not noms:
        return ((texte, False),)
    motif = re.compile("(" + "|".join(re.escape(n) for n in sorted(noms, key=len, reverse=True)) + ")", re.IGNORECASE)
    morceaux: list[tuple[str, bool]] = []
    for i, piece in enumerate(motif.split(texte)):
        if piece:
            morceaux.append((piece, i % 2 == 1))
    return tuple(morceaux)


# Événements dont l'acteur du dict (celui qui est NOMMÉ dans l'UI) doit apparaître dans le texte : si la phrase du NLG n'a pas de slot de
# joueur (« Le mitrailleur tire de partout… », « Le sage sort un réflexe… »), on lui ajoute le nom en tête.
_ACTEUR_EN_TETE = {"goal", "yellow", "second_yellow", "red", "shot_off", "penalty_missed", "save"}
_TIREUR_APRES = {"save": " Frappe de ", "defense": " Tir de "}  # l'acteur du dict est le gardien / le défenseur : on ajoute le tireur


def _present(parts: tuple[tuple[str, bool], ...], nom: str | None) -> bool:
    return bool(nom) and any(est_joueur and texte.lower() == nom.lower() for texte, est_joueur in parts)


def completer_protagonistes(
    kind: str, parts: tuple[tuple[str, bool], ...], acteur: str | None, tireur: str | None = None, entrant: str | None = None
) -> tuple[tuple[str, bool], ...]:
    """Complète le texte du NLG avec les protagonistes qu'il ne nomme pas (phrases à surnom, sans slot de joueur), pour que l'UI dise
    toujours QUI : l'acteur en tête (« Cameron Archer — … »), le tireur après un arrêt ou une défense (« … Frappe de X. »), l'entrant
    d'un remplacement (« … Entrant : X. »). Un nom déjà présent dans le texte n'est jamais répété."""
    if kind in _ACTEUR_EN_TETE and acteur and not _present(parts, acteur):
        parts = ((acteur, True), (" — ", False)) + parts
    if kind in _TIREUR_APRES and tireur and not _present(parts, tireur):
        parts = parts + ((_TIREUR_APRES[kind], False), (tireur, True), (".", False))
    if kind == "sub" and entrant and not _present(parts, entrant):
        parts = parts + ((" Entrant : ", False), (entrant, True), (".", False))
    return parts


def _timeline(match: Match, home: Club, away: Club, label: str):
    """`Timeline` (engine/narrative.py) du match : compositions réelles du jour (titulaires de `MatchEvents`), occasions intercalées."""
    if str(_ENGINE_DIR) not in sys.path:
        sys.path.insert(0, str(_ENGINE_DIR))
    from narrative import build_timeline, match_result_from  # noqa: PLC0415 -- engine/ n'est pas un paquet

    events = match.events

    def lineup(club: Club, stats: list):
        par_nom = {p.name: p for p in club.players}
        titulaires = [par_nom[s.player_name] for s in stats if s.started and s.player_name in par_nom]
        return replace(pick_best_formation(club), players=titulaires)

    result = match_result_from(match, events, lineup(home, events.home_lineup), lineup(away, events.away_lineup), date=label)
    return build_timeline(result)


def generate_nlg_feed(match: Match, home: Club, away: Club, label: str) -> list[LiveEvent]:
    """Fil du match raconté par le NLG, chronologique, avec coup d'envoi et coup de sifflet final. `label` : suffixe du `match_id`
    (journée, poule...), qui varie la graine du tirage des occasions. Lève `NlgUnavailable` si le NLG ne peut pas le produire."""
    global _sequence
    events = match.events
    cle = (match.home, match.away, label, id(events), tuple((g.minute, g.scorer) for g in events.goals))
    with _lock:
        if cle in _cache:
            return _cache[cle]

        python = _nlg_python()
        db = _ensure_work_db()
        if str(_ENGINE_DIR) not in sys.path:
            sys.path.insert(0, str(_ENGINE_DIR))
        from nlg_ingestion import timeline_to_events, write_jsonl  # noqa: PLC0415

        timeline = _timeline(match, home, away, label)
        _sequence += 1
        skipped: list[tuple[int, str]] = []
        dicts = timeline_to_events(timeline, match_sequence=_sequence, home_squad=home.players, away_squad=away.players, skipped=skipped)
        if not dicts:
            raise NlgUnavailable("aucun événement convertible (joueurs sans id ?)")

        with tempfile.TemporaryDirectory() as dossier:
            fichier = write_jsonl(dicts, Path(dossier) / "match.jsonl")
            processus = subprocess.run(
                [str(python), "-c", _NARRER, str(db), str(fichier)],
                cwd=NLG_DIR, capture_output=True, timeout=_TIMEOUT_S, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        if processus.returncode != 0:
            raise NlgUnavailable(processus.stderr.decode("utf-8", "replace")[-500:])
        resultats = {r["event_id"]: r for r in json.loads(processus.stdout.decode("utf-8"))}

        noms = {p.id: p.name for club in (home, away) for p in club.players if p.id is not None}
        # Tireur d'une occasion arrêtée / défendue : le NarrativeEvent le nomme, le dict (acteur = gardien ou défenseur) non. Appariement par
        # (minute, issue, club du tireur), dans l'ordre : le dict garde l'ordre de la timeline.
        tireurs: dict[tuple, list[str]] = {}
        for e in timeline.events:
            if e.event_type == "occasion" and e.outcome in ("arret", "tacle", "degagement"):
                tireurs.setdefault((e.minute, e.outcome, e.team), []).append(e.main_player)
        feed: list[tuple[LiveEvent, int]] = [
            (LiveEvent(0, "start", _TITLES["start"], None, None, (("Le coup d'envoi est donné.", False),)), 0),
            (LiveEvent(_FIN_DU_MATCH, "end", _TITLES["end"], None, None, (("Le coup de sifflet final retentit.", False),)), 10**6),
        ]
        score = {"home": 0, "away": 0}
        for dico in dicts:
            res = resultats.get(dico["event_id"])
            if res is None or res.get("texte") is None:
                continue  # poteau / barre : non commentés en V2.1
            kind = _KIND_BY_SCENARIO.get(res["scenario"])
            if kind is None:
                continue
            if kind == "goal":
                score["home" if dico["is_home"] else "away"] += 1
            joueurs = {noms.get(dico.get(c)) for c in ("player_id", "passeur_id", "receveur_id", "sortant_id", "entrant_id")}
            tireur = None
            if dico["event_type"] == "occasion" and dico["outcome"] in ("arret", "tacle", "degagement"):
                club_tireur = dico["home_team"] if dico["player_team"] == dico["away_team"] else dico["away_team"]
                file = tireurs.get((dico["minute"], dico["outcome"], club_tireur))
                tireur = file.pop(0) if file else None
                joueurs.add(tireur)
            parts = _marquer_joueurs(res["texte"], joueurs)
            parts = completer_protagonistes(kind, parts, noms.get(dico["player_id"]), tireur, noms.get(dico.get("entrant_id")))
            if kind == "goal":
                parts += ((f" ({score['home']}-{score['away']})", False),)
            feed.append((
                LiveEvent(dico["minute"], kind, _TITLES[kind], "home" if dico["is_home"] else "away", dico["player_team"], parts),
                dico["event_id"],
            ))
        ordonne = [e for e, _ in sorted(feed, key=lambda t: (t[0].minute, _ORDER[t[0].kind], t[1]))]
        _cache[cle] = ordonne
        return ordonne
