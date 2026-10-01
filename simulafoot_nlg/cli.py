"""CLI simulafoot_nlg.

Commandes :
    python cli.py init-db
    python cli.py import-players --xlsx data/joueurs.xlsx
    python cli.py import-seed
    python cli.py convert-commentary --xlsx data/seed_source/banque_de_phrases_simulafoot.xlsx
    python cli.py select --scenario BUT --player-id 1 --match-sequence 1
    python cli.py narrate --events evenements.jsonl [--dry-run]

Note sur l'import de data/import/import_players.py : `import` est un mot-cle
Python, donc `from data.import.import_players import ...` est une ERREUR DE
SYNTAXE (le nom du dossier suit exactement l'arborescence demandee dans le
brief, qui n'est pas un identifiant Python valide en import statique).
Contournement standard : `importlib.import_module` prend une chaine, pas un
identifiant -- le mot-cle ne pose alors aucun probleme, la restriction ne
s'applique qu'a la forme syntaxique `import x.y.z`. `# type: ignore` localise
sur cette seule ligne (mypy ne peut pas typer un import dynamique par
chaine) -- pas de `# type: ignore` ailleurs dans ce fichier.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlite3 import Connection  # noqa: E402

from engine.anti_repeat import update_cooldown  # noqa: E402
from engine.context_builder import dict_to_context  # noqa: E402
from engine.db import get_sqlite  # noqa: E402
from engine.event_contract import validate_event_stream  # noqa: E402
from engine.models import MatchContext  # noqa: E402
from engine.narrative_adapter import event_to_scenario  # noqa: E402
from engine.phrase_selector import AucunCandidatError  # noqa: E402
from engine.phrase_selector import select as select_phrase  # noqa: E402
from engine.player_resolver import resolve  # noqa: E402
from engine.scenario_engine import load_scenario  # noqa: E402
from engine.selectivity import Selectivite  # noqa: E402
from scripts.convert_commentary_xlsx_to_yaml import DEFAULT_YAML_PATH, convertir  # noqa: E402
from scripts.export_analytics import export_analytics  # noqa: E402
from scripts.import_seed import import_seed  # noqa: E402
from scripts.init_db import DEFAULT_SCHEMA_PATH, init_db  # noqa: E402
from scripts.reset_seed import reset_seed  # noqa: E402


class _ImportStatsLike(Protocol):
    """Forme de data.import.import_players.ImportStats -- ce Protocol existe
    UNIQUEMENT parce que ce module ne peut pas etre importe statiquement (son
    package s'appelle "import", mot-cle reserve) : mypy ne peut donc pas
    connaitre le vrai type de retour d'import_players, seulement sa forme,
    reproduite ici a la main."""

    players_imported: int
    attributes_mapped: int
    columns_ignored: tuple[str, ...]


_import_players_module = importlib.import_module("data.import.import_players")
import_players: Callable[[str | Path, str | Path, str | Path], _ImportStatsLike] = (
    _import_players_module.import_players
)

ROOT = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = ROOT / "data" / "simulafoot.db"
DEFAULT_DUCKDB_PATH = ROOT / "data" / "analytics.duckdb"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("simulafoot_nlg.cli")


def _cmd_init_db(args: argparse.Namespace) -> None:
    init_db(db_path=args.db, schema_path=DEFAULT_SCHEMA_PATH)
    print(f"Base initialisée : {args.db}")


def _cmd_import_players(args: argparse.Namespace) -> None:
    try:
        stats = import_players(args.xlsx, args.duckdb, args.db)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Import impossible : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(
        f"{stats.players_imported} joueurs importés, "
        f"{stats.attributes_mapped} attributs mappés, "
        f"{len(stats.columns_ignored)} colonnes ignorées : "
        f"{', '.join(stats.columns_ignored) or '(aucune)'}"
    )


def _cmd_import_seed(args: argparse.Namespace) -> None:
    try:
        stats = import_seed(args.db)
    except FileNotFoundError as exc:
        print(f"Import impossible : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except ValueError as exc:  # inclut SeedValidationError
        print(f"Banque invalide, rien n'a été importé : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(
        f"{stats.scenarios} scénarios, {stats.variants} variantes, "
        f"{stats.phrases} phrases, {stats.dictionaries} entrées de dictionnaire importés"
    )


def _cmd_reset_seed(args: argparse.Namespace) -> None:
    try:
        deleted = reset_seed(args.db, yes=args.yes)
    except ValueError as exc:
        print(f"Reset refusé : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"Banque et historique vidés ({sum(deleted.values())} lignes) ; joueurs conservés.")


def _cmd_convert_commentary(args: argparse.Namespace) -> None:
    try:
        n_phrases = convertir(args.xlsx, args.out)
    except FileNotFoundError as exc:
        print(f"Conversion impossible : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except ValueError as exc:  # inclut CommentaryConversionError
        print(f"Classeur invalide, rien n'a été écrit : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"{n_phrases} phrases écrites dans {args.out} -- lancez `import-seed` pour les importer en base.")


def _cmd_export_analytics(args: argparse.Namespace) -> None:
    counts = export_analytics(args.db, args.duckdb)
    for table, count in counts.items():
        print(f"{table}: {count} lignes exportées")


def _cmd_select(args: argparse.Namespace) -> None:
    """Commande de développement : sélectionne une phrase pour un (scénario, joueur) avec un
    contexte minimal (match_id="cli", pas un vrai événement) et l'affiche. Jamais de texte inventé :
    scénario introuvable ou à sec -> erreur explicite. La graine est explicite (--seed)."""
    if not Path(args.db).exists():
        print(f"Base introuvable : {args.db} -- lancez `python cli.py init-db` d'abord.", file=sys.stderr)
        raise SystemExit(1)

    conn = get_sqlite(args.db)
    try:
        scenario = load_scenario(conn, args.scenario)
        if scenario is None:
            print(f'Scénario "{args.scenario}" introuvable (banque pas encore importée ?).', file=sys.stderr)
            raise SystemExit(1)

        try:
            player = resolve(args.player_id, conn)
        except KeyError as exc:
            print(f"Joueur {args.player_id} introuvable.", file=sys.stderr)
            raise SystemExit(1) from exc

        try:
            resultat = select_phrase(
                conn,
                args.scenario,
                player,
                MatchContext(match_id="cli"),
                seed=args.seed,
                match_sequence=args.match_sequence,
                selectivite=Selectivite.depuis_base(conn),
            )
        except AucunCandidatError as exc:
            print(f"select : {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        print(resultat.rendered_text)
    finally:
        conn.close()


def narrer_flux(
    conn: Connection, evenements: Iterable[Mapping[str, Any]], selectivite: Selectivite, *, enregistrer: bool = True
) -> Iterator[dict[str, Any]]:
    """Pipeline d'integration : pour chaque evenement du flux -- validation (event_contract), scenario
    (narrative_adapter), joueur et contexte (player_resolver / context_builder), phrase rendue (select),
    puis enregistrement de l'usage (update_cooldown) pour que le cooldown et la similarite voient les
    evenements deja racontes du flux. Une phrase de secours n'est jamais enregistree. Un evenement sans
    scenario en V2.1 (poteau / barre) est signale `scenario: None`, sans texte. La graine de chaque
    evenement est `match_id|match_sequence|event_id` (explicite, jamais une horloge)."""
    for evenement in validate_event_stream(evenements):
        scenario = event_to_scenario(evenement)
        if scenario is None:
            yield {"event_id": evenement["event_id"], "minute": evenement["minute"], "scenario": None, "texte": None}
            continue
        joueur = resolve(evenement["player_id"], conn)
        contexte = dict_to_context(evenement, conn)
        resultat = select_phrase(
            conn,
            scenario,
            joueur,
            contexte,
            seed=f"{evenement['match_id']}|{evenement['match_sequence']}|{evenement['event_id']}",
            match_sequence=evenement["match_sequence"],
            selectivite=selectivite,
        )
        if enregistrer and not resultat.phrase.is_fallback:
            update_cooldown(
                conn, resultat.phrase, joueur, evenement["match_id"], resultat.rendered_text,
                match_sequence=evenement["match_sequence"],
            )
        yield {
            "event_id": evenement["event_id"],
            "minute": evenement["minute"],
            "scenario": scenario,
            "texte": resultat.rendered_text,
            "secours": resultat.phrase.is_fallback,
        }


def _lire_evenements(source: str) -> Iterator[dict[str, Any]]:
    """Flux JSON Lines (un dict par ligne, lignes vides ignorees) depuis un fichier ou `-` (stdin)."""
    flux = sys.stdin if source == "-" else Path(source).open(encoding="utf-8")
    try:
        for numero, ligne in enumerate(flux, 1):
            if ligne.strip():
                try:
                    yield json.loads(ligne)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Ligne {numero} : JSON invalide ({exc.msg}).") from exc
    finally:
        if flux is not sys.stdin:
            flux.close()


def _cmd_narrate(args: argparse.Namespace) -> None:
    """Raconte un flux d'evenements (JSON Lines, contrat de engine/event_contract.py) : une ligne
    "minute' texte" par evenement commente. Enregistre l'usage de chaque phrase (cooldown, similarite)
    sauf avec --dry-run."""
    if not Path(args.db).exists():
        print(f"Base introuvable : {args.db} -- lancez `python cli.py init-db` d'abord.", file=sys.stderr)
        raise SystemExit(1)
    if args.events != "-" and not Path(args.events).exists():
        print(f"Fichier d'evenements introuvable : {args.events}", file=sys.stderr)
        raise SystemExit(1)

    conn = get_sqlite(args.db)
    non_commentes = 0
    try:
        selectivite = Selectivite.depuis_base(conn)
        try:
            for resultat in narrer_flux(conn, _lire_evenements(args.events), selectivite, enregistrer=not args.dry_run):
                if resultat["texte"] is None:
                    non_commentes += 1
                else:
                    print(f"{resultat['minute']}' {resultat['texte']}")
        except AucunCandidatError as exc:
            print(f"narrate : {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        except (ValueError, KeyError) as exc:
            print(f"narrate : evenement refuse, {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
    finally:
        conn.close()
    if non_commentes:
        print(f"{non_commentes} evenement(s) non commente(s) en V2.1 (poteau / barre).", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cli.py", description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_SQLITE_PATH), help="Chemin de simulafoot.db")
    parser.add_argument("--duckdb", default=str(DEFAULT_DUCKDB_PATH), help="Chemin de analytics.duckdb")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Crée data/simulafoot.db depuis data/schema.sql")

    p_import = sub.add_parser("import-players", help="Importe joueurs.xlsx dans DuckDB puis SQLite")
    p_import.add_argument("--xlsx", required=True, help="Chemin vers joueurs.xlsx")

    sub.add_parser("import-seed", help="Importe data/seed/*.yml dans SQLite")

    p_reset = sub.add_parser(
        "reset-seed",
        help="Vide la banque de phrases et l'historique (joueurs conservés) -- exporter l'historique avant",
    )
    p_reset.add_argument("--yes", action="store_true", help="Confirme la suppression (obligatoire)")

    p_convert = sub.add_parser(
        "convert-commentary", help="Convertit le classeur Excel de commentaire en data/seed/scenarios.yml"
    )
    p_convert.add_argument(
        "--xlsx", required=True, type=Path, help="Chemin vers le classeur banque_de_phrases_*.xlsx"
    )
    p_convert.add_argument(
        "--out", type=Path, default=DEFAULT_YAML_PATH, help="Chemin du scenarios.yml à écrire"
    )

    sub.add_parser("export-analytics", help="Exporte les tables d'usage SQLite vers DuckDB")

    p_select = sub.add_parser(
        "select", help="Sélectionne une phrase (échoue si la banque n'est pas importée)"
    )
    p_select.add_argument("--scenario", required=True)
    p_select.add_argument("--player-id", required=True, type=int)
    p_select.add_argument("--seed", default="0", help="Graine explicite du tirage (défaut : 0)")
    p_select.add_argument(
        "--match-sequence", required=True, type=int, help="Rang du match (unité du cooldown), obligatoire"
    )

    p_narrate = sub.add_parser(
        "narrate", help="Raconte un flux d'événements JSON Lines (contrat engine/event_contract.py)"
    )
    p_narrate.add_argument("--events", required=True, help="Fichier JSON Lines des événements, ou - pour stdin")
    p_narrate.add_argument("--dry-run", action="store_true", help="N'enregistre pas l'usage (phrase_history)")

    args = parser.parse_args(argv)
    handlers: dict[str, Callable[[argparse.Namespace], None]] = {
        "init-db": _cmd_init_db,
        "import-players": _cmd_import_players,
        "import-seed": _cmd_import_seed,
        "reset-seed": _cmd_reset_seed,
        "convert-commentary": _cmd_convert_commentary,
        "export-analytics": _cmd_export_analytics,
        "select": _cmd_select,
        "narrate": _cmd_narrate,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
