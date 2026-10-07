"""Ligue des Champions au VRAI format (depuis 2024-25) : PHASE DE LIGUE à 36 clubs, classement unique ; 8 premiers qualifiés directement
pour les 8es de finale, 9e-24e en BARRAGES (aller-retour), 25e-36e éliminés ; puis 8es, quarts et demies en aller-retour, finale sur un
seul match.

- 36 clubs en 4 chapeaux de 9 (onglet « Ligue des Champions » de data/joueurs.xlsx). Chaque club joue 8 matchs de phase de ligue, contre
  2 adversaires de CHAQUE chapeau (le sien compris), un à domicile et un à l'extérieur : 144 matchs, 8 journées de 18 matchs.
- Le tirage évite que deux clubs d'un même championnat se rencontrent en phase de ligue (comme le vrai tirage, qui limite aussi les
  adversaires d'une même association : ici zéro rencontre, par recherche locale -- voir `_minimise_conflicts`).
- Barrages : 9/10 contre 23/24, 11/12 contre 21/22, 13/14 contre 19/20, 15/16 contre 17/18 ; le mieux classé reçoit le match RETOUR.
- 8es de finale : chaque tête de série 1-8 rencontre un vainqueur de barrages (1-2 contre ceux des 15e-18e, ..., 7-8 contre ceux des
  9e-10e/23e-24e), tirage au sort au sein de chaque paire de têtes de série ; le tableau est ensuite figé (1 et 2 sur deux moitiés).
- Pas de séance de tirs au but pour les matchs de phase de ligue (nuls possibles) ; égalité d'une confrontation : mêmes règles que le reste
  du moteur (voir knockout._resolve_tiebreak).

Réutilise le moteur de la Compétition Perso (`CustomCompetition` HYBRID) : la phase de ligue est UN seul `Group` de 36 clubs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ligue1sim.clubs import Club, load_all_clubs
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.groups import Group
from ligue1sim.knockout import Bracket, Round, Tie, _seed_order
from ligue1sim.schedule import Journee, Match

CL_SHEET = "Ligue des Champions"
CL_HEADER_ROW = 14
NB_CLUBS = 36
NB_POTS = 4
POT_SIZE = 9
LEAGUE_PHASE_MATCHDAYS = 8
DIRECT_SPOTS = 8  # 1er-8e : 8es de finale directement
PLAYOFF_SPOTS = 16  # 9e-24e : barrages
LEAGUE_PHASE_NAME = "Phase de ligue"

POT_COLUMN = "Chapeau"
# Colonne à utiliser pour charger les effectifs : elle correspond exactement
# à la colonne "Club" de "Infos principales" (vérifié), contrairement à
# "Club" (nom d'affichage usuel, différent pour certains clubs -- ex. "FC
# Bruges" vs "Club Brugge KV").
CLUB_ROSTER_COLUMN = "Club (base joueurs)"


def _read_pots(path: str) -> dict[int, list[str]]:
    """{numéro de chapeau (1-4) : noms de club (colonne CLUB_ROSTER_COLUMN)}."""
    df = pd.read_excel(path, sheet_name=CL_SHEET, header=CL_HEADER_ROW, nrows=NB_CLUBS)
    return {int(pot): group[CLUB_ROSTER_COLUMN].tolist() for pot, group in df.groupby(POT_COLUMN)}


def load_champions_league_clubs(path: str) -> list[Club]:
    """Effectifs complets des 36 clubs qualifiés, chargés depuis le vivier
    complet (voir `clubs.load_all_clubs`)."""
    pots = _read_pots(path)
    names = {name for pot_clubs in pots.values() for name in pot_clubs}
    options = {o.name: o for o in load_all_clubs(path) if o.name in names}
    missing = names - options.keys()
    if missing:
        raise ValueError(f"Clubs de la Ligue des Champions introuvables dans le vivier : {sorted(missing)}")
    return [options[name].as_club() for name in names]


def _fixtures(pots: list[list[str]]) -> list[tuple[str, str]]:
    """144 matchs (domicile, extérieur) : dans un chapeau, i reçoit i+1 (cycle de 9) ; entre deux chapeaux p < q, p_i reçoit q_i et q_(i+1)
    reçoit p_i -- chaque club joue ainsi 2 adversaires de chaque chapeau, un à domicile, un à l'extérieur."""
    fixtures: list[tuple[str, str]] = []
    for p, pot in enumerate(pots):
        for i in range(POT_SIZE):
            fixtures.append((pot[i], pot[(i + 1) % POT_SIZE]))
        for q in range(p + 1, NB_POTS):
            for i in range(POT_SIZE):
                fixtures.append((pot[i], pots[q][i]))
                fixtures.append((pots[q][(i + 1) % POT_SIZE], pot[i]))
    return fixtures


