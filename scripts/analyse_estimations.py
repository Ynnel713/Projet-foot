"""Analyse des écarts entre durées estimées et réelles (ticket v2-realisme/01g).

Lit le registre `docs/agents/suivi-estimations.md` et donne, par catégorie de ticket :
- le rapport réel / estimé médian, sa dispersion (quartiles, extrêmes, part des écarts au-delà de 30 %) ;
- les postes (analyse, développement, tests, intégration) les plus sous-estimés, par rapport des sommes
  réel / estimé du poste ;
- un coefficient brut (médiane arrondie à 0,05), proposé au propriétaire et appliqué nulle part.

Usage : uv run python -m scripts.analyse_estimations [chemin_du_registre] [--min-n 5]

`--min-n` : nombre minimal de lignes d'une catégorie pour afficher un coefficient brut (en dessous : « — »).
Sortie déterministe (aucun aléa, aucune horloge) : deux exécutions sur le même registre donnent le même texte."""

from __future__ import annotations

import math
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

REGISTRE = Path(__file__).resolve().parent.parent / "docs" / "agents" / "suivi-estimations.md"

# Catégories listées par le ticket 01g, affichées même sans ligne (n = 0) ; les autres suivent par ordre alphabétique.
CATEGORIES_TICKET = ("mesure", "placement", "décision", "exécution", "physique", "perception", "validation",
                     "documentation")
POSTES = ("analyse", "développement", "tests", "intégration")
SEUIL_ECART = 0.30  # seuil du registre : cause obligatoire au-delà de 30 %
PAS_COEFFICIENT = 0.05

_DATE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_POSTES = re.compile(r"^(\d+)/(\d+)/(\d+)/(\d+)")


@dataclass(frozen=True)
class Ligne:
    date: str
    ticket: str
    categorie: str
    estime: int
    reel: int
    postes_estimes: tuple[int, int, int, int] | None
    postes_reels: tuple[int, int, int, int] | None
    chronometre: bool

    @property
    def ratio(self) -> float:
        return self.reel / self.estime


@dataclass(frozen=True)
class Dispersion:
    n: int
    mediane: float
    q1: float
    q3: float
    minimum: float
    maximum: float
    part_hors_seuil: float  # part des lignes dont |réel/estimé − 1| > 30 %


@dataclass(frozen=True)
class Poste:
    nom: str
    estime: int
    reel: int

    @property
    def ratio(self) -> float:
        """Réel / estimé ; infini si le poste n'était pas prévu (estimé 0) mais a coûté du temps."""
        return self.reel / self.estime if self.estime else math.inf


def _postes(cellule: str) -> tuple[int, int, int, int] | None:
    m = _POSTES.match(cellule.strip())
    return tuple(int(g) for g in m.groups()) if m else None  # type: ignore[return-value]


def lire_registre(texte: str) -> tuple[list[Ligne], list[tuple[int, str]]]:
    """Lignes du tableau du registre, et rejets (numéro de ligne, motif) pour celles qui ne se lisent pas."""
    lignes: list[Ligne] = []
    rejets: list[tuple[int, str]] = []
    for numero, brute in enumerate(texte.splitlines(), start=1):
        if not brute.startswith("|"):
            continue
        cellules = [c.strip() for c in brute.strip().strip("|").split("|")]
        if not cellules or not _DATE.match(cellules[0]):
            continue  # en-tête, séparateur ou tableau d'un autre format
        if len(cellules) < 10:
            rejets.append((numero, f"{len(cellules)} colonnes au lieu de 10"))
            continue
        date, ticket, categorie, estime, reel, _ecart, p_est, p_reel, _confiance, cause = cellules[:10]
        try:
            estime_min, reel_min = int(estime), int(reel)
        except ValueError:
            rejets.append((numero, f"durées illisibles ({estime!r}, {reel!r})"))
            continue
        if estime_min <= 0:
            rejets.append((numero, "durée estimée nulle"))
            continue
        lignes.append(Ligne(date, ticket, categorie.lower(), estime_min, reel_min, _postes(p_est), _postes(p_reel),
                            chronometre="non chronométrée" not in cause))
    return lignes, rejets


def dispersion(ratios: list[float]) -> Dispersion:
    if not ratios:
        raise ValueError("aucun ratio")
    ordonnes = sorted(ratios)
    if len(ordonnes) == 1:
        q1 = q3 = ordonnes[0]
    else:
        q1, _, q3 = statistics.quantiles(ordonnes, n=4, method="inclusive")
    hors = sum(1 for r in ordonnes if abs(r - 1) > SEUIL_ECART + 1e-12)
    return Dispersion(len(ordonnes), statistics.median(ordonnes), q1, q3, ordonnes[0], ordonnes[-1],
                      hors / len(ordonnes))


