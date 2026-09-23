"""Pipeline d'habillage visuel des matchs : transforme un événement du
moteur (voir ligue1sim.events) déjà décidé -- buteur, minute, carton... --
en une séquence animée jouable côté Streamlit, SANS jamais influencer le
résultat du match (voir invariants 1-2 de docs/simulation_physique_archi.md).

Pipeline pour un BUT (le seul type couvert par templates.py aujourd'hui --
simplifié le 22/09/2026 à plusieurs reprises : `Sequence` porte directement
des keyframes continus (`animation.types`), `templates.py` construit
directement des `Sequence`, et `sequence_generator.py` porte le choix du
gabarit + le calage sur le résultat connu -- plus d'étages motion.py/
ball.py/render/payload.py/spatial.SpatialEvent/sequences.build_sequence
séparés) :

    GoalEvent (ligue1sim.events, déjà doté de .zone/.assist_zone)
      -> PitchLayoutState        spatial.py -- XI placé (pitch_layout) +
                                  sens d'attaque, converti en
                                  start_positions normalisés
      -> Sequence                sequence_generator.generate_sequence(
                                  event, lineup, pitch_layout_state, rng)
                                  -- LE pivot, déjà sérialisable via .to_json()
      -> render_sequence()       render/component.py -- composant Streamlit

Le moteur Poisson (ligue1sim.simulation/ligue1sim.events) n'est jamais
modifié par ce sous-package -- voir docs/simulation_physique_archi.md.

NOTE ARCHI : `spatial.py` a été restreint le 22/09/2026 aux seules
conversions de référentiel (`SpatialEvent`/`build_spatial_event` supprimés,
absorbés par `templates.py`) -- voir docs/simulation_physique_archi.md pour
l'historique.
"""

from __future__ import annotations

from ligue1sim.animation.types import Sequence
from ligue1sim.events import GoalEvent, MatchEvents


def build_animation(event: GoalEvent, match_events: MatchEvents, *, match_label: str) -> Sequence:
    """Point d'entrée unique du pipeline : un but déjà décidé par le moteur
    + le contexte du match -> une `Sequence` prête pour
    `animation.render.component.render_sequence`.

    Reste à écrire : construire un `spatial.PitchLayoutState` pour l'équipe
    du buteur (via `pitch_layout.place_starting_xi` sur `match_events`, puis
    `spatial.placed_player_to_normalized`), puis appeler
    `sequence_generator.generate_sequence(event, lineup, state, rng)` --
    voir ce module pour le détail (choix du gabarit, calage sur le buteur/
    passeur/minute réels).

    Ne couvre encore que `GoalEvent` -- les autres types d'événement
    (carton, remplacement...) n'ont aucun gabarit dans `templates.py`."""
    # TODO(animation): chaîner les étages du pipeline (voir docstring
    # ci-dessus et docs/simulation_physique_archi.md).
    raise NotImplementedError
