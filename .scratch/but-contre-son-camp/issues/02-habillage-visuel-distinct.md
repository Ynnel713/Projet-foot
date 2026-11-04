# 02: Habillage visuel distinct du but contre son camp

**What to build:** une fois le but contre son camp modélisé dans le moteur (ticket 01), l'animation doit le distinguer d'un but normal — pas de célébration du joueur fautif (voir aussi `celebration-but` si ce chantier est en cours), réaction d'abattement plutôt que de joie, scénario de mise en scène dédié (déviation/mauvaise relance plutôt qu'un geste de tir classique).

**Blocked by:** 01 (modéliser le but contre son camp dans le moteur).

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Un but contre son camp affiché utilise un scénario visuel distinct d'un but normal
- [ ] Aucune célébration n'est affichée pour ce type de but
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique à ce que le ticket 01 a déjà décidé
- [ ] Propriétaire valide visuellement le scénario sur un échantillon de clips

**Note :** `templates.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