def postes_par_ecart(lignes: list[Ligne]) -> list[Poste]:
    """Postes classés du plus sous-estimé au moins sous-estimé (lignes dont les deux répartitions sont connues ;
    un poste à 0 estimé et 0 réel est écarté)."""
    estimes = [0, 0, 0, 0]
    reels = [0, 0, 0, 0]
    for ligne in lignes:
        if ligne.postes_estimes is None or ligne.postes_reels is None:
            continue
        for i in range(4):
            estimes[i] += ligne.postes_estimes[i]
            reels[i] += ligne.postes_reels[i]
    postes = [Poste(POSTES[i], estimes[i], reels[i]) for i in range(4) if estimes[i] or reels[i]]
    return sorted(postes, key=lambda p: (-p.ratio, POSTES.index(p.nom)))


def coefficient_brut(d: Dispersion | None, min_n: int) -> float | None:
    """Médiane arrondie au pas de 0,05 (arrondi au plus proche, demi vers le haut) ; None sous `min_n` lignes."""
    if d is None or d.n < min_n:
        return None
    return round(math.floor(d.mediane / PAS_COEFFICIENT + 0.5) * PAS_COEFFICIENT, 2)


def categories(lignes: list[Ligne]) -> list[str]:
    autres = sorted({l.categorie for l in lignes} - set(CATEGORIES_TICKET))
    return [*CATEGORIES_TICKET, *autres]


def _f(x: float) -> str:
    return "∞" if math.isinf(x) else f"{x:.2f}".replace(".", ",")


def _pct(x: float) -> str:
    return f"{round(x * 100)} %"


def rapport(lignes: list[Ligne], rejets: list[tuple[int, str]], min_n: int = 5) -> str:
    sortie = [
        "# Analyse des estimations (ticket v2-realisme/01g)",
        "",
        f"Lignes lues : {len(lignes)} ; rejetées : {len(rejets)} ; "
        f"avec postes détaillés : {sum(1 for l in lignes if l.postes_estimes and l.postes_reels)} ; "
        f"sans la mention « non chronométrée » : {sum(1 for l in lignes if l.chronometre)}.",
    ]
    for numero, motif in rejets:
        sortie.append(f"- rejet ligne {numero} : {motif}")
    sortie += [
        "",
        f"Coefficient brut : médiane réel / estimé arrondie à {_f(PAS_COEFFICIENT)}, affiché à partir de {min_n} "
        "lignes. Proposition au propriétaire, appliquée nulle part.",
        "",
        "## Rapport réel / estimé par catégorie",
        "",
        "| Catégorie | n | Médiane | Q1 – Q3 | Min – max | Écart > 30 % | Coefficient brut |",
        "|---|---|---|---|---|---|---|",
    ]
    groupes = [(c, [l for l in lignes if l.categorie == c]) for c in categories(lignes)]
    groupes.append(("toutes", lignes))
    for nom, groupe in groupes:
        if not groupe:
            sortie.append(f"| {nom} | 0 | — | — | — | — | — |")
            continue
        d = dispersion([l.ratio for l in groupe])
        coef = coefficient_brut(d, min_n)
        sortie.append(f"| {nom} | {d.n} | {_f(d.mediane)} | {_f(d.q1)} – {_f(d.q3)} | "
                      f"{_f(d.minimum)} – {_f(d.maximum)} | {_pct(d.part_hors_seuil)} | "
                      f"{'—' if coef is None else _f(coef)} |")
    sortie += [
        "",
        "## Postes, du plus au moins sous-estimé (réel / estimé, sommes de la catégorie)",
        "",
        "| Catégorie | n (postes détaillés) | Postes |",
        "|---|---|---|",
    ]
    for nom, groupe in groupes:
        detailles = [l for l in groupe if l.postes_estimes and l.postes_reels]
        if not detailles:
            continue
        postes = ", ".join(f"{p.nom} {_f(p.ratio)} ({p.reel}/{p.estime} min)" for p in postes_par_ecart(detailles))
        sortie.append(f"| {nom} | {len(detailles)} | {postes} |")
    return "\n".join(sortie) + "\n"


def main(argv: list[str]) -> int:
    chemin = REGISTRE
    min_n = 5
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--min-n":
            min_n = int(args.pop(0))
        else:
            chemin = Path(arg)
    lignes, rejets = lire_registre(chemin.read_text(encoding="utf-8"))
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stdout.write(rapport(lignes, rejets, min_n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
