"""Point d'entrée Streamlit : embarque une `Sequence` (voir
animation.types) dans un composant HTML/JS/canvas
(`streamlit.components.v1.html`) -- Streamlit n'a aucune primitive
d'animation native, voir docs/simulation_physique_archi.md.
"""

from __future__ import annotations

from ligue1sim.animation.types import Sequence


def render_sequence(sequence: Sequence, *, height: int = 420) -> None:
    """Affiche `sequence` dans l'écran de détail de match (app.py), via
    `sequence.to_json()` -- le seul contrat que le composant HTML/JS/canvas
    doit connaître (voir invariant 5, docs/simulation_physique_archi.md),
    jamais les dataclasses Python.

    Le template HTML/JS/canvas lui-même (boucle requestAnimationFrame,
    interpolation des keyframes avec easing) reste à écrire -- hors scope
    du squelette, voir docs/simulation_physique_archi.md."""
    # TODO(animation): st.components.v1.html(_TEMPLATE.format(payload=json.dumps(sequence.to_json())), height=height)
    raise NotImplementedError
