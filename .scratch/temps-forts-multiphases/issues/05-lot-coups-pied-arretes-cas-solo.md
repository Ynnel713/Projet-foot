# 05: Généralisation — lot "coups de pied arrêtés et cas solo"

**What to build:** les gabarits `coup_franc`, `corner`, `penalty` et `but_gag` reçoivent chacun une phase de construction : pour les coups de pied arrêtés, la phase de construction est la séquence qui mène à l'obtention du coup de pied arrêté (dégagement contré, faute, etc.) plutôt qu'une construction de jeu ouvert classique. C'est le lot le plus différent architecturalement, isolé en dernier pour contenir le risque.

**Blocked by:** 04 (lot "transition / pressing") — séquencé pour garder `templates.py` vert lot après lot.

**Status:** ready-for-agent

- [ ] Chacun des 4 gabarits de ce lot est précédé d'au moins un type de phase de construction cohérent avec son contexte (coup de pied arrêté ou solo)
- [ ] Continuité des positions (ballon + joueurs) vérifiée sur un échantillon couvrant les 4 gabarits
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Les 12 gabarits sont désormais tous couverts (fin de la généralisation) — vérification croisée sur l'ensemble du catalogue
- [ ] Propriétaire valide visuellement un échantillon représentatif des 4 gabarits et un échantillon couvrant les 12 gabarits au global

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.
