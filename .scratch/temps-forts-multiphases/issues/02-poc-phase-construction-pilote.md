# 02: POC — phase de construction chaînée au gabarit pilote `contre_attaque`

**What to build:** pour les temps forts qui utilisent le gabarit `contre_attaque`, l'utilisateur voit désormais une phase de construction (perte de balle / transition) avant le geste décisif, au lieu de démarrer directement sur l'action finale. Le ballon et les joueurs repartent exactement de la position où la phase de construction s'est arrêtée, sans saut visible à la jonction. Les 11 autres gabarits restent inchangés (un seul geste décisif, comme aujourd'hui).

**Blocked by:** None dans ce lot de tickets. Préalable externe, piloté ailleurs : clôture du chantier « mouvement collectif » (Phase 5) et d'A1.1 (inertie) sur `motion.py`/`templates.py`, pour ne pas cumuler deux refontes en parallèle.

**Status:** ready-for-agent

- [ ] Sur l'échantillon de référence, les clips du gabarit `contre_attaque` durent au moins 10 secondes
- [ ] Aucun saut de position mesurable à la jonction entre la phase de construction et la conclusion
- [ ] Déterminisme bit-à-bit vérifié (sha256 de `event_ref`, jamais `random`/`hash()`/horloge)
- [ ] Résultat sportif (score, buteurs, cartons, remplacements) strictement identique
- [ ] Les 11 autres gabarits sont 100 % identiques clip à clip (aucun effet de bord)
- [ ] Propriétaire valide visuellement la continuité sur un échantillon de clips `contre_attaque`

**Note :** `templates.py`, `narrative.py`, `sequence_generator.py`, `ball.py`/`motion.py` sont sous exception (`CLAUDE.md`) — exception à demander au propriétaire avant de coder, selon les fichiers réellement touchés.
