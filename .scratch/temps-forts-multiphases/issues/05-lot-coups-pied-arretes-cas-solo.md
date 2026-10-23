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

**Exception accordée (23/10/2026) :** le propriétaire a validé explicitement l'exception `CLAUDE.md` pour `src/ligue1sim/animation/templates.py` (seul fichier interdit touché, avec `tests/test_templates.py`). Aucun autre fichier interdit modifié.

**Décisions du propriétaire (22-23/10/2026) :**
- `but_gag` : même mécanisme que les 8 gabarits de jeu ouvert, fréquence de tirage inchangée (« réaliste » = reste rare).
- `coup_franc` : faute exactement au point du coup franc ; pendant le tir, le fautif est à 9,15 m réglementaires du ballon.
- `penalty` : faute à un point variable dans la surface, ballon replacé (glissement) jusqu'au point de penalty pendant la construction ; pendant le tir, le fautif est à l'entrée de la surface (ligne des 16,5 m) et hors de l'arc ; les coéquipiers du tireur sont aussi hors de l'arc (minimum latéral dérivé du règlement, ~7,31 m au lieu de 6 m).
- `corner` : un seul défenseur scripté, ballon sans porteur pendant la construction.
