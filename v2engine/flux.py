"""Flux aléatoires par sous-système (ticket v2-realisme/01a, décision D-V13).

Un générateur `random.Random` par sous-système, tous dérivés de la même base par sha256 de « base|nom » (clé stable,
jamais `hash()`). Ajouter ou retirer un tirage dans un flux ne décale plus les tirages des autres : un écart entre deux
profils devient attribuable au sous-système qui a changé.

`simulate_match` sème les flux au coup d'envoi avec une base tirée du module `random` : une graine posée par
`random.seed` reste la seule graine d'un match (D-V06 inchangée, déterminisme à graine fixée).

Flux (01a puis 01b) : perception (ce que le joueur voit ou lit, drapeau de hors-jeu compris) ; décision (ce qu'il
choisit, dont l'espace d'un appel et le partenaire d'une remise en jeu) ; duel (tentative, issue et faute du tacle, perte de balle en conduite) ;
passe (contrôle, précision et dosage) ; tir (déclenchement, contre, arrêt, déviation, non cadré, penalty) ; placement
(erreur de Positioning, appel en profondeur) ; défense (rôles défensifs, suivi, compensation, défenseur d'équilibre) ;
arbitrage (gravité d'une faute, tirage au sort du coup d'envoi). Plus aucun tirage du moteur dans le module `random`
hors la base du match (test de garde : `tests/test_v2engine_flux.py`).

Les objets ne sont jamais remplacés (`seed_streams` les ressème) : `from v2engine.flux import PERCEPTION` reste
valable, et un test peut remplacer un tirage par `monkeypatch.setattr("v2engine.flux.PERCEPTION.random", ...)`.
"""

from __future__ import annotations

import hashlib
import random

PERCEPTION = random.Random()
DECISION = random.Random()
DUEL = random.Random()
PASSE = random.Random()
TIR = random.Random()
PLACEMENT = random.Random()
DEFENSE = random.Random()
ARBITRAGE = random.Random()
STREAMS = {"perception": PERCEPTION, "decision": DECISION, "duel": DUEL, "passe": PASSE, "tir": TIR,
           "placement": PLACEMENT, "defense": DEFENSE, "arbitrage": ARBITRAGE}


def stream_seed(base: int, name: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{base}|{name}".encode()).digest()[:8], "big")


def seed_streams(base: int) -> None:
    for name, rng in STREAMS.items():
        rng.seed(stream_seed(base, name))


seed_streams(0)
