# 01: Penalty accordé après revisionnage VAR

**What to build:** pour un penalty déjà tiré par le moteur (événement déjà décidé, tiré ou raté), la séquence ajoute une étape de revue avant le tir : l'arbitre ne siffle rien au premier abord, un temps d'arrêt « revu par la VAR » s'affiche, puis le penalty est accordé et joué normalement. Ne crée ni ne recalcule aucun évènement — habille un penalty qui allait de toute façon être tiré, contrairement à `but-refuse` qui rhabille une occasion existante.

**Blocked by:** None.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur l'échantillon de référence, au moins un penalty existant est précédé d'une étape de revue VAR avant d'être tiré
- [ ] L'issue du penalty (but/arrêt/raté) reste strictement celle déjà décidée par le moteur
- [ ] Un penalty SANS cette mise en scène (la majorité, par dosage) reste inchangé — pas systématique
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide visuellement la scène de revue sur un échantillon de clips

**Note :** `narrative.py`, `templates.py` sous exception (`CLAUDE.md`) — exception à demander avant de coder.
