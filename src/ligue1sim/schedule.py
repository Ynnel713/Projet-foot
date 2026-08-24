"""Génération du calendrier d'une saison (round-robin, 1/2/4 manches)."""

from __future__ import annotations

from dataclasses import dataclass, field

from ligue1sim.clubs import Club

_BYE = "__BYE__"


@dataclass
class Match:
    home: str
    away: str
    home_goals: int | None = None
    away_goals: int | None = None
    events: "MatchEvents | None" = None

    @property
    def played(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


@dataclass
class Journee:
    number: int
    matches: list[Match] = field(default_factory=list)

    @property
    def played(self) -> bool:
        return all(m.played for m in self.matches)


def generate_calendar(clubs: list[Club], legs: int = 2) -> list[Journee]:
    """Génère un calendrier round-robin pour n'importe quel nombre de clubs.

    `legs` fixe le nombre de manches entre chaque paire de clubs :
    1 = aller simple, 2 = aller-retour (défaut), 4 = double aller-retour.
    Chaque manche paire est le miroir (domicile/extérieur inversés) de la
    manche impaire précédente.

    Pour n clubs pairs, un round-robin simple donne (n-1) journées de n/2
    matchs (ex. 18 clubs → 17 journées de 9 matchs par manche). Un effectif
    **impair** est géré comme un vrai calendrier : une équipe "exemptée"
    (bye) par journée, donc n journées de (n-1)/2 matchs par manche.
    """
    if legs not in (1, 2, 4):
        raise ValueError("legs doit valoir 1, 2 ou 4 (aller simple, aller-retour, double aller-retour).")
    if len(clubs) < 2:
        raise ValueError("Il faut au moins 2 clubs pour générer un calendrier.")

    real_names = {c.name for c in clubs}
    names = [c.name for c in clubs]
    if len(names) % 2 != 0:
        names.append(_BYE)

    base_rounds = _round_robin_rounds(names)
    mirrored_rounds = [[(away, home) for home, away in pairs] for pairs in base_rounds]
    leg_sequence = [base_rounds if i % 2 == 0 else mirrored_rounds for i in range(legs)]

    calendar: list[Journee] = []
    number = 1
    for rounds in leg_sequence:
        for pairs in rounds:
            matches = [
                Match(home, away) for home, away in pairs if home in real_names and away in real_names
            ]
            calendar.append(Journee(number, matches))
            number += 1

    return calendar


def _round_robin_rounds(names: list[str]) -> list[list[tuple[str, str]]]:
    """Méthode du cercle : produit n-1 journées où chaque équipe rencontre
    chaque autre exactement une fois."""
    teams = list(names)
    n = len(teams)
    rounds: list[list[tuple[str, str]]] = []

    for round_num in range(n - 1):
        pairs = []
        for i in range(n // 2):
            team_a, team_b = teams[i], teams[n - 1 - i]
            pairs.append((team_a, team_b) if round_num % 2 == 0 else (team_b, team_a))
        rounds.append(pairs)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    return rounds
