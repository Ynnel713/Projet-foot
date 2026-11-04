# 02: Carton rouge requalifié après revisionnage VAR

**What to build:** pour un carton rouge direct déjà tiré par le moteur (`events.py`, `CardEvent.red_card_type == "direct"`), la séquence montre l'arbitre sifflant d'abord un jaune, puis la VAR intervenant pour le faire revenir sur sa décision et requalifier en rouge. Même principe que le ticket 01 : aucun nouvel évènement créé, habille un carton déjà décidé.

**Blocked by:** None, indépendant du ticket 01.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur l'échantillon de référence, au moins un carton rouge direct existant est précédé d'une étape « jaune puis VAR » avant la requalification
- [ ] Le carton reste strictement celui déjà décidé par le moteur (même joueur, même minute)
- [ ] Un carton rouge SANS cette mise en scène (la majorité, par dosage) reste inchangé
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide visuellement la scène sur un échantillon de clips

**Note :** `narrative.py`, `templates.py` sous exception (`CLAUDE.md`) — exception à demander avant de coder.
