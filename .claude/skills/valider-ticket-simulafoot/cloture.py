"""Porte de clôture d'un ticket Simulafoot (skill valider-ticket-simulafoot). Bibliothèque standard seule.

  empreinte [--base REV] [FICHIER...]   empreinte sha256 du changement : révision de base + contenu actuel des
                                        fichiers du ticket. Sans fichier : tout le dépôt suivi et non ignoré
                                        (sert à prouver qu'une vérification n'a rien modifié).
  decision --ticket ID --rapport FICHIER [--qc VERDICT] --base REV FICHIER... [--reserves-acceptees]
                                        verdict de clôture VALIDÉ / REFUSÉ / BLOQUÉ, journalisé ici même (une ligne
                                        `<ID>/cloture` dans .claude/qc/journal.jsonl) ; code 0 si VALIDÉ. Le verdict
                                        QC est lu dans le journal (dernière entrée `<ID>`), --qc doit lui correspondre.
  verrou                                appelé par .claude/qc/verrou-commit.ps1 : code 0 seulement si la dernière
                                        entrée du journal est une clôture VALIDÉ encore vraie (voir `verrou`).
  --selftest                            vérifie la table de décision.

Seule écriture : l'ajout d'une ligne au journal par `decision`."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
JOURNAL = RACINE / ".claude" / "qc" / "journal.jsonl"
CHAMPS_JOURNAL = ("id", "sous_etape", "horodatage", "verdict", "justification")  # ceux qu'exige append.ps1
CHAMPS_CLOTURE = ("ticket", "base", "fichiers", "empreinte", "rapport", "rapport_sha256", "qc_id", "expert",
                  "reserves_acceptees")
# Fichiers qu'un commit de ticket peut contenir sans être dans FICHIERS : suivi documentaire mis à jour après la
# clôture (statut du ticket, plan, journal). Tout autre fichier indexé doit avoir été revu.
HORS_REVUE = ("docs/", ".scratch/", "Plan architecte Simulafoot.md", "PROJET_SIMULAFOOT.md", ".claude/qc/journal.jsonl")
VERDICTS_EXPERT = ("APPROVED", "APPROVED_WITH_RESERVATIONS", "REJECTED", "INCONCLUSIVE")
SECTIONS = ("Identification", "Analyse du réalisme", "Vérifications", "Anomalies", "Recommandation finale")
_QC = {"VALIDÉ": "VALIDÉ", "VALIDE": "VALIDÉ", "REFUSÉ": "REFUSÉ", "REFUSE": "REFUSÉ", "BLOQUÉ": "BLOQUÉ", "BLOQUE": "BLOQUÉ"}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def empreinte(base: str | None, fichiers: list[str]) -> str:
    h = hashlib.sha256()
    if base:
        h.update(f"base:{_git('rev-parse', base).strip()}\n".encode())
    if not fichiers:
        fichiers = [f for f in _git("ls-files", "-co", "--exclude-standard", "-z").split("\0") if f]
    for f in sorted(set(fichiers)):
        p = Path(f)
        h.update(f.replace("\\", "/").encode() + b"\0")
        h.update(p.read_bytes() if p.is_file() else b"<absent>")
        h.update(b"\0")
    return h.hexdigest()


def lire_rapport(texte: str, ticket: str, empreinte_attendue: str) -> tuple[str | None, list[str]]:
    """Verdict de l'expert et liste des défauts du rapport (vide si exploitable)."""
    defauts = []
    verdicts = re.findall(r"^Verdict\s*:\s*(\S+)\s*$", texte, re.M)
    verdicts = [v for v in verdicts if v in VERDICTS_EXPERT]
    if len(verdicts) != 1:
        defauts.append(f"{len(verdicts)} ligne(s) « Verdict : » valide(s), il en faut une")
    t = re.search(r"^Ticket\s*:\s*(.+?)\s*$", texte, re.M)
    if not t or t.group(1) != ticket:
        defauts.append(f"ticket du rapport « {t.group(1) if t else 'absent'} » ≠ « {ticket} »")
    e = re.search(r"^Empreinte\s*:\s*([0-9a-f]+)\s*$", texte, re.M)
    if not e or e.group(1) != empreinte_attendue:
        defauts.append("empreinte du rapport absente ou différente du changement actuel (code modifié depuis la revue ?)")
    for s in SECTIONS:
        if not re.search(rf"^##\s*{re.escape(s)}\b", texte, re.M):
            defauts.append(f"section « {s} » absente")
    if "DEMANDE DE VÉRIFICATIONS" in texte and not verdicts:
        defauts.append("vérifications demandées non traitées")
    return (verdicts[0] if len(verdicts) == 1 else None), defauts


