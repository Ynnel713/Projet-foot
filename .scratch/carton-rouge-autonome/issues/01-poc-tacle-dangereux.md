# 01: POC — tacle dangereux comme temps fort autonome

**What to build:** pour un carton rouge déjà tiré par le moteur (`events.py`, `CardEvent.red_card_type`) qui n'est PAS déjà proche d'un but existant, devient un temps fort autonome à part entière dans le match — scénario « tacle dangereux », un nouveau gabarit sans geste de tir, qui se conclut sur le carton plutôt que sur une occasion. Visible dans la vraie séquence de temps forts du match, pas seulement en incrustation sur un autre clip.

**Blocked by:** None.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur l'échantillon de référence, au moins un carton rouge éligible (pas proche d'un but) devient un clip autonome avec le gabarit « tacle dangereux »
- [ ] Un carton rouge déjà proche d'un but existant NE devient PAS un clip autonome (reste uniquement en incrustation, comme aujourd'hui — pas de redondance)
- [ ] Le carton affiché dans ce nouveau clip correspond exactement au carton déjà tiré par le moteur (même joueur, même minute, aucun second tirage)
- [ ] Durée du clip dans la fourchette courte dédiée (10-25s), jamais la fourchette des buts/occasions (20-40s)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif (cartons, exclusion du joueur) strictement identique
- [ ] Les gabarits existants sont 100 % identiques clip à clip
- [ ] Propriétaire valide visuellement la crédibilité du scénario sur un échantillon de clips

**Note :** `narrative.py`, `templates.py` et `render/canvas.html` sont sous exception (`CLAUDE.md`) — exception à demander explicitement au propriétaire avant de coder. Étude technique courte (TRD) recommandée avant de coder, vu la sensibilité de `narrative.py`.