def _edge_matchdays() -> list[int]:
    """Journée (0-7) de chacune des 144 rencontres de `_fixtures`, dans le MÊME ordre, telle que chaque club joue exactement une fois par
    journée (coloriage d'arêtes à 8 couleurs du graphe des adversaires). Le graphe est symétrique : il ne dépend que des positions dans les
    chapeaux, pas des clubs ; le coloriage est donc calculé une fois (recherche en profondeur déterministe) puis appliqué à tout tirage."""
    edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for p in range(NB_POTS):
        for i in range(POT_SIZE):
            edges.append(((p, i), (p, (i + 1) % POT_SIZE)))
        for q in range(p + 1, NB_POTS):
            for i in range(POT_SIZE):
                edges.append(((p, i), (q, i)))
                edges.append(((q, (i + 1) % POT_SIZE), (p, i)))
    colors: list[int | None] = [None] * len(edges)
    used: dict[tuple[int, int], set[int]] = {}
    for u, v in edges:
        used.setdefault(u, set())
        used.setdefault(v, set())

    def domain(index: int) -> list[int]:
        u, v = edges[index]
        return [c for c in range(LEAGUE_PHASE_MATCHDAYS) if c not in used[u] and c not in used[v]]

    def solve() -> bool:
        choice, options = None, None
        for index in range(len(edges)):
            if colors[index] is None:
                d = domain(index)
                if options is None or len(d) < len(options):
                    choice, options = index, d
                    if len(d) <= 1:
                        break
        if choice is None:
            return True
        u, v = edges[choice]
        for c in options:
            colors[choice] = c
            used[u].add(c)
            used[v].add(c)
            if solve():
                return True
            colors[choice] = None
            used[u].discard(c)
            used[v].discard(c)
        return False

    if not solve():  # pragma: no cover -- la recherche aboutit sans retour arrière sur ce graphe
        raise RuntimeError("Aucun calendrier de phase de ligue à 8 journées trouvé.")
    return [c for c in colors if c is not None]


def _championnats(path: str) -> dict[str, str]:
    return {o.name: o.championnat for o in load_all_clubs(path)}


def _count_conflicts(pots: list[list[str]], championnat: dict[str, str]) -> int:
    """Rencontres entre deux clubs du même championnat (« Autres clubs » ne compte pas : ce n'est pas un pays)."""
    return sum(
        1
        for home, away in _fixtures(pots)
        if championnat.get(home) == championnat.get(away) and championnat.get(home) not in (None, "Autres clubs")
    )


def _minimise_conflicts(pots: list[list[str]], championnat: dict[str, str], max_swaps: int = 4000) -> list[list[str]]:
    """Recherche locale : échange deux clubs d'un même chapeau quand cela réduit le nombre de rencontres entre clubs d'un même championnat,
    jusqu'à zéro (ou `max_swaps` essais). Aucun échange entre chapeaux : chaque club reste dans son chapeau (chapeaux = niveau)."""
    best = _count_conflicts(pots, championnat)
    for _ in range(max_swaps):
        if best == 0:
            break
        pot = int(np.random.randint(NB_POTS))
        i, j = np.random.choice(POT_SIZE, size=2, replace=False)
        pots[pot][i], pots[pot][j] = pots[pot][j], pots[pot][i]
        score = _count_conflicts(pots, championnat)
        if score <= best:
            best = score
        else:
            pots[pot][i], pots[pot][j] = pots[pot][j], pots[pot][i]
    return pots


