"""Tests de l'analyse des estimations (ticket v2-realisme/01g) : registre factice aux ratios connus,
puis lecture du registre réel."""

from __future__ import annotations

import hashlib
import math

import pytest

from scripts import analyse_estimations as ae

_EN_TETE = """# Registre factice

| Date de clôture | Ticket | Catégorie | Estimé (min) | Réel (min) | Écart | Postes estimés | Postes réels | Confiance annoncée | Cause de l'écart |
|---|---|---|---|---|---|---|---|---|---|
"""


def _ligne(ticket: str, cat: str, est: int | str, reel: int | str, p_est: str = "—", p_reel: str = "—",
           cause: str = "durée réelle estimée, non chronométrée") -> str:
    return f"| 01/11/2026 | {ticket} | {cat} | {est} | {reel} | x | {p_est} | {p_reel} | moyenne | {cause} |\n"


# Catégorie « mesure » : ratios 0,5 / 1,0 / 1,5 / 2,0 → médiane 1,25, Q1 0,875, Q3 1,625, 3 sur 4 au-delà de 30 %.
_FACTICE = _EN_TETE + "".join([
    _ligne("t/1", "mesure", 100, 150, "10/20/30/40", "20/20/30/30"),
    _ligne("t/2", "mesure", 100, 100, "10/20/30/40 (+25 réserves)", "10/40/30/20"),
    _ligne("t/3", "mesure", 100, 50),
    _ligne("t/4", "mesure", 100, 200, "0/10/10/10", "5/10/10/10", cause="chronométré"),
    _ligne("t/5", "Données", 80, 60),
    _ligne("t/6", "mesure", "~90", 100),
    "| 02/11/2026 | t/7 | mesure | 90 |\n",
])


@pytest.fixture
def factice() -> tuple[list[ae.Ligne], list[tuple[int, str]]]:
    return ae.lire_registre(_FACTICE)


def test_lecture_lignes_et_rejets(factice) -> None:
    lignes, rejets = factice
    assert [l.ticket for l in lignes] == ["t/1", "t/2", "t/3", "t/4", "t/5"]
    assert [motif.split(" ")[0] for _, motif in rejets] == ["durées", "4"]  # durée illisible, colonnes manquantes
    assert lignes[1].postes_estimes == (10, 20, 30, 40)  # suffixe « (+25 réserves) » toléré
    assert lignes[2].postes_estimes is None and lignes[4].categorie == "données"
    assert [l.chronometre for l in lignes] == [False, False, False, True, False]


def test_ratios_mediane_et_quartiles_exacts(factice) -> None:
    lignes, _ = factice
    d = ae.dispersion([l.ratio for l in lignes if l.categorie == "mesure"])
    assert (d.n, d.minimum, d.maximum) == (4, 0.5, 2.0)
    assert math.isclose(d.mediane, 1.25, abs_tol=1e-9)
    assert math.isclose(d.q1, 0.875, abs_tol=1e-9) and math.isclose(d.q3, 1.625, abs_tol=1e-9)
    assert math.isclose(d.part_hors_seuil, 0.75, abs_tol=1e-9)


def test_seuil_de_30_pourcent_non_franchi_a_la_limite() -> None:
    d = ae.dispersion([1.3, 0.7])
    assert d.part_hors_seuil == 0.0 and math.isclose(d.mediane, 1.0)
    assert math.isclose(d.q1, 0.85) and math.isclose(d.q3, 1.15)
    seul = ae.dispersion([1.4])
    assert (seul.q1, seul.mediane, seul.q3, seul.part_hors_seuil) == (1.4, 1.4, 1.4, 1.0)


def test_postes_classes_du_plus_sous_estime(factice) -> None:
    lignes, _ = factice
    postes = ae.postes_par_ecart([l for l in lignes if l.categorie == "mesure"])
    # sommes : analyse 35/20, développement 70/50, tests 70/70, intégration 60/90 (ligne sans postes écartée)
    assert [(p.nom, p.reel, p.estime) for p in postes] == [
        ("analyse", 35, 20), ("développement", 70, 50), ("tests", 70, 70), ("intégration", 60, 90)]
    assert math.isclose(postes[0].ratio, 1.75) and math.isclose(postes[-1].ratio, 2 / 3)


def test_poste_non_prevu_sans_division_par_zero() -> None:
    lignes, _ = ae.lire_registre(_EN_TETE + _ligne("t/8", "documentation", 60, 70, "30/30/0/0", "30/30/10/0"))
    postes = ae.postes_par_ecart(lignes)
    assert postes[0].nom == "tests" and math.isinf(postes[0].ratio)
    assert "intégration" not in [p.nom for p in postes]  # 0 estimé, 0 réel : écarté


def test_coefficient_brut_arrondi_et_seuil_d_effectif(factice) -> None:
    lignes, _ = factice
    d = ae.dispersion([l.ratio for l in lignes if l.categorie == "mesure"])
    assert ae.coefficient_brut(d, min_n=5) is None
    assert ae.coefficient_brut(d, min_n=4) == 1.25
    assert ae.coefficient_brut(ae.dispersion([31 / 30]), min_n=1) == 1.05
    assert ae.coefficient_brut(ae.dispersion([1.024]), min_n=1) == 1.0


def test_rapport_affiche_toutes_les_categories_du_ticket(factice) -> None:
    lignes, rejets = factice
    texte = ae.rapport(lignes, rejets, min_n=4)
    for categorie in ae.CATEGORIES_TICKET:
        assert f"| {categorie} |" in texte
    assert "| perception | 0 | — |" in texte
    # 0,875 et 1,625 sont exacts en binaire : l'affichage à 2 décimales arrondit au pair (0,88 et 1,62)
    assert "| mesure | 4 | 1,25 | 0,88 – 1,62 | 0,50 – 2,00 | 75 % | 1,25 |" in texte
    assert "| données | 1 |" in texte and "| toutes | 5 |" in texte
    assert "rejetées : 2" in texte and "« non chronométrée » : 1" in texte


def test_registre_reel_lu_sans_rejet_et_sortie_deterministe() -> None:
    texte = ae.REGISTRE.read_text(encoding="utf-8")
    lignes, rejets = ae.lire_registre(texte)
    assert rejets == [] and len(lignes) >= 20
    empreintes = {hashlib.sha256(ae.rapport(*ae.lire_registre(texte)).encode()).hexdigest() for _ in range(2)}
    assert len(empreintes) == 1
