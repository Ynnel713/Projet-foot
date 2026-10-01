"""pilotes_v2/*.py -> data/seed/v2/<module>.yml (un YAML par pilote, decision D4).

Meme forme que le pipeline v1 (classeur -> scenarios.yml) : chaque module expose
`DEFAUT` (et parfois `SURNOM`), listes de (texte, [(attribut, operateur, valeur)]) ;
`PILOTES_METADATA` (scripts/convert_commentary_xlsx_to_yaml.py) porte le libelle, le
cooldown et les slots autorises. Pas d'import direct des modules en base : le YAML
reste l'unique entree de scripts/import_seed.py (une seule source de verite, SPEC
section 6, note A2).

Reutilise le convertisseur v1 : valider_slots (slot autorise pour le scenario),
_slots_for_phrase (expression de chaque slot), verifier_move_canonique
(preferred_moves dans le reservoir) et _group_variants (DEFAUT/SURNOM, libelles).

Ecrit UNIQUEMENT les fichiers <module>.yml du dossier de sortie : ne supprime rien et
ne touche jamais data/seed/fallback/ (fichiers ecrits a la main)."""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.convert_commentary_xlsx_to_yaml import (  # noqa: E402
    PILOTES_METADATA,
    CommentaryConversionError,
    _group_variants,
    _slots_for_phrase,
    valider_slots,
    verifier_move_canonique,
)

logger = logging.getLogger(__name__)

DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "seed" / "v2"


def _module_pilote(nom: str) -> ModuleType:
    return importlib.import_module(f"pilotes_v2.{nom}")


def _lignes(module: ModuleType, nom: str, code: str) -> list[dict[str, Any]]:
    """Lignes (meme forme que le chemin classeur) d'un module : DEFAUT d'abord
    (variante vide), puis SURNOM s'il existe."""
    cooldown = PILOTES_METADATA[code].cooldown_matches
    lignes: list[dict[str, Any]] = []
    for variante, phrases in (("", module.DEFAUT), ("SURNOM", getattr(module, "SURNOM", []))):
        for rang, (texte, conditions) in enumerate(phrases, 1):
            origine = f"pilotes_v2/{nom}.py, {variante or 'DEFAUT'} n°{rang}"
            try:
                valider_slots(texte, code, rang)
                for attribut, _, valeur in conditions:
                    verifier_move_canonique(attribut, valeur, origine)
            except CommentaryConversionError as exc:
                raise CommentaryConversionError(f"{origine} : {exc}") from exc
            lignes.append(
                {
                    "phrase": texte,
                    "variant": variante or None,
                    "weight": 1.0,
                    "cooldown_matches": cooldown,
                    "conditions": [
                        {"attribute": a, "operator": o, "value": v, "mandatory": True}
                        for a, o, v in conditions
                    ],
                    "slots": _slots_for_phrase(texte),
                }
            )
    return lignes


def convertir_pilote(nom: str) -> list[dict[str, Any]]:
    """Le YAML (liste d'UN scenario) du module pilotes_v2/<nom>.py."""
    code = nom.upper()
    if code not in PILOTES_METADATA:
        raise CommentaryConversionError(
            f"pilotes_v2/{nom}.py : aucune entree {code!r} dans PILOTES_METADATA "
            f"(connues : {sorted(PILOTES_METADATA)})."
        )
    lignes = _lignes(_module_pilote(nom), nom, code)
    return [{"code": code, "label": PILOTES_METADATA[code].label, "variants": _group_variants(lignes)}]


def convertir_pilotes(out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, int]:
    """Ecrit out_dir/<module>.yml pour chacun des pilotes de PILOTES_METADATA.
    Retourne le nombre de phrases ecrites par code de scenario."""
    out_dir.mkdir(parents=True, exist_ok=True)
    nombres: dict[str, int] = {}
    for code in PILOTES_METADATA:
        nom = code.lower()
        scenarios = convertir_pilote(nom)
        (out_dir / f"{nom}.yml").write_text(
            yaml.safe_dump(scenarios, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        nombres[code] = sum(len(v["phrases"]) for v in scenarios[0]["variants"])
    logger.info("%d pilotes, %d phrases écrits dans %s", len(nombres), sum(nombres.values()), out_dir)
    return nombres


def main(argv: list[str] | None = None) -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    convertir_pilotes(args.out)


if __name__ == "__main__":
    main()
