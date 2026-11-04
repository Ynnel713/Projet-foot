# 02: POC — phase de construction chaînée au gabarit pilote `contre_attaque`

**What to build:** pour les temps forts qui utilisent le gabarit `contre_attaque`, l'utilisateur voit désormais deux phases de construction enchaînées avant le geste décisif — possession adverse, puis perte de balle (tacle, passe interceptée, ou autre) — au lieu de démarrer directement sur l'action finale. Scénario confirmé par le propriétaire (22/10/2026). Le ballon et les joueurs repartent exactement de la position où chaque phase s'est arrêtée, sans saut visible aux jonctions. Les 11 autres gabarits restent inchangés (un seul geste décisif, comme aujourd'hui).

**Blocked by:** None dans ce lot de tickets. Préalable externe déjà vérifié satisfait (22/10/2026) : clôture du chantier « mouvement collectif » Phase 5 (`a5e7d3d`) et d'A1.1 (`cf63f0f`), tous deux commités.

**Status:** livré (22/10/2026, `c8cd06b`) ; statut mis à jour le 04/11/2026 d'après `git log` (l'ancien statut n'avait pas été reporté)

- [ ] Sur l'échantillon de référence, les clips du gabarit pilote durent au moins 20 secondes
- [ ] Aucun saut de position mesurable à la jonction entre la phase de construction et la conclusion
- [ ] Déterminisme bit-à-bit vérifié (sha256 de `event_ref`, jamais `random`/`hash()`/horloge)
- [ ] Résultat sportif (score, buteurs, cartons, remplacements) strictement identique
- [ ] Les 11 autres gabarits sont 100 % identiques clip à clip (aucun effet de bord)
- [ ] Propriétaire valide visuellement la continuité sur un échantillon de clips `contre_attaque`

**Note :** `templates.py`, `narrative.py`, `sequence_generator.py`, `ball.py`/`motion.py` sont sous exception (`CLAUDE.md`) — exception à demander au propriétaire avant de coder, selon les fichiers réellement touchés.
