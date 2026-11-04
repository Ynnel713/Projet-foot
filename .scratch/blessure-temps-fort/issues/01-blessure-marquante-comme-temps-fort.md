# 01: Blessure marquante comme temps fort autonome

**What to build:** pour une blessure déjà tirée par le moteur (`events.py`, `InjuryEvent`) qui n'est PAS déjà proche d'un but existant, devient un temps fort autonome — un joueur touché, l'intervention du staff médical, le remplacement forcé qui s'ensuit. Même mécanisme que `carton-rouge-autonome` : réutilise le tirage existant, pas de second tirage, filtre d'éligibilité identique (pas de redondance avec un but proche).

**Blocked by:** None.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur l'échantillon de référence, au moins une blessure éligible (pas proche d'un but) devient un clip autonome
- [ ] Une blessure déjà proche d'un but existant NE devient PAS un clip autonome (pas de redondance)
- [ ] La blessure affichée correspond exactement à celle déjà tirée par le moteur (même joueur, même minute, même durée d'indisponibilité)
- [ ] Durée du clip dans la fourchette courte des incidents (10-25s, comme `carton-rouge-autonome`)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif (composition, remplacement forcé) strictement identique
- [ ] Propriétaire valide visuellement la crédibilité du scénario sur un échantillon de clips

**Note :** `narrative.py`, `templates.py` sous exception (`CLAUDE.md`) — exception à demander avant de coder.