def draw_league_phase(path: str) -> Group:
    """Tirage de la phase de ligue : un seul `Group` de 36 clubs, 8 journées de 18 matchs. Les chapeaux sont mélangés (tirage au sort),
    puis ajustés pour qu'aucun club n'en rencontre un du même championnat."""
    pots_by_number = _read_pots(path)
    pots = [list(pots_by_number[n]) for n in sorted(pots_by_number)]
    for pot in pots:
        np.random.shuffle(pot)
    pots = _minimise_conflicts(pots, _championnats(path))

    clubs_by_name = {o.name: o.as_club() for o in load_all_clubs(path)}
    fixtures = _fixtures(pots)
    journees = [Journee(number=d + 1, matches=[]) for d in range(LEAGUE_PHASE_MATCHDAYS)]
    for (home, away), matchday in zip(fixtures, _edge_matchdays(), strict=True):
        journees[matchday].matches.append(Match(home, away))
    clubs = [clubs_by_name[name] for pot in pots for name in pot]
    return Group(name=LEAGUE_PHASE_NAME, clubs=clubs, calendar=journees)


def _playoff_round(ranking: list[str]) -> Round:
    """Barrages : 9/10 (têtes de série) contre 23/24, 11/12 contre 21/22, 13/14 contre 19/20, 15/16 contre 17/18 ; le tirage apparie
    au hasard les deux têtes de série et les deux non têtes de série de chaque bloc. `Tie.home` = le non tête de série (reçoit l'ALLER) ;
    la tête de série reçoit le retour."""
    ties: list[Tie] = []
    for block in range(4):
        seeded = ranking[DIRECT_SPOTS + 2 * block : DIRECT_SPOTS + 2 * block + 2]
        unseeded = ranking[DIRECT_SPOTS + PLAYOFF_SPOTS - 2 * block - 2 : DIRECT_SPOTS + PLAYOFF_SPOTS - 2 * block]
        order = np.random.permutation(2)
        for s, u in zip(seeded, [unseeded[k] for k in order], strict=True):
            ties.append(Tie(home=u, away=s))
    return Round(number=1, ties=ties, label="Barrages")


def _round_of_16(top8: list[str], playoffs: Round) -> Round:
    """8es de finale : les têtes de série 1-2 rencontrent les vainqueurs des barrages issus des 15e-18e, 3-4 ceux des 13e-14e/19e-20e,
    5-6 ceux des 11e-12e/21e-22e, 7-8 ceux des 9e-10e/23e-24e (les mieux classés évitent les barragistes les plus forts) ; au sein de
    chaque paire de têtes de série, tirage au sort. La tête de série reçoit le retour. Les confrontations sont rangées dans l'ordre du
    tableau standard 8 équipes (1 et 2 sur des moitiés opposées), que `advance_round` apparie ensuite deux par deux."""
    by_seed: dict[int, Tie] = {}
    for block in range(4):
        winners = [playoffs.ties[2 * block].winner, playoffs.ties[2 * block + 1].winner]
        seeds = (2 * (3 - block) + 1, 2 * (3 - block) + 2)
        for seed, k in zip(seeds, np.random.permutation(2), strict=True):
            by_seed[seed] = Tie(home=winners[k], away=top8[seed - 1])
    return Round(number=2, ties=[by_seed[seed] for seed in _seed_order(DIRECT_SPOTS)], label="8es de finale")


def build_knockout(groups: list[Group]) -> Bracket:
    """Tableau de la Ligue des Champions à partir de la phase de ligue terminée : barrages (9e-24e), puis 8es avec les 8 premiers."""
    ranking = groups[0].standings()["Club"].tolist()
    top8 = ranking[:DIRECT_SPOTS]
    bracket = Bracket(rounds=[_playoff_round(ranking)])
    bracket.advance_hooks[1] = lambda playoffs: _round_of_16(top8, playoffs)
    return bracket


def start_champions_league(path: str, legs: int = 2) -> CustomCompetition:
    """Nouvelle Ligue des Champions au vrai format, prête à simuler. `legs` : manches des confrontations à élimination directe (2, le
    vrai format) ; la finale se joue toujours sur un seul match."""
    clubs = load_champions_league_clubs(path)
    return CustomCompetition(
        format=CompetitionFormat.HYBRID,
        legs=legs,
        clubs=clubs,
        preset_groups=[draw_league_phase(path)],
        label="Ligue des Champions",
        knockout_legs=legs,
        final_legs=1,
        knockout_builder=build_knockout,
        league_phase=True,
    )
