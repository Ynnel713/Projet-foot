"""Frontière entre le pipeline Python (animation.sequences.Sequence) et le
rendu HTML/JS/canvas embarqué dans Streamlit. `Sequence.to_json()` porte le
contrat JSON lui-même (voir animation.sequences) -- ce sous-package ne
contient plus que le point d'entrée Streamlit (component.py).
"""
