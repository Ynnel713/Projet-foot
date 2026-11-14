"""Graines réservées à la validation indépendante (ticket v2-realisme/18b, protocole validé par le propriétaire le
14/11/2026, `docs/INDICATEURS_V2.md` section 40).

Le banc joue le match d'indice `k` avec la graine `AUDIT_SEED + k` (`scripts/measure_v2.run`). Les indices de
`RESERVED_START` à `RESERVED_END` (exclu) ne servent jamais à calibrer : ils sont réservés à la série de validation du
ticket 18c, par blocs de `BLOCK_SIZE`, un bloc par passage, jamais réutilisé. Le banc refuse une série qui en touche un
sans l'option `--validation`, et refuse en mode validation une série qui en sort.
"""

from __future__ import annotations

RESERVED_START = 100_000  # premier indice réservé (graine 20 360 923) ; indices déjà utilisés : 0 à environ 2 120
BLOCK_SIZE = 2_000  # un passage de validation : 1 000 matchs, portés à 2 000 pour les indicateurs à confirmer
RESERVED_BLOCKS = 50  # 100 000 à 199 999 : de quoi refaire la validation après chaque correction
RESERVED_END = RESERVED_START + BLOCK_SIZE * RESERVED_BLOCKS


class ReservedSeedError(ValueError):
    """Série du banc incompatible avec la réserve des graines de validation."""


def seed_indices(start: int, n_matches: int, profile: bool = False) -> range:
    """Indices de graine joués par une série : avec un profil, chaque affiche est jouée deux fois (indice `i // 2`)."""
    if n_matches <= 0:
        return range(0)
    if profile:
        return range(start // 2, (start + n_matches - 1) // 2 + 1)
    return range(start, start + n_matches)


def is_reserved(index: int) -> bool:
    return RESERVED_START <= index < RESERVED_END


def check_series(start: int, n_matches: int, profile: bool = False, validation: bool = False) -> None:
    """Lève `ReservedSeedError` si la série touche la réserve hors validation, ou en sort en validation."""
    seeds = seed_indices(start, n_matches, profile)
    if not seeds:
        return
    touches = seeds.start < RESERVED_END and seeds.stop > RESERVED_START
    inside = seeds.start >= RESERVED_START and seeds.stop <= RESERVED_END
    if validation and not inside:
        raise ReservedSeedError(
            f"validation : graines {seeds.start} à {seeds.stop - 1} hors de la réserve "
            f"({RESERVED_START} à {RESERVED_END - 1}, ticket v2-realisme/18b)")
    if not validation and touches:
        raise ReservedSeedError(
            f"graines {seeds.start} à {seeds.stop - 1} : la plage {RESERVED_START} à {RESERVED_END - 1} est réservée "
            f"à la validation indépendante (ticket v2-realisme/18b) ; elle ne sert jamais à calibrer. "
            f"Option --validation pour la série du ticket 18c.")
