# 04: Généralisation — lot "transition / pressing"

**What to build:** les gabarits `recuperation_haute`, `decalage_enroulee` et `percee_individuelle` reçoivent chacun une phase de construction compatible, même principe que les lots précédents.

**Blocked by:** 03 (lot "jeu collectif ouvert") — séquencé pour garder `templates.py` vert lot après lot, un seul lot à la fois sur ce fichier partagé. Et 07 (mouvement des adversaires scriptés pendant la construction) — défaut visuel signalé par le propriétaire (22/10/2026), à régler avant de généraliser à 3 gabarits de plus plutôt que de le répandre davantage.

**Status:** livré (23/10/2026, `1aaddd4`) ; statut mis à jour le 04/11/2026 d'après `git log` (l'ancien statut n'avait pas été reporté)

- [ ] Chacun des 3 gabarits de ce lot est précédé d'au moins un type de phase de construction tactiquement cohérent
- [ ] Continuité des positions (ballon + joueurs) vérifiée sur un échantillon couvrant les 3 gabarits
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Les gabarits hors de ce lot sont 100 % identiques clip à clip
- [ ] Propriétaire valide visuellement un échantillon représentatif des 3 gabarits

**Décision prise avec le propriétaire (22/10/2026)** sur `percee_individuelle` : même mécanisme que les autres gabarits. La construction décrit la perte de balle ADVERSE, jamais le côté collectif/solo de la conclusion elle-même — pas de conflit avec le caractère "solo" de ce gabarit.

**Exception plancher constatée (voir `docs/TRD_PRODUIT.md` NFR-P02)** : sur `decalage_enroulee` (ancrage passeur comme `debordement_centre_tete`/`profondeur_1v1`), un but sans passeur crédité laisse la construction omise (~4-5 % des clips mesurés). `recuperation_haute` (ancrage `support1`, tactique) et `percee_individuelle` (ancrage `scorer`, seul rôle du gabarit) n'ont pas cette exception.

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.