def decider(expert: str | None, defauts: list[str], qc: str | None, reserves_acceptees: bool) -> tuple[str, str]:
    """Table de clôture : seul APPROVED (ou réserves acceptées par le propriétaire) + QC VALIDÉ donne VALIDÉ."""
    if expert == "REJECTED" or qc == "REFUSÉ":
        return "REFUSÉ", f"expert {expert or 'sans verdict'}, QC {qc or 'absent'}"
    if defauts:
        return "BLOQUÉ", "rapport expert inexploitable : " + " ; ".join(defauts)
    if qc is None:
        return "BLOQUÉ", "verdict du contrôle qualité absent"
    if expert == "INCONCLUSIVE" or qc == "BLOQUÉ":
        return "BLOQUÉ", f"expert {expert}, QC {qc}"
    if expert == "APPROVED_WITH_RESERVATIONS" and not reserves_acceptees:
        return "BLOQUÉ", "réserves de l'expert non acceptées explicitement par le propriétaire"
    return "VALIDÉ", f"expert {expert}{' (réserves acceptées par le propriétaire)' if expert != 'APPROVED' else ''}, QC VALIDÉ"


def lire_journal() -> list[dict]:
    """Entrées du journal ; ValueError à la moindre ligne illisible ou incomplète (même règle qu'append.ps1)."""
    if not JOURNAL.is_file():
        return []
    entrees = []
    for n, ligne in enumerate(JOURNAL.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not ligne.strip():
            continue
        try:
            e = json.loads(ligne)
        except json.JSONDecodeError as err:
            raise ValueError(f"ligne {n} illisible ({err})") from None
        if not isinstance(e, dict) or any(c not in e for c in CHAMPS_JOURNAL) or e["verdict"] not in _QC.values():
            raise ValueError(f"ligne {n} incomplète ou verdict invalide")
        entrees.append(e)
    return entrees


def qc_courant(entrees: list[dict], ticket: str) -> dict | None:
    """Dernière entrée du contrôle qualité (valider-etape, sous-étape = identifiant du ticket)."""
    return next((e for e in reversed(entrees) if e["sous_etape"] == ticket), None)


def _sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def journaliser(entree: dict) -> None:
    """Ajoute une ligne en une seule écriture : une interruption laisse au pire une ligne tronquée, que le verrou refuse."""
    prefixe = b""
    if JOURNAL.is_file() and JOURNAL.stat().st_size and not JOURNAL.read_bytes().endswith(b"\n"):
        prefixe = b"\r\n"
    with JOURNAL.open("ab") as f:
        f.write(prefixe + json.dumps(entree, ensure_ascii=False).encode("utf-8") + b"\r\n")


def _non_indexes(fichiers: list[str]) -> list[str]:
    """Fichiers revus dont l'arbre de travail diffère de l'index (modifiés, non suivis, supprimés hors index)."""
    jetons = _git("status", "--porcelain", "-z", "--untracked-files=all", "--", *fichiers).split("\0")
    sortie, i = [], 0
    while i < len(jetons):
        j = jetons[i]
        i += 1
        if len(j) < 4:
            continue
        if j[0] in "RC":
            i += 1  # chemin d'origine du renommage
        if j[1] != " ":
            sortie.append(j[3:])
    return sortie


def verrou() -> list[str]:
    """Raisons de refuser un commit (vide = autorisé). Ne fait confiance à aucun champ de l'entrée : tout est recalculé."""
    try:
        entrees = lire_journal()
    except ValueError as err:
        return [f"journal invalide : {err}"]
    if not entrees:
        return ["journal vide, aucune clôture"]
    c = entrees[-1]
    if not str(c["sous_etape"]).endswith("/cloture"):
        return [f"dernière entrée « {c['sous_etape']} » = {c['verdict']} : pas une clôture (une entrée QC seule ne vaut"
                " pas clôture)"]
    if c["verdict"] != "VALIDÉ":
        return [f"dernière clôture « {c['sous_etape']} » = {c['verdict']}"]
    manquants = [k for k in CHAMPS_CLOTURE if k not in c]
    if manquants:
        return [f"clôture sans les champs {', '.join(manquants)} (entrée ancienne ou écrite à la main)"]
    ticket, fichiers = c["ticket"], c["fichiers"]
    textes = ("ticket", "base", "empreinte", "rapport", "rapport_sha256", "qc_id", "expert")
    bien_formee = (all(isinstance(c[k], str) and c[k] for k in textes)
                   and c["sous_etape"] == f"{ticket}/cloture"
                   and isinstance(fichiers, list) and fichiers and all(isinstance(f, str) and f for f in fichiers)
                   and isinstance(c["reserves_acceptees"], bool))
    if not bien_formee:
        return ["clôture mal formée (champ vide, type inattendu ou ticket incohérent)"]
    ids = [e["id"] for e in entrees]
    if len(set(ids)) != len(ids):
        return ["identifiants dupliqués dans le journal, référence QC ambiguë"]
    raisons = []
    qc = qc_courant(entrees[:-1], ticket)
    if qc is None or qc["id"] != c["qc_id"] or qc["verdict"] != "VALIDÉ":
        raisons.append(f"la clôture ne cite pas le dernier contrôle qualité VALIDÉ de {ticket}")
    try:
        actuelle = empreinte(c["base"], fichiers)
    except (subprocess.CalledProcessError, OSError):
        return raisons + [f"empreinte impossible à recalculer (base {c['base']!r})"]
    if actuelle != c["empreinte"]:
        raisons.append("code modifié depuis la revue (empreinte différente)")
    rapport = Path(c["rapport"])
    if _sha256(rapport) != c["rapport_sha256"]:
        raisons.append(f"rapport de l'expert absent ou modifié depuis la clôture : {rapport}")
    else:
        expert, defauts = lire_rapport(rapport.read_text(encoding="utf-8"), ticket, actuelle)
        if expert != c["expert"]:
            raisons.append(f"verdict du rapport ({expert}) ≠ verdict journalisé ({c['expert']})")
        verdict, raison = decider(expert, defauts, "VALIDÉ", c["reserves_acceptees"])
        if verdict != "VALIDÉ":
            raisons.append(raison)
    hors = [f for f in _git("diff", "--cached", "--name-only", "-z").split("\0")
            if f and f not in fichiers and not f.startswith(HORS_REVUE)]
    if hors:
        raisons.append(f"fichiers indexés non revus : {', '.join(hors)}")
    non_indexes = _non_indexes(fichiers)
    if non_indexes:
        raisons.append(f"fichiers revus dont la version indexée n'est pas celle revue : {', '.join(non_indexes)}")
    return raisons


def _selftest() -> None:
    ok = []
    assert decider("APPROVED", ok, "VALIDÉ", False)[0] == "VALIDÉ"
    assert decider("REJECTED", ok, "VALIDÉ", False)[0] == "REFUSÉ"  # désaccord : expert refuse
    assert decider("APPROVED", ok, "REFUSÉ", False)[0] == "REFUSÉ"  # désaccord : QC refuse
    assert decider("APPROVED", ok, "BLOQUÉ", False)[0] == "BLOQUÉ"
    assert decider("INCONCLUSIVE", ok, "VALIDÉ", False)[0] == "BLOQUÉ"
    assert decider("APPROVED_WITH_RESERVATIONS", ok, "VALIDÉ", False)[0] == "BLOQUÉ"
    assert decider("APPROVED_WITH_RESERVATIONS", ok, "VALIDÉ", True)[0] == "VALIDÉ"
    assert decider("APPROVED", ok, None, False)[0] == "BLOQUÉ"
    assert decider(None, ["absent"], "VALIDÉ", True)[0] == "BLOQUÉ"  # rapport absent ≠ accord
    corps = "".join(f"## {s}\nx\n" for s in SECTIONS)
    bon = f"Ticket : c/01\nEmpreinte : ab12\nVerdict : APPROVED\n{corps}"
    assert lire_rapport(bon, "c/01", "ab12") == ("APPROVED", [])
    assert lire_rapport(bon, "c/02", "ab12")[1]  # mauvais ticket
    assert lire_rapport(bon, "c/01", "cd34")[1]  # code changé depuis la revue
    assert lire_rapport(bon.replace("## Anomalies", "## Autre"), "c/01", "ab12")[1]  # incomplet
    assert lire_rapport(bon + "Verdict : REJECTED\n", "c/01", "ab12")[0] is None  # deux verdicts
    assert lire_rapport("Ticket : c/01\nDEMANDE DE VÉRIFICATIONS\nV1 — ...", "c/01", "ab12")[0] is None
    print("selftest OK")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
        return 0
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("empreinte")
    pe.add_argument("--base")
    pe.add_argument("fichiers", nargs="*")
    pd = sub.add_parser("decision")
    pd.add_argument("--ticket", required=True)
    pd.add_argument("--rapport", required=True)
    pd.add_argument("--qc")
    pd.add_argument("--base", required=True)
    pd.add_argument("--reserves-acceptees", action="store_true")
    pd.add_argument("fichiers", nargs="+")
    sub.add_parser("verrou")
    a = parser.parse_args()
    if a.cmd == "empreinte":
        print(empreinte(a.base, a.fichiers))
        return 0
    if a.cmd == "verrou":
        os.chdir(RACINE)
        raisons = verrou()
        for r in raisons:
            print(f"REFUS:{r}")
        return 1 if raisons else 0
    try:
        entrees = lire_journal()
    except ValueError as err:
        print(f"CLOTURE:BLOQUÉ\nRAISON:journal invalide, rien n'est journalisé : {err}")
        return 1
    rapport = Path(a.rapport).resolve()
    texte = rapport.read_text(encoding="utf-8") if rapport.is_file() else ""
    emp = empreinte(a.base, a.fichiers)
    expert, defauts = lire_rapport(texte, a.ticket, emp)
    if not texte:
        defauts.insert(0, f"rapport introuvable ou vide : {a.rapport}")
    qc = qc_courant(entrees, a.ticket)
    qc_verdict = qc["verdict"] if qc else None
    if a.qc and _QC.get(a.qc.upper()) != qc_verdict:
        defauts.append(f"verdict QC annoncé {a.qc} ≠ dernier verdict journalisé {qc_verdict or 'absent'}")
    verdict, raison = decider(expert, defauts, qc_verdict, a.reserves_acceptees)
    journaliser({
        "id": str(uuid.uuid4()), "sous_etape": f"{a.ticket}/cloture",
        "horodatage": datetime.now(timezone.utc).isoformat(), "verdict": verdict,
        "justification": f"expert {expert or 'sans verdict'} (empreinte {emp[:8]}) ; QC {qc_verdict or 'absent'} ; {raison}",
        "ticket": a.ticket, "base": _git("rev-parse", a.base).strip(), "fichiers": sorted(set(a.fichiers)),
        "empreinte": emp, "rapport": str(rapport), "rapport_sha256": _sha256(rapport) or "",
        "qc_id": qc["id"] if qc else "", "expert": expert or "", "reserves_acceptees": a.reserves_acceptees,
    })
    print(f"CLOTURE:{verdict}")
    print(f"RAISON:{raison}")
    return 0 if verdict == "VALIDÉ" else 1


if __name__ == "__main__":
    sys.exit(main())
