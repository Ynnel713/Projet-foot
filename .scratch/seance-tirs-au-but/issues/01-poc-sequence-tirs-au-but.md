# 01: POC — une séance de tirs au but animée

**What to build:** pour un match de phase à élimination directe décidé aux tirs au but (`knockout.py`, `decided_by_penalties`), les temps forts incluent désormais la séance tir par tir — chaque tir réutilise le gabarit `penalty` existant, dans l'ordre et avec l'issue (but/arrêt/raté) déjà fixés par `_penalty_shootout_score` et le score déjà décidé. Aucun nouveau tirage : le vainqueur de la séance reste celui déjà décidé par `_resolve_tiebreak`, cette séquence ne fait que le montrer tir par tir au lieu d'un score affiché seul.

**Blocked by:** None.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur un match décidé aux tirs au but dans l'échantillon de référence, chaque tir de la séance apparaît comme un temps fort distinct, dans le bon ordre
- [ ] Le nombre de tirs et leur issue (but/arrêt/raté) correspondent exactement au score de séance déjà tiré (`penalty_score`), jamais un nouveau tirage parallèle
- [ ] Le dernier tir de la séance (celui qui scelle la qualification) est identifiable comme tel à l'écran
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat de la séance (vainqueur, score) strictement identique à ce que `knockout.py` avait déjà décidé
- [ ] Aucune régression sur les matchs sans séance de tirs au but
- [ ] Propriétaire valide visuellement la séquence complète sur un échantillon de séances

**Note :** `knockout.py`, `narrative.py`, `templates.py` sous exception (`CLAUDE.md`) — exception à demander explicitement avant de coder. Étude technique courte (TRD) recommandée vu la sensibilité de `narrative.py`/`knockout.py`.
